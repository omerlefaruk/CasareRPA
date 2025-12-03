"""
Email nodes package for CasareRPA.

Provides nodes for sending and receiving emails via SMTP and IMAP,
with support for attachments, HTML content, and email management.

Modules:
- email_base: Shared utilities and PropertyDef constants
- send_nodes: SMTP send operations (SendEmailNode)
- receive_nodes: IMAP read operations (ReadEmailsNode, GetEmailContentNode, FilterEmailsNode)
- imap_nodes: IMAP management (MarkEmailNode, DeleteEmailNode, MoveEmailNode, SaveAttachmentNode)
"""

from .email_base import (
    EMAIL_PASSWORD_PROP,
    EMAIL_USERNAME_PROP,
    IMAP_PORT_DEFAULT,
    IMAP_SERVER_DEFAULT,
    SMTP_PORT_DEFAULT,
    SMTP_SERVER_DEFAULT,
    decode_header_value,
    parse_email_message,
)
from .imap_nodes import (
    DeleteEmailNode,
    MarkEmailNode,
    MoveEmailNode,
    SaveAttachmentNode,
)
from .receive_nodes import (
    FilterEmailsNode,
    GetEmailContentNode,
    ReadEmailsNode,
)
from .send_nodes import SendEmailNode

__all__ = [
    # Send nodes
    "SendEmailNode",
    # Receive nodes
    "ReadEmailsNode",
    "GetEmailContentNode",
    "FilterEmailsNode",
    # IMAP management nodes
    "SaveAttachmentNode",
    "MarkEmailNode",
    "DeleteEmailNode",
    "MoveEmailNode",
    # Utilities
    "decode_header_value",
    "parse_email_message",
    # Constants
    "EMAIL_USERNAME_PROP",
    "EMAIL_PASSWORD_PROP",
    "SMTP_SERVER_DEFAULT",
    "SMTP_PORT_DEFAULT",
    "IMAP_SERVER_DEFAULT",
    "IMAP_PORT_DEFAULT",
]
