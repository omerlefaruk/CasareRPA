"""
Comprehensive tests for email nodes.

Tests 8 email nodes:
- SendEmailNode, ReadEmailsNode, GetEmailContentNode, FilterEmailsNode
- SaveAttachmentNode, MarkEmailNode, DeleteEmailNode, MoveEmailNode

Mocks SMTP and IMAP operations.
"""

import pytest
import tempfile
import email
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.nodes.email_nodes import (
    SendEmailNode,
    ReadEmailsNode,
    GetEmailContentNode,
    FilterEmailsNode,
    SaveAttachmentNode,
    MarkEmailNode,
    DeleteEmailNode,
    MoveEmailNode,
    _decode_header_value,
    _parse_email_message,
)


class TestSendEmailNode:
    """Tests for SendEmailNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        """Create mock execution context."""
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    @patch("casare_rpa.nodes.email_nodes.smtplib.SMTP")
    async def test_send_email_success(self, mock_smtp, execution_context) -> None:
        """Test successful email sending."""
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        node = SendEmailNode(
            node_id="test_send",
            config={
                "smtp_server": "smtp.test.com",
                "smtp_port": 587,
                "use_tls": True,
                "use_ssl": False,
            },
        )
        node.set_input_value("from_email", "sender@test.com")
        node.set_input_value("to_email", "recipient@test.com")
        node.set_input_value("subject", "Test Subject")
        node.set_input_value("body", "Test body content")
        node.set_input_value("username", "user")
        node.set_input_value("password", "pass")

        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_smtp.assert_called_once()
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user", "pass")
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()

    @pytest.mark.asyncio
    @patch("casare_rpa.nodes.email_nodes.smtplib.SMTP_SSL")
    async def test_send_email_ssl(self, mock_smtp_ssl, execution_context) -> None:
        """Test email sending with SSL."""
        mock_server = MagicMock()
        mock_smtp_ssl.return_value = mock_server

        node = SendEmailNode(
            node_id="test_send_ssl",
            config={
                "smtp_server": "smtp.test.com",
                "smtp_port": 465,
                "use_tls": False,
                "use_ssl": True,
            },
        )
        node.set_input_value("from_email", "sender@test.com")
        node.set_input_value("to_email", "recipient@test.com")
        node.set_input_value("subject", "Test Subject")
        node.set_input_value("body", "Test body content")

        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_smtp_ssl.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_no_recipient_error(self, execution_context) -> None:
        """Test error when no recipient provided."""
        node = SendEmailNode(node_id="test_send_no_to")
        node.set_input_value("from_email", "sender@test.com")
        node.set_input_value("to_email", "")
        node.set_input_value("subject", "Test")
        node.set_input_value("body", "Test")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "recipient" in result["error"].lower()

    @pytest.mark.asyncio
    @patch("casare_rpa.nodes.email_nodes.smtplib.SMTP")
    async def test_send_email_with_cc_bcc(self, mock_smtp, execution_context) -> None:
        """Test email with CC and BCC recipients."""
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        node = SendEmailNode(node_id="test_send_cc")
        node.set_input_value("from_email", "sender@test.com")
        node.set_input_value("to_email", "recipient@test.com")
        node.set_input_value("cc", "cc1@test.com, cc2@test.com")
        node.set_input_value("bcc", "bcc@test.com")
        node.set_input_value("subject", "Test")
        node.set_input_value("body", "Test")

        result = await node.execute(execution_context)

        assert result["success"] is True
        # Check all recipients included
        call_args = mock_server.sendmail.call_args
        recipients = call_args[0][1]
        assert len(recipients) == 4

    @pytest.mark.asyncio
    @patch("casare_rpa.nodes.email_nodes.smtplib.SMTP")
    async def test_send_email_html_body(self, mock_smtp, execution_context) -> None:
        """Test HTML email body."""
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        node = SendEmailNode(
            node_id="test_send_html", config={"is_html": True, "use_tls": False}
        )
        node.set_input_value("from_email", "sender@test.com")
        node.set_input_value("to_email", "recipient@test.com")
        node.set_input_value("subject", "Test")
        node.set_input_value("body", "<h1>HTML Content</h1>")

        result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    @patch("casare_rpa.nodes.email_nodes.smtplib.SMTP")
    async def test_send_email_auth_failure(self, mock_smtp, execution_context) -> None:
        """Test authentication failure handling."""
        import smtplib

        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(
            535, b"Auth failed"
        )
        mock_smtp.return_value = mock_server

        node = SendEmailNode(node_id="test_send_auth_fail")
        node.set_input_value("from_email", "sender@test.com")
        node.set_input_value("to_email", "recipient@test.com")
        node.set_input_value("subject", "Test")
        node.set_input_value("body", "Test")
        node.set_input_value("username", "user")
        node.set_input_value("password", "wrong")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "authentication" in result["error"].lower()

    def test_send_email_node_ports(self) -> None:
        """Test SendEmailNode follows ExecutionResult pattern."""
        node = SendEmailNode(node_id="test_ports")
        assert node.node_type == "SendEmailNode"
        assert "exec_in" in [p.name for p in node.input_ports.values()]
        assert "exec_out" in [p.name for p in node.output_ports.values()]
        assert "success" in [p.name for p in node.output_ports.values()]


class TestReadEmailsNode:
    """Tests for ReadEmailsNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        """Create mock execution context."""
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    def _create_mock_email(self, subject, from_addr, body):
        """Create a mock email message bytes."""
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = "test@test.com"
        return msg.as_bytes()

    @pytest.mark.asyncio
    @patch("casare_rpa.nodes.email_nodes.imaplib.IMAP4_SSL")
    async def test_read_emails_success(self, mock_imap, execution_context) -> None:
        """Test successful email reading."""
        mock_mail = MagicMock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", None)
        mock_mail.select.return_value = ("OK", [b"5"])
        mock_mail.search.return_value = ("OK", [b"1 2 3"])

        email_data = self._create_mock_email("Test Subject", "sender@test.com", "Body")
        mock_mail.fetch.return_value = ("OK", [(b"1", email_data)])

        node = ReadEmailsNode(node_id="test_read")
        node.set_input_value("imap_server", "imap.test.com")
        node.set_input_value("username", "user@test.com")
        node.set_input_value("password", "pass")
        node.set_input_value("folder", "INBOX")
        node.set_input_value("limit", 10)

        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_mail.login.assert_called_once()
        mock_mail.select.assert_called_once_with("INBOX")
        mock_mail.search.assert_called_once()
        mock_mail.logout.assert_called_once()

    @pytest.mark.asyncio
    async def test_read_emails_no_credentials_error(self, execution_context) -> None:
        """Test error when credentials missing."""
        node = ReadEmailsNode(node_id="test_read_no_creds")
        node.set_input_value("imap_server", "imap.test.com")
        node.set_input_value("username", "")
        node.set_input_value("password", "")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    @patch("casare_rpa.nodes.email_nodes.imaplib.IMAP4_SSL")
    async def test_read_emails_with_search_criteria(
        self, mock_imap, execution_context
    ) -> None:
        """Test reading emails with custom search criteria."""
        mock_mail = MagicMock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", None)
        mock_mail.select.return_value = ("OK", [b"5"])
        mock_mail.search.return_value = ("OK", [b""])
        mock_mail.fetch.return_value = ("OK", [])

        node = ReadEmailsNode(node_id="test_read_search")
        node.set_input_value("imap_server", "imap.test.com")
        node.set_input_value("username", "user")
        node.set_input_value("password", "pass")
        node.set_input_value("search_criteria", "UNSEEN")

        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_mail.search.assert_called_once_with(None, "UNSEEN")


