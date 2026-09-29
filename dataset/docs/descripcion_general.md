# AnesLLM — Dataset General Description

## What it is

AnesLLM is a clinical decision-support benchmark for **anesthesia**. Each record is a
*decision window* extracted from real surgical cases: everything observable to the
anesthesiologist **before** a decision, paired with (a) the action the clinician actually took
and (b) two consensus alternatives estimated from the actions of all clinicians in the cohort
(supervised LightGBM, case-grouped out-of-fold predictions).

The dataset is derived from [VitalDB](https://vitaldb.net), a public open dataset of
high-resolution intraoperative biosignals from **Seoul National University Hospital**.

## Purpose

Train and evaluate systems that recommend the next anesthetic adjustment (hypnotic or opioid),
mimicking the decision-making of an anesthesiologist.

## Key dimensions

| Metric | Value |
|---|---:|
| Total cases | 3,168 |
| Decision windows | 84,813 |
| Splits | `dev` / `train` / `test` |
| Action classes | 5 (+ `vasopressor` as option) |

## Splits

| Split | Purpose | Cases | Windows | Windows/case (mean) |
|---|---|---:|---:|---:|
| `train` | bulk training data | 2,994 | 80,933 | 27.03 |
| `test`  | balanced, maximum-quality evaluation | 149 | 3,457 | 23.20 |
| `dev`   | engineered edge cases (heavy missing data) | 25 | 423 | 16.92 |
| **Total** | | **3,168** | **84,813** | **26.77** |

## Record format

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

### `input` — everything observable *before* the decision

- patient demographics and preoperative status (`pt_*`),
- preoperative laboratory results (`lab_*`),
- vital-sign time series of the window (`vitals_json`: MAP, HR, BIS, SBP, DBP, SpO2, EtCO2),
- drug concentration time series and PK/PD features,
- history of previous actions and clinical events,
- monitoring flags, coverage counters and trend features.

### `output` — the three labels

| Label | Type | Description |
|---|---|---|
| `result_1` | object `{action, ratio}` | Primary consensus action + model probability |
| `result_aux` | object `{action, ratio}` | Alternative consensus action + model probability |
| `result_real` | string | Action the clinician actually took (*ground truth*, no ratio) |

## Action vocabulary (labels)

The labels use a reduced vocabulary: 5 canonical classes plus the `vasopressor` option.

| Class | Source drug | Meaning |
|---|---|---|
| `increase_hypnotic` | propofol (TIVA) | hypnotic rate up |
| `reduce_hypnotic` | propofol (TIVA) | hypnotic rate down |
| `increase_opioid` | remifentanil | opioid rate up |
| `reduce_opioid` | remifentanil | opioid rate down |
| `no_action` | — | no infusion-rate change at that moment |
| `vasopressor` *(option)* | vasopressor | auxiliary recommendation only |

`vasopressor` is added to the option set **by anesthetic criteria** — only where it is clinically
relevant — so a model may propose it, but it is **never a ground-truth class**: it never appears
in `result_real`. It acts as an **auxiliary** recommendation; in the released data it appears in
`result_aux` (1.0% of windows) and only occasionally as the primary `result_1` (0.5%).

## Difficulty

Each **case** is labelled `easy`, `medium` or `hard` according to the mean confidence of its
windows (`result_1.ratio + result_aux.ratio`): `easy` ≥ p75, `hard` < p25, `medium` otherwise.
See `reports/split_manifest.csv` for the per-case breakdown.

## Related documents

| Document | Content |
|---|---|
| `descripcion_general.md` | This document: what the dataset is, structure and format |
| `recuento_etiquetas.md` | Absolute counts of `result_1`, `result_aux` and `result_real` |
| `prevalencia_etiquetas.md` | Prevalence (%), ratio distribution and label agreements |
| `../reports/data_dictionary.csv` | Variable codebook (English descriptions) |

## Privacy note

VitalDB is de-identified at source, but two direct identifiers (`pt_caseid`, `pt_subjectid`)
remain in the patient fields and must be removed before any public release.
