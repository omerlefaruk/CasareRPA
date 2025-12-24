#!/usr/bin/env python3
"""
Block hardcoded secrets, API keys, tokens, passwords.
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

SECRET_PATTERNS = [
    r'api_key\s*=\s*["\'][^"\']+["\']',
    r'API_KEY\s*=\s*["\'][^"\']+["\']',
    r'token\s*=\s*["\'][^"\']+["\']',
    r'TOKEN\s*=\s*["\'][^"\']+["\']',
    r'password\s*=\s*["\'][^"\']+["\']',
    r'PASSWORD\s*=\s*["\'][^"\']+["\']',
    r'secret\s*=\s*["\'][^"\']+["\']',
    r'SECRET\s*=\s*["\'][^"\']+["\']',
    r"Authorization:\s*Bearer\s+[a-zA-Z0-9_\-\.]+",
    r"Authorization:\s*Basic\s+[a-zA-Z0-9_\-\.]+",
]

# Patterns to ignore (test fixtures, docs)
IGNORE_PATTERNS = [
    r"def test_",
    r"# test",
    r"TODO",
    r"EXAMPLE",
    r"placeholder",
]


def check_file(filepath: str) -> list[str]:
    """Check for hardcoded secrets"""
    errors = []

    # Skip test files and docs
    if "test" in filepath or "docs" in filepath or ".md" in filepath:
        return errors

    try:
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return errors

    for i, line in enumerate(lines, 1):
        # Skip comments
        if line.strip().startswith("#"):
            continue

        # Skip ignore patterns
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in IGNORE_PATTERNS):
            continue

        for secret_pattern in SECRET_PATTERNS:
            if re.search(secret_pattern, line, re.IGNORECASE):
                errors.append(
                    f"{filepath}:{i} - Hardcoded secret detected. Use environment variables instead.\n  {line.strip()}"
                )
                break

    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--all",
        action="store_true",
        help="Scan all Python files under src/ and config/ instead of only staged files.",
    )
    args = parser.parse_args()

    base = Path(__file__).parent.parent
    src_dir = base / "src"
    config_dir = base / "config"

    all_errors = []

    if not args.all:
        try:
            staged_output = subprocess.check_output(
                ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
                cwd=base,
                text=True,
            )
        except Exception:
            return 0

        staged_files: list[Path] = []
        for raw in staged_output.splitlines():
            raw = raw.strip()
            if not raw or not raw.endswith(".py"):
                continue
            path = (base / raw).resolve()
            if not path.is_file():
                continue
            if path.is_relative_to(src_dir) or path.is_relative_to(config_dir):
                staged_files.append(path)

        if not staged_files:
            return 0

        for path in staged_files:
            errors = check_file(str(path))
            all_errors.extend(errors)
    else:
        for search_dir in [src_dir, config_dir]:
            if not search_dir.exists():
                continue

            for root, _, files in os.walk(search_dir):
                for file in files:
                    if file.endswith(".py"):
                        filepath = os.path.join(root, file)
                        errors = check_file(filepath)
                        all_errors.extend(errors)

    if all_errors:
        print("[ERROR] Hardcoded secrets detected (use environment variables):")
        for error in all_errors[:10]:
            print(f"   {error}")
        if len(all_errors) > 10:
            print(f"   ... and {len(all_errors) - 10} more")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