class TestGetEmailContentNode:
    """Tests for GetEmailContentNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        """Create mock execution context."""
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_get_email_content(self, execution_context) -> None:
        """Test extracting email content."""
        email_data = {
            "subject": "Test Subject",
            "from": "sender@test.com",
            "to": "recipient@test.com",
            "date": "2024-01-15T10:30:00",
            "body_text": "Plain text body",
            "body_html": "<p>HTML body</p>",
            "attachments": [{"filename": "doc.pdf", "size": 1024}],
        }

        node = GetEmailContentNode(node_id="test_content")
        node.set_input_value("email", email_data)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("subject") == "Test Subject"
        assert node.get_output_value("from") == "sender@test.com"
        assert node.get_output_value("body_text") == "Plain text body"
        assert len(node.get_output_value("attachments")) == 1

    @pytest.mark.asyncio
    async def test_get_email_content_no_data_error(self, execution_context) -> None:
        """Test error when no email data provided."""
        node = GetEmailContentNode(node_id="test_no_data")
        node.set_input_value("email", None)

        result = await node.execute(execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_get_email_content_invalid_data_error(
        self, execution_context
    ) -> None:
        """Test error when email data is invalid type."""
        node = GetEmailContentNode(node_id="test_invalid")
        node.set_input_value("email", "not a dict")

        result = await node.execute(execution_context)

        assert result["success"] is False


class TestFilterEmailsNode:
    """Tests for FilterEmailsNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        """Create mock execution context."""
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.fixture
    def sample_emails(self) -> None:
        """Create sample email list for filtering."""
        return [
            {
                "subject": "Invoice #123",
                "from": "billing@company.com",
                "has_attachments": True,
            },
            {
                "subject": "Meeting Request",
                "from": "manager@company.com",
                "has_attachments": False,
            },
            {
                "subject": "Invoice #456",
                "from": "billing@company.com",
                "has_attachments": True,
            },
            {
                "subject": "Newsletter",
                "from": "newsletter@external.com",
                "has_attachments": False,
            },
        ]

    @pytest.mark.asyncio
    async def test_filter_by_subject(self, execution_context, sample_emails) -> None:
        """Test filtering emails by subject."""
        node = FilterEmailsNode(node_id="test_filter_subject")
        node.set_input_value("emails", sample_emails)
        node.set_input_value("subject_contains", "Invoice")

        result = await node.execute(execution_context)

        assert result["success"] is True
        filtered = node.get_output_value("filtered")
        assert len(filtered) == 2
        assert all("Invoice" in e["subject"] for e in filtered)

    @pytest.mark.asyncio
    async def test_filter_by_sender(self, execution_context, sample_emails) -> None:
        """Test filtering emails by sender."""
        node = FilterEmailsNode(node_id="test_filter_from")
        node.set_input_value("emails", sample_emails)
        node.set_input_value("from_contains", "billing")

        result = await node.execute(execution_context)

        assert result["success"] is True
        filtered = node.get_output_value("filtered")
        assert len(filtered) == 2
        assert all("billing" in e["from"] for e in filtered)

    @pytest.mark.asyncio
    async def test_filter_by_attachments(
        self, execution_context, sample_emails
    ) -> None:
        """Test filtering emails with attachments."""
        node = FilterEmailsNode(node_id="test_filter_attach")
        node.set_input_value("emails", sample_emails)
        node.set_input_value("has_attachments", True)

        result = await node.execute(execution_context)

        assert result["success"] is True
        filtered = node.get_output_value("filtered")
        assert len(filtered) == 2
        assert all(e["has_attachments"] for e in filtered)

    @pytest.mark.asyncio
    async def test_filter_combined_criteria(
        self, execution_context, sample_emails
    ) -> None:
        """Test filtering with multiple criteria."""
        node = FilterEmailsNode(node_id="test_filter_combined")
        node.set_input_value("emails", sample_emails)
        node.set_input_value("subject_contains", "Invoice")
        node.set_input_value("from_contains", "billing")

        result = await node.execute(execution_context)

        assert result["success"] is True
        filtered = node.get_output_value("filtered")
        assert len(filtered) == 2

    @pytest.mark.asyncio
    async def test_filter_case_insensitive(
        self, execution_context, sample_emails
    ) -> None:
        """Test filter is case-insensitive."""
        node = FilterEmailsNode(node_id="test_filter_case")
        node.set_input_value("emails", sample_emails)
        node.set_input_value("subject_contains", "invoice")  # lowercase

        result = await node.execute(execution_context)

        assert result["success"] is True
        filtered = node.get_output_value("filtered")
        assert len(filtered) == 2

    @pytest.mark.asyncio
    async def test_filter_empty_result(self, execution_context, sample_emails) -> None:
        """Test filter returning no matches."""
        node = FilterEmailsNode(node_id="test_filter_empty")
        node.set_input_value("emails", sample_emails)
        node.set_input_value("subject_contains", "NonexistentSubject")

        result = await node.execute(execution_context)

        assert result["success"] is True
        filtered = node.get_output_value("filtered")
        assert len(filtered) == 0


