# AnesLLM — Label Prevalence

Prevalence (percentage of windows) of each action for the three labels, the distribution of the
consensus `ratio`, and agreement measures between labels.

## Global prevalence (%)

| Action | `result_1` | `result_aux` | `result_real` |
|---|---:|---:|---:|
| `increase_hypnotic` | 4.3% | 7.1% | 8.0% |
| `reduce_hypnotic` | 7.0% | 16.5% | 12.1% |
| `increase_opioid` | 22.9% | 32.3% | 24.3% |
| `reduce_opioid` | 25.7% | 34.6% | 27.7% |
| `no_action` | 39.6% | 8.6% | 27.9% |
| `vasopressor` *(option, not GT)* | 0.5% | 1.0% | – |
| **Total windows** | **84,813** | **84,813** | **84,813** |

## Prevalence by split — `train` (%)

| Action | `result_1` | `result_aux` | `result_real` |
|---|---:|---:|---:|
| `increase_hypnotic` | 4.3% | 7.1% | 8.0% |
| `reduce_hypnotic` | 6.9% | 16.4% | 12.0% |
| `increase_opioid` | 22.9% | 32.3% | 24.3% |
| `reduce_opioid` | 25.7% | 34.5% | 27.8% |
| `no_action` | 39.6% | 8.6% | 27.9% |
| `vasopressor` *(option, not GT)* | 0.5% | 1.1% | – |
| **Total windows** | **80,933** | **80,933** | **80,933** |

## Prevalence by split — `test` (%)

| Action | `result_1` | `result_aux` | `result_real` |
|---|---:|---:|---:|
| `increase_hypnotic` | 4.9% | 6.0% | 8.4% |
| `reduce_hypnotic` | 8.4% | 18.2% | 13.3% |
| `increase_opioid` | 22.2% | 31.1% | 23.8% |
| `reduce_opioid` | 24.8% | 35.9% | 27.2% |
| `no_action` | 39.3% | 8.1% | 27.3% |
| `vasopressor` *(option, not GT)* | 0.3% | 0.6% | – |
| **Total windows** | **3,457** | **3,457** | **3,457** |

## Prevalence by split — `dev` (%)

| Action | `result_1` | `result_aux` | `result_real` |
|---|---:|---:|---:|
| `increase_hypnotic` | 3.8% | 8.3% | 9.2% |
| `reduce_hypnotic` | 10.4% | 21.5% | 14.7% |
| `increase_opioid` | 25.3% | 31.4% | 27.2% |
| `reduce_opioid` | 26.0% | 31.2% | 28.8% |
| `no_action` | 34.5% | 7.6% | 20.1% |
| `vasopressor` *(option, not GT)* | 0.0% | 0.0% | – |
| **Total windows** | **423** | **423** | **423** |

## Consensus `ratio` distribution

The `ratio` field of `result_1` and `result_aux` is the probability assigned by the consensus model to each action.

### `overall`

| Label | n | Mean | Std | Min | p25 | p50 | p75 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `result_1` | 84,813 | 0.571 | 0.170 | 0.203 | 0.443 | 0.555 | 0.683 | 0.999 |
| `result_aux` | 84,813 | 0.230 | 0.105 | 0.000 | 0.155 | 0.229 | 0.300 | 0.495 |

### `train`

| Label | n | Mean | Std | Min | p25 | p50 | p75 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `result_1` | 80,933 | 0.571 | 0.169 | 0.203 | 0.443 | 0.555 | 0.683 | 0.999 |
| `result_aux` | 80,933 | 0.230 | 0.105 | 0.000 | 0.155 | 0.229 | 0.300 | 0.495 |

### `test`

| Label | n | Mean | Std | Min | p25 | p50 | p75 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `result_1` | 3,457 | 0.570 | 0.173 | 0.225 | 0.440 | 0.556 | 0.687 | 0.998 |
| `result_aux` | 3,457 | 0.229 | 0.103 | 0.001 | 0.156 | 0.231 | 0.296 | 0.493 |

### `dev`

| Label | n | Mean | Std | Min | p25 | p50 | p75 | Max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `result_1` | 423 | 0.537 | 0.177 | 0.220 | 0.392 | 0.515 | 0.659 | 0.997 |
| `result_aux` | 423 | 0.236 | 0.093 | 0.001 | 0.178 | 0.237 | 0.288 | 0.477 |

## Agreement between labels

Interpretation: `top1_accuracy` = how often `result_1` matches `result_real`; `top2_recall` = how often `result_real` is among `result_1` and `result_aux` (plausible coverage).

| Split | Windows | top1_accuracy | top2_recall | result_1 == result_aux |
|---|---:|---:|---:|---:|
| `overall` | 84,813 | 55.8% | 80.4% | 0.0% |
| `train` | 80,933 | 55.8% | 80.4% | 0.0% |
| `test` | 3,457 | 56.8% | 81.3% | 0.0% |
| `dev` | 423 | 49.4% | 73.8% | 0.0% |

## Global confusion matrix — `result_1` vs `result_real`

Rows = `result_real` (ground truth), columns = `result_1`.

| real \ r1 | `increase_hypnotic` | `reduce_hypnotic` | `increase_opioid` | `reduce_opioid` | `no_action` |
|---|---:|---:|---:|---:|---:|
| `increase_hypnotic` | 1654 | 310 | 1610 | 887 | 2275 |
| `reduce_hypnotic` | 299 | 2798 | 1141 | 2001 | 3906 |
| `increase_opioid` | 818 | 577 | 10400 | 5457 | 3343 |
| `reduce_opioid` | 405 | 1428 | 5026 | 12496 | 4085 |
| `no_action` | 493 | 836 | 1243 | 954 | 19974 |

## Global confusion matrix — `result_aux` vs `result_real`

Rows = `result_real` (ground truth), columns = `result_aux`.

| real \ aux | `increase_hypnotic` | `reduce_hypnotic` | `increase_opioid` | `reduce_opioid` | `no_action` |
|---|---:|---:|---:|---:|---:|
| `increase_hypnotic` | 1361 | 749 | 2157 | 1587 | 880 |
| `reduce_hypnotic` | 420 | 2876 | 1761 | 3849 | 1202 |
| `increase_opioid` | 1556 | 1315 | 7102 | 8604 | 1995 |
| `reduce_opioid` | 659 | 2845 | 11062 | 7563 | 1233 |
| `no_action` | 2007 | 6174 | 5273 | 7720 | 1991 |

## Associated CSV files

- `reports/result_label_prevalence.csv` — prevalences (long format)
- `reports/result_ratio_distribution.csv` — ratio distribution
- `reports/result_label_agreement.csv` — agreement measures
- `reports/confusion_result_1_vs_real.csv` and `reports/confusion_result_aux_vs_real.csv` — confusion matrices
