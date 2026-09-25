# -*- coding: utf-8 -*-
"""Lanza la evaluación del subgrupo no-opioide (1 repetición) para todos los modelos.

- 11 LLMs  -> src/llm/eval.py --no-opioid  (prompt_no_opioid.txt, 3 opciones a-c)
- laya/jev -> src/classification/eval.py --no-opioid

Resultados en results/data_results/<modelo>_noopioid/ y logs en results/logs/.

Uso:
    python src/run_noopioid.py
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable  # mismo intérprete (para laya, usar el Python del sistema con GPU)

# (model, backend, workers)
LLM_MODELS = [
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
    ("medgemma:27b", "ollama", 4),
]

# (model, workers)
CLASSIFIERS = [
    ("laya", 1),
    ("jev", 8),
]


def sanitize(name):
    return re.sub(r'[<>:"/\\|?*]', "_", name)


def main():
    logs = ROOT / "results" / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    procs = []

    for model, backend, workers in LLM_MODELS:
        cmd = [
            PY, str(ROOT / "src" / "llm" / "eval.py"),
            "--model", model,
            "--backend", backend,
            "--split", "test",
            "--repeats", "1",
            "--workers", str(workers),
            "--no-opioid",
            "--resume",
        ]
        log = logs / f"{sanitize(model)}_noopioid.log"
        fh = open(log, "a", encoding="utf-8")
        fh.write(f"\n===== NO-OPIOID run {model} ({backend}, workers={workers}) =====\n")
        fh.flush()
        p = subprocess.Popen(cmd, stdout=fh, stderr=subprocess.STDOUT)
        procs.append((model, p, fh))
        print(f"[lanzado] {model:32s} llm        workers={workers}")

    for model, workers in CLASSIFIERS:
        cmd = [
            PY, str(ROOT / "src" / "classification" / "eval.py"),
            "--model", model,
            "--split", "test",
            "--repeats", "1",
            "--workers", str(workers),
            "--no-opioid",
            "--resume",
        ]
        log = logs / f"{sanitize(model)}_noopioid.log"
        fh = open(log, "a", encoding="utf-8")
        fh.write(f"\n===== NO-OPIOID run {model} (classifier, workers={workers}) =====\n")
        fh.flush()
        p = subprocess.Popen(cmd, stdout=fh, stderr=subprocess.STDOUT)
        procs.append((model, p, fh))
        print(f"[lanzado] {model:32s} classifier workers={workers}")

    print(f"\n{len(procs)} procesos en paralelo (subgrupo no-opioide, 1 repetición).\n")

    for model, p, fh in procs:
        rc = p.wait()
        fh.close()
        mark = "OK" if rc == 0 else f"exit {rc}"
        print(f"[fin] {model:32s} -> {mark}")

    print("\nTerminado. Resultados en results/data_results/<modelo>_noopioid/")


if __name__ == "__main__":
    main()
