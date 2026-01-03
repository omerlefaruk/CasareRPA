"""
CasareRPA - AI Switch Node

Multi-way branching using natural language classification.
Routes execution to one of multiple output paths based on AI analysis.
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
        tooltip="Context data for AI classification",
    ),
    PropertyDef(
        "question",
        PropertyType.TEXT,
        default="",
        label="Question",
        placeholder="What type of document is this?",
        tooltip="Question to determine which branch to take",
        essential=True,
    ),
    PropertyDef(
        "options",
        PropertyType.STRING,
        default="",
        label="Options",
        placeholder="invoice, receipt, contract, other",
        tooltip="Comma-separated list of branch options",
        essential=True,
    ),
    PropertyDef(
        "model",
        PropertyType.STRING,
        default="gpt-4o-mini",
        label="Model",
        tooltip="LLM model to use",
    ),
    PropertyDef(
        "temperature",
        PropertyType.FLOAT,
        default=0.0,
        min_value=0.0,
        max_value=2.0,
        label="Temperature",
        tooltip="Low temperature for consistent branching",
    ),
)
@node(category="llm", exec_outputs=["exec_default"])
class AISwitchNode(LLMBaseNode):
    """
    Multi-way branching using AI classification.

    Given a question and a list of options, the AI determines which option
    best matches the context and routes execution accordingly.

    Example:
    - Question: "What type of document is this?"
    - Options: ["invoice", "receipt", "contract", "other"]
    - The AI analyzes the context and routes to the matching exec port.
    """

    NODE_NAME = "AI Switch"
    NODE_CATEGORY = "AI/ML"
    NODE_DESCRIPTION = "Multi-way branch using AI classification"

    # Maximum number of dynamic output ports
    MAX_OPTIONS = 10

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name=self.NODE_NAME, **kwargs)
        self._options: list[str] = []
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Execution input
        self.add_exec_input("exec_in")

        # Data inputs
        self.add_input_port("question", DataType.STRING)
        self.add_input_port("options", DataType.LIST)
        self.add_input_port("context", DataType.ANY)
        self._define_common_input_ports()

        # Data outputs
        self.add_output_port("selected_option", DataType.STRING)
        self.add_output_port("confidence", DataType.FLOAT)
        self.add_output_port("reasoning", DataType.STRING)
        self.add_output_port("all_scores", DataType.DICT)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

        # Default exec output (fallback)
        self.add_exec_output("exec_default")

    def _update_dynamic_ports(self, options: list[str]) -> None:
        """Update dynamic exec output ports based on options."""
        # Remove old dynamic ports
        for old_option in self._options:
            port_name = f"exec_{self._sanitize_port_name(old_option)}"
            if hasattr(self, "_output_ports") and port_name in self._output_ports:
                del self._output_ports[port_name]

        # Add new dynamic ports
        self._options = options[: self.MAX_OPTIONS]
        for option in self._options:
            port_name = f"exec_{self._sanitize_port_name(option)}"
            if not hasattr(self, "_output_ports") or port_name not in self._output_ports:
                self.add_exec_output(port_name)

    def _sanitize_port_name(self, option: str) -> str:
        """Convert option to valid port name."""
        return option.lower().replace(" ", "_").replace("-", "_")[:20]

    async def _execute_llm(
        self,
        context: ExecutionContext,
        manager: LLMResourceManager,
    ) -> ExecutionResult:
        """Execute switch classification."""
        question = self.get_parameter("question")
        options = self.get_parameter("options")
        eval_context = self.get_parameter("context")

        if not question:
            self._set_switch_error("Question is required")
            return {"success": False, "error": "Question is required", "next_nodes": []}

        # Parse options if string
        if isinstance(options, str):
            try:
                options = json.loads(options)
            except json.JSONDecodeError:
                options = [o.strip() for o in options.split(",") if o.strip()]

        if not options or not isinstance(options, list):
            self._set_switch_error("Options list is required")
            return {
                "success": False,
                "error": "Options list is required",
                "next_nodes": [],
            }

        # Update dynamic ports
        self._update_dynamic_ports(options)

        # Convert context to string
        if eval_context is not None:
            if isinstance(eval_context, dict | list):
                context_str = json.dumps(eval_context, indent=2, default=str)
            else:
                context_str = str(eval_context)
        else:
            context_str = "No context provided"

        model = self.get_parameter("model") or self.DEFAULT_MODEL
        temperature = self.get_parameter("temperature") or 0.0

        options_str = ", ".join(f'"{o}"' for o in options)

        prompt = f"""Given the following question and context, classify into one of these options: {options_str}

Question: {question}

Context:
{context_str}

Respond with a JSON object containing:
- "selected": the chosen option (must be exactly one from the list)
- "confidence": a number between 0.0 and 1.0 indicating certainty
- "reasoning": a brief explanation of your choice
- "scores": an object mapping each option to its score (0.0-1.0)

Return ONLY the JSON, no other text."""

        try:
            response = await manager.completion(
                prompt=prompt,
                model=model,
                system_prompt="You are a classifier. Analyze the context and select the best matching option. Be precise.",
                temperature=float(temperature),
                max_tokens=600,
            )

            # Parse response
            content = response.content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

            result_data = json.loads(content)

            selected = str(result_data.get("selected", ""))
            confidence = float(result_data.get("confidence", 0.5))
            reasoning = str(result_data.get("reasoning", ""))
            all_scores = result_data.get("scores", {})

            # Validate selected option
            if selected not in options:
                # Try to find closest match
                selected_lower = selected.lower()
                for opt in options:
                    if opt.lower() == selected_lower:
                        selected = opt
                        break
                else:
                    # Default to first option with low confidence
                    selected = options[0]
                    confidence = 0.3
                    reasoning = f"AI selected '{result_data.get('selected')}' which is not in options. Defaulting to '{selected}'."

            self.set_output_value("selected_option", selected)
            self.set_output_value("confidence", confidence)
            self.set_output_value("reasoning", reasoning)
            self.set_output_value("all_scores", all_scores)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.info(
                f"AI switch: '{question[:30]}...' -> {selected} (confidence: {confidence:.2f})"
            )

            # Determine next exec port
            port_name = f"exec_{self._sanitize_port_name(selected)}"
            return {
                "success": True,
                "data": {
                    "selected_option": selected,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "all_scores": all_scores,
                },
                "next_nodes": [port_name],
            }

        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse AI response: {e}"
            self._set_switch_error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "next_nodes": ["exec_default"],
            }

        except Exception as e:
            error_msg = str(e)
            self._set_switch_error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "next_nodes": ["exec_default"],
            }

    def _set_switch_error(self, error_msg: str) -> None:
        """Set output values for error case."""
        self.set_output_value("selected_option", "")
        self.set_output_value("confidence", 0.0)
        self.set_output_value("reasoning", "")
        self.set_output_value("all_scores", {})
        self.set_output_value("success", False)
        self.set_output_value("error", error_msg)


__all__ = ["AISwitchNode"]
