"""REST API endpoints for the Industrial Safety Intelligence Platform."""

import sqlite3
from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Query

from safety_intelligence.config import DATA_DIR
from safety_intelligence.analytics.metrics_evaluator import SafetyMetricsEvaluator
from safety_intelligence.analytics.repeated_conditions import RepeatedUnsafeConditionAnalyzer
from safety_intelligence.analytics.isa18_alarms import ISA18AlarmAnalyzer
from safety_intelligence.analytics.acknowledgement_sla import AcknowledgementSLAAnalyzer
from safety_intelligence.analytics.corrective_actions import CorrectiveActionAnalyzer
from safety_intelligence.validation.edge_case_detector import EdgeCaseDetector

router = APIRouter(prefix="/api")


def _get_active_dataset_dir() -> Path:
    full_db = DATA_DIR / "full" / "safety_platform.db"
    if full_db.exists():
        return DATA_DIR / "full"
    starter_db = DATA_DIR / "starter" / "safety_platform.db"
    if starter_db.exists():
        return DATA_DIR / "starter"
    raise HTTPException(status_code=404, detail="No generated dataset found. Run generation first.")


@router.get("/health")
def health() -> Dict[str, str]:
    return {"status": "HEALTHY", "platform": "Industrial Safety Intelligence Platform", "version": "1.0.0"}


@router.get("/overview")
def get_overview() -> Dict[str, Any]:
    dataset_dir = _get_active_dataset_dir()
    evaluator = SafetyMetricsEvaluator(dataset_dir)
    return evaluator.compute_all_metrics()


@router.get("/repeated-conditions")
def get_repeated_conditions() -> Dict[str, Any]:
    dataset_dir = _get_active_dataset_dir()
    db_path = dataset_dir / "safety_platform.db"
    analyzer = RepeatedUnsafeConditionAnalyzer(db_path)
    return analyzer.analyze()


@router.get("/isa18-alarms")
def get_isa18_alarms() -> Dict[str, Any]:
    dataset_dir = _get_active_dataset_dir()
    db_path = dataset_dir / "safety_platform.db"
    analyzer = ISA18AlarmAnalyzer(db_path)
    return analyzer.analyze()


@router.get("/operator-shifts")
def get_operator_shifts() -> Dict[str, Any]:
    dataset_dir = _get_active_dataset_dir()
    db_path = dataset_dir / "safety_platform.db"
    analyzer = AcknowledgementSLAAnalyzer(db_path)
    return analyzer.analyze()


@router.get("/corrective-actions")
def get_corrective_actions() -> Dict[str, Any]:
    dataset_dir = _get_active_dataset_dir()
    db_path = dataset_dir / "safety_platform.db"
    analyzer = CorrectiveActionAnalyzer(db_path)
    return analyzer.analyze()


@router.get("/anomalies")
def get_anomalies() -> Dict[str, Any]:
    dataset_dir = _get_active_dataset_dir()
    db_path = dataset_dir / "safety_platform.db"
    gt_path = dataset_dir / "ground_truth" / "ground_truth_anomalies.json"
    detector = EdgeCaseDetector(db_path, gt_path)
    return detector.run_detection()


@router.get("/entities/{table_name}")
def get_table_records(
    table_name: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> Dict[str, Any]:
    allowed_tables = [
        "plants",
        "machines",
        "safety_zones",
        "machine_safety_zones",
        "interlocks",
        "alarm_definitions",
        "operator_shifts",
        "machine_state_history",
        "alarm_events",
        "acknowledgements",
        "incidents",
        "corrective_actions",
    ]
    if table_name not in allowed_tables:
        raise HTTPException(status_code=400, detail=f"Invalid table '{table_name}'. Allowed: {allowed_tables}")

    dataset_dir = _get_active_dataset_dir()
    db_path = dataset_dir / "safety_platform.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_count = cursor.fetchone()[0]

    cursor.execute(f"SELECT * FROM {table_name} LIMIT ? OFFSET ?", (limit, offset))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return {
        "table": table_name,
        "total_records": total_count,
        "limit": limit,
        "offset": offset,
        "records": rows,
    }
