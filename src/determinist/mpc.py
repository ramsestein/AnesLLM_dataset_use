# -*- coding: utf-8 -*-
"""Baseline determinista: MEKF-MPC adaptativo (MEKFMPCPolicy)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import evaluate, write_test, write_consistency
from policies.mpc_policy import MEKFMPCPolicy


def main():
    preds = evaluate(lambda: MEKFMPCPolicy(), "mpc")
    n = write_test("mpc", preds)
    m = write_consistency("mpc", preds)
    print(f"mpc: {n} test, {m} consistencia")


if __name__ == "__main__":
    main()
