"""Unit tests for Fenwick Tree (Binary Indexed Tree) prefix and range aggregations."""
from datetime import datetime, timedelta, timezone
from src.algorithms.fenwick import FenwickTree, TimeAggregateIndex
from src.core.models import AssetType, Component, FaultReport, SensorRange, Severity, TimeInterval


def test_fenwick_tree_basic_prefix_and_range():
    ft = FenwickTree(10)
    # Add values: index 2 += 5.0, index 5 += 3.0, index 7 += 2.0
    ft.update(2, 5.0)
    ft.update(5, 3.0)
    ft.update(7, 2.0)

    assert ft.query_prefix(1) == 0.0
    assert ft.query_prefix(2) == 5.0
    assert ft.query_prefix(5) == 8.0
    assert ft.query_prefix(10) == 10.0

    # Range [2, 5] -> 5 + 3 = 8
    assert ft.query_range(2, 5) == 8.0
    # Range [6, 8] -> 2
    assert ft.query_range(6, 8) == 2.0
    # Range [3, 4] -> 0
    assert ft.query_range(3, 4) == 0.0


def test_time_aggregate_index_range_sum(sample_fault_report):
    t_start = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    t_end = datetime(2026, 1, 10, 0, 0, tzinfo=timezone.utc)
    
    idx = TimeAggregateIndex(min_time=t_start, max_time=t_end, bucket_seconds=3600)
    idx.insert_fault(sample_fault_report)

    # Query range covering the report
    res = idx.query_range(
        datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 2, 0, 0, tzinfo=timezone.utc)
    )
    assert res.total_faults == 1
    assert res.total_power_loss_kwh == 3200.0
    assert res.severity_counts["HIGH"] == 1
    assert res.severity_counts["LOW"] == 0

    # Query outside range
    res_outside = idx.query_range(
        datetime(2026, 1, 5, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 6, 0, 0, tzinfo=timezone.utc)
    )
    assert res_outside.total_faults == 0
    assert res_outside.total_power_loss_kwh == 0.0

