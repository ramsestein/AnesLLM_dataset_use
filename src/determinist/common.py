# -*- coding: utf-8 -*-
"""Utilidades compartidas para los baselines deterministas (rules, pid, clads, fuzzy).

Cada estrategia se ejecuta sobre el test set completo y se guarda en
results/data_results/<name>/test.jsonl (mismo formato que los LLMs) más
<name>_repeats3/test.jsonl para la consistencia (determinista → consistencia 1.0).
"""
import csv
import json
import random
from pathlib import Path

from config import MAP_ACC_LO

ROOT = Path(__file__).resolve().parent.parent.parent  # src/determinist -> raíz
DATA = ROOT / "dataset" / "data" / "test"
MANIFEST = ROOT / "dataset" / "reports" / "split_manifest.csv"
RESULTS = ROOT / "results" / "data_results"

ACTIONS = ["increase_hypnotic", "reduce_hypnotic", "increase_opioid",
           "reduce_opioid", "no_action"]
ACTION_TO_LETTER = {a: chr(ord("a") + i) for i, a in enumerate(ACTIONS)}
LETTER_TO_ACTION = {ch: a for a, ch in ACTION_TO_LETTER.items()}

# Acciones fuera del alcance de los controladores (solo hipnótico/no_action)
OPIOID = {"increase_opioid", "reduce_opioid"}
VASO = {"vasopressor"}
EXCLUDED = OPIOID | VASO


