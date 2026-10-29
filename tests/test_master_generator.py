"""Unit tests for Master Data generation and ID nomenclature."""

import random
import re
import pytest
from safety_intelligence.config import STARTER_PROFILE, DEFAULT_SEED
from safety_intelligence.generator.master_generator import MasterDataGenerator


@pytest.fixture
def master_data():
    rng = random.Random(DEFAULT_SEED)
    gen = MasterDataGenerator(STARTER_PROFILE, rng)
    return gen.generate_all()


def test_plants_generation(master_data):
    plants = master_data[0]
    assert len(plants) == STARTER_PROFILE.num_plants
    for p in plants:
        assert re.match(r"^PLT-\d{2}$", p.plant_id)
        assert p.operational_status == "ACTIVE"
        assert p.total_lines >= 1


def test_machines_generation(master_data):
    machines = master_data[1]
    plants = master_data[0]
    plant_ids = {p.plant_id for p in plants}
    assert len(machines) == STARTER_PROFILE.num_machines
    for m in machines:
        assert re.match(r"^MCH-\d{3}$", m.machine_id)
        assert m.plant_id in plant_ids
        assert m.status == "RUNNING"
        assert m.criticality in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def test_safety_zones_nomenclature(master_data):
    zones = master_data[2]
    plants = master_data[0]
    plant_ids = {p.plant_id for p in plants}
    for z in zones:
        # Nomenclature convention: SAFE-<plant-id>-001
        assert re.match(r"^SAFE-[A-Z0-9]+-\d{3}$", z.zone_id)
        assert z.plant_id in plant_ids
        assert z.required_sil_level in ["SIL_1", "SIL_2", "SIL_3", "SIL_4"]


def test_interlocks_generation(master_data):
    interlocks = master_data[4]
    machines = master_data[1]
    m_ids = {m.machine_id for m in machines}
    for itl in interlocks:
        assert re.match(r"^ITL-[A-Z0-9]+-\d{2}$", itl.interlock_id)
        assert itl.machine_id in m_ids
        assert itl.state in ["HEALTHY", "TRIPPED", "BYPASSED", "FAULT"]


def test_alarm_definitions_catalog(master_data):
    defs = master_data[5]
    assert len(defs) == STARTER_PROFILE.num_alarm_defs
    for d in defs:
        assert re.match(r"^DEF-\d{3}$", d.alarm_def_id)
        assert d.sla_ack_seconds in [120, 300, 900, 3600]
