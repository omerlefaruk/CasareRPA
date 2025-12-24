#!/usr/bin/env python3
"""
Enforce UnifiedHttpClient usage.
Block raw aiohttp, httpx imports outside infrastructure/http/
"""

import argparse
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


def _get_staged_python_files(base_dir: Path, src_dir: Path) -> list[Path]:
    try:
        output = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            cwd=base_dir,
            text=True,
        )
    except Exception:
        return []

    staged_files: list[Path] = []
    for raw in output.splitlines():
        raw = raw.strip()
        if not raw or not raw.endswith(".py"):
            continue
        path = (base_dir / raw).resolve()
        if not path.is_file():
            continue
        if not path.is_relative_to(src_dir):
            continue
        staged_files.append(path)

    return staged_files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--all",
        action="store_true",
        help="Scan all Python files under src/casare_rpa instead of only staged files.",
    )
    args = parser.parse_args()

    base = Path(__file__).parent.parent
    src_dir = base / "src" / "casare_rpa"

    if not src_dir.exists():
        return 0

    all_errors = []
    if args.all:
        for root, _, files in os.walk(src_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    errors = check_file(filepath)
                    all_errors.extend(errors)
    else:
        staged_files = _get_staged_python_files(base, src_dir)
        if not staged_files:
            return 0
        for path in staged_files:
            errors = check_file(str(path))
            all_errors.extend(errors)

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
