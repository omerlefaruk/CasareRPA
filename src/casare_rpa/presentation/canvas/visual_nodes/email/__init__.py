"""
Visual Nodes - Email
"""

from casare_rpa.presentation.canvas.visual_nodes.email.nodes import (
    VisualDeleteEmailNode,
    VisualFilterEmailsNode,
    VisualGetEmailContentNode,
    VisualMarkEmailNode,
    VisualMoveEmailNode,
    VisualReadEmailsNode,
    VisualSaveAttachmentNode,
    VisualSendEmailNode,
)

__all__ = [
    "VisualSendEmailNode",
    "VisualReadEmailsNode",
    "VisualGetEmailContentNode",
    "VisualSaveAttachmentNode",
    "VisualFilterEmailsNode",
    "VisualMarkEmailNode",
    "VisualDeleteEmailNode",
    "VisualMoveEmailNode",
]
