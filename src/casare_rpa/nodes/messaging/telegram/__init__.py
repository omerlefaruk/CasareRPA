"""
Telegram Bot API Nodes

Provides nodes for sending messages, photos, documents, and more
via the Telegram Bot API.
"""

from casare_rpa.nodes.messaging.telegram.telegram_actions import (
    TelegramAnswerCallbackNode,
    TelegramDeleteMessageNode,
    TelegramEditMessageNode,
    TelegramGetUpdatesNode,
    TelegramSendMediaGroupNode,
)
from casare_rpa.nodes.messaging.telegram.telegram_base import TelegramBaseNode
from casare_rpa.nodes.messaging.telegram.telegram_send import (
    # Reusable PropertyDef constants
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TELEGRAM_CREDENTIAL_NAME,
    TELEGRAM_DISABLE_NOTIFICATION,
    TELEGRAM_PARSE_MODE,
    TelegramSendDocumentNode,
    TelegramSendLocationNode,
    TelegramSendMessageNode,
    TelegramSendPhotoNode,
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
