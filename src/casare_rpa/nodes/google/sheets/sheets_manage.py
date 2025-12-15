"""
CasareRPA - Google Sheets Management Nodes

Nodes for managing spreadsheets and worksheets:
- SheetsCreateSpreadsheetNode: Create new spreadsheet
- SheetsGetSpreadsheetNode: Get spreadsheet metadata
- SheetsAddSheetNode: Add worksheet to spreadsheet
- SheetsDeleteSheetNode: Delete worksheet
- SheetsCopySheetNode: Copy sheet to another spreadsheet
- SheetsDuplicateSheetNode: Duplicate sheet within spreadsheet
- SheetsRenameSheetNode: Rename a sheet
"""

from __future__ import annotations
from casare_rpa.domain.decorators import node, properties


from typing import Any, Dict

from loguru import logger

from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.infrastructure.resources.google_sheets_client import (
    GoogleSheetsClient,
)
from casare_rpa.nodes.google.google_base import SheetsBaseNode


@properties()
@node(category="google")
class SheetsCreateSpreadsheetNode(SheetsBaseNode):
    """
    Create a new Google Spreadsheet.

    Inputs:
        - title: Title for the new spreadsheet
        - sheets: Optional list of sheet names to create (default: ["Sheet1"])
        - locale: Locale string (default: "en_US")

    Outputs:
        - success: Whether operation succeeded
        - spreadsheet_id: ID of created spreadsheet
        - spreadsheet_url: URL to access spreadsheet
        - result: Full spreadsheet properties
    """

    # @category: google
    # @requires: none
    # @ports: title, sheets, locale -> spreadsheet_id, spreadsheet_url

    NODE_NAME = "Create Spreadsheet"
    CATEGORY = "Google Sheets"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Create Spreadsheet", **kwargs)

    def _define_ports(self) -> None:
        """Define input and output ports."""
        # Auth ports
        self._define_common_input_ports()

        # Specific inputs
        self.add_input_port("title", DataType.STRING, required=True)
        self.add_input_port("sheets", DataType.LIST, required=False)
        self.add_input_port("locale", DataType.STRING, required=False)

        # Outputs
        self._define_common_output_ports()
        self.add_output_port("spreadsheet_id", DataType.STRING)
        self.add_output_port("spreadsheet_url", DataType.STRING)

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Create a new spreadsheet."""
        # Get parameters
        title = self.get_parameter("title")
        if hasattr(context, "resolve_value"):
            title = context.resolve_value(title)

        if not title:
            self._set_error_outputs("Spreadsheet title is required")
            return {"success": False, "error": "Title is required", "next_nodes": []}

        sheets = self.get_parameter("sheets")
        if isinstance(sheets, str) and hasattr(context, "resolve_value"):
            sheets = context.resolve_value(sheets)
        if not sheets:
            sheets = ["Sheet1"]

        locale = self.get_parameter("locale", "en_US")
        if hasattr(context, "resolve_value"):
            locale = context.resolve_value(locale)

        # Create spreadsheet
        result = await client.create_spreadsheet(
            title=title,
            sheets=sheets,
            locale=locale,
        )

        # Set outputs
        spreadsheet_id = result.spreadsheet_id
        spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"

        self.set_output_value("success", True)
        self.set_output_value("error", "")
        self.set_output_value("spreadsheet_id", spreadsheet_id)
        self.set_output_value("spreadsheet_url", spreadsheet_url)
        self.set_output_value(
            "result",
            {
                "spreadsheet_id": spreadsheet_id,
                "title": result.title,
                "locale": result.locale,
                "time_zone": result.time_zone,
                "sheets": [
                    s.get("properties", {}).get("title", "") for s in result.sheets
                ],
            },
        )

        logger.info(f"Created spreadsheet: {title} ({spreadsheet_id})")

        return {
            "success": True,
            "data": {"spreadsheet_id": spreadsheet_id, "title": title},
            "next_nodes": ["exec_out"],
        }


@properties()
@node(category="google")
class SheetsGetSpreadsheetNode(SheetsBaseNode):
    """
    Get spreadsheet metadata.

    Inputs:
        - spreadsheet_id: Spreadsheet ID
        - include_grid_data: Include cell data (default: False)

    Outputs:
        - success: Whether operation succeeded
        - result: Spreadsheet properties
        - title: Spreadsheet title
        - sheets: List of sheet names
    """

    # @category: google
    # @requires: none
    # @ports: include_grid_data -> title, sheets

    NODE_NAME = "Get Spreadsheet"
    CATEGORY = "Google Sheets"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Get Spreadsheet", **kwargs)

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_spreadsheet_input_port()

        self.add_input_port("include_grid_data", DataType.BOOLEAN, required=False)

        self._define_common_output_ports()
        self.add_output_port("title", DataType.STRING)
        self.add_output_port("sheets", DataType.LIST)

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Get spreadsheet metadata."""
        spreadsheet_id = self._get_spreadsheet_id(context)
        if not spreadsheet_id:
            self._set_error_outputs("Spreadsheet ID is required")
            return {
                "success": False,
                "error": "Spreadsheet ID is required",
                "next_nodes": [],
            }

        include_grid_data = self.get_parameter("include_grid_data", False)

        result = await client.get_spreadsheet(
            spreadsheet_id=spreadsheet_id,
            include_grid_data=include_grid_data,
        )

        sheet_names = [s.get("properties", {}).get("title", "") for s in result.sheets]

        self.set_output_value("success", True)
        self.set_output_value("error", "")
        self.set_output_value("title", result.title)
        self.set_output_value("sheets", sheet_names)
        self.set_output_value(
            "result",
            {
                "spreadsheet_id": result.spreadsheet_id,
                "title": result.title,
                "locale": result.locale,
                "time_zone": result.time_zone,
                "sheets": result.sheets,
            },
        )

        logger.info(f"Got spreadsheet: {result.title} ({spreadsheet_id})")

        return {
            "success": True,
            "data": {"spreadsheet_id": spreadsheet_id, "title": result.title},
            "next_nodes": ["exec_out"],
        }


