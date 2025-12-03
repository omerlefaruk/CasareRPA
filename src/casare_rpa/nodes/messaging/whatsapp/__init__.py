"""
CasareRPA - WhatsApp Nodes

Nodes for WhatsApp Business Cloud API integrations.
"""

from casare_rpa.nodes.messaging.whatsapp.whatsapp_send import (
    WhatsAppSendMessageNode,
    WhatsAppSendTemplateNode,
    WhatsAppSendImageNode,
    WhatsAppSendDocumentNode,
    WhatsAppSendLocationNode,
    WhatsAppSendVideoNode,
    WhatsAppSendInteractiveNode,
    # Reusable PropertyDef constants
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_PHONE_NUMBER_ID,
    WHATSAPP_CREDENTIAL_NAME,
    WHATSAPP_TO,
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
