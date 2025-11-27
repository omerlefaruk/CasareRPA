"""
Visual Nodes - Office Automation
"""

from .nodes import (
    VisualExcelOpenNode,
    VisualExcelReadCellNode,
    VisualExcelWriteCellNode,
    VisualExcelGetRangeNode,
    VisualExcelCloseNode,
    VisualWordOpenNode,
    VisualWordGetTextNode,
    VisualWordReplaceTextNode,
    VisualWordCloseNode,
    VisualOutlookSendEmailNode,
    VisualOutlookReadEmailsNode,
    VisualOutlookGetInboxCountNode,
)

__all__ = [
    "VisualExcelOpenNode",
    "VisualExcelReadCellNode",
    "VisualExcelWriteCellNode",
    "VisualExcelGetRangeNode",
    "VisualExcelCloseNode",
    "VisualWordOpenNode",
    "VisualWordGetTextNode",
    "VisualWordReplaceTextNode",
    "VisualWordCloseNode",
    "VisualOutlookSendEmailNode",
    "VisualOutlookReadEmailsNode",
    "VisualOutlookGetInboxCountNode",
]
