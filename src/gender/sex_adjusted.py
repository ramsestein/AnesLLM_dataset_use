# -*- coding: utf-8 -*-
"""Modelo ajustado por sexo (GEE) — oportunidad vs. comportamiento, sin coste de API.

Para cada sistema (modelos no deterministas + anestesiólogo) se ajusta una regresión
logística con ecuaciones de estimación generalizadas (GEE), agrupada por caso, con
estructura de correlación de trabajo intercambiable y errores estándar robustos:

  - Acción contraindicada (cualquier red flag):
        sexo + PAM + BIS + FC + edad + ASA + tipo de cirugía
  - Acción contraindicada + antropometría (mismo modelo + peso y talla)
  - Acierto de consenso (predicción == result_1):
        sexo + PAM + BIS + FC + edad + ASA + tipo de cirugía + peso + talla

Si el efecto del sexo desaparece al ajustar por la fisiología de la ventana, apoya
la explicación de "oportunidad" (las mujeres simplemente presentan más a menudo la
condición), en lugar de un comportamiento distinto del sistema.

Salidas en results/analysis/:
  sex_adjusted_contra.csv     efecto del sexo sobre acción contraindicada
  sex_adjusted_consensus.csv  efecto del sexo sobre acierto de consenso
  sex_adjusted_full.csv       coeficientes de todos los términos
  sex_adjusted.md             resumen legible
"""
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import norm
from statsmodels.genmod.cov_struct import Exchangeable, Independence

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
OUT = RESULTS / "analysis"

HUMAN_LABEL = "anesthesiologist"

# Agrupación de pt_opname en "tipo de cirugía" (reglas por palabra clave, en orden).
# Los recuentos por categoría se imprimen en sex_adjusted.md para su verificación.
SURGERY_RULES = [
    ("Transplantation", ("transplant", "donor")),
    ("Thyroid", ("thyroid", "parathyroid")),
    ("Biliary/Pancreas", ("cholecyst", "pancreatect")),
    ("Hepatic", ("hepatect", "segmentect")),
    ("Stomach", ("gastrect", "ivor")),
    ("Breast", ("mastect", "breast")),
    ("Major resection", ("lobect", "pneumonect", "bilobect")),
    ("Minor resection", ("sgmentect", "wedge", "metastasect", "mediastinal")),
    ("Vascular", ("ligation", "fistula", "aneurysm")),
    ("Colorectal", ("anterior resection", "colect", "cecect", "colost",
                    "hartmann", "ileost", "appendect", "hemicolect",
                    "exploratory laparotomy")),
]


def surgery_type(opname):
    o = (opname or "").lower()
    for cat, kws in SURGERY_RULES:
        if any(k in o for k in kws):
            return cat
    return "Others"


