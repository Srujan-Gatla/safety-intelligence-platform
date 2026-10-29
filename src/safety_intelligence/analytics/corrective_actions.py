"""Analyzes corrective action status lifecycles, verification compliance, and recurrence prevention."""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List


class CorrectiveActionAnalyzer:
    """Evaluates maintenance and engineering corrective action health, verification, and recurrence."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def analyze(self) -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        status_breakdown = self._analyze_status_breakdown(cursor)
        verification_audit = self._analyze_verification_compliance(cursor)
        action_types = self._analyze_action_types(cursor)
        effectiveness = self._analyze_effectiveness(cursor)

        conn.close()

        return {
            "status_breakdown": status_breakdown,
            "verification_compliance": verification_audit,
            "action_type_distribution": action_types,
            "effectiveness_metrics": effectiveness,
        }

    def _analyze_status_breakdown(self, cursor: sqlite3.Cursor) -> Dict[str, int]:
        cursor.execute("SELECT status, COUNT(*) FROM corrective_actions GROUP BY status;")
        return {r[0]: r[1] for r in cursor.fetchall()}

    def _analyze_verification_compliance(self, cursor: sqlite3.Cursor) -> Dict[str, Any]:
        cursor.execute("SELECT COUNT(*) FROM corrective_actions WHERE status = 'CLOSED';")
        total_closed = cursor.fetchone()[0]

        cursor.execute("""
        SELECT COUNT(*) 
        FROM corrective_actions 
        WHERE status = 'CLOSED' AND (verified_by IS NULL OR verification_date IS NULL);
        """)
        unverified_closed = cursor.fetchone()[0]

        verified_closed = total_closed - unverified_closed
        compliance_rate = (
            round((verified_closed / total_closed) * 100, 2) if total_closed > 0 else 100.0
        )

        return {
            "total_closed_actions": total_closed,
            "verified_closed_actions": verified_closed,
            "unverified_closed_actions": unverified_closed,
            "verification_compliance_percent": compliance_rate,
            "compliance_risk_level": "CRITICAL" if unverified_closed > 0 else "LOW",
        }

    def _analyze_action_types(self, cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
        cursor.execute("""
        SELECT action_type, COUNT(*), AVG(effectiveness_score)
        FROM corrective_actions
        GROUP BY action_type
        ORDER BY COUNT(*) DESC;
        """)
        return [
            {
                "action_type": r[0],
                "count": r[1],
                "avg_effectiveness_score": round(r[2] or 0.0, 2),
            }
            for r in cursor.fetchall()
        ]

    def _analyze_effectiveness(self, cursor: sqlite3.Cursor) -> Dict[str, Any]:
        cursor.execute("""
        SELECT 
            AVG(effectiveness_score),
            MIN(effectiveness_score),
            MAX(effectiveness_score)
        FROM corrective_actions
        WHERE effectiveness_score IS NOT NULL;
        """)
        row = cursor.fetchone()
        return {
            "average_effectiveness_score": round(row[0] or 0.0, 2),
            "min_effectiveness_score": round(row[1] or 0.0, 2),
            "max_effectiveness_score": round(row[2] or 0.0, 2),
        }
