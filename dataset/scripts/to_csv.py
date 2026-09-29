# -*- coding: utf-8 -*-
"""
to_csv.py — flatten selected windows into a CSV table (one row per window).

Usage:
    python to_csv.py test -o test.csv                   # all test windows
    python to_csv.py test --limit 100 -o sample.csv
    python to_csv.py test --columns window_id,pt_age,result_real -o t.csv

By default every input field plus result_real / result_1 / result_aux and case
difficulty are emitted as columns. Nested values (dicts/lists) are serialized
as compact JSON strings; missing values are empty.
"""

import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402


def cell(v):
    if v is None:
        return ""
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return str(round(v, 6))
    return str(v)


def main():
    ap = argparse.ArgumentParser(description="Flatten dataset windows into CSV.")
    ap.add_argument("sources", nargs="+", help="split name(s) or case*.jsonl file(s)")
    ap.add_argument("-o", "--output", required=True, help="output CSV file")
    ap.add_argument("--columns",
                    help="comma-separated input feature columns to include "
                         "(IDs and labels are always included)")
    ap.add_argument("--limit", type=int, help="max rows")
    args = ap.parse_args()

    records = []
    for s in args.sources:
        records.extend(common.iter_split(s) if s in common.SPLITS else common.load_jsonl(s))
    if args.limit is not None:
        records = records[:args.limit]

    manifest = common.load_manifest()

    # window_id y case_id ya van como columnas fijas; se evita duplicarlos
    input_keys = sorted({k for r in records for k in common.get_input(r)
                         if k not in ("window_id", "case_id")})
    if args.columns:
        keep = [c.strip() for c in args.columns.split(",") if c.strip()]
        input_keys = [k for k in input_keys if k in keep]

    header = (["window_id", "case_id", "difficulty"] + input_keys +
              ["result_real", "result_1", "result_1_ratio", "result_aux", "result_aux_ratio"])

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in records:
            inp = common.get_input(r)
            out = common.get_output(r) or {}
            r1 = out.get("result_1") or {}
            raux = out.get("result_aux") or {}
            cid = r.get("case_id")
            row = [r.get("window_id"), cid, manifest.get(str(cid), {}).get("difficulty", "")]
            row += [cell(inp.get(k)) for k in input_keys]
            row += [cell(out.get("result_real")),
                    cell(r1.get("action")), cell(r1.get("ratio")),
                    cell(raux.get("action")), cell(raux.get("ratio"))]
            w.writerow(row)

    print(f"{len(records)} rows, {len(header)} columns -> {args.output}")


if __name__ == "__main__":
    main()
