"""
Fixtures for trigger node tests.

Provides:
- Common trigger node fixtures
- Sample payloads for testing populate_from_trigger_event
"""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any


@pytest.fixture
def sample_telegram_payload() -> Dict[str, Any]:
    """Sample Telegram trigger payload."""
    return {
        "message_id": 12345,
        "chat_id": 987654321,
        "user_id": 111222333,
        "username": "testuser",
        "first_name": "Test",
        "text": "Hello bot!",
        "is_command": False,
        "command": "",
        "command_args": "",
        "message_type": "text",
        "raw_update": {"update_id": 12345},
    }


@pytest.fixture
def sample_whatsapp_payload() -> Dict[str, Any]:
    """Sample WhatsApp trigger payload."""
    return {
        "message_id": "wamid.test123",
        "from_number": "+15551234567",
        "to_number": "+15557654321",
        "timestamp": "1234567890",
        "text": "Hello from WhatsApp!",
        "message_type": "text",
        "media_id": "",
        "media_url": "",
        "caption": "",
        "contact_name": "Test User",
        "raw_message": {"id": "wamid.test123"},
    }


@pytest.fixture
def sample_gmail_payload() -> Dict[str, Any]:
    """Sample Gmail trigger payload."""
    return {
        "message_id": "msg123abc",
        "thread_id": "thread456def",
        "subject": "Test Email Subject",
        "from_email": "sender@example.com",
        "from_name": "Test Sender",
        "to_email": "recipient@example.com",
        "date": "2025-12-03T10:00:00Z",
        "snippet": "This is a preview...",
        "body_text": "Full email body text",
        "body_html": "<p>Full email body</p>",
        "labels": ["INBOX", "IMPORTANT"],
        "has_attachments": True,
        "attachments": [{"filename": "doc.pdf", "size": 1024}],
        "raw_message": {"id": "msg123abc"},
    }


@pytest.fixture
def sample_calendar_payload() -> Dict[str, Any]:
    """Sample Google Calendar trigger payload."""
    return {
        "event_id": "event123xyz",
        "calendar_id": "primary",
        "summary": "Team Meeting",
        "description": "Weekly sync meeting",
        "start": "2025-12-03T14:00:00Z",
        "end": "2025-12-03T15:00:00Z",
        "location": "Conference Room A",
        "attendees": ["user1@example.com", "user2@example.com"],
        "event_type": "upcoming",
        "minutes_until_start": 15,
        "organizer": "organizer@example.com",
        "html_link": "https://calendar.google.com/event/123",
        "status": "confirmed",
        "created": "2025-12-01T10:00:00Z",
        "updated": "2025-12-02T10:00:00Z",
    }


@pytest.fixture
def sample_drive_payload() -> Dict[str, Any]:
    """Sample Google Drive trigger payload."""
    return {
        "file_id": "file123abc",
        "file_name": "document.pdf",
        "mime_type": "application/pdf",
        "event_type": "created",
        "modified_time": "2025-12-03T10:00:00Z",
        "size": 102400,
        "parent_id": "folder789",
        "parent_name": "Documents",
        "web_view_link": "https://drive.google.com/file/d/123/view",
        "download_url": "https://drive.google.com/uc?id=123",
        "changed_by": "user@example.com",
        "raw_change": {"kind": "drive#change"},
    }


@pytest.fixture
def sample_sheets_payload() -> Dict[str, Any]:
    """Sample Google Sheets trigger payload."""
    return {
        "spreadsheet_id": "spreadsheet123",
        "sheet_name": "Sheet1",
        "event_type": "new_row",
        "row_number": 10,
        "column": "A",
        "old_value": None,
        "new_value": "New Data",
        "row_data": ["Col1", "Col2", "Col3"],
        "row_dict": {"Name": "Col1", "Value": "Col2", "Status": "Col3"},
        "changed_cells": ["A10", "B10", "C10"],
        "timestamp": "2025-12-03T10:00:00Z",
        "raw_data": {"range": "Sheet1!A10:C10"},
    }
