# -*- coding: utf-8 -*-
"""Análisis 3 — contrafactual de sexo (ejecución).

Genera las versiones "male" y "female" de cada ventana y las envía a los 5
modelos que razonan, reutilizando `render_case`, `prompt.txt`, `BACKENDS`,
`CAPS`, `parse_letter` y la lógica de reintentos de `src/llm/eval.py`
(sin modificarlo).

Uso:
    python src/sex_counterfactual.py --dry-run
    python src/sex_counterfactual.py --workers 8 --resume
"""
import argparse
import csv
import hashlib
import json
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT
sys.path.insert(0, str(SRC))
from llm import eval as ev  # noqa: E402

DATA = ROOT / "src" / "dataset" / "data" / "test"
PROMPT_PATH = SRC / "src" / "llm" / "prompt.txt"
OUT_DIR = ROOT / "results" / "data_results" /"sex_cf"

SEED = 42

# (model, backend) — los 5 modelos que razonan, con los identificadores,
# backend y configuración de S02_model_registry.csv.
MODELS = [
    ("claude-opus-5-5", "claude"),
    ("gpt-6-sol", "openai"),
    ("gemini-3.1-pro-preview", "gemini"),
    ("deepseek-v4-pro", "deepseek"),
    ("deepseek-flash", "deepseek"),
]

EXPECTED_PRIMARY = 354
N_SECONDARY = 300

# Lista de palabras clave del diseño (sobre pt_opname + pt_dx, minúsculas).
# `cervix` (cérvix uterino) y NO `cervical` (casi siempre columna cervical).
SEX_KEYWORDS = [
    "breast", "mastect", "prostate", "hysterect", "oophor", "salping",
    "myomect", "uterus", "uterine", "ovary", "ovarian", "endometr",
    "cervix", "vagin", "vulv", "tubal", "testicular", "testis", "scrot",
    "penis", "fournier", "turp", "transurethral", "orchi", "orchid",
    "vasect", "circumcis", "perineal",
]

# Palabras de sexo que NO deben aparecer fuera de la cabecera del caso.
SEX_OUTSIDE_RE = re.compile(
    r"\b(male|female|woman|man|she|he|her|his)\b", re.IGNORECASE)


def sanitize(name):
    return re.sub(r'[<>:"/\\|?*]', "_", name)


def load_test_windows(data_dir):
    windows = []
    for f in sorted(Path(data_dir).glob("case*.jsonl")):
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    windows.append(json.loads(line))
    return windows


def is_vasopressor(rec):
    """True si alguna referencia (result_1/result_aux/result_real) es vasopressor."""
    out = rec.get("output", {})
    r1 = (out.get("result_1") or {}).get("action")
    raux = (out.get("result_aux") or {}).get("action")
    rr = out.get("result_real")
    return rr == "vasopressor" or r1 == "vasopressor" or raux == "vasopressor"


def is_sex_specific(inp):
    text = ((inp.get("pt_opname") or "") + " " + (inp.get("pt_dx") or "")).lower()
    return any(k in text for k in SEX_KEYWORDS)


def select_windows(windows):
    """Devuelve (post, sex_cases, non_excluded, primary, secondary)."""
    post = [w for w in windows if not is_vasopressor(w)]
    sex_cases = {}
    for w in post:
        if is_sex_specific(w["input"]):
            sex_cases.setdefault(w["case_id"], []).append(w)
    non_excluded = [w for w in post if w["case_id"] not in sex_cases]
    primary = [w for w in non_excluded
               if w["input"].get("map_current") is not None
               and w["input"]["map_current"] < 65]
    primary_ids = {w["window_id"] for w in primary}
    pool = [w for w in non_excluded if w["window_id"] not in primary_ids]
    rng = random.Random(SEED)
    secondary = rng.sample(pool, N_SECONDARY)
    return post, sex_cases, non_excluded, primary, secondary


