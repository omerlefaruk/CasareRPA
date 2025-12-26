"""
Fixtures for chain executor tests.

Provides mock agents that return controlled results for testing
orchestration logic without spawning expensive AI agents.
"""

from typing import Optional

import pytest

from casare_rpa.domain.entities.chain import (
    AgentResult,
    AgentType,
    ChainConfig,
    Issue,
    IssueCategory,
    IssueSeverity,
)
from casare_rpa.domain.interfaces.agent_orchestrator import IAgentOrchestrator
from casare_rpa.domain.services.chain_executor import ChainExecutor


class MockAgentOrchestrator(IAgentOrchestrator):
    """
    Mock orchestrator for testing chain execution.

    Returns controlled results without spawning real agents.
    """

    def __init__(self):
        """Initialize the mock orchestrator."""
        self.call_log: list[tuple[AgentType, str]] = []
        self._results: dict[AgentType, AgentResult] = {}
        self._approvals: dict[str, bool] = {}
        self._parallel_capable: set[tuple[AgentType, AgentType]] = set()
        self._side_effects: dict[AgentType, iter] = {}

        # Default results for each agent type
        self._setup_default_results()

    def _setup_default_results(self) -> None:
        """Setup default successful results for each agent type."""
        self._results = {
            AgentType.EXPLORE: AgentResult(
                success=True,
                agent_type=AgentType.EXPLORE,
                data={"patterns_found": []},
            ),
            AgentType.ARCHITECT: AgentResult(
                success=True,
                agent_type=AgentType.ARCHITECT,
                data={"plan": "Implementation plan"},
                requires_approval=False,  # Default: no approval needed
            ),
            AgentType.BUILDER: AgentResult(
                success=True,
                agent_type=AgentType.BUILDER,
                data={"files_created": []},
            ),
            AgentType.REFACTOR: AgentResult(
                success=True,
                agent_type=AgentType.REFACTOR,
                data={"files_refactored": []},
            ),
            AgentType.QUALITY: AgentResult(
                success=True,
                agent_type=AgentType.QUALITY,
                data={"tests_run": 0, "tests_passed": True},
            ),
            AgentType.REVIEWER: AgentResult(
                success=True,
                agent_type=AgentType.REVIEWER,
                status="APPROVED",
                issues=[],
            ),
            AgentType.DOCS: AgentResult(
                success=True,
                agent_type=AgentType.DOCS,
                data={"docs_updated": []},
            ),
            AgentType.RESEARCHER: AgentResult(
                success=True,
                agent_type=AgentType.RESEARCHER,
                data={"findings": []},
            ),
            AgentType.UI: AgentResult(
                success=True,
                agent_type=AgentType.UI,
                data={"ui_components": []},
            ),
            AgentType.INTEGRATIONS: AgentResult(
                success=True,
                agent_type=AgentType.INTEGRATIONS,
                data={"integrations": []},
            ),
            AgentType.SECURITY_AUDITOR: AgentResult(
                success=True,
                agent_type=AgentType.SECURITY_AUDITOR,
                data={"vulnerabilities": []},
            ),
        }

    def set_result(self, agent_type: AgentType, result: AgentResult) -> None:
        """
        Set the result to return for an agent type.

        Args:
            agent_type: The agent type
            result: The result to return
        """
        self._results[agent_type] = result

    def set_side_effect(self, agent_type: AgentType, results: list[AgentResult]) -> None:
        """
        Set a side effect (multiple results) for an agent type.

        Useful for testing loops where the first call returns ISSUES
        and the second returns APPROVED.

        Args:
            agent_type: The agent type
            results: List of results to return in sequence
        """
        if agent_type not in self._side_effects:
            self._side_effects = {}
        self._side_effects[agent_type] = iter(results)

    def set_approval(self, key: str, approved: bool) -> None:
        """
        Set the approval response for a key.

        Args:
            key: The approval key
            approved: Whether to approve
        """
        self._approvals[key] = approved

    def enable_parallel(self, a: AgentType, b: AgentType) -> None:
        """Enable parallel execution between two agent types."""
        self._parallel_capable.add((a, b))
        self._parallel_capable.add((b, a))

    async def launch(
        self,
        agent_type: AgentType,
        prompt: str,
        config: Optional[ChainConfig] = None,
    ) -> AgentResult:
        """
        Mock launch - returns controlled result.

        Args:
            agent_type: Type of agent to launch
            prompt: The prompt (logged but not used)
            config: Optional config

        Returns:
            Controlled AgentResult
        """
        self.call_log.append((agent_type, prompt))

        # Check for side effects first
        if hasattr(self, "_side_effects") and agent_type in self._side_effects:
            try:
                return next(self._side_effects[agent_type])
            except StopIteration:
                pass

        return self._results.get(agent_type, AgentResult(success=True, agent_type=agent_type))

    async def launch_parallel(
        self,
        agent_configs: list[tuple[AgentType, str]],
        config: Optional[ChainConfig] = None,
    ) -> list[AgentResult]:
        """
        Mock parallel launch - returns results for all agents.

        Args:
            agent_configs: List of (agent_type, prompt) tuples
            config: Optional config

        Returns:
            List of AgentResults
        """
        results = []
        for agent_type, prompt in agent_configs:
            result = await self.launch(agent_type, prompt, config)
            results.append(result)
        return results

    def can_run_parallel(self, agent_type: AgentType, other: AgentType) -> bool:
        """
        Check if two agents can run in parallel.

        Args:
            agent_type: First agent type
            other: Second agent type

        Returns:
            True if parallel execution is enabled
        """
        return (agent_type, other) in self._parallel_capable

    async def request_approval(
        self,
        agent_type: AgentType,
        message: str,
        context: dict,
    ) -> bool:
        """
        Mock approval request - returns pre-configured response.

        Args:
            agent_type: The agent requesting approval
            message: The approval message
            context: Additional context

        Returns:
            Pre-configured approval response
        """
        # Check for exact key match first
        key = f"{agent_type.value}:{message}"
        if key in self._approvals:
            return self._approvals[key]

        # Check for agent_type-only match
        if agent_type.value in self._approvals:
            return self._approvals[agent_type.value]

        # Check for agent_type enum match
        if str(agent_type) in self._approvals:
            return self._approvals[str(agent_type)]

        # Default: approve
        return True

    def get_call_order(self) -> list[AgentType]:
        """Get the order agents were called."""
        return [agent_type for agent_type, _ in self.call_log]

    def call_count(self, agent_type: AgentType) -> int:
        """Get the number of times an agent was called."""
        return sum(1 for at, _ in self.call_log if at == agent_type)

    def reset(self) -> None:
        """Reset the mock orchestrator."""
        self.call_log.clear()
        self._side_effects = {}
        self._approvals = {}
        self._setup_default_results()


