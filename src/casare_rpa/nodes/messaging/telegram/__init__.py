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
    # Reusable PropertyDef constants
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CREDENTIAL_NAME,
    TELEGRAM_CHAT_ID,
    TELEGRAM_PARSE_MODE,
    TELEGRAM_DISABLE_NOTIFICATION,
)
from .telegram_actions import (
    TelegramEditMessageNode,
    TelegramDeleteMessageNode,
    TelegramSendMediaGroupNode,
    TelegramAnswerCallbackNode,
    TelegramGetUpdatesNode,
)

__all__ = [
    "TelegramBaseNode",
    # Send nodes
    "TelegramSendMessageNode",
    "TelegramSendPhotoNode",
    "TelegramSendDocumentNode",
    "TelegramSendLocationNode",
    # Action nodes
    "TelegramEditMessageNode",
    "TelegramDeleteMessageNode",
    "TelegramSendMediaGroupNode",
    "TelegramAnswerCallbackNode",
    "TelegramGetUpdatesNode",
    # Reusable PropertyDef constants
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CREDENTIAL_NAME",
    "TELEGRAM_CHAT_ID",
    "TELEGRAM_PARSE_MODE",
    "TELEGRAM_DISABLE_NOTIFICATION",
]
