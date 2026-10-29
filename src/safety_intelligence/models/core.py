"""Core master data models for Industrial Safety Intelligence Platform."""

from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field


class Plant(BaseModel):
    """Manufacturing facility hosting production lines and safety zones."""
    plant_id: str = Field(..., description="Unique Plant ID, e.g., PLT-01")
    name: str = Field(..., description="Facility name")
    code: str = Field(..., description="Alpha-3 uppercase facility code")
    location: str = Field(..., description="Geographical jurisdiction")
    timezone: str = Field(..., description="IANA timezone name")
    operational_status: str = Field(..., description="ACTIVE, MAINTENANCE, DECOMMISSIONED")
    total_lines: int = Field(..., ge=1, le=50, description="Count of production lines")
    created_at: str = Field(..., description="ISO 8601 UTC creation timestamp")


class Machine(BaseModel):
    """Industrial asset operating inside production cells and safety zones."""
    machine_id: str = Field(..., description="Deterministic machine ID, e.g., MCH-001")
    plant_id: str = Field(..., description="Foreign key to Plant")
    name: str = Field(..., description="Machine asset name")
    type: str = Field(..., description="CNC_MILL, ROBOTIC_ARM, HYDRAULIC_PRESS, CONVEYOR, etc.")
    criticality: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    installation_date: str = Field(..., description="ISO 8601 date YYYY-MM-DD")
    status: str = Field(..., description="RUNNING, IDLE, MAINTENANCE, TRIPPED, STOPPED")
    firmware_version: str = Field(..., description="Semantic firmware version string")


class SafetyZone(BaseModel):
    """Enclosed perimeter with safety integrity levels protecting operators."""
    zone_id: str = Field(..., description="Standard ID SAFE-<plant-id>-001")
    plant_id: str = Field(..., description="Foreign key to Plant")
    name: str = Field(..., description="Safety zone title")
    hazard_classification: str = Field(..., description="MECHANICAL_PINCH, HIGH_VOLTAGE, etc.")
    required_sil_level: str = Field(..., description="SIL_1, SIL_2, SIL_3, SIL_4")
    access_state: str = Field(..., description="RESTRICTED, CONTROLLED, OPEN, EMERGENCY_ISOLATED")
    max_occupancy: int = Field(..., ge=0, le=20, description="Max allowed personnel")
    created_at: str = Field(..., description="ISO 8601 UTC creation timestamp")


class MachineSafetyZone(BaseModel):
    """Bridge table mapping many-to-many relationship between Machines and SafetyZones."""
    mapping_id: str = Field(..., description="Unique bridge mapping ID")
    machine_id: str = Field(..., description="Foreign key to Machine")
    zone_id: str = Field(..., description="Foreign key to SafetyZone")
    primary_containment: bool = Field(..., description="True if primary containment zone")
    effective_from: str = Field(..., description="Start of assignment timestamp")
    effective_to: Optional[str] = Field(None, description="End of assignment timestamp or null")
    active_status: bool = Field(..., description="True if current active mapping")


class Interlock(BaseModel):
    """Physical or optical safety switch inhibiting dangerous machine motion."""
    interlock_id: str = Field(..., description="Interlock ID ITL-<machine-id>-01")
    machine_id: str = Field(..., description="Foreign key to Machine")
    zone_id: str = Field(..., description="Foreign key to SafetyZone")
    name: str = Field(..., description="Sensor tag name")
    interlock_type: str = Field(..., description="GUARD_DOOR, LIGHT_CURTAIN, EMERGENCY_STOP, etc.")
    safety_standard: str = Field(..., description="ISO_13849_1_CAT4, IEC_62061_SIL3, ANSI_B11_19")
    state: str = Field(..., description="HEALTHY, TRIPPED, BYPASSED, FAULT")
    last_tested_date: str = Field(..., description="ISO 8601 calibration date")
    bypass_allowed: bool = Field(..., description="Whether bypass is administratively permissible")


class AlarmDefinition(BaseModel):
    """Catalog of alarm limits and response procedures conforming to ISA-18.2."""
    alarm_def_id: str = Field(..., description="Unique alarm definition DEF-001")
    code: str = Field(..., description="Telemetry code tag, e.g., ALM_E_STOP_TRIP")
    name: str = Field(..., description="Human-readable alarm label")
    category: str = Field(..., description="SAFETY, PROCESS, MECHANICAL, ELECTRICAL")
    default_severity: str = Field(..., description="CRITICAL, HIGH, MEDIUM, LOW")
    sla_ack_seconds: int = Field(..., ge=30, le=7200, description="SLA acknowledgement threshold")
    auto_resettable: bool = Field(..., description="True if self-clearing upon condition recovery")
    requires_investigation: bool = Field(..., description="True if mandatory incident review")
    description: str = Field(..., description="Operator SOP instructions")
