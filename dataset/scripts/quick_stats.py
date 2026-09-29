# -*- coding: utf-8 -*-
"""
quick_stats.py — fast console summary of the dataset.

Usage:
    python quick_stats.py               # all splits + overall
    python quick_stats.py test          # one split
    python quick_stats.py case.jsonl    # one file (or several files)

Prints cases, windows, windows/case, and the label distribution of
result_real / result_1 / result_aux.
"""

import argparse
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402


def summarize(records):
    n = len(records)
    n_cases = len({r.get("case_id") for r in records})
    labels = {k: Counter() for k in ("result_real", "result_1", "result_aux")}
    for r in records:
        out = common.get_output(r) or {}
        for k in labels:
            labels[k][common.get_action(out.get(k))] += 1
    return n, n_cases, labels


def print_summary(name, records):
    n, n_cases, labels = summarize(records)
    print(f"== {name} ==  cases={n_cases}  windows={n}")
    if n:
        print(f"   windows/case mean={n / n_cases:.2f}")
    for k in ("result_real", "result_1", "result_aux"):
        total = sum(labels[k].values())
        parts = [f"{a}: {c} ({100.0 * c / total:.1f}%)" if total else f"{a}: 0"
                 for a, c in sorted(labels[k].items(), key=lambda x: -x[1])]
        print(f"   {k:<12} " + "  ".join(parts))
    print()


def main():
    ap = argparse.ArgumentParser(description="Fast console summary of the dataset.")
    ap.add_argument("targets", nargs="*", help="split name(s) or case*.jsonl file(s)")
    args = ap.parse_args()

    targets = args.targets or common.SPLITS
    for t in targets:
        if t in common.SPLITS:
            print_summary(f"split:{t}", list(common.iter_split(t)))
        else:
            print_summary(os.path.basename(t), common.load_jsonl(t))


if __name__ == "__main__":
    main()