def load_difficulty():
    diff = {}
    if MANIFEST.exists():
        with open(MANIFEST, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                diff[row["case_id"]] = row.get("difficulty", "unknown")
    return diff


def load_windows():
    """Ventanas del test ordenadas por caso y decision_time_abs (para stateful)."""
    recs = []
    for f in sorted(DATA.glob("case*.jsonl")):
        for line in open(f, encoding="utf-8"):
            recs.append(json.loads(line))
    recs.sort(key=lambda r: (r["case_id"], r["input"].get("decision_time_abs") or 0))
    return recs


def build_row(inp):
    """Mapea el input del dataset a las claves que esperan las políticas.

    Ojo: el dataset usa minúsculas (map_current/hr_current/bis_current) para los
    valores crudos del instante; las mayúsculas (MAP_current/HR_current) están
    nulas en ~50% de ventanas (NIBP). Las políticas leen minúsculas.
    """
    return {
        "bis_current": inp.get("bis_current"),
        "map_current": inp.get("map_current"),
        "hr_current": inp.get("hr_current"),
        "propofol_ce_current": inp.get("propofol_ce_current"),
        # tendencias (rising/falling/stable) para el lazo de nocicepción
        "hr_trend": inp.get("hr_trend"),
        "bis_trend": inp.get("bis_trend"),
        "map_trend": inp.get("map_trend"),
        # propofol_rate_current no existe en el dataset: las políticas usan su default
    }


def map_action(action):
    """Acción (5 clases) -> (letter, predicted_action)."""
    if action in ACTION_TO_LETTER:
        return ACTION_TO_LETTER[action], action
    return None, action


def apply_analgesia(policy_action, row):
    """Gate de seguridad sin reglas de opioides.

    Los controladores solo emiten no_action o hipnótico (nunca opioides):
    1. MAP < MAP_ACC_LO -> no_action (seguridad)
    2. en otro caso, la acción hipnótica de la política
    """
    map_v = row.get("map_current")
    if map_v is not None and map_v < MAP_ACC_LO:
        return "no_action"
    if policy_action in ("increase_hypnotic", "reduce_hypnotic", "no_action"):
        return policy_action
    return "no_action"


def evaluate(policy_factory, name):
    """Ejecuta la política sobre el test completo.

    Devuelve dict window_id -> record (formato idéntico al de eval.py).
    Las políticas stateful se resetean al cambiar de caso.
    """
    diff = load_difficulty()
    windows = load_windows()

    predictions = {}
    current_case = None
    policy = policy_factory()

    for rec in windows:
        wid = rec["window_id"]
        case_id = rec["case_id"]
        # Solo el subgrupo no-opioide: ninguna referencia (result_real, result_1,
        # result_aux) es opioide ni vasopressor.
        out = rec.get("output", {})
        r1 = (out.get("result_1") or {}).get("action")
        raux = (out.get("result_aux") or {}).get("action")
        rr = out.get("result_real")
        if rr in EXCLUDED or r1 in EXCLUDED or raux in EXCLUDED:
            continue
        if case_id != current_case:
            current_case = case_id
            policy.reset()
        try:
            row = build_row(rec["input"])
            action = policy.decide(row)
            # gate de seguridad (sin reglas de opioides)
            action = apply_analgesia(action, row)
        except Exception as e:
            action = "error"
        letter, paction = map_action(action)
        result_real = rec["output"]["result_real"]
        predictions[wid] = {
            "window_id": wid,
            "case_id": case_id,
            "result_real": result_real,
            "difficulty": diff.get(str(case_id), "unknown"),
            "letter": letter,
            "predicted_action": paction,
            "correct": 1 if paction == result_real else 0,
            "error": action == "error",
            "raw_response": action,
            "explanation": "",
        }
    return predictions


def compute_summary(records, model, repeats=1):
    """Resumen igual que eval.py, pero 'invalid' = sin predicción (no por letter)."""
    correct = invalid = errors = 0
    per_diff, per_class = {}, {}
    consistency_sum, consistency_n = 0.0, 0
    for r in records:
        d = r.get("difficulty", "unknown")
        per_diff.setdefault(d, [0, 0])
        per_diff[d][0] += 1
        per_diff[d][1] += int(r.get("correct") == 1)
        cl = r.get("result_real")
        if cl:
            per_class.setdefault(cl, [0, 0])
            per_class[cl][0] += 1
            per_class[cl][1] += int(r.get("correct") == 1)
        if r.get("correct") == 1:
            correct += 1
        if r.get("predicted_action") is None:
            invalid += 1
        if r.get("error"):
            errors += 1
        c = r.get("consistency")
        if c is not None:
            consistency_sum += c
            consistency_n += 1
    n = len(records)
    s = {
        "model": model, "backend": "deterministic", "split": "test",
        "n_windows": n, "repeats": repeats,
        "accuracy": round(correct / n, 4) if n else 0.0,
        "invalid_responses": invalid, "errors": errors,
        "accuracy_by_difficulty": {d: round(c / t, 4) if t else None
                                   for d, (t, c) in per_diff.items()},
        "accuracy_by_class": {a: round(c / t, 4) if t else None
                              for a, (t, c) in per_class.items()},
    }
    if repeats > 1 and consistency_n:
        s["mean_consistency"] = round(consistency_sum / consistency_n, 4)
    return s


def write_test(name, predictions):
    folder = RESULTS / name
    folder.mkdir(parents=True, exist_ok=True)
    rows = sorted(predictions.values(), key=lambda r: r["window_id"])
    with open(folder / "test.jsonl", "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    (folder / "summary.json").write_text(
        json.dumps(compute_summary(rows, name), ensure_ascii=False, indent=2),
        encoding="utf-8")
    return len(rows)


def write_consistency(name, predictions, limit=100, seed=42):
    """Consistencia determinista: replica la selección seed=42 de eval.py."""
    folder = RESULTS / (name + "_repeats3")
    folder.mkdir(parents=True, exist_ok=True)

    all_ids = []
    for f in sorted(DATA.glob("case*.jsonl")):
        for line in open(f, encoding="utf-8"):
            all_ids.append(json.loads(line)["window_id"])
    rng = random.Random(seed)
    selected = set(rng.sample(all_ids, min(limit, len(all_ids))))

    rows = []
    for wid in sorted(selected):
        p = predictions.get(wid)
        if p is None:
            continue
        letter = p["letter"]
        rows.append({
            "window_id": p["window_id"],
            "case_id": p["case_id"],
            "result_real": p["result_real"],
            "difficulty": p["difficulty"],
            "letter": letter,
            "predicted_action": p["predicted_action"],
            "correct": p["correct"],
            "error": False,
            "repeats": 3,
            "letters": [letter] * 3,
            "consistency": 1.0,
            "responses": [{"letter": letter, "raw": p["raw_response"],
                           "explanation": "", "error": False}] * 3,
        })
    with open(folder / "test.jsonl", "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    (folder / "summary.json").write_text(
        json.dumps(compute_summary(rows, name, repeats=3), ensure_ascii=False, indent=2),
        encoding="utf-8")
    return len(rows)
