# -*- coding: utf-8 -*-
"""
describe_dataset.py
-------------------
Scans dataset/data/{dev,train,test}/*.jsonl and generates:
  - descriptive CSVs in dataset/reports/
  - Markdown documents in dataset/docs/ (English)

Generated documents:
  - descripcion_general.md  : what the dataset is, structure, format, vocabulary
  - recuento_etiquetas.md   : absolute counts of result_1 / result_aux / result_real
  - prevalencia_etiquetas.md: prevalence (%), ratio distribution and label agreements
"""

import csv
import glob
import json
import os
import statistics
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "dataset", "data")
REPORTS_DIR = os.path.join(ROOT, "dataset", "reports")
DOCS_DIR = os.path.join(ROOT, "dataset", "docs")

SPLITS = ["dev", "train", "test"]
ACTION_ORDER = [
    "increase_hypnotic",
    "reduce_hypnotic",
    "increase_opioid",
    "reduce_opioid",
    "no_action",
]
# Optional action that may appear in result_1 / result_aux but never in result_real
EXTRA_ACTIONS = ["vasopressor"]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_split(split):
    """Returns (list of records, windows per case) for one split."""
    pattern = os.path.join(DATA_DIR, split, "case*.jsonl")
    records = []
    windows_per_case = []
    for path in sorted(glob.glob(pattern)):
        n = 0
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
                n += 1
        if n:
            windows_per_case.append(n)
    return records, windows_per_case


def get_action(value):
    """result_real is a string; result_1 / result_aux are dicts {action, ratio}."""
    if isinstance(value, dict):
        return value.get("action")
    return value


def get_ratio(value):
    if isinstance(value, dict):
        r = value.get("ratio")
        return r if isinstance(r, (int, float)) else None
    return None


# ---------------------------------------------------------------------------
# Computation
# ---------------------------------------------------------------------------

def percentile(sorted_vals, q):
    """Linear-interpolation percentile (q in [0, 100])."""
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = (len(sorted_vals) - 1) * (q / 100.0)
    lo = int(pos)
    hi = lo + 1
    if hi >= len(sorted_vals):
        return sorted_vals[-1]
    frac = pos - lo
    return sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo])


def summarize(records, windows_per_case):
    """Aggregates counters, ratios and agreements for one split."""
    n_windows = len(records)
    n_cases = len(windows_per_case)

    counts = {label: Counter() for label in ["result_1", "result_aux", "result_real"]}
    ratios = {label: [] for label in ["result_1", "result_aux"]}

    top1 = 0
    top2 = 0
    r1_eq_aux = 0
    real_in_r1 = 0
    real_in_aux = 0
    conf_r1 = Counter()   # (real, result_1)
    conf_aux = Counter()  # (real, result_aux)

    for rec in records:
        out = rec.get("output") or {}
        real = get_action(out.get("result_real"))
        r1 = get_action(out.get("result_1"))
        aux = get_action(out.get("result_aux"))

        counts["result_real"][real] += 1
        counts["result_1"][r1] += 1
        counts["result_aux"][aux] += 1

        r1_ratio = get_ratio(out.get("result_1"))
        aux_ratio = get_ratio(out.get("result_aux"))
        if r1_ratio is not None:
            ratios["result_1"].append(r1_ratio)
        if aux_ratio is not None:
            ratios["result_aux"].append(aux_ratio)

        if r1 == real:
            top1 += 1
        if real in (r1, aux):
            top2 += 1
        if r1 == aux:
            r1_eq_aux += 1
        if real == r1:
            real_in_r1 += 1
        if real == aux:
            real_in_aux += 1

        conf_r1[(real, r1)] += 1
        conf_aux[(real, aux)] += 1

    if windows_per_case:
        wpc_mean = statistics.mean(windows_per_case)
        wpc_median = statistics.median(windows_per_case)
        wpc_min = min(windows_per_case)
        wpc_max = max(windows_per_case)
    else:
        wpc_mean = wpc_median = wpc_min = wpc_max = None

    ratio_stats = {}
    for label in ["result_1", "result_aux"]:
        vals = sorted(ratios[label])
        if vals:
            ratio_stats[label] = {
                "n": len(vals),
                "mean": statistics.mean(vals),
                "std": statistics.pstdev(vals) if len(vals) > 1 else 0.0,
                "min": vals[0],
                "p25": percentile(vals, 25),
                "p50": percentile(vals, 50),
                "p75": percentile(vals, 75),
                "max": vals[-1],
            }
        else:
            ratio_stats[label] = None

    return {
        "n_cases": n_cases,
        "n_windows": n_windows,
        "counts": counts,
        "ratios": ratios,
        "ratio_stats": ratio_stats,
        "windows_per_case": {
            "mean": wpc_mean,
            "median": wpc_median,
            "min": wpc_min,
            "max": wpc_max,
        },
        "agreement": {
            "top1_accuracy": top1 / n_windows if n_windows else None,
            "top2_recall": top2 / n_windows if n_windows else None,
            "result1_equals_aux": r1_eq_aux / n_windows if n_windows else None,
            "real_in_result1": real_in_r1 / n_windows if n_windows else None,
            "real_in_result_aux": real_in_aux / n_windows if n_windows else None,
        },
        "conf_r1": conf_r1,
        "conf_aux": conf_aux,
    }


