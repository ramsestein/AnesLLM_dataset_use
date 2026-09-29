# -*- coding: utf-8 -*-
"""Perfil de edad del dataset: rango, media ± SD y casos pediátricos (<18) por partición.

La edad es un atributo de caso (campo `input.pt_age`, constante en todas las ventanas
del caso). Lee `dataset/data/{train,dev,test}/case*.jsonl` y escribe
`dataset/reports/age_profile.csv` con el resumen por partición y global.
"""
import csv
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "dataset" / "data"
OUT = ROOT / "dataset" / "reports"

PEDIATRIC_THRESHOLD = 18  # edad < 18 años


def case_age(path):
    """Devuelve la edad del caso leyendo la primera ventana del fichero."""
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            return (r.get("input") or {}).get("pt_age")
    return None


def summarize(split, files):
    ages = []
    missing = 0
    for f in files:
        a = case_age(f)
        if a is None:
            missing += 1
        else:
            ages.append(float(a))
    n = len(files)
    pediatric = sum(1 for a in ages if a < PEDIATRIC_THRESHOLD)
    return {
        "split": split,
        "n_cases": n,
        "age_missing": missing,
        "age_min": round(min(ages), 1) if ages else None,
        "age_median": round(statistics.median(ages), 1) if ages else None,
        "age_max": round(max(ages), 1) if ages else None,
        "age_mean": round(statistics.mean(ages), 1) if ages else None,
        "age_sd": round(statistics.stdev(ages), 1) if len(ages) > 1 else None,
        "pediatric_cases_lt18": pediatric,
        "pediatric_pct": round(100 * pediatric / n, 1) if n else None,
    }


def main():
    rows = []
    for split in ("train", "dev", "test"):
        files = sorted((DATA / split).glob("case*.jsonl"))
        rows.append(summarize(split, files))

    all_files = [f for split in ("train", "dev", "test")
                 for f in sorted((DATA / split).glob("case*.jsonl"))]
    overall = summarize("all", all_files)
    rows.append(overall)

    OUT.mkdir(parents=True, exist_ok=True)
    fields = ["split", "n_cases", "age_missing", "age_min", "age_median",
              "age_max", "age_mean", "age_sd", "pediatric_cases_lt18", "pediatric_pct"]
    with open(OUT / "age_profile.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"{OUT / 'age_profile.csv'} -> {len(rows)} filas")
    for r in rows:
        print(f"  {r['split']:5s}: n={r['n_cases']}, "
              f"edad {r['age_min']}–{r['age_max']} "
              f"(mediana {r['age_median']}, media {r['age_mean']} ± {r['age_sd']}), "
              f"pediátricos (<18) = {r['pediatric_cases_lt18']} "
              f"({r['pediatric_pct']}%), sin edad = {r['age_missing']}")


if __name__ == "__main__":
    main()
