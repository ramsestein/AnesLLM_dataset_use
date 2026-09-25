# -*- coding: utf-8 -*-
"""Análisis completo del benchmark AnesLLM (17 modelos: 11 LLM + 2 clasificación + 4 deterministas).

Lee results/test_all.csv y results/consistency_all.csv (ya filtrados de vasopressor)
y el dataset (dataset/data/test/*.jsonl) para red flags y suelo de "acción previa".

Genera results/analysis/: metrics_summary.csv, ceilings_floors.csv,
error_taxonomy.csv, red_flags.csv, difficulty.csv, consistency_quadrants.csv,
paired_mcnemar.csv, model_agreement.csv, confusion_<model>.csv y report.md.
"""
import csv
import json
import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "dataset" / "data" / "test"
RESULTS = ROOT / "results"
OUT = RESULTS / "analysis"
IMG = RESULTS / "img"

ACTIONS = ["increase_hypnotic", "reduce_hypnotic", "increase_opioid",
           "reduce_opioid", "no_action"]
DRUG = {
    "increase_hypnotic": "hypnotic", "reduce_hypnotic": "hypnotic",
    "increase_opioid": "opioid", "reduce_opioid": "opioid",
    "no_action": "none",
}
DIRECTION = {
    "increase_hypnotic": "increase", "reduce_hypnotic": "reduce",
    "increase_opioid": "increase", "reduce_opioid": "reduce",
    "no_action": "none",
}


def sanitize(name):
    return re.sub(r'[<>:"/\\|?*]', "_", name)

# temperatura usada por modelo (0 salvo los que la rechazan; deterministas N/A)
TEMPERATURE = {
    "gpt-6-sol": "default (no 0)", "claude-opus-4-8": "default (no 0)",
    "rules": "N/A (determinista)", "pid": "N/A (determinista)",
    "clads": "N/A (determinista)", "fuzzy": "N/A (determinista)",
}


# ---------------------------------------------------------------- carga
def load_dataset():
    """window_id -> record completo del dataset (para vitals y orden temporal)."""
    ds = {}
    for f in sorted(DATA.glob("case*.jsonl")):
        for line in open(f, encoding="utf-8"):
            r = json.loads(line)
            ds[r["window_id"]] = r
    return ds


