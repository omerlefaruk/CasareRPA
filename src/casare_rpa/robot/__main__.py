"""
Entry point for running the robot CLI as a module.

Usage:
    python -m casare_rpa.robot.cli start --config config/robot.yaml
    python -m casare_rpa.robot.cli stop --robot-id worker-01
    python -m casare_rpa.robot.cli status
"""

from casare_rpa.robot.cli import main

if __name__ == "__main__":
    main()
