"""
CasareRPA - Google Docs Base Node

Abstract base class for all Google Docs nodes with shared functionality.
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
from casare_rpa.infrastructure.resources.google_docs_client import (
    GoogleDocsClient,
    GoogleDocsConfig,
    GoogleDocsAPIError,
)


class DocsBaseNode(BaseNode):
    """
    Abstract base class for Google Docs nodes.

    Provides common functionality:
    - Google Docs client access
    - OAuth2 token configuration from credentials/env
    - Error handling
    - Standard output ports

    Subclasses implement _execute_docs() for specific operations.
    """

    # Required OAuth2 scopes for Docs operations
    REQUIRED_SCOPES = [
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/drive.file",
    ]

    def __init__(
        self, node_id: str, name: str = "Google Docs Node", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self._client: Optional[GoogleDocsClient] = None

    def _define_common_input_ports(self) -> None:
        """Define standard Google Docs input ports."""
        self.add_input_port(
            "access_token", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "credential_name", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "document_id", PortType.INPUT, DataType.STRING, required=True
        )

    def _define_common_output_ports(self) -> None:
        """Define standard Google Docs output ports."""
        self.add_output_port("document_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def _get_docs_client(self, context: ExecutionContext) -> GoogleDocsClient:
        """
        Get or create Google Docs client from context.

        Args:
            context: Execution context

        Returns:
            Configured Google Docs client instance
        """
        # Check if client exists in context
        if hasattr(context, "resources") and "google_docs" in context.resources:
            return context.resources["google_docs"]

        # Get access token
        access_token = await self._get_access_token(context)
        if not access_token:
            raise GoogleDocsAPIError("No Google OAuth2 access token configured")

        # Create client
        config = GoogleDocsConfig(access_token=access_token)
        client = GoogleDocsClient(config)

        # Store in context for reuse
        if hasattr(context, "resources"):
            context.resources["google_docs"] = client

        self._client = client
        return client

    async def _get_access_token(self, context: ExecutionContext) -> Optional[str]:
        """Get access token from context, credentials, or environment."""
        # Try direct parameter first
        token = self.get_parameter("access_token")
        if token:
            if hasattr(context, "resolve_value"):
                token = context.resolve_value(token)
            return token

        # Try context variables
        if hasattr(context, "get_variable"):
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
            for name in ["google", "google_docs", "default_google"]:
                cred = credential_manager.get_oauth_credential(name)
                if cred and cred.access_token:
                    return cred.access_token
        except Exception as e:
            logger.debug(f"Could not get credential: {e}")

        # Try environment
        return os.environ.get("GOOGLE_ACCESS_TOKEN")

    def _get_document_id(self, context: ExecutionContext) -> str:
        """Get document ID from parameter, resolving variables."""
        doc_id = self.get_parameter("document_id")
        if hasattr(context, "resolve_value"):
            doc_id = context.resolve_value(doc_id)
        return str(doc_id) if doc_id else ""

    def _set_error_outputs(self, error_msg: str) -> None:
        """Set output values for error case."""
        self.set_output_value("success", False)
        self.set_output_value("error", error_msg)
        self.set_output_value("document_id", "")

    def _set_success_outputs(self, document_id: str) -> None:
        """Set output values for successful response."""
        self.set_output_value("success", True)
        self.set_output_value("error", "")
        self.set_output_value("document_id", document_id)

    @abstractmethod
    async def _execute_docs(
        self,
        context: ExecutionContext,
        client: GoogleDocsClient,
    ) -> ExecutionResult:
        """
        Execute the Google Docs operation.

        Args:
            context: Execution context
            client: Google Docs client

        Returns:
            Execution result
        """
        ...

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute the Google Docs node."""
        self.status = NodeStatus.RUNNING

        try:
            # Get Google Docs client
            client = await self._get_docs_client(context)

            async with client:
                # Execute specific Docs operation
                result = await self._execute_docs(context, client)

            if result.get("success", False):
                self.status = NodeStatus.SUCCESS
            else:
                self.status = NodeStatus.ERROR

            return result

        except GoogleDocsAPIError as e:
            error_msg = str(e)
            logger.error(f"Google Docs API error: {error_msg}")
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

        except Exception as e:
            error_msg = f"Google Docs error: {str(e)}"
            logger.error(error_msg)
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


__all__ = ["DocsBaseNode"]
