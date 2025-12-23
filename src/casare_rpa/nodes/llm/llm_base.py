"""
CasareRPA - LLM Base Node

Abstract base class for all LLM nodes with shared functionality.
Uses CredentialAwareMixin for vault-integrated credential resolution.
"""

from __future__ import annotations

import os
from abc import abstractmethod
from typing import Any

from loguru import logger

from casare_rpa.domain.credentials import CredentialAwareMixin
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.infrastructure.resources.llm_resource_manager import (
    LLMConfig,
    LLMProvider,
    LLMResourceManager,
)


@properties()
@node(category="llm")
class LLMBaseNode(CredentialAwareMixin, BaseNode):
    """
    Abstract base class for LLM nodes.

    Provides common functionality:
    - LLM resource manager access
    - Model/provider configuration
    - Token usage tracking
    - Error handling
    - Standard output ports

    Credential Resolution (in order):
    1. Vault lookup (via credential_name parameter)
    2. Context variable (llm_api_key)
    3. Environment variables (OPENAI_API_KEY, ANTHROPIC_API_KEY, LLM_API_KEY)

    Subclasses implement _execute_llm() for specific operations.
    """

    # @category: integration
    # @requires: none
    # @ports: none -> none

    # Default model settings
    DEFAULT_MODEL: str = "gemini-3-flash-preview"
    DEFAULT_TEMPERATURE: float = 0.7
    DEFAULT_MAX_TOKENS: int = 1000

    def __init__(self, node_id: str, name: str = "LLM Node", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name

    def _define_common_input_ports(self) -> None:
        """Define standard LLM input ports."""
        # Credential ports
        self.add_input_port("credential_name", DataType.STRING, required=False)
        self.add_input_port("api_key", DataType.STRING, required=False)
        # Model config ports
        self.add_input_port("model", DataType.STRING, required=False)
        self.add_input_port("temperature", DataType.FLOAT, required=False)
        self.add_input_port("max_tokens", DataType.INTEGER, required=False)
        self.add_input_port("system_prompt", DataType.STRING, required=False)

    def _define_common_output_ports(self) -> None:
        """Define standard LLM output ports."""
        self.add_output_port("response", DataType.STRING)
        self.add_output_port("tokens_used", DataType.INTEGER)
        self.add_output_port("model_used", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def _get_llm_manager(self, context: ExecutionContext) -> LLMResourceManager:
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
        api_key = await self._get_api_key(context)
        provider = self._get_provider(context)

        model = self.get_parameter("model") or self.DEFAULT_MODEL
        model = context.resolve_value(model) if hasattr(context, "resolve_value") else model

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

    async def _get_api_key(self, context: ExecutionContext) -> str | None:
        """
        Get API key using unified credential resolution.

        Resolution order:
        1. Vault lookup (via credential_name parameter)
        2. Direct parameter (api_key)
        3. Context variable (llm_api_key)
        4. Environment variables (OPENAI_API_KEY, ANTHROPIC_API_KEY, LLM_API_KEY)

        Args:
            context: ExecutionContext with credential provider

        Returns:
            API key string or None
        """
        # Use CredentialAwareMixin for vault and direct params
        api_key = await self.resolve_credential(
            context,
            credential_name_param="credential_name",
            direct_param="api_key",
            context_var="llm_api_key",
            credential_field="api_key",
            required=False,
        )

        if api_key:
            return api_key

        # Fallback to environment variables for multiple providers
        for env_var in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "LLM_API_KEY"]:
            key = os.environ.get(env_var)
            if key:
                logger.debug(f"Using LLM API key from {env_var}")
                return key

        # Fallback: try legacy credential manager
        try:
            from casare_rpa.utils.security.credential_manager import credential_manager

            for key_name in ["openai_api_key", "anthropic_api_key", "llm_api_key"]:
                key = credential_manager.get(key_name)
                if key:
                    logger.debug(f"Using legacy credential: {key_name}")
                    return key
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Legacy credential lookup failed: {e}")

        return None

    def _get_provider(self, context: ExecutionContext) -> LLMProvider:
        """Determine LLM provider from model name or config."""
        model = self.get_parameter("model") or self.DEFAULT_MODEL

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
            manager = await self._get_llm_manager(context)

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
