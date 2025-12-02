"""
CasareRPA - Google Drive Base Node

Abstract base class for all Google Drive nodes with shared functionality.
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
from casare_rpa.infrastructure.resources.google_drive_client import (
    GoogleDriveClient,
    DriveConfig,
    DriveAPIError,
    DriveMimeType,
)


class DriveBaseNode(BaseNode):
    """
    Abstract base class for Google Drive nodes.

    Provides common functionality:
    - Google Drive client access
    - OAuth token configuration from credentials/env
    - Error handling
    - Standard output ports (success, error)

    Required OAuth scopes:
        https://www.googleapis.com/auth/drive (full access)
        or more restricted scopes depending on operation

    Subclasses implement _execute_drive() for specific operations.
    """

    # Required OAuth scopes for Drive operations
    REQUIRED_SCOPES = ["https://www.googleapis.com/auth/drive"]

    def __init__(self, node_id: str, name: str = "Drive Node", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self._client: Optional[GoogleDriveClient] = None

    def _define_common_input_ports(self) -> None:
        """Define standard Google Drive input ports for authentication."""
        self.add_input_port(
            "access_token", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "credential_name", PortType.INPUT, DataType.STRING, required=False
        )

    def _define_common_output_ports(self) -> None:
        """Define standard Google Drive output ports."""
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def _get_drive_client(self, context: ExecutionContext) -> GoogleDriveClient:
        """
        Get or create Google Drive client from context.

        Args:
            context: Execution context

        Returns:
            Configured Google Drive client instance

        Raises:
            DriveAPIError: If no access token is configured
        """
        # Check if client exists in context
        if hasattr(context, "resources") and "google_drive" in context.resources:
            return context.resources["google_drive"]

        # Get access token
        access_token = await self._get_access_token(context)
        if not access_token:
            raise DriveAPIError("No Google Drive access token configured")

        # Create client
        config = DriveConfig(access_token=access_token)
        client = GoogleDriveClient(config)

        # Store in context for reuse
        if hasattr(context, "resources"):
            context.resources["google_drive"] = client

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
            for name in ["google", "google_drive", "gdrive"]:
                cred = credential_manager.get_oauth_credential(name)
                if cred and cred.access_token:
                    return cred.access_token
        except Exception as e:
            logger.debug(f"Could not get credential: {e}")

        # Try environment
        return os.environ.get("GOOGLE_ACCESS_TOKEN")

    def _resolve_value(self, context: ExecutionContext, value: Any) -> Any:
        """Resolve a value using the execution context."""
        if value and hasattr(context, "resolve_value"):
            return context.resolve_value(value)
        return value

    def _set_error_outputs(self, error_msg: str) -> None:
        """Set output values for error case."""
        self.set_output_value("success", False)
        self.set_output_value("error", error_msg)

    def _set_success_outputs(self) -> None:
        """Set output values for successful response."""
        self.set_output_value("success", True)
        self.set_output_value("error", "")

    @staticmethod
    def get_mime_type_from_extension(file_path: str) -> str:
        """Get MIME type from file extension."""
        from pathlib import Path

        ext = Path(file_path).suffix
        return DriveMimeType.from_extension(ext)

    @staticmethod
    def is_google_workspace_type(mime_type: str) -> bool:
        """Check if MIME type is a Google Workspace document."""
        return mime_type.startswith("application/vnd.google-apps.")

    @abstractmethod
    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: GoogleDriveClient,
    ) -> ExecutionResult:
        """
        Execute the Google Drive operation.

        Args:
            context: Execution context
            client: Google Drive client

        Returns:
            Execution result
        """
        ...

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute the Google Drive node."""
        self.status = NodeStatus.RUNNING

        try:
            # Get Google Drive client
            client = await self._get_drive_client(context)

            async with client:
                # Execute specific Drive operation
                result = await self._execute_drive(context, client)

            if result.get("success", False):
                self.status = NodeStatus.SUCCESS
            else:
                self.status = NodeStatus.ERROR

            return result

        except DriveAPIError as e:
            error_msg = str(e)
            logger.error(f"Google Drive API error: {error_msg}")
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

        except Exception as e:
            error_msg = f"Google Drive error: {str(e)}"
            logger.error(error_msg)
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


__all__ = ["DriveBaseNode"]
