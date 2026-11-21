"""Unit tests for Page-Hinkley and CUSUM streaming drift detection."""
import numpy as np
from src.algorithms.drift_detector import CUSUMDriftDetector, PageHinkleyDriftDetector


def test_page_hinkley_drift_detection():
    detector = PageHinkleyDriftDetector(delta=0.05, threshold_lambda=30.0, alpha=0.99)
    np.random.seed(42)

    # Phase 1: Stationary baseline (no drift expected)
    stationary = np.random.normal(loc=5.0, scale=0.2, size=150)
    drift_seen = False
    for val in stationary:
        drift, _ = detector.update(val)
        if drift:
            drift_seen = True
    assert not drift_seen, "False positive drift detected in stationary series."

    # Phase 2: Gradual upward drift (degradation onset)
    drifting = [5.0 + 0.08 * i + np.random.normal(0, 0.2) for i in range(1, 100)]
    drift_detected = False
    for val in drifting:
        drift, _ = detector.update(val)
        if drift:
            drift_detected = True
            break
    assert drift_detected, "Page-Hinkley failed to detect gradual upward drift."


def test_cusum_abrupt_step_drift():
    detector = CUSUMDriftDetector(target_mean=10.0, threshold_h=6.0)

    # Stationary at target
    for _ in range(50):
        drift, _ = detector.update(10.0 + np.random.normal(0, 0.1))
        assert not drift

    # Sudden step increase to 18.0
    step_detected = False
    for _ in range(15):
        drift, _ = detector.update(18.0)
        if drift:
            step_detected = True
            break
    assert step_detected, "CUSUM failed to detect abrupt step change."

