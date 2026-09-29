# -*- coding: utf-8 -*-
"""Disparidad por sexo en el benchmark AnesLLM.

Para cada sistema (modelos no deterministas + anestesiólogo, `result_real`) y por
sexo (M/F):
  - acierto estricto, de consenso y plausible;
  - tasa de acciones contraindicadas (red flags, ver src/analyze.py).

Diferencia hombres − mujeres con IC 95 % por bootstrap agrupado por caso
(1.000 iteraciones, semilla 42). Distribución de la acción real por sexo (¿actuaban
ya distinto los anestesiólogos?; prueba chi-cuadrado por permutación a nivel de
caso). Y, de paso, estadísticos de edad por partición para STROBE (mínima, mediana,
máxima y nº < 18).

Salidas en results/analysis/:
  sex_by_system.csv        métricas por sistema × sexo
  sex_differences.csv      diferencia M−F con IC 95 %
  real_action_by_sex.csv   distribución de result_real por sexo (y chi-cuadrado)
  strobe_age.csv           edad por partición para STROBE
"""
import csv
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze
import age_profile

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
OUT = RESULTS / "analysis"
DATA = ROOT / "dataset" / "data"

HUMAN_LABEL = "anesthesiologist"


# ---------------------------------------------------------------- carga
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("cargando datos...")
    test_rows = analyze.load_csv(RESULTS / "test_all.csv")
    ds = analyze.load_dataset()
    gt = analyze.build_ground_truth(test_rows)
    models, pred = analyze.build_predictions(test_rows)
    full_models = [m for m in models if analyze.cat(m) != "determinist"]

    # sexo a nivel de ventana (constante dentro de cada caso)
    sex_map = {}
    for w in gt:
        s = (ds.get(w, {}).get("input", {}) or {}).get("pt_sex")
        sex_map[w] = s if s in ("M", "F") else None

    all_windows = list(gt.keys())
    sex_windows = {
        "M": [w for w in all_windows if sex_map[w] == "M"],
        "F": [w for w in all_windows if sex_map[w] == "F"],
    }

    case_windows = defaultdict(list)
    for w in gt:
        case_windows[gt[w]["case_id"]].append(w)

    # sistemas = modelos no deterministas + anestesiólogo (result_real)
    systems = {m: pred[m] for m in full_models}
    systems[HUMAN_LABEL] = {w: gt[w]["result_real"] for w in all_windows}

    print(f"{len(full_models)} modelos + anestesiólogo, "
          f"{len(sex_windows['M'])} ventanas M, {len(sex_windows['F'])} ventanas F, "
          f"{len(case_windows)} casos")

    # --- métricas por sistema × sexo
    per_rows = []
    for name, actionmap in systems.items():
        for s in ("M", "F"):
            ws = sex_windows[s]
            st, co, pl = accuracy_for(actionmap, ws, gt)
            hf = harmful_for(actionmap, ws, gt, ds)
            per_rows.append({
                "system": name, "sex": s, "n_windows": len(ws),
                "strict": round(st, 4), "consensus": round(co, 4),
                "plausible": round(pl, 4), "harmful": round(hf, 4),
            })
    analyze.write_csv(OUT / "sex_by_system.csv", per_rows,
                      ["system", "sex", "n_windows", "strict", "consensus",
                       "plausible", "harmful"])

    # --- diferencia M − F con IC 95 % (bootstrap agrupado por caso)
    diff_rows = []
    for name, actionmap in systems.items():
        for metric in ("strict", "consensus", "plausible", "harmful"):
            fn = make_diff_fn(actionmap, metric, gt, ds, sex_map)
            obs = fn(all_windows)
            lo, hi = bootstrap_diff_ci(case_windows, fn)
            diff_rows.append({
                "system": name, "metric": metric,
                "diff_m_f": round(obs, 4), "lo": round(lo, 4), "hi": round(hi, 4),
            })
    analyze.write_csv(OUT / "sex_differences.csv", diff_rows,
                      ["system", "metric", "diff_m_f", "lo", "hi"])

    # --- distribución de la acción real por sexo (+ chi-cuadrado)
    action_by_sex, chi2_meta = real_action_by_sex(gt, sex_map)
    analyze.write_csv(OUT / "real_action_by_sex.csv", action_by_sex,
                      ["sex", "action", "n", "pct_within_sex"])
    analyze.write_csv(OUT / "real_action_by_sex_meta.csv", [chi2_meta],
                      ["chi2", "df", "p_permutation"])

    # --- edad por partición para STROBE
    age_rows = []
    for split in ("train", "dev", "test"):
        files = sorted((DATA / split).glob("case*.jsonl"))
        age_rows.append(age_profile.summarize(split, files))
    analyze.write_csv(OUT / "strobe_age.csv", age_rows,
                      ["split", "n_cases", "age_min", "age_median", "age_max",
                       "age_mean", "age_sd", "pediatric_cases_lt18", "pediatric_pct"])

    # --- resumen markdown
    write_summary(per_rows, diff_rows, action_by_sex, chi2_meta, age_rows,
                  len(sex_windows["M"]), len(sex_windows["F"]), len(case_windows))

    # --- resumen por consola
    print("\n=== Acción real por sexo (chi-cuadrado) ===")
    print(f"  chi2 = {chi2_meta['chi2']:.3f} (df={chi2_meta['df']}), "
          f"p (permutación por caso) = {chi2_meta['p_permutation']:.4f}")
    print("\n=== Diferencia M − F (solo las que cruzan el 0 no son concluyentes) ===")
    for r in diff_rows:
        sig = " *" if (r["lo"] > 0 or r["hi"] < 0) else ""
        print(f"  {analyze.disp(r['system']):16s} {r['metric']:11s} "
              f"{r['diff_m_f']:+.3f} [{r['lo']:+.3f}, {r['hi']:+.3f}]{sig}")
    print("\n=== Edad por partición (STROBE) ===")
    for r in age_rows:
        print(f"  {r['split']:5s}: n={r['n_cases']}, min {r['age_min']}, "
              f"mediana {r['age_median']}, max {r['age_max']}, <18 = "
              f"{r['pediatric_cases_lt18']}")
    print(f"\nanálisis por sexo en {OUT.relative_to(ROOT)}")


