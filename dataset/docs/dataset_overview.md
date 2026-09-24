# AnesLLM Decision Dataset — Overview

## What it is

AnesLLM is a clinical decision-support benchmark for **anesthesia**. Each record is a
*decision window* extracted from real surgical cases: all the information available to the
anesthesiologist **before** a decision, paired with (a) the action the clinician actually took
and (b) two consensus alternatives derived from clinician actions in similar cases
(unsupervised clustering).

The dataset is derived from [VitalDB](https://vitaldb.net), a public open dataset of
high-resolution intraoperative biosignals from **Seoul National University Hospital** (6,388
surgical cases).

## What it is for

The dataset is designed to train and evaluate systems that recommend the next anesthetic
adjustment (hypnotic or opioid), mimicking the decision-making of an anesthesiologist. It is
split into three complementary sets:

| Split | Purpose | Cases | Windows |
|---|---|---|---|
| `train` | bulk training data | 2,994 | 80,933 |
| `test`  | balanced, maximum-quality evaluation | 149 | 3,457 |
| `dev`   | edge cases (heavy missing data) for engineering | 25 | 423 |
| **Total** | | **3,168** | **84,813** |

## What a record looks like

One JSON line per decision window, in per-case files `case<caseid>.jsonl`:

```json
{
  "window_id": "case14_w127",
  "case_id": "14",
  "input": { "...280 pre-decision fields..." },
  "output": {
    "result_1":    { "action": "reduce_hypnotic", "ratio": 0.48 },
    "result_aux":  { "action": "reduce_opioid",   "ratio": 0.45 },
    "result_real": "reduce_hypnotic"
  }
}
```

- **`input`** — everything observable *before* the decision:
  - patient demographics and preoperative status (`pt_*`),
  - preoperative laboratory results (`lab_*`),
  - vital-sign time series of the window (`vitals_json`: MAP, HR, BIS, SBP, DBP, SpO2, EtCO2),
  - drug concentration time series and PK/PD features,
  - history of previous actions and clinical events,
  - monitoring flags, coverage counters and trend features.
- **`output`** — the three results:
  - `result_1` — primary consensus action + supporting ratio,
  - `result_aux` — alternative consensus action + supporting ratio,
  - `result_real` — the action the clinician actually took (ground truth, no ratio).

## Action vocabulary

Five ground-truth classes with direction:

- `increase_hypnotic`
- `reduce_hypnotic`
- `increase_opioid`
- `reduce_opioid`
- `no_action`

`vasopressor` is kept as a *possible option* (a model may propose it) but is **not** a
ground-truth class. Ventilation actions (`increase_fio2`, `reduce_peep`, …) were removed from
both options and ground truth.

## Difficulty

Each **case** is labelled `easy`, `medium` or `hard` according to the mean confidence of its
windows (`result_1.ratio + result_aux.ratio`): `easy` ≥ p75, `hard` < p25, `medium` otherwise.

| Difficulty | Cases |
|---|---|
| easy | 792 |
| medium | 1,584 |
| hard | 792 |

## Files

```
dataset/
├── dev/  train/  test/        # case<caseid>.jsonl, one line per window
├── split_manifest.csv         # case_id, difficulty, split, n_windows, null_score
└── reports/                   # audits, data dictionary, strategy tables
```

## Key design choices (summary)

- **Window**: 10 minutes of vitals, 20 minutes of action history; the decision is taken at the
  end of the window.
- **Ground truth** (`result_real`): the drug-rate change the clinician actually performed,
  mapped to the 5 canonical classes (`no_action` when nothing changed).
- **Consensus alternatives** (`result_1` / `result_aux`): the two most frequent actions taken
  by clinicians in similar cases, found by unsupervised clustering of the windows; `ratio` is
  the proportion of similar cases supporting each action. No LLM is involved in deriving them.
- **Anonymization note**: VitalDB is de-identified at source, but two direct identifiers
  (`pt_caseid`, `pt_subjectid`) are still present in the patient fields and should be removed
  before any public release.

See `docs/dataset_design.md` for the full pipeline and `docs/audit_report.md` for the
verification results.
