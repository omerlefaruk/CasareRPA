#!/usr/bin/env python3
"""
Measure and track KPI baselines for the CasareRPA refactor program.

This script captures baseline metrics before major refactoring work begins,
allowing us to track deltas and prevent regressions.

KPIs measured:
- Desktop startup time
- Dashboard bundle size
- Python test runtime
- Lint/type issue counts
- Boundary violations
- Code coverage (optional, requires pytest-cov)

Output format: JSON for easy parsing and diff tracking.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class KPIBaselines:
    """KPI baseline measurements."""

    # Timestamp
    timestamp: str
    git_commit: str
    git_branch: str

    # Performance metrics
    desktop_startup_ms: Optional[int] = None
    dashboard_bundle_bytes: Optional[int] = None
    dashboard_gzip_bytes: Optional[int] = None

    # Quality metrics
    test_runtime_seconds: Optional[float] = None
    test_count: Optional[int] = None
    test_passed: Optional[int] = None
    test_failed: Optional[int] = None

    # Lint/type metrics
    ruff_errors: Optional[int] = None
    ruff_warnings: Optional[int] = None
    mypy_errors: Optional[int] = None

    # Boundary violations
    domain_purity_violations: Optional[int] = None
    application_purity_violations: Optional[int] = None
    presentation_direction_violations: Optional[int] = None

    # Code metrics
    python_file_count: Optional[int] = None
    python_line_count: Optional[int] = None


def get_git_info() -> tuple[str, str]:
    """Get current git commit hash and branch."""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).parent.parent,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        commit = "unknown"

    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=Path(__file__).parent.parent,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        branch = "unknown"

    return commit, branch


def count_python_files(base_path: Path) -> tuple[int, int]:
    """Count Python files and lines of code."""
    file_count = 0
    line_count = 0

    for root, _, files in os.walk(base_path / "src" / "casare_rpa"):
        for file in files:
            if file.endswith(".py"):
                file_count += 1
                filepath = os.path.join(root, file)
                with open(filepath, encoding="utf-8", errors="ignore") as f:
                    line_count += sum(1 for _ in f)

    return file_count, line_count


def run_check_script(script_name: str) -> int:
    """Run a check script and return the number of violations (exit code)."""
    script_path = Path(__file__).parent / script_name
    if not script_path.exists():
        return -1  # Script doesn't exist

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
        )
        # Count errors in output
        error_count = result.stdout.count("[ERROR]")
        return error_count
    except Exception:
        return -1


def measure_dashboard_bundle(base_path: Path) -> tuple[Optional[int], Optional[int]]:
    """Measure dashboard bundle size (requires npm run build)."""
    dist_dir = base_path / "monitoring-dashboard" / "dist"

    if not dist_dir.exists():
        return None, None

    total_bytes = 0
    gzip_bytes = 0

    for asset in dist_dir.rglob("*"):
        if asset.is_file():
            total_bytes += asset.stat().st_size

    # Try to find .gz files if they exist
    for gz_file in dist_dir.rglob("*.gz"):
        gzip_bytes += gz_file.stat().st_size

    # Estimate gzip if not pre-compressed
    if gzip_bytes == 0 and total_bytes > 0:
        gzip_bytes = int(total_bytes * 0.3)  # Rough estimate

    return total_bytes, gzip_bytes


def measure_tests(base_path: Path) -> tuple[Optional[float], Optional[int], Optional[int], Optional[int]]:
    """Run unit tests and measure runtime/results."""
    try:
        start = time.time()
        result = subprocess.run(
            [
                sys.executable, "-m", "pytest",
                "-m", "unit",
                "--tb=no",
                "-q",
                "tests/"
            ],
            cwd=base_path,
            capture_output=True,
            text=True,
        )
        runtime = time.time() - start

        # Parse output for counts
        output = result.stdout + result.stderr
        passed = output.count("PASSED")
        failed = output.count("FAILED")

        # Estimate total test count from summary line if available
        total = None
        for line in output.split("\n"):
            if "==" in line and "s" in line:
                parts = line.split()
                for part in parts:
                    if "collected" in part:
                        try:
                            total = int(part.split()[0])
                        except (ValueError, IndexError):
                            pass

        return runtime, total, passed, failed
    except Exception:
        return None, None, None, None


def measure_lint(base_path: Path) -> tuple[Optional[int], Optional[int]]:
    """Run ruff lint and count errors/warnings."""
    try:
        result = subprocess.run(
            ["ruff", "check", "src/", "tests/"],
            cwd=base_path,
            capture_output=True,
            text=True,
        )
        # Count issues
        output = result.stdout + result.stderr
        return output.count("\n"), 0  # Rough line count
    except Exception:
        return None, None


def measure_mypy(base_path: Path) -> Optional[int]:
    """Run mypy and count errors."""
    try:
        result = subprocess.run(
            ["mypy", "src/casare_rpa/domain"],
            cwd=base_path,
            capture_output=True,
            text=True,
        )
        # Count errors
        output = result.stdout + result.stderr
        return output.count("error:")
    except Exception:
        return None


def measure_startup(base_path: Path) -> Optional[int]:
    """
    Measure desktop startup time.
    Note: This requires Xvfb or similar on CI, and may not work on all platforms.
    Returns None if measurement fails.
    """
    # This is platform-dependent and may require display setup
    # Skip for now and return None
    return None


def main():
    parser = argparse.ArgumentParser(description="Measure KPI baselines")
    parser.add_argument("--output", "-o", help="Output JSON file")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON")
    args = parser.parse_args()

    base_path = Path(__file__).parent.parent

    print(f"Measuring KPI baselines for CasareRPA...")

    # Get git info
    commit, branch = get_git_info()
    print(f"  Git: {commit[:8]} ({branch})")

    # Measure metrics
    print("  Counting Python files...")
    file_count, line_count = count_python_files(base_path)
    print(f"    {file_count} files, {line_count:,} lines")

    print("  Checking boundary violations...")
    domain_violations = run_check_script("check_domain_purity.py")
    app_violations = run_check_script("check_application_purity.py")
    pres_violations = run_check_script("check_presentation_dependency_direction.py")
    print(f"    Domain: {domain_violations}, App: {app_violations}, Pres: {pres_violations}")

    print("  Running lint checks...")
    ruff_err, _ = measure_lint(base_path)
    mypy_err = measure_mypy(base_path)
    print(f"    Ruff: ~{ruff_err} issues, Mypy: {mypy_err} errors")

    print("  Measuring dashboard bundle...")
    bundle_bytes, gzip_bytes = measure_dashboard_bundle(base_path)
    if bundle_bytes:
        print(f"    Bundle: {bundle_bytes:,} bytes (gz: ~{gzip_bytes:,})")
    else:
        print("    Bundle: not built (run npm run build in monitoring-dashboard/)")
        bundle_bytes, gzip_bytes = None, None

    # Tests are slow, skip by default
    # print("  Running tests...")
    # test_time, test_total, test_passed, test_failed = measure_tests(base_path)

    # Build baseline data
    baselines = KPIBaselines(
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        git_commit=commit,
        git_branch=branch,
        desktop_startup_ms=None,  # Requires display
        dashboard_bundle_bytes=bundle_bytes,
        dashboard_gzip_bytes=gzip_bytes,
        test_runtime_seconds=None,
        test_count=None,
        test_passed=None,
        test_failed=None,
        ruff_errors=ruff_err,
        ruff_warnings=None,
        mypy_errors=mypy_err,
        domain_purity_violations=domain_violations,
        application_purity_violations=app_violations,
        presentation_direction_violations=pres_violations,
        python_file_count=file_count,
        python_line_count=line_count,
    )

    # Output
    if args.pretty:
        print("\n" + "=" * 50)
        print(json.dumps(asdict(baselines), indent=2))
        print("=" * 50)
    else:
        print("\nKPI Baseline Summary:")
        print(f"  Python files: {file_count:,}")
        print(f"  Python lines: {line_count:,}")
        print(f"  Boundary violations: {domain_violations + app_violations + pres_violations}")
        print(f"  Lint issues: ~{ruff_err}")
        print(f"  Type errors: {mypy_err}")
        if bundle_bytes:
            print(f"  Dashboard bundle: {bundle_bytes:,} bytes")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(asdict(baselines), f, indent=2)
        print(f"\nSaved baselines to {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
