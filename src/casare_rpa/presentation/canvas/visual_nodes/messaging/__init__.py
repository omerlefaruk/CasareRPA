"""Visual nodes for messaging category (Telegram, WhatsApp)."""

from casare_rpa.presentation.canvas.visual_nodes.messaging.nodes import (
    VisualTelegramSendDocumentNode,
    VisualTelegramSendLocationNode,
    VisualTelegramSendMessageNode,
    VisualTelegramSendPhotoNode,
)
from casare_rpa.presentation.canvas.visual_nodes.messaging.telegram_action_nodes import (
    VisualTelegramAnswerCallbackNode,
    VisualTelegramDeleteMessageNode,
    VisualTelegramEditMessageNode,
    VisualTelegramGetUpdatesNode,
    VisualTelegramSendMediaGroupNode,
)
from casare_rpa.presentation.canvas.visual_nodes.messaging.whatsapp_nodes import (
    VisualWhatsAppSendDocumentNode,
    VisualWhatsAppSendImageNode,
    VisualWhatsAppSendInteractiveNode,
    VisualWhatsAppSendLocationNode,
    VisualWhatsAppSendMessageNode,
    VisualWhatsAppSendTemplateNode,
    VisualWhatsAppSendVideoNode,
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
