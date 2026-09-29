# -*- coding: utf-8 -*-
"""
filter.py — filter decision windows by criteria and write a new JSONL.

Usage:
    python filter.py test --real reduce_hypnotic -o out.jsonl
    python filter.py test --r1 increase_opioid -o out.jsonl
    python filter.py train --difficulty hard -o out.jsonl
    python filter.py test --sex F -o out.jsonl
    python filter.py test --monitoring NIBP -o out.jsonl
    python filter.py test --case 1001 1004 -o out.jsonl
    python filter.py test --min-windows 20 --max-windows 30 -o out.jsonl
    python filter.py test --real no_action --limit 100 --shuffle --seed 7 -o out.jsonl
    python filter.py a.jsonl b.jsonl --real no_action -o out.jsonl

Sources: split names (dev/train/test) or case*.jsonl files. Output is written as
JSON lines (full records, one per window).
"""

import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402


def windows_per_case(records):
    c = {}
    for r in records:
        cid = r.get("case_id")
        c[cid] = c.get(cid, 0) + 1
    return c


def main():
    ap = argparse.ArgumentParser(description="Filter dataset windows into a new JSONL.")
    ap.add_argument("sources", nargs="+", help="split name(s) or case*.jsonl file(s)")
    ap.add_argument("-o", "--output", required=True, help="output JSONL file")
    ap.add_argument("--real", help="filter by result_real action")
    ap.add_argument("--r1", help="filter by result_1 action")
    ap.add_argument("--aux", help="filter by result_aux action")
    ap.add_argument("--difficulty", choices=["easy", "medium", "hard"])
    ap.add_argument("--sex", choices=["M", "F"])
    ap.add_argument("--monitoring", choices=["ART", "NIBP", "NONE"])
    ap.add_argument("--case", nargs="+", help="filter by case_id")
    ap.add_argument("--min-windows", type=int, help="min windows per case")
    ap.add_argument("--max-windows", type=int, help="max windows per case")
    ap.add_argument("--limit", type=int, help="max output windows")
    ap.add_argument("--shuffle", action="store_true", help="shuffle before --limit")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    records = []
    for s in args.sources:
        records.extend(common.iter_split(s) if s in common.SPLITS else common.load_jsonl(s))

    wpc = windows_per_case(records)
    manifest = common.load_manifest()
    case_set = {str(c) for c in args.case} if args.case else None

    def keep(r):
        out = common.get_output(r) or {}
        inp = common.get_input(r)
        cid = r.get("case_id")
        if args.real and common.get_action(out.get("result_real")) != args.real:
            return False
        if args.r1 and common.get_action(out.get("result_1")) != args.r1:
            return False
        if args.aux and common.get_action(out.get("result_aux")) != args.aux:
            return False
        if args.difficulty and manifest.get(str(cid), {}).get("difficulty") != args.difficulty:
            return False
        if args.sex and inp.get("pt_sex") != args.sex:
            return False
        if args.monitoring and inp.get("monitoring_type") != args.monitoring:
            return False
        if case_set is not None and str(cid) not in case_set:
            return False
        n = wpc.get(cid, 0)
        if args.min_windows is not None and n < args.min_windows:
            return False
        if args.max_windows is not None and n > args.max_windows:
            return False
        return True

    selected = [r for r in records if keep(r)]
    if args.shuffle:
        random.Random(args.seed).shuffle(selected)
    if args.limit is not None:
        selected = selected[:args.limit]

    with open(args.output, "w", encoding="utf-8") as f:
        for r in selected:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"{len(selected)} windows -> {args.output}")


if __name__ == "__main__":
    main()
