"""Visual nodes for messaging category (Telegram, WhatsApp)."""

from .nodes import (
    VisualTelegramSendMessageNode,
    VisualTelegramSendPhotoNode,
    VisualTelegramSendDocumentNode,
    VisualTelegramSendLocationNode,
)
from .telegram_action_nodes import (
    VisualTelegramEditMessageNode,
    VisualTelegramDeleteMessageNode,
    VisualTelegramSendMediaGroupNode,
    VisualTelegramAnswerCallbackNode,
    VisualTelegramGetUpdatesNode,
)
from .whatsapp_nodes import (
    VisualWhatsAppSendMessageNode,
    VisualWhatsAppSendTemplateNode,
    VisualWhatsAppSendImageNode,
    VisualWhatsAppSendDocumentNode,
    VisualWhatsAppSendVideoNode,
    VisualWhatsAppSendLocationNode,
    VisualWhatsAppSendInteractiveNode,
)

__all__ = [
    # Telegram - Send
    "VisualTelegramSendMessageNode",
    "VisualTelegramSendPhotoNode",
    "VisualTelegramSendDocumentNode",
    "VisualTelegramSendLocationNode",
    # Telegram - Actions
    "VisualTelegramEditMessageNode",
    "VisualTelegramDeleteMessageNode",
    "VisualTelegramSendMediaGroupNode",
    "VisualTelegramAnswerCallbackNode",
    "VisualTelegramGetUpdatesNode",
    # WhatsApp
    "VisualWhatsAppSendMessageNode",
    "VisualWhatsAppSendTemplateNode",
    "VisualWhatsAppSendImageNode",
    "VisualWhatsAppSendDocumentNode",
    "VisualWhatsAppSendVideoNode",
    "VisualWhatsAppSendLocationNode",
    "VisualWhatsAppSendInteractiveNode",
]
