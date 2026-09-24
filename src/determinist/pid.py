# -*- coding: utf-8 -*-
"""Baseline determinista: controlador PID de BIS (PID_Aubouin)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import evaluate, write_test, write_consistency
from policies.pid_policy import PIDPolicy


def main():
    preds = evaluate(lambda: PIDPolicy(), "pid")
    n = write_test("pid", preds)
    m = write_consistency("pid", preds)
    print(f"pid: {n} test, {m} consistencia")


if __name__ == "__main__":
    main()
