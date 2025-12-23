#!/usr/bin/env python3
"""
Verify that domain layer has NO imports from infrastructure or application.
Domain should only depend on itself.
"""

import os
import re
import sys
from pathlib import Path

FORBIDDEN_IMPORTS = [
    "casare_rpa.infrastructure",
    "casare_rpa.application",
    "casare_rpa.presentation",
]

# Files allowed to have some cross-layer imports (mostly for backward compatibility or visual node interaction)
EXCLUSIONS = [
    "port_type_system.py",
    "headless_validator.py",
    "workflow_validator.py",
]


def check_file(filepath: str) -> list[str]:
    """Check a Python file for forbidden imports"""
    if any(filepath.endswith(excl) for excl in EXCLUSIONS):
        return []

    errors = []
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()
        for i, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith("#"):
                continue
            # Check for actual imports, not just substring mentions
            if "from " in line or "import " in line:
                for forbidden in FORBIDDEN_IMPORTS:
                    if forbidden in line:
                        errors.append(
                            f"{filepath}:{i} - Forbidden import: {forbidden}\n  {line.strip()}"
                        )
                        break
    return errors


def main():
    base = Path(__file__).parent.parent
    domain_dir = base / "src" / "casare_rpa" / "domain"

    if not domain_dir.exists():
        return 0

    all_errors = []
    for root, _, files in os.walk(domain_dir):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                errors = check_file(filepath)
                all_errors.extend(errors)

    if all_errors:
        print(
            "[ERROR] Domain purity violations (domain/ should not import from infrastructure/application):"
        )
        for error in all_errors:
            print(f"   {error}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
