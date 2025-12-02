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
from .google_client import (
    GoogleAPIClient,
    GoogleConfig,
    GoogleCredentials,
    GoogleScope,
    GoogleAPIError,
    GoogleAuthError,
    GoogleQuotaError,
    SCOPES as GOOGLE_SCOPES,
    create_google_client,
)
from .google_docs_client import (
    GoogleDocsClient,
    GoogleDocsConfig,
    GoogleDocument,
    GoogleDocsAPIError,
    ExportFormat as DocsExportFormat,
    DocumentStyle,
)
from .google_calendar_client import (
    GoogleCalendarClient,
    GoogleCalendarAPIError,
    CalendarConfig,
    CalendarEvent,
    Calendar,
    FreeBusyInfo,
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
    # Google
    "GoogleAPIClient",
    "GoogleConfig",
    "GoogleCredentials",
    "GoogleScope",
    "GoogleAPIError",
    "GoogleAuthError",
    "GoogleQuotaError",
    "GOOGLE_SCOPES",
    "create_google_client",
    # Google Docs
    "GoogleDocsClient",
    "GoogleDocsConfig",
    "GoogleDocument",
    "GoogleDocsAPIError",
    "DocsExportFormat",
    "DocumentStyle",
    # Google Calendar
    "GoogleCalendarClient",
    "GoogleCalendarAPIError",
    "CalendarConfig",
    "CalendarEvent",
    "Calendar",
    "FreeBusyInfo",
]
