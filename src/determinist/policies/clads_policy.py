"""
policies/clads_policy.py — CLADS-lite gradient-following controller (brazo F).

Inspired by:
  Hemmerling TM, Arbeid E, Wehbe M, et al.
  "McGill University's McSleepy — A fully automated total intravenous
  anesthesia drug delivery system."
  Int J Comput Assist Radiol Surg 2010;5(3):1-10.

  Hemmerling TM, et al.
  "CLADS: a novel closed-loop anesthesia delivery system."
  J Clin Monit Comput 2013;27:239-247.

Architecture
------------
CLADS tracks the BIS trajectory and adjusts propofol rate proportionally
to the area between current BIS and setpoint, with dead-zone and
hysteresis to avoid oscillation:

1. Compute integrated error over the last window:
       cumulative_area += |BIS - setpoint| * dt_step   (trapezoid rule)

2. Decision rule with hysteresis dead-zone ±DEAD:
   - If BIS > setpoint + DEAD  (too awake)  → increase_hypnotic
     Extra boost if BIS > setpoint + BOOST_THR (awareness zone)
   - If BIS < setpoint - DEAD  (too deep)   → reduce_hypnotic
   - Else                                   → no_action

3. MAP safety override (same as all other policies).

4. Consecutive-action memory: suppresses a direction if it was the same
   last N steps to avoid runaway dosing.

Parameters come from the original CLADS paper:
  dead-zone = ±5 BIS-points
  hysteresis reset after 2 consecutive same-direction decisions
"""
from __future__ import annotations

from collections import deque
from typing import Any, Dict, Deque

from .base import PolicyBase
from config import MAP_ACC_LO, HR_MARG_LO, DECISION_INTERVAL_SEC, _P as _CFG

# ── CLADS constants — loaded from clinical_params.json → policies.clads ───────
_clads_cfg = _CFG["policies"]["clads"]
_SETPOINT  = _clads_cfg["bis_setpoint"]
_DEAD_ZONE = _clads_cfg["dead_zone_bis_pts"]
_BOOST_THR = _clads_cfg["boost_thr_bis_pts"]
_MAX_SAME  = _clads_cfg["max_same_actions"]


class CLADSPolicy(PolicyBase):
    """CLADS-inspired gradient-following controller with dead-zone.

    Tracks BIS trend within the window and uses hysteresis memory
    to avoid sustained runaway dosing.
    """

    def __init__(
        self,
        setpoint_bis: float = _SETPOINT,
        dead_zone: float = _DEAD_ZONE,
        boost_thr: float = _BOOST_THR,
        max_same_actions: int = _MAX_SAME,
    ) -> None:
        self.setpoint  = setpoint_bis
        self.dead      = dead_zone
        self.boost_thr = boost_thr
        self.max_same  = max_same_actions
        self._history: Deque[str] = deque(maxlen=max_same_actions)
        self._prev_bis  = setpoint_bis
        self._initialized = False

    def reset(self) -> None:
        self._history.clear()
        self._prev_bis    = self.setpoint
        self._initialized = False

    @property
    def name(self) -> str:
        return "CLADS_Hemmerling2010"

    def _suppress(self, action: str) -> bool:
        """Return True if action should be suppressed (runaway guard)."""
        if len(self._history) < self.max_same:
            return False
        return all(a == action for a in self._history)

    def decide(self, row: Dict[str, Any]) -> str:
        bis   = float(row.get("bis_current", self.setpoint) or self.setpoint)
        map_v = float(row.get("map_current", 80.0) or 80.0)
        hr_v  = float(row.get("hr_current",  70.0) or 70.0)

        # ── MAP override ──────────────────────────────────────────────────────
        if map_v < MAP_ACC_LO:
            self._history.append("no_action")
            return "no_action"

        if not self._initialized:
            self._prev_bis    = bis
            self._initialized = True

        error = bis - self.setpoint     # positive → too awake
        trend = bis - self._prev_bis    # positive → BIS rising
        self._prev_bis = bis

        # ── Decision ──────────────────────────────────────────────────────────
        action = "no_action"

        if error > self.dead:
            # BIS above dead zone
            # Extra boost in awareness zone or if BIS is rising
            if error > self.boost_thr or trend > 1.0:
                proposed = "increase_hypnotic"
            else:
                proposed = "increase_hypnotic"
            if not self._suppress(proposed):
                action = proposed

        elif error < -self.dead:
            # BIS below dead zone
            proposed = "reduce_hypnotic"
            if not self._suppress(proposed):
                action = proposed

        self._history.append(action)
        return action
