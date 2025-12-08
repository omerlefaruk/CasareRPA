"""Visual nodes for Google Sheets operations.

All nodes use cascading credential pickers:
1. NodeGoogleCredentialWidget - Google account selection
2. NodeGoogleSpreadsheetWidget - Spreadsheet selection (cascades from credential)
3. NodeGoogleSheetWidget - Sheet tab selection (cascades from spreadsheet)
"""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.presentation.canvas.graph.node_widgets import (
    NodeGoogleCredentialWidget,
    NodeGoogleSpreadsheetWidget,
    NodeGoogleSheetWidget,
)

# Google Sheets API scopes
SHEETS_READONLY_SCOPE = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SHEETS_FULL_SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]


class VisualGoogleSheetsBaseNode(VisualNode):
    """Base class for Google Sheets visual nodes with credential picker integration."""

    # Subclasses should set this to SHEETS_READONLY_SCOPE or SHEETS_FULL_SCOPE
    REQUIRED_SCOPES = SHEETS_FULL_SCOPE

    def __init__(self, qgraphics_item=None) -> None:
        super().__init__(qgraphics_item)

    def setup_widgets(self) -> None:
        """Setup credential and spreadsheet picker widgets."""
        # Credential picker
        self._cred_widget = NodeGoogleCredentialWidget(
            name="credential_id",
            label="Google Account",
            scopes=self.REQUIRED_SCOPES,
        )
        if self._cred_widget:
            self.add_custom_widget(self._cred_widget)
            self._cred_widget.setParentItem(self.view)

        # Spreadsheet picker (cascading from credential)
        self._spreadsheet_widget = NodeGoogleSpreadsheetWidget(
            name="spreadsheet_id",
            label="Spreadsheet",
            credential_widget=self._cred_widget,
        )
        if self._spreadsheet_widget:
            self.add_custom_widget(self._spreadsheet_widget)
            self._spreadsheet_widget.setParentItem(self.view)

    def setup_sheet_widget(self) -> None:
        """Setup sheet picker widget (call from subclass if needed)."""
        self._sheet_widget = NodeGoogleSheetWidget(
            name="sheet_name",
            label="Sheet",
            spreadsheet_widget=self._spreadsheet_widget,
            credential_widget=self._cred_widget,
        )
        if self._sheet_widget:
            self.add_custom_widget(self._sheet_widget)
            self._sheet_widget.setParentItem(self.view)


# =============================================================================
# Cell Operations
# =============================================================================


