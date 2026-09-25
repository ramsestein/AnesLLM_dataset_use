# -*- coding: utf-8 -*-
"""Análisis y reporte del subgrupo no-opioide con el prompt de 3 opciones.

Consolida las evaluaciones dedicadas (results/data_results/<modelo>_noopioid/,
13 modelos: 11 LLM + laya + jev) junto con los baselines deterministas
(rules, pid, clads, fuzzy, que ya evalúan solo el subgrupo).

Genera:
- results/analysis/no_opioid_subgroup.csv   (strict / consensus / plausible / harmful)
- results/analysis/no_opioid_red_flags.csv  (tasas por red flag)
- results/analysis/no_opioid_report.md
- results/img/subgroup_*.png                (ranking y scatter, sin classifiers)

Uso:
    python src/analyze_noopioid.py
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import analyze

RESULTS = analyze.RESULTS
DATA_RESULTS = RESULTS / "data_results"
OUT = RESULTS / "analysis"
IMG = RESULTS / "img"

# directorios con la evaluación no-opioide dedicada (prompt de 3 opciones)
NO_OPIOID_DIRS = [
    "deepseek-flash_noopioid",
    "deepseek-v4-pro_noopioid",
    "gemini-3.1-flash-lite_noopioid",
    "gemini-3.1-pro-preview_noopioid",
    "gpt-4o_noopioid",
    "gpt-5.4-mini_noopioid",
    "gpt-5.4_noopioid",
    "gpt-6-sol_noopioid",
    "claude-haiku-4-5-20251001_noopioid",
    "claude-opus-4-8_noopioid",
    "medgemma_27b_noopioid",
    "laya_noopioid",
    "jev_noopioid",
]

DETERMINIST_DIRS = ["rules", "pid", "clads", "fuzzy"]

# offsets del scatter (dx, dy) en puntos, relativo al punto del modelo.
# Edita para recolocar etiquetas; (0, 0) = sin desplazar.
SCATTER_OFFSETS = {
    "deepseek-4.1-flash": (0, 18),
    "gpt-6-sol": (12, 14),
    "rules": (0, -16),
    "clads": (-6, 20),
    "deepseek-v4-pro": (-24, -4),
    "gemini-3.1-pro-preview": (18, 0),
    "fuzzy": (0, -16),
    "pid": (-14, 0),
    "gpt-5.4": (16, 4),
    "haiku-4.5": (0, 14),
    "opus-4.8": (0, -14),
    "gpt-4o": (0, -14),
    "gpt-5.4-mini": (16, 0),
    "medgemma:27b": (0, -14),
    "gemini-3.1-flash-lite": (0, -14),
    "laya": (0, 14),
    "jev": (0, -14),
}

# techo humano de referencia: aproximación con los valores del análisis general
# (el humano real tenía las 5 opciones, incluyendo opioides, y no es comparable
# en el subgrupo de 3 opciones).
HUMAN_ACC_APPROX = 0.82
HUMAN_SAFETY_APPROX = 0.968


def load_difficulty():
    diff = {}
    manifest = analyze.ROOT / "dataset" / "reports" / "split_manifest.csv"
    if manifest.exists():
        with open(manifest, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                diff[row["case_id"]] = row.get("difficulty", "unknown")
    return diff


def model_name(folder):
    s = folder / "summary.json"
    if s.exists():
        try:
            return json.loads(s.read_text(encoding="utf-8"))["model"]
        except Exception:
            pass
    return folder.name


def load_pred(path):
    """window_id -> predicted_action (solo acciones válidas)."""
    pred = {}
    if not path.exists():
        return pred
    for line in open(path, encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        a = r.get("predicted_action")
        if a in analyze.ACTIONS:
            pred[r["window_id"]] = a
    return pred


def build_gt(ds, difficulty):
    """window_id -> gt, restringido al subgrupo no-opioide."""
    excluded = analyze.OPIOID | analyze.VASO
    gt = {}
    for wid, rec in ds.items():
        out = rec.get("output", {})
        r1 = out.get("result_1") or {}
        raux = out.get("result_aux") or {}
        rr = out.get("result_real")
        if rr in excluded or r1.get("action") in excluded or raux.get("action") in excluded:
            continue
        gt[wid] = {
            "case_id": rec["case_id"],
            "difficulty": difficulty.get(str(rec["case_id"]), "unknown"),
            "result_real": rr,
            "result_1_action": r1.get("action"),
            "result_1_ratio": r1.get("ratio"),
            "result_aux_action": raux.get("action"),
            "result_aux_ratio": raux.get("ratio"),
        }
    return gt


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"  {path.relative_to(analyze.ROOT)} -> {len(rows)} filas")


def _rank_chart(nop, models, metric, ceiling, fname):
    acc = {m: nop["models"][m] for m in models}
    ms = sorted(models, key=lambda m: -acc[m][metric])
    labels = ["human reference zone (full information, 5 options, plausible)"] + [analyze.disp(m) for m in ms]
    values = [ceiling] + [acc[m][metric] for m in ms]
    y = list(range(len(labels)))
    fig, ax = plt.subplots(figsize=(10, 7.5))
    bars = ax.barh(y, values, height=0.6)
    bars[0].set_color(analyze.CAT_COLOR["human"])
    for b, m in zip(bars[1:], ms):
        b.set_color(analyze.color_of(m))
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel(f"Accuracy ({metric}, no-opioid subgroup)")
    ax.set_xlim(0, 1)
    ax.set_title(f"Model ranking by {metric} (no-opioid subgroup)")
    handles = [Patch(color=analyze.CAT_COLOR["human"], label="human reference zone (full information, 5 options, plausible)")]
    for c in sorted({analyze.cat(m) for m in models}):
        handles.append(Patch(color=analyze.CAT_COLOR[c], label=c))
    ax.legend(handles=handles, loc="lower right", fontsize=8)
    plt.tight_layout()
    plt.savefig(IMG / fname, dpi=150)
    plt.close(fig)
    print(f"  {IMG.relative_to(analyze.ROOT) / fname}")


def _scatter(nop, hflag, models):
    """Accuracy vs safety para el subgrupo, SIN classifiers (laya/jev).

    Eje X = accuracy vs result_1 (consensus). El techo humano se aproxima con los
    valores del análisis general (acc 0.82, safety 0.968).
    """
    acc = {m: nop["models"][m] for m in models}
    pts = [(m, acc[m]["consensus"], hflag[m]) for m in models]
    ys = [1 - p[2] for p in pts]
    acc_ceiling = HUMAN_ACC_APPROX
    safety_ceiling = HUMAN_SAFETY_APPROX
    xmax = min(1.0, acc_ceiling + 0.08)

    # jitter vertical para puntos apilados
    seen = {}
    plot_pts = []
    for (m, x, _), yv in zip(pts, ys):
        k = seen.get(round(yv, 2), 0)
        seen[round(yv, 2)] = k + 1
        plot_pts.append((m, x, yv - k * 0.003))

    fig, ax = plt.subplots(figsize=(16, 8))
    for m, x, y in sorted(plot_pts, key=lambda t: -t[2]):
        ox, oy = SCATTER_OFFSETS.get(analyze.disp(m), (0, 0))
        ax.scatter(x, y, s=90, color=analyze.color_of(m))
        ax.annotate(analyze.disp(m), (x, y), fontsize=8,
                    textcoords="offset points", xytext=(ox, oy))

    ax.add_patch(Rectangle((acc_ceiling, safety_ceiling),
                           xmax - acc_ceiling, 1.02 - safety_ceiling,
                           color="green", alpha=0.16, zorder=0))
    ax.axhline(safety_ceiling, color="green", linestyle="--", linewidth=1, alpha=0.35)
    ax.axvline(acc_ceiling, color="green", linestyle="--", linewidth=1, alpha=0.35)

    ax.set_xlabel("Accuracy vs result_1 (consensus) \u2014 no-opioid subgroup")
    ax.set_ylabel("1 \u2212 harmful action rate (red flags, higher = better)")
    ax.set_title("Accuracy vs safety (red flags, no-opioid subgroup)")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.55, 1.02)
    ax.set_xticks([round(i * 0.1, 2) for i in range(11)])
    ax.set_yticks([0.6, 0.7, 0.8, 0.9, 1.0])
    handles = [Patch(facecolor="green", alpha=0.4,
                     label=f"human zone (acc \u2265 {acc_ceiling:.2f}, "
                           f"safety \u2265 {safety_ceiling:.3f})")]
    for c in sorted({analyze.cat(m) for m in models}):
        handles.append(Patch(color=analyze.CAT_COLOR[c], label=c))
    ax.legend(handles=handles, loc="lower right", fontsize=8)

    plt.tight_layout()
    plt.savefig(IMG / "subgroup_harmful_vs_accuracy.png", dpi=150)
    plt.close(fig)
    print(f"  {IMG.relative_to(analyze.ROOT) / 'subgroup_harmful_vs_accuracy.png'}")


def write_report(nop, hflag, models, floors, ds):
    lines = []
    lines.append("# AnesLLM No-opioid Subgroup Analysis (3-option prompt)")
    lines.append("")
    lines.append(f"- Windows: **{nop['n']}**")
    lines.append(f"- Human ceiling (approx general): accuracy {HUMAN_ACC_APPROX:.2f} · "
                 f"safety {HUMAN_SAFETY_APPROX:.3f}")
    lines.append(f"- Class distribution: {nop['class_distribution']}")
    lines.append("")
    lines.append("## 1. Accuracy")
    lines.append("")
    lines.append("| model | strict | consensus | plausible | harmful rate |")
    lines.append("|---|---|---|---|---|")
    for m in sorted(models, key=lambda m: -nop["models"][m]["consensus"]):
        v = nop["models"][m]
        lines.append(f"| {analyze.disp(m)} | {v['strict']:.3f} | {v['consensus']:.3f} | "
                     f"{v['plausibility']:.3f} | {hflag[m]:.3f} |")
    lines.append(f"| *always no_action (floor)* | {floors['floor_always_no_action']:.3f} | \u2014 | \u2014 | 0.000 |")
    lines.append(f"| *previous action (floor)* | {floors['floor_previous_action']:.3f} | \u2014 | \u2014 | 0.000 |")
    lines.append(f"| *random expected (floor)* | {floors['floor_random_expected']:.3f} | \u2014 | \u2014 | 0.000 |")
    lines.append("")
    lines.append("## 2. Red flags (harmful action rate)")
    lines.append("")
    lines.append("| model | harmful rate |")
    lines.append("|---|---|")
    for m in sorted(models, key=lambda m: hflag[m]):
        lines.append(f"| {analyze.disp(m)} | {hflag[m]:.3f} |")
    lines.append("")
    (OUT / "no_opioid_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"  {OUT.relative_to(analyze.ROOT) / 'no_opioid_report.md'}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    IMG.mkdir(parents=True, exist_ok=True)

    ds = analyze.load_dataset()
    difficulty = load_difficulty()
    gt = build_gt(ds, difficulty)

    models = []
    pred = {}
    for d in NO_OPIOID_DIRS + DETERMINIST_DIRS:
        folder = DATA_RESULTS / d
        m = model_name(folder)
        models.append(m)
        pred[m] = load_pred(folder / "test.jsonl")

    print(f"{len(models)} modelos, {len(gt)} ventanas no-opioide")

    nop = analyze.no_opioid_subgroup(models, pred, gt)
    hflag = analyze.subgroup_red_flag_rate(models, pred, gt, ds, nop["wids"])
    human_safety = analyze.subgroup_human_safety(gt, ds, nop["wids"])
    floors = analyze.ceilings_and_floors(gt, ds)

    # CSVs
    rows = [{"model": m, "strict": round(nop["models"][m]["strict"], 4),
             "consensus": round(nop["models"][m]["consensus"], 4),
             "plausibility": round(nop["models"][m]["plausibility"], 4),
             "harmful_rate": round(hflag[m], 4)} for m in models]
    rows += [
        {"model": "floor_always_no_action",
         "strict": round(floors["floor_always_no_action"], 4),
         "consensus": "", "plausibility": "", "harmful_rate": 0.0},
        {"model": "floor_previous_action",
         "strict": round(floors["floor_previous_action"], 4),
         "consensus": "", "plausibility": "", "harmful_rate": 0.0},
        {"model": "floor_random_expected",
         "strict": round(floors["floor_random_expected"], 4),
         "consensus": "", "plausibility": "", "harmful_rate": 0.0},
    ]
    write_csv(OUT / "no_opioid_subgroup.csv", rows,
              ["model", "strict", "consensus", "plausibility", "harmful_rate"])
    write_csv(OUT / "no_opioid_subgroup_meta.csv",
              [{"n_windows": nop["n"],
                "human_consensus": round(nop["human_consensus"], 4),
                "human_plausible": round(nop["human_plausible"], 4),
                "human_safety": round(human_safety, 4),
                "class_distribution": json.dumps(nop["class_distribution"])}],
              ["n_windows", "human_consensus", "human_plausible",
               "human_safety", "class_distribution"])

    # gráficas: ranking por consensus + scatter con todos los modelos
    _rank_chart(nop, models, "consensus", nop["human_consensus"],
                "subgroup_ranking_consensus.png")
    scatter_models = models
    _scatter(nop, hflag, scatter_models)

    write_report(nop, hflag, models, floors, ds)
    print("análisis no-opioide completo en", OUT)


if __name__ == "__main__":
    main()
