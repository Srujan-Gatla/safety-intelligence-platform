"""Unit tests for transactional event generation, naming, and derived calculations."""

import random
import re
import pytest
from datetime import datetime
from safety_intelligence.config import STARTER_PROFILE, DEFAULT_SEED
from safety_intelligence.generator.master_generator import MasterDataGenerator
from safety_intelligence.generator.event_generator import TransactionalEventGenerator


@pytest.fixture
def event_data():
    rng = random.Random(DEFAULT_SEED)
    master_gen = MasterDataGenerator(STARTER_PROFILE, rng)
    (plants, machines, zones, bridges, interlocks, alarm_defs) = master_gen.generate_all()
    event_gen = TransactionalEventGenerator(
        STARTER_PROFILE, rng, plants, machines, zones, interlocks, alarm_defs
    )
    return event_gen.generate_all()


def test_alarm_events_nomenclature(event_data):
    alarms = event_data[2]
    assert len(alarms) >= STARTER_PROFILE.num_alarm_events
    for a in alarms:
        # ALM-<machine-id>-000001
        assert re.match(r"^ALM-[A-Z0-9]+-\d{6}$", a.alarm_event_id)
        assert a.severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]


def test_acknowledgements_derived_values(event_data):
    acks = event_data[3]
    alarms = {a.alarm_event_id: a for a in event_data[2]}
    assert len(acks) > 0
    for ack in acks:
        # ACK-<alarm-id>-01
        assert re.match(r"^ACK-ALM-[A-Z0-9]+-\d{6}-\d{2}$", ack.ack_id)
        alm = alarms[ack.alarm_event_id]
        t0 = datetime.fromisoformat(alm.timestamp)
        t1 = datetime.fromisoformat(ack.ack_timestamp)
        expected_latency = (t1 - t0).total_seconds()
        assert abs(ack.latency_seconds - expected_latency) < 0.05


def test_incidents_and_actions(event_data):
    incidents = event_data[4]
    actions = event_data[5]
    recurrent_gt = event_data[6]

    assert len(incidents) > 0
    assert len(actions) > 0
    assert len(recurrent_gt) >= 2

    for inc in incidents:
        # INC-2026-000001
        assert re.match(r"^INC-\d{4}-\d{6}$", inc.incident_id)

    for act in actions:
        # ACT-<incident-id>-01
        assert re.match(r"^ACT-INC-\d{4}-\d{6}-\d{2}$", act.action_id)
