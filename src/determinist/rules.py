# -*- coding: utf-8 -*-
"""Baseline determinista: reglas clínicas de umbral (RuleBased_Liu2006)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import evaluate, write_test, write_consistency
from policies.rule_policy import RuleBasedPolicy


def main():
    preds = evaluate(lambda: RuleBasedPolicy(), "rules")
    n = write_test("rules", preds)
    m = write_consistency("rules", preds)
    print(f"rules: {n} test, {m} consistencia")


if __name__ == "__main__":
    main()
