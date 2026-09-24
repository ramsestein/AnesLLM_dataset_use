# -*- coding: utf-8 -*-
"""Baseline determinista: controlador difuso PD de BIS (FuzzyPD_Shieh2006)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import evaluate, write_test, write_consistency
from policies.fuzzy_policy import FuzzyPDPolicy


def main():
    preds = evaluate(lambda: FuzzyPDPolicy(), "fuzzy")
    n = write_test("fuzzy", preds)
    m = write_consistency("fuzzy", preds)
    print(f"fuzzy: {n} test, {m} consistencia")


if __name__ == "__main__":
    main()
