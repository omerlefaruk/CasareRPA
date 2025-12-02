"""
CasareRPA - Gmail Base Node

Abstract base class for all Gmail nodes with shared functionality.
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
from casare_rpa.infrastructure.resources.gmail_client import (
    GmailAPIError,
    GmailClient,
    GmailConfig,
)


class GmailBaseNode(BaseNode):
    """
    Abstract base class for Gmail nodes.

    Provides common functionality:
    - Gmail client access via OAuth 2.0
    - Access token configuration from credentials/env
    - Error handling
    - Standard output ports

    Required OAuth Scopes:
    - https://www.googleapis.com/auth/gmail.modify (read/write access)
    - https://www.googleapis.com/auth/gmail.send (send only)
    - https://www.googleapis.com/auth/gmail.readonly (read only)

    Subclasses implement _execute_gmail() for specific operations.
    """

    REQUIRED_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

    def __init__(self, node_id: str, name: str = "Gmail Node", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self._client: Optional[GmailClient] = None

    def _define_common_input_ports(self) -> None:
        """Define standard Gmail input ports."""
        self.add_input_port(
            "access_token", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "credential_name", PortType.INPUT, DataType.STRING, required=False
        )

    def _define_common_output_ports(self) -> None:
        """Define standard Gmail output ports."""
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def _get_gmail_client(self, context: ExecutionContext) -> GmailClient:
        """
        Get or create Gmail client from context.

        Args:
            context: Execution context

        Returns:
            Configured Gmail client instance
        """
        # Check if client exists in context
        if hasattr(context, "resources") and "gmail" in context.resources:
            return context.resources["gmail"]

        # Get access token
        access_token = await self._get_access_token(context)
        if not access_token:
            raise GmailAPIError("No Gmail access token configured")

        # Create client
        config = GmailConfig(access_token=access_token)
        client = GmailClient(config)

        # Store in context for reuse
        if hasattr(context, "resources"):
            context.resources["gmail"] = client

        self._client = client
        return client

    async def _get_access_token(self, context: ExecutionContext) -> Optional[str]:
        """Get OAuth access token from context, credentials, or environment."""
        # Try direct parameter first
        token = self.get_parameter("access_token")
        if token:
            if hasattr(context, "resolve_value"):
                token = context.resolve_value(token)
            return token

        # Try context variables
        if hasattr(context, "get_variable"):
            token = context.get_variable("gmail_access_token")
            if token:
                return token
            # Also try generic google access token
            token = context.get_variable("google_access_token")
            if token:
                return token

        # Try credential manager with credential_name
        try:
            from casare_rpa.utils.security.credential_manager import credential_manager

            cred_name = self.get_parameter("credential_name")
            if cred_name:
                if hasattr(context, "resolve_value"):
                    cred_name = context.resolve_value(cred_name)
                cred = credential_manager.get_oauth_credential(cred_name)
                if cred and cred.access_token:
                    return cred.access_token

            # Try default credential names
            for name in ["gmail", "google", "google_workspace", "default_google"]:
                cred = credential_manager.get_oauth_credential(name)
                if cred and cred.access_token:
                    return cred.access_token
        except Exception as e:
            logger.debug(f"Could not get credential: {e}")

        # Try environment variables
        token = os.environ.get("GMAIL_ACCESS_TOKEN")
        if token:
            return token
        token = os.environ.get("GOOGLE_ACCESS_TOKEN")
        if token:
            return token

        return None

    def _set_error_outputs(self, error_msg: str) -> None:
        """Set output values for error case."""
        self.set_output_value("success", False)
        self.set_output_value("error", error_msg)

    def _set_success_outputs(self) -> None:
        """Set output values for successful response."""
        self.set_output_value("success", True)
        self.set_output_value("error", "")

    @abstractmethod
    async def _execute_gmail(
        self,
        context: ExecutionContext,
        client: GmailClient,
    ) -> ExecutionResult:
        """
        Execute the Gmail operation.

        Args:
            context: Execution context
            client: Gmail client

        Returns:
            Execution result
        """
        ...

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute the Gmail node."""
        self.status = NodeStatus.RUNNING

        try:
            # Get Gmail client
            client = await self._get_gmail_client(context)

            async with client:
                # Execute specific Gmail operation
                result = await self._execute_gmail(context, client)

            if result.get("success", False):
                self.status = NodeStatus.SUCCESS
            else:
                self.status = NodeStatus.ERROR

            return result

        except GmailAPIError as e:
            error_msg = str(e)
            logger.error(f"Gmail API error: {error_msg}")
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

        except Exception as e:
            error_msg = f"Gmail error: {str(e)}"
            logger.error(error_msg)
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


__all__ = ["GmailBaseNode"]