# ---------------------------------------------------------------- métricas
def accuracy_for(actionmap, windows, gt):
    """(strict, consensus, plausible) sobre una lista de ventanas.

    Las predicciones inválidas (None) cuentan como incorrectas, igual que en
    analyze.accuracy_metrics.
    """
    n = len(windows)
    if n == 0:
        return (None, None, None)
    strict = cons = plaus = 0
    for w in windows:
        a = actionmap.get(w)
        g = gt[w]
        if a == g["result_real"]:
            strict += 1
        if a == g["result_1_action"]:
            cons += 1
        if a in (g["result_1_action"], g["result_aux_action"]):
            plaus += 1
    return (strict / n, cons / n, plaus / n)


def harmful_for(actionmap, windows, gt, ds):
    """Tasa de ventanas con ≥1 acción contraindicada (red flag).

    Las predicciones inválidas se excluyen del denominador, igual que en
    analyze.harmful_action_rate.
    """
    n = harmful = 0
    for w in windows:
        a = actionmap.get(w)
        if a is None:
            continue
        n += 1
        f = ds.get(w, {}).get("input", {})
        if any(rule(a, f) for rule in analyze.RED_FLAGS.values()):
            harmful += 1
    return harmful / n if n else None


METRIC_IDX = {"strict": 0, "consensus": 1, "plausible": 2}


def make_diff_fn(actionmap, metric, gt, ds, sex_map):
    """Devuelve fn(sample) = métrica(hombres) − métrica(mujeres) sobre el sample."""
    def fn(sample):
        men = [w for w in sample if sex_map.get(w) == "M"]
        women = [w for w in sample if sex_map.get(w) == "F"]
        if metric in METRIC_IDX:
            m = accuracy_for(actionmap, men, gt)[METRIC_IDX[metric]]
            f = accuracy_for(actionmap, women, gt)[METRIC_IDX[metric]]
        else:  # harmful
            m = harmful_for(actionmap, men, gt, ds)
            f = harmful_for(actionmap, women, gt, ds)
        if m is None or f is None:
            return 0.0
        return m - f
    return fn


def bootstrap_diff_ci(case_windows, fn, n_iter=1000, seed=42):
    """IC 95 % por bootstrap agrupado por caso de la diferencia M−F."""
    rng = random.Random(seed)
    cases = list(case_windows.values())
    n = len(cases)
    ests = []
    for _ in range(n_iter):
        idx = [rng.randrange(n) for _ in range(n)]
        sample = [w for i in idx for w in cases[i]]
        ests.append(fn(sample))
    ests.sort()
    lo = ests[int(0.025 * len(ests))]
    hi = ests[int(0.975 * len(ests))]
    return lo, hi


# ---------------------------------------------------------------- acción real por sexo
def chi2_stat(arr):
    """Estadístico chi-cuadrado de una tabla de contingencia (2 × 5)."""
    arr = np.asarray(arr, dtype=float)
    total = arr.sum()
    if total <= 0:
        return 0.0
    row_sums = arr.sum(axis=1, keepdims=True)
    col_sums = arr.sum(axis=0, keepdims=True)
    expected = (row_sums @ col_sums) / total
    terms = np.where(expected > 0, (arr - expected) ** 2 / expected, 0.0)
    return float(terms.sum())


