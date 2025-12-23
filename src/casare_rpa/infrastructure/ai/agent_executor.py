"""
CasareRPA - Agent Executor

Implements the ReAct (Reason + Act) pattern for autonomous AI agents.
Manages multi-step reasoning, tool execution, and safety limits.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from casare_rpa.infrastructure.execution import ExecutionContext
    from casare_rpa.infrastructure.resources.llm_resource_manager import (
        LLMResourceManager,
    )

from casare_rpa.infrastructure.ai.agent_tools import (
    AgentToolRegistry,
    get_default_tool_registry,
)


class StepType(Enum):
    """Type of agent step."""

    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    FINAL_ANSWER = "final_answer"
    ERROR = "error"


@dataclass
class AgentStep:
    """Represents a single step in agent execution."""

    step_number: int
    step_type: StepType
    content: str
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[Dict[str, Any]] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_number": self.step_number,
            "step_type": self.step_type.value,
            "content": self.content,
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "tool_output": self.tool_output,
            "timestamp": self.timestamp,
        }


@dataclass
class AgentResult:
    """Result of agent execution."""

    success: bool
    result: Any
    steps: List[AgentStep] = field(default_factory=list)
    total_tokens: int = 0
    execution_time: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "result": self.result,
            "steps": [s.to_dict() for s in self.steps],
            "total_tokens": self.total_tokens,
            "execution_time": self.execution_time,
            "error": self.error,
        }


class AgentExecutor:
    """
    Executes AI agents using the ReAct pattern.

    ReAct Pattern:
    1. Reason: Think about what to do next
    2. Act: Choose and execute a tool
    3. Observe: Process the tool result
    4. Repeat until goal is achieved or limit reached

    Safety Features:
    - Maximum step limit
    - Execution timeout
    - Tool confirmation for dangerous operations
    - Error recovery
    """

    DEFAULT_SYSTEM_PROMPT = """You are an AI agent that completes tasks by using tools.

You follow the ReAct pattern:
1. THOUGHT: Think about what you need to do next
2. ACTION: Choose a tool and provide parameters
3. OBSERVATION: Analyze the tool result

Continue until you can provide a final answer.

Important rules:
- Always think before acting
- Use the most appropriate tool for each step
- When you have the final answer, use the "finish" tool
- If you encounter errors, try alternative approaches
- Be concise but thorough

Available tools:
{tools}

Respond in this exact JSON format:
{{
  "thought": "your reasoning about what to do next",
  "action": "tool_name",
  "action_input": {{"param1": "value1", "param2": "value2"}}
}}

