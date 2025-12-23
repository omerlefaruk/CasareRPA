from __future__ import annotations

import argparse
import sys
from pathlib import Path

FILES = ("AGENTS.md", "CLAUDE.md", "GEMINI.md")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _render_claude(source: str) -> str:
    rendered = source.replace(".agent/", ".claude/")
    rendered = rendered.replace(
        "AGENTS.md references `.claude/` paths.",
        "AGENTS.md references `.agent/` paths.",
    )
    return rendered


def _render_gemini(source: str) -> str:
    return source


def _check(root: Path) -> int:
    source = root / FILES[0]
    if not source.exists():
        print(f"Missing {FILES[0]} at {source}")
        return 1

    source_text = _read_text(source)
    claude_text = _render_claude(source_text)
    gemini_text = _render_gemini(source_text)
    mismatched: list[str] = []
    missing: list[str] = []

    for name in FILES[1:]:
        target = root / name
        if not target.exists():
            missing.append(name)
            continue
        target_text = _read_text(target)
        expected = claude_text if name == "CLAUDE.md" else gemini_text
        if target_text != expected:
            mismatched.append(name)

    if missing or mismatched:
        if missing:
            print(f"Missing files: {', '.join(missing)}")
        if mismatched:
            print(f"Out of sync: {', '.join(mismatched)}")
        print("Run: python scripts/sync_agent_guides.py")
        return 1

    print("Agent guide files are in sync.")
    return 0


def _sync(root: Path) -> int:
    source = root / FILES[0]
    if not source.exists():
        print(f"Missing {FILES[0]} at {source}")
        return 1

    source_text = _read_text(source)
    claude_text = _render_claude(source_text)
    gemini_text = _render_gemini(source_text)
    updated: list[str] = []

    for name in FILES[1:]:
        target = root / name
        expected = claude_text if name == "CLAUDE.md" else gemini_text
        if not target.exists() or _read_text(target) != expected:
            _write_text(target, expected)
            updated.append(name)

    if updated:
        print(f"Synced: {', '.join(updated)}")
    else:
        print("No changes needed.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync AGENTS.md -> CLAUDE.md/GEMINI.md with path rewrites or verify they match."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if files are out of sync.",
    )
    args = parser.parse_args()

    root = _repo_root()
    if args.check:
        return _check(root)
    return _sync(root)


if __name__ == "__main__":
    sys.exit(main())
