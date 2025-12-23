"""Visual nodes for Telegram action nodes (edit, delete, media group, callback)."""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.messaging.telegram import (
    TelegramAnswerCallbackNode,
    TelegramDeleteMessageNode,
    TelegramEditMessageNode,
    TelegramGetUpdatesNode,
    TelegramSendMediaGroupNode,
)
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


class VisualTelegramEditMessageNode(VisualNode):
    """Visual representation of TelegramEditMessageNode."""

    __identifier__ = "casare_rpa.messaging"
    NODE_NAME = "Telegram: Edit Message"
    NODE_CATEGORY = "messaging/telegram/actions"
    CASARE_NODE_CLASS = "TelegramEditMessageNode"

    def __init__(self) -> None:
        """Initialize Telegram Edit Message node."""
        super().__init__()
        # Connection settings
        self.add_text_input(
            "bot_token",
            "Bot Token",
            text="",
            tab="connection",
            placeholder_text="From @BotFather or use credential",
        )
        self.add_text_input(
            "credential_name",
            "Credential Name",
            text="",
            tab="connection",
            placeholder_text="telegram",
        )
        # Edit settings
        self.add_text_input(
            "chat_id",
            "Chat ID",
            text="",
            tab="properties",
            placeholder_text="123456789 or @username",
        )
        self.add_text_input(
            "message_id",
            "Message ID",
            text="",
            tab="properties",
            placeholder_text="ID of message to edit",
        )
        self.add_text_input(
            "text",
            "New Text",
            text="",
            tab="properties",
            placeholder_text="Updated message content",
        )
        self.add_combo_menu(
            "parse_mode",
            "Parse Mode",
            items=["", "Markdown", "MarkdownV2", "HTML"],
            tab="properties",
        )

    def get_node_class(self) -> type:
        return TelegramEditMessageNode

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("chat_id", DataType.STRING)
        self.add_typed_input("message_id", DataType.INTEGER)
        self.add_typed_input("text", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("message_id", DataType.INTEGER)
        self.add_typed_output("chat_id", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualTelegramDeleteMessageNode(VisualNode):
    """Visual representation of TelegramDeleteMessageNode."""

    __identifier__ = "casare_rpa.messaging"
    NODE_NAME = "Telegram: Delete Message"
    NODE_CATEGORY = "messaging/telegram/actions"
    CASARE_NODE_CLASS = "TelegramDeleteMessageNode"

    def __init__(self) -> None:
        """Initialize Telegram Delete Message node."""
        super().__init__()
        # Connection settings
        self.add_text_input(
            "bot_token",
            "Bot Token",
            text="",
            tab="connection",
            placeholder_text="From @BotFather or use credential",
        )
        self.add_text_input(
            "credential_name",
            "Credential Name",
            text="",
            tab="connection",
            placeholder_text="telegram",
        )
        # Delete settings
        self.add_text_input(
            "chat_id",
            "Chat ID",
            text="",
            tab="properties",
            placeholder_text="123456789 or @username",
        )
        self.add_text_input(
            "message_id",
            "Message ID",
            text="",
            tab="properties",
            placeholder_text="ID of message to delete",
        )

    def get_node_class(self) -> type:
        return TelegramDeleteMessageNode

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("chat_id", DataType.STRING)
        self.add_typed_input("message_id", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualTelegramSendMediaGroupNode(VisualNode):
    """Visual representation of TelegramSendMediaGroupNode."""

    __identifier__ = "casare_rpa.messaging"
    NODE_NAME = "Telegram: Send Media Group"
    NODE_CATEGORY = "messaging/telegram/send"
    CASARE_NODE_CLASS = "TelegramSendMediaGroupNode"

    def __init__(self) -> None:
        """Initialize Telegram Send Media Group node."""
        super().__init__()
        # Connection settings
        self.add_text_input(
            "bot_token",
            "Bot Token",
            text="",
            tab="connection",
            placeholder_text="From @BotFather or use credential",
        )
        self.add_text_input(
            "credential_name",
            "Credential Name",
            text="",
            tab="connection",
            placeholder_text="telegram",
        )
        # Media group settings
        self.add_text_input(
            "chat_id",
            "Chat ID",
            text="",
            tab="properties",
            placeholder_text="123456789 or @username",
        )
        self.add_text_input(
            "media_json",
            "Media (JSON)",
            text="",
            tab="properties",
            placeholder_text='[{"type":"photo","media":"url"}]',
        )
        self._safe_create_property("disable_notification", False, widget_type=1, tab="advanced")

    def get_node_class(self) -> type:
        return TelegramSendMediaGroupNode

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("chat_id", DataType.STRING)
        self.add_typed_input("media_json", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("message_ids", DataType.STRING)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualTelegramAnswerCallbackNode(VisualNode):
    """Visual representation of TelegramAnswerCallbackNode."""

    __identifier__ = "casare_rpa.messaging"
    NODE_NAME = "Telegram: Answer Callback"
    NODE_CATEGORY = "messaging/telegram/actions"
    CASARE_NODE_CLASS = "TelegramAnswerCallbackNode"

    def __init__(self) -> None:
        """Initialize Telegram Answer Callback node."""
        super().__init__()
        # Connection settings
        self.add_text_input(
            "bot_token",
            "Bot Token",
            text="",
            tab="connection",
            placeholder_text="From @BotFather or use credential",
        )
        self.add_text_input(
            "credential_name",
            "Credential Name",
            text="",
            tab="connection",
            placeholder_text="telegram",
        )
        # Callback settings
        self.add_text_input(
            "callback_query_id",
            "Callback Query ID",
            text="",
            tab="properties",
            placeholder_text="From trigger payload",
        )
        self.add_text_input(
            "text",
            "Response Text",
            text="",
            tab="properties",
            placeholder_text="Optional notification text",
        )
        self._safe_create_property("show_alert", False, widget_type=1, tab="properties")
        self.add_text_input(
            "url",
            "URL",
            text="",
            tab="advanced",
            placeholder_text="URL to open (for games)",
        )

    def get_node_class(self) -> type:
        return TelegramAnswerCallbackNode

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("callback_query_id", DataType.STRING)
        self.add_typed_input("text", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualTelegramGetUpdatesNode(VisualNode):
    """Visual representation of TelegramGetUpdatesNode."""

    __identifier__ = "casare_rpa.messaging"
    NODE_NAME = "Telegram: Get Updates"
    NODE_CATEGORY = "messaging/telegram/actions"
    CASARE_NODE_CLASS = "TelegramGetUpdatesNode"

    def __init__(self) -> None:
        """Initialize Telegram Get Updates node."""
        super().__init__()
        # Connection settings
        self.add_text_input(
            "bot_token",
            "Bot Token",
            text="",
            tab="connection",
            placeholder_text="From @BotFather or use credential",
        )
        self.add_text_input(
            "credential_name",
            "Credential Name",
            text="",
            tab="connection",
            placeholder_text="telegram",
        )
        # Update settings
        self.add_text_input(
            "offset",
            "Offset",
            text="",
            tab="properties",
            placeholder_text="Starting update ID",
        )
        self.add_text_input(
            "limit",
            "Limit",
            text="100",
            tab="properties",
            placeholder_text="1-100",
        )
        self.add_text_input(
            "timeout",
            "Timeout",
            text="30",
            tab="properties",
            placeholder_text="Seconds for long polling",
        )

    def get_node_class(self) -> type:
        return TelegramGetUpdatesNode

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("offset", DataType.INTEGER)
        self.add_typed_input("limit", DataType.INTEGER)
        self.add_typed_input("timeout", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("updates_json", DataType.STRING)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("last_update_id", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


__all__ = [
    "VisualTelegramEditMessageNode",
    "VisualTelegramDeleteMessageNode",
    "VisualTelegramSendMediaGroupNode",
    "VisualTelegramAnswerCallbackNode",
    "VisualTelegramGetUpdatesNode",
]
