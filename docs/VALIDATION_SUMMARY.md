# Validation Summary Report

**Dataset Directory:** `data\full`  
**Overall Validation Status:** **PASSED**  

---

## 1. Relational Integrity Checks
- **Primary Key Uniqueness:** PASSED (12 tables verified)
- **Foreign Key Referential Integrity:** PASSED (19 relationships verified)
- **Domain Enum Constraints:** PASSED (6 columns checked)
- **Timeline Coherence:** PASSED (shift and alarm intervals verified)

---

## 2. Arithmetic Reconciliation & Lifecycles
- **Alarm Duration Arithmetic:** PASSED (50250 records reconciled)
- **Acknowledgement Latency Arithmetic:** PASSED (43165 records reconciled)
- **SLA Breach Threshold Flags:** PASSED (43165 records reconciled)
- **Machine State Transition Continuity:** PASSED (532 state transitions verified)

---

## 3. Deliberate Edge Cases / Negative Scenarios Audit
Audited against independent ground truth (`ground_truth_anomalies.json`):

| Edge Case Type | Detected Count | Detection Rule | System Decision |
| :--- | :--- | :--- | :--- |
| **ACK_BEFORE_ALARM** | 50 | `ack_timestamp < alarm_timestamp` | `REJECT_ACK_TIME_SKEW` |
| **INTERLOCK_STATE_IMPOSSIBLE** | 30 | `RUNNING` + `TRIPPED` + bypass=0 | `FLAG_SENSOR_FAILURE` |
| **INCIDENT_LACKS_TRIGGERING_CONTEXT** | 25 | Null trigger + 0 prior alarms | `AUDIT_UNLOGGED_TRIGGER` |
| **ALARM_FLOOD_REPLAY_DUPLICATE** | 250 | Duplicate telemetry replay burst | `DEDUPLICATE_REPLAY_TELEMETRY` |
| **ACTION_CLOSED_WITHOUT_VERIFICATION** | 30 | Status `CLOSED` with null QA | `REOPEN_UNVERIFIED_ACTION` |

### Ground Truth Detection Metrics
- **True Positives (TP):** 385
- **False Positives (FP):** 0
- **False Negatives (FN):** 0
- **Precision:** 1.0
- **Recall:** 1.0
- **F1 Score:** **1.0**
