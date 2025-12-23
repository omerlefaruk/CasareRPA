"""
Visual Nodes - Office Automation
"""

from casare_rpa.presentation.canvas.visual_nodes.office_automation.nodes import (
    VisualExcelCloseNode,
    VisualExcelGetRangeNode,
    VisualExcelOpenNode,
    VisualExcelReadCellNode,
    VisualExcelWriteCellNode,
    VisualOutlookGetInboxCountNode,
    VisualOutlookReadEmailsNode,
    VisualOutlookSendEmailNode,
    VisualWordCloseNode,
    VisualWordGetTextNode,
    VisualWordOpenNode,
    VisualWordReplaceTextNode,
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
