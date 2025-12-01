"""
CasareRPA - Trigger Implementations

This module auto-imports all trigger implementations to register them
with the TriggerRegistry.
"""

# Import all trigger implementations to register them
from .webhook import WebhookTrigger
from .scheduled import ScheduledTrigger
from .file_watch import FileWatchTrigger
from .email_trigger import EmailTrigger
from .app_event import AppEventTrigger
from .error_trigger import ErrorTrigger
from .workflow_call import WorkflowCallTrigger
from .form_trigger import FormTrigger
from .chat_trigger import ChatTrigger
from .rss_trigger import RSSFeedTrigger
from .sse_trigger import SSETrigger
from .telegram_trigger import TelegramTrigger
from .whatsapp_trigger import WhatsAppTrigger

__all__ = [
    "WebhookTrigger",
    "ScheduledTrigger",
    "FileWatchTrigger",
    "EmailTrigger",
    "AppEventTrigger",
    "ErrorTrigger",
    "WorkflowCallTrigger",
    "FormTrigger",
    "ChatTrigger",
    "RSSFeedTrigger",
    "SSETrigger",
    "TelegramTrigger",
    "WhatsAppTrigger",
]
