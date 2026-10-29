"""Integration tests for analytics modules and repeated hazard detection."""

from pathlib import Path
import pytest
from safety_intelligence.config import DATA_DIR
from safety_intelligence.analytics.repeated_conditions import RepeatedUnsafeConditionAnalyzer
from safety_intelligence.analytics.isa18_alarms import ISA18AlarmAnalyzer
from safety_intelligence.analytics.acknowledgement_sla import AcknowledgementSLAAnalyzer
from safety_intelligence.analytics.metrics_evaluator import SafetyMetricsEvaluator


@pytest.fixture
def db_path():
    p = DATA_DIR / "starter" / "safety_platform.db"
    if not p.exists():
        from safety_intelligence.generator.engine import GenerationEngine
        GenerationEngine().run("starter")
    return p


def test_repeated_unsafe_conditions_discovery(db_path):
    analyzer = RepeatedUnsafeConditionAnalyzer(db_path)
    res = analyzer.analyze()
    assert res["total_repeated_conditions_found"] >= 2
    assert len(res["recurrent_incidents"]) >= 2
    for r in res["recurrent_incidents"]:
        assert r["pattern_type"] == "RECURRENT_INCIDENT"
        assert r["days_to_recurrence"] > 0


def test_isa18_compliance(db_path):
    analyzer = ISA18AlarmAnalyzer(db_path)
    res = analyzer.analyze()
    assert res["total_alarms"] > 0
    assert res["nuisance_alarm_count"] > 0
    assert "CRITICAL" in res["severity_distribution"]


def test_safety_metrics_evaluator():
    evaluator = SafetyMetricsEvaluator(DATA_DIR / "starter")
    metrics = evaluator.compute_all_metrics()
    kpis = metrics["safety_kpis"]
    assert kpis["incident_recurrence_rate_percent"] >= 0
    assert metrics["recurrent_hazard_evaluation"]["f1_score"] >= 0.80
