"""
Demo script showing a robot connecting to the orchestrator.

This script demonstrates:
1. Robot connecting to orchestrator via WebSocket
2. Registration and heartbeat
3. Receiving and executing jobs
4. Reporting progress and completion

Usage:
    # Default robot:
    python scripts/demo_robot.py

    # Named robot:
    python scripts/demo_robot.py --name "Robot-Alpha"

    # Connect to different orchestrator:
    python scripts/demo_robot.py --url ws://192.168.1.100:8765
"""

import argparse
import asyncio
import sys
import uuid
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loguru import logger

from casare_rpa.robot.websocket_client import RobotWebSocketClient


# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO",
)


class DemoRobot:
    """Demo robot that connects to orchestrator."""

    def __init__(self, robot_id: str, robot_name: str, orchestrator_url: str):
        self.robot_id = robot_id
        self.robot_name = robot_name
        self.orchestrator_url = orchestrator_url

        self.client = RobotWebSocketClient(
            robot_id=robot_id,
            robot_name=robot_name,
            orchestrator_url=orchestrator_url,
            max_concurrent_jobs=1,
        )

        self.client.set_callbacks(
            on_job_assigned=self._on_job_assigned,
            on_job_cancelled=self._on_job_cancelled,
            on_connected=self._on_connected,
            on_disconnected=self._on_disconnected,
        )

    def _on_connected(self):
        """Called when connected to orchestrator."""
        print(f"\n[{self.robot_name}] Connected to orchestrator!")
        print(f"[{self.robot_name}] Waiting for jobs...\n")

    def _on_disconnected(self):
        """Called when disconnected from orchestrator."""
        print(f"\n[{self.robot_name}] Disconnected from orchestrator\n")

    async def _on_job_assigned(self, job_data: dict):
        """Handle job assignment from orchestrator."""
        job_id = job_data.get("job_id")
        workflow_name = job_data.get("workflow_name", "Unknown")

        print(f"\n[{self.robot_name}] Received job: {job_id[:8]} - {workflow_name}")
        print(f"[{self.robot_name}] Executing workflow...")

        try:
            # Simulate job execution with progress updates
            for progress in [10, 25, 50, 75, 90, 100]:
                await asyncio.sleep(1)  # Simulate work
                await self.client.send_job_progress(
                    job_id=job_id,
                    progress=progress,
                    current_node=f"node_{progress // 25}",
                    message=f"Processing step {progress // 25}"
                )
                print(f"[{self.robot_name}] Progress: {progress}%")

            # Report completion
            await self.client.send_job_complete(
                job_id=job_id,
                result={"status": "success", "message": "Demo job completed"},
                duration_ms=6000,
            )
            print(f"[{self.robot_name}] Job completed successfully!\n")

        except Exception as e:
            # Report failure
            await self.client.send_job_failed(
                job_id=job_id,
                error_message=str(e),
            )
            print(f"[{self.robot_name}] Job failed: {e}\n")

    async def _on_job_cancelled(self, job_id: str, reason: str):
        """Handle job cancellation."""
        print(f"[{self.robot_name}] Job cancelled: {job_id[:8]} - {reason}")

    async def run(self):
        """Run the demo robot."""
        print("\n" + "=" * 60)
        print(f"  CasareRPA Demo Robot: {self.robot_name}")
        print("=" * 60)
        print(f"\nRobot ID: {self.robot_id}")
        print(f"Connecting to: {self.orchestrator_url}")
        print("\nPress Ctrl+C to stop\n")

        try:
            await self.client.connect()
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            await self.client.disconnect("Robot shutdown")
            print("Robot stopped.")


def main():
    parser = argparse.ArgumentParser(description="Demo robot for CasareRPA Orchestrator")
    parser.add_argument(
        "--name",
        default="Demo-Robot",
        help="Robot name (default: Demo-Robot)",
    )
    parser.add_argument(
        "--url",
        default="ws://localhost:8765",
        help="Orchestrator WebSocket URL (default: ws://localhost:8765)",
    )
    parser.add_argument(
        "--id",
        default=None,
        help="Robot ID (default: auto-generated)",
    )

    args = parser.parse_args()

    robot_id = args.id or str(uuid.uuid4())

    robot = DemoRobot(
        robot_id=robot_id,
        robot_name=args.name,
        orchestrator_url=args.url,
    )

    try:
        asyncio.run(robot.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
