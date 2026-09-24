# -*- coding: utf-8 -*-
"""Lanza la evaluación completa: todos los casos de test, sin repeticiones.

Uso (después de que termine el batch de consistencia):
    python src/run_full.py

Resultados en results/<modelo>/test.jsonl + summary.json y logs en results/logs/.
"""
import re
import subprocess
import sys
from pathlib import Path

from run_consistency import MODELS, ROOT, sanitize

PY = sys.executable  # mismo intérprete
SPLIT = "test"


def main():
    logs = ROOT / "results" / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    procs = []
    for model, backend, workers in MODELS:
        cmd = [
            PY, str(ROOT / "src" / "eval.py"),
            "--model", model,
            "--backend", backend,
            "--split", SPLIT,
            "--repeats", "1",          # sin repeticiones
            "--workers", str(workers),
            "--resume",
        ]
        log = logs / f"{sanitize(model)}_full.log"
        fh = open(log, "a", encoding="utf-8")
        fh.write(f"\n===== FULL run {model} ({backend}, workers={workers}) =====\n")
        fh.flush()
        p = subprocess.Popen(cmd, stdout=fh, stderr=subprocess.STDOUT)
        procs.append((model, p, fh))
        print(f"[lanzado] {model:32s} {backend:9s} workers={workers}")

    print(f"\n{len(procs)} procesos en paralelo (todos los casos, sin repeticiones).\n")

    for model, p, fh in procs:
        rc = p.wait()
        fh.close()
        mark = "OK" if rc == 0 else f"exit {rc}"
        print(f"[fin] {model:32s} -> {mark}")

    print("\nTodos terminaron. Resultados en results/<modelo>/ y logs en results/logs/.")


if __name__ == "__main__":
    main()