@properties()
@node(category="google")
class SheetsAddSheetNode(SheetsBaseNode):
    """
    Add a new sheet (worksheet) to an existing spreadsheet.

    Inputs:
        - spreadsheet_id: Target spreadsheet ID
        - sheet_name: Name for the new sheet
        - row_count: Initial row count (default: 1000)
        - column_count: Initial column count (default: 26)

    Outputs:
        - success: Whether operation succeeded
        - sheet_id: Numeric ID of created sheet
        - sheet_name: Name of created sheet
        - result: Full sheet properties
    """

    # @category: google
    # @requires: none
    # @ports: sheet_name, row_count, column_count -> sheet_id, sheet_name

    NODE_NAME = "Add Sheet"
    CATEGORY = "Google Sheets"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Add Sheet", **kwargs)

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_spreadsheet_input_port()

        self.add_input_port("sheet_name", DataType.STRING, required=True)
        self.add_input_port("row_count", DataType.INTEGER, required=False)
        self.add_input_port("column_count", DataType.INTEGER, required=False)

        self._define_common_output_ports()
        self.add_output_port("sheet_id", DataType.INTEGER)
        self.add_output_port("sheet_name", DataType.STRING)

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Add a new sheet to spreadsheet."""
        spreadsheet_id = self._get_spreadsheet_id(context)
        if not spreadsheet_id:
            self._set_error_outputs("Spreadsheet ID is required")
            return {
                "success": False,
                "error": "Spreadsheet ID is required",
                "next_nodes": [],
            }

        sheet_name = self.get_parameter("sheet_name")
        if hasattr(context, "resolve_value"):
            sheet_name = context.resolve_value(sheet_name)

        if not sheet_name:
            self._set_error_outputs("Sheet name is required")
            return {
                "success": False,
                "error": "Sheet name is required",
                "next_nodes": [],
            }

        row_count = self.get_parameter("row_count", 1000)
        column_count = self.get_parameter("column_count", 26)

        result = await client.add_sheet(
            spreadsheet_id=spreadsheet_id,
            sheet_name=sheet_name,
            row_count=row_count,
            column_count=column_count,
        )

        self.set_output_value("success", True)
        self.set_output_value("error", "")
        self.set_output_value("sheet_id", result.sheet_id)
        self.set_output_value("sheet_name", result.title)
        self.set_output_value(
            "result",
            {
                "sheet_id": result.sheet_id,
                "title": result.title,
                "index": result.index,
                "row_count": result.row_count,
                "column_count": result.column_count,
            },
        )

        logger.info(f"Added sheet '{sheet_name}' to {spreadsheet_id}")

        return {
            "success": True,
            "data": {"sheet_id": result.sheet_id, "sheet_name": result.title},
            "next_nodes": ["exec_out"],
        }


@properties()
@node(category="google")
class SheetsDeleteSheetNode(SheetsBaseNode):
    """
    Delete a sheet from a spreadsheet.

    Inputs:
        - spreadsheet_id: Target spreadsheet ID
        - sheet_id: Numeric ID of sheet to delete

    Outputs:
        - success: Whether operation succeeded
        - result: Deletion confirmation
    """

    # @category: google
    # @requires: none
    # @ports: sheet_id -> none

    NODE_NAME = "Delete Sheet"
    CATEGORY = "Google Sheets"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Delete Sheet", **kwargs)

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_spreadsheet_input_port()

        self.add_input_port("sheet_id", DataType.INTEGER, required=True)

        self._define_common_output_ports()

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Delete a sheet from spreadsheet."""
        spreadsheet_id = self._get_spreadsheet_id(context)
        if not spreadsheet_id:
            self._set_error_outputs("Spreadsheet ID is required")
            return {
                "success": False,
                "error": "Spreadsheet ID is required",
                "next_nodes": [],
            }

        sheet_id = self.get_parameter("sheet_id")
        if hasattr(context, "resolve_value"):
            sheet_id = context.resolve_value(sheet_id)

        if sheet_id is None:
            self._set_error_outputs("Sheet ID is required")
            return {"success": False, "error": "Sheet ID is required", "next_nodes": []}

        sheet_id = int(sheet_id)

        await client.delete_sheet(
            spreadsheet_id=spreadsheet_id,
            sheet_id=sheet_id,
        )

        self.set_output_value("success", True)
        self.set_output_value("error", "")
        self.set_output_value(
            "result",
            {"deleted": True, "sheet_id": sheet_id},
        )

        logger.info(f"Deleted sheet {sheet_id} from {spreadsheet_id}")

        return {
            "success": True,
            "data": {"sheet_id": sheet_id, "deleted": True},
            "next_nodes": ["exec_out"],
        }