def load_csv(path):
    with open(path, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- estadística
def cohen_kappa(cm):
    """cm: dict {(actual, predicted): count}."""
    n = sum(cm.values())
    if n == 0:
        return 0.0
    p_o = sum(cm.get((c, c), 0) for c in ACTIONS) / n
    row = {c: sum(cm.get((c, p), 0) for p in ACTIONS) for c in ACTIONS}
    col = {c: sum(cm.get((a, c), 0) for a in ACTIONS) for c in ACTIONS}
    p_e = sum(row[c] * col[c] for c in ACTIONS) / (n * n)
    return (p_o - p_e) / (1 - p_e) if p_e < 1 else 0.0


def fleiss_kappa(ratings):
    """ratings: lista de sujetos; cada sujeto = lista de conteos por categoría."""
    n = len(ratings)
    if n == 0:
        return 0.0
    k = len(ratings[0])
    N = sum(ratings[0])
    if N < 2:
        return 0.0
    p = [0.0] * k
    for r in ratings:
        for j in range(k):
            p[j] += r[j]
    total = n * N
    p = [x / total for x in p]
    P_i = [(sum(x * x for x in r) - N) / (N * (N - 1)) for r in ratings]
    P_bar = sum(P_i) / n
    P_e = sum(x * x for x in p)
    return (P_bar - P_e) / (1 - P_e) if P_e < 1 else 1.0


def mcnemar_p(b, c):
    """Test exacto de McNemar (binomial bilateral) sobre pares discordantes."""
    n = b + c
    if n == 0:
        return 1.0
    m = min(b, c)
    p = 2 * sum(math.comb(n, k) for k in range(m + 1)) / (2 ** n)
    return min(1.0, p)


def bootstrap_ci(case_windows, metric, n_iter=1000, seed=42):
    """IC 95% por bootstrap agrupado por caso (remuestrea casos)."""
    rng = random.Random(seed)
    cases = list(case_windows.values())
    n = len(cases)
    ests = []
    for _ in range(n_iter):
        idx = [rng.randrange(n) for _ in range(n)]
        sample = [w for i in idx for w in cases[i]]
        ests.append(metric(sample))
    ests.sort()
    lo = ests[int(0.025 * len(ests))]
    hi = ests[int(0.975 * len(ests))]
    return lo, hi


# ---------------------------------------------------------------- estructuras
def build_ground_truth(test_rows):
    """window_id -> dict con gt del CSV (una fila por ventana)."""
    gt = {}
    for r in test_rows:
        if r["window_id"] not in gt:
            gt[r["window_id"]] = {
                "case_id": r["case_id"],
                "difficulty": r["difficulty"],
                "result_real": r["result_real"],
                "result_1_action": r["result_1_action"],
                "result_1_ratio": fnum(r["result_1_ratio"]),
                "result_aux_action": r["result_aux_action"],
                "result_aux_ratio": fnum(r["result_aux_ratio"]),
            }
    return gt


def build_predictions(test_rows):
    """model -> {window_id -> predicted_action} (válidas = en ACTIONS)."""
    models = sorted({r["model"] for r in test_rows})
    pred = {m: {} for m in models}
    for r in test_rows:
        a = r["predicted_action"]
        pred[r["model"]][r["window_id"]] = a if a in ACTIONS else None
    return models, pred


# ---------------------------------------------------------------- sección 1-2
def accuracy_metrics(models, pred, gt):
    """Por modelo: estricta, consenso, plausibilidad, ponderada."""
    out = {}
    for m in models:
        strict = cons = plaus = 0
        wsum = 0.0
        n = 0
        for wid, g in gt.items():
            p = pred[m].get(wid)
            if p is None:
                n += 1
                continue
            n += 1
            if p == g["result_real"]:
                strict += 1
            if p == g["result_1_action"]:
                cons += 1
            if p in (g["result_1_action"], g["result_aux_action"]):
                plaus += 1
                if p == g["result_1_action"]:
                    wsum += g["result_1_ratio"] or 0.0
                else:
                    wsum += g["result_aux_ratio"] or 0.0
        out[m] = {
            "strict": strict / n, "consensus": cons / n,
            "plausibility": plaus / n, "weighted": wsum / n,
            "n": n,
        }
    return out


def ceilings_and_floors(gt, ds):
    """Techo humano y suelos globales."""
    n = len(gt)
    real_consensus = sum(1 for g in gt.values()
                         if g["result_real"] == g["result_1_action"]) / n
    real_plausible = sum(1 for g in gt.values()
                         if g["result_real"] in (g["result_1_action"], g["result_aux_action"])) / n

    # suelo: siempre no_action
    always_no_action = sum(1 for g in gt.values() if g["result_real"] == "no_action") / n

    # suelo: acción previa (orden temporal por caso)
    by_case = defaultdict(list)
    for wid, g in gt.items():
        rec = ds.get(wid, {})
        t = rec.get("input", {}).get("decision_time_abs") or 0
        by_case[g["case_id"]].append((t, g["result_real"]))
    prev_correct = 0
    prev_n = 0
    for cid, seq in by_case.items():
        seq.sort(key=lambda x: x[0])
        prev = "no_action"
        for t, real in seq:
            if prev == real:
                prev_correct += 1
            prev_n += 1
            prev = real
    previous_action = prev_correct / prev_n if prev_n else 0.0

    # suelo: aleatorio según distribución de clases (analítico)
    dist = Counter(g["result_real"] for g in gt.values())
    p = {c: dist[c] / n for c in ACTIONS}
    random_expected = sum(p[c] ** 2 for c in ACTIONS)

    return {
        "n_windows": n,
        "human_consensus": real_consensus,
        "human_plausible": real_plausible,
        "floor_always_no_action": always_no_action,
        "floor_previous_action": previous_action,
        "floor_random_expected": random_expected,
        "class_distribution": dict(dist),
    }


# ---------------------------------------------------------------- sección 3
def classification_metrics(models, pred, gt, ds):
    """balanced accuracy, macro-F1, kappa, recall por clase, intervención, colapso."""
    out = {}
    for m in models:
        cm = Counter()
        pred_dist = Counter()
        for wid, g in gt.items():
            p = pred[m].get(wid)
            if p is None:
                p = "__invalid__"
            cm[(g["result_real"], p)] += 1
            pred_dist[p] += 1
        # recall por clase
        recalls = {}
        for c in ACTIONS:
            tp = cm.get((c, c), 0)
            total = sum(cm.get((c, pp), 0) for pp in ACTIONS)
            recalls[c] = tp / total if total else 0.0
        balanced_acc = sum(recalls.values()) / len(ACTIONS)
        # macro-F1
        f1s = []
        for c in ACTIONS:
            tp = cm.get((c, c), 0)
            fp = sum(cm.get((a, c), 0) for a in ACTIONS if a != c)
            fn = sum(cm.get((c, pp), 0) for pp in ACTIONS if pp != c)
            prec = tp / (tp + fp) if (tp + fp) else 0.0
            rec = tp / (tp + fn) if (tp + fn) else 0.0
            f1s.append(2 * prec * rec / (prec + rec) if (prec + rec) else 0.0)
        macro_f1 = sum(f1s) / len(f1s)
        kappa = cohen_kappa(cm)
        # índice de intervención
        model_acts = sum(pred_dist[c] for c in ACTIONS if c != "no_action")
        clinician_acts = sum(1 for g in gt.values() if g["result_real"] != "no_action")
        n = len(gt)
        intervention_idx = (model_acts / n) / (clinician_acts / n) if clinician_acts else None
        # colapso de modo: tasa "misma respuesta que ventana anterior"
        same_as_prev = same_as_previous(pred[m], gt, ds)
        out[m] = {
            "balanced_accuracy": balanced_acc, "macro_f1": macro_f1,
            "cohen_kappa": kappa, "recall_by_class": recalls,
            "predicted_distribution": dict(pred_dist),
            "intervention_index": intervention_idx,
            "same_as_previous_rate": same_as_prev,
            "confusion": cm,
        }
    return out


def same_as_previous(model_pred, gt, ds):
    """Tasa de 'misma respuesta que la ventana anterior del mismo caso'."""
    by_case = defaultdict(list)
    for wid, g in gt.items():
        rec = ds.get(wid, {}).get("input", {})
        t = rec.get("decision_time_abs") or 0
        by_case[g["case_id"]].append((t, model_pred.get(wid), g["result_real"]))
    same_model = same_clin = 0
    n = 0
    for cid, seq in by_case.items():
        seq.sort(key=lambda x: x[0])
        for i in range(1, len(seq)):
            n += 1
            if seq[i][1] is not None and seq[i][1] == seq[i - 1][1]:
                same_model += 1
            if seq[i][2] == seq[i - 1][2]:
                same_clin += 1
    return (same_model / n if n else 0.0, same_clin / n if n else 0.0)


# ---------------------------------------------------------------- sección 4
def error_taxonomy(models, pred, gt):
    """Clasifica cada error en: dirección opuesta / fármaco distinto /
    sobreintervención / infratratamiento / otro."""
    out = {}
    for m in models:
        counts = Counter()
        for wid, g in gt.items():
            p = pred[m].get(wid)
            a = g["result_real"]
            if p == a:
                counts["correct"] += 1
            elif p is None:
                counts["invalid"] += 1
            elif a == "no_action":
                counts["over_intervention"] += 1
            elif p == "no_action":
                counts["under_treatment"] += 1
            elif DRUG[p] == DRUG[a] and DIRECTION[p] != DIRECTION[a]:
                counts["opposite_direction"] += 1
            elif DIRECTION[p] == DIRECTION[a] and DRUG[p] != DRUG[a]:
                counts["wrong_drug"] += 1
            else:
                counts["other"] += 1
        out[m] = dict(counts)
    return out


RED_FLAGS = {
    "incr_hypnotic_bis_lt40": lambda p, f: p == "increase_hypnotic"
        and f.get("bis_current") is not None and 0 < f["bis_current"] < 40,
    "incr_hypnotic_map_lt65": lambda p, f: p == "increase_hypnotic"
        and f.get("map_current") is not None and f["map_current"] < 65,
    "incr_opioid_hr_lt50": lambda p, f: p == "increase_opioid"
        and f.get("hr_current") is not None and f["hr_current"] < 50,
    "reduce_hypnotic_bis_gt60": lambda p, f: p == "reduce_hypnotic"
        and f.get("bis_current") is not None and f["bis_current"] > 60,
}


def red_flags(models, pred, gt, ds):
    """Tasa de recomendaciones fisiológicamente dañinas por modelo."""
    out = {}
    for m in models:
        counts = {name: 0 for name in RED_FLAGS}
        n = 0
        for wid, g in gt.items():
            p = pred[m].get(wid)
            if p is None:
                continue
            f = ds.get(wid, {}).get("input", {})
            n += 1
            for name, rule in RED_FLAGS.items():
                if rule(p, f):
                    counts[name] += 1
        out[m] = {k: v / n for k, v in counts.items()}
        out[m]["n"] = n
    return out


def harmful_action_rate(models, pred, gt, ds):
    """Fracción de ventanas donde el modelo emite una acción potencialmente
    dañina activa (red flag). Daño clínico real, no desacuerdo con result_real."""
    out = {}
    for m in models:
        n = harmful = 0
        for wid, g in gt.items():
            p = pred[m].get(wid)
            if p is None:
                continue
            f = ds.get(wid, {}).get("input", {})
            n += 1
            if any(rule(p, f) for rule in RED_FLAGS.values()):
                harmful += 1
        out[m] = harmful / n if n else 0.0
    return out


def human_red_flags(gt, ds):
    """Red flags de las decisiones humanas (result_real / result_1 / result_aux).

    Devuelve por referencia: n, tasa de ventanas con >=1 red flag ('any') y la
    tasa de cada red flag individual.
    """
    refs = [("result_real", "result_real"),
            ("result_1", "result_1_action"),
            ("result_aux", "result_aux_action")]
    out = {}
    for label, key in refs:
        counts = {name: 0 for name in RED_FLAGS}
        n = anyf = 0
        for wid, g in gt.items():
            p = g.get(key)
            if p is None:
                continue
            f = ds.get(wid, {}).get("input", {})
            n += 1
            hit = False
            for name, rule in RED_FLAGS.items():
                if rule(p, f):
                    counts[name] += 1
                    hit = True
            if hit:
                anyf += 1
        out[label] = {k: v / n if n else 0.0 for k, v in counts.items()}
        out[label]["n"] = n
        out[label]["any"] = anyf / n if n else 0.0
    return out


def subgroup_red_flag_rate(models, pred, gt, ds, wids):
    """Tasa de red flags por modelo restringida a un subconjunto de ventanas."""
    wset = set(wids)
    out = {}
    for m in models:
        n = harmful = 0
        for w in wset:
            p = pred[m].get(w)
            if p is None:
                continue
            f = ds.get(w, {}).get("input", {})
            n += 1
            if any(rule(p, f) for rule in RED_FLAGS.values()):
                harmful += 1
        out[m] = harmful / n if n else 0.0
    return out


def subgroup_human_safety(gt, ds, wids):
    """1 - tasa de red flags de result_real sobre un subconjunto de ventanas."""
    wset = set(wids)
    n = harmful = 0
    for w in wset:
        p = gt[w]["result_real"]
        if p is None:
            continue
        f = ds.get(w, {}).get("input", {})
        n += 1
        if any(rule(p, f) for rule in RED_FLAGS.values()):
            harmful += 1
    return 1 - (harmful / n) if n else 1.0


# ---------------------------------------------------------------- sección 5
def difficulty_stratification(models, pred, gt):
    out = {}
    for m in models:
        per = defaultdict(lambda: [0, 0])
        for wid, g in gt.items():
            per[g["difficulty"]][0] += 1
            per[g["difficulty"]][1] += int(pred[m].get(wid) == g["result_real"])
        out[m] = {d: c / t for d, (t, c) in per.items()}
    return out


# ---------------------------------------------------------------- sección 8
OPIOID = {"increase_opioid", "reduce_opioid"}
VASO = {"vasopressor"}


def no_opioid_subgroup(models, pred, gt):
    """Subgrupo de ventanas donde NINGUNA referencia (result_real, result_1,
    result_aux) es opioide ni vasopressor: solo hipnótico / no_action.

    Permite aislar la parte 'pura' del benchmark (control de hipnosis) de la
    analgesia, que domina la distribución global (~51% de opioides en real).
    """
    excluded = OPIOID | VASO
    wids = [w for w, g in gt.items()
            if g["result_real"] not in excluded
            and g["result_1_action"] not in excluded
            and g["result_aux_action"] not in excluded]
    n = len(wids)
    human_cons = (sum(1 for w in wids
                      if gt[w]["result_real"] == gt[w]["result_1_action"]) / n
                  if n else 0.0)
    human_plaus = (sum(1 for w in wids
                       if gt[w]["result_real"] in
                       (gt[w]["result_1_action"], gt[w]["result_aux_action"])) / n
                   if n else 0.0)
    dist = Counter(gt[w]["result_real"] for w in wids)
    models_out = {}
    for m in models:
        strict = cons = plaus = 0
        for w in wids:
            p = pred[m].get(w)
            if p is None:
                continue
            if p == gt[w]["result_real"]:
                strict += 1
            if p == gt[w]["result_1_action"]:
                cons += 1
            if p in (gt[w]["result_1_action"], gt[w]["result_aux_action"]):
                plaus += 1
        models_out[m] = {
            "strict": strict / n if n else 0.0,
            "consensus": cons / n if n else 0.0,
            "plausibility": plaus / n if n else 0.0,
        }
    return {
        "n": n,
        "human_consensus": human_cons,
        "human_plausible": human_plaus,
        "class_distribution": dict(dist),
        "models": models_out,
        "wids": wids,
    }


def paired_mcnemar(models, pred, gt):
    """Matriz de p-valores McNemar entre pares de modelos."""
    wids = list(gt.keys())
    correct = {m: {w: (pred[m].get(w) == gt[w]["result_real"]) for w in wids} for m in models}
    matrix = {}
    for a in models:
        for b in models:
            if a >= b:
                continue
            b_disc = c_disc = 0
            for w in wids:
                ca, cb = correct[a][w], correct[b][w]
                if ca and not cb:
                    b_disc += 1
                elif cb and not ca:
                    c_disc += 1
            matrix[(a, b)] = mcnemar_p(b_disc, c_disc)
    return matrix


def bootstrap_accuracy(models, pred, gt, case_windows):
    """IC95 bootstrap por caso para estricta, consenso y plausibilidad."""
    out = {}
    allw = [w for ws in case_windows.values() for w in ws]
    for m in models:
        def strict(sample):
            return (sum(1 for w in sample if pred[m].get(w) == gt[w]["result_real"]) / len(sample)
                    if sample else 0.0)
        def consensus(sample):
            return (sum(1 for w in sample if pred[m].get(w) == gt[w]["result_1_action"]) / len(sample)
                    if sample else 0.0)
        def plaus(sample):
            return (sum(1 for w in sample
                        if pred[m].get(w) in (gt[w]["result_1_action"], gt[w]["result_aux_action"]))
                    / len(sample) if sample else 0.0)
        out[m] = {
            "strict": (strict(allw),) + bootstrap_ci(case_windows, strict),
            "consensus": (consensus(allw),) + bootstrap_ci(case_windows, consensus),
            "plausibility": (plaus(allw),) + bootstrap_ci(case_windows, plaus),
        }
    return out


# ---------------------------------------------------------------- sección 6
def consistency_analysis(cons_rows):
    """Cuadrantes, inestabilidad->error, Fleiss kappa por modelo."""
    by_model = defaultdict(list)
    for r in cons_rows:
        by_model[r["model"]].append(r)
    out = {}
    for m, rows in by_model.items():
        quad = Counter()
        inst_err = [0, 0]
        stable_err = [0, 0]
        ratings = []
        for r in rows:
            letters = json.loads(r["letters"]) if r.get("letters") else []
            letters = [x for x in letters if x in "abcde"]
            stable = len(set(letters)) <= 1 if letters else True
            correct = r["correct"] == "1"
            if stable and correct:
                quad["stable_correct"] += 1
            elif stable and not correct:
                quad["stable_incorrect"] += 1
            elif not stable and correct:
                quad["unstable_correct"] += 1
            else:
                quad["unstable_incorrect"] += 1
            if stable:
                stable_err[0] += 1
                stable_err[1] += int(not correct)
            else:
                inst_err[0] += 1
                inst_err[1] += int(not correct)
            # Fleiss: 3 repeticiones como raters, 5 categorías (a-e)
            if letters:
                ratings.append([letters.count(ch) for ch in "abcde"])
        out[m] = {
            "quadrants": dict(quad),
            "error_rate_stable": stable_err[1] / stable_err[0] if stable_err[0] else None,
            "error_rate_unstable": inst_err[1] / inst_err[0] if inst_err[0] else None,
            "fleiss_kappa": fleiss_kappa(ratings),
            "n": len(rows),
        }
    return out


# ---------------------------------------------------------------- sección 7
def model_agreement(models, pred, gt):
    """Fleiss kappa entre modelos, ensemble mayoritario, ventanas donde fallan todos."""
    wids = list(gt.keys())
    ratings = []
    ensemble_correct = 0
    all_fail = 0
    for w in wids:
        votes = Counter()
        for m in models:
            p = pred[m].get(w)
            if p in ACTIONS:
                votes[p] += 1
        # Fleiss: categorías = 5 acciones; cada modelo es un rater
        ratings.append([votes.get(c, 0) for c in ACTIONS])
        if votes:
            majority = votes.most_common(1)[0][0]
            if majority == gt[w]["result_real"]:
                ensemble_correct += 1
        # ¿fallan todos?
        if all(pred[m].get(w) != gt[w]["result_real"] for m in models):
            all_fail += 1
    return {
        "fleiss_kappa_models": fleiss_kappa(ratings),
        "ensemble_majority_accuracy": ensemble_correct / len(wids),
        "windows_all_fail": all_fail,
        "n_windows": len(wids),
    }


# ---------------------------------------------------------------- salida
def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"  {path.relative_to(ROOT)} -> {len(rows)} filas")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("cargando datos...")
    test_rows = load_csv(RESULTS / "test_all.csv")
    cons_rows = load_csv(RESULTS / "consistency_all.csv")
    ds = load_dataset()

    gt = build_ground_truth(test_rows)
    models, pred = build_predictions(test_rows)
    full_models = [m for m in models if cat(m) != "determinist"]
    case_windows = defaultdict(list)
    for w in gt:
        case_windows[gt[w]["case_id"]].append(w)

    print(f"{len(models)} modelos, {len(gt)} ventanas, {len(case_windows)} casos")

    # --- sección 1-2: acierto + techo/suelo
    acc = accuracy_metrics(full_models, pred, gt)
    cf = ceilings_and_floors(gt, ds)
    write_csv(OUT / "metrics_summary.csv",
              [{"model": m, **acc[m]} for m in full_models],
              ["model", "n", "strict", "consensus", "plausibility", "weighted"])
    write_csv(OUT / "ceilings_floors.csv", [cf],
              list(cf.keys()))

    # --- sección 3: clasificación
    clf = classification_metrics(full_models, pred, gt, ds)
    write_csv(OUT / "classification.csv",
              [{"model": m,
                "balanced_accuracy": round(v["balanced_accuracy"], 4),
                "macro_f1": round(v["macro_f1"], 4),
                "cohen_kappa": round(v["cohen_kappa"], 4),
                "intervention_index": round(v["intervention_index"], 4)
                if v["intervention_index"] is not None else None,
                "same_as_previous_model": round(v["same_as_previous_rate"][0], 4),
                "same_as_previous_clinician": round(v["same_as_previous_rate"][1], 4)}
               for m, v in clf.items()],
              ["model", "balanced_accuracy", "macro_f1", "cohen_kappa",
               "intervention_index", "same_as_previous_model", "same_as_previous_clinician"])
    for m in full_models:
        cm = clf[m]["confusion"]
        rows = []
        for a in ACTIONS:
            rows.append({"actual": a,
                         **{p: cm.get((a, p), 0) for p in ACTIONS}})
        write_csv(OUT / f"confusion_{sanitize(m)}.csv", rows,
                  ["actual"] + ACTIONS)

    # --- sección 4: errores + red flags
    tax = error_taxonomy(full_models, pred, gt)
    write_csv(OUT / "error_taxonomy.csv",
              [{"model": m, **tax[m]} for m in full_models],
              ["model", "correct", "opposite_direction", "wrong_drug",
               "over_intervention", "under_treatment", "other", "invalid"])
    rf = red_flags(full_models, pred, gt, ds)
    write_csv(OUT / "red_flags.csv",
              [{"model": m, **{k: round(v, 4) for k, v in rf[m].items() if k != "n"},
                "n": rf[m]["n"]} for m in full_models],
              ["model", "n"] + list(RED_FLAGS.keys()))

    # --- sección 5: fiabilidad
    diff = difficulty_stratification(full_models, pred, gt)
    write_csv(OUT / "difficulty.csv",
              [{"model": m, **diff[m]} for m in full_models],
              ["model", "easy", "medium", "hard"])
    mcn = paired_mcnemar(full_models, pred, gt)
    write_csv(OUT / "paired_mcnemar.csv",
              [{"model_a": a, "model_b": b, "mcnemar_p": round(p, 6)}
               for (a, b), p in sorted(mcn.items())],
              ["model_a", "model_b", "mcnemar_p"])
    boot = bootstrap_accuracy(full_models, pred, gt, case_windows)
    write_csv(OUT / "bootstrap_ci.csv",
              [{"model": m,
                "strict": round(v["strict"][0], 4),
                "strict_lo": round(v["strict"][1], 4),
                "strict_hi": round(v["strict"][2], 4),
                "consensus": round(v["consensus"][0], 4),
                "consensus_lo": round(v["consensus"][1], 4),
                "consensus_hi": round(v["consensus"][2], 4),
                "plausibility": round(v["plausibility"][0], 4),
                "plausibility_lo": round(v["plausibility"][1], 4),
                "plausibility_hi": round(v["plausibility"][2], 4)}
               for m, v in boot.items()],
              ["model", "strict", "strict_lo", "strict_hi",
               "consensus", "consensus_lo", "consensus_hi",
               "plausibility", "plausibility_lo", "plausibility_hi"])

    # --- sección 6: consistencia
    cons = consistency_analysis(cons_rows)
    write_csv(OUT / "consistency_quadrants.csv",
              [{"model": m,
                "stable_correct": v["quadrants"].get("stable_correct", 0),
                "stable_incorrect": v["quadrants"].get("stable_incorrect", 0),
                "unstable_correct": v["quadrants"].get("unstable_correct", 0),
                "unstable_incorrect": v["quadrants"].get("unstable_incorrect", 0),
                "error_rate_stable": round(v["error_rate_stable"], 4)
                if v["error_rate_stable"] is not None else None,
                "error_rate_unstable": round(v["error_rate_unstable"], 4)
                if v["error_rate_unstable"] is not None else None,
                "fleiss_kappa": round(v["fleiss_kappa"], 4)}
               for m, v in cons.items()],
              ["model", "stable_correct", "stable_incorrect",
               "unstable_correct", "unstable_incorrect",
               "error_rate_stable", "error_rate_unstable", "fleiss_kappa"])

    # --- sección 7: acuerdo entre modelos
    agree = model_agreement(full_models, pred, gt)
    write_csv(OUT / "model_agreement.csv",
              [{"fleiss_kappa_models": round(agree["fleiss_kappa_models"], 4),
                "ensemble_majority_accuracy": round(agree["ensemble_majority_accuracy"], 4),
                "windows_all_fail": agree["windows_all_fail"],
                "n_windows": agree["n_windows"]}],
              ["fleiss_kappa_models", "ensemble_majority_accuracy",
               "windows_all_fail", "n_windows"])

    # --- sección 8: subgrupo sin opioide ni vasopressor
    nop = no_opioid_subgroup(models, pred, gt)
    write_csv(OUT / "no_opioid_subgroup.csv",
              [{"model": m, **nop["models"][m]} for m in models],
              ["model", "strict", "consensus", "plausibility"])
    write_csv(OUT / "no_opioid_subgroup_meta.csv",
              [{"n_windows": nop["n"],
                "human_consensus": round(nop["human_consensus"], 4),
                "human_plausible": round(nop["human_plausible"], 4),
                "class_distribution": json.dumps(nop["class_distribution"])}],
              ["n_windows", "human_consensus", "human_plausible",
               "class_distribution"])

    # --- sección 9: red flags de las decisiones humanas
    hrf = human_red_flags(gt, ds)
    write_csv(OUT / "human_red_flags.csv",
              [{"reference": ref, "n": v["n"], "any": round(v["any"], 4),
                **{k: round(v[k], 4) for k in RED_FLAGS}}
               for ref, v in hrf.items()],
              ["reference", "n", "any"] + list(RED_FLAGS.keys()))
    human_safety = 1 - hrf["result_real"]["any"]

    # --- gráficas del subgrupo no-opioide
    nop_wids = nop["wids"]
    nop_hflag = subgroup_red_flag_rate(models, pred, gt, ds, nop_wids)
    nop_human_safety = subgroup_human_safety(gt, ds, nop_wids)
    make_subgroup_plots(nop, nop_hflag, nop_human_safety, models)

    # --- reporte Markdown
    write_report(acc, cf, clf, tax, rf, diff, boot, cons, agree, nop, full_models, models)
    hflag = harmful_action_rate(full_models, pred, gt, ds)
    make_plots(acc, cf, hflag, human_safety, full_models)
    print("análisis completo en", OUT)


