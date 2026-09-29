# -*- coding: utf-8 -*-
"""Shared helpers for the dataset/scripts command-line utilities."""

import csv
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))   # dataset/scripts
DATASET_DIR = os.path.dirname(HERE)                  # dataset
ROOT = os.path.dirname(DATASET_DIR)                  # workspace root
DATA_DIR = os.path.join(DATASET_DIR, "data")
REPORTS_DIR = os.path.join(DATASET_DIR, "reports")
MANIFEST_PATH = os.path.join(REPORTS_DIR, "split_manifest.csv")

SPLITS = ["dev", "train", "test"]
ACTIONS = ["increase_hypnotic", "reduce_hypnotic", "increase_opioid",
           "reduce_opioid", "no_action"]
EXTRA_ACTIONS = ["vasopressor"]
ALL_ACTIONS = ACTIONS + EXTRA_ACTIONS

KEY_LABS = ["hb", "hct", "plt", "wbc", "na", "k", "gluc", "cr", "lac", "ph", "hco3", "be"]
MONITORING = {"ART": "arterial line", "NIBP": "non-invasive blood pressure", "NONE": "none"}
LAB_UNITS = {"hb": "g/dL", "hct": "%", "plt": "K/uL", "wbc": "K/uL",
             "na": "mEq/L", "k": "mEq/L", "gluc": "mg/dL", "cr": "mg/dL",
             "lac": "mmol/L", "ph": "", "hco3": "mEq/L", "be": "mEq/L"}


def load_jsonl(path):
    """Reads a JSONL file into a list of records."""
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def iter_split(split):
    """Yields every record of a split (dev / train / test)."""
    for path in sorted(glob.glob(os.path.join(DATA_DIR, split, "case*.jsonl"))):
        yield from load_jsonl(path)


def case_files(split):
    """Returns the sorted list of case*.jsonl paths of a split."""
    return sorted(glob.glob(os.path.join(DATA_DIR, split, "case*.jsonl")))


def get_input(rec):
    """Returns the input dict, tolerating a bare input (no `input` key)."""
    return rec["input"] if isinstance(rec, dict) and "input" in rec else rec


def get_output(rec):
    return rec.get("output") if isinstance(rec, dict) else None


def get_action(value):
    """result_real is a string; result_1 / result_aux are dicts {action, ratio}."""
    return value.get("action") if isinstance(value, dict) else value


def get_ratio(value):
    if isinstance(value, dict):
        r = value.get("ratio")
        return r if isinstance(r, (int, float)) else None
    return None


def load_manifest():
    """Returns {case_id: {difficulty, split, n_windows, null_score}}."""
    manifest = {}
    with open(MANIFEST_PATH, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            manifest[row["case_id"]] = {
                "difficulty": row.get("difficulty"),
                "split": row.get("split"),
                "n_windows": int(row["n_windows"]) if row.get("n_windows") else None,
                "null_score": float(row["null_score"]) if row.get("null_score") else None,
            }
    return manifest


def fmt(v):
    """Formats a value for prose: None -> None, floats trimmed to 2 decimals."""
    if v is None:
        return None
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        v = round(v, 2)
    return str(v)


def render_case(inp):
    """Renders one decision window into clinical prose (no identifiers)."""
    lines = []
    sex = {"M": "male", "F": "female"}.get(inp.get("pt_sex"), inp.get("pt_sex"))

    age = fmt(inp.get("pt_age"))
    head = f"{age}-year-old {sex}" if age else f"{sex} patient"
    attrs = []
    for f, u in [("pt_weight", "kg"), ("pt_height", "cm")]:
        v = fmt(inp.get(f))
        if v is not None:
            attrs.append(f"{v} {u}")
    if fmt(inp.get("pt_bmi")) is not None:
        attrs.append(f"BMI {fmt(inp['pt_bmi'])}")
    if fmt(inp.get("pt_asa")) is not None:
        attrs.append(f"ASA {fmt(inp['pt_asa'])}")
    demo = head + (f" ({', '.join(attrs)})" if attrs else "")

    surg = str(inp["pt_opname"]) if inp.get("pt_opname") else "an unspecified procedure"
    ctx = [str(inp[f]) for f in ("pt_optype", "pt_approach", "pt_position", "pt_ane_type")
           if inp.get(f)]
    emop = "emergency" if inp.get("pt_emop") else "elective"
    opening = f"A {demo} patient is undergoing {surg}"
    if ctx:
        opening += f" ({', '.join(ctx)})"
    opening += f", {emop}."
    lines.append(opening)

    if inp.get("pt_dx"):
        lines.append(f"Diagnosis: {inp['pt_dx']}.")
    if inp.get("pt_department"):
        lines.append(f"Department: {inp['pt_department']}.")
    if inp.get("monitoring_type"):
        lines.append(f"Monitoring: {MONITORING.get(inp['monitoring_type'], inp['monitoring_type'])}.")

    vit = []
    for name, label, unit in [("hr_current", "HR", "bpm"),
                              ("map_current", "MAP", "mmHg"),
                              ("spo2_current", "SpO2", "%"),
                              ("etco2_current", "EtCO2", "mmHg"),
                              ("bis_current", "BIS", "")]:
        v = fmt(inp.get(name))
        if v is not None:
            vit.append(f"{label} {v}" + (f" {unit}" if unit else ""))
    if vit:
        lines.append("Current vitals: " + ", ".join(vit) + ".")

    tr = []
    for name, label in [("hr_trend", "HR"), ("map_trend", "MAP"), ("bis_trend", "BIS"),
                        ("spo2_trend", "SpO2"), ("etco2_trend", "EtCO2")]:
        v = inp.get(name)
        if v is not None:
            tr.append(f"{label} {v}")
    if tr:
        lines.append("Recent trends: " + ", ".join(tr) + ".")

    dr = []
    for name, label in [("ce_propofol", "propofol effect-site concentration"),
                        ("ce_remi", "remifentanil effect-site concentration"),
                        ("exp_sevo", "sevoflurane expired concentration"),
                        ("mac", "MAC")]:
        v = fmt(inp.get(name))
        if v is not None:
            dr.append(f"{label} {v}")
    if dr:
        lines.append("Drugs: " + ", ".join(dr) + ".")

    ve = []
    for name, label in [("set_fio2", "FiO2"), ("set_peep", "PEEP"),
                        ("set_tv", "tidal volume"), ("set_rr", "respiratory rate")]:
        v = fmt(inp.get(name))
        if v is not None:
            ve.append(f"{label} {v}")
    if ve:
        lines.append("Ventilator: " + ", ".join(ve) + ".")

    la = []
    for t in KEY_LABS:
        v = fmt(inp.get(f"lab_{t}"))
        if v is not None:
            u = LAB_UNITS.get(t, "")
            la.append(f"{t} {v}" + (f" {u}" if u else ""))
    if la:
        lines.append("Preoperative labs: " + ", ".join(la) + ".")

    hs = inp.get("history_summary")
    if hs:
        lines.append(f"Recent course: {hs}")

    return "\n".join(lines)
