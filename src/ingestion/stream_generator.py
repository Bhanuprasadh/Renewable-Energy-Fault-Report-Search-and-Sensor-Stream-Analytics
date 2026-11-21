"""Synthetic sensor stream generator with drift injection, noise, and adverse edge cases."""
from __future__ import annotations

import math
import random
from datetime import datetime, timedelta, timezone
from typing import Generator, List, Optional
from src.core.models import SensorReading


class SensorStreamGenerator:
    """Generates continuous timestamped sensor telemetry with stationary, drifting, and corrupted modes."""

    def __init__(
        self,
        asset_id: str = "WIND-TX-001",
        metric_name: str = "Bearing_Vibration_RMS",
        unit: str = "mm/s",
        base_value: float = 3.5,
        noise_std: float = 0.35,
        start_time: Optional[datetime] = None,
        sample_interval_sec: int = 5,
        seed: int = 42
    ):
        self.asset_id = asset_id
        self.metric_name = metric_name
        self.unit = unit
        self.base_value = base_value
        self.noise_std = noise_std
        self.current_time = start_time or datetime(2026, 4, 1, 0, 0, 0, tzinfo=timezone.utc)
        self.sample_interval = timedelta(seconds=sample_interval_sec)
        self.step_count = 0
        self.rng = random.Random(seed)

    def generate_reading(
        self,
        drift_slope: float = 0.0,
        abrupt_jump: float = 0.0,
        inject_nan: bool = False,
        inject_spike: bool = False,
        inject_negative: bool = False,
        out_of_order_offset_sec: int = 0
    ) -> SensorReading:
        """Produce a single sensor reading with optional anomaly or drift parameters."""
        self.step_count += 1
        t = self.current_time + (self.sample_interval * self.step_count)
        if out_of_order_offset_sec != 0:
            t = t - timedelta(seconds=out_of_order_offset_sec)

        # Baseline sinusoidal diurnal pattern + gaussian noise
        diurnal = 0.2 * math.sin(2 * math.pi * self.step_count / 100.0)
        noise = self.rng.gauss(0, self.noise_std)
        drift = drift_slope * self.step_count
        val = self.base_value + diurnal + noise + drift + abrupt_jump

        if inject_nan:
            val = float("nan")
        elif inject_spike:
            val += self.base_value * 5.0
        elif inject_negative:
            val = -abs(val)

        is_anom = (drift_slope != 0.0) or (abrupt_jump != 0.0) or inject_spike or inject_negative

        reading_id = f"READ-{self.asset_id}-{self.step_count:06d}"
        return SensorReading(
            reading_id=reading_id,
            asset_id=self.asset_id,
            timestamp=t,
            metric_name=self.metric_name,
            value=round(val, 4) if not math.isnan(val) else val,
            unit=self.unit,
            is_anomalous=is_anom
        )

    def generate_stream(
        self,
        total_steps: int = 500,
        drift_start_step: int = 250,
        drift_slope: float = 0.025,
        inject_adverse_cases: bool = True
    ) -> Generator[SensorReading, None, None]:
        """Yield a stream of sensor readings with normal phase, drift phase, and rare edge cases."""
        for step in range(1, total_steps + 1):
            curr_drift = drift_slope if step >= drift_start_step else 0.0
            nan_flag = False
            spike_flag = False
            late_sec = 0

            # Inject adverse edge cases if requested
            if inject_adverse_cases:
                if step == 50:
                    nan_flag = True  # Missing value
                elif step == 120:
                    spike_flag = True  # Sensor glitch spike
                elif step == 180:
                    late_sec = 60  # Late arrival (out-of-order)

            yield self.generate_reading(
                drift_slope=curr_drift,
                inject_nan=nan_flag,
                inject_spike=spike_flag,
                out_of_order_offset_sec=late_sec
            )

