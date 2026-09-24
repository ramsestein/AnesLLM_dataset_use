# -*- coding: utf-8 -*-
"""Filtra del análisis las ventanas cuyo ground truth incluye "vasopressor".

Regla: si `result_1`, `result_aux` o `result_real` es "vasopressor", la pregunta no
es respondible por los modelos (solo emiten a-e) y se elimina de los CSVs.

Uso:
    python src/filter_vasopressor.py
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS = ROOT / "results"

VASO_FIELDS = ["result_1_action", "result_aux_action", "result_real"]


def filter_csv(path):
    """Elimina filas con vasopressor en alguno de los campos de ground truth."""
    with open(path, encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        return 0, 0, set()

    kept, removed_ids = [], set()
    for r in rows:
        if any(r.get(f) == "vasopressor" for f in VASO_FIELDS):
            removed_ids.add(r.get("window_id"))
            continue
        kept.append(r)

    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(kept)
    return len(rows) - len(kept), len(rows), removed_ids


def main():
    total_removed = set()
    for name in ["test_all.csv", "consistency_all.csv"]:
        p = RESULTS / name
        if not p.exists():
            print(f"{name}: no existe")
            continue
        removed, total, ids = filter_csv(p)
        total_removed |= ids
        print(f"{name}: {removed} filas eliminadas de {total} (quedan {total - removed})")

    audit = RESULTS / "excluded_vasopressor_windows.csv"
    with open(audit, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["window_id"])
        for wid in sorted(total_removed):
            w.writerow([wid])
    print(f"{audit.name}: {len(total_removed)} ventanas excluidas")


if __name__ == "__main__":
    main()
