# -*- coding: utf-8 -*-
"""Ejecuta todos los baselines deterministas en secuencia."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rules import main as run_rules
from pid import main as run_pid
from clads import main as run_clads
from fuzzy import main as run_fuzzy


def main():
    for fn in (run_rules, run_pid, run_clads, run_fuzzy):
        fn()


if __name__ == "__main__":
    main()