class VisualSheetsGetCellNode(VisualGoogleSheetsBaseNode):
    """Visual representation of SheetsGetCellNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Get Cell"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsGetCellNode"
    REQUIRED_SCOPES = SHEETS_READONLY_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("cell", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("value", DataType.ANY)
        self.add_typed_output("formatted_value", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_sheet_widget()


class VisualSheetsSetCellNode(VisualGoogleSheetsBaseNode):
    """Visual representation of SheetsSetCellNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Set Cell"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsSetCellNode"
    REQUIRED_SCOPES = SHEETS_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("cell", DataType.STRING)
        self.add_typed_input("value", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("updated_range", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_sheet_widget()


class VisualSheetsGetRangeNode(VisualGoogleSheetsBaseNode):
    """Visual representation of SheetsGetRangeNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Get Range"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsGetRangeNode"
    REQUIRED_SCOPES = SHEETS_READONLY_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("range", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("values", DataType.LIST)
        self.add_typed_output("row_count", DataType.INTEGER)
        self.add_typed_output("column_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_sheet_widget()


class VisualSheetsWriteRangeNode(VisualGoogleSheetsBaseNode):
    """Visual representation of SheetsWriteRangeNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Write Range"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsWriteRangeNode"
    REQUIRED_SCOPES = SHEETS_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("range", DataType.STRING)
        self.add_typed_input("values", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("updated_range", DataType.STRING)
        self.add_typed_output("updated_rows", DataType.INTEGER)
        self.add_typed_output("updated_columns", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_sheet_widget()


class VisualSheetsClearRangeNode(VisualGoogleSheetsBaseNode):
    """Visual representation of SheetsClearRangeNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Clear Range"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsClearRangeNode"
    REQUIRED_SCOPES = SHEETS_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("range", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("cleared_range", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_sheet_widget()


# =============================================================================
# Sheet Operations
# =============================================================================


class VisualSheetsCreateSpreadsheetNode(VisualNode):
    """Visual representation of SheetsCreateSpreadsheetNode.

    This node creates a new spreadsheet, so only needs credential picker.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Create Spreadsheet"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsCreateSpreadsheetNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("title", DataType.STRING)
        self.add_typed_input("sheet_names", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("spreadsheet_id", DataType.STRING)
        self.add_typed_output("spreadsheet_url", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        self._cred_widget = NodeGoogleCredentialWidget(
            name="credential_id",
            label="Google Account",
            scopes=SHEETS_FULL_SCOPE,
        )
        if self._cred_widget:
            self.add_custom_widget(self._cred_widget)
            self._cred_widget.setParentItem(self.view)


class VisualSheetsGetSpreadsheetNode(VisualGoogleSheetsBaseNode):
    """Visual representation of SheetsGetSpreadsheetNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Get Spreadsheet"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsGetSpreadsheetNode"
    REQUIRED_SCOPES = SHEETS_READONLY_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("title", DataType.STRING)
        self.add_typed_output("sheets", DataType.LIST)
        self.add_typed_output("locale", DataType.STRING)
        self.add_typed_output("time_zone", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsAddSheetNode(VisualGoogleSheetsBaseNode):
    """Visual representation of SheetsAddSheetNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Add Sheet"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsAddSheetNode"
    REQUIRED_SCOPES = SHEETS_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("sheet_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("sheet_id", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsDeleteSheetNode(VisualGoogleSheetsBaseNode):
    """Visual representation of SheetsDeleteSheetNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Delete Sheet"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsDeleteSheetNode"
    REQUIRED_SCOPES = SHEETS_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("sheet_id", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_sheet_widget()


class VisualSheetsDuplicateSheetNode(VisualGoogleSheetsBaseNode):
    """Visual representation of SheetsDuplicateSheetNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Duplicate Sheet"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsDuplicateSheetNode"
    REQUIRED_SCOPES = SHEETS_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("sheet_id", DataType.INTEGER)
        self.add_typed_input("new_sheet_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("new_sheet_id", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_sheet_widget()


class VisualSheetsRenameSheetNode(VisualGoogleSheetsBaseNode):
    """Visual representation of SheetsRenameSheetNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Rename Sheet"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsRenameSheetNode"
    REQUIRED_SCOPES = SHEETS_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("sheet_id", DataType.INTEGER)
        self.add_typed_input("new_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_sheet_widget()


# =============================================================================
# Row/Column Operations
# =============================================================================


class VisualSheetsAppendRowNode(VisualGoogleSheetsBaseNode):
    """Visual representation of SheetsAppendRowNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Append Row"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsAppendRowNode"
    REQUIRED_SCOPES = SHEETS_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("values", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("updated_range", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_sheet_widget()


class VisualSheetsInsertRowNode(VisualGoogleSheetsBaseNode):
    """Visual representation of SheetsInsertRowNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Insert Row"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsInsertRowNode"
    REQUIRED_SCOPES = SHEETS_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("sheet_id", DataType.INTEGER)
        self.add_typed_input("row_index", DataType.INTEGER)
        self.add_typed_input("num_rows", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_sheet_widget()


class VisualSheetsDeleteRowNode(VisualGoogleSheetsBaseNode):
    """Visual representation of SheetsDeleteRowNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Delete Row"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsDeleteRowNode"
    REQUIRED_SCOPES = SHEETS_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("sheet_id", DataType.INTEGER)
        self.add_typed_input("start_row", DataType.INTEGER)
        self.add_typed_input("num_rows", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_sheet_widget()


class VisualSheetsInsertColumnNode(VisualGoogleSheetsBaseNode):
    """Visual representation of SheetsInsertColumnNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Insert Column"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsInsertColumnNode"
    REQUIRED_SCOPES = SHEETS_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("sheet_id", DataType.INTEGER)
        self.add_typed_input("column_index", DataType.INTEGER)
        self.add_typed_input("num_columns", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_sheet_widget()


class VisualSheetsDeleteColumnNode(VisualGoogleSheetsBaseNode):
    """Visual representation of SheetsDeleteColumnNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Delete Column"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsDeleteColumnNode"
    REQUIRED_SCOPES = SHEETS_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("sheet_id", DataType.INTEGER)
        self.add_typed_input("start_column", DataType.INTEGER)
        self.add_typed_input("num_columns", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_sheet_widget()


# =============================================================================
# Format Operations
# =============================================================================


class VisualSheetsFormatCellsNode(VisualGoogleSheetsBaseNode):
    """Visual representation of SheetsFormatCellsNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Format Cells"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsFormatCellsNode"
    REQUIRED_SCOPES = SHEETS_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("sheet_id", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_sheet_widget()


class VisualSheetsAutoResizeNode(VisualGoogleSheetsBaseNode):
    """Visual representation of SheetsAutoResizeNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Auto Resize"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsAutoResizeNode"
    REQUIRED_SCOPES = SHEETS_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("sheet_id", DataType.INTEGER)
        self.add_typed_input("start_index", DataType.INTEGER)
        self.add_typed_input("end_index", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_sheet_widget()


# =============================================================================
# Batch Operations
# =============================================================================


class VisualSheetsBatchUpdateNode(VisualGoogleSheetsBaseNode):
    """Visual representation of SheetsBatchUpdateNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Batch Update"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsBatchUpdateNode"
    REQUIRED_SCOPES = SHEETS_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("data", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("total_updated_rows", DataType.INTEGER)
        self.add_typed_output("total_updated_columns", DataType.INTEGER)
        self.add_typed_output("total_updated_cells", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsBatchGetNode(VisualGoogleSheetsBaseNode):
    """Visual representation of SheetsBatchGetNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Batch Get"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsBatchGetNode"
    REQUIRED_SCOPES = SHEETS_READONLY_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("ranges", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("value_ranges", DataType.LIST)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsBatchClearNode(VisualGoogleSheetsBaseNode):
    """Visual representation of SheetsBatchClearNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Batch Clear"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsBatchClearNode"
    REQUIRED_SCOPES = SHEETS_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("ranges", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("cleared_ranges", DataType.LIST)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)
