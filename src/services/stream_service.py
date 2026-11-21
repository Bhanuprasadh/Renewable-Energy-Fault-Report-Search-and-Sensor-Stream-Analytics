"""Streaming analytics service tracking percentiles via t-digest and detecting concept drift."""
from __future__ import annotations

from collections import deque
from typing import Any, Deque, Dict, List, Optional
from src.algorithms.drift_detector import CUSUMDriftDetector, PageHinkleyDriftDetector
from src.algorithms.tdigest import TDigest
from src.baselines.exact_percentiles import ExactPercentilesBaseline
from src.core.config import AlgorithmConfig
from src.core.models import SensorReading
from src.ingestion.validator import DataValidator


class StreamAnalyticsService:
    """Manages online sensor stream processing, t-digest percentile sketching, and drift alarms."""

    def __init__(self, config: Optional[AlgorithmConfig] = None, max_history: int = 1000):
        self.config = config or AlgorithmConfig()
        self.tdigest = TDigest(delta=self.config.TDIGEST_DELTA)
        self.exact_baseline = ExactPercentilesBaseline()
        self.ph_detector = PageHinkleyDriftDetector(
            delta=self.config.DRIFT_DELTA,
            threshold_lambda=self.config.DRIFT_LAMBDA,
            alpha=self.config.DRIFT_ALPHA
        )
        self.cusum_detector = CUSUMDriftDetector(target_mean=3.5, threshold_h=8.0)
        self.validator = DataValidator()

        self.reading_history: Deque[SensorReading] = deque(maxlen=max_history)
        self.drift_events: List[Dict[str, Any]] = []
        self.anomaly_count = 0
        self.validation_errors: List[str] = []

    def reset(self) -> None:
        self.tdigest = TDigest(delta=self.config.TDIGEST_DELTA)
        self.exact_baseline = ExactPercentilesBaseline()
        self.ph_detector.reset()
        self.cusum_detector.reset()
        self.validator.reset()
        self.reading_history.clear()
        self.drift_events.clear()
        self.anomaly_count = 0
        self.validation_errors.clear()

    def process_reading(self, reading: SensorReading) -> Dict[str, Any]:
        """Ingest single sensor reading through validation, t-digest sketch, and drift detector."""
        val_res = self.validator.validate_sensor_reading(reading)
        if not val_res.is_valid:
            self.validation_errors.extend(val_res.errors)
            return {
                "reading": reading,
                "is_valid": False,
                "errors": val_res.errors,
                "drift_alert": False,
                "ph_stat": 0.0
            }

        val = reading.value
        self.reading_history.append(reading)

        # Update t-digest and exact baseline
        self.tdigest.update(val)
        self.exact_baseline.update(val)

        # Drift detection
        ph_drift, ph_meta = self.ph_detector.update(val)
        cusum_drift, cusum_meta = self.cusum_detector.update(val)

        has_drift = ph_drift or cusum_drift
        if has_drift:
            self.anomaly_count += 1
            event = {
                "step": len(self.reading_history),
                "timestamp": reading.timestamp.isoformat(),
                "asset_id": reading.asset_id,
                "metric_name": reading.metric_name,
                "value": val,
                "page_hinkley_drift": ph_drift,
                "cusum_drift": cusum_drift,
                "ph_stat": ph_meta.get("ph_stat", 0.0),
                "running_mean": ph_meta.get("mean", 0.0)
            }
            self.drift_events.append(event)

        return {
            "reading": reading,
            "is_valid": True,
            "errors": [],
            "drift_alert": has_drift,
            "ph_stat": ph_meta.get("ph_stat", 0.0),
            "running_mean": ph_meta.get("running_mean", val),
            "percentiles": self.tdigest.get_percentiles_summary()
        }

    def get_percentile_comparison(self) -> Dict[str, Any]:
        """Compare t-digest sketch percentiles against exact sorted baseline (error & memory)."""
        td_summary = self.tdigest.get_percentiles_summary()
        exact_summary = self.exact_baseline.get_percentiles_summary()

        errors = {}
        for k in ["p50", "p90", "p95", "p99"]:
            ev = exact_summary.get(k, 0.0)
            tv = td_summary.get(k, 0.0)
            abs_err = abs(tv - ev)
            rel_err = (abs_err / abs(ev) * 100.0) if ev != 0.0 else 0.0
            errors[k] = {
                "exact": round(ev, 3),
                "tdigest": round(tv, 3),
                "abs_error": round(abs_err, 4),
                "rel_error_pct": round(rel_err, 2)
            }

        return {
            "samples_processed": len(self.reading_history),
            "tdigest_memory_bytes": self.tdigest.memory_bytes(),
            "exact_memory_bytes": self.exact_baseline.memory_bytes(),
            "memory_reduction_ratio": round(self.exact_baseline.memory_bytes() / max(1, self.tdigest.memory_bytes()), 2),
            "comparison": errors
        }

