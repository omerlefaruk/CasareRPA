"""
CasareRPA - Gmail Nodes

Nodes for sending, reading, and managing emails via Gmail API v1.
"""

from casare_rpa.nodes.google.google_base import GmailBaseNode
from casare_rpa.nodes.google.gmail.gmail_send import (
    GmailSendEmailNode,
    GmailSendWithAttachmentNode,
    GmailReplyToEmailNode,
    GmailForwardEmailNode,
    GmailCreateDraftNode,
)
from casare_rpa.nodes.google.gmail.gmail_read import (
    GmailGetEmailNode,
    GmailSearchEmailsNode,
    GmailGetThreadNode,
    GmailGetAttachmentNode,
)

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
