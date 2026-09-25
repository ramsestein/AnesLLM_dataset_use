# AnesLLM — Evaluation Guide

This guide explains how to load the dataset and evaluate a model against it.

## 1. Loading the data

The data lives in `dataset/data/{dev,train,test}/case<caseid>.jsonl`: one JSON object per line, one
line per decision window, all windows of a case in the same file.

```python
import json
from pathlib import Path

def load(split):
    for f in sorted((Path("dataset/data") / split).glob("case*.jsonl")):
        for line in open(f, encoding="utf-8"):
            yield json.loads(line)

for rec in load("test"):
    x = rec["input"]      # dict with 280 pre-decision features
    out = rec["output"]   # dict with result_1 / result_aux / result_real
```

## 2. Record contract

```json
{
  "window_id": "case14_w127",
  "case_id": "14",
  "input": { "...280 fields, everything observable BEFORE the decision..." },
  "output": {
    "result_1":    { "action": "reduce_hypnotic", "ratio": 0.48 },
    "result_aux":  { "action": "reduce_opioid",   "ratio": 0.45 },
    "result_real": "reduce_hypnotic"
  }
}
```

- **`input`** is the model input. Nulls are encoded as JSON `null`. The nested `*_json` fields
  are JSON objects (e.g. `vitals_json`, `staleness_json`, `actions_history_json`).
- **`output.result_real`** is the ground-truth action (no ratio) — the action the clinician
  actually performed.
- **`output.result_1`** and **`output.result_aux`** are the primary and alternative consensus
  actions: top-2 of a LightGBM model trained to predict the clinician's action (case-grouped
  out-of-fold predictions); `ratio` is the model probability.

## 3. Action vocabulary

Ground truth (`result_real`) is always one of:

- `increase_hypnotic`, `reduce_hypnotic`, `increase_opioid`, `reduce_opioid`, `no_action`

The consensus alternatives (`result_1`, `result_aux`) may additionally be `vasopressor` (a valid
*option*, but never a ground-truth label). Ventilation actions never appear.

## 4. Metrics

Two standard metrics capture how well a model reproduces the clinician:

- **top-1 accuracy** — the model's single best action equals `result_real`:
  `acc = mean(argmax(model(x)) == result_real)`.
- **top-2 recall** — `result_real` is among the model's two best actions.

Reference numbers — agreement between the generated alternatives and the real action, on the
full set:

| metric | value |
|---|---|
| top-1 accuracy | 55.8% |
| top-2 recall | 80.4% |

Because the true action is not always unique (several actions can be acceptable), the dataset
also provides the alternative action and supports external-validity evaluation (see
`docs/dataset_design.md`, §5–6).

## 5. Difficulty

Each case has a difficulty label in `dataset/reports/split_manifest.csv`
(`case_id, difficulty, split, n_windows, null_score`):

- `easy` — high consensus confidence (≥ p75 of the per-case confidence),
- `hard` — low consensus confidence (< p25),
- `medium` — otherwise.

Use these to report performance by difficulty (a model should do better on `easy` than on
`hard`).

## 6. Splits

- **`train`** — train your model here.
- **`test`** — balanced (stratified by difficulty) and curated to have **no physiologically
  impossible values**; the reference for final evaluation.
- **`dev`** — 25 edge cases with heavy missing data and deliberately retained bad values; use it
  to harden your data-loading and null handling, not for performance reporting.

## 7. Practical notes

- **Nulls**: coverage varies a lot per variable (see `dataset/reports/coverage_by_variable.csv`).
  The `dev` split is the stress test for null handling.
- **Vitals**: current values are also available as top-level `*_current` fields; the raw
  time series are in `input.vitals_json` (signals: MAP, HR, BIS, SBP, DBP, SpO2, EtCO2).
- **No leakage**: `input` contains no post-decision information (audited — see
  `docs/audit_report.md`).
- **Identifiers**: drop `pt_caseid` and `pt_subjectid` before training or release.
