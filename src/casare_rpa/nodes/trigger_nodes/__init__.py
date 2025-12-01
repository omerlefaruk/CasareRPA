"""
CasareRPA - Trigger Nodes Package

Visual trigger nodes for workflow entry points.
Each trigger type has a corresponding node that can be placed on the canvas.
"""

from .base_trigger_node import BaseTriggerNode, trigger_node

# Trigger node implementations (imported after definition)
from .webhook_trigger_node import WebhookTriggerNode
from .schedule_trigger_node import ScheduleTriggerNode
from .file_watch_trigger_node import FileWatchTriggerNode
from .email_trigger_node import EmailTriggerNode
from .app_event_trigger_node import AppEventTriggerNode
from .error_trigger_node import ErrorTriggerNode
from .workflow_call_trigger_node import WorkflowCallTriggerNode
from .form_trigger_node import FormTriggerNode
from .chat_trigger_node import ChatTriggerNode
from .rss_feed_trigger_node import RSSFeedTriggerNode
from .sse_trigger_node import SSETriggerNode

__all__ = [
    # Base
    "BaseTriggerNode",
    "trigger_node",
    # Trigger nodes
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
]
