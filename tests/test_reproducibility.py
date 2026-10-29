"""Unit test for Step 10: Fixed-seed deterministic reproducibility."""

import shutil
from pathlib import Path
from safety_intelligence.config import DEFAULT_SEED, DATA_DIR
from safety_intelligence.generator.engine import GenerationEngine


def test_seed_reproducibility():
    run1_dir = DATA_DIR / "_test_run1"
    run2_dir = DATA_DIR / "_test_run2"

    try:
        eng1 = GenerationEngine(seed=DEFAULT_SEED, output_dir=run1_dir)
        res1 = eng1.run("starter")

        eng2 = GenerationEngine(seed=DEFAULT_SEED, output_dir=run2_dir)
        res2 = eng2.run("starter")

        m1 = res1["manifest"]
        m2 = res2["manifest"]

        # Exact row counts match
        assert m1["row_counts"] == m2["row_counts"]

        # Exact SHA-256 cryptographic hashes match
        assert m1["sha256_checksums"] == m2["sha256_checksums"]

    finally:
        shutil.rmtree(run1_dir, ignore_errors=True)
        shutil.rmtree(run2_dir, ignore_errors=True)
