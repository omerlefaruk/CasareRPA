"""
CasareRPA - AI Decision Table Node

Fuzzy-match rules in a decision table using AI.
Supports complex conditions with natural language matching.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from loguru import logger

from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    PortType,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.infrastructure.resources.llm_resource_manager import LLMResourceManager
from casare_rpa.nodes.llm.llm_base import LLMBaseNode


class AIDecisionTableNode(LLMBaseNode):
    """
    Evaluate a decision table using AI fuzzy matching.

    Decision table format:
    {
        "rules": [
            {
                "conditions": {"field1": "value1", "field2": "value2"},
                "action": "action_name",
                "priority": 1
            },
            ...
        ],
        "default_action": "fallback_action"
    }

    The AI evaluates the context against each rule's conditions,
    selecting the best matching rule even with approximate matches.
    """

    NODE_NAME = "AI Decision Table"
    NODE_CATEGORY = "AI/ML"
    NODE_DESCRIPTION = "Evaluate decision table with AI fuzzy matching"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name=self.NODE_NAME, **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Execution ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        # Data inputs
        self.add_input_port("decision_table", PortType.INPUT, DataType.DICT)
        self.add_input_port("context", PortType.INPUT, DataType.ANY)
        self._define_common_input_ports()

        # Data outputs
        self.add_output_port("matched_action", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("matched_rule_index", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("confidence", PortType.OUTPUT, DataType.FLOAT)
        self.add_output_port("reasoning", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("all_matches", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def _execute_llm(
        self,
        context: ExecutionContext,
        manager: LLMResourceManager,
    ) -> ExecutionResult:
        """Execute decision table evaluation."""
        decision_table = self.get_parameter("decision_table")
        eval_context = self.get_parameter("context")

        if hasattr(context, "resolve_value"):
            decision_table = context.resolve_value(decision_table)
            eval_context = context.resolve_value(eval_context)

        # Parse decision table if string
        if isinstance(decision_table, str):
            try:
                decision_table = json.loads(decision_table)
            except json.JSONDecodeError as e:
                self._set_decision_error(f"Invalid decision table JSON: {e}")
                return {
                    "success": False,
                    "error": f"Invalid JSON: {e}",
                    "next_nodes": [],
                }

        if not decision_table or not isinstance(decision_table, dict):
            self._set_decision_error("Decision table is required")
            return {
                "success": False,
                "error": "Decision table is required",
                "next_nodes": [],
            }

        rules = decision_table.get("rules", [])
        default_action = decision_table.get("default_action", "no_action")

        if not rules:
            self._set_decision_error("Decision table has no rules")
            return {"success": False, "error": "No rules defined", "next_nodes": []}

        # Convert context to string
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

        # Format rules for prompt
        rules_str = self._format_rules_for_prompt(rules)

        prompt = f"""Evaluate the following decision table rules against the given context.

Decision Table Rules:
{rules_str}

Default Action: {default_action}

Context to evaluate:
{context_str}

For each rule, determine how well the context matches the conditions (0.0 to 1.0).
Then select the best matching rule considering both match score and priority.

Respond with a JSON object containing:
- "matched_rule_index": index of best matching rule (0-based), or -1 if using default
- "matched_action": the action from the matched rule, or default_action if no match
- "confidence": confidence in the match (0.0 to 1.0)
- "reasoning": explanation of why this rule was selected
- "all_matches": array of objects with rule_index, score, and matched_conditions for each rule

Return ONLY the JSON, no other text."""

        try:
            response = await manager.completion(
                prompt=prompt,
                model=model,
                system_prompt="You are a decision engine. Evaluate rules against context using fuzzy matching. Consider semantic similarity, not just exact matches.",
                temperature=float(temperature),
                max_tokens=1000,
            )

            # Parse response
            content = response.content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

            result_data = json.loads(content)

            matched_rule_index = int(result_data.get("matched_rule_index", -1))
            matched_action = str(result_data.get("matched_action", default_action))
            confidence = float(result_data.get("confidence", 0.5))
            reasoning = str(result_data.get("reasoning", ""))
            all_matches = result_data.get("all_matches", [])

            # Validate matched_rule_index
            if matched_rule_index >= len(rules):
                matched_rule_index = -1
                matched_action = default_action
                confidence = 0.3

            self.set_output_value("matched_action", matched_action)
            self.set_output_value("matched_rule_index", matched_rule_index)
            self.set_output_value("confidence", confidence)
            self.set_output_value("reasoning", reasoning)
            self.set_output_value("all_matches", all_matches)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.info(
                f"AI decision table: rule {matched_rule_index} -> '{matched_action}' "
                f"(confidence: {confidence:.2f})"
            )

            return {
                "success": True,
                "data": {
                    "matched_action": matched_action,
                    "matched_rule_index": matched_rule_index,
                    "confidence": confidence,
                    "reasoning": reasoning,
                    "all_matches": all_matches,
                },
                "next_nodes": ["exec_out"],
            }

        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse AI response: {e}"
            self._set_decision_error(error_msg)
            return {"success": False, "error": error_msg, "next_nodes": []}

        except Exception as e:
            error_msg = str(e)
            self._set_decision_error(error_msg)
            return {"success": False, "error": error_msg, "next_nodes": []}

    def _format_rules_for_prompt(self, rules: List[Dict[str, Any]]) -> str:
        """Format rules as a readable string for the prompt."""
        lines = []
        for i, rule in enumerate(rules):
            conditions = rule.get("conditions", {})
            action = rule.get("action", "no_action")
            priority = rule.get("priority", 0)

            cond_str = ", ".join(f"{k}={v}" for k, v in conditions.items())
            lines.append(
                f"Rule {i}: IF ({cond_str}) THEN action='{action}' [priority={priority}]"
            )

        return "\n".join(lines)

    def _set_decision_error(self, error_msg: str) -> None:
        """Set output values for error case."""
        self.set_output_value("matched_action", "")
        self.set_output_value("matched_rule_index", -1)
        self.set_output_value("confidence", 0.0)
        self.set_output_value("reasoning", "")
        self.set_output_value("all_matches", [])
        self.set_output_value("success", False)
        self.set_output_value("error", error_msg)


__all__ = ["AIDecisionTableNode"]
