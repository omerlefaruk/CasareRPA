"""
CasareRPA - Trigger Implementations

This module auto-imports all trigger implementations to register them
with the TriggerRegistry.
"""

# Import all trigger implementations to register them
from casare_rpa.triggers.implementations.webhook import WebhookTrigger
from casare_rpa.triggers.implementations.scheduled import ScheduledTrigger
from casare_rpa.triggers.implementations.file_watch import FileWatchTrigger
from casare_rpa.triggers.implementations.email_trigger import EmailTrigger
from casare_rpa.triggers.implementations.app_event import AppEventTrigger
from casare_rpa.triggers.implementations.error_trigger import ErrorTrigger
from casare_rpa.triggers.implementations.workflow_call import WorkflowCallTrigger
from casare_rpa.triggers.implementations.form_trigger import FormTrigger
from casare_rpa.triggers.implementations.chat_trigger import ChatTrigger
from casare_rpa.triggers.implementations.rss_trigger import RSSFeedTrigger
from casare_rpa.triggers.implementations.sse_trigger import SSETrigger
from casare_rpa.triggers.implementations.telegram_trigger import TelegramTrigger
from casare_rpa.triggers.implementations.whatsapp_trigger import WhatsAppTrigger

# Google Workspace triggers
from casare_rpa.triggers.implementations.google_trigger_base import (
    GoogleTriggerBase,
    GoogleAPIClient,
    GoogleCredentials,
)
from casare_rpa.triggers.implementations.gmail_trigger import GmailTrigger
from casare_rpa.triggers.implementations.sheets_trigger import SheetsTrigger
from casare_rpa.triggers.implementations.drive_trigger import DriveTrigger
from casare_rpa.triggers.implementations.calendar_trigger import CalendarTrigger

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
    # Google Workspace
    "GoogleTriggerBase",
    "GoogleAPIClient",
    "GoogleCredentials",
    "GmailTrigger",
    "SheetsTrigger",
    "DriveTrigger",
    "CalendarTrigger",
]
