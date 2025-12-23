#!/usr/bin/env python3
"""
Block hardcoded hex colors in presentation layer.
Enforce use of Theme/THEME constants.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

# Pattern for hex colors
HEX_COLOR_PATTERN = r"['\"]#[0-9a-fA-F]{3,8}['\"]"


def _run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _changed_paths() -> list[str]:
    """Return staged paths, falling back to working tree diff."""
    output = _run_git(["diff", "--name-only", "--cached"])
    if not output:
        output = _run_git(["diff", "--name-only", "HEAD"])
    if not output:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def check_file(filepath: str) -> list[str]:
    """Check for hardcoded colors"""
    errors = []

    # Skip non-UI files
    if "test" in filepath or "__pycache__" in filepath:
        return errors

    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()
        for i, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith("#"):
                continue

            # Skip lines with THEME/Theme assignments or usage
            if "THEME" in line or "Theme" in line:
                continue

            matches = re.findall(HEX_COLOR_PATTERN, line)
            if matches:
                for match in matches:
                    errors.append(
                        f"{filepath}:{i} - Hardcoded color {match}. Use THEME constant instead.\n  {line.strip()}"
                    )

    return errors


def main() -> int:
    base = Path(__file__).parent.parent
    presentation_dir = base / "src" / "casare_rpa" / "presentation"

    if not presentation_dir.exists():
        return 0

    changed = _changed_paths()
    if not changed:
        return 0

    all_errors: list[str] = []
    for rel_path in changed:
        if not rel_path.endswith(".py"):
            continue

        abs_path = base / rel_path
        if not abs_path.exists():
            continue

        normalized = str(abs_path).replace("\\", "/")
        if "/src/casare_rpa/presentation/" not in normalized:
            continue

        all_errors.extend(check_file(str(abs_path)))

    if all_errors:
        print("[ERROR] Theme color violations (use THEME constants, no hardcoded #hex colors):")
        for error in all_errors[:10]:
            print(f"   {error}")
        if len(all_errors) > 10:
            print(f"   ... and {len(all_errors) - 10} more")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