Or when finished:
{{
  "thought": "I have completed the task",
  "action": "finish",
  "action_input": {{"result": "final answer", "summary": "what was done"}}
}}
"""

    def __init__(
        self,
        tool_registry: Optional[AgentToolRegistry] = None,
        max_steps: int = 10,
        timeout_seconds: float = 300.0,
        model: str = "gpt-4o-mini",
    ) -> None:
        """
        Initialize agent executor.

        Args:
            tool_registry: Registry of available tools
            max_steps: Maximum number of steps before stopping
            timeout_seconds: Maximum execution time
            model: LLM model to use for reasoning
        """
        self._tool_registry = tool_registry or get_default_tool_registry()
        self._max_steps = max_steps
        self._timeout = timeout_seconds
        self._model = model

    async def execute(
        self,
        goal: str,
        context: ExecutionContext,
        manager: LLMResourceManager,
        available_tools: Optional[List[str]] = None,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:
        """
        Execute agent to achieve the given goal.

        Args:
            goal: The objective for the agent to achieve
            context: Execution context for tool execution
            manager: LLM resource manager
            available_tools: List of tool names to make available (None = all)
            initial_context: Additional context to provide to the agent

        Returns:
            AgentResult with execution details
        """
        start_time = time.time()
        steps: List[AgentStep] = []
        total_tokens = 0
        step_number = 0

        # Build system prompt with available tools
        tools_desc = self._tool_registry.get_prompt_descriptions(available_tools)
        system_prompt = self.DEFAULT_SYSTEM_PROMPT.format(tools=tools_desc)

        # Build initial message
        user_message = f"Goal: {goal}"
        if initial_context:
            context_str = json.dumps(initial_context, indent=2, default=str)
            user_message += f"\n\nContext:\n{context_str}"

        # Conversation history for multi-turn
        messages = [user_message]
        observations: List[str] = []

        try:
            while step_number < self._max_steps:
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > self._timeout:
                    error_msg = f"Agent timeout after {elapsed:.1f}s"
                    steps.append(
                        AgentStep(
                            step_number=step_number,
                            step_type=StepType.ERROR,
                            content=error_msg,
                        )
                    )
                    return AgentResult(
                        success=False,
                        result=None,
                        steps=steps,
                        total_tokens=total_tokens,
                        execution_time=elapsed,
                        error=error_msg,
                    )

                step_number += 1

                # Build prompt with history
                full_prompt = self._build_prompt(messages, observations)

                # Get LLM response
                response = await manager.completion(
                    prompt=full_prompt,
                    model=self._model,
                    system_prompt=system_prompt,
                    temperature=0.2,
                    max_tokens=1000,
                )
                total_tokens += response.total_tokens

                # Parse response
                parsed = self._parse_response(response.content)

                if not parsed:
                    # Invalid response format
                    steps.append(
                        AgentStep(
                            step_number=step_number,
                            step_type=StepType.ERROR,
                            content=f"Failed to parse response: {response.content[:200]}",
                        )
                    )
                    observations.append(
                        "Error: Invalid response format. Please respond with valid JSON."
                    )
                    continue

                thought = parsed.get("thought", "")
                action = parsed.get("action", "")
                action_input = parsed.get("action_input", {})

                # Record thought
                if thought:
                    steps.append(
                        AgentStep(
                            step_number=step_number,
                            step_type=StepType.THOUGHT,
                            content=thought,
                        )
                    )

                # Check for finish action
                if action == "finish":
                    result = action_input.get("result", "")
                    summary = action_input.get("summary", "")

                    steps.append(
                        AgentStep(
                            step_number=step_number,
                            step_type=StepType.FINAL_ANSWER,
                            content=f"{result}\n\nSummary: {summary}" if summary else result,
                            tool_name="finish",
                            tool_input=action_input,
                        )
                    )

                    return AgentResult(
                        success=True,
                        result=result,
                        steps=steps,
                        total_tokens=total_tokens,
                        execution_time=time.time() - start_time,
                    )

                # Execute tool
                if action:
                    tool = self._tool_registry.get(action)

                    if not tool:
                        observation = f"Error: Unknown tool '{action}'. Available tools: {', '.join(t.name for t in self._tool_registry.list_tools(available_tools))}"
                    elif available_tools and action not in available_tools:
                        observation = f"Error: Tool '{action}' is not available for this task."
                    else:
                        # Execute tool
                        tool_result = await self._tool_registry.execute_tool(
                            name=action,
                            parameters=action_input,
                            context=context,
                        )

                        steps.append(
                            AgentStep(
                                step_number=step_number,
                                step_type=StepType.ACTION,
                                content=f"Using tool: {action}",
                                tool_name=action,
                                tool_input=action_input,
                                tool_output=tool_result,
                            )
                        )

                        # Format observation
                        if tool_result.get("success"):
                            observation = f"Tool '{action}' succeeded: {json.dumps(tool_result.get('result', tool_result), default=str)}"
                        else:
                            observation = f"Tool '{action}' failed: {tool_result.get('error', 'Unknown error')}"

                    steps.append(
                        AgentStep(
                            step_number=step_number,
                            step_type=StepType.OBSERVATION,
                            content=observation,
                        )
                    )
                    observations.append(observation)

            # Max steps reached
            error_msg = f"Agent reached maximum steps ({self._max_steps})"
            steps.append(
                AgentStep(
                    step_number=step_number,
                    step_type=StepType.ERROR,
                    content=error_msg,
                )
            )

            return AgentResult(
                success=False,
                result=None,
                steps=steps,
                total_tokens=total_tokens,
                execution_time=time.time() - start_time,
                error=error_msg,
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Agent execution error: {error_msg}")

            steps.append(
                AgentStep(
                    step_number=step_number,
                    step_type=StepType.ERROR,
                    content=error_msg,
                )
            )

            return AgentResult(
                success=False,
                result=None,
                steps=steps,
                total_tokens=total_tokens,
                execution_time=time.time() - start_time,
                error=error_msg,
            )

    def _build_prompt(
        self,
        messages: List[str],
        observations: List[str],
    ) -> str:
        """Build the prompt including history."""
        parts = [messages[0]]  # Initial goal

        if observations:
            parts.append("\nPrevious observations:")
            for i, obs in enumerate(observations[-5:], 1):  # Last 5 observations
                parts.append(f"{i}. {obs}")

        parts.append("\nWhat is your next step?")

        return "\n".join(parts)

    def _parse_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse LLM response into structured format."""
        content = content.strip()

        # Try to extract JSON from response
        if content.startswith("```"):
            lines = content.split("\n")
            # Find the content between code fences
            json_lines = []
            in_json = False
            for line in lines:
                if line.startswith("```") and not in_json:
                    in_json = True
                    continue
                elif line.startswith("```"):
                    break
                elif in_json:
                    json_lines.append(line)
            content = "\n".join(json_lines)

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try to find JSON object in text
        start = content.find("{")
        end = content.rfind("}") + 1

        if start >= 0 and end > start:
            try:
                return json.loads(content[start:end])
            except json.JSONDecodeError:
                pass

        return None


__all__ = [
    "StepType",
    "AgentStep",
    "AgentResult",
    "AgentExecutor",
]
