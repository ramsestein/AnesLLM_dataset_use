# -*- coding: utf-8 -*-
"""Lanza la ejecución del contrafactual de sexo (análisis 3) en paralelo.

Cada modelo se ejecuta con: --models <model> --workers 8 --resume.
Los resultados van a results/sex_cf/raw_<modelo>.jsonl y el log a results/logs/.

Uso:
    python src/run_sex_counterfactual.py
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable  # mismo intérprete

WORKERS = 64

MODELS = [
    "claude-opus-5-5",
    "gpt-6-sol",
    "gemini-3.1-pro-preview",
    "deepseek-v4-pro",
    "deepseek-flash",
]


def sanitize(name):
    return re.sub(r'[<>:"/\\|?*]', "_", name)


def main():
    logs = ROOT / "results" / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    procs = []
    for model in MODELS:
        cmd = [
            PY, str(ROOT / "src" / "gender" / "sex_counterfactual.py"),
            "--models", model,
            "--workers", str(WORKERS),
            "--resume",
        ]
        log = logs / f"sexcf_{sanitize(model)}.log"
        fh = open(log, "a", encoding="utf-8")
        fh.write(f"\n===== sex_counterfactual run {model} (workers={WORKERS}) =====\n")
        fh.flush()
        p = subprocess.Popen(cmd, stdout=fh, stderr=subprocess.STDOUT)
        procs.append((model, p, fh))
        print(f"[lanzado] {model:32s} workers={WORKERS}", flush=True)

    print(f"\n{len(procs)} procesos en paralelo. Esperando a que terminen...\n", flush=True)

    for model, p, fh in procs:
        rc = p.wait()
        fh.close()
        mark = "OK" if rc == 0 else f"exit {rc}"
        print(f"[fin] {model:32s} -> {mark}", flush=True)

    print("\nTodos terminaron. Resultados en results/sex_cf/.", flush=True)


if __name__ == "__main__":
    main()