@properties()
@node(category="google")
class SheetsCopySheetNode(SheetsBaseNode):
    """
    Copy a sheet to another spreadsheet.

    Inputs:
        - source_spreadsheet_id: Source spreadsheet ID
        - source_sheet_id: Sheet ID to copy
        - destination_spreadsheet_id: Target spreadsheet ID

    Outputs:
        - success: Whether operation succeeded
        - new_sheet_id: ID of the copied sheet
        - new_sheet_name: Name of the copied sheet
        - result: Full sheet properties
    """

    # @category: google
    # @requires: none
    # @ports: source_spreadsheet_id, source_sheet_id, destination_spreadsheet_id -> new_sheet_id, new_sheet_name

    NODE_NAME = "Copy Sheet"
    CATEGORY = "Google Sheets"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Copy Sheet", **kwargs)

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()

        self.add_input_port("source_spreadsheet_id", DataType.STRING, required=True)
        self.add_input_port("source_sheet_id", DataType.INTEGER, required=True)
        self.add_input_port(
            "destination_spreadsheet_id", DataType.STRING, required=True
        )

        self._define_common_output_ports()
        self.add_output_port("new_sheet_id", DataType.INTEGER)
        self.add_output_port("new_sheet_name", DataType.STRING)

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Copy a sheet to another spreadsheet."""
        source_id = self.get_parameter("source_spreadsheet_id")
        if hasattr(context, "resolve_value"):
            source_id = context.resolve_value(source_id)

        if not source_id:
            self._set_error_outputs("Source spreadsheet ID is required")
            return {
                "success": False,
                "error": "Source spreadsheet ID is required",
                "next_nodes": [],
            }

        sheet_id = self.get_parameter("source_sheet_id")
        if hasattr(context, "resolve_value"):
            sheet_id = context.resolve_value(sheet_id)

        if sheet_id is None:
            self._set_error_outputs("Source sheet ID is required")
            return {
                "success": False,
                "error": "Source sheet ID is required",
                "next_nodes": [],
            }

        dest_id = self.get_parameter("destination_spreadsheet_id")
        if hasattr(context, "resolve_value"):
            dest_id = context.resolve_value(dest_id)

        if not dest_id:
            self._set_error_outputs("Destination spreadsheet ID is required")
            return {
                "success": False,
                "error": "Destination spreadsheet ID is required",
                "next_nodes": [],
            }

        result = await client.copy_sheet(
            source_spreadsheet_id=source_id,
            source_sheet_id=int(sheet_id),
            destination_spreadsheet_id=dest_id,
        )

        self.set_output_value("success", True)
        self.set_output_value("error", "")
        self.set_output_value("new_sheet_id", result.sheet_id)
        self.set_output_value("new_sheet_name", result.title)
        self.set_output_value(
            "result",
            {
                "sheet_id": result.sheet_id,
                "title": result.title,
                "index": result.index,
            },
        )

        logger.info(f"Copied sheet {sheet_id} to {dest_id}")

        return {
            "success": True,
            "data": {"new_sheet_id": result.sheet_id, "new_sheet_name": result.title},
            "next_nodes": ["exec_out"],
        }


@properties()
@node(category="google")
class SheetsDuplicateSheetNode(SheetsBaseNode):
    """
    Duplicate a sheet within the same spreadsheet.

    Inputs:
        - spreadsheet_id: Spreadsheet ID
        - source_sheet_id: Sheet ID to duplicate
        - new_sheet_name: Name for the duplicate (optional)
        - insert_index: Position for new sheet (optional)

    Outputs:
        - success: Whether operation succeeded
        - new_sheet_id: ID of the duplicated sheet
        - new_sheet_name: Name of the duplicated sheet
        - result: Full sheet properties
    """

    # @category: google
    # @requires: none
    # @ports: source_sheet_id, new_sheet_name, insert_index -> new_sheet_id, new_sheet_name

    NODE_NAME = "Duplicate Sheet"
    CATEGORY = "Google Sheets"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Duplicate Sheet", **kwargs)

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_spreadsheet_input_port()

        self.add_input_port("source_sheet_id", DataType.INTEGER, required=True)
        self.add_input_port("new_sheet_name", DataType.STRING, required=False)
        self.add_input_port("insert_index", DataType.INTEGER, required=False)

        self._define_common_output_ports()
        self.add_output_port("new_sheet_id", DataType.INTEGER)
        self.add_output_port("new_sheet_name", DataType.STRING)

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Duplicate a sheet within spreadsheet."""
        spreadsheet_id = self._get_spreadsheet_id(context)
        if not spreadsheet_id:
            self._set_error_outputs("Spreadsheet ID is required")
            return {
                "success": False,
                "error": "Spreadsheet ID is required",
                "next_nodes": [],
            }

        source_sheet_id = self.get_parameter("source_sheet_id")
        if hasattr(context, "resolve_value"):
            source_sheet_id = context.resolve_value(source_sheet_id)

        if source_sheet_id is None:
            self._set_error_outputs("Source sheet ID is required")
            return {
                "success": False,
                "error": "Source sheet ID is required",
                "next_nodes": [],
            }

        new_name = self.get_parameter("new_sheet_name")
        if new_name and hasattr(context, "resolve_value"):
            new_name = context.resolve_value(new_name)

        insert_index = self.get_parameter("insert_index")

        # Build duplicate request
        dup_request: Dict[str, Any] = {
            "sourceSheetId": int(source_sheet_id),
        }
        if new_name:
            dup_request["newSheetName"] = new_name
        if insert_index is not None:
            dup_request["insertSheetIndex"] = int(insert_index)

        # Use batchUpdate API
        result = await client.batch_update(
            spreadsheet_id=spreadsheet_id,
            requests=[{"duplicateSheet": dup_request}],
        )

        replies = result.get("replies", [{}])
        dup_reply = replies[0].get("duplicateSheet", {})
        props = dup_reply.get("properties", {})

        new_sheet_id = props.get("sheetId", 0)
        new_sheet_name = props.get("title", "")

        self.set_output_value("success", True)
        self.set_output_value("error", "")
        self.set_output_value("new_sheet_id", new_sheet_id)
        self.set_output_value("new_sheet_name", new_sheet_name)
        self.set_output_value("result", props)

        logger.info(f"Duplicated sheet {source_sheet_id} as '{new_sheet_name}'")

        return {
            "success": True,
            "data": {"new_sheet_id": new_sheet_id, "new_sheet_name": new_sheet_name},
            "next_nodes": ["exec_out"],
        }


