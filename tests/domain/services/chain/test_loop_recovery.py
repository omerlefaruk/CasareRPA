"""
Tests for loop recovery in chain executor.

Tests the core logic: when reviewer returns ISSUES, the chain
loops back to BUILDER for fixes, up to max_iterations.
"""

import pytest

from casare_rpa.domain.entities.chain import (
    AgentResult,
    AgentType,
    ChainStatus,
    Issue,
    IssueCategory,
    IssueSeverity,
    TaskType,
)


class TestLoopRecovery:
    """Test loop-based error recovery."""

    @pytest.mark.asyncio
    async def test_approved_on_first_attempt(self, chain_executor, mock_orchestrator):
        """Chain completes successfully on first iteration."""
        result = await chain_executor.execute("Add OAuth2 support")

        assert result.status == ChainStatus.APPROVED
        assert result.iterations == 1
        assert mock_orchestrator.call_count(AgentType.REVIEWER) == 1

    @pytest.mark.asyncio
    async def test_loop_once_then_approve(self, chain_executor, mock_orchestrator):
        """Chain loops once when reviewer finds issues, then approves."""
        # First call: ISSUES, Second call: APPROVED
        issues_result = AgentResult(
            success=False,
            agent_type=AgentType.REVIEWER,
            status="ISSUES",
            issues=[
                Issue(
                    line=42,
                    category=IssueCategory.ERROR_HANDLING,
                    severity=IssueSeverity.MEDIUM,
                    description="Missing error handling",
                )
            ],
        )

        mock_orchestrator.set_side_effect(
            AgentType.REVIEWER,
            [issues_result, mock_orchestrator._results[AgentType.REVIEWER]],
        )

        result = await chain_executor.execute("Add OAuth2 support", max_iterations=3)

        assert result.status == ChainStatus.APPROVED
        assert result.iterations == 2
        # BUILDER called twice (initial + fix)
        assert mock_orchestrator.call_count(AgentType.BUILDER) == 2
        # REVIEWER called twice (initial + re-review)
        assert mock_orchestrator.call_count(AgentType.REVIEWER) == 2

    @pytest.mark.asyncio
    async def test_loop_twice_then_approve(self, chain_executor, mock_orchestrator):
        """Chain loops twice before approval."""
        issues_result = AgentResult(
            success=False,
            agent_type=AgentType.REVIEWER,
            status="ISSUES",
            issues=[
                Issue(
                    line=42,
                    category=IssueCategory.ERROR_HANDLING,
                    severity=IssueSeverity.MEDIUM,
                    description="Missing error handling",
                )
            ],
        )

        # ISSUES, ISSUES, APPROVED
        mock_orchestrator.set_side_effect(
            AgentType.REVIEWER,
            [issues_result, issues_result, mock_orchestrator._results[AgentType.REVIEWER]],
        )

        result = await chain_executor.execute("Add feature", max_iterations=3)

        assert result.status == ChainStatus.APPROVED
        assert result.iterations == 3
        assert mock_orchestrator.call_count(AgentType.BUILDER) == 3
        assert mock_orchestrator.call_count(AgentType.REVIEWER) == 3

    @pytest.mark.asyncio
    async def test_escalate_after_max_iterations(self, chain_executor, mock_orchestrator):
        """Escalate to human when max iterations exceeded."""
        issues_result = AgentResult(
            success=False,
            agent_type=AgentType.REVIEWER,
            status="ISSUES",
            issues=[
                Issue(
                    line=42,
                    category=IssueCategory.ARCHITECTURE,
                    severity=IssueSeverity.HIGH,
                    description="Complex architectural issue",
                )
            ],
        )

        # Always return ISSUES (4 times for 3 iterations + one check)
        mock_orchestrator.set_side_effect(
            AgentType.REVIEWER,
            [issues_result, issues_result, issues_result, issues_result],
        )

        result = await chain_executor.execute("Complex feature", max_iterations=3)

        assert result.status == ChainStatus.ESCALATED
        assert result.iterations == 3
        assert result.escalated_reason == "Max iterations (3) exceeded"
        assert len(result.issues) > 0

    @pytest.mark.asyncio
    async def test_escalation_preserves_issues(self, chain_executor, mock_orchestrator):
        """Escalated result includes the issues that caused escalation."""
        test_issues = [
            Issue(
                line=42,
                category=IssueCategory.ERROR_HANDLING,
                severity=IssueSeverity.HIGH,
                description="First issue",
            ),
            Issue(
                line=78,
                category=IssueCategory.TYPE_SAFETY,
                severity=IssueSeverity.MEDIUM,
                description="Second issue",
            ),
        ]

        issues_result = AgentResult(
            success=False,
            agent_type=AgentType.REVIEWER,
            status="ISSUES",
            issues=test_issues,
        )

        mock_orchestrator.set_side_effect(
            AgentType.REVIEWER,
            [issues_result, issues_result, issues_result],
        )

        result = await chain_executor.execute("Add feature", max_iterations=2)

        assert result.status == ChainStatus.ESCALATED
        assert result.issues == test_issues

    @pytest.mark.asyncio
    async def test_loop_with_different_severity_issues(self, chain_executor, mock_orchestrator):
        """Loop handles issues of different severity levels."""
        # First: LOW severity issues (should loop)
        low_issues = AgentResult(
            success=False,
            agent_type=AgentType.REVIEWER,
            status="ISSUES",
            issues=[
                Issue(
                    line=10,
                    category=IssueCategory.CODING_STANDARDS,
                    severity=IssueSeverity.LOW,
                    description="Style issue",
                )
            ],
        )

        # Second: APPROVED
        approved = mock_orchestrator._results[AgentType.REVIEWER]

        mock_orchestrator.set_side_effect(AgentType.REVIEWER, [low_issues, approved])

        result = await chain_executor.execute("Add feature", max_iterations=3)

        assert result.status == ChainStatus.APPROVED
        assert result.iterations == 2

    @pytest.mark.asyncio
    async def test_custom_max_iterations(self, chain_executor, mock_orchestrator):
        """Respect custom max_iterations setting."""
        issues_result = AgentResult(
            success=False,
            agent_type=AgentType.REVIEWER,
            status="ISSUES",
            issues=[
                Issue(
                    line=1,
                    category=IssueCategory.CORRECTNESS,
                    severity=IssueSeverity.HIGH,
                    description="Bug",
                )
            ],
        )

        # Set up for 5 iterations
        mock_orchestrator.set_side_effect(
            AgentType.REVIEWER,
            [issues_result] * 6,  # 5 iterations + final check
        )

        result = await chain_executor.execute("Add feature", max_iterations=5)

        assert result.status == ChainStatus.ESCALATED
        assert result.iterations == 5

    @pytest.mark.asyncio
    async def test_zero_max_iterations_escapes_immediately(self, chain_executor, mock_orchestrator):
        """Zero max_iterations means no loops."""
        issues_result = AgentResult(
            success=False,
            agent_type=AgentType.REVIEWER,
            status="ISSUES",
            issues=[],
        )

        mock_orchestrator.set_side_effect(
            AgentType.REVIEWER,
            [issues_result],
        )

        result = await chain_executor.execute("Add feature", max_iterations=1)

        # With max_iterations=1, one attempt is made
        assert result.iterations == 1

    @pytest.mark.asyncio
    async def test_quality_fails_still_loop(self, chain_executor, mock_orchestrator):
        """Chain continues even if QUALITY phase finds failures."""
        # QUALITY returns failures but still success=True
        quality_with_failures = AgentResult(
            success=True,
            agent_type=AgentType.QUALITY,
            data={"tests_run": 10, "tests_passed": False, "failures": 2},
        )

        mock_orchestrator.set_result(AgentType.QUALITY, quality_with_failures)

        # REVIEWER still approves
        result = await chain_executor.execute("Add feature", max_iterations=3)

        # Chain completes even with test failures (reviewer approved)
        assert result.status == ChainStatus.APPROVED

    @pytest.mark.asyncio
    async def test_loop_resets_after_approve(self, chain_executor, mock_orchestrator):
        """After APPROVED, loop counter resets for next chain."""
        # First chain: one loop then approve
        issues = AgentResult(
            success=False,
            agent_type=AgentType.REVIEWER,
            status="ISSUES",
            issues=[],
        )

        mock_orchestrator.set_side_effect(
            AgentType.REVIEWER,
            [issues, mock_orchestrator._results[AgentType.REVIEWER]],
        )

        result1 = await chain_executor.execute("Feature 1", max_iterations=3)
        assert result1.iterations == 2

        # Reset for second chain
        mock_orchestrator.call_log.clear()

        # Second chain: approve immediately
        result2 = await chain_executor.execute("Feature 2", max_iterations=3)
        assert result2.iterations == 1


