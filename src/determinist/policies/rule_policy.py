"""
policies/rule_policy.py — Clinical threshold rule-based policy (brazo D).

Implements a deterministic lookup-table controller reproducing the
"standard clinical protocol" baseline used in closed-loop comparative
studies (e.g. Liu 2006 Anesth Analg, Sakai 2000 Anesth Analg).

Decision logic (evaluated in priority order each window)
---------------------------------------------------------
1. MAP < 55        → vasopressor          (severe hypotension)
2. MAP < 65        → vasopressor          (moderate hypotension)
3. BIS > 70        → increase_hypnotic    (awareness zone)
4. BIS > 60        → increase_hypnotic    (light anaesthesia)
5. BIS < 30        → reduce_hypnotic      (critical overdose)
6. BIS < 40        → reduce_hypnotic      (deep hypnosis)
7. HR < 45         → reduce_opioid        (bradycardia — attenuate opioid)
8. else            → no_action

No memory or integration — purely reactive.
"""
from __future__ import annotations
from typing import Any, Dict
from .base import PolicyBase
from config import (
    BIS_ACC_LO, BIS_ACC_HI, BIS_MARG_LO, BIS_MARG_HI,
    MAP_ACC_LO, MAP_SEVERE_THR,
    HR_MARG_LO,
)


class RuleBasedPolicy(PolicyBase):
    """Deterministic threshold-lookup controller.

    Stateless — no reset() needed.
    """

    @property
    def name(self) -> str:
        return "RuleBased_Liu2006"

    def decide(self, row: Dict[str, Any]) -> str:
        bis   = float(row.get("bis_current", 50) or 50)
        map_v = float(row.get("map_current", 80) or 80)
        hr_v  = float(row.get("hr_current",  70) or 70)

        # Priority 1-2: MAP safety
        if map_v < MAP_ACC_LO:
            return "no_action"

        # Priority 3-4: awareness / light anaesthesia
        if bis > BIS_MARG_HI:        # > 65
            return "increase_hypnotic"
        if bis > BIS_ACC_HI:         # > 60
            return "increase_hypnotic"

        # Priority 5-6: overdose
        if bis < BIS_MARG_LO:        # < 35
            return "reduce_hypnotic"
        if bis < BIS_ACC_LO:         # < 40
            return "reduce_hypnotic"

        # Priority 7: bradycardia
        if hr_v < HR_MARG_LO:        # < 45
            return "reduce_opioid"

        return "no_action"

    def reset(self) -> None:
        pass
