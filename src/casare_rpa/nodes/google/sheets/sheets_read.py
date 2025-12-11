"""
CasareRPA - Google Sheets Read Nodes

Nodes for reading data from Google Sheets: cells, ranges, rows, columns, and search.
"""

from __future__ import annotations

from typing import Any, List

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
from casare_rpa.nodes.google.google_base import SheetsBaseNode


# ============================================================================
# Reusable Property Definitions for Sheets Read Nodes
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

SHEETS_VALUE_RENDER = PropertyDef(
    "value_render_option",
    PropertyType.CHOICE,
    default="FORMATTED_VALUE",
    choices=["FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA"],
    label="Value Render",
    tooltip="How values should be represented: formatted, raw, or formula",
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
    SHEETS_VALUE_RENDER,
)
@executable_node
class SheetsGetCellNode(SheetsBaseNode):
    """
    Read a single cell value from Google Sheets.

    Inputs:
        - spreadsheet_id: Spreadsheet ID from URL
        - sheet_name: Sheet/tab name
        - cell: Cell reference in A1 notation (e.g., "A1", "B5")

    Outputs:
        - value: Cell value (any type)
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: sheet_name, cell, value_render_option -> value

    NODE_TYPE = "sheets_get_cell"
    NODE_CATEGORY = "Google Sheets"
    NODE_DISPLAY_NAME = "Sheets: Get Cell"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Sheets Get Cell", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_spreadsheet_input_port()

        self.add_input_port(
            "sheet_name", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("cell", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port(
            "value_render_option", PortType.INPUT, DataType.STRING, required=False
        )

        self._define_common_output_ports()
        self.add_output_port("value", PortType.OUTPUT, DataType.ANY)

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Read a single cell value."""
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

        value_render = self.get_parameter("value_render_option") or "FORMATTED_VALUE"

        range_notation = self.build_a1_range(sheet_name, start_cell=cell)
        logger.debug(f"Reading cell {range_notation} from {spreadsheet_id}")

        values = await client.get_values(
            spreadsheet_id,
            range_notation,
            value_render_option=value_render,
        )

        value = values[0][0] if values and values[0] else None

        self._set_success_outputs(value)
        self.set_output_value("value", value)

        logger.info(f"Sheets cell {cell} read successfully: {value}")

        return {
            "success": True,
            "value": value,
            "cell": cell,
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
    SHEETS_VALUE_RENDER,
    PropertyDef(
        "major_dimension",
        PropertyType.CHOICE,
        default="ROWS",
        choices=["ROWS", "COLUMNS"],
        label="Major Dimension",
        tooltip="Whether to return rows or columns as the major dimension",
        tab="advanced",
    ),
)
@executable_node
class SheetsGetRangeNode(SheetsBaseNode):
    """
    Read a range of values from Google Sheets.

    Inputs:
        - spreadsheet_id: Spreadsheet ID from URL
        - range: A1 notation range (e.g., "Sheet1!A1:B10")

    Outputs:
        - values: 2D list of cell values
        - row_count: Number of rows returned
        - column_count: Number of columns returned
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: range, value_render_option, major_dimension -> values, row_count, column_count

    NODE_TYPE = "sheets_get_range"
    NODE_CATEGORY = "Google Sheets"
    NODE_DISPLAY_NAME = "Sheets: Get Range"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Sheets Get Range", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_spreadsheet_input_port()

        self.add_input_port("range", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port(
            "value_render_option", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "major_dimension", PortType.INPUT, DataType.STRING, required=False
        )

        self._define_common_output_ports()
        self.add_output_port("values", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("row_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("column_count", PortType.OUTPUT, DataType.INTEGER)

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Read a range of values."""
        spreadsheet_id = self._get_spreadsheet_id(context)

        range_notation = self.get_parameter("range")
        if hasattr(context, "resolve_value") and range_notation:
            range_notation = context.resolve_value(range_notation)

        if not range_notation:
            self._set_error_outputs("Range is required")
            return {"success": False, "error": "Range is required", "next_nodes": []}

        value_render = self.get_parameter("value_render_option") or "FORMATTED_VALUE"

        logger.debug(f"Reading range {range_notation} from {spreadsheet_id}")

        values = await client.get_values(
            spreadsheet_id,
            range_notation,
            value_render_option=value_render,
        )

        row_count = len(values)
        column_count = max(len(row) for row in values) if values else 0

        self._set_success_outputs(values)
        self.set_output_value("values", values)
        self.set_output_value("row_count", row_count)
        self.set_output_value("column_count", column_count)

        logger.info(f"Sheets range read: {row_count} rows x {column_count} cols")

        return {
            "success": True,
            "values": values,
            "row_count": row_count,
            "column_count": column_count,
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
        tooltip="1-based row number to read",
        min_value=1,
    ),
    PropertyDef(
        "start_col",
        PropertyType.STRING,
        default="A",
        label="Start Column",
        placeholder="A",
        tooltip="Starting column letter",
    ),
    PropertyDef(
        "end_col",
        PropertyType.STRING,
        default="Z",
        label="End Column",
        placeholder="Z",
        tooltip="Ending column letter",
    ),
    SHEETS_VALUE_RENDER,
)
@executable_node
class SheetsGetRowNode(SheetsBaseNode):
    """
    Read an entire row from Google Sheets.

    Inputs:
        - spreadsheet_id: Spreadsheet ID from URL
        - sheet_name: Sheet/tab name
        - row_num: 1-based row number

    Outputs:
        - values: List of cell values in the row
        - cell_count: Number of cells returned
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: sheet_name, row_num, start_col, end_col, value_render_option -> values, cell_count

    NODE_TYPE = "sheets_get_row"
    NODE_CATEGORY = "Google Sheets"
    NODE_DISPLAY_NAME = "Sheets: Get Row"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Sheets Get Row", **kwargs)
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
            "start_col", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("end_col", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port(
            "value_render_option", PortType.INPUT, DataType.STRING, required=False
        )

        self._define_common_output_ports()
        self.add_output_port("values", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("cell_count", PortType.OUTPUT, DataType.INTEGER)

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Read an entire row."""
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

        start_col = self.get_parameter("start_col") or "A"
        end_col = self.get_parameter("end_col") or "Z"
        value_render = self.get_parameter("value_render_option") or "FORMATTED_VALUE"

        range_notation = f"{sheet_name}!{start_col}{row_num}:{end_col}{row_num}"
        logger.debug(f"Reading row {range_notation} from {spreadsheet_id}")

        values = await client.get_values(
            spreadsheet_id,
            range_notation,
            value_render_option=value_render,
        )

        row_values: List[Any] = values[0] if values else []
        cell_count = len(row_values)

        self._set_success_outputs(row_values)
        self.set_output_value("values", row_values)
        self.set_output_value("cell_count", cell_count)

        logger.info(f"Sheets row {row_num} read: {cell_count} cells")

        return {
            "success": True,
            "values": row_values,
            "cell_count": cell_count,
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
        "column",
        PropertyType.STRING,
        default="A",
        required=True,
        label="Column",
        placeholder="A",
        tooltip="Column letter (e.g., 'A', 'B', 'AA')",
    ),
    PropertyDef(
        "start_row",
        PropertyType.INTEGER,
        default=1,
        label="Start Row",
        placeholder="1",
        tooltip="1-based starting row number",
        min_value=1,
    ),
    PropertyDef(
        "end_row",
        PropertyType.INTEGER,
        default=1000,
        label="End Row",
        placeholder="1000",
        tooltip="1-based ending row number",
        min_value=1,
    ),
    SHEETS_VALUE_RENDER,
)
@executable_node
class SheetsGetColumnNode(SheetsBaseNode):
    """
    Read an entire column from Google Sheets.

    Inputs:
        - spreadsheet_id: Spreadsheet ID from URL
        - sheet_name: Sheet/tab name
        - column: Column letter (e.g., "A", "B", "AA")

    Outputs:
        - values: List of cell values in the column
        - cell_count: Number of cells returned
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: sheet_name, column, start_row, end_row, value_render_option -> values, cell_count

    NODE_TYPE = "sheets_get_column"
    NODE_CATEGORY = "Google Sheets"
    NODE_DISPLAY_NAME = "Sheets: Get Column"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Sheets Get Column", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_spreadsheet_input_port()

        self.add_input_port(
            "sheet_name", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("column", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port(
            "start_row", PortType.INPUT, DataType.INTEGER, required=False
        )
        self.add_input_port("end_row", PortType.INPUT, DataType.INTEGER, required=False)
        self.add_input_port(
            "value_render_option", PortType.INPUT, DataType.STRING, required=False
        )

        self._define_common_output_ports()
        self.add_output_port("values", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("cell_count", PortType.OUTPUT, DataType.INTEGER)

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Read an entire column."""
        spreadsheet_id = self._get_spreadsheet_id(context)

        sheet_name = self.get_parameter("sheet_name")
        if hasattr(context, "resolve_value") and sheet_name:
            sheet_name = context.resolve_value(sheet_name)
        sheet_name = sheet_name or "Sheet1"

        column = self.get_parameter("column")
        if hasattr(context, "resolve_value") and column:
            column = context.resolve_value(column)

        if not column:
            self._set_error_outputs("Column letter is required")
            return {
                "success": False,
                "error": "Column letter is required",
                "next_nodes": [],
            }

        column = column.upper()
        start_row = int(self.get_parameter("start_row") or 1)
        end_row = int(self.get_parameter("end_row") or 1000)
        value_render = self.get_parameter("value_render_option") or "FORMATTED_VALUE"

        range_notation = f"{sheet_name}!{column}{start_row}:{column}{end_row}"
        logger.debug(f"Reading column {range_notation} from {spreadsheet_id}")

        values_2d = await client.get_values(
            spreadsheet_id,
            range_notation,
            value_render_option=value_render,
        )

        column_values: List[Any] = [row[0] if row else None for row in values_2d]
        while column_values and column_values[-1] is None:
            column_values.pop()

        cell_count = len(column_values)

        self._set_success_outputs(column_values)
        self.set_output_value("values", column_values)
        self.set_output_value("cell_count", cell_count)

        logger.info(f"Sheets column {column} read: {cell_count} cells")

        return {
            "success": True,
            "values": column_values,
            "cell_count": cell_count,
            "column": column,
            "next_nodes": [],
        }


