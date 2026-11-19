# Scalar ST analysis

This component reads the eight normal Dataset 3 controls. It constructs a single-scan control-flow graph (CFG), finds the variables on which the supplied property depends, and checks the property after each simulated scan. It runs locally with the Python standard library. The command accepts a control ID from `controls/index.json` and verifies its source and property hashes before use.

```sh
python -B analyze.py --all
python -B analyze.py --case countdown__normal --state-limit 80000
```

The first command is a short check of all eight controls. With the default limit of 256 retained states, each returns `UNKNOWN` because unexplored states remain. The second command explores the countdown control to completion. It reports 12 CFG nodes, 14 edges and the property-related variables `hazard`, `pump` and `start`. The audit reaches 67,535 states and checks 270,140 transitions before reporting `SAFE`. Increasing the limit increases time and memory use.

To reproduce the completed audit for every included control, run `python -B analyze.py --all --state-limit 270000`. All eight reachable-state closures completed on Windows with CPython 3.13.2. Per-control counts and verdicts are in [verified_controls.json](verified_controls.json). The short check also ran with CPython 3.8.20.

## Relation to the paper

`st_syntax.py` and `scalar_model.py` contain parsing, scalar typing and scan-execution functions from the evaluated research code. `scan_cfg.py` uses its single-scan CFG, data- and guard-dependency collection, and transitive backward traversal from the property variables. The counts and property dependencies can be compared directly on the original controls. `origin.json` identifies the original modules, line selections, adaptations, and file hashes.

`state_check.py` is derived from the project's independent explicit-state validation oracle. It enumerates Boolean input combinations at each reachable retained state and evaluates the entire program against the requirement after each scan. The graph analysis and the property check use the same program, and the checker explores all retained variables. A completed closure yields `SAFE` under the stated program and input model. An observed violation yields `VIOLATION`, and reaching the state limit yields `UNKNOWN`. The output contains verdicts and counts.

The paper's trigger-guided test generator and symbolic verification backend are separate algorithms. This component exposes the front end, dependency analysis, concrete scan semantics, and the independent explicit-state audit. Fresh audit times and state counts are specific to this component. The paper's detector and baseline metrics are reproduced from archived per-task observations in the main results artifact.

## Inputs, provenance, and licenses

Each `controls/<id>/` folder contains the original unmodified `original.st` and `props.json` for one normal task. The safety property and scan behavior are evaluated directly from these files. The ST subset supports one scalar program with `BOOL`, `INT`, and `DINT`, assignments and conditional statements. The explicit-state audit supports up to eight Boolean inputs. Integer operations use the source model's fixed-width signed semantics.

Required Notice: Copyright (c) 2026 PLC-TGV contributors. Original software is licensed under [PolyForm Noncommercial 1.0.0](licenses/PolyForm-Noncommercial-1.0.0.txt). The contributors' original data contributions in these eight normal controls, their property files, and related documentation use [CC BY-NC 4.0](licenses/CC-BY-NC-4.0.txt). Attribute the PLC-TGV contributors and accompanying paper, retain notices, and identify modifications.
