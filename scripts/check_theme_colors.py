#!/usr/bin/env python3
"""
Block hardcoded hex colors in presentation layer.
Enforce use of Theme/THEME constants.
"""

import re
import subprocess
import sys
from pathlib import Path

# Pattern for hex colors
HEX_COLOR_PATTERN = r"['\"]#[0-9a-fA-F]{3,8}['\"]"


def check_file(filepath: str) -> list[str]:
    """Check for hardcoded colors"""
    errors = []

    # Skip non-UI files and theme system (color definitions)
    if (
        "test" in filepath
        or "__pycache__" in filepath
        or "theme_system" in filepath
    ):
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

            # Skip lines with intentional color markers (data visualization, syntax highlighting)
            if (
                "theme-colors: allow" in line
                or "noqa:" in line
                or "syntax highlighting" in line.lower()
            ):
                continue

            matches = re.findall(HEX_COLOR_PATTERN, line)
            if matches:
                for match in matches:
                    errors.append(
                        f"{filepath}:{i} - Hardcoded color {match}. Use THEME constant instead.\n  {line.strip()}"
                    )

    return errors


def main():
    # Use git to find the actual repo root (works with worktrees)
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            base = Path(result.stdout.strip())
        else:
            base = Path(__file__).parent.parent
    except Exception:
        base = Path(__file__).parent.parent
    presentation_dir = base / "src" / "casare_rpa" / "presentation"

    if not presentation_dir.exists():
        return 0

    # Incremental enforcement: only check staged presentation files by default.
    # This prevents new hardcoded colors without blocking commits on legacy files.
    files_to_check: list[str] = []
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout:
            for relpath in result.stdout.splitlines():
                relpath = relpath.strip()
                if not relpath.endswith(".py"):
                    continue
                fullpath = (base / relpath).resolve()
                if presentation_dir in fullpath.parents:
                    files_to_check.append(str(fullpath))
    except Exception:
        files_to_check = []

    if not files_to_check:
        return 0

    all_errors = []
    for filepath in files_to_check:
        errors = check_file(filepath)
        all_errors.extend(errors)

    if all_errors:
        print("[ERROR] Theme color violations (use THEME constants, no hardcoded #hex colors):")
        for error in all_errors[:10]:  # Show first 10
            print(f"   {error}")
        if len(all_errors) > 10:
            print(f"   ... and {len(all_errors) - 10} more")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
