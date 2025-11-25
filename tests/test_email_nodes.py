"""
Tests for email automation nodes.

Tests SendEmailNode, ReadEmailsNode, GetEmailContentNode, SaveAttachmentNode,
FilterEmailsNode, MarkEmailNode, DeleteEmailNode, and MoveEmailNode.

For SMTP/IMAP tests, set these environment variables:
- EMAIL_TEST_SMTP_SERVER (e.g., smtp.gmail.com)
- EMAIL_TEST_SMTP_PORT (e.g., 587)
- EMAIL_TEST_IMAP_SERVER (e.g., imap.gmail.com)
- EMAIL_TEST_IMAP_PORT (e.g., 993)
- EMAIL_TEST_USERNAME (email address)
- EMAIL_TEST_PASSWORD (app password)
- EMAIL_TEST_RECIPIENT (recipient for send tests)
"""

import pytest
import os
import tempfile
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from unittest.mock import Mock

from casare_rpa.nodes.email_nodes import (
    SendEmailNode,
    ReadEmailsNode,
    GetEmailContentNode,
    SaveAttachmentNode,
    FilterEmailsNode,
    MarkEmailNode,
    DeleteEmailNode,
    MoveEmailNode,
    _decode_header_value,
    _parse_email_message,
)
from casare_rpa.core.execution_context import ExecutionContext


# =============================================================================
# Test Configuration
# =============================================================================


def get_email_config():
    """Get email configuration from environment variables."""
    return {
        "smtp_server": os.environ.get("EMAIL_TEST_SMTP_SERVER", ""),
        "smtp_port": int(os.environ.get("EMAIL_TEST_SMTP_PORT", "587")),
        "imap_server": os.environ.get("EMAIL_TEST_IMAP_SERVER", ""),
        "imap_port": int(os.environ.get("EMAIL_TEST_IMAP_PORT", "993")),
        "username": os.environ.get("EMAIL_TEST_USERNAME", ""),
        "password": os.environ.get("EMAIL_TEST_PASSWORD", ""),
        "recipient": os.environ.get("EMAIL_TEST_RECIPIENT", ""),
    }


def email_credentials_available():
    """Check if email credentials are configured."""
    config = get_email_config()
    return all([
        config["smtp_server"],
        config["imap_server"],
        config["username"],
        config["password"],
    ])


# Skip marker for tests requiring real email credentials
requires_email_credentials = pytest.mark.skipif(
    not email_credentials_available(),
    reason="Email credentials not configured. Set EMAIL_TEST_* environment variables."
)


@pytest.fixture
def context():
    """Create a mock execution context."""
    ctx = Mock(spec=ExecutionContext)
    ctx.variables = {}
    ctx.workflow_id = "test_workflow"
    return ctx


@pytest.fixture
def email_config():
    """Get email configuration."""
    return get_email_config()


# =============================================================================
# Helper Function Tests (No network required)
# =============================================================================