def check_versions(caseF, caseM):
    """Comprueba que las dos versiones solo difieren en "male"/"female" de la
    cabecera y que no hay palabras de sexo fuera de ella.

    Devuelve (full_ok, header_ok, hits).
    """
    full_ok = (caseM == caseF.replace("female", "male")
               and caseF == caseM.replace("male", "female"))
    hf = caseF.split("\n")[0]
    hm = caseM.split("\n")[0]
    header_ok = (hm == hf.replace("female", "male")
                 and hf == hm.replace("male", "female"))
    rest = "\n".join(caseF.split("\n")[1:])
    hits = SEX_OUTSIDE_RE.findall(rest)
    return full_ok, header_ok, hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=str(DATA))
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    ap.add_argument("--workers", type=int, default=1,
                    help="solicitudes concurrentes por modelo")
    ap.add_argument("--sleep", type=float, default=0.0)
    ap.add_argument("--resume", action="store_true",
                    help="salta los pares ya guardados con respuesta válida")
    ap.add_argument("--dry-run", action="store_true",
                    help="genera casos y comprueba, sin llamar a las API")
    ap.add_argument("--models",
                    default=",".join(m for m, _ in MODELS),
                    help="modelos a ejecutar, separados por coma")
    args = ap.parse_args()

    ev.load_env()

    wanted = [m.strip() for m in args.models.split(",") if m.strip()]
    selected = [(m, b) for m, b in MODELS if m in wanted]
    if not selected:
        sys.exit("ningún modelo seleccionado")

    prompt_tpl = PROMPT_PATH.read_text(encoding="utf-8")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    windows = load_test_windows(args.data_dir)
    post, sex_cases, non_excluded, primary, secondary = select_windows(windows)

    # ---- lista de casos excluidos (imprime y guarda) ----
    excluded_path = out_dir / "excluded_sex_specific_cases.csv"
    with open(excluded_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["case_id", "n_windows", "pt_opname", "pt_dx"])
        for cid in sorted(sex_cases):
            ws = sex_cases[cid]
            w.writerow([cid, len(ws),
                        ws[0]["input"].get("pt_opname") or "",
                        ws[0]["input"].get("pt_dx") or ""])
    print(f"casos sexo-específicos excluidos: {len(sex_cases)} -> {excluded_path}")
    for cid in sorted(sex_cases):
        print(f"  case{cid}: {len(sex_cases[cid])} ventanas")

    # ---- recuento principal obligatorio ----
    if len(primary) != EXPECTED_PRIMARY:
        print(f"ERROR: se esperaban {EXPECTED_PRIMARY} ventanas principales "
              f"(MAP < 65), se obtuvieron {len(primary)}. Se detiene.")
        sys.exit(1)

    # ---- genera y comprueba TODAS las versiones antes de llamar a la API ----
    cases = {}
    for x in primary + secondary:
        inp = x["input"]
        inpF = dict(inp)
        inpF["pt_sex"] = "F"
        inpM = dict(inp)
        inpM["pt_sex"] = "M"
        caseF = ev.render_case(inpF)
        caseM = ev.render_case(inpM)
        full_ok, header_ok, hits = check_versions(caseF, caseM)
        if not full_ok or not header_ok or hits:
            print(f"ABORTO en {x['window_id']}: full_ok={full_ok} "
                  f"header_ok={header_ok} sex_outside_header={hits}")
            sys.exit(1)
        cases[(x["window_id"], "F")] = caseF
        cases[(x["window_id"], "M")] = caseM

    # ---- manifiesto de selección (reproducibilidad) ----
    manifest_path = out_dir / "selection_manifest.csv"
    with open(manifest_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["window_id", "case_id", "set", "map_current", "sex_original"])
        for set_name, wlist in [("primary", primary), ("secondary", secondary)]:
            for x in wlist:
                w.writerow([x["window_id"], x["case_id"], set_name,
                            x["input"].get("map_current"),
                            x["input"].get("pt_sex")])

    n_windows = len(primary) + len(secondary)
    n_calls = n_windows * 2 * len(selected)
    print(f"test total={len(windows)} post-vasopressor={len(post)} "
          f"no-excluidas={len(non_excluded)}")
    print(f"principales={len(primary)} secundarias={len(secondary)} "
          f"ventanas={n_windows} modelos={len(selected)} llamadas={n_calls}")
    print(f"comprobaciones de sexo OK para las {n_windows} ventanas")

    if args.dry_run:
        print("DRY-RUN: sin llamadas a API.")
        return

    # ---- tareas (set, window, version), barajadas con random.Random(42) ----
    base_tasks = []
    for set_name, wlist in [("primary", primary), ("secondary", secondary)]:
        for x in wlist:
            base_tasks.append((set_name, x, "F"))
            base_tasks.append((set_name, x, "M"))
    rng = random.Random(SEED)
    rng.shuffle(base_tasks)

    for model, backend in selected:
        fn = ev.BACKENDS[backend]
        out_file = out_dir / f"raw_{sanitize(model)}.jsonl"

        # resume: pares ya guardados con respuesta válida
        existing = {}
        if args.resume and out_file.exists():
            for line in open(out_file, encoding="utf-8"):
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("parsed_action") is not None and \
                        not str(r.get("raw_response", "")).startswith("ERROR"):
                    existing[(r["window_id"], r["version"])] = r

        todo = []
        for set_name, x, ver in base_tasks:
            if (x["window_id"], ver) in existing:
                continue
            prompt = prompt_tpl.replace("{case}", cases[(x["window_id"], ver)])
            todo.append((set_name, x, ver, prompt))

        print(f"model={model} backend={backend} pendientes={len(todo)} "
              f"(ya hechas={len(existing)})")

        def run_call(prompt):
            if args.sleep:
                time.sleep(args.sleep)
            last_err = "empty response"
            for _ in range(3):  # reintenta vacíos / errores transitorios
                try:
                    raw = fn(model, prompt)
                    if raw and raw.strip():
                        letter = ev.parse_letter(raw, "abcde")
                        return raw, ev.LETTER_TO_ACTION.get(letter)
                    last_err = "empty response"
                except Exception as e:
                    last_err = str(e)
                time.sleep(1.0)
            return f"ERROR: {last_err}", None

        # escribe primero las ya válidas (resume) para no perderlas
        with open(out_file, "w", encoding="utf-8") as fh:
            for r in existing.values():
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")

        done = 0
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(run_call, t[3]): t for t in todo}
            for fut in as_completed(futs):
                set_name, x, ver, prompt = futs[fut]
                raw, action = fut.result()
                rec = {
                    "model": model,
                    "window_id": x["window_id"],
                    "case_id": x["case_id"],
                    "set": set_name,
                    "version": ver,
                    "sex_original": x["input"].get("pt_sex"),
                    "prompt_hash": hashlib.sha256(
                        prompt.encode("utf-8")).hexdigest(),
                    "raw_response": raw,
                    "parsed_action": action,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                with open(out_file, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                done += 1
                if done % 100 == 0:
                    print(f"  {done}/{len(todo)}", flush=True)
        print(f"  terminado {model}: {done} llamadas nuevas")

    print(f"resultados en {out_dir}")


if __name__ == "__main__":
    main()
