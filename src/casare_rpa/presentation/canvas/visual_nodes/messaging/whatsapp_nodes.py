"""Visual nodes for WhatsApp messaging."""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.nodes.messaging.whatsapp import (
    WhatsAppSendMessageNode,
    WhatsAppSendTemplateNode,
    WhatsAppSendImageNode,
    WhatsAppSendDocumentNode,
    WhatsAppSendVideoNode,
    WhatsAppSendLocationNode,
    WhatsAppSendInteractiveNode,
)


class VisualWhatsAppSendMessageNode(VisualNode):
    """Visual representation of WhatsAppSendMessageNode."""

    __identifier__ = "casare_rpa.messaging"
    NODE_NAME = "WhatsApp: Send Message"
    NODE_CATEGORY = "messaging/whatsapp"
    CASARE_NODE_CLASS = "WhatsAppSendMessageNode"

    def __init__(self) -> None:
        """Initialize WhatsApp Send Message node."""
        super().__init__()
        # Connection settings
        self.add_text_input(
            "access_token",
            "Access Token",
            text="",
            tab="connection",
            placeholder_text="Meta Graph API token or use credential",
        )
        self.add_text_input(
            "phone_number_id",
            "Phone Number ID",
            text="",
            tab="connection",
            placeholder_text="From Meta Business Suite",
        )
        self.add_text_input(
            "credential_name",
            "Credential Name",
            text="",
            tab="connection",
            placeholder_text="whatsapp",
        )
        # Message settings
        self.add_text_input(
            "to",
            "To (Phone Number)",
            text="",
            tab="properties",
            placeholder_text="+1234567890",
        )
        self.add_text_input(
            "text",
            "Message Text",
            text="",
            tab="properties",
            placeholder_text="Hello, World!",
        )
        self._safe_create_property("preview_url", False, widget_type=1, tab="properties")

    def get_node_class(self) -> type:
        return WhatsAppSendMessageNode

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("to", DataType.STRING)
        self.add_typed_input("text", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("message_id", DataType.STRING)
        self.add_typed_output("phone_number", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualWhatsAppSendTemplateNode(VisualNode):
    """Visual representation of WhatsAppSendTemplateNode."""

    __identifier__ = "casare_rpa.messaging"
    NODE_NAME = "WhatsApp: Send Template"
    NODE_CATEGORY = "messaging/whatsapp"
    CASARE_NODE_CLASS = "WhatsAppSendTemplateNode"

    def __init__(self) -> None:
        """Initialize WhatsApp Send Template node."""
        super().__init__()
        # Connection settings
        self.add_text_input(
            "access_token",
            "Access Token",
            text="",
            tab="connection",
            placeholder_text="Meta Graph API token or use credential",
        )
        self.add_text_input(
            "phone_number_id",
            "Phone Number ID",
            text="",
            tab="connection",
            placeholder_text="From Meta Business Suite",
        )
        self.add_text_input(
            "credential_name",
            "Credential Name",
            text="",
            tab="connection",
            placeholder_text="whatsapp",
        )
        # Template settings
        self.add_text_input(
            "to",
            "To (Phone Number)",
            text="",
            tab="properties",
            placeholder_text="+1234567890",
        )
        self.add_text_input(
            "template_name",
            "Template Name",
            text="",
            tab="properties",
            placeholder_text="hello_world",
        )
        self.add_text_input(
            "language_code",
            "Language Code",
            text="en_US",
            tab="properties",
            placeholder_text="en_US",
        )
        self.add_text_input(
            "components",
            "Components (JSON)",
            text="",
            tab="advanced",
            placeholder_text='[{"type": "body", "parameters": [...]}]',
        )

    def get_node_class(self) -> type:
        return WhatsAppSendTemplateNode

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("to", DataType.STRING)
        self.add_typed_input("template_name", DataType.STRING)
        self.add_typed_input("language_code", DataType.STRING)
        self.add_typed_input("components", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("message_id", DataType.STRING)
        self.add_typed_output("phone_number", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualWhatsAppSendImageNode(VisualNode):
    """Visual representation of WhatsAppSendImageNode."""

    __identifier__ = "casare_rpa.messaging"
    NODE_NAME = "WhatsApp: Send Image"
    NODE_CATEGORY = "messaging/whatsapp"
    CASARE_NODE_CLASS = "WhatsAppSendImageNode"

    def __init__(self) -> None:
        """Initialize WhatsApp Send Image node."""
        super().__init__()
        # Connection settings
        self.add_text_input(
            "access_token",
            "Access Token",
            text="",
            tab="connection",
            placeholder_text="Meta Graph API token or use credential",
        )
        self.add_text_input(
            "phone_number_id",
            "Phone Number ID",
            text="",
            tab="connection",
            placeholder_text="From Meta Business Suite",
        )
        self.add_text_input(
            "credential_name",
            "Credential Name",
            text="",
            tab="connection",
            placeholder_text="whatsapp",
        )
        # Image settings
        self.add_text_input(
            "to",
            "To (Phone Number)",
            text="",
            tab="properties",
            placeholder_text="+1234567890",
        )
        self.add_text_input(
            "image",
            "Image",
            text="",
            tab="properties",
            placeholder_text="URL or media ID",
        )
        self.add_text_input(
            "caption",
            "Caption",
            text="",
            tab="properties",
            placeholder_text="Optional caption",
        )

    def get_node_class(self) -> type:
        return WhatsAppSendImageNode

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("to", DataType.STRING)
        self.add_typed_input("image", DataType.STRING)
        self.add_typed_input("caption", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("message_id", DataType.STRING)
        self.add_typed_output("phone_number", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualWhatsAppSendDocumentNode(VisualNode):
    """Visual representation of WhatsAppSendDocumentNode."""

    __identifier__ = "casare_rpa.messaging"
    NODE_NAME = "WhatsApp: Send Document"
    NODE_CATEGORY = "messaging/whatsapp"
    CASARE_NODE_CLASS = "WhatsAppSendDocumentNode"

    def __init__(self) -> None:
        """Initialize WhatsApp Send Document node."""
        super().__init__()
        # Connection settings
        self.add_text_input(
            "access_token",
            "Access Token",
            text="",
            tab="connection",
            placeholder_text="Meta Graph API token or use credential",
        )
        self.add_text_input(
            "phone_number_id",
            "Phone Number ID",
            text="",
            tab="connection",
            placeholder_text="From Meta Business Suite",
        )
        self.add_text_input(
            "credential_name",
            "Credential Name",
            text="",
            tab="connection",
            placeholder_text="whatsapp",
        )
        # Document settings
        self.add_text_input(
            "to",
            "To (Phone Number)",
            text="",
            tab="properties",
            placeholder_text="+1234567890",
        )
        self.add_text_input(
            "document",
            "Document",
            text="",
            tab="properties",
            placeholder_text="URL or media ID",
        )
        self.add_text_input(
            "filename",
            "Filename",
            text="",
            tab="properties",
            placeholder_text="report.pdf",
        )
        self.add_text_input(
            "caption",
            "Caption",
            text="",
            tab="properties",
            placeholder_text="Optional caption",
        )

    def get_node_class(self) -> type:
        return WhatsAppSendDocumentNode

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("to", DataType.STRING)
        self.add_typed_input("document", DataType.STRING)
        self.add_typed_input("filename", DataType.STRING)
        self.add_typed_input("caption", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("message_id", DataType.STRING)
        self.add_typed_output("phone_number", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualWhatsAppSendVideoNode(VisualNode):
    """Visual representation of WhatsAppSendVideoNode."""

    __identifier__ = "casare_rpa.messaging"
    NODE_NAME = "WhatsApp: Send Video"
    NODE_CATEGORY = "messaging/whatsapp"
    CASARE_NODE_CLASS = "WhatsAppSendVideoNode"

    def __init__(self) -> None:
        """Initialize WhatsApp Send Video node."""
        super().__init__()
        # Connection settings
        self.add_text_input(
            "access_token",
            "Access Token",
            text="",
            tab="connection",
            placeholder_text="Meta Graph API token or use credential",
        )
        self.add_text_input(
            "phone_number_id",
            "Phone Number ID",
            text="",
            tab="connection",
            placeholder_text="From Meta Business Suite",
        )
        self.add_text_input(
            "credential_name",
            "Credential Name",
            text="",
            tab="connection",
            placeholder_text="whatsapp",
        )
        # Video settings
        self.add_text_input(
            "to",
            "To (Phone Number)",
            text="",
            tab="properties",
            placeholder_text="+1234567890",
        )
        self.add_text_input(
            "video",
            "Video",
            text="",
            tab="properties",
            placeholder_text="URL or media ID",
        )
        self.add_text_input(
            "caption",
            "Caption",
            text="",
            tab="properties",
            placeholder_text="Optional caption",
        )

    def get_node_class(self) -> type:
        return WhatsAppSendVideoNode

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("to", DataType.STRING)
        self.add_typed_input("video", DataType.STRING)
        self.add_typed_input("caption", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("message_id", DataType.STRING)
        self.add_typed_output("phone_number", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualWhatsAppSendLocationNode(VisualNode):
    """Visual representation of WhatsAppSendLocationNode."""

    __identifier__ = "casare_rpa.messaging"
    NODE_NAME = "WhatsApp: Send Location"
    NODE_CATEGORY = "messaging/whatsapp"
    CASARE_NODE_CLASS = "WhatsAppSendLocationNode"

    def __init__(self) -> None:
        """Initialize WhatsApp Send Location node."""
        super().__init__()
        # Connection settings
        self.add_text_input(
            "access_token",
            "Access Token",
            text="",
            tab="connection",
            placeholder_text="Meta Graph API token or use credential",
        )
        self.add_text_input(
            "phone_number_id",
            "Phone Number ID",
            text="",
            tab="connection",
            placeholder_text="From Meta Business Suite",
        )
        self.add_text_input(
            "credential_name",
            "Credential Name",
            text="",
            tab="connection",
            placeholder_text="whatsapp",
        )
        # Location settings
        self.add_text_input(
            "to",
            "To (Phone Number)",
            text="",
            tab="properties",
            placeholder_text="+1234567890",
        )
        self.add_text_input(
            "latitude",
            "Latitude",
            text="",
            tab="properties",
            placeholder_text="-90 to 90",
        )
        self.add_text_input(
            "longitude",
            "Longitude",
            text="",
            tab="properties",
            placeholder_text="-180 to 180",
        )
        self.add_text_input(
            "location_name",
            "Location Name",
            text="",
            tab="properties",
            placeholder_text="Office",
        )
        self.add_text_input(
            "address",
            "Address",
            text="",
            tab="properties",
            placeholder_text="123 Main St",
        )

    def get_node_class(self) -> type:
        return WhatsAppSendLocationNode

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("to", DataType.STRING)
        self.add_typed_input("latitude", DataType.FLOAT)
        self.add_typed_input("longitude", DataType.FLOAT)
        self.add_typed_input("name", DataType.STRING)
        self.add_typed_input("address", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("message_id", DataType.STRING)
        self.add_typed_output("phone_number", DataType.STRING)
        self.add_typed_output("latitude", DataType.FLOAT)
        self.add_typed_output("longitude", DataType.FLOAT)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualWhatsAppSendInteractiveNode(VisualNode):
    """Visual representation of WhatsAppSendInteractiveNode."""

    __identifier__ = "casare_rpa.messaging"
    NODE_NAME = "WhatsApp: Send Interactive"
    NODE_CATEGORY = "messaging/whatsapp"
    CASARE_NODE_CLASS = "WhatsAppSendInteractiveNode"

    def __init__(self) -> None:
        """Initialize WhatsApp Send Interactive node."""
        super().__init__()
        # Connection settings
        self.add_text_input(
            "access_token",
            "Access Token",
            text="",
            tab="connection",
            placeholder_text="Meta Graph API token or use credential",
        )
        self.add_text_input(
            "phone_number_id",
            "Phone Number ID",
            text="",
            tab="connection",
            placeholder_text="From Meta Business Suite",
        )
        self.add_text_input(
            "credential_name",
            "Credential Name",
            text="",
            tab="connection",
            placeholder_text="whatsapp",
        )
        # Interactive settings
        self.add_text_input(
            "to",
            "To (Phone Number)",
            text="",
            tab="properties",
            placeholder_text="+1234567890",
        )
        self.add_combo_menu(
            "interactive_type",
            "Interactive Type",
            items=["button", "list"],
            tab="properties",
        )
        self.add_text_input(
            "body_text",
            "Body Text",
            text="",
            tab="properties",
            placeholder_text="Choose an option:",
        )
        self.add_text_input(
            "action_json",
            "Action (JSON)",
            text="",
            tab="properties",
            placeholder_text='{"buttons": [...]}',
        )
        self.add_text_input(
            "header_json",
            "Header (JSON)",
            text="",
            tab="advanced",
            placeholder_text='{"type": "text", "text": "Header"}',
        )
        self.add_text_input(
            "footer_text",
            "Footer Text",
            text="",
            tab="advanced",
            placeholder_text="Optional footer",
        )

    def get_node_class(self) -> type:
        return WhatsAppSendInteractiveNode

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("to", DataType.STRING)
        self.add_typed_input("interactive_type", DataType.STRING)
        self.add_typed_input("body_text", DataType.STRING)
        self.add_typed_input("action_json", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("message_id", DataType.STRING)
        self.add_typed_output("phone_number", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


__all__ = [
    "VisualWhatsAppSendMessageNode",
    "VisualWhatsAppSendTemplateNode",
    "VisualWhatsAppSendImageNode",
    "VisualWhatsAppSendDocumentNode",
    "VisualWhatsAppSendVideoNode",
    "VisualWhatsAppSendLocationNode",
    "VisualWhatsAppSendInteractiveNode",
]
