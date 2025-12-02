"""
CasareRPA - Google Sheets Nodes

Nodes for Google Sheets operations: reading, writing, managing spreadsheet data,
and batch operations.
"""

from casare_rpa.nodes.google.sheets.sheets_base import SheetsBaseNode
from casare_rpa.nodes.google.sheets.sheets_read import (
    SheetsGetCellNode,
    SheetsGetRangeNode,
    SheetsGetRowNode,
    SheetsGetColumnNode,
    SheetsSearchNode,
    SheetsGetSheetInfoNode,
)
from casare_rpa.nodes.google.sheets.sheets_write import (
    SheetsWriteCellNode,
    SheetsWriteRangeNode,
    SheetsAppendRowNode,
    SheetsUpdateRowNode,
    SheetsInsertRowNode,
    SheetsDeleteRowNode,
    SheetsClearRangeNode,
)
from casare_rpa.nodes.google.sheets.sheets_manage import (
    SheetsCreateSpreadsheetNode,
    SheetsGetSpreadsheetNode,
    SheetsAddSheetNode,
    SheetsDeleteSheetNode,
    SheetsCopySheetNode,
    SheetsDuplicateSheetNode,
    SheetsRenameSheetNode,
)
from casare_rpa.nodes.google.sheets.sheets_batch import (
    SheetsBatchUpdateNode,
    SheetsBatchGetNode,
    SheetsBatchClearNode,
)

__all__ = [
    # Base
    "SheetsBaseNode",
    # Read nodes (6)
    "SheetsGetCellNode",
    "SheetsGetRangeNode",
    "SheetsGetRowNode",
    "SheetsGetColumnNode",
    "SheetsSearchNode",
    "SheetsGetSheetInfoNode",
    # Write nodes (7)
    "SheetsWriteCellNode",
    "SheetsWriteRangeNode",
    "SheetsAppendRowNode",
    "SheetsUpdateRowNode",
    "SheetsInsertRowNode",
    "SheetsDeleteRowNode",
    "SheetsClearRangeNode",
    # Management nodes (7)
    "SheetsCreateSpreadsheetNode",
    "SheetsGetSpreadsheetNode",
    "SheetsAddSheetNode",
    "SheetsDeleteSheetNode",
    "SheetsCopySheetNode",
    "SheetsDuplicateSheetNode",
    "SheetsRenameSheetNode",
    # Batch nodes (3)
    "SheetsBatchUpdateNode",
    "SheetsBatchGetNode",
    "SheetsBatchClearNode",
]
