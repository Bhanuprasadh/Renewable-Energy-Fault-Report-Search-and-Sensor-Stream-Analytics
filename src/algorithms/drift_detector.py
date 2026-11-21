"""Streaming concept drift detectors (Page-Hinkley and CUSUM) for sensor degradation."""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple


class PageHinkleyDriftDetector:
    """Page-Hinkley test for detecting gradual degradation (concept drift) in continuous streams.
    
    Maintains cumulative difference between streaming values and rolling mean,
    flagging when cumulative deviance exceeds decision threshold lambda.
    """

    def __init__(
        self,
        delta: float = 0.05,
        threshold_lambda: float = 50.0,
        alpha: float = 0.995,
        min_instances: int = 30
    ):
        self.delta = delta
        self.threshold_lambda = threshold_lambda
        self.alpha = alpha
        self.min_instances = min_instances
        self.reset()

    def reset(self) -> None:
        self.sample_count = 0
        self.mean = 0.0
        self.sum_diff = 0.0
        self.min_sum_diff = float("inf")
        self.drift_detected = False
        self.history_values: List[float] = []

    def update(self, val: float) -> Tuple[bool, Dict[str, float]]:
        """Feed new observation. Returns (drift_detected_flag, telemetry_dict)."""
        if math.isnan(val) or math.isinf(val):
            return False, {"stat": 0.0, "mean": self.mean}

        self.sample_count += 1
        self.history_values.append(val)

        # Update fading / running mean
        if self.sample_count == 1:
            self.mean = val
        else:
            self.mean = self.alpha * self.mean + (1.0 - self.alpha) * val

        # Cumulative difference
        self.sum_diff += (val - self.mean - self.delta)
        if self.sum_diff < self.min_sum_diff:
            self.min_sum_diff = self.sum_diff

        # Page-Hinkley statistic
        ph_stat = self.sum_diff - self.min_sum_diff
        self.drift_detected = False

        if self.sample_count > self.min_instances and ph_stat > self.threshold_lambda:
            self.drift_detected = True
            # Auto-reset after flagging drift to detect subsequent drifts
            self.sum_diff = 0.0
            self.min_sum_diff = float("inf")

        telemetry = {
            "step": self.sample_count,
            "val": val,
            "running_mean": round(self.mean, 4),
            "ph_stat": round(ph_stat, 4),
            "threshold": self.threshold_lambda,
            "drift_detected": float(self.drift_detected)
        }
        return self.drift_detected, telemetry


class CUSUMDriftDetector:
    """Cumulative Sum (CUSUM) test for rapid detection of abrupt mean step-changes."""

    def __init__(self, target_mean: float, slack_k: float = 0.5, threshold_h: float = 5.0):
        self.target_mean = target_mean
        self.slack_k = slack_k
        self.threshold_h = threshold_h
        self.s_pos = 0.0
        self.s_neg = 0.0
        self.step = 0

    def reset(self) -> None:
        self.s_pos = 0.0
        self.s_neg = 0.0
        self.step = 0

    def update(self, val: float) -> Tuple[bool, Dict[str, float]]:
        self.step += 1
        self.s_pos = max(0.0, self.s_pos + (val - self.target_mean - self.slack_k))
        self.s_neg = max(0.0, self.s_neg - (val - self.target_mean + self.slack_k))

        drift = (self.s_pos > self.threshold_h) or (self.s_neg > self.threshold_h)
        if drift:
            # reset accumulators
            self.s_pos = 0.0
            self.s_neg = 0.0

        return drift, {
            "step": self.step,
            "s_pos": round(self.s_pos, 3),
            "s_neg": round(self.s_neg, 3),
            "threshold": self.threshold_h,
            "abrupt_drift": float(drift)
        }

