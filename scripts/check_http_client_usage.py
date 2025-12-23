#!/usr/bin/env python3
"""
Enforce UnifiedHttpClient usage.
Block raw aiohttp, httpx imports outside infrastructure/http/
"""

import os
import re
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
