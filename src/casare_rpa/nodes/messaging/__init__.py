"""
CasareRPA Messaging Nodes

Nodes for messaging platform integrations:
- Telegram Bot API
- WhatsApp Business Cloud API
"""

from casare_rpa.nodes.messaging.telegram import (
    TelegramAnswerCallbackNode,
    TelegramDeleteMessageNode,
    TelegramEditMessageNode,
    TelegramGetUpdatesNode,
    TelegramSendDocumentNode,
    TelegramSendLocationNode,
    TelegramSendMediaGroupNode,
    TelegramSendMessageNode,
    TelegramSendPhotoNode,
)
from casare_rpa.nodes.messaging.whatsapp import (
    WhatsAppSendDocumentNode,
    WhatsAppSendImageNode,
    WhatsAppSendInteractiveNode,
    WhatsAppSendLocationNode,
    WhatsAppSendMessageNode,
    WhatsAppSendTemplateNode,
    WhatsAppSendVideoNode,
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
