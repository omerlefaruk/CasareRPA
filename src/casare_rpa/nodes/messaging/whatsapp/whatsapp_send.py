"""
CasareRPA - WhatsApp Send Nodes

Nodes for sending messages, templates, media, and locations via WhatsApp Business Cloud API.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
import json

from loguru import logger

from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    PortType,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.infrastructure.resources.whatsapp_client import WhatsAppClient
from .whatsapp_base import WhatsAppBaseNode


class WhatsAppSendMessageNode(WhatsAppBaseNode):
    """
    Send a text message via WhatsApp.

    Inputs:
        - to: Recipient phone number (with country code, e.g., +1234567890)
        - text: Message text
        - preview_url: Enable URL preview (default: False)

    Outputs:
        - message_id: Sent message ID
        - phone_number: Recipient phone number
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "whatsapp_send_message"
    NODE_CATEGORY = "messaging"
    NODE_DISPLAY_NAME = "WhatsApp: Send Message"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="WhatsApp Send Message", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        # Common ports
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Message-specific ports
        self.add_input_port("text", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port(
            "preview_url", PortType.INPUT, DataType.BOOLEAN, required=False
        )

        # Additional output
        self.add_output_port("text", PortType.OUTPUT, DataType.STRING)

    async def _execute_whatsapp(
        self,
        context: ExecutionContext,
        client: WhatsAppClient,
    ) -> ExecutionResult:
        """Send a text message."""
        to = self._get_recipient(context)

        # Get text
        text = self.get_parameter("text")
        if hasattr(context, "resolve_value"):
            text = context.resolve_value(text)

        if not text:
            self._set_error_outputs("Text message is required")
            return {
                "success": False,
                "error": "Text message is required",
                "next_nodes": [],
            }

        # Get optional params
        preview_url = self.get_parameter("preview_url") or False

        logger.debug(f"Sending WhatsApp message to {to}")

        # Send message
        result = await client.send_message(
            to=to,
            text=text,
            preview_url=preview_url,
        )

        # Set outputs
        self._set_success_outputs(result.message_id, result.phone_number)
        self.set_output_value("text", text)

        logger.info(f"WhatsApp message sent: {result.message_id}")

        return {
            "success": True,
            "message_id": result.message_id,
            "phone_number": result.phone_number,
            "next_nodes": [],
        }


class WhatsAppSendTemplateNode(WhatsAppBaseNode):
    """
    Send a template message via WhatsApp.

    Templates must be pre-approved by Meta/WhatsApp.

    Inputs:
        - to: Recipient phone number
        - template_name: Name of approved template
        - language_code: Template language (e.g., "en_US")
        - components: JSON string of template components/variables

    Outputs:
        - message_id: Sent message ID
        - phone_number: Recipient phone number
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "whatsapp_send_template"
    NODE_CATEGORY = "messaging"
    NODE_DISPLAY_NAME = "WhatsApp: Send Template"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="WhatsApp Send Template", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Template-specific ports
        self.add_input_port(
            "template_name", PortType.INPUT, DataType.STRING, required=True
        )
        self.add_input_port(
            "language_code", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "components", PortType.INPUT, DataType.STRING, required=False
        )

        # Additional output
        self.add_output_port("template_name", PortType.OUTPUT, DataType.STRING)

    async def _execute_whatsapp(
        self,
        context: ExecutionContext,
        client: WhatsAppClient,
    ) -> ExecutionResult:
        """Send a template message."""
        to = self._get_recipient(context)

        # Get template name
        template_name = self.get_parameter("template_name")
        if hasattr(context, "resolve_value"):
            template_name = context.resolve_value(template_name)

        if not template_name:
            self._set_error_outputs("Template name is required")
            return {
                "success": False,
                "error": "Template name is required",
                "next_nodes": [],
            }

        # Get language code
        language_code = self.get_parameter("language_code") or "en_US"
        if hasattr(context, "resolve_value"):
            language_code = context.resolve_value(language_code)

        # Get components (JSON string)
        components = None
        components_str = self.get_parameter("components")
        if components_str:
            if hasattr(context, "resolve_value"):
                components_str = context.resolve_value(components_str)
            try:
                components = json.loads(components_str)
            except json.JSONDecodeError as e:
                self._set_error_outputs(f"Invalid components JSON: {e}")
                return {
                    "success": False,
                    "error": f"Invalid components JSON: {e}",
                    "next_nodes": [],
                }

        logger.debug(f"Sending WhatsApp template '{template_name}' to {to}")

        # Send template
        result = await client.send_template(
            to=to,
            template_name=template_name,
            language_code=language_code,
            components=components,
        )

        # Set outputs
        self._set_success_outputs(result.message_id, result.phone_number)
        self.set_output_value("template_name", template_name)

        logger.info(f"WhatsApp template sent: {result.message_id}")

        return {
            "success": True,
            "message_id": result.message_id,
            "phone_number": result.phone_number,
            "next_nodes": [],
        }


class WhatsAppSendImageNode(WhatsAppBaseNode):
    """
    Send an image via WhatsApp.

    Inputs:
        - to: Recipient phone number
        - image: Image URL or media ID
        - caption: Optional caption

    Outputs:
        - message_id: Sent message ID
        - phone_number: Recipient phone number
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "whatsapp_send_image"
    NODE_CATEGORY = "messaging"
    NODE_DISPLAY_NAME = "WhatsApp: Send Image"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="WhatsApp Send Image", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Image-specific ports
        self.add_input_port("image", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port("caption", PortType.INPUT, DataType.STRING, required=False)

        # Additional output
        self.add_output_port("image_path", PortType.OUTPUT, DataType.STRING)

    async def _execute_whatsapp(
        self,
        context: ExecutionContext,
        client: WhatsAppClient,
    ) -> ExecutionResult:
        """Send an image."""
        to = self._get_recipient(context)

        # Get image
        image = self.get_parameter("image")
        if hasattr(context, "resolve_value"):
            image = context.resolve_value(image)

        if not image:
            self._set_error_outputs("Image is required")
            return {"success": False, "error": "Image is required", "next_nodes": []}

        # Get optional caption
        caption = self.get_parameter("caption")
        if caption and hasattr(context, "resolve_value"):
            caption = context.resolve_value(caption)

        logger.debug(f"Sending WhatsApp image to {to}")

        # Send image
        result = await client.send_image(
            to=to,
            image=image,
            caption=caption,
        )

        # Set outputs
        self._set_success_outputs(result.message_id, result.phone_number)
        self.set_output_value("image_path", str(image))

        logger.info(f"WhatsApp image sent: {result.message_id}")

        return {
            "success": True,
            "message_id": result.message_id,
            "phone_number": result.phone_number,
            "next_nodes": [],
        }


class WhatsAppSendDocumentNode(WhatsAppBaseNode):
    """
    Send a document via WhatsApp.

    Inputs:
        - to: Recipient phone number
        - document: Document URL or media ID
        - filename: Display filename
        - caption: Optional caption

    Outputs:
        - message_id: Sent message ID
        - phone_number: Recipient phone number
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "whatsapp_send_document"
    NODE_CATEGORY = "messaging"
    NODE_DISPLAY_NAME = "WhatsApp: Send Document"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="WhatsApp Send Document", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Document-specific ports
        self.add_input_port("document", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port("filename", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port("caption", PortType.INPUT, DataType.STRING, required=False)

        # Additional output
        self.add_output_port("document_path", PortType.OUTPUT, DataType.STRING)

    async def _execute_whatsapp(
        self,
        context: ExecutionContext,
        client: WhatsAppClient,
    ) -> ExecutionResult:
        """Send a document."""
        to = self._get_recipient(context)

        # Get document
        document = self.get_parameter("document")
        if hasattr(context, "resolve_value"):
            document = context.resolve_value(document)

        if not document:
            self._set_error_outputs("Document is required")
            return {"success": False, "error": "Document is required", "next_nodes": []}

        # Get optional params
        filename = self.get_parameter("filename")
        if filename and hasattr(context, "resolve_value"):
            filename = context.resolve_value(filename)

        caption = self.get_parameter("caption")
        if caption and hasattr(context, "resolve_value"):
            caption = context.resolve_value(caption)

        logger.debug(f"Sending WhatsApp document to {to}")

        # Send document
        result = await client.send_document(
            to=to,
            document=document,
            filename=filename,
            caption=caption,
        )

        # Set outputs
        self._set_success_outputs(result.message_id, result.phone_number)
        self.set_output_value("document_path", str(document))

        logger.info(f"WhatsApp document sent: {result.message_id}")

        return {
            "success": True,
            "message_id": result.message_id,
            "phone_number": result.phone_number,
            "next_nodes": [],
        }


class WhatsAppSendVideoNode(WhatsAppBaseNode):
    """
    Send a video via WhatsApp.

    Inputs:
        - to: Recipient phone number
        - video: Video URL or media ID
        - caption: Optional caption

    Outputs:
        - message_id: Sent message ID
        - phone_number: Recipient phone number
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "whatsapp_send_video"
    NODE_CATEGORY = "messaging"
    NODE_DISPLAY_NAME = "WhatsApp: Send Video"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="WhatsApp Send Video", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Video-specific ports
        self.add_input_port("video", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port("caption", PortType.INPUT, DataType.STRING, required=False)

        # Additional output
        self.add_output_port("video_path", PortType.OUTPUT, DataType.STRING)

    async def _execute_whatsapp(
        self,
        context: ExecutionContext,
        client: WhatsAppClient,
    ) -> ExecutionResult:
        """Send a video."""
        to = self._get_recipient(context)

        # Get video
        video = self.get_parameter("video")
        if hasattr(context, "resolve_value"):
            video = context.resolve_value(video)

        if not video:
            self._set_error_outputs("Video is required")
            return {"success": False, "error": "Video is required", "next_nodes": []}

        # Get optional caption
        caption = self.get_parameter("caption")
        if caption and hasattr(context, "resolve_value"):
            caption = context.resolve_value(caption)

        logger.debug(f"Sending WhatsApp video to {to}")

        # Send video
        result = await client.send_video(
            to=to,
            video=video,
            caption=caption,
        )

        # Set outputs
        self._set_success_outputs(result.message_id, result.phone_number)
        self.set_output_value("video_path", str(video))

        logger.info(f"WhatsApp video sent: {result.message_id}")

        return {
            "success": True,
            "message_id": result.message_id,
            "phone_number": result.phone_number,
            "next_nodes": [],
        }


class WhatsAppSendLocationNode(WhatsAppBaseNode):
    """
    Send a location via WhatsApp.

    Inputs:
        - to: Recipient phone number
        - latitude: Location latitude (-90 to 90)
        - longitude: Location longitude (-180 to 180)
        - name: Location name
        - address: Location address

    Outputs:
        - message_id: Sent message ID
        - phone_number: Recipient phone number
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "whatsapp_send_location"
    NODE_CATEGORY = "messaging"
    NODE_DISPLAY_NAME = "WhatsApp: Send Location"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="WhatsApp Send Location", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Location-specific ports
        self.add_input_port("latitude", PortType.INPUT, DataType.FLOAT, required=True)
        self.add_input_port("longitude", PortType.INPUT, DataType.FLOAT, required=True)
        self.add_input_port("name", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port("address", PortType.INPUT, DataType.STRING, required=False)

        # Additional outputs
        self.add_output_port("latitude", PortType.OUTPUT, DataType.FLOAT)
        self.add_output_port("longitude", PortType.OUTPUT, DataType.FLOAT)

    async def _execute_whatsapp(
        self,
        context: ExecutionContext,
        client: WhatsAppClient,
    ) -> ExecutionResult:
        """Send a location."""
        to = self._get_recipient(context)

        # Get coordinates
        latitude = self.get_parameter("latitude")
        longitude = self.get_parameter("longitude")

        if hasattr(context, "resolve_value"):
            latitude = context.resolve_value(latitude)
            longitude = context.resolve_value(longitude)

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            self._set_error_outputs("Invalid latitude or longitude")
            return {
                "success": False,
                "error": "Invalid latitude or longitude",
                "next_nodes": [],
            }

        # Validate range
        if not (-90 <= latitude <= 90):
            self._set_error_outputs("Latitude must be between -90 and 90")
            return {
                "success": False,
                "error": "Latitude must be between -90 and 90",
                "next_nodes": [],
            }

        if not (-180 <= longitude <= 180):
            self._set_error_outputs("Longitude must be between -180 and 180")
            return {
                "success": False,
                "error": "Longitude must be between -180 and 180",
                "next_nodes": [],
            }

        # Get optional params
        name = self.get_parameter("name")
        if name and hasattr(context, "resolve_value"):
            name = context.resolve_value(name)

        address = self.get_parameter("address")
        if address and hasattr(context, "resolve_value"):
            address = context.resolve_value(address)

        logger.debug(f"Sending WhatsApp location to {to}")

        # Send location
        result = await client.send_location(
            to=to,
            latitude=latitude,
            longitude=longitude,
            name=name,
            address=address,
        )

        # Set outputs
        self._set_success_outputs(result.message_id, result.phone_number)
        self.set_output_value("latitude", latitude)
        self.set_output_value("longitude", longitude)

        logger.info(f"WhatsApp location sent: {result.message_id}")

        return {
            "success": True,
            "message_id": result.message_id,
            "phone_number": result.phone_number,
            "next_nodes": [],
        }


class WhatsAppSendInteractiveNode(WhatsAppBaseNode):
    """
    Send an interactive message (buttons, lists) via WhatsApp.

    Inputs:
        - to: Recipient phone number
        - interactive_type: "button" or "list"
        - body_text: Message body
        - action_json: JSON string of action object
        - header_json: Optional JSON header object
        - footer_text: Optional footer text

    Outputs:
        - message_id: Sent message ID
        - phone_number: Recipient phone number
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "whatsapp_send_interactive"
    NODE_CATEGORY = "messaging"
    NODE_DISPLAY_NAME = "WhatsApp: Send Interactive"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="WhatsApp Send Interactive", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Interactive-specific ports
        self.add_input_port(
            "interactive_type", PortType.INPUT, DataType.STRING, required=True
        )
        self.add_input_port("body_text", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port(
            "action_json", PortType.INPUT, DataType.STRING, required=True
        )
        self.add_input_port(
            "header_json", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "footer_text", PortType.INPUT, DataType.STRING, required=False
        )

        # Additional output
        self.add_output_port("interactive_type", PortType.OUTPUT, DataType.STRING)

    async def _execute_whatsapp(
        self,
        context: ExecutionContext,
        client: WhatsAppClient,
    ) -> ExecutionResult:
        """Send an interactive message."""
        to = self._get_recipient(context)

        # Get interactive type
        interactive_type = self.get_parameter("interactive_type")
        if hasattr(context, "resolve_value"):
            interactive_type = context.resolve_value(interactive_type)

        if interactive_type not in ["button", "list"]:
            self._set_error_outputs("Interactive type must be 'button' or 'list'")
            return {
                "success": False,
                "error": "Interactive type must be 'button' or 'list'",
                "next_nodes": [],
            }

        # Get body text
        body_text = self.get_parameter("body_text")
        if hasattr(context, "resolve_value"):
            body_text = context.resolve_value(body_text)

        if not body_text:
            self._set_error_outputs("Body text is required")
            return {
                "success": False,
                "error": "Body text is required",
                "next_nodes": [],
            }

        # Get action (JSON string)
        action_json = self.get_parameter("action_json")
        if hasattr(context, "resolve_value"):
            action_json = context.resolve_value(action_json)

        try:
            action = json.loads(action_json)
        except json.JSONDecodeError as e:
            self._set_error_outputs(f"Invalid action JSON: {e}")
            return {
                "success": False,
                "error": f"Invalid action JSON: {e}",
                "next_nodes": [],
            }

        # Get optional header
        header = None
        header_json = self.get_parameter("header_json")
        if header_json:
            if hasattr(context, "resolve_value"):
                header_json = context.resolve_value(header_json)
            try:
                header = json.loads(header_json)
            except json.JSONDecodeError as e:
                self._set_error_outputs(f"Invalid header JSON: {e}")
                return {
                    "success": False,
                    "error": f"Invalid header JSON: {e}",
                    "next_nodes": [],
                }

        # Get optional footer
        footer_text = self.get_parameter("footer_text")
        if footer_text and hasattr(context, "resolve_value"):
            footer_text = context.resolve_value(footer_text)

        logger.debug(f"Sending WhatsApp interactive message to {to}")

        # Send interactive
        result = await client.send_interactive(
            to=to,
            interactive_type=interactive_type,
            body_text=body_text,
            action=action,
            header=header,
            footer_text=footer_text,
        )

        # Set outputs
        self._set_success_outputs(result.message_id, result.phone_number)
        self.set_output_value("interactive_type", interactive_type)

        logger.info(f"WhatsApp interactive sent: {result.message_id}")

        return {
            "success": True,
            "message_id": result.message_id,
            "phone_number": result.phone_number,
            "next_nodes": [],
        }


__all__ = [
    "WhatsAppSendMessageNode",
    "WhatsAppSendTemplateNode",
    "WhatsAppSendImageNode",
    "WhatsAppSendDocumentNode",
    "WhatsAppSendVideoNode",
    "WhatsAppSendLocationNode",
    "WhatsAppSendInteractiveNode",
]
