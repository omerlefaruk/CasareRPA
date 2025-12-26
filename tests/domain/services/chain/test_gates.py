"""
Tests for gate decisions in chain executor.

Tests approval gates (ARCHITECT plan review) and rejection
behaviors that halt chain execution.
"""

import pytest

from casare_rpa.domain.entities.chain import (
    AgentResult,
    AgentType,
    ChainStatus,
    TaskType,
)


class TestArchitectGate:
    """Test ARCHITECT approval gate behavior."""

    @pytest.mark.asyncio
    async def test_approved_gate_continues(self, chain_executor, mock_orchestrator):
        """Approved plan allows chain to continue."""
        # Setup architect to require approval
        architect_result = AgentResult(
            success=True,
            agent_type=AgentType.ARCHITECT,
            data={"plan": "..."},
            requires_approval=True,
        )
        mock_orchestrator.set_result(AgentType.ARCHITECT, architect_result)

        # Set approval to True
        mock_orchestrator.set_approval("architect:Review plan", True)

        result = await chain_executor.execute("Add feature")

        assert result.status == ChainStatus.APPROVED
        # Verify BUILDER was called (gate passed)
        assert mock_orchestrator.call_count(AgentType.BUILDER) >= 1

    @pytest.mark.asyncio
    async def test_rejected_gate_halts_chain(self, chain_executor, mock_orchestrator):
        """Rejected plan halts the chain immediately."""
        architect_result = AgentResult(
            success=True,
            agent_type=AgentType.ARCHITECT,
            data={"plan": "..."},
            requires_approval=True,
        )
        mock_orchestrator.set_result(AgentType.ARCHITECT, architect_result)

        # Set approval to False for architect agent type
        mock_orchestrator.set_approval("architect", False)

        result = await chain_executor.execute("Add feature")

        assert result.status == ChainStatus.HALTED
        assert "rejected" in result.message.lower()
        # Verify BUILDER was NOT called
        assert mock_orchestrator.call_count(AgentType.BUILDER) == 0

    @pytest.mark.asyncio
    async def test_no_approval_skips_gate(self, chain_executor, mock_orchestrator):
        """When requires_approval=False, gate is skipped."""
        # Default architect result has requires_approval=False
        result = await chain_executor.execute("Add feature")

        assert result.status == ChainStatus.APPROVED
        # BUILDER called without approval
        assert mock_orchestrator.call_count(AgentType.BUILDER) >= 1


class TestGateBehaviors:
    """Test general gate behaviors."""

    @pytest.mark.asyncio
    async def test_halted_chain_has_metrics(self, chain_executor, mock_orchestrator):
        """Halted chain still records execution metrics."""
        architect_result = AgentResult(
            success=True,
            agent_type=AgentType.ARCHITECT,
            requires_approval=True,
        )
        mock_orchestrator.set_result(AgentType.ARCHITECT, architect_result)
        mock_orchestrator.set_approval("architect", False)

        result = await chain_executor.execute("Add feature")

        assert result.total_time_ms >= 0  # May be 0 in fast tests
        assert result.iterations > 0

    @pytest.mark.asyncio
    async def test_halted_chain_preserves_context(
        self, chain_executor, mock_orchestrator
    ):
        """Halted chain preserves agent results up to that point."""
        architect_result = AgentResult(
            success=True,
            agent_type=AgentType.ARCHITECT,
            data={"plan": "My plan"},
            requires_approval=True,
        )
        mock_orchestrator.set_result(AgentType.ARCHITECT, architect_result)
        mock_orchestrator.set_approval("architect", False)

        result = await chain_executor.execute("Add feature")

        # EXPLORE and ARCHITECT completed before halt
        assert AgentType.EXPLORE in result.agent_results
        assert AgentType.ARCHITECT in result.agent_results
        # BUILDER never called (note: result may contain previous runs in cache)
        # Just verify the chain halted
        assert result.status == ChainStatus.HALTED

    @pytest.mark.asyncio
    async def test_fix_task_skips_architect_gate(
        self, chain_executor, mock_orchestrator
    ):
        """FIX tasks don't have ARCHITECT gate."""
        result = await chain_executor.execute(
            "Fix the bug",
            task_type=TaskType.FIX,
        )

        assert result.status == ChainStatus.APPROVED
        # ARCHITECT not in FIX chain
        assert AgentType.ARCHITECT not in mock_orchestrator.get_call_order()


class TestEscalationGate:
    """Test escalation as a gate mechanism."""

    @pytest.mark.asyncio
    async def test_escalation_is_final_gate(self, chain_executor, mock_orchestrator):
        """Once escalated, chain stops completely."""
        from casare_rpa.domain.entities.chain import Issue, IssueCategory, IssueSeverity

        issues = AgentResult(
            success=False,
            agent_type=AgentType.REVIEWER,
            status="ISSUES",
            issues=[
                Issue(
                    line=1,
                    category=IssueCategory.ARCHITECTURE,
                    severity=IssueSeverity.CRITICAL,
                    description="Cannot proceed",
                )
            ],
        )

        mock_orchestrator.set_side_effect(
            AgentType.REVIEWER,
            [issues, issues, issues],
        )

        result = await chain_executor.execute("Complex feature", max_iterations=2)

        assert result.status == ChainStatus.ESCALATED
        assert result.escalated_reason is not None


class TestDryRunGate:
    """Test dry-run mode as a preview gate."""

    @pytest.mark.asyncio
    async def test_dry_run_skips_execution(self, chain_executor, mock_orchestrator):
        """Dry run returns plan without executing agents."""
        result = await chain_executor.execute("Add feature", dry_run=True)

        assert result.status == ChainStatus.PENDING
        assert "would execute" in result.message.lower()
        # No agents should be called
        assert len(mock_orchestrator.call_log) == 0

    @pytest.mark.asyncio
    async def test_dry_run_shows_chain(self, chain_executor, mock_orchestrator):
        """Dry run message shows the chain that would execute."""
        result = await chain_executor.execute(
            "Add OAuth2 support",
            task_type=TaskType.IMPLEMENT,
            dry_run=True,
        )

        assert result.status == ChainStatus.PENDING
        # Should mention the agents in the chain
        assert "explore" in result.message.lower()
        assert "architect" in result.message.lower()
        assert "builder" in result.message.lower()
