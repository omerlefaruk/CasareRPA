"""
CasareRPA - Google Sheets Trigger Node

Trigger node that monitors Google Sheets for changes.
Workflow starts when cells are modified in the monitored range.
"""

from typing import Any

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.trigger_nodes.base_trigger_node import BaseTriggerNode
from casare_rpa.triggers.base import TriggerType


@properties(
    # Connection settings
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        placeholder="google",
        tooltip="Name of stored Google OAuth credential",
        tab="connection",
    ),
    # Spreadsheet settings
    PropertyDef(
        "spreadsheet_id",
        PropertyType.STRING,
        default="",
        required=True,
        label="Spreadsheet ID",
        placeholder="1ABC123xyz...",
        tooltip="Google Sheets spreadsheet ID to monitor",
    ),
    PropertyDef(
        "sheet_name",
        PropertyType.STRING,
        default="Sheet1",
        label="Sheet Name",
        placeholder="Sheet1",
        tooltip="Name of the sheet to monitor",
    ),
    PropertyDef(
        "range",
        PropertyType.STRING,
        default="",
        label="Range",
        placeholder="A1:Z1000",
        tooltip="Cell range to monitor (empty = entire sheet)",
    ),
    # Polling settings
    PropertyDef(
        "polling_interval",
        PropertyType.INTEGER,
        default=30,
        label="Polling Interval (sec)",
        tooltip="Seconds between checks for changes",
    ),
    # Event types
    PropertyDef(
        "trigger_on_new_row",
        PropertyType.BOOLEAN,
        default=True,
        label="Trigger on New Row",
        tooltip="Trigger when a new row is added",
    ),
    PropertyDef(
        "trigger_on_cell_change",
        PropertyType.BOOLEAN,
        default=True,
        label="Trigger on Cell Change",
        tooltip="Trigger when cell values change",
    ),
    PropertyDef(
        "trigger_on_delete",
        PropertyType.BOOLEAN,
        default=False,
        label="Trigger on Delete",
        tooltip="Trigger when rows are deleted",
        tab="advanced",
    ),
    # Filtering
    PropertyDef(
        "watch_columns",
        PropertyType.STRING,
        default="",
        label="Watch Columns",
        placeholder="A,B,C",
        tooltip="Comma-separated columns to watch (empty = all)",
    ),
    PropertyDef(
        "ignore_empty_rows",
        PropertyType.BOOLEAN,
        default=True,
        label="Ignore Empty Rows",
        tooltip="Don't trigger on completely empty rows",
        tab="advanced",
    ),
)
@node(category="triggers", exec_inputs=[])
class SheetsTriggerNode(BaseTriggerNode):
    """
    Google Sheets trigger node that monitors for spreadsheet changes.

    Polls Sheets API to detect changes in monitored range.
    Requires Google OAuth credentials with Sheets scope.

    Outputs:
    - spreadsheet_id: ID of the spreadsheet
    - sheet_name: Name of the modified sheet
    - event_type: Type of change (new_row, cell_change, delete)
    - row_number: Row number of the change
    - column: Column letter of the change
    - old_value: Previous cell value (for changes)
    - new_value: New cell value
    - row_data: Full row data as list
    - row_dict: Row data as dict (using header row as keys)
    - changed_cells: List of changed cell references
    - timestamp: When the change was detected
    - raw_data: Full change data
    """

    # @category: trigger
    # @requires: none
    # @ports: none -> none

    trigger_display_name = "Google Sheets"
    trigger_description = "Trigger workflow when Google Sheets data changes"
    trigger_icon = "sheets"
    trigger_category = "triggers"

    def __init__(self, node_id: str, config: dict | None = None) -> None:
        super().__init__(node_id, config)
        self.name = "Sheets Trigger"
        self.node_type = "SheetsTriggerNode"

    def _define_payload_ports(self) -> None:
        """Define Sheets-specific output ports."""
        self.add_output_port("spreadsheet_id", DataType.STRING, "Spreadsheet ID")
        self.add_output_port("sheet_name", DataType.STRING, "Sheet Name")
        self.add_output_port("event_type", DataType.STRING, "Event Type")
        self.add_output_port("row_number", DataType.INTEGER, "Row Number")
        self.add_output_port("column", DataType.STRING, "Column")
        self.add_output_port("old_value", DataType.ANY, "Old Value")
        self.add_output_port("new_value", DataType.ANY, "New Value")
        self.add_output_port("row_data", DataType.LIST, "Row Data (List)")
        self.add_output_port("row_dict", DataType.DICT, "Row Data (Dict)")
        self.add_output_port("changed_cells", DataType.LIST, "Changed Cells")
        self.add_output_port("timestamp", DataType.STRING, "Timestamp")
        self.add_output_port("raw_data", DataType.DICT, "Raw Data")

    def get_trigger_type(self) -> TriggerType:
        return TriggerType.SHEETS

    def get_trigger_config(self) -> dict[str, Any]:
        """Get Sheets-specific configuration."""
        # Parse comma-separated columns
        watch_columns_str = self.get_parameter("watch_columns", "")
        watch_columns = [c.strip().upper() for c in watch_columns_str.split(",") if c.strip()]

        return {
            "credential_name": self.get_parameter("credential_name", "google"),
            "spreadsheet_id": self.get_parameter("spreadsheet_id", ""),
            "sheet_name": self.get_parameter("sheet_name", "Sheet1"),
            "range": self.get_parameter("range", ""),
            "polling_interval": self.get_parameter("polling_interval", 30),
            "trigger_on_new_row": self.get_parameter("trigger_on_new_row", True),
            "trigger_on_cell_change": self.get_parameter("trigger_on_cell_change", True),
            "trigger_on_delete": self.get_parameter("trigger_on_delete", False),
            "watch_columns": watch_columns,
            "ignore_empty_rows": self.get_parameter("ignore_empty_rows", True),
        }
