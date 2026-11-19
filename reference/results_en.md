## Detection effectiveness

| Group | Method | TP | TN | FP | FN | U (+/−) | F1 | Coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D1 | PLC-Defuser | 0 | 174 | 0 | 0 | 486 (330/156) | N/A | 26.36% |
| D1 | ESBMC-LLB | 291 | 329 | 0 | 0 | 40 (39/1) | 93.72% | 93.94% |
| D1 | PLC-TGV | 313 | 325 | 0 | 14 | 8 (3/5) | 97.36% | 98.79% |
| D2 | PLC-Defuser | 78 | 78 | 0 | 0 | 161 (83/78) | 65.27% | 49.21% |
| D2 | ESBMC-LLB | 161 | 156 | 0 | 0 | 0 (0/0) | 100.00% | 100.00% |
| D2 | PLC-TGV | 159 | 156 | 0 | 0 | 2 (2/0) | 99.38% | 99.37% |
| D3 | PLC-Defuser | 7 | 6 | 0 | 0 | 8 (6/2) | 70.00% | 61.90% |
| D3 | ESBMC-LLB | 0 | 8 | 0 | 0 | 13 (13/0) | 0.00% | 38.10% |
| D3 | PLC-TGV | 13 | 8 | 0 | 0 | 0 (0/0) | 100.00% | 100.00% |
| Public total | PLC-Defuser | 78 | 252 | 0 | 0 | 647 (413/234) | 27.42% | 33.78% |
| Public total | ESBMC-LLB | 452 | 485 | 0 | 0 | 40 (39/1) | 95.86% | 95.91% |
| Public total | PLC-TGV | 472 | 481 | 0 | 14 | 10 (5/5) | 98.03% | 98.98% |
| All tasks | PLC-Defuser | 85 | 258 | 0 | 0 | 655 (419/236) | 28.86% | 34.37% |
| All tasks | ESBMC-LLB | 452 | 493 | 0 | 0 | 53 (52/1) | 94.56% | 94.69% |
| All tasks | PLC-TGV | 485 | 489 | 0 | 14 | 10 (5/5) | 98.08% | 99.00% |

## Dataset 3 by group

| Group | Method | TP | TN | FP | FN | U (+/−) | F1 | Coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Delayed | PLC-Defuser | 2 | 0 | 0 | 0 | 3 (3/0) | 57.14% | 40.00% |
| Delayed | ESBMC-LLB | 0 | 0 | 0 | 0 | 5 (5/0) | 0.00% | 0.00% |
| Delayed | PLC-TGV | 5 | 0 | 0 | 0 | 0 (0/0) | 100.00% | 100.00% |
| Counter updates | PLC-Defuser | 5 | 6 | 0 | 0 | 5 (3/2) | 76.92% | 68.75% |
| Counter updates | ESBMC-LLB | 0 | 8 | 0 | 0 | 8 (8/0) | 0.00% | 50.00% |
| Counter updates | PLC-TGV | 8 | 8 | 0 | 0 | 0 (0/0) | 100.00% | 100.00% |

## Ablation

| Config. | TP | TN | FP | FN | U | F1 | Correct property verdicts | Via test | Via verifier | Median to confirmation (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 9 | 8 | 0 | 0 | 4 | 81.82% | 17/21 | 0 | 9 | 1857.216 |
| B | 13 | 8 | 0 | 0 | 0 | 100.00% | 21/21 | 13 | 0 | 0.998 |
| C | 13 | 8 | 0 | 0 | 0 | 100.00% | 21/21 | 13 | 0 | 0.952 |

## Paired confirmation times

| Ratio | Shared confirmed attacks | Median per-task ratio |
| --- | --- | --- |
| A/B | 9 | 1973.88 |
| B/C | 13 | 1.01 |

## Recorded runtime

| Group | Method | Resolved/total | Median (s) | P95 (s) | Rejection median (s) | Error median (s) |
| --- | --- | --- | --- | --- | --- | --- |
| D1 | PLC-Defuser | 174/660 | 0.894 | 0.953 | 0.004 | N/A |
| D1 | ESBMC-LLB | 620/660 | 0.058 | 98.656 | N/A | 0.123 |
| D1 | PLC-TGV | 652/660 | 0.816 | 0.930 | 0.780 | N/A |
| D2 | PLC-Defuser | 156/317 | 0.722 | 0.767 | 0.003 | N/A |
| D2 | ESBMC-LLB | 317/317 | 0.060 | 0.525 | N/A | N/A |
| D2 | PLC-TGV | 315/317 | 0.820 | 0.903 | 0.791 | N/A |
| D3 | PLC-Defuser | 13/21 | 24.028 | 8654.509 | 0.005 | 3480.909 |
| D3 | ESBMC-LLB | 8/21 | 0.123 | 0.161 | N/A | N/A |
| D3 | PLC-TGV | 21/21 | 0.939 | 3.111 | N/A | N/A |

## Runtime over all submissions

| Method | Tasks | Total (s) | Mean (s) |
| --- | --- | --- | --- |
| PLC-Defuser | 998 | 48257.35 | 48.35 |
| ESBMC-LLB | 998 | 5507.88 | 5.52 |
| PLC-TGV | 998 | 849.71 | 0.85 |
