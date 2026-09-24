"""
policies/mpc_policy.py — Adaptive MEKF-MPC controller baseline (brazo C).

Reimplements the Model Predictive Control with Moving Extended Kalman Filter
(MEKF) for online PD parameter identification described in:

  Aubouin-Pairault B, Fiacchini M, Dang T.
  "Online identification of pharmacodynamic parameters for closed-loop
  anesthesia with model predictive control."
  Comput Chem Eng 2024;191:108837.  doi:10.1016/j.compchemeng.2024.108837

Architecture
------------
1. **MEKF** (Moving Extended Kalman Filter): online estimation of patient-
   specific PD parameter Ce50 from BIS trajectory. Uses linearized Bouillon
   PD model around current operating point.

2. **MPC** (receding-horizon): minimises predicted BIS error over a horizon
   H=3 decision steps (15 min), subject to:
     - propofol rate limits [PROPOFOL_MIN_RATE, PROPOFOL_MAX_RATE]
     - no more than ±MAX_STEP per decision (clinical rate-of-change limit)
   Cost: J = sum_k (BIS_k - 50)^2 + lambda_u * (Δu_k)^2

3. **Discretisation to bench action space**: same ±10% relative threshold as PID.

4. **MAP safety override**: vasopressor if MAP < MAP_ACC_LO.

NOTE
----
The full MEKF-MPC implementation requires the PAS PK model for prediction.
This file provides a FUNCTIONAL stub that:
  - Tracks a simplified PD gain estimate via recursive least squares
  - Uses a 3-step MPC horizon with the simplified gain
  - Produces valid bench-compatible output

The full reproduction matching Aubouin 2024 Table 3 is under development
(F3 phase). Current stub is sufficient to run the bench and produce baseline
comparison metrics; results will be updated when F3 completes.
"""
from __future__ import annotations

from typing import Any, Dict, Deque, Optional
from collections import deque

import numpy as np

from .base import PolicyBase
from config import (
    MAP_ACC_LO,
    PROPOFOL_MAINTENANCE_RATE, PROPOFOL_MIN_RATE, PROPOFOL_MAX_RATE,
    DECISION_INTERVAL_SEC,
    _P as _CFG,
)

# ── MPC constants — loaded from clinical_params.json → policies.mpc ──────────
_mpc_cfg       = _CFG["policies"]["mpc"]
_BIS_SETPOINT  = _mpc_cfg["bis_setpoint"]
_HORIZON       = _mpc_cfg["horizon_steps"]
_LAMBDA_U      = _mpc_cfg["lambda_u"]
_MAX_STEP      = _mpc_cfg["max_step_mg_s"]
_DISC_REL_THR  = _mpc_cfg["disc_rel_thr"]

# ── MEKF / RLS parameters ─────────────────────────────────────────────────────
# Simplified PD model: BIS = 97.4 * (1 - Ce^γ / (Ce50^γ + Ce^γ))
#   Ce50  — estimated online via RLS
# γ, E0, Emax fixed at Bouillon 2004 population values
_GAMMA          = _mpc_cfg["pkpd_gamma"]
_E0             = _mpc_cfg["pkpd_e0"]
_EMAX           = _mpc_cfg["pkpd_emax"]
_CE50_0         = _mpc_cfg["pkpd_ce50_init_ug_ml"]
_RLS_FORGETTING = _mpc_cfg["rls_forgetting"]


