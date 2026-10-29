# Maintenance & Quality Engineering Dossier

## Recurring Unsafe Conditions & Root Cause Diagnosis
Total Recurrent Incidents Detected: **6**

| Machine | Safety Zone | Hazard Type | Recurrence Interval | Intervening Action | Root Cause Diagnosis |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `MCH-002` | `SAFE-PLT02-001` | EMERGENCY_STOP_FAILURE | 14.0 days | `ACT-INC-2026-000033-01` | Ineffective corrective action closed without mitigating root drift |
| `MCH-002` | `SAFE-PLT02-001` | EMERGENCY_STOP_FAILURE | 3.7 days | `None` | Repeat mechanical or procedural failure under similar operational conditions |
| `MCH-003` | `SAFE-PLT03-001` | UNCONTROLLED_MOTION | 12.0 days | `ACT-INC-2026-000035-01` | Ineffective corrective action closed without mitigating root drift |
| `MCH-004` | `SAFE-PLT04-001` | EMERGENCY_STOP_FAILURE | 7.0 days | `ACT-INC-2026-000037-01` | Ineffective corrective action closed without mitigating root drift |
| `MCH-005` | `SAFE-PLT01-001` | INTERLOCK_BYPASS_VIOLATION | 11.0 days | `ACT-INC-2026-000039-01` | Ineffective corrective action closed without mitigating root drift |
| `MCH-010` | `SAFE-PLT02-001` | THERMAL_RUNAWAY_BREACH | 2.6 days | `ACT-INC-2026-000014-01` | Corrective action closed without independent QA verification |

---

## Chronic Interlock Tripping Sensors
Total Repeating Sensor Trips: **59**

