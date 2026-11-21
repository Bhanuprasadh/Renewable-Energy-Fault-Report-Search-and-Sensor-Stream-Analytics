"""Pydantic schemas and domain entities for renewable energy fault reports and sensor streams."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class AssetType(str, Enum):
    SOLAR_PV = "SOLAR_PV"
    WIND_TURBINE = "WIND_TURBINE"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @property
    def level(self) -> int:
        levels = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        return levels[self.value]


class Component(str, Enum):
    # Solar components
    INVERTER = "INVERTER"
    SOLAR_PANEL = "SOLAR_PANEL"
    COMBINER_BOX = "COMBINER_BOX"
    BATTERY_STORAGE = "BATTERY_STORAGE"
    MPPT_CONTROLLER = "MPPT_CONTROLLER"

    # Wind components
    GEARBOX = "GEARBOX"
    GENERATOR = "GENERATOR"
    PITCH_SYSTEM = "PITCH_SYSTEM"
    YAW_SYSTEM = "YAW_SYSTEM"
    ROTOR_BLADE = "ROTOR_BLADE"
    MAIN_BEARING = "MAIN_BEARING"

    # Shared / Grid
    TRANSFORMER = "TRANSFORMER"
    SUBSTATION_BREAKER = "SUBSTATION_BREAKER"


class TimeInterval(BaseModel):
    start_time: datetime
    end_time: datetime

    @model_validator(mode="after")
    def validate_interval(self) -> TimeInterval:
        if self.start_time > self.end_time:
            raise ValueError(f"start_time ({self.start_time}) cannot be after end_time ({self.end_time})")
        return self

    @property
    def duration_hours(self) -> float:
        return (self.end_time - self.start_time).total_seconds() / 3600.0


class SensorRange(BaseModel):
    metric_name: str
    min_val: float
    max_val: float
    unit: str

    @model_validator(mode="after")
    def validate_range(self) -> SensorRange:
        if self.min_val > self.max_val:
            raise ValueError(f"min_val ({self.min_val}) cannot exceed max_val ({self.max_val})")
        return self


class FaultReport(BaseModel):
    fault_id: str = Field(..., description="Stable fault report identifier, e.g. FLT-00100")
    asset_id: str = Field(..., description="Asset identifier, e.g. WIND-TX-042")
    asset_type: AssetType
    component: Component
    severity: Severity
    time_interval: TimeInterval
    sensor_range: SensorRange
    fault_description: str
    maintenance_notes: str
    root_cause_category: str
    power_loss_kwh: float = Field(default=0.0, ge=0.0)
    version: int = Field(default=1, ge=1)
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime

    @field_validator("fault_id")
    @classmethod
    def validate_fault_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("fault_id cannot be empty")
        return v.strip()


class SensorReading(BaseModel):
    reading_id: str
    asset_id: str
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    is_anomalous: bool = False


class QueryFilter(BaseModel):
    asset_types: Optional[List[AssetType]] = None
    components: Optional[List[Component]] = None
    min_severity: Optional[Severity] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metric_name: Optional[str] = None
    min_sensor_val: Optional[float] = None
    max_sensor_val: Optional[float] = None


class SearchResultItem(BaseModel):
    fault: FaultReport
    bm25_score: float
    semantic_score: float
    hybrid_score: float
    match_explanation: Dict[str, Any]
    validated: bool = True


class RangeAggregateResult(BaseModel):
    query_start: datetime
    query_end: datetime
    total_faults: int
    total_power_loss_kwh: float
    severity_counts: Dict[str, int]
    execution_time_ms: float
    algorithm_used: str  # "FenwickTree" or "LinearScanBaseline"

