"""Deterministic generator for Master entities: Plant, Machine, SafetyZone, Interlock, AlarmDefinition."""

import random
from typing import List, Tuple
from datetime import datetime, timezone

from safety_intelligence.config import (
    ScaleProfile,
    MACHINE_TYPES,
    HAZARD_TYPES,
    INTERLOCK_TYPES,
    SEVERITIES,
    SLA_ACK_TARGETS,
)
from safety_intelligence.models.core import (
    Plant,
    Machine,
    SafetyZone,
    MachineSafetyZone,
    Interlock,
    AlarmDefinition,
)


class MasterDataGenerator:
    """Generates master data entities deterministically using a fixed random seed."""

    def __init__(self, profile: ScaleProfile, rng: random.Random):
        self.profile = profile
        self.rng = rng

    def generate_all(self) -> Tuple[
        List[Plant],
        List[Machine],
        List[SafetyZone],
        List[MachineSafetyZone],
        List[Interlock],
        List[AlarmDefinition],
    ]:
        plants = self.generate_plants()
        safety_zones = self.generate_safety_zones(plants)
        machines = self.generate_machines(plants)
        bridge_mappings = self.generate_machine_safety_zones(machines, safety_zones)
        interlocks = self.generate_interlocks(machines, safety_zones)
        alarm_definitions = self.generate_alarm_definitions()

        return plants, machines, safety_zones, bridge_mappings, interlocks, alarm_definitions

    def generate_plants(self) -> List[Plant]:
        plant_templates = [
            ("PLT-01", "Austin Advanced Gigafactory", "ATX", "Austin, USA", "America/Chicago", 12),
            ("PLT-02", "Detroit Precision Powertrain", "DET", "Detroit, USA", "America/Detroit", 10),
            ("PLT-03", "Stuttgart High-Tech Assembly", "STU", "Stuttgart, Germany", "Europe/Berlin", 14),
            ("PLT-04", "Yokohama Precision Robotics", "YOK", "Yokohama, Japan", "Asia/Tokyo", 8),
        ]
        plants: List[Plant] = []
        for i in range(self.profile.num_plants):
            template = plant_templates[i % len(plant_templates)]
            p_id = f"PLT-{i+1:02d}"
            plants.append(
                Plant(
                    plant_id=p_id,
                    name=template[1] if i < len(plant_templates) else f"Industrial Site {p_id}",
                    code=template[2] if i < len(plant_templates) else f"PL{i+1}",
                    location=template[3] if i < len(plant_templates) else "Global Site",
                    timezone=template[4] if i < len(plant_templates) else "UTC",
                    operational_status="ACTIVE",
                    total_lines=template[5] if i < len(plant_templates) else 8,
                    created_at="2026-01-01T00:00:00Z",
                )
            )
        return plants

    def generate_safety_zones(self, plants: List[Plant]) -> List[SafetyZone]:
        zones: List[SafetyZone] = []
        sil_levels = ["SIL_1", "SIL_2", "SIL_3", "SIL_4"]
        access_states = ["RESTRICTED", "CONTROLLED", "OPEN"]

        for plant in plants:
            plant_tag = plant.plant_id.replace("-", "")
            for z_idx in range(1, self.profile.num_zones_per_plant + 1):
                zone_id = f"SAFE-{plant_tag}-{z_idx:03d}"
                hazard = self.rng.choice(HAZARD_TYPES)
                sil = self.rng.choice(sil_levels)
                access = self.rng.choice(access_states)
                max_occ = 0 if hazard == "ROBOTIC_COLLISION" else self.rng.randint(1, 8)
                zones.append(
                    SafetyZone(
                        zone_id=zone_id,
                        plant_id=plant.plant_id,
                        name=f"{plant.code} Zone {z_idx:02d} ({hazard.replace('_', ' ').title()})",
                        hazard_classification=hazard,
                        required_sil_level=sil,
                        access_state=access,
                        max_occupancy=max_occ,
                        created_at="2026-01-15T00:00:00Z",
                    )
                )
        return zones

    def generate_machines(self, plants: List[Plant]) -> List[Machine]:
        machines: List[Machine] = []
        criticalities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        num_plants = len(plants)

        for m_idx in range(1, self.profile.num_machines + 1):
            machine_id = f"MCH-{m_idx:03d}"
            plant = plants[(m_idx - 1) % num_plants]
            m_type = MACHINE_TYPES[(m_idx - 1) % len(MACHINE_TYPES)]
            crit = criticalities[(m_idx - 1) % len(criticalities)]
            machines.append(
                Machine(
                    machine_id=machine_id,
                    plant_id=plant.plant_id,
                    name=f"{m_type.replace('_', ' ').title()} Unit {m_idx:03d}",
                    type=m_type,
                    criticality=crit,
                    installation_date="2024-06-15",
                    status="RUNNING",
                    firmware_version=f"v{(m_idx % 4) + 1}.{(m_idx % 9)}.{(m_idx % 5)}",
                )
            )
        return machines

    def generate_machine_safety_zones(
        self, machines: List[Machine], zones: List[SafetyZone]
    ) -> List[MachineSafetyZone]:
        bridges: List[MachineSafetyZone] = []
        zones_by_plant = {}
        for z in zones:
            zones_by_plant.setdefault(z.plant_id, []).append(z)

        mapping_counter = 1
        for m in machines:
            plant_zones = zones_by_plant.get(m.plant_id, [])
            if not plant_zones:
                continue
            # Primary containment zone
            primary_zone = plant_zones[mapping_counter % len(plant_zones)]
            plant_tag = m.plant_id.replace("-", "")
            mapping_id = f"MSZ-{plant_tag}-{mapping_counter:04d}"
            bridges.append(
                MachineSafetyZone(
                    mapping_id=mapping_id,
                    machine_id=m.machine_id,
                    zone_id=primary_zone.zone_id,
                    primary_containment=True,
                    effective_from="2026-01-15T00:00:00Z",
                    effective_to=None,
                    active_status=True,
                )
            )
            mapping_counter += 1

            # Secondary zone for 20% of machines (multi-zone boundary)
            if mapping_counter % 5 == 0 and len(plant_zones) > 1:
                secondary_zone = plant_zones[(mapping_counter + 1) % len(plant_zones)]
                mapping_id_sec = f"MSZ-{plant_tag}-{mapping_counter:04d}"
                bridges.append(
                    MachineSafetyZone(
                        mapping_id=mapping_id_sec,
                        machine_id=m.machine_id,
                        zone_id=secondary_zone.zone_id,
                        primary_containment=False,
                        effective_from="2026-01-15T00:00:00Z",
                        effective_to=None,
                        active_status=True,
                    )
                )
                mapping_counter += 1

        return bridges

    def generate_interlocks(
        self, machines: List[Machine], zones: List[SafetyZone]
    ) -> List[Interlock]:
        interlocks: List[Interlock] = []
        zones_by_plant = {}
        for z in zones:
            zones_by_plant.setdefault(z.plant_id, []).append(z)

        standards = ["ISO_13849_1_CAT4", "IEC_62061_SIL3", "ANSI_B11_19"]

        for m in machines:
            plant_zones = zones_by_plant.get(m.plant_id, [])
            assigned_zone = plant_zones[0] if plant_zones else None
            zone_id = assigned_zone.zone_id if assigned_zone else "SAFE-DEFAULT-001"

            for i_idx in range(1, self.profile.num_interlocks_per_machine + 1):
                interlock_id = f"ITL-{m.machine_id.replace('-', '')}-{i_idx:02d}"
                itype = INTERLOCK_TYPES[(i_idx - 1) % len(INTERLOCK_TYPES)]
                std = standards[(i_idx - 1) % len(standards)]
                # E-Stops never allow bypass; guard doors may allow bypass for maintenance
                bypass_allowed = itype in ["GUARD_DOOR", "ENCLOSURE_LATCH"]
                interlocks.append(
                    Interlock(
                        interlock_id=interlock_id,
                        machine_id=m.machine_id,
                        zone_id=zone_id,
                        name=f"{m.name} {itype.replace('_', ' ').title()} {i_idx:02d}",
                        interlock_type=itype,
                        safety_standard=std,
                        state="HEALTHY",
                        last_tested_date="2026-09-15",
                        bypass_allowed=bypass_allowed,
                    )
                )
        return interlocks

    def generate_alarm_definitions(self) -> List[AlarmDefinition]:
        definitions: List[AlarmDefinition] = []
        categories = ["SAFETY", "PROCESS", "MECHANICAL", "ELECTRICAL"]
        severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

        base_codes = [
            ("ALM_E_STOP_TRIP", "Emergency Stop Triggered", "SAFETY", "CRITICAL", False, True),
            ("ALM_GUARD_BREACH", "Safety Perimeter Guard Breached", "SAFETY", "CRITICAL", False, True),
            ("ALM_LIGHT_CURTAIN_TRIP", "Optical Light Curtain Interrupted", "SAFETY", "HIGH", False, True),
            ("ALM_INTERLOCK_FAULT", "Safety Interlock Circuit Discrepancy", "SAFETY", "CRITICAL", False, True),
            ("ALM_PRESSURE_MAT_VIOLATION", "Pressure Mat Zone Trespass", "SAFETY", "HIGH", False, True),
            ("ALM_THERMAL_OVERLIMIT", "Motor Stator Temperature High", "PROCESS", "HIGH", True, False),
            ("ALM_HYDRAULIC_PRESSURE_LOW", "Hydraulic Manifold Pressure Drop", "MECHANICAL", "MEDIUM", True, False),
            ("ALM_VIBRATION_EXCESS", "Spindle Vibration Amplitude Warning", "MECHANICAL", "MEDIUM", True, False),
            ("ALM_CURRENT_OVERLOAD", "Main Drive Overcurrent Inrush", "ELECTRICAL", "HIGH", True, False),
            ("ALM_LUBRICATION_FLOW_FAIL", "Linear Guide Lubrication Fault", "MECHANICAL", "LOW", True, False),
            ("ALM_PNEUMATIC_PRESSURE_DROP", "Main Air Header Pressure Bleed", "PROCESS", "LOW", True, False),
            ("ALM_CONVEYOR_JAM_DETECTED", "Transfer Infeed Jam Sensor Active", "PROCESS", "MEDIUM", True, False),
            ("ALM_SERVO_ENCODER_SYNC_LOST", "Axis Motion Synchronization Loss", "ELECTRICAL", "HIGH", False, True),
            ("ALM_COOLANT_FLOW_INTERRUPT", "Spindle Coolant Closed Loop Fault", "PROCESS", "LOW", True, False),
            ("ALM_HAZARD_ZONE_OVEROCCUPANCY", "Safety Zone Personnel Limit Exceeded", "SAFETY", "CRITICAL", False, True),
        ]

        for def_idx in range(1, self.profile.num_alarm_defs + 1):
            def_id = f"DEF-{def_idx:03d}"
            base = base_codes[(def_idx - 1) % len(base_codes)]
            cat = base[2] if def_idx <= len(base_codes) else categories[def_idx % len(categories)]
            sev = base[3] if def_idx <= len(base_codes) else severities[def_idx % len(severities)]
            code = f"{base[0]}_{def_idx:03d}" if def_idx > len(base_codes) else base[0]
            name = f"{base[1]} (Variant {def_idx:03d})" if def_idx > len(base_codes) else base[1]
            sla = SLA_ACK_TARGETS.get(sev, 900)
            auto_resettable = base[4]
            requires_investigation = base[5] or sev == "CRITICAL"

            definitions.append(
                AlarmDefinition(
                    alarm_def_id=def_id,
                    code=code,
                    name=name,
                    category=cat,
                    default_severity=sev,
                    sla_ack_seconds=sla,
                    auto_resettable=auto_resettable,
                    requires_investigation=requires_investigation,
                    description=f"Standard procedure for {name}. Follow Lockout/Tagout protocol if safety critical.",
                )
            )
        return definitions
