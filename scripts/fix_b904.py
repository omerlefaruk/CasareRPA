#!/usr/bin/env python
"""
Auto-fix B904 violations: Add 'from err' or 'from None' to raise statements in except blocks.

This script parses Python files and adds 'from err' to raise statements that are
inside except blocks but don't have a 'from' clause.
"""

import json
import re
import subprocess
from pathlib import Path


def get_b904_violations():
    """Get all B904 violations from ruff."""
    result = subprocess.run(
        ["ruff", "check", "src/", "--select=B904", "--output-format=json"],
        capture_output=True,
        text=True,
    )
    if not result.stdout:
        return []
    return json.loads(result.stdout)


def fix_file_b904(filepath: str, violations: list) -> int:
    """
    Fix B904 violations in a single file.

    Returns number of fixes applied.
    """
    path = Path(filepath)
    if not path.exists():
        return 0

    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")

    # Group violations by line number
    line_violations = {}
    for v in violations:
        row = v.get("location", {}).get("row")
        if row:
            line_violations[row] = v

    fixes_applied = 0
    modified_lines = []

    # Track except block context
    in_except_block = False
    except_var = None
    except_indent = 0

    for i, line in enumerate(lines, 1):
        # Check for except clause
        except_match = re.match(
            r"^(\s*)except\s+(\w+(?:\s+as\s+(\w+))?|\s*as\s+(\w+)|\s*:\s*|[^:]+\s+as\s+(\w+))\s*:",
            line,
        )
        if except_match:
            in_except_block = True
            except_indent = len(except_match.group(1))
            # Extract the exception variable name (e, err, ex, exc, etc.)
            if except_match.group(3):
                except_var = except_match.group(3)
            elif except_match.group(4):
                except_var = except_match.group(4)
            elif except_match.group(5):
                except_var = except_match.group(5)
            else:
                except_var = None

        # Check if we've exited the except block (dedent)
        stripped = line.lstrip()
        if stripped and in_except_block:
            current_indent = len(line) - len(stripped)
            if current_indent <= except_indent and not stripped.startswith(("#", ")", "]", "}")):
                # Keywords that continue the try block
                if not any(stripped.startswith(kw) for kw in ("except", "else:", "finally:")):
                    in_except_block = False
                    except_var = None

        # Check if this line has a B904 violation
        if i in line_violations and in_except_block:
            # Check if line has a raise without 'from'
            # Pattern: raise SomeException(...) without 'from'
            raise_match = re.search(r"(\s*raise\s+\w+(?:\([^)]*\))?)\s*$", line)
            if raise_match and "from " not in line:
                # Determine what to add
                if except_var:
                    new_line = line.rstrip() + f" from {except_var}"
                else:
                    new_line = line.rstrip() + " from None"
                modified_lines.append(new_line)
                fixes_applied += 1
                continue

        modified_lines.append(line)

    if fixes_applied > 0:
        path.write_text("\n".join(modified_lines), encoding="utf-8")
        print(f"  Fixed {fixes_applied} violations in {filepath}")

    return fixes_applied


def main():
    print("Fetching B904 violations...")
    violations = get_b904_violations()
    print(f"Found {len(violations)} B904 violations")

    # Group by file
    files = {}
    for v in violations:
        filepath = v.get("filename", "")
        if filepath:
            if filepath not in files:
                files[filepath] = []
            files[filepath].append(v)

    print(f"\nProcessing {len(files)} files...")
    total_fixes = 0

    for filepath, file_violations in files.items():
        fixes = fix_file_b904(filepath, file_violations)
        total_fixes += fixes

    print(f"\nTotal fixes applied: {total_fixes}")

    # Re-run ruff to see remaining issues
    print("\nRe-checking with ruff...")
    result = subprocess.run(
        ["ruff", "check", "src/", "--select=B904", "--statistics"],
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout)
    else:
        print("No B904 violations remaining!")


if __name__ == "__main__":
    main()
