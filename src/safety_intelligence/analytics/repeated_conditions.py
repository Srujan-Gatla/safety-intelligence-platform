"""Detects repeated unsafe conditions across machines, safety zones, and action lifecycles."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class RepeatedUnsafeConditionAnalyzer:
    """Analyzes incidents, machine states, interlocks, and actions to discover repeated hazards."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def analyze(self) -> Dict[str, Any]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        recurrent_incidents = self._find_recurrent_incidents(cursor)
        chronic_interlock_trips = self._find_chronic_interlock_trips(cursor)
        zone_hazard_hotspots = self._find_zone_hazard_hotspots(cursor)

        conn.close()

        total_patterns = len(recurrent_incidents) + len(chronic_interlock_trips)

        return {
            "total_repeated_conditions_found": total_patterns,
            "recurrent_incidents": recurrent_incidents,
            "chronic_interlock_trips": chronic_interlock_trips,
            "zone_hazard_hotspots": zone_hazard_hotspots,
        }

    def _find_recurrent_incidents(self, cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
        query = """
        SELECT 
            i.incident_id,
            i.plant_id,
            i.machine_id,
            m.name as machine_name,
            i.zone_id,
            z.name as zone_name,
            i.timestamp,
            i.severity,
            i.incident_type,
            i.description,
            act.action_id,
            act.status as action_status,
            act.effectiveness_score,
            act.verified_by,
            act.action_type
        FROM incidents i
        JOIN machines m ON i.machine_id = m.machine_id
        JOIN safety_zones z ON i.zone_id = z.zone_id
        LEFT JOIN corrective_actions act ON i.incident_id = act.incident_id
        ORDER BY i.machine_id, i.timestamp ASC;
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        recurrent_cases = []
        by_machine: Dict[str, List[Any]] = {}

        for r in rows:
            m_id = r[2]
            by_machine.setdefault(m_id, []).append(r)

        for m_id, inc_list in by_machine.items():
            if len(inc_list) < 2:
                continue

            for i in range(len(inc_list) - 1):
                first = inc_list[i]
                second = inc_list[i + 1]

                t1 = datetime.fromisoformat(first[6])
                t2 = datetime.fromisoformat(second[6])
                delta_days = round((t2 - t1).total_seconds() / 86400, 1)

                # Same machine, same or related hazard type within 30 days
                if first[8] == second[8] and delta_days <= 30.0:
                    intervening_action = first[10]
                    act_status = first[11]
                    eff_score = first[12]
                    v_by = first[13]

                    # Traceability assessment
                    if act_status == "CLOSED" and (eff_score is not None and eff_score < 0.60):
                        root_cause = "Ineffective corrective action closed without mitigating root drift"
                    elif act_status == "CLOSED" and v_by is None:
                        root_cause = "Corrective action closed without independent QA verification"
                    else:
                        root_cause = "Repeat mechanical or procedural failure under similar operational conditions"

                    recurrent_cases.append({
                        "pattern_type": "RECURRENT_INCIDENT",
                        "machine_id": m_id,
                        "machine_name": first[3],
                        "zone_id": first[4],
                        "zone_name": first[5],
                        "hazard_type": first[8],
                        "first_incident_id": first[0],
                        "first_incident_timestamp": first[6],
                        "recurrent_incident_id": second[0],
                        "recurrent_incident_timestamp": second[6],
                        "days_to_recurrence": delta_days,
                        "intervening_action_id": intervening_action,
                        "action_effectiveness": eff_score,
                        "root_cause_diagnosis": root_cause,
                        "severity_escalation": (
                            "ESCALATED" if second[7] == "CRITICAL" and first[7] != "CRITICAL" else "MAINTAINED"
                        ),
                    })

        return recurrent_cases

    def _find_chronic_interlock_trips(self, cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
        query = """
        SELECT 
            h.machine_id,
            m.name as machine_name,
            h.interlock_trip_id,
            itl.name as interlock_name,
            itl.interlock_type,
            itl.zone_id,
            COUNT(*) as trip_count,
            MIN(h.timestamp) as first_trip_ts,
            MAX(h.timestamp) as last_trip_ts
        FROM machine_state_history h
        JOIN machines m ON h.machine_id = m.machine_id
        LEFT JOIN interlocks itl ON h.interlock_trip_id = itl.interlock_id
        WHERE h.new_state = 'TRIPPED' AND h.interlock_trip_id IS NOT NULL
        GROUP BY h.machine_id, h.interlock_trip_id
        HAVING COUNT(*) >= 2
        ORDER BY trip_count DESC;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        chronic_trips = []

        for m_id, m_name, itl_id, itl_name, itl_type, z_id, count, first_ts, last_ts in rows:
            chronic_trips.append({
                "pattern_type": "CHRONIC_INTERLOCK_TRIP",
                "machine_id": m_id,
                "machine_name": m_name,
                "interlock_id": itl_id,
                "interlock_name": itl_name or "Unknown Interlock",
                "interlock_type": itl_type or "SAFETY_SENSOR",
                "zone_id": z_id,
                "trip_count": count,
                "first_trip": first_ts,
                "last_trip": last_ts,
                "risk_rating": "CRITICAL" if count >= 4 else "HIGH",
                "recommendation": (
                    f"Perform mechanical alignment and electrical loop test on {itl_id}. "
                    "Repeated tripping indicates physical guard misalignment or optical sensor drift."
                ),
            })

        return chronic_trips

    def _find_zone_hazard_hotspots(self, cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
        query = """
        SELECT 
            z.zone_id,
            z.name as zone_name,
            z.plant_id,
            z.hazard_classification,
            COUNT(DISTINCT i.incident_id) as total_incidents,
            COUNT(DISTINCT m.machine_id) as machines_involved,
            SUM(i.lost_work_hours) as total_lost_hours
        FROM safety_zones z
        JOIN incidents i ON z.zone_id = i.zone_id
        JOIN machines m ON i.machine_id = m.machine_id
        GROUP BY z.zone_id
        ORDER BY total_incidents DESC;
        """
        cursor.execute(query)
        hotspots = []
        for z_id, z_name, p_id, hazard, total_inc, total_mch, lost_hrs in cursor.fetchall():
            hotspots.append({
                "zone_id": z_id,
                "zone_name": z_name,
                "plant_id": p_id,
                "hazard_classification": hazard,
                "total_incidents": total_inc,
                "machines_involved": total_mch,
                "total_lost_hours": round(lost_hrs or 0.0, 1),
            })
        return hotspots
