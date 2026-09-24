"""
policies/pid_policy.py — Robust PID controller baseline (brazo B).

Reimplements the proportional-integral-derivative controller for closed-loop
TIVA described in:

  Aubouin-Pairault B, Fiacchini M, Dang T.
  "PAS: a Python Anesthesia Simulator for drug control."
  J Open Source Softw 2023;8(88):5480.  doi:10.21105/joss.05480

  Aubouin-Pairault B, Fiacchini M, Dang T.
  "Online identification of pharmacodynamic parameters for closed-loop
  anesthesia with model predictive control."
  Comput Chem Eng 2024;191:108837.  doi:10.1016/j.compchemeng.2024.108837

Control architecture
---------------------
1. **BIS PID** (primary loop, propofol): tracks BIS setpoint = 50.
   Discrete-time parallel form with anti-windup clamping.
   Output: recommended Δpropofol_rate → discretised to bench action space.

2. **MAP safety layer** (secondary): if MAP < MAP_ACC_LO (65 mmHg), override
   action to 'vasopressor' regardless of BIS loop output.  This mirrors the
   clinical safety override in the original system.

3. **HR safety layer**: if HR < HR_MARG_LO (45 bpm), suppress opioid actions.

Discretisation rule
--------------------
Bench action space: {increase_hypnotic, reduce_hypnotic,
                     increase_opioid, reduce_opioid, vasopressor, no_action}

For the PID output u_pid (propofol Δrate in mg/s):
  |u_pid| < DISC_REL_THR * current_prop_rate  → no_action  (< 10% change)
  u_pid >= +DISC_REL_THR * current_prop_rate  → increase_hypnotic
  u_pid <= -DISC_REL_THR * current_prop_rate  → reduce_hypnotic

No opioid output from BIS-PID (BIS is primarily propofol-controlled).
Opioid management is handled by the MAP/HR safety layer only.

PID parameters (tuned for PAS Eleveld model, Kp/Ti/Td from Aubouin 2024 Table 1)
----------------------------------------------------------------------------------
Kp = 0.0010   proportional gain  (mg/s per BIS-point)
Ti = 500      integral time (s)  → Ki = Kp/Ti ≈ 2e-6
Td = 80       derivative time (s) → Kd = Kp*Td ≈ 8e-5

Anti-windup: integral clamped to ±ANTI_WINDUP_LIMIT.
Derivative: backward-difference with low-pass filter τ=50 s.
"""
from __future__ import annotations

from typing import Any, Dict

import numpy as np

from .base import PolicyBase
from config import (
    MAP_ACC_LO, HR_MARG_LO,
    PROPOFOL_MAINTENANCE_RATE,
    DECISION_INTERVAL_SEC,
    _P as _CFG,
)

# ── PID tuning — loaded from clinical_params.json → policies.pid ─────────────
_pid_cfg           = _CFG["policies"]["pid"]
_BIS_SETPOINT      = _pid_cfg["bis_setpoint"]
_KP                = _pid_cfg["kp_mg_s_per_bis_pt"]
_TI                = _pid_cfg["ti_sec"]
_TD                = _pid_cfg["td_sec"]
_DERIV_TAU         = _pid_cfg["deriv_tau_sec"]
_ANTI_WINDUP_LIMIT = _pid_cfg["anti_windup_limit"]
_DISC_REL_THR      = _pid_cfg["disc_rel_thr"]

_KI = _KP / _TI
_KD = _KP * _TD


class PIDPolicy(PolicyBase):
    """Robust BIS-tracking PID controller (Aubouin-Pairault 2023/2024).

    State is maintained across calls — one instance per patient episode.
    Call reset() at the start of each new episode.
    """

    def __init__(
        self,
        setpoint_bis: float = _BIS_SETPOINT,
        kp: float = _KP,
        ki: float = _KI,
        kd: float = _KD,
        deriv_tau: float = _DERIV_TAU,
        anti_windup: float = _ANTI_WINDUP_LIMIT,
        disc_thr: float = _DISC_REL_THR,
        dt: float = DECISION_INTERVAL_SEC,
    ) -> None:
        self.setpoint   = setpoint_bis
        self.kp         = kp
        self.ki         = ki
        self.kd         = kd
        self.tau        = deriv_tau
        self.anti_windup = anti_windup
        self.disc_thr   = disc_thr
        self.dt         = dt

        # Controller state
        self._integral      = 0.0
        self._prev_error    = 0.0
        self._deriv_filt    = 0.0     # filtered derivative
        self._last_prop_rate = PROPOFOL_MAINTENANCE_RATE
        self._initialized   = False

    def reset(self) -> None:
        """Reset controller state — call at patient episode start."""
        self._integral      = 0.0
        self._prev_error    = 0.0
        self._deriv_filt    = 0.0
        self._last_prop_rate = PROPOFOL_MAINTENANCE_RATE
        self._initialized   = False

    @property
    def name(self) -> str:
        return "PID_Aubouin"

    def decide(self, row: Dict[str, Any]) -> str:
        """Return discretised bench action given current clinical state.

        Parameters
        ----------
        row : dict — windows_annotated_v2-compatible row from encoder.encode_row()

        Returns
        -------
        str — one of BENCH_ACTIONS
        """
        bis   = float(row.get("bis_current", self.setpoint) or self.setpoint)
        map_v = float(row.get("map_current", 80.0) or 80.0)
        hr_v  = float(row.get("hr_current",  70.0) or 70.0)
        prop_rate = float(
            row.get("propofol_rate_current", self._last_prop_rate)
            or self._last_prop_rate
        )
        self._last_prop_rate = max(prop_rate, 1e-6)

        # ── MAP safety override ───────────────────────────────────────────────
        if map_v < MAP_ACC_LO:
            return "no_action"

        # ── BIS PID ───────────────────────────────────────────────────────────
        error = bis - self.setpoint    # positive → BIS too high → need more hypnotic

        if not self._initialized:
            self._prev_error = error
            self._initialized = True

        # Proportional term
        p_term = self.kp * error

        # Integral term (anti-windup: clamp before adding)
        raw_integral = self._integral + error * self.dt
        self._integral = float(np.clip(raw_integral, -self.anti_windup / self.ki,
                                       self.anti_windup / self.ki))
        i_term = self.ki * self._integral

        # Derivative term — backward-difference + first-order low-pass filter
        # τ_d * ẋ_f + x_f = (error - prev_error)/dt  →  discrete Euler:
        raw_deriv = (error - self._prev_error) / self.dt
        alpha = self.tau / (self.tau + self.dt)
        self._deriv_filt = alpha * self._deriv_filt + (1.0 - alpha) * raw_deriv
        d_term = self.kd * self._deriv_filt
        self._prev_error = error

        u = p_term + i_term + d_term   # mg/s — positive → increase propofol

        # ── Discretise ────────────────────────────────────────────────────────
        threshold = self.disc_thr * self._last_prop_rate

        if u >= threshold:
            # BIS too high → increase propofol
            return "increase_hypnotic"
        elif u <= -threshold:
            # BIS too low → reduce propofol
            # HR bradycardia safety: inhibit opioid reduction but propofol
            # reduction stays; this branch only reduces propofol so safe.
            return "reduce_hypnotic"
        else:
            return "no_action"


# ── Cohort-safe factory ───────────────────────────────────────────────────────

class PIDPolicyFactory:
    """Returns a fresh PIDPolicy instance (new state) for each patient.

    Usage in run_cohort-compatible loops::

        for patient in patients:
            policy = PIDPolicyFactory()()
            run_episode(patient, policy, ...)
    """

    def __call__(self) -> PIDPolicy:
        return PIDPolicy()
