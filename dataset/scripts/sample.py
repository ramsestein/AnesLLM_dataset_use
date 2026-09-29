# -*- coding: utf-8 -*-
"""
sample.py — random sampling of windows or whole cases.

Usage:
    python sample.py test 100 -o sample.jsonl               # 100 random windows
    python sample.py test 20 --per-class -o sample.jsonl    # 20 windows per result_real class
    python sample.py test 50 --stratified -o sample.jsonl   # 50 windows, class-proportional
    python sample.py test 10 --cases -o sample.jsonl        # 10 whole cases

    --seed N  for reproducibility.
"""

import argparse
import json
import os
import random
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Sample dataset windows or cases.")
    ap.add_argument("source", help="split name (dev/train/test) or case*.jsonl file")
    ap.add_argument("n", type=int, help="number of windows/cases")
    ap.add_argument("-o", "--output", required=True, help="output JSONL file")
    ap.add_argument("--per-class", action="store_true", help="n windows per result_real class")
    ap.add_argument("--stratified", action="store_true", help="n windows proportional to class")
    ap.add_argument("--cases", action="store_true", help="sample whole cases instead of windows")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    records = list(common.iter_split(args.source) if args.source in common.SPLITS
                   else common.load_jsonl(args.source))

    if args.cases:
        by_case = defaultdict(list)
        for r in records:
            by_case[r.get("case_id")].append(r)
        cids = list(by_case)
        rng.shuffle(cids)
        selected = [r for cid in cids[:args.n] for r in by_case[cid]]
    elif args.per_class or args.stratified:
        by_class = defaultdict(list)
        for r in records:
            cls = common.get_action((common.get_output(r) or {}).get("result_real"))
            by_class[cls].append(r)
        if args.per_class:
            selected = []
            for cls, rs in sorted(by_class.items(), key=lambda x: x[0] or ""):
                picked = rng.sample(rs, min(args.n, len(rs)))
                selected.extend(picked)
                print(f"class {cls}: {len(picked)}")
        else:  # stratified, class-proportional
            total = len(records)
            selected = []
            for cls, rs in by_class.items():
                k = round(args.n * len(rs) / total)
                selected.extend(rng.sample(rs, min(k, len(rs))))
    else:
        selected = rng.sample(records, min(args.n, len(records)))

    with open(args.output, "w", encoding="utf-8") as f:
        for r in selected:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"{len(selected)} windows -> {args.output}")


if __name__ == "__main__":
    main()
