# -*- coding: utf-8 -*-
"""Evaluación de modelos LLM sobre el benchmark AnesLLM.

Cada ventana se presenta como un caso clínico (en inglés) y el modelo debe responder
con una letra a-e correspondiente a una de las 5 acciones. Los resultados se guardan
en results/<model>/<split>.jsonl + results/<model>/summary.json.

Uso:
    python src/eval.py --model llama3.1 --backend ollama --split test [--limit 20]
    python src/eval.py --model gpt-4o --backend openai --split test
    python src/eval.py --model deepseek-chat --backend deepseek --split test
    python src/eval.py --model gemini-2.0-flash --backend gemini --split test
    python src/eval.py --model claude-3-5-sonnet-20241022 --backend claude --split test

Backends: ollama | openai | deepseek | gemini | claude
"""
import argparse
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "dataset" / "data"
PROMPT_PATH = Path(__file__).resolve().parent / "prompt.txt"
MANIFEST = ROOT / "dataset" / "reports" / "split_manifest.csv"

# orden fijo de opciones (a-e). Debe coincidir con el prompt.
ACTIONS = ["increase_hypnotic", "reduce_hypnotic", "increase_opioid",
           "reduce_opioid", "no_action"]
LETTER_TO_ACTION = {chr(ord("a") + i): a for i, a in enumerate(ACTIONS)}
ACTION_TO_LETTER = {a: ch for ch, a in LETTER_TO_ACTION.items()}

KEY_LABS = ["hb", "hct", "plt", "wbc", "na", "k", "gluc", "cr", "lac", "ph", "hco3", "be"]

# topes de salida crecientes: empieza mínimo y sube solo si el modelo no responde
CAPS = (16, 64, 256, 1024)


def parse_letter(text):
    """Extrae la letra (a-e) de una respuesta, tolerando respuestas largas/de razonamiento."""
    if not text:
        return None
    t = text.strip()
    if len(t) == 1 and t.lower() in LETTER_TO_ACTION:
        return t.lower()
    # letra al inicio: "c", "c)", "c -", "c."
    m = re.match(r"^\s*\(?([a-e])\)?\s*(?:[-.:\u2013\u2014]|$)", t, re.IGNORECASE)
    if m:
        return m.group(1).lower()
    # patrones explícitos: "answer: c", "option c", "choose c", ...
    m = (re.search(r"\banswer\b[^a-e]{0,20}\b([a-e])\b", t, re.IGNORECASE)
         or re.search(r"\boption\b[^a-e]{0,20}\b([a-e])\b", t, re.IGNORECASE)
         or re.search(r"\b(?:choose|select|choice|letter)\b[^a-e]{0,20}\b([a-e])\b",
                      t, re.IGNORECASE))
    if m:
        return m.group(1).lower()
    # decisión en negrita al final: "**a**"
    m = re.search(r"\*\*\s*([a-e])\s*\*\*\s*$", t, re.IGNORECASE)
    if m:
        return m.group(1).lower()
    # última letra suelta: los modelos que razonan ponen la respuesta al final
    letters = re.findall(r"\b([a-e])\b", t, re.IGNORECASE)
    if letters:
        return letters[-1].lower()
    return None


def is_clean_letter(text):
    """True si la respuesta es una letra limpia (no razonamiento truncado)."""
    if not text:
        return False
    t = text.strip()
    return bool(re.match(r"^\(?[a-eA-E]\)?(?:\s*[-.:\u2013\u2014]|\s|$)", t))


# ---------------------------------------------------------------- env & HTTP
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


# ---------------------------------------------------------------- backends
def call_ollama(model, prompt):
    url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
    for cap in CAPS:
        payload = {"model": model, "prompt": prompt, "stream": False}
        # los modelos cloud de ollama (ej. gpt-oss:20b-cloud) devuelven vacío con options
        if ":cloud" not in model:
            payload["options"] = {"num_predict": cap, "temperature": 0}
        r = http_post_json(url, {"Content-Type": "application/json"}, payload)
        if parse_letter(r["response"]):
            return r["response"]
    raise RuntimeError("ollama: respuesta sin letra")


