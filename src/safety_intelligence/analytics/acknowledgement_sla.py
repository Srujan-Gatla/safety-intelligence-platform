"""Acknowledgement SLA performance, latency distributions, and operator shift correlation."""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List


class AcknowledgementSLAAnalyzer:
    """Analyzes operator acknowledgement timelines, SLA compliance rates, and shift correlations."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def analyze(self) -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        overall_metrics = self._analyze_overall_metrics(cursor)
        by_severity = self._analyze_by_severity(cursor)
        by_shift = self._analyze_by_shift(cursor)
        delayed_during_floods = self._analyze_delayed_during_floods(cursor)

        conn.close()

        return {
            "overall_metrics": overall_metrics,
            "performance_by_severity": by_severity,
            "performance_by_shift_type": by_shift,
            "flood_correlation": delayed_during_floods,
        }

    def _analyze_overall_metrics(self, cursor: sqlite3.Cursor) -> Dict[str, Any]:
        cursor.execute("SELECT COUNT(*) FROM alarm_events;")
        total_alarms = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*), AVG(latency_seconds) FROM acknowledgements WHERE latency_seconds >= 0;")
        row = cursor.fetchone()
        total_acks = row[0]
        avg_latency = round(row[1] or 0.0, 2)

        cursor.execute("SELECT COUNT(*) FROM acknowledgements WHERE sla_breached = 1;")
        breaches = cursor.fetchone()[0]

        ack_rate = round((total_acks / total_alarms) * 100, 2) if total_alarms > 0 else 0.0
        sla_compliance = round(((total_acks - breaches) / total_acks) * 100, 2) if total_acks > 0 else 100.0

        return {
            "total_alarms": total_alarms,
            "total_acknowledged": total_acks,
            "acknowledgement_rate_percent": ack_rate,
            "average_latency_seconds": avg_latency,
            "total_sla_breaches": breaches,
            "sla_compliance_rate_percent": sla_compliance,
        }

    def _analyze_by_severity(self, cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
        query = """
        SELECT 
            a.severity,
            COUNT(ack.ack_id) as ack_count,
            AVG(ack.latency_seconds) as avg_latency,
            SUM(ack.sla_breached) as breach_count,
            AVG(d.sla_ack_seconds) as target_sla
        FROM acknowledgements ack
        JOIN alarm_events a ON ack.alarm_event_id = a.alarm_event_id
        JOIN alarm_definitions d ON a.alarm_def_id = d.alarm_def_id
        WHERE ack.latency_seconds >= 0
        GROUP BY a.severity
        ORDER BY CASE a.severity 
            WHEN 'CRITICAL' THEN 1 
            WHEN 'HIGH' THEN 2 
            WHEN 'MEDIUM' THEN 3 
            WHEN 'LOW' THEN 4 
            ELSE 5 END;
        """
        cursor.execute(query)
        results = []
        for sev, count, avg_lat, breaches, target in cursor.fetchall():
            compliance = round(((count - breaches) / count) * 100, 2) if count > 0 else 100.0
            results.append({
                "severity": sev,
                "target_sla_seconds": int(target),
                "total_acknowledgements": count,
                "average_latency_seconds": round(avg_lat or 0.0, 1),
                "sla_breaches": breaches,
                "compliance_rate_percent": compliance,
            })
        return results

    def _analyze_by_shift(self, cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
        query = """
        SELECT 
            s.shift_type,
            COUNT(ack.ack_id) as total_acks,
            AVG(ack.latency_seconds) as avg_latency,
            SUM(ack.sla_breached) as breaches
        FROM acknowledgements ack
        JOIN operator_shifts s ON ack.shift_id = s.shift_id
        WHERE ack.latency_seconds >= 0
        GROUP BY s.shift_type
        ORDER BY avg_latency DESC;
        """
        cursor.execute(query)
        shift_perf = []
        for s_type, total, avg_lat, breaches in cursor.fetchall():
            comp = round(((total - breaches) / total) * 100, 2) if total > 0 else 100.0
            shift_perf.append({
                "shift_type": s_type,
                "total_acknowledgements": total,
                "average_latency_seconds": round(avg_lat or 0.0, 1),
                "sla_breaches": breaches,
                "compliance_percent": comp,
            })
        return shift_perf

    def _analyze_delayed_during_floods(self, cursor: sqlite3.Cursor) -> Dict[str, Any]:
        cursor.execute("""
        SELECT 
            AVG(CASE WHEN a.is_flood = 1 THEN ack.latency_seconds ELSE NULL END) as avg_flood_latency,
            AVG(CASE WHEN a.is_flood = 0 THEN ack.latency_seconds ELSE NULL END) as avg_normal_latency
        FROM acknowledgements ack
        JOIN alarm_events a ON ack.alarm_event_id = a.alarm_event_id
        WHERE ack.latency_seconds >= 0;
        """)
        row = cursor.fetchone()
        flood_lat = round(row[0] or 0.0, 1)
        normal_lat = round(row[1] or 0.0, 1)
        delay_factor = round(flood_lat / normal_lat, 2) if normal_lat > 0 else 1.0

        return {
            "avg_latency_during_alarm_flood_seconds": flood_lat,
            "avg_latency_during_normal_operations_seconds": normal_lat,
            "operator_overload_delay_multiplier": delay_factor,
        }