class TestSaveAttachmentNode:
    """Tests for SaveAttachmentNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        """Create mock execution context."""
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.fixture
    def temp_dir(self) -> None:
        """Create temp directory for attachments."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_save_attachment_no_uid_error(
        self, execution_context, temp_dir
    ) -> None:
        """Test error when no email UID provided."""
        node = SaveAttachmentNode(node_id="test_save_no_uid")
        node.set_input_value("imap_server", "imap.test.com")
        node.set_input_value("username", "user")
        node.set_input_value("password", "pass")
        node.set_input_value("email_uid", "")
        node.set_input_value("save_path", temp_dir)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "uid" in result["error"].lower()

    @pytest.mark.asyncio
    @patch("casare_rpa.nodes.email_nodes.imaplib.IMAP4_SSL")
    async def test_save_attachment_success(
        self, mock_imap, execution_context, temp_dir
    ) -> None:
        """Test successful attachment save."""
        # Create email with attachment
        msg = MIMEMultipart()
        msg["Subject"] = "Test"
        msg["From"] = "sender@test.com"

        from email.mime.application import MIMEApplication

        attachment = MIMEApplication(b"file content", Name="test.txt")
        attachment["Content-Disposition"] = 'attachment; filename="test.txt"'
        msg.attach(attachment)

        mock_mail = MagicMock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", None)
        mock_mail.select.return_value = ("OK", [b"1"])
        mock_mail.fetch.return_value = ("OK", [(b"1", msg.as_bytes())])

        node = SaveAttachmentNode(node_id="test_save")
        node.set_input_value("imap_server", "imap.test.com")
        node.set_input_value("username", "user")
        node.set_input_value("password", "pass")
        node.set_input_value("email_uid", "1")
        node.set_input_value("save_path", temp_dir)
        node.set_input_value("folder", "INBOX")

        result = await node.execute(execution_context)

        assert result["success"] is True
        saved_files = node.get_output_value("saved_files")
        assert len(saved_files) == 1
        assert Path(saved_files[0]).exists()


