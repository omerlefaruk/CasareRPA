"""
Interface for agent orchestration in chain execution.

This abstraction allows the ChainExecutor to work with either
real AI agents (production) or mock agents (testing).
"""

from abc import ABC, abstractmethod

from casare_rpa.domain.entities.chain import (
    AgentResult,
    AgentType,
    ChainConfig,
)


class IAgentOrchestrator(ABC):
    """
    Interface for launching and managing AI agents.

    Implementations:
    - RealAgentOrchestrator: Spawns actual Task agents (production)
    - MockAgentOrchestrator: Returns controlled results (testing)
    """

    @abstractmethod
    async def launch(
        self,
        agent_type: AgentType,
        prompt: str,
        config: ChainConfig | None = None,
    ) -> AgentResult:
        """
        Launch an agent with the given prompt.

        Args:
            agent_type: Type of agent to launch
            prompt: The prompt/task for the agent
            config: Optional chain configuration

        Returns:
            AgentResult with the agent's output
        """
        pass

    @abstractmethod
    async def launch_parallel(
        self,
        agent_configs: list[tuple[AgentType, str]],
        config: ChainConfig | None = None,
    ) -> list[AgentResult]:
        """
        Launch multiple agents in parallel.

        Args:
            agent_configs: List of (agent_type, prompt) tuples
            config: Optional chain configuration

        Returns:
            List of AgentResults, one per agent
        """
        pass

    @abstractmethod
    def can_run_parallel(self, agent_type: AgentType, other: AgentType) -> bool:
        """
        Check if two agent types can run in parallel.

        Args:
            agent_type: First agent type
            other: Second agent type

        Returns:
            True if agents can run in parallel
        """
        pass

    @abstractmethod
    async def request_approval(
        self,
        agent_type: AgentType,
        message: str,
        context: dict,
    ) -> bool:
        """
        Request human approval for a gate.

        Args:
            agent_type: The agent requesting approval
            message: Message to show the human
            context: Additional context for the decision

        Returns:
            True if approved, False if rejected
        """
        pass
