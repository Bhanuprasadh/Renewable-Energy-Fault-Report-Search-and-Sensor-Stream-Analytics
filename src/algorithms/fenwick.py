"""Fenwick Tree (Binary Indexed Tree) for O(log N) time-interval prefix and range aggregations."""
from __future__ import annotations

import math
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
from src.core.models import FaultReport, RangeAggregateResult


class FenwickTree:
    """1D Binary Indexed Tree for prefix and range sum queries in O(log N) time."""

    def __init__(self, size: int):
        self.size = size
        self.tree: List[float] = [0.0] * (size + 1)

    def update(self, idx: int, delta: float) -> None:
        """Add delta to element at 1-based index idx."""
        if idx <= 0 or idx > self.size:
            return
        while idx <= self.size:
            self.tree[idx] += delta
            idx += idx & (-idx)

    def query_prefix(self, idx: int) -> float:
        """Query cumulative sum in range [1, idx]."""
        if idx <= 0:
            return 0.0
        idx = min(idx, self.size)
        total = 0.0
        while idx > 0:
            total += self.tree[idx]
            idx -= idx & (-idx)
        return total

    def query_range(self, left: int, right: int) -> float:
        """Query sum in range [left, right] (1-based inclusive)."""
        if left > right or right <= 0 or left > self.size:
            return 0.0
        left = max(1, left)
        right = min(self.size, right)
        return self.query_prefix(right) - self.query_prefix(left - 1)


class TimeAggregateIndex:
    """Discretized Fenwick Tree index over timestamp intervals for rapid range aggregation."""

    def __init__(
        self,
        min_time: datetime,
        max_time: datetime,
        bucket_seconds: int = 3600
    ):
        self.min_time = min_time.astimezone(timezone.utc)
        self.max_time = max_time.astimezone(timezone.utc)
        self.bucket_seconds = bucket_seconds

        total_seconds = max(1.0, (self.max_time - self.min_time).total_seconds())
        self.num_buckets = max(1, math.ceil(total_seconds / self.bucket_seconds))

        # Separate Fenwick trees for power loss and fault count
        self.power_loss_tree = FenwickTree(self.num_buckets)
        self.fault_count_tree = FenwickTree(self.num_buckets)
        
        # Severity-specific Fenwick trees
        self.severity_trees: Dict[str, FenwickTree] = {
            "LOW": FenwickTree(self.num_buckets),
            "MEDIUM": FenwickTree(self.num_buckets),
            "HIGH": FenwickTree(self.num_buckets),
            "CRITICAL": FenwickTree(self.num_buckets)
        }

    def _time_to_bucket(self, dt: datetime) -> int:
        """Convert a datetime to 1-based bucket index."""
        dt_utc = dt.astimezone(timezone.utc)
        offset_sec = (dt_utc - self.min_time).total_seconds()
        bucket = int(offset_sec // self.bucket_seconds) + 1
        return max(1, min(self.num_buckets, bucket))

    def get_bucket_bounds(self, start_time: datetime, end_time: datetime) -> Tuple[datetime, datetime]:
        """Return the exact start and end datetimes of the bucket range covered by start_time to end_time."""
        from datetime import timedelta
        left_bucket = self._time_to_bucket(start_time)
        right_bucket = self._time_to_bucket(end_time)

        b_start = self.min_time + timedelta(seconds=(left_bucket - 1) * self.bucket_seconds)
        b_end = self.min_time + timedelta(seconds=right_bucket * self.bucket_seconds)
        return b_start, b_end

    def insert_fault(self, report: FaultReport) -> None:
        """Index a fault report into the corresponding discretized time bucket."""
        if report.is_deleted:
            return
        bucket = self._time_to_bucket(report.time_interval.start_time)
        self.power_loss_tree.update(bucket, report.power_loss_kwh)
        self.fault_count_tree.update(bucket, 1.0)
        
        sev = report.severity.value
        if sev in self.severity_trees:
            self.severity_trees[sev].update(bucket, 1.0)

    def bulk_load(self, reports: List[FaultReport]) -> None:
        """Bulk load a list of fault reports."""
        for r in reports:
            self.insert_fault(r)

    def query_range(self, start_time: datetime, end_time: datetime) -> RangeAggregateResult:
        """Execute O(log B) range query across time bounds."""
        start_perf = time.perf_counter()
        left_bucket = self._time_to_bucket(start_time)
        right_bucket = self._time_to_bucket(end_time)

        total_loss = self.power_loss_tree.query_range(left_bucket, right_bucket)
        total_count = int(self.fault_count_tree.query_range(left_bucket, right_bucket))

        sev_counts = {
            sev: int(tree.query_range(left_bucket, right_bucket))
            for sev, tree in self.severity_trees.items()
        }

        elapsed_ms = (time.perf_counter() - start_perf) * 1000.0
        return RangeAggregateResult(
            query_start=start_time,
            query_end=end_time,
            total_faults=total_count,
            total_power_loss_kwh=round(total_loss, 2),
            severity_counts=sev_counts,
            execution_time_ms=elapsed_ms,
            algorithm_used="FenwickTree"
        )
