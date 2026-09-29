# -*- coding: utf-8 -*-
"""
dataset_sha256.py — deterministic SHA-256 fingerprint of the dataset.

By default it selects 42 windows with a seeded RNG (seed=42) and hashes their
canonical JSON serialization (sorted keys, compact separators). The selection is
fully deterministic: all window IDs are sorted, then sampled with random.Random(42).

Usage:
    python dataset_sha256.py                 # compute and store the fingerprint
    python dataset_sha256.py --verify        # recompute and compare with the stored hash
    python dataset_sha256.py --all           # hash the ENTIRE dataset (all windows)
    python dataset_sha256.py --seed 42 --n 42

The manifest is written to dataset/reports/dataset_sha256.json.
"""

import argparse
import hashlib
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

MANIFEST_PATH = os.path.join(common.REPORTS_DIR, "dataset_sha256.json")


def canonical(record):
    """Canonical JSON serialization: sorted keys, compact separators, UTF-8."""
    return json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def hash_records(records):
    """SHA-256 over the canonical serialization of a list of records."""
    payload = "\n".join(canonical(r) for r in records).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_all():
    """Returns ({window_id: record}, sorted_window_ids, {split: n_windows})."""
    by_wid = {}
    counts = {}
    for split in common.SPLITS:
        cnt = 0
        for r in common.iter_split(split):
            by_wid[r["window_id"]] = r
            cnt += 1
        counts[split] = cnt
    return by_wid, sorted(by_wid), counts


def main():
    ap = argparse.ArgumentParser(description="Deterministic SHA-256 fingerprint of the dataset.")
    ap.add_argument("--seed", type=int, default=42, help="RNG seed for the sample")
    ap.add_argument("--n", type=int, default=42, help="number of windows to sample")
    ap.add_argument("--all", action="store_true",
                    help="hash every window (full fingerprint, no manifest)")
    ap.add_argument("--verify", action="store_true",
                    help="compare against the stored sha256 and exit")
    args = ap.parse_args()

    by_wid, wids, counts = load_all()

    if args.all:
        digest = hash_records([by_wid[w] for w in wids])
        print(f"sha256 (all {len(wids)} windows) = {digest}")
        return

    rng = random.Random(args.seed)
    selected = sorted(rng.sample(wids, min(args.n, len(wids))))
    digest = hash_records([by_wid[w] for w in selected])

    if args.verify:
        if not os.path.exists(MANIFEST_PATH):
            print("no stored manifest; run without --verify first")
            sys.exit(1)
        stored = json.load(open(MANIFEST_PATH, encoding="utf-8"))
        if stored.get("sha256") == digest:
            print("OK: dataset matches stored sha256")
            sys.exit(0)
        print("MISMATCH: dataset differs from stored sha256")
        print("  stored :", stored.get("sha256"))
        print("  current:", digest)
        sys.exit(1)

    manifest = {
        "algorithm": "sha256",
        "seed": args.seed,
        "n_selected": len(selected),
        "total_windows": len(wids),
        "total_cases": len({r["case_id"] for r in by_wid.values()}),
        "windows_by_split": counts,
        "selected_window_ids": selected,
        "sha256": digest,
    }
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"seed={args.seed}  selected={len(selected)} windows  "
          f"sha256={digest}")
    print(f"manifest -> {os.path.relpath(MANIFEST_PATH)}")


if __name__ == "__main__":
    main()
