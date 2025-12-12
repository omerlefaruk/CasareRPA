# Infrastructure Resources Index

Quick reference for resource managers. Use for fast discovery.

## Overview

| Aspect | Description |
|--------|-------------|
| Purpose | Resource managers for external infrastructure |
| Files | 14 files |
| Exports | 44 total exports |

## Browser Resources

| Export | Source | Description |
|--------|--------|-------------|
| `BrowserResourceManager` | `browser_resource_manager.py` | Playwright browser lifecycle |

## LLM Resources

| Export | Source | Description |
|--------|--------|-------------|
| `LLMResourceManager` | `llm_resource_manager.py` | LLM client management |
| `LLMConfig` | `llm_resource_manager.py` | LLM configuration |
| `LLMProvider` | `llm_resource_manager.py` | Provider enum (OpenAI, Anthropic, etc.) |
| `LLMResponse` | `llm_resource_manager.py` | LLM response data |
| `LLMUsageMetrics` | `llm_resource_manager.py` | Token usage tracking |

## Document AI

| Export | Source | Description |
|--------|--------|-------------|
| `DocumentAIManager` | `document_ai_manager.py` | Document processing |
| `DocumentType` | `document_ai_manager.py` | Document type enum |
| `DocumentClassification` | `document_ai_manager.py` | Classification result |
| `ExtractionResult` | `document_ai_manager.py` | Data extraction result |
| `TableExtractionResult` | `document_ai_manager.py` | Table extraction result |
| `ValidationResult` | `document_ai_manager.py` | Validation result |

## Messaging

### Telegram

| Export | Source | Description |
|--------|--------|-------------|
| `TelegramClient` | `telegram_client.py` | Telegram Bot API client |
| `TelegramConfig` | `telegram_client.py` | Telegram configuration |
| `TelegramMessage` | `telegram_client.py` | Message data |
| `TelegramAPIError` | `telegram_client.py` | API error |

### WhatsApp

| Export | Source | Description |
|--------|--------|-------------|
| `WhatsAppClient` | `whatsapp_client.py` | WhatsApp Business API client |
| `WhatsAppConfig` | `whatsapp_client.py` | WhatsApp configuration |
| `WhatsAppMessage` | `whatsapp_client.py` | Message data |
| `WhatsAppTemplate` | `whatsapp_client.py` | Message template |
| `WhatsAppAPIError` | `whatsapp_client.py` | API error |

## Google Services

### Base Client

| Export | Source | Description |
|--------|--------|-------------|
| `GoogleAPIClient` | `google_client.py` | Base Google API client |
| `GoogleConfig` | `google_client.py` | Google configuration |
| `GoogleCredentials` | `google_client.py` | Credential data |
| `GoogleScope` | `google_client.py` | OAuth scope enum |
| `GoogleAPIError` | `google_client.py` | API error |
| `GoogleAuthError` | `google_client.py` | Authentication error |
| `GoogleQuotaError` | `google_client.py` | Quota exceeded |
| `GOOGLE_SCOPES` | `google_client.py` | Scope constants |
| `create_google_client()` | `google_client.py` | Factory function |

### Google Docs

| Export | Source | Description |
|--------|--------|-------------|
| `GoogleDocsClient` | `google_docs_client.py` | Docs API client |
| `GoogleDocsConfig` | `google_docs_client.py` | Docs configuration |
| `GoogleDocument` | `google_docs_client.py` | Document data |
| `GoogleDocsAPIError` | `google_docs_client.py` | API error |
| `DocsExportFormat` | `google_docs_client.py` | Export format enum |
| `DocumentStyle` | `google_docs_client.py` | Document styling |

### Google Calendar

| Export | Source | Description |
|--------|--------|-------------|
| `GoogleCalendarClient` | `google_calendar_client.py` | Calendar API client |
| `GoogleCalendarAPIError` | `google_calendar_client.py` | API error |
| `CalendarConfig` | `google_calendar_client.py` | Calendar configuration |
| `CalendarEvent` | `google_calendar_client.py` | Event data |
| `Calendar` | `google_calendar_client.py` | Calendar data |
| `FreeBusyInfo` | `google_calendar_client.py` | Free/busy information |

### Google Sheets

| Export | Source | Description |
|--------|--------|-------------|
| `GoogleSheetsClient` | `google_sheets_client.py` | Sheets API client |

### Google Drive

| Export | Source | Description |
|--------|--------|-------------|
| `GoogleDriveClient` | `google_drive_client.py` | Drive API client |

### Gmail

| Export | Source | Description |
|--------|--------|-------------|
| `GmailClient` | `gmail_client.py` | Gmail API client |

## Unified Manager

| Export | Source | Description |
|--------|--------|-------------|
| `UnifiedResourceManager` | `unified_resource_manager.py` | Unified resource lifecycle |

## Usage Patterns

```python
# Browser management
from casare_rpa.infrastructure.resources import BrowserResourceManager

browser_mgr = BrowserResourceManager()
await browser_mgr.get_browser()
page = await browser_mgr.get_page()

# LLM usage
from casare_rpa.infrastructure.resources import (
    LLMResourceManager, LLMConfig, LLMProvider
)

config = LLMConfig(
    provider=LLMProvider.OPENAI,
    model="gpt-4o-mini",
)
llm = LLMResourceManager(config)
response = await llm.complete("Generate workflow...")

# Google services
from casare_rpa.infrastructure.resources import (
    GoogleAPIClient, GoogleConfig, create_google_client
)

config = GoogleConfig(credential_id="my-credential")
client = create_google_client(config)

# Messaging
from casare_rpa.infrastructure.resources import (
    TelegramClient, TelegramConfig
)

config = TelegramConfig(bot_token="...")
client = TelegramClient(config)
await client.send_message(chat_id, text)
```

## Related Modules

| Module | Relation |
|--------|----------|
| `infrastructure.security` | Credential management |
| `nodes.google/` | Google service nodes |
| `nodes.messaging/` | Messaging nodes |
| `nodes.llm/` | LLM nodes |
