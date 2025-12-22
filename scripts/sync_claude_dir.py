from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys

SYNC_DIRS = ("agents", "commands", "rules", "skills", "workflows", "artifacts")
SOURCE_DIR = ".agent"
DEST_DIR = ".claude"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _collect_files(base: Path) -> set[Path]:
    if not base.exists():
        return set()
    return {path.relative_to(base) for path in base.rglob("*") if path.is_file()}


def _read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _remove_empty_dirs(base: Path) -> None:
    if not base.exists():
        return
    for path in sorted(base.rglob("*"), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()


def _sync_tree(source: Path, dest: Path) -> list[str]:
    updated: list[str] = []
    if not source.exists():
        return updated

    dest.mkdir(parents=True, exist_ok=True)
    source_files = _collect_files(source)
    dest_files = _collect_files(dest)

    for extra in sorted(dest_files - source_files):
        (dest / extra).unlink()
        updated.append(str(extra))

    for rel_path in sorted(source_files):
        source_file = source / rel_path
        dest_file = dest / rel_path
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        if not dest_file.exists() or _read_bytes(dest_file) != _read_bytes(source_file):
            shutil.copy2(source_file, dest_file)
            updated.append(str(rel_path))

    _remove_empty_dirs(dest)
    return updated


def _is_linked_dir(dest: Path, source: Path) -> bool:
    if not dest.exists():
        return False
    try:
        resolved = dest.resolve(strict=True)
    except FileNotFoundError:
        return False
    return resolved == source.resolve(strict=True) and dest.is_dir()


def _remove_dir(path: Path) -> None:
    if not path.exists():
        return
    if path.is_symlink():
        path.unlink()
        return
    try:
        resolved = path.resolve(strict=True)
        if resolved != path.absolute():
            if sys.platform.startswith("win"):
                subprocess.run(
                    ["cmd", "/c", "rmdir", str(path)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            else:
                path.unlink()
            return
    except FileNotFoundError:
        pass
    shutil.rmtree(path)


def _create_link(dest: Path, source: Path) -> None:
    if sys.platform.startswith("win"):
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(dest), str(source)],
            check=True,
            capture_output=True,
            text=True,
        )
    else:
        dest.symlink_to(source, target_is_directory=True)


def _sync_links(source_root: Path, dest_root: Path) -> int:
    updated: list[str] = []
    dest_root.mkdir(parents=True, exist_ok=True)

    for name in SYNC_DIRS:
        source_dir = source_root / name
        dest_dir = dest_root / name
        if not source_dir.exists():
            continue
        if _is_linked_dir(dest_dir, source_dir):
            continue
        if dest_dir.exists():
            _remove_dir(dest_dir)
        _create_link(dest_dir, source_dir)
        updated.append(name)

    if updated:
        print("Linked .claude to .agent.")
    else:
        print("No .claude link changes needed.")
    return 0


def _check_tree(source: Path, dest: Path) -> list[str]:
    issues: list[str] = []
    if not source.exists():
        return issues
    if not dest.exists():
        issues.append(f"Missing directory: {dest}")
        return issues

    source_files = _collect_files(source)
    dest_files = _collect_files(dest)

    for missing in sorted(source_files - dest_files):
        issues.append(f"Missing file: {dest / missing}")
    for extra in sorted(dest_files - source_files):
        issues.append(f"Extra file: {dest / extra}")
    for rel_path in sorted(source_files & dest_files):
        source_file = source / rel_path
        dest_file = dest / rel_path
        if _read_bytes(source_file) != _read_bytes(dest_file):
            issues.append(f"Mismatch: {dest_file}")
    return issues


def _sync(root: Path, use_links: bool) -> int:
    source_root = root / SOURCE_DIR
    dest_root = root / DEST_DIR
    if not source_root.exists():
        print(f"Missing {SOURCE_DIR} at {source_root}")
        return 1

    if use_links:
        return _sync_links(source_root, dest_root)

    updated: list[str] = []
    for name in SYNC_DIRS:
        updated.extend(
            _sync_tree(source_root / name, dest_root / name),
        )

    if updated:
        print("Synced .claude from .agent.")
    else:
        print("No .claude changes needed.")
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
        print("Found .claude sync issues:")
        for issue in issues:
            print(f"  - {issue}")
        print("Run: python scripts/sync_claude_dir.py")
        return 1

    print(".claude is in sync with .agent.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync .agent/ -> .claude/ or verify they match.",
    )
    parser.add_argument(
        "--link",
        action="store_true",
        help="Create directory junctions/symlinks instead of copying files.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if .claude does not match .agent.",
    )
    args = parser.parse_args()

    root = _repo_root()
    if args.check:
        return _check(root)
    return _sync(root, args.link)


if __name__ == "__main__":
    sys.exit(main())
