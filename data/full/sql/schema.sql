
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
        