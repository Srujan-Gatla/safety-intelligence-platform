"""Integration tests for validation suites: integrity, arithmetic, and edge cases."""

from pathlib import Path
import pytest
from safety_intelligence.config import DATA_DIR
from safety_intelligence.validation.validator import DatasetValidator


@pytest.fixture
def starter_dataset_dir():
    d = DATA_DIR / "starter"
    if not (d / "safety_platform.db").exists():
        from safety_intelligence.generator.engine import GenerationEngine
        GenerationEngine().run("starter")
    return d


def test_validation_overall_pass(starter_dataset_dir):
    validator = DatasetValidator(starter_dataset_dir)
    res = validator.validate_all()
    assert res["overall_status"] == "PASSED"
    assert res["integrity_checks"]["passed"] is True
    assert res["arithmetic_checks"]["passed"] is True


def test_edge_case_detection_metrics(starter_dataset_dir):
    validator = DatasetValidator(starter_dataset_dir)
    res = validator.validate_all()
    eval_m = res["edge_case_audit"]["evaluation_against_ground_truth"]
    assert eval_m["precision"] >= 0.95
    assert eval_m["recall"] >= 0.95
    assert eval_m["f1_score"] >= 0.95
