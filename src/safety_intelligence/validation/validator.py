"""Orchestrator for all validation suites: schema integrity, arithmetic reconciliation, and edge case audits."""

import json
from pathlib import Path
from typing import Any, Dict

from safety_intelligence.validation.integrity_checker import IntegrityChecker
from safety_intelligence.validation.arithmetic_checker import ArithmeticChecker
from safety_intelligence.validation.edge_case_detector import EdgeCaseDetector


class DatasetValidator:
    """Runs complete end-to-end dataset validation and generates summary reports."""

    def __init__(self, dataset_dir: Path):
        self.dataset_dir = dataset_dir
        self.db_path = dataset_dir / "safety_platform.db"
        self.gt_path = dataset_dir / "ground_truth" / "ground_truth_anomalies.json"

    def validate_all(self) -> Dict[str, Any]:
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found at {self.db_path}")

        integrity = IntegrityChecker(self.db_path).run_all_checks()
        arithmetic = ArithmeticChecker(self.db_path).run_all_checks()
        edge_cases = EdgeCaseDetector(self.db_path, self.gt_path).run_detection()

        overall_status = "PASSED" if (integrity["passed"] and arithmetic["passed"]) else "FAILED"

        summary = {
            "dataset_directory": str(self.dataset_dir),
            "overall_status": overall_status,
            "integrity_checks": integrity,
            "arithmetic_checks": arithmetic,
            "edge_case_audit": edge_cases,
        }

        # Save summary JSON
        summary_path = self.dataset_dir / "validation_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return summary

    def generate_markdown_report(self) -> str:
        res = self.validate_all()
        integ = res["integrity_checks"]
        arith = res["arithmetic_checks"]
        ec = res["edge_case_audit"]
        eval_metrics = ec.get("evaluation_against_ground_truth", {})

        md = f"""# Validation Summary Report

**Dataset Directory:** `{res['dataset_directory']}`  
**Overall Validation Status:** **{res['overall_status']}**  

---

## 1. Relational Integrity Checks
- **Primary Key Uniqueness:** {'PASSED' if integ['primary_key_checks']['passed'] else 'FAILED'} ({integ['primary_key_checks']['total_tables_checked']} tables verified)
- **Foreign Key Referential Integrity:** {'PASSED' if integ['foreign_key_checks']['passed'] else 'FAILED'} ({integ['foreign_key_checks']['total_relations_checked']} relationships verified)
- **Domain Enum Constraints:** {'PASSED' if integ['enum_checks']['passed'] else 'FAILED'} ({integ['enum_checks']['total_enum_columns_checked']} columns checked)
- **Timeline Coherence:** {'PASSED' if integ['timeline_checks']['passed'] else 'FAILED'} (shift and alarm intervals verified)

---

## 2. Arithmetic Reconciliation & Lifecycles
- **Alarm Duration Arithmetic:** {'PASSED' if arith['duration_checks']['passed'] else 'FAILED'} ({arith['duration_checks']['total_checked']} records reconciled)
- **Acknowledgement Latency Arithmetic:** {'PASSED' if arith['latency_checks']['passed'] else 'FAILED'} ({arith['latency_checks']['total_checked']} records reconciled)
- **SLA Breach Threshold Flags:** {'PASSED' if arith['sla_checks']['passed'] else 'FAILED'} ({arith['sla_checks']['total_checked']} records reconciled)
- **Machine State Transition Continuity:** {'PASSED' if arith['lifecycle_checks']['passed'] else 'FAILED'} ({arith['lifecycle_checks']['total_transitions_checked']} state transitions verified)

---

## 3. Deliberate Edge Cases / Negative Scenarios Audit
Audited against independent ground truth (`ground_truth_anomalies.json`):

| Edge Case Type | Detected Count | Detection Rule | System Decision |
| :--- | :--- | :--- | :--- |
| **ACK_BEFORE_ALARM** | {ec['breakdown'].get('ACK_BEFORE_ALARM', 0)} | `ack_timestamp < alarm_timestamp` | `REJECT_ACK_TIME_SKEW` |
| **INTERLOCK_STATE_IMPOSSIBLE** | {ec['breakdown'].get('INTERLOCK_STATE_IMPOSSIBLE', 0)} | `RUNNING` + `TRIPPED` + bypass=0 | `FLAG_SENSOR_FAILURE` |
| **INCIDENT_LACKS_TRIGGERING_CONTEXT** | {ec['breakdown'].get('INCIDENT_LACKS_TRIGGERING_CONTEXT', 0)} | Null trigger + 0 prior alarms | `AUDIT_UNLOGGED_TRIGGER` |
| **ALARM_FLOOD_REPLAY_DUPLICATE** | {ec['breakdown'].get('ALARM_FLOOD_REPLAY_DUPLICATE', 0)} | Duplicate telemetry replay burst | `DEDUPLICATE_REPLAY_TELEMETRY` |
| **ACTION_CLOSED_WITHOUT_VERIFICATION** | {ec['breakdown'].get('ACTION_CLOSED_WITHOUT_VERIFICATION', 0)} | Status `CLOSED` with null QA | `REOPEN_UNVERIFIED_ACTION` |

### Ground Truth Detection Metrics
- **True Positives (TP):** {eval_metrics.get('true_positives', 'N/A')}
- **False Positives (FP):** {eval_metrics.get('false_positives', 'N/A')}
- **False Negatives (FN):** {eval_metrics.get('false_negatives', 'N/A')}
- **Precision:** {eval_metrics.get('precision', 'N/A')}
- **Recall:** {eval_metrics.get('recall', 'N/A')}
- **F1 Score:** **{eval_metrics.get('f1_score', 'N/A')}**
"""
        # Save markdown report to docs/VALIDATION_SUMMARY.md
        docs_file = self.dataset_dir.parent.parent / "docs" / "VALIDATION_SUMMARY.md"
        docs_file.write_text(md, encoding="utf-8")
        return md
