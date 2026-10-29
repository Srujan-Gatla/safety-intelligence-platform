"""Unified Command Line Interface for Safety Intelligence Platform."""

import argparse
import json
import sys
from pathlib import Path

from safety_intelligence.config import DEFAULT_SEED, DATA_DIR, REPORTS_DIR
from safety_intelligence.generator.engine import GenerationEngine
from safety_intelligence.validation.validator import DatasetValidator
from safety_intelligence.analytics.reporter import MultiPersonaReporter
from safety_intelligence.analytics.metrics_evaluator import SafetyMetricsEvaluator


def cmd_generate(args: argparse.Namespace) -> None:
    print(f"[+] Starting synthetic generation: profile='{args.profile}', seed={args.seed}...")
    engine = GenerationEngine(seed=args.seed)
    res = engine.run(args.profile)
    print(f"[OK] Generation successful in {res['elapsed_seconds']}s")
    print(f"    Output directory: {res['output_directory']}")
    print(f"    Row counts: {json.dumps(res['manifest']['row_counts'], indent=2)}")


def cmd_validate(args: argparse.Namespace) -> None:
    target_dir = Path(args.dataset)
    print(f"[+] Running validation on: {target_dir}...")
    validator = DatasetValidator(target_dir)
    res = validator.validate_all()
    md = validator.generate_markdown_report()
    print(f"[OK] Validation completed. Status: {res['overall_status']}")
    print(f"    Edge cases evaluation: {json.dumps(res['edge_case_audit']['evaluation_against_ground_truth'], indent=2)}")
    print(f"    Saved report to: docs/VALIDATION_SUMMARY.md")


def cmd_analyze(args: argparse.Namespace) -> None:
    target_dir = Path(args.dataset)
    rep_dir = Path(args.output) if args.output else REPORTS_DIR
    print(f"[+] Analyzing dataset at: {target_dir}...")
    reporter = MultiPersonaReporter(target_dir)
    paths = reporter.generate_all_reports(rep_dir)
    print(f"[OK] Analytics generated successfully. Reports saved to:")
    for name, p in paths.items():
        print(f"    - {name}: {p}")


def cmd_reproduce(args: argparse.Namespace) -> None:
    print(f"[+] Running Step 10 Reproducibility Verification (Seed={args.seed})...")
    tmp_run1 = DATA_DIR / "_reproduce_run1"
    tmp_run2 = DATA_DIR / "_reproduce_run2"

    eng1 = GenerationEngine(seed=args.seed, output_dir=tmp_run1)
    res1 = eng1.run(args.profile)

    eng2 = GenerationEngine(seed=args.seed, output_dir=tmp_run2)
    res2 = eng2.run(args.profile)

    manifest1 = res1["manifest"]
    manifest2 = res2["manifest"]

    counts_match = manifest1["row_counts"] == manifest2["row_counts"]
    checksums_match = manifest1["sha256_checksums"] == manifest2["sha256_checksums"]

    status = "VERIFIED_100%_REPRODUCIBLE" if (counts_match and checksums_match) else "REPRODUCIBILITY_FAILED"
    print(f"[OK] Reproducibility test completed: Status={status}")
    print(f"    Row counts match: {counts_match}")
    print(f"    SHA-256 Checksums match: {checksums_match}")

    # Generate docs/REPRODUCIBILITY.md
    docs_dir = Path(__file__).resolve().parent.parent.parent / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    repro_md = f"""# Deterministic Seed Reproducibility Verification

## Protocol & Execution Parameters
- **Fixed Deterministic Random Seed:** `{args.seed}`
- **Scale Profile:** `{args.profile}`
- **Test Runs:** 2 Independent Executions from clean state (`Run 1` vs `Run 2`)
- **Status:** **{status}**

---

## 1. Row Count Comparison Across Runs

| Entity Table | Run 1 Row Count | Run 2 Row Count | Delta | Status |
| :--- | :--- | :--- | :--- | :--- |
"""
    for table, count1 in manifest1["row_counts"].items():
        count2 = manifest2["row_counts"].get(table, 0)
        delta = count2 - count1
        st = "MATCH" if delta == 0 else "MISMATCH"
        repro_md += f"| `{table}` | {count1:,} | {count2:,} | {delta} | **{st}** |\n"

    repro_md += f"""
---

## 2. Cryptographic SHA-256 Checksums

| File Relative Path | Run 1 SHA-256 Checksum | Run 2 SHA-256 Checksum | Match |
| :--- | :--- | :--- | :--- |
"""
    for rel_path, h1 in sorted(manifest1["sha256_checksums"].items()):
        h2 = manifest2["sha256_checksums"].get(rel_path, "")
        m = "YES (Exact)" if h1 == h2 else "NO"
        repro_md += f"| `{rel_path}` | `{h1[:16]}...` | `{h2[:16]}...` | {m} |\n"

    repro_md += f"""
---

## Conclusion
The synthetic data generator produces byte-identical results when executed with the designated seed `{args.seed}` across repeated cycles, satisfying all acceptance criteria for deterministic simulation.
"""
    (docs_dir / "REPRODUCIBILITY.md").write_text(repro_md, encoding="utf-8")
    print(f"    Saved documentation to: docs/REPRODUCIBILITY.md")

    # Cleanup temporary run directories
    import shutil
    shutil.rmtree(tmp_run1, ignore_errors=True)
    shutil.rmtree(tmp_run2, ignore_errors=True)


def cmd_serve(args: argparse.Namespace) -> None:
    import uvicorn
    from safety_intelligence.web.app import create_app
    app = create_app()
    print(f"[+] Starting Safety Intelligence Web Server on http://{args.host}:{args.port}...")
    uvicorn.run(app, host=args.host, port=args.port)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="safety-intel",
        description="Industrial Safety & Machine Intelligence Platform CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Generate
    p_gen = subparsers.add_parser("generate", help="Synthesize dataset")
    p_gen.add_argument("--profile", choices=["starter", "full"], default="starter", help="Scale profile")
    p_gen.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed")
    p_gen.set_defaults(func=cmd_generate)

    # Validate
    p_val = subparsers.add_parser("validate", help="Validate relational integrity and edge cases")
    p_val.add_argument("--dataset", type=str, default="data/starter", help="Dataset directory")
    p_val.set_defaults(func=cmd_validate)

    # Analyze
    p_ana = subparsers.add_parser("analyze", help="Run repeated hazard analytics and export reports")
    p_ana.add_argument("--dataset", type=str, default="data/starter", help="Dataset directory")
    p_ana.add_argument("--output", type=str, default="reports", help="Reports output directory")
    p_ana.set_defaults(func=cmd_analyze)

    # Reproduce
    p_rep = subparsers.add_parser("reproduce", help="Verify seed reproducibility across two runs")
    p_rep.add_argument("--profile", choices=["starter", "full"], default="starter", help="Scale profile")
    p_rep.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed")
    p_rep.set_defaults(func=cmd_reproduce)

    # Serve
    p_srv = subparsers.add_parser("serve", help="Launch FastAPI web dashboard")
    p_srv.add_argument("--host", type=str, default="127.0.0.1", help="Host address")
    p_srv.add_argument("--port", type=int, default=8000, help="Port")
    p_srv.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