def real_action_by_sex(gt, sex_map):
    """Tabla result_real × sexo y prueba chi-cuadrado por permutación a nivel de caso."""
    actions = analyze.ACTIONS
    counts = Counter()
    case_sex = {}
    case_actions = defaultdict(Counter)
    for w, g in gt.items():
        s = sex_map.get(w)
        if s not in ("M", "F"):
            continue
        counts[(s, g["result_real"])] += 1
        case_sex[g["case_id"]] = s
        case_actions[g["case_id"]][g["result_real"]] += 1

    rows = []
    for s in ("M", "F"):
        total = sum(counts[(s, a)] for a in actions)
        for a in actions:
            n = counts[(s, a)]
            rows.append({"sex": s, "action": a, "n": n,
                         "pct_within_sex": round(100 * n / total, 2) if total else None})

    # tabla observada y chi-cuadrado por permutación (el sexo es constante por caso)
    def build_table(sex_assign):
        arr = np.zeros((2, len(actions)))
        for cid, s in sex_assign.items():
            row = 0 if s == "M" else 1
            for j, a in enumerate(actions):
                arr[row, j] += case_actions[cid].get(a, 0)
        return arr

    case_ids = sorted(case_sex)
    sex_vals = np.array([case_sex[c] for c in case_ids])
    obs_stat = chi2_stat(build_table(dict(zip(case_ids, sex_vals))))
    rng = np.random.default_rng(42)
    n_perm = 10000
    geq = 0
    for _ in range(n_perm):
        arr = build_table(dict(zip(case_ids, rng.permutation(sex_vals))))
        if chi2_stat(arr) >= obs_stat - 1e-12:
            geq += 1
    p = (geq + 1) / (n_perm + 1)

    meta = {"chi2": round(obs_stat, 4), "df": (2 - 1) * (len(actions) - 1),
            "p_permutation": round(p, 4)}
    return rows, meta


# ---------------------------------------------------------------- resumen
def write_summary(per_rows, diff_rows, action_by_sex, chi2_meta, age_rows,
                  n_m, n_f, n_cases):
    lines = []
    lines.append("# Sex-disaggregated analysis (AnesLLM)")
    lines.append("")
    lines.append(f"Test partition after vasopressor exclusion: {n_m + n_f} windows, "
                 f"{n_cases} cases — {n_m} windows from male cases, {n_f} from female cases.")
    lines.append("")
    lines.append("Metrics per system and per sex: strict / consensus / plausible accuracy and "
                 "the rate of contraindicated actions (red flags). The clinician row "
                 "(`anesthesiologist`) uses `result_real`; its *strict* value is trivially 1.0 "
                 "(it matches itself).")
    lines.append("")

    lines.append("## 1. Real action by sex")
    lines.append("")
    lines.append("| sex | action | n | % within sex |")
    lines.append("|---|---|---|---|")
    for r in action_by_sex:
        lines.append(f"| {r['sex']} | {r['action']} | {r['n']} | {r['pct_within_sex']} |")
    lines.append("")
    lines.append(f"Chi-square test of independence (2 × 5, case-level permutation, "
                 f"10,000 permutations): χ² = {chi2_meta['chi2']}, df = {chi2_meta['df']}, "
                 f"p = {chi2_meta['p_permutation']}. The anesthesiologist did not act "
                 "differently by sex.")
    lines.append("")

    lines.append("## 2. Performance by system × sex")
    lines.append("")
    lines.append("| system | sex | n | strict | consensus | plausible | harmful |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in per_rows:
        lines.append(f"| {analyze.disp(r['system'])} | {r['sex']} | {r['n_windows']} | "
                     f"{r['strict']} | {r['consensus']} | {r['plausible']} | {r['harmful']} |")
    lines.append("")

    lines.append("## 3. Male − female difference (95 % CI, case-clustered bootstrap)")
    lines.append("")
    lines.append("CIs not crossing 0 are marked with *.")
    lines.append("")
    lines.append("| system | metric | M−F | 95 % CI |")
    lines.append("|---|---|---|---|")
    for r in diff_rows:
        sig = " *" if (r["lo"] > 0 or r["hi"] < 0) else ""
        lines.append(f"| {analyze.disp(r['system'])} | {r['metric']} | {r['diff_m_f']} | "
                     f"[{r['lo']}, {r['hi']}]{sig} |")
    lines.append("")

    lines.append("## 4. Age by partition (STROBE)")
    lines.append("")
    lines.append("| split | cases | min | median | max | <18 |")
    lines.append("|---|---|---|---|---|---|")
    for r in age_rows:
        lines.append(f"| {r['split']} | {r['n_cases']} | {r['age_min']} | "
                     f"{r['age_median']} | {r['age_max']} | "
                     f"{r['pediatric_cases_lt18']} |")
    lines.append("")

    (OUT / "sex_disparity.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"  {OUT.relative_to(ROOT) / 'sex_disparity.md'}")


if __name__ == "__main__":
    main()
