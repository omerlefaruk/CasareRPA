"""
CasareRPA - AI Agent Node

Autonomous multi-step reasoning with tool use.
Implements ReAct pattern for complex task completion.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from loguru import logger

from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    PortType,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.infrastructure.resources.llm_resource_manager import LLMResourceManager
from casare_rpa.nodes.llm.llm_base import LLMBaseNode


class AIAgentNode(LLMBaseNode):
    """
    Autonomous AI agent with multi-step reasoning.

    The agent uses the ReAct (Reason + Act) pattern to:
    1. Analyze the goal
    2. Plan steps needed
    3. Execute tools iteratively
    4. Observe results and adapt

    Features:
    - Multi-step reasoning with intermediate thoughts
    - Tool calling via registered agent tools
    - Safety limits (max steps, timeout)
    - Full execution trace for debugging

    Example goals:
    - "Find the order status for customer 12345"
    - "Extract all emails from inbox and summarize them"
    - "Download the report and calculate totals"
    """

    NODE_NAME = "AI Agent"
    NODE_CATEGORY = "AI/ML"
    NODE_DESCRIPTION = "Autonomous AI agent with tool use for complex tasks"

    # Default limits
    DEFAULT_MAX_STEPS = 10
    DEFAULT_TIMEOUT = 300.0  # 5 minutes

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name=self.NODE_NAME, **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Execution ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("exec_error", PortType.EXEC_OUTPUT)

        # Data inputs
        self.add_input_port("goal", PortType.INPUT, DataType.STRING)
        self.add_input_port("context", PortType.INPUT, DataType.ANY, required=False)
        self.add_input_port(
            "available_tools", PortType.INPUT, DataType.LIST, required=False
        )
        self.add_input_port(
            "max_steps", PortType.INPUT, DataType.INTEGER, required=False
        )
        self.add_input_port("timeout", PortType.INPUT, DataType.FLOAT, required=False)
        self._define_common_input_ports()

        # Data outputs
        self.add_output_port("result", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("steps_taken", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("step_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("total_tokens", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("execution_time", PortType.OUTPUT, DataType.FLOAT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def _execute_llm(
        self,
        context: ExecutionContext,
        manager: LLMResourceManager,
    ) -> ExecutionResult:
        """Execute the AI agent."""
        goal = self.get_parameter("goal")
        agent_context = self.get_parameter("context")
        available_tools = self.get_parameter("available_tools")
        max_steps = self.get_parameter("max_steps") or self.DEFAULT_MAX_STEPS
        timeout = self.get_parameter("timeout") or self.DEFAULT_TIMEOUT

        if hasattr(context, "resolve_value"):
            goal = context.resolve_value(goal)
            agent_context = context.resolve_value(agent_context)
            available_tools = context.resolve_value(available_tools)
            max_steps = context.resolve_value(max_steps)
            timeout = context.resolve_value(timeout)

        if not goal:
            self._set_agent_error("Goal is required")
            return {"success": False, "error": "Goal is required", "next_nodes": []}

        # Parse available_tools if string
        if isinstance(available_tools, str):
            try:
                available_tools = json.loads(available_tools)
            except json.JSONDecodeError:
                available_tools = [
                    t.strip() for t in available_tools.split(",") if t.strip()
                ]

        # Convert context to dict if needed
        initial_context: Optional[Dict[str, Any]] = None
        if agent_context is not None:
            if isinstance(agent_context, dict):
                initial_context = agent_context
            elif isinstance(agent_context, str):
                try:
                    initial_context = json.loads(agent_context)
                except json.JSONDecodeError:
                    initial_context = {"context": agent_context}
            else:
                initial_context = {"context": str(agent_context)}

        model = self.get_parameter("model") or self.DEFAULT_MODEL
        if hasattr(context, "resolve_value"):
            model = context.resolve_value(model)

        try:
            from casare_rpa.infrastructure.ai.agent_executor import AgentExecutor

            # Create agent executor
            executor = AgentExecutor(
                max_steps=int(max_steps),
                timeout_seconds=float(timeout),
                model=model,
            )

            # Execute agent
            result = await executor.execute(
                goal=goal,
                context=context,
                manager=manager,
                available_tools=available_tools,
                initial_context=initial_context,
            )

            # Set outputs
            self.set_output_value("result", result.result)
            self.set_output_value("steps_taken", [s.to_dict() for s in result.steps])
            self.set_output_value("step_count", len(result.steps))
            self.set_output_value("total_tokens", result.total_tokens)
            self.set_output_value("execution_time", result.execution_time)
            self.set_output_value("success", result.success)
            self.set_output_value("error", result.error or "")

            logger.info(
                f"AI agent: '{goal[:50]}...' -> "
                f"{'success' if result.success else 'failed'} "
                f"({len(result.steps)} steps, {result.total_tokens} tokens)"
            )

            if result.success:
                return {
                    "success": True,
                    "data": result.to_dict(),
                    "next_nodes": ["exec_out"],
                }
            else:
                return {
                    "success": False,
                    "error": result.error or "Agent failed",
                    "next_nodes": ["exec_error"],
                }

        except ImportError as e:
            error_msg = f"Agent executor not available: {e}"
            self._set_agent_error(error_msg)
            return {"success": False, "error": error_msg, "next_nodes": ["exec_error"]}

        except Exception as e:
            error_msg = str(e)
            self._set_agent_error(error_msg)
            return {"success": False, "error": error_msg, "next_nodes": ["exec_error"]}

    def _set_agent_error(self, error_msg: str) -> None:
        """Set output values for error case."""
        self.set_output_value("result", None)
        self.set_output_value("steps_taken", [])
        self.set_output_value("step_count", 0)
        self.set_output_value("total_tokens", 0)
        self.set_output_value("execution_time", 0.0)
        self.set_output_value("success", False)
        self.set_output_value("error", error_msg)


__all__ = ["AIAgentNode"]