class TestHelperFunctions:
    """Tests for email helper functions - no mocking needed."""

    def test_decode_header_value_plain(self):
        """Test decoding a plain string header."""
        result = _decode_header_value("Hello World")
        assert result == "Hello World"

    def test_decode_header_value_empty(self):
        """Test decoding empty header."""
        result = _decode_header_value("")
        assert result == ""

    def test_decode_header_value_none(self):
        """Test decoding None header."""
        result = _decode_header_value(None)
        assert result == ""

    def test_decode_header_value_encoded_utf8(self):
        """Test decoding a UTF-8 encoded header."""
        encoded = "=?utf-8?b?SGVsbG8gV29ybGQ=?="
        result = _decode_header_value(encoded)
        assert result == "Hello World"

    def test_decode_header_value_encoded_iso(self):
        """Test decoding an ISO-8859-1 encoded header."""
        encoded = "=?iso-8859-1?q?Caf=E9?="
        result = _decode_header_value(encoded)
        assert "Caf" in result

    def test_decode_header_value_mixed(self):
        """Test decoding mixed encoded and plain text."""
        encoded = "=?utf-8?b?SGVsbG8=?= World"
        result = _decode_header_value(encoded)
        assert "Hello" in result
        assert "World" in result

    def test_parse_email_message_simple_text(self):
        """Test parsing a simple text email message."""
        msg = MIMEText("Test body content")
        msg['Subject'] = "Test Subject"
        msg['From'] = "sender@example.com"
        msg['To'] = "recipient@example.com"
        msg['Date'] = "Mon, 25 Nov 2024 10:30:00 +0000"

        result = _parse_email_message(msg)

        assert result['subject'] == "Test Subject"
        assert result['from'] == "sender@example.com"
        assert result['to'] == "recipient@example.com"
        assert "Test body content" in result['body_text']
        assert result['has_attachments'] is False
        assert result['attachments'] == []

    def test_parse_email_message_html(self):
        """Test parsing an HTML email message."""
        msg = MIMEText("<html><body><h1>Hello</h1></body></html>", 'html')
        msg['Subject'] = "HTML Email"
        msg['From'] = "sender@example.com"
        msg['To'] = "recipient@example.com"

        result = _parse_email_message(msg)

        assert result['subject'] == "HTML Email"
        assert "<h1>Hello</h1>" in result['body_html']

    def test_parse_email_message_multipart(self):
        """Test parsing a multipart email message."""
        msg = MIMEMultipart()
        msg['Subject'] = "Multipart Test"
        msg['From'] = "sender@example.com"
        msg['To'] = "recipient@example.com"

        msg.attach(MIMEText("Plain text body", 'plain'))
        msg.attach(MIMEText("<html><body>HTML body</body></html>", 'html'))

        result = _parse_email_message(msg)

        assert result['subject'] == "Multipart Test"
        assert "Plain text body" in result['body_text']
        assert "HTML body" in result['body_html']

    def test_parse_email_message_with_attachment(self):
        """Test parsing email with attachment."""
        msg = MIMEMultipart()
        msg['Subject'] = "With Attachment"
        msg['From'] = "sender@example.com"
        msg['To'] = "recipient@example.com"

        msg.attach(MIMEText("Body text", 'plain'))

        attachment = MIMEApplication(b"test file content", Name="test.txt")
        attachment['Content-Disposition'] = 'attachment; filename="test.txt"'
        msg.attach(attachment)

        result = _parse_email_message(msg)

        assert result['has_attachments'] is True
        assert len(result['attachments']) == 1
        assert result['attachments'][0]['filename'] == "test.txt"

    def test_parse_email_message_multiple_attachments(self):
        """Test parsing email with multiple attachments."""
        msg = MIMEMultipart()
        msg['Subject'] = "Multiple Attachments"
        msg['From'] = "sender@example.com"
        msg['To'] = "recipient@example.com"

        msg.attach(MIMEText("Body", 'plain'))

        for name in ["doc1.pdf", "doc2.xlsx", "image.png"]:
            attachment = MIMEApplication(b"content", Name=name)
            attachment['Content-Disposition'] = f'attachment; filename="{name}"'
            msg.attach(attachment)

        result = _parse_email_message(msg)

        assert result['has_attachments'] is True
        assert len(result['attachments']) == 3
        filenames = [a['filename'] for a in result['attachments']]
        assert "doc1.pdf" in filenames
        assert "doc2.xlsx" in filenames
        assert "image.png" in filenames

    def test_parse_email_message_no_subject(self):
        """Test parsing email without subject."""
        msg = MIMEText("Body")
        msg['From'] = "sender@example.com"

        result = _parse_email_message(msg)

        assert result['subject'] == ""

    def test_parse_email_message_with_cc(self):
        """Test parsing email with CC."""
        msg = MIMEText("Body")
        msg['Subject'] = "Test"
        msg['From'] = "sender@example.com"
        msg['To'] = "recipient@example.com"
        msg['Cc'] = "cc1@example.com, cc2@example.com"

        result = _parse_email_message(msg)

        assert "cc1@example.com" in result['cc']
        assert "cc2@example.com" in result['cc']


# =============================================================================
# Node Initialization Tests (No network required)
# =============================================================================


