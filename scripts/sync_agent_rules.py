from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SOURCE_DIR = ".agent"
DEST_DIR = "agent-rules"
SYNC_DIRS = ("agents", "commands", "rules", "skills")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _collect_files(base: Path) -> set[Path]:
    if not base.exists():
        return set()
    return {path.relative_to(base) for path in base.rglob("*") if path.is_file()}


def _read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _sync_tree(source: Path, dest: Path) -> list[str]:
    updated: list[str] = []
    if not source.exists():
        return updated
    dest.mkdir(parents=True, exist_ok=True)
    for rel_path in sorted(_collect_files(source)):
        source_file = source / rel_path
        dest_file = dest / rel_path
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        if not dest_file.exists() or _read_bytes(dest_file) != _read_bytes(source_file):
            shutil.copy2(source_file, dest_file)
            updated.append(str(rel_path))
    return updated


def _check_tree(source: Path, dest: Path) -> list[str]:
    issues: list[str] = []
    if not source.exists():
        return issues
    if not dest.exists():
        issues.append(f"Missing directory: {dest}")
        return issues
    for rel_path in sorted(_collect_files(source)):
        source_file = source / rel_path
        dest_file = dest / rel_path
        if not dest_file.exists():
            issues.append(f"Missing file: {dest_file}")
            continue
        if _read_bytes(dest_file) != _read_bytes(source_file):
            issues.append(f"Mismatch: {dest_file}")
    return issues


def _sync(root: Path) -> int:
    source_root = root / SOURCE_DIR
    dest_root = root / DEST_DIR
    if not source_root.exists():
        print(f"Missing {SOURCE_DIR} at {source_root}")
        return 1

    updated: list[str] = []
    for name in SYNC_DIRS:
        updated.extend(
            _sync_tree(source_root / name, dest_root / name),
        )

    if updated:
        print("Synced agent-rules from .agent.")
    else:
        print("No agent-rules changes needed.")
    return 0


def _check(root: Path) -> int:
    source_root = root / SOURCE_DIR
    dest_root = root / DEST_DIR
    if not source_root.exists():
        print(f"Missing {SOURCE_DIR} at {source_root}")
        return 1

    issues: list[str] = []
    for name in SYNC_DIRS:
        issues.extend(
            _check_tree(source_root / name, dest_root / name),
        )

    if issues:
        print("Found agent-rules sync issues:")
        for issue in issues:
            print(f"  - {issue}")
        print("Run: python scripts/sync_agent_rules.py")
        return 1

    print("agent-rules is in sync with .agent.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync .agent/ -> agent-rules/ or verify they match.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if agent-rules does not match .agent.",
    )
    args = parser.parse_args()

    root = _repo_root()
    if args.check:
        return _check(root)
    return _sync(root)


if __name__ == "__main__":
    sys.exit(main())
