"""
CasareRPA - Telegram Base Node

Abstract base class for all Telegram nodes with shared functionality.
"""

from __future__ import annotations

import os
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
from casare_rpa.infrastructure.resources.telegram_client import (
    TelegramClient,
    TelegramConfig,
    TelegramAPIError,
)


class TelegramBaseNode(BaseNode):
    """
    Abstract base class for Telegram nodes.

    Provides common functionality:
    - Telegram client access
    - Bot token configuration from credentials/env
    - Error handling
    - Standard output ports

    Subclasses implement _execute_telegram() for specific operations.
    """

    def __init__(
        self, node_id: str, name: str = "Telegram Node", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self._client: Optional[TelegramClient] = None

    def _define_common_input_ports(self) -> None:
        """Define standard Telegram input ports."""
        self.add_input_port(
            "bot_token", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "credential_name", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("chat_id", PortType.INPUT, DataType.STRING, required=True)

    def _define_common_output_ports(self) -> None:
        """Define standard Telegram output ports."""
        self.add_output_port("message_id", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("chat_id", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def _get_telegram_client(self, context: ExecutionContext) -> TelegramClient:
        """
        Get or create Telegram client from context.

        Args:
            context: Execution context

        Returns:
            Configured Telegram client instance
        """
        # Check if client exists in context
        if hasattr(context, "resources") and "telegram" in context.resources:
            return context.resources["telegram"]

        # Get bot token
        bot_token = await self._get_bot_token(context)
        if not bot_token:
            raise TelegramAPIError("No Telegram bot token configured")

        # Create client
        config = TelegramConfig(bot_token=bot_token)
        client = TelegramClient(config)

        # Store in context for reuse
        if hasattr(context, "resources"):
            context.resources["telegram"] = client

        self._client = client
        return client

    async def _get_bot_token(self, context: ExecutionContext) -> Optional[str]:
        """Get bot token from context, credentials, or environment."""
        # Try direct parameter first
        token = self.get_parameter("bot_token")
        if token:
            if hasattr(context, "resolve_value"):
                token = context.resolve_value(token)
            return token

        # Try context variables
        if hasattr(context, "get_variable"):
            token = context.get_variable("telegram_bot_token")
            if token:
                return token

        # Try credential manager with credential_name
        try:
            from casare_rpa.utils.security.credential_manager import credential_manager

            cred_name = self.get_parameter("credential_name")
            if cred_name:
                if hasattr(context, "resolve_value"):
                    cred_name = context.resolve_value(cred_name)
                cred = credential_manager.get_telegram_credential(cred_name)
                if cred and cred.bot_token:
                    return cred.bot_token

            # Try default credential names
            for name in ["telegram", "telegram_bot", "default_telegram"]:
                cred = credential_manager.get_telegram_credential(name)
                if cred and cred.bot_token:
                    return cred.bot_token
        except Exception as e:
            logger.debug(f"Could not get credential: {e}")

        # Try environment
        return os.environ.get("TELEGRAM_BOT_TOKEN")

    def _get_chat_id(self, context: ExecutionContext) -> str:
        """Get chat ID from parameter, resolving variables."""
        chat_id = self.get_parameter("chat_id")
        if hasattr(context, "resolve_value"):
            chat_id = context.resolve_value(chat_id)
        return str(chat_id)

    def _set_error_outputs(self, error_msg: str) -> None:
        """Set output values for error case."""
        self.set_output_value("success", False)
        self.set_output_value("error", error_msg)
        self.set_output_value("message_id", 0)
        self.set_output_value("chat_id", 0)

    def _set_success_outputs(
        self,
        message_id: int,
        chat_id: int,
    ) -> None:
        """Set output values for successful response."""
        self.set_output_value("success", True)
        self.set_output_value("error", "")
        self.set_output_value("message_id", message_id)
        self.set_output_value("chat_id", chat_id)

    @abstractmethod
    async def _execute_telegram(
        self,
        context: ExecutionContext,
        client: TelegramClient,
    ) -> ExecutionResult:
        """
        Execute the Telegram operation.

        Args:
            context: Execution context
            client: Telegram client

        Returns:
            Execution result
        """
        ...

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute the Telegram node."""
        self.status = NodeStatus.RUNNING

        try:
            # Get Telegram client
            client = await self._get_telegram_client(context)

            async with client:
                # Execute specific Telegram operation
                result = await self._execute_telegram(context, client)

            if result.get("success", False):
                self.status = NodeStatus.SUCCESS
            else:
                self.status = NodeStatus.ERROR

            return result

        except TelegramAPIError as e:
            error_msg = str(e)
            logger.error(f"Telegram API error: {error_msg}")
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

        except Exception as e:
            error_msg = f"Telegram error: {str(e)}"
            logger.error(error_msg)
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


__all__ = ["TelegramBaseNode"]
