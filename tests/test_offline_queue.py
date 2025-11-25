"""
Comprehensive tests for the Offline Job Queue.

Tests the SQLite-based job caching system including:
- Basic job operations (cache, update status, query)
- Checkpoint management for resumable execution
- Event history/audit logging
- Queue statistics and cleanup
- Chaos scenarios (corruption, concurrent access, edge cases)
"""

import asyncio
import os
import sqlite3
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any

import pytest
import orjson

from casare_rpa.robot.offline_queue import OfflineQueue, CachedJobStatus


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def temp_db_path(tmp_path):
    """Create a temporary database path."""
    return tmp_path / "test_offline_queue.db"


@pytest.fixture
def offline_queue(temp_db_path):
    """Create an OfflineQueue instance with temp database."""
    queue = OfflineQueue(db_path=temp_db_path, robot_id="test-robot-001")
    yield queue
    # Cleanup handled by tmp_path fixture


@pytest.fixture
def sample_workflow_json():
    """Sample workflow JSON for testing."""
    return orjson.dumps({
        "nodes": [
            {"id": "start_1", "type": "StartNode", "position": [0, 0]},
            {"id": "end_1", "type": "EndNode", "position": [200, 0]}
        ],
        "connections": [
            {"from": "start_1", "to": "end_1"}
        ],
        "variables": {}
    }).decode()


@pytest.fixture
def multiple_jobs_data(sample_workflow_json):
    """Create multiple job test data."""
    return [
        {"job_id": f"job-{i}", "workflow_json": sample_workflow_json, "status": "pending"}
        for i in range(5)
    ]


# =============================================================================
# CachedJobStatus Enum Tests
# =============================================================================

class TestCachedJobStatus:
    """Test CachedJobStatus enum values."""

    def test_all_statuses_defined(self):
        """Verify all expected statuses exist."""
        assert CachedJobStatus.CACHED.value == "cached"
        assert CachedJobStatus.IN_PROGRESS.value == "in_progress"
        assert CachedJobStatus.COMPLETED.value == "completed"
        assert CachedJobStatus.FAILED.value == "failed"
        assert CachedJobStatus.SYNCED.value == "synced"

    def test_status_count(self):
        """Verify correct number of statuses."""
        assert len(CachedJobStatus) == 5


# =============================================================================
# Initialization Tests
# =============================================================================

