# -*- coding: utf-8 -*-
"""Evaluación de modelos de clasificación estructurada sobre el benchmark AnesLLM.

- laya: motor local "System 1" (paquete `laya`, checkpoint convaiinnovations/laya).
- jev:  API hosted "System One" (POST https://thejevai.com/v1/systemone).

Ambos reciben el MISMO caso clínico en prosa (render_case de src/llm/eval.py) y una
pregunta `choice` con las 5 acciones. Los resultados se guardan con el MISMO formato
que src/llm/eval.py (results/data_results/<modelo>/test.jsonl + summary.json y
<modelo>_repeats3/ para auto-consistencia), de modo que consolidate.py y analyze.py
los integran sin cambios.

Uso:
    python src/classification/eval.py --model laya --split test --limit 20
    python src/classification/eval.py --model jev --split test
    python src/classification/eval.py --model laya --split test --repeats 3
"""
import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent  # src/
sys.path.insert(0, str(SRC))
from llm.eval import (render_case, sanitize, LETTER_TO_ACTION,
                      ACTION_TO_LETTER, compute_summary, print_summary)

ROOT = SRC.parent
DATA = ROOT / "dataset" / "data"
MANIFEST = ROOT / "dataset" / "reports" / "split_manifest.csv"

ACTIONS = ["increase_hypnotic", "reduce_hypnotic", "increase_opioid",
           "reduce_opioid", "no_action"]

# subgrupo no-opioide (mismo criterio que src/determinist/common.py)
OPIOID = {"increase_opioid", "reduce_opioid"}
VASO = {"vasopressor"}
EXCLUDED = OPIOID | VASO


def is_no_opioid(rec):
    """True si ninguna referencia (result_real/result_1/result_aux) es opioide ni vasopressor."""
    out = rec.get("output", {})
    r1 = (out.get("result_1") or {}).get("action")
    raux = (out.get("result_aux") or {}).get("action")
    rr = out.get("result_real")
    return not (rr in EXCLUDED or r1 in EXCLUDED or raux in EXCLUDED)


# descripciones cortas de cada opción para el modelo (claves = opciones)
ACTION_DESC = {
    "increase_hypnotic": "deepen anesthesia (raise hypnotic, e.g. more propofol)",
    "reduce_hypnotic": "lighten anesthesia (lower hypnotic, e.g. less propofol)",
    "increase_opioid": "increase analgesia (raise opioid, e.g. more remifentanil)",
    "reduce_opioid": "decrease analgesia (lower opioid, e.g. less remifentanil)",
    "no_action": "no change needed right now",
}


def build_questions():
    return {
        "decision": {
            "type": "choice",
            "instructions": (
                "You are an anesthesiologist in the middle of a real surgical case. "
                "Based ONLY on the patient state below, choose the single best next "
                "anesthetic adjustment."
            ),
            "criteria": dict(ACTION_DESC),
        }
    }


# ---------------------------------------------------------------- laya (local)
_LAYA_AGENT = None


def _get_laya_agent(max_len=1024):
    global _LAYA_AGENT
    if _LAYA_AGENT is None:
        import laya
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _LAYA_AGENT = laya.load("convaiinnovations/laya", device=device)
        print(f"[laya] device={device}")
    # ModernBERT-large admite contexto amplio; por defecto 512 trunca los casos.
    if _LAYA_AGENT.cfg.get("max_len", 512) < max_len:
        _LAYA_AGENT.cfg["max_len"] = max_len
    return _LAYA_AGENT


def _pack(answer):
    return {
        "choice": answer.get("choice"),
        "confidence": answer.get("confidence"),
        "answer_confidence": answer.get("answer_confidence"),
        "probabilities": answer.get("probabilities"),
    }


def _laya_eval(states, args):
    agent = _get_laya_agent(args.max_len)
    q = build_questions()
    out = []
    bs = max(1, args.batch_size)
    for start in range(0, len(states), bs):
        chunk = states[start:start + bs]
        try:
            results = agent.predict_batch(chunk, q, max_len=args.max_len,
                                          batch_size=bs)
            for r in results:
                out.append(_pack(r["answers"]["decision"]))
        except Exception:
            # fallback individual (más lento, tolerante a estados problemáticos)
            for s in chunk:
                try:
                    r = agent.predict(s, q, max_len=args.max_len)
                    out.append(_pack(r["answers"]["decision"]))
                except Exception as e:
                    out.append({"choice": None, "error": True, "message": str(e)})
        if args.sleep:
            time.sleep(args.sleep)
    return out


# ---------------------------------------------------------------- jev (hosted)
JEV_URL = "https://thejevai.com/v1/systemone"


def _http_post_json(url, headers, payload, timeout=180):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _call_jev(state):
    key = os.environ.get("JEV_API_KEY")
    if not key:
        raise RuntimeError("missing JEV_API_KEY")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json",
               "User-Agent": "AnesLLM-benchmark/1.0",
               "Accept": "application/json"}
    payload = {"model": "jev-latest", "state": state, "questions": build_questions()}
    r = _http_post_json(JEV_URL, headers, payload)
    # la API envuelve la respuesta en data.result; la doc muestra answers arriba
    if "answers" in r:
        return r["answers"]["decision"]
    data = r.get("data", {}) or {}
    result = data.get("result", {}) or {}
    if "answers" in result:
        return result["answers"]["decision"]
    raise RuntimeError("jev: respuesta inesperada: " + json.dumps(r)[:200])


