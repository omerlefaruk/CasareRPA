"""Trim AGENTS.md to reduce tokens.

Keeps only essential commands, removes verbose sections.
"""

import re
from pathlib import Path


def trim_agents_md(source_path: Path, backup: bool = True) -> None:
    """Trim AGENTS.md to essential content.

    Keeps:
    - Quick Commands
    - Tech Stack
    - Core Rules table
    - Modern Node Standard
    - Key Indexes

    Removes:
    - Detailed explanations
    - Extended examples
    - Verbose tables

    Args:
        source_path: Path to AGENTS.md
        backup: Create backup before modifying
    """
    if backup:
        backup_path = source_path.parent / f"{source_path.name}.backup"
        backup_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Created backup: {backup_path}")

    content = source_path.read_text(encoding="utf-8")

    sections = {
        "Quick Commands": True,
        "Tech Stack": True,
        "Core Rules": True,
        "Modern Node Standard": True,
        "Key Indexes": True,
        "Knowledge Base": False,
        "Git Workflow": False,
        "Commit Format": False,
        "Maintenance Automation": True,
        "MCP Server Audit": False,
        "Rules Cleanup": False,
    }

    trimmed_lines = []
    in_section = False
    section_indent = 0

    for line in content.split("\n"):
        if line.startswith("#"):
            match = re.match(r"^(#+)\s+(.+)$", line)
            if match:
                indent = len(match.group(1))
                section_name = match.group(2).strip()

                if section_name in sections:
                    in_section = True
                    section_indent = indent
                    trimmed_lines.append(line)
                else:
                    in_section = False
                continue

        if in_section:
            trimmed_lines.append(line)

    trimmed_content = "\n".join(trimmed_lines)

    source_path.write_text(trimmed_content, encoding="utf-8")

    original_lines = len(content.split("\n"))
    trimmed_lines_count = len(trimmed_lines)
    reduction = (1 - trimmed_lines_count / original_lines) * 100

    print("Trimmed AGENTS.md")
    print(f"  Original: {original_lines} lines")
    print(f"  Trimmed: {trimmed_lines_count} lines")
    print(f"  Reduction: {reduction:.1f}%")


def create_minimal_agents_md(source_path: Path) -> Path:
    """Create minimal version of AGENTS.md.

    Creates AGENTS.md.minimal with only essential info.

    Args:
        source_path: Path to AGENTS.md

    Returns:
        Path to minimal file
    """
    minimal = """# CasareRPA Agent Guide

## Quick Commands
```bash
pytest tests/ -v && ruff check src/ && black src/ tests/
python run.py && python manage.py canvas
```

## Core Rules

| Rule | Description |
|------|-------------|
| index-first | Read _index.md before grep/glob |
| parallel | Launch independent reads in parallel |
| no-silent-failures | Wrap external calls in try/except |
| async-first | No blocking I/O in async |
| theme-only | No hardcoded colors |

## Node Standard

```python
@properties(PropertyDef("url", PropertyType.STRING))
@node(category="browser")
class MyNode(BaseNode):
    def _define_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_input_port("url", DataType.STRING)
```

## Key Indexes
- `src/casare_rpa/nodes/_index.md`
- `src/casare_rpa/domain/_index.md`
- `.brain/_index.md`
"""

    minimal_path = source_path.parent / "AGENTS.minimal.md"
    minimal_path.write_text(minimal, encoding="utf-8")

    return minimal_path


def optimize_opencode_json(opencode_path: Path, max_files: int = 6) -> None:
    """Optimize opencode.json to limit loaded rule files.

    Keeps only essential instruction files.

    Args:
        opencode_path: Path to opencode.json
        max_files: Maximum number of rule files to keep
    """
    import json

    with open(opencode_path, encoding="utf-8") as f:
        config = json.load(f)

    if "instructions" not in config:
        return

    instructions = config["instructions"]

    essential = [
        ".opencode/rules/00-role.md",
        ".opencode/rules/01-core.md",
        ".opencode/rules/03-nodes.md",
        ".opencode/rules/06-enforcement.md",
        ".opencode/rules/ui/signal-slot-rules.md",
    ]

    filtered = [
        inst for inst in instructions if inst in essential or len(instructions) <= max_files
    ]

    config["instructions"] = filtered[:max_files]

    with open(opencode_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print("Optimized opencode.json")
    print(f"  Original: {len(instructions)} files")
    print(f"  Kept: {len(filtered)} files")


if __name__ == "__main__":
    import sys

    base_dir = Path(__file__).parent.parent
    agents_md = base_dir / "AGENTS.md"
    opencode_json = base_dir / "opencode.json"

    if "--minimal" in sys.argv:
        create_minimal_agents_md(agents_md)
    elif "--opencode" in sys.argv:
        optimize_opencode_json(opencode_json)
    else:
        trim_agents_md(agents_md)
