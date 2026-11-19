# PLC-TGV

This repository accompanies the PLC-TGV study on detecting PLC logic bombs with trigger-guided test generation and symbolic verification. It contains the measurements behind the paper, source-analysis components, and eight normal Structured Text programs. [中文说明](README.zh-CN.md)

## Reproduce the paper tables

From the repository root, run the following commands with Python 3.8 or later. These steps use only the standard library and work offline. Choose a new directory for each run.

```shell
python -B tools/verify.py
python -B reproduce.py --output reproduced
```

Open `reproduced/results_en.md` or `reproduced/results_zh.md`. The machine-readable `reproduced/summary.json` includes paired per-task time ratios. The [reference tables](reference/results_en.md) give the expected values.

| Method | End-to-end F1, 998 tasks | Mean recorded seconds per submitted task |
| --- | ---: | ---: |
| PLC-TGV | 98.08% | 0.85 |
| PLC-Defuser | 28.86% | 48.35 |
| ESBMC-LLB | 94.56% | 5.52 |

These times are the original serial measurements. Running the commands above measures no solver time. Each submitted task is counted once, including unresolved tasks.

## What is included

| Material | Scope |
| --- | --- |
| [Task index](data/task_index.json) | 660 PLC-Defuser benchmark tasks, 317 ESBMC-LLB tasks and 21 counter benchmark tasks. Each row records the label and the input hashes. |
| [Safety requirements](data/property_index.json) | All 998 tasks reference one of six byte-distinct property files. The index maps the exact SHA-256 to the file and its number of tasks. |
| [Recorded outcomes](results/) | Three sets of 998 primary outcomes and timings, plus three sets of 21 ablation observations. Replay evidence in the released observations is represented by confirmation flags and sequence fingerprints. |
| [Source analysis](analysis/README.md) | Structured Text parsing, scan control flow, property dependencies and scalar execution. The accompanying finite-state check runs on the eight included normal programs. |
| [PLCopen XML reader](xml_frontend/inspect_plcopen.py) | Reports program units, ST syntax categories and LD wiring from a local project. It uses the structural reader from the XML analysis path. [Module origins](xml_frontend/module_origins.json) |
| [Input provenance](docs/DATA.md) | Corpus versions, upstream citations, label definitions, and the location of the original program and property in the study inventory. |

The complete tables can be regenerated from the saved observations. The source-analysis examples exercise parts of the verification pipeline on real inputs. A fresh run of all three historical detectors on all 998 programs also requires the original input collections and detector environments. Executable attack programs and input traces capable of activating them are omitted from this public repository. Third-party source collections are cited at their original releases.

See [measurement and metric definitions](docs/METRICS.md) and [licensing](LICENSE.md).
