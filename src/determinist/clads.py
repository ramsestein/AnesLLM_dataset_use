# -*- coding: utf-8 -*-
"""Baseline determinista: CLADS-lite (CLADS_Hemmerling2010)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import evaluate, write_test
from policies.clads_policy import CLADSPolicy


def main():
    preds = evaluate(lambda: CLADSPolicy(), "clads")
    n = write_test("clads", preds)
    print(f"clads: {n} test")


if __name__ == "__main__":
    main()
