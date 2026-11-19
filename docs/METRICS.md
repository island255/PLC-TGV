# Interpreting the regenerated tables

A task has an attack or negative label. A confirmed violation on an attack-labelled task counts as TP, and an alert on a negative as FP. A completed no-alert decision counts as FN or TN according to the label. A rejected input, error, unknown result or unconfirmed counterexample remains unresolved. Let U+ and U− count unresolved positive and negative tasks.

- End-to-end F1 = 2 TP / (2 TP + FP + FN + U+).
- Decision coverage = (TP + TN + FP + FN) / submitted tasks.
- For PLC-Defuser on Dataset 1 the released interface rejected every attack input. The table marks its dataset-specific F1 unavailable and includes every task in the pooled counts. ESBMC-LLB accepted the Dataset 3 attack inputs and returned unknown for all 13, yielding an end-to-end F1 of zero there.

RQ1 evaluates all 977 public tasks; RQ2 evaluates the 21 Dataset 3 tasks. The combined scores count each of the 998 tasks exactly once. The paper's baselines are the released PLC-Defuser components and the reconstructed ESBMC-LLB author artifact reporting version 8.3.0. The 1,030-task historical evaluation used a different population.

RQ3 compares symbolic verification and replay (A), adding trigger-guided generation (B), and applying property-based filtering to that generation (C). All three use the same 21 tasks. Confirmation-path counts refer to the first path that supplied a replay-confirmed violation. Each configuration's median attack confirmation time uses the attacks it confirmed. The median paired speedup uses only attacks confirmed by both configurations. For A/B there are nine such attacks; the median is 1,973.88. Runtime ratios in this comparison do not characterize all submitted tasks.

RQ4 uses one serial observation per task and includes time spent on unresolved inputs in totals and means. Median and P95 times for completed decisions use resolved tasks only. The P95 is the nearest-rank percentile. There was no preset per-task wall-clock limit in these final runs. Program exploration bounds still applied. The 998 retained observations include no manually stopped run.

`results/{ours,defuser,esbmc}.json` contain the three sets of primary observations. `results/ablation-{a,b,c}.json` contain the separate ablation observations. `original_record_sha256` identifies the original detailed run record. A trace or schedule field in these compact records is a cryptographic fingerprint. The program does not interpret it as an executable trace.