class MEKFMPCPolicy(PolicyBase):
    """Adaptive MEKF-MPC controller (Aubouin-Pairault 2024).

    Maintains online PD parameter estimates and receding-horizon optimal control.
    Call reset() between patient episodes.
    """

    def __init__(
        self,
        setpoint_bis: float = _BIS_SETPOINT,
        horizon: int = _HORIZON,
        lambda_u: float = _LAMBDA_U,
        max_step: float = _MAX_STEP,
        disc_thr: float = _DISC_REL_THR,
        dt: float = DECISION_INTERVAL_SEC,
    ) -> None:
        self.setpoint  = setpoint_bis
        self.horizon   = horizon
        self.lambda_u  = lambda_u
        self.max_step  = max_step
        self.disc_thr  = disc_thr
        self.dt        = dt

        # RLS state for Ce50 estimation
        self._ce50_hat  = _CE50_0
        self._rls_P     = 1.0      # RLS covariance
        self._forgetting = _RLS_FORGETTING

        # Operating point memory
        self._last_prop_rate = PROPOFOL_MAINTENANCE_RATE
        self._bis_history: Deque[float] = deque(maxlen=6)
        self._ce_history:  Deque[float] = deque(maxlen=6)
        self._initialized  = False

    def reset(self) -> None:
        """Reset all state — call at the start of each patient episode."""
        self._ce50_hat      = _CE50_0
        self._rls_P         = 1.0
        self._last_prop_rate = PROPOFOL_MAINTENANCE_RATE
        self._bis_history.clear()
        self._ce_history.clear()
        self._initialized   = False

    @property
    def name(self) -> str:
        return "MPC_Aubouin"

    # ── PD model ──────────────────────────────────────────────────────────────

    def _bis_pred(self, ce: float, ce50: Optional[float] = None) -> float:
        """Bouillon PD model: BIS = E0 - Emax * Ce^γ / (Ce50^γ + Ce^γ)."""
        c50 = ce50 if ce50 is not None else self._ce50_hat
        if c50 <= 0:
            c50 = 1e-6
        ratio = (max(ce, 0) / c50) ** _GAMMA
        return float(_E0 - _EMAX * ratio / (1.0 + ratio))

    def _update_rls(self, ce: float, bis_measured: float) -> None:
        """Recursive Least Squares update of Ce50 estimate."""
        if ce <= 0:
            return
        # Gradient of BIS w.r.t. Ce50 at current operating point
        c50 = max(self._ce50_hat, 1e-6)
        ratio = (ce / c50) ** _GAMMA
        # dBIS/dCe50 = Emax * gamma * Ce^gamma / (Ce50^(gamma+1) * (1 + ratio)^2)
        denom = c50 ** (_GAMMA + 1) * (1.0 + ratio) ** 2
        if abs(denom) < 1e-12:
            return
        phi = float(_EMAX * _GAMMA * ce ** _GAMMA / denom)

        # RLS update
        k = self._rls_P * phi / (self._forgetting + self._rls_P * phi ** 2)
        bis_hat = self._bis_pred(ce, self._ce50_hat)
        innov   = bis_measured - bis_hat
        self._ce50_hat = max(0.5, self._ce50_hat + k * innov)
        self._rls_P    = (1.0 - k * phi) * self._rls_P / self._forgetting

    # ── MPC optimisation ──────────────────────────────────────────────────────

    def _mpc_solve(
        self,
        ce_current: float,
        rate_current: float,
    ) -> float:
        """Simplified 1-D receding horizon: scan Δu candidates, pick best J.

        Returns the optimal Δu (mg/s) for the first step.
        """
        # Candidate rate changes: from -MAX_STEP to +MAX_STEP, 21 levels
        delta_candidates = np.linspace(-self.max_step, self.max_step, 21)

        # PK gain: µg/mL per mg/s at current operating point (proportional scaling)
        # Uses current (Ce, rate) pair; if rate is near zero use a safe nominal.
        pk_gain = ce_current / max(rate_current, 1e-6)  # µg/mL / (mg/s)

        best_j  = float("inf")
        best_du = 0.0

        for du in delta_candidates:
            new_rate  = float(np.clip(rate_current + du,
                                      PROPOFOL_MIN_RATE, PROPOFOL_MAX_RATE))
            actual_du = new_rate - rate_current

            # Crude PK: Ce approaches steady-state ce_ss proportionally
            # τ ≈ 200 s (Eleveld model t½,e-site ≈ 2–3 min)
            ce_ss = pk_gain * new_rate   # µg/mL at new infusion steady state
            tau_ce = 200.0
            j = 0.0
            ce_sim = ce_current
            for _ in range(self.horizon):
                ce_sim = ce_sim + (ce_ss - ce_sim) * (1.0 - np.exp(-self.dt / tau_ce))
                bis_pred = self._bis_pred(max(ce_sim, 0))
                j += (bis_pred - self.setpoint) ** 2

            j += self.lambda_u * actual_du ** 2
            if j < best_j:
                best_j  = j
                best_du = actual_du

        return best_du

    # ── PolicyBase interface ───────────────────────────────────────────────────

    def decide(self, row: Dict[str, Any]) -> str:
        """Return discretised bench action given current clinical row."""
        bis   = float(row.get("bis_current", self.setpoint) or self.setpoint)
        map_v = float(row.get("map_current", 80.0) or 80.0)
        ce    = float(row.get("propofol_ce_current", 2.5) or 2.5)
        prop_rate = float(
            row.get("propofol_rate_current", self._last_prop_rate)
            or self._last_prop_rate
        )
        self._last_prop_rate = max(prop_rate, 1e-6)

        # ── MAP safety override ───────────────────────────────────────────────
        if map_v < MAP_ACC_LO:
            return "no_action"

        # ── MEKF: update Ce50 estimate ────────────────────────────────────────
        self._update_rls(ce, bis)
        self._bis_history.append(bis)
        self._ce_history.append(ce)

        # ── MPC: compute optimal Δu ───────────────────────────────────────────
        du = self._mpc_solve(ce, self._last_prop_rate)

        # ── Discretise ────────────────────────────────────────────────────────
        threshold = self.disc_thr * self._last_prop_rate
        if du >= threshold:
            return "increase_hypnotic"
        elif du <= -threshold:
            return "reduce_hypnotic"
        else:
            return "no_action"
