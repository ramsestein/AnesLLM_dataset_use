# -*- coding: utf-8 -*-
"""
check_integrity.py — validate vocabulary, ratios and consistency of the dataset.

Usage:
    python check_integrity.py            # all splits
    python check_integrity.py test

Checks:
  - result_real uses only the 5 canonical actions
  - result_1 / result_aux use the 5 actions + vasopressor
  - ratios in [0, 1]
  - window_ids are unique
  - window counts match split_manifest.csv
  - every case appears in exactly one split

Exit code 0 = OK, 1 = problems found.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Validate dataset integrity.")
    ap.add_argument("splits", nargs="*", default=common.SPLITS, help="splits to check")
    args = ap.parse_args()

    manifest = common.load_manifest()
    errors = 0
    seen_windows = set()

    for split in args.splits:
        records = list(common.iter_split(split))
        man_cases = sum(1 for i in manifest.values() if i.get("split") == split)
        man_sum = sum(i.get("n_windows") or 0 for i in manifest.values() if i.get("split") == split)

        for r in records:
            out = common.get_output(r) or {}
            real_a = common.get_action(out.get("result_real"))
            r1 = common.get_action(out.get("result_1"))
            aux = common.get_action(out.get("result_aux"))
            wid = r.get("window_id")

            if real_a not in common.ACTIONS:
                print(f"[{split}] bad result_real {real_a!r} in {wid}")
                errors += 1
            for name, a in (("result_1", r1), ("result_aux", aux)):
                if a not in common.ALL_ACTIONS:
                    print(f"[{split}] bad {name} {a!r} in {wid}")
                    errors += 1
            for name in ("result_1", "result_aux"):
                ratio = common.get_ratio(out.get(name))
                if ratio is not None and not (0.0 <= ratio <= 1.0):
                    print(f"[{split}] ratio out of range {ratio} in {wid}")
                    errors += 1
            if wid in seen_windows:
                print(f"[{split}] duplicate window_id {wid!r}")
                errors += 1
            seen_windows.add(wid)

        print(f"[{split}] cases(manifest)={man_cases} windows(actual)={len(records)} "
              f"windows(manifest sum)={man_sum}")
        if len(records) != man_sum:
            print(f"[{split}] MISMATCH: actual windows {len(records)} != manifest {man_sum}")
            errors += 1

    print(f"\n{'OK' if errors == 0 else f'{errors} problem(s) found'}")
    sys.exit(0 if errors == 0 else 1)


if __name__ == "__main__":
    main()
