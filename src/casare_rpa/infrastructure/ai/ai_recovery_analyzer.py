"""
CasareRPA - AI Recovery Analyzer

LLM-powered error recovery recommendation system that analyzes errors
and suggests appropriate recovery strategies based on context.
"""

from __future__ import annotations

import base64
import json
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger


class RecoveryStrategy(Enum):
    """Available recovery strategies."""

    RETRY = "retry"
    SKIP = "skip"
    FALLBACK = "fallback"
    COMPENSATE = "compensate"
    ABORT = "abort"
    ESCALATE = "escalate"
    MANUAL = "manual"


@dataclass
class RecoveryRecommendation:
    """
    AI-generated recovery recommendation for an error.

    Attributes:
        strategy: Recommended recovery strategy
        confidence: Confidence score (0.0 to 1.0)
        reasoning: Explanation of why this strategy was chosen
        suggested_fix: Optional code/selector fix suggestion
        retry_with_modifications: Modified inputs for retry strategy
        alternative_strategies: Ranked list of alternative strategies
    """

    strategy: RecoveryStrategy
    confidence: float
    reasoning: str
    suggested_fix: str | None = None
    retry_with_modifications: dict[str, Any] | None = None
    alternative_strategies: list[RecoveryStrategy] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "strategy": self.strategy.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "suggested_fix": self.suggested_fix,
            "retry_with_modifications": self.retry_with_modifications,
            "alternative_strategies": [s.value for s in self.alternative_strategies],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecoveryRecommendation:
        """Create from dictionary."""
        return cls(
            strategy=RecoveryStrategy(data.get("strategy", "abort")),
            confidence=data.get("confidence", 0.0),
            reasoning=data.get("reasoning", ""),
            suggested_fix=data.get("suggested_fix"),
            retry_with_modifications=data.get("retry_with_modifications"),
            alternative_strategies=[
                RecoveryStrategy(s) for s in data.get("alternative_strategies", [])
            ],
        )


@dataclass
class ErrorContext:
    """
    Context information about an error for AI analysis.

    Attributes:
        error_type: Type/class of the exception
        error_message: Error message string
        node_type: Type of node that failed
        node_inputs: Input values to the failed node
        node_config: Configuration of the failed node
        screenshot_base64: Base64-encoded screenshot (for browser errors)
        stack_trace: Full stack trace
        execution_history: Recent execution history
        workflow_name: Name of the workflow
        attempt_count: Number of times this has been tried
    """

    error_type: str
    error_message: str
    node_type: str
    node_inputs: dict[str, Any]
    node_config: dict[str, Any]
    screenshot_base64: str | None = None
    stack_trace: str | None = None
    execution_history: list[dict[str, Any]] = field(default_factory=list)
    workflow_name: str = ""
    attempt_count: int = 1


