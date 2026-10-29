"""Ground truth models for injected edge cases and repeated unsafe conditions."""

from typing import Optional
from pydantic import BaseModel, Field


class GroundTruthAnomaly(BaseModel):
    """Ground truth record for an injected anomaly or negative edge case."""
    anomaly_id: str = Field(..., description="Unique anomaly record ID, e.g., GT-ANOM-00001")
    entity_type: str = Field(..., description="Target table name (e.g. Acknowledgement, Interlock, etc.)")
    entity_id: str = Field(..., description="Primary key of anomalous entity")
    issue_type: str = Field(
        ...,
        description=(
            "One of: ACK_BEFORE_ALARM, INTERLOCK_STATE_IMPOSSIBLE, "
            "INCIDENT_LACKS_TRIGGERING_CONTEXT, ALARM_FLOOD_REPLAY_DUPLICATE, "
            "ACTION_CLOSED_WITHOUT_VERIFICATION"
        ),
    )
    description: str = Field(..., description="Human-readable description of the anomaly")
    detection_rule: str = Field(..., description="Deterministic validation rule that flags this")
    expected_decision: str = Field(..., description="Expected system decision/action to resolve")
    severity: str = Field(..., description="CRITICAL, HIGH, MEDIUM, LOW")
    injected_timestamp: str = Field(..., description="Timestamp context of the injected record")


class GroundTruthRecurrentHazard(BaseModel):
    """Ground truth record for known repeated unsafe conditions."""
    pattern_id: str = Field(..., description="Unique pattern ID, e.g., GT-REC-0001")
    machine_id: str = Field(..., description="Machine undergoing recurrent unsafe condition")
    zone_id: str = Field(..., description="Associated safety zone")
    hazard_type: str = Field(..., description="Category of recurrent hazard")
    first_incident_id: str = Field(..., description="Initial incident ID")
    recurrent_incident_id: str = Field(..., description="Repeated incident ID")
    intervening_action_id: str = Field(..., description="Action that failed to prevent recurrence")
    days_to_recurrence: float = Field(..., description="Time delta in days between incidents")
    root_cause_finding: str = Field(..., description="Explanation of why hazard recurred")
