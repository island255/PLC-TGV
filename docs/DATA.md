# Task and file provenance

The unit is a task (program, safety requirement and execution profile). The [index](../data/task_index.json) retains the original task ID even if another task has identical inputs. The 977 public tasks contain 602 distinct source byte sequences and 607 distinct source–requirement combinations.

| Dataset | Corpus | Tasks | Source identity |
| --- | --- | ---: | --- |
| 1 | C1, water-tank programs | 60 | PLC-LD dataset snapshot `c2ee23242361f5e9f17bdfc47991edc176a420b9` in the ESBMC-LLB artifact |
| 1 | C4, SWaT archive | 300 | PLC-Defuser v1.0.0, Zenodo record 14014820 |
| 1 | C4, SWaT repository version | 300 | PLC-Defuser snapshot `0361129c1fc3a0b55d63f1df2bdd66897fb7f4ba` |
| 2 | C2, adaptive | 5 | ESBMC-LLB artifact `d97a8b04724230e1e41cca901faeac4d72c67be3` |
| 2 | C3, scaling | 312 | Same artifact revision. The retained task list contains 312 entries. |
| 3 | Delayed counters | 5 | Dantas et al., IEC 61131-3 Formal Verification Benchmark Suite, revision `8de8d1fe3ab67499727954d44f00abed5f58db80` |
| 3 | Counter-update structures | 16 | Eight normal programs paired with eight known injected versions. Normal program sources and all properties are supplied. |

## Reading the records

`source` and `properties` are historical paths relative to the original study workspace. `packaged_source` and `packaged_properties` are paths relative to this repository. A null packaged source denotes a program whose bytes are absent from this distribution. Every packaged property can be verified against the original bytes for its task. All file digests are SHA-256; line endings are significant. The [public source index](../data/public_provenance.json) also records the relative paths and revisions in the original public corpora. The [Dataset 3 manifest](../data/dataset3.json) preserves the original task IDs, origins, and native-input digests where available.

The label `attack_label` comes from the benchmark or the known construction of the controlled case. The detection tables compare these labels with analyzer outputs. In individual C1, C2 and C4 records, an availability objective is represented by a tautological invariant. In those tasks the executed profile also matters for availability faults. Reading the invariant on its own does not reproduce the detector's decision.

The original observations identify methods, environments and analyzed bytes. The digests in [results/identity](../results/identity/) belong to the original measurement environment. The [package checksums](../SHA256SUMS.json) identify the files shipped in this version.

## Primary sources and credit

- L. Rinieri et al., *PLC-Defuser: Detecting hidden Ladder Logic Bombs in PLCs via Control Flow Graph and model checking*, Computers & Security 169 (2026), 104983. [Paper](https://doi.org/10.1016/j.cose.2026.104983) · [archived dataset](https://doi.org/10.5281/zenodo.14014820)
- P. Dantas, L. Cordeiro and W. Junior, *Detecting Ladder Logic Bombs in IEC 61131-3 PLC Programs using ESBMC-PLC+: A Formal Verification Approach with Trigger Synthesis*. [Paper](https://arxiv.org/abs/2607.08417) · [versioned author artifact](https://doi.org/10.5281/zenodo.20930052)
- P. Dantas et al., *IEC 61131-3 Formal Verification Benchmark Suite*. The version used for the five delayed cases is identified above. [Benchmark project](https://github.com/pierredantas/esbmc-plc-benchmark-suite)

Third-party materials retain their original licenses. See [license scope](../LICENSE.md).