def _jev_eval(states, args):
    def run(state):
        if args.sleep:
            time.sleep(args.sleep)
        last = "empty response"
        for _ in range(3):
            try:
                ans = _call_jev(state)
                p = _pack(ans)
                if p["choice"]:
                    return p
                last = "empty choice"
            except Exception as e:
                last = str(e)
            time.sleep(1.0)
        return {"choice": None, "error": True, "message": last}

    if args.workers <= 1:
        return [run(s) for s in states]
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        return list(ex.map(run, states))


BACKENDS = {"laya": _laya_eval, "jev": _jev_eval}


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def load_difficulty():
    diff = {}
    if MANIFEST.exists():
        import csv
        with open(MANIFEST, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                diff[row["case_id"]] = row.get("difficulty", "unknown")
    return diff


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=sorted(BACKENDS))
    ap.add_argument("--split", default="test", choices=["dev", "train", "test"])
    ap.add_argument("--limit", type=int, default=0, help="max windows (0 = all)")
    ap.add_argument("--data-dir", default=str(DATA))
    ap.add_argument("--output", default="")
    ap.add_argument("--sleep", type=float, default=0.0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--max-len", type=int, default=1024,
                    help="laya max context tokens")
    ap.add_argument("--no-opioid", action="store_true",
                    help="restringir al subgrupo sin opioide ni vasopressor")
    args = ap.parse_args()

    load_env()

    data_dir = Path(args.data_dir) / args.split
    if args.output:
        out_dir = Path(args.output)
    else:
        name = sanitize(args.model)
        if args.repeats > 1:
            name += f"_repeats{args.repeats}"
        out_dir = ROOT / "results" / "data_results" / name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{args.split}.jsonl"

    difficulty = load_difficulty()

    existing = {}
    if args.resume and out_file.exists():
        for line in open(out_file, encoding="utf-8"):
            try:
                r = json.loads(line)
                if not r.get("error") and r.get("letter") is not None:
                    existing[r["window_id"]] = r
            except Exception:
                pass

    all_windows = []
    for f in sorted(data_dir.glob("case*.jsonl")):
        for line in open(f, encoding="utf-8"):
            all_windows.append(json.loads(line))

    if args.no_opioid:
        all_windows = [w for w in all_windows if is_no_opioid(w)]

    if args.limit and args.limit < len(all_windows):
        rng = random.Random(args.seed)
        selected = {w["window_id"] for w in rng.sample(all_windows, args.limit)}
        all_windows = [w for w in all_windows if w["window_id"] in selected]

    windows = [w for w in all_windows if w["window_id"] not in existing]

    print(f"model={args.model} split={args.split} windows={len(windows)}")

    # tareas planas: (índice de ventana, estado), repetido --repeats veces
    flat = []
    for i, rec in enumerate(windows):
        state = render_case(rec["input"])
        for _ in range(args.repeats):
            flat.append((i, state))

    results = BACKENDS[args.model]([s for _, s in flat], args)

    window_res = [[] for _ in windows]
    for (i, _), res in zip(flat, results):
        window_res[i].append(res)

    records = []
    for i, rec in enumerate(windows):
        wid = rec["window_id"]
        case_id = rec["case_id"]
        result_real = rec["output"]["result_real"]
        d = difficulty.get(str(case_id), "unknown")
        resps = window_res[i]

        letters = [ACTION_TO_LETTER[r["choice"]] for r in resps
                   if not r.get("error") and r.get("choice") in ACTION_TO_LETTER]
        errs = sum(1 for r in resps if r.get("error"))

        if args.repeats > 1 and letters:
            cnt = Counter(letters)
            majority, _ = cnt.most_common(1)[0]
            consistency = cnt[majority] / len(letters)
        elif args.repeats > 1:
            majority = None
            consistency = None
        else:
            majority = letters[0] if letters else None
            consistency = None

        predicted = LETTER_TO_ACTION.get(majority)
        ok = 1 if predicted == result_real else 0

        rec_out = {
            "window_id": wid, "case_id": case_id, "result_real": result_real,
            "difficulty": d, "letter": majority, "predicted_action": predicted,
            "correct": ok, "error": (errs == len(resps) and len(resps) > 0),
        }
        if args.repeats > 1:
            rec_out["repeats"] = args.repeats
            rec_out["letters"] = letters
            rec_out["consistency"] = round(consistency, 4) if consistency is not None else None
            rec_out["responses"] = [
                {"letter": ACTION_TO_LETTER.get(r.get("choice")),
                 "raw": json.dumps({k: r.get(k) for k in
                                    ("choice", "confidence", "probabilities")},
                                   ensure_ascii=False, default=str),
                 "explanation": "",
                 "error": bool(r.get("error"))}
                for r in resps]
        else:
            first = resps[0] if resps else {}
            rec_out["raw_response"] = json.dumps(
                {k: first.get(k) for k in ("choice", "confidence", "probabilities")},
                ensure_ascii=False, default=str)
            rec_out["explanation"] = ""
        records.append(rec_out)

    merged = list(existing.values()) + records
    with open(out_file, "w", encoding="utf-8") as fh:
        for rec_out in merged:
            fh.write(json.dumps(rec_out, ensure_ascii=False) + "\n")

    summary = compute_summary(merged, args.model, args.model, args.split, args.repeats)
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False,
                                                     indent=2), encoding="utf-8")
    print_summary(summary, out_file, out_dir)


if __name__ == "__main__":
    main()
