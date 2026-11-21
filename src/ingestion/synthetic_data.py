"""Synthetic data generation: 20 curated gold records and 1,000 realistic domain records for renewable energy assets."""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Tuple

from src.core.config import DATA_DIR, DOMAIN_RECORDS_FILE, GOLD_RECORDS_FILE, SAMPLE_QUERIES_FILE
from src.core.models import AssetType, Component, FaultReport, SensorRange, Severity, TimeInterval

# 20 Manually Checked Gold Standard Records for Ground Truth Relevance & Unit Testing
CURATED_GOLD_RECORDS = [
    {
        "fault_id": "FLT-GOLD-001",
        "asset_id": "WIND-TX-001",
        "asset_type": "WIND_TURBINE",
        "component": "GEARBOX",
        "severity": "CRITICAL",
        "time_interval": {
            "start_time": "2026-01-05T08:00:00Z",
            "end_time": "2026-01-05T14:30:00Z"
        },
        "sensor_range": {
            "metric_name": "Bearing_Vibration_RMS",
            "min_val": 4.8,
            "max_val": 12.4,
            "unit": "mm/s"
        },
        "fault_description": "High-speed stage planetary gear pitting and severe bearing vibration spike.",
        "maintenance_notes": "Emergency shutdown initiated. Oil analysis showed ferrous particle concentration exceeding 120 ppm. Intermediate shaft bearing replaced.",
        "root_cause_category": "Mechanical Wear",
        "power_loss_kwh": 6500.0,
        "version": 1,
        "is_deleted": False,
        "created_at": "2026-01-05T08:15:00Z",
        "updated_at": "2026-01-05T15:00:00Z"
    },
    {
        "fault_id": "FLT-GOLD-002",
        "asset_id": "SOLAR-CA-014",
        "asset_type": "SOLAR_PV",
        "component": "INVERTER",
        "severity": "HIGH",
        "time_interval": {
            "start_time": "2026-01-08T11:00:00Z",
            "end_time": "2026-01-08T16:00:00Z"
        },
        "sensor_range": {
            "metric_name": "IGBT_Junction_Temp",
            "min_val": 88.0,
            "max_val": 115.5,
            "unit": "Celsius"
        },
        "fault_description": "Central inverter bridge IGBT junction thermal runaway and switching desynchronization.",
        "maintenance_notes": "Cooling fan filter clogged with desert dust. Fan motor replaced and thermal paste reapplied to IGBT heat sink.",
        "root_cause_category": "Cooling Failure",
        "power_loss_kwh": 3800.0,
        "version": 1,
        "is_deleted": False,
        "created_at": "2026-01-08T11:20:00Z",
        "updated_at": "2026-01-08T17:00:00Z"
    },
    {
        "fault_id": "FLT-GOLD-003",
        "asset_id": "WIND-WY-023",
        "asset_type": "WIND_TURBINE",
        "component": "PITCH_SYSTEM",
        "severity": "CRITICAL",
        "time_interval": {
            "start_time": "2026-01-12T03:15:00Z",
            "end_time": "2026-01-12T09:45:00Z"
        },
        "sensor_range": {
            "metric_name": "Hydraulic_Pitch_Pressure",
            "min_val": 45.0,
            "max_val": 82.0,
            "unit": "bar"
        },
        "fault_description": "Blade 2 hydraulic pitch actuator seal rupture causing blade feathering failure during high-wind gust.",
        "maintenance_notes": "Rapid hydraulic pressure drop from nominal 180 bar down to 45 bar. Backup accumulator deployed. High-pressure seal replaced.",
        "root_cause_category": "Hydraulic Failure",
        "power_loss_kwh": 5200.0,
        "version": 1,
        "is_deleted": False,
        "created_at": "2026-01-12T03:30:00Z",
        "updated_at": "2026-01-12T11:00:00Z"
    },
    {
        "fault_id": "FLT-GOLD-004",
        "asset_id": "SOLAR-AZ-005",
        "asset_type": "SOLAR_PV",
        "component": "COMBINER_BOX",
        "severity": "MEDIUM",
        "time_interval": {
            "start_time": "2026-01-15T12:00:00Z",
            "end_time": "2026-01-15T15:30:00Z"
        },
        "sensor_range": {
            "metric_name": "String_Current_Imbalance",
            "min_val": 2.1,
            "max_val": 8.9,
            "unit": "Amperes"
        },
        "fault_description": "Combiner box string 4 blown DC fuse due to sustained partial shading mismatch and thermal stress.",
        "maintenance_notes": "15A gPV cylindrical fuse replaced. IR thermography revealed localized connection terminal hotspot.",
        "root_cause_category": "Electrical Fault",
        "power_loss_kwh": 420.0,
        "version": 1,
        "is_deleted": False,
        "created_at": "2026-01-15T12:10:00Z",
        "updated_at": "2026-01-15T16:00:00Z"
    },
    {
        "fault_id": "FLT-GOLD-005",
        "asset_id": "WIND-OR-088",
        "asset_type": "WIND_TURBINE",
        "component": "GENERATOR",
        "severity": "HIGH",
        "time_interval": {
            "start_time": "2026-01-18T14:00:00Z",
            "end_time": "2026-01-18T22:00:00Z"
        },
        "sensor_range": {
            "metric_name": "Stator_Winding_Temp",
            "min_val": 110.0,
            "max_val": 158.0,
            "unit": "Celsius"
        },
        "fault_description": "DFIG generator stator winding phase U overheating and asymmetric phase current draw.",
        "maintenance_notes": "Insulation resistance dropped below 5 Megohms. Stator cleaned with dry ice blasting and localized re-insulation applied.",
        "root_cause_category": "Insulation Degradation",
        "power_loss_kwh": 7100.0,
        "version": 1,
        "is_deleted": False,
        "created_at": "2026-01-18T14:20:00Z",
        "updated_at": "2026-01-18T23:00:00Z"
    },
    {
        "fault_id": "FLT-GOLD-006",
        "asset_id": "SOLAR-NV-031",
        "asset_type": "SOLAR_PV",
        "component": "SOLAR_PANEL",
        "severity": "MEDIUM",
        "time_interval": {
            "start_time": "2026-01-22T09:30:00Z",
            "end_time": "2026-01-22T17:00:00Z"
        },
        "sensor_range": {
            "metric_name": "Module_Hotspot_Delta_T",
            "min_val": 15.0,
            "max_val": 42.5,
            "unit": "Celsius"
        },
        "fault_description": "Bypass diode short-circuit causing localized module cell hot-spot and polymer backsheet yellowing.",
        "maintenance_notes": "Junction box Schottky diode bypassed permanently. Damaged 400W monocrystalline module swapped out under warranty.",
        "root_cause_category": "Component Degradation",
        "power_loss_kwh": 310.0,
        "version": 1,
        "is_deleted": False,
        "created_at": "2026-01-22T10:00:00Z",
        "updated_at": "2026-01-22T17:30:00Z"
    },
    {
        "fault_id": "FLT-GOLD-007",
        "asset_id": "WIND-IA-012",
        "asset_type": "WIND_TURBINE",
        "component": "YAW_SYSTEM",
        "severity": "HIGH",
        "time_interval": {
            "start_time": "2026-01-25T18:00:00Z",
            "end_time": "2026-01-26T02:00:00Z"
        },
        "sensor_range": {
            "metric_name": "Yaw_Motor_Current",
            "min_val": 28.0,
            "max_val": 64.0,
            "unit": "Amperes"
        },
        "fault_description": "Yaw drive gear tooth spalling and drive motor 2 excessive torque stall during wind direction tracking.",
        "maintenance_notes": "Pinion gear backlash inspected. Found 3 mm radial play. Yaw brake caliper pads replaced and bull gear relubricated.",
        "root_cause_category": "Mechanical Wear",
        "power_loss_kwh": 4800.0,
        "version": 1,
        "is_deleted": False,
        "created_at": "2026-01-25T18:30:00Z",
        "updated_at": "2026-01-26T03:00:00Z"
    },
    {
        "fault_id": "FLT-GOLD-008",
        "asset_id": "SOLAR-NM-077",
        "asset_type": "SOLAR_PV",
        "component": "BATTERY_STORAGE",
        "severity": "CRITICAL",
        "time_interval": {
            "start_time": "2026-01-28T13:00:00Z",
            "end_time": "2026-01-28T19:00:00Z"
        },
        "sensor_range": {
            "metric_name": "BESS_Rack_Temp_Variance",
            "min_val": 6.5,
            "max_val": 18.2,
            "unit": "Celsius"
        },
        "fault_description": "Lithium-ion BESS rack 3 thermal divergence and internal cell resistance deviation during C-rate discharge.",
        "maintenance_notes": "BMS triggered safety contactor open. HVAC coolant loop air bubble purged and module 3B removed for offline cycling.",
        "root_cause_category": "Thermal Runaway Precursor",
        "power_loss_kwh": 5100.0,
        "version": 1,
        "is_deleted": False,
        "created_at": "2026-01-28T13:15:00Z",
        "updated_at": "2026-01-28T20:00:00Z"
    },
    {
        "fault_id": "FLT-GOLD-009",
        "asset_id": "WIND-CO-055",
        "asset_type": "WIND_TURBINE",
        "component": "MAIN_BEARING",
        "severity": "HIGH",
        "time_interval": {
            "start_time": "2026-02-01T06:00:00Z",
            "end_time": "2026-02-01T16:00:00Z"
        },
        "sensor_range": {
            "metric_name": "Main_Bearing_Acoustic_Emission",
            "min_val": 42.0,
            "max_val": 89.0,
            "unit": "dB"
        },
        "fault_description": "Main spherical roller bearing raceway micro-cracking and automated grease distributor failure.",
        "maintenance_notes": "Progressive grease line blockage cleared at injector nozzle 4. Flushed old lubricant and injected lithium complex EP grease.",
        "root_cause_category": "Lubrication Starvation",
        "power_loss_kwh": 6200.0,
        "version": 1,
        "is_deleted": False,
        "created_at": "2026-02-01T06:30:00Z",
        "updated_at": "2026-02-01T17:00:00Z"
    },
    {
        "fault_id": "FLT-GOLD-010",
        "asset_id": "SOLAR-TX-102",
        "asset_type": "SOLAR_PV",
        "component": "MPPT_CONTROLLER",
        "severity": "LOW",
        "time_interval": {
            "start_time": "2026-02-04T10:00:00Z",
            "end_time": "2026-02-04T13:00:00Z"
        },
        "sensor_range": {
            "metric_name": "MPPT_Efficiency_Tracking",
            "min_val": 84.0,
            "max_val": 91.2,
            "unit": "Percent"
        },
        "fault_description": "MPPT tracking oscillation in fluctuating irradiance conditions due to firmware perturbation step size.",
        "maintenance_notes": "Firmware updated from v2.3.1 to v2.4.0 with adaptive hill-climbing algorithm. Tracking stability verified.",
        "root_cause_category": "Firmware Bug",
        "power_loss_kwh": 180.0,
        "version": 1,
        "is_deleted": False,
        "created_at": "2026-02-04T10:15:00Z",
        "updated_at": "2026-02-04T13:30:00Z"
    },
    {
        "fault_id": "FLT-GOLD-011",
        "asset_id": "WIND-ND-004",
        "asset_type": "WIND_TURBINE",
        "component": "ROTOR_BLADE",
        "severity": "HIGH",
        "time_interval": {
            "start_time": "2026-02-08T00:00:00Z",
            "end_time": "2026-02-08T12:00:00Z"
        },
        "sensor_range": {
            "metric_name": "Blade_Aero_Acoustic_Noise",
            "min_val": 92.0,
            "max_val": 118.0,
            "unit": "dBA"
        },
        "fault_description": "Blade tip leading-edge erosion and aerodynamic delamination following freezing rain event.",
        "maintenance_notes": "Rope access technician applied polyurethane leading-edge protective tape over 4-meter section near tip.",
        "root_cause_category": "Environmental Erosion",
        "power_loss_kwh": 5900.0,
        "version": 1,
        "is_deleted": False,
        "created_at": "2026-02-08T00:45:00Z",
        "updated_at": "2026-02-08T13:00:00Z"
    },
    {
        "fault_id": "FLT-GOLD-012",
        "asset_id": "SOLAR-FL-019",
        "asset_type": "SOLAR_PV",
        "component": "TRANSFORMER",
        "severity": "CRITICAL",
        "time_interval": {
            "start_time": "2026-02-12T07:00:00Z",
            "end_time": "2026-02-12T15:00:00Z"
        },
        "sensor_range": {
            "metric_name": "Transformer_Top_Oil_Temp",
            "min_val": 94.0,
            "max_val": 128.0,
            "unit": "Celsius"
        },
        "fault_description": "Medium-voltage step-up transformer top oil overheating and Buchholz gas accumulation alarm.",
        "maintenance_notes": "DGA test indicated acetylene traces (0.8 ppm). Forced air radiator fans rewired after contactor failure.",
        "root_cause_category": "Thermal & Electrical Stress",
        "power_loss_kwh": 8400.0,
        "version": 1,
        "is_deleted": False,
        "created_at": "2026-02-12T07:20:00Z",
        "updated_at": "2026-02-12T16:00:00Z"
    },
    {
        "fault_id": "FLT-GOLD-013",
        "asset_id": "WIND-IL-033",
        "asset_type": "WIND_TURBINE",
        "component": "SUBSTATION_BREAKER",
        "severity": "HIGH",
        "time_interval": {
            "start_time": "2026-02-15T16:30:00Z",
            "end_time": "2026-02-15T21:00:00Z"
        },
        "sensor_range": {
            "metric_name": "SF6_Gas_Pressure",
            "min_val": 4.1,
            "max_val": 5.8,
            "unit": "bar"
        },
        "fault_description": "Substation 34.5kV feeder vacuum breaker SF6 insulation gas low pressure trip during feeder fault.",
        "maintenance_notes": "Gas manifold O-ring seal replaced and re-pressurized with certified SF6 gas. Trip latch mechanism re-timed.",
        "root_cause_category": "Gas Leakage",
        "power_loss_kwh": 4600.0,
        "version": 1,
        "is_deleted": False,
        "created_at": "2026-02-15T16:45:00Z",
        "updated_at": "2026-02-15T22:00:00Z"
    },
    {
        "fault_id": "FLT-GOLD-014",
        "asset_id": "SOLAR-UT-008",
        "asset_type": "SOLAR_PV",
        "component": "SOLAR_PANEL",
        "severity": "LOW",
        "time_interval": {
            "start_time": "2026-02-18T11:00:00Z",
            "end_time": "2026-02-18T14:00:00Z"
        },
        "sensor_range": {
            "metric_name": "Soiling_Ratio",
            "min_val": 0.76,
            "max_val": 0.88,
            "unit": "Ratio"
        },
        "fault_description": "Significant soiling loss across tracker row 12 following regional dust storm.",
        "maintenance_notes": "Autonomous dry cleaning robot deployed across block B. Soiling ratio recovered to 0.985.",
        "root_cause_category": "Environmental Soiling",
        "power_loss_kwh": 220.0,
        "version": 1,
        "is_deleted": False,
        "created_at": "2026-02-18T11:30:00Z",
        "updated_at": "2026-02-18T14:30:00Z"
    },
    {
        "fault_id": "FLT-GOLD-015",
        "asset_id": "WIND-MN-061",
        "asset_type": "WIND_TURBINE",
        "component": "GEARBOX",
        "severity": "MEDIUM",
        "time_interval": {
            "start_time": "2026-02-21T05:00:00Z",
            "end_time": "2026-02-21T11:00:00Z"
        },
        "sensor_range": {
            "metric_name": "Gearbox_Oil_Particle_Count",
            "min_val": 1800.0,
            "max_val": 4200.0,
            "unit": "particles/mL"
        },
        "fault_description": "Gearbox offline conditioning filter saturation causing optical particle sensor threshold breach.",
        "maintenance_notes": "10-micron pleated cellulose filter cartridge replaced. Main lube pump pressure restored to 3.2 bar.",
        "root_cause_category": "Filtration Saturation",
        "power_loss_kwh": 2900.0,
        "version": 1,
        "is_deleted": False,
        "created_at": "2026-02-21T05:30:00Z",
        "updated_at": "2026-02-21T11:30:00Z"
    },
    {
        "fault_id": "FLT-GOLD-016",
        "asset_id": "SOLAR-CO-022",
        "asset_type": "SOLAR_PV",
        "component": "INVERTER",
        "severity": "HIGH",
        "time_interval": {
            "start_time": "2026-02-24T12:00:00Z",
            "end_time": "2026-02-24T18:00:00Z"
        },
        "sensor_range": {
            "metric_name": "DC_Bus_Ripple_Voltage",
            "min_val": 14.5,
            "max_val": 38.0,
            "unit": "Volts"
        },
        "fault_description": "DC link capacitor bank degradation causing high AC ripple on 800V DC bus.",
        "maintenance_notes": "Capacitor C3 and C4 electrolyte drying identified with ESR meter. Replaced full capacitor bank module.",
        "root_cause_category": "Electrical Degradation",
        "power_loss_kwh": 3400.0,
        "version": 1,
        "is_deleted": False,
        "created_at": "2026-02-24T12:15:00Z",
        "updated_at": "2026-02-24T18:45:00Z"
    },
    {
        "fault_id": "FLT-GOLD-017",
        "asset_id": "WIND-OK-017",
        "asset_type": "WIND_TURBINE",
        "component": "PITCH_SYSTEM",
        "severity": "MEDIUM",
        "time_interval": {
            "start_time": "2026-02-27T08:00:00Z",
            "end_time": "2026-02-27T13:00:00Z"
        },
        "sensor_range": {
            "metric_name": "Pitch_Motor_Encoder_Delta",
            "min_val": 1.8,
            "max_val": 5.2,
            "unit": "Degrees"
        },
        "fault_description": "Optical pitch encoder signal noise and position mismatch relative to safety limit switches.",
        "maintenance_notes": "Encoder optical disc cleaned with isopropyl alcohol. Cable shielding ground lug tightened.",
        "root_cause_category": "Sensor Signal Noise",
        "power_loss_kwh": 2100.0,
        "version": 1,
        "is_deleted": False,
        "created_at": "2026-02-27T08:30:00Z",
        "updated_at": "2026-02-27T13:30:00Z"
    },
    {
        "fault_id": "FLT-GOLD-018",
        "asset_id": "SOLAR-NC-003",
        "asset_type": "SOLAR_PV",
        "component": "BATTERY_STORAGE",
        "severity": "LOW",
        "time_interval": {
            "start_time": "2026-03-02T10:00:00Z",
            "end_time": "2026-03-02T13:00:00Z"
        },
        "sensor_range": {
            "metric_name": "Aux_Chiller_Current",
            "min_val": 12.0,
            "max_val": 26.5,
            "unit": "Amperes"
        },
        "fault_description": "Auxiliary liquid cooling chiller pump high vibration and flow constriction.",
        "maintenance_notes": "Centrifugal pump impeller inspected for cavitations. Suction strainer cleaned of debris.",
        "root_cause_category": "Cooling System",
        "power_loss_kwh": 140.0,
        "version": 1,
        "is_deleted": False,
        "created_at": "2026-03-02T10:15:00Z",
        "updated_at": "2026-03-02T13:15:00Z"
    },
    {
        "fault_id": "FLT-GOLD-019",
        "asset_id": "WIND-KS-071",
        "asset_type": "WIND_TURBINE",
        "component": "GENERATOR",
        "severity": "CRITICAL",
        "time_interval": {
            "start_time": "2026-03-05T01:00:00Z",
            "end_time": "2026-03-05T09:00:00Z"
        },
        "sensor_range": {
            "metric_name": "Generator_NDE_Bearing_Vib",
            "min_val": 6.2,
            "max_val": 16.8,
            "unit": "mm/s"
        },
        "fault_description": "Generator Non-Drive-End (NDE) ceramic bearing fluting discharge and catastrophic cage fatigue.",
        "maintenance_notes": "Shaft grounding brush worn completely down. Replaced insulated bearing and installed new dual carbon grounding ring.",
        "root_cause_category": "Electrical Bearing Fluting",
        "power_loss_kwh": 7800.0,
        "version": 1,
        "is_deleted": False,
        "created_at": "2026-03-05T01:30:00Z",
        "updated_at": "2026-03-05T10:00:00Z"
    },
    {
        "fault_id": "FLT-GOLD-020",
        "asset_id": "SOLAR-GA-044",
        "asset_type": "SOLAR_PV",
        "component": "TRANSFORMER",
        "severity": "HIGH",
        "time_interval": {
            "start_time": "2026-03-08T14:00:00Z",
            "end_time": "2026-03-08T20:00:00Z"
        },
        "sensor_range": {
            "metric_name": "Winding_Hotspot_Temp",
            "min_val": 105.0,
            "max_val": 142.0,
            "unit": "Celsius"
        },
        "fault_description": "Pad-mounted transformer secondary winding thermal hotspot under continuous peak grid export.",
        "maintenance_notes": "Oil sampling confirmed elevated CO/CO2 ratio indicating paper insulation thermal distress. Load curtailed by 15% pending cool-down.",
        "root_cause_category": "Thermal Overload",
        "power_loss_kwh": 4100.0,
        "version": 1,
        "is_deleted": False,
        "created_at": "2026-03-08T14:20:00Z",
        "updated_at": "2026-03-08T21:00:00Z"
    }
]

