"""
Parallel agent executor for decomposed task execution.

Coordinates the execution of parallel agents based on decomposition
results and schedules.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Callable

from loguru import logger

from casare_rpa.domain.entities.chain import AgentType
from casare_rpa.domain.entities.task_decomposition import (
    DecompositionExecutionResult,
    DecompositionResult,
    Subtask,
    SubtaskResult,
    SubtaskStatus,
)
from casare_rpa.domain.services.agent_scheduler import AgentScheduler, Schedule
from casare_rpa.domain.services.decomposition_engine import DecompositionEngine
from casare_rpa.domain.services.task_analyzer import TaskAnalyzer


@dataclass
class ExecutorConfig:
    """Configuration for parallel agent executor."""

    fail_fast: bool = True
    max_parallel: int = 5
    timeout_per_subtask: int = 300
    total_timeout: int = 3600
    collect_metrics: bool = True
    dry_run: bool = False
    enable_parallel: bool = True


@dataclass
class AgentLaunchContext:
    """Context for launching an agent."""

    agent_type: AgentType
    prompt: str
    subtask_id: str
    phase_index: int
    timeout_seconds: int


class ParallelAgentExecutor:
    """
    Executes decomposed tasks with parallel scheduling.

    Coordinates with agent orchestrator to run subtasks,
    collects results, and handles errors.
    """

    def __init__(
        self,
        agent_launcher: Callable[[AgentLaunchContext], Any] | None = None,
        engine: DecompositionEngine | None = None,
        scheduler: AgentScheduler | None = None,
    ) -> None:
        """
        Initialize the executor.

        Args:
            agent_launcher: Function to launch an agent (takes AgentLaunchContext, returns awaitable)
            engine: Decomposition engine to use
            scheduler: Agent scheduler to use
        """
        self._agent_launcher = agent_launcher
        self._engine = engine or DecompositionEngine(TaskAnalyzer())
        self._scheduler = scheduler or AgentScheduler()
        self._results: dict[str, SubtaskResult] = {}

    def set_agent_launcher(self, launcher: Callable[[AgentLaunchContext], Any]) -> None:
        """Set the agent launcher function."""
        self._agent_launcher = launcher

    async def execute(
        self,
        task_description: str,
        config: ExecutorConfig | None = None,
        context: dict[str, Any] | None = None,
    ) -> DecompositionExecutionResult:
        """
        Execute a decomposed task.

        Args:
            task_description: The task to decompose and execute
            config: Execution configuration
            context: Additional context for decomposition

        Returns:
            DecompositionExecutionResult with all subtask results
        """
        config = config or ExecutorConfig()

        if config.dry_run:
            return await self._execute_dry_run(task_description, context)

        start_time = time.time()

        # Phase 1: Decompose
        logger.info(f"Decomposing task: {task_description[:100]}...")
        decomposition = self._engine.decompose(task_description, context)

        logger.info(
            f"Decomposed into {len(decomposition.subtasks)} subtasks, "
            f"{len(decomposition.parallel_groups)} parallel groups"
        )

        # Phase 2: Create schedule
        schedule = self._scheduler.create_schedule(decomposition)

        logger.info(
            f"Schedule: {schedule.total_phases} phases, "
            f"{schedule.parallel_phases} parallel, "
            f"{schedule.sequential_phases} sequential"
        )

        # Phase 3: Execute by schedule
        completed_subtasks: set[str] = set()
        phases_executed = 0

        for phase in schedule.phases:
            logger.info(
                f"Executing phase {phase.phase_index + 1}/{schedule.total_phases} "
                f"({'parallel' if phase.can_run_parallel else 'sequential'})"
            )

            # Get subtasks for this phase
            phase_subtasks = [s for s in decomposition.subtasks if s.id in phase.subtask_ids]

            # Check if we can proceed
            if not self._scheduler.can_proceed_to_phase(phase, completed_subtasks, decomposition):
                logger.warning(f"Phase {phase.phase_index} dependencies not met, skipping")
                continue

            # Execute phase
            phase_results = await self._execute_phase(
                phase_subtasks,
                phase,
                config,
            )

            # Update completed subtasks
            for result in phase_results:
                if result.success:
                    completed_subtasks.add(result.subtask_id)

            # Check for failures
            if config.fail_fast:
                for result in phase_results:
                    if not result.success:
                        logger.error(f"Subtask {result.subtask_id} failed, aborting (fail_fast)")
                        return self._build_result(
                            task_description,
                            start_time,
                            len(decomposition.parallel_groups),
                            phases_executed + 1,
                            decomposition.estimated_savings_ms,
                            status="partial",
                        )

            phases_executed += 1

        # Phase 4: Build result
        return self._build_result(
            task_description,
            start_time,
            len(decomposition.parallel_groups),
            phases_executed,
            decomposition.estimated_savings_ms,
            status="completed",
        )

    async def _execute_dry_run(
        self,
        task_description: str,
        context: dict[str, Any] | None,
    ) -> DecompositionExecutionResult:
        """Execute in dry-run mode (no actual agent execution)."""
        decomposition = self._engine.decompose(task_description, context)
        schedule = self._scheduler.create_schedule(decomposition)

        logger.info("[DRY RUN] Execution plan:")
        for i, phase in enumerate(schedule.phases):
            subtasks = [s for s in decomposition.subtasks if s.id in phase.subtask_ids]
            agent_names = [s.agent_type.value for s in subtasks]
            logger.info(
                f"  Phase {i + 1}: {', '.join(agent_names)} "
                f"({'parallel' if phase.can_run_parallel else 'sequential'})"
            )

        return DecompositionExecutionResult(
            original_task=task_description,
            subtask_results={},
            total_time_ms=0,
            total_tokens=0,
            parallel_groups_executed=len(decomposition.parallel_groups),
            sequential_phases=len(decomposition.parallel_groups),
            phases_executed=0,
            status="dry_run",
            estimated_savings_ms=decomposition.estimated_savings_ms,
        )

    async def _execute_phase(
        self,
        subtasks: list[Subtask],
        phase,
        config: ExecutorConfig,
    ) -> list[SubtaskResult]:
        """Execute a single phase of subtasks."""
        if not config.enable_parallel or not phase.can_run_parallel:
            # Sequential execution
            results = []
            for subtask in subtasks:
                result = await self._execute_subtask(subtask, config)
                results.append(result)
            return results

        # Parallel execution
        tasks = [self._execute_subtask(s, config) for s in subtasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    SubtaskResult(
                        subtask_id=subtasks[i].id,
                        success=False,
                        agent_type=subtasks[i].agent_type,
                        error_message=str(result),
                        status=SubtaskStatus.FAILED,
                    )
                )
            else:
                processed_results.append(result)

        return processed_results

    async def _execute_subtask(
        self,
        subtask: Subtask,
        config: ExecutorConfig,
    ) -> SubtaskResult:
        """Execute a single subtask."""
        logger.info(f"Executing subtask {subtask.id}: {subtask.title}")

        start = time.time()

        try:
            if self._agent_launcher is None:
                # Simulated execution for testing
                await asyncio.sleep(0.1)
                result = SubtaskResult(
                    subtask_id=subtask.id,
                    success=True,
                    agent_type=subtask.agent_type,
                    execution_time_ms=int((time.time() - start) * 1000),
                    output=f"Simulated completion of {subtask.title}",
                    status=SubtaskStatus.COMPLETED,
                )
            else:
                # Real agent execution
                launch_context = AgentLaunchContext(
                    agent_type=subtask.agent_type,
                    prompt=self._build_prompt(subtask),
                    subtask_id=subtask.id,
                    phase_index=0,
                    timeout_seconds=subtask.timeout_seconds,
                )

                agent_result = await self._agent_launcher(launch_context)

                execution_time_ms = int((time.time() - start) * 1000)

                result = SubtaskResult(
                    subtask_id=subtask.id,
                    success=agent_result.success if hasattr(agent_result, "success") else True,
                    agent_type=subtask.agent_type,
                    execution_time_ms=execution_time_ms,
                    data=agent_result.data if hasattr(agent_result, "data") else {},
                    error_message=agent_result.error_message
                    if hasattr(agent_result, "error_message")
                    else None,
                    output=str(agent_result),
                    status=SubtaskStatus.COMPLETED,
                )

        except TimeoutError:
            logger.error(f"Subtask {subtask.id} timed out")
            result = SubtaskResult(
                subtask_id=subtask.id,
                success=False,
                agent_type=subtask.agent_type,
                execution_time_ms=int((time.time() - start) * 1000),
                error_message=f"Timeout after {subtask.timeout_seconds}s",
                status=SubtaskStatus.FAILED,
            )
        except Exception as e:
            logger.error(f"Subtask {subtask.id} failed: {e}")
            result = SubtaskResult(
                subtask_id=subtask.id,
                success=False,
                agent_type=subtask.agent_type,
                execution_time_ms=int((time.time() - start) * 1000),
                error_message=str(e),
                status=SubtaskStatus.FAILED,
            )

        self._results[subtask.id] = result
        return result

    def _build_prompt(self, subtask: Subtask) -> str:
        """Build prompt for agent from subtask."""
        lines = [
            f"# Task: {subtask.title}",
            "",
            subtask.description,
            "",
        ]

        if subtask.metadata.get("layer"):
            lines.append(f"## Layer: {subtask.metadata['layer']}")

        return "\n".join(lines)

    def _build_result(
        self,
        original_task: str,
        start_time: float,
        total_groups: int,
        phases_executed: int,
        estimated_savings: int,
        status: str,
    ) -> DecompositionExecutionResult:
        """Build final execution result."""
        total_time_ms = int((time.time() - start_time) * 1000)
        total_tokens = sum(r.tokens_used for r in self._results.values())

        return DecompositionExecutionResult(
            original_task=original_task,
            subtask_results=self._results.copy(),
            total_time_ms=total_time_ms,
            total_tokens=total_tokens,
            parallel_groups_executed=phases_executed,
            sequential_phases=total_groups,
            phases_executed=phases_executed,
            status=status,
            estimated_savings_ms=estimated_savings,
        )

    def get_decomposition_only(
        self,
        task_description: str,
        context: dict[str, Any] | None = None,
    ) -> DecompositionResult:
        """
        Get only the decomposition without executing.

        Args:
            task_description: Task to decompose
            context: Optional context

        Returns:
            DecompositionResult
        """
        return self._engine.decompose(task_description, context)

    def get_schedule_only(
        self,
        task_description: str,
        context: dict[str, Any] | None = None,
    ) -> Schedule:
        """
        Get only the schedule without executing.

        Args:
            task_description: Task to schedule
            context: Optional context

        Returns:
            Schedule
        """
        decomposition = self._engine.decompose(task_description, context)
        return self._scheduler.create_schedule(decomposition)
