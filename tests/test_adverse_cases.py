"""Adverse edge-case tests: duplicate IDs, missing values, corrupt ranges, and late arrivals."""
import math
from datetime import datetime, timedelta, timezone
from src.core.models import SensorReading
from src.ingestion.validator import DataValidator


def test_duplicate_fault_id_detection():
    validator = DataValidator()
    raw = {
        "fault_id": "FLT-DUP-001",
        "asset_id": "SOLAR-CA-001",
        "asset_type": "SOLAR_PV",
        "component": "INVERTER",
        "severity": "LOW",
        "time_interval": {
            "start_time": "2026-01-01T10:00:00Z",
            "end_time": "2026-01-01T12:00:00Z"
        },
        "sensor_range": {
            "metric_name": "Voltage",
            "min_val": 10.0,
            "max_val": 20.0,
            "unit": "V"
        },
        "fault_description": "First report",
        "maintenance_notes": "None",
        "root_cause_category": "Normal",
        "power_loss_kwh": 50.0,
        "created_at": "2026-01-01T10:00:00Z",
        "updated_at": "2026-01-01T12:00:00Z"
    }

    res1 = validator.validate_fault_report(raw)
    assert res1.is_valid is True

    # Same fault_id again
    res2 = validator.validate_fault_report(raw)
    assert res2.is_valid is False
    assert any("Duplicate fault_id" in err for err in res2.errors)


def test_corrupted_nan_sensor_reading():
    validator = DataValidator()
    reading = SensorReading(
        reading_id="READ-001",
        asset_id="WIND-TX-001",
        timestamp=datetime.now(timezone.utc),
        metric_name="Vibration",
        value=float("nan"),
        unit="mm/s"
    )
    res = validator.validate_sensor_reading(reading)
    assert res.is_valid is False
    assert any("invalid numeric value" in err for err in res.errors)


def test_out_of_order_late_arrival():
    validator = DataValidator()
    t_now = datetime.now(timezone.utc)
    
    r1 = SensorReading(
        reading_id="READ-001",
        asset_id="WIND-TX-001",
        timestamp=t_now,
        metric_name="Vibration",
        value=3.2,
        unit="mm/s"
    )
    validator.validate_sensor_reading(r1)

    # Late arrival timestamped 30 seconds BEFORE r1
    r_late = SensorReading(
        reading_id="READ-002",
        asset_id="WIND-TX-001",
        timestamp=t_now - timedelta(seconds=30),
        metric_name="Vibration",
        value=3.1,
        unit="mm/s"
    )
    res_late = validator.validate_sensor_reading(r_late)
    assert res_late.is_valid is False
    assert any("Out-of-order/late event detected" in err for err in res_late.errors)

