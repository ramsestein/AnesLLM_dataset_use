# -*- coding: utf-8 -*-
"""Verifica empíricamente si cada modelo razona (usa tokens de "thinking").

Lanza N llamadas por modelo con un prompt corto y mira los tokens de razonamiento
que devuelve cada API en su respuesta:
- OpenAI / DeepSeek: usage.completion_tokens_details.reasoning_tokens
- Gemini:            usageMetadata.thoughtsTokenCount
- Claude:            content con thinking

Uso:
    python src/verify_reasoning.py [--n 10]
"""

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PROMPT = ("You are an anesthesiologist in a surgical case. Choose the single best "
          "next adjustment:\na) increase_hypnotic\nb) reduce_hypnotic\nc) no_action\n"
          "Respond with exactly one letter.")


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def http_post_json(url, headers, payload, timeout=180):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


# --- modelos: (name, base_url, key_env, kind) ---
MODELS = [
    ("gpt-4o", "https://api.openai.com/v1", "OPENAI_API_KEY", "openai"),
    ("gpt-5.4-mini", "https://api.openai.com/v1", "OPENAI_API_KEY", "openai"),
    ("gpt-5.4", "https://api.openai.com/v1", "OPENAI_API_KEY", "openai"),
    ("gpt-6-sol", "https://api.openai.com/v1", "OPENAI_API_KEY", "openai"),
    ("deepseek-flash", "https://api.deepseek.com", "DEEPSEEK_API_KEY", "openai"),
    ("deepseek-v4-pro", "https://api.deepseek.com", "DEEPSEEK_API_KEY", "openai"),
    ("gemini-3.1-flash-lite", None, "GEMINI_API_KEY", "gemini"),
    ("gemini-3.1-pro-preview", None, "GEMINI_API_KEY", "gemini"),
]


def openai_reasoning(r):
    """Devuelve (reasoning_tokens, total_completion_tokens) o (None, None)."""
    try:
        usage = r["usage"]
        det = usage.get("completion_tokens_details") or {}
        rt = det.get("reasoning_tokens")
        total = usage.get("completion_tokens")
        return rt, total
    except (KeyError, TypeError):
        return None, None


def gemini_thoughts(r):
    try:
        um = r.get("usageMetadata") or {}
        return um.get("thoughtsTokenCount"), um.get("candidatesTokenCount")
    except (KeyError, TypeError):
        return None, None


def call_openai(model, base_url, key_env):
    key = os.environ.get(key_env)
    if not key:
        raise RuntimeError(f"missing {key_env}")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    payload = {"model": model, "messages": [{"role": "user", "content": PROMPT}],
               "max_completion_tokens": 1024}
    r = http_post_json(base_url + "/chat/completions", headers, payload)
    return openai_reasoning(r), r


def call_gemini(model, key_env):
    key = os.environ.get(key_env)
    if not key:
        raise RuntimeError(f"missing {key_env}")
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={key}")
    r = http_post_json(url, {"Content-Type": "application/json"},
                       {"contents": [{"parts": [{"text": PROMPT}]}],
                        "generationConfig": {"maxOutputTokens": 1024}})
    return gemini_thoughts(r), r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10, help="llamadas por modelo")
    args = ap.parse_args()
    load_env()

    print(f"{'model':28s} {'n':>3s} {'reasoning_ok':>13s} {'avg_reason':>11s} {'avg_total':>10s}  conclusion")
    print("-" * 90)
    for model, base_url, key_env, kind in MODELS:
        counts = []
        totals = []
        errs = 0
        for _ in range(args.n):
            try:
                if kind == "openai":
                    (rt, tot), _ = call_openai(model, base_url, key_env)
                else:
                    (rt, tot), _ = call_gemini(model, key_env)
                if rt is not None:
                    counts.append(rt)
                if tot is not None:
                    totals.append(tot)
            except Exception as e:
                errs += 1
        n_ok = len(counts)
        avg_r = sum(counts) / n_ok if n_ok else None
        avg_t = sum(totals) / len(totals) if totals else None
        if errs:
            conclusion = f"ERRORS={errs}"
        elif n_ok == 0:
            conclusion = "no reasoning field (does not reason)"
        elif avg_r == 0:
            conclusion = "reasoning field present but 0 -> no reasoning"
        else:
            conclusion = "REASONS"
        rs = f"{avg_r:.1f}" if avg_r is not None else "—"
        ts = f"{avg_t:.1f}" if avg_t is not None else "—"
        print(f"{model:28s} {args.n:3d} {n_ok:13d} {rs:>11s} {ts:>10s}  {conclusion}")


if __name__ == "__main__":
    main()
