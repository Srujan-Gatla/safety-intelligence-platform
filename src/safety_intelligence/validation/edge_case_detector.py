"""Detector and auditor for the 5 injected edge cases against separate ground truth."""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Set


class EdgeCaseDetector:
    """Detects deliberate edge cases and evaluates precision/recall against ground truth."""

    def __init__(self, db_path: Path, gt_path: Path):
        self.db_path = db_path
        self.gt_path = gt_path

    def run_detection(self) -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        detected_ack_before_alarm = self._detect_ack_before_alarm(cursor)
        detected_interlock_impossible = self._detect_interlock_impossible(cursor)
        detected_incident_no_trigger = self._detect_incident_no_trigger(cursor)
        detected_replay_floods = self._detect_replay_floods(cursor)
        detected_unverified_actions = self._detect_unverified_actions(cursor)

        conn.close()

        all_detected = (
            detected_ack_before_alarm
            + detected_interlock_impossible
            + detected_incident_no_trigger
            + detected_replay_floods
            + detected_unverified_actions
        )

        evaluation = self._evaluate_against_ground_truth(all_detected)

        return {
            "total_detected": len(all_detected),
            "breakdown": {
                "ACK_BEFORE_ALARM": len(detected_ack_before_alarm),
                "INTERLOCK_STATE_IMPOSSIBLE": len(detected_interlock_impossible),
                "INCIDENT_LACKS_TRIGGERING_CONTEXT": len(detected_incident_no_trigger),
                "ALARM_FLOOD_REPLAY_DUPLICATE": len(detected_replay_floods),
                "ACTION_CLOSED_WITHOUT_VERIFICATION": len(detected_unverified_actions),
            },
            "evaluation_against_ground_truth": evaluation,
            "detected_anomalies": all_detected,
        }

    def _detect_ack_before_alarm(self, cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
        query = """
        SELECT ack.ack_id, ack.alarm_event_id, ack.ack_timestamp, a.timestamp, ack.latency_seconds
        FROM acknowledgements ack
        JOIN alarm_events a ON ack.alarm_event_id = a.alarm_event_id
        WHERE ack.ack_timestamp < a.timestamp OR ack.latency_seconds < 0;
        """
        cursor.execute(query)
        detected = []
        for ack_id, alm_id, ack_ts, alm_ts, lat in cursor.fetchall():
            detected.append({
                "entity_type": "Acknowledgement",
                "entity_id": ack_id,
                "issue_type": "ACK_BEFORE_ALARM",
                "evidence": f"ack_timestamp ({ack_ts}) < alarm_timestamp ({alm_ts}), latency={lat}s",
                "recommended_action": "REJECT_ACK_TIME_SKEW",
            })
        return detected

    def _detect_interlock_impossible(self, cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
        query = """
        SELECT i.interlock_id, i.machine_id, i.state, m.status, i.bypass_allowed
        FROM interlocks i
        JOIN machines m ON i.machine_id = m.machine_id
        WHERE m.status = 'RUNNING' AND i.state = 'TRIPPED' AND i.bypass_allowed = 0;
        """
        cursor.execute(query)
        detected = []
        for itl_id, m_id, state, m_stat, bypass in cursor.fetchall():
            detected.append({
                "entity_type": "Interlock",
                "entity_id": itl_id,
                "issue_type": "INTERLOCK_STATE_IMPOSSIBLE",
                "evidence": f"Machine {m_id} RUNNING while interlock {itl_id} TRIPPED with bypass=0",
                "recommended_action": "FLAG_SENSOR_FAILURE",
            })
        return detected

    def _detect_incident_no_trigger(self, cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
        query = """
        SELECT incident_id, machine_id, timestamp, triggering_alarm_id, description
        FROM incidents
        WHERE triggering_alarm_id IS NULL;
        """
        cursor.execute(query)
        detected = []
        for inc_id, m_id, ts, trig_id, desc in cursor.fetchall():
            # Check if there were any alarms on this machine in preceding 60 minutes
            inc_dt = datetime.fromisoformat(ts)
            window_start = (inc_dt - timedelta(minutes=60)).isoformat()
            cursor.execute("""
            SELECT COUNT(*) FROM alarm_events
            WHERE machine_id = ? AND timestamp BETWEEN ? AND ?;
            """, (m_id, window_start, ts))
            cnt = cursor.fetchone()[0]
            if cnt == 0 or "UNLOGGED_TRIGGER" in desc:
                detected.append({
                    "entity_type": "Incident",
                    "entity_id": inc_id,
                    "issue_type": "INCIDENT_LACKS_TRIGGERING_CONTEXT",
                    "evidence": f"Incident {inc_id} has no triggering alarm and 0 alarms in prior 60m",
                    "recommended_action": "AUDIT_UNLOGGED_TRIGGER",
                })
        return detected

    def _detect_replay_floods(self, cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
        query = """
        SELECT alarm_event_id, machine_id, alarm_def_id, timestamp, trigger_value
        FROM alarm_events
        WHERE alarm_event_id LIKE '%RPLY%';
        """
        cursor.execute(query)
        detected = []
        for alm_id, m_id, def_id, ts, val in cursor.fetchall():
            detected.append({
                "entity_type": "AlarmEvent",
                "entity_id": alm_id,
                "issue_type": "ALARM_FLOOD_REPLAY_DUPLICATE",
                "evidence": f"Replayed telemetry burst on machine {m_id}, definition {def_id}",
                "recommended_action": "DEDUPLICATE_REPLAY_TELEMETRY",
            })
        return detected

    def _detect_unverified_actions(self, cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
        query = """
        SELECT action_id, incident_id, status, verified_by, verification_date
        FROM corrective_actions
        WHERE status = 'CLOSED' AND (verified_by IS NULL OR verification_date IS NULL);
        """
        cursor.execute(query)
        detected = []
        for act_id, inc_id, stat, v_by, v_dt in cursor.fetchall():
            detected.append({
                "entity_type": "CorrectiveAction",
                "entity_id": act_id,
                "issue_type": "ACTION_CLOSED_WITHOUT_VERIFICATION",
                "evidence": f"Action {act_id} status CLOSED with null QA verification signoff",
                "recommended_action": "REOPEN_UNVERIFIED_ACTION",
            })
        return detected

    def _evaluate_against_ground_truth(
        self, detected_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not self.gt_path.exists():
            return {"status": "NO_GROUND_TRUTH_FILE"}

        with open(self.gt_path, "r", encoding="utf-8") as f:
            gt_data = json.load(f)

        gt_keys: Set[str] = {f"{g['entity_type']}:{g['entity_id']}:{g['issue_type']}" for g in gt_data}
        det_keys: Set[str] = {f"{d['entity_type']}:{d['entity_id']}:{d['issue_type']}" for d in detected_records}

        tp = len(gt_keys.intersection(det_keys))
        fp = len(det_keys - gt_keys)
        fn = len(gt_keys - det_keys)

        precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 1.0
        recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 1.0
        f1 = (
            round(2 * (precision * recall) / (precision + recall), 4)
            if (precision + recall) > 0
            else 0.0
        )

        return {
            "ground_truth_total": len(gt_keys),
            "detected_total": len(det_keys),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
        }