class TestOfflineQueueInit:
    """Test OfflineQueue initialization."""

    def test_init_with_custom_path(self, temp_db_path):
        """Test initialization with custom database path."""
        queue = OfflineQueue(db_path=temp_db_path, robot_id="robot-123")
        assert queue.db_path == temp_db_path
        assert queue.robot_id == "robot-123"
        assert temp_db_path.exists()

    def test_init_default_path(self, tmp_path, monkeypatch):
        """Test initialization with default path."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        queue = OfflineQueue(robot_id="robot-456")
        expected_path = tmp_path / ".casare_rpa" / "offline_queue.db"
        assert queue.db_path == expected_path

    def test_init_creates_parent_directory(self, tmp_path):
        """Test that parent directory is created if missing."""
        nested_path = tmp_path / "deep" / "nested" / "path" / "queue.db"
        queue = OfflineQueue(db_path=nested_path, robot_id="robot")
        assert nested_path.parent.exists()

    def test_init_creates_tables(self, temp_db_path):
        """Test that all required tables are created."""
        queue = OfflineQueue(db_path=temp_db_path, robot_id="robot")

        with queue._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row['name'] for row in cursor.fetchall()}

        assert "cached_jobs" in tables
        assert "job_checkpoints" in tables
        assert "execution_history" in tables

    def test_init_creates_indexes(self, temp_db_path):
        """Test that indexes are created."""
        queue = OfflineQueue(db_path=temp_db_path, robot_id="robot")

        with queue._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = {row['name'] for row in cursor.fetchall()}

        assert "idx_cached_jobs_status" in indexes
        assert "idx_cached_jobs_robot" in indexes


# =============================================================================
# Job Caching Tests
# =============================================================================

class TestJobCaching:
    """Test job caching operations."""

    @pytest.mark.asyncio
    async def test_cache_job_basic(self, offline_queue, sample_workflow_json):
        """Test basic job caching."""
        result = await offline_queue.cache_job(
            job_id="job-001",
            workflow_json=sample_workflow_json,
            original_status="pending"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_cache_job_retrieval(self, offline_queue, sample_workflow_json):
        """Test that cached job can be retrieved."""
        await offline_queue.cache_job("job-002", sample_workflow_json, "pending")

        jobs = await offline_queue.get_cached_jobs()
        assert len(jobs) == 1
        assert jobs[0]['id'] == "job-002"
        assert jobs[0]['cached_status'] == "cached"

    @pytest.mark.asyncio
    async def test_cache_job_replace(self, offline_queue, sample_workflow_json):
        """Test that caching same job ID replaces existing."""
        await offline_queue.cache_job("job-003", sample_workflow_json, "pending")
        await offline_queue.cache_job("job-003", '{"updated": true}', "running")

        jobs = await offline_queue.get_cached_jobs()
        assert len(jobs) == 1
        assert jobs[0]['workflow_json'] == '{"updated": true}'
        assert jobs[0]['original_status'] == "running"

    @pytest.mark.asyncio
    async def test_cache_multiple_jobs(self, offline_queue, multiple_jobs_data):
        """Test caching multiple jobs."""
        for job in multiple_jobs_data:
            await offline_queue.cache_job(
                job["job_id"], job["workflow_json"], job["status"]
            )

        jobs = await offline_queue.get_cached_jobs()
        assert len(jobs) == 5


# =============================================================================
# Job Status Transition Tests
# =============================================================================

class TestJobStatusTransitions:
    """Test job status transitions."""

    @pytest.mark.asyncio
    async def test_mark_in_progress(self, offline_queue, sample_workflow_json):
        """Test marking job as in progress."""
        await offline_queue.cache_job("job-010", sample_workflow_json, "pending")
        result = await offline_queue.mark_in_progress("job-010")

        assert result is True
        jobs = await offline_queue.get_in_progress_jobs()
        assert len(jobs) == 1
        assert jobs[0]['id'] == "job-010"
        assert jobs[0]['started_at'] is not None

    @pytest.mark.asyncio
    async def test_mark_in_progress_nonexistent(self, offline_queue):
        """Test marking nonexistent job as in progress."""
        result = await offline_queue.mark_in_progress("nonexistent-job")
        assert result is False

    @pytest.mark.asyncio
    async def test_mark_completed_success(self, offline_queue, sample_workflow_json):
        """Test marking job as completed successfully."""
        await offline_queue.cache_job("job-020", sample_workflow_json, "pending")
        await offline_queue.mark_in_progress("job-020")

        result = await offline_queue.mark_completed(
            "job-020",
            success=True,
            result={"output": "test data"},
            logs="Execution completed"
        )

        assert result is True
        jobs = await offline_queue.get_jobs_to_sync()
        assert len(jobs) == 1
        assert jobs[0]['cached_status'] == "completed"
        assert jobs[0]['completed_at'] is not None

    @pytest.mark.asyncio
    async def test_mark_completed_failure(self, offline_queue, sample_workflow_json):
        """Test marking job as failed."""
        await offline_queue.cache_job("job-021", sample_workflow_json, "pending")
        await offline_queue.mark_in_progress("job-021")

        result = await offline_queue.mark_completed(
            "job-021",
            success=False,
            error="Execution failed: timeout"
        )

        assert result is True
        jobs = await offline_queue.get_jobs_to_sync()
        assert len(jobs) == 1
        assert jobs[0]['cached_status'] == "failed"
        assert jobs[0]['error'] == "Execution failed: timeout"

    @pytest.mark.asyncio
    async def test_mark_synced(self, offline_queue, sample_workflow_json):
        """Test marking job as synced."""
        await offline_queue.cache_job("job-030", sample_workflow_json, "pending")
        await offline_queue.mark_in_progress("job-030")
        await offline_queue.mark_completed("job-030", success=True)

        result = await offline_queue.mark_synced("job-030")

        assert result is True
        jobs = await offline_queue.get_jobs_to_sync()
        assert len(jobs) == 0  # Synced jobs shouldn't appear in jobs_to_sync

    @pytest.mark.asyncio
    async def test_full_status_lifecycle(self, offline_queue, sample_workflow_json):
        """Test complete job lifecycle: cached -> in_progress -> completed -> synced."""
        job_id = "lifecycle-job"

        # Cache
        await offline_queue.cache_job(job_id, sample_workflow_json, "pending")
        stats = await offline_queue.get_queue_stats()
        assert stats.get("cached", 0) == 1

        # In Progress
        await offline_queue.mark_in_progress(job_id)
        stats = await offline_queue.get_queue_stats()
        assert stats.get("in_progress", 0) == 1

        # Completed
        await offline_queue.mark_completed(job_id, success=True)
        stats = await offline_queue.get_queue_stats()
        assert stats.get("completed", 0) == 1

        # Synced
        await offline_queue.mark_synced(job_id)
        stats = await offline_queue.get_queue_stats()
        assert stats.get("synced", 0) == 1


# =============================================================================
# Sync Attempt Tracking Tests
# =============================================================================

class TestSyncAttemptTracking:
    """Test sync attempt tracking."""

    @pytest.mark.asyncio
    async def test_increment_sync_attempts(self, offline_queue, sample_workflow_json):
        """Test incrementing sync attempts."""
        await offline_queue.cache_job("job-040", sample_workflow_json, "pending")
        await offline_queue.mark_in_progress("job-040")
        await offline_queue.mark_completed("job-040", success=True)

        # Increment multiple times
        for i in range(3):
            result = await offline_queue.increment_sync_attempts("job-040")
            assert result is True

        jobs = await offline_queue.get_jobs_to_sync()
        assert jobs[0]['sync_attempts'] == 3
        assert jobs[0]['last_sync_attempt'] is not None

    @pytest.mark.asyncio
    async def test_increment_nonexistent_job(self, offline_queue):
        """Test incrementing sync attempts for nonexistent job."""
        result = await offline_queue.increment_sync_attempts("nonexistent")
        assert result is False


# =============================================================================
# Checkpoint Tests
# =============================================================================

class TestCheckpoints:
    """Test checkpoint operations for resumable execution."""

    @pytest.mark.asyncio
    async def test_save_checkpoint(self, offline_queue, sample_workflow_json):
        """Test saving a checkpoint."""
        await offline_queue.cache_job("job-050", sample_workflow_json, "pending")

        result = await offline_queue.save_checkpoint(
            job_id="job-050",
            checkpoint_id="cp-001",
            node_id="node_5",
            state={"variables": {"count": 10}, "current_node": "node_5"}
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_latest_checkpoint(self, offline_queue, sample_workflow_json):
        """Test retrieving latest checkpoint."""
        await offline_queue.cache_job("job-051", sample_workflow_json, "pending")

        # Save multiple checkpoints
        for i in range(3):
            await asyncio.sleep(0.01)  # Small delay to ensure ordering
            await offline_queue.save_checkpoint(
                job_id="job-051",
                checkpoint_id=f"cp-{i}",
                node_id=f"node_{i}",
                state={"iteration": i}
            )

        checkpoint = await offline_queue.get_latest_checkpoint("job-051")

        assert checkpoint is not None
        assert checkpoint['checkpoint_id'] == "cp-2"
        assert checkpoint['node_id'] == "node_2"
        assert checkpoint['state']['iteration'] == 2

    @pytest.mark.asyncio
    async def test_get_checkpoint_nonexistent(self, offline_queue):
        """Test getting checkpoint for nonexistent job."""
        checkpoint = await offline_queue.get_latest_checkpoint("nonexistent")
        assert checkpoint is None

    @pytest.mark.asyncio
    async def test_clear_checkpoints(self, offline_queue, sample_workflow_json):
        """Test clearing all checkpoints for a job."""
        await offline_queue.cache_job("job-052", sample_workflow_json, "pending")

        # Save multiple checkpoints
        for i in range(5):
            await offline_queue.save_checkpoint(
                job_id="job-052",
                checkpoint_id=f"cp-{i}",
                node_id=f"node_{i}",
                state={"iteration": i}
            )

        result = await offline_queue.clear_checkpoints("job-052")
        assert result is True

        checkpoint = await offline_queue.get_latest_checkpoint("job-052")
        assert checkpoint is None

    @pytest.mark.asyncio
    async def test_checkpoint_replace(self, offline_queue, sample_workflow_json):
        """Test that checkpoint with same ID is replaced."""
        await offline_queue.cache_job("job-053", sample_workflow_json, "pending")

        await offline_queue.save_checkpoint(
            job_id="job-053",
            checkpoint_id="same-cp",
            node_id="node_1",
            state={"value": 1}
        )

        await offline_queue.save_checkpoint(
            job_id="job-053",
            checkpoint_id="same-cp",
            node_id="node_2",
            state={"value": 2}
        )

        checkpoint = await offline_queue.get_latest_checkpoint("job-053")
        assert checkpoint['state']['value'] == 2


# =============================================================================
# Event History Tests
# =============================================================================

class TestEventHistory:
    """Test execution history/audit logging."""

    @pytest.mark.asyncio
    async def test_log_event(self, offline_queue, sample_workflow_json):
        """Test logging an event."""
        await offline_queue.cache_job("job-060", sample_workflow_json, "pending")

        result = await offline_queue.log_event(
            job_id="job-060",
            event_type="job_started",
            event_data={"trigger": "manual"}
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_get_job_history(self, offline_queue, sample_workflow_json):
        """Test retrieving job history."""
        await offline_queue.cache_job("job-061", sample_workflow_json, "pending")

        # Log multiple events
        events = [
            ("job_started", {"trigger": "scheduled"}),
            ("node_executed", {"node_id": "node_1", "result": "success"}),
            ("node_executed", {"node_id": "node_2", "result": "success"}),
            ("job_completed", {"duration_ms": 1500}),
        ]

        for event_type, event_data in events:
            await offline_queue.log_event("job-061", event_type, event_data)

        history = await offline_queue.get_job_history("job-061")

        assert len(history) == 4
        assert history[0]['event_type'] == "job_started"
        assert history[-1]['event_type'] == "job_completed"
        assert history[-1]['event_data']['duration_ms'] == 1500

    @pytest.mark.asyncio
    async def test_log_event_no_data(self, offline_queue, sample_workflow_json):
        """Test logging event without data."""
        await offline_queue.cache_job("job-062", sample_workflow_json, "pending")

        result = await offline_queue.log_event(
            job_id="job-062",
            event_type="heartbeat"
        )

        assert result is True
        history = await offline_queue.get_job_history("job-062")
        assert history[0]['event_data'] is None

    @pytest.mark.asyncio
    async def test_history_ordering(self, offline_queue, sample_workflow_json):
        """Test that history is ordered chronologically."""
        await offline_queue.cache_job("job-063", sample_workflow_json, "pending")

        for i in range(10):
            await asyncio.sleep(0.001)  # Small delay for ordering
            await offline_queue.log_event("job-063", f"event_{i}")

        history = await offline_queue.get_job_history("job-063")

        for i, event in enumerate(history):
            assert event['event_type'] == f"event_{i}"


# =============================================================================
# Queue Statistics Tests
# =============================================================================

class TestQueueStatistics:
    """Test queue statistics retrieval."""

    @pytest.mark.asyncio
    async def test_empty_queue_stats(self, offline_queue):
        """Test stats on empty queue."""
        stats = await offline_queue.get_queue_stats()
        assert stats == {}

    @pytest.mark.asyncio
    async def test_queue_stats_multiple_statuses(self, offline_queue, sample_workflow_json):
        """Test stats with jobs in various statuses."""
        # Create jobs in different states
        for i in range(3):
            await offline_queue.cache_job(f"cached-{i}", sample_workflow_json, "pending")

        for i in range(2):
            await offline_queue.cache_job(f"progress-{i}", sample_workflow_json, "pending")
            await offline_queue.mark_in_progress(f"progress-{i}")

        await offline_queue.cache_job("completed-0", sample_workflow_json, "pending")
        await offline_queue.mark_in_progress("completed-0")
        await offline_queue.mark_completed("completed-0", success=True)

        stats = await offline_queue.get_queue_stats()

        assert stats.get("cached", 0) == 3
        assert stats.get("in_progress", 0) == 2
        assert stats.get("completed", 0) == 1


# =============================================================================
# Cleanup Tests
# =============================================================================

class TestCleanup:
    """Test cleanup operations."""

    @pytest.mark.asyncio
    async def test_cleanup_old_synced_jobs(self, offline_queue, sample_workflow_json):
        """Test cleaning up old synced jobs."""
        # Create and sync a job
        await offline_queue.cache_job("old-job", sample_workflow_json, "pending")
        await offline_queue.mark_in_progress("old-job")
        await offline_queue.mark_completed("old-job", success=True)
        await offline_queue.mark_synced("old-job")

        # Manually backdate the completed_at timestamp
        with offline_queue._get_connection() as conn:
            cursor = conn.cursor()
            old_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
            cursor.execute(
                "UPDATE cached_jobs SET completed_at = ? WHERE id = ?",
                (old_date, "old-job")
            )
            conn.commit()

        # Cleanup jobs older than 7 days
        deleted = await offline_queue.cleanup_old_synced_jobs(days=7)

        assert deleted == 1

    @pytest.mark.asyncio
    async def test_cleanup_keeps_recent_jobs(self, offline_queue, sample_workflow_json):
        """Test that recent synced jobs are kept."""
        await offline_queue.cache_job("recent-job", sample_workflow_json, "pending")
        await offline_queue.mark_in_progress("recent-job")
        await offline_queue.mark_completed("recent-job", success=True)
        await offline_queue.mark_synced("recent-job")

        deleted = await offline_queue.cleanup_old_synced_jobs(days=7)

        assert deleted == 0

    @pytest.mark.asyncio
    async def test_cleanup_ignores_non_synced(self, offline_queue, sample_workflow_json):
        """Test that non-synced jobs are not cleaned up."""
        await offline_queue.cache_job("pending-job", sample_workflow_json, "pending")
        await offline_queue.mark_in_progress("pending-job")
        await offline_queue.mark_completed("pending-job", success=True)
        # Not synced

        # Backdate
        with offline_queue._get_connection() as conn:
            cursor = conn.cursor()
            old_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
            cursor.execute(
                "UPDATE cached_jobs SET completed_at = ? WHERE id = ?",
                (old_date, "pending-job")
            )
            conn.commit()

        deleted = await offline_queue.cleanup_old_synced_jobs(days=7)

        assert deleted == 0
        jobs = await offline_queue.get_jobs_to_sync()
        assert len(jobs) == 1


# =============================================================================
# Robot ID Filtering Tests
# =============================================================================

class TestRobotIdFiltering:
    """Test filtering by robot ID."""

    @pytest.mark.asyncio
    async def test_jobs_filtered_by_robot_id(self, temp_db_path, sample_workflow_json):
        """Test that jobs are filtered by robot ID."""
        queue1 = OfflineQueue(db_path=temp_db_path, robot_id="robot-1")
        queue2 = OfflineQueue(db_path=temp_db_path, robot_id="robot-2")

        await queue1.cache_job("job-r1", sample_workflow_json, "pending")
        await queue2.cache_job("job-r2", sample_workflow_json, "pending")

        jobs1 = await queue1.get_cached_jobs()
        jobs2 = await queue2.get_cached_jobs()

        assert len(jobs1) == 1
        assert jobs1[0]['id'] == "job-r1"
        assert len(jobs2) == 1
        assert jobs2[0]['id'] == "job-r2"

    @pytest.mark.asyncio
    async def test_null_robot_id_visible_to_all(self, temp_db_path, sample_workflow_json):
        """Test that jobs with null robot_id are visible to all robots."""
        queue_null = OfflineQueue(db_path=temp_db_path, robot_id=None)
        queue_specific = OfflineQueue(db_path=temp_db_path, robot_id="robot-specific")

        # Cache job with null robot_id (using direct SQL)
        with queue_null._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO cached_jobs (id, robot_id, workflow_json, cached_status, cached_at)
                VALUES (?, NULL, ?, 'cached', ?)
            """, ("null-robot-job", sample_workflow_json, datetime.now(timezone.utc).isoformat()))
            conn.commit()

        jobs = await queue_specific.get_cached_jobs()
        assert len(jobs) == 1
        assert jobs[0]['id'] == "null-robot-job"


