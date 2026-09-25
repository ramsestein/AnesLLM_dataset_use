# -*- coding: utf-8 -*-
"""Lanza las evaluaciones de consistencia de todos los modelos en paralelo.

Cada modelo se evalúa con: --limit 100 --repeats 3 --seed 42 --split test --resume.
Los resultados van a results/<modelo>_repeats3/ y el log a results/logs/.

Uso:
    python src/run_consistency.py
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PY = sys.executable  # mismo intérprete

LIMIT = 100
REPEATS = 3
SEED = 42
SPLIT = "test"

# (model, backend, workers)
MODELS = [
    # --- API ---
    ("deepseek-flash", "deepseek", 8),
    ("deepseek-v4-pro", "deepseek", 8),
    ("gemini-3.1-flash-lite", "gemini", 8),
    ("gemini-3.1-pro-preview", "gemini", 8),
    ("gpt-4o", "openai", 8),
    ("gpt-5.4-mini", "openai", 8),
    ("gpt-5.4", "openai", 8),
    ("gpt-6-sol", "openai", 8),
    ("claude-haiku-4-5-20251001", "claude", 8),
    ("claude-opus-4-8", "claude", 8),
    # --- ollama local ---
    ("medgemma:27b", "ollama", 4),
]


def sanitize(name):
    return re.sub(r'[<>:"/\\|?*]', "_", name)


def main():
    logs = ROOT / "results" / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    procs = []
    for model, backend, workers in MODELS:
        cmd = [
            PY, str(ROOT / "src" / "llm" / "eval.py"),
            "--model", model,
            "--backend", backend,
            "--split", SPLIT,
            "--limit", str(LIMIT),
            "--repeats", str(REPEATS),
            "--seed", str(SEED),
            "--workers", str(workers),
            "--resume",
        ]
        log = logs / f"{sanitize(model)}_repeats{REPEATS}.log"
        fh = open(log, "a", encoding="utf-8")
        fh.write(f"\n===== run {model} ({backend}, workers={workers}) =====\n")
        fh.flush()
        p = subprocess.Popen(cmd, stdout=fh, stderr=subprocess.STDOUT)
        procs.append((model, backend, workers, p, fh))
        print(f"[lanzado] {model:32s} {backend:9s} workers={workers}")

    print(f"\n{len(procs)} procesos en paralelo. Esperando a que terminen...\n")

    for model, backend, workers, p, fh in procs:
        rc = p.wait()
        fh.close()
        mark = "OK" if rc == 0 else f"exit {rc}"
        print(f"[fin] {model:32s} -> {mark}")

    print("\nTodos terminaron. Resultados en results/<modelo>_repeats3/ y logs en results/logs/.")


if __name__ == "__main__":
    main()
