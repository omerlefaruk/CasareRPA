"""
CasareRPA - Visual Trigger Nodes

All visual trigger node implementations for the canvas.
"""

from casare_rpa.domain.value_objects.types import DataType
from .base import VisualTriggerNode


class VisualWebhookTriggerNode(VisualTriggerNode):
    """Visual representation of WebhookTriggerNode."""

    __identifier__ = "casare_rpa.triggers"
    NODE_NAME = "Webhook Trigger"
    NODE_CATEGORY = "triggers/general"

    def _setup_payload_ports(self) -> None:
        """Setup webhook-specific output ports."""
        self.add_typed_output("payload", DataType.DICT)
        self.add_typed_output("headers", DataType.DICT)
        self.add_typed_output("query_params", DataType.DICT)
        self.add_typed_output("method", DataType.STRING)
        self.add_typed_output("path", DataType.STRING)
        self.add_typed_output("client_ip", DataType.STRING)


class VisualScheduleTriggerNode(VisualTriggerNode):
    """Visual representation of ScheduleTriggerNode."""

    __identifier__ = "casare_rpa.triggers"
    NODE_NAME = "Schedule Trigger"
    NODE_CATEGORY = "triggers/general"

    def _setup_payload_ports(self) -> None:
        """Setup schedule-specific output ports."""
        self.add_typed_output("trigger_time", DataType.STRING)
        self.add_typed_output("run_number", DataType.INTEGER)
        self.add_typed_output("scheduled_time", DataType.STRING)


class VisualFileWatchTriggerNode(VisualTriggerNode):
    """Visual representation of FileWatchTriggerNode."""

    __identifier__ = "casare_rpa.triggers"
    NODE_NAME = "File Watch Trigger"
    NODE_CATEGORY = "triggers/general"

    def _setup_payload_ports(self) -> None:
        """Setup file watch-specific output ports."""
        self.add_typed_output("file_path", DataType.STRING)
        self.add_typed_output("file_name", DataType.STRING)
        self.add_typed_output("event_type", DataType.STRING)
        self.add_typed_output("directory", DataType.STRING)
        self.add_typed_output("old_path", DataType.STRING)


class VisualEmailTriggerNode(VisualTriggerNode):
    """Visual representation of EmailTriggerNode."""

    __identifier__ = "casare_rpa.triggers"
    NODE_NAME = "Email Trigger"
    NODE_CATEGORY = "triggers/general"

    def _setup_payload_ports(self) -> None:
        """Setup email-specific output ports."""
        self.add_typed_output("email", DataType.DICT)
        self.add_typed_output("subject", DataType.STRING)
        self.add_typed_output("sender", DataType.STRING)
        self.add_typed_output("body", DataType.STRING)
        self.add_typed_output("html_body", DataType.STRING)
        self.add_typed_output("attachments", DataType.LIST)
        self.add_typed_output("received_at", DataType.STRING)


class VisualAppEventTriggerNode(VisualTriggerNode):
    """Visual representation of AppEventTriggerNode."""

    __identifier__ = "casare_rpa.triggers"
    NODE_NAME = "App Event Trigger"
    NODE_CATEGORY = "triggers/general"

    def _setup_payload_ports(self) -> None:
        """Setup app event-specific output ports."""
        self.add_typed_output("event_data", DataType.DICT)
        self.add_typed_output("event_type", DataType.STRING)
        self.add_typed_output("window_title", DataType.STRING)
        self.add_typed_output("process_name", DataType.STRING)
        self.add_typed_output("url", DataType.STRING)
        self.add_typed_output("timestamp", DataType.STRING)


class VisualErrorTriggerNode(VisualTriggerNode):
    """Visual representation of ErrorTriggerNode."""

    __identifier__ = "casare_rpa.triggers"
    NODE_NAME = "Error Trigger"
    NODE_CATEGORY = "triggers/general"

    def _setup_payload_ports(self) -> None:
        """Setup error-specific output ports."""
        self.add_typed_output("error", DataType.DICT)
        self.add_typed_output("error_type", DataType.STRING)
        self.add_typed_output("error_message", DataType.STRING)
        self.add_typed_output("workflow_id", DataType.STRING)
        self.add_typed_output("node_id", DataType.STRING)
        self.add_typed_output("stack_trace", DataType.STRING)
        self.add_typed_output("timestamp", DataType.STRING)


class VisualWorkflowCallTriggerNode(VisualTriggerNode):
    """Visual representation of WorkflowCallTriggerNode."""

    __identifier__ = "casare_rpa.triggers"
    NODE_NAME = "Workflow Call Trigger"
    NODE_CATEGORY = "triggers/general"

    def _setup_payload_ports(self) -> None:
        """Setup workflow call-specific output ports."""
        self.add_typed_output("params", DataType.DICT)
        self.add_typed_output("caller_workflow_id", DataType.STRING)
        self.add_typed_output("caller_node_id", DataType.STRING)
        self.add_typed_output("call_id", DataType.STRING)


