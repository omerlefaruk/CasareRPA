"""
Email base module with shared utilities for email nodes.

Contains helper functions for parsing and decoding email messages,
plus shared PropertyDef constants for email-related nodes.
"""

from __future__ import annotations

from email.header import decode_header
from email.message import Message as EmailMessage
from email.utils import parsedate_to_datetime
from typing import Any, Dict

from casare_rpa.domain.schemas import PropertyDef, PropertyType

# =============================================================================
# Email-specific PropertyDef constants
# =============================================================================

EMAIL_USERNAME_PROP = PropertyDef(
    "username",
    PropertyType.STRING,
    default="",
    label="Username",
    tooltip="Email account username (or use Credential Name for vault lookup)",
    tab="connection",
)

EMAIL_PASSWORD_PROP = PropertyDef(
    "password",
    PropertyType.STRING,
    default="",
    label="Password",
    tooltip="Email account password (or use Credential Name for vault lookup)",
    tab="connection",
)

# IMAP connection defaults
IMAP_SERVER_DEFAULT = "imap.gmail.com"
IMAP_PORT_DEFAULT = 993

# SMTP connection defaults
SMTP_SERVER_DEFAULT = "smtp.gmail.com"
SMTP_PORT_DEFAULT = 587


# =============================================================================
# Email parsing utilities
# =============================================================================


def decode_header_value(value: str) -> str:
    """
    Decode email header value.

    Handles RFC 2047 encoded headers (e.g., =?utf-8?Q?Subject?=).

    Args:
        value: The header value to decode

    Returns:
        Decoded string
    """
    if not value:
        return ""
    decoded_parts = decode_header(value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            try:
                result.append(part.decode(charset or "utf-8", errors="replace"))
            except (LookupError, UnicodeDecodeError):
                result.append(part.decode("utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


def parse_email_message(msg: EmailMessage) -> dict[str, Any]:
    """
    Parse an email message into a dictionary.

    Extracts headers, body (text/html), and attachment metadata.

    Args:
        msg: Email message object

    Returns:
        Dictionary with email fields:
        - message_id: str
        - subject: str
        - from: str
        - to: str
        - cc: str
        - date: str (ISO format)
        - date_obj: datetime or None
        - body_text: str
        - body_html: str
        - attachments: List[Dict] with filename, content_type, size
        - has_attachments: bool
    """
    # Get basic headers
    subject = decode_header_value(msg.get("Subject", ""))
    from_addr = decode_header_value(msg.get("From", ""))
    to_addr = decode_header_value(msg.get("To", ""))
    cc_addr = decode_header_value(msg.get("Cc", ""))
    date_str = msg.get("Date", "")
    message_id = msg.get("Message-ID", "")

    # Parse date
    date = None
    if date_str:
        try:
            date = parsedate_to_datetime(date_str)
        except (ValueError, TypeError):
            pass

    # Get body
    body_text = ""
    body_html = ""
    attachments = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            if "attachment" in content_disposition:
                # Attachment
                filename = part.get_filename()
                if filename:
                    filename = decode_header_value(filename)
                    attachments.append(
                        {
                            "filename": filename,
                            "content_type": content_type,
                            "size": len(part.get_payload(decode=True) or b""),
                        }
                    )
            elif content_type == "text/plain":
                try:
                    body_text = part.get_payload(decode=True).decode("utf-8", errors="replace")
                except (AttributeError, UnicodeDecodeError):
                    body_text = str(part.get_payload())
            elif content_type == "text/html":
                try:
                    body_html = part.get_payload(decode=True).decode("utf-8", errors="replace")
                except (AttributeError, UnicodeDecodeError):
                    body_html = str(part.get_payload())
    else:
        # Not multipart
        content_type = msg.get_content_type()
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                text = payload.decode("utf-8", errors="replace")
                if content_type == "text/html":
                    body_html = text
                else:
                    body_text = text
        except (AttributeError, UnicodeDecodeError):
            body_text = str(msg.get_payload())

    return {
        "message_id": message_id,
        "subject": subject,
        "from": from_addr,
        "to": to_addr,
        "cc": cc_addr,
        "date": date.isoformat() if date else "",
        "date_obj": date,
        "body_text": body_text,
        "body_html": body_html,
        "attachments": attachments,
        "has_attachments": len(attachments) > 0,
    }
