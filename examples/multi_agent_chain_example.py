"""
CasareRPA - Multi-Agent Chain Example

Demonstrates how to chain multiple AI agents programmatically.
Each agent's output feeds into the next agent's context.

Pattern: Researcher → Analyzer → Summarizer

Usage:
    python examples/multi_agent_chain_example.py
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from loguru import logger


@dataclass
class AgentConfig:
    """Configuration for a single agent in the chain."""

    name: str
    goal: str
    role: str
    max_steps: int = 5
    timeout: float = 120.0
    model: str = "gpt-4o-mini"
    available_tools: Optional[List[str]] = None


@dataclass
class ChainResult:
    """Result of a multi-agent chain execution."""

    success: bool
    final_result: Any = None
    agent_results: Dict[str, Any] = field(default_factory=dict)
    total_tokens: int = 0
    total_time: float = 0.0
    error: Optional[str] = None


class MultiAgentChain:
    """
    Chains multiple AI agents sequentially.

    Each agent receives the previous agent's output as context,
    enabling complex multi-step reasoning workflows.

    Example:
        ```python
        chain = MultiAgentChain()
        chain.add_agent(AgentConfig(
            name="researcher",
            goal="Research the topic: {topic}",
            role="expert researcher"
        ))
        chain.add_agent(AgentConfig(
            name="analyzer",
            goal="Analyze the research findings",
            role="data analyst"
        ))
        chain.add_agent(AgentConfig(
            name="summarizer",
            goal="Create executive summary",
            role="business writer"
        ))

        result = await chain.execute({"topic": "AI in Healthcare"})
        ```
    """

    def __init__(self) -> None:
        self.agents: List[AgentConfig] = []
        self._execution_context: Optional[Any] = None
        self._llm_manager: Optional[Any] = None

    def add_agent(self, agent: AgentConfig) -> "MultiAgentChain":
        """Add an agent to the chain."""
        self.agents.append(agent)
        return self

    async def execute(
        self,
        initial_context: Dict[str, Any],
        execution_context: Optional[Any] = None,
        llm_manager: Optional[Any] = None,
    ) -> ChainResult:
        """
        Execute the agent chain.

        Args:
            initial_context: Variables to inject into the first agent's goal
            execution_context: CasareRPA execution context (optional)
            llm_manager: LLM resource manager (optional)

        Returns:
            ChainResult with final output and all intermediate results
        """
        from casare_rpa.infrastructure.ai.agent_executor import AgentExecutor

        result = ChainResult(success=True)
        current_context = initial_context.copy()

        for i, agent_config in enumerate(self.agents):
            logger.info(
                f"Executing agent [{i+1}/{len(self.agents)}]: {agent_config.name}"
            )

            # Format goal with current context
            goal = (
                agent_config.goal.format(**current_context)
                if current_context
                else agent_config.goal
            )

            try:
                executor = AgentExecutor(
                    max_steps=agent_config.max_steps,
                    timeout_seconds=agent_config.timeout,
                    model=agent_config.model,
                )

                # Build agent-specific context
                agent_context = {
                    "role": agent_config.role,
                    "agent_name": agent_config.name,
                    "chain_position": i + 1,
                    "previous_results": current_context,
                }

                agent_result = await executor.execute(
                    goal=goal,
                    context=execution_context,
                    manager=llm_manager,
                    available_tools=agent_config.available_tools,
                    initial_context=agent_context,
                )

                # Store result
                result.agent_results[agent_config.name] = {
                    "success": agent_result.success,
                    "result": agent_result.result,
                    "steps": len(agent_result.steps),
                    "tokens": agent_result.total_tokens,
                    "time": agent_result.execution_time,
                }

                result.total_tokens += agent_result.total_tokens
                result.total_time += agent_result.execution_time

                if not agent_result.success:
                    result.success = False
                    result.error = (
                        f"Agent '{agent_config.name}' failed: {agent_result.error}"
                    )
                    logger.error(result.error)
                    break

                # Pass result to next agent as context
                current_context = {
                    "previous_agent": agent_config.name,
                    "previous_result": agent_result.result,
                    **current_context,
                }

                logger.info(
                    f"Agent '{agent_config.name}' completed: "
                    f"{len(agent_result.steps)} steps, {agent_result.total_tokens} tokens"
                )

            except Exception as e:
                result.success = False
                result.error = f"Agent '{agent_config.name}' error: {e}"
                logger.exception(result.error)
                break

        if result.success:
            result.final_result = current_context.get("previous_result")

        return result


# =============================================================================
# PREDEFINED CHAIN TEMPLATES
# =============================================================================


def create_research_chain() -> MultiAgentChain:
    """
    Create a research → analyze → summarize chain.

    Usage:
        chain = create_research_chain()
        result = await chain.execute({"topic": "Quantum Computing"})
    """
    chain = MultiAgentChain()

    chain.add_agent(
        AgentConfig(
            name="researcher",
            goal="Research and gather comprehensive information about: {topic}. "
            "Find key facts, statistics, recent developments, and expert opinions. "
            "Return findings as structured JSON with 'facts', 'statistics', 'developments', 'sources'.",
            role="expert researcher with access to current information",
            max_steps=7,
            timeout=180.0,
        )
    )

    chain.add_agent(
        AgentConfig(
            name="analyzer",
            goal="Analyze the research findings from the previous agent. "
            "Identify patterns, trends, opportunities, and potential risks. "
            "Provide critical analysis with supporting evidence. "
            "Return as JSON with 'patterns', 'trends', 'opportunities', 'risks', 'evidence'.",
            role="strategic analyst specializing in trend analysis",
            max_steps=5,
            timeout=120.0,
        )
    )

    chain.add_agent(
        AgentConfig(
            name="summarizer",
            goal="Create an executive summary suitable for C-level presentation. "
            "Be concise but comprehensive. Include actionable recommendations. "
            "Return as JSON with 'summary', 'key_takeaways', 'recommendations', 'next_steps'.",
            role="executive communication specialist",
            max_steps=3,
            timeout=60.0,
        )
    )

    return chain


def create_code_review_chain() -> MultiAgentChain:
    """
    Create a code review chain: analyze → security → improvements.

    Usage:
        chain = create_code_review_chain()
        result = await chain.execute({"code": "def foo(): ..."})
    """
    chain = MultiAgentChain()

    chain.add_agent(
        AgentConfig(
            name="code_analyzer",
            goal="Analyze the provided code for quality, readability, and adherence to best practices. "
            "Identify the language, frameworks used, and code structure. "
            "Code to analyze: {code}",
            role="senior software engineer with expertise in code review",
            max_steps=5,
        )
    )

    chain.add_agent(
        AgentConfig(
            name="security_reviewer",
            goal="Review the code analysis for security vulnerabilities. "
            "Check for common security issues (injection, XSS, auth flaws, etc.). "
            "Rate severity and provide remediation steps.",
            role="security specialist and penetration tester",
            max_steps=5,
        )
    )

    chain.add_agent(
        AgentConfig(
            name="improvement_suggester",
            goal="Based on the code analysis and security review, suggest concrete improvements. "
            "Prioritize by impact and effort. Provide refactored code examples where helpful.",
            role="tech lead focused on code quality and maintainability",
            max_steps=5,
        )
    )

    return chain


def create_content_pipeline_chain() -> MultiAgentChain:
    """
    Create a content generation pipeline: outline → draft → polish.

    Usage:
        chain = create_content_pipeline_chain()
        result = await chain.execute({
            "topic": "Remote Work Best Practices",
            "format": "blog post",
            "audience": "managers"
        })
    """
    chain = MultiAgentChain()

    chain.add_agent(
        AgentConfig(
            name="outliner",
            goal="Create a detailed outline for a {format} about '{topic}' targeting {audience}. "
            "Include main sections, key points, and suggested examples.",
            role="content strategist",
            max_steps=3,
        )
    )

    chain.add_agent(
        AgentConfig(
            name="writer",
            goal="Write the full {format} following the outline from the previous agent. "
            "Match the tone and depth appropriate for {audience}. "
            "Make it engaging and informative.",
            role="professional content writer",
            max_steps=5,
        )
    )

    chain.add_agent(
        AgentConfig(
            name="editor",
            goal="Edit and polish the draft. Fix grammar, improve flow, enhance clarity. "
            "Ensure consistency in tone and style. Add a compelling hook and conclusion.",
            role="senior editor and copywriter",
            max_steps=3,
        )
    )

    return chain


# =============================================================================
# EXAMPLE USAGE
# =============================================================================


async def main():
    """Example demonstrating multi-agent chain execution."""

    # Example 1: Research chain
    print("\n" + "=" * 60)
    print("EXAMPLE: Research Chain")
    print("=" * 60)

    chain = create_research_chain()

    # Note: In real usage, provide actual execution_context and llm_manager
    # This is a demonstration of the API
    print(f"\nChain has {len(chain.agents)} agents:")
    for i, agent in enumerate(chain.agents):
        print(f"  [{i+1}] {agent.name}: {agent.role}")

    print("\nTo execute:")
    print('  result = await chain.execute({"topic": "AI in Healthcare"})')

    # Example 2: Custom chain
    print("\n" + "=" * 60)
    print("EXAMPLE: Custom Chain")
    print("=" * 60)

    custom_chain = MultiAgentChain()
    custom_chain.add_agent(
        AgentConfig(
            name="extractor",
            goal="Extract key entities and relationships from: {data}",
            role="data extraction specialist",
        )
    )
    custom_chain.add_agent(
        AgentConfig(
            name="validator",
            goal="Validate the extracted entities. Check for accuracy and completeness.",
            role="data quality analyst",
        )
    )

    print(f"\nCustom chain has {len(custom_chain.agents)} agents")
    print('  result = await custom_chain.execute({"data": "..."})')


if __name__ == "__main__":
    asyncio.run(main())
