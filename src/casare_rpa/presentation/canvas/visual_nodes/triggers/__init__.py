"""
CasareRPA - Visual Trigger Nodes Package

Visual representations of trigger nodes for the canvas.
"""

from casare_rpa.presentation.canvas.visual_nodes.triggers.base import (
    TRIGGER_ACCENT_COLOR,
    TRIGGER_LISTENING_COLOR,
    VisualTriggerNode,
)
from casare_rpa.presentation.canvas.visual_nodes.triggers.nodes import (
    VisualAppEventTriggerNode,
    VisualCalendarTriggerNode,
    VisualChatTriggerNode,
    VisualDriveTriggerNode,
    VisualEmailTriggerNode,
    VisualErrorTriggerNode,
    VisualFileWatchTriggerNode,
    VisualFormTriggerNode,
    # Google triggers
    VisualGmailTriggerNode,
    VisualRSSFeedTriggerNode,
    VisualScheduleTriggerNode,
    VisualSheetsTriggerNode,
    VisualSSETriggerNode,
    # Messaging triggers
    VisualTelegramTriggerNode,
    # General triggers
    VisualWebhookTriggerNode,
    VisualWhatsAppTriggerNode,
    VisualWorkflowCallTriggerNode,
)

__all__ = [
    # Base
    "VisualTriggerNode",
    "TRIGGER_ACCENT_COLOR",
    "TRIGGER_LISTENING_COLOR",
    # General triggers
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
    # Messaging triggers
    "VisualTelegramTriggerNode",
    "VisualWhatsAppTriggerNode",
    # Google triggers
    "VisualGmailTriggerNode",
    "VisualDriveTriggerNode",
    "VisualSheetsTriggerNode",
    "VisualCalendarTriggerNode",
]
