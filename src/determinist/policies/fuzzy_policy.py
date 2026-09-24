"""
policies/fuzzy_policy.py — Fuzzy PD controller baseline (brazo E).

Reimplements the Mamdani fuzzy-logic BIS controller described in:

  Shieh J-S, Dai C-Y, Wen Y-R, Young S-T.
  "A novel fuzzy control of propofol sedation in endoscopy."
  J Med Syst 2006; 30(5):361-367.

  Sawaguchi Y, et al.
  "A model-free adaptive control of anesthesia with two prediction
  schemes." Proc IEEE EMBC 2008.

Architecture
------------
Inputs:
  e  = BIS_current - BIS_setpoint   (error, positive → too awake)
  de = (e - e_prev) / dt            (rate of change)

Fuzzy sets for error e  (in BIS-points):
  NL (Negative Large) < -20
  NM (Negative Medium) -20..-10
  NS (Negative Small)  -10..-3
  ZE (Zero)            -3..+3
  PS (Positive Small)   3..10
  PM (Positive Medium) 10..20
  PL (Positive Large)  > 20

Fuzzy sets for rate de/dt (in BIS-points/s):
  DN (Decreasing)  < -0.05
  ST (Stable)      -0.05..+0.05
  IN (Increasing)  > +0.05

Rule base → crisp output mapped to bench actions:
  output ≥ +1.0  → increase_hypnotic
  output ≤ -1.0  → reduce_hypnotic
  otherwise      → no_action

MAP override: MAP < ACC_LO → vasopressor (same as PID/MPC).
"""
from __future__ import annotations

from typing import Any, Dict
import numpy as np

from .base import PolicyBase
from config import MAP_ACC_LO, HR_MARG_LO, DECISION_INTERVAL_SEC, _P as _CFG

_FUZZY_BIS_SETPOINT = _CFG["policies"]["fuzzy"]["bis_setpoint"]


# ── Membership functions (triangular / trapezoidal) ──────────────────────────

def _trap(x: float, a: float, b: float, c: float, d: float) -> float:
    """Trapezoid: rises a→b, flat b→c, falls c→d."""
    if x <= a or x >= d:
        return 0.0
    if b <= x <= c:
        return 1.0
    if x < b:
        return (x - a) / (b - a)
    return (d - x) / (d - c)


def _tri(x: float, a: float, b: float, c: float) -> float:
    """Triangle: rises a→b, falls b→c."""
    return _trap(x, a, b, b, c)


# Error membership (BIS-points)
def _e_NL(e): return _trap(e, -1e9, -1e9, -20, -10)
def _e_NM(e): return _tri(e, -20, -12, -4)
def _e_NS(e): return _tri(e, -10,  -5,  0)
def _e_ZE(e): return _tri(e,  -4,   0,  4)
def _e_PS(e): return _tri(e,   0,   5, 10)
def _e_PM(e): return _tri(e,   4,  12, 20)
def _e_PL(e): return _trap(e,  10,  20, 1e9, 1e9)


# Rate membership (BIS-points / s)
def _r_DN(r): return _trap(r, -1e9, -1e9, -0.10, -0.02)
def _r_ST(r): return _tri(r,  -0.06,  0.0,  0.06)
def _r_IN(r): return _trap(r,  0.02,  0.10, 1e9,  1e9)


# ── Rule base: (e_label, r_label) → crisp output [-3 .. +3] ─────────────────
# Positive output = need MORE propofol (BIS too high → increase_hypnotic)
# Negative output = need LESS propofol (BIS too low  → reduce_hypnotic)
_RULES: dict[tuple[str, str], float] = {
    # Error \ Rate    DN       ST       IN
    ("NL", "DN"):  -3.0,
    ("NL", "ST"):  -2.5,
    ("NL", "IN"):  -2.0,
    ("NM", "DN"):  -2.0,
    ("NM", "ST"):  -1.5,
    ("NM", "IN"):  -1.0,
    ("NS", "DN"):  -1.0,
    ("NS", "ST"):  -0.5,
    ("NS", "IN"):   0.0,
    ("ZE", "DN"):  -0.5,
    ("ZE", "ST"):   0.0,
    ("ZE", "IN"):  +0.5,
    ("PS", "DN"):   0.0,
    ("PS", "ST"):  +0.5,
    ("PS", "IN"):  +1.0,
    ("PM", "DN"):  +1.0,
    ("PM", "ST"):  +1.5,
    ("PM", "IN"):  +2.0,
    ("PL", "DN"):  +2.0,
    ("PL", "ST"):  +2.5,
    ("PL", "IN"):  +3.0,
}

_E_FUNCS  = {"NL": _e_NL, "NM": _e_NM, "NS": _e_NS,
             "ZE": _e_ZE, "PS": _e_PS, "PM": _e_PM, "PL": _e_PL}
_R_FUNCS  = {"DN": _r_DN, "ST": _r_ST, "IN": _r_IN}

# Action thresholds
_ACT_POS =  1.0   # output ≥ this → increase_hypnotic
_ACT_NEG = -1.0   # output ≤ this → reduce_hypnotic


class FuzzyPDPolicy(PolicyBase):
    """Mamdani fuzzy PD controller for BIS tracking.

    State: previous BIS error (for derivative term).
    Call reset() between patients.
    """

    def __init__(
        self,
        setpoint_bis: float = _FUZZY_BIS_SETPOINT,
        dt: float = DECISION_INTERVAL_SEC,
        act_pos: float = _ACT_POS,
        act_neg: float = _ACT_NEG,
    ) -> None:
        self.setpoint  = setpoint_bis
        self.dt        = dt
        self.act_pos   = act_pos
        self.act_neg   = act_neg
        self._prev_e   = 0.0
        self._initialized = False

    def reset(self) -> None:
        self._prev_e      = 0.0
        self._initialized = False

    @property
    def name(self) -> str:
        return "FuzzyPD_Shieh2006"

    def _infer(self, e: float, de: float) -> float:
        """Mamdani inference → defuzzified crisp output (weighted mean)."""
        num = 0.0
        den = 0.0
        for (e_l, r_l), output in _RULES.items():
            mu = min(_E_FUNCS[e_l](e), _R_FUNCS[r_l](de))
            if mu > 0:
                num += mu * output
                den += mu
        return num / den if den > 1e-9 else 0.0

    def decide(self, row: Dict[str, Any]) -> str:
        bis   = float(row.get("bis_current", self.setpoint) or self.setpoint)
        map_v = float(row.get("map_current", 80.0) or 80.0)

        # MAP override
        if map_v < MAP_ACC_LO:
            return "no_action"

        e = bis - self.setpoint   # positive → BIS too high → need more propofol

        if not self._initialized:
            self._prev_e      = e
            self._initialized = True

        de = (e - self._prev_e) / self.dt
        self._prev_e = e

        u = self._infer(e, de)

        if u >= self.act_pos:
            return "increase_hypnotic"
        elif u <= self.act_neg:
            return "reduce_hypnotic"
        return "no_action"