def build_all():
    per_split = {}
    all_records = []
    all_wpc = []
    for split in SPLITS:
        records, wpc = load_split(split)
        per_split[split] = summarize(records, wpc)
        all_records.extend(records)
        all_wpc.extend(wpc)
    per_split["overall"] = summarize(all_records, all_wpc)
    return per_split


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

def write_csvs(data):
    os.makedirs(REPORTS_DIR, exist_ok=True)

    # 1) absolute counts
    with open(os.path.join(REPORTS_DIR, "result_label_counts.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["split", "label", "action", "count"])
        for split in ["dev", "train", "test", "overall"]:
            for label in ["result_1", "result_aux", "result_real"]:
                counter = data[split]["counts"][label]
                for action in ACTION_ORDER + EXTRA_ACTIONS:
                    w.writerow([split, label, action, counter.get(action, 0)])
                known = set(ACTION_ORDER + EXTRA_ACTIONS)
                others = sum(c for a, c in counter.items() if a not in known)
                if others:
                    w.writerow([split, label, "(other)", others])

    # 2) prevalences
    with open(os.path.join(REPORTS_DIR, "result_label_prevalence.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["split", "label", "action", "count", "prevalence"])
        for split in ["dev", "train", "test", "overall"]:
            n = data[split]["n_windows"]
            for label in ["result_1", "result_aux", "result_real"]:
                counter = data[split]["counts"][label]
                for action in ACTION_ORDER + EXTRA_ACTIONS:
                    c = counter.get(action, 0)
                    prev = c / n if n else None
                    w.writerow([split, label, action, c, f"{prev:.4f}" if prev is not None else ""])

    # 3) agreements
    with open(os.path.join(REPORTS_DIR, "result_label_agreement.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["split", "n_windows", "top1_accuracy", "top2_recall",
                    "result1_equals_aux", "real_in_result1", "real_in_result_aux"])
        for split in ["dev", "train", "test", "overall"]:
            d = data[split]
            a = d["agreement"]
            w.writerow([split, d["n_windows"],
                        f"{a['top1_accuracy']:.4f}" if a["top1_accuracy"] is not None else "",
                        f"{a['top2_recall']:.4f}" if a["top2_recall"] is not None else "",
                        f"{a['result1_equals_aux']:.4f}" if a["result1_equals_aux"] is not None else "",
                        f"{a['real_in_result1']:.4f}" if a["real_in_result1"] is not None else "",
                        f"{a['real_in_result_aux']:.4f}" if a["real_in_result_aux"] is not None else ""])

    # 4) ratio distribution
    with open(os.path.join(REPORTS_DIR, "result_ratio_distribution.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["split", "label", "n", "mean", "std", "min", "p25", "p50", "p75", "max"])
        for split in ["dev", "train", "test", "overall"]:
            for label in ["result_1", "result_aux"]:
                st = data[split]["ratio_stats"][label]
                if st:
                    w.writerow([split, label, st["n"],
                                f"{st['mean']:.4f}", f"{st['std']:.4f}",
                                f"{st['min']:.4f}", f"{st['p25']:.4f}", f"{st['p50']:.4f}",
                                f"{st['p75']:.4f}", f"{st['max']:.4f}"])

    # 5) confusion matrices
    for label, conf_key in [("result_1", "conf_r1"), ("result_aux", "conf_aux")]:
        path = os.path.join(REPORTS_DIR, f"confusion_{label}_vs_real.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["split", "real", label, "count"])
            for split in ["dev", "train", "test", "overall"]:
                conf = data[split][conf_key]
                for real in ACTION_ORDER:
                    for pred in ACTION_ORDER:
                        w.writerow([split, real, pred, conf.get((real, pred), 0)])

    # 6) split summary
    with open(os.path.join(REPORTS_DIR, "split_summary.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["split", "n_cases", "n_windows",
                    "windows_per_case_mean", "windows_per_case_median",
                    "windows_per_case_min", "windows_per_case_max"])
        for split in ["dev", "train", "test", "overall"]:
            d = data[split]
            wpc = d["windows_per_case"]
            w.writerow([split, d["n_cases"], d["n_windows"],
                        f"{wpc['mean']:.2f}" if wpc["mean"] is not None else "",
                        f"{wpc['median']:.2f}" if wpc["median"] is not None else "",
                        wpc["min"] if wpc["min"] is not None else "",
                        wpc["max"] if wpc["max"] is not None else ""])


# ---------------------------------------------------------------------------
# Markdown generation
# ---------------------------------------------------------------------------

def _pct(count, total):
    if not total:
        return "–"
    return f"{100.0 * count / total:.1f}%"


def _counts_table(data, split, label):
    n = data[split]["n_windows"]
    c = data[split]["counts"][label]
    lines = ["| Action | Count | Prevalence |",
             "|---|---:|---:|"]
    for action in ACTION_ORDER:
        cnt = c.get(action, 0)
        lines.append(f"| `{action}` | {cnt:,} | {_pct(cnt, n)} |")
    # vasopressor (allowed option, not ground truth)
    vp = c.get("vasopressor", 0)
    if vp:
        lines.append(f"| `vasopressor` *(option, not GT)* | {vp:,} | {_pct(vp, n)} |")
    # any residual value
    known = set(ACTION_ORDER + EXTRA_ACTIONS)
    others = sum(cnt for a, cnt in c.items() if a not in known)
    if others:
        lines.append(f"| *(others)* | {others:,} | {_pct(others, n)} |")
    lines.append(f"| **Total** | **{n:,}** | **100%** |")
    return "\n".join(lines)


def _confusion_md(data, split, conf_key):
    header = "| real \\ " + conf_key.replace("conf_", "") + " | " + " | ".join(f"`{a}`" for a in ACTION_ORDER) + " |"
    sep = "|---|" + "---:|" * len(ACTION_ORDER)
    rows = [header, sep]
    for real in ACTION_ORDER:
        cells = [str(data[split][conf_key].get((real, pred), 0)) for pred in ACTION_ORDER]
        rows.append(f"| `{real}` | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def gen_descripcion_general(data):
    total = data["overall"]
    tr = data["train"]; te = data["test"]; dv = data["dev"]
    vp1 = 100.0 * total['counts']['result_1'].get('vasopressor', 0) / total['n_windows']
    vp2 = 100.0 * total['counts']['result_aux'].get('vasopressor', 0) / total['n_windows']
    content = f"""# AnesLLM — Dataset General Description

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
| Total cases | {total['n_cases']:,} |
| Decision windows | {total['n_windows']:,} |
| Splits | `dev` / `train` / `test` |
| Action classes | 5 (+ `vasopressor` as option) |

## Splits

| Split | Purpose | Cases | Windows | Windows/case (mean) |
|---|---|---:|---:|---:|
| `train` | bulk training data | {tr['n_cases']:,} | {tr['n_windows']:,} | {tr['windows_per_case']['mean']:.2f} |
| `test`  | balanced, maximum-quality evaluation | {te['n_cases']:,} | {te['n_windows']:,} | {te['windows_per_case']['mean']:.2f} |
| `dev`   | engineered edge cases (heavy missing data) | {dv['n_cases']:,} | {dv['n_windows']:,} | {dv['windows_per_case']['mean']:.2f} |
| **Total** | | **{total['n_cases']:,}** | **{total['n_windows']:,}** | **{total['windows_per_case']['mean']:.2f}** |

## Record format

One JSON line per decision window, in per-case files `case<caseid>.jsonl`:

```json
{{
  "window_id": "case14_w127",
  "case_id": "14",
  "input": {{ "...280 pre-decision fields..." }},
  "output": {{
    "result_1":    {{ "action": "reduce_hypnotic", "ratio": 0.48 }},
    "result_aux":  {{ "action": "reduce_opioid",   "ratio": 0.45 }},
    "result_real": "reduce_hypnotic"
  }}
}}
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
| `result_1` | object `{{action, ratio}}` | Primary consensus action + model probability |
| `result_aux` | object `{{action, ratio}}` | Alternative consensus action + model probability |
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
`result_aux` ({vp2:.1f}% of windows) and only occasionally as the primary `result_1` ({vp1:.1f}%).

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
"""
    return content


def gen_recuento_etiquetas(data):
    content = """# AnesLLM — Label Counts

Absolute **counts** of each action for the three `output` labels: `result_1` (primary
consensus), `result_aux` (alternative consensus) and `result_real` (ground truth). Totals match
the number of windows in each split.

## Global (all splits)

"""
    for label, name in [("result_1", "`result_1` — primary consensus"),
                        ("result_aux", "`result_aux` — alternative consensus"),
                        ("result_real", "`result_real` — ground truth")]:
        content += f"### {name}\n\n"
        content += _counts_table(data, "overall", label) + "\n\n"

    for split in ["train", "test", "dev"]:
        content += f"## Split `{split}`\n\n"
        for label, name in [("result_1", "`result_1`"),
                            ("result_aux", "`result_aux`"),
                            ("result_real", "`result_real`")]:
            content += f"### {name}\n\n"
            content += _counts_table(data, split, label) + "\n\n"

    content += """## Associated CSV files

- `reports/result_label_counts.csv` — absolute counts (long format)
- `reports/result_label_prevalence.csv` — counts and prevalences (long format)
"""
    return content


def gen_prevalencia_etiquetas(data):
    content = """# AnesLLM — Label Prevalence

Prevalence (percentage of windows) of each action for the three labels, the distribution of the
consensus `ratio`, and agreement measures between labels.

## Global prevalence (%)

"""
    header = "| Action | `result_1` | `result_aux` | `result_real` |"
    sep = "|---|---:|---:|---:|"

    def table_lines(d):
        n = d["n_windows"]
        out = []
        for action in ACTION_ORDER:
            cells = [f"{100.0 * d['counts'][l].get(action, 0) / n:.1f}%" for l in ["result_1", "result_aux", "result_real"]]
            out.append(f"| `{action}` | " + " | ".join(cells) + " |")
        vp1 = f"{100.0 * d['counts']['result_1'].get('vasopressor', 0) / n:.1f}%"
        vp2 = f"{100.0 * d['counts']['result_aux'].get('vasopressor', 0) / n:.1f}%"
        out.append(f"| `vasopressor` *(option, not GT)* | {vp1} | {vp2} | – |")
        out.append(f"| **Total windows** | **{n:,}** | **{n:,}** | **{n:,}** |")
        return out

    content += "\n".join([header, sep] + table_lines(data["overall"])) + "\n\n"

    for split in ["train", "test", "dev"]:
        content += f"## Prevalence by split — `{split}` (%)\n\n"
        content += "\n".join([header, sep] + table_lines(data[split])) + "\n\n"

    # ratios
    content += "## Consensus `ratio` distribution\n\n"
    content += ("The `ratio` field of `result_1` and `result_aux` is the probability assigned by "
                "the consensus model to each action.\n\n")
    for split in ["overall", "train", "test", "dev"]:
        content += f"### `{split}`\n\n"
        content += "| Label | n | Mean | Std | Min | p25 | p50 | p75 | Max |\n"
        content += "|---|---:|---:|---:|---:|---:|---:|---:|---:|\n"
        for label in ["result_1", "result_aux"]:
            st = data[split]["ratio_stats"][label]
            if st:
                content += (f"| `{label}` | {st['n']:,} | {st['mean']:.3f} | {st['std']:.3f} | "
                            f"{st['min']:.3f} | {st['p25']:.3f} | {st['p50']:.3f} | "
                            f"{st['p75']:.3f} | {st['max']:.3f} |\n")
        content += "\n"

    # agreements
    content += "## Agreement between labels\n\n"
    content += ("Interpretation: `top1_accuracy` = how often `result_1` matches `result_real`; "
                "`top2_recall` = how often `result_real` is among `result_1` and `result_aux` "
                "(plausible coverage).\n\n")
    content += "| Split | Windows | top1_accuracy | top2_recall | result_1 == result_aux |\n"
    content += "|---|---:|---:|---:|---:|\n"
    for split in ["overall", "train", "test", "dev"]:
        a = data[split]["agreement"]
        content += (f"| `{split}` | {data[split]['n_windows']:,} | "
                    f"{100.0 * a['top1_accuracy']:.1f}% | {100.0 * a['top2_recall']:.1f}% | "
                    f"{100.0 * a['result1_equals_aux']:.1f}% |\n")
    content += "\n"

    # confusion matrices (global)
    content += "## Global confusion matrix — `result_1` vs `result_real`\n\n"
    content += "Rows = `result_real` (ground truth), columns = `result_1`.\n\n"
    content += _confusion_md(data, "overall", "conf_r1") + "\n\n"

    content += "## Global confusion matrix — `result_aux` vs `result_real`\n\n"
    content += "Rows = `result_real` (ground truth), columns = `result_aux`.\n\n"
    content += _confusion_md(data, "overall", "conf_aux") + "\n\n"

    content += """## Associated CSV files

- `reports/result_label_prevalence.csv` — prevalences (long format)
- `reports/result_ratio_distribution.csv` — ratio distribution
- `reports/result_label_agreement.csv` — agreement measures
- `reports/confusion_result_1_vs_real.csv` and `reports/confusion_result_aux_vs_real.csv` — confusion matrices
"""
    return content


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    data = build_all()
    write_csvs(data)
    os.makedirs(DOCS_DIR, exist_ok=True)

    docs = {
        "descripcion_general.md": gen_descripcion_general(data),
        "recuento_etiquetas.md": gen_recuento_etiquetas(data),
        "prevalencia_etiquetas.md": gen_prevalencia_etiquetas(data),
    }
    for name, content in docs.items():
        with open(os.path.join(DOCS_DIR, name), "w", encoding="utf-8") as f:
            f.write(content)
        print(f"generated: dataset/docs/{name}")

    print("done")


if __name__ == "__main__":
    main()