def write_report(acc, cf, clf, tax, rf, diff, boot, cons, agree, nop, full_models, all_models):
    lines = []
    lines.append(f"# AnesLLM Benchmark Analysis ({len(full_models)} models)")
    lines.append("")
    lines.append(f"- Windows (test, vasopressor excluded): **{cf['n_windows']}**")
    lines.append(f"- **Human ceiling** (consensus vs result_1): {cf['human_consensus']:.3f} · "
                 f"(plausible {{result_1, result_aux}}): {cf['human_plausible']:.3f}")
    lines.append(f"- Floors: always no_action {cf['floor_always_no_action']:.3f} · "
                 f"previous action {cf['floor_previous_action']:.3f} · "
                 f"random {cf['floor_random_expected']:.3f}")
    lines.append("")
    lines.append("## 1. Accuracy against each reference")
    lines.append("")
    lines.append("| model | strict (result_real) | consensus (result_1) | plausible {1,aux} | weighted |")
    lines.append("|---|--|--|--|--|")
    for m in sorted(full_models, key=lambda m: -acc[m]["consensus"]):
        lines.append(f"| {m} | {acc[m]['strict']:.3f} | {acc[m]['consensus']:.3f} | "
                     f"{acc[m]['plausibility']:.3f} | {acc[m]['weighted']:.3f} |")
    lines.append("")
    lines.append("## 3. Classification quality")
    lines.append("")
    lines.append("| model | balanced acc | macro-F1 | Cohen κ | intervention index |")
    lines.append("|---|---|---|---|---|")
    for m in sorted(full_models, key=lambda m: -clf[m]["macro_f1"]):
        v = clf[m]
        ii = f"{v['intervention_index']:.2f}" if v["intervention_index"] is not None else "—"
        lines.append(f"| {m} | {v['balanced_accuracy']:.3f} | {v['macro_f1']:.3f} | "
                     f"{v['cohen_kappa']:.3f} | {ii} |")
    lines.append("")
    lines.append("## 4. Error taxonomy (proportion of windows)")
    lines.append("")
    lines.append("| model | opposite direction | wrong drug | over-intervention | under-treatment | other |")
    lines.append("|---|---|---|---|---|---|")
    for m in sorted(full_models):
        t = tax[m]
        n = sum(t.values()) or 1
        lines.append(f"| {m} | {t.get('opposite_direction',0)/n:.3f} | "
                     f"{t.get('wrong_drug',0)/n:.3f} | {t.get('over_intervention',0)/n:.3f} | "
                     f"{t.get('under_treatment',0)/n:.3f} | {t.get('other',0)/n:.3f} |")
    lines.append("")
    lines.append("## 5. Reliability (case-clustered bootstrap, 95% CI)")
    lines.append("")
    lines.append("| model | consensus (CI) | plausible (CI) |")
    lines.append("|---|---|---|")
    for m in sorted(full_models, key=lambda m: -boot[m]["consensus"][0]):
        c = boot[m]["consensus"]
        p = boot[m]["plausibility"]
        lines.append(f"| {m} | {c[0]:.3f} [{c[1]:.3f}, {c[2]:.3f}] | "
                     f"{p[0]:.3f} [{p[1]:.3f}, {p[2]:.3f}] |")
    lines.append("")
    lines.append("## 6. Consistency (3 repeats)")
    lines.append("")
    lines.append("| model | Fleiss κ | error rate stable | error rate unstable |")
    lines.append("|---|---|---|---|")
    for m in sorted(full_models):
        v = cons[m]
        eu = f"{v['error_rate_unstable']:.3f}" if v["error_rate_unstable"] is not None else "—"
        es = f"{v['error_rate_stable']:.3f}" if v["error_rate_stable"] is not None else "—"
        lines.append(f"| {m} | {v['fleiss_kappa']:.3f} | {es} | {eu} |")
    lines.append("")
    lines.append("## 7. Inter-model agreement")
    lines.append("")
    lines.append(f"- Fleiss κ ({len(full_models)} models): **{agree['fleiss_kappa_models']:.3f}**")
    lines.append(f"- Majority-vote ensemble: **{agree['ensemble_majority_accuracy']:.3f}**")
    lines.append(f"- Windows where all models fail: **{agree['windows_all_fail']}**")
    lines.append("")
    lines.append("## 8. No-opioid subgroup (no opioid/vasopressor in any reference)")
    lines.append("")
    lines.append(f"- Windows: **{nop['n']}** · human consensus {nop['human_consensus']:.3f} · "
                 f"plausible {nop['human_plausible']:.3f}")
    lines.append(f"- Class distribution: {nop['class_distribution']}")
    lines.append("")
    lines.append("| model | strict | consensus | plausible |")
    lines.append("|---|---|---|---|")
    for m in sorted(all_models, key=lambda m: -nop["models"][m]["consensus"]):
        v = nop["models"][m]
        lines.append(f"| {m} | {v['strict']:.3f} | {v['consensus']:.3f} | "
                     f"{v['plausibility']:.3f} |")
    lines.append("")
    (OUT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"  {OUT.relative_to(ROOT) / 'report.md'}")


