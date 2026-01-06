#!/usr/bin/env python
"""
Integration Test Runner Script.

Provides a convenient way to run integration tests with various options.

Usage:
    python scripts/run_integration_tests.py              # Run all integration tests
    python scripts/run_integration_tests.py --coverage   # Run with coverage report
    python scripts/run_integration_tests.py --verbose    # Verbose output
    python scripts/run_integration_tests.py --file NAME  # Run specific test file
"""

import sys
from pathlib import Path

# Add src to path for imports
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "src"))


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Run CasareRPA integration tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              Run all integration tests
  %(prog)s --coverage                   Run with HTML coverage report
  %(prog)s --file test_project_lifecycle Run specific test file
  %(prog)s --verbose                    Show detailed output
  %(prog)s --parallel                   Run tests in parallel
        """,
    )
    parser.add_argument(
        "--coverage",
        "-c",
        action="store_true",
        help="Generate coverage report (HTML)",
    )
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        metavar="NAME",
        help="Run specific test file (e.g., test_project_lifecycle)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output (-vv for extra verbose)",
    )
    parser.add_argument(
        "--parallel",
        "-p",
        action="store_true",
        help="Run tests in parallel (requires pytest-xdist)",
    )
    parser.add_argument(
        "--keep",
        "-k",
        action="store_true",
        help="Keep test artifacts (don't clean up on failure)",
    )

    args = parser.parse_args()

    # Build pytest arguments
    pytest_args = ["-m", "integration"]

    # Verbose flag
    if args.verbose:
        pytest_args.append("-vv" if args.verbose else "-v")
    else:
        pytest_args.append("-v")

    # Coverage
    if args.coverage:
        pytest_args.extend(
            [
                "--cov=src/casare_rpa",
                "--cov-report=html",
                "--cov-report=term-missing",
            ]
        )

    # Parallel execution
    if args.parallel:
        pytest_args.extend(["-n", "auto"])

    # Specific file
    if args.file:
        filename = args.file
        if not filename.startswith("test_"):
            filename = f"test_{filename}"
        if not filename.endswith(".py"):
            filename = f"{filename}.py"
        test_path = Path(__file__).parent.parent / "tests" / "integration" / filename
        if test_path.exists():
            pytest_args = [str(test_path), "-v"]
        else:
            print(f"Error: Test file not found: {test_path}")
            sys.exit(1)

    # Import and run pytest
    import pytest

    print(f"Running: pytest {' '.join(pytest_args)}")
    print()

    exit_code = pytest.main(pytest_args)

    if args.coverage and exit_code == 0:
        print("\nCoverage report: htmlcov/index.html")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
