"""Baseline O(N) range aggregate calculator for correctness oracle."""
from __future__ import annotations

import time
from datetime import datetime
from typing import Dict, List
from src.core.models import FaultReport, RangeAggregateResult


class ExactAggregatesBaseline:
    """Exact O(N) linear range aggregation serving as ground-truth oracle for Fenwick Tree."""

    def __init__(self, records: List[FaultReport]):
        self.records = records

    def query_range(self, start_time: datetime, end_time: datetime) -> RangeAggregateResult:
        start_perf = time.perf_counter()
        total_faults = 0
        total_power_loss = 0.0
        severity_counts: Dict[str, int] = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}

        for r in self.records:
            if r.is_deleted:
                continue
            # Event timestamp is contained within query window
            r_start = r.time_interval.start_time
            if start_time <= r_start <= end_time:
                total_faults += 1
                total_power_loss += r.power_loss_kwh
                severity_counts[r.severity.value] += 1

        elapsed_ms = (time.perf_counter() - start_perf) * 1000.0
        return RangeAggregateResult(
            query_start=start_time,
            query_end=end_time,
            total_faults=total_faults,
            total_power_loss_kwh=round(total_power_loss, 2),
            severity_counts=severity_counts,
            execution_time_ms=elapsed_ms,
            algorithm_used="LinearScanBaseline"
        )

