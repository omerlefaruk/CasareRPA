"""
CasareRPA - Google Sheets Nodes

Nodes for Google Sheets operations: reading, writing, managing spreadsheet data,
and batch operations.
"""

from casare_rpa.nodes.google.google_base import SheetsBaseNode
from casare_rpa.nodes.google.sheets.sheets_batch import (
    SheetsBatchClearNode,
    SheetsBatchGetNode,
    SheetsBatchUpdateNode,
)
from casare_rpa.nodes.google.sheets.sheets_manage import (
    SheetsAddSheetNode,
    SheetsCopySheetNode,
    SheetsCreateSpreadsheetNode,
    SheetsDeleteSheetNode,
    SheetsDuplicateSheetNode,
    SheetsGetSpreadsheetNode,
    SheetsRenameSheetNode,
)
from casare_rpa.nodes.google.sheets.sheets_read import (
    SheetsGetCellNode,
    SheetsGetColumnNode,
    SheetsGetRangeNode,
    SheetsGetRowNode,
    SheetsGetSheetInfoNode,
    SheetsSearchNode,
)
from casare_rpa.nodes.google.sheets.sheets_write import (
    SheetsAppendRowNode,
    SheetsClearRangeNode,
    SheetsDeleteRowNode,
    SheetsInsertRowNode,
    SheetsUpdateRowNode,
    SheetsWriteCellNode,
    SheetsWriteRangeNode,
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
