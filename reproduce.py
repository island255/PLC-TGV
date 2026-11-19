"""Regenerate the paper's tables from the released labels and measured outcomes.

    python reproduce.py --output reproduced

Requires Python 3.8+ and the standard library. Times come from recorded runs.
This program reads JSON metadata only. Percentiles use the nearest-rank rule.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
from statistics import median


METHODS = {"defuser": "PLC-Defuser", "esbmc": "ESBMC-LLB", "ours": "PLC-TGV"}
DATASETS = ("D1", "D2", "D3")
STRUCTURES = ("nonzero", "stride", "conditional", "reset", "nested", "countdown",
              "extra_state", "two_stage")
DECISIONS = {"VIOLATION", "SAFE"}


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def index_rows(rows, description):
    indexed = {}
    for row in rows:
        key = row["id"]
        if not isinstance(key, str) or not key or key in indexed:
            raise ValueError(f"{description}: missing or duplicate ID {key!r}")
        indexed[key] = row
    return indexed


def check_ids(actual, expected, description):
    missing = set(expected) - set(actual)
    extra = set(actual) - set(expected)
    if missing or extra:
        raise ValueError(f"{description}: missing {sorted(missing)[:5]}, unexpected {sorted(extra)[:5]}")


def inventory(root):
    tasks = index_rows(read(root / "data/task_index.json"), "task index")
    d3 = index_rows(read(root / "data/dataset3.json")["tasks"], "D3 manifest")
    public_ids = [f"case_{i:04d}" for i in range(977)]
    delayed = [f"ext__retained_{i:03d}" for i in range(5)]
    counters = [f"{s}__{v}" for s in STRUCTURES for v in ("normal", "injected_attack")]
    groups = {
        "D1": public_ids[:60] + public_ids[377:], "D2": public_ids[60:377],
        "D3": delayed + counters, "Public": public_ids,
        "All": public_ids + delayed + counters, "Delayed": delayed, "Counter": counters,
    }
    check_ids(tasks, groups["All"], "998-task index")
    check_ids(d3, groups["D3"], "21-task D3 manifest")
    for number, group in enumerate(DATASETS, 1):
        for key in groups[group]:
            row = tasks[key]
            if row["dataset"] != number or type(row["attack_label"]) is not bool:
                raise ValueError(f"{key}: invalid dataset or attack label")
            if not row.get("hashes", {}).get("source") or not row["hashes"].get("properties"):
                raise ValueError(f"{key}: missing program or property fingerprint")
            if number == 3:
                other = d3[key]
                if (other["attack_label"] is not row["attack_label"]
                        or other["hashes"] != row["hashes"]):
                    raise ValueError(f"{key}: inconsistent D3 label or fingerprints")
    return tasks, groups


def load_results(root, name, tasks, keys):
    rows = index_rows(read(root / "results" / (name + ".json")), name)
    check_ids(rows, keys, name)
    for key, row in rows.items():
        if row["dataset"] != tasks[key]["dataset"] or row["hashes"] != tasks[key]["hashes"]:
            raise ValueError(f"{name}/{key}: input identity mismatch")
        seconds = row["seconds"]
        if type(seconds) not in (float, int) or not math.isfinite(seconds) or seconds < 0:
            raise ValueError(f"{name}/{key}: invalid measured duration")
        result = row["result"]
        status = result["verdict"]
        if status not in DECISIONS | {"UNKNOWN"} and not status.startswith(("ERROR", "UNSUPPORTED")):
            raise ValueError(f"{name}/{key}: unexpected verdict {status!r} in this release")
        if result.get("right_censored"):
            raise ValueError(f"{name}/{key}: no observation in the 998-task cohort was censored")
    return rows


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def detection(tasks, rows, keys):
    counts = dict.fromkeys(("TP", "TN", "FP", "FN", "U_pos", "U_neg"), 0)
    admitted_positive = False
    reasons = Counter()
    for key in keys:
        attack = tasks[key]["attack_label"]
        result = rows[key]["result"]
        status = result["verdict"]
        if attack and not status.startswith("UNSUPPORTED") and result.get("invoked") is not False:
            admitted_positive = True
        if status == "VIOLATION":
            outcome = "TP" if attack else "FP"
        elif status == "SAFE":
            outcome = "FN" if attack else "TN"
        else:
            outcome = "U_pos" if attack else "U_neg"
            reasons[status] += 1
        counts[outcome] += 1
    tp, tn, fp, fn, up, un = (counts[c] for c in ("TP", "TN", "FP", "FN", "U_pos", "U_neg"))
    return dict(counts, submitted=len(keys), unresolved=up + un, reasons=dict(reasons),
                precision=ratio(tp, tp + fp), recall=ratio(tp, tp + fn + up),
                f1=ratio(2 * tp, 2 * tp + fp + fn + up) if admitted_positive else None,
                coverage=ratio(tp + tn + fp + fn, len(keys)))


def timings(rows, keys):
    elapsed, decisions, rejections, errors = [], [], [], []
    for key in keys:
        seconds = rows[key]["seconds"]
        elapsed.append(seconds)
        verdict = rows[key]["result"]["verdict"]
        if verdict in DECISIONS:
            decisions.append(seconds)
        elif verdict.startswith("UNSUPPORTED"):
            rejections.append(seconds)
        elif verdict.startswith("ERROR"):
            errors.append(seconds)
    decisions.sort()
    total = math.fsum(elapsed)
    return dict(total_seconds=total, mean_seconds=total / len(keys), resolved=len(decisions),
                submitted=len(keys), median_seconds=median(decisions) if decisions else None,
                p95_seconds=decisions[math.ceil(0.95 * len(decisions)) - 1] if decisions else None,
                rejection_median=median(rejections) if rejections else None,
                error_median=median(errors) if errors else None)


def confirmation_route(result):
    """Count each confirmed task once, even if a path contains duplicate observations."""
    paths = []
    for field, label in (("generator_candidates", "test"), ("symbolic_replays", "verifier")):
        if any((trial.get("replay") or {}).get("confirmed") is True for trial in result.get(field, [])):
            paths.append(label)
    expected = int(result["verdict"] == "VIOLATION")
    if len(paths) != expected:
        raise ValueError("Ablation record has an absent, ambiguous, or unexpected confirmation path")
    return paths[0] if paths else None


def ablation(tasks, rows, keys):
    routes = Counter()
    attack_times = {}
    correct = 0
    for key in keys:
        row = rows[key]
        result = row["result"]
        expected_verdict = "VIOLATION" if tasks[key]["attack_label"] else "SAFE"
        correct += (result["verdict"] == expected_verdict)
        route = confirmation_route(result)
        if route:
            routes[route] += 1
            if tasks[key]["attack_label"]:
                attack_times[key] = row["seconds"]
    report = dict(detection=detection(tasks, rows, keys), property_correct=correct,
                  test=routes["test"], verifier=routes["verifier"],
                  attack_median_seconds=median(attack_times.values()) if attack_times else None)
    return report, attack_times


def summarize(root):
    tasks, groups = inventory(root)
    counts, runtime, ablations, pairs = {}, {}, {}, {}
    for name in METHODS:
        rows = load_results(root, name, tasks, groups["All"])
        counts[name] = {group: detection(tasks, rows, keys) for group, keys in groups.items()}
        runtime[name] = {group: timings(rows, groups[group]) for group in (*DATASETS, "All")}
    attack_times = {}
    for config in ("A", "B", "C"):
        rows = load_results(root, "ablation-" + config.lower(), tasks, groups["D3"])
        ablations[config], attack_times[config] = ablation(tasks, rows, groups["D3"])
    for earlier, later in (("A", "B"), ("B", "C")):
        before, after = attack_times[earlier], attack_times[later]
        shared = sorted(before.keys() & after.keys())
        if any(after[key] <= 0 for key in shared):
            raise ValueError(f"{later}: zero time to confirmation in a paired comparison")
        ratios = {key: before[key] / after[key] for key in shared}
        pairs[earlier + "/" + later] = {
            "common_attacks": len(shared), "median_ratio": median(ratios.values()) if ratios else None,
            "per_task_ratio": ratios,
        }
    return dict(group_sizes={g: len(v) for g, v in groups.items()}, detection=counts,
                runtime=runtime, ablation=ablations, paired_speedups=pairs)


def table(headers, rows):
    lines = [headers, ["---"] * len(headers), *rows]
    return "\n".join("| " + " | ".join(map(str, row)) + " |" for row in lines)


def format_value(value, spec, missing):
    return missing if value is None else format(value, spec)


def render(report, chinese):
    def tr(en, zh):
        return zh if chinese else en

    def fmt(value, spec):
        return format_value(value, spec, tr("N/A", "不适用"))

    titles = [
        tr("Detection effectiveness", "检测效果"), tr("Dataset 3 by group", "数据集 3 分组结果"),
        tr("Ablation", "模块消融"), tr("Paired confirmation times", "配对确认用时"),
        tr("Recorded runtime", "实测时间开销"), tr("Runtime over all submissions", "全部任务的用时"),
    ]
    group_names = dict(D1="D1", D2="D2", D3="D3", Public=tr("Public total", "公开合计"),
                       All=tr("All tasks", "全部任务"), Delayed=tr("Delayed", "长延迟"),
                       Counter=tr("Counter updates", "计数更新"))
    det_header = [tr("Group", "任务组"), tr("Method", "方法"), "TP", "TN", "FP", "FN",
                  "U (+/−)", "F1", tr("Coverage", "覆盖率")]
    tables = []
    for sets in ((*DATASETS, "Public", "All"), ("Delayed", "Counter")):
        rows = []
        for group in sets:
            for method, name in METHODS.items():
                m = report["detection"][method][group]
                rows.append([group_names[group], name, m["TP"], m["TN"], m["FP"], m["FN"],
                             f"{m['unresolved']} ({m['U_pos']}/{m['U_neg']})",
                             fmt(m["f1"], ".2%"), fmt(m["coverage"], ".2%")])
        tables.append(table(det_header, rows))
    rows = []
    for config, a in report["ablation"].items():
        m = a["detection"]
        rows.append([config, m["TP"], m["TN"], m["FP"], m["FN"], m["unresolved"],
                     fmt(m["f1"], ".2%"), f"{a['property_correct']}/{m['submitted']}",
                     a["test"], a["verifier"], fmt(a["attack_median_seconds"], ".3f")])
    tables.append(table([tr("Config.", "配置"), "TP", "TN", "FP", "FN", "U", "F1",
                         tr("Correct property verdicts", "性质判定正确"),
                         tr("Via test", "用例确认"), tr("Via verifier", "符号反例确认"),
                         tr("Median to confirmation (s)", "攻击确认中位用时（秒）")], rows))
    tables.append(table([tr("Ratio", "用时比"), tr("Shared confirmed attacks", "共同确认攻击"),
                         tr("Median per-task ratio", "逐任务比值的中位数")],
                        [[k, p["common_attacks"], fmt(p["median_ratio"], ".2f")]
                         for k, p in report["paired_speedups"].items()]))
    rows = []
    for group in DATASETS:
        for method, name in METHODS.items():
            t = report["runtime"][method][group]
            rows.append([group, name, f"{t['resolved']}/{t['submitted']}",
                         *[fmt(t[k], ".3f") for k in ("median_seconds", "p95_seconds",
                                                        "rejection_median", "error_median")]])
    tables.append(table([tr("Group", "任务组"), tr("Method", "方法"), tr("Resolved/total", "判定/提交"),
                         tr("Median (s)", "判定中位数（秒）"), tr("P95 (s)", "判定P95（秒）"),
                         tr("Rejection median (s)", "拒绝中位数（秒）"),
                         tr("Error median (s)", "错误中位数（秒）")], rows))
    rows = []
    for method, name in METHODS.items():
        t = report["runtime"][method]["All"]
        rows.append([name, t["submitted"], fmt(t["total_seconds"], ".2f"), fmt(t["mean_seconds"], ".2f")])
    tables.append(table([tr("Method", "方法"), tr("Tasks", "任务数"),
                         tr("Total (s)", "总用时（秒）"), tr("Mean (s)", "每项平均用时（秒）")], rows))
    return "\n\n".join("## " + title + "\n\n" + body for title, body in zip(titles, tables)) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["tables"], nargs="?", default="tables")
    parser.add_argument("--output", type=Path, required=True, help="new output directory")
    args = parser.parse_args()
    try:
        report = summarize(Path(__file__).resolve().parent)
        outputs = {"summary.json": json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                   "results_en.md": render(report, False), "results_zh.md": render(report, True)}
        args.output.mkdir(parents=True, exist_ok=False)
        for name, value in outputs.items():
            (args.output / name).write_bytes(value.encode("utf-8"))
    except (OSError, KeyError, ValueError, TypeError) as exc:
        parser.exit(1, f"Table regeneration failed: {exc}\n")
    print(f"998 tasks, 3 methods and 3 ablations verified. Tables saved to {args.output}")


if __name__ == "__main__":
    main()
