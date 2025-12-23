#!/usr/bin/env python3
"""
Enforce logging standards:
- No print() in infrastructure/ and nodes/
- Use loguru logger instead
- OK in: presentation (UI), tests, scripts
"""

import os
import re
import sys
from pathlib import Path


def check_file(filepath: str) -> list[str]:
    """Check for print() usage in restricted areas"""
    errors = []

    # Only check infrastructure and nodes
    if not ("infrastructure" in filepath or "nodes/" in filepath):
        return errors

    # Skip test files
    if "test" in filepath:
        return errors

    with open(filepath) as f:
        lines = f.readlines()
        for i, line in enumerate(lines, 1):
            # Look for print() calls
            if re.search(r"\bprint\s*\(", line) and not line.strip().startswith("#"):
                # Make sure it's not in a string or comment
                if "print" in line and "logger" not in line:
                    errors.append(
                        f"{filepath}:{i} - Use logger instead of print()\n  {line.strip()}"
                    )

    return errors


def main():
    base = Path(__file__).parent.parent
    src_dir = base / "src" / "casare_rpa"

    if not src_dir.exists():
        return 0

    all_errors = []
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                errors = check_file(filepath)
                all_errors.extend(errors)

    if all_errors:
        print("[ERROR] Logger usage violations (use loguru logger, not print()):")
        for error in all_errors[:10]:
            print(f"   {error}")
        if len(all_errors) > 10:
            print(f"   ... and {len(all_errors) - 10} more")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
