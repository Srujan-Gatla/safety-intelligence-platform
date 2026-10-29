"""Validates Primary Key uniqueness, Foreign Key referential integrity, and Enums."""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List


class IntegrityChecker:
    """Checks relational integrity constraints, foreign keys, and enum values."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def run_all_checks(self) -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        pk_results = self._check_primary_keys(cursor)
        fk_results = self._check_foreign_keys(cursor)
        enum_results = self._check_enums(cursor)
        date_results = self._check_timeline_coherence(cursor)

        conn.close()

        all_passed = (
            pk_results["passed"]
            and fk_results["passed"]
            and enum_results["passed"]
            and date_results["passed"]
        )

        return {
            "passed": all_passed,
            "primary_key_checks": pk_results,
            "foreign_key_checks": fk_results,
            "enum_checks": enum_results,
            "timeline_checks": date_results,
        }

    def _check_primary_keys(self, cursor: sqlite3.Cursor) -> Dict[str, Any]:
        tables_pks = [
            ("plants", "plant_id"),
            ("machines", "machine_id"),
            ("safety_zones", "zone_id"),
            ("machine_safety_zones", "mapping_id"),
            ("interlocks", "interlock_id"),
            ("alarm_definitions", "alarm_def_id"),
            ("operator_shifts", "shift_id"),
            ("machine_state_history", "state_event_id"),
            ("alarm_events", "alarm_event_id"),
            ("acknowledgements", "ack_id"),
            ("incidents", "incident_id"),
            ("corrective_actions", "action_id"),
        ]

        pk_issues = []
        for table, pk in tables_pks:
            query = f"""
            SELECT {pk}, COUNT(*) 
            FROM {table} 
            GROUP BY {pk} 
            HAVING COUNT(*) > 1;
            """
            cursor.execute(query)
            dups = cursor.fetchall()
            if dups:
                pk_issues.append({"table": table, "pk_column": pk, "duplicates": dups})

        return {
            "passed": len(pk_issues) == 0,
            "total_tables_checked": len(tables_pks),
            "issues": pk_issues,
        }

    def _check_foreign_keys(self, cursor: sqlite3.Cursor) -> Dict[str, Any]:
        fk_relations = [
            ("machines", "plant_id", "plants", "plant_id"),
            ("safety_zones", "plant_id", "plants", "plant_id"),
            ("machine_safety_zones", "machine_id", "machines", "machine_id"),
            ("machine_safety_zones", "zone_id", "safety_zones", "zone_id"),
            ("interlocks", "machine_id", "machines", "machine_id"),
            ("interlocks", "zone_id", "safety_zones", "zone_id"),
            ("operator_shifts", "plant_id", "plants", "plant_id"),
            ("machine_state_history", "machine_id", "machines", "machine_id"),
            ("machine_state_history", "shift_id", "operator_shifts", "shift_id"),
            ("alarm_events", "machine_id", "machines", "machine_id"),
            ("alarm_events", "alarm_def_id", "alarm_definitions", "alarm_def_id"),
            ("alarm_events", "shift_id", "operator_shifts", "shift_id"),
            ("acknowledgements", "alarm_event_id", "alarm_events", "alarm_event_id"),
            ("acknowledgements", "shift_id", "operator_shifts", "shift_id"),
            ("incidents", "plant_id", "plants", "plant_id"),
            ("incidents", "machine_id", "machines", "machine_id"),
            ("incidents", "zone_id", "safety_zones", "zone_id"),
            ("incidents", "shift_id", "operator_shifts", "shift_id"),
            ("corrective_actions", "incident_id", "incidents", "incident_id"),
        ]

        fk_issues = []
        for child_tbl, child_col, parent_tbl, parent_col in fk_relations:
            query = f"""
            SELECT c.{child_col}
            FROM {child_tbl} c
            LEFT JOIN {parent_tbl} p ON c.{child_col} = p.{parent_col}
            WHERE c.{child_col} IS NOT NULL AND p.{parent_col} IS NULL;
            """
            cursor.execute(query)
            orphans = cursor.fetchall()
            if orphans:
                fk_issues.append({
                    "child_table": child_tbl,
                    "child_column": child_col,
                    "parent_table": parent_tbl,
                    "orphan_count": len(orphans),
                    "sample_orphans": [o[0] for o in orphans[:5]],
                })

        return {
            "passed": len(fk_issues) == 0,
            "total_relations_checked": len(fk_relations),
            "issues": fk_issues,
        }

    def _check_enums(self, cursor: sqlite3.Cursor) -> Dict[str, Any]:
        enum_rules = [
            ("machines", "criticality", ["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            ("safety_zones", "required_sil_level", ["SIL_1", "SIL_2", "SIL_3", "SIL_4"]),
            ("alarm_events", "severity", ["CRITICAL", "HIGH", "MEDIUM", "LOW"]),
            ("operator_shifts", "shift_type", ["MORNING", "AFTERNOON", "NIGHT"]),
            ("incidents", "severity", ["CRITICAL", "MAJOR", "MINOR", "NEAR_MISS"]),
            ("corrective_actions", "status", ["PENDING", "IN_PROGRESS", "COMPLETED", "VERIFIED", "CLOSED"]),
        ]

        enum_issues = []
        for tbl, col, allowed in enum_rules:
            allowed_str = ",".join(f"'{v}'" for v in allowed)
            query = f"""
            SELECT DISTINCT {col} 
            FROM {tbl} 
            WHERE {col} NOT IN ({allowed_str});
            """
            cursor.execute(query)
            invalids = cursor.fetchall()
            if invalids:
                enum_issues.append({
                    "table": tbl,
                    "column": col,
                    "invalid_values": [i[0] for i in invalids],
                })

        return {
            "passed": len(enum_issues) == 0,
            "total_enum_columns_checked": len(enum_rules),
            "issues": enum_issues,
        }

    def _check_timeline_coherence(self, cursor: sqlite3.Cursor) -> Dict[str, Any]:
        timeline_issues = []

        # 1. Shifts: end_time >= start_time
        cursor.execute("SELECT shift_id, start_time, end_time FROM operator_shifts WHERE end_time < start_time;")
        bad_shifts = cursor.fetchall()
        if bad_shifts:
            timeline_issues.append({
                "rule": "Shift end_time >= start_time",
                "violations": len(bad_shifts),
            })

        # 2. Alarms: cleared_timestamp >= timestamp
        cursor.execute("""
        SELECT alarm_event_id, timestamp, cleared_timestamp 
        FROM alarm_events 
        WHERE cleared_timestamp IS NOT NULL AND cleared_timestamp < timestamp;
        """)
        bad_alarms = cursor.fetchall()
        if bad_alarms:
            timeline_issues.append({
                "rule": "Alarm cleared_timestamp >= timestamp",
                "violations": len(bad_alarms),
            })

        # Note: acknowledgements where ack_timestamp < alarm.timestamp are injected edge cases,
        # which are audited by the EdgeCaseDetector!

        return {
            "passed": len(timeline_issues) == 0,
            "issues": timeline_issues,
        }
