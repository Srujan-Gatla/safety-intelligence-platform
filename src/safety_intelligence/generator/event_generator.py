"""Transactional event generator for shifts, machine states, alarms, acknowledgements, incidents, and actions."""

import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple

from safety_intelligence.config import (
    ScaleProfile,
    ISA_FLOOD_THRESHOLD_ALARMS,
    ISA_FLOOD_WINDOW_SECONDS,
    ISA_CHATTERING_WINDOW_SECONDS,
    ISA_CHATTERING_MIN_TRANSITIONS,
    ISA_FLEETING_MAX_SECONDS,
    SLA_ACK_TARGETS,
)
from safety_intelligence.models.core import (
    Plant,
    Machine,
    SafetyZone,
    Interlock,
    AlarmDefinition,
)
from safety_intelligence.models.transactions import (
    OperatorShift,
    MachineStateHistory,
    AlarmEvent,
    Acknowledgement,
    Incident,
    CorrectiveAction,
)
from safety_intelligence.models.ground_truth import GroundTruthRecurrentHazard


class TransactionalEventGenerator:
    """Generates time-ordered operational events, state changes, alarms, acknowledgements, and incidents."""

    def __init__(
        self,
        profile: ScaleProfile,
        rng: random.Random,
        plants: List[Plant],
        machines: List[Machine],
        zones: List[SafetyZone],
        interlocks: List[Interlock],
        alarm_defs: List[AlarmDefinition],
    ):
        self.profile = profile
        self.rng = rng
        self.plants = plants
        self.machines = machines
        self.zones = zones
        self.interlocks = interlocks
        self.alarm_defs = alarm_defs

        self.machines_by_plant = {}
        for m in machines:
            self.machines_by_plant.setdefault(m.plant_id, []).append(m)

        self.zones_by_plant = {}
        for z in zones:
            self.zones_by_plant.setdefault(z.plant_id, []).append(z)

        self.interlocks_by_machine = {}
        for itl in interlocks:
            self.interlocks_by_machine.setdefault(itl.machine_id, []).append(itl)

        self.machines_by_id = {m.machine_id: m for m in machines}
        self.alarm_defs_by_id = {d.alarm_def_id: d for d in alarm_defs}

    def generate_all(self) -> Tuple[
        List[OperatorShift],
        List[MachineStateHistory],
        List[AlarmEvent],
        List[Acknowledgement],
        List[Incident],
        List[CorrectiveAction],
        List[GroundTruthRecurrentHazard],
    ]:
        shifts = self.generate_shifts()
        shifts_by_plant_time = self._index_shifts(shifts)

        alarm_events = self.generate_alarms(shifts_by_plant_time)
        state_history = self.generate_state_history(shifts_by_plant_time, alarm_events)
        acknowledgements = self.generate_acknowledgements(alarm_events, shifts_by_plant_time)
        incidents, corrective_actions, recurrent_gt = self.generate_incidents_and_actions(
            alarm_events, state_history, shifts_by_plant_time
        )

        return (
            shifts,
            state_history,
            alarm_events,
            acknowledgements,
            incidents,
            corrective_actions,
            recurrent_gt,
        )

    def generate_shifts(self) -> List[OperatorShift]:
        shifts: List[OperatorShift] = []
        operators = [
            ("OPR-1001", "Marcus Vance"),
            ("OPR-1002", "Elena Rostova"),
            ("OPR-1003", "Chen Wei"),
            ("OPR-1004", "Amara Okafor"),
            ("OPR-1005", "Hans Gruber"),
            ("OPR-1006", "Sofia Rodriguez"),
            ("OPR-1007", "Kenji Sato"),
            ("OPR-1008", "David Kim"),
        ]
        supervisors = ["Sarah Connor", "Jim Lovell", "Ada Lovelace", "Alan Turing"]

        shift_blocks = [
            ("MORNING", 6, 14),
            ("AFTERNOON", 14, 22),
            ("NIGHT", 22, 6),
        ]

        total_days = self.profile.duration_days
        start_dt = self.profile.start_date

        for plant in self.plants:
            p_code = plant.plant_id.replace("-", "")
            shift_seq = 1
            for day_offset in range(total_days):
                day_start = start_dt + timedelta(days=day_offset)
                date_str = day_start.strftime("%Y%m%d")

                for s_type, s_hour, e_hour in shift_blocks:
                    shift_id = f"SHF-{p_code}-{date_str}-{shift_seq:02d}"
                    shift_start = day_start.replace(hour=s_hour, minute=0, second=0)
                    if s_type == "NIGHT":
                        shift_end = shift_start + timedelta(hours=8)
                    else:
                        shift_end = day_start.replace(hour=e_hour, minute=0, second=0)

                    opr = operators[(shift_seq + day_offset) % len(operators)]
                    sup = supervisors[(day_offset) % len(supervisors)]

                    shifts.append(
                        OperatorShift(
                            shift_id=shift_id,
                            plant_id=plant.plant_id,
                            operator_id=opr[0],
                            operator_name=opr[1],
                            shift_type=s_type,
                            start_time=shift_start.isoformat(),
                            end_time=shift_end.isoformat(),
                            supervisor_name=sup,
                            turnover_notes=f"Normal shift turnover at {plant.code}.",
                        )
                    )
                    shift_seq += 1

        return shifts

    def _index_shifts(self, shifts: List[OperatorShift]) -> Dict[str, List[OperatorShift]]:
        indexed = {}
        for s in shifts:
            indexed.setdefault(s.plant_id, []).append(s)
        return indexed

    def _find_shift_for_timestamp(
        self, plant_id: str, ts: datetime, shifts_by_plant: Dict[str, List[OperatorShift]]
    ) -> OperatorShift:
        plant_shifts = shifts_by_plant.get(plant_id, [])
        ts_iso = ts.isoformat()
        for s in plant_shifts:
            if s.start_time <= ts_iso <= s.end_time:
                return s
        return plant_shifts[0] if plant_shifts else None

    def generate_alarms(
        self, shifts_by_plant: Dict[str, List[OperatorShift]]
    ) -> List[AlarmEvent]:
        alarms: List[AlarmEvent] = []
        target_count = self.profile.num_alarm_events
        start_dt = self.profile.start_date
        total_seconds = int(self.profile.duration_days * 86400)

        # Distribute alarms across patterns:
        # 1. Alarm Floods (~15% of events): bursts of >10 alarms in <10 mins
        # 2. Chattering Alarms (~10% of events): rapid repetitive oscillation
        # 3. Fleeting Alarms (~10% of events): auto-clearing in <5s
        # 4. Critical & High Safety Alarms (~15% of events)
        # 5. Routine Process / Mechanical Alarms (~50% of events)

        machine_alarm_counters = {m.machine_id: 0 for m in self.machines}
        alarm_event_pool: List[Tuple[datetime, Machine, AlarmDefinition, str, float]] = []

        # 1. Alarm Floods
        num_floods = max(3, self.profile.duration_days // 3)
        for _ in range(num_floods):
            flood_machine = self.rng.choice(self.machines)
            flood_start_sec = self.rng.randint(3600, total_seconds - 3600)
            flood_start_dt = start_dt + timedelta(seconds=flood_start_sec)
            flood_size = self.rng.randint(12, 25)  # ISA-18.2 > 10 alarms / 10 mins
            for f_i in range(flood_size):
                f_ts = flood_start_dt + timedelta(seconds=self.rng.randint(0, 540))
                def_choice = self.rng.choice(self.alarm_defs)
                dur = float(self.rng.randint(60, 1800))
                alarm_event_pool.append((f_ts, flood_machine, def_choice, "FLOOD", dur))

        # 2. Chattering Alarms (burst of >= 3 within 60s)
        num_chatters = max(5, self.profile.num_machines // 2)
        for _ in range(num_chatters):
            chatter_machine = self.rng.choice(self.machines)
            chatter_def = self.rng.choice(
                [d for d in self.alarm_defs if d.category in ["PROCESS", "MECHANICAL"]]
                or self.alarm_defs
            )
            chatter_start_sec = self.rng.randint(1800, total_seconds - 1800)
            chatter_start_dt = start_dt + timedelta(seconds=chatter_start_sec)
            reps = self.rng.randint(4, 8)
            for r in range(reps):
                c_ts = chatter_start_dt + timedelta(seconds=r * self.rng.randint(5, 12))
                dur = float(self.rng.randint(3, 8))
                alarm_event_pool.append((c_ts, chatter_machine, chatter_def, "CHATTERING", dur))

        # 3. Fleeting Alarms (cleared in < 5 seconds)
        num_fleeting = max(10, self.profile.num_alarm_events // 20)
        for _ in range(num_fleeting):
            f_machine = self.rng.choice(self.machines)
            f_def = self.rng.choice(
                [d for d in self.alarm_defs if d.auto_resettable] or self.alarm_defs
            )
            f_sec = self.rng.randint(60, total_seconds - 60)
            f_ts = start_dt + timedelta(seconds=f_sec)
            dur = round(self.rng.uniform(0.5, 4.5), 2)  # < 5.0 seconds
            alarm_event_pool.append((f_ts, f_machine, f_def, "FLEETING", dur))

        # 4. Fill remainder with baseline & safety alarms
        remaining = max(100, target_count - len(alarm_event_pool))
        for _ in range(remaining):
            m = self.rng.choice(self.machines)
            # 20% critical/high safety, 80% other
            if self.rng.random() < 0.20:
                safety_defs = [d for d in self.alarm_defs if d.category == "SAFETY"]
                d = self.rng.choice(safety_defs or self.alarm_defs)
                dur = float(self.rng.randint(300, 7200))
            else:
                d = self.rng.choice(self.alarm_defs)
                dur = float(self.rng.randint(30, 3600))
            sec = self.rng.randint(0, total_seconds - 60)
            ts = start_dt + timedelta(seconds=sec)
            alarm_event_pool.append((ts, m, d, "NORMAL", dur))

        # Sort pool chronologically to preserve strict event ordering
        alarm_event_pool.sort(key=lambda x: x[0])

        # Step 6: Derive ISA-18.2 flood and chattering dynamically from rolling windows
        machine_timestamps = {}
        for ts, m, d, _, _ in alarm_event_pool:
            machine_timestamps.setdefault(m.machine_id, []).append((ts, d.alarm_def_id))

        for ts, m, d, gen_type, dur in alarm_event_pool:
            machine_alarm_counters[m.machine_id] += 1
            seq = machine_alarm_counters[m.machine_id]
            m_code = m.machine_id.replace("-", "")
            alarm_id = f"ALM-{m_code}-{seq:06d}"

            plant_id = m.plant_id
            shift = self._find_shift_for_timestamp(plant_id, ts, shifts_by_plant)
            shift_id = shift.shift_id if shift else "SHF-UNKNOWN"

            # Zone lookup
            plant_zones = self.zones_by_plant.get(plant_id, [])
            zone_id = plant_zones[0].zone_id if plant_zones else None

            cleared_ts = ts + timedelta(seconds=dur)
            sev = d.default_severity

            # ISA-18.2 rolling flood calculation: count alarms on this machine in [ts - 10 min, ts]
            all_machine_ts = machine_timestamps[m.machine_id]
            window_start = ts - timedelta(seconds=ISA_FLOOD_WINDOW_SECONDS)
            flood_count = sum(1 for (other_ts, _) in all_machine_ts if window_start <= other_ts <= ts)
            is_flood = flood_count > ISA_FLOOD_THRESHOLD_ALARMS

            # ISA-18.2 rolling chattering calculation: count same def on same machine in [ts - 60s, ts]
            chatter_window = ts - timedelta(seconds=ISA_CHATTERING_WINDOW_SECONDS)
            chatter_count = sum(
                1 for (other_ts, other_def) in all_machine_ts
                if chatter_window <= other_ts <= ts and other_def == d.alarm_def_id
            )
            is_chattering = chatter_count >= ISA_CHATTERING_MIN_TRANSITIONS

            # ISA-18.2 fleeting calculation
            is_fleeting = dur < ISA_FLEETING_MAX_SECONDS

            is_nuisance = is_chattering or is_fleeting
            nuisance_type = "CHATTERING" if is_chattering else ("FLEETING" if is_fleeting else "NONE")

            trigger_val = round(self.rng.uniform(105.0, 180.0), 2)
            thresh_val = 100.0

            alarms.append(
                AlarmEvent(
                    alarm_event_id=alarm_id,
                    machine_id=m.machine_id,
                    alarm_def_id=d.alarm_def_id,
                    zone_id=zone_id,
                    shift_id=shift_id,
                    timestamp=ts.isoformat(),
                    cleared_timestamp=cleared_ts.isoformat(),
                    duration_seconds=dur,
                    severity=sev,
                    trigger_value=trigger_val,
                    threshold_value=thresh_val,
                    lifecycle_state="CLEARED",
                    is_nuisance=is_nuisance,
                    nuisance_type=nuisance_type,
                    is_flood=is_flood,
                )
            )

        return alarms

    def generate_state_history(
        self,
        shifts_by_plant: Dict[str, List[OperatorShift]],
        alarms: List[AlarmEvent],
    ) -> List[MachineStateHistory]:
        history: List[MachineStateHistory] = []
        state_seq = 1

        # Group critical alarms by machine to guarantee non-overlapping, strictly continuous state transitions
        alarms_by_machine = {}
        for a in alarms:
            if a.severity in ["CRITICAL", "HIGH"]:
                alarms_by_machine.setdefault(a.machine_id, []).append(a)

        for m in self.machines:
            m_alarms = alarms_by_machine.get(m.machine_id, [])
            m_alarms.sort(key=lambda x: x.timestamp)
            m_code = m.machine_id.replace("-", "")

            current_state = "RUNNING"
            last_ts = self.profile.start_date.isoformat()

            for alm in m_alarms[:6]:  # Up to 6 state trip events per machine
                alm_ts = alm.timestamp
                clr_ts = alm.cleared_timestamp or alm_ts
                if alm_ts <= last_ts:
                    continue  # Skip overlapping events to preserve strict continuity

                itls = self.interlocks_by_machine.get(m.machine_id, [])
                itl_id = itls[0].interlock_id if itls else None

                # 1. RUNNING -> TRIPPED
                state_id_trip = f"MST-{m_code}-{state_seq:06d}"
                history.append(
                    MachineStateHistory(
                        state_event_id=state_id_trip,
                        machine_id=m.machine_id,
                        shift_id=alm.shift_id,
                        previous_state="RUNNING",
                        new_state="TRIPPED",
                        timestamp=alm_ts,
                        transition_reason=f"Emergency trip triggered by alarm {alm.alarm_event_id}",
                        interlock_trip_id=itl_id,
                    )
                )
                state_seq += 1

                # 2. TRIPPED -> RUNNING
                state_id_rec = f"MST-{m_code}-{state_seq:06d}"
                history.append(
                    MachineStateHistory(
                        state_event_id=state_id_rec,
                        machine_id=m.machine_id,
                        shift_id=alm.shift_id,
                        previous_state="TRIPPED",
                        new_state="RUNNING",
                        timestamp=clr_ts,
                        transition_reason=f"Safety reset and clearance for alarm {alm.alarm_event_id}",
                        interlock_trip_id=None,
                    )
                )
                state_seq += 1
                last_ts = clr_ts

        history.sort(key=lambda x: x.timestamp)
        return history

    def generate_acknowledgements(
        self,
        alarms: List[AlarmEvent],
        shifts_by_plant: Dict[str, List[OperatorShift]],
    ) -> List[Acknowledgement]:
        acknowledgements: List[Acknowledgement] = []
        ack_methods = ["HMI_TOUCH", "PHYSICAL_CONSOLE", "SCADA_DESK"]

        # Operator acknowledges ~85% of alarms (fleeting alarms often auto-clear without ack)
        for alm in alarms:
            if alm.nuisance_type == "FLEETING" and self.rng.random() < 0.8:
                continue  # Fleeting alarm cleared before operator touch

            if self.rng.random() > 0.90:
                continue  # 10% unacknowledged / ignored alarms

            alm_ts = datetime.fromisoformat(alm.timestamp)
            alm_def = self.alarm_defs_by_id.get(alm.alarm_def_id)
            sla_limit = alm_def.sla_ack_seconds if alm_def else 300

            # 85% acknowledged within SLA, 15% delayed (breached SLA)
            is_delayed = self.rng.random() < 0.15
            if is_delayed:
                latency = float(self.rng.randint(sla_limit + 10, sla_limit * 3))
            else:
                latency = round(self.rng.uniform(10.0, float(max(15, sla_limit - 10))), 2)

            ack_dt = alm_ts + timedelta(seconds=latency)
            sla_breached = latency > sla_limit

            # Deterministic nomenclature: ACK-<alarm-id>-01
            ack_id = f"ACK-{alm.alarm_event_id}-01"

            m_obj = self.machines_by_id.get(alm.machine_id)
            plant_id = m_obj.plant_id if m_obj else "PLT-01"
            shift = self._find_shift_for_timestamp(
                plant_id, ack_dt, shifts_by_plant
            )
            opr_id = shift.operator_id if shift else "OPR-1001"

            comment = (
                f"SLA Breached ({int(latency)}s latency). Operator investigation required."
                if sla_breached
                else "Acknowledged on primary console."
            )

            acknowledgements.append(
                Acknowledgement(
                    ack_id=ack_id,
                    alarm_event_id=alm.alarm_event_id,
                    shift_id=alm.shift_id,
                    operator_id=opr_id,
                    ack_timestamp=ack_dt.isoformat(),
                    latency_seconds=latency,
                    sla_breached=sla_breached,
                    ack_method=self.rng.choice(ack_methods),
                    comment=comment,
                )
            )

        acknowledgements.sort(key=lambda x: x.ack_timestamp)
        return acknowledgements

    def generate_incidents_and_actions(
        self,
        alarms: List[AlarmEvent],
        state_history: List[MachineStateHistory],
        shifts_by_plant: Dict[str, List[OperatorShift]],
    ) -> Tuple[List[Incident], List[CorrectiveAction], List[GroundTruthRecurrentHazard]]:
        incidents: List[Incident] = []
        actions: List[CorrectiveAction] = []
        recurrent_gt: List[GroundTruthRecurrentHazard] = []

        incident_types = [
            "INTERLOCK_BYPASS_VIOLATION",
            "ZONE_INTRUSION_DURING_CYCLE",
            "EMERGENCY_STOP_FAILURE",
            "THERMAL_RUNAWAY_BREACH",
            "UNCONTROLLED_MOTION",
        ]
        action_types = [
            "HARDWARE_REPLACEMENT",
            "SOFTWARE_INTERLOCK_UPDATE",
            "OPERATOR_RETRAINING",
            "SENSOR_CALIBRATION",
            "SAFETY_GUARD_REDESIGN",
        ]
        engineers = [
            "Dr. Aris Thorne (Chief Safety Eng)",
            "Ing. Marcus Vance (Reliability)",
            "Linnea Blom (Mechatronics QA)",
            "Daisuke Sato (OT Security Lead)",
        ]

        critical_alarms = [a for a in alarms if a.severity == "CRITICAL"]
        # Generate baseline incidents
        num_incidents = max(10, min(len(critical_alarms), self.profile.num_machines // 2))
        incident_candidates = self.rng.sample(critical_alarms, num_incidents)

        incident_seq = 1
        year_str = "2026"

        for alm in incident_candidates:
            inc_id = f"INC-{year_str}-{incident_seq:06d}"
            ts = datetime.fromisoformat(alm.timestamp) + timedelta(seconds=self.rng.randint(30, 300))
            itype = self.rng.choice(incident_types)
            sev = "CRITICAL" if itype == "EMERGENCY_STOP_FAILURE" else "MAJOR"
            osha = sev == "CRITICAL"
            lost_hours = round(self.rng.uniform(2.5, 24.0), 1) if osha else round(self.rng.uniform(0.5, 3.0), 1)

            # Machine lookup
            m = next((m for m in self.machines if m.machine_id == alm.machine_id), self.machines[0])
            plant_id = m.plant_id
            zone_id = alm.zone_id or "SAFE-PLT01-001"

            incidents.append(
                Incident(
                    incident_id=inc_id,
                    plant_id=plant_id,
                    machine_id=m.machine_id,
                    zone_id=zone_id,
                    triggering_alarm_id=alm.alarm_event_id,
                    shift_id=alm.shift_id,
                    timestamp=ts.isoformat(),
                    severity=sev,
                    incident_type=itype,
                    description=f"{sev} incident on {m.name}: {itype.replace('_', ' ')}.",
                    osha_reportable=osha,
                    lost_work_hours=lost_hours,
                    machine_state_at_incident="TRIPPED",
                    lifecycle_status="RESOLVED",
                )
            )

            # Generate corresponding Corrective Action
            act_id = f"ACT-{inc_id}-01"
            atype = self.rng.choice(action_types)
            due_dt = (ts + timedelta(days=5)).strftime("%Y-%m-%d")
            comp_dt = (ts + timedelta(days=3)).strftime("%Y-%m-%d")
            ver_dt = (ts + timedelta(days=4)).strftime("%Y-%m-%d")
            eng = self.rng.choice(engineers)

            actions.append(
                CorrectiveAction(
                    action_id=act_id,
                    incident_id=inc_id,
                    action_type=atype,
                    description=f"Implemented {atype.replace('_', ' ')} following root cause analysis.",
                    assigned_to=eng,
                    due_date=due_dt,
                    completed_date=comp_dt,
                    verified_by="Elena Rostova (Compliance QA)",
                    verification_date=ver_dt,
                    status="CLOSED",
                    effectiveness_score=round(self.rng.uniform(0.85, 0.98), 2),
                    recurrence_prevention_notes="Interlock dual-channel circuit upgraded and tested.",
                )
            )
            incident_seq += 1

        # Core Business Objective: Inject deliberate REPEATED UNSAFE CONDITIONS (Recurrent Incidents)
        # Select 3 machines where a corrective action was closed, but the unsafe condition recurred!
        num_recurrent_patterns = max(2, min(5, len(self.machines) // 6))
        recurrent_machines = self.machines[:num_recurrent_patterns]

        for p_idx, r_m in enumerate(recurrent_machines, start=1):
            inc_first_id = f"INC-{year_str}-{incident_seq:06d}"
            incident_seq += 1
            inc_second_id = f"INC-{year_str}-{incident_seq:06d}"
            incident_seq += 1

            first_ts = self.profile.start_date + timedelta(days=2, hours=self.rng.randint(8, 16))
            recur_days = self.rng.randint(7, 14)
            second_ts = first_ts + timedelta(days=recur_days)

            hazard = self.rng.choice(incident_types)
            plant_id = r_m.plant_id
            plant_zones = self.zones_by_plant.get(plant_id, self.zones)
            zone_id = plant_zones[0].zone_id

            first_shift = self._find_shift_for_timestamp(plant_id, first_ts, shifts_by_plant)
            second_shift = self._find_shift_for_timestamp(plant_id, second_ts, shifts_by_plant)

            # First Incident
            incidents.append(
                Incident(
                    incident_id=inc_first_id,
                    plant_id=plant_id,
                    machine_id=r_m.machine_id,
                    zone_id=zone_id,
                    triggering_alarm_id=None,
                    shift_id=first_shift.shift_id if first_shift else "SHF-UNKNOWN",
                    timestamp=first_ts.isoformat(),
                    severity="MAJOR",
                    incident_type=hazard,
                    description=f"Initial safety event on {r_m.name}: {hazard.replace('_', ' ')}.",
                    osha_reportable=False,
                    lost_work_hours=2.0,
                    machine_state_at_incident="TRIPPED",
                    lifecycle_status="RESOLVED",
                )
            )

            # Action closed prematurely / ineffectively
            act_id = f"ACT-{inc_first_id}-01"
            act_comp_dt = (first_ts + timedelta(days=3)).strftime("%Y-%m-%d")
            actions.append(
                CorrectiveAction(
                    action_id=act_id,
                    incident_id=inc_first_id,
                    action_type="OPERATOR_RETRAINING",
                    description="Superficial retraining without addressing root mechanical interlock drift.",
                    assigned_to="Marcus Vance (Reliability)",
                    due_date=(first_ts + timedelta(days=5)).strftime("%Y-%m-%d"),
                    completed_date=act_comp_dt,
                    verified_by="Auditor (Provisional)",
                    verification_date=act_comp_dt,
                    status="CLOSED",
                    effectiveness_score=0.35,  # Low effectiveness leading to recurrence
                    recurrence_prevention_notes="Briefing given, but physical hardware was unchanged.",
                )
            )

            # Recurrent Incident
            incidents.append(
                Incident(
                    incident_id=inc_second_id,
                    plant_id=plant_id,
                    machine_id=r_m.machine_id,
                    zone_id=zone_id,
                    triggering_alarm_id=None,
                    shift_id=second_shift.shift_id if second_shift else "SHF-UNKNOWN",
                    timestamp=second_ts.isoformat(),
                    severity="CRITICAL",
                    incident_type=hazard,
                    description=f"RECURRENT unsafe condition on {r_m.name}: {hazard.replace('_', ' ')} repeated after action {act_id} was closed.",
                    osha_reportable=True,
                    lost_work_hours=8.0,
                    machine_state_at_incident="TRIPPED",
                    lifecycle_status="UNDER_INVESTIGATION",
                )
            )

            # Record in Ground Truth
            pattern_id = f"GT-REC-{p_idx:04d}"
            recurrent_gt.append(
                GroundTruthRecurrentHazard(
                    pattern_id=pattern_id,
                    machine_id=r_m.machine_id,
                    zone_id=zone_id,
                    hazard_type=hazard,
                    first_incident_id=inc_first_id,
                    recurrent_incident_id=inc_second_id,
                    intervening_action_id=act_id,
                    days_to_recurrence=float(recur_days),
                    root_cause_finding=(
                        f"Corrective action {act_id} failed to prevent recurrence of {hazard}. "
                        f"Hardware drift in zone {zone_id} remained unmitigated."
                    ),
                )
            )

        incidents.sort(key=lambda x: x.timestamp)
        actions.sort(key=lambda x: x.action_id)

        return incidents, actions, recurrent_gt
