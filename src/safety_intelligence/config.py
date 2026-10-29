"""Configuration settings, constants, and scale profiles for Safety Intelligence Platform."""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class ScaleProfile:
    name: str
    num_plants: int
    num_machines: int
    num_zones_per_plant: int
    num_interlocks_per_machine: int
    num_alarm_defs: int
    num_alarm_events: int
    duration_days: int
    start_date: datetime
    # Edge case target counts
    num_ack_before_alarm: int
    num_interlock_impossible: int
    num_incident_no_trigger: int
    num_replay_clusters: int
    replay_alarms_per_cluster: int
    num_unverified_actions: int


# Fixed deterministic random seed
DEFAULT_SEED = 20261022

# Baseline Start Date: October 1, 2026 UTC
BASE_START_TIME = datetime(2026, 10, 1, 0, 0, 0, tzinfo=timezone.utc)

# Scale Profiles: Starter (fast verification) vs Full (50,000 alarms baseline)
STARTER_PROFILE = ScaleProfile(
    name="starter",
    num_plants=4,
    num_machines=12,
    num_zones_per_plant=4,
    num_interlocks_per_machine=3,
    num_alarm_defs=40,
    num_alarm_events=2000,
    duration_days=7,
    start_date=BASE_START_TIME,
    num_ack_before_alarm=15,
    num_interlock_impossible=10,
    num_incident_no_trigger=8,
    num_replay_clusters=2,
    replay_alarms_per_cluster=25,
    num_unverified_actions=10,
)

FULL_PROFILE = ScaleProfile(
    name="full",
    num_plants=4,
    num_machines=60,
    num_zones_per_plant=6,
    num_interlocks_per_machine=4,
    num_alarm_defs=200,
    num_alarm_events=50000,
    duration_days=30,
    start_date=BASE_START_TIME,
    num_ack_before_alarm=50,
    num_interlock_impossible=30,
    num_incident_no_trigger=25,
    num_replay_clusters=5,
    replay_alarms_per_cluster=50,
    num_unverified_actions=30,
)

# Project Directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
DOCS_DIR = BASE_DIR / "docs"

# ISA-18.2 Alarms Standard Constants
ISA_FLOOD_THRESHOLD_ALARMS = 10  # > 10 alarms per 10 minutes
ISA_FLOOD_WINDOW_SECONDS = 600   # 10 minutes window
ISA_CHATTERING_WINDOW_SECONDS = 60  # 60 seconds
ISA_CHATTERING_MIN_TRANSITIONS = 3  # >= 3 alarms in 60s
ISA_FLEETING_MAX_SECONDS = 5.0     # cleared in < 5 seconds without operator action

# SLA Acknowledgement Targets (seconds)
SLA_ACK_TARGETS = {
    "CRITICAL": 120,   # 2 minutes
    "HIGH": 300,       # 5 minutes
    "MEDIUM": 900,     # 15 minutes
    "LOW": 3600,       # 60 minutes
}

# Machine Types and Failure Hazards
MACHINE_TYPES = [
    "CNC_MILL",
    "ROBOTIC_ARM",
    "HYDRAULIC_PRESS",
    "CONVEYOR",
    "STAMPING_UNIT",
    "INJECTION_MOLDER",
]

HAZARD_TYPES = [
    "MECHANICAL_PINCH",
    "HIGH_VOLTAGE",
    "THERMAL_RADIATION",
    "CHEMICAL_EXPOSURE",
    "ROBOTIC_COLLISION",
]

INTERLOCK_TYPES = [
    "GUARD_DOOR",
    "LIGHT_CURTAIN",
    "EMERGENCY_STOP",
    "PRESSURE_MAT",
    "ENCLOSURE_LATCH",
]

SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
MACHINE_STATES = ["RUNNING", "IDLE", "MAINTENANCE", "TRIPPED", "STOPPED"]
SHIFT_TYPES = ["MORNING", "AFTERNOON", "NIGHT"]