class TestMarkEmailNode:
    """Tests for MarkEmailNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        """Create mock execution context."""
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_mark_email_no_uid_error(self, execution_context) -> None:
        """Test error when no email UID provided."""
        node = MarkEmailNode(node_id="test_mark_no_uid")
        node.set_input_value("imap_server", "imap.test.com")
        node.set_input_value("username", "user")
        node.set_input_value("password", "pass")
        node.set_input_value("email_uid", "")
        node.set_input_value("mark_as", "read")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "uid" in result["error"].lower()

    @pytest.mark.asyncio
    @patch("casare_rpa.nodes.email_nodes.imaplib.IMAP4_SSL")
    async def test_mark_as_read(self, mock_imap, execution_context) -> None:
        """Test marking email as read."""
        mock_mail = MagicMock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", None)
        mock_mail.select.return_value = ("OK", [b"1"])
        mock_mail.store.return_value = ("OK", None)

        node = MarkEmailNode(node_id="test_mark_read")
        node.set_input_value("imap_server", "imap.test.com")
        node.set_input_value("username", "user")
        node.set_input_value("password", "pass")
        node.set_input_value("email_uid", "123")
        node.set_input_value("mark_as", "read")

        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_mail.store.assert_called_once_with(b"123", "+FLAGS", "\\Seen")

    @pytest.mark.asyncio
    @patch("casare_rpa.nodes.email_nodes.imaplib.IMAP4_SSL")
    async def test_mark_as_unread(self, mock_imap, execution_context) -> None:
        """Test marking email as unread."""
        mock_mail = MagicMock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", None)
        mock_mail.select.return_value = ("OK", [b"1"])
        mock_mail.store.return_value = ("OK", None)

        node = MarkEmailNode(node_id="test_mark_unread")
        node.set_input_value("imap_server", "imap.test.com")
        node.set_input_value("username", "user")
        node.set_input_value("password", "pass")
        node.set_input_value("email_uid", "123")
        node.set_input_value("mark_as", "unread")

        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_mail.store.assert_called_once_with(b"123", "-FLAGS", "\\Seen")

    @pytest.mark.asyncio
    @patch("casare_rpa.nodes.email_nodes.imaplib.IMAP4_SSL")
    async def test_mark_as_flagged(self, mock_imap, execution_context) -> None:
        """Test flagging email."""
        mock_mail = MagicMock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", None)
        mock_mail.select.return_value = ("OK", [b"1"])
        mock_mail.store.return_value = ("OK", None)

        node = MarkEmailNode(node_id="test_mark_flagged")
        node.set_input_value("imap_server", "imap.test.com")
        node.set_input_value("username", "user")
        node.set_input_value("password", "pass")
        node.set_input_value("email_uid", "123")
        node.set_input_value("mark_as", "flagged")

        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_mail.store.assert_called_once_with(b"123", "+FLAGS", "\\Flagged")


class TestDeleteEmailNode:
    """Tests for DeleteEmailNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        """Create mock execution context."""
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_delete_email_no_uid_error(self, execution_context) -> None:
        """Test error when no email UID provided."""
        node = DeleteEmailNode(node_id="test_delete_no_uid")
        node.set_input_value("imap_server", "imap.test.com")
        node.set_input_value("username", "user")
        node.set_input_value("password", "pass")
        node.set_input_value("email_uid", "")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "uid" in result["error"].lower()

    @pytest.mark.asyncio
    @patch("casare_rpa.nodes.email_nodes.imaplib.IMAP4_SSL")
    async def test_delete_email_success(self, mock_imap, execution_context) -> None:
        """Test successful email deletion."""
        mock_mail = MagicMock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", None)
        mock_mail.select.return_value = ("OK", [b"1"])
        mock_mail.store.return_value = ("OK", None)

        node = DeleteEmailNode(node_id="test_delete")
        node.set_input_value("imap_server", "imap.test.com")
        node.set_input_value("username", "user")
        node.set_input_value("password", "pass")
        node.set_input_value("email_uid", "123")
        node.set_input_value("folder", "INBOX")

        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_mail.store.assert_called_once_with(b"123", "+FLAGS", "\\Deleted")

    @pytest.mark.asyncio
    @patch("casare_rpa.nodes.email_nodes.imaplib.IMAP4_SSL")
    async def test_delete_email_permanent(self, mock_imap, execution_context) -> None:
        """Test permanent email deletion with expunge."""
        mock_mail = MagicMock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", None)
        mock_mail.select.return_value = ("OK", [b"1"])
        mock_mail.store.return_value = ("OK", None)

        node = DeleteEmailNode(node_id="test_delete_perm", config={"permanent": True})
        node.set_input_value("imap_server", "imap.test.com")
        node.set_input_value("username", "user")
        node.set_input_value("password", "pass")
        node.set_input_value("email_uid", "123")

        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_mail.expunge.assert_called_once()


