"""
CasareRPA Robot CLI - Standalone Entry Point

This module provides a standalone CLI entry point that avoids circular imports
by importing the robot.cli module only when needed.

Usage:
    casare-robot start --config config/robot.yaml
    casare-robot stop --robot-id worker-01
    casare-robot status
"""


def main() -> None:
    """Entry point that imports robot CLI lazily."""
    from casare_rpa.robot.cli import app

    app()


if __name__ == "__main__":
    main()
