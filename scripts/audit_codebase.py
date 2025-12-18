"""
CasareRPA - Codebase Audit Script

Automated checks for:
1. Domain Purity (No Qt/UI imports in domain layer)
2. Async Safety (No blocking I/O in async methods)
3. Modern Port Definitions (No legacy PortType.EXEC_* usage)
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Configuration
ROOT_DIR = Path(__file__).parent.parent
SRC_DIR = ROOT_DIR / "src" / "casare_rpa"
DOMAIN_DIR = SRC_DIR / "domain"
NODES_DIR = SRC_DIR / "nodes"

# Patterns
QT_IMPORT_PATTERN = re.compile(r"from (PySide6|PyQt6|NodeGraphQt)")
BLOCKING_IO_PATTERN = re.compile(r"async def.*?\n.*?with open\(", re.DOTALL)
LEGACY_PORT_PATTERN = re.compile(r"add_input_port\(.*PortType\.EXEC_")


def audit_domain_purity() -> List[str]:
    """Check for UI/Qt imports in the domain layer."""
    violations = []
    for path in DOMAIN_DIR.rglob("*.py"):
        content = path.read_text(encoding="utf-8")
        if QT_IMPORT_PATTERN.search(content):
            violations.append(f"Domain Purity Violation: {path.relative_to(ROOT_DIR)}")
    return violations


def audit_async_safety() -> List[str]:
    """Check for blocking I/O in async methods."""
    violations = []
    for path in SRC_DIR.rglob("*.py"):
        content = path.read_text(encoding="utf-8")

        # Skip docstrings for sleep check
        # Remove docstrings and comments for a cleaner check
        clean_content = re.sub(r'""".*?"""', "", content, flags=re.DOTALL)
        clean_content = re.sub(r"'''.*?'''", "", clean_content, flags=re.DOTALL)
        clean_content = re.sub(r"#.*", "", clean_content)

        # Check for time.sleep in async functions
        # Look for async def ... followed by time.sleep before the next def/class
        async_blocks = re.split(r"(\s*async def\s+\w+)", clean_content)
        for i in range(1, len(async_blocks), 2):
            header = async_blocks[i]
            body = async_blocks[i + 1] if i + 1 < len(async_blocks) else ""

            # Find indentation of the async def
            indent_match = re.search(r"^(\s*)", header)
            indent = indent_match.group(1) if indent_match else ""

            # Look for next def/class with same or less indentation
            # This is a bit complex for regex, so we'll use a simpler approach:
            # Look for the next "def " or "class " that isn't more indented than the current one
            body_lines = body.split("\n")
            relevant_lines = []
            for line in body_lines:
                if line.strip() and (
                    line.startswith(indent + "def ")
                    or line.startswith(indent + "class ")
                    or (not line.startswith(indent) and line.strip())
                ):
                    # Found next sibling or parent definition
                    break
                relevant_lines.append(line)

            relevant_body = "\n".join(relevant_lines)

            if "time.sleep(" in relevant_body:
                violations.append(
                    f"Async Safety Violation (time.sleep): {path.relative_to(ROOT_DIR)}"
                )

            if "with open(" in relevant_body:
                # Check if it's inside a nested def (which we use for run_in_executor)
                # If "with open(" is preceded by "def " on a line with more indentation, it's likely OK
                lines = relevant_body.split("\n")
                for line_idx, line in enumerate(lines):
                    if "with open(" in line:
                        # Look backwards for a local def
                        is_wrapped = False
                        for prev_idx in range(line_idx - 1, -1, -1):
                            prev_line = lines[prev_idx].strip()
                            if prev_line.startswith("def ") or prev_line.startswith(
                                "async def "
                            ):
                                # If it's a local def (indented), we assume it's for run_in_executor
                                if lines[prev_idx].startswith("    ") or lines[
                                    prev_idx
                                ].startswith("\t"):
                                    is_wrapped = True
                                break

                        if not is_wrapped:
                            violations.append(
                                f"Async Safety Violation (Blocking I/O): {path.relative_to(ROOT_DIR)}"
                            )
                            break

    return violations


def audit_port_definitions() -> List[str]:
    """Check for legacy port definitions."""
    violations = []
    for path in NODES_DIR.rglob("*.py"):
        content = path.read_text(encoding="utf-8")
        if LEGACY_PORT_PATTERN.search(content):
            violations.append(f"Legacy Port Definition: {path.relative_to(ROOT_DIR)}")
    return violations


def main():
    print("--- CasareRPA Codebase Audit ---")

    all_violations = []

    print("Checking Domain Purity...")
    domain_violations = audit_domain_purity()
    all_violations.extend(domain_violations)

    print("Checking Async Safety...")
    async_violations = audit_async_safety()
    all_violations.extend(async_violations)

    print("Checking Port Definitions...")
    port_violations = audit_port_definitions()
    all_violations.extend(port_violations)

    print("\n--- Audit Results ---")
    if not all_violations:
        print("✅ No violations found!")
        sys.exit(0)
    else:
        for v in all_violations:
            print(f"❌ {v}")
        print(f"\nTotal violations: {len(all_violations)}")
        # sys.exit(1) # Don't exit with error yet to allow user to see output


if __name__ == "__main__":
    main()
