# -*- coding: utf-8 -*-
"""Config autocontenida para los baselines deterministas.

Carga clinical_params.json (copia local) y expone solo las constantes que usan
las políticas. Sin referencias externas a D:\\anesllm.
"""
import json
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent


def load_clinical_params(path=None) -> dict:
    p = path or (BENCH_DIR / "clinical_params.json")
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


_P = load_clinical_params()

# ── Tiempo ────────────────────────────────────────────────────────────────────
DECISION_INTERVAL_SEC = _P["simulation"]["decision_interval_sec"]

# ── Dosis / infusiones ────────────────────────────────────────────────────────
PROPOFOL_MAINTENANCE_RATE = _P["maintenance_rates"]["propofol_mg_s"]
_dl = _P["dose_limits"]
PROPOFOL_MIN_RATE = _dl["propofol_min_mg_s"]
PROPOFOL_MAX_RATE = _dl["propofol_max_mg_s"]

# ── Umbrales de daño (legacy) ─────────────────────────────────────────────────
MAP_SEVERE_THR = _P["harm_thresholds"]["map_severe_mmhg"]

# ── Bandas de seguridad (BIS / MAP / HR) ──────────────────────────────────────
_BIS = _P["safety_lanes"]["BIS"]
BIS_ACC_LO = _BIS["acceptable_lo"]
BIS_ACC_HI = _BIS["acceptable_hi"]
BIS_MARG_LO = _BIS["marginal_lo"]
BIS_MARG_HI = _BIS["marginal_hi"]

_MAP = _P["safety_lanes"]["MAP"]
MAP_ACC_LO = _MAP["acceptable_lo"]
MAP_ACC_HI = _MAP["acceptable_hi"]
MAP_MARG_LO = _MAP["marginal_lo"]

_HR = _P["safety_lanes"]["HR"]
HR_ACC_LO = _HR["acceptable_lo"]
HR_ACC_HI = _HR["acceptable_hi"]
HR_MARG_LO = _HR["marginal_lo"]
HR_MARG_HI = _HR["marginal_hi"]
