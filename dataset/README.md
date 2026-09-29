# AnesLLM — Anesthesia Decision Dataset

AnesLLM is a clinical decision-support benchmark for **anesthesia**. It contains intraoperative
*decision windows* derived from [VitalDB](https://vitaldb.net) (Seoul National University
Hospital): everything observable before a decision, plus the action the clinician actually took
and two consensus alternatives estimated from the actions of all clinicians in the cohort
(supervised LightGBM, case-grouped out-of-fold predictions).

- **3,168 cases** · **84,813 decision windows**
- Splits: `dev` (25) · `train` (2,994) · `test` (149)
- 5 action classes: `increase_hypnotic`, `reduce_hypnotic`, `increase_opioid`,
  `reduce_opioid`, `no_action` (+ `vasopressor` as an option, never ground truth)

## Repository layout

```
dataset/
├── data/{dev,train,test}/      # case<caseid>.jsonl — one JSON per window
├── docs/                       # descriptive documentation (Markdown)
├── reports/                    # split_manifest.csv, audits, data dictionary, sha256
└── scripts/                    # command-line utilities (see below)
```

## Documentation

| Document | Content |
|---|---|
| [docs/descripcion_general.md](docs/descripcion_general.md) | General description, structure, format, action vocabulary (start here) |
| [docs/recuento_etiquetas.md](docs/recuento_etiquetas.md) | Absolute counts of `result_1` / `result_aux` / `result_real` |
| [docs/prevalencia_etiquetas.md](docs/prevalencia_etiquetas.md) | Label prevalence, ratio distribution, agreement, confusion matrices |
| [docs/dataset_overview.md](docs/dataset_overview.md) | What the dataset is (overview) |
| [docs/dataset_design.md](docs/dataset_design.md) | Full pipeline: extraction, clusters, external validation, difficulty, splits |
| [docs/audit_report.md](docs/audit_report.md) | Verification results |
| [docs/evaluation_guide.md](docs/evaluation_guide.md) | How to load the data and evaluate a model |
| [reports/data_dictionary.csv](reports/data_dictionary.csv) | Variable codebook (English descriptions) |

## Scripts

Command-line utilities in `dataset/scripts/` (all read the JSONL files directly):

| Script | What it does |
|---|---|
| `to_prompt.py` | Converts a window into a working LLM prompt (`prompt.txt` template) |
| `quick_stats.py` | Fast console summary: cases, windows, label distribution |
| `filter.py` | Filter windows by label / difficulty / sex / monitoring / case → new JSONL |
| `to_csv.py` | Flatten windows into a CSV table (one row per window) |
| `sample.py` | Random / per-class / stratified sampling of windows or cases |
| `check_integrity.py` | Validate vocabulary, ratios, window-id uniqueness and manifest consistency |
| `dataset_sha256.py` | Deterministic SHA-256 fingerprint of the dataset |

Examples:

```powershell
python scripts/to_prompt.py data/test/case1001.jsonl --line 0
python scripts/quick_stats.py test
python scripts/filter.py test --real no_action --limit 100 -o subset.jsonl
python scripts/to_csv.py test --limit 100 -o test_sample.csv
python scripts/sample.py test 20 --per-class -o sample.jsonl
python scripts/check_integrity.py
python scripts/dataset_sha256.py --verify
```

## Dataset integrity (SHA-256)

The dataset ships with a deterministic fingerprint: **42 windows** selected with seed **42**
(sorted window IDs sampled via `random.Random(42)`), serialized canonically (sorted keys,
compact JSON) and hashed with SHA-256.

- **SHA-256**: `ade21848e44b6e99b7abe34cc4355d15392164bfeee3ebbfcb44fa01644cc082`
- **Manifest**: `reports/dataset_sha256.json` (seed, selected window IDs, totals, hash)

Verify after download:

```powershell
python scripts/dataset_sha256.py --verify
```

> Note: the fingerprint covers the 42 sampled windows, not every one of the 84,813. To hash the
> entire dataset instead, run `python scripts/dataset_sha256.py --all`.

## Quick facts

- **Record format**: one JSON object per line, `{ window_id, case_id, input, output }`.
- **`input`**: 280 pre-decision fields (patient, labs, vitals, drug history, events, trends).
- **`output`**: `result_1` (primary consensus action + model probability), `result_aux`
  (alternative consensus action + ratio), `result_real` (action the clinician actually took).
- **Action vocabulary**: `increase_hypnotic` / `reduce_hypnotic` (propofol), `increase_opioid` /
  `reduce_opioid` (remifentanil), `no_action`; `vasopressor` is kept as an option only.
- **Difficulty**: each case is `easy` / `medium` / `hard` (see `split_manifest.csv`).
- **Privacy note**: direct identifiers (`pt_caseid`, `pt_subjectid`) are removed in the released
  dataset.

## Loading example

```python
import json

with open("data/test/case1001.jsonl", encoding="utf-8") as f:
    for line in f:
        record = json.loads(line)
        x = record["input"]            # 280 features
        y = record["output"]           # result_1 / result_aux / result_real
        print(record["window_id"], y["result_real"])
```
