"""
Demo script showing orchestrator dispatching jobs to robots.

This script demonstrates the complete orchestrator-robot flow:
1. Start orchestrator with WebSocket server
2. Robots connect and register
3. Jobs are queued and dispatched to available robots
4. Job progress and completion are tracked

Usage:
    # Terminal 1 - Start Orchestrator:
    python scripts/demo_orchestrator.py

    # Terminal 2 - Start Robot:
    python scripts/demo_robot.py

    # Or start multiple robots:
    python scripts/demo_robot.py --name "Robot-1"
    python scripts/demo_robot.py --name "Robot-2"
"""

import asyncio
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loguru import logger

from casare_rpa.orchestrator.engine import OrchestratorEngine
from casare_rpa.orchestrator.models import Job, JobStatus, JobPriority


# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO",
)


async def main():
    """Main demo function."""
    print("\n" + "=" * 60)
    print("  CasareRPA Orchestrator Demo")
    print("=" * 60 + "\n")

    # Create engine
    engine = OrchestratorEngine(
        load_balancing="round_robin",
        dispatch_interval=5,
    )

    # Start engine (connects to data service)
    await engine.start()

    # Start WebSocket server
    port = 8765
    await engine.start_server(host="0.0.0.0", port=port)

    print(f"\nOrchestrator running on ws://localhost:{port}")
    print("\nTo connect robots, run in another terminal:")
    print("  python scripts/demo_robot.py --name 'My-Robot'")
    print("\nPress Ctrl+C to stop\n")

    # Wait for robots to connect
    print("Waiting for robots to connect...")

    try:
        while True:
            # Display connected robots
            robots = engine.connected_robots
            if robots:
                print(f"\nConnected robots ({len(robots)}): {', '.join(robots)}")

                # Queue a test job if we have robots
                if len(robots) > 0 and not hasattr(main, "_job_queued"):
                    main._job_queued = True
                    await queue_test_job(engine)
            else:
                print("No robots connected yet...")

            await asyncio.sleep(5)

    except KeyboardInterrupt:
        print("\n\nShutting down...")

    finally:
        await engine.stop()
        print("Orchestrator stopped.")


async def queue_test_job(engine: OrchestratorEngine):
    """Queue a test job to demonstrate dispatch."""
    print("\n" + "-" * 40)
    print("Queuing test job...")

    # Create a simple test workflow
    test_workflow = {
        "metadata": {
            "name": "Test Workflow",
            "version": "1.0",
            "created": datetime.utcnow().isoformat(),
        },
        "nodes": [
            {
                "id": "start_1",
                "type": "StartNode",
                "position": {"x": 100, "y": 100},
            },
            {
                "id": "log_1",
                "type": "LogNode",
                "position": {"x": 300, "y": 100},
                "config": {"message": "Hello from orchestrator!"},
            },
            {
                "id": "end_1",
                "type": "EndNode",
                "position": {"x": 500, "y": 100},
            },
        ],
        "connections": [
            {"from": {"node": "start_1", "port": "exec_out"}, "to": {"node": "log_1", "port": "exec_in"}},
            {"from": {"node": "log_1", "port": "exec_out"}, "to": {"node": "end_1", "port": "exec_in"}},
        ],
    }

    import json
    workflow_json = json.dumps(test_workflow)

    # Submit job
    job = await engine.submit_job(
        workflow_id=str(uuid.uuid4()),
        workflow_name="Test Workflow",
        workflow_json=workflow_json,
        priority=JobPriority.NORMAL,
    )

    if job:
        print(f"Job queued: {job.id[:8]}")
        print(f"Status: {job.status.value}")
    else:
        print("Failed to queue job")

    print("-" * 40 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
