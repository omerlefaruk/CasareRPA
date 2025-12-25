#!/usr/bin/env python
"""
Claude Code Mode Switcher

Switch between different Claude Code context modes:
- minimal: ~2KB tokens, fastest
- standard: ~10-12KB tokens, balanced (default)
- full: ~30KB+ tokens, maximum context

Usage:
    python scripts/switch_claude_mode.py minimal
    python scripts/switch_claude_mode.py standard
    python scripts/switch_claude_mode.py full
    python scripts/switch_claude_mode.py status
"""

import argparse
import json
import shutil
from pathlib import Path

# Mode definitions
MODES = {
    "minimal": {
        "description": "~2KB tokens - Quick sessions, debugging",
        "config": ".claude/claude-minimal.json",
    },
    "standard": {
        "description": "~10-12KB tokens - Normal development (default)",
        "config": ".claude/claude-standard.json",
    },
    "full": {
        "description": "~30KB+ tokens - Deep research, documentation",
        "config": ".claude/claude-full.json",
    },
}

ACTIVE_FILE = ".claude/claude-active.json"


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def get_active_mode(project_root: Path) -> str | None:
    """Get the currently active mode."""
    active_file = project_root / ACTIVE_FILE
    if active_file.exists():
        try:
            with open(active_file) as f:
                data = json.load(f)
                return data.get("mode")
        except (OSError, json.JSONDecodeError):
            return None
    return None


def set_mode(project_root: Path, mode: str) -> bool:
    """Set the active Claude Code mode."""
    if mode not in MODES:
        print(f"Error: Unknown mode '{mode}'. Available modes: {', '.join(MODES.keys())}")
        return False

    # Read the mode config
    config_file = project_root / MODES[mode]["config"]
    if not config_file.exists():
        print(f"Error: Config file not found: {config_file}")
        return False

    with open(config_file) as f:
        config = json.load(f)

    # Write the active mode file
    active_file = project_root / ACTIVE_FILE
    with open(active_file, "w") as f:
        json.dump(
            {
                "mode": mode,
                "description": MODES[mode]["description"],
                "config": str(MODES[mode]["config"]),
                "instructions": config.get("instructions", []),
                "token_budget": config.get("context", {}).get("token_budget", "unknown"),
            },
            f,
            indent=2,
        )

    print(f"✓ Claude Code mode set to: {mode}")
    print(f"  {MODES[mode]['description']}")
    return True


def print_status(project_root: Path):
    """Print the current mode status."""
    active = get_active_mode(project_root)

    print("Claude Code Mode Status")
    print("=" * 50)

    if active:
        active_file = project_root / ACTIVE_FILE
        with open(active_file) as f:
            data = json.load(f)
        print(f"Active Mode: {active}")
        print(f"Description: {data.get('description', 'N/A')}")
        print(f"Token Budget: {data.get('token_budget', 'N/A')}")
    else:
        print("Active Mode: None (using default)")

    print()
    print("Available Modes:")
    for mode, info in MODES.items():
        marker = " →" if mode == active else "  "
        print(f"  {marker} {mode:10s} {info['description']}")


def main():
    parser = argparse.ArgumentParser(description="Switch between Claude Code context modes")
    parser.add_argument(
        "mode",
        nargs="?",
        choices=list(MODES.keys()) + ["status"],
        help="Mode to switch to (minimal, standard, full) or 'status' to show current mode",
        default="status",
    )

    args = parser.parse_args()
    project_root = get_project_root()

    if args.mode == "status":
        print_status(project_root)
    else:
        set_mode(project_root, args.mode)


if __name__ == "__main__":
    main()