class VisualFormTriggerNode(VisualTriggerNode):
    """Visual representation of FormTriggerNode."""

    __identifier__ = "casare_rpa.triggers"
    NODE_NAME = "Form Trigger"
    NODE_CATEGORY = "triggers/general"

    def _setup_payload_ports(self) -> None:
        """Setup form-specific output ports."""
        self.add_typed_output("form_data", DataType.DICT)
        self.add_typed_output("submitted_at", DataType.STRING)
        self.add_typed_output("user_id", DataType.STRING)
        self.add_typed_output("ip_address", DataType.STRING)


class VisualChatTriggerNode(VisualTriggerNode):
    """Visual representation of ChatTriggerNode."""

    __identifier__ = "casare_rpa.triggers"
    NODE_NAME = "Chat Trigger"
    NODE_CATEGORY = "triggers/general"

    def _setup_payload_ports(self) -> None:
        """Setup chat-specific output ports."""
        self.add_typed_output("message", DataType.STRING)
        self.add_typed_output("user_id", DataType.STRING)
        self.add_typed_output("user_name", DataType.STRING)
        self.add_typed_output("channel_id", DataType.STRING)
        self.add_typed_output("platform", DataType.STRING)
        self.add_typed_output("timestamp", DataType.STRING)
        self.add_typed_output("reply_to", DataType.STRING)


class VisualRSSFeedTriggerNode(VisualTriggerNode):
    """Visual representation of RSSFeedTriggerNode."""

    __identifier__ = "casare_rpa.triggers"
    NODE_NAME = "RSS Feed Trigger"
    NODE_CATEGORY = "triggers/general"

    def _setup_payload_ports(self) -> None:
        """Setup RSS-specific output ports."""
        self.add_typed_output("item", DataType.DICT)
        self.add_typed_output("title", DataType.STRING)
        self.add_typed_output("link", DataType.STRING)
        self.add_typed_output("description", DataType.STRING)
        self.add_typed_output("published", DataType.STRING)
        self.add_typed_output("author", DataType.STRING)
        self.add_typed_output("categories", DataType.LIST)


class VisualSSETriggerNode(VisualTriggerNode):
    """Visual representation of SSETriggerNode."""

    __identifier__ = "casare_rpa.triggers"
    NODE_NAME = "SSE Trigger"
    NODE_CATEGORY = "triggers/general"

    def _setup_payload_ports(self) -> None:
        """Setup SSE-specific output ports."""
        self.add_typed_output("event_type", DataType.STRING)
        self.add_typed_output("data", DataType.ANY)
        self.add_typed_output("raw_data", DataType.STRING)
        self.add_typed_output("event_id", DataType.STRING)
        self.add_typed_output("retry", DataType.INTEGER)
        self.add_typed_output("timestamp", DataType.STRING)


# =============================================================================
# Messaging Triggers
# =============================================================================


class VisualTelegramTriggerNode(VisualTriggerNode):
    """Visual representation of TelegramTriggerNode."""

    __identifier__ = "casare_rpa.triggers"
    NODE_NAME = "Telegram Trigger"
    NODE_CATEGORY = "triggers/messaging"
    CASARE_NODE_CLASS = "TelegramTriggerNode"

    def _setup_payload_ports(self) -> None:
        """Setup Telegram-specific output ports."""
        self.add_typed_output("message_id", DataType.INTEGER)
        self.add_typed_output("chat_id", DataType.INTEGER)
        self.add_typed_output("user_id", DataType.INTEGER)
        self.add_typed_output("username", DataType.STRING)
        self.add_typed_output("first_name", DataType.STRING)
        self.add_typed_output("text", DataType.STRING)
        self.add_typed_output("is_command", DataType.BOOLEAN)
        self.add_typed_output("command", DataType.STRING)
        self.add_typed_output("command_args", DataType.STRING)
        self.add_typed_output("message_type", DataType.STRING)
        self.add_typed_output("raw_update", DataType.DICT)


class VisualWhatsAppTriggerNode(VisualTriggerNode):
    """Visual representation of WhatsAppTriggerNode."""

    __identifier__ = "casare_rpa.triggers"
    NODE_NAME = "WhatsApp Trigger"
    NODE_CATEGORY = "triggers/messaging"
    CASARE_NODE_CLASS = "WhatsAppTriggerNode"

    def _setup_payload_ports(self) -> None:
        """Setup WhatsApp-specific output ports."""
        self.add_typed_output("message_id", DataType.STRING)
        self.add_typed_output("from_number", DataType.STRING)
        self.add_typed_output("to_number", DataType.STRING)
        self.add_typed_output("timestamp", DataType.STRING)
        self.add_typed_output("text", DataType.STRING)
        self.add_typed_output("message_type", DataType.STRING)
        self.add_typed_output("media_id", DataType.STRING)
        self.add_typed_output("media_url", DataType.STRING)
        self.add_typed_output("caption", DataType.STRING)
        self.add_typed_output("contact_name", DataType.STRING)
        self.add_typed_output("raw_message", DataType.DICT)


