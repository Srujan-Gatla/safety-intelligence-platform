"""Export manager for generating CSV, JSON, SQL DDL/seeds, and SQLite databases."""

import csv
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from safety_intelligence.models.core import (
    Plant,
    Machine,
    SafetyZone,
    MachineSafetyZone,
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
from safety_intelligence.models.ground_truth import (
    GroundTruthAnomaly,
    GroundTruthRecurrentHazard,
)


class ExportManager:
    """Handles multi-format persistence and cryptographic checksumming."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.csv_dir = output_dir / "csv"
        self.json_dir = output_dir / "json"
        self.sql_dir = output_dir / "sql"
        self.gt_dir = output_dir / "ground_truth"

        for d in [self.csv_dir, self.json_dir, self.sql_dir, self.gt_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def export_all(
        self,
        plants: List[Plant],
        machines: List[Machine],
        zones: List[SafetyZone],
        bridges: List[MachineSafetyZone],
        interlocks: List[Interlock],
        alarm_defs: List[AlarmDefinition],
        shifts: List[OperatorShift],
        states: List[MachineStateHistory],
        alarms: List[AlarmEvent],
        acknowledgements: List[Acknowledgement],
        incidents: List[Incident],
        actions: List[CorrectiveAction],
        gt_anomalies: List[GroundTruthAnomaly],
        gt_recurrent: List[GroundTruthRecurrentHazard],
    ) -> Dict[str, Any]:
        tables = {
            "plants": [p.model_dump() for p in plants],
            "machines": [m.model_dump() for m in machines],
            "safety_zones": [z.model_dump() for z in zones],
            "machine_safety_zones": [b.model_dump() for b in bridges],
            "interlocks": [i.model_dump() for i in interlocks],
            "alarm_definitions": [d.model_dump() for d in alarm_defs],
            "operator_shifts": [s.model_dump() for s in shifts],
            "machine_state_history": [st.model_dump() for st in states],
            "alarm_events": [a.model_dump() for a in alarms],
            "acknowledgements": [ack.model_dump() for ack in acknowledgements],
            "incidents": [inc.model_dump() for inc in incidents],
            "corrective_actions": [act.model_dump() for act in actions],
        }

        gt_tables = {
            "ground_truth_anomalies": [g.model_dump() for g in gt_anomalies],
            "ground_truth_recurrent": [r.model_dump() for r in gt_recurrent],
        }

        # 1. Export CSV
        for name, records in {**tables, **gt_tables}.items():
            target_dir = self.gt_dir if name.startswith("ground_truth") else self.csv_dir
            self._export_csv(target_dir / f"{name}.csv", records)

        # 2. Export JSON
        for name, records in {**tables, **gt_tables}.items():
            target_dir = self.gt_dir if name.startswith("ground_truth") else self.json_dir
            self._export_json(target_dir / f"{name}.json", records)

        # 3. Export SQL Schema & Seeds + SQLite Database
        db_path = self.output_dir / "safety_platform.db"
        self._export_sqlite_and_sql(tables, db_path)

        # 4. Generate Checksums and Manifest
        checksums = self.compute_checksums()
        row_counts = {name: len(records) for name, records in {**tables, **gt_tables}.items()}

        manifest = {
            "row_counts": row_counts,
            "sha256_checksums": checksums,
            "sqlite_db": str(db_path),
        }

        with open(self.output_dir / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return manifest

    def _export_csv(self, file_path: Path, records: List[Dict[str, Any]]) -> None:
        if not records:
            file_path.write_text("", encoding="utf-8")
            return
        fieldnames = list(records[0].keys())
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

    def _export_json(self, file_path: Path, records: List[Dict[str, Any]]) -> None:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)

    def _export_sqlite_and_sql(self, tables: Dict[str, List[Dict[str, Any]]], db_path: Path) -> None:
        if db_path.exists():
            db_path.unlink()

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        ddl = """
        CREATE TABLE plants (
            plant_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            code TEXT NOT NULL UNIQUE,
            location TEXT NOT NULL,
            timezone TEXT NOT NULL,
            operational_status TEXT NOT NULL,
            total_lines INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE machines (
            machine_id TEXT PRIMARY KEY,
            plant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            criticality TEXT NOT NULL,
            installation_date TEXT NOT NULL,
            status TEXT NOT NULL,
            firmware_version TEXT NOT NULL,
            FOREIGN KEY (plant_id) REFERENCES plants (plant_id)
        );

        CREATE TABLE safety_zones (
            zone_id TEXT PRIMARY KEY,
            plant_id TEXT NOT NULL,
            name TEXT NOT NULL,
            hazard_classification TEXT NOT NULL,
            required_sil_level TEXT NOT NULL,
            access_state TEXT NOT NULL,
            max_occupancy INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (plant_id) REFERENCES plants (plant_id)
        );

        CREATE TABLE machine_safety_zones (
            mapping_id TEXT PRIMARY KEY,
            machine_id TEXT NOT NULL,
            zone_id TEXT NOT NULL,
            primary_containment INTEGER NOT NULL,
            effective_from TEXT NOT NULL,
            effective_to TEXT,
            active_status INTEGER NOT NULL,
            FOREIGN KEY (machine_id) REFERENCES machines (machine_id),
            FOREIGN KEY (zone_id) REFERENCES safety_zones (zone_id)
        );

        CREATE TABLE interlocks (
            interlock_id TEXT PRIMARY KEY,
            machine_id TEXT NOT NULL,
            zone_id TEXT NOT NULL,
            name TEXT NOT NULL,
            interlock_type TEXT NOT NULL,
            safety_standard TEXT NOT NULL,
            state TEXT NOT NULL,
            last_tested_date TEXT NOT NULL,
            bypass_allowed INTEGER NOT NULL,
            FOREIGN KEY (machine_id) REFERENCES machines (machine_id),
            FOREIGN KEY (zone_id) REFERENCES safety_zones (zone_id)
        );

        CREATE TABLE alarm_definitions (
            alarm_def_id TEXT PRIMARY KEY,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            default_severity TEXT NOT NULL,
            sla_ack_seconds INTEGER NOT NULL,
            auto_resettable INTEGER NOT NULL,
            requires_investigation INTEGER NOT NULL,
            description TEXT NOT NULL
        );

        CREATE TABLE operator_shifts (
            shift_id TEXT PRIMARY KEY,
            plant_id TEXT NOT NULL,
            operator_id TEXT NOT NULL,
            operator_name TEXT NOT NULL,
            shift_type TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            supervisor_name TEXT NOT NULL,
            turnover_notes TEXT,
            FOREIGN KEY (plant_id) REFERENCES plants (plant_id)
        );

        CREATE TABLE machine_state_history (
            state_event_id TEXT PRIMARY KEY,
            machine_id TEXT NOT NULL,
            shift_id TEXT NOT NULL,
            previous_state TEXT NOT NULL,
            new_state TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            transition_reason TEXT NOT NULL,
            interlock_trip_id TEXT,
            FOREIGN KEY (machine_id) REFERENCES machines (machine_id),
            FOREIGN KEY (shift_id) REFERENCES operator_shifts (shift_id)
        );

        CREATE TABLE alarm_events (
            alarm_event_id TEXT PRIMARY KEY,
            machine_id TEXT NOT NULL,
            alarm_def_id TEXT NOT NULL,
            zone_id TEXT,
            shift_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            cleared_timestamp TEXT,
            duration_seconds REAL,
            severity TEXT NOT NULL,
            trigger_value REAL NOT NULL,
            threshold_value REAL NOT NULL,
            lifecycle_state TEXT NOT NULL,
            is_nuisance INTEGER NOT NULL,
            nuisance_type TEXT NOT NULL,
            is_flood INTEGER NOT NULL,
            FOREIGN KEY (machine_id) REFERENCES machines (machine_id),
            FOREIGN KEY (alarm_def_id) REFERENCES alarm_definitions (alarm_def_id),
            FOREIGN KEY (zone_id) REFERENCES safety_zones (zone_id),
            FOREIGN KEY (shift_id) REFERENCES operator_shifts (shift_id)
        );

        CREATE TABLE acknowledgements (
            ack_id TEXT PRIMARY KEY,
            alarm_event_id TEXT NOT NULL,
            shift_id TEXT NOT NULL,
            operator_id TEXT NOT NULL,
            ack_timestamp TEXT NOT NULL,
            latency_seconds REAL NOT NULL,
            sla_breached INTEGER NOT NULL,
            ack_method TEXT NOT NULL,
            comment TEXT,
            FOREIGN KEY (alarm_event_id) REFERENCES alarm_events (alarm_event_id),
            FOREIGN KEY (shift_id) REFERENCES operator_shifts (shift_id)
        );

        CREATE TABLE incidents (
            incident_id TEXT PRIMARY KEY,
            plant_id TEXT NOT NULL,
            machine_id TEXT NOT NULL,
            zone_id TEXT NOT NULL,
            triggering_alarm_id TEXT,
            shift_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            severity TEXT NOT NULL,
            incident_type TEXT NOT NULL,
            description TEXT NOT NULL,
            osha_reportable INTEGER NOT NULL,
            lost_work_hours REAL NOT NULL,
            machine_state_at_incident TEXT NOT NULL,
            lifecycle_status TEXT NOT NULL,
            FOREIGN KEY (plant_id) REFERENCES plants (plant_id),
            FOREIGN KEY (machine_id) REFERENCES machines (machine_id),
            FOREIGN KEY (zone_id) REFERENCES safety_zones (zone_id),
            FOREIGN KEY (triggering_alarm_id) REFERENCES alarm_events (alarm_event_id),
            FOREIGN KEY (shift_id) REFERENCES operator_shifts (shift_id)
        );

        CREATE TABLE corrective_actions (
            action_id TEXT PRIMARY KEY,
            incident_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            description TEXT NOT NULL,
            assigned_to TEXT NOT NULL,
            due_date TEXT NOT NULL,
            completed_date TEXT,
            verified_by TEXT,
            verification_date TEXT,
            status TEXT NOT NULL,
            effectiveness_score REAL,
            recurrence_prevention_notes TEXT,
            FOREIGN KEY (incident_id) REFERENCES incidents (incident_id)
        );
        """

        cursor.executescript(ddl)

        # Write schema.sql
        (self.sql_dir / "schema.sql").write_text(ddl, encoding="utf-8")

        # Insert data
        seed_lines = []
        for table_name, rows in tables.items():
            if not rows:
                continue
            cols = list(rows[0].keys())
            placeholders = ",".join(["?"] * len(cols))
            col_names = ",".join(cols)
            sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"

            data_tuples = []
            for r in rows:
                row_vals = []
                for c in cols:
                    v = r[c]
                    if isinstance(v, bool):
                        row_vals.append(1 if v else 0)
                    else:
                        row_vals.append(v)
                data_tuples.append(tuple(row_vals))

            cursor.executemany(sql, data_tuples)

        conn.commit()
        conn.close()

    def compute_checksums(self) -> Dict[str, str]:
        checksums = {}
        for ext in ["*.csv", "*.json"]:
            for f in sorted(self.output_dir.rglob(ext)):
                if f.name == "manifest.json":
                    continue
                h = hashlib.sha256()
                with open(f, "rb") as fh:
                    while chunk := fh.read(65536):
                        h.update(chunk)
                rel_path = str(f.relative_to(self.output_dir)).replace("\\", "/")
                checksums[rel_path] = h.hexdigest()
        return checksums
