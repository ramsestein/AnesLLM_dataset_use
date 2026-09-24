# -*- coding: utf-8 -*-
"""Consolida los resultados de eval.py en dos CSVs:

- results/test_all.csv            -> run completo (todos los casos, sin repeticiones)
- results/consistency_all.csv     -> run de auto-consistencia (3 repeticiones)

Cada fila incluye la respuesta del modelo y el ground-truth del dataset
(result_1, result_aux y result_real) para poder cruzar los datos.
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "dataset" / "data" / "test"
RESULTS = ROOT / "results"
DATA_RESULTS = RESULTS / "data_results"


def clean(v):
    """Aplana saltos de línea y espacios múltiples para que no rompan el CSV."""
    if v is None:
        return ""
    s = str(v)
    s = s.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    return re.sub(r"\s+", " ", s).strip()


def _round(v):
    return round(v, 4) if isinstance(v, (int, float)) else v


def load_dataset():
    """window_id -> {result_1_action, result_1_ratio, result_aux_action,
                     result_aux_ratio, result_real}"""
    ds = {}
    for f in sorted(DATA.glob("case*.jsonl")):
        for line in open(f, encoding="utf-8"):
            r = json.loads(line)
            out = r.get("output", {})
            r1 = out.get("result_1") or {}
            raux = out.get("result_aux") or {}
            ds[r["window_id"]] = {
                "result_1_action": r1.get("action"),
                "result_1_ratio": _round(r1.get("ratio")),
                "result_aux_action": raux.get("action"),
                "result_aux_ratio": _round(raux.get("ratio")),
                "result_real": out.get("result_real"),
            }
    return ds


def read_jsonl(path):
    rows = []
    if not path.exists():
        return rows
    for line in open(path, encoding="utf-8"):
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    return rows


def model_name(folder):
    """Recupera el nombre real del modelo desde summary.json (sin sanitizar)."""
    s = folder / "summary.json"
    if s.exists():
        try:
            return json.loads(s.read_text(encoding="utf-8"))["model"]
        except Exception:
            pass
    return folder.name


def test_rows(ds):
    rows = []
    for d in sorted(DATA_RESULTS.glob("*")):
        if not d.is_dir() or d.name == "logs" or d.name.endswith("_repeats3"):
            continue
        f = d / "test.jsonl"
        if not f.exists():
            continue
        model = model_name(d)
        for r in read_jsonl(f):
            gt = ds.get(r.get("window_id"), {})
            rows.append({
                "model": model,
                "window_id": r.get("window_id"),
                "case_id": r.get("case_id"),
                "difficulty": r.get("difficulty"),
                "letter": r.get("letter"),
                "predicted_action": r.get("predicted_action"),
                "correct": r.get("correct"),
                "error": r.get("error"),
                "raw_response": clean(r.get("raw_response")),
                "explanation": clean(r.get("explanation")),
                **gt,
            })
    return rows


def consistency_rows(ds):
    rows = []
    for d in sorted(DATA_RESULTS.glob("*_repeats3")):
        f = d / "test.jsonl"
        if not f.exists():
            continue
        model = model_name(d)
        for r in read_jsonl(f):
            gt = ds.get(r.get("window_id"), {})
            resp = [{"letter": x.get("letter"), "raw": clean(x.get("raw")),
                     "explanation": clean(x.get("explanation")), "error": x.get("error")}
                    for x in (r.get("responses") or [])]
            rows.append({
                "model": model,
                "window_id": r.get("window_id"),
                "case_id": r.get("case_id"),
                "difficulty": r.get("difficulty"),
                "letter": r.get("letter"),
                "predicted_action": r.get("predicted_action"),
                "correct": r.get("correct"),
                "error": r.get("error"),
                "repeats": r.get("repeats"),
                "letters": json.dumps(r.get("letters"), ensure_ascii=False)
                           if r.get("letters") is not None else "",
                "consistency": r.get("consistency"),
                "responses": json.dumps(resp, ensure_ascii=False) if resp else "",
                **gt,
            })
    return rows


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)
    print(f"{path} -> {len(rows)} filas")


def main():
    ds = load_dataset()
    print(f"dataset: {len(ds)} ventanas")

    t_fields = ["model", "window_id", "case_id", "difficulty",
                "letter", "predicted_action", "correct", "error",
                "raw_response", "explanation",
                "result_1_action", "result_1_ratio", "result_aux_action",
                "result_aux_ratio", "result_real"]
    write_csv(RESULTS / "test_all.csv", test_rows(ds), t_fields)

    c_fields = ["model", "window_id", "case_id", "difficulty",
                "letter", "predicted_action", "correct", "error",
                "repeats", "letters", "consistency", "responses",
                "result_1_action", "result_1_ratio", "result_aux_action",
                "result_aux_ratio", "result_real"]
    write_csv(RESULTS / "consistency_all.csv", consistency_rows(ds), c_fields)


if __name__ == "__main__":
    main()
