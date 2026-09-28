"""
policies/base.py — Abstract policy interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class PolicyBase(ABC):
    """Abstract base class for anesthesia policies.

    A policy receives a row dict (AnesLLM v2 parquet format) and returns
    one of BENCH_ACTIONS as a str.
    """

    @abstractmethod
    def decide(self, row: Dict[str, Any]) -> str:
        """Return an action token given the current clinical row.

        Parameters
        ----------
        row : dict
            A windows_annotated_v2-compatible row built by encoder.encode_row().

        Returns
        -------
        str — one of BENCH_ACTIONS
        """

    def reset(self) -> None:
        """Reset any internal state for a new patient episode (default: no-op)."""

    @property
    def name(self) -> str:
        return self.__class__.__name__