class TestLoopBehavior:
    """Test specific loop behaviors."""

    @pytest.mark.asyncio
    async def test_builder_called_again_after_issues(self, chain_executor, mock_orchestrator):
        """BUILDER is called again after ISSUES."""
        issues = AgentResult(
            success=False,
            agent_type=AgentType.REVIEWER,
            status="ISSUES",
            issues=[],
        )

        mock_orchestrator.set_side_effect(
            AgentType.REVIEWER,
            [issues, mock_orchestrator._results[AgentType.REVIEWER]],
        )

        await chain_executor.execute("Add feature", max_iterations=3)

        # Verify BUILDER called twice
        assert mock_orchestrator.call_count(AgentType.BUILDER) == 2

    @pytest.mark.asyncio
    async def test_quality_called_again_after_issues(self, chain_executor, mock_orchestrator):
        """QUALITY is called again after fixes."""
        issues = AgentResult(
            success=False,
            agent_type=AgentType.REVIEWER,
            status="ISSUES",
            issues=[],
        )

        mock_orchestrator.set_side_effect(
            AgentType.REVIEWER,
            [issues, mock_orchestrator._results[AgentType.REVIEWER]],
        )

        await chain_executor.execute("Add feature", max_iterations=3)

        # QUALITY called twice (initial + re-check)
        assert mock_orchestrator.call_count(AgentType.QUALITY) == 2

    @pytest.mark.asyncio
    async def test_explore_not_repeated(self, chain_executor, mock_orchestrator):
        """EXPLORE is not repeated on loops."""
        issues = AgentResult(
            success=False,
            agent_type=AgentType.REVIEWER,
            status="ISSUES",
            issues=[],
        )

        mock_orchestrator.set_side_effect(
            AgentType.REVIEWER,
            [issues, mock_orchestrator._results[AgentType.REVIEWER]],
        )

        await chain_executor.execute("Add feature", max_iterations=3)

        # EXPLORE called only once
        assert mock_orchestrator.call_count(AgentType.EXPLORE) == 1

    @pytest.mark.asyncio
    async def test_docs_runs_after_approval(self, chain_executor, mock_orchestrator):
        """DOCS phase runs after successful approval."""
        await chain_executor.execute("Add feature", max_iterations=3)

        # Verify DOCS was called
        assert AgentType.DOCS in mock_orchestrator.get_call_order()
        # DOCS comes after REVIEWER
        order = mock_orchestrator.get_call_order()
        assert order.index(AgentType.REVIEWER) < order.index(AgentType.DOCS)

    @pytest.mark.asyncio
    async def test_docs_not_run_for_escalated(self, chain_executor, mock_orchestrator):
        """DOCS phase does NOT run if chain escalates."""
        issues = AgentResult(
            success=False,
            agent_type=AgentType.REVIEWER,
            status="ISSUES",
            issues=[],
        )

        mock_orchestrator.set_side_effect(
            AgentType.REVIEWER,
            [issues, issues, issues],
        )

        result = await chain_executor.execute("Add feature", max_iterations=2)

        assert result.status == ChainStatus.ESCALATED
        # DOCS should not be called on escalation
        assert AgentType.DOCS not in mock_orchestrator.get_call_order()

    @pytest.mark.asyncio
    async def test_docs_not_run_for_research(self, chain_executor, mock_orchestrator):
        """DOCS phase does NOT run for RESEARCH tasks."""
        await chain_executor.execute(
            "Research OAuth patterns",
            task_type=TaskType.RESEARCH,
        )

        # DOCS should not be called for research
        assert AgentType.DOCS not in mock_orchestrator.get_call_order()