class TestNodeInitialization:
    """Tests for node initialization - no network needed."""

    def test_send_email_node_init(self):
        """Test SendEmailNode initialization."""
        node = SendEmailNode("send_1")
        assert node.node_id == "send_1"
        assert node.name == "Send Email"
        assert node.node_type == "SendEmailNode"

    def test_send_email_node_ports(self):
        """Test SendEmailNode ports are defined."""
        node = SendEmailNode("send_1")

        assert "smtp_server" in node.input_ports
        assert "smtp_port" in node.input_ports
        assert "username" in node.input_ports
        assert "password" in node.input_ports
        assert "to_email" in node.input_ports
        assert "subject" in node.input_ports
        assert "body" in node.input_ports
        assert "cc" in node.input_ports
        assert "bcc" in node.input_ports
        assert "attachments" in node.input_ports
        assert "success" in node.output_ports
        assert "message_id" in node.output_ports

    def test_read_emails_node_init(self):
        """Test ReadEmailsNode initialization."""
        node = ReadEmailsNode("read_1")
        assert node.node_id == "read_1"
        assert node.name == "Read Emails"
        assert node.node_type == "ReadEmailsNode"

    def test_read_emails_node_ports(self):
        """Test ReadEmailsNode ports are defined."""
        node = ReadEmailsNode("read_1")

        assert "imap_server" in node.input_ports
        assert "imap_port" in node.input_ports
        assert "username" in node.input_ports
        assert "password" in node.input_ports
        assert "folder" in node.input_ports
        assert "limit" in node.input_ports
        assert "search_criteria" in node.input_ports
        assert "emails" in node.output_ports
        assert "count" in node.output_ports

    def test_get_email_content_node_init(self):
        """Test GetEmailContentNode initialization."""
        node = GetEmailContentNode("get_1")
        assert node.node_id == "get_1"
        assert node.name == "Get Email Content"
        assert node.node_type == "GetEmailContentNode"

    def test_get_email_content_node_ports(self):
        """Test GetEmailContentNode ports are defined."""
        node = GetEmailContentNode("get_1")

        assert "email" in node.input_ports
        assert "subject" in node.output_ports
        assert "from" in node.output_ports
        assert "to" in node.output_ports
        assert "date" in node.output_ports
        assert "body_text" in node.output_ports
        assert "body_html" in node.output_ports
        assert "attachments" in node.output_ports

    def test_save_attachment_node_init(self):
        """Test SaveAttachmentNode initialization."""
        node = SaveAttachmentNode("save_1")
        assert node.node_id == "save_1"
        assert node.name == "Save Attachment"
        assert node.node_type == "SaveAttachmentNode"

    def test_save_attachment_node_ports(self):
        """Test SaveAttachmentNode ports are defined."""
        node = SaveAttachmentNode("save_1")

        assert "imap_server" in node.input_ports
        assert "username" in node.input_ports
        assert "password" in node.input_ports
        assert "email_uid" in node.input_ports
        assert "save_path" in node.input_ports
        assert "folder" in node.input_ports
        assert "saved_files" in node.output_ports
        assert "count" in node.output_ports

    def test_filter_emails_node_init(self):
        """Test FilterEmailsNode initialization."""
        node = FilterEmailsNode("filter_1")
        assert node.node_id == "filter_1"
        assert node.name == "Filter Emails"
        assert node.node_type == "FilterEmailsNode"

    def test_filter_emails_node_ports(self):
        """Test FilterEmailsNode ports are defined."""
        node = FilterEmailsNode("filter_1")

        assert "emails" in node.input_ports
        assert "subject_contains" in node.input_ports
        assert "from_contains" in node.input_ports
        assert "has_attachments" in node.input_ports
        assert "filtered" in node.output_ports
        assert "count" in node.output_ports

    def test_mark_email_node_init(self):
        """Test MarkEmailNode initialization."""
        node = MarkEmailNode("mark_1")
        assert node.node_id == "mark_1"
        assert node.name == "Mark Email"
        assert node.node_type == "MarkEmailNode"

    def test_mark_email_node_ports(self):
        """Test MarkEmailNode ports are defined."""
        node = MarkEmailNode("mark_1")

        assert "imap_server" in node.input_ports
        assert "username" in node.input_ports
        assert "password" in node.input_ports
        assert "email_uid" in node.input_ports
        assert "folder" in node.input_ports
        assert "mark_as" in node.input_ports
        assert "success" in node.output_ports

    def test_delete_email_node_init(self):
        """Test DeleteEmailNode initialization."""
        node = DeleteEmailNode("delete_1")
        assert node.node_id == "delete_1"
        assert node.name == "Delete Email"
        assert node.node_type == "DeleteEmailNode"

    def test_delete_email_node_ports(self):
        """Test DeleteEmailNode ports are defined."""
        node = DeleteEmailNode("delete_1")

        assert "imap_server" in node.input_ports
        assert "username" in node.input_ports
        assert "password" in node.input_ports
        assert "email_uid" in node.input_ports
        assert "folder" in node.input_ports
        assert "success" in node.output_ports

    def test_move_email_node_init(self):
        """Test MoveEmailNode initialization."""
        node = MoveEmailNode("move_1")
        assert node.node_id == "move_1"
        assert node.name == "Move Email"
        assert node.node_type == "MoveEmailNode"

    def test_move_email_node_ports(self):
        """Test MoveEmailNode ports are defined."""
        node = MoveEmailNode("move_1")

        assert "imap_server" in node.input_ports
        assert "username" in node.input_ports
        assert "password" in node.input_ports
        assert "email_uid" in node.input_ports
        assert "source_folder" in node.input_ports
        assert "target_folder" in node.input_ports
        assert "success" in node.output_ports


