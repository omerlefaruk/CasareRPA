from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _scan_paths(root: Path, needle: str) -> list[Path]:
    matches: list[Path] = []
    for path in root.rglob("*.md"):
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="utf-8", errors="ignore")
        if needle in content:
            matches.append(path)
    return matches


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ensure .agent/ and .claude/ docs do not cross-reference path roots.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root (default: current).",
    )
    args = parser.parse_args()

    root = Path(args.root)
    agent_root = root / ".agent"
    claude_root = root / ".claude"

    issues: list[str] = []
    if agent_root.exists():
        for path in _scan_paths(agent_root, ".claude/"):
            issues.append(f"{path}: contains .claude/")
    if claude_root.exists():
        for path in _scan_paths(claude_root, ".agent/"):
            issues.append(f"{path}: contains .agent/")

    if issues:
        print("Path hygiene violations found:")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print("Path hygiene check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
