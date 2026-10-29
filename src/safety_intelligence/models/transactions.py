"""Transactional and event models for Industrial Safety Intelligence Platform."""

from typing import Optional
from pydantic import BaseModel, Field


class OperatorShift(BaseModel):
    """Operator duty cycle and shift assignment."""
    shift_id: str = Field(..., description="Unique shift ID SHF-YYYYMMDD-01")
    plant_id: str = Field(..., description="Foreign key to Plant")
    operator_id: str = Field(..., description="Operator badge ID OPR-0001")
    operator_name: str = Field(..., description="Technician full name")
    shift_type: str = Field(..., description="MORNING, AFTERNOON, NIGHT")
    start_time: str = Field(..., description="ISO 8601 start timestamp")
    end_time: str = Field(..., description="ISO 8601 end timestamp")
    supervisor_name: str = Field(..., description="Plant safety officer name")
    turnover_notes: Optional[str] = Field(None, description="Handover observations")


class MachineStateHistory(BaseModel):
    """Immutable audit trail of machine operational state changes."""
    state_event_id: str = Field(..., description="State event ID MST-MCH001-000001")
    machine_id: str = Field(..., description="Foreign key to Machine")
    shift_id: str = Field(..., description="Foreign key to OperatorShift")
    previous_state: str = Field(..., description="Prior state: RUNNING, IDLE, etc.")
    new_state: str = Field(..., description="New state: RUNNING, IDLE, TRIPPED, etc.")
    timestamp: str = Field(..., description="ISO 8601 transition timestamp")
    transition_reason: str = Field(..., description="Reason for transition")
    interlock_trip_id: Optional[str] = Field(None, description="Linked interlock if trip")


class AlarmEvent(BaseModel):
    """Alarm telemetry event conforming to ISA-18.2."""
    alarm_event_id: str = Field(..., description="ID ALM-<machine-id>-000001")
    machine_id: str = Field(..., description="Foreign key to Machine")
    alarm_def_id: str = Field(..., description="Foreign key to AlarmDefinition")
    zone_id: Optional[str] = Field(None, description="Foreign key to SafetyZone")
    shift_id: str = Field(..., description="Foreign key to OperatorShift")
    timestamp: str = Field(..., description="ISO 8601 alarm trigger timestamp")
    cleared_timestamp: Optional[str] = Field(None, description="ISO 8601 clearance timestamp")
    duration_seconds: Optional[float] = Field(None, description="Derived duration seconds")
    severity: str = Field(..., description="CRITICAL, HIGH, MEDIUM, LOW")
    trigger_value: float = Field(..., description="Sensor measured trip value")
    threshold_value: float = Field(..., description="Configured trip limit")
    lifecycle_state: str = Field(..., description="ACTIVE, ACKNOWLEDGED, CLEARED, ESCALATED")
    is_nuisance: bool = Field(False, description="Derived nuisance alarm flag")
    nuisance_type: str = Field("NONE", description="NONE, CHATTERING, FLEETING")
    is_flood: bool = Field(False, description="Derived alarm flood flag")


class Acknowledgement(BaseModel):
    """Operator acknowledgement of active alarm condition."""
    ack_id: str = Field(..., description="ID ACK-<alarm-id>-01")
    alarm_event_id: str = Field(..., description="Foreign key to AlarmEvent")
    shift_id: str = Field(..., description="Foreign key to OperatorShift")
    operator_id: str = Field(..., description="Operator badge ID")
    ack_timestamp: str = Field(..., description="ISO 8601 timestamp of acknowledgement")
    latency_seconds: float = Field(..., description="Derived latency from alarm activation")
    sla_breached: bool = Field(False, description="Derived: latency > SLA limit")
    ack_method: str = Field(..., description="HMI_TOUCH, PHYSICAL_CONSOLE, SCADA_DESK")
    comment: Optional[str] = Field(None, description="Operator context comment")


class Incident(BaseModel):
    """Critical safety incident, emergency stop, or safety perimeter breach."""
    incident_id: str = Field(..., description="ID INC-YYYY-000001")
    plant_id: str = Field(..., description="Foreign key to Plant")
    machine_id: str = Field(..., description="Foreign key to Machine")
    zone_id: str = Field(..., description="Foreign key to SafetyZone")
    triggering_alarm_id: Optional[str] = Field(None, description="Foreign key to AlarmEvent")
    shift_id: str = Field(..., description="Foreign key to OperatorShift")
    timestamp: str = Field(..., description="ISO 8601 incident occurrence timestamp")
    severity: str = Field(..., description="CRITICAL, MAJOR, MINOR, NEAR_MISS")
    incident_type: str = Field(..., description="INTERLOCK_BYPASS_VIOLATION, etc.")
    description: str = Field(..., description="Narrative summary")
    osha_reportable: bool = Field(False, description="OSHA mandatory reporting flag")
    lost_work_hours: float = Field(0.0, description="Downtime / lost work hours")
    machine_state_at_incident: str = Field(..., description="Machine state at time of incident")
    lifecycle_status: str = Field(..., description="REPORTED, UNDER_INVESTIGATION, etc.")


class CorrectiveAction(BaseModel):
    """Remedial engineering action deployed to prevent incident recurrence."""
    action_id: str = Field(..., description="ID ACT-<incident-id>-01")
    incident_id: str = Field(..., description="Foreign key to Incident")
    action_type: str = Field(..., description="HARDWARE_REPLACEMENT, RETRAINING, etc.")
    description: str = Field(..., description="Remediation plan description")
    assigned_to: str = Field(..., description="Lead maintenance engineer")
    due_date: str = Field(..., description="Committed completion date YYYY-MM-DD")
    completed_date: Optional[str] = Field(None, description="Completion date YYYY-MM-DD")
    verified_by: Optional[str] = Field(None, description="QA / Safety officer name")
    verification_date: Optional[str] = Field(None, description="Verification date YYYY-MM-DD")
    status: str = Field(..., description="PENDING, IN_PROGRESS, COMPLETED, VERIFIED, CLOSED")
    effectiveness_score: Optional[float] = Field(None, description="Derived score 0.0-1.0")
    recurrence_prevention_notes: Optional[str] = Field(None, description="Design change notes")
