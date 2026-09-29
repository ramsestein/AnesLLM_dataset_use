# AnesLLM — Label Counts

Absolute **counts** of each action for the three `output` labels: `result_1` (primary
consensus), `result_aux` (alternative consensus) and `result_real` (ground truth). Totals match
the number of windows in each split.

## Global (all splits)

### `result_1` — primary consensus

| Action | Count | Prevalence |
|---|---:|---:|
| `increase_hypnotic` | 3,669 | 4.3% |
| `reduce_hypnotic` | 5,949 | 7.0% |
| `increase_opioid` | 19,420 | 22.9% |
| `reduce_opioid` | 21,795 | 25.7% |
| `no_action` | 33,583 | 39.6% |
| `vasopressor` *(option, not GT)* | 397 | 0.5% |
| **Total** | **84,813** | **100%** |

### `result_aux` — alternative consensus

| Action | Count | Prevalence |
|---|---:|---:|
| `increase_hypnotic` | 6,003 | 7.1% |
| `reduce_hypnotic` | 13,959 | 16.5% |
| `increase_opioid` | 27,355 | 32.3% |
| `reduce_opioid` | 29,323 | 34.6% |
| `no_action` | 7,301 | 8.6% |
| `vasopressor` *(option, not GT)* | 872 | 1.0% |
| **Total** | **84,813** | **100%** |

### `result_real` — ground truth

| Action | Count | Prevalence |
|---|---:|---:|
| `increase_hypnotic` | 6,782 | 8.0% |
| `reduce_hypnotic` | 10,231 | 12.1% |
| `increase_opioid` | 20,630 | 24.3% |
| `reduce_opioid` | 23,532 | 27.7% |
| `no_action` | 23,638 | 27.9% |
| **Total** | **84,813** | **100%** |

## Split `train`

### `result_1`

| Action | Count | Prevalence |
|---|---:|---:|
| `increase_hypnotic` | 3,482 | 4.3% |
| `reduce_hypnotic` | 5,614 | 6.9% |
| `increase_opioid` | 18,545 | 22.9% |
| `reduce_opioid` | 20,828 | 25.7% |
| `no_action` | 32,079 | 39.6% |
| `vasopressor` *(option, not GT)* | 385 | 0.5% |
| **Total** | **80,933** | **100%** |

### `result_aux`

| Action | Count | Prevalence |
|---|---:|---:|
| `increase_hypnotic` | 5,760 | 7.1% |
| `reduce_hypnotic` | 13,238 | 16.4% |
| `increase_opioid` | 26,147 | 32.3% |
| `reduce_opioid` | 27,949 | 34.5% |
| `no_action` | 6,988 | 8.6% |
| `vasopressor` *(option, not GT)* | 851 | 1.1% |
| **Total** | **80,933** | **100%** |

### `result_real`

| Action | Count | Prevalence |
|---|---:|---:|
| `increase_hypnotic` | 6,452 | 8.0% |
| `reduce_hypnotic` | 9,710 | 12.0% |
| `increase_opioid` | 19,691 | 24.3% |
| `reduce_opioid` | 22,470 | 27.8% |
| `no_action` | 22,610 | 27.9% |
| **Total** | **80,933** | **100%** |

## Split `test`

### `result_1`

| Action | Count | Prevalence |
|---|---:|---:|
| `increase_hypnotic` | 171 | 4.9% |
| `reduce_hypnotic` | 291 | 8.4% |
| `increase_opioid` | 768 | 22.2% |
| `reduce_opioid` | 857 | 24.8% |
| `no_action` | 1,358 | 39.3% |
| `vasopressor` *(option, not GT)* | 12 | 0.3% |
| **Total** | **3,457** | **100%** |

### `result_aux`

| Action | Count | Prevalence |
|---|---:|---:|
| `increase_hypnotic` | 208 | 6.0% |
| `reduce_hypnotic` | 630 | 18.2% |
| `increase_opioid` | 1,075 | 31.1% |
| `reduce_opioid` | 1,242 | 35.9% |
| `no_action` | 281 | 8.1% |
| `vasopressor` *(option, not GT)* | 21 | 0.6% |
| **Total** | **3,457** | **100%** |

### `result_real`

| Action | Count | Prevalence |
|---|---:|---:|
| `increase_hypnotic` | 291 | 8.4% |
| `reduce_hypnotic` | 459 | 13.3% |
| `increase_opioid` | 824 | 23.8% |
| `reduce_opioid` | 940 | 27.2% |
| `no_action` | 943 | 27.3% |
| **Total** | **3,457** | **100%** |

## Split `dev`

### `result_1`

| Action | Count | Prevalence |
|---|---:|---:|
| `increase_hypnotic` | 16 | 3.8% |
| `reduce_hypnotic` | 44 | 10.4% |
| `increase_opioid` | 107 | 25.3% |
| `reduce_opioid` | 110 | 26.0% |
| `no_action` | 146 | 34.5% |
| **Total** | **423** | **100%** |

### `result_aux`

| Action | Count | Prevalence |
|---|---:|---:|
| `increase_hypnotic` | 35 | 8.3% |
| `reduce_hypnotic` | 91 | 21.5% |
| `increase_opioid` | 133 | 31.4% |
| `reduce_opioid` | 132 | 31.2% |
| `no_action` | 32 | 7.6% |
| **Total** | **423** | **100%** |

### `result_real`

| Action | Count | Prevalence |
|---|---:|---:|
| `increase_hypnotic` | 39 | 9.2% |
| `reduce_hypnotic` | 62 | 14.7% |
| `increase_opioid` | 115 | 27.2% |
| `reduce_opioid` | 122 | 28.8% |
| `no_action` | 85 | 20.1% |
| **Total** | **423** | **100%** |

## Associated CSV files

- `reports/result_label_counts.csv` — absolute counts (long format)
- `reports/result_label_prevalence.csv` — counts and prevalences (long format)
