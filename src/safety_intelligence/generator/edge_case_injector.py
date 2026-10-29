"""Injects the 5 required negative edge cases and records them into separate ground truth."""

import random
from datetime import datetime, timedelta
from typing import List, Tuple

from safety_intelligence.config import ScaleProfile
from safety_intelligence.models.core import Machine, Interlock
from safety_intelligence.models.transactions import (
    AlarmEvent,
    Acknowledgement,
    Incident,
    CorrectiveAction,
    MachineStateHistory,
)
from safety_intelligence.models.ground_truth import GroundTruthAnomaly


class EdgeCaseInjector:
    """Injects 5 labeled edge cases into transaction records and compiles ground truth."""

    def __init__(self, profile: ScaleProfile, rng: random.Random):
        self.profile = profile
        self.rng = rng

    def inject_all(
        self,
        machines: List[Machine],
        interlocks: List[Interlock],
        alarms: List[AlarmEvent],
        acknowledgements: List[Acknowledgement],
        incidents: List[Incident],
        actions: List[CorrectiveAction],
        state_history: List[MachineStateHistory],
    ) -> Tuple[
        List[Acknowledgement],
        List[Interlock],
        List[Incident],
        List[AlarmEvent],
        List[CorrectiveAction],
        List[GroundTruthAnomaly],
    ]:
        ground_truth: List[GroundTruthAnomaly] = []
        anomaly_counter = 1

        # 1. Edge Case 1: Acknowledgement before alarm
        anomaly_counter = self._inject_ack_before_alarm(
            acknowledgements, alarms, ground_truth, anomaly_counter
        )

        # 2. Edge Case 2: Interlock state impossible
        anomaly_counter = self._inject_interlock_impossible(
            interlocks, machines, state_history, ground_truth, anomaly_counter
        )

        # 3. Edge Case 3: Safety incident lacks triggering context
        anomaly_counter = self._inject_incident_no_trigger(
            incidents, alarms, ground_truth, anomaly_counter
        )

        # 4. Edge Case 4: Alarm flood duplicated by replay
        anomaly_counter = self._inject_replay_flood(
            alarms, ground_truth, anomaly_counter
        )

        # 5. Edge Case 5: Action closed without verification
        anomaly_counter = self._inject_unverified_actions(
            actions, ground_truth, anomaly_counter
        )

        ground_truth.sort(key=lambda x: x.anomaly_id)
        return acknowledgements, interlocks, incidents, alarms, actions, ground_truth

    def _inject_ack_before_alarm(
        self,
        acknowledgements: List[Acknowledgement],
        alarms: List[AlarmEvent],
        ground_truth: List[GroundTruthAnomaly],
        counter: int,
    ) -> int:
        alarms_by_id = {a.alarm_event_id: a for a in alarms}
        target_count = min(self.profile.num_ack_before_alarm, len(acknowledgements))
        sampled_indices = self.rng.sample(range(len(acknowledgements)), target_count)

        for idx in sampled_indices:
            ack = acknowledgements[idx]
            linked_alarm = alarms_by_id.get(ack.alarm_event_id)
            if not linked_alarm:
                continue

            alarm_dt = datetime.fromisoformat(linked_alarm.timestamp)
            # Set ack_timestamp to 30 to 180 seconds BEFORE alarm triggered
            skew_seconds = self.rng.randint(30, 180)
            corrupted_ack_dt = alarm_dt - timedelta(seconds=skew_seconds)

            # Update acknowledgement record
            ack.ack_timestamp = corrupted_ack_dt.isoformat()
            ack.latency_seconds = -float(skew_seconds)
            ack.comment = "Acknowledged via remote terminal (timestamp desynchronized)."

            anom_id = f"GT-ANOM-{counter:05d}"
            counter += 1
            ground_truth.append(
                GroundTruthAnomaly(
                    anomaly_id=anom_id,
                    entity_type="Acknowledgement",
                    entity_id=ack.ack_id,
                    issue_type="ACK_BEFORE_ALARM",
                    description=(
                        f"Acknowledgement {ack.ack_id} timestamp precedes alarm "
                        f"{ack.alarm_event_id} by {skew_seconds}s (clock skew / packet reordering)."
                    ),
                    detection_rule="Acknowledgement.ack_timestamp < AlarmEvent.timestamp",
                    expected_decision="REJECT_ACK_TIME_SKEW",
                    severity="HIGH",
                    injected_timestamp=ack.ack_timestamp,
                )
            )

        return counter

    def _inject_interlock_impossible(
        self,
        interlocks: List[Interlock],
        machines: List[Machine],
        state_history: List[MachineStateHistory],
        ground_truth: List[GroundTruthAnomaly],
        counter: int,
    ) -> int:
        running_machines = {m.machine_id for m in machines if m.status == "RUNNING"}
        target_count = min(self.profile.num_interlock_impossible, len(interlocks))

        candidate_interlocks = [
            itl for itl in interlocks
            if itl.machine_id in running_machines and not itl.bypass_allowed
        ]
        selected = self.rng.sample(
            candidate_interlocks, min(target_count, len(candidate_interlocks))
        )

        for itl in selected:
            # Physical impossibility: machine is actively RUNNING while safety interlock is TRIPPED
            # and bypass is strictly forbidden by safety standard
            itl.state = "TRIPPED"

            anom_id = f"GT-ANOM-{counter:05d}"
            counter += 1
            ground_truth.append(
                GroundTruthAnomaly(
                    anomaly_id=anom_id,
                    entity_type="Interlock",
                    entity_id=itl.interlock_id,
                    issue_type="INTERLOCK_STATE_IMPOSSIBLE",
                    description=(
                        f"Interlock {itl.interlock_id} is marked TRIPPED on actively RUNNING "
                        f"machine {itl.machine_id} with bypass_allowed=False."
                    ),
                    detection_rule="Machine.status == 'RUNNING' and Interlock.state == 'TRIPPED' and not Interlock.bypass_allowed",
                    expected_decision="FLAG_SENSOR_FAILURE",
                    severity="CRITICAL",
                    injected_timestamp=self.profile.start_date.isoformat(),
                )
            )

        return counter

    def _inject_incident_no_trigger(
        self,
        incidents: List[Incident],
        alarms: List[AlarmEvent],
        ground_truth: List[GroundTruthAnomaly],
        counter: int,
    ) -> int:
        target_count = min(self.profile.num_incident_no_trigger, len(incidents))
        sampled_indices = self.rng.sample(range(len(incidents)), target_count)

        for idx in sampled_indices:
            inc = incidents[idx]
            # Strip triggering alarm and point to orphan/none
            inc.triggering_alarm_id = None
            inc.description = f"{inc.description} [UNLOGGED_TRIGGER: Occurred without pre-alarm telemetry]"

            anom_id = f"GT-ANOM-{counter:05d}"
            counter += 1
            ground_truth.append(
                GroundTruthAnomaly(
                    anomaly_id=anom_id,
                    entity_type="Incident",
                    entity_id=inc.incident_id,
                    issue_type="INCIDENT_LACKS_TRIGGERING_CONTEXT",
                    description=(
                        f"High severity safety incident {inc.incident_id} lacks triggering alarm "
                        f"and has no pre-incident sensor alarm telemetry."
                    ),
                    detection_rule="Incident.triggering_alarm_id is NULL and preceding_alarm_count == 0",
                    expected_decision="AUDIT_UNLOGGED_TRIGGER",
                    severity="CRITICAL",
                    injected_timestamp=inc.timestamp,
                )
            )

        return counter

    def _inject_replay_flood(
        self,
        alarms: List[AlarmEvent],
        ground_truth: List[GroundTruthAnomaly],
        counter: int,
    ) -> int:
        flood_alarms = [a for a in alarms if a.is_flood]
        if len(flood_alarms) < 20:
            flood_alarms = alarms[:50]

        num_clusters = self.profile.num_replay_clusters
        cluster_size = self.profile.replay_alarms_per_cluster

        for c_idx in range(num_clusters):
            start_idx = (c_idx * cluster_size) % max(1, len(flood_alarms) - cluster_size)
            source_cluster = flood_alarms[start_idx : start_idx + cluster_size]

            # Replay after 48 hours with identical telemetry payload and sequence structure
            replay_offset = timedelta(hours=48 + c_idx * 12)

            for src in source_cluster:
                src_ts = datetime.fromisoformat(src.timestamp)
                replay_ts = src_ts + replay_offset
                cleared_ts = (
                    datetime.fromisoformat(src.cleared_timestamp) + replay_offset
                    if src.cleared_timestamp
                    else None
                )

                # Duplicate replay ID nomenclature
                m_code = src.machine_id.replace("-", "")
                dup_alarm_id = f"ALM-{m_code}-RPLY{counter:04d}"

                replayed_alarm = AlarmEvent(
                    alarm_event_id=dup_alarm_id,
                    machine_id=src.machine_id,
                    alarm_def_id=src.alarm_def_id,
                    zone_id=src.zone_id,
                    shift_id=src.shift_id,
                    timestamp=replay_ts.isoformat(),
                    cleared_timestamp=cleared_ts.isoformat() if cleared_ts else None,
                    duration_seconds=src.duration_seconds,
                    severity=src.severity,
                    trigger_value=src.trigger_value,  # Exact duplicate payload
                    threshold_value=src.threshold_value,
                    lifecycle_state="CLEARED",
                    is_nuisance=src.is_nuisance,
                    nuisance_type=src.nuisance_type,
                    is_flood=True,
                )
                alarms.append(replayed_alarm)

                anom_id = f"GT-ANOM-{counter:05d}"
                counter += 1
                ground_truth.append(
                    GroundTruthAnomaly(
                        anomaly_id=anom_id,
                        entity_type="AlarmEvent",
                        entity_id=dup_alarm_id,
                        issue_type="ALARM_FLOOD_REPLAY_DUPLICATE",
                        description=(
                            f"Alarm flood event {dup_alarm_id} is an exact replayed duplicate "
                            f"of telemetry packet {src.alarm_event_id} from machine {src.machine_id}."
                        ),
                        detection_rule="Exact payload and frequency match within replay window",
                        expected_decision="DEDUPLICATE_REPLAY_TELEMETRY",
                        severity="MEDIUM",
                        injected_timestamp=replayed_alarm.timestamp,
                    )
                )

        alarms.sort(key=lambda x: x.timestamp)
        return counter

    def _inject_unverified_actions(
        self,
        actions: List[CorrectiveAction],
        ground_truth: List[GroundTruthAnomaly],
        counter: int,
    ) -> int:
        target_count = min(self.profile.num_unverified_actions, len(actions))
        sampled_indices = self.rng.sample(range(len(actions)), target_count)

        for idx in sampled_indices:
            act = actions[idx]
            # Compliance violation: action status closed without QA signoff
            act.status = "CLOSED"
            act.verified_by = None
            act.verification_date = None
            act.description = f"{act.description} [UNVERIFIED: Closed by maintenance bypass]"

            anom_id = f"GT-ANOM-{counter:05d}"
            counter += 1
            ground_truth.append(
                GroundTruthAnomaly(
                    anomaly_id=anom_id,
                    entity_type="CorrectiveAction",
                    entity_id=act.action_id,
                    issue_type="ACTION_CLOSED_WITHOUT_VERIFICATION",
                    description=(
                        f"Corrective action {act.action_id} for incident {act.incident_id} "
                        f"marked CLOSED without mandatory verified_by and verification_date."
                    ),
                    detection_rule="CorrectiveAction.status == 'CLOSED' and (verified_by is NULL or verification_date is NULL)",
                    expected_decision="REOPEN_UNVERIFIED_ACTION",
                    severity="HIGH",
                    injected_timestamp=act.completed_date or "2026-10-15",
                )
            )

        return counter
