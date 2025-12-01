"""
CasareRPA - Infrastructure Resources
Resource managers for external infrastructure (browser, desktop, LLM, etc.).
"""

from .browser_resource_manager import BrowserResourceManager
from .llm_resource_manager import (
    LLMResourceManager,
    LLMConfig,
    LLMProvider,
    LLMResponse,
    LLMUsageMetrics,
)
from .document_ai_manager import (
    DocumentAIManager,
    DocumentType,
    DocumentClassification,
    ExtractionResult,
    TableExtractionResult,
    ValidationResult,
)
from .telegram_client import (
    TelegramClient,
    TelegramConfig,
    TelegramMessage,
    TelegramAPIError,
)
from .whatsapp_client import (
    WhatsAppClient,
    WhatsAppConfig,
    WhatsAppMessage,
    WhatsAppTemplate,
    WhatsAppAPIError,
)

__all__ = [
    "BrowserResourceManager",
    "LLMResourceManager",
    "LLMConfig",
    "LLMProvider",
    "LLMResponse",
    "LLMUsageMetrics",
    "DocumentAIManager",
    "DocumentType",
    "DocumentClassification",
    "ExtractionResult",
    "TableExtractionResult",
    "ValidationResult",
    "TelegramClient",
    "TelegramConfig",
    "TelegramMessage",
    "TelegramAPIError",
    "WhatsAppClient",
    "WhatsAppConfig",
    "WhatsAppMessage",
    "WhatsAppTemplate",
    "WhatsAppAPIError",
]
