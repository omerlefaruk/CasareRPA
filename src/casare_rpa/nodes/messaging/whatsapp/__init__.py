"""
CasareRPA - WhatsApp Nodes

Nodes for WhatsApp Business Cloud API integrations.
"""

from casare_rpa.nodes.messaging.whatsapp.whatsapp_send import (
    # Reusable PropertyDef constants
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_CREDENTIAL_NAME,
    WHATSAPP_PHONE_NUMBER_ID,
    WHATSAPP_TO,
    WhatsAppSendDocumentNode,
    WhatsAppSendImageNode,
    WhatsAppSendInteractiveNode,
    WhatsAppSendLocationNode,
    WhatsAppSendMessageNode,
    WhatsAppSendTemplateNode,
    WhatsAppSendVideoNode,
)

__all__ = [
    "WhatsAppSendMessageNode",
    "WhatsAppSendTemplateNode",
    "WhatsAppSendImageNode",
    "WhatsAppSendDocumentNode",
    "WhatsAppSendLocationNode",
    "WhatsAppSendVideoNode",
    "WhatsAppSendInteractiveNode",
    # Reusable PropertyDef constants
    "WHATSAPP_ACCESS_TOKEN",
    "WHATSAPP_PHONE_NUMBER_ID",
    "WHATSAPP_CREDENTIAL_NAME",
    "WHATSAPP_TO",
]
