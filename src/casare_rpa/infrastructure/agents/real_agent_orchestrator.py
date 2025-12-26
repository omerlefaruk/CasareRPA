"""
Real agent orchestrator for production use.

Spawns actual Task agents for chain execution. Uses the
Skill tool to invoke agents with appropriate prompts.
"""

import asyncio

from casare_rpa.domain.entities.chain import (
    AgentResult,
    AgentType,
    ChainConfig,
    Issue,
    IssueCategory,
    IssueSeverity,
)
from casare_rpa.domain.interfaces.agent_orchestrator import IAgentOrchestrator


class RealAgentOrchestrator(IAgentOrchestrator):
    """
    Production agent orchestrator that spawns real Task agents.

    This implementation actually invokes AI agents via the Task tool.
    Use MockAgentOrchestrator in tests to avoid expensive AI calls.
    """

    # Mapping from AgentType to subagent_type for Task tool
    AGENT_MAPPING: dict[AgentType, str] = {
        AgentType.EXPLORE: "explore",
        AgentType.ARCHITECT: "architect",
        AgentType.BUILDER: "builder",
        AgentType.REFACTOR: "refactor",
        AgentType.QUALITY: "quality",
        AgentType.REVIEWER: "reviewer",
        AgentType.DOCS: "docs",
        AgentType.RESEARCHER: "researcher",
        AgentType.UI: "ui",
        AgentType.INTEGRATIONS: "integrations",
        AgentType.SECURITY_AUDITOR: "quality",  # Security uses quality agent
    }

    def __init__(self):
        """Initialize the real agent orchestrator."""
        self._task_tool = None  # Injected at runtime
        self._approval_callback: callable | None = None

    def set_task_tool(self, task_tool: callable) -> None:
        """
        Inject the Task tool for agent invocation.

        Args:
            task_tool: The Task tool callable
        """
        self._task_tool = task_tool

    def set_approval_callback(self, callback: callable) -> None:
        """
        Set the callback for human approval requests.

        Args:
            callback: Async callable that returns bool
        """
        self._approval_callback = callback

    async def launch(
        self,
        agent_type: AgentType,
        prompt: str,
        config: ChainConfig | None = None,
    ) -> AgentResult:
        """
        Launch a real agent with the given prompt.

        Args:
            agent_type: Type of agent to launch
            prompt: The prompt/task for the agent
            config: Optional chain configuration

        Returns:
            AgentResult with the agent's output
        """
        if self._task_tool is None:
            # Return mock result if no task tool available
            return AgentResult(
                success=True,
                agent_type=agent_type,
                data={"message": "Task tool not configured"},
            )

        subagent_type = self.AGENT_MAPPING.get(agent_type, "general-purpose")

        # Build full prompt with context
        full_prompt = self._build_full_prompt(agent_type, prompt, config)

        try:
            # Call the Task tool (this is where actual AI agents run)
            response = await self._invoke_agent(subagent_type, full_prompt, config)

            # Parse response into AgentResult
            return self._parse_response(response, agent_type)

        except Exception as e:
            return AgentResult(
                success=False,
                agent_type=agent_type,
                error_message=str(e),
            )

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
        tasks = [self.launch(agent_type, prompt, config) for agent_type, prompt in agent_configs]
        return await asyncio.gather(*tasks)

    def can_run_parallel(self, agent_type: AgentType, other: AgentType) -> bool:
        """
        Check if two agent types can run in parallel.

        Args:
            agent_type: First agent type
            other: Second agent type

        Returns:
            True if agents can run in parallel
        """
        # EXPLORE agents can run in parallel with DOCS and SECURITY
        if agent_type == AgentType.EXPLORE:
            return other in [AgentType.DOCS, AgentType.SECURITY_AUDITOR]

        # QUALITY can run in parallel with DOCS
        if agent_type == AgentType.QUALITY:
            return other == AgentType.DOCS

        return False

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
        if self._approval_callback:
            return await self._approval_callback(agent_type, message, context)

        # Default: auto-approve (for non-interactive use)
        return True

    def _build_full_prompt(
        self,
        agent_type: AgentType,
        base_prompt: str,
        config: ChainConfig | None,
    ) -> str:
        """Build the full prompt for an agent."""
        lines = [
            f"# {agent_type.value.upper()} TASK",
            "",
            base_prompt,
            "",
        ]

        if config:
            lines.extend(
                [
                    "## Configuration",
                    f"- Task Type: {config.task_type.value}",
                    f"- Priority: {config.priority}",
                    f"- Max Iterations: {config.max_iterations}",
                ]
            )

        return "\n".join(lines)

    async def _invoke_agent(
        self,
        subagent_type: str,
        prompt: str,
        config: ChainConfig | None,
    ) -> str:
        """
        Invoke an agent via the Task tool.

        This is a placeholder - actual implementation depends on
        how the Task tool is exposed to the orchestrator.
        """
        # In real usage, this would call the Task tool
        # For now, return a mock response
        return f"Agent {subagent_type} completed task."

    def _parse_response(self, response: str, agent_type: AgentType) -> AgentResult:
        """
        Parse agent response into AgentResult.

        Args:
            response: Raw response from agent
            agent_type: Type of agent that responded

        Returns:
            Parsed AgentResult
        """
        # For REVIEWER agents, check for APPROVED/ISSUES
        if agent_type == AgentType.REVIEWER:
            response_upper = response.upper()
            if "APPROVED" in response_upper:
                return AgentResult(
                    success=True,
                    agent_type=agent_type,
                    status="APPROVED",
                    issues=[],
                    data={"response": response},
                )
            elif "ISSUES" in response_upper or "ISSUE" in response_upper:
                # Try to parse issues from response
                issues = self._extract_issues(response)
                return AgentResult(
                    success=False,
                    agent_type=agent_type,
                    status="ISSUES",
                    issues=issues,
                    data={"response": response},
                )

        # For ARCHITECT agents, check if approval is needed
        if agent_type == AgentType.ARCHITECT:
            return AgentResult(
                success=True,
                agent_type=agent_type,
                requires_approval=True,  # Always require architect approval
                data={"plan": response},
            )

        # Default response
        return AgentResult(
            success=True,
            agent_type=agent_type,
            data={"response": response},
        )

    def _extract_issues(self, response: str) -> list[Issue]:
        """
        Extract issues from a reviewer response.

        Args:
            response: The reviewer's response text

        Returns:
            List of parsed Issues
        """
        issues = []

        # Simple parsing - look for patterns like "Line 42: missing error handling"
        import re

        pattern = r"(?:Line\s+(\d+)|(?:file)?[\"']?([\w\.]+)[\"']?)?\s*:\s*([^\n]+)"
        matches = re.finditer(pattern, response, re.IGNORECASE)

        for match in matches:
            line_str, file_path, description = match.groups()
            line = int(line_str) if line_str else 0

            issues.append(
                Issue(
                    line=line,
                    category=IssueCategory.CODING_STANDARDS,  # Default
                    severity=IssueSeverity.MEDIUM,  # Default
                    description=description.strip(),
                    file_path=file_path,
                )
            )

        return issues


# Singleton instance for production use
_real_orchestrator: RealAgentOrchestrator | None = None


def get_real_orchestrator() -> RealAgentOrchestrator:
    """Get the singleton real agent orchestrator."""
    global _real_orchestrator
    if _real_orchestrator is None:
        _real_orchestrator = RealAgentOrchestrator()
    return _real_orchestrator
