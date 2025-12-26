"""
Decomposition engine for building dependency graphs and parallel groups.

Analyzes work items from TaskAnalyzer and builds optimized execution plans.
"""

import time
from collections import defaultdict
from typing import Any

from casare_rpa.domain.entities.chain import AgentType
from casare_rpa.domain.entities.task_decomposition import (
    DecompositionResult,
    ParallelGroup,
    ResourceRequest,
    ResourceType,
    Subtask,
    SubtaskPriority,
)
from casare_rpa.domain.services.task_analyzer import TaskAnalyzer, WorkItem


class DecompositionEngine:
    """
    Decomposes tasks into subtasks with dependency analysis.

    Builds a dependency graph and identifies parallelizable groups.
    """

    # Agent type dependencies (which must come before others)
    DEPENDENCY_RULES: dict[AgentType, set[AgentType]] = {
        AgentType.EXPLORE: set(),
        AgentType.RESEARCHER: {AgentType.EXPLORE},
        AgentType.ARCHITECT: {AgentType.EXPLORE, AgentType.RESEARCHER},
        AgentType.BUILDER: {AgentType.ARCHITECT},
        AgentType.UI: {AgentType.ARCHITECT},
        AgentType.INTEGRATIONS: {AgentType.ARCHITECT},
        AgentType.REFACTOR: {AgentType.ARCHITECT},
        AgentType.QUALITY: {AgentType.BUILDER, AgentType.UI, AgentType.INTEGRATIONS},
        AgentType.DOCS: {AgentType.ARCHITECT},
        AgentType.REVIEWER: {AgentType.QUALITY, AgentType.DOCS},
    }

    # Parallel compatibility matrix
    PARALLEL_COMPATIBILITY: dict[AgentType, set[AgentType]] = {
        AgentType.EXPLORE: {AgentType.EXPLORE, AgentType.RESEARCHER, AgentType.DOCS},
        AgentType.BUILDER: {AgentType.UI, AgentType.INTEGRATIONS},
        AgentType.UI: {AgentType.INTEGRATIONS},
        AgentType.QUALITY: {AgentType.DOCS},
    }

    # Agent resource needs
    RESOURCE_NEEDS: dict[AgentType, ResourceRequest] = {
        AgentType.BUILDER: ResourceRequest(ResourceType.NONE),
        AgentType.UI: ResourceRequest(ResourceType.NONE),
        AgentType.INTEGRATIONS: ResourceRequest(ResourceType.HTTP_CLIENT),
        AgentType.QUALITY: ResourceRequest(ResourceType.NONE),
    }

    def __init__(self, analyzer: TaskAnalyzer | None = None) -> None:
        self.analyzer = analyzer or TaskAnalyzer()

    def decompose(
        self,
        task_description: str,
        context: dict[str, Any] | None = None,
    ) -> DecompositionResult:
        """
        Decompose a task into subtasks.

        Args:
            task_description: The original task
            context: Additional context (layer, scope, etc.)

        Returns:
            DecompositionResult with subtasks and parallel groups
        """
        start_time = time.time()

        # Analyze task into work items
        work_items = self.analyzer.analyze(task_description, context)

        # Create subtasks
        subtasks = self._create_subtasks(work_items, context or {})

        # Build dependency graph
        dependency_graph = self._build_dependency_graph(subtasks)

        # Identify parallel groups
        parallel_groups = self._identify_parallel_groups(subtasks, dependency_graph)

        # Calculate totals
        total_tokens = sum(s.estimated_tokens for s in subtasks)
        estimated_savings = self._calculate_savings(parallel_groups)

        return DecompositionResult(
            original_task=task_description,
            subtasks=subtasks,
            dependency_graph=dependency_graph,
            parallel_groups=parallel_groups,
            total_estimated_tokens=total_tokens,
            estimated_savings_ms=estimated_savings,
            metadata={
                "context": context or {},
                "decomposition_time_ms": int((time.time() - start_time) * 1000),
            },
        )

    def _create_subtasks(
        self,
        work_items: list[WorkItem],
        context: dict[str, Any],
    ) -> list[Subtask]:
        """Create Subtask entities from work items."""
        subtasks = []

        for i, item in enumerate(work_items):
            priority = self._determine_priority(item, i, len(work_items))
            resource_needs = self.RESOURCE_NEEDS.get(
                item.agent_type, ResourceRequest(ResourceType.NONE)
            )

            subtask = Subtask(
                id=f"subtask_{i + 1}",
                title=item.title,
                description=item.description or item.title,
                agent_type=item.agent_type,
                priority=priority,
                resource_needs=resource_needs,
                metadata={
                    "layer": item.layer,
                    "requires_parallel": item.requires_parallel,
                },
            )
            subtasks.append(subtask)

        return subtasks

    def _determine_priority(
        self,
        item: WorkItem,
        index: int,
        total: int,
    ) -> SubtaskPriority:
        """Determine subtask priority."""
        if item.agent_type == AgentType.EXPLORE:
            return SubtaskPriority.CRITICAL
        if item.agent_type == AgentType.ARCHITECT:
            return SubtaskPriority.HIGH
        if item.agent_type == AgentType.REVIEWER:
            return SubtaskPriority.HIGH
        return SubtaskPriority.NORMAL

    def _build_dependency_graph(
        self,
        subtasks: list[Subtask],
    ) -> dict[str, list[str]]:
        """
        Build dependency graph from agent type rules.

        Returns: dict mapping subtask_id -> [subtask_ids it depends on]
        """
        graph = {}
        subtask_by_agent: dict[AgentType, list[Subtask]] = defaultdict(list)

        # Group subtasks by agent type
        for subtask in subtasks:
            subtask_by_agent[subtask.agent_type].append(subtask)

        # Build dependencies
        for subtask in subtasks:
            dependencies = []

            # Find prerequisite agent types
            prereqs = self.DEPENDENCY_RULES.get(subtask.agent_type, set())

            for prereq_type in prereqs:
                # Add all subtasks of prerequisite type as dependencies
                for prereq_subtask in subtask_by_agent.get(prereq_type, []):
                    if prereq_subtask.id != subtask.id:
                        dependencies.append(prereq_subtask.id)

            graph[subtask.id] = dependencies

        return graph

    def _identify_parallel_groups(
        self,
        subtasks: list[Subtask],
        dependency_graph: dict[str, list[str]],
    ) -> list[ParallelGroup]:
        """
        Identify groups of subtasks that can run in parallel.

        Uses topological sorting to group independent tasks.
        """
        # Build adjacency and in-degree maps
        in_degree: dict[str, int] = {s.id: 0 for s in subtasks}
        adjacency: dict[str, list[str]] = defaultdict(list)

        for subtask_id, deps in dependency_graph.items():
            in_degree[subtask_id] = len(deps)
            for dep in deps:
                adjacency[dep].append(subtask_id)

        # Kahn's algorithm for parallel groups
        groups = []
        queue = [sid for sid, deg in in_degree.items() if deg == 0]

        phase_index = 0
        while queue:
            current_level = queue.copy()
            queue = []

            # Check if current level can run in parallel
            can_parallel = self._can_group_run_parallel(current_level, subtasks)

            groups.append(
                ParallelGroup(
                    subtask_ids=current_level,
                    phase_index=phase_index,
                    can_parallel_execute=can_parallel,
                )
            )
            phase_index += 1

            # Process current level
            for subtask_id in current_level:
                for neighbor in adjacency[subtask_id]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        return groups

    def _can_group_run_parallel(
        self,
        subtask_ids: list[str],
        all_subtasks: list[Subtask],
    ) -> bool:
        """Check if all subtasks in group can run in parallel."""
        subtasks_by_id = {s.id: s for s in all_subtasks}

        for i, sid1 in enumerate(subtask_ids):
            for sid2 in subtask_ids[i + 1 :]:
                s1 = subtasks_by_id.get(sid1)
                s2 = subtasks_by_id.get(sid2)

                if s1 and s2:
                    if not self._are_parallel_compatible(s1.agent_type, s2.agent_type):
                        return False

        return True

    def _are_parallel_compatible(self, type1: AgentType, type2: AgentType) -> bool:
        """Check if two agent types can run in parallel."""
        if type1 == type2:
            # Same type can run in parallel if explicitly allowed
            compatible = self.PARALLEL_COMPATIBILITY.get(type1, set())
            return type1 in compatible

        compatible = self.PARALLEL_COMPATIBILITY.get(type1, set())
        return type2 in compatible

    def _calculate_savings(self, parallel_groups: list[ParallelGroup]) -> int:
        """Estimate time savings from parallel execution."""
        # Assume each group takes 1 unit, parallel groups execute simultaneously
        parallel_savings = sum(
            len(g.subtask_ids) - 1 for g in parallel_groups if g.can_parallel_execute
        )

        # Rough estimate: 5 minutes per subtask, saved by parallel execution
        return parallel_savings * 5 * 60 * 1000  # ms

    def can_run_parallel(
        self,
        subtask1: Subtask,
        subtask2: Subtask,
    ) -> bool:
        """
        Check if two subtasks can run in parallel.

        Based on agent type compatibility and dependencies.
        """
        if subtask1.id == subtask2.id:
            return False

        # Check explicit dependency
        if subtask2.id in subtask1.dependencies:
            return False
        if subtask1.id in subtask2.dependencies:
            return False

        return self._are_parallel_compatible(subtask1.agent_type, subtask2.agent_type)
