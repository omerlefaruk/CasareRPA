"""
CasareRPA - Google Sheets Base Node

Abstract base class for all Google Sheets nodes with shared functionality.
"""

from __future__ import annotations

import os
import re
from abc import abstractmethod
from typing import Any, Dict, Optional

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
    PortType,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.infrastructure.resources.google_sheets_client import (
    GoogleSheetsClient,
    GoogleSheetsConfig,
    GoogleSheetsError,
)


class SheetsBaseNode(BaseNode):
    """
    Abstract base class for Google Sheets nodes.

    Provides common functionality:
    - Google Sheets client access
    - Authentication from credentials, context, or environment
    - Error handling
    - Standard output ports

    Subclasses implement _execute_sheets() for specific operations.
    """

    NODE_NAME = "Sheets Base"
    CATEGORY = "Google Sheets"

    def __init__(self, node_id: str, name: str = "Sheets Node", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self._client: Optional[GoogleSheetsClient] = None

    def _define_common_input_ports(self) -> None:
        """Define standard Sheets authentication input ports."""
        self.add_input_port(
            "service_account_file",
            PortType.INPUT,
            DataType.STRING,
            required=False,
        )
        self.add_input_port(
            "access_token",
            PortType.INPUT,
            DataType.STRING,
            required=False,
        )
        self.add_input_port(
            "credential_name",
            PortType.INPUT,
            DataType.STRING,
            required=False,
        )

    def _define_spreadsheet_input_port(self) -> None:
        """Define spreadsheet_id input port."""
        self.add_input_port(
            "spreadsheet_id",
            PortType.INPUT,
            DataType.STRING,
            required=True,
        )

    def _define_common_output_ports(self) -> None:
        """Define standard Sheets output ports."""
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("result", PortType.OUTPUT, DataType.ANY)

    async def _get_sheets_config(self, context: ExecutionContext) -> GoogleSheetsConfig:
        """
        Build GoogleSheetsConfig from parameters and context.

        Priority:
        1. Direct parameters (service_account_file, access_token)
        2. Credential manager lookup
        3. Context variables
        4. Environment variables

        Returns:
            GoogleSheetsConfig instance
        """
        config_kwargs: Dict[str, Any] = {
            "timeout": self.get_parameter("timeout", 30.0),
            "max_retries": self.get_parameter("max_retries", 3),
        }

        # Try service account file
        sa_file = self.get_parameter("service_account_file")
        if sa_file:
            if hasattr(context, "resolve_value"):
                sa_file = context.resolve_value(sa_file)
            if sa_file and os.path.exists(sa_file):
                config_kwargs["service_account_file"] = sa_file
                return GoogleSheetsConfig(**config_kwargs)

        # Try access token
        access_token = self.get_parameter("access_token")
        if access_token:
            if hasattr(context, "resolve_value"):
                access_token = context.resolve_value(access_token)
            if access_token:
                config_kwargs["access_token"] = access_token
                return GoogleSheetsConfig(**config_kwargs)

        # Try credential manager
        try:
            from casare_rpa.utils.security.credential_manager import credential_manager

            cred_name = self.get_parameter("credential_name")
            if cred_name:
                if hasattr(context, "resolve_value"):
                    cred_name = context.resolve_value(cred_name)
                # Look for Google credential
                cred = credential_manager.get_google_credential(cred_name)
                if cred:
                    if (
                        hasattr(cred, "service_account_json")
                        and cred.service_account_json
                    ):
                        config_kwargs["service_account_json"] = (
                            cred.service_account_json
                        )
                        return GoogleSheetsConfig(**config_kwargs)
                    if hasattr(cred, "access_token") and cred.access_token:
                        config_kwargs["access_token"] = cred.access_token
                        return GoogleSheetsConfig(**config_kwargs)

            # Try default credential names
            for name in ["google", "google_sheets", "gcp", "default_google"]:
                cred = credential_manager.get_google_credential(name)
                if cred:
                    if (
                        hasattr(cred, "service_account_json")
                        and cred.service_account_json
                    ):
                        config_kwargs["service_account_json"] = (
                            cred.service_account_json
                        )
                        return GoogleSheetsConfig(**config_kwargs)
                    if hasattr(cred, "access_token") and cred.access_token:
                        config_kwargs["access_token"] = cred.access_token
                        return GoogleSheetsConfig(**config_kwargs)
        except Exception as e:
            logger.debug(f"Could not get Google credential from manager: {e}")

        # Try context variables
        if hasattr(context, "get_variable"):
            sa_file = context.get_variable("google_service_account_file")
            if sa_file and os.path.exists(sa_file):
                config_kwargs["service_account_file"] = sa_file
                return GoogleSheetsConfig(**config_kwargs)

            access_token = context.get_variable("google_access_token")
            if access_token:
                config_kwargs["access_token"] = access_token
                return GoogleSheetsConfig(**config_kwargs)

        # Try environment variables
        env_sa_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if env_sa_file and os.path.exists(env_sa_file):
            config_kwargs["service_account_file"] = env_sa_file
            return GoogleSheetsConfig(**config_kwargs)

        env_api_key = os.environ.get("GOOGLE_SHEETS_API_KEY")
        if env_api_key:
            config_kwargs["api_key"] = env_api_key
            return GoogleSheetsConfig(**config_kwargs)

        # Return empty config - will fail during authentication
        return GoogleSheetsConfig(**config_kwargs)

    async def _get_sheets_client(self, context: ExecutionContext) -> GoogleSheetsClient:
        """
        Get or create Google Sheets client.

        Args:
            context: Execution context

        Returns:
            Configured GoogleSheetsClient instance
        """
        # Check if client exists in context
        if hasattr(context, "resources") and "google_sheets" in context.resources:
            return context.resources["google_sheets"]

        # Build config and create client
        sheets_config = await self._get_sheets_config(context)
        client = GoogleSheetsClient(sheets_config)

        # Store in context for reuse
        if hasattr(context, "resources"):
            context.resources["google_sheets"] = client

        self._client = client
        return client

    def _get_spreadsheet_id(self, context: ExecutionContext) -> str:
        """Get spreadsheet ID from parameter, resolving variables."""
        spreadsheet_id = self.get_parameter("spreadsheet_id")
        if hasattr(context, "resolve_value"):
            spreadsheet_id = context.resolve_value(spreadsheet_id)
        return str(spreadsheet_id) if spreadsheet_id else ""

    def _set_error_outputs(self, error_msg: str) -> None:
        """Set output values for error case."""
        self.set_output_value("success", False)
        self.set_output_value("error", error_msg)
        self.set_output_value("result", None)

    def _set_success_outputs(self, result: Any) -> None:
        """Set output values for successful response."""
        self.set_output_value("success", True)
        self.set_output_value("error", "")
        self.set_output_value("result", result)

    # =========================================================================
    # A1 Notation Helpers
    # =========================================================================

    REQUIRED_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    @staticmethod
    def column_letter_to_index(column: str) -> int:
        """Convert column letter(s) to 0-based index. A=0, B=1, ..., Z=25, AA=26."""
        result = 0
        for char in column.upper():
            result = result * 26 + (ord(char) - ord("A") + 1)
        return result - 1

    @staticmethod
    def index_to_column_letter(index: int) -> str:
        """Convert 0-based index to column letter(s). 0=A, 1=B, ..., 25=Z, 26=AA."""
        result = ""
        index += 1
        while index > 0:
            index, remainder = divmod(index - 1, 26)
            result = chr(ord("A") + remainder) + result
        return result

    @classmethod
    def cell_to_indices(cls, cell: str) -> tuple[int, int]:
        """Convert A1 notation cell to (row, col) 0-based indices."""
        match = re.match(r"([A-Z]+)(\d+)", cell.upper())
        if not match:
            raise ValueError(f"Invalid cell reference: {cell}")
        col = cls.column_letter_to_index(match.group(1))
        row = int(match.group(2)) - 1
        return row, col

    @classmethod
    def indices_to_cell(cls, row: int, col: int) -> str:
        """Convert (row, col) 0-based indices to A1 notation."""
        return f"{cls.index_to_column_letter(col)}{row + 1}"

    @classmethod
    def build_a1_range(
        cls,
        sheet_name: Optional[str] = None,
        start_cell: Optional[str] = None,
        end_cell: Optional[str] = None,
        start_row: Optional[int] = None,
        start_col: Optional[int] = None,
        end_row: Optional[int] = None,
        end_col: Optional[int] = None,
    ) -> str:
        """
        Build A1 notation range string.

        Can use either cell references (A1, B10) or numeric indices.
        """
        if start_cell:
            cell_ref = start_cell
            if end_cell:
                cell_ref = f"{start_cell}:{end_cell}"
        elif start_row is not None and start_col is not None:
            start = cls.indices_to_cell(start_row, start_col)
            if end_row is not None and end_col is not None:
                end = cls.indices_to_cell(end_row, end_col)
                cell_ref = f"{start}:{end}"
            else:
                cell_ref = start
        else:
            cell_ref = "A1"

        if sheet_name:
            if " " in sheet_name or "!" in sheet_name or "'" in sheet_name:
                safe_name = sheet_name.replace("'", "''")
                sheet_name = f"'{safe_name}'"
            return f"{sheet_name}!{cell_ref}"
        return cell_ref

    @abstractmethod
    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """
        Execute the Sheets operation.

        Args:
            context: Execution context
            client: Google Sheets client

        Returns:
            Execution result
        """
        ...

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute the Google Sheets node."""
        self.status = NodeStatus.RUNNING

        try:
            # Get Sheets client
            client = await self._get_sheets_client(context)

            async with client:
                # Execute specific Sheets operation
                result = await self._execute_sheets(context, client)

            if result.get("success", False):
                self.status = NodeStatus.SUCCESS
            else:
                self.status = NodeStatus.ERROR

            return result

        except GoogleSheetsError as e:
            error_msg = str(e)
            logger.error(f"Google Sheets API error: {error_msg}")
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

        except Exception as e:
            error_msg = f"Google Sheets error: {str(e)}"
            logger.error(error_msg)
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


__all__ = ["SheetsBaseNode"]