@properties()
@node(category="google")
class SheetsRenameSheetNode(SheetsBaseNode):
    """
    Rename a sheet in a spreadsheet.

    Inputs:
        - spreadsheet_id: Spreadsheet ID
        - sheet_id: Numeric ID of sheet to rename
        - new_name: New name for the sheet

    Outputs:
        - success: Whether operation succeeded
        - result: Update confirmation
    """

    # @category: google
    # @requires: none
    # @ports: sheet_id, new_name -> none

    NODE_NAME = "Rename Sheet"
    CATEGORY = "Google Sheets"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Rename Sheet", **kwargs)

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_spreadsheet_input_port()

        self.add_input_port("sheet_id", DataType.INTEGER, required=True)
        self.add_input_port("new_name", DataType.STRING, required=True)

        self._define_common_output_ports()

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Rename a sheet in spreadsheet."""
        spreadsheet_id = self._get_spreadsheet_id(context)
        if not spreadsheet_id:
            self._set_error_outputs("Spreadsheet ID is required")
            return {
                "success": False,
                "error": "Spreadsheet ID is required",
                "next_nodes": [],
            }

        sheet_id = self.get_parameter("sheet_id")
        if hasattr(context, "resolve_value"):
            sheet_id = context.resolve_value(sheet_id)

        if sheet_id is None:
            self._set_error_outputs("Sheet ID is required")
            return {"success": False, "error": "Sheet ID is required", "next_nodes": []}

        new_name = self.get_parameter("new_name")
        if hasattr(context, "resolve_value"):
            new_name = context.resolve_value(new_name)

        if not new_name:
            self._set_error_outputs("New name is required")
            return {"success": False, "error": "New name is required", "next_nodes": []}

        # Use batchUpdate API for rename
        await client.batch_update(
            spreadsheet_id=spreadsheet_id,
            requests=[
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": int(sheet_id),
                            "title": new_name,
                        },
                        "fields": "title",
                    }
                }
            ],
        )

        self.set_output_value("success", True)
        self.set_output_value("error", "")
        self.set_output_value(
            "result",
            {"sheet_id": int(sheet_id), "new_name": new_name},
        )

        logger.info(f"Renamed sheet {sheet_id} to '{new_name}'")

        return {
            "success": True,
            "data": {"sheet_id": int(sheet_id), "new_name": new_name},
            "next_nodes": ["exec_out"],
        }


__all__ = [
    "SheetsCreateSpreadsheetNode",
    "SheetsGetSpreadsheetNode",
    "SheetsAddSheetNode",
    "SheetsDeleteSheetNode",
    "SheetsCopySheetNode",
    "SheetsDuplicateSheetNode",
    "SheetsRenameSheetNode",
]
