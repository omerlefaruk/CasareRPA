"""Visual nodes for Google Sheets operations."""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


# =============================================================================
# Cell Operations
# =============================================================================


class VisualSheetsGetCellNode(VisualNode):
    """Visual representation of SheetsGetCellNode.

    Widgets are auto-generated from SheetsGetCellNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Get Cell"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsGetCellNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("cell", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("value", DataType.ANY)
        self.add_typed_output("formatted_value", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsSetCellNode(VisualNode):
    """Visual representation of SheetsSetCellNode.

    Widgets are auto-generated from SheetsSetCellNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Set Cell"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsSetCellNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("cell", DataType.STRING)
        self.add_typed_input("value", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("updated_range", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsGetRangeNode(VisualNode):
    """Visual representation of SheetsGetRangeNode.

    Widgets are auto-generated from SheetsGetRangeNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Get Range"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsGetRangeNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("range", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("values", DataType.ARRAY)
        self.add_typed_output("row_count", DataType.INTEGER)
        self.add_typed_output("column_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsWriteRangeNode(VisualNode):
    """Visual representation of SheetsWriteRangeNode.

    Widgets are auto-generated from SheetsWriteRangeNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Write Range"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsWriteRangeNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("range", DataType.STRING)
        self.add_typed_input("values", DataType.ARRAY)
        self.add_exec_output("exec_out")
        self.add_typed_output("updated_range", DataType.STRING)
        self.add_typed_output("updated_rows", DataType.INTEGER)
        self.add_typed_output("updated_columns", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsClearRangeNode(VisualNode):
    """Visual representation of SheetsClearRangeNode.

    Widgets are auto-generated from SheetsClearRangeNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Clear Range"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsClearRangeNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("range", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("cleared_range", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


# =============================================================================
# Sheet Operations
# =============================================================================


class VisualSheetsCreateSpreadsheetNode(VisualNode):
    """Visual representation of SheetsCreateSpreadsheetNode.

    Widgets are auto-generated from SheetsCreateSpreadsheetNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Create Spreadsheet"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsCreateSpreadsheetNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("title", DataType.STRING)
        self.add_typed_input("sheet_names", DataType.ARRAY)
        self.add_exec_output("exec_out")
        self.add_typed_output("spreadsheet_id", DataType.STRING)
        self.add_typed_output("spreadsheet_url", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsGetSpreadsheetNode(VisualNode):
    """Visual representation of SheetsGetSpreadsheetNode.

    Widgets are auto-generated from SheetsGetSpreadsheetNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Get Spreadsheet"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsGetSpreadsheetNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("title", DataType.STRING)
        self.add_typed_output("sheets", DataType.ARRAY)
        self.add_typed_output("locale", DataType.STRING)
        self.add_typed_output("time_zone", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsAddSheetNode(VisualNode):
    """Visual representation of SheetsAddSheetNode.

    Widgets are auto-generated from SheetsAddSheetNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Add Sheet"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsAddSheetNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("sheet_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("sheet_id", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsDeleteSheetNode(VisualNode):
    """Visual representation of SheetsDeleteSheetNode.

    Widgets are auto-generated from SheetsDeleteSheetNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Delete Sheet"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsDeleteSheetNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("sheet_id", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsDuplicateSheetNode(VisualNode):
    """Visual representation of SheetsDuplicateSheetNode.

    Widgets are auto-generated from SheetsDuplicateSheetNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Duplicate Sheet"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsDuplicateSheetNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("sheet_id", DataType.INTEGER)
        self.add_typed_input("new_sheet_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("new_sheet_id", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsRenameSheetNode(VisualNode):
    """Visual representation of SheetsRenameSheetNode.

    Widgets are auto-generated from SheetsRenameSheetNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Rename Sheet"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsRenameSheetNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("sheet_id", DataType.INTEGER)
        self.add_typed_input("new_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


# =============================================================================
# Row/Column Operations
# =============================================================================


class VisualSheetsAppendRowNode(VisualNode):
    """Visual representation of SheetsAppendRowNode.

    Widgets are auto-generated from SheetsAppendRowNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Append Row"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsAppendRowNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("values", DataType.ARRAY)
        self.add_exec_output("exec_out")
        self.add_typed_output("updated_range", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsInsertRowNode(VisualNode):
    """Visual representation of SheetsInsertRowNode.

    Widgets are auto-generated from SheetsInsertRowNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Insert Row"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsInsertRowNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("sheet_id", DataType.INTEGER)
        self.add_typed_input("row_index", DataType.INTEGER)
        self.add_typed_input("num_rows", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsDeleteRowNode(VisualNode):
    """Visual representation of SheetsDeleteRowNode.

    Widgets are auto-generated from SheetsDeleteRowNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Delete Row"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsDeleteRowNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("sheet_id", DataType.INTEGER)
        self.add_typed_input("start_row", DataType.INTEGER)
        self.add_typed_input("num_rows", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsInsertColumnNode(VisualNode):
    """Visual representation of SheetsInsertColumnNode.

    Widgets are auto-generated from SheetsInsertColumnNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Insert Column"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsInsertColumnNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("sheet_id", DataType.INTEGER)
        self.add_typed_input("column_index", DataType.INTEGER)
        self.add_typed_input("num_columns", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsDeleteColumnNode(VisualNode):
    """Visual representation of SheetsDeleteColumnNode.

    Widgets are auto-generated from SheetsDeleteColumnNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Delete Column"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsDeleteColumnNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("sheet_id", DataType.INTEGER)
        self.add_typed_input("start_column", DataType.INTEGER)
        self.add_typed_input("num_columns", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


# =============================================================================
# Format Operations
# =============================================================================


class VisualSheetsFormatCellsNode(VisualNode):
    """Visual representation of SheetsFormatCellsNode.

    Widgets are auto-generated from SheetsFormatCellsNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Format Cells"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsFormatCellsNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("sheet_id", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsAutoResizeNode(VisualNode):
    """Visual representation of SheetsAutoResizeNode.

    Widgets are auto-generated from SheetsAutoResizeNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Auto Resize"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsAutoResizeNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("sheet_id", DataType.INTEGER)
        self.add_typed_input("start_index", DataType.INTEGER)
        self.add_typed_input("end_index", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


# =============================================================================
# Batch Operations
# =============================================================================


class VisualSheetsBatchUpdateNode(VisualNode):
    """Visual representation of SheetsBatchUpdateNode.

    Widgets are auto-generated from SheetsBatchUpdateNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Batch Update"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsBatchUpdateNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("data", DataType.ARRAY)
        self.add_exec_output("exec_out")
        self.add_typed_output("total_updated_rows", DataType.INTEGER)
        self.add_typed_output("total_updated_columns", DataType.INTEGER)
        self.add_typed_output("total_updated_cells", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsBatchGetNode(VisualNode):
    """Visual representation of SheetsBatchGetNode.

    Widgets are auto-generated from SheetsBatchGetNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Batch Get"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsBatchGetNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("ranges", DataType.ARRAY)
        self.add_exec_output("exec_out")
        self.add_typed_output("value_ranges", DataType.ARRAY)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsBatchClearNode(VisualNode):
    """Visual representation of SheetsBatchClearNode.

    Widgets are auto-generated from SheetsBatchClearNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Batch Clear"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsBatchClearNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("ranges", DataType.ARRAY)
        self.add_exec_output("exec_out")
        self.add_typed_output("cleared_ranges", DataType.ARRAY)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)
