# -*- coding: utf-8 -*-
"""
to_prompt.py
------------
Converts AnesLLM decision windows (dataset/data/{dev,train,test}/case*.jsonl) into
a working LLM prompt, using the prompt template in prompt.txt (same directory).

The record's `input` (280 pre-decision fields) is rendered into clinical prose and
injected into the template's `{case}` placeholder.

Usage:
    python to_prompt.py path/to/case14.jsonl                  # first window
    python to_prompt.py path/to/case14.jsonl --line 3         # window at line 3
    python to_prompt.py path/to/case14.jsonl --window case14_w127
    python to_prompt.py path/to/case14.jsonl --all            # every window
    Get-Content case14.jsonl | python to_prompt.py            # one record from stdin
    python to_prompt.py path/to/case14.jsonl --raw-case       # case prose only

The final prompt is printed to stdout; the ground-truth reference (window_id,
result_real, result_1, result_aux) is printed to stderr.
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

HERE = Path(__file__).resolve().parent
DEFAULT_PROMPT = HERE / "prompt.txt"


def load_records(path):
    """Reads JSONL records from a file path or from stdin when path is None."""
    handle = sys.stdin if path in (None, "-") else open(path, encoding="utf-8")
    try:
        records = []
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
        return records
    finally:
        if handle is not sys.stdin:
            handle.close()


def reference_text(record):
    """Builds a one-line ground-truth reference for stderr."""
    wid = record.get("window_id")
    cid = record.get("case_id")
    out = common.get_output(record) or {}
    r1 = out.get("result_1") or {}
    raux = out.get("result_aux") or {}
    real = out.get("result_real")
    parts = [f"window_id: {wid}", f"case_id: {cid}"]
    if real is not None:
        parts.append(f"result_real: {real}")
    if r1.get("action") is not None:
        parts.append(f"result_1: {r1.get('action')} (ratio {common.fmt(r1.get('ratio'))})")
    if raux.get("action") is not None:
        parts.append(f"result_aux: {raux.get('action')} (ratio {common.fmt(raux.get('ratio'))})")
    return " | ".join(parts)


def main():
    ap = argparse.ArgumentParser(description="Convert AnesLLM windows into a working LLM prompt.")
    ap.add_argument("path", nargs="?", default=None,
                    help="JSONL file (case*.jsonl). Omit to read from stdin.")
    ap.add_argument("--window", metavar="ID", help="select a window by window_id")
    ap.add_argument("--line", type=int, default=None,
                    help="select a window by 0-based line index")
    ap.add_argument("--all", action="store_true", help="render every window in the file")
    ap.add_argument("--limit", type=int, default=None,
                    help="with --all: maximum number of windows to render")
    ap.add_argument("--raw-case", action="store_true",
                    help="print only the rendered case prose (no template)")
    ap.add_argument("--no-reference", action="store_true",
                    help="do not print the ground-truth reference to stderr")
    ap.add_argument("--prompt-file", default=str(DEFAULT_PROMPT),
                    help=f"prompt template to use (default: {DEFAULT_PROMPT.name})")
    args = ap.parse_args()

    records = load_records(args.path)

    selected = []
    if args.window is not None:
        selected = [r for r in records if r.get("window_id") == args.window]
        if not selected:
            sys.stderr.write(f"error: window_id {args.window!r} not found\n")
            sys.exit(1)
    elif args.all:
        selected = records
        if args.limit is not None:
            selected = selected[:args.limit]
    elif args.line is not None:
        if not (0 <= args.line < len(records)):
            sys.stderr.write(f"error: line {args.line} out of range (0..{len(records) - 1})\n")
            sys.exit(1)
        selected = [records[args.line]]
    else:
        selected = records[:1]

    template = Path(args.prompt_file).read_text(encoding="utf-8")

    outputs = []
    refs = []
    for rec in selected:
        case = common.render_case(common.get_input(rec))
        outputs.append(case if args.raw_case else template.replace("{case}", case))
        refs.append(reference_text(rec))

    print("\n\n---\n\n".join(outputs))

    if not args.no_reference and refs:
        sys.stderr.write("[reference] " + " || ".join(refs) + "\n")


if __name__ == "__main__":
    main()