# =============================================================================
# Google Triggers
# =============================================================================


class VisualGmailTriggerNode(VisualTriggerNode):
    """Visual representation of GmailTriggerNode."""

    __identifier__ = "casare_rpa.triggers"
    NODE_NAME = "Gmail Trigger"
    NODE_CATEGORY = "triggers/google"
    CASARE_NODE_CLASS = "GmailTriggerNode"

    def _setup_payload_ports(self) -> None:
        """Setup Gmail-specific output ports."""
        self.add_typed_output("message_id", DataType.STRING)
        self.add_typed_output("thread_id", DataType.STRING)
        self.add_typed_output("subject", DataType.STRING)
        self.add_typed_output("from_email", DataType.STRING)
        self.add_typed_output("from_name", DataType.STRING)
        self.add_typed_output("to_email", DataType.STRING)
        self.add_typed_output("date", DataType.STRING)
        self.add_typed_output("snippet", DataType.STRING)
        self.add_typed_output("body_text", DataType.STRING)
        self.add_typed_output("body_html", DataType.STRING)
        self.add_typed_output("labels", DataType.LIST)
        self.add_typed_output("has_attachments", DataType.BOOLEAN)
        self.add_typed_output("attachments", DataType.LIST)
        self.add_typed_output("raw_message", DataType.DICT)


class VisualDriveTriggerNode(VisualTriggerNode):
    """Visual representation of DriveTriggerNode."""

    __identifier__ = "casare_rpa.triggers"
    NODE_NAME = "Google Drive Trigger"
    NODE_CATEGORY = "triggers/google"
    CASARE_NODE_CLASS = "DriveTriggerNode"

    def _setup_payload_ports(self) -> None:
        """Setup Drive-specific output ports."""
        self.add_typed_output("file_id", DataType.STRING)
        self.add_typed_output("file_name", DataType.STRING)
        self.add_typed_output("mime_type", DataType.STRING)
        self.add_typed_output("event_type", DataType.STRING)
        self.add_typed_output("modified_time", DataType.STRING)
        self.add_typed_output("size", DataType.INTEGER)
        self.add_typed_output("parent_id", DataType.STRING)
        self.add_typed_output("parent_name", DataType.STRING)
        self.add_typed_output("web_view_link", DataType.STRING)
        self.add_typed_output("download_url", DataType.STRING)
        self.add_typed_output("changed_by", DataType.STRING)
        self.add_typed_output("raw_change", DataType.DICT)


class VisualSheetsTriggerNode(VisualTriggerNode):
    """Visual representation of SheetsTriggerNode."""

    __identifier__ = "casare_rpa.triggers"
    NODE_NAME = "Google Sheets Trigger"
    NODE_CATEGORY = "triggers/google"
    CASARE_NODE_CLASS = "SheetsTriggerNode"

    def _setup_payload_ports(self) -> None:
        """Setup Sheets-specific output ports."""
        self.add_typed_output("spreadsheet_id", DataType.STRING)
        self.add_typed_output("sheet_name", DataType.STRING)
        self.add_typed_output("event_type", DataType.STRING)
        self.add_typed_output("row_number", DataType.INTEGER)
        self.add_typed_output("column", DataType.STRING)
        self.add_typed_output("old_value", DataType.ANY)
        self.add_typed_output("new_value", DataType.ANY)
        self.add_typed_output("row_data", DataType.LIST)
        self.add_typed_output("row_dict", DataType.DICT)
        self.add_typed_output("changed_cells", DataType.LIST)
        self.add_typed_output("timestamp", DataType.STRING)
        self.add_typed_output("raw_data", DataType.DICT)


class VisualCalendarTriggerNode(VisualTriggerNode):
    """Visual representation of CalendarTriggerNode."""

    __identifier__ = "casare_rpa.triggers"
    NODE_NAME = "Google Calendar Trigger"
    NODE_CATEGORY = "triggers/google"
    CASARE_NODE_CLASS = "CalendarTriggerNode"

    def _setup_payload_ports(self) -> None:
        """Setup Calendar-specific output ports."""
        self.add_typed_output("event_id", DataType.STRING)
        self.add_typed_output("calendar_id", DataType.STRING)
        self.add_typed_output("summary", DataType.STRING)
        self.add_typed_output("description", DataType.STRING)
        self.add_typed_output("start", DataType.STRING)
        self.add_typed_output("end", DataType.STRING)
        self.add_typed_output("location", DataType.STRING)
        self.add_typed_output("attendees", DataType.LIST)
        self.add_typed_output("event_type", DataType.STRING)
        self.add_typed_output("minutes_until_start", DataType.INTEGER)
        self.add_typed_output("organizer", DataType.STRING)
        self.add_typed_output("html_link", DataType.STRING)
        self.add_typed_output("status", DataType.STRING)
        self.add_typed_output("created", DataType.STRING)
        self.add_typed_output("updated", DataType.STRING)


# Export all visual trigger node classes
ALL_VISUAL_TRIGGER_NODES = [
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
]
