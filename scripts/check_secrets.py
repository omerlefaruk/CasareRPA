#!/usr/bin/env python3
"""
Block hardcoded secrets, API keys, tokens, passwords.
"""

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


def main() -> int:
    base = Path(__file__).parent.parent

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
        if not (
            normalized.startswith(str(base / "src").replace("\\", "/"))
            or normalized.startswith(str(base / "config").replace("\\", "/"))
        ):
            continue

        all_errors.extend(check_file(str(abs_path)))

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