| Interlock Tag | Machine | Sensor Type | Trip Count | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| `ITL-MCH009-01` | `MCH-009` | GUARD_DOOR | **6** | Perform mechanical alignment and electrical loop test on ITL-MCH009-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH014-01` | `MCH-014` | GUARD_DOOR | **6** | Perform mechanical alignment and electrical loop test on ITL-MCH014-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH024-01` | `MCH-024` | GUARD_DOOR | **6** | Perform mechanical alignment and electrical loop test on ITL-MCH024-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH027-01` | `MCH-027` | GUARD_DOOR | **6** | Perform mechanical alignment and electrical loop test on ITL-MCH027-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH029-01` | `MCH-029` | GUARD_DOOR | **6** | Perform mechanical alignment and electrical loop test on ITL-MCH029-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH034-01` | `MCH-034` | GUARD_DOOR | **6** | Perform mechanical alignment and electrical loop test on ITL-MCH034-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH039-01` | `MCH-039` | GUARD_DOOR | **6** | Perform mechanical alignment and electrical loop test on ITL-MCH039-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH042-01` | `MCH-042` | GUARD_DOOR | **6** | Perform mechanical alignment and electrical loop test on ITL-MCH042-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH046-01` | `MCH-046` | GUARD_DOOR | **6** | Perform mechanical alignment and electrical loop test on ITL-MCH046-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH050-01` | `MCH-050` | GUARD_DOOR | **6** | Perform mechanical alignment and electrical loop test on ITL-MCH050-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH051-01` | `MCH-051` | GUARD_DOOR | **6** | Perform mechanical alignment and electrical loop test on ITL-MCH051-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH055-01` | `MCH-055` | GUARD_DOOR | **6** | Perform mechanical alignment and electrical loop test on ITL-MCH055-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH006-01` | `MCH-006` | GUARD_DOOR | **5** | Perform mechanical alignment and electrical loop test on ITL-MCH006-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH007-01` | `MCH-007` | GUARD_DOOR | **5** | Perform mechanical alignment and electrical loop test on ITL-MCH007-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH010-01` | `MCH-010` | GUARD_DOOR | **5** | Perform mechanical alignment and electrical loop test on ITL-MCH010-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH015-01` | `MCH-015` | GUARD_DOOR | **5** | Perform mechanical alignment and electrical loop test on ITL-MCH015-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH028-01` | `MCH-028` | GUARD_DOOR | **5** | Perform mechanical alignment and electrical loop test on ITL-MCH028-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH030-01` | `MCH-030` | GUARD_DOOR | **5** | Perform mechanical alignment and electrical loop test on ITL-MCH030-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH032-01` | `MCH-032` | GUARD_DOOR | **5** | Perform mechanical alignment and electrical loop test on ITL-MCH032-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH033-01` | `MCH-033` | GUARD_DOOR | **5** | Perform mechanical alignment and electrical loop test on ITL-MCH033-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH038-01` | `MCH-038` | GUARD_DOOR | **5** | Perform mechanical alignment and electrical loop test on ITL-MCH038-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH041-01` | `MCH-041` | GUARD_DOOR | **5** | Perform mechanical alignment and electrical loop test on ITL-MCH041-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH044-01` | `MCH-044` | GUARD_DOOR | **5** | Perform mechanical alignment and electrical loop test on ITL-MCH044-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH045-01` | `MCH-045` | GUARD_DOOR | **5** | Perform mechanical alignment and electrical loop test on ITL-MCH045-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH048-01` | `MCH-048` | GUARD_DOOR | **5** | Perform mechanical alignment and electrical loop test on ITL-MCH048-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH052-01` | `MCH-052` | GUARD_DOOR | **5** | Perform mechanical alignment and electrical loop test on ITL-MCH052-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH057-01` | `MCH-057` | GUARD_DOOR | **5** | Perform mechanical alignment and electrical loop test on ITL-MCH057-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH058-01` | `MCH-058` | GUARD_DOOR | **5** | Perform mechanical alignment and electrical loop test on ITL-MCH058-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH059-01` | `MCH-059` | GUARD_DOOR | **5** | Perform mechanical alignment and electrical loop test on ITL-MCH059-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH002-01` | `MCH-002` | GUARD_DOOR | **4** | Perform mechanical alignment and electrical loop test on ITL-MCH002-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH003-01` | `MCH-003` | GUARD_DOOR | **4** | Perform mechanical alignment and electrical loop test on ITL-MCH003-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH004-01` | `MCH-004` | GUARD_DOOR | **4** | Perform mechanical alignment and electrical loop test on ITL-MCH004-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH008-01` | `MCH-008` | GUARD_DOOR | **4** | Perform mechanical alignment and electrical loop test on ITL-MCH008-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH011-01` | `MCH-011` | GUARD_DOOR | **4** | Perform mechanical alignment and electrical loop test on ITL-MCH011-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH012-01` | `MCH-012` | GUARD_DOOR | **4** | Perform mechanical alignment and electrical loop test on ITL-MCH012-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH013-01` | `MCH-013` | GUARD_DOOR | **4** | Perform mechanical alignment and electrical loop test on ITL-MCH013-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH017-01` | `MCH-017` | GUARD_DOOR | **4** | Perform mechanical alignment and electrical loop test on ITL-MCH017-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH019-01` | `MCH-019` | GUARD_DOOR | **4** | Perform mechanical alignment and electrical loop test on ITL-MCH019-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH020-01` | `MCH-020` | GUARD_DOOR | **4** | Perform mechanical alignment and electrical loop test on ITL-MCH020-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH021-01` | `MCH-021` | GUARD_DOOR | **4** | Perform mechanical alignment and electrical loop test on ITL-MCH021-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH022-01` | `MCH-022` | GUARD_DOOR | **4** | Perform mechanical alignment and electrical loop test on ITL-MCH022-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH023-01` | `MCH-023` | GUARD_DOOR | **4** | Perform mechanical alignment and electrical loop test on ITL-MCH023-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH026-01` | `MCH-026` | GUARD_DOOR | **4** | Perform mechanical alignment and electrical loop test on ITL-MCH026-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH036-01` | `MCH-036` | GUARD_DOOR | **4** | Perform mechanical alignment and electrical loop test on ITL-MCH036-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH037-01` | `MCH-037` | GUARD_DOOR | **4** | Perform mechanical alignment and electrical loop test on ITL-MCH037-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH040-01` | `MCH-040` | GUARD_DOOR | **4** | Perform mechanical alignment and electrical loop test on ITL-MCH040-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH047-01` | `MCH-047` | GUARD_DOOR | **4** | Perform mechanical alignment and electrical loop test on ITL-MCH047-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH049-01` | `MCH-049` | GUARD_DOOR | **4** | Perform mechanical alignment and electrical loop test on ITL-MCH049-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH060-01` | `MCH-060` | GUARD_DOOR | **4** | Perform mechanical alignment and electrical loop test on ITL-MCH060-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH001-01` | `MCH-001` | GUARD_DOOR | **3** | Perform mechanical alignment and electrical loop test on ITL-MCH001-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH018-01` | `MCH-018` | GUARD_DOOR | **3** | Perform mechanical alignment and electrical loop test on ITL-MCH018-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH025-01` | `MCH-025` | GUARD_DOOR | **3** | Perform mechanical alignment and electrical loop test on ITL-MCH025-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH031-01` | `MCH-031` | GUARD_DOOR | **3** | Perform mechanical alignment and electrical loop test on ITL-MCH031-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH043-01` | `MCH-043` | GUARD_DOOR | **3** | Perform mechanical alignment and electrical loop test on ITL-MCH043-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH053-01` | `MCH-053` | GUARD_DOOR | **3** | Perform mechanical alignment and electrical loop test on ITL-MCH053-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH054-01` | `MCH-054` | GUARD_DOOR | **3** | Perform mechanical alignment and electrical loop test on ITL-MCH054-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH056-01` | `MCH-056` | GUARD_DOOR | **3** | Perform mechanical alignment and electrical loop test on ITL-MCH056-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH005-01` | `MCH-005` | GUARD_DOOR | **2** | Perform mechanical alignment and electrical loop test on ITL-MCH005-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |
| `ITL-MCH016-01` | `MCH-016` | GUARD_DOOR | **2** | Perform mechanical alignment and electrical loop test on ITL-MCH016-01. Repeated tripping indicates physical guard misalignment or optical sensor drift. |

---

## Verification Compliance Audit
- **Closed Actions Audited:** 35
- **Unverified Actions (Compliance Violation):** **30**
- **Verification Rate:** 14.29%
