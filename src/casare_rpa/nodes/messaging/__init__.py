"""
CasareRPA Messaging Nodes

Nodes for messaging platform integrations:
- Telegram Bot API
- WhatsApp Business Cloud API
"""

from casare_rpa.nodes.messaging.telegram import (
    TelegramSendMessageNode,
    TelegramSendPhotoNode,
    TelegramSendDocumentNode,
    TelegramSendLocationNode,
    TelegramEditMessageNode,
    TelegramDeleteMessageNode,
    TelegramSendMediaGroupNode,
    TelegramAnswerCallbackNode,
    TelegramGetUpdatesNode,
)
from casare_rpa.nodes.messaging.whatsapp import (
    WhatsAppSendMessageNode,
    WhatsAppSendTemplateNode,
    WhatsAppSendImageNode,
    WhatsAppSendDocumentNode,
    WhatsAppSendVideoNode,
    WhatsAppSendLocationNode,
    WhatsAppSendInteractiveNode,
)

__all__ = [
    # Telegram - Send
    "TelegramSendMessageNode",
    "TelegramSendPhotoNode",
    "TelegramSendDocumentNode",
    "TelegramSendLocationNode",
    # Telegram - Actions
    "TelegramEditMessageNode",
    "TelegramDeleteMessageNode",
    "TelegramSendMediaGroupNode",
    "TelegramAnswerCallbackNode",
    "TelegramGetUpdatesNode",
    # WhatsApp
    "WhatsAppSendMessageNode",
    "WhatsAppSendTemplateNode",
    "WhatsAppSendImageNode",
    "WhatsAppSendDocumentNode",
    "WhatsAppSendVideoNode",
    "WhatsAppSendLocationNode",
    "WhatsAppSendInteractiveNode",
]
