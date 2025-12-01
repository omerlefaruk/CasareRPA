"""
CasareRPA - LLM Base Node

Abstract base class for all LLM nodes with shared functionality.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Optional

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
    PortType,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.infrastructure.resources.llm_resource_manager import (
    LLMResourceManager,
    LLMConfig,
    LLMProvider,
)


class LLMBaseNode(BaseNode):
    """
    Abstract base class for LLM nodes.

    Provides common functionality:
    - LLM resource manager access
    - Model/provider configuration
    - Token usage tracking
    - Error handling
    - Standard output ports

    Subclasses implement _execute_llm() for specific operations.
    """

    # Default model settings
    DEFAULT_MODEL: str = "gpt-4o-mini"
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 1000

    def __init__(self, node_id: str, name: str = "LLM Node", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name

    def _define_common_input_ports(self) -> None:
        """Define standard LLM input ports."""
        self.add_input_port("model", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port(
            "temperature", PortType.INPUT, DataType.FLOAT, required=False
        )
        self.add_input_port(
            "max_tokens", PortType.INPUT, DataType.INTEGER, required=False
        )
        self.add_input_port(
            "system_prompt", PortType.INPUT, DataType.STRING, required=False
        )

    def _define_common_output_ports(self) -> None:
        """Define standard LLM output ports."""
        self.add_output_port("response", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("tokens_used", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("model_used", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    def _get_llm_manager(self, context: ExecutionContext) -> LLMResourceManager:
        """
        Get or create LLM resource manager from context.

        Args:
            context: Execution context

        Returns:
            LLM resource manager instance
        """
        # Check if manager exists in context
        if hasattr(context, "resources") and "llm" in context.resources:
            return context.resources["llm"]

        # Create new manager
        manager = LLMResourceManager()

        # Configure from context variables or environment
        api_key = self._get_api_key(context)
        provider = self._get_provider(context)

        model = self.get_parameter("model") or self.DEFAULT_MODEL
        model = (
            context.resolve_value(model) if hasattr(context, "resolve_value") else model
        )

        config = LLMConfig(
            provider=provider,
            model=model,
            api_key=api_key,
        )
        manager.configure(config)

        # Store in context for reuse
        if hasattr(context, "resources"):
            context.resources["llm"] = manager

        return manager

    def _get_api_key(self, context: ExecutionContext) -> Optional[str]:
        """Get API key from context or credentials."""
        # Try context variables first
        if hasattr(context, "get_variable"):
            key = context.get_variable("llm_api_key")
            if key:
                return key

        # Try credential manager
        try:
            from casare_rpa.utils.security.credential_manager import credential_manager

            # Try provider-specific keys
            for key_name in ["openai_api_key", "anthropic_api_key", "llm_api_key"]:
                key = credential_manager.get(key_name)
                if key:
                    return key
        except Exception:
            pass

        # Try environment
        import os

        for env_var in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "LLM_API_KEY"]:
            key = os.environ.get(env_var)
            if key:
                return key

        return None

    def _get_provider(self, context: ExecutionContext) -> LLMProvider:
        """Determine LLM provider from model name or config."""
        model = self.get_parameter("model") or self.DEFAULT_MODEL
        if hasattr(context, "resolve_value"):
            model = context.resolve_value(model)

        model_lower = model.lower()

        if "claude" in model_lower:
            return LLMProvider.ANTHROPIC
        elif "azure" in model_lower or model_lower.startswith("azure/"):
            return LLMProvider.AZURE
        elif "ollama" in model_lower or model_lower.startswith("ollama/"):
            return LLMProvider.OLLAMA
        else:
            return LLMProvider.OPENAI

    def _set_error_outputs(self, error_msg: str) -> None:
        """Set output values for error case."""
        self.set_output_value("success", False)
        self.set_output_value("error", error_msg)
        self.set_output_value("response", "")
        self.set_output_value("tokens_used", 0)
        self.set_output_value("model_used", "")

    def _set_success_outputs(
        self,
        response: str,
        tokens_used: int,
        model_used: str,
    ) -> None:
        """Set output values for successful response."""
        self.set_output_value("success", True)
        self.set_output_value("error", "")
        self.set_output_value("response", response)
        self.set_output_value("tokens_used", tokens_used)
        self.set_output_value("model_used", model_used)

    @abstractmethod
    async def _execute_llm(
        self,
        context: ExecutionContext,
        manager: LLMResourceManager,
    ) -> ExecutionResult:
        """
        Execute the LLM operation.

        Args:
            context: Execution context
            manager: LLM resource manager

        Returns:
            Execution result
        """
        ...

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute the LLM node."""
        self.status = NodeStatus.RUNNING

        try:
            # Get LLM manager
            manager = self._get_llm_manager(context)

            # Execute specific LLM operation
            result = await self._execute_llm(context, manager)

            if result.get("success", False):
                self.status = NodeStatus.SUCCESS
            else:
                self.status = NodeStatus.ERROR

            return result

        except ImportError as e:
            error_msg = str(e)
            logger.error(f"LLM dependency error: {error_msg}")
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

        except Exception as e:
            error_msg = f"LLM error: {str(e)}"
            logger.error(error_msg)
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


__all__ = ["LLMBaseNode"]