def call_openai_compatible(model, prompt, base_url, key_env):
    key = os.environ.get(key_env)
    if not key:
        raise RuntimeError(f"missing env var {key_env}")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    messages = [{"role": "user", "content": prompt}]
    # modelos nuevos usan max_completion_tokens; gpt-6 rechaza temperature 0 y max_tokens
    for cap in CAPS:
        for token_param in ("max_completion_tokens", "max_tokens"):
            for temperature in (0, None):
                payload = {"model": model, "messages": messages, token_param: cap}
                if temperature is not None:
                    payload["temperature"] = temperature
                try:
                    r = http_post_json(base_url + "/chat/completions", headers, payload)
                except urllib.error.HTTPError as e:
                    if e.code == 400:
                        continue
                    raise
                content = r["choices"][0]["message"]["content"] or ""
                if parse_letter(content):
                    return content
    raise RuntimeError("respuesta sin letra en todos los intentos")


def call_gemini(model, prompt):
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("missing GEMINI_API_KEY")
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={key}")
    for cap in CAPS:
        r = http_post_json(url, {"Content-Type": "application/json"},
                           {"contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {"temperature": 0, "maxOutputTokens": cap}})
        try:
            text = r["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError):
            text = ""  # modelo con thinking: se quedó sin presupuesto, subir tope
        if parse_letter(text):
            return text
    raise RuntimeError("gemini: respuesta sin letra")


def call_claude(model, prompt):
    key = os.environ.get("CLAUDE_API_KEY")
    if not key:
        raise RuntimeError("missing CLAUDE_API_KEY")
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01",
               "Content-Type": "application/json"}
    # opus-4-8 rechaza temperature; desactivamos thinking para minimizar output
    last_reasoning = None
    for cap in CAPS:
        for temperature in (0, None):
            for thinking in ({"type": "disabled"}, None):
                payload = {"model": model, "max_tokens": cap,
                           "messages": [{"role": "user", "content": prompt}]}
                if temperature is not None:
                    payload["temperature"] = temperature
                if thinking is not None:
                    payload["thinking"] = thinking
                try:
                    r = http_post_json(
                        "https://api.anthropic.com/v1/messages", headers, payload)
                except urllib.error.HTTPError as e:
                    if e.code == 400:
                        continue
                    raise
                text = r["content"][0]["text"] or ""
                if is_clean_letter(text):
                    return text
                # razonamiento: guardar el más completo y subir el tope
                if text and (last_reasoning is None or len(text) > len(last_reasoning)):
                    last_reasoning = text
    # sin respuesta limpia: extraer la decisión del razonamiento completo
    letter = parse_letter(last_reasoning) if last_reasoning else None
    if letter:
        return letter
    raise RuntimeError("claude: respuesta sin letra")


BACKENDS = {
    "ollama": call_ollama,
    "openai": lambda m, p: call_openai_compatible(
        m, p, "https://api.openai.com/v1", "OPENAI_API_KEY"),
    "deepseek": lambda m, p: call_openai_compatible(
        m, p, "https://api.deepseek.com", "DEEPSEEK_API_KEY"),
    "gemini": call_gemini,
    "claude": call_claude,
}


# ---------------------------------------------------------------- rendering
def fmt(v):
    if v is None:
        return None
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        v = round(v, 2)
    return str(v)


MONITORING = {"ART": "arterial line", "NIBP": "non-invasive blood pressure", "NONE": "none"}


LAB_UNITS = {"hb": "g/dL", "hct": "%", "plt": "K/uL", "wbc": "K/uL",
             "na": "mEq/L", "k": "mEq/L", "gluc": "mg/dL", "cr": "mg/dL",
             "lac": "mmol/L", "ph": "", "hco3": "mEq/L", "be": "mEq/L"}


def render_case(inp):
    """Convierte una ventana en un caso clínico en prosa (sin identificadores)."""
    lines = []
    sex = {"M": "male", "F": "female"}.get(inp.get("pt_sex"), inp.get("pt_sex"))

    # --- paciente y cirugía ---
    age = fmt(inp.get("pt_age"))
    head = f"{age}-year-old {sex}" if age else f"{sex} patient"
    attrs = []
    for f, u in [("pt_weight", "kg"), ("pt_height", "cm")]:
        v = fmt(inp.get(f))
        if v is not None:
            attrs.append(f"{v} {u}")
    if fmt(inp.get("pt_bmi")) is not None:
        attrs.append(f"BMI {fmt(inp['pt_bmi'])}")
    if fmt(inp.get("pt_asa")) is not None:
        attrs.append(f"ASA {fmt(inp['pt_asa'])}")
    demo = head + (f" ({', '.join(attrs)})" if attrs else "")

    surg = str(inp["pt_opname"]) if inp.get("pt_opname") else "an unspecified procedure"
    ctx = [str(inp[f]) for f in ("pt_optype", "pt_approach", "pt_position", "pt_ane_type")
           if inp.get(f)]
    emop = "emergency" if inp.get("pt_emop") else "elective"
    opening = f"A {demo} patient is undergoing {surg}"
    if ctx:
        opening += f" ({', '.join(ctx)})"
    opening += f", {emop}."
    lines.append(opening)

    if inp.get("pt_dx"):
        lines.append(f"Diagnosis: {inp['pt_dx']}.")
    if inp.get("pt_department"):
        lines.append(f"Department: {inp['pt_department']}.")
    if inp.get("monitoring_type"):
        lines.append(f"Monitoring: {MONITORING.get(inp['monitoring_type'], inp['monitoring_type'])}.")

    # --- vitales actuales ---
    vit = []
    for name, label, unit in [("HR_current", "HR", "bpm"),
                              ("MAP_current", "MAP", "mmHg"),
                              ("SBP_current", "SBP", "mmHg"),
                              ("DBP_current", "DBP", "mmHg"),
                              ("SpO2_current", "SpO2", "%"),
                              ("EtCO2_current", "EtCO2", "mmHg"),
                              ("BIS_current", "BIS", "")]:
        v = fmt(inp.get(name))
        if v is not None:
            vit.append(f"{label} {v}" + (f" {unit}" if unit else ""))
    if vit:
        lines.append("Current vitals: " + ", ".join(vit) + ".")

    # --- tendencias recientes ---
    tr = []
    for name, label in [("hr_trend", "HR"), ("map_trend", "MAP"), ("bis_trend", "BIS"),
                        ("spo2_trend", "SpO2"), ("etco2_trend", "EtCO2")]:
        v = inp.get(name)
        if v is not None:
            tr.append(f"{label} {v}")
    if tr:
        lines.append("Recent trends: " + ", ".join(tr) + ".")

    # --- fármacos / PKPD ---
    dr = []
    for name, label in [("ce_propofol", "propofol effect-site concentration"),
                        ("ce_remi", "remifentanil effect-site concentration"),
                        ("exp_sevo", "sevoflurane expired concentration"),
                        ("mac", "MAC")]:
        v = fmt(inp.get(name))
        if v is not None:
            dr.append(f"{label} {v}")
    if dr:
        lines.append("Drugs: " + ", ".join(dr) + ".")

    # --- ventilador ---
    ve = []
    for name, label in [("set_fio2", "FiO2"), ("set_peep", "PEEP"),
                        ("set_tv", "tidal volume"), ("set_rr", "respiratory rate")]:
        v = fmt(inp.get(name))
        if v is not None:
            ve.append(f"{label} {v}")
    if ve:
        lines.append("Ventilator: " + ", ".join(ve) + ".")

    # --- labs preoperatorios ---
    la = []
    for t in KEY_LABS:
        v = fmt(inp.get(f"lab_{t}"))
        if v is not None:
            u = LAB_UNITS.get(t, "")
            la.append(f"{t} {v}" + (f" {u}" if u else ""))
    if la:
        lines.append("Preoperative labs: " + ", ".join(la) + ".")

    # --- historial ---
    hs = inp.get("history_summary")
    if hs:
        lines.append(f"Recent course: {hs}")

    return "\n".join(lines)


# ---------------------------------------------------------------- parsing
def strip_letter(text, letter):
    """Quita la letra inicial y el separador para dejar solo la explicación."""
    t = text.strip()
    m = re.match(r"^\s*" + re.escape(letter) + r"\b", t, re.IGNORECASE)
    if m:
        return t[m.end():].lstrip(" .:;-\u2013\u2014()").strip()
    return t


def sanitize(name):
    """Reemplaza caracteres no válidos en rutas de Windows."""
    return re.sub(r'[<>:"/\\|?*]', "_", name)


# ---------------------------------------------------------------- main
def load_difficulty():
    diff = {}
    if MANIFEST.exists():
        import csv
        with open(MANIFEST, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                diff[row["case_id"]] = row.get("difficulty", "unknown")
    return diff


def compute_summary(records, model, backend, split, repeats):
    correct = invalid = errors = 0
    per_diff = {}
    per_class = {}
    consistency_sum = 0.0
    consistency_n = 0
    for r in records:
        d = r.get("difficulty", "unknown")
        per_diff.setdefault(d, [0, 0])
        per_diff[d][0] += 1
        per_diff[d][1] += int(r.get("correct") == 1)
        cl = r.get("result_real")
        if cl:
            per_class.setdefault(cl, [0, 0])
            per_class[cl][0] += 1
            per_class[cl][1] += int(r.get("correct") == 1)
        if r.get("correct") == 1:
            correct += 1
        if r.get("letter") is None:
            invalid += 1
        if r.get("error"):
            errors += 1
        c = r.get("consistency")
        if c is not None:
            consistency_sum += c
            consistency_n += 1
    n = len(records)
    acc = correct / n if n else 0.0
    s = {
        "model": model, "backend": backend, "split": split,
        "n_windows": n, "repeats": repeats, "accuracy": round(acc, 4),
        "invalid_responses": invalid, "errors": errors,
        "accuracy_by_difficulty": {d: round(c / t, 4) if t else None
                                   for d, (t, c) in per_diff.items()},
        "accuracy_by_class": {a: round(c / t, 4) if t else None
                              for a, (t, c) in per_class.items()},
    }
    if repeats > 1 and consistency_n:
        s["mean_consistency"] = round(consistency_sum / consistency_n, 4)
    return s


def print_summary(summary, out_file, out_dir):
    acc = summary["accuracy"]
    print(f"\naccuracy: {acc:.4f} ({summary['n_windows']} windows) · "
          f"invalid: {summary['invalid_responses']} · errors: {summary['errors']}")
    if "mean_consistency" in summary:
        print(f"mean self-consistency: {summary['mean_consistency']:.4f}")
    print("accuracy by difficulty:", {d: (round(c, 3) if c is not None else None)
                                      for d, c in summary["accuracy_by_difficulty"].items()})
    print("accuracy by class:", {a: (round(c, 3) if c is not None else None)
                                 for a, c in summary["accuracy_by_class"].items()})
    print(f"results -> {out_file}")
    print(f"summary -> {out_dir / 'summary.json'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--backend", required=True, choices=sorted(BACKENDS))
    ap.add_argument("--split", default="test", choices=["dev", "train", "test"])
    ap.add_argument("--limit", type=int, default=0, help="max windows to evaluate (0 = all)")
    ap.add_argument("--data-dir", default=str(DATA))
    ap.add_argument("--output", default="")
    ap.add_argument("--sleep", type=float, default=0.0)
    ap.add_argument("--workers", type=int, default=1,
                    help="concurrent requests (parallel evaluation)")
    ap.add_argument("--repeats", type=int, default=1,
                    help="times each window is sent (self-consistency check)")
    ap.add_argument("--seed", type=int, default=42,
                    help="seed for selecting the --limit subset (reproducible)")
    ap.add_argument("--resume", action="store_true",
                    help="skip windows already in the output file")
    args = ap.parse_args()

    load_env()
    if args.backend not in BACKENDS:
        sys.exit(f"unknown backend: {args.backend}")
    fn = BACKENDS[args.backend]

    prompt_tpl = PROMPT_PATH.read_text(encoding="utf-8")
    data_dir = Path(args.data_dir) / args.split
    if args.output:
        out_dir = Path(args.output)
    else:
        name = sanitize(args.model)
        if args.repeats > 1:
            name += f"_repeats{args.repeats}"
        out_dir = ROOT / "results" / name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{args.split}.jsonl"

    difficulty = load_difficulty()

    # resume: resultados ya guardados (para no repetirlos y no perderlos)
    existing = {}
    if args.resume and out_file.exists():
        for line in open(out_file, encoding="utf-8"):
            try:
                r = json.loads(line)
                # descarta errores y respuestas sin letra para re-evaluarlas
                if not r.get("error") and r.get("letter") is not None:
                    existing[r["window_id"]] = r
            except Exception:
                pass

    # todas las ventanas, en orden
    all_windows = []
    for f in sorted(data_dir.glob("case*.jsonl")):
        for line in open(f, encoding="utf-8"):
            all_windows.append(json.loads(line))

    # subconjunto reproducible (seed) sobre TODAS las ventanas
    if args.limit and args.limit < len(all_windows):
        rng = random.Random(args.seed)
        selected = {w["window_id"] for w in rng.sample(all_windows, args.limit)}
        all_windows = [w for w in all_windows if w["window_id"] in selected]

    # ventanas a evaluar ahora (salta las ya guardadas si --resume)
    windows = [w for w in all_windows if w["window_id"] not in existing]

    print(f"model={args.model} backend={args.backend} split={args.split} "
          f"windows={len(windows)}")

    # tareas = (índice de ventana, prompt), repetidas --repeats veces
    tasks = []
    for i, rec in enumerate(windows):
        prompt = prompt_tpl.replace("{case}", render_case(rec["input"]))
        for _ in range(args.repeats):
            tasks.append((i, prompt))

    def run_task(task):
        i, prompt = task
        if args.sleep:
            time.sleep(args.sleep)
        last_err = "empty response"
        for _ in range(3):  # reintenta respuestas vacías / errores transitorios
            try:
                raw = fn(args.model, prompt)
                if raw and raw.strip():
                    letter = parse_letter(raw)
                    return {"letter": letter, "raw": raw,
                            "explanation": strip_letter(raw, letter) if letter else raw,
                            "error": False}
                last_err = "empty response"
            except Exception as e:
                last_err = str(e)
            time.sleep(1.0)
        return {"letter": None, "raw": f"ERROR: {last_err}", "explanation": "", "error": True}

    window_res = [[] for _ in windows]
    done_tasks = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for (i, _), res in zip(tasks, ex.map(run_task, tasks)):
            window_res[i].append(res)
            done_tasks += 1
            if done_tasks % 500 == 0:
                print(f"  {done_tasks}/{len(tasks)} requests")

    records = []
    for i, rec in enumerate(windows):
        wid = rec["window_id"]
        case_id = rec["case_id"]
        result_real = rec["output"]["result_real"]
        d = difficulty.get(str(case_id), "unknown")
        resps = window_res[i]

        letters = [r["letter"] for r in resps if not r["error"] and r["letter"] is not None]
        errs = sum(1 for r in resps if r["error"])

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
            rec_out["responses"] = [{"letter": r["letter"], "raw": r["raw"],
                                     "explanation": r["explanation"], "error": r["error"]}
                                    for r in resps]
        else:
            first = resps[0] if resps else {}
            rec_out["raw_response"] = first.get("raw")
            rec_out["explanation"] = first.get("explanation", "")
        records.append(rec_out)

    # fusiona con lo ya guardado (resume) y escribe
    merged = list(existing.values()) + records
    with open(out_file, "w", encoding="utf-8") as fh:
        for rec_out in merged:
            fh.write(json.dumps(rec_out, ensure_ascii=False) + "\n")

    summary = compute_summary(merged, args.model, args.backend, args.split, args.repeats)
    with open(out_dir / "summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)

    print_summary(summary, out_file, out_dir)


if __name__ == "__main__":
    main()