class AIRecoveryAnalyzer:
    """
    LLM-powered error recovery analyzer.

    Analyzes error context and recommends appropriate recovery strategies
    using vision-capable LLMs when screenshots are available.

    Usage:
        analyzer = AIRecoveryAnalyzer()
        recommendation = await analyzer.analyze_error(error_context)
    """

    # System prompt for error analysis
    SYSTEM_PROMPT = """You are an expert RPA error analyst. Your task is to analyze automation errors and recommend recovery strategies.

Available recovery strategies:
- retry: Retry the same operation (good for transient failures, network issues)
- skip: Skip this node and continue (good for non-critical operations)
- fallback: Use an alternative approach (good when primary method fails)
- compensate: Undo previous operations (good for partial failures)
- abort: Stop the workflow (good for critical failures)
- escalate: Notify human operator (good for unexpected situations)
- manual: Requires human intervention (good for authentication, captchas)

Analyze the error context and respond with a JSON object containing:
{
    "strategy": "one of the strategies above",
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation of your choice",
    "suggested_fix": "optional: specific fix suggestion like updated selector or value",
    "retry_with_modifications": {"param": "new_value"} or null,
    "alternative_strategies": ["list", "of", "alternatives"]
}

Consider:
1. Error type and message
2. Node type and what it was trying to do
3. Screenshot context (if provided)
4. How many times this has been attempted
5. Whether the error is likely transient or persistent"""

    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_tokens: int = 1000,
    ) -> None:
        """
        Initialize the AI recovery analyzer.

        Args:
            model: LLM model to use (should support vision for screenshots)
            temperature: Sampling temperature (lower = more deterministic)
            max_tokens: Maximum tokens in response
        """
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._llm_manager: Any | None = None

    async def _get_llm_manager(self) -> Any:
        """Get or create LLM resource manager."""
        if self._llm_manager is None:
            from casare_rpa.infrastructure.resources.llm_resource_manager import (
                LLMConfig,
                LLMProvider,
                LLMResourceManager,
            )

            self._llm_manager = LLMResourceManager()

            # Detect provider from model name
            if "claude" in self._model.lower():
                provider = LLMProvider.ANTHROPIC
            else:
                provider = LLMProvider.OPENAI

            config = LLMConfig(
                provider=provider,
                model=self._model,
            )
            self._llm_manager.configure(config)

        return self._llm_manager

    def _build_error_prompt(self, context: ErrorContext) -> str:
        """Build the error analysis prompt."""
        prompt_parts = [
            "## Error Analysis Request",
            "",
            f"**Error Type**: {context.error_type}",
            f"**Error Message**: {context.error_message}",
            f"**Node Type**: {context.node_type}",
            f"**Workflow**: {context.workflow_name or 'Unknown'}",
            f"**Attempt Count**: {context.attempt_count}",
        ]

        if context.node_inputs:
            prompt_parts.extend(
                [
                    "",
                    "**Node Inputs**:",
                    "```json",
                    json.dumps(self._sanitize_for_json(context.node_inputs), indent=2),
                    "```",
                ]
            )

        if context.node_config:
            prompt_parts.extend(
                [
                    "",
                    "**Node Configuration**:",
                    "```json",
                    json.dumps(self._sanitize_for_json(context.node_config), indent=2),
                    "```",
                ]
            )

        if context.stack_trace:
            # Include last 10 lines of stack trace
            trace_lines = context.stack_trace.strip().split("\n")[-10:]
            prompt_parts.extend(
                [
                    "",
                    "**Stack Trace (last 10 lines)**:",
                    "```",
                    "\n".join(trace_lines),
                    "```",
                ]
            )

        if context.execution_history:
            # Include last 5 execution entries
            recent_history = context.execution_history[-5:]
            prompt_parts.extend(
                [
                    "",
                    "**Recent Execution History**:",
                    "```json",
                    json.dumps(recent_history, indent=2, default=str),
                    "```",
                ]
            )

        prompt_parts.extend(
            [
                "",
                "Please analyze this error and recommend a recovery strategy.",
                "If a screenshot is provided, use it to understand the current state.",
            ]
        )

        return "\n".join(prompt_parts)

    def _sanitize_for_json(self, obj: Any) -> Any:
        """Sanitize object for JSON serialization (remove non-serializable items)."""
        if isinstance(obj, dict):
            return {
                k: self._sanitize_for_json(v) for k, v in obj.items() if self._is_serializable(v)
            }
        elif isinstance(obj, (list, tuple)):
            return [self._sanitize_for_json(item) for item in obj if self._is_serializable(item)]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            return str(obj)

    def _is_serializable(self, obj: Any) -> bool:
        """Check if object is JSON-serializable."""
        try:
            json.dumps(obj)
            return True
        except (TypeError, ValueError):
            return False

    def _parse_llm_response(self, response_text: str) -> RecoveryRecommendation:
        """Parse LLM response into RecoveryRecommendation."""
        # Extract JSON from response (may be wrapped in markdown code blocks)
        content = response_text.strip()
        if "```json" in content:
            start = content.index("```json") + 7
            end = content.index("```", start)
            content = content[start:end].strip()
        elif "```" in content:
            start = content.index("```") + 3
            end = content.index("```", start)
            content = content[start:end].strip()

        try:
            data = json.loads(content)
            return RecoveryRecommendation.from_dict(data)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            # Return default recommendation
            return RecoveryRecommendation(
                strategy=RecoveryStrategy.ABORT,
                confidence=0.3,
                reasoning=f"Failed to parse AI response: {response_text[:200]}",
            )

    async def analyze_error(
        self,
        error: Exception,
        node_context: dict[str, Any],
        screenshot: bytes | None = None,
        execution_history: list[dict[str, Any]] | None = None,
    ) -> RecoveryRecommendation:
        """
        Analyze an error and recommend a recovery strategy.

        Args:
            error: The exception that occurred
            node_context: Context about the failed node including:
                - node_type: Type of the node
                - node_inputs: Input values
                - node_config: Configuration
                - workflow_name: Name of workflow
                - attempt_count: How many times tried
            screenshot: Optional screenshot bytes (PNG/JPEG)
            execution_history: Recent execution history

        Returns:
            RecoveryRecommendation with strategy and details
        """
        try:
            # Build error context
            screenshot_b64 = None
            if screenshot:
                screenshot_b64 = base64.b64encode(screenshot).decode("utf-8")

            context = ErrorContext(
                error_type=type(error).__name__,
                error_message=str(error),
                node_type=node_context.get("node_type", "Unknown"),
                node_inputs=node_context.get("node_inputs", {}),
                node_config=node_context.get("node_config", {}),
                screenshot_base64=screenshot_b64,
                stack_trace=traceback.format_exc(),
                execution_history=execution_history or [],
                workflow_name=node_context.get("workflow_name", ""),
                attempt_count=node_context.get("attempt_count", 1),
            )

            return await self._analyze_with_llm(context)

        except Exception as e:
            logger.error(f"AI recovery analysis failed: {e}")
            # Return safe default on failure
            return RecoveryRecommendation(
                strategy=RecoveryStrategy.ABORT,
                confidence=0.5,
                reasoning=f"AI analysis failed: {e}. Recommending abort for safety.",
                alternative_strategies=[
                    RecoveryStrategy.RETRY,
                    RecoveryStrategy.ESCALATE,
                ],
            )

    async def _analyze_with_llm(self, context: ErrorContext) -> RecoveryRecommendation:
        """Perform LLM analysis of error context."""
        manager = await self._get_llm_manager()
        prompt = self._build_error_prompt(context)

        try:
            if context.screenshot_base64:
                # Use vision model for screenshot analysis
                from casare_rpa.infrastructure.resources.llm_resource_manager import (
                    ImageContent,
                )

                images = [
                    ImageContent(
                        base64_data=context.screenshot_base64,
                        media_type="image/png",
                    )
                ]

                response = await manager.vision_completion(
                    prompt=prompt,
                    images=images,
                    model=self._model,
                    system_prompt=self.SYSTEM_PROMPT,
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                )
            else:
                # Text-only analysis
                response = await manager.completion(
                    prompt=prompt,
                    model=self._model,
                    system_prompt=self.SYSTEM_PROMPT,
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                )

            logger.debug(
                f"AI recovery analysis completed: model={response.model}, "
                f"tokens={response.total_tokens}"
            )

            return self._parse_llm_response(response.content)

        except ImportError as e:
            logger.error(f"LLM dependencies not available: {e}")
            raise
        except Exception as e:
            logger.error(f"LLM completion failed: {e}")
            raise

    async def analyze_error_from_context(
        self,
        error_context: ErrorContext,
    ) -> RecoveryRecommendation:
        """
        Analyze error from pre-built ErrorContext.

        Args:
            error_context: Complete error context

        Returns:
            RecoveryRecommendation with strategy and details
        """
        try:
            return await self._analyze_with_llm(error_context)
        except Exception as e:
            logger.error(f"AI recovery analysis failed: {e}")
            return RecoveryRecommendation(
                strategy=RecoveryStrategy.ABORT,
                confidence=0.5,
                reasoning=f"AI analysis failed: {e}. Recommending abort for safety.",
                alternative_strategies=[
                    RecoveryStrategy.RETRY,
                    RecoveryStrategy.ESCALATE,
                ],
            )

    def get_default_recommendation(
        self,
        error: Exception,
        node_type: str,
    ) -> RecoveryRecommendation:
        """
        Get a default recommendation without AI analysis.

        Uses heuristics based on error type and node type.

        Args:
            error: The exception
            node_type: Type of node that failed

        Returns:
            Heuristic-based recommendation
        """
        error_type = type(error).__name__
        error_msg = str(error).lower()

        # Timeout errors - often transient, retry
        if "timeout" in error_type.lower() or "timeout" in error_msg:
            return RecoveryRecommendation(
                strategy=RecoveryStrategy.RETRY,
                confidence=0.7,
                reasoning="Timeout errors are often transient. Retry recommended.",
                retry_with_modifications={"timeout": "extended"},
                alternative_strategies=[RecoveryStrategy.SKIP, RecoveryStrategy.ABORT],
            )

        # Element not found - might need selector update
        if "element" in error_msg and ("not found" in error_msg or "not exist" in error_msg):
            return RecoveryRecommendation(
                strategy=RecoveryStrategy.FALLBACK,
                confidence=0.6,
                reasoning="Element not found. Try alternative selector or approach.",
                alternative_strategies=[RecoveryStrategy.RETRY, RecoveryStrategy.SKIP],
            )

        # Network errors - retry with backoff
        if any(x in error_msg for x in ["network", "connection", "refused", "unreachable"]):
            return RecoveryRecommendation(
                strategy=RecoveryStrategy.RETRY,
                confidence=0.8,
                reasoning="Network error detected. Retry with backoff recommended.",
                retry_with_modifications={"delay": 5000},
                alternative_strategies=[RecoveryStrategy.ABORT],
            )

        # Authentication errors - escalate
        if any(x in error_msg for x in ["auth", "login", "permission", "forbidden", "401", "403"]):
            return RecoveryRecommendation(
                strategy=RecoveryStrategy.ESCALATE,
                confidence=0.8,
                reasoning="Authentication/permission error requires human intervention.",
                alternative_strategies=[RecoveryStrategy.ABORT],
            )

        # Validation errors - likely configuration issue
        if any(x in error_msg for x in ["validation", "invalid", "required"]):
            return RecoveryRecommendation(
                strategy=RecoveryStrategy.ABORT,
                confidence=0.7,
                reasoning="Validation error indicates configuration issue. Review inputs.",
                alternative_strategies=[RecoveryStrategy.SKIP],
            )

        # Default: abort for unknown errors
        return RecoveryRecommendation(
            strategy=RecoveryStrategy.ABORT,
            confidence=0.5,
            reasoning=f"Unknown error type ({error_type}). Aborting for safety.",
            alternative_strategies=[RecoveryStrategy.RETRY, RecoveryStrategy.ESCALATE],
        )


__all__ = [
    "AIRecoveryAnalyzer",
    "RecoveryRecommendation",
    "RecoveryStrategy",
    "ErrorContext",
]
