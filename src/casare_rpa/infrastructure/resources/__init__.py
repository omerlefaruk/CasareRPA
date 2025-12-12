"""
CasareRPA - Infrastructure Resources
Resource managers for external infrastructure (browser, desktop, LLM, etc.).
"""

from casare_rpa.infrastructure.resources.browser_resource_manager import (
    BrowserResourceManager,
)
from casare_rpa.infrastructure.resources.resource_registry import (
    ResourceRegistry,
    get_resource_registry,
    reset_resource_registry,
)
from casare_rpa.infrastructure.resources.document_ai_manager import (
    DocumentAIManager,
    DocumentClassification,
    DocumentType,
    ExtractionResult,
    TableExtractionResult,
    ValidationResult,
)
from casare_rpa.infrastructure.resources.google_calendar_client import (
    Calendar,
    CalendarConfig,
    CalendarEvent,
    FreeBusyInfo,
    GoogleCalendarAPIError,
    GoogleCalendarClient,
)
from casare_rpa.infrastructure.resources.google_client import (
    SCOPES as GOOGLE_SCOPES,
    GoogleAPIClient,
    GoogleAPIError,
    GoogleAuthError,
    GoogleConfig,
    GoogleCredentials,
    GoogleQuotaError,
    GoogleScope,
    create_google_client,
)
from casare_rpa.infrastructure.resources.google_docs_client import (
    DocumentStyle,
    ExportFormat as DocsExportFormat,
    GoogleDocsAPIError,
    GoogleDocsClient,
    GoogleDocsConfig,
    GoogleDocument,
)
from casare_rpa.infrastructure.resources.llm_resource_manager import (
    LLMConfig,
    LLMProvider,
    LLMResourceManager,
    LLMResponse,
    LLMUsageMetrics,
)
from casare_rpa.infrastructure.resources.telegram_client import (
    TelegramAPIError,
    TelegramClient,
    TelegramConfig,
    TelegramMessage,
)
from casare_rpa.infrastructure.resources.whatsapp_client import (
    WhatsAppAPIError,
    WhatsAppClient,
    WhatsAppConfig,
    WhatsAppMessage,
    WhatsAppTemplate,
)

__all__ = [
    # Resource Registry
    "ResourceRegistry",
    "get_resource_registry",
    "reset_resource_registry",
    # Resource Managers
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
