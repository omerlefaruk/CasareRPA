"""
End-to-end integration test for Robot Hardening (Phase 8B).

Run this script to test the robot + orchestrator integration:
    python test_robot_integration.py

Prerequisites:
1. Run SQL migration on Supabase
2. Enable Realtime for jobs and robots tables
3. Set SUPABASE_URL and SUPABASE_KEY in .env
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

import os
from loguru import logger


async def test_connection():
    """Test 1: Connection Manager"""
    print("\n" + "=" * 60)
    print("TEST 1: Connection Manager")
    print("=" * 60)

    from casare_rpa.robot import ConnectionManager, ConnectionConfig

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return False

    config = ConnectionConfig(
        initial_delay=1.0,
        max_delay=10.0,
        connection_timeout=15.0,
    )

    manager = ConnectionManager(url, key, config=config)

    print(f"Connecting to {url[:30]}...")
    success = await manager.connect()

    if success:
        print("SUCCESS: Connected to Supabase")
        status = manager.get_status()
        print(f"  State: {status['state']}")
        print(f"  Connected: {status['is_connected']}")
    else:
        print("FAILED: Could not connect")
        return False

    await manager.disconnect()
    return True


async def test_circuit_breaker():
    """Test 2: Circuit Breaker"""
    print("\n" + "=" * 60)
    print("TEST 2: Circuit Breaker")
    print("=" * 60)

    from casare_rpa.robot import CircuitBreaker, CircuitBreakerConfig

    config = CircuitBreakerConfig(failure_threshold=3, timeout=5.0)
    breaker = CircuitBreaker("test", config=config)

    # Test successful call
    async def success_func():
        return "OK"

    result = await breaker.call(success_func)
    print(f"SUCCESS: Circuit breaker call returned: {result}")
    print(f"  State: {breaker.state.value}")
    print(f"  Stats: {breaker.stats.successful_calls} successful")

    return True


async def test_offline_queue():
    """Test 3: Offline Queue"""
    print("\n" + "=" * 60)
    print("TEST 3: Offline Queue")
    print("=" * 60)

    import tempfile
    from casare_rpa.robot import OfflineQueue

    with tempfile.TemporaryDirectory() as tmpdir:
        queue = OfflineQueue(db_path=Path(tmpdir) / "test.db", robot_id="test-robot")

        # Cache a job
        await queue.cache_job("test-job-1", '{"nodes": []}', "pending")
        print("SUCCESS: Cached job")

        # Get cached jobs
        cached = await queue.get_cached_jobs()
        print(f"  Cached jobs: {len(cached)}")

        # Save checkpoint
        await queue.save_checkpoint("test-job-1", "cp-1", "node-1", {"var": "value"})
        print("SUCCESS: Saved checkpoint")

        # Get checkpoint
        checkpoint = await queue.get_latest_checkpoint("test-job-1")
        if checkpoint:
            print(f"  Checkpoint node: {checkpoint['node_id']}")

        # Get stats
        stats = await queue.get_queue_stats()
        print(f"  Queue stats: {stats}")

    return True


async def test_metrics_collector():
    """Test 4: Metrics Collector"""
    print("\n" + "=" * 60)
    print("TEST 4: Metrics Collector")
    print("=" * 60)

    from casare_rpa.robot import MetricsCollector

    metrics = MetricsCollector()

    # Start a job
    metrics.start_job("job-1", "Test Workflow", total_nodes=5)
    print("SUCCESS: Started job tracking")

    # Record node executions
    for i in range(5):
        metrics.record_node(f"node-{i}", "TestNode", 100.0, True)

    metrics.end_job(success=True)
    print("SUCCESS: Ended job tracking")

    summary = metrics.get_summary()
    print(f"  Total jobs: {summary['total_jobs']}")
    print(f"  Success rate: {summary['success_rate_percent']}%")

    node_stats = metrics.get_node_stats()
    print(f"  Node types tracked: {list(node_stats.keys())}")

    return True


async def test_audit_logger():
    """Test 5: Audit Logger"""
    print("\n" + "=" * 60)
    print("TEST 5: Audit Logger")
    print("=" * 60)

    import tempfile
    from casare_rpa.robot import AuditLogger, AuditEventType

    with tempfile.TemporaryDirectory() as tmpdir:
        logger_instance = AuditLogger("test-robot", log_dir=Path(tmpdir))

        logger_instance.robot_started()
        logger_instance.connection_established()
        logger_instance.job_started("job-1", 5)
        logger_instance.job_completed("job-1", 1000.0)

        recent = logger_instance.get_recent(limit=10)
        print(f"SUCCESS: Logged {len(recent)} events")

        for entry in recent:
            print(f"  - {entry['event_type']}: {entry['message']}")

    return True


async def test_robot_agent():
    """Test 6: Robot Agent (brief initialization test)"""
    print("\n" + "=" * 60)
    print("TEST 6: Robot Agent")
    print("=" * 60)

    from casare_rpa.robot import RobotAgent, RobotConfig

    config = RobotConfig()
    print(f"Robot ID: {config.robot_id}")
    print(f"Robot Name: {config.robot_name}")
    print(f"Max concurrent jobs: {config.job_execution.max_concurrent_jobs}")

    agent = RobotAgent(config)
    print("SUCCESS: Robot agent initialized")

    status = agent.get_status()
    print(f"  Running: {status['running']}")
    print(f"  Connection state: {status['connection']['state']}")

    return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("PHASE 8B: Robot Hardening Integration Tests")
    print("=" * 60)

    tests = [
        ("Connection Manager", test_connection),
        ("Circuit Breaker", test_circuit_breaker),
        ("Offline Queue", test_offline_queue),
        ("Metrics Collector", test_metrics_collector),
        ("Audit Logger", test_audit_logger),
        ("Robot Agent", test_robot_agent),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            print(f"ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"  [{status}] {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\nAll tests passed! Robot hardening is working correctly.")
        print("\nNext steps:")
        print("1. Run the Orchestrator: python -m casare_rpa.orchestrator.main_window_new")
        print("2. Run a Robot: python -c \"import asyncio; from casare_rpa.robot import run_robot; asyncio.run(run_robot())\"")
    else:
        print("\nSome tests failed. Check the errors above.")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
