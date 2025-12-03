"""Visual nodes for messaging category (Telegram, WhatsApp)."""

from casare_rpa.presentation.canvas.visual_nodes.messaging.nodes import (
    VisualTelegramSendMessageNode,
    VisualTelegramSendPhotoNode,
    VisualTelegramSendDocumentNode,
    VisualTelegramSendLocationNode,
)
from casare_rpa.presentation.canvas.visual_nodes.messaging.telegram_action_nodes import (
    VisualTelegramEditMessageNode,
    VisualTelegramDeleteMessageNode,
    VisualTelegramSendMediaGroupNode,
    VisualTelegramAnswerCallbackNode,
    VisualTelegramGetUpdatesNode,
)
from casare_rpa.presentation.canvas.visual_nodes.messaging.whatsapp_nodes import (
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
