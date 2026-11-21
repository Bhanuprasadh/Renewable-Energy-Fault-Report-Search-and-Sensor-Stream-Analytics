"""Unit tests for Pydantic domain models and validation rules."""
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError
from src.core.models import AssetType, Component, FaultReport, SensorRange, Severity, TimeInterval


def test_valid_time_interval():
    t1 = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 1, 1, 15, 0, tzinfo=timezone.utc)
    interval = TimeInterval(start_time=t1, end_time=t2)
    assert interval.duration_hours == 5.0


def test_invalid_time_interval_raises_error():
    t1 = datetime(2026, 1, 1, 15, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    with pytest.raises(ValidationError):
        TimeInterval(start_time=t1, end_time=t2)


def test_invalid_sensor_range_raises_error():
    with pytest.raises(ValidationError):
        SensorRange(metric_name="Temperature", min_val=100.0, max_val=50.0, unit="Celsius")


def test_severity_level_ranking():
    assert Severity.LOW.level < Severity.MEDIUM.level
    assert Severity.MEDIUM.level < Severity.HIGH.level
    assert Severity.HIGH.level < Severity.CRITICAL.level