# Query evaluation benchmark for MRR / NDCG ranking evaluation
CURATED_SAMPLE_QUERIES = [
    {
        "query_id": "Q-001",
        "query_text": "gearbox bearing vibration pitting high-speed shaft",
        "structured_filter": {"asset_types": ["WIND_TURBINE"], "components": ["GEARBOX"]},
        "relevant_fault_ids": ["FLT-GOLD-001", "FLT-GOLD-015"]
    },
    {
        "query_id": "Q-002",
        "query_text": "inverter IGBT temperature thermal runaway dust cooling",
        "structured_filter": {"asset_types": ["SOLAR_PV"], "components": ["INVERTER"]},
        "relevant_fault_ids": ["FLT-GOLD-002", "FLT-GOLD-016"]
    },
    {
        "query_id": "Q-003",
        "query_text": "hydraulic pitch actuator seal leak feathering failure",
        "structured_filter": {"asset_types": ["WIND_TURBINE"], "components": ["PITCH_SYSTEM"]},
        "relevant_fault_ids": ["FLT-GOLD-003", "FLT-GOLD-017"]
    },
    {
        "query_id": "Q-004",
        "query_text": "combiner box blown fuse string current imbalance",
        "structured_filter": {"asset_types": ["SOLAR_PV"], "components": ["COMBINER_BOX"]},
        "relevant_fault_ids": ["FLT-GOLD-004"]
    },
    {
        "query_id": "Q-005",
        "query_text": "generator stator winding overheating asymmetric current",
        "structured_filter": {"asset_types": ["WIND_TURBINE"], "components": ["GENERATOR"]},
        "relevant_fault_ids": ["FLT-GOLD-005", "FLT-GOLD-019"]
    },
    {
        "query_id": "Q-006",
        "query_text": "battery storage thermal runaway BESS cell temperature variance",
        "structured_filter": {"asset_types": ["SOLAR_PV"], "components": ["BATTERY_STORAGE"]},
        "relevant_fault_ids": ["FLT-GOLD-008", "FLT-GOLD-018"]
    },
    {
        "query_id": "Q-007",
        "query_text": "transformer top oil temperature Buchholz gas alarm",
        "structured_filter": {"components": ["TRANSFORMER"]},
        "relevant_fault_ids": ["FLT-GOLD-012", "FLT-GOLD-020"]
    }
]


