"""
Tests for DecompositionEngine.
"""

import pytest

from casare_rpa.domain.entities.chain import AgentType
from casare_rpa.domain.entities.task_decomposition import (
    DecompositionResult,
    Subtask,
    SubtaskPriority,
)
from casare_rpa.domain.services.decomposition_engine import DecompositionEngine
from casare_rpa.domain.services.task_analyzer import TaskAnalyzer


class TestDecompositionEngine:
    """Test task decomposition into subtasks."""

    def test_decompose_returns_result(self):
        """Test decomposition returns valid result."""
        engine = DecompositionEngine()
        result = engine.decompose("Implement feature")

        assert isinstance(result, DecompositionResult)
        assert result.original_task == "Implement feature"
        assert len(result.subtasks) > 0
        assert isinstance(result.dependency_graph, dict)
        assert isinstance(result.parallel_groups, list)

    def test_dependency_graph_structure(self):
        """Test dependency graph has correct structure."""
        engine = DecompositionEngine()
        result = engine.decompose("Implement feature")

        # All subtask IDs should be in the graph
        subtask_ids = {s.id for s in result.subtasks}
        graph_keys = set(result.dependency_graph.keys())

        assert subtask_ids == graph_keys

    def test_explore_has_no_dependencies(self):
        """Test explore subtasks have no dependencies."""
        engine = DecompositionEngine()
        result = engine.decompose("Implement feature")

        explore_subtasks = [s for s in result.subtasks if s.agent_type == AgentType.EXPLORE]

        for subtask in explore_subtasks:
            assert len(result.dependency_graph[subtask.id]) == 0

    def test_architect_depends_on_explore(self):
        """Test architect depends on explore."""
        engine = DecompositionEngine()
        result = engine.decompose("Implement feature")

        explore_ids = {s.id for s in result.subtasks if s.agent_type == AgentType.EXPLORE}
        architect_subtasks = [s for s in result.subtasks if s.agent_type == AgentType.ARCHITECT]

        for arch_subtask in architect_subtasks:
            deps = result.dependency_graph[arch_subtask.id]
            # Should depend on at least one explore
            assert any(dep in explore_ids for dep in deps)

    def test_parallel_groups_identified(self):
        """Test parallel groups are identified."""
        engine = DecompositionEngine()
        # Use a task that will generate multiple phases
        result = engine.decompose("Implement node with dialog and tests")

        # Should have at least 1 group
        assert len(result.parallel_groups) >= 1

    def test_parallel_group_structure(self):
        """Test parallel groups have valid structure."""
        engine = DecompositionEngine()
        result = engine.decompose("Implement node with dialog and tests")

        all_subtask_ids = {s.id for s in result.subtasks}

        for group in result.parallel_groups:
            # All subtask IDs in groups should exist
            for sid in group.subtask_ids:
                assert sid in all_subtask_ids

    def test_can_run_parallel_check(self):
        """Test parallel compatibility check."""
        engine = DecompositionEngine()
        # Use task that generates multiple explores
        result = engine.decompose("Implement node with dialog and tests")

        # Find two explore subtasks (should be parallel compatible)
        explore_subtasks = [s for s in result.subtasks if s.agent_type == AgentType.EXPLORE]

        if len(explore_subtasks) >= 2:
            assert engine.can_run_parallel(explore_subtasks[0], explore_subtasks[1])

    def test_builder_ui_parallel_compatible(self):
        """Test builder and UI can run in parallel."""
        engine = DecompositionEngine()

        subtask1 = Subtask(
            id="1",
            title="Builder",
            description="Build backend",
            agent_type=AgentType.BUILDER,
            dependencies=[],
        )
        subtask2 = Subtask(
            id="2",
            title="UI",
            description="Build UI",
            agent_type=AgentType.UI,
            dependencies=[],
        )

        assert engine.can_run_parallel(subtask1, subtask2)

    def test_architect_not_parallel_with_explore(self):
        """Test architect is not parallel with explore (depends on it)."""
        engine = DecompositionEngine()
        result = engine.decompose("Implement node with dialog")

        explore_subtasks = [s for s in result.subtasks if s.agent_type == AgentType.EXPLORE]
        architect_subtasks = [s for s in result.subtasks if s.agent_type == AgentType.ARCHITECT]

        if explore_subtasks and architect_subtasks:
            # Architect depends on explore, so not parallel
            assert not engine.can_run_parallel(explore_subtasks[0], architect_subtasks[0])

    def test_estimated_savings_calculated(self):
        """Test estimated time savings are calculated."""
        engine = DecompositionEngine()
        result = engine.decompose("Implement node with dialog")

        # Should calculate some savings
        assert result.estimated_savings_ms >= 0

    def test_complex_task_decomposition(self):
        """Test decomposition of a complex task."""
        engine = DecompositionEngine()
        result = engine.decompose("Implement node with dialog and tests")

        # Should have multiple subtasks
        assert len(result.subtasks) >= 2
        assert len(result.parallel_groups) >= 1
