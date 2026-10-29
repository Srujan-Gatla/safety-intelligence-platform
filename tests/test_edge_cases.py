"""Unit tests for the 5 injected edge cases and ground truth separation."""

import random
import pytest
from safety_intelligence.config import STARTER_PROFILE, DEFAULT_SEED
from safety_intelligence.generator.master_generator import MasterDataGenerator
from safety_intelligence.generator.event_generator import TransactionalEventGenerator
from safety_intelligence.generator.edge_case_injector import EdgeCaseInjector


@pytest.fixture
def edge_case_data():
    rng = random.Random(DEFAULT_SEED)
    master_gen = MasterDataGenerator(STARTER_PROFILE, rng)
    (plants, machines, zones, bridges, interlocks, alarm_defs) = master_gen.generate_all()
    event_gen = TransactionalEventGenerator(
        STARTER_PROFILE, rng, plants, machines, zones, interlocks, alarm_defs
    )
    (shifts, state_history, alarms, acks, incidents, actions, recurrent_gt) = event_gen.generate_all()
    injector = EdgeCaseInjector(STARTER_PROFILE, rng)
    return injector.inject_all(
        machines, interlocks, alarms, acks, incidents, actions, state_history
    )


def test_edge_case_types_coverage(edge_case_data):
    gt = edge_case_data[5]
    issue_types = {g.issue_type for g in gt}
    expected = {
        "ACK_BEFORE_ALARM",
        "INTERLOCK_STATE_IMPOSSIBLE",
        "INCIDENT_LACKS_TRIGGERING_CONTEXT",
        "ALARM_FLOOD_REPLAY_DUPLICATE",
        "ACTION_CLOSED_WITHOUT_VERIFICATION",
    }
    assert expected.issubset(issue_types)


def test_no_target_leakage_in_features(edge_case_data):
    acks = edge_case_data[0]
    for ack in acks:
        # Verify no label column like is_anomaly or issue_type in primary model
        dump = ack.model_dump()
        assert "is_anomaly" not in dump
        assert "issue_type" not in dump
        assert "ground_truth_label" not in dump