@node_schema(
    SHEETS_SERVICE_ACCOUNT,
    SHEETS_ACCESS_TOKEN,
    SHEETS_CREDENTIAL_NAME,
    SHEETS_SPREADSHEET_ID,
    PropertyDef(
        "search_value",
        PropertyType.STRING,
        default="",
        required=True,
        label="Search Value",
        placeholder="search text",
        tooltip="Value to search for in the spreadsheet",
    ),
    SHEETS_SHEET_NAME,
    PropertyDef(
        "search_range",
        PropertyType.STRING,
        default="",
        label="Search Range",
        placeholder="A1:Z1000",
        tooltip="Optional range to limit search (empty = entire sheet)",
    ),
    PropertyDef(
        "match_case",
        PropertyType.BOOLEAN,
        default=False,
        label="Match Case",
        tooltip="Case-sensitive search",
    ),
    PropertyDef(
        "match_entire_cell",
        PropertyType.BOOLEAN,
        default=False,
        label="Match Entire Cell",
        tooltip="Only match if entire cell content equals search value",
    ),
)
@executable_node
class SheetsSearchNode(SheetsBaseNode):
    """
    Search for values in Google Sheets.

    Inputs:
        - spreadsheet_id: Spreadsheet ID from URL
        - search_value: Value to search for
        - sheet_name: Optional - limit search to specific sheet
        - search_range: Optional - limit search to specific range

    Outputs:
        - results: List of matches with cell, value, row, col info
        - match_count: Number of matches found
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: search_value, sheet_name, search_range, match_case, match_entire_cell -> results, match_count, first_match

    NODE_TYPE = "sheets_search"
    NODE_CATEGORY = "Google Sheets"
    NODE_DISPLAY_NAME = "Sheets: Search"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Sheets Search", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_spreadsheet_input_port()

        self.add_input_port(
            "search_value", PortType.INPUT, DataType.STRING, required=True
        )
        self.add_input_port(
            "sheet_name", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "search_range", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "match_case", PortType.INPUT, DataType.BOOLEAN, required=False
        )
        self.add_input_port(
            "match_entire_cell", PortType.INPUT, DataType.BOOLEAN, required=False
        )

        self._define_common_output_ports()
        self.add_output_port("results", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("match_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("first_match", PortType.OUTPUT, DataType.OBJECT)

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Search for values in the spreadsheet."""
        spreadsheet_id = self._get_spreadsheet_id(context)

        search_value = self.get_parameter("search_value")
        if hasattr(context, "resolve_value") and search_value:
            search_value = context.resolve_value(search_value)

        if not search_value:
            self._set_error_outputs("Search value is required")
            return {
                "success": False,
                "error": "Search value is required",
                "next_nodes": [],
            }

        sheet_name = self.get_parameter("sheet_name")
        if hasattr(context, "resolve_value") and sheet_name:
            sheet_name = context.resolve_value(sheet_name)

        search_range = self.get_parameter("search_range")
        if hasattr(context, "resolve_value") and search_range:
            search_range = context.resolve_value(search_range)

        match_case = bool(self.get_parameter("match_case"))
        match_entire_cell = bool(self.get_parameter("match_entire_cell"))

        logger.debug(f"Searching for '{search_value}' in {spreadsheet_id}")

        spreadsheet_info = await client.get_spreadsheet(spreadsheet_id)
        sheets_to_search = spreadsheet_info.sheets

        if sheet_name:
            sheets_to_search = [
                s
                for s in spreadsheet_info.sheets
                if s.get("properties", {}).get("title") == sheet_name
            ]

        results: List[dict] = []
        search_lower = search_value.lower() if not match_case else search_value

        for sheet in sheets_to_search:
            sheet_title = sheet.get("properties", {}).get("title", "Sheet1")
            grid_props = sheet.get("properties", {}).get("gridProperties", {})
            row_count = grid_props.get("rowCount", 1000)

            if search_range:
                range_to_search = f"{sheet_title}!{search_range}"
            else:
                range_to_search = f"'{sheet_title}'!A1:ZZ{row_count}"

            try:
                values = await client.get_values(spreadsheet_id, range_to_search)
            except Exception:
                continue

            for row_idx, row in enumerate(values):
                for col_idx, cell_value in enumerate(row):
                    cell_str = str(cell_value) if cell_value is not None else ""
                    compare_value = cell_str if match_case else cell_str.lower()

                    found = False
                    if match_entire_cell:
                        found = compare_value == (
                            search_value if match_case else search_lower
                        )
                    else:
                        found = search_lower in compare_value

                    if found:
                        cell_ref = self.indices_to_cell(row_idx, col_idx)
                        results.append(
                            {
                                "sheet": sheet_title,
                                "cell": cell_ref,
                                "row": row_idx + 1,
                                "column": self.index_to_column_letter(col_idx),
                                "column_index": col_idx + 1,
                                "value": cell_value,
                            }
                        )

        match_count = len(results)
        first_match = results[0] if results else None

        self._set_success_outputs(results)
        self.set_output_value("results", results)
        self.set_output_value("match_count", match_count)
        self.set_output_value("first_match", first_match)

        logger.info(f"Sheets search found {match_count} matches")

        return {
            "success": True,
            "results": results,
            "match_count": match_count,
            "first_match": first_match,
            "next_nodes": [],
        }


