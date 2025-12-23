"""Visual nodes for messaging category (Telegram, WhatsApp)."""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.messaging.telegram import (
    TelegramSendDocumentNode,
    TelegramSendLocationNode,
    TelegramSendMessageNode,
    TelegramSendPhotoNode,
)
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode

# =============================================================================
# Telegram Nodes
# =============================================================================


class VisualTelegramSendMessageNode(VisualNode):
    """Visual representation of TelegramSendMessageNode."""

    __identifier__ = "casare_rpa.messaging"
    NODE_NAME = "Telegram: Send Message"
    NODE_CATEGORY = "messaging/telegram/send"
    CASARE_NODE_CLASS = "TelegramSendMessageNode"

    def __init__(self) -> None:
        """Initialize Telegram Send Message node."""
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
        # Message settings
        self.add_text_input(
            "chat_id",
            "Chat ID",
            text="",
            tab="properties",
            placeholder_text="123456789 or @username",
        )
        self.add_text_input(
            "text",
            "Message Text",
            text="",
            tab="properties",
            placeholder_text="Hello, World!",
        )
        self.add_combo_menu(
            "parse_mode",
            "Parse Mode",
            items=["", "Markdown", "MarkdownV2", "HTML"],
            tab="properties",
        )
        self._safe_create_property("disable_notification", False, widget_type=1, tab="advanced")
        self.add_text_input(
            "reply_to_message_id",
            "Reply To Message ID",
            text="",
            tab="advanced",
            placeholder_text="Optional",
        )

    def get_node_class(self) -> type:
        return TelegramSendMessageNode

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("chat_id", DataType.STRING)
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("parse_mode", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("message_id", DataType.INTEGER)
        self.add_typed_output("chat_id", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualTelegramSendPhotoNode(VisualNode):
    """Visual representation of TelegramSendPhotoNode."""

    __identifier__ = "casare_rpa.messaging"
    NODE_NAME = "Telegram: Send Photo"
    NODE_CATEGORY = "messaging/telegram/send"
    CASARE_NODE_CLASS = "TelegramSendPhotoNode"

    def __init__(self) -> None:
        """Initialize Telegram Send Photo node."""
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
        # Photo settings
        self.add_text_input(
            "chat_id",
            "Chat ID",
            text="",
            tab="properties",
            placeholder_text="123456789 or @username",
        )
        self.add_text_input(
            "photo",
            "Photo",
            text="",
            tab="properties",
            placeholder_text="File path, URL, or file_id",
        )
        self.add_text_input(
            "caption",
            "Caption",
            text="",
            tab="properties",
            placeholder_text="Optional caption (0-1024 chars)",
        )
        self.add_combo_menu(
            "parse_mode",
            "Parse Mode",
            items=["", "Markdown", "MarkdownV2", "HTML"],
            tab="properties",
        )
        self._safe_create_property("disable_notification", False, widget_type=1, tab="advanced")

    def get_node_class(self) -> type:
        return TelegramSendPhotoNode

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("chat_id", DataType.STRING)
        self.add_typed_input("photo", DataType.STRING)
        self.add_typed_input("caption", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("message_id", DataType.INTEGER)
        self.add_typed_output("chat_id", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualTelegramSendDocumentNode(VisualNode):
    """Visual representation of TelegramSendDocumentNode."""

    __identifier__ = "casare_rpa.messaging"
    NODE_NAME = "Telegram: Send Document"
    NODE_CATEGORY = "messaging/telegram/send"
    CASARE_NODE_CLASS = "TelegramSendDocumentNode"

    def __init__(self) -> None:
        """Initialize Telegram Send Document node."""
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
        # Document settings
        self.add_text_input(
            "chat_id",
            "Chat ID",
            text="",
            tab="properties",
            placeholder_text="123456789 or @username",
        )
        self.add_text_input(
            "document",
            "Document",
            text="",
            tab="properties",
            placeholder_text="File path, URL, or file_id",
        )
        self.add_text_input(
            "filename",
            "Filename",
            text="",
            tab="properties",
            placeholder_text="Optional custom filename",
        )
        self.add_text_input(
            "caption",
            "Caption",
            text="",
            tab="properties",
            placeholder_text="Optional caption",
        )
        self.add_combo_menu(
            "parse_mode",
            "Parse Mode",
            items=["", "Markdown", "MarkdownV2", "HTML"],
            tab="properties",
        )
        self._safe_create_property("disable_notification", False, widget_type=1, tab="advanced")

    def get_node_class(self) -> type:
        return TelegramSendDocumentNode

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("chat_id", DataType.STRING)
        self.add_typed_input("document", DataType.STRING)
        self.add_typed_input("filename", DataType.STRING)
        self.add_typed_input("caption", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("message_id", DataType.INTEGER)
        self.add_typed_output("chat_id", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualTelegramSendLocationNode(VisualNode):
    """Visual representation of TelegramSendLocationNode."""

    __identifier__ = "casare_rpa.messaging"
    NODE_NAME = "Telegram: Send Location"
    NODE_CATEGORY = "messaging/telegram/send"
    CASARE_NODE_CLASS = "TelegramSendLocationNode"

    def __init__(self) -> None:
        """Initialize Telegram Send Location node."""
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
        # Location settings
        self.add_text_input(
            "chat_id",
            "Chat ID",
            text="",
            tab="properties",
            placeholder_text="123456789 or @username",
        )
        self.add_text_input(
            "latitude",
            "Latitude",
            text="",
            tab="properties",
            placeholder_text="-90 to 90",
        )
        self.add_text_input(
            "longitude",
            "Longitude",
            text="",
            tab="properties",
            placeholder_text="-180 to 180",
        )
        self._safe_create_property("disable_notification", False, widget_type=1, tab="advanced")

    def get_node_class(self) -> type:
        return TelegramSendLocationNode

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("chat_id", DataType.STRING)
        self.add_typed_input("latitude", DataType.FLOAT)
        self.add_typed_input("longitude", DataType.FLOAT)
        self.add_exec_output("exec_out")
        self.add_typed_output("message_id", DataType.INTEGER)
        self.add_typed_output("chat_id", DataType.INTEGER)
        self.add_typed_output("latitude", DataType.FLOAT)
        self.add_typed_output("longitude", DataType.FLOAT)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)
