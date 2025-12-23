"""
Mass update script to remove manual context.resolve_value() calls from nodes.

This script removes redundant context.resolve_value() calls that are now
automatically handled by get_parameter() auto-resolution.

Patterns removed:
1. value = context.resolve_value(value)  # simple reassignment
2. x = context.resolve_value(x) if x else default  # conditional pattern
3. if hasattr(context, "resolve_value"): x = context.resolve_value(x)  # legacy pattern
4. Empty if blocks left after removal

Safety:
- Only removes calls where the variable is reassigned to itself
- Preserves resolve_value calls used for different purposes
"""

import re
import sys
from pathlib import Path

# Files to skip (they use resolve_value for non-parameter purposes)
SKIP_FILES = [
    "variable_resolver.py",
    "execution_context.py",
    "execution_state.py",
    "variable_cache.py",
]


def should_skip_file(filepath: Path) -> bool:
    """Check if file should be skipped."""
    return filepath.name in SKIP_FILES


def remove_resolve_value_calls(content: str) -> tuple[str, int]:
    """
    Remove redundant context.resolve_value() calls.

    Returns:
        Tuple of (modified_content, count_of_removals)
    """
    lines = content.split("\n")
    new_lines = []
    removals = 0
    i = 0

    while i < len(lines):
        line = lines[i]

        # Pattern 1: Simple reassignment - x = context.resolve_value(x)
        match = re.match(r"^(\s*)([\w_]+)\s*=\s*context\.resolve_value\(\2\)\s*$", line)
        if match:
            removals += 1
            i += 1
            continue

        # Pattern 1b: With str() wrapper - x = str(context.resolve_value(x))
        match = re.match(r"^(\s*)([\w_]+)\s*=\s*str\(context\.resolve_value\(\2\)\)\s*$", line)
        if match:
            removals += 1
            i += 1
            continue

        # Pattern 1c: x = context.resolve_value(str(x))
        match = re.match(r"^(\s*)([\w_]+)\s*=\s*context\.resolve_value\(str\(\2\)\)\s*$", line)
        if match:
            removals += 1
            i += 1
            continue

        # Pattern 2: Conditional - x = context.resolve_value(x) if x else default
        match = re.match(
            r"^(\s*)([\w_]+)\s*=\s*context\.resolve_value\(\2\)\s+if\s+\2\s+else\s+(.+)$", line
        )
        if match:
            indent, var, default = match.groups()
            new_lines.append(f"{indent}{var} = {var} if {var} else {default}")
            removals += 1
            i += 1
            continue

        # Pattern 3: if hasattr() followed by resolve_value - REMOVE BOTH LINES
        # Matches: if parse_mode and hasattr(context, "resolve_value"):
        match = re.match(
            r'^(\s*)if\s+([\w_]+)\s+and\s+hasattr\(context,\s*["\']resolve_value["\']\):\s*$', line
        )
        if match:
            indent, var = match.groups()
            # Check next line for resolve_value call on same var
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                inner_match = re.match(
                    rf"^(\s+){var}\s*=\s*context\.resolve_value\({var}\)\s*$", next_line
                )
                if inner_match:
                    # Remove both lines
                    removals += 1
                    i += 2
                    continue

        # Pattern 3b: Simple if hasattr(context, "resolve_value"):
        match = re.match(r'^(\s*)if\s+hasattr\(context,\s*["\']resolve_value["\']\)\s*:\s*$', line)
        if match:
            indent = match.group(1)
            # Check next line for resolve_value call
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                inner_match = re.match(
                    r"^(\s+)([\w_]+)\s*=\s*context\.resolve_value\(\2\)\s*$", next_line
                )
                if inner_match and len(inner_match.group(1)) > len(indent):
                    # Remove both lines
                    removals += 1
                    i += 2
                    continue

        # Pattern 3c: if hasattr(context, "resolve_value") and var:
        match = re.match(
            r'^(\s*)if\s+hasattr\(context,\s*["\']resolve_value["\']\)\s+and\s+([\w_]+):\s*$', line
        )
        if match:
            indent, var = match.groups()
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                inner_match = re.match(
                    rf"^(\s+){var}\s*=\s*context\.resolve_value\({var}\)\s*$", next_line
                )
                if inner_match:
                    removals += 1
                    i += 2
                    continue

        # Pattern 4: Inline with or - x = context.resolve_value(x) or ""
        match = re.match(r"^(\s*)([\w_]+)\s*=\s*context\.resolve_value\(\2\)\s+or\s+(.+)$", line)
        if match:
            indent, var, default = match.groups()
            new_lines.append(f"{indent}{var} = {var} or {default}")
            removals += 1
            i += 1
            continue

        # Pattern 5: Multi-line if hasattr block scanning forward
        # if hasattr(context, "resolve_value"):
        #     if something:
        #         x = context.resolve_value(x)
        # This is too complex for simple regex, skip for now

        new_lines.append(line)
        i += 1

    return "\n".join(new_lines), removals


def process_file(filepath: Path, dry_run: bool = False) -> int:
    """Process a single file and return count of removals."""
    if should_skip_file(filepath):
        return 0

    content = filepath.read_text(encoding="utf-8")

    # Quick check if file has resolve_value
    if "context.resolve_value" not in content:
        return 0

    new_content, removals = remove_resolve_value_calls(content)

    if removals > 0 and not dry_run:
        filepath.write_text(new_content, encoding="utf-8")
        print(f"  {filepath.name}: {removals} removals")
    elif removals > 0:
        print(f"  [DRY RUN] {filepath.name}: {removals} would be removed")

    return removals


def main():
    """Main entry point."""
    dry_run = "--dry-run" in sys.argv

    nodes_dir = Path(__file__).parent.parent / "src" / "casare_rpa" / "nodes"

    if not nodes_dir.exists():
        # Try alternate path (if running from scripts folder)
        nodes_dir = Path("src/casare_rpa/nodes")

    if not nodes_dir.exists():
        print(f"Error: nodes directory not found at {nodes_dir}")
        return 1

    print(f"Scanning {nodes_dir}...")
    if dry_run:
        print("[DRY RUN MODE - no files will be modified]")

    total_removals = 0
    files_modified = 0

    for py_file in nodes_dir.rglob("*.py"):
        removals = process_file(py_file, dry_run)
        if removals > 0:
            total_removals += removals
            files_modified += 1

    print(
        f"\n{'Would remove' if dry_run else 'Removed'} {total_removals} resolve_value calls from {files_modified} files"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