class TestMoveEmailNode:
    """Tests for MoveEmailNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        """Create mock execution context."""
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_move_email_no_uid_error(self, execution_context) -> None:
        """Test error when no email UID provided."""
        node = MoveEmailNode(node_id="test_move_no_uid")
        node.set_input_value("imap_server", "imap.test.com")
        node.set_input_value("username", "user")
        node.set_input_value("password", "pass")
        node.set_input_value("email_uid", "")
        node.set_input_value("target_folder", "Archive")

        result = await node.execute(execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_move_email_no_target_error(self, execution_context) -> None:
        """Test error when no target folder provided."""
        node = MoveEmailNode(node_id="test_move_no_target")
        node.set_input_value("imap_server", "imap.test.com")
        node.set_input_value("username", "user")
        node.set_input_value("password", "pass")
        node.set_input_value("email_uid", "123")
        node.set_input_value("target_folder", "")

        result = await node.execute(execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    @patch("casare_rpa.nodes.email_nodes.imaplib.IMAP4_SSL")
    async def test_move_email_success(self, mock_imap, execution_context) -> None:
        """Test successful email move."""
        mock_mail = MagicMock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", None)
        mock_mail.select.return_value = ("OK", [b"1"])
        mock_mail.copy.return_value = ("OK", None)
        mock_mail.store.return_value = ("OK", None)

        node = MoveEmailNode(node_id="test_move")
        node.set_input_value("imap_server", "imap.test.com")
        node.set_input_value("username", "user")
        node.set_input_value("password", "pass")
        node.set_input_value("email_uid", "123")
        node.set_input_value("source_folder", "INBOX")
        node.set_input_value("target_folder", "Archive")

        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_mail.copy.assert_called_once_with(b"123", "Archive")
        mock_mail.store.assert_called_once_with(b"123", "+FLAGS", "\\Deleted")
        mock_mail.expunge.assert_called_once()


class TestEmailHelperFunctions:
    """Tests for email helper functions."""

    def test_decode_header_value_plain(self) -> None:
        """Test decoding plain header value."""
        result = _decode_header_value("Simple Subject")
        assert result == "Simple Subject"

    def test_decode_header_value_empty(self) -> None:
        """Test decoding empty header."""
        result = _decode_header_value("")
        assert result == ""

    def test_decode_header_value_none(self) -> None:
        """Test decoding None header."""
        result = _decode_header_value(None)
        assert result == ""

    def test_parse_email_message_simple(self) -> None:
        """Test parsing simple email message."""
        msg = MIMEText("Test body content")
        msg["Subject"] = "Test Subject"
        msg["From"] = "sender@test.com"
        msg["To"] = "recipient@test.com"

        parsed = _parse_email_message(msg)

        assert parsed["subject"] == "Test Subject"
        assert parsed["from"] == "sender@test.com"
        assert parsed["to"] == "recipient@test.com"
        assert parsed["body_text"] == "Test body content"
        assert parsed["has_attachments"] is False

    def test_parse_email_message_multipart(self) -> None:
        """Test parsing multipart email message."""
        msg = MIMEMultipart()
        msg["Subject"] = "Multipart Test"
        msg["From"] = "sender@test.com"
        msg["To"] = "recipient@test.com"

        msg.attach(MIMEText("Plain text body", "plain"))
        msg.attach(MIMEText("<p>HTML body</p>", "html"))

        parsed = _parse_email_message(msg)

        assert parsed["subject"] == "Multipart Test"
        assert "Plain text body" in parsed["body_text"]
        assert "<p>HTML body</p>" in parsed["body_html"]

    def test_parse_email_message_with_attachment(self) -> None:
        """Test parsing email with attachment."""
        msg = MIMEMultipart()
        msg["Subject"] = "With Attachment"
        msg["From"] = "sender@test.com"

        msg.attach(MIMEText("Body content"))

        from email.mime.application import MIMEApplication

        attachment = MIMEApplication(b"file content", Name="document.pdf")
        attachment["Content-Disposition"] = 'attachment; filename="document.pdf"'
        msg.attach(attachment)

        parsed = _parse_email_message(msg)

        assert parsed["has_attachments"] is True
        assert len(parsed["attachments"]) == 1
        assert parsed["attachments"][0]["filename"] == "document.pdf"
