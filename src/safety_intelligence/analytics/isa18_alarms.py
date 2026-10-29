"""ISA-18.2 alarm management analytics: alarm floods, chattering alarms, fleeting alarms, and rationalization."""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List


class ISA18AlarmAnalyzer:
    """Evaluates industrial telemetry against ANSI/ISA-18.2-2016 alarm performance standards."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def analyze(self) -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        flood_summary = self._analyze_floods(cursor)
        chattering_summary = self._analyze_chattering(cursor)
        fleeting_summary = self._analyze_fleeting(cursor)
        severity_dist = self._analyze_severity_distribution(cursor)
        category_dist = self._analyze_category_distribution(cursor)
        top_bad_actors = self._analyze_bad_actors(cursor)

        conn.close()

        total_alarms = sum(severity_dist.values())
        nuisance_count = chattering_summary["total_chattering_events"] + fleeting_summary["total_fleeting_events"]
        nuisance_ratio = round(nuisance_count / total_alarms, 4) if total_alarms > 0 else 0.0

        return {
            "total_alarms": total_alarms,
            "nuisance_alarm_count": nuisance_count,
            "nuisance_alarm_ratio": nuisance_ratio,
            "alarm_floods": flood_summary,
            "chattering_alarms": chattering_summary,
            "fleeting_alarms": fleeting_summary,
            "severity_distribution": severity_dist,
            "category_distribution": category_dist,
            "top_bad_actor_machines": top_bad_actors,
        }

    def _analyze_floods(self, cursor: sqlite3.Cursor) -> Dict[str, Any]:
        cursor.execute("SELECT COUNT(*) FROM alarm_events WHERE is_flood = 1;")
        flood_alarms = cursor.fetchone()[0]

        cursor.execute("""
        SELECT machine_id, COUNT(*) as flood_alarms_count
        FROM alarm_events
        WHERE is_flood = 1
        GROUP BY machine_id
        ORDER BY flood_alarms_count DESC
        LIMIT 5;
        """)
        top_flood_machines = [
            {"machine_id": r[0], "flood_alarms": r[1]} for r in cursor.fetchall()
        ]

        return {
            "total_flood_alarm_events": flood_alarms,
            "isa_flood_standard": "> 10 alarms per 10-minute interval",
            "top_flood_machines": top_flood_machines,
        }

    def _analyze_chattering(self, cursor: sqlite3.Cursor) -> Dict[str, Any]:
        cursor.execute("SELECT COUNT(*) FROM alarm_events WHERE nuisance_type = 'CHATTERING';")
        total_chattering = cursor.fetchone()[0]

        cursor.execute("""
        SELECT a.machine_id, d.code, d.name, COUNT(*) as chatter_count
        FROM alarm_events a
        JOIN alarm_definitions d ON a.alarm_def_id = d.alarm_def_id
        WHERE a.nuisance_type = 'CHATTERING'
        GROUP BY a.machine_id, a.alarm_def_id
        ORDER BY chatter_count DESC
        LIMIT 5;
        """)
        top_chattering = [
            {"machine_id": r[0], "code": r[1], "name": r[2], "count": r[3]}
            for r in cursor.fetchall()
        ]

        return {
            "total_chattering_events": total_chattering,
            "isa_chattering_criteria": ">= 3 transitions per minute for identical alarm tag",
            "top_chattering_tags": top_chattering,
        }

    def _analyze_fleeting(self, cursor: sqlite3.Cursor) -> Dict[str, Any]:
        cursor.execute("SELECT COUNT(*) FROM alarm_events WHERE nuisance_type = 'FLEETING';")
        total_fleeting = cursor.fetchone()[0]

        cursor.execute("""
        SELECT a.machine_id, d.code, AVG(a.duration_seconds) as avg_duration, COUNT(*) as count
        FROM alarm_events a
        JOIN alarm_definitions d ON a.alarm_def_id = d.alarm_def_id
        WHERE a.nuisance_type = 'FLEETING'
        GROUP BY a.machine_id, a.alarm_def_id
        ORDER BY count DESC
        LIMIT 5;
        """)
        top_fleeting = [
            {"machine_id": r[0], "code": r[1], "avg_duration_sec": round(r[2], 2), "count": r[3]}
            for r in cursor.fetchall()
        ]

        return {
            "total_fleeting_events": total_fleeting,
            "isa_fleeting_criteria": "Alarm duration < 5 seconds auto-cleared without operator intervention",
            "top_fleeting_tags": top_fleeting,
        }

    def _analyze_severity_distribution(self, cursor: sqlite3.Cursor) -> Dict[str, int]:
        cursor.execute("SELECT severity, COUNT(*) FROM alarm_events GROUP BY severity;")
        return {r[0]: r[1] for r in cursor.fetchall()}

    def _analyze_category_distribution(self, cursor: sqlite3.Cursor) -> Dict[str, int]:
        cursor.execute("""
        SELECT d.category, COUNT(*) 
        FROM alarm_events a
        JOIN alarm_definitions d ON a.alarm_def_id = d.alarm_def_id
        GROUP BY d.category;
        """)
        return {r[0]: r[1] for r in cursor.fetchall()}

    def _analyze_bad_actors(self, cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
        cursor.execute("""
        SELECT a.machine_id, m.name, m.type, COUNT(*) as total_alarms,
               SUM(CASE WHEN a.severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count
        FROM alarm_events a
        JOIN machines m ON a.machine_id = m.machine_id
        GROUP BY a.machine_id
        ORDER BY total_alarms DESC
        LIMIT 5;
        """)
        return [
            {
                "machine_id": r[0],
                "machine_name": r[1],
                "machine_type": r[2],
                "total_alarms": r[3],
                "critical_alarms": r[4],
            }
            for r in cursor.fetchall()
        ]
