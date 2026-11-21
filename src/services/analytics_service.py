"""Time-series analytics service comparing Fenwick Tree aggregations with baseline linear scan."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from src.algorithms.fenwick import TimeAggregateIndex
from src.baselines.exact_aggregates import ExactAggregatesBaseline
from src.core.config import AlgorithmConfig
from src.core.models import FaultReport, RangeAggregateResult


class AnalyticsService:
    """Manages Fenwick tree range indexes and benchmarks performance against linear scans."""

    def __init__(self, config: Optional[AlgorithmConfig] = None):
        self.config = config or AlgorithmConfig()
        self.fenwick_index: Optional[TimeAggregateIndex] = None
        self.baseline_index: Optional[ExactAggregatesBaseline] = None
        self.reports: List[FaultReport] = []

    def load_reports(self, reports: List[FaultReport]) -> None:
        """Construct both Fenwick tree and Baseline scanner."""
        self.reports = [r for r in reports if not r.is_deleted]
        if not self.reports:
            return

        min_time = min(r.time_interval.start_time for r in self.reports)
        max_time = max(r.time_interval.end_time for r in self.reports)

        self.fenwick_index = TimeAggregateIndex(
            min_time=min_time,
            max_time=max_time,
            bucket_seconds=self.config.FENWICK_BUCKET_SECONDS
        )
        self.fenwick_index.bulk_load(self.reports)
        self.baseline_index = ExactAggregatesBaseline(self.reports)

    def query_range_comparison(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Run range query on both Fenwick Tree and Baseline Scan, verifying identical results."""
        if not self.fenwick_index or not self.baseline_index:
            raise RuntimeError("AnalyticsService has no reports loaded.")

        b_start, b_end = self.fenwick_index.get_bucket_bounds(start_time, end_time)
        fenwick_res = self.fenwick_index.query_range(start_time, end_time)
        baseline_res = self.baseline_index.query_range(b_start, b_end)

        speedup = (baseline_res.execution_time_ms / max(0.0001, fenwick_res.execution_time_ms))
        power_loss_diff = abs(fenwick_res.total_power_loss_kwh - baseline_res.total_power_loss_kwh)
        count_diff = abs(fenwick_res.total_faults - baseline_res.total_faults)

        is_verified = (count_diff == 0) and (power_loss_diff < 0.1)

        return {
            "query_window": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "fenwick": fenwick_res.model_dump(),
            "baseline": baseline_res.model_dump(),
            "speedup_factor": round(speedup, 2),
            "results_match_oracle": is_verified,
            "power_loss_diff_kwh": round(power_loss_diff, 4)
        }