def generate_synthetic_domain_records(num_records: int = 1000, seed: int = 42) -> List[dict]:
    """Deterministically generate realistic domain records for renewable energy assets."""
    random.seed(seed)
    base_start = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    
    # Realistic templates
    solar_components = [
        (Component.INVERTER, "IGBT_Junction_Temp", 60.0, 120.0, "Celsius", [
            ("Central inverter DC bus undervoltage trip during cloud edge event.", "DC disconnect switch cycled; capacitor bank pre-charge circuit verified.", "Voltage Fluctuation", 2800.0),
            ("Inverter MPPT bridge over-temperature warning on channel B.", "Heat exchanger cleaned with low-pressure nitrogen spray. Fans tested OK.", "Thermal Dissipation", 1950.0),
            ("Inverter gate drive board optical fiber communication dropout.", "Replaced optic transceiver module on master controller rack.", "Control Hardware", 3100.0)
        ]),
        (Component.SOLAR_PANEL, "Module_Hotspot_Delta_T", 5.0, 50.0, "Celsius", [
            ("String diode failure causing localized cell overheating and reverse current.", "Defective panel marked and isolated from string via branch connector.", "Diode Breakdown", 320.0),
            ("Potential-Induced Degradation (PID) detected on negative rail string.", "PID recovery box connected to apply reverse bias voltage overnight.", "PID Stress", 550.0),
            ("Micro-cracking on cell matrix following heavy hail event.", "Electroluminescence imaging completed. 4 modules scheduled for swap.", "Physical Impact", 410.0)
        ]),
        (Component.COMBINER_BOX, "String_Current_Imbalance", 0.5, 12.0, "Amperes", [
            ("Loose lug termination in DC combiner box causing high contact resistance.", "Torqued all terminals to 9.5 Nm and applied anti-corrosion grease.", "Loose Connection", 380.0),
            ("Surge protection device (SPD) status flag tripped after lightning storm.", "Type II DIN-rail surge arrester cartridge replaced.", "Lightning Surge", 240.0)
        ]),
        (Component.BATTERY_STORAGE, "BESS_Rack_Temp_Variance", 1.0, 25.0, "Celsius", [
            ("Cell balancing failure in container 2 leading to state-of-charge divergence.", "Equalization charging cycle executed over 12 hours.", "Cell Imbalance", 1200.0),
            ("Chilled liquid coolant pump flow rate alarm on battery rack 4.", "Impeller flushed and expansion tank level restored to 80%.", "Auxiliary Cooling", 1600.0)
        ]),
        (Component.MPPT_CONTROLLER, "MPPT_Efficiency_Tracking", 80.0, 99.5, "Percent", [
            ("MPPT tracking deadlock at local minima under partial snow cover.", "Updated tracking search interval parameter in supervisory controller.", "Algorithm Anomaly", 420.0)
        ]),
        (Component.TRANSFORMER, "Transformer_Top_Oil_Temp", 65.0, 135.0, "Celsius", [
            ("Substation solar step-up transformer high oil temperature alarm.", "Auxiliary fan bank turned on manually; oil level sight glass verified.", "Cooling Limitation", 4500.0)
        ])
    ]

    wind_components = [
        (Component.GEARBOX, "Bearing_Vibration_RMS", 1.5, 15.0, "mm/s", [
            ("High-speed shaft bearing cage wear and metallic debris generation.", "Offline filtration unit replaced; vibration monitoring frequency increased.", "Mechanical Fatigue", 5800.0),
            ("Planet carrier axial play out of manufacturer tolerance.", "Endplay measured with dial indicator. Shim pack adjusted by 0.35 mm.", "Tolerancing Wear", 6200.0),
            ("Gearbox lube oil foaming and pressure drop below 1.8 bar.", "Anti-foaming additive dosed into sump; oil suction screen cleared.", "Lubrication Degradation", 3400.0)
        ]),
        (Component.GENERATOR, "Stator_Winding_Temp", 80.0, 165.0, "Celsius", [
            ("Generator drive-end bearing temperature spike during rated wind speed.", "Automated grease pump recharged with synthetic ester grease.", "Thermal Friction", 4900.0),
            ("Rotor slip ring sparking and asymmetric brush wear.", "Carbon brushes replaced and commutating surface polished with fine stone.", "Electrical Arcing", 3800.0)
        ]),
        (Component.PITCH_SYSTEM, "Hydraulic_Pitch_Pressure", 30.0, 210.0, "bar", [
            ("Blade 1 pitch cylinder internal seal bypass during storm shutdown.", "Proportional valve spool inspected; replaced rod seal assembly.", "Hydraulic Seal Leak", 5100.0),
            ("Pitch drive electric motor brake slip during 18 m/s turbulent gust.", "Air gap adjusted to 0.4 mm and brake friction disc cleaned.", "Brake Wear", 4700.0)
        ]),
        (Component.YAW_SYSTEM, "Yaw_Motor_Current", 15.0, 75.0, "Amperes", [
            ("Nacelle yaw drive gear tooth crack detected during untwist operation.", "Pinion gear replaced; gear mesh backlash reset to 1.2 mm.", "Fatigue Fracture", 4400.0),
            ("Yaw hydraulic friction brake chatter during high yaw angle adjustment.", "Brake pressure regulator adjusted to 120 bar; brake lining replaced.", "Brake Chatter", 3100.0)
        ]),
        (Component.MAIN_BEARING, "Main_Bearing_Acoustic_Emission", 35.0, 95.0, "dB", [
            ("Main rotor bearing slow-speed raceway spalling and grease discoloration.", "Lubricant sample sent for ferrography; automatic greaser pulse increased.", "Grease Starvation", 6800.0)
        ]),
        (Component.ROTOR_BLADE, "Blade_Aero_Acoustic_Noise", 85.0, 125.0, "dBA", [
            ("Trailing edge bond-line split near 75% blade radius.", "Composite epoxy resin infusion patch applied by elevated platform team.", "Structural Delamination", 5400.0)
        ])
    ]

    records: List[dict] = []
    
    # Include gold records first
    for gold in CURATED_GOLD_RECORDS:
        records.append(gold.copy())

    # Generate remaining up to num_records
    current_time = base_start
    severities = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]
    severity_weights = [0.35, 0.35, 0.20, 0.10]

    for idx in range(len(CURATED_GOLD_RECORDS) + 1, num_records + 1):
        is_solar = random.random() < 0.5
        asset_type = AssetType.SOLAR_PV if is_solar else AssetType.WIND_TURBINE
        state_code = random.choice(["CA", "TX", "AZ", "WY", "CO", "OR", "IA", "NV", "NM", "FL"])
        asset_id = f"{'SOLAR' if is_solar else 'WIND'}-{state_code}-{random.randint(1, 999):03d}"

        comp_pool = solar_components if is_solar else wind_components
        comp, metric_name, m_min, m_max, unit, templates = random.choice(comp_pool)
        desc, notes, cause, base_loss = random.choice(templates)

        # Time interval: span from 1 to 16 hours
        current_time += timedelta(minutes=random.randint(45, 180))
        duration_hrs = random.uniform(1.0, 12.0)
        end_time = current_time + timedelta(hours=duration_hrs)

        # Sensor range
        val1 = random.uniform(m_min, m_max)
        val2 = random.uniform(val1, min(m_max * 1.25, val1 + (m_max - m_min) * 0.6))
        
        # Severity
        sev = random.choices(severities, weights=severity_weights, k=1)[0]
        loss = round(base_loss * random.uniform(0.7, 1.4) * (sev.level / 2.0), 1)

        rec = {
            "fault_id": f"FLT-{idx:05d}",
            "asset_id": asset_id,
            "asset_type": asset_type.value,
            "component": comp.value,
            "severity": sev.value,
            "time_interval": {
                "start_time": current_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            "sensor_range": {
                "metric_name": metric_name,
                "min_val": round(val1, 2),
                "max_val": round(val2, 2),
                "unit": unit
            },
            "fault_description": desc,
            "maintenance_notes": notes,
            "root_cause_category": cause,
            "power_loss_kwh": loss,
            "version": 1,
            "is_deleted": False,
            "created_at": (current_time + timedelta(minutes=15)).isoformat(),
            "updated_at": (end_time + timedelta(minutes=30)).isoformat()
        }
        records.append(rec)

    return records


def initialize_datasets_if_missing() -> Tuple[List[dict], List[dict], List[dict]]:
    """Ensure data directory and dataset files exist on disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Gold records
    if not GOLD_RECORDS_FILE.exists():
        with open(GOLD_RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(CURATED_GOLD_RECORDS, f, indent=2)

    # 2. Domain 1000 records
    if not DOMAIN_RECORDS_FILE.exists():
        records = generate_synthetic_domain_records(num_records=1000, seed=42)
        with open(DOMAIN_RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
    else:
        with open(DOMAIN_RECORDS_FILE, "r", encoding="utf-8") as f:
            records = json.load(f)

    # 3. Sample queries
    if not SAMPLE_QUERIES_FILE.exists():
        with open(SAMPLE_QUERIES_FILE, "w", encoding="utf-8") as f:
            json.dump(CURATED_SAMPLE_QUERIES, f, indent=2)

    return CURATED_GOLD_RECORDS, records, CURATED_SAMPLE_QUERIES


if __name__ == "__main__":
    g, d, q = initialize_datasets_if_missing()
    print(f"Initialized {len(g)} gold records, {len(d)} domain records, and {len(q)} sample queries.")

