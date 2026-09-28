# AnesLLM Dataset — Audit Report

This report describes the verification checks performed on the final `dataset/`
(dev/train/test) and their results. It is purely descriptive; the corresponding machine-readable
outputs live in `dataset/reports/`.

## 1. Split integrity

Checks that the three splits are disjoint and well-formed.

- **Case overlap** between dev/train/test: **0** — every case appears in exactly one split.
- **Duplicate `window_id`**: **0**.
- **Temporal order**: 0 cases with decreasing timestamps. 526 cases have two consecutive
  windows with the *same* `time_since_induction_sec` (duplicate timestamps, not disorder).

Output: `dataset/reports/split_integrity.csv`.

## 2. Output consistency

Checks the validity of the `output` block of every window.

- `ratio` values within `[0, 1]` and `result_1.ratio + result_aux.ratio ≤ 1`: **0 violations**.
- `result_1.action ≠ result_aux.action`: **always true**.
- Vocabulary: `result_real` always in the 5 ground-truth classes; `result_1`/`result_aux` always
  in the 6-option vocabulary (5 classes + `vasopressor`): **0 violations**.
- Concordance (agreement between model and clinician):

| Group | top1 = result_real | result_real ∈ top2 |
|---|---|---|
| overall | 55.8% | 80.4% |
| easy | 61.5% | 86.6% |
| medium | 56.5% | 80.9% |
| hard | 50.1% | 74.7% |

Output: `dataset/reports/output_consistency.csv`.

## 3. Leakage

Confirms no post-decision information is present in `input`. All 21 excluded columns
(`gt_action`, `event_*`, `acceptable_set`, `top2*`, `entropy`, `fragility`, `dt_next`,
horizons `*_h1..h5`, presence flags, etc.) are absent from `input`: **no leakage**.

Output: `dataset/reports/leakage.csv`.

## 4. Class balance

Ground-truth class distribution (overall):

| action | share |
|---|---|
| `no_action` | 27.9% |
| `reduce_opioid` | 27.8% |
| `increase_opioid` | 24.3% |
| `reduce_hypnotic` | 12.1% |
| `increase_hypnotic` | 8.0% |

Output: `dataset/reports/class_balance.csv`.

## 5. Numeric sanity

Range checks against physiologically plausible bounds. Most variables are clean. Findings:

- **Impossible hemodynamic values** (negative or absurd blood pressure, e.g. `MAP < 0` or
  `MAP > 250`) affect **1,730 windows** across dev and train, originating from VitalDB track
  artifacts. They are **kept but reported** (see §9).
- `lab_cr`: 27 values above 20 mg/dL (max 21.45). `mac`: 1 value above 3 (max 3.1).
- `PPV`/`SVV` showed heavy artifacts (>100%) and were **removed entirely** from the dataset.

Output: `dataset/reports/numeric_sanity.csv`.

## 6. Train/test drift

Compares feature distributions between `train` and `test` (Kolmogorov–Smirnov test + Population
Stability Index) to verify the test set is representative.

- `result_real` class distribution: total-variation distance **0.011** → no drift.
- No feature shows meaningful drift except `lab_k` (PSI 0.14) and `lab_plt` (PSI 0.11), mildly
  shifted. The dataset is **portable** between train and test.

Output: `dataset/reports/train_test_drift.csv`.

## 7. Missingness

Null fraction per window, aggregated by split and difficulty.

| Group | mean null score |
|---|---|
| dev | 0.313 |
| train | 0.119 |
| test | 0.124 |
| easy | 0.129 |
| medium | 0.117 |
| hard | 0.120 |

Output: `dataset/reports/missingness.csv`.

## 8. Coverage per variable

Percentage of non-null values for each of the 280 input fields (plus the 7 vital signals),
broken down by split and by difficulty.

Output: `dataset/reports/coverage_by_variable.csv`.

## 9. Bad-value case inventory

Cases containing at least one physiologically impossible value, with the offending fields:

- `dev`: 1 case (`case3807`, 5/423 windows = 1.18%).
- `train`: 864 cases (1,725/80,933 windows = 2.13%).
- `test`: **0** — any case with impossible values was moved out of test into train to guarantee
  maximum evaluation quality.

Output: `audit/bad_cases.csv` (case, split, number of bad windows, reasons).

## 10. Privacy (k-anonymity)

Evaluated at window level.

- With **demographics only**, windows are grouped (k ≥ 3), but this is misleading: windows of
  the same patient repeat the same profile.
- Adding **vital signs** makes 75.3% of windows unique (**k = 1**): the concrete vitals
  re-identify the window.
- Direct identifiers `pt_caseid` and `pt_subjectid` are present and must be removed before any
  public release.

## 11. Data dictionary

Every variable is documented (identifier, type, English description) in
`dataset/reports/data_dictionary.csv` (292 entries: 280 input fields + 7 vitals + 5 output fields).
