"""Generation engine orchestrating end-to-end deterministic data synthesis."""

import random
import time
from pathlib import Path
from typing import Any, Dict, Optional

from safety_intelligence.config import (
    DEFAULT_SEED,
    DATA_DIR,
    ScaleProfile,
    STARTER_PROFILE,
    FULL_PROFILE,
)
from safety_intelligence.generator.master_generator import MasterDataGenerator
from safety_intelligence.generator.event_generator import TransactionalEventGenerator
from safety_intelligence.generator.edge_case_injector import EdgeCaseInjector
from safety_intelligence.generator.export_manager import ExportManager


class GenerationEngine:
    """Main orchestrator for synthetic dataset generation with seed reproducibility."""

    def __init__(self, seed: int = DEFAULT_SEED, output_dir: Optional[Path] = None):
        self.seed = seed
        self.output_dir = output_dir

    def run(self, profile_name: str = "starter") -> Dict[str, Any]:
        start_time = time.time()
        rng = random.Random(self.seed)

        profile: ScaleProfile = (
            FULL_PROFILE if profile_name.lower() == "full" else STARTER_PROFILE
        )

        out_dir = self.output_dir or (DATA_DIR / profile.name)
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Master Data Generation
        master_gen = MasterDataGenerator(profile, rng)
        (
            plants,
            machines,
            zones,
            bridges,
            interlocks,
            alarm_defs,
        ) = master_gen.generate_all()

        # 2. Transactional Event Generation
        event_gen = TransactionalEventGenerator(
            profile, rng, plants, machines, zones, interlocks, alarm_defs
        )
        (
            shifts,
            state_history,
            alarms,
            acknowledgements,
            incidents,
            actions,
            recurrent_gt,
        ) = event_gen.generate_all()

        # 3. Inject Labeled Edge Cases
        edge_injector = EdgeCaseInjector(profile, rng)
        (
            acknowledgements,
            interlocks,
            incidents,
            alarms,
            actions,
            gt_anomalies,
        ) = edge_injector.inject_all(
            machines,
            interlocks,
            alarms,
            acknowledgements,
            incidents,
            actions,
            state_history,
        )

        # 4. Multi-format Export & Cryptographic Checksums
        export_mgr = ExportManager(out_dir)
        manifest = export_mgr.export_all(
            plants,
            machines,
            zones,
            bridges,
            interlocks,
            alarm_defs,
            shifts,
            state_history,
            alarms,
            acknowledgements,
            incidents,
            actions,
            gt_anomalies,
            recurrent_gt,
        )

        elapsed = round(time.time() - start_time, 2)

        return {
            "status": "SUCCESS",
            "seed": self.seed,
            "profile": profile.name,
            "elapsed_seconds": elapsed,
            "output_directory": str(out_dir),
            "manifest": manifest,
        }
