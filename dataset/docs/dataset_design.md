# AnesLLM Dataset — Design and Creation

This document describes how the dataset was designed and built, end to end. The pipeline runs
in two stages: (1) extraction of the decision windows from the raw VitalDB signals, and
(2) enrichment and re-derivation of the *acceptable actions* and the final splits.

## 1. Source: VitalDB

[VitalDB](https://vitaldb.net) is a public dataset of high-resolution intraoperative biosignals
from **Seoul National University Hospital** (South Korea), comprising 6,388 surgical cases with
continuous waveforms (ECG, arterial pressure, plethysmography, capnography, BIS…) and clinical
records (demographics, labs, drugs, ventilator settings).

## 2. Step 1 — Extraction of decision windows

### 2.1 Window definition

Each decision is anchored to a point in time; everything *before* that point is the model's
input, and the action taken *at* that point is the label.

- **Vitals window**: the 10 minutes preceding the decision (sampled as a time series with
  offsets from the decision point).
- **Action/event history**: the 20 minutes preceding the decision.
- **Decision point**: `t = 0`, the moment the anesthesiologist acts.

This 10-minute / 20-minute split was chosen as a compromise between having enough context to
characterize the hemodynamic state and keeping the window short enough that the state is still
the one being acted upon.

### 2.2 Action vocabulary and `no_action`

The raw signal of interest is the **infusion rate of the two drug families**:

- hypnotics (propofol, sevoflurane),
- opioids (remifentanil).

A ground-truth action is the *direction of change* of a drug infusion at the decision point:

- `increase_hypnotic` / `reduce_hypnotic` (hypnotic rate up/down),
- `increase_opioid` / `reduce_opioid` (opioid rate up/down),
- `no_action` — **no infusion-rate change was performed** at that moment.

The `no_action` rule is what turns a dense, mostly-stationary signal into a classification
problem: the large majority of intraoperative time is "do nothing", and the model must learn
when (and how) to intervene.

### 2.3 `result_real` (ground truth)

`result_real` is the fine-grained action the clinician actually performed, mapped to the five
canonical classes above. Two simplifications were applied:

- **`vasopressor`** is kept as a *possible option* (a recommendation system should be able to
  propose it) but removed as a ground-truth class, because vasopressor management is a distinct
  problem with different pharmacology.
- **Ventilation actions** (FiO₂, PEEP, tidal volume, respiratory rate, volatile-agent changes)
  are removed from both options and ground truth, scoping the dataset to hypnotic/opioid
  titration.

After filtering, the dataset contains **84,813 windows** from **3,168 cases**.

## 3. Step 2 — Enrichment

Two enrichments were added on top of the extracted windows:

- **Preoperative laboratories** (`lab_*`): last preoperative value per (case, test) and its age,
  fetched from the VitalDB labs endpoint (34 tests).
- **Signal filling** (`vitals_json`): windows with missing vital signs were filled from the
  VitalDB track API (HR, MAP, SBP, DBP, SpO₂, EtCO₂), keeping the real staleness of each value.
  PPV/SVV were later **removed** because of heavy artifacts.

## 4. Acceptable actions — cluster analysis

The core modeling question: given a window, which set of actions is *acceptable*? Seven
candidate strategies were evaluated, each producing a top-2 `(result_1, result_aux)` with
confidence ratios:

| strategy | method |
|---|---|
| `knn` | k-NN, euclidean, K=50 (baseline) |
| `random_forest` | out-of-fold probabilities (3 folds) |
| `lightgbm` | out-of-fold probabilities (3 folds) |
| `logistic` | softmax logistic regression (3 folds) |
| `centroid` | softmax(−distance to class centroid) |
| `dwknn` | distance-weighted k-NN |
| `umap_knn` | UMAP (10 dims) + k-NN K=50 |

The neighborhood/pool for these models used **6 classes** (the 5 final classes plus
`vasopressor`), so the model can propose vasopressors without them being a target in the final
dataset.

## 5. External validation — three reviewers

The ground truth comes from the clinicians of the source hospital (Korea). To obtain
**external coherence** and avoid circular validation, three annotators **external to the Korean
hospital** reviewed a subset of **298 windows** and, for each, declared
the set of actions they considered valid (`valid_actions`).

Scoring of a strategy on a reviewed window:

- **+1.0** if its `top1` is in the reviewer's `valid_actions`,
- **+0.8** if its `top2` is in `valid_actions`,

summed over the three reviewers (max 3.0 per window).

## 6. Coherence analysis and strategy selection

Each strategy was scored along two axes:

1. **Internal coherence** — agreement with the real action (`result_real`):

| strategy | top1 = real | real ∈ top2 |
|---|---|---|
| **lightgbm** | **55.8%** | **80.4%** |
| logistic | 53.7% | 78.7% |
| random_forest | 53.5% | 78.2% |
| dwknn | 51.2% | 75.6% |
| knn | 50.9% | 75.3% |
| umap_knn | 46.4% | 71.2% |
| centroid | 38.6% | 64.2% |

2. **External coherence** — agreement with the three reviewers:

| strategy | % of max score |
|---|---|
| random_forest | 99.1% |
| **lightgbm** | **98.9%** |
| dwknn | 97.1% |
| knn | 97.0% |
| logistic | 96.2% |
| umap_knn | 93.1% |
| centroid | 85.9% |

**LightGBM was selected**: it is the best against the real action and statistically tied with
random forest against the reviewers. Its top-2 became `result_1` / `result_aux`.

## 7. Difficulty split (easy / medium / hard)

Difficulty is defined **per case** (windows of a case stay together). The confidence of a window
is `result_1.ratio + result_aux.ratio`; the case score is the mean over its windows. With
percentiles computed at case level (p25 = 0.7772, p75 = 0.8318):

- `easy` — mean ≥ p75 (high model confidence),
- `hard` — mean < p25 (low confidence),
- `medium` — otherwise.

This yields a clean 25 / 50 / 25 split: **792 easy, 1,584 medium, 792 hard**.

## 8. Final splits (dev / train / test)

### 8.1 `dev` — engineered edge cases

25 cases selected for having the **highest null fraction** (heaviest missing data), to stress-test
systems that handle nulls poorly. The dev set **deliberately keeps bad physiological values**
(impossible hemodynamics from VitalDB artifacts); they are **not removed**, only **reported**.
The inventory of bad-value cases (with the offending fields and the reason) is maintained in
`audit/bad_cases.csv`:

- `dev` contains **1** bad case (`case3807`),
- `train` contains **864** bad cases — the reasons are the offending fields themselves
  (`map_current`, `MAP_current`, `DBP_current` with negative/absurd blood pressure, plus
  `lab_cr` and `mac` outliers), as listed in `audit/bad_cases.csv`.

### 8.2 `train` — the bulk

All remaining cases (2,994 after the test filtering below), used for training.

### 8.3 `test` — balanced and maximum quality

- **Representative**: stratified by difficulty (25 / 50 / 25).
- **No impossible values**: any case containing a physiologically impossible value was **moved
  out of test into train**, guaranteeing that the evaluation set has the highest data quality.
  Final test set: **149 cases, 0 windows with impossible values**.

## 9. Portability (transferability)

Despite the curation above, the test set remains **portable**: a drift analysis (KS test + PSI)
between `train` and `test` found no meaningful distribution shift — the `result_real` class
distribution is nearly identical (total-variation distance 0.011) and no feature drifts except
`lab_k` (PSI 0.14) and `lab_plt` (PSI 0.11). Models trained on `train` therefore transfer
fairly to `test`.

## 10. Privacy

VitalDB is de-identified at source, but the patient fields still carry two direct identifiers
(`pt_caseid`, `pt_subjectid`). A k-anonymity evaluation at window level shows that including
vital signs makes ~75% of windows unique (k = 1). For any public release, the direct
identifiers must be removed and the quasi-identifiers (demographics, clinical context, vitals)
generalized or suppressed.

## 11. Reproducibility

The final dataset and its splits are deterministic: the split assignment is recorded in
`dataset/split_manifest.csv`, and every case belongs to exactly one split. The full data
dictionary is in `dataset/reports/data_dictionary.csv`.
