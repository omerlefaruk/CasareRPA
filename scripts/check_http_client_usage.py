#!/usr/bin/env python3
"""
Enforce UnifiedHttpClient usage.
Block raw aiohttp, httpx imports outside infrastructure/http/
"""

import os
import re
import subprocess
import sys
from pathlib import Path

FORBIDDEN_HTTP_IMPORTS = [
    r"import\s+aiohttp",
    r"from\s+aiohttp",
    r"import\s+httpx",
    r"from\s+httpx",
    r"import\s+requests",
    r"from\s+requests",
]


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
    output = _run_git(["diff", "--name-only", "--cached"])
    if not output:
        output = _run_git(["diff", "--name-only", "HEAD"])
    if not output:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def check_file(filepath: str) -> list[str]:
    """Check for raw HTTP client imports"""
    errors = []

    # Normalize path for cross-platform comparison (Windows uses backslashes)
    normalized_path = filepath.replace("\\", "/")

    # Allow raw imports in infrastructure/http/ or tests
    if "infrastructure/http" in normalized_path or "test" in normalized_path:
        return errors

    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()
        for i, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith("#"):
                continue

            for pattern in FORBIDDEN_HTTP_IMPORTS:
                if re.search(pattern, line):
                    errors.append(
                        f"{filepath}:{i} - Use UnifiedHttpClient instead of raw HTTP library\n  {line.strip()}"
                    )
                    break

    return errors


def main() -> int:
    base = Path(__file__).parent.parent
    src_dir = base / "src" / "casare_rpa"

    if not src_dir.exists():
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
        if "/src/casare_rpa/" not in normalized:
            continue

        all_errors.extend(check_file(str(abs_path)))

    if all_errors:
        print(
            "[ERROR] HTTP client violations (use UnifiedHttpClient, not raw aiohttp/httpx/requests):"
        )
        for error in all_errors[:10]:
            print(f"   {error}")
        if len(all_errors) > 10:
            print(f"   ... and {len(all_errors) - 10} more")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
