"""Baseline exact percentile calculator storing all streaming values in memory."""
from __future__ import annotations

import sys
from typing import Dict, List
import numpy as np


class ExactPercentilesBaseline:
    """Stores full stream history and calculates exact percentiles via sorting (O(N log N) / O(N) space)."""

    def __init__(self):
        self.values: List[float] = []

    def update(self, value: float) -> None:
        self.values.append(value)

    def get_percentile(self, q: float) -> float:
        """q in [0, 100]. Returns exact percentile."""
        if not self.values:
            return 0.0
        return float(np.percentile(self.values, q))

    def get_percentiles_summary(self) -> Dict[str, float]:
        if not self.values:
            return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0}
        arr = np.array(self.values)
        return {
            "p50": float(np.percentile(arr, 50)),
            "p90": float(np.percentile(arr, 90)),
            "p95": float(np.percentile(arr, 95)),
            "p99": float(np.percentile(arr, 99))
        }

    def memory_bytes(self) -> int:
        return sys.getsizeof(self.values) + len(self.values) * 8

