"""Validates derived calculations, arithmetic reconciliation, and lifecycle transitions."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class ArithmeticChecker:
    """Verifies derived values (durations, latencies, SLAs, status transitions) against source records."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def run_all_checks(self) -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        duration_results = self._check_alarm_durations(cursor)
        latency_results = self._check_acknowledgement_latencies(cursor)
        sla_results = self._check_sla_calculations(cursor)
        lifecycle_results = self._check_lifecycle_transitions(cursor)

        conn.close()

        all_passed = (
            duration_results["passed"]
            and latency_results["passed"]
            and sla_results["passed"]
            and lifecycle_results["passed"]
        )

        return {
            "passed": all_passed,
            "duration_checks": duration_results,
            "latency_checks": latency_results,
            "sla_checks": sla_results,
            "lifecycle_checks": lifecycle_results,
        }

    def _check_alarm_durations(self, cursor: sqlite3.Cursor) -> Dict[str, Any]:
        cursor.execute("""
        SELECT alarm_event_id, timestamp, cleared_timestamp, duration_seconds 
        FROM alarm_events 
        WHERE cleared_timestamp IS NOT NULL;
        """)
        rows = cursor.fetchall()
        discrepancies = []

        for alm_id, ts_str, clr_str, recorded_dur in rows:
            t0 = datetime.fromisoformat(ts_str)
            t1 = datetime.fromisoformat(clr_str)
            expected_dur = (t1 - t0).total_seconds()
            if abs(expected_dur - recorded_dur) > 0.05:
                discrepancies.append({
                    "alarm_id": alm_id,
                    "expected": expected_dur,
                    "recorded": recorded_dur,
                })

        return {
            "passed": len(discrepancies) == 0,
            "total_checked": len(rows),
            "discrepancy_count": len(discrepancies),
            "sample_discrepancies": discrepancies[:5],
        }

    def _check_acknowledgement_latencies(self, cursor: sqlite3.Cursor) -> Dict[str, Any]:
        cursor.execute("""
        SELECT ack.ack_id, a.timestamp, ack.ack_timestamp, ack.latency_seconds 
        FROM acknowledgements ack
        JOIN alarm_events a ON ack.alarm_event_id = a.alarm_event_id;
        """)
        rows = cursor.fetchall()
        discrepancies = []

        for ack_id, alm_ts_str, ack_ts_str, recorded_latency in rows:
            t_alm = datetime.fromisoformat(alm_ts_str)
            t_ack = datetime.fromisoformat(ack_ts_str)
            expected_latency = (t_ack - t_alm).total_seconds()
            if abs(expected_latency - recorded_latency) > 0.05:
                discrepancies.append({
                    "ack_id": ack_id,
                    "expected": expected_latency,
                    "recorded": recorded_latency,
                })

        return {
            "passed": len(discrepancies) == 0,
            "total_checked": len(rows),
            "discrepancy_count": len(discrepancies),
            "sample_discrepancies": discrepancies[:5],
        }

    def _check_sla_calculations(self, cursor: sqlite3.Cursor) -> Dict[str, Any]:
        cursor.execute("""
        SELECT ack.ack_id, ack.latency_seconds, d.sla_ack_seconds, ack.sla_breached
        FROM acknowledgements ack
        JOIN alarm_events a ON ack.alarm_event_id = a.alarm_event_id
        JOIN alarm_definitions d ON a.alarm_def_id = d.alarm_def_id;
        """)
        rows = cursor.fetchall()
        mismatches = []

        for ack_id, latency, sla_target, recorded_breach in rows:
            # For normal cases (latency >= 0), breach must match latency > sla_target
            if latency >= 0:
                expected_breach = 1 if latency > sla_target else 0
                if recorded_breach != expected_breach:
                    mismatches.append({
                        "ack_id": ack_id,
                        "latency": latency,
                        "sla_target": sla_target,
                        "recorded_breach": recorded_breach,
                        "expected_breach": expected_breach,
                    })

        return {
            "passed": len(mismatches) == 0,
            "total_checked": len(rows),
            "mismatch_count": len(mismatches),
            "sample_mismatches": mismatches[:5],
        }

    def _check_lifecycle_transitions(self, cursor: sqlite3.Cursor) -> Dict[str, Any]:
        cursor.execute("""
        SELECT state_event_id, machine_id, previous_state, new_state, timestamp
        FROM machine_state_history
        ORDER BY machine_id, timestamp ASC;
        """)
        rows = cursor.fetchall()
        issues = []
        last_state = {}

        for state_id, m_id, prev_s, new_s, ts in rows:
            if prev_s == new_s:
                issues.append({
                    "state_event_id": state_id,
                    "machine_id": m_id,
                    "issue": "Self-transition where previous_state == new_state",
                })
            if m_id in last_state and last_state[m_id] != prev_s:
                issues.append({
                    "state_event_id": state_id,
                    "machine_id": m_id,
                    "issue": f"State discontinuity: expected previous {last_state[m_id]}, got {prev_s}",
                })
            last_state[m_id] = new_s

        return {
            "passed": len(issues) == 0,
            "total_transitions_checked": len(rows),
            "issue_count": len(issues),
            "sample_issues": issues[:5],
        }
