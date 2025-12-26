"""
Tests for TaskAnalyzer.
"""

import pytest

from casare_rpa.domain.entities.chain import AgentType
from casare_rpa.domain.services.task_analyzer import TaskAnalyzer, WorkItem


class TestTaskAnalyzer:
    """Test task analysis and decomposition."""

    def test_simple_task_decomposition(self):
        """Test simple task is decomposed into work items."""
        analyzer = TaskAnalyzer()
        items = analyzer.analyze("Implement login node")

        # Should have explore + implementation + test + review
        assert len(items) >= 4
        assert any(i.agent_type == AgentType.EXPLORE for i in items)
        assert any(i.agent_type == AgentType.BUILDER for i in items)
        assert any(i.agent_type == AgentType.QUALITY for i in items)
        assert any(i.agent_type == AgentType.REVIEWER for i in items)

    def test_parallel_indicators(self):
        """Test detection of parallelizable work."""
        analyzer = TaskAnalyzer()
        # Use a pattern that will be split by period
        items = analyzer.analyze("Implement login node. Create register node")

        # Should have multiple explore tasks (parallel)
        explore_items = [i for i in items if i.agent_type == AgentType.EXPLORE]
        assert len(explore_items) > 1

    def test_layer_detection(self):
        """Test detection of layer hints."""
        analyzer = TaskAnalyzer()
        items = analyzer.analyze("Add entity and widget", context={"layer": "domain"})

        # Should return some work items
        assert len(items) > 0

    def test_ui_task_classification(self):
        """Test UI tasks are classified correctly."""
        analyzer = TaskAnalyzer()
        items = analyzer.analyze("Create login dialog")

        # Should have UI agent for dialog keyword
        ui_items = [i for i in items if i.agent_type == AgentType.UI]
        assert len(ui_items) > 0

    def test_fix_task_classification(self):
        """Test fix tasks are classified correctly."""
        analyzer = TaskAnalyzer()
        items = analyzer.analyze("Fix bug in login")

        # Should have builder for fixes
        assert any(i.agent_type == AgentType.BUILDER for i in items)

    def test_refactor_task_classification(self):
        """Test refactor tasks are classified correctly."""
        analyzer = TaskAnalyzer()
        items = analyzer.analyze("Refactor login module")

        # Should have refactor agent
        assert any(i.agent_type == AgentType.REFACTOR for i in items)

    def test_always_adds_explore(self):
        """Test that explore is always added."""
        analyzer = TaskAnalyzer()
        items = analyzer.analyze("Write tests for existing feature")

        # Should still add explore phase
        explore_items = [i for i in items if i.agent_type == AgentType.EXPLORE]
        assert len(explore_items) > 0

    def test_always_adds_reviewer_for_implementation(self):
        """Test that reviewer is added for implementation tasks."""
        analyzer = TaskAnalyzer()
        items = analyzer.analyze("Build new component")

        # Should add reviewer for implementation tasks
        reviewer_items = [i for i in items if i.agent_type == AgentType.REVIEWER]
        assert len(reviewer_items) > 0
