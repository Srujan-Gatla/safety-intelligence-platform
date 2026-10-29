# Deterministic Seed Reproducibility Verification

## Protocol & Execution Parameters
- **Fixed Deterministic Random Seed:** `20261022`
- **Scale Profile:** `starter`
- **Test Runs:** 2 Independent Executions from clean state (`Run 1` vs `Run 2`)
- **Status:** **VERIFIED_100%_REPRODUCIBLE**

---

## 1. Row Count Comparison Across Runs

| Entity Table | Run 1 Row Count | Run 2 Row Count | Delta | Status |
| :--- | :--- | :--- | :--- | :--- |
| `plants` | 4 | 4 | 0 | **MATCH** |
| `machines` | 12 | 12 | 0 | **MATCH** |
| `safety_zones` | 16 | 16 | 0 | **MATCH** |
| `machine_safety_zones` | 15 | 15 | 0 | **MATCH** |
| `interlocks` | 36 | 36 | 0 | **MATCH** |
| `alarm_definitions` | 40 | 40 | 0 | **MATCH** |
| `operator_shifts` | 84 | 84 | 0 | **MATCH** |
| `machine_state_history` | 96 | 96 | 0 | **MATCH** |
| `alarm_events` | 2,050 | 2,050 | 0 | **MATCH** |
| `acknowledgements` | 1,728 | 1,728 | 0 | **MATCH** |
| `incidents` | 14 | 14 | 0 | **MATCH** |
| `corrective_actions` | 12 | 12 | 0 | **MATCH** |
| `ground_truth_anomalies` | 93 | 93 | 0 | **MATCH** |
| `ground_truth_recurrent` | 2 | 2 | 0 | **MATCH** |

---

## 2. Cryptographic SHA-256 Checksums

| File Relative Path | Run 1 SHA-256 Checksum | Run 2 SHA-256 Checksum | Match |
| :--- | :--- | :--- | :--- |
| `csv/acknowledgements.csv` | `587e1c1dc7a4e3a2...` | `587e1c1dc7a4e3a2...` | YES (Exact) |
| `csv/alarm_definitions.csv` | `4de335c6c8f9d87e...` | `4de335c6c8f9d87e...` | YES (Exact) |
| `csv/alarm_events.csv` | `276c868c1ac7b502...` | `276c868c1ac7b502...` | YES (Exact) |
| `csv/corrective_actions.csv` | `8f23b7ea67fab086...` | `8f23b7ea67fab086...` | YES (Exact) |
| `csv/incidents.csv` | `59194851a94c3449...` | `59194851a94c3449...` | YES (Exact) |
| `csv/interlocks.csv` | `eb82539968518fc6...` | `eb82539968518fc6...` | YES (Exact) |
| `csv/machine_safety_zones.csv` | `56ace12923c8992f...` | `56ace12923c8992f...` | YES (Exact) |
| `csv/machine_state_history.csv` | `5fef02e69991b14c...` | `5fef02e69991b14c...` | YES (Exact) |
| `csv/machines.csv` | `7df0477e2dc82466...` | `7df0477e2dc82466...` | YES (Exact) |
| `csv/operator_shifts.csv` | `d929c64942b4661f...` | `d929c64942b4661f...` | YES (Exact) |
| `csv/plants.csv` | `f252d86b42b3dbc9...` | `f252d86b42b3dbc9...` | YES (Exact) |
| `csv/safety_zones.csv` | `39de84f0c4796815...` | `39de84f0c4796815...` | YES (Exact) |
| `ground_truth/ground_truth_anomalies.csv` | `8356626976cd3658...` | `8356626976cd3658...` | YES (Exact) |
| `ground_truth/ground_truth_anomalies.json` | `9d1456ee6ec1a6f0...` | `9d1456ee6ec1a6f0...` | YES (Exact) |
| `ground_truth/ground_truth_recurrent.csv` | `1814f02ee1d85f75...` | `1814f02ee1d85f75...` | YES (Exact) |
| `ground_truth/ground_truth_recurrent.json` | `c618678957ecc8b3...` | `c618678957ecc8b3...` | YES (Exact) |
| `json/acknowledgements.json` | `d2b555d681750579...` | `d2b555d681750579...` | YES (Exact) |
| `json/alarm_definitions.json` | `7b12e0336afb8f2c...` | `7b12e0336afb8f2c...` | YES (Exact) |
| `json/alarm_events.json` | `3532acd1bb4ec0ca...` | `3532acd1bb4ec0ca...` | YES (Exact) |
| `json/corrective_actions.json` | `f8ce06b8e6c8c311...` | `f8ce06b8e6c8c311...` | YES (Exact) |
| `json/incidents.json` | `e54d1d544a40ff1c...` | `e54d1d544a40ff1c...` | YES (Exact) |
| `json/interlocks.json` | `bdee99c1156f13b0...` | `bdee99c1156f13b0...` | YES (Exact) |
| `json/machine_safety_zones.json` | `7c1b34a54e307ad1...` | `7c1b34a54e307ad1...` | YES (Exact) |
| `json/machine_state_history.json` | `d6eca32d0957122e...` | `d6eca32d0957122e...` | YES (Exact) |
| `json/machines.json` | `04297c9ea93c2c2f...` | `04297c9ea93c2c2f...` | YES (Exact) |
| `json/operator_shifts.json` | `3846fa65169fc5a9...` | `3846fa65169fc5a9...` | YES (Exact) |
| `json/plants.json` | `83c2042aaf64968c...` | `83c2042aaf64968c...` | YES (Exact) |
| `json/safety_zones.json` | `73d62f35d97e9bfe...` | `73d62f35d97e9bfe...` | YES (Exact) |

---

## Conclusion
The synthetic data generator produces byte-identical results when executed with the designated seed `20261022` across repeated cycles, satisfying all acceptance criteria for deterministic simulation.
