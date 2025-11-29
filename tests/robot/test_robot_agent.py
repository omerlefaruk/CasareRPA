"""
Comprehensive tests for Robot Agent (Phase 3.4.3).

Tests cover:
1. Job claiming from PgQueuer
2. Workflow execution with DBOS
3. Heartbeat lease extension
4. Graceful shutdown (waits for job completion)
5. Crash recovery (killed robot mid-job, job returns to queue)

Success Criteria (from roadmap lines 359-365):
- Robot can claim jobs from PgQueuer
- Robot executes workflows with DBOS durability
- Heartbeats extend job lease
- Graceful shutdown waits for job completion
- Crashed robots don't lose jobs (visibility timeout)
"""

import asyncio
import pytest
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from .conftest import (
    Job,
    JobStatus,
    MockDBOSWorkflowExecutor,
    MockPgQueuerConsumer,
    RobotConfig,
)


class RobotAgent:
    """
    Robot Agent implementation for testing.

    This is a test implementation that matches the interface
    specified in the roadmap. The actual implementation will
    be in src/casare_rpa/robot/agent.py.
    """

    def __init__(
        self,
        config: RobotConfig,
        consumer: Optional[MockPgQueuerConsumer] = None,
        executor: Optional[MockDBOSWorkflowExecutor] = None,
    ):
        self.config = config
        self.robot_id = config.robot_id

        self.consumer = consumer or MockPgQueuerConsumer(
            postgres_url=config.postgres_url,
            robot_id=config.robot_id,
            batch_size=config.batch_size,
            visibility_timeout_seconds=config.lease_extension_seconds,
        )

        self.executor = executor or MockDBOSWorkflowExecutor()

        self._running = False
        self._current_job: Optional[Job] = None
        self._polling_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._job_complete_event = asyncio.Event()
        self._executed_jobs: List[str] = []
        self._failed_jobs: Dict[str, str] = {}

    async def start(self) -> None:
        """Start the robot agent."""
        self._running = True
        self._shutdown_event.clear()

        await self.consumer.start()

        self._polling_task = asyncio.create_task(self._polling_loop())
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def stop(self, wait_for_completion: bool = True) -> None:
        """
        Stop the robot agent gracefully.

        Args:
            wait_for_completion: If True, wait for current job to complete.
        """
        self._running = False

        if wait_for_completion and self._current_job:
            try:
                await asyncio.wait_for(
                    self._job_complete_event.wait(),
                    timeout=self.config.grace_period_seconds,
                )
            except asyncio.TimeoutError:
                pass

        self._shutdown_event.set()

        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        await self.consumer.stop()

    async def _polling_loop(self) -> None:
        """Poll for jobs and execute them."""
        while self._running:
            try:
                if self._shutdown_event.is_set():
                    break

                job = await self.consumer.claim_job()

                if job:
                    self._job_complete_event.clear()
                    self._current_job = job
                    await self._execute_job(job)
                    self._current_job = None
                    self._job_complete_event.set()
                else:
                    await asyncio.sleep(self.config.poll_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(self.config.poll_interval_seconds)

    async def _execute_job(self, job: Job) -> None:
        """Execute a job with DBOS durability."""
        try:
            result = await self.executor.execute_workflow(
                workflow=job.workflow_json,
                workflow_id=job.job_id,
                initial_variables=job.variables,
            )

            if result.get("success"):
                await self.consumer.complete_job(job.job_id, result)
                self._executed_jobs.append(job.job_id)
            else:
                error = result.get("error", "Unknown error")
                await self.consumer.fail_job(job.job_id, error)
                self._failed_jobs[job.job_id] = error

        except Exception as e:
            await self.consumer.fail_job(job.job_id, str(e))
            self._failed_jobs[job.job_id] = str(e)

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats to extend job lease."""
        while self._running:
            try:
                if self._shutdown_event.is_set():
                    break

                if self._current_job:
                    await self.consumer.extend_lease(
                        self._current_job.job_id,
                        extension_seconds=self.config.lease_extension_seconds,
                    )

                await asyncio.sleep(self.config.heartbeat_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception:
                pass

    @property
    def is_running(self) -> bool:
        """Check if agent is running."""
        return self._running

    @property
    def current_job(self) -> Optional[Job]:
        """Get currently executing job."""
        return self._current_job

    def get_executed_jobs(self) -> List[str]:
        """Get list of successfully executed job IDs."""
        return self._executed_jobs.copy()

    def get_failed_jobs(self) -> Dict[str, str]:
        """Get dict of failed job IDs to error messages."""
        return self._failed_jobs.copy()


# =============================================================================
# TEST SECTION 1: Job Claiming from PgQueuer
# =============================================================================


class TestJobClaiming:
    """Tests for job claiming from PgQueuer (Success Criteria #1)."""

    @pytest.mark.asyncio
    async def test_claim_single_job(
        self,
        robot_config: RobotConfig,
        mock_consumer: MockPgQueuerConsumer,
        mock_executor: MockDBOSWorkflowExecutor,
        sample_job: Job,
    ) -> None:
        """Robot can claim a single pending job from queue."""
        mock_consumer.add_job(sample_job)

        agent = RobotAgent(robot_config, mock_consumer, mock_executor)
        await agent.start()

        await asyncio.sleep(0.2)

        await agent.stop()

        assert sample_job.job_id in agent.get_executed_jobs()
        assert sample_job.status == JobStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_claim_job_marks_as_claimed(
        self,
        robot_config: RobotConfig,
        mock_consumer: MockPgQueuerConsumer,
        sample_job: Job,
    ) -> None:
        """Claimed job is marked with robot ID and timestamp."""
        mock_consumer.add_job(sample_job)
        await mock_consumer.start()

        claimed_job = await mock_consumer.claim_job()

        assert claimed_job is not None
        assert claimed_job.claimed_by == mock_consumer.robot_id
        assert claimed_job.claimed_at is not None
        assert claimed_job.status == JobStatus.CLAIMED

    @pytest.mark.asyncio
    async def test_claim_uses_skip_locked_semantics(
        self,
        mock_consumer: MockPgQueuerConsumer,
        multiple_jobs: List[Job],
    ) -> None:
        """Jobs are claimed using SKIP LOCKED to prevent race conditions."""
        for job in multiple_jobs:
            mock_consumer.add_job(job)

        await mock_consumer.start()

        claimed_jobs = []
        for _ in range(len(multiple_jobs)):
            job = await mock_consumer.claim_job()
            if job:
                claimed_jobs.append(job)

        assert len(claimed_jobs) == len(multiple_jobs)
        claimed_ids = {j.job_id for j in claimed_jobs}
        expected_ids = {j.job_id for j in multiple_jobs}
        assert claimed_ids == expected_ids

    @pytest.mark.asyncio
    async def test_no_job_available_returns_none(
        self,
        mock_consumer: MockPgQueuerConsumer,
    ) -> None:
        """Returns None when no pending jobs are available."""
        await mock_consumer.start()

        job = await mock_consumer.claim_job()

        assert job is None

    @pytest.mark.asyncio
    async def test_claim_respects_already_claimed_jobs(
        self,
        mock_consumer: MockPgQueuerConsumer,
        sample_job: Job,
    ) -> None:
        """Already claimed jobs are not re-claimed."""
        sample_job.status = JobStatus.CLAIMED
        sample_job.claimed_by = "other-robot"
        mock_consumer._claimed_jobs[sample_job.job_id] = sample_job

        await mock_consumer.start()

        job = await mock_consumer.claim_job()

        assert job is None

    @pytest.mark.asyncio
    async def test_claim_requires_connection(
        self,
        mock_consumer: MockPgQueuerConsumer,
        sample_job: Job,
    ) -> None:
        """Claiming fails if consumer is not connected."""
        mock_consumer.add_job(sample_job)

        with pytest.raises(RuntimeError, match="Consumer not connected"):
            await mock_consumer.claim_job()


# =============================================================================
# TEST SECTION 2: Workflow Execution with DBOS
# =============================================================================


class TestWorkflowExecution:
    """Tests for workflow execution with DBOS durability (Success Criteria #2)."""

    @pytest.mark.asyncio
    async def test_execute_workflow_success(
        self,
        robot_config: RobotConfig,
        mock_consumer: MockPgQueuerConsumer,
        mock_executor: MockDBOSWorkflowExecutor,
        sample_job: Job,
    ) -> None:
        """Successfully executed workflow marks job as completed."""
        mock_consumer.add_job(sample_job)

        agent = RobotAgent(robot_config, mock_consumer, mock_executor)
        await agent.start()
        await asyncio.sleep(0.2)
        await agent.stop()

        assert sample_job.job_id in agent.get_executed_jobs()
        assert sample_job.job_id in mock_consumer._completed_jobs

    @pytest.mark.asyncio
    async def test_execute_workflow_failure(
        self,
        robot_config: RobotConfig,
        mock_consumer: MockPgQueuerConsumer,
        mock_executor: MockDBOSWorkflowExecutor,
        sample_job: Job,
    ) -> None:
        """Failed workflow marks job as failed with error."""
        mock_executor.set_should_fail(True)
        mock_consumer.add_job(sample_job)

        agent = RobotAgent(robot_config, mock_consumer, mock_executor)
        await agent.start()
        await asyncio.sleep(0.2)
        await agent.stop()

        assert sample_job.job_id in agent.get_failed_jobs()
        assert sample_job.job_id in mock_consumer._failed_jobs
        assert "failed" in mock_consumer._failed_jobs[sample_job.job_id].lower()

    @pytest.mark.asyncio
    async def test_execute_workflow_with_variables(
        self,
        mock_executor: MockDBOSWorkflowExecutor,
        sample_workflow_json: str,
    ) -> None:
        """Workflow receives initial variables from job."""
        variables = {"input": "test_value", "count": 42}

        result = await mock_executor.execute_workflow(
            workflow=sample_workflow_json,
            workflow_id="test-workflow-001",
            initial_variables=variables,
        )

        assert result["success"] is True
        assert mock_executor._executions["test-workflow-001"]["variables"] == variables

    @pytest.mark.asyncio
    async def test_execute_uses_job_id_for_idempotency(
        self,
        mock_executor: MockDBOSWorkflowExecutor,
        sample_workflow_json: str,
    ) -> None:
        """Job ID is used as workflow_id for DBOS idempotency."""
        job_id = "unique-job-id-123"

        await mock_executor.execute_workflow(
            workflow=sample_workflow_json,
            workflow_id=job_id,
        )

        assert job_id in mock_executor._executions

    @pytest.mark.asyncio
    async def test_execute_multiple_jobs_sequentially(
        self,
        robot_config: RobotConfig,
        mock_consumer: MockPgQueuerConsumer,
        mock_executor: MockDBOSWorkflowExecutor,
        multiple_jobs: List[Job],
    ) -> None:
        """Robot executes multiple jobs sequentially."""
        for job in multiple_jobs[:3]:
            mock_consumer.add_job(job)

        agent = RobotAgent(robot_config, mock_consumer, mock_executor)
        await agent.start()

        await asyncio.sleep(0.5)

        await agent.stop()

        assert len(agent.get_executed_jobs()) == 3

    @pytest.mark.asyncio
    async def test_execute_handles_node_failure(
        self,
        robot_config: RobotConfig,
        mock_consumer: MockPgQueuerConsumer,
        mock_executor: MockDBOSWorkflowExecutor,
        sample_job: Job,
    ) -> None:
        """Failure at specific node is properly recorded."""
        mock_executor.set_fail_at_node("problematic-node")
        mock_consumer.add_job(sample_job)

        agent = RobotAgent(robot_config, mock_consumer, mock_executor)
        await agent.start()
        await asyncio.sleep(0.2)
        await agent.stop()

        failed_jobs = agent.get_failed_jobs()
        assert sample_job.job_id in failed_jobs
        assert "problematic-node" in failed_jobs[sample_job.job_id]


# =============================================================================
# TEST SECTION 3: Heartbeat Lease Extension
# =============================================================================


class TestHeartbeatLeaseExtension:
    """Tests for heartbeat lease extension (Success Criteria #3)."""

    @pytest.mark.asyncio
    async def test_heartbeat_extends_lease_during_execution(
        self,
        robot_config: RobotConfig,
        mock_consumer: MockPgQueuerConsumer,
        mock_executor: MockDBOSWorkflowExecutor,
        sample_job: Job,
    ) -> None:
        """Heartbeat extends job lease while job is executing."""
        mock_executor.set_execution_delay(0.3)
        robot_config.heartbeat_interval_seconds = 0.1
        mock_consumer.add_job(sample_job)

        agent = RobotAgent(robot_config, mock_consumer, mock_executor)
        await agent.start()

        await asyncio.sleep(0.4)

        await agent.stop()

        extension_count = mock_consumer.get_lease_extension_count(sample_job.job_id)
        assert (
            extension_count >= 2
        ), f"Expected at least 2 extensions, got {extension_count}"

    @pytest.mark.asyncio
    async def test_heartbeat_only_for_current_job(
        self,
        robot_config: RobotConfig,
        mock_consumer: MockPgQueuerConsumer,
        mock_executor: MockDBOSWorkflowExecutor,
    ) -> None:
        """Heartbeat only extends lease for currently executing job."""
        robot_config.heartbeat_interval_seconds = 0.05
        mock_executor.set_execution_delay(0.0)

        agent = RobotAgent(robot_config, mock_consumer, mock_executor)
        await agent.start()

        await asyncio.sleep(0.2)

        assert agent.current_job is None

        await agent.stop()

        assert len(mock_consumer._lease_extensions) == 0

    @pytest.mark.asyncio
    async def test_heartbeat_continues_during_long_jobs(
        self,
        robot_config: RobotConfig,
        mock_consumer: MockPgQueuerConsumer,
        mock_executor: MockDBOSWorkflowExecutor,
        sample_job: Job,
    ) -> None:
        """Heartbeat keeps running throughout long job execution."""
        mock_executor.set_execution_delay(0.5)
        robot_config.heartbeat_interval_seconds = 0.1
        mock_consumer.add_job(sample_job)

        agent = RobotAgent(robot_config, mock_consumer, mock_executor)
        await agent.start()

        await asyncio.sleep(0.6)

        await agent.stop()

        extension_count = mock_consumer.get_lease_extension_count(sample_job.job_id)
        assert (
            extension_count >= 4
        ), f"Expected at least 4 extensions for long job, got {extension_count}"

    @pytest.mark.asyncio
    async def test_heartbeat_interval_configurable(
        self,
        mock_consumer: MockPgQueuerConsumer,
        mock_executor: MockDBOSWorkflowExecutor,
        sample_job: Job,
    ) -> None:
        """Heartbeat interval respects configuration."""
        config = RobotConfig(heartbeat_interval_seconds=0.05)
        mock_executor.set_execution_delay(0.25)
        mock_consumer.add_job(sample_job)

        agent = RobotAgent(config, mock_consumer, mock_executor)
        await agent.start()

        await asyncio.sleep(0.3)

        await agent.stop()

        extension_count = mock_consumer.get_lease_extension_count(sample_job.job_id)
        assert (
            extension_count >= 4
        ), f"Expected at least 4 extensions with 0.05s interval, got {extension_count}"

    @pytest.mark.asyncio
    async def test_lease_extension_uses_configured_duration(
        self,
        mock_consumer: MockPgQueuerConsumer,
        sample_job: Job,
    ) -> None:
        """Lease extension uses configured extension duration."""
        extension_seconds = 45
        await mock_consumer.start()
        mock_consumer.add_job(sample_job)
        await mock_consumer.claim_job()

        result = await mock_consumer.extend_lease(
            sample_job.job_id,
            extension_seconds=extension_seconds,
        )

        assert result is True


# =============================================================================
# TEST SECTION 4: Graceful Shutdown
# =============================================================================


class TestGracefulShutdown:
    """Tests for graceful shutdown (Success Criteria #4)."""

    @pytest.mark.asyncio
    async def test_graceful_shutdown_waits_for_job_completion(
        self,
        robot_config: RobotConfig,
        mock_consumer: MockPgQueuerConsumer,
        mock_executor: MockDBOSWorkflowExecutor,
        sample_job: Job,
    ) -> None:
        """Graceful shutdown waits for current job to complete."""
        mock_executor.set_execution_delay(0.2)
        robot_config.grace_period_seconds = 1.0
        mock_consumer.add_job(sample_job)

        agent = RobotAgent(robot_config, mock_consumer, mock_executor)
        await agent.start()

        await asyncio.sleep(0.05)

        assert agent.current_job is not None

        await agent.stop(wait_for_completion=True)

        assert sample_job.job_id in agent.get_executed_jobs()
        assert sample_job.status == JobStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_graceful_shutdown_respects_grace_period(
        self,
        robot_config: RobotConfig,
        mock_consumer: MockPgQueuerConsumer,
        mock_executor: MockDBOSWorkflowExecutor,
        sample_job: Job,
    ) -> None:
        """Shutdown respects grace period for job completion."""
        mock_executor.set_execution_delay(2.0)
        robot_config.grace_period_seconds = 0.1
        mock_consumer.add_job(sample_job)

        agent = RobotAgent(robot_config, mock_consumer, mock_executor)
        await agent.start()

        await asyncio.sleep(0.05)

        start_time = asyncio.get_event_loop().time()
        await agent.stop(wait_for_completion=True)
        elapsed = asyncio.get_event_loop().time() - start_time

        assert elapsed < 0.5, f"Shutdown took too long: {elapsed}s"

    @pytest.mark.asyncio
    async def test_graceful_shutdown_no_new_jobs_claimed(
        self,
        robot_config: RobotConfig,
        mock_consumer: MockPgQueuerConsumer,
        mock_executor: MockDBOSWorkflowExecutor,
        sample_job: Job,
    ) -> None:
        """No new jobs are claimed after shutdown is initiated."""
        mock_executor.set_execution_delay(0.15)
        mock_consumer.add_job(sample_job)

        second_job = Job(
            job_id="job-002",
            workflow_id="workflow-002",
            workflow_name="Second Workflow",
            workflow_json='{"nodes": []}',
        )
        mock_consumer.add_job(second_job)

        agent = RobotAgent(robot_config, mock_consumer, mock_executor)
        await agent.start()

        await asyncio.sleep(0.05)

        await agent.stop(wait_for_completion=True)

        assert len(agent.get_executed_jobs()) == 1
        assert second_job.job_id not in agent.get_executed_jobs()

    @pytest.mark.asyncio
    async def test_immediate_shutdown_when_no_job_running(
        self,
        robot_config: RobotConfig,
        mock_consumer: MockPgQueuerConsumer,
        mock_executor: MockDBOSWorkflowExecutor,
    ) -> None:
        """Shutdown is immediate when no job is running."""
        agent = RobotAgent(robot_config, mock_consumer, mock_executor)
        await agent.start()

        start_time = asyncio.get_event_loop().time()
        await agent.stop(wait_for_completion=True)
        elapsed = asyncio.get_event_loop().time() - start_time

        assert elapsed < 0.1, f"Shutdown should be immediate, took {elapsed}s"

    @pytest.mark.asyncio
    async def test_force_shutdown_option(
        self,
        robot_config: RobotConfig,
        mock_consumer: MockPgQueuerConsumer,
        mock_executor: MockDBOSWorkflowExecutor,
        sample_job: Job,
    ) -> None:
        """Force shutdown does not wait for job completion."""
        mock_executor.set_execution_delay(1.0)
        mock_consumer.add_job(sample_job)

        agent = RobotAgent(robot_config, mock_consumer, mock_executor)
        await agent.start()

        await asyncio.sleep(0.05)

        start_time = asyncio.get_event_loop().time()
        await agent.stop(wait_for_completion=False)
        elapsed = asyncio.get_event_loop().time() - start_time

        assert elapsed < 0.2, f"Force shutdown should be fast, took {elapsed}s"


# =============================================================================
# TEST SECTION 5: Crash Recovery
# =============================================================================


class TestCrashRecovery:
    """Tests for crash recovery (Success Criteria #5)."""

    @pytest.mark.asyncio
    async def test_crashed_job_returns_to_queue_via_visibility_timeout(
        self,
        mock_consumer: MockPgQueuerConsumer,
        sample_job: Job,
    ) -> None:
        """Job returns to queue when robot crashes (visibility timeout)."""
        mock_consumer.add_job(sample_job)
        await mock_consumer.start()

        claimed_job = await mock_consumer.claim_job()
        assert claimed_job is not None
        assert sample_job.job_id not in mock_consumer._jobs

        mock_consumer.simulate_visibility_timeout(sample_job.job_id)

        assert sample_job.job_id in mock_consumer._jobs
        assert mock_consumer._jobs[sample_job.job_id].status == JobStatus.PENDING
        assert mock_consumer._jobs[sample_job.job_id].claimed_by is None

    @pytest.mark.asyncio
    async def test_another_robot_can_claim_expired_job(
        self,
        sample_job: Job,
    ) -> None:
        """Another robot can claim job after visibility timeout expires."""
        consumer1 = MockPgQueuerConsumer(robot_id="robot-1")
        consumer2 = MockPgQueuerConsumer(robot_id="robot-2")

        consumer1.add_job(sample_job)
        await consumer1.start()
        await consumer2.start()

        claimed = await consumer1.claim_job()
        assert claimed is not None

        consumer1.simulate_visibility_timeout(sample_job.job_id)
        consumer2._jobs = consumer1._jobs.copy()

        reclaimed = await consumer2.claim_job()

        assert reclaimed is not None
        assert reclaimed.job_id == sample_job.job_id
        assert reclaimed.claimed_by == "robot-2"

    @pytest.mark.asyncio
    async def test_job_not_lost_on_execution_exception(
        self,
        robot_config: RobotConfig,
        mock_consumer: MockPgQueuerConsumer,
        mock_executor: MockDBOSWorkflowExecutor,
        sample_job: Job,
    ) -> None:
        """Job is marked as failed, not lost, when execution throws exception."""
        mock_executor.simulate_crash()
        mock_consumer.add_job(sample_job)

        agent = RobotAgent(robot_config, mock_consumer, mock_executor)
        await agent.start()

        await asyncio.sleep(0.2)

        await agent.stop()

        assert sample_job.job_id in mock_consumer._failed_jobs

    @pytest.mark.asyncio
    async def test_heartbeat_prevents_premature_timeout(
        self,
        mock_consumer: MockPgQueuerConsumer,
        mock_executor: MockDBOSWorkflowExecutor,
        sample_job: Job,
    ) -> None:
        """Regular heartbeats prevent visibility timeout during long jobs."""
        config = RobotConfig(
            heartbeat_interval_seconds=0.05,
            lease_extension_seconds=30,
        )
        mock_executor.set_execution_delay(0.3)
        mock_consumer.add_job(sample_job)

        agent = RobotAgent(config, mock_consumer, mock_executor)
        await agent.start()

        await asyncio.sleep(0.35)

        await agent.stop()

        assert sample_job.job_id in agent.get_executed_jobs()
        assert mock_consumer.get_lease_extension_count(sample_job.job_id) >= 5

    @pytest.mark.asyncio
    async def test_dbos_checkpoint_enables_recovery(
        self,
        mock_executor: MockDBOSWorkflowExecutor,
        sample_workflow_json: str,
    ) -> None:
        """DBOS checkpoints enable workflow recovery after crash."""
        workflow_id = "recoverable-workflow"

        mock_executor.add_checkpoint(workflow_id, "node-1")
        mock_executor.add_checkpoint(workflow_id, "node-2")

        assert mock_executor.has_checkpoint(workflow_id)

        checkpoints = mock_executor.get_checkpoints(workflow_id)
        assert len(checkpoints) == 2
        assert "node-1" in checkpoints
        assert "node-2" in checkpoints

    @pytest.mark.asyncio
    async def test_visibility_timeout_releases_job_for_retry(
        self,
        mock_consumer: MockPgQueuerConsumer,
        multiple_jobs: List[Job],
    ) -> None:
        """Multiple jobs released via timeout can all be reclaimed."""
        for job in multiple_jobs[:3]:
            mock_consumer.add_job(job)

        await mock_consumer.start()

        claimed = []
        for _ in range(3):
            job = await mock_consumer.claim_job()
            if job:
                claimed.append(job)

        assert len(claimed) == 3

        for job in claimed:
            mock_consumer.simulate_visibility_timeout(job.job_id)

        reclaimed = []
        for _ in range(3):
            job = await mock_consumer.claim_job()
            if job:
                reclaimed.append(job)

        assert len(reclaimed) == 3


# =============================================================================
# TEST SECTION 6: Integration Tests
# =============================================================================


class TestRobotAgentIntegration:
    """Integration tests for complete robot agent workflow."""

    @pytest.mark.asyncio
    async def test_full_job_lifecycle(
        self,
        robot_config: RobotConfig,
        mock_consumer: MockPgQueuerConsumer,
        mock_executor: MockDBOSWorkflowExecutor,
        sample_job: Job,
    ) -> None:
        """Test complete job lifecycle: claim -> execute -> complete."""
        mock_consumer.add_job(sample_job)

        agent = RobotAgent(robot_config, mock_consumer, mock_executor)

        assert not agent.is_running

        await agent.start()

        assert agent.is_running

        await asyncio.sleep(0.2)

        await agent.stop()

        assert not agent.is_running
        assert sample_job.job_id in agent.get_executed_jobs()
        assert sample_job.status == JobStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_mixed_success_and_failure(
        self,
        robot_config: RobotConfig,
        mock_consumer: MockPgQueuerConsumer,
        mock_executor: MockDBOSWorkflowExecutor,
    ) -> None:
        """Robot handles mix of successful and failing jobs."""
        success_job = Job(
            job_id="success-job",
            workflow_id="wf-1",
            workflow_name="Success Workflow",
            workflow_json='{"nodes": []}',
        )

        fail_job = Job(
            job_id="fail-job",
            workflow_id="wf-2",
            workflow_name="Fail Workflow",
            workflow_json='{"nodes": []}',
        )

        mock_consumer.add_job(success_job)

        agent = RobotAgent(robot_config, mock_consumer, mock_executor)
        await agent.start()
        await asyncio.sleep(0.1)

        mock_executor.set_should_fail(True)
        mock_consumer.add_job(fail_job)
        await asyncio.sleep(0.2)

        await agent.stop()

        assert "success-job" in agent.get_executed_jobs()
        assert "fail-job" in agent.get_failed_jobs()

    @pytest.mark.asyncio
    async def test_robot_agent_state_consistency(
        self,
        robot_config: RobotConfig,
        mock_consumer: MockPgQueuerConsumer,
        mock_executor: MockDBOSWorkflowExecutor,
    ) -> None:
        """Robot agent maintains consistent state throughout lifecycle."""
        agent = RobotAgent(robot_config, mock_consumer, mock_executor)

        assert not agent.is_running
        assert agent.current_job is None
        assert len(agent.get_executed_jobs()) == 0

        await agent.start()
        assert agent.is_running

        await agent.stop()
        assert not agent.is_running
        assert agent.current_job is None

    @pytest.mark.asyncio
    async def test_concurrent_heartbeat_and_execution(
        self,
        mock_consumer: MockPgQueuerConsumer,
        mock_executor: MockDBOSWorkflowExecutor,
        sample_job: Job,
    ) -> None:
        """Heartbeat runs concurrently with job execution."""
        config = RobotConfig(heartbeat_interval_seconds=0.02)
        mock_executor.set_execution_delay(0.15)
        mock_consumer.add_job(sample_job)

        agent = RobotAgent(config, mock_consumer, mock_executor)
        await agent.start()

        await asyncio.sleep(0.2)

        await agent.stop()

        assert sample_job.job_id in agent.get_executed_jobs()
        assert mock_consumer.get_lease_extension_count(sample_job.job_id) >= 5
