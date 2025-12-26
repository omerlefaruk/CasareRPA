"""
Tests for agent sequencing in chain executor.

Tests that agents are called in the correct order for different
task types.
"""

import pytest

from casare_rpa.domain.entities.chain import (
    AgentType,
    ChainStatus,
    TaskType,
)


class TestAgentSequencing:
    """Test agent execution order."""

    @pytest.mark.asyncio
    async def test_implement_chain_sequence(self, chain_executor, mock_orchestrator):
        """IMPLEMENT chain calls agents in correct order."""
        result = await chain_executor.execute("Add OAuth2 support")

        order = mock_orchestrator.get_call_order()
        assert order == [
            AgentType.EXPLORE,
            AgentType.ARCHITECT,
            AgentType.BUILDER,
            AgentType.QUALITY,
            AgentType.REVIEWER,
            AgentType.DOCS,  # Runs after approval
        ]
        assert result.status == ChainStatus.APPROVED

    @pytest.mark.asyncio
    async def test_fix_chain_sequence(self, chain_executor, mock_orchestrator):
        """FIX chain skips ARCHITECT."""
        result = await chain_executor.execute(
            "Fix null pointer",
            task_type=TaskType.FIX,
        )

        order = mock_orchestrator.get_call_order()
        assert order == [
            AgentType.EXPLORE,
            AgentType.BUILDER,
            AgentType.QUALITY,
            AgentType.REVIEWER,
            AgentType.DOCS,
        ]
        assert AgentType.ARCHITECT not in order
        assert result.status == ChainStatus.APPROVED

    @pytest.mark.asyncio
    async def test_refactor_chain_sequence(self, chain_executor, mock_orchestrator):
        """REFACTOR chain uses REFACTOR agent."""
        result = await chain_executor.execute(
            "Refactor HTTP client",
            task_type=TaskType.REFACTOR,
        )

        order = mock_orchestrator.get_call_order()
        assert order == [
            AgentType.EXPLORE,
            AgentType.REFACTOR,
            AgentType.QUALITY,
            AgentType.REVIEWER,
            AgentType.DOCS,
        ]
        assert result.status == ChainStatus.APPROVED

    @pytest.mark.asyncio
    async def test_research_chain_sequence(self, chain_executor, mock_orchestrator):
        """RESEARCH chain has no reviewer loop."""
        result = await chain_executor.execute(
            "Research OAuth2 patterns",
            task_type=TaskType.RESEARCH,
        )

        order = mock_orchestrator.get_call_order()
        assert order == [
            AgentType.EXPLORE,
            AgentType.RESEARCHER,
        ]
        # No REVIEWER, no DOCS for research
        assert AgentType.REVIEWER not in order
        assert AgentType.DOCS not in order
        assert result.status == ChainStatus.APPROVED

    @pytest.mark.asyncio
    async def test_security_chain_sequence(self, chain_executor, mock_orchestrator):
        """SECURITY chain uses SECURITY_AUDITOR."""
        result = await chain_executor.execute(
            "Security audit for auth flow",
            task_type=TaskType.SECURITY,
        )

        order = mock_orchestrator.get_call_order()
        assert order == [
            AgentType.EXPLORE,
            AgentType.SECURITY_AUDITOR,
            AgentType.REVIEWER,
            AgentType.DOCS,
        ]
        assert result.status == ChainStatus.APPROVED

    @pytest.mark.asyncio
    async def test_ui_chain_sequence(self, chain_executor, mock_orchestrator):
        """UI chain uses UI agent."""
        result = await chain_executor.execute(
            "Create settings UI",
            task_type=TaskType.UI,
        )

        order = mock_orchestrator.get_call_order()
        assert AgentType.UI in order
        assert result.status == ChainStatus.APPROVED

    @pytest.mark.asyncio
    async def test_integration_chain_sequence(self, chain_executor, mock_orchestrator):
        """INTEGRATION chain uses INTEGRATIONS agent."""
        result = await chain_executor.execute(
            "Integrate with Google API",
            task_type=TaskType.INTEGRATION,
        )

        order = mock_orchestrator.get_call_order()
        assert AgentType.INTEGRATIONS in order
        assert result.status == ChainStatus.APPROVED

    @pytest.mark.asyncio
    async def test_explore_called_once_per_iteration(self, chain_executor, mock_orchestrator):
        """EXPLORE is called once, not repeated on loops."""
        # Setup: reviewer returns ISSUES first time, APPROVED second
        mock_orchestrator.set_side_effect(
            AgentType.REVIEWER,
            [
                # First call: ISSUES
                mock_orchestrator._results[AgentType.REVIEWER].__class__(
                    success=False,
                    agent_type=AgentType.REVIEWER,
                    status="ISSUES",
                    issues=[],
                ),
                # Second call: APPROVED
                mock_orchestrator._results[AgentType.REVIEWER],
            ],
        )

        await chain_executor.execute("Add feature", max_iterations=3)

        # EXPLORE called once, BUILDER called twice (initial + fix)
        assert mock_orchestrator.call_count(AgentType.EXPLORE) == 1
        assert mock_orchestrator.call_count(AgentType.BUILDER) == 2

    @pytest.mark.asyncio
    async def test_architect_not_repeated_on_loop(self, chain_executor, mock_orchestrator):
        """ARCHITECT is called once even on loop."""
        mock_orchestrator.set_side_effect(
            AgentType.REVIEWER,
            [
                # ISSUES
                mock_orchestrator._results[AgentType.REVIEWER].__class__(
                    success=False,
                    agent_type=AgentType.REVIEWER,
                    status="ISSUES",
                    issues=[],
                ),
                # APPROVED
                mock_orchestrator._results[AgentType.REVIEWER],
            ],
        )

        await chain_executor.execute("Add feature", max_iterations=3)

        # ARCHITECT called once, not repeated
        assert mock_orchestrator.call_count(AgentType.ARCHITECT) == 1

    @pytest.mark.asyncio
    async def test_quality_called_each_iteration(self, chain_executor, mock_orchestrator):
        """QUALITY is called each iteration."""
        mock_orchestrator.set_side_effect(
            AgentType.REVIEWER,
            [
                # ISSUES
                mock_orchestrator._results[AgentType.REVIEWER].__class__(
                    success=False,
                    agent_type=AgentType.REVIEWER,
                    status="ISSUES",
                    issues=[],
                ),
                # APPROVED
                mock_orchestrator._results[AgentType.REVIEWER],
            ],
        )

        await chain_executor.execute("Add feature", max_iterations=3)

        # QUALITY called twice (initial + re-check after fix)
        assert mock_orchestrator.call_count(AgentType.QUALITY) == 2
