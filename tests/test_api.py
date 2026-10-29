"""Integration tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from safety_intelligence.web.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_api_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "HEALTHY"


def test_api_overview(client):
    r = client.get("/api/overview")
    assert r.status_code == 200
    data = r.json()
    assert "safety_kpis" in data
    assert "recurrent_hazard_evaluation" in data


def test_api_repeated_conditions(client):
    r = client.get("/api/repeated-conditions")
    assert r.status_code == 200
    data = r.json()
    assert "recurrent_incidents" in data
    assert "chronic_interlock_trips" in data


def test_api_isa18_alarms(client):
    r = client.get("/api/isa18-alarms")
    assert r.status_code == 200
    data = r.json()
    assert "severity_distribution" in data
    assert "nuisance_alarm_count" in data


def test_api_anomalies(client):
    r = client.get("/api/anomalies")
    assert r.status_code == 200
    data = r.json()
    assert "evaluation_against_ground_truth" in data


def test_api_table_explorer(client):
    r = client.get("/api/entities/machines?limit=10")
    assert r.status_code == 200
    data = r.json()
    assert data["table"] == "machines"
    assert len(data["records"]) <= 10
