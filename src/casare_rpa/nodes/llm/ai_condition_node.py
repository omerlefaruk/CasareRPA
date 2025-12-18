"""
CasareRPA - AI Condition Node

Evaluate natural language conditions using LLM.
Returns boolean result with confidence score.
"""

from __future__ import annotations

import json
from typing import Any

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.infrastructure.resources.llm_resource_manager import LLMResourceManager
from casare_rpa.nodes.llm.llm_base import LLMBaseNode


@properties(
    PropertyDef(
        "context",
        PropertyType.ANY,
        required=True,
        label="Context",
        tooltip="Context data for AI evaluation",
    ),
    PropertyDef(
        "condition",
        PropertyType.TEXT,
        default="",
        label="Condition",
        placeholder="Is the email about a complaint?",
        tooltip="Natural language condition to evaluate",
        essential=True,
    ),
    PropertyDef(
        "model",
        PropertyType.STRING,
        default="gpt-4o-mini",
        label="Model",
        tooltip="LLM model for condition evaluation",
    ),
    PropertyDef(
        "temperature",
        PropertyType.FLOAT,
        default=0.0,
        min_value=0.0,
        max_value=2.0,
        label="Temperature",
        tooltip="Low temperature for consistent evaluation",
    ),
)
@node(category="llm")
class AIConditionNode(LLMBaseNode):
    """
    Evaluate a condition using natural language with AI.

    Instead of writing Python expressions, describe the condition in plain English.
    The AI evaluates the context against the condition and returns true/false.

    Example conditions:
    - "Is the email about a complaint?"
    - "Does the invoice total exceed $1000?"
    - "Is this customer a premium member?"
    """

    NODE_NAME = "AI Condition"
    NODE_CATEGORY = "AI/ML"
    NODE_DESCRIPTION = "Evaluate a natural language condition using AI"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name=self.NODE_NAME, **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Execution ports
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_true")
        self.add_exec_output("exec_false")

        # Data inputs
        self.add_input_port("condition", DataType.STRING)
        self.add_input_port("context", DataType.ANY)
        self._define_common_input_ports()

        # Data outputs
        self.add_output_port("result", DataType.BOOLEAN)
        self.add_output_port("confidence", DataType.FLOAT)
        self.add_output_port("reasoning", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def _execute_llm(
        self,
        context: ExecutionContext,
        manager: LLMResourceManager,
    ) -> ExecutionResult:
        """Execute condition evaluation."""
        condition = self.get_parameter("condition")
        eval_context = self.get_parameter("context")

        if hasattr(context, "resolve_value"):
            condition = context.resolve_value(condition)
            eval_context = context.resolve_value(eval_context)

        if not condition:
            self._set_condition_error("Condition is required")
            return {
                "success": False,
                "error": "Condition is required",
                "next_nodes": [],
            }

        # Convert context to string if needed
        if eval_context is not None:
            if isinstance(eval_context, (dict, list)):
                context_str = json.dumps(eval_context, indent=2, default=str)
            else:
                context_str = str(eval_context)
        else:
            context_str = "No context provided"

        model = self.get_parameter("model") or self.DEFAULT_MODEL
        temperature = self.get_parameter("temperature") or 0.0

        if hasattr(context, "resolve_value"):
            model = context.resolve_value(model)

        prompt = f"""Evaluate the following condition against the given context.

Condition: {condition}

Context:
{context_str}

Respond with a JSON object containing:
- "result": true or false (whether the condition is met)
- "confidence": a number between 0.0 and 1.0 indicating certainty
- "reasoning": a brief explanation of your evaluation

Return ONLY the JSON, no other text."""

        try:
            response = await manager.completion(
                prompt=prompt,
                model=model,
                system_prompt="You are a condition evaluator. Analyze the context and determine if the condition is true or false. Be precise and logical.",
                temperature=float(temperature),
                max_tokens=500,
            )

            # Parse response
            content = response.content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

            result_data = json.loads(content)

            result = bool(result_data.get("result", False))
            confidence = float(result_data.get("confidence", 0.5))
            reasoning = str(result_data.get("reasoning", ""))

            self.set_output_value("result", result)
            self.set_output_value("confidence", confidence)
            self.set_output_value("reasoning", reasoning)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.info(
                f"AI condition: '{condition[:50]}...' -> {result} "
                f"(confidence: {confidence:.2f})"
            )

            # Return appropriate exec path based on result
            next_node = "exec_true" if result else "exec_false"
            return {
                "success": True,
                "data": {
                    "result": result,
                    "confidence": confidence,
                    "reasoning": reasoning,
                },
                "next_nodes": [next_node],
            }

        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse AI response: {e}"
            self._set_condition_error(error_msg)
            return {"success": False, "error": error_msg, "next_nodes": []}

        except Exception as e:
            error_msg = str(e)
            self._set_condition_error(error_msg)
            return {"success": False, "error": error_msg, "next_nodes": []}

    def _set_condition_error(self, error_msg: str) -> None:
        """Set output values for error case."""
        self.set_output_value("result", False)
        self.set_output_value("confidence", 0.0)
        self.set_output_value("reasoning", "")
        self.set_output_value("success", False)
        self.set_output_value("error", error_msg)


__all__ = ["AIConditionNode"]