@node_schema(
    SHEETS_SERVICE_ACCOUNT,
    SHEETS_ACCESS_TOKEN,
    SHEETS_CREDENTIAL_NAME,
    SHEETS_SPREADSHEET_ID,
)
@executable_node
class SheetsGetSheetInfoNode(SheetsBaseNode):
    """
    Get spreadsheet metadata and sheet information.

    Inputs:
        - spreadsheet_id: Spreadsheet ID from URL

    Outputs:
        - title: Spreadsheet title
        - sheets: List of sheet info objects
        - sheet_count: Number of sheets
        - locale: Spreadsheet locale
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: none -> title, sheets, sheet_count, locale

    NODE_TYPE = "sheets_get_sheet_info"
    NODE_CATEGORY = "Google Sheets"
    NODE_DISPLAY_NAME = "Sheets: Get Sheet Info"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Sheets Get Sheet Info", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_spreadsheet_input_port()

        self._define_common_output_ports()
        self.add_output_port("title", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("sheets", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("sheet_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("locale", PortType.OUTPUT, DataType.STRING)

    async def _execute_sheets(
        self,
        context: ExecutionContext,
        client: GoogleSheetsClient,
    ) -> ExecutionResult:
        """Get spreadsheet metadata."""
        spreadsheet_id = self._get_spreadsheet_id(context)

        logger.debug(f"Getting sheet info for {spreadsheet_id}")

        spreadsheet_info = await client.get_spreadsheet(spreadsheet_id)

        sheets_list = []
        for sheet in spreadsheet_info.sheets:
            props = sheet.get("properties", {})
            grid_props = props.get("gridProperties", {})
            sheets_list.append(
                {
                    "sheet_id": props.get("sheetId"),
                    "title": props.get("title"),
                    "index": props.get("index"),
                    "row_count": grid_props.get("rowCount", 1000),
                    "column_count": grid_props.get("columnCount", 26),
                    "frozen_row_count": grid_props.get("frozenRowCount", 0),
                    "frozen_column_count": grid_props.get("frozenColumnCount", 0),
                }
            )

        title = spreadsheet_info.title
        sheet_count = len(sheets_list)
        locale = spreadsheet_info.locale

        result_data = {
            "title": title,
            "sheets": sheets_list,
            "sheet_count": sheet_count,
            "locale": locale,
        }

        self._set_success_outputs(result_data)
        self.set_output_value("title", title)
        self.set_output_value("sheets", sheets_list)
        self.set_output_value("sheet_count", sheet_count)
        self.set_output_value("locale", locale)

        logger.info(f"Sheets info retrieved: '{title}' with {sheet_count} sheets")

        return {
            "success": True,
            "title": title,
            "sheets": sheets_list,
            "sheet_count": sheet_count,
            "locale": locale,
            "next_nodes": [],
        }


__all__ = [
    "SheetsGetCellNode",
    "SheetsGetRangeNode",
    "SheetsGetRowNode",
    "SheetsGetColumnNode",
    "SheetsSearchNode",
    "SheetsGetSheetInfoNode",
]
