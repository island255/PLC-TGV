"""Check the released bytes and the association of each task with its inputs."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys


ROOT = Path(__file__).resolve().parents[1]


def load(relative):
    return (ROOT / relative).read_text(encoding="utf-8-sig")


def local_file(relative):
    name = PurePosixPath(relative)
    if name.is_absolute() or ".." in name.parts or "\\" in relative or ":" in relative:
        raise ValueError(f"Invalid package-relative path: {relative!r}")
    p = ROOT.joinpath(*name.parts).resolve(strict=True)
    p.relative_to(ROOT)
    if not p.is_file():
        raise ValueError(f"Expected a regular file: {relative}")
    return p


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def verify():
    checksums = json.loads(load("SHA256SUMS.json"))
    if not checksums:
        raise ValueError("Empty package checksum manifest")
    for relative, expected in checksums.items():
        if digest(local_file(relative)) != expected:
            raise ValueError(f"Checksum mismatch: {relative}")
    tasks = json.loads(load("data/task_index.json"))
    if len(tasks) != 998 or len({t["id"] for t in tasks}) != 998:
        raise ValueError("Task index must contain 998 different IDs")
    normal_sources = 0
    properties = set()
    for task in tasks:
        for kind in ("properties", "source"):
            field = task["packaged_" + kind]
            if field is None and kind == "source":
                continue
            if field not in checksums or checksums[field] != task["hashes"][kind]:
                raise ValueError(f"Incorrect {kind} reference on {task['id']}")
            if kind == "source":
                if task["dataset"] != 3 or task["attack_label"]:
                    raise ValueError(f"Unexpected local source for {task['id']}")
                normal_sources += 1
            else:
                properties.add(field)
    if normal_sources != 8 or len(properties) != 6:
        raise ValueError("Unexpected distribution of packaged inputs")
    print(f"Verified {len(checksums)} package files.")
    print("Verified 998 task-to-property references, 6 distinct property files, and 8 original normal sources.")


if __name__ == "__main__":
    try:
        verify()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        sys.exit(f"Integrity check failed: {exc}")
