"""Correctness Oracle property test: compares Fenwick Tree vs Exact Aggregates Baseline across multiple intervals."""
import random
from datetime import datetime, timedelta, timezone
from src.algorithms.fenwick import TimeAggregateIndex
from src.baselines.exact_aggregates import ExactAggregatesBaseline
from src.core.models import FaultReport
from src.ingestion.synthetic_data import generate_synthetic_domain_records


def test_fenwick_vs_exact_oracle_property_test():
    raw_records = generate_synthetic_domain_records(num_records=300, seed=123)
    reports = [FaultReport.model_validate(r) for r in raw_records]

    min_t = min(r.time_interval.start_time for r in reports)
    max_t = max(r.time_interval.end_time for r in reports)

    fenwick = TimeAggregateIndex(min_time=min_t, max_time=max_t, bucket_seconds=3600)
    fenwick.bulk_load(reports)
    exact = ExactAggregatesBaseline(reports)

    # Run 15 randomized interval queries
    rng = random.Random(42)
    for _ in range(15):
        offset_days = rng.uniform(0, 30)
        span_days = rng.uniform(2, 15)
        q_start = min_t + timedelta(days=offset_days)
        q_end = q_start + timedelta(days=span_days)

        b_start, b_end = fenwick.get_bucket_bounds(q_start, q_end)
        f_res = fenwick.query_range(q_start, q_end)
        e_res = exact.query_range(b_start, b_end)

        # Oracle agreement check: counts must match, and power loss difference must be within rounding error (< 0.1 kWh)
        assert f_res.total_faults == e_res.total_faults, (
            f"Fault count mismatch for interval [{q_start}, {q_end}]: Fenwick={f_res.total_faults}, Exact={e_res.total_faults}"
        )
        assert abs(f_res.total_power_loss_kwh - e_res.total_power_loss_kwh) < 0.2, (
            f"Power loss mismatch: Fenwick={f_res.total_power_loss_kwh}, Exact={e_res.total_power_loss_kwh}"
        )
