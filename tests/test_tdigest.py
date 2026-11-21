"""Unit tests for t-Digest streaming quantile sketch."""
import numpy as np
from src.algorithms.tdigest import TDigest
from src.baselines.exact_percentiles import ExactPercentilesBaseline


def test_tdigest_accuracy_on_normal_distribution():
    np.random.seed(42)
    data = np.random.normal(loc=10.0, scale=2.5, size=2000).tolist()

    td = TDigest(delta=100.0)
    exact = ExactPercentilesBaseline()

    for x in data:
        td.update(x)
        exact.update(x)

    td_summary = td.get_percentiles_summary()
    exact_summary = exact.get_percentiles_summary()

    # Monotonicity check
    assert td_summary["p50"] <= td_summary["p90"] <= td_summary["p95"] <= td_summary["p99"]

    # Accuracy within tight tolerances (<= 3.5% relative error)
    for p in ["p50", "p90", "p95", "p99"]:
        abs_err = abs(td_summary[p] - exact_summary[p])
        rel_err = (abs_err / exact_summary[p]) * 100.0
        assert rel_err < 3.5, f"Percentile {p} relative error {rel_err:.2f}% exceeds tolerance."


def test_tdigest_merge():
    td1 = TDigest(delta=50.0)
    td2 = TDigest(delta=50.0)

    for i in range(1, 101):
        td1.update(float(i))
    for i in range(101, 201):
        td2.update(float(i))

    merged = td1.merge(td2)
    assert merged.total_weight == 200.0
    # Median of 1..200 is 100.5
    median_val = merged.percentile(50.0)
    assert 95.0 <= median_val <= 106.0

