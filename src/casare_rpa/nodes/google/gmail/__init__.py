"""
CasareRPA - Gmail Nodes

Nodes for sending, reading, and managing emails via Gmail API v1.
"""

from casare_rpa.nodes.google.gmail.gmail_read import (
    GmailGetAttachmentNode,
    GmailGetEmailNode,
    GmailGetThreadNode,
    GmailSearchEmailsNode,
)
from casare_rpa.nodes.google.gmail.gmail_send import (
    GmailCreateDraftNode,
    GmailForwardEmailNode,
    GmailReplyToEmailNode,
    GmailSendEmailNode,
    GmailSendWithAttachmentNode,
)
from casare_rpa.nodes.google.google_base import GmailBaseNode

__all__ = [
    # Base
    "GmailBaseNode",
    # Send Nodes
    "GmailSendEmailNode",
    "GmailSendWithAttachmentNode",
    "GmailReplyToEmailNode",
    "GmailForwardEmailNode",
    "GmailCreateDraftNode",
    # Read Nodes
    "GmailGetEmailNode",
    "GmailSearchEmailsNode",
    "GmailGetThreadNode",
    "GmailGetAttachmentNode",
]
