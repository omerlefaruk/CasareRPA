"""
CasareRPA - AI Recovery Node

LLM-powered error recovery node that analyzes errors and recommends
appropriate recovery strategies based on context and screenshots.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)
from casare_rpa.infrastructure.execution import ExecutionContext


@properties(
    PropertyDef(
        "model",
        PropertyType.STRING,
        default="gpt-4o",
        label="AI Model",
        tooltip="LLM model for error analysis (vision-capable recommended)",
        placeholder="gpt-4o",
    ),
    PropertyDef(
        "use_screenshot",
        PropertyType.BOOLEAN,
        default=True,
        label="Analyze Screenshot",
        tooltip="Include page screenshot in analysis (for browser errors)",
    ),
    PropertyDef(
        "fallback_to_heuristic",
        PropertyType.BOOLEAN,
        default=True,
        label="Fallback to Heuristic",
        tooltip="Use heuristic analysis if AI fails",
    ),
    PropertyDef(
        "min_confidence",
        PropertyType.FLOAT,
        default=0.5,
        min_value=0.0,
        max_value=1.0,
        label="Min Confidence",
        tooltip="Minimum confidence threshold to accept AI recommendation",
    ),
)
@node(category="error_handling")
class AIRecoveryNode(BaseNode):
    """
    AI-powered error recovery analysis node.

    Analyzes error context using LLM to recommend recovery strategies.
    Integrates with vision models to analyze screenshots for browser errors.

    Input Ports:
        - error_message: Error message string
        - error_type: Type/class of the exception
        - error_node: ID of the node that failed
        - stack_trace: Optional stack trace
        - screenshot: Optional screenshot bytes (for browser errors)
        - execution_history: Optional recent execution history

    Output Ports:
        - strategy: Recommended recovery strategy
        - confidence: Confidence score (0.0 to 1.0)
        - reasoning: Explanation of the recommendation
        - suggested_fix: Optional fix suggestion
        - retry_modifications: Optional modified parameters for retry
        - alternatives: List of alternative strategies
    """

    # @category: error_handling
    # @requires: litellm
    # @ports: error_message, error_type, error_node, stack_trace, screenshot, execution_history -> strategy, confidence, reasoning, suggested_fix, retry_modifications, alternatives

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize AI Recovery node."""
        super().__init__(node_id, config)
        self.name = "AI Recovery"
        self.node_type = "AIRecoveryNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Input ports
        self.add_input_port("error_message", DataType.STRING)
        self.add_input_port("error_type", DataType.STRING)
        self.add_input_port("error_node", DataType.STRING)
        self.add_input_port("stack_trace", DataType.STRING, required=False)
        self.add_input_port("screenshot", DataType.BYTES, required=False)
        self.add_input_port("execution_history", DataType.LIST, required=False)
        self.add_input_port("node_context", DataType.DICT, required=False)

        # Output ports
        self.add_output_port("strategy", DataType.STRING)
        self.add_output_port("confidence", DataType.FLOAT)
        self.add_output_port("reasoning", DataType.STRING)
        self.add_output_port("suggested_fix", DataType.STRING)
        self.add_output_port("retry_modifications", DataType.DICT)
        self.add_output_port("alternatives", DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute AI recovery analysis.

        Args:
            context: Execution context

        Returns:
            Result with recovery recommendation
        """
        self.status = NodeStatus.RUNNING

        try:
            # Get inputs
            error_message = self.get_input_value("error_message") or "Unknown error"
            error_type = self.get_input_value("error_type") or "Exception"
            error_node = self.get_input_value("error_node") or ""
            stack_trace = self.get_input_value("stack_trace")
            screenshot = self.get_input_value("screenshot")
            execution_history = self.get_input_value("execution_history") or []
            node_context = self.get_input_value("node_context") or {}

            # Get parameters
            model = self.get_parameter("model", "gpt-4o")
            use_screenshot = self.get_parameter("use_screenshot", True)
            fallback_to_heuristic = self.get_parameter("fallback_to_heuristic", True)
            min_confidence = self.get_parameter("min_confidence", 0.5)

            # Build node context if not provided
            if not node_context:
                node_context = {
                    "node_type": error_node,
                    "node_inputs": {},
                    "node_config": {},
                    "workflow_name": getattr(context, "workflow_name", ""),
                    "attempt_count": 1,
                }

            # Add workflow context
            node_context["workflow_name"] = getattr(context, "workflow_name", "")

            # Get screenshot if enabled and available from context
            screenshot_bytes: Optional[bytes] = None
            if use_screenshot:
                if screenshot:
                    screenshot_bytes = screenshot
                elif hasattr(context, "get_active_page"):
                    page = context.get_active_page()
                    if page:
                        try:
                            screenshot_bytes = await page.screenshot(type="png")
                        except Exception as e:
                            logger.warning(f"Failed to capture screenshot: {e}")

            # Perform AI analysis
            recommendation = await self._analyze_error(
                error_message=error_message,
                error_type=error_type,
                node_context=node_context,
                screenshot=screenshot_bytes,
                execution_history=execution_history,
                model=model,
            )

            # Check confidence threshold
            if recommendation.confidence < min_confidence and fallback_to_heuristic:
                logger.info(
                    f"AI confidence {recommendation.confidence:.1%} below threshold "
                    f"{min_confidence:.1%}, using heuristic"
                )
                recommendation = await self._get_heuristic_recommendation(
                    error_message=error_message,
                    error_type=error_type,
                    node_type=node_context.get("node_type", ""),
                )

            # Set outputs
            self.set_output_value("strategy", recommendation.strategy.value)
            self.set_output_value("confidence", recommendation.confidence)
            self.set_output_value("reasoning", recommendation.reasoning)
            self.set_output_value("suggested_fix", recommendation.suggested_fix or "")
            self.set_output_value(
                "retry_modifications",
                recommendation.retry_with_modifications or {},
            )
            self.set_output_value(
                "alternatives",
                [s.value for s in recommendation.alternative_strategies],
            )

            logger.info(
                f"AI Recovery recommendation: {recommendation.strategy.value} "
                f"(confidence: {recommendation.confidence:.1%})"
            )

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": recommendation.to_dict(),
                "next_nodes": ["exec_out"],
            }

        except ImportError as e:
            error_msg = f"LLM dependencies not available: {e}"
            logger.error(error_msg)
            return self._handle_analysis_failure(error_msg, fallback_to_heuristic)

        except Exception as e:
            error_msg = f"AI recovery analysis failed: {e}"
            logger.error(error_msg)
            return self._handle_analysis_failure(error_msg, fallback_to_heuristic)

    async def _analyze_error(
        self,
        error_message: str,
        error_type: str,
        node_context: Dict[str, Any],
        screenshot: Optional[bytes],
        execution_history: List[Dict[str, Any]],
        model: str,
    ) -> Any:
        """Perform AI analysis of the error."""
        from casare_rpa.infrastructure.ai.ai_recovery_analyzer import (
            AIRecoveryAnalyzer,
        )

        analyzer = AIRecoveryAnalyzer(model=model)

        # Create exception for analysis
        class ReconstructedError(Exception):
            pass

        error = ReconstructedError(error_message)
        error.__class__.__name__ = error_type

        return await analyzer.analyze_error(
            error=error,
            node_context=node_context,
            screenshot=screenshot,
            execution_history=execution_history,
        )

    async def _get_heuristic_recommendation(
        self,
        error_message: str,
        error_type: str,
        node_type: str,
    ) -> Any:
        """Get heuristic-based recommendation."""
        from casare_rpa.infrastructure.ai.ai_recovery_analyzer import (
            AIRecoveryAnalyzer,
        )

        analyzer = AIRecoveryAnalyzer()

        class ReconstructedError(Exception):
            pass

        error = ReconstructedError(error_message)
        error.__class__.__name__ = error_type

        return analyzer.get_default_recommendation(error, node_type)

    def _handle_analysis_failure(
        self,
        error_msg: str,
        fallback_to_heuristic: bool,
    ) -> ExecutionResult:
        """Handle failure in AI analysis."""
        from casare_rpa.infrastructure.ai.ai_recovery_analyzer import (
            RecoveryStrategy,
        )

        # Set safe default outputs
        self.set_output_value("strategy", RecoveryStrategy.ABORT.value)
        self.set_output_value("confidence", 0.3)
        self.set_output_value("reasoning", error_msg)
        self.set_output_value("suggested_fix", "")
        self.set_output_value("retry_modifications", {})
        self.set_output_value(
            "alternatives",
            [RecoveryStrategy.ESCALATE.value, RecoveryStrategy.RETRY.value],
        )

        self.status = NodeStatus.SUCCESS  # Node succeeded, analysis failed
        return {
            "success": True,
            "data": {
                "strategy": RecoveryStrategy.ABORT.value,
                "confidence": 0.3,
                "reasoning": error_msg,
                "analysis_failed": True,
            },
            "next_nodes": ["exec_out"],
        }


__all__ = ["AIRecoveryNode"]
