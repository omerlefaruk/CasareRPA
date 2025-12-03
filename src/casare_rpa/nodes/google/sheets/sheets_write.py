"""
CasareRPA - Google Sheets Write Nodes

Nodes for writing data to Google Sheets: cells, ranges, rows, and managing data.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    PortType,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.infrastructure.resources.google_sheets_client import GoogleSheetsClient
from casare_rpa.nodes.google.sheets.sheets_base import SheetsBaseNode


# ============================================================================
# Reusable Property Definitions for Sheets Write Nodes
# ============================================================================

SHEETS_SERVICE_ACCOUNT = PropertyDef(
    "service_account_file",
    PropertyType.FILE_PATH,
    default="",
    label="Service Account File",
    placeholder="/path/to/credentials.json",
    tooltip="Google service account JSON credentials file",
    tab="connection",
)

SHEETS_ACCESS_TOKEN = PropertyDef(
    "access_token",
    PropertyType.STRING,
    default="",
    label="Access Token",
    placeholder="ya29.xxx...",
    tooltip="OAuth 2.0 access token (alternative to service account)",
    tab="connection",
)

SHEETS_CREDENTIAL_NAME = PropertyDef(
    "credential_name",
    PropertyType.STRING,
    default="",
    label="Credential Name",
    placeholder="google_sheets",
    tooltip="Name of stored Google credential (alternative to direct auth)",
    tab="connection",
)

SHEETS_SPREADSHEET_ID = PropertyDef(
    "spreadsheet_id",
    PropertyType.STRING,
    default="",
    required=True,
    label="Spreadsheet ID",
    placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    tooltip="Google Sheets spreadsheet ID (from URL)",
)

SHEETS_SHEET_NAME = PropertyDef(
    "sheet_name",
    PropertyType.STRING,
    default="Sheet1",
    label="Sheet Name",
    placeholder="Sheet1",
    tooltip="Name of the sheet/tab within the spreadsheet",
)

SHEETS_VALUE_INPUT_OPTION = PropertyDef(
    "value_input_option",
    PropertyType.CHOICE,
    default="USER_ENTERED",
    choices=["USER_ENTERED", "RAW"],
    label="Value Input Option",
    tooltip="USER_ENTERED parses values (dates, formulas), RAW stores as-is",
    tab="advanced",
)


@node_schema(
    SHEETS_SERVICE_ACCOUNT,
    SHEETS_ACCESS_TOKEN,
    SHEETS_CREDENTIAL_NAME,
    SHEETS_SPREADSHEET_ID,
    SHEETS_SHEET_NAME,
    PropertyDef(
        "cell",
        PropertyType.STRING,
        default="A1",
        required=True,
        label="Cell",
        placeholder="A1",
        tooltip="Cell reference in A1 notation",
    ),
    PropertyDef(
        "value",
        PropertyType.ANY,
        default="",
        required=True,
        label="Value",
        placeholder="Enter value",
        tooltip="Value to write to the cell",
    ),
    SHEETS_VALUE_INPUT_OPTION,
)
@executable_node
class SheetsWriteCellNode(SheetsBaseNode):
    """
    Write a single cell value to Google Sheets.

    Inputs:
        - spreadsheet_id: Spreadsheet ID from URL
        - sheet_name: Sheet/tab name
        - cell: Cell reference in A1 notation (e.g., "A1", "B5")
        - value: Value to write

    Outputs:
        - updated_cells: Number of cells updated (1)
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "sheets_write_cell"
    NODE_CATEGORY = "Google Sheets"
    NODE_DISPLAY_NAME = "Sheets: Write Cell"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Sheets Write Cell", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_spreadsheet_input_port()

        self.add_input_port(
            "sheet_name", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("cell", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port("value", PortType.INPUT, DataType.ANY, required=True)
        self.add_input_port(
            "value_input_option", PortType.INPUT, DataType.STRING, required=False
        )

        self._define_common_output_ports()
        self.add_output_port("updated_cells", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("updated_range", PortType.OUTPUT, DataType.STRING)

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Write a single cell value."""
        spreadsheet_id = self._get_spreadsheet_id(context)

        sheet_name = self.get_parameter("sheet_name")
        if hasattr(context, "resolve_value") and sheet_name:
            sheet_name = context.resolve_value(sheet_name)
        sheet_name = sheet_name or "Sheet1"

        cell = self.get_parameter("cell")
        if hasattr(context, "resolve_value") and cell:
            cell = context.resolve_value(cell)

        if not cell:
            self._set_error_outputs("Cell reference is required")
            return {
                "success": False,
                "error": "Cell reference is required",
                "next_nodes": [],
            }

        value = self.get_parameter("value")
        if hasattr(context, "resolve_value") and value is not None:
            value = context.resolve_value(value)

        value_input_option = self.get_parameter("value_input_option") or "USER_ENTERED"

        range_notation = self.build_a1_range(sheet_name, start_cell=cell)
        logger.debug(f"Writing to cell {range_notation} in {spreadsheet_id}")

        result = await client.update_values(
            spreadsheet_id,
            range_notation,
            [[value]],
            value_input_option=value_input_option,
        )

        updated_cells = result.get("updatedCells", 1)
        updated_range = result.get("updatedRange", range_notation)

        self._set_success_outputs(
            {"updated_cells": updated_cells, "updated_range": updated_range}
        )
        self.set_output_value("updated_cells", updated_cells)
        self.set_output_value("updated_range", updated_range)

        logger.info(f"Sheets cell {cell} written successfully")

        return {
            "success": True,
            "updated_cells": updated_cells,
            "updated_range": updated_range,
            "next_nodes": [],
        }


@node_schema(
    SHEETS_SERVICE_ACCOUNT,
    SHEETS_ACCESS_TOKEN,
    SHEETS_CREDENTIAL_NAME,
    SHEETS_SPREADSHEET_ID,
    PropertyDef(
        "range",
        PropertyType.STRING,
        default="Sheet1!A1:B10",
        required=True,
        label="Range",
        placeholder="Sheet1!A1:B10",
        tooltip="Range in A1 notation (e.g., 'Sheet1!A1:B10')",
    ),
    PropertyDef(
        "values",
        PropertyType.JSON,
        default=[],
        required=True,
        label="Values",
        placeholder="[[1,2],[3,4]]",
        tooltip="2D array of values to write",
    ),
    SHEETS_VALUE_INPUT_OPTION,
)
@executable_node
class SheetsWriteRangeNode(SheetsBaseNode):
    """
    Write a range of values to Google Sheets.

    Inputs:
        - spreadsheet_id: Spreadsheet ID from URL
        - range: A1 notation range (e.g., "Sheet1!A1:B10")
        - values: 2D array of values to write

    Outputs:
        - updated_cells: Number of cells updated
        - updated_rows: Number of rows updated
        - updated_columns: Number of columns updated
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "sheets_write_range"
    NODE_CATEGORY = "Google Sheets"
    NODE_DISPLAY_NAME = "Sheets: Write Range"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Sheets Write Range", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_spreadsheet_input_port()

        self.add_input_port("range", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port("values", PortType.INPUT, DataType.ARRAY, required=True)
        self.add_input_port(
            "value_input_option", PortType.INPUT, DataType.STRING, required=False
        )

        self._define_common_output_ports()
        self.add_output_port("updated_cells", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("updated_rows", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("updated_columns", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("updated_range", PortType.OUTPUT, DataType.STRING)

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Write a range of values."""
        spreadsheet_id = self._get_spreadsheet_id(context)

        range_notation = self.get_parameter("range")
        if hasattr(context, "resolve_value") and range_notation:
            range_notation = context.resolve_value(range_notation)

        if not range_notation:
            self._set_error_outputs("Range is required")
            return {"success": False, "error": "Range is required", "next_nodes": []}

        values = self.get_parameter("values")
        if hasattr(context, "resolve_value") and values:
            values = context.resolve_value(values)

        if not values or not isinstance(values, list):
            self._set_error_outputs("Values must be a 2D array")
            return {
                "success": False,
                "error": "Values must be a 2D array",
                "next_nodes": [],
            }

        if values and not isinstance(values[0], list):
            values = [values]

        value_input_option = self.get_parameter("value_input_option") or "USER_ENTERED"

        logger.debug(f"Writing to range {range_notation} in {spreadsheet_id}")

        result = await client.update_values(
            spreadsheet_id,
            range_notation,
            values,
            value_input_option=value_input_option,
        )

        updated_cells = result.get("updatedCells", 0)
        updated_rows = result.get("updatedRows", len(values))
        updated_columns = result.get(
            "updatedColumns", max(len(r) for r in values) if values else 0
        )
        updated_range = result.get("updatedRange", range_notation)

        self._set_success_outputs(
            {
                "updated_cells": updated_cells,
                "updated_rows": updated_rows,
                "updated_columns": updated_columns,
            }
        )
        self.set_output_value("updated_cells", updated_cells)
        self.set_output_value("updated_rows", updated_rows)
        self.set_output_value("updated_columns", updated_columns)
        self.set_output_value("updated_range", updated_range)

        logger.info(f"Sheets range written: {updated_cells} cells")

        return {
            "success": True,
            "updated_cells": updated_cells,
            "updated_rows": updated_rows,
            "updated_columns": updated_columns,
            "updated_range": updated_range,
            "next_nodes": [],
        }


@node_schema(
    SHEETS_SERVICE_ACCOUNT,
    SHEETS_ACCESS_TOKEN,
    SHEETS_CREDENTIAL_NAME,
    SHEETS_SPREADSHEET_ID,
    SHEETS_SHEET_NAME,
    PropertyDef(
        "values",
        PropertyType.JSON,
        default=[],
        required=True,
        label="Row Values",
        placeholder='["value1", "value2", "value3"]',
        tooltip="Array of values for the new row",
    ),
    SHEETS_VALUE_INPUT_OPTION,
)
@executable_node
class SheetsAppendRowNode(SheetsBaseNode):
    """
    Append a row to the end of data in a Google Sheet.

    Inputs:
        - spreadsheet_id: Spreadsheet ID from URL
        - sheet_name: Sheet/tab name
        - values: Array of values for the new row

    Outputs:
        - updated_cells: Number of cells updated
        - updated_range: Range that was updated
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "sheets_append_row"
    NODE_CATEGORY = "Google Sheets"
    NODE_DISPLAY_NAME = "Sheets: Append Row"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Sheets Append Row", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_spreadsheet_input_port()

        self.add_input_port(
            "sheet_name", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("values", PortType.INPUT, DataType.ARRAY, required=True)
        self.add_input_port(
            "value_input_option", PortType.INPUT, DataType.STRING, required=False
        )

        self._define_common_output_ports()
        self.add_output_port("updated_cells", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("updated_range", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("table_range", PortType.OUTPUT, DataType.STRING)

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Append a row to the end of data."""
        spreadsheet_id = self._get_spreadsheet_id(context)

        sheet_name = self.get_parameter("sheet_name")
        if hasattr(context, "resolve_value") and sheet_name:
            sheet_name = context.resolve_value(sheet_name)
        sheet_name = sheet_name or "Sheet1"

        values = self.get_parameter("values")
        if hasattr(context, "resolve_value") and values:
            values = context.resolve_value(values)

        if not values or not isinstance(values, list):
            self._set_error_outputs("Values must be an array")
            return {
                "success": False,
                "error": "Values must be an array",
                "next_nodes": [],
            }

        if isinstance(values[0], list):
            values_2d = values
        else:
            values_2d = [values]

        value_input_option = self.get_parameter("value_input_option") or "USER_ENTERED"

        range_notation = f"{sheet_name}!A:A"

        logger.debug(f"Appending row to {sheet_name} in {spreadsheet_id}")

        result = await client.append_values(
            spreadsheet_id,
            range_notation,
            values_2d,
            value_input_option=value_input_option,
        )

        updates = result.get("updates", {})
        updated_cells = updates.get("updatedCells", len(values_2d[0]))
        updated_range = updates.get("updatedRange", "")
        table_range = result.get("tableRange", "")

        self._set_success_outputs(
            {
                "updated_cells": updated_cells,
                "updated_range": updated_range,
            }
        )
        self.set_output_value("updated_cells", updated_cells)
        self.set_output_value("updated_range", updated_range)
        self.set_output_value("table_range", table_range)

        logger.info(f"Sheets row appended: {updated_cells} cells at {updated_range}")

        return {
            "success": True,
            "updated_cells": updated_cells,
            "updated_range": updated_range,
            "table_range": table_range,
            "next_nodes": [],
        }


@node_schema(
    SHEETS_SERVICE_ACCOUNT,
    SHEETS_ACCESS_TOKEN,
    SHEETS_CREDENTIAL_NAME,
    SHEETS_SPREADSHEET_ID,
    SHEETS_SHEET_NAME,
    PropertyDef(
        "row_num",
        PropertyType.INTEGER,
        default=1,
        required=True,
        label="Row Number",
        placeholder="1",
        tooltip="1-based row number to update",
        min_value=1,
    ),
    PropertyDef(
        "values",
        PropertyType.JSON,
        default=[],
        required=True,
        label="Row Values",
        placeholder='["value1", "value2", "value3"]',
        tooltip="Array of values to write to the row",
    ),
    PropertyDef(
        "start_col",
        PropertyType.STRING,
        default="A",
        label="Start Column",
        placeholder="A",
        tooltip="Starting column letter",
    ),
    SHEETS_VALUE_INPUT_OPTION,
)
@executable_node
class SheetsUpdateRowNode(SheetsBaseNode):
    """
    Update an existing row in Google Sheets.

    Inputs:
        - spreadsheet_id: Spreadsheet ID from URL
        - sheet_name: Sheet/tab name
        - row_num: 1-based row number to update
        - values: Array of values to write

    Outputs:
        - updated_cells: Number of cells updated
        - updated_range: Range that was updated
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "sheets_update_row"
    NODE_CATEGORY = "Google Sheets"
    NODE_DISPLAY_NAME = "Sheets: Update Row"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Sheets Update Row", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_spreadsheet_input_port()

        self.add_input_port(
            "sheet_name", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("row_num", PortType.INPUT, DataType.INTEGER, required=True)
        self.add_input_port("values", PortType.INPUT, DataType.ARRAY, required=True)
        self.add_input_port(
            "start_col", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "value_input_option", PortType.INPUT, DataType.STRING, required=False
        )

        self._define_common_output_ports()
        self.add_output_port("updated_cells", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("updated_range", PortType.OUTPUT, DataType.STRING)

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Update an existing row."""
        spreadsheet_id = self._get_spreadsheet_id(context)

        sheet_name = self.get_parameter("sheet_name")
        if hasattr(context, "resolve_value") and sheet_name:
            sheet_name = context.resolve_value(sheet_name)
        sheet_name = sheet_name or "Sheet1"

        row_num = self.get_parameter("row_num")
        if hasattr(context, "resolve_value"):
            row_num = context.resolve_value(row_num)
        row_num = int(row_num) if row_num else 1

        if row_num < 1:
            self._set_error_outputs("Row number must be at least 1")
            return {
                "success": False,
                "error": "Row number must be at least 1",
                "next_nodes": [],
            }

        values = self.get_parameter("values")
        if hasattr(context, "resolve_value") and values:
            values = context.resolve_value(values)

        if not values or not isinstance(values, list):
            self._set_error_outputs("Values must be an array")
            return {
                "success": False,
                "error": "Values must be an array",
                "next_nodes": [],
            }

        start_col = self.get_parameter("start_col") or "A"
        value_input_option = self.get_parameter("value_input_option") or "USER_ENTERED"

        end_col_idx = self.column_letter_to_index(start_col) + len(values) - 1
        end_col = self.index_to_column_letter(end_col_idx)
        range_notation = f"{sheet_name}!{start_col}{row_num}:{end_col}{row_num}"

        logger.debug(f"Updating row {row_num} in {spreadsheet_id}")

        result = await client.update_values(
            spreadsheet_id,
            range_notation,
            [values],
            value_input_option=value_input_option,
        )

        updated_cells = result.get("updatedCells", len(values))
        updated_range = result.get("updatedRange", range_notation)

        self._set_success_outputs(
            {
                "updated_cells": updated_cells,
                "updated_range": updated_range,
            }
        )
        self.set_output_value("updated_cells", updated_cells)
        self.set_output_value("updated_range", updated_range)

        logger.info(f"Sheets row {row_num} updated: {updated_cells} cells")

        return {
            "success": True,
            "updated_cells": updated_cells,
            "updated_range": updated_range,
            "row_num": row_num,
            "next_nodes": [],
        }


@node_schema(
    SHEETS_SERVICE_ACCOUNT,
    SHEETS_ACCESS_TOKEN,
    SHEETS_CREDENTIAL_NAME,
    SHEETS_SPREADSHEET_ID,
    SHEETS_SHEET_NAME,
    PropertyDef(
        "row_num",
        PropertyType.INTEGER,
        default=1,
        required=True,
        label="Row Number",
        placeholder="1",
        tooltip="1-based row number where to insert",
        min_value=1,
    ),
    PropertyDef(
        "values",
        PropertyType.JSON,
        default=[],
        required=False,
        label="Row Values",
        placeholder='["value1", "value2"]',
        tooltip="Optional values to write to the new row",
    ),
    SHEETS_VALUE_INPUT_OPTION,
)
@executable_node
class SheetsInsertRowNode(SheetsBaseNode):
    """
    Insert a new row at a specific position in Google Sheets.

    This inserts an empty row at the specified position and optionally
    writes values to it. Existing rows are shifted down.

    Inputs:
        - spreadsheet_id: Spreadsheet ID from URL
        - sheet_name: Sheet/tab name
        - row_num: 1-based row number where to insert
        - values: Optional array of values for the new row

    Outputs:
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "sheets_insert_row"
    NODE_CATEGORY = "Google Sheets"
    NODE_DISPLAY_NAME = "Sheets: Insert Row"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Sheets Insert Row", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_spreadsheet_input_port()

        self.add_input_port(
            "sheet_name", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("row_num", PortType.INPUT, DataType.INTEGER, required=True)
        self.add_input_port("values", PortType.INPUT, DataType.ARRAY, required=False)
        self.add_input_port(
            "value_input_option", PortType.INPUT, DataType.STRING, required=False
        )

        self._define_common_output_ports()
        self.add_output_port("inserted_row", PortType.OUTPUT, DataType.INTEGER)

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Insert a new row at a specific position."""
        spreadsheet_id = self._get_spreadsheet_id(context)

        sheet_name = self.get_parameter("sheet_name")
        if hasattr(context, "resolve_value") and sheet_name:
            sheet_name = context.resolve_value(sheet_name)
        sheet_name = sheet_name or "Sheet1"

        row_num = self.get_parameter("row_num")
        if hasattr(context, "resolve_value"):
            row_num = context.resolve_value(row_num)
        row_num = int(row_num) if row_num else 1

        if row_num < 1:
            self._set_error_outputs("Row number must be at least 1")
            return {
                "success": False,
                "error": "Row number must be at least 1",
                "next_nodes": [],
            }

        logger.debug(f"Inserting row at position {row_num} in {spreadsheet_id}")

        sheet_info = await client.get_sheet_by_name(spreadsheet_id, sheet_name)
        if not sheet_info:
            self._set_error_outputs(f"Sheet '{sheet_name}' not found")
            return {
                "success": False,
                "error": f"Sheet '{sheet_name}' not found",
                "next_nodes": [],
            }

        sheet_id = sheet_info.sheet_id
        insert_request = {
            "requests": [
                {
                    "insertDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": row_num - 1,
                            "endIndex": row_num,
                        },
                        "inheritFromBefore": row_num > 1,
                    }
                }
            ]
        }

        await client.batch_update(spreadsheet_id, insert_request["requests"])

        values = self.get_parameter("values")
        if hasattr(context, "resolve_value") and values:
            values = context.resolve_value(values)

        if values and isinstance(values, list):
            value_input_option = (
                self.get_parameter("value_input_option") or "USER_ENTERED"
            )
            end_col_idx = len(values) - 1
            end_col = self.index_to_column_letter(end_col_idx)
            range_notation = f"{sheet_name}!A{row_num}:{end_col}{row_num}"

            await client.update_values(
                spreadsheet_id,
                range_notation,
                [values],
                value_input_option=value_input_option,
            )

        self._set_success_outputs({"inserted_row": row_num})
        self.set_output_value("inserted_row", row_num)

        logger.info(f"Sheets row inserted at position {row_num}")

        return {
            "success": True,
            "inserted_row": row_num,
            "next_nodes": [],
        }


@node_schema(
    SHEETS_SERVICE_ACCOUNT,
    SHEETS_ACCESS_TOKEN,
    SHEETS_CREDENTIAL_NAME,
    SHEETS_SPREADSHEET_ID,
    SHEETS_SHEET_NAME,
    PropertyDef(
        "row_num",
        PropertyType.INTEGER,
        default=1,
        required=True,
        label="Row Number",
        placeholder="1",
        tooltip="1-based row number to delete",
        min_value=1,
    ),
    PropertyDef(
        "num_rows",
        PropertyType.INTEGER,
        default=1,
        label="Number of Rows",
        placeholder="1",
        tooltip="Number of rows to delete (default: 1)",
        min_value=1,
    ),
)
@executable_node
class SheetsDeleteRowNode(SheetsBaseNode):
    """
    Delete one or more rows from Google Sheets.

    Inputs:
        - spreadsheet_id: Spreadsheet ID from URL
        - sheet_name: Sheet/tab name
        - row_num: 1-based row number to start deletion
        - num_rows: Number of rows to delete (default: 1)

    Outputs:
        - deleted_rows: Number of rows deleted
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "sheets_delete_row"
    NODE_CATEGORY = "Google Sheets"
    NODE_DISPLAY_NAME = "Sheets: Delete Row"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Sheets Delete Row", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_spreadsheet_input_port()

        self.add_input_port(
            "sheet_name", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("row_num", PortType.INPUT, DataType.INTEGER, required=True)
        self.add_input_port(
            "num_rows", PortType.INPUT, DataType.INTEGER, required=False
        )

        self._define_common_output_ports()
        self.add_output_port("deleted_rows", PortType.OUTPUT, DataType.INTEGER)

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Delete one or more rows."""
        spreadsheet_id = self._get_spreadsheet_id(context)

        sheet_name = self.get_parameter("sheet_name")
        if hasattr(context, "resolve_value") and sheet_name:
            sheet_name = context.resolve_value(sheet_name)
        sheet_name = sheet_name or "Sheet1"

        row_num = self.get_parameter("row_num")
        if hasattr(context, "resolve_value"):
            row_num = context.resolve_value(row_num)
        row_num = int(row_num) if row_num else 1

        if row_num < 1:
            self._set_error_outputs("Row number must be at least 1")
            return {
                "success": False,
                "error": "Row number must be at least 1",
                "next_nodes": [],
            }

        num_rows = self.get_parameter("num_rows")
        if hasattr(context, "resolve_value"):
            num_rows = context.resolve_value(num_rows)
        num_rows = int(num_rows) if num_rows else 1

        logger.debug(
            f"Deleting {num_rows} row(s) starting at {row_num} in {spreadsheet_id}"
        )

        sheet_info = await client.get_sheet_by_name(spreadsheet_id, sheet_name)
        if not sheet_info:
            self._set_error_outputs(f"Sheet '{sheet_name}' not found")
            return {
                "success": False,
                "error": f"Sheet '{sheet_name}' not found",
                "next_nodes": [],
            }

        sheet_id = sheet_info.sheet_id
        delete_request = {
            "requests": [
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": row_num - 1,
                            "endIndex": row_num - 1 + num_rows,
                        }
                    }
                }
            ]
        }

        await client.batch_update(spreadsheet_id, delete_request["requests"])

        self._set_success_outputs({"deleted_rows": num_rows})
        self.set_output_value("deleted_rows", num_rows)

        logger.info(f"Sheets {num_rows} row(s) deleted starting at row {row_num}")

        return {
            "success": True,
            "deleted_rows": num_rows,
            "start_row": row_num,
            "next_nodes": [],
        }


@node_schema(
    SHEETS_SERVICE_ACCOUNT,
    SHEETS_ACCESS_TOKEN,
    SHEETS_CREDENTIAL_NAME,
    SHEETS_SPREADSHEET_ID,
    PropertyDef(
        "range",
        PropertyType.STRING,
        default="Sheet1!A1:Z1000",
        required=True,
        label="Range",
        placeholder="Sheet1!A1:Z1000",
        tooltip="Range in A1 notation to clear (e.g., 'Sheet1!A1:Z1000')",
    ),
)
@executable_node
class SheetsClearRangeNode(SheetsBaseNode):
    """
    Clear values from a range in Google Sheets.

    This clears the values but keeps formatting intact.

    Inputs:
        - spreadsheet_id: Spreadsheet ID from URL
        - range: A1 notation range to clear

    Outputs:
        - cleared_range: The range that was cleared
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "sheets_clear_range"
    NODE_CATEGORY = "Google Sheets"
    NODE_DISPLAY_NAME = "Sheets: Clear Range"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Sheets Clear Range", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_spreadsheet_input_port()

        self.add_input_port("range", PortType.INPUT, DataType.STRING, required=True)

        self._define_common_output_ports()
        self.add_output_port("cleared_range", PortType.OUTPUT, DataType.STRING)

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Clear values from a range."""
        spreadsheet_id = self._get_spreadsheet_id(context)

        range_notation = self.get_parameter("range")
        if hasattr(context, "resolve_value") and range_notation:
            range_notation = context.resolve_value(range_notation)

        if not range_notation:
            self._set_error_outputs("Range is required")
            return {"success": False, "error": "Range is required", "next_nodes": []}

        logger.debug(f"Clearing range {range_notation} in {spreadsheet_id}")

        result = await client.clear_values(spreadsheet_id, range_notation)

        cleared_range = result.get("clearedRange", range_notation)

        self._set_success_outputs({"cleared_range": cleared_range})
        self.set_output_value("cleared_range", cleared_range)

        logger.info(f"Sheets range cleared: {cleared_range}")

        return {
            "success": True,
            "cleared_range": cleared_range,
            "next_nodes": [],
        }


__all__ = [
    "SheetsWriteCellNode",
    "SheetsWriteRangeNode",
    "SheetsAppendRowNode",
    "SheetsUpdateRowNode",
    "SheetsInsertRowNode",
    "SheetsDeleteRowNode",
    "SheetsClearRangeNode",
]
