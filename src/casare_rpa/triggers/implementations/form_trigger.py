"""
CasareRPA - Form Submission Trigger

Trigger that fires when a form is submitted.
This is a specialized webhook for handling form data.
"""

from datetime import UTC, datetime, timezone
from typing import Any, Dict, Optional

from loguru import logger

from casare_rpa.triggers.base import BaseTrigger, TriggerStatus, TriggerType
from casare_rpa.triggers.registry import register_trigger


@register_trigger
class FormTrigger(BaseTrigger):
    """
    Trigger that responds to form submissions.

    This trigger provides a webhook endpoint specifically designed
    for form submissions, with built-in validation and field mapping.

    Configuration options:
        form_id: Unique identifier for the form
        fields: Expected form fields with types and validation
        required_fields: List of required field names
        redirect_url: URL to redirect after form submission
        success_message: Message to show on successful submission

    Payload provided to workflow:
        form_id: ID of the submitted form
        fields: Dictionary of submitted field values
        submitted_at: When the form was submitted
        submitter_ip: IP address of submitter (if available)
    """

    trigger_type = TriggerType.FORM
    display_name = "Form Submission"
    description = "Trigger when a form is submitted"
    icon = "clipboard-list"
    category = "External"

    async def start(self) -> bool:
        """
        Start the form submission trigger.

        The form endpoint is handled by TriggerManager's HTTP server.
        """
        self._status = TriggerStatus.ACTIVE
        form_id = self.config.config.get("form_id", self.config.id)
        logger.info(f"Form trigger started: {self.config.name} (form_id: {form_id})")
        return True

    async def stop(self) -> bool:
        """Stop the form submission trigger."""
        self._status = TriggerStatus.INACTIVE
        logger.info(f"Form trigger stopped: {self.config.name}")
        return True

    async def process_submission(
        self, form_data: dict[str, Any], submitter_ip: str | None = None
    ) -> tuple[bool, str | None]:
        """
        Process a form submission.

        Called by TriggerManager when a form is submitted to this trigger's endpoint.

        Args:
            form_data: Dictionary of form field values
            submitter_ip: IP address of the submitter

        Returns:
            Tuple of (success, error_message)
        """
        config = self.config.config

        # Validate required fields
        required_fields = config.get("required_fields", [])
        for field in required_fields:
            if field not in form_data or not form_data[field]:
                return False, f"Required field missing: {field}"

        # Validate field types (basic validation)
        field_definitions = config.get("fields", {})
        for field_name, field_value in form_data.items():
            if field_name in field_definitions:
                field_type = field_definitions[field_name].get("type", "string")
                validation_error = self._validate_field(field_name, field_value, field_type)
                if validation_error:
                    return False, validation_error

        # Build payload
        payload = {
            "form_id": config.get("form_id", self.config.id),
            "fields": form_data,
            "submitted_at": datetime.now(UTC).isoformat(),
            "submitter_ip": submitter_ip,
        }

        # Also flatten fields into payload for easy variable access
        payload.update(form_data)

        metadata = {
            "source": "form",
            "form_name": self.config.name,
        }

        success = await self.emit(payload, metadata)
        return success, None if success else "Failed to process form"

    def _validate_field(self, field_name: str, field_value: Any, field_type: str) -> str | None:
        """Validate a form field value."""
        if field_type == "string":
            if not isinstance(field_value, str):
                return f"Field '{field_name}' must be a string"

        elif field_type == "number":
            try:
                float(field_value)
            except (TypeError, ValueError):
                return f"Field '{field_name}' must be a number"

        elif field_type == "integer":
            try:
                int(field_value)
            except (TypeError, ValueError):
                return f"Field '{field_name}' must be an integer"

        elif field_type == "email":
            import re

            if not re.match(r"^[^@]+@[^@]+\.[^@]+$", str(field_value)):
                return f"Field '{field_name}' must be a valid email"

        elif field_type == "boolean":
            if not isinstance(field_value, bool) and field_value not in [
                "true",
                "false",
                "1",
                "0",
            ]:
                return f"Field '{field_name}' must be a boolean"

        return None

    def validate_config(self) -> tuple[bool, str | None]:
        """Validate form trigger configuration."""
        # Form trigger has minimal required config
        return True, None

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get JSON schema for form trigger configuration."""
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Trigger name"},
                "enabled": {"type": "boolean", "default": True},
                "priority": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 3,
                    "default": 1,
                },
                "cooldown_seconds": {"type": "integer", "minimum": 0, "default": 0},
                "form_id": {
                    "type": "string",
                    "description": "Unique form identifier",
                },
                "fields": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": [
                                    "string",
                                    "number",
                                    "integer",
                                    "email",
                                    "boolean",
                                    "date",
                                ],
                            },
                            "label": {"type": "string"},
                            "placeholder": {"type": "string"},
                            "default": {},
                        },
                    },
                    "description": "Form field definitions",
                },
                "required_fields": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "Required field names",
                },
                "redirect_url": {
                    "type": "string",
                    "description": "URL to redirect after submission",
                },
                "success_message": {
                    "type": "string",
                    "default": "Form submitted successfully",
                    "description": "Message to show on success",
                },
            },
            "required": ["name"],
        }
