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

__all__ = [
    # Telegram
    "TelegramSendMessageNode",
    "TelegramSendPhotoNode",
    "TelegramSendDocumentNode",
    "TelegramSendLocationNode",
]
