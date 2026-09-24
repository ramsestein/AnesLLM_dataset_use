# AnesLLM — Anesthesia Decision Dataset

AnesLLM is a clinical decision-support benchmark for **anesthesia**. It contains intraoperative
*decision windows* derived from [VitalDB](https://vitaldb.net) (Seoul National University
Hospital): everything observable before a decision, plus the action the clinician actually took
and two consensus alternatives derived from clinician actions in similar cases
(unsupervised clustering).

- **3,168 cases** · **84,813 decision windows**
- Splits: `dev` (25) · `train` (2,994) · `test` (149)
- 5 action classes: `increase_hypnotic`, `reduce_hypnotic`, `increase_opioid`,
  `reduce_opioid`, `no_action`

## Repository layout

```
dataset/
├── dev/  train/  test/        # case<caseid>.jsonl — one JSON per window (line-delimited)
├── split_manifest.csv         # case_id, difficulty, split, n_windows, null_score
└── reports/                   # audits, data dictionary, strategy tables

docs/
├── dataset_overview.md        # what the dataset is (start here)
├── dataset_design.md          # how it was designed and built
├── audit_report.md            # verification results
└── evaluation_guide.md        # how to load and evaluate

audit/                         # scripts that regenerate the audits
```

## Documentation

| Document | Content |
|---|---|
| [docs/dataset_overview.md](docs/dataset_overview.md) | General description, structure, vocabulary, splits |
| [docs/dataset_design.md](docs/dataset_design.md) | Full pipeline: extraction, clusters, external validation, difficulty, splits |
| [docs/audit_report.md](docs/audit_report.md) | Descriptive report of the audits performed |
| [docs/evaluation_guide.md](docs/evaluation_guide.md) | How to load the data and evaluate a model |
| [dataset/reports/data_dictionary.csv](dataset/reports/data_dictionary.csv) | Variable codebook (292 variables, English descriptions) |

## Quick facts

- **Record format**: one JSON object per line, `{ window_id, case_id, input, output }`.
- **`input`**: 280 pre-decision fields (patient, labs, vitals, drug history, events, trends).
- **`output`**: `result_1` (primary consensus action + supporting ratio), `result_aux`
  (alternative consensus action + ratio), `result_real` (action the clinician actually took).
- **Difficulty**: each case is `easy` / `medium` / `hard` (see `split_manifest.csv`).
- **Privacy note**: two direct identifiers (`pt_caseid`, `pt_subjectid`) remain in the patient
  fields; remove them before any public release.

## Loading example

```python
import json

with open("dataset/test/case14.jsonl", encoding="utf-8") as f:
    for line in f:
        record = json.loads(line)
        x = record["input"]            # 280 features
        y = record["output"]           # result_1 / result_aux / result_real
        print(record["window_id"], y["result_real"])
```
