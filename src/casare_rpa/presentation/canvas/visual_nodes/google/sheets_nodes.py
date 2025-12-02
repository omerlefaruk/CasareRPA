"""Visual nodes for Google Sheets operations."""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


# =============================================================================
# Cell Operations
# =============================================================================


class VisualSheetsGetCellNode(VisualNode):
    """Visual representation of SheetsGetCellNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Get Cell"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsGetCellNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "spreadsheet_id",
            "Spreadsheet ID",
            text="",
            tab="properties",
            placeholder_text="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
        )
        self.add_text_input("sheet_name", "Sheet Name", text="Sheet1", tab="properties")
        self.add_text_input(
            "cell", "Cell", text="A1", tab="properties", placeholder_text="A1"
        )

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
    """Visual representation of SheetsSetCellNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Set Cell"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsSetCellNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "spreadsheet_id", "Spreadsheet ID", text="", tab="properties"
        )
        self.add_text_input("sheet_name", "Sheet Name", text="Sheet1", tab="properties")
        self.add_text_input("cell", "Cell", text="A1", tab="properties")

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
    """Visual representation of SheetsGetRangeNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Get Range"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsGetRangeNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "spreadsheet_id", "Spreadsheet ID", text="", tab="properties"
        )
        self.add_text_input("sheet_name", "Sheet Name", text="Sheet1", tab="properties")
        self.add_text_input(
            "range",
            "Range",
            text="A1:Z100",
            tab="properties",
            placeholder_text="A1:C10",
        )

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
    """Visual representation of SheetsWriteRangeNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Write Range"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsWriteRangeNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "spreadsheet_id", "Spreadsheet ID", text="", tab="properties"
        )
        self.add_text_input("sheet_name", "Sheet Name", text="Sheet1", tab="properties")
        self.add_text_input("range", "Start Cell", text="A1", tab="properties")

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
    """Visual representation of SheetsClearRangeNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Clear Range"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsClearRangeNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "spreadsheet_id", "Spreadsheet ID", text="", tab="properties"
        )
        self.add_text_input("sheet_name", "Sheet Name", text="Sheet1", tab="properties")
        self.add_text_input("range", "Range", text="A1:Z100", tab="properties")

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
    """Visual representation of SheetsCreateSpreadsheetNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Create Spreadsheet"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsCreateSpreadsheetNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("title", "Title", text="New Spreadsheet", tab="properties")

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
    """Visual representation of SheetsGetSpreadsheetNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Get Spreadsheet"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsGetSpreadsheetNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "spreadsheet_id", "Spreadsheet ID", text="", tab="properties"
        )

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
    """Visual representation of SheetsAddSheetNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Add Sheet"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsAddSheetNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "spreadsheet_id", "Spreadsheet ID", text="", tab="properties"
        )
        self.add_text_input(
            "sheet_name", "Sheet Name", text="New Sheet", tab="properties"
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("sheet_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("sheet_id", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsDeleteSheetNode(VisualNode):
    """Visual representation of SheetsDeleteSheetNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Delete Sheet"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsDeleteSheetNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "spreadsheet_id", "Spreadsheet ID", text="", tab="properties"
        )
        self.add_text_input("sheet_id", "Sheet ID", text="0", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("sheet_id", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsDuplicateSheetNode(VisualNode):
    """Visual representation of SheetsDuplicateSheetNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Duplicate Sheet"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsDuplicateSheetNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "spreadsheet_id", "Spreadsheet ID", text="", tab="properties"
        )
        self.add_text_input("sheet_id", "Source Sheet ID", text="0", tab="properties")
        self.add_text_input(
            "new_sheet_name", "New Sheet Name", text="Copy", tab="properties"
        )

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
    """Visual representation of SheetsRenameSheetNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Rename Sheet"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsRenameSheetNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "spreadsheet_id", "Spreadsheet ID", text="", tab="properties"
        )
        self.add_text_input("sheet_id", "Sheet ID", text="0", tab="properties")
        self.add_text_input("new_name", "New Name", text="", tab="properties")

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
    """Visual representation of SheetsAppendRowNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Append Row"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsAppendRowNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "spreadsheet_id", "Spreadsheet ID", text="", tab="properties"
        )
        self.add_text_input("sheet_name", "Sheet Name", text="Sheet1", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("values", DataType.ARRAY)
        self.add_exec_output("exec_out")
        self.add_typed_output("updated_range", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsInsertRowNode(VisualNode):
    """Visual representation of SheetsInsertRowNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Insert Row"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsInsertRowNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "spreadsheet_id", "Spreadsheet ID", text="", tab="properties"
        )
        self.add_text_input("sheet_id", "Sheet ID", text="0", tab="properties")
        self.add_text_input(
            "row_index", "Row Index (0-based)", text="0", tab="properties"
        )
        self.add_text_input("num_rows", "Number of Rows", text="1", tab="properties")

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
    """Visual representation of SheetsDeleteRowNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Delete Row"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsDeleteRowNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "spreadsheet_id", "Spreadsheet ID", text="", tab="properties"
        )
        self.add_text_input("sheet_id", "Sheet ID", text="0", tab="properties")
        self.add_text_input(
            "start_row", "Start Row (0-based)", text="0", tab="properties"
        )
        self.add_text_input("num_rows", "Number of Rows", text="1", tab="properties")

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
    """Visual representation of SheetsInsertColumnNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Insert Column"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsInsertColumnNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "spreadsheet_id", "Spreadsheet ID", text="", tab="properties"
        )
        self.add_text_input("sheet_id", "Sheet ID", text="0", tab="properties")
        self.add_text_input(
            "column_index", "Column Index (0-based)", text="0", tab="properties"
        )
        self.add_text_input(
            "num_columns", "Number of Columns", text="1", tab="properties"
        )

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
    """Visual representation of SheetsDeleteColumnNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Delete Column"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsDeleteColumnNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "spreadsheet_id", "Spreadsheet ID", text="", tab="properties"
        )
        self.add_text_input("sheet_id", "Sheet ID", text="0", tab="properties")
        self.add_text_input(
            "start_column", "Start Column (0-based)", text="0", tab="properties"
        )
        self.add_text_input(
            "num_columns", "Number of Columns", text="1", tab="properties"
        )

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
    """Visual representation of SheetsFormatCellsNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Format Cells"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsFormatCellsNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "spreadsheet_id", "Spreadsheet ID", text="", tab="properties"
        )
        self.add_text_input("sheet_id", "Sheet ID", text="0", tab="properties")
        self.add_text_input("start_row", "Start Row", text="0", tab="properties")
        self.add_text_input("end_row", "End Row", text="1", tab="properties")
        self.add_text_input("start_column", "Start Column", text="0", tab="properties")
        self.add_text_input("end_column", "End Column", text="1", tab="properties")
        # Format options
        self.add_checkbox("bold", "Bold", state=False, tab="formatting")
        self.add_checkbox("italic", "Italic", state=False, tab="formatting")
        self.add_text_input("font_size", "Font Size", text="10", tab="formatting")
        self.add_text_input(
            "background_color",
            "Background (R,G,B)",
            text="",
            tab="formatting",
            placeholder_text="255,255,0",
        )
        self.add_text_input(
            "text_color",
            "Text Color (R,G,B)",
            text="",
            tab="formatting",
            placeholder_text="0,0,0",
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("sheet_id", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsAutoResizeNode(VisualNode):
    """Visual representation of SheetsAutoResizeNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Auto Resize"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsAutoResizeNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "spreadsheet_id", "Spreadsheet ID", text="", tab="properties"
        )
        self.add_text_input("sheet_id", "Sheet ID", text="0", tab="properties")
        self.add_text_input("start_index", "Start Index", text="0", tab="properties")
        self.add_text_input("end_index", "End Index", text="26", tab="properties")
        self.add_combo_menu(
            "dimension", "Dimension", items=["COLUMNS", "ROWS"], tab="properties"
        )

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
    """Visual representation of SheetsBatchUpdateNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Batch Update"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsBatchUpdateNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "spreadsheet_id", "Spreadsheet ID", text="", tab="properties"
        )

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
    """Visual representation of SheetsBatchGetNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Batch Get"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsBatchGetNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "spreadsheet_id", "Spreadsheet ID", text="", tab="properties"
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("ranges", DataType.ARRAY)
        self.add_exec_output("exec_out")
        self.add_typed_output("value_ranges", DataType.ARRAY)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSheetsBatchClearNode(VisualNode):
    """Visual representation of SheetsBatchClearNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Sheets: Batch Clear"
    NODE_CATEGORY = "google/sheets"
    CASARE_NODE_CLASS = "SheetsBatchClearNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "spreadsheet_id", "Spreadsheet ID", text="", tab="properties"
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("spreadsheet_id", DataType.STRING)
        self.add_typed_input("ranges", DataType.ARRAY)
        self.add_exec_output("exec_out")
        self.add_typed_output("cleared_ranges", DataType.ARRAY)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)
