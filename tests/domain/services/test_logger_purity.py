"""Test that domain layer has no external imports.

This test validates the DDD principle that the domain layer must remain
pure and free from infrastructure dependencies.
"""

import subprocess


def test_domain_no_loguru_imports():
    """Domain layer must not import loguru directly."""
    result = subprocess.run(
        ["rg", "--glob=*.py", "from loguru import|import loguru", "src/casare_rpa/domain/"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, (
        f"Found loguru imports in domain layer:\n{result.stdout}\n"
        "Domain layer must use LoggerService from domain.interfaces.logger"
    )


def test_domain_no_infrastructure_imports():
    """Domain layer must not import from infrastructure."""
    result = subprocess.run(
        ["rg", "--glob=*.py", "from casare_rpa.infrastructure", "src/casare_rpa/domain/"],
        capture_output=True,
        text=True,
    )
    assert result.returncode in (0, 1), f"rg failed:\n{result.stderr}"
    # Allow test imports but not production code
    violations = [
        line for line in result.stdout.splitlines() if line.strip() and "test" not in line.lower()
    ]
    assert not violations, (
        f"Found infrastructure imports in domain layer:\n{violations}\n"
        "Domain layer must depend only on stdlib and internal domain modules"
    )
