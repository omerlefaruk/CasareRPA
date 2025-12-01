"""
CasareRPA - Visual Trigger Nodes Package

Visual representations of trigger nodes for the canvas.
"""

from .base import VisualTriggerNode, TRIGGER_ACCENT_COLOR, TRIGGER_LISTENING_COLOR
from .nodes import (
    VisualWebhookTriggerNode,
    VisualScheduleTriggerNode,
    VisualFileWatchTriggerNode,
    VisualEmailTriggerNode,
    VisualAppEventTriggerNode,
    VisualErrorTriggerNode,
    VisualWorkflowCallTriggerNode,
    VisualFormTriggerNode,
    VisualChatTriggerNode,
    VisualRSSFeedTriggerNode,
    VisualSSETriggerNode,
)

__all__ = [
    # Base
    "VisualTriggerNode",
    "TRIGGER_ACCENT_COLOR",
    "TRIGGER_LISTENING_COLOR",
    # Visual trigger nodes
    "VisualWebhookTriggerNode",
    "VisualScheduleTriggerNode",
    "VisualFileWatchTriggerNode",
    "VisualEmailTriggerNode",
    "VisualAppEventTriggerNode",
    "VisualErrorTriggerNode",
    "VisualWorkflowCallTriggerNode",
    "VisualFormTriggerNode",
    "VisualChatTriggerNode",
    "VisualRSSFeedTriggerNode",
    "VisualSSETriggerNode",
]
