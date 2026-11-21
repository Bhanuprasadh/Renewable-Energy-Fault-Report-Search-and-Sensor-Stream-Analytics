"""Test suite configuration and shared fixtures."""
from datetime import datetime, timezone
import pytest
from src.core.models import AssetType, Component, FaultReport, SensorRange, Severity, TimeInterval


@pytest.fixture
def sample_fault_report() -> FaultReport:
    return FaultReport(
        fault_id="FLT-TEST-001",
        asset_id="WIND-TX-999",
        asset_type=AssetType.WIND_TURBINE,
        component=Component.GEARBOX,
        severity=Severity.HIGH,
        time_interval=TimeInterval(
            start_time=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 1, 1, 14, 0, tzinfo=timezone.utc)
        ),
        sensor_range=SensorRange(
            metric_name="Bearing_Vibration_RMS",
            min_val=4.5,
            max_val=11.2,
            unit="mm/s"
        ),
        fault_description="High-speed planetary pinion gear teeth pitting.",
        maintenance_notes="Lubrication oil filtered and pinion gear relubricated.",
        root_cause_category="Mechanical Wear",
        power_loss_kwh=3200.0,
        version=1,
        is_deleted=False,
        created_at=datetime(2026, 1, 1, 10, 15, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, 14, 30, tzinfo=timezone.utc)
    )

