"""
Google Sheets nodes for CasareRPA.

Provides nodes for interacting with Google Sheets API:
- Cell and range operations
- Sheet management
- Row and column operations
- Formatting and batch operations
"""

from typing import Any, Dict

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, ExecutionResult
from casare_rpa.infrastructure.execution import ExecutionContext


async def _get_sheets_service(context: ExecutionContext, credential_name: str) -> Any:
    """Get authenticated Sheets service from context."""
    google_client = context.resources.get("google_client")
    if not google_client:
        raise RuntimeError(
            "Google client not initialized. " "Use 'Google: Authenticate' node first."
        )
    return await google_client.get_service("sheets", "v4", credential_name)


def _parse_range(spreadsheet_id: str, range_notation: str) -> str:
    """Ensure range notation is valid."""
    if "!" in range_notation:
        return range_notation
    return f"Sheet1!{range_notation}"


# =============================================================================
# Cell Operations
# =============================================================================


class SheetsGetCellNode(BaseNode):
    """Get value from a single cell."""

    # @category: google
    # @requires: none
    # @ports: spreadsheet_id, cell, sheet_name -> value, formatted_value, success, error

    NODE_NAME = "Sheets: Get Cell"
    CATEGORY = "google/sheets"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("spreadsheet_id", DataType.STRING, "Spreadsheet ID")
        self.add_input_port("cell", DataType.STRING, "Cell address (e.g., A1)")
        self.add_input_port("sheet_name", DataType.STRING, "Sheet name")
        self.add_exec_output()
        self.add_output_port("value", DataType.ANY, "Cell value")
        self.add_output_port("formatted_value", DataType.STRING, "Formatted value")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            spreadsheet_id = self.get_input_value(
                "spreadsheet_id"
            ) or self.get_parameter("spreadsheet_id", "")
            cell = self.get_input_value("cell") or self.get_parameter("cell", "A1")
            sheet_name = self.get_input_value("sheet_name") or self.get_parameter(
                "sheet_name", "Sheet1"
            )

            if not spreadsheet_id:
                raise ValueError("Spreadsheet ID is required")

            service = await _get_sheets_service(context, credential_name)

            range_notation = f"{sheet_name}!{cell}"
            result = (
                service.spreadsheets()
                .values()
                .get(
                    spreadsheetId=spreadsheet_id,
                    range=range_notation,
                    valueRenderOption="FORMATTED_VALUE",
                )
                .execute()
            )

            values = result.get("values", [[]])
            value = values[0][0] if values and values[0] else None

            self.set_output_value("value", value)
            self.set_output_value(
                "formatted_value", str(value) if value is not None else ""
            )
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "value": value}

        except Exception as e:
            logger.error(f"Sheets get cell error: {e}")
            self.set_output_value("value", None)
            self.set_output_value("formatted_value", "")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class SheetsSetCellNode(BaseNode):
    """Set value in a single cell."""

    # @category: google
    # @requires: none
    # @ports: spreadsheet_id, cell, value, sheet_name -> updated_range, success, error

    NODE_NAME = "Sheets: Set Cell"
    CATEGORY = "google/sheets"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("spreadsheet_id", DataType.STRING, "Spreadsheet ID")
        self.add_input_port("cell", DataType.STRING, "Cell address (e.g., A1)")
        self.add_input_port("value", DataType.ANY, "Value to set")
        self.add_input_port("sheet_name", DataType.STRING, "Sheet name")
        self.add_exec_output()
        self.add_output_port("updated_range", DataType.STRING, "Updated range")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            spreadsheet_id = self.get_input_value(
                "spreadsheet_id"
            ) or self.get_parameter("spreadsheet_id", "")
            cell = self.get_input_value("cell") or self.get_parameter("cell", "A1")
            value = self.get_input_value("value")
            sheet_name = self.get_input_value("sheet_name") or self.get_parameter(
                "sheet_name", "Sheet1"
            )

            if not spreadsheet_id:
                raise ValueError("Spreadsheet ID is required")

            service = await _get_sheets_service(context, credential_name)

            range_notation = f"{sheet_name}!{cell}"
            body = {"values": [[value]]}

            result = (
                service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=spreadsheet_id,
                    range=range_notation,
                    valueInputOption="USER_ENTERED",
                    body=body,
                )
                .execute()
            )

            self.set_output_value("updated_range", result.get("updatedRange", ""))
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "updated_range": result.get("updatedRange")}

        except Exception as e:
            logger.error(f"Sheets set cell error: {e}")
            self.set_output_value("updated_range", "")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class SheetsGetRangeNode(BaseNode):
    """Get values from a range of cells."""

    # @category: google
    # @requires: none
    # @ports: spreadsheet_id, range, sheet_name -> values, row_count, column_count, success, error

    NODE_NAME = "Sheets: Get Range"
    CATEGORY = "google/sheets"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("spreadsheet_id", DataType.STRING, "Spreadsheet ID")
        self.add_input_port("range", DataType.STRING, "Range (e.g., A1:C10)")
        self.add_input_port("sheet_name", DataType.STRING, "Sheet name")
        self.add_exec_output()
        self.add_output_port("values", DataType.LIST, "2D array of values")
        self.add_output_port("row_count", DataType.INTEGER, "Number of rows")
        self.add_output_port("column_count", DataType.INTEGER, "Number of columns")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            spreadsheet_id = self.get_input_value(
                "spreadsheet_id"
            ) or self.get_parameter("spreadsheet_id", "")
            range_addr = self.get_input_value("range") or self.get_parameter(
                "range", "A1:Z100"
            )
            sheet_name = self.get_input_value("sheet_name") or self.get_parameter(
                "sheet_name", "Sheet1"
            )

            if not spreadsheet_id:
                raise ValueError("Spreadsheet ID is required")

            service = await _get_sheets_service(context, credential_name)

            range_notation = f"{sheet_name}!{range_addr}"
            result = (
                service.spreadsheets()
                .values()
                .get(
                    spreadsheetId=spreadsheet_id,
                    range=range_notation,
                    valueRenderOption="FORMATTED_VALUE",
                )
                .execute()
            )

            values = result.get("values", [])
            row_count = len(values)
            column_count = max(len(row) for row in values) if values else 0

            self.set_output_value("values", values)
            self.set_output_value("row_count", row_count)
            self.set_output_value("column_count", column_count)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {
                "success": True,
                "row_count": row_count,
                "column_count": column_count,
            }

        except Exception as e:
            logger.error(f"Sheets get range error: {e}")
            self.set_output_value("values", [])
            self.set_output_value("row_count", 0)
            self.set_output_value("column_count", 0)
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class SheetsWriteRangeNode(BaseNode):
    """Write values to a range of cells."""

    # @category: google
    # @requires: none
    # @ports: spreadsheet_id, range, values, sheet_name -> updated_range, updated_rows, updated_columns, success, error

    NODE_NAME = "Sheets: Write Range"
    CATEGORY = "google/sheets"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("spreadsheet_id", DataType.STRING, "Spreadsheet ID")
        self.add_input_port("range", DataType.STRING, "Starting cell (e.g., A1)")
        self.add_input_port("values", DataType.LIST, "2D array of values")
        self.add_input_port("sheet_name", DataType.STRING, "Sheet name")
        self.add_exec_output()
        self.add_output_port("updated_range", DataType.STRING, "Updated range")
        self.add_output_port("updated_rows", DataType.INTEGER, "Number of rows updated")
        self.add_output_port(
            "updated_columns", DataType.INTEGER, "Number of columns updated"
        )
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            spreadsheet_id = self.get_input_value(
                "spreadsheet_id"
            ) or self.get_parameter("spreadsheet_id", "")
            range_addr = self.get_input_value("range") or self.get_parameter(
                "range", "A1"
            )
            values = self.get_input_value("values") or []
            sheet_name = self.get_input_value("sheet_name") or self.get_parameter(
                "sheet_name", "Sheet1"
            )

            if not spreadsheet_id:
                raise ValueError("Spreadsheet ID is required")
            if not values:
                raise ValueError("Values array is required")

            service = await _get_sheets_service(context, credential_name)

            range_notation = f"{sheet_name}!{range_addr}"
            body = {"values": values}

            result = (
                service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=spreadsheet_id,
                    range=range_notation,
                    valueInputOption="USER_ENTERED",
                    body=body,
                )
                .execute()
            )

            self.set_output_value("updated_range", result.get("updatedRange", ""))
            self.set_output_value("updated_rows", result.get("updatedRows", 0))
            self.set_output_value("updated_columns", result.get("updatedColumns", 0))
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "updated_range": result.get("updatedRange")}

        except Exception as e:
            logger.error(f"Sheets write range error: {e}")
            self.set_output_value("updated_range", "")
            self.set_output_value("updated_rows", 0)
            self.set_output_value("updated_columns", 0)
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class SheetsClearRangeNode(BaseNode):
    """Clear values from a range of cells."""

    # @category: google
    # @requires: none
    # @ports: spreadsheet_id, range, sheet_name -> cleared_range, success, error

    NODE_NAME = "Sheets: Clear Range"
    CATEGORY = "google/sheets"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("spreadsheet_id", DataType.STRING, "Spreadsheet ID")
        self.add_input_port("range", DataType.STRING, "Range to clear (e.g., A1:C10)")
        self.add_input_port("sheet_name", DataType.STRING, "Sheet name")
        self.add_exec_output()
        self.add_output_port("cleared_range", DataType.STRING, "Cleared range")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            spreadsheet_id = self.get_input_value(
                "spreadsheet_id"
            ) or self.get_parameter("spreadsheet_id", "")
            range_addr = self.get_input_value("range") or self.get_parameter(
                "range", "A1:Z100"
            )
            sheet_name = self.get_input_value("sheet_name") or self.get_parameter(
                "sheet_name", "Sheet1"
            )

            if not spreadsheet_id:
                raise ValueError("Spreadsheet ID is required")

            service = await _get_sheets_service(context, credential_name)

            range_notation = f"{sheet_name}!{range_addr}"

            result = (
                service.spreadsheets()
                .values()
                .clear(spreadsheetId=spreadsheet_id, range=range_notation, body={})
                .execute()
            )

            self.set_output_value("cleared_range", result.get("clearedRange", ""))
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "cleared_range": result.get("clearedRange")}

        except Exception as e:
            logger.error(f"Sheets clear range error: {e}")
            self.set_output_value("cleared_range", "")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


