"""
CasareRPA - Google Calendar Base Node

Abstract base class for all Google Calendar nodes with shared functionality.
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
from casare_rpa.infrastructure.resources.google_calendar_client import (
    GoogleCalendarAPIError,
    GoogleCalendarClient,
    CalendarConfig,
)


class CalendarBaseNode(BaseNode):
    """
    Abstract base class for Google Calendar nodes.

    Provides common functionality:
    - Calendar client access via OAuth 2.0
    - Access token configuration from credentials/env
    - Error handling
    - Standard output ports

    Required OAuth Scopes:
    - https://www.googleapis.com/auth/calendar (full access)
    - https://www.googleapis.com/auth/calendar.readonly (read only)
    - https://www.googleapis.com/auth/calendar.events (events only)

    Subclasses implement _execute_calendar() for specific operations.
    """

    REQUIRED_SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def __init__(
        self, node_id: str, name: str = "Calendar Node", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self._client: Optional[GoogleCalendarClient] = None

    def _define_common_input_ports(self) -> None:
        """Define standard Calendar input ports."""
        self.add_input_port(
            "access_token", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "credential_name", PortType.INPUT, DataType.STRING, required=False
        )

    def _define_common_output_ports(self) -> None:
        """Define standard Calendar output ports."""
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def _get_calendar_client(
        self, context: ExecutionContext
    ) -> GoogleCalendarClient:
        """
        Get or create Calendar client from context.

        Args:
            context: Execution context

        Returns:
            Configured Calendar client instance
        """
        if hasattr(context, "resources") and "calendar" in context.resources:
            return context.resources["calendar"]

        access_token = await self._get_access_token(context)
        if not access_token:
            raise GoogleCalendarAPIError("No Google Calendar access token configured")

        config = CalendarConfig(access_token=access_token)
        client = GoogleCalendarClient(config)

        if hasattr(context, "resources"):
            context.resources["calendar"] = client

        self._client = client
        return client

    async def _get_access_token(self, context: ExecutionContext) -> Optional[str]:
        """Get OAuth access token from context, credentials, or environment."""
        token = self.get_parameter("access_token")
        if token:
            if hasattr(context, "resolve_value"):
                token = context.resolve_value(token)
            return token

        if hasattr(context, "get_variable"):
            token = context.get_variable("calendar_access_token")
            if token:
                return token
            token = context.get_variable("google_access_token")
            if token:
                return token

        try:
            from casare_rpa.utils.security.credential_manager import credential_manager

            cred_name = self.get_parameter("credential_name")
            if cred_name:
                if hasattr(context, "resolve_value"):
                    cred_name = context.resolve_value(cred_name)
                cred = credential_manager.get_oauth_credential(cred_name)
                if cred and cred.access_token:
                    return cred.access_token

            for name in ["calendar", "google_calendar", "google", "google_workspace"]:
                cred = credential_manager.get_oauth_credential(name)
                if cred and cred.access_token:
                    return cred.access_token
        except Exception as e:
            logger.debug(f"Could not get credential: {e}")

        token = os.environ.get("GOOGLE_CALENDAR_ACCESS_TOKEN")
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
    async def _execute_calendar(
        self,
        context: ExecutionContext,
        client: GoogleCalendarClient,
    ) -> ExecutionResult:
        """
        Execute the Calendar operation.

        Args:
            context: Execution context
            client: Calendar client

        Returns:
            Execution result
        """
        ...

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute the Calendar node."""
        self.status = NodeStatus.RUNNING

        try:
            client = await self._get_calendar_client(context)

            async with client:
                result = await self._execute_calendar(context, client)

            if result.get("success", False):
                self.status = NodeStatus.SUCCESS
            else:
                self.status = NodeStatus.ERROR

            return result

        except GoogleCalendarAPIError as e:
            error_msg = str(e)
            logger.error(f"Calendar API error: {error_msg}")
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

        except Exception as e:
            error_msg = f"Calendar error: {str(e)}"
            logger.error(error_msg)
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


__all__ = ["CalendarBaseNode"]
