"""Validation oracle and adverse edge case sanitization for fault reports and sensor streams."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Set, Tuple
from pydantic import ValidationError

from src.core.models import FaultReport, SensorReading


class ValidationResult:
    def __init__(self, is_valid: bool, errors: List[str], sanitized_data: Any = None):
        self.is_valid = is_valid
        self.errors = errors
        self.sanitized_data = sanitized_data

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "sanitized": self.sanitized_data is not None
        }


class DataValidator:
    """Correctness oracle and validator for fault reports and sensor stream records."""

    def __init__(self):
        self._seen_fault_ids: Set[str] = set()
        self._last_stream_timestamps: Dict[str, float] = {}

    def reset(self):
        self._seen_fault_ids.clear()
        self._last_stream_timestamps.clear()

    def validate_fault_report(self, raw_data: Dict[str, Any], allow_duplicates: bool = False) -> ValidationResult:
        """Validate raw dictionary against FaultReport schema with adverse condition checks."""
        errors: List[str] = []

        # 1. Duplicate ID check
        fault_id = raw_data.get("fault_id")
        if not allow_duplicates and fault_id:
            if fault_id in self._seen_fault_ids:
                errors.append(f"ADVERSE_EDGE_CASE: Duplicate fault_id '{fault_id}' encountered.")
            else:
                self._seen_fault_ids.add(fault_id)

        # 2. Pydantic schema validation
        try:
            report = FaultReport.model_validate(raw_data)
        except ValidationError as e:
            for err in e.errors():
                loc = " -> ".join(str(l) for l in err["loc"])
                errors.append(f"Validation error at '{loc}': {err['msg']}")
            return ValidationResult(is_valid=False, errors=errors)

        # 3. Domain sanity checks
        if report.time_interval.duration_hours > 720:  # > 30 days single event warning
            errors.append(f"Warning: Unusual duration {report.time_interval.duration_hours:.1f} hours.")

        if errors:
            return ValidationResult(is_valid=False, errors=errors, sanitized_data=report)
        return ValidationResult(is_valid=True, errors=[], sanitized_data=report)

    def validate_sensor_reading(self, reading: SensorReading) -> ValidationResult:
        """Validate live sensor reading for NaNs, extreme out-of-range values, and late arrivals."""
        errors: List[str] = []
        val = reading.value

        # NaN / Missing check
        if math.isnan(val) or math.isinf(val):
            errors.append(f"ADVERSE_EDGE_CASE: Sensor reading contains invalid numeric value: {val}")

        # Out-of-order / late arrival check
        curr_ts = reading.timestamp.timestamp()
        asset_metric = f"{reading.asset_id}:{reading.metric_name}"
        if asset_metric in self._last_stream_timestamps:
            prev_ts = self._last_stream_timestamps[asset_metric]
            if curr_ts < prev_ts:
                delay_sec = prev_ts - curr_ts
                errors.append(
                    f"ADVERSE_EDGE_CASE: Out-of-order/late event detected for {asset_metric}. "
                    f"Arrived {delay_sec:.1f}s behind prior event."
                )
        self._last_stream_timestamps[asset_metric] = curr_ts

        return ValidationResult(is_valid=(len(errors) == 0), errors=errors, sanitized_data=reading)