@pytest.fixture
def mock_orchestrator():
    """Provide a mock agent orchestrator for testing."""
    orchestrator = MockAgentOrchestrator()
    yield orchestrator
    orchestrator.reset()


@pytest.fixture
def chain_executor(mock_orchestrator):
    """Provide a chain executor with mock orchestrator."""
    return ChainExecutor(orchestrator=mock_orchestrator)


# Helper fixtures for common test scenarios


@pytest.fixture
def sample_issues():
    """Sample issues for testing loop behavior."""
    return [
        Issue(
            line=42,
            category=IssueCategory.ERROR_HANDLING,
            severity=IssueSeverity.MEDIUM,
            description="Missing error handling",
            file_path="src/example.py",
        ),
        Issue(
            line=78,
            category=IssueCategory.TYPE_SAFETY,
            severity=IssueSeverity.LOW,
            description="Type hint should be Optional[str]",
            file_path="src/example.py",
        ),
    ]


@pytest.fixture
def reviewer_issues(sample_issues):
    """AgentResult with issues for testing."""
    return AgentResult(
        success=False,
        agent_type=AgentType.REVIEWER,
        status="ISSUES",
        issues=sample_issues,
    )


@pytest.fixture
def reviewer_approved():
    """AgentResult with approved status."""
    return AgentResult(
        success=True,
        agent_type=AgentType.REVIEWER,
        status="APPROVED",
        issues=[],
    )