# =============================================================================
# Sheet Operations
# =============================================================================


class SheetsCreateSpreadsheetNode(BaseNode):
    """Create a new Google Spreadsheet."""

    # @category: google
    # @requires: none
    # @ports: title, sheet_names -> spreadsheet_id, spreadsheet_url, success, error

    NODE_NAME = "Sheets: Create Spreadsheet"
    CATEGORY = "google/sheets"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("title", DataType.STRING, "Spreadsheet title")
        self.add_input_port("sheet_names", DataType.LIST, "Initial sheet names")
        self.add_exec_output()
        self.add_output_port("spreadsheet_id", DataType.STRING, "New spreadsheet ID")
        self.add_output_port("spreadsheet_url", DataType.STRING, "Spreadsheet URL")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            title = self.get_input_value("title") or self.get_parameter(
                "title", "New Spreadsheet"
            )
            sheet_names = self.get_input_value("sheet_names") or ["Sheet1"]

            service = await _get_sheets_service(context, credential_name)

            sheets = [{"properties": {"title": name}} for name in sheet_names]
            body = {"properties": {"title": title}, "sheets": sheets}

            result = service.spreadsheets().create(body=body).execute()

            spreadsheet_id = result.get("spreadsheetId", "")
            spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"

            self.set_output_value("spreadsheet_id", spreadsheet_id)
            self.set_output_value("spreadsheet_url", spreadsheet_url)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "spreadsheet_id": spreadsheet_id}

        except Exception as e:
            logger.error(f"Sheets create spreadsheet error: {e}")
            self.set_output_value("spreadsheet_id", "")
            self.set_output_value("spreadsheet_url", "")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class SheetsGetSpreadsheetNode(BaseNode):
    """Get spreadsheet metadata."""

    # @category: google
    # @requires: none
    # @ports: spreadsheet_id -> title, sheets, locale, time_zone, success, error

    NODE_NAME = "Sheets: Get Spreadsheet"
    CATEGORY = "google/sheets"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("spreadsheet_id", DataType.STRING, "Spreadsheet ID")
        self.add_exec_output()
        self.add_output_port("title", DataType.STRING, "Spreadsheet title")
        self.add_output_port("sheets", DataType.LIST, "List of sheets")
        self.add_output_port("locale", DataType.STRING, "Locale")
        self.add_output_port("time_zone", DataType.STRING, "Time zone")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            spreadsheet_id = self.get_input_value(
                "spreadsheet_id"
            ) or self.get_parameter("spreadsheet_id", "")

            if not spreadsheet_id:
                raise ValueError("Spreadsheet ID is required")

            service = await _get_sheets_service(context, credential_name)

            result = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

            properties = result.get("properties", {})
            sheets = [
                {
                    "title": s.get("properties", {}).get("title", ""),
                    "sheet_id": s.get("properties", {}).get("sheetId", 0),
                    "index": s.get("properties", {}).get("index", 0),
                }
                for s in result.get("sheets", [])
            ]

            self.set_output_value("title", properties.get("title", ""))
            self.set_output_value("sheets", sheets)
            self.set_output_value("locale", properties.get("locale", ""))
            self.set_output_value("time_zone", properties.get("timeZone", ""))
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "spreadsheet_id": spreadsheet_id}

        except Exception as e:
            logger.error(f"Sheets get spreadsheet error: {e}")
            self.set_output_value("title", "")
            self.set_output_value("sheets", [])
            self.set_output_value("locale", "")
            self.set_output_value("time_zone", "")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class SheetsAddSheetNode(BaseNode):
    """Add a new sheet to a spreadsheet."""

    # @category: google
    # @requires: none
    # @ports: spreadsheet_id, sheet_name -> sheet_id, success, error

    NODE_NAME = "Sheets: Add Sheet"
    CATEGORY = "google/sheets"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("spreadsheet_id", DataType.STRING, "Spreadsheet ID")
        self.add_input_port("sheet_name", DataType.STRING, "New sheet name")
        self.add_exec_output()
        self.add_output_port("sheet_id", DataType.INTEGER, "New sheet ID")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            spreadsheet_id = self.get_input_value(
                "spreadsheet_id"
            ) or self.get_parameter("spreadsheet_id", "")
            sheet_name = self.get_input_value("sheet_name") or self.get_parameter(
                "sheet_name", "New Sheet"
            )

            if not spreadsheet_id:
                raise ValueError("Spreadsheet ID is required")

            service = await _get_sheets_service(context, credential_name)

            body = {"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]}

            result = (
                service.spreadsheets()
                .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
                .execute()
            )

            sheet_id = (
                result.get("replies", [{}])[0]
                .get("addSheet", {})
                .get("properties", {})
                .get("sheetId", 0)
            )

            self.set_output_value("sheet_id", sheet_id)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "sheet_id": sheet_id}

        except Exception as e:
            logger.error(f"Sheets add sheet error: {e}")
            self.set_output_value("sheet_id", 0)
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class SheetsDeleteSheetNode(BaseNode):
    """Delete a sheet from a spreadsheet."""

    # @category: google
    # @requires: none
    # @ports: spreadsheet_id, sheet_id -> success, error

    NODE_NAME = "Sheets: Delete Sheet"
    CATEGORY = "google/sheets"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("spreadsheet_id", DataType.STRING, "Spreadsheet ID")
        self.add_input_port("sheet_id", DataType.INTEGER, "Sheet ID to delete")
        self.add_exec_output()
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            spreadsheet_id = self.get_input_value(
                "spreadsheet_id"
            ) or self.get_parameter("spreadsheet_id", "")
            sheet_id = self.get_input_value("sheet_id")
            if sheet_id is None:
                sheet_id = self.get_parameter("sheet_id", 0)

            if not spreadsheet_id:
                raise ValueError("Spreadsheet ID is required")

            service = await _get_sheets_service(context, credential_name)

            body = {"requests": [{"deleteSheet": {"sheetId": sheet_id}}]}

            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body
            ).execute()

            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True}

        except Exception as e:
            logger.error(f"Sheets delete sheet error: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class SheetsDuplicateSheetNode(BaseNode):
    """Duplicate a sheet within a spreadsheet."""

    # @category: google
    # @requires: none
    # @ports: spreadsheet_id, sheet_id, new_sheet_name -> new_sheet_id, success, error

    NODE_NAME = "Sheets: Duplicate Sheet"
    CATEGORY = "google/sheets"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("spreadsheet_id", DataType.STRING, "Spreadsheet ID")
        self.add_input_port("sheet_id", DataType.INTEGER, "Source sheet ID")
        self.add_input_port("new_sheet_name", DataType.STRING, "New sheet name")
        self.add_exec_output()
        self.add_output_port("new_sheet_id", DataType.INTEGER, "New sheet ID")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            spreadsheet_id = self.get_input_value(
                "spreadsheet_id"
            ) or self.get_parameter("spreadsheet_id", "")
            sheet_id = self.get_input_value("sheet_id")
            if sheet_id is None:
                sheet_id = self.get_parameter("sheet_id", 0)
            new_sheet_name = self.get_input_value(
                "new_sheet_name"
            ) or self.get_parameter("new_sheet_name", "Copy")

            if not spreadsheet_id:
                raise ValueError("Spreadsheet ID is required")

            service = await _get_sheets_service(context, credential_name)

            body = {
                "requests": [
                    {
                        "duplicateSheet": {
                            "sourceSheetId": sheet_id,
                            "newSheetName": new_sheet_name,
                        }
                    }
                ]
            }

            result = (
                service.spreadsheets()
                .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
                .execute()
            )

            new_sheet_id = (
                result.get("replies", [{}])[0]
                .get("duplicateSheet", {})
                .get("properties", {})
                .get("sheetId", 0)
            )

            self.set_output_value("new_sheet_id", new_sheet_id)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "new_sheet_id": new_sheet_id}

        except Exception as e:
            logger.error(f"Sheets duplicate sheet error: {e}")
            self.set_output_value("new_sheet_id", 0)
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class SheetsRenameSheetNode(BaseNode):
    """Rename a sheet in a spreadsheet."""

    # @category: google
    # @requires: none
    # @ports: spreadsheet_id, sheet_id, new_name -> success, error

    NODE_NAME = "Sheets: Rename Sheet"
    CATEGORY = "google/sheets"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("spreadsheet_id", DataType.STRING, "Spreadsheet ID")
        self.add_input_port("sheet_id", DataType.INTEGER, "Sheet ID")
        self.add_input_port("new_name", DataType.STRING, "New sheet name")
        self.add_exec_output()
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            spreadsheet_id = self.get_input_value(
                "spreadsheet_id"
            ) or self.get_parameter("spreadsheet_id", "")
            sheet_id = self.get_input_value("sheet_id")
            if sheet_id is None:
                sheet_id = self.get_parameter("sheet_id", 0)
            new_name = self.get_input_value("new_name") or self.get_parameter(
                "new_name", "Renamed"
            )

            if not spreadsheet_id:
                raise ValueError("Spreadsheet ID is required")

            service = await _get_sheets_service(context, credential_name)

            body = {
                "requests": [
                    {
                        "updateSheetProperties": {
                            "properties": {"sheetId": sheet_id, "title": new_name},
                            "fields": "title",
                        }
                    }
                ]
            }

            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body
            ).execute()

            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True}

        except Exception as e:
            logger.error(f"Sheets rename sheet error: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


# =============================================================================
# Row/Column Operations
# =============================================================================


class SheetsAppendRowNode(BaseNode):
    """Append a row to a sheet."""

    # @category: google
    # @requires: none
    # @ports: spreadsheet_id, values, sheet_name -> updated_range, success, error

    NODE_NAME = "Sheets: Append Row"
    CATEGORY = "google/sheets"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("spreadsheet_id", DataType.STRING, "Spreadsheet ID")
        self.add_input_port("values", DataType.LIST, "Row values")
        self.add_input_port("sheet_name", DataType.STRING, "Sheet name")
        self.add_exec_output()
        self.add_output_port("updated_range", DataType.STRING, "Updated range")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            spreadsheet_id = self.get_input_value(
                "spreadsheet_id"
            ) or self.get_parameter("spreadsheet_id", "")
            values = self.get_input_value("values") or []
            sheet_name = self.get_input_value("sheet_name") or self.get_parameter(
                "sheet_name", "Sheet1"
            )

            if not spreadsheet_id:
                raise ValueError("Spreadsheet ID is required")

            service = await _get_sheets_service(context, credential_name)

            range_notation = f"{sheet_name}!A1"
            body = {"values": [values]}

            result = (
                service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=spreadsheet_id,
                    range=range_notation,
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                    body=body,
                )
                .execute()
            )

            self.set_output_value(
                "updated_range", result.get("updates", {}).get("updatedRange", "")
            )
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True}

        except Exception as e:
            logger.error(f"Sheets append row error: {e}")
            self.set_output_value("updated_range", "")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class SheetsInsertRowNode(BaseNode):
    """Insert a row at a specific position."""

    # @category: google
    # @requires: none
    # @ports: spreadsheet_id, sheet_id, row_index, num_rows -> success, error

    NODE_NAME = "Sheets: Insert Row"
    CATEGORY = "google/sheets"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("spreadsheet_id", DataType.STRING, "Spreadsheet ID")
        self.add_input_port("sheet_id", DataType.INTEGER, "Sheet ID")
        self.add_input_port("row_index", DataType.INTEGER, "Row index (0-based)")
        self.add_input_port("num_rows", DataType.INTEGER, "Number of rows to insert")
        self.add_exec_output()
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            spreadsheet_id = self.get_input_value(
                "spreadsheet_id"
            ) or self.get_parameter("spreadsheet_id", "")
            sheet_id = self.get_input_value("sheet_id")
            if sheet_id is None:
                sheet_id = self.get_parameter("sheet_id", 0)
            row_index = self.get_input_value("row_index")
            if row_index is None:
                row_index = self.get_parameter("row_index", 0)
            num_rows = self.get_input_value("num_rows")
            if num_rows is None:
                num_rows = self.get_parameter("num_rows", 1)

            if not spreadsheet_id:
                raise ValueError("Spreadsheet ID is required")

            service = await _get_sheets_service(context, credential_name)

            body = {
                "requests": [
                    {
                        "insertDimension": {
                            "range": {
                                "sheetId": sheet_id,
                                "dimension": "ROWS",
                                "startIndex": row_index,
                                "endIndex": row_index + num_rows,
                            },
                            "inheritFromBefore": False,
                        }
                    }
                ]
            }

            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body
            ).execute()

            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True}

        except Exception as e:
            logger.error(f"Sheets insert row error: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class SheetsDeleteRowNode(BaseNode):
    """Delete rows from a sheet."""

    # @category: google
    # @requires: none
    # @ports: spreadsheet_id, sheet_id, start_row, num_rows -> success, error

    NODE_NAME = "Sheets: Delete Row"
    CATEGORY = "google/sheets"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("spreadsheet_id", DataType.STRING, "Spreadsheet ID")
        self.add_input_port("sheet_id", DataType.INTEGER, "Sheet ID")
        self.add_input_port("start_row", DataType.INTEGER, "Start row index (0-based)")
        self.add_input_port("num_rows", DataType.INTEGER, "Number of rows to delete")
        self.add_exec_output()
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            spreadsheet_id = self.get_input_value(
                "spreadsheet_id"
            ) or self.get_parameter("spreadsheet_id", "")
            sheet_id = self.get_input_value("sheet_id")
            if sheet_id is None:
                sheet_id = self.get_parameter("sheet_id", 0)
            start_row = self.get_input_value("start_row")
            if start_row is None:
                start_row = self.get_parameter("start_row", 0)
            num_rows = self.get_input_value("num_rows")
            if num_rows is None:
                num_rows = self.get_parameter("num_rows", 1)

            if not spreadsheet_id:
                raise ValueError("Spreadsheet ID is required")

            service = await _get_sheets_service(context, credential_name)

            body = {
                "requests": [
                    {
                        "deleteDimension": {
                            "range": {
                                "sheetId": sheet_id,
                                "dimension": "ROWS",
                                "startIndex": start_row,
                                "endIndex": start_row + num_rows,
                            }
                        }
                    }
                ]
            }

            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body
            ).execute()

            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True}

        except Exception as e:
            logger.error(f"Sheets delete row error: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class SheetsInsertColumnNode(BaseNode):
    """Insert columns at a specific position."""

    # @category: google
    # @requires: none
    # @ports: spreadsheet_id, sheet_id, column_index, num_columns -> success, error

    NODE_NAME = "Sheets: Insert Column"
    CATEGORY = "google/sheets"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("spreadsheet_id", DataType.STRING, "Spreadsheet ID")
        self.add_input_port("sheet_id", DataType.INTEGER, "Sheet ID")
        self.add_input_port("column_index", DataType.INTEGER, "Column index (0-based)")
        self.add_input_port(
            "num_columns", DataType.INTEGER, "Number of columns to insert"
        )
        self.add_exec_output()
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            spreadsheet_id = self.get_input_value(
                "spreadsheet_id"
            ) or self.get_parameter("spreadsheet_id", "")
            sheet_id = self.get_input_value("sheet_id")
            if sheet_id is None:
                sheet_id = self.get_parameter("sheet_id", 0)
            column_index = self.get_input_value("column_index")
            if column_index is None:
                column_index = self.get_parameter("column_index", 0)
            num_columns = self.get_input_value("num_columns")
            if num_columns is None:
                num_columns = self.get_parameter("num_columns", 1)

            if not spreadsheet_id:
                raise ValueError("Spreadsheet ID is required")

            service = await _get_sheets_service(context, credential_name)

            body = {
                "requests": [
                    {
                        "insertDimension": {
                            "range": {
                                "sheetId": sheet_id,
                                "dimension": "COLUMNS",
                                "startIndex": column_index,
                                "endIndex": column_index + num_columns,
                            },
                            "inheritFromBefore": False,
                        }
                    }
                ]
            }

            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body
            ).execute()

            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True}

        except Exception as e:
            logger.error(f"Sheets insert column error: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class SheetsDeleteColumnNode(BaseNode):
    """Delete columns from a sheet."""

    # @category: google
    # @requires: none
    # @ports: spreadsheet_id, sheet_id, start_column, num_columns -> success, error

    NODE_NAME = "Sheets: Delete Column"
    CATEGORY = "google/sheets"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("spreadsheet_id", DataType.STRING, "Spreadsheet ID")
        self.add_input_port("sheet_id", DataType.INTEGER, "Sheet ID")
        self.add_input_port(
            "start_column", DataType.INTEGER, "Start column index (0-based)"
        )
        self.add_input_port(
            "num_columns", DataType.INTEGER, "Number of columns to delete"
        )
        self.add_exec_output()
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            spreadsheet_id = self.get_input_value(
                "spreadsheet_id"
            ) or self.get_parameter("spreadsheet_id", "")
            sheet_id = self.get_input_value("sheet_id")
            if sheet_id is None:
                sheet_id = self.get_parameter("sheet_id", 0)
            start_column = self.get_input_value("start_column")
            if start_column is None:
                start_column = self.get_parameter("start_column", 0)
            num_columns = self.get_input_value("num_columns")
            if num_columns is None:
                num_columns = self.get_parameter("num_columns", 1)

            if not spreadsheet_id:
                raise ValueError("Spreadsheet ID is required")

            service = await _get_sheets_service(context, credential_name)

            body = {
                "requests": [
                    {
                        "deleteDimension": {
                            "range": {
                                "sheetId": sheet_id,
                                "dimension": "COLUMNS",
                                "startIndex": start_column,
                                "endIndex": start_column + num_columns,
                            }
                        }
                    }
                ]
            }

            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body
            ).execute()

            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True}

        except Exception as e:
            logger.error(f"Sheets delete column error: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


# =============================================================================
# Format Operations
# =============================================================================


class SheetsFormatCellsNode(BaseNode):
    """Format cells in a range."""

    # @category: google
    # @requires: none
    # @ports: spreadsheet_id, sheet_id, start_row, end_row, start_column, end_column -> success, error

    NODE_NAME = "Sheets: Format Cells"
    CATEGORY = "google/sheets"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("spreadsheet_id", DataType.STRING, "Spreadsheet ID")
        self.add_input_port("sheet_id", DataType.INTEGER, "Sheet ID")
        self.add_input_port("start_row", DataType.INTEGER, "Start row index")
        self.add_input_port("end_row", DataType.INTEGER, "End row index")
        self.add_input_port("start_column", DataType.INTEGER, "Start column index")
        self.add_input_port("end_column", DataType.INTEGER, "End column index")
        self.add_exec_output()
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            spreadsheet_id = self.get_input_value(
                "spreadsheet_id"
            ) or self.get_parameter("spreadsheet_id", "")
            sheet_id = self.get_input_value("sheet_id") or self.get_parameter(
                "sheet_id", 0
            )
            start_row = self.get_input_value("start_row") or 0
            end_row = self.get_input_value("end_row") or 1
            start_column = self.get_input_value("start_column") or 0
            end_column = self.get_input_value("end_column") or 1

            bold = self.get_parameter("bold", False)
            italic = self.get_parameter("italic", False)
            font_size = self.get_parameter("font_size", 10)
            bg_color = self.get_parameter("background_color", "")
            text_color = self.get_parameter("text_color", "")

            if not spreadsheet_id:
                raise ValueError("Spreadsheet ID is required")

            service = await _get_sheets_service(context, credential_name)

            cell_format: Dict[str, Any] = {
                "textFormat": {"bold": bold, "italic": italic, "fontSize": font_size}
            }

            if bg_color:
                parts = bg_color.split(",")
                if len(parts) == 3:
                    cell_format["backgroundColor"] = {
                        "red": float(parts[0]) / 255,
                        "green": float(parts[1]) / 255,
                        "blue": float(parts[2]) / 255,
                    }

            if text_color:
                parts = text_color.split(",")
                if len(parts) == 3:
                    cell_format["textFormat"]["foregroundColor"] = {
                        "red": float(parts[0]) / 255,
                        "green": float(parts[1]) / 255,
                        "blue": float(parts[2]) / 255,
                    }

            body = {
                "requests": [
                    {
                        "repeatCell": {
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": start_row,
                                "endRowIndex": end_row,
                                "startColumnIndex": start_column,
                                "endColumnIndex": end_column,
                            },
                            "cell": {"userEnteredFormat": cell_format},
                            "fields": "userEnteredFormat(backgroundColor,textFormat)",
                        }
                    }
                ]
            }

            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body
            ).execute()

            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True}

        except Exception as e:
            logger.error(f"Sheets format cells error: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class SheetsAutoResizeNode(BaseNode):
    """Auto-resize columns to fit content."""

    # @category: google
    # @requires: none
    # @ports: spreadsheet_id, sheet_id, start_index, end_index -> success, error

    NODE_NAME = "Sheets: Auto Resize"
    CATEGORY = "google/sheets"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("spreadsheet_id", DataType.STRING, "Spreadsheet ID")
        self.add_input_port("sheet_id", DataType.INTEGER, "Sheet ID")
        self.add_input_port("start_index", DataType.INTEGER, "Start column index")
        self.add_input_port("end_index", DataType.INTEGER, "End column index")
        self.add_exec_output()
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            spreadsheet_id = self.get_input_value(
                "spreadsheet_id"
            ) or self.get_parameter("spreadsheet_id", "")
            sheet_id = self.get_input_value("sheet_id") or self.get_parameter(
                "sheet_id", 0
            )
            start_index = self.get_input_value("start_index") or 0
            end_index = self.get_input_value("end_index") or 26
            dimension = self.get_parameter("dimension", "COLUMNS")

            if not spreadsheet_id:
                raise ValueError("Spreadsheet ID is required")

            service = await _get_sheets_service(context, credential_name)

            body = {
                "requests": [
                    {
                        "autoResizeDimensions": {
                            "dimensions": {
                                "sheetId": sheet_id,
                                "dimension": dimension,
                                "startIndex": start_index,
                                "endIndex": end_index,
                            }
                        }
                    }
                ]
            }

            service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body
            ).execute()

            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True}

        except Exception as e:
            logger.error(f"Sheets auto resize error: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


# =============================================================================
# Batch Operations
# =============================================================================


class SheetsBatchUpdateNode(BaseNode):
    """Execute multiple updates in a single batch."""

    # @category: google
    # @requires: none
    # @ports: spreadsheet_id, data -> total_updated_rows, total_updated_columns, total_updated_cells, success, error

    NODE_NAME = "Sheets: Batch Update"
    CATEGORY = "google/sheets"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("spreadsheet_id", DataType.STRING, "Spreadsheet ID")
        self.add_input_port("data", DataType.LIST, "Array of {range, values} objects")
        self.add_exec_output()
        self.add_output_port(
            "total_updated_rows", DataType.INTEGER, "Total rows updated"
        )
        self.add_output_port(
            "total_updated_columns", DataType.INTEGER, "Total columns updated"
        )
        self.add_output_port(
            "total_updated_cells", DataType.INTEGER, "Total cells updated"
        )
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            spreadsheet_id = self.get_input_value(
                "spreadsheet_id"
            ) or self.get_parameter("spreadsheet_id", "")
            data = self.get_input_value("data") or []

            if not spreadsheet_id:
                raise ValueError("Spreadsheet ID is required")
            if not data:
                raise ValueError("Data array is required")

            service = await _get_sheets_service(context, credential_name)

            body = {
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {"range": item.get("range", "A1"), "values": item.get("values", [])}
                    for item in data
                ],
            }

            result = (
                service.spreadsheets()
                .values()
                .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
                .execute()
            )

            self.set_output_value(
                "total_updated_rows", result.get("totalUpdatedRows", 0)
            )
            self.set_output_value(
                "total_updated_columns", result.get("totalUpdatedColumns", 0)
            )
            self.set_output_value(
                "total_updated_cells", result.get("totalUpdatedCells", 0)
            )
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True}

        except Exception as e:
            logger.error(f"Sheets batch update error: {e}")
            self.set_output_value("total_updated_rows", 0)
            self.set_output_value("total_updated_columns", 0)
            self.set_output_value("total_updated_cells", 0)
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class SheetsBatchGetNode(BaseNode):
    """Get values from multiple ranges in a single batch."""

    # @category: google
    # @requires: none
    # @ports: spreadsheet_id, ranges -> value_ranges, success, error

    NODE_NAME = "Sheets: Batch Get"
    CATEGORY = "google/sheets"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("spreadsheet_id", DataType.STRING, "Spreadsheet ID")
        self.add_input_port("ranges", DataType.LIST, "Array of range strings")
        self.add_exec_output()
        self.add_output_port("value_ranges", DataType.LIST, "Array of value ranges")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            spreadsheet_id = self.get_input_value(
                "spreadsheet_id"
            ) or self.get_parameter("spreadsheet_id", "")
            ranges = self.get_input_value("ranges") or []

            if not spreadsheet_id:
                raise ValueError("Spreadsheet ID is required")
            if not ranges:
                raise ValueError("Ranges array is required")

            service = await _get_sheets_service(context, credential_name)

            result = (
                service.spreadsheets()
                .values()
                .batchGet(
                    spreadsheetId=spreadsheet_id,
                    ranges=ranges,
                    valueRenderOption="FORMATTED_VALUE",
                )
                .execute()
            )

            value_ranges = [
                {"range": vr.get("range", ""), "values": vr.get("values", [])}
                for vr in result.get("valueRanges", [])
            ]

            self.set_output_value("value_ranges", value_ranges)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True}

        except Exception as e:
            logger.error(f"Sheets batch get error: {e}")
            self.set_output_value("value_ranges", [])
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class SheetsBatchClearNode(BaseNode):
    """Clear multiple ranges in a single batch."""

    # @category: google
    # @requires: none
    # @ports: spreadsheet_id, ranges -> cleared_ranges, success, error

    NODE_NAME = "Sheets: Batch Clear"
    CATEGORY = "google/sheets"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("spreadsheet_id", DataType.STRING, "Spreadsheet ID")
        self.add_input_port("ranges", DataType.LIST, "Array of range strings")
        self.add_exec_output()
        self.add_output_port("cleared_ranges", DataType.LIST, "Cleared ranges")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            spreadsheet_id = self.get_input_value(
                "spreadsheet_id"
            ) or self.get_parameter("spreadsheet_id", "")
            ranges = self.get_input_value("ranges") or []

            if not spreadsheet_id:
                raise ValueError("Spreadsheet ID is required")
            if not ranges:
                raise ValueError("Ranges array is required")

            service = await _get_sheets_service(context, credential_name)

            result = (
                service.spreadsheets()
                .values()
                .batchClear(spreadsheetId=spreadsheet_id, body={"ranges": ranges})
                .execute()
            )

            self.set_output_value("cleared_ranges", result.get("clearedRanges", []))
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True}

        except Exception as e:
            logger.error(f"Sheets batch clear error: {e}")
            self.set_output_value("cleared_ranges", [])
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}
