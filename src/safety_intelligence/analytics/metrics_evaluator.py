"""Evaluates end-to-end performance metrics, ground truth precision/recall, and safety KPIs."""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Set

from safety_intelligence.analytics.repeated_conditions import RepeatedUnsafeConditionAnalyzer
from safety_intelligence.analytics.isa18_alarms import ISA18AlarmAnalyzer
from safety_intelligence.analytics.acknowledgement_sla import AcknowledgementSLAAnalyzer
from safety_intelligence.analytics.corrective_actions import CorrectiveActionAnalyzer


class SafetyMetricsEvaluator:
    """Computes operational safety KPIs and rigorous ground truth evaluation scores."""

    def __init__(self, dataset_dir: Path):
        self.dataset_dir = dataset_dir
        self.db_path = dataset_dir / "safety_platform.db"
        self.gt_anom_path = dataset_dir / "ground_truth" / "ground_truth_anomalies.json"
        self.gt_recur_path = dataset_dir / "ground_truth" / "ground_truth_recurrent.json"

    def compute_all_metrics(self) -> Dict[str, Any]:
        repeated_res = RepeatedUnsafeConditionAnalyzer(self.db_path).analyze()
        isa18_res = ISA18AlarmAnalyzer(self.db_path).analyze()
        sla_res = AcknowledgementSLAAnalyzer(self.db_path).analyze()
        actions_res = CorrectiveActionAnalyzer(self.db_path).analyze()

        recurrent_eval = self._evaluate_recurrent_patterns(repeated_res["recurrent_incidents"])
        kpis = self._compute_kpis(repeated_res, isa18_res, sla_res, actions_res)

        return {
            "dataset_directory": str(self.dataset_dir),
            "safety_kpis": kpis,
            "recurrent_hazard_evaluation": recurrent_eval,
            "repeated_conditions_summary": {
                "recurrent_incidents_detected": len(repeated_res["recurrent_incidents"]),
                "chronic_interlock_trips_detected": len(repeated_res["chronic_interlock_trips"]),
                "hazard_hotspots": len(repeated_res["zone_hazard_hotspots"]),
            },
            "isa18_summary": {
                "total_alarms": isa18_res["total_alarms"],
                "nuisance_alarm_ratio": isa18_res["nuisance_alarm_ratio"],
                "flood_alarms": isa18_res["alarm_floods"]["total_flood_alarm_events"],
            },
            "sla_summary": sla_res["overall_metrics"],
            "corrective_actions_summary": {
                "verification_compliance_percent": actions_res["verification_compliance"]["verification_compliance_percent"],
                "unverified_closed_actions": actions_res["verification_compliance"]["unverified_closed_actions"],
            },
        }

    def _evaluate_recurrent_patterns(
        self, detected_recurrent: list
    ) -> Dict[str, Any]:
        if not self.gt_recur_path.exists():
            return {"status": "NO_RECURRENT_GROUND_TRUTH_FILE"}

        with open(self.gt_recur_path, "r", encoding="utf-8") as f:
            gt_recurrent = json.load(f)

        gt_pairs: Set[str] = {f"{g['machine_id']}:{g['hazard_type']}" for g in gt_recurrent}
        det_pairs: Set[str] = {f"{d['machine_id']}:{d['hazard_type']}" for d in detected_recurrent}

        tp = len(gt_pairs.intersection(det_pairs))
        fp = len(det_pairs - gt_pairs)
        fn = len(gt_pairs - det_pairs)

        precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 1.0
        recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 1.0
        f1 = (
            round(2 * (precision * recall) / (precision + recall), 4)
            if (precision + recall) > 0
            else 0.0
        )

        return {
            "ground_truth_recurrent_patterns": len(gt_pairs),
            "detected_recurrent_patterns": len(det_pairs),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
        }

    def _compute_kpis(
        self,
        repeated_res: Dict[str, Any],
        isa18_res: Dict[str, Any],
        sla_res: Dict[str, Any],
        actions_res: Dict[str, Any],
    ) -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM incidents;")
        total_incidents = cursor.fetchone()[0]

        recurrent_count = len(repeated_res["recurrent_incidents"])
        recurrence_rate = (
            round((recurrent_count / total_incidents) * 100, 2)
            if total_incidents > 0
            else 0.0
        )

        # Average Mean Time To Recurrence (days)
        days_list = [c["days_to_recurrence"] for c in repeated_res["recurrent_incidents"]]
        avg_mttr_days = round(sum(days_list) / len(days_list), 1) if days_list else None

        conn.close()

        return {
            "incident_recurrence_rate_percent": recurrence_rate,
            "mean_time_between_recurrent_conditions_days": avg_mttr_days,
            "isa18_nuisance_alarm_percent": round(isa18_res["nuisance_alarm_ratio"] * 100, 2),
            "operator_acknowledgement_sla_compliance_percent": sla_res["overall_metrics"]["sla_compliance_rate_percent"],
            "unverified_closed_action_rate_percent": round(
                100.0 - actions_res["verification_compliance"]["verification_compliance_percent"], 2
            ),
        }
