"""
CasareRPA - Visual Trigger Nodes Package

Visual representations of trigger nodes for the canvas.
"""

from .base import VisualTriggerNode, TRIGGER_ACCENT_COLOR, TRIGGER_LISTENING_COLOR
from .nodes import (
    # General triggers
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
    # Messaging triggers
    VisualTelegramTriggerNode,
    VisualWhatsAppTriggerNode,
    # Google triggers
    VisualGmailTriggerNode,
    VisualDriveTriggerNode,
    VisualSheetsTriggerNode,
    VisualCalendarTriggerNode,
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