DETERMINIST = {"rules", "pid", "clads", "fuzzy"}
CLASSIFIERS = {"laya", "jev"}
DISPLAY = {
    "deepseek-flash": "deepseek-4.1-flash",
    "claude-haiku-4-5-20251001": "haiku-4.5",
    "claude-opus-4-8": "opus-4.8",
}
CAT_COLOR = {
    "human": "#2ca02c",
    "llm": "#1f77b4",
    "determinist": "#ff7f0e",
    "classifier": "#000000",
}


def disp(m):
    return DISPLAY.get(m, m)


def cat(m):
    if m in DETERMINIST:
        return "determinist"
    if m in CLASSIFIERS:
        return "classifier"
    return "llm"


def color_of(m):
    return CAT_COLOR[cat(m)]


def make_subgroup_plots(nop, hflag, human_safety, models):
    """Gráficas del subgrupo no-opioide (solo hipnótico/no_action): ranking
    plausible, ranking consensus y accuracy vs safety (red flags)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch, Rectangle

    IMG.mkdir(parents=True, exist_ok=True)

    acc = {m: nop["models"][m] for m in models}
    cf = {"human_plausible": nop["human_plausible"],
          "human_consensus": nop["human_consensus"]}
    present_cats = sorted({cat(m) for m in models})

    def _rank_chart(metric, ceiling, fname):
        ms = sorted(models, key=lambda m: -acc[m][metric])
        labels = ["human ceiling"] + [disp(m) for m in ms]
        values = [ceiling] + [acc[m][metric] for m in ms]
        y = list(range(len(labels)))
        fig, ax = plt.subplots(figsize=(10, 7.5))
        bars = ax.barh(y, values, height=0.6)
        bars[0].set_color(CAT_COLOR["human"])
        for b, m in zip(bars[1:], ms):
            b.set_color(color_of(m))
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=8)
        ax.invert_yaxis()
        ax.set_xlabel("Accuracy (no-opioid subgroup)")
        ax.set_xlim(0, 1)
        ax.set_title(f"Model ranking by {metric} (no-opioid subgroup)")
        handles = [Patch(color=CAT_COLOR["human"], label="human ceiling")]
        for c in present_cats:
            handles.append(Patch(color=CAT_COLOR[c], label=c))
        ax.legend(handles=handles, loc="lower right", fontsize=8)
        plt.tight_layout()
        plt.savefig(IMG / fname, dpi=150)
        plt.close(fig)
        print(f"  {IMG.relative_to(ROOT) / fname}")

    _rank_chart("plausibility", cf["human_plausible"], "subgroup_ranking_plausible.png")
    _rank_chart("consensus", cf["human_consensus"], "subgroup_ranking_consensus.png")

    # scatter accuracy vs safety
    pts = [(m, acc[m]["plausibility"], hflag[m]) for m in models]
    ys = [1 - p[2] for p in pts]
    acc_plausible = cf["human_plausible"]
    xmax = min(1.0, acc_plausible + 0.08)

    seen = defaultdict(int)
    plot_pts = []
    for (m, x, _), yv in zip(pts, ys):
        k = seen[round(yv, 2)]
        seen[round(yv, 2)] += 1
        plot_pts.append((m, x, yv - k * 0.003))

    OFFSETS = [(7, 5), (7, -9), (-5, 7), (-5, -9), (9, 0), (9, -6), (-7, -4), (-7, 4)]
    OVERRIDES = {
        "clads": (0, 16),
        "fuzzy": (-16, -6),
        "deepseek-4.1-flash": (0, 14),
        "gpt-6-sol": (14, 10),
        "deepseek-v4-pro": (0, -14),
        "rules": (0, -16),
        "gemini-3.1-pro-preview": (0, -18),
        "pid": (18, 0),
        "gpt-5.4": (0, -14),
        "laya": (14, 6),
        "haiku-4.5": (0, 14),
        "jev": (0, 14),
        "opus-4.8": (0, -14),
        "gpt-4o": (0, -14),
        "gpt-5.4-mini": (0, -14),
        "medgemma:27b": (0, -14),
        "gemini-3.1-flash-lite": (0, -14),
    }

    fig, ax = plt.subplots(figsize=(16, 8))
    for i, (m, x, yv2) in enumerate(sorted(plot_pts, key=lambda t: -t[2])):
        ox, oy = OVERRIDES.get(disp(m), OFFSETS[i % len(OFFSETS)])
        ax.scatter(x, yv2, s=90, color=color_of(m))
        ax.annotate(disp(m), (x, yv2), fontsize=8,
                    textcoords="offset points", xytext=(ox, oy))

    ax.add_patch(Rectangle((acc_plausible, human_safety),
                           xmax - acc_plausible, 1.02 - human_safety,
                           color="green", alpha=0.16, zorder=0))
    ax.axhline(human_safety, color="green", linestyle="--", linewidth=1, alpha=0.35)
    ax.axvline(acc_plausible, color="green", linestyle="--", linewidth=1, alpha=0.35)

    ax.set_xlabel("Combined accuracy (plausible) \u2014 no-opioid subgroup")
    ax.set_ylabel("1 \u2212 harmful action rate (red flags, higher = better)")
    ax.set_title("Accuracy vs safety (red flags, no-opioid subgroup)")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.78, 1.02)
    ax.set_xticks([round(i * 0.1, 2) for i in range(11)])
    ax.set_yticks([round(0.8 + i * 0.05, 2) for i in range(5)])
    handles = [Patch(facecolor="green", alpha=0.4,
                     label=f"human zone (acc \u2265 {acc_plausible:.2f}, "
                           f"safety \u2265 {human_safety:.3f})")]
    for c in present_cats:
        handles.append(Patch(color=CAT_COLOR[c], label=c))
    ax.legend(handles=handles, loc="lower right", fontsize=8)

    plt.tight_layout()
    plt.savefig(IMG / "subgroup_harmful_vs_accuracy.png", dpi=150)
    plt.close(fig)
    print(f"  {IMG.relative_to(ROOT) / 'subgroup_harmful_vs_accuracy.png'}")


def make_plots(acc, cf, hflag, human_safety, models):
    """Gráficas: ranking plausible, ranking consensus (con techo humano como barra) y precisión vs daño (red flags)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    IMG.mkdir(parents=True, exist_ok=True)

    present_cats = sorted({cat(m) for m in models})

    def _rank_chart(metric, ceiling, fname):
        ms = sorted([m for m in models if cat(m) != "determinist"],
                    key=lambda m: -acc[m][metric])
        labels = ["human ceiling"] + [disp(m) for m in ms]
        values = [ceiling] + [acc[m][metric] for m in ms]
        y = list(range(len(labels)))

        fig, ax = plt.subplots(figsize=(10, 7.5))
        bars = ax.barh(y, values, height=0.6)
        bars[0].set_color(CAT_COLOR["human"])
        for b, m in zip(bars[1:], ms):
            b.set_color(color_of(m))
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=8)
        ax.invert_yaxis()
        ax.set_xlabel("Accuracy")
        ax.set_xlim(0, 1)
        ax.set_title(f"Model ranking by {metric} (human ceiling as bar)")
        handles = [Patch(color=CAT_COLOR["human"], label="human ceiling")]
        for c in sorted({cat(m) for m in ms}):
            handles.append(Patch(color=CAT_COLOR[c], label=c))
        ax.legend(handles=handles, loc="lower right", fontsize=8)
        plt.tight_layout()
        plt.savefig(IMG / fname, dpi=150)
        plt.close(fig)
        print(f"  {IMG.relative_to(ROOT) / fname}")

    _rank_chart("plausibility", cf["human_plausible"], "ranking_plausible.png")
    _rank_chart("consensus", cf["human_consensus"], "ranking_consensus.png")

    # --- Gráfica 3: accuracy vs seguridad (red flags = daño activo) ---
    pts = []
    for m in models:
        if cat(m) == "determinist":
            continue
        pts.append((m, acc[m]["plausibility"], hflag[m]))

    xs = [p[1] for p in pts]
    # eje y = safety = 1 - red_flag_rate → arriba = mejor (menos daño activo)
    ys = [1 - p[2] for p in pts]

    acc_plausible = cf["human_plausible"]
    xmax = 1.0

    # separar puntos apilados con un jitter vertical mínimo (solo visual)
    seen = defaultdict(int)
    plot_pts = []
    for (m, x, _), yv in zip(pts, ys):
        k = seen[round(yv, 2)]
        seen[round(yv, 2)] += 1
        plot_pts.append((m, x, yv - k * 0.003))

    # offsets escalonados para que las etiquetas no se solapen
    OFFSETS = [(7, 5), (7, -9), (-5, 7), (-5, -9), (9, 0), (9, -6), (-7, -4), (-7, 4)]
    # ajustes manuales por nombre de display (separan etiquetas apiladas)
    OVERRIDES = {
        "gpt-6-sol": (0, 18),
        "deepseek-4.1-flash": (0, 18),
        "deepseek-v4-pro": (-22, 0),
        "gemini-3.1-pro-preview": (-16, -18),
        "gpt-5.4": (22, 2),
        "laya": (14, 6),
        "haiku-4.5": (0, 16),
        "opus-4.8": (18, 8),
        "jev": (0, -16),
        "gpt-4o": (0, -14),
        "gpt-5.4-mini": (16, 0),
        "medgemma:27b": (0, -14),
        "gemini-3.1-flash-lite": (0, -14),
    }

    fig, ax = plt.subplots(figsize=(16, 8))
    for i, (m, x, yv2) in enumerate(sorted(plot_pts, key=lambda t: -t[2])):
        ox, oy = OVERRIDES.get(disp(m), OFFSETS[i % len(OFFSETS)])
        ax.scatter(x, yv2, s=90, color=color_of(m))
        ax.annotate(disp(m), (x, yv2), fontsize=8,
                    textcoords="offset points", xytext=(ox, oy))

    # zona humana: combined accuracy >= techo plausible Y safety >= techo humano
    from matplotlib.patches import Rectangle
    ax.add_patch(Rectangle((acc_plausible, human_safety),
                           xmax - acc_plausible, 1.02 - human_safety,
                           color="green", alpha=0.16, zorder=0))
    # límites humanos: seguridad (eje y) y accuracy (eje x), tono suave
    ax.axhline(human_safety, color="green", linestyle="--", linewidth=1, alpha=0.35)
    ax.axvline(acc_plausible, color="green", linestyle="--", linewidth=1, alpha=0.35)

    ax.set_xlabel("Combined accuracy (plausible: result_1 or result_aux)")
    ax.set_ylabel("1 \u2212 harmful action rate (red flags, higher = better)")
    ax.set_title("Accuracy vs safety (red flags)")
    ax.set_xlim(0.3, 1.0)
    ax.set_ylim(0.78, 1.02)
    ax.set_xticks([round(0.3 + i * 0.1, 2) for i in range(8)])   # 0.3..1.0 paso 0.1
    ax.set_yticks([round(0.8 + i * 0.05, 2) for i in range(5)])  # 0.8..1.0 paso 0.05
    handles = [Patch(facecolor="green", alpha=0.4,
                     label=f"human zone (acc \u2265 {acc_plausible:.2f}, "
                           f"safety \u2265 {human_safety:.3f})")]
    for c in sorted({cat(m) for m in pts}):
        handles.append(Patch(color=CAT_COLOR[c], label=c))
    ax.legend(handles=handles, loc="lower right", fontsize=8)

    plt.tight_layout()
    plt.savefig(IMG / "harmful_vs_accuracy.png", dpi=150)
    plt.close(fig)
    print(f"  {IMG.relative_to(ROOT) / 'harmful_vs_accuracy.png'}")


if __name__ == "__main__":
    main()