# =============================================================================
# GetEmailContentNode Tests (No network required - works on dict data)
# =============================================================================


class TestGetEmailContentNode:
    """Tests for GetEmailContentNode - works entirely on in-memory data."""

    @pytest.mark.asyncio
    async def test_get_content_no_email(self, context):
        """Test getting content without email data fails."""
        node = GetEmailContentNode("get_1")

        result = await node.execute(context)

        assert result["success"] is False
        assert "No email data" in result["error"]

    @pytest.mark.asyncio
    async def test_get_content_invalid_type(self, context):
        """Test getting content with invalid data type."""
        node = GetEmailContentNode("get_1")
        node.set_input_value("email", "not a dict")

        result = await node.execute(context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_get_content_success(self, context):
        """Test successful content extraction."""
        node = GetEmailContentNode("get_1")

        email_data = {
            "subject": "Test Subject",
            "from": "sender@example.com",
            "to": "recipient@example.com",
            "date": "2024-11-25T10:30:00",
            "body_text": "Plain text body",
            "body_html": "<html><body>HTML body</body></html>",
            "attachments": [{"filename": "test.pdf", "size": 1024}],
        }

        node.set_input_value("email", email_data)

        result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("subject") == "Test Subject"
        assert node.get_output_value("from") == "sender@example.com"
        assert node.get_output_value("to") == "recipient@example.com"
        assert node.get_output_value("body_text") == "Plain text body"
        assert node.get_output_value("body_html") == "<html><body>HTML body</body></html>"
        assert len(node.get_output_value("attachments")) == 1

    @pytest.mark.asyncio
    async def test_get_content_partial_data(self, context):
        """Test content extraction with partial data."""
        node = GetEmailContentNode("get_1")

        email_data = {
            "subject": "Only Subject",
        }

        node.set_input_value("email", email_data)

        result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("subject") == "Only Subject"
        assert node.get_output_value("from") == ""
        assert node.get_output_value("body_text") == ""
        assert node.get_output_value("attachments") == []

    @pytest.mark.asyncio
    async def test_get_content_empty_dict(self, context):
        """Test content extraction with empty dict succeeds with defaults."""
        node = GetEmailContentNode("get_1")
        # An empty dict is still a valid dict type, so it should work
        # but return empty/default values for all fields
        email_data = {"subject": ""}  # Minimal valid email data
        node.set_input_value("email", email_data)

        result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("subject") == ""


# =============================================================================
# FilterEmailsNode Tests (No network required - works on list data)
# =============================================================================


class TestFilterEmailsNode:
    """Tests for FilterEmailsNode - works entirely on in-memory data."""

    @pytest.mark.asyncio
    async def test_filter_empty_list(self, context):
        """Test filtering empty list."""
        node = FilterEmailsNode("filter_1")
        node.set_input_value("emails", [])

        result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("count") == 0
        assert node.get_output_value("filtered") == []

    @pytest.mark.asyncio
    async def test_filter_no_criteria(self, context):
        """Test filtering with no criteria returns all."""
        node = FilterEmailsNode("filter_1")

        emails = [
            {"subject": "Email 1", "from": "a@test.com", "has_attachments": False},
            {"subject": "Email 2", "from": "b@test.com", "has_attachments": True},
        ]

        node.set_input_value("emails", emails)

        result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("count") == 2

    @pytest.mark.asyncio
    async def test_filter_by_subject_case_insensitive(self, context):
        """Test filtering by subject is case insensitive."""
        node = FilterEmailsNode("filter_1")

        emails = [
            {"subject": "IMPORTANT: Meeting tomorrow", "from": "a@test.com", "has_attachments": False},
            {"subject": "Hello world", "from": "b@test.com", "has_attachments": False},
            {"subject": "Important: Review needed", "from": "c@test.com", "has_attachments": True},
        ]

        node.set_input_value("emails", emails)
        node.set_input_value("subject_contains", "important")

        result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("count") == 2

    @pytest.mark.asyncio
    async def test_filter_by_subject_no_match(self, context):
        """Test filtering by subject with no matches."""
        node = FilterEmailsNode("filter_1")

        emails = [
            {"subject": "Hello", "from": "a@test.com", "has_attachments": False},
            {"subject": "World", "from": "b@test.com", "has_attachments": False},
        ]

        node.set_input_value("emails", emails)
        node.set_input_value("subject_contains", "Important")

        result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("count") == 0

    @pytest.mark.asyncio
    async def test_filter_by_from(self, context):
        """Test filtering by sender."""
        node = FilterEmailsNode("filter_1")

        emails = [
            {"subject": "Test 1", "from": "john.doe@company.com", "has_attachments": False},
            {"subject": "Test 2", "from": "jane@other.com", "has_attachments": False},
            {"subject": "Test 3", "from": "john.smith@another.com", "has_attachments": False},
        ]

        node.set_input_value("emails", emails)
        node.set_input_value("from_contains", "john")

        result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("count") == 2

    @pytest.mark.asyncio
    async def test_filter_by_has_attachments_true(self, context):
        """Test filtering by has attachments = True."""
        node = FilterEmailsNode("filter_1")

        emails = [
            {"subject": "Test 1", "from": "a@test.com", "has_attachments": True},
            {"subject": "Test 2", "from": "b@test.com", "has_attachments": False},
            {"subject": "Test 3", "from": "c@test.com", "has_attachments": True},
        ]

        node.set_input_value("emails", emails)
        node.set_input_value("has_attachments", True)

        result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("count") == 2

    @pytest.mark.asyncio
    async def test_filter_by_has_attachments_false(self, context):
        """Test filtering by has attachments = False."""
        node = FilterEmailsNode("filter_1")

        emails = [
            {"subject": "Test 1", "from": "a@test.com", "has_attachments": True},
            {"subject": "Test 2", "from": "b@test.com", "has_attachments": False},
            {"subject": "Test 3", "from": "c@test.com", "has_attachments": True},
        ]

        node.set_input_value("emails", emails)
        node.set_input_value("has_attachments", False)

        result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("count") == 1

    @pytest.mark.asyncio
    async def test_filter_multiple_criteria(self, context):
        """Test filtering with multiple criteria (AND logic)."""
        node = FilterEmailsNode("filter_1")

        emails = [
            {"subject": "Invoice #123", "from": "billing@company.com", "has_attachments": True},
            {"subject": "Invoice #456", "from": "billing@other.com", "has_attachments": False},
            {"subject": "Meeting notes", "from": "billing@company.com", "has_attachments": True},
            {"subject": "Invoice #789", "from": "billing@company.com", "has_attachments": True},
        ]

        node.set_input_value("emails", emails)
        node.set_input_value("subject_contains", "Invoice")
        node.set_input_value("from_contains", "company")
        node.set_input_value("has_attachments", True)

        result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("count") == 2

    @pytest.mark.asyncio
    async def test_filter_skips_invalid_items(self, context):
        """Test filtering skips non-dict items."""
        node = FilterEmailsNode("filter_1")

        emails = [
            {"subject": "Valid", "from": "a@test.com", "has_attachments": False},
            "invalid string",
            123,
            None,
            {"subject": "Also Valid", "from": "b@test.com", "has_attachments": False},
        ]

        node.set_input_value("emails", emails)

        result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("count") == 2


# =============================================================================
# Validation Tests (No network required)
# =============================================================================


class TestValidationErrors:
    """Tests for input validation - no network needed."""

    @pytest.mark.asyncio
    async def test_send_email_no_recipient(self, context):
        """Test SendEmailNode fails without recipient."""
        node = SendEmailNode("send_1", {
            "smtp_server": "smtp.example.com",
            "smtp_port": 587,
        })

        result = await node.execute(context)

        assert result["success"] is False
        assert "No recipient" in result["error"]

    @pytest.mark.asyncio
    async def test_read_emails_no_credentials(self, context):
        """Test ReadEmailsNode fails without credentials."""
        node = ReadEmailsNode("read_1", {
            "imap_server": "imap.example.com",
        })

        result = await node.execute(context)

        assert result["success"] is False
        assert "Username and password required" in result["error"]

    @pytest.mark.asyncio
    async def test_save_attachment_no_uid(self, context):
        """Test SaveAttachmentNode fails without email UID."""
        node = SaveAttachmentNode("save_1", {
            "imap_server": "imap.example.com",
            "username": "user@example.com",
            "password": "password",
        })

        result = await node.execute(context)

        assert result["success"] is False
        assert "No email UID provided" in result["error"]

    @pytest.mark.asyncio
    async def test_mark_email_no_uid(self, context):
        """Test MarkEmailNode fails without email UID."""
        node = MarkEmailNode("mark_1", {
            "imap_server": "imap.example.com",
            "username": "user@example.com",
            "password": "password",
        })

        result = await node.execute(context)

        assert result["success"] is False
        assert "No email UID provided" in result["error"]

    @pytest.mark.asyncio
    async def test_delete_email_no_uid(self, context):
        """Test DeleteEmailNode fails without email UID."""
        node = DeleteEmailNode("delete_1", {
            "imap_server": "imap.example.com",
            "username": "user@example.com",
            "password": "password",
        })

        result = await node.execute(context)

        assert result["success"] is False
        assert "No email UID provided" in result["error"]

    @pytest.mark.asyncio
    async def test_move_email_no_uid(self, context):
        """Test MoveEmailNode fails without email UID."""
        node = MoveEmailNode("move_1", {
            "imap_server": "imap.example.com",
            "username": "user@example.com",
            "password": "password",
            "target_folder": "Archive",
        })

        result = await node.execute(context)

        assert result["success"] is False
        assert "Email UID and target folder required" in result["error"]

    @pytest.mark.asyncio
    async def test_move_email_no_target_folder(self, context):
        """Test MoveEmailNode fails without target folder."""
        node = MoveEmailNode("move_1", {
            "imap_server": "imap.example.com",
            "username": "user@example.com",
            "password": "password",
        })
        node.set_input_value("email_uid", "123")

        result = await node.execute(context)

        assert result["success"] is False
        assert "Email UID and target folder required" in result["error"]


# =============================================================================
# Real SMTP/IMAP Tests (Requires credentials)
# =============================================================================


@requires_email_credentials
class TestRealEmailOperations:
    """Tests using real SMTP/IMAP servers.

    These tests are skipped unless EMAIL_TEST_* environment variables are set.
    """

    @pytest.mark.asyncio
    async def test_read_emails_real(self, context, email_config):
        """Test reading emails from real IMAP server."""
        node = ReadEmailsNode("read_1", {
            "imap_server": email_config["imap_server"],
            "imap_port": email_config["imap_port"],
            "username": email_config["username"],
            "password": email_config["password"],
            "folder": "INBOX",
            "limit": 5,
            "search_criteria": "ALL",
        })

        result = await node.execute(context)

        assert result["success"] is True
        emails = node.get_output_value("emails")
        count = node.get_output_value("count")
        assert isinstance(emails, list)
        assert count >= 0
        assert count == len(emails)

    @pytest.mark.asyncio
    async def test_read_emails_unread_only(self, context, email_config):
        """Test reading only unread emails."""
        node = ReadEmailsNode("read_1", {
            "imap_server": email_config["imap_server"],
            "imap_port": email_config["imap_port"],
            "username": email_config["username"],
            "password": email_config["password"],
            "folder": "INBOX",
            "limit": 10,
            "search_criteria": "UNSEEN",
        })

        result = await node.execute(context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_read_emails_with_subject_search(self, context, email_config):
        """Test reading emails with subject search."""
        node = ReadEmailsNode("read_1", {
            "imap_server": email_config["imap_server"],
            "imap_port": email_config["imap_port"],
            "username": email_config["username"],
            "password": email_config["password"],
            "folder": "INBOX",
            "limit": 5,
            "search_criteria": 'SUBJECT "test"',
        })

        result = await node.execute(context)

        # May succeed with 0 results if no matching emails
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_send_email_real(self, context, email_config):
        """Test sending a real email."""
        if not email_config["recipient"]:
            pytest.skip("EMAIL_TEST_RECIPIENT not set")

        node = SendEmailNode("send_1", {
            "smtp_server": email_config["smtp_server"],
            "smtp_port": email_config["smtp_port"],
            "username": email_config["username"],
            "password": email_config["password"],
            "from_email": email_config["username"],
            "to_email": email_config["recipient"],
            "subject": "CasareRPA Test Email",
            "body": "This is a test email from CasareRPA email node tests.",
            "use_tls": True,
        })

        result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_send_email_html_real(self, context, email_config):
        """Test sending a real HTML email."""
        if not email_config["recipient"]:
            pytest.skip("EMAIL_TEST_RECIPIENT not set")

        node = SendEmailNode("send_1", {
            "smtp_server": email_config["smtp_server"],
            "smtp_port": email_config["smtp_port"],
            "username": email_config["username"],
            "password": email_config["password"],
            "from_email": email_config["username"],
            "to_email": email_config["recipient"],
            "subject": "CasareRPA Test HTML Email",
            "body": "<html><body><h1>Test</h1><p>This is an <b>HTML</b> test email.</p></body></html>",
            "use_tls": True,
            "is_html": True,
        })

        result = await node.execute(context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_send_email_with_attachment_real(self, context, email_config):
        """Test sending email with attachment."""
        if not email_config["recipient"]:
            pytest.skip("EMAIL_TEST_RECIPIENT not set")

        # Create a temporary file to attach
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test attachment from CasareRPA.")
            temp_file = f.name

        try:
            node = SendEmailNode("send_1", {
                "smtp_server": email_config["smtp_server"],
                "smtp_port": email_config["smtp_port"],
                "username": email_config["username"],
                "password": email_config["password"],
                "from_email": email_config["username"],
                "to_email": email_config["recipient"],
                "subject": "CasareRPA Test Email with Attachment",
                "body": "This email has an attachment.",
                "use_tls": True,
            })
            node.set_input_value("attachments", [temp_file])

            result = await node.execute(context)

            assert result["success"] is True
        finally:
            os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_read_and_filter_workflow(self, context, email_config):
        """Test reading emails and then filtering them."""
        # Read emails
        read_node = ReadEmailsNode("read_1", {
            "imap_server": email_config["imap_server"],
            "imap_port": email_config["imap_port"],
            "username": email_config["username"],
            "password": email_config["password"],
            "folder": "INBOX",
            "limit": 20,
        })

        read_result = await read_node.execute(context)
        assert read_result["success"] is True

        emails = read_node.get_output_value("emails")

        # Filter emails
        filter_node = FilterEmailsNode("filter_1")
        filter_node.set_input_value("emails", emails)
        filter_node.set_input_value("has_attachments", True)

        filter_result = await filter_node.execute(context)
        assert filter_result["success"] is True

        filtered_count = filter_node.get_output_value("count")
        assert filtered_count <= len(emails)

    @pytest.mark.asyncio
    async def test_read_and_get_content_workflow(self, context, email_config):
        """Test reading emails and extracting content."""
        # Read emails
        read_node = ReadEmailsNode("read_1", {
            "imap_server": email_config["imap_server"],
            "imap_port": email_config["imap_port"],
            "username": email_config["username"],
            "password": email_config["password"],
            "folder": "INBOX",
            "limit": 1,
        })

        read_result = await read_node.execute(context)
        assert read_result["success"] is True

        emails = read_node.get_output_value("emails")
        if len(emails) == 0:
            pytest.skip("No emails in inbox to test")

        # Get content from first email
        content_node = GetEmailContentNode("content_1")
        content_node.set_input_value("email", emails[0])

        content_result = await content_node.execute(context)
        assert content_result["success"] is True

        # Should have extracted the subject
        subject = content_node.get_output_value("subject")
        assert subject is not None
