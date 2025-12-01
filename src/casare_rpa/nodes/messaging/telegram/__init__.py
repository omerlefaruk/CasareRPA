"""
Telegram Bot API Nodes

Provides nodes for sending messages, photos, documents, and more
via the Telegram Bot API.
"""

from .telegram_base import TelegramBaseNode
from .telegram_send import (
    TelegramSendMessageNode,
    TelegramSendPhotoNode,
    TelegramSendDocumentNode,
    TelegramSendLocationNode,
)

__all__ = [
    "TelegramBaseNode",
    "TelegramSendMessageNode",
    "TelegramSendPhotoNode",
    "TelegramSendDocumentNode",
    "TelegramSendLocationNode",
]
