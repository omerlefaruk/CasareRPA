"""
CasareRPA - Trigger Nodes Package

Visual trigger nodes for workflow entry points.
Each trigger type has a corresponding node that can be placed on the canvas.
"""

from casare_rpa.nodes.trigger_nodes.base_trigger_node import (
    BaseTriggerNode,
    trigger_node,
)

# Trigger node implementations (imported after definition)
from casare_rpa.nodes.trigger_nodes.webhook_trigger_node import WebhookTriggerNode
from casare_rpa.nodes.trigger_nodes.schedule_trigger_node import ScheduleTriggerNode
from casare_rpa.nodes.trigger_nodes.file_watch_trigger_node import FileWatchTriggerNode
from casare_rpa.nodes.trigger_nodes.email_trigger_node import EmailTriggerNode
from casare_rpa.nodes.trigger_nodes.app_event_trigger_node import AppEventTriggerNode
from casare_rpa.nodes.trigger_nodes.error_trigger_node import ErrorTriggerNode
from casare_rpa.nodes.trigger_nodes.workflow_call_trigger_node import (
    WorkflowCallTriggerNode,
)
from casare_rpa.nodes.trigger_nodes.form_trigger_node import FormTriggerNode
from casare_rpa.nodes.trigger_nodes.chat_trigger_node import ChatTriggerNode
from casare_rpa.nodes.trigger_nodes.rss_feed_trigger_node import RSSFeedTriggerNode
from casare_rpa.nodes.trigger_nodes.sse_trigger_node import SSETriggerNode

# Messaging triggers
from casare_rpa.nodes.trigger_nodes.telegram_trigger_node import TelegramTriggerNode
from casare_rpa.nodes.trigger_nodes.whatsapp_trigger_node import WhatsAppTriggerNode

# Google triggers
from casare_rpa.nodes.trigger_nodes.gmail_trigger_node import GmailTriggerNode
from casare_rpa.nodes.trigger_nodes.drive_trigger_node import DriveTriggerNode
from casare_rpa.nodes.trigger_nodes.sheets_trigger_node import SheetsTriggerNode
from casare_rpa.nodes.trigger_nodes.calendar_trigger_node import CalendarTriggerNode

__all__ = [
    # Base
    "BaseTriggerNode",
    "trigger_node",
    # General trigger nodes
    "WebhookTriggerNode",
    "ScheduleTriggerNode",
    "FileWatchTriggerNode",
    "EmailTriggerNode",
    "AppEventTriggerNode",
    "ErrorTriggerNode",
    "WorkflowCallTriggerNode",
    "FormTriggerNode",
    "ChatTriggerNode",
    "RSSFeedTriggerNode",
    "SSETriggerNode",
    # Messaging triggers
    "TelegramTriggerNode",
    "WhatsAppTriggerNode",
    # Google triggers
    "GmailTriggerNode",
    "DriveTriggerNode",
    "SheetsTriggerNode",
    "CalendarTriggerNode",
]
