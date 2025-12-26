"""
Agent scheduler for dependency-aware parallel execution.

Creates optimal execution schedules from decomposition results.
"""

from dataclasses import dataclass, field
from typing import Any

from casare_rpa.domain.entities.task_decomposition import (
    DecompositionResult,
    Subtask,
)


@dataclass
class ScheduledPhase:
    """A phase of execution with subtasks to run."""

    phase_index: int
    subtask_ids: list[str]
    can_run_parallel: bool = True
    estimated_duration_ms: int = 0
    dependencies_met: bool = True


@dataclass
class Schedule:
    """Complete execution schedule from decomposition."""

    original_task: str
    phases: list[ScheduledPhase]
    total_phases: int = 0
    estimated_duration_ms: int = 0
    parallel_phases: int = 0
    sequential_phases: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentScheduler:
    """
    Creates execution schedules from decomposition results.

    Optimizes for parallel execution while respecting dependencies.
    """

    def __init__(self) -> None:
        self._default_subtask_duration_ms = 5 * 60 * 1000  # 5 minutes

    def create_schedule(self, decomposition: DecompositionResult) -> Schedule:
        """
        Create an execution schedule from decomposition result.

        Args:
            decomposition: The decomposition result to schedule

        Returns:
            Schedule with optimized phases
        """
        phases = []
        parallel_count = 0
        sequential_count = 0
        total_duration = 0

        for i, group in enumerate(decomposition.parallel_groups):
            subtasks = [s for s in decomposition.subtasks if s.id in group.subtask_ids]
            phase_duration = self._estimate_phase_duration(subtasks, group.can_parallel_execute)

            phase = ScheduledPhase(
                phase_index=i,
                subtask_ids=group.subtask_ids,
                can_run_parallel=group.can_parallel_execute,
                estimated_duration_ms=phase_duration,
            )
            phases.append(phase)

            total_duration += phase_duration
            if group.can_parallel_execute:
                parallel_count += 1
            else:
                sequential_count += 1

        return Schedule(
            original_task=decomposition.original_task,
            phases=phases,
            total_phases=len(phases),
            estimated_duration_ms=total_duration,
            parallel_phases=parallel_count,
            sequential_phases=sequential_count,
            metadata={
                "estimated_savings_ms": decomposition.estimated_savings_ms,
                "total_tokens": decomposition.total_estimated_tokens,
            },
        )

    def _estimate_phase_duration(self, subtasks: list[Subtask], can_parallel: bool) -> int:
        """Estimate duration of a phase based on subtasks."""
        if not subtasks:
            return 0

        if can_parallel:
            # Parallel phase: duration is max of subtasks (they run simultaneously)
            return max(s.estimated_tokens * 0.1 for s in subtasks)  # Rough token-to-time conversion
        else:
            # Sequential phase: sum of all subtask durations
            return sum(s.estimated_tokens * 0.1 for s in subtasks)

    def get_subtasks_for_phase(
        self,
        phase: ScheduledPhase,
        decomposition: DecompositionResult,
    ) -> list[Subtask]:
        """Get subtask objects for a given phase."""
        subtasks_by_id = {s.id: s for s in decomposition.subtasks}
        return [subtasks_by_id[sid] for sid in phase.subtask_ids if sid in subtasks_by_id]

    def can_proceed_to_phase(
        self,
        phase: ScheduledPhase,
        completed_subtasks: set[str],
        decomposition: DecompositionResult,
    ) -> bool:
        """Check if all dependencies for a phase are met."""
        subtasks = self.get_subtasks_for_phase(phase, decomposition)

        for subtask in subtasks:
            for dep_id in subtask.dependencies:
                if dep_id not in completed_subtasks:
                    return False

        return True

    def get_ready_phases(
        self,
        schedule: Schedule,
        completed_subtasks: set[str],
        decomposition: DecompositionResult,
    ) -> list[ScheduledPhase]:
        """Get all phases whose dependencies are met."""
        ready = []

        for phase in schedule.phases:
            if self.can_proceed_to_phase(phase, completed_subtasks, decomposition):
                ready.append(phase)

        return ready

    def estimate_remaining_time(
        self,
        schedule: Schedule,
        completed_phases: set[int],
    ) -> int:
        """Estimate remaining time for incomplete phases."""
        remaining = 0

        for phase in schedule.phases:
            if phase.phase_index not in completed_phases:
                remaining += phase.estimated_duration_ms

        return remaining
