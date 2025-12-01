"""
CasareRPA - WhatsApp Nodes

Nodes for WhatsApp Business Cloud API integrations.
"""

from .whatsapp_send import (
    WhatsAppSendMessageNode,
    WhatsAppSendTemplateNode,
    WhatsAppSendImageNode,
    WhatsAppSendDocumentNode,
    WhatsAppSendLocationNode,
    WhatsAppSendVideoNode,
    WhatsAppSendInteractiveNode,
)

__all__ = [
    "WhatsAppSendMessageNode",
    "WhatsAppSendTemplateNode",
    "WhatsAppSendImageNode",
    "WhatsAppSendDocumentNode",
    "WhatsAppSendLocationNode",
    "WhatsAppSendVideoNode",
    "WhatsAppSendInteractiveNode",
]
