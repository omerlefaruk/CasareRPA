"""
CasareRPA Messaging Nodes

Nodes for messaging platform integrations:
- Telegram Bot API
- WhatsApp Business Cloud API
"""

from .telegram import (
    TelegramSendMessageNode,
    TelegramSendPhotoNode,
    TelegramSendDocumentNode,
    TelegramSendLocationNode,
)
from .whatsapp import (
    WhatsAppSendMessageNode,
    WhatsAppSendTemplateNode,
    WhatsAppSendImageNode,
    WhatsAppSendDocumentNode,
    WhatsAppSendVideoNode,
    WhatsAppSendLocationNode,
    WhatsAppSendInteractiveNode,
)

__all__ = [
    # Telegram
    "TelegramSendMessageNode",
    "TelegramSendPhotoNode",
    "TelegramSendDocumentNode",
    "TelegramSendLocationNode",
    # WhatsApp
    "WhatsAppSendMessageNode",
    "WhatsAppSendTemplateNode",
    "WhatsAppSendImageNode",
    "WhatsAppSendDocumentNode",
    "WhatsAppSendVideoNode",
    "WhatsAppSendLocationNode",
    "WhatsAppSendInteractiveNode",
]