def clean_phys(v):
    """MAP/BIS/FC: los valores <= 0 se tratan como ausentes (sin señal)."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return np.nan
    return v if v > 0 else np.nan


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("cargando datos...")
    test_rows = analyze.load_csv(RESULTS / "test_all.csv")
    ds = analyze.load_dataset()
    gt = analyze.build_ground_truth(test_rows)
    models, pred = analyze.build_predictions(test_rows)
    full_models = [m for m in models if analyze.cat(m) != "determinist"]

    # --- tabla base (una fila por ventana)
    rows = []
    for w, g in gt.items():
        inp = (ds.get(w) or {}).get("input") or {}
        rows.append({
            "window_id": w,
            "case_id": g["case_id"],
            "sex_F": 1 if inp.get("pt_sex") == "F" else 0,
            "map": clean_phys(inp.get("map_current")),
            "bis": clean_phys(inp.get("bis_current")),
            "hr": clean_phys(inp.get("hr_current")),
            "age": inp.get("pt_age"),
            "asa": inp.get("pt_asa"),
            "weight": inp.get("pt_weight"),
            "height": inp.get("pt_height"),
            "surgery": surgery_type(inp.get("pt_opname")),
        })
    df = pd.DataFrame(rows)
    # ASA desconocido -> 2 (moda); fisiología ausente -> complete-case
    df["asa"] = pd.to_numeric(df["asa"], errors="coerce").fillna(2.0)
    df = df.dropna(subset=["map", "bis", "hr", "age", "weight", "height"])
    df = df.reset_index(drop=True)
    print(f"{len(df)} ventanas completas para el modelo (de {len(gt)})")

    # Agrupar categorías de cirugía con <10 casos en "Other/rare" (evita
    # separación en estratos vacíos con eventos raros).
    case_surgery = df.groupby("case_id")["surgery"].first()
    cat_counts = case_surgery.value_counts()
    rare = {c for c, n in cat_counts.items() if n < 10}
    df["surgery"] = df["surgery"].apply(lambda c: "Other/rare" if c in rare else c)

    systems = {m: pred[m] for m in full_models}
    systems[HUMAN_LABEL] = {w: gt[w]["result_real"] for w in gt}

    contra_rows = []
    cons_rows = []
    full_rows = []
    for name, actionmap in systems.items():
        contra = []
        consensus = []
        for _, r in df.iterrows():
            w = r["window_id"]
            a = actionmap.get(w)
            # acción contraindicada (cualquier red flag); inválida -> 0 (no propone)
            if a is not None and any(rule(a, input_of(ds, w)) for rule in analyze.RED_FLAGS.values()):
                contra.append(1)
            else:
                contra.append(0)
            # acierto de consenso
            consensus.append(1 if a == gt[w]["result_1_action"] else 0)
        df["contra"] = contra
        df["consensus"] = consensus

        n_ev = int(df["contra"].sum())
        res_c, n_c = fit_gee(df, "contra", with_body=False)
        res_cb, n_cb = fit_gee(df, "contra", with_body=True)
        res_n, n_n = fit_gee(df, "consensus", with_body=True)
        if res_c is not None:
            contra_rows.append(extract_sex(name, "contraindicated", res_c, n_c,
                                           n_events=n_ev))
            full_rows += extract_full(name, "contraindicated", res_c)
        if res_cb is not None:
            contra_rows.append(extract_sex(name, "contraindicated+anthropometry",
                                           res_cb, n_cb, n_events=n_ev))
            full_rows += extract_full(name, "contraindicated+anthropometry", res_cb)
        if res_n is not None:
            cons_rows.append(extract_sex(name, "consensus", res_n, n_n))
            full_rows += extract_full(name, "consensus", res_n)

    analyze.write_csv(OUT / "sex_adjusted_contra.csv", contra_rows,
                      ["system", "outcome", "n", "n_events", "sex_coef", "sex_or",
                       "sex_se", "sex_z", "sex_p", "unstable", "cov_struct"])
    analyze.write_csv(OUT / "sex_adjusted_consensus.csv", cons_rows,
                      ["system", "outcome", "n", "sex_coef", "sex_or",
                       "sex_se", "sex_z", "sex_p", "cov_struct"])
    analyze.write_csv(OUT / "sex_adjusted_full.csv", full_rows,
                      ["system", "outcome", "term", "coef", "se", "z", "p"])

    write_summary(contra_rows, cons_rows, df)
    print(f"  {OUT.relative_to(ROOT) / 'sex_adjusted.md'}")
    print(f"análisis ajustado por sexo en {OUT.relative_to(ROOT)}")


def input_of(ds, w):
    rec = ds.get(w) or {}
    return rec.get("input") or {}


def fit_gee(df, outcome, with_body):
    """Ajusta GEE logística y devuelve (resultado, n). None si no converge."""
    preds = ["sex_F", "map", "bis", "hr", "age", "asa", "C(surgery)"]
    if with_body:
        preds = preds + ["weight", "height"]
    formula = f"{outcome} ~ " + " + ".join(preds)
    sub = df.dropna(subset=["sex_F", "map", "bis", "hr", "age", "asa",
                            "weight", "height"]).copy()
    sub["surgery"] = sub["surgery"].astype("category")
    for cov in (Exchangeable(), Independence()):
        try:
            model = sm.GEE.from_formula(formula, groups="case_id", data=sub,
                                        family=sm.families.Binomial(), cov_struct=cov)
            res = model.fit(maxiter=100)
            if getattr(res, "converged", True):
                return res, len(sub)
        except Exception:
            continue
    return None, len(sub)


def extract_sex(system, outcome, res, n, n_events=None):
    """Coeficiente del sexo (F vs M) con OR, SE, z y p."""
    coef = res.params["sex_F"]
    se = res.bse["sex_F"]
    z = coef / se if se else None
    p = 2 * (1 - norm.cdf(abs(z))) if z is not None else None
    unstable = int((n_events is not None and n_events < 50)
                   or (abs(coef) > 4) or (se and se > 2))
    row = {
        "system": system, "outcome": outcome, "n": n,
        "sex_coef": round(coef, 4),
        "sex_or": round(float(np.exp(coef)), 3),
        "sex_se": round(se, 4),
        "sex_z": round(float(z), 3) if z is not None else None,
        "sex_p": round(float(p), 4) if p is not None else None,
        "cov_struct": getattr(res, "cov_type", ""),
    }
    if n_events is not None:
        row["n_events"] = n_events
        row["unstable"] = unstable
    return row


def extract_full(system, outcome, res):
    rows = []
    for term in res.params.index:
        rows.append({"system": system, "outcome": outcome, "term": term,
                     "coef": round(float(res.params[term]), 5),
                     "se": round(float(res.bse[term]), 5),
                     "z": round(float(res.params[term] / res.bse[term]), 3)
                     if res.bse[term] else None,
                     "p": round(float(2 * (1 - norm.cdf(
                         abs(res.params[term] / res.bse[term])))), 5)
                     if res.bse[term] else None})
    return rows


def write_summary(contra_rows, cons_rows, df):
    lines = []
    lines.append("# Sex-adjusted models (GEE, case-clustered) — AnesLLM")
    lines.append("")
    lines.append("Logistic GEE (exchangeable working correlation, robust SE), clustered by "
                 "case. Sex effect is female vs male (`sex_F`). Outcome 1: any contraindicated "
                 "action (red flag). Outcome 2: consensus accuracy (prediction = `result_1`). "
                 "Predictors as described in `src/sex_adjusted.py`; ASA unknown imputed to 2; "
                 "MAP/BIS/HR values ≤ 0 treated as missing (complete-case). Surgery categories "
                 "with < 10 cases are merged into `Other/rare` to avoid separation.")
    lines.append("")
    lines.append(f"Complete-case windows: {len(df)}.")
    lines.append("")

    contra_plain = [r for r in contra_rows if r["outcome"] == "contraindicated"]
    contra_body = [r for r in contra_rows if r["outcome"] == "contraindicated+anthropometry"]

    lines.append("## 1. Contraindicated action: sex effect (adjusted)")
    lines.append("")
    lines.append("| system | n | events | sex OR (F vs M) | 95 % CI | p |")
    lines.append("|---|---|---|---|---|---|")
    for r in contra_plain:
        lo, hi = or_ci(r)
        flag = " *" if r.get("unstable") else ""
        lines.append(f"| {analyze.disp(r['system'])}{flag} | {r['n']} | {r.get('n_events', '')} | "
                     f"{r['sex_or']} | [{lo}, {hi}] | {r['sex_p']} |")
    lines.append("")
    lines.append("* marked rows: few contraindicated events (< 50) or extreme coefficients — "
                 "estimates are unstable; read alongside the opportunity/behavior analysis "
                 "(`sex_opportunity.md`).")
    lines.append("")

    lines.append("## 2. Contraindicated action + anthropometry: sex effect")
    lines.append("")
    lines.append("Same as §1 plus weight and height. If the sex effect shrinks here, "
                 "anthropometry is the likely channel.")
    lines.append("")
    lines.append("| system | n | events | sex OR (F vs M) | 95 % CI | p |")
    lines.append("|---|---|---|---|---|---|")
    for r in contra_body:
        lo, hi = or_ci(r)
        flag = " *" if r.get("unstable") else ""
        lines.append(f"| {analyze.disp(r['system'])}{flag} | {r['n']} | {r.get('n_events', '')} | "
                     f"{r['sex_or']} | [{lo}, {hi}] | {r['sex_p']} |")
    lines.append("")

    lines.append("## 3. Consensus accuracy: sex effect (adjusted)")
    lines.append("")
    lines.append("| system | n | sex OR (F vs M) | 95 % CI | p |")
    lines.append("|---|---|---|---|---|")
    for r in cons_rows:
        lo, hi = or_ci(r)
        lines.append(f"| {analyze.disp(r['system'])} | {r['n']} | {r['sex_or']} | "
                     f"[{lo}, {hi}] | {r['sex_p']} |")
    lines.append("")

    lines.append("## 4. Surgery type (keyword grouping, for reference)")
    lines.append("")
    counts = df.groupby("case_id")["surgery"].first().value_counts()
    lines.append("| surgery type | cases |")
    lines.append("|---|---|")
    for cat, n in counts.items():
        lines.append(f"| {cat} | {n} |")
    lines.append("")

    (OUT / "sex_adjusted.md").write_text("\n".join(lines), encoding="utf-8")


def or_ci(r):
    if r["sex_se"] is None or r["sex_coef"] is None:
        return "—", "—"
    lo = round(float(np.exp(r["sex_coef"] - 1.96 * r["sex_se"])), 3)
    hi = round(float(np.exp(r["sex_coef"] + 1.96 * r["sex_se"])), 3)
    return lo, hi


if __name__ == "__main__":
    main()