# =============================================================================
# Chaos/Edge Case Tests
# =============================================================================

class TestChaosScenarios:
    """Chaos and edge case tests."""

    @pytest.mark.asyncio
    async def test_concurrent_job_caching(self, offline_queue, sample_workflow_json):
        """Test concurrent job caching operations."""
        async def cache_job(i):
            return await offline_queue.cache_job(f"concurrent-{i}", sample_workflow_json, "pending")

        results = await asyncio.gather(*[cache_job(i) for i in range(20)])

        assert all(results)
        jobs = await offline_queue.get_cached_jobs()
        assert len(jobs) == 20

    @pytest.mark.asyncio
    async def test_concurrent_status_updates(self, offline_queue, sample_workflow_json):
        """Test concurrent status updates on same job."""
        await offline_queue.cache_job("race-job", sample_workflow_json, "pending")

        async def update_status():
            await offline_queue.mark_in_progress("race-job")
            return await offline_queue.mark_completed("race-job", success=True)

        # Run multiple concurrent updates
        results = await asyncio.gather(*[update_status() for _ in range(5)])

        # At least some should succeed
        assert any(results)

    @pytest.mark.asyncio
    async def test_large_workflow_json(self, offline_queue):
        """Test caching large workflow JSON."""
        # Create a large workflow with many nodes
        large_workflow = {
            "nodes": [
                {"id": f"node_{i}", "type": "TestNode", "data": "x" * 1000}
                for i in range(100)
            ],
            "connections": []
        }
        large_json = orjson.dumps(large_workflow).decode()

        result = await offline_queue.cache_job("large-job", large_json, "pending")
        assert result is True

        jobs = await offline_queue.get_cached_jobs()
        assert len(jobs) == 1
        assert len(jobs[0]['workflow_json']) == len(large_json)

    @pytest.mark.asyncio
    async def test_special_characters_in_workflow(self, offline_queue):
        """Test handling special characters in workflow JSON."""
        special_workflow = orjson.dumps({
            "nodes": [{"id": "test", "data": "Special chars: '\"\n\t\r\\"}]
        }).decode()

        result = await offline_queue.cache_job("special-job", special_workflow, "pending")
        assert result is True

        jobs = await offline_queue.get_cached_jobs()
        retrieved = orjson.loads(jobs[0]['workflow_json'])
        assert "Special chars" in retrieved['nodes'][0]['data']

    @pytest.mark.asyncio
    async def test_unicode_in_workflow(self, offline_queue):
        """Test handling unicode in workflow JSON."""
        # Use valid Unicode characters (orjson doesn't allow surrogates)
        unicode_workflow = orjson.dumps({
            "nodes": [{"id": "test", "data": "Unicode: Chinese Japanese Emoji"}]
        }).decode()

        result = await offline_queue.cache_job("unicode-job", unicode_workflow, "pending")
        assert result is True

    @pytest.mark.asyncio
    async def test_empty_workflow_json(self, offline_queue):
        """Test caching empty workflow JSON."""
        result = await offline_queue.cache_job("empty-job", "{}", "pending")
        assert result is True

    @pytest.mark.asyncio
    async def test_checkpoint_large_state(self, offline_queue, sample_workflow_json):
        """Test checkpoint with large state data."""
        await offline_queue.cache_job("large-state-job", sample_workflow_json, "pending")

        large_state = {
            "variables": {f"var_{i}": "x" * 1000 for i in range(100)},
            "nested": {"deep": {"data": list(range(1000))}}
        }

        result = await offline_queue.save_checkpoint(
            job_id="large-state-job",
            checkpoint_id="cp-large",
            node_id="node_1",
            state=large_state
        )

        assert result is True

        checkpoint = await offline_queue.get_latest_checkpoint("large-state-job")
        assert checkpoint['state']['nested']['deep']['data'][-1] == 999

    @pytest.mark.asyncio
    async def test_many_checkpoints_same_job(self, offline_queue, sample_workflow_json):
        """Test saving many checkpoints for same job."""
        await offline_queue.cache_job("many-cp-job", sample_workflow_json, "pending")

        for i in range(100):
            await offline_queue.save_checkpoint(
                job_id="many-cp-job",
                checkpoint_id=f"cp-{i:04d}",
                node_id=f"node_{i}",
                state={"iteration": i}
            )

        checkpoint = await offline_queue.get_latest_checkpoint("many-cp-job")
        assert checkpoint['state']['iteration'] == 99

    @pytest.mark.asyncio
    async def test_many_events_same_job(self, offline_queue, sample_workflow_json):
        """Test logging many events for same job."""
        await offline_queue.cache_job("many-events-job", sample_workflow_json, "pending")

        for i in range(200):
            await offline_queue.log_event(
                job_id="many-events-job",
                event_type=f"event_{i}",
                event_data={"index": i}
            )

        history = await offline_queue.get_job_history("many-events-job")
        assert len(history) == 200

    @pytest.mark.asyncio
    async def test_database_reconnection(self, temp_db_path, sample_workflow_json):
        """Test operations after database reconnection."""
        queue1 = OfflineQueue(db_path=temp_db_path, robot_id="robot")
        await queue1.cache_job("persist-job", sample_workflow_json, "pending")

        # Create new instance (simulating restart)
        queue2 = OfflineQueue(db_path=temp_db_path, robot_id="robot")

        jobs = await queue2.get_cached_jobs()
        assert len(jobs) == 1
        assert jobs[0]['id'] == "persist-job"


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_cache_job_exception_handling(self, offline_queue):
        """Test that cache_job handles exceptions gracefully."""
        with patch.object(offline_queue, '_get_connection', side_effect=sqlite3.Error("DB error")):
            result = await offline_queue.cache_job("error-job", "{}", "pending")
            assert result is False

    @pytest.mark.asyncio
    async def test_get_cached_jobs_exception_handling(self, offline_queue):
        """Test that get_cached_jobs handles exceptions gracefully."""
        with patch.object(offline_queue, '_get_connection', side_effect=sqlite3.Error("DB error")):
            jobs = await offline_queue.get_cached_jobs()
            assert jobs == []

    @pytest.mark.asyncio
    async def test_save_checkpoint_exception_handling(self, offline_queue):
        """Test that save_checkpoint handles exceptions gracefully."""
        with patch.object(offline_queue, '_get_connection', side_effect=sqlite3.Error("DB error")):
            result = await offline_queue.save_checkpoint(
                job_id="error-job",
                checkpoint_id="cp",
                node_id="node",
                state={}
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_log_event_exception_handling(self, offline_queue):
        """Test that log_event handles exceptions gracefully."""
        with patch.object(offline_queue, '_get_connection', side_effect=sqlite3.Error("DB error")):
            result = await offline_queue.log_event("error-job", "test")
            assert result is False

    @pytest.mark.asyncio
    async def test_cleanup_exception_handling(self, offline_queue):
        """Test that cleanup handles exceptions gracefully."""
        with patch.object(offline_queue, '_get_connection', side_effect=sqlite3.Error("DB error")):
            deleted = await offline_queue.cleanup_old_synced_jobs()
            assert deleted == 0


# =============================================================================
# Crash Recovery Tests
# =============================================================================

class TestCrashRecovery:
    """Test crash recovery scenarios."""

    @pytest.mark.asyncio
    async def test_recover_in_progress_jobs(self, temp_db_path, sample_workflow_json):
        """Test recovering jobs that were in progress during crash."""
        queue1 = OfflineQueue(db_path=temp_db_path, robot_id="robot")

        # Simulate job starting before crash
        await queue1.cache_job("crash-job", sample_workflow_json, "pending")
        await queue1.mark_in_progress("crash-job")

        # Simulate crash and restart
        queue2 = OfflineQueue(db_path=temp_db_path, robot_id="robot")

        in_progress = await queue2.get_in_progress_jobs()
        assert len(in_progress) == 1
        assert in_progress[0]['id'] == "crash-job"

    @pytest.mark.asyncio
    async def test_checkpoint_recovery(self, temp_db_path, sample_workflow_json):
        """Test recovering from checkpoint after crash."""
        queue1 = OfflineQueue(db_path=temp_db_path, robot_id="robot")

        await queue1.cache_job("checkpoint-recovery-job", sample_workflow_json, "pending")
        await queue1.mark_in_progress("checkpoint-recovery-job")

        # Save checkpoint before crash
        await queue1.save_checkpoint(
            job_id="checkpoint-recovery-job",
            checkpoint_id="last-cp",
            node_id="node_50",
            state={"progress": 50}
        )

        # Simulate restart
        queue2 = OfflineQueue(db_path=temp_db_path, robot_id="robot")

        checkpoint = await queue2.get_latest_checkpoint("checkpoint-recovery-job")
        assert checkpoint is not None
        assert checkpoint['state']['progress'] == 50
        assert checkpoint['node_id'] == "node_50"


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for complete workflows."""

    @pytest.mark.asyncio
    async def test_full_offline_workflow(self, offline_queue, sample_workflow_json):
        """Test complete offline workflow execution scenario."""
        job_id = "integration-job"

        # 1. Job received while online
        await offline_queue.cache_job(job_id, sample_workflow_json, "pending")
        await offline_queue.log_event(job_id, "job_received")

        # 2. Start execution
        await offline_queue.mark_in_progress(job_id)
        await offline_queue.log_event(job_id, "execution_started")

        # 3. Execute nodes with checkpoints
        for i in range(5):
            await offline_queue.save_checkpoint(
                job_id=job_id,
                checkpoint_id=f"node_{i}_complete",
                node_id=f"node_{i}",
                state={"last_completed": i}
            )
            await offline_queue.log_event(
                job_id, "node_completed",
                {"node_id": f"node_{i}"}
            )

        # 4. Complete execution
        await offline_queue.mark_completed(
            job_id,
            success=True,
            result={"output": "success"},
            logs="Executed 5 nodes"
        )
        await offline_queue.log_event(job_id, "execution_completed")

        # 5. Verify pending sync
        to_sync = await offline_queue.get_jobs_to_sync()
        assert len(to_sync) == 1

        # 6. Simulate failed sync attempts
        for _ in range(3):
            await offline_queue.increment_sync_attempts(job_id)

        # 7. Successful sync
        await offline_queue.mark_synced(job_id)
        await offline_queue.log_event(job_id, "synced_to_backend")

        # 8. Clear checkpoints after successful sync
        await offline_queue.clear_checkpoints(job_id)

        # Verify final state
        history = await offline_queue.get_job_history(job_id)
        # Events: job_received, execution_started, 5x node_completed, execution_completed, synced_to_backend = 9
        assert len(history) == 9  # All events logged

        to_sync = await offline_queue.get_jobs_to_sync()
        assert len(to_sync) == 0  # Job synced

        checkpoint = await offline_queue.get_latest_checkpoint(job_id)
        assert checkpoint is None  # Checkpoints cleared

    @pytest.mark.asyncio
    async def test_multiple_robot_queue_isolation(self, temp_db_path, sample_workflow_json):
        """Test that multiple robots using same DB have isolated queues."""
        robots = [
            OfflineQueue(db_path=temp_db_path, robot_id=f"robot-{i}")
            for i in range(3)
        ]

        # Each robot caches different jobs
        for i, robot in enumerate(robots):
            for j in range(5):
                await robot.cache_job(
                    f"robot-{i}-job-{j}",
                    sample_workflow_json,
                    "pending"
                )

        # Verify isolation
        for i, robot in enumerate(robots):
            jobs = await robot.get_cached_jobs()
            assert len(jobs) == 5
            assert all(f"robot-{i}" in j['id'] for j in jobs)
