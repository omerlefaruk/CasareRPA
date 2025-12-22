"""
CasareRPA - Webhook Trigger

Trigger that fires when an HTTP webhook request is received.
Supports multiple authentication methods:
- API key
- Bearer token
- HMAC signature (SHA256, SHA1, SHA384, SHA512)
"""

from typing import Any, Dict, Optional

from loguru import logger

from casare_rpa.triggers.base import BaseTrigger, TriggerStatus, TriggerType
from casare_rpa.triggers.registry import register_trigger


@register_trigger
class WebhookTrigger(BaseTrigger):
    """
    Trigger that responds to HTTP webhook requests.

    Configuration options:
        endpoint: URL path for the webhook (e.g., "/webhooks/invoice")
        auth_type: Authentication type:
            - none: No authentication
            - api_key: X-API-Key header
            - bearer: Bearer token in Authorization header
            - hmac_sha256: HMAC-SHA256 signature (GitHub-compatible)
            - hmac_sha1: HMAC-SHA1 signature
            - hmac_sha384: HMAC-SHA384 signature
            - hmac_sha512: HMAC-SHA512 signature
        secret: Secret key for authentication
        hmac_header: Custom header name for HMAC signature
        hmac_provider: HMAC provider (github, stripe, generic)
        methods: Allowed HTTP methods (default: ["POST"])
        payload_mapping: JSONPath mappings for extracting data from payload
        headers_filter: Required headers for the request

    The webhook is served by the TriggerManager's HTTP server.
    Requests are routed to this trigger based on the trigger ID or custom endpoint.
    """

    trigger_type = TriggerType.WEBHOOK
    display_name = "Webhook"
    description = "Trigger workflow via HTTP POST request"
    icon = "webhook"
    category = "External"

    async def start(self) -> bool:
        """
        Start the webhook trigger.

        The actual HTTP endpoint is managed by TriggerManager.
        This method just marks the trigger as active.
        """
        self._status = TriggerStatus.ACTIVE
        logger.info(
            f"Webhook trigger started: {self.config.name} "
            f"(endpoint: {self.config.config.get('endpoint', '/hooks/' + self.config.id)})"
        )
        return True

    async def stop(self) -> bool:
        """Stop the webhook trigger."""
        self._status = TriggerStatus.INACTIVE
        logger.info(f"Webhook trigger stopped: {self.config.name}")
        return True

    def validate_config(self) -> tuple[bool, Optional[str]]:
        """Validate webhook configuration."""
        config = self.config.config

        # Endpoint is optional (defaults to /hooks/{trigger_id})
        endpoint = config.get("endpoint", "")
        if endpoint and not endpoint.startswith("/"):
            return False, "Endpoint must start with '/'"

        # Auth type validation
        auth_type = config.get("auth_type", "none")
        valid_auth_types = [
            "none",
            "api_key",
            "bearer",
            "jwt",
            "hmac_sha256",
            "hmac_sha1",
            "hmac_sha384",
            "hmac_sha512",
        ]
        if auth_type not in valid_auth_types:
            return False, f"Invalid auth_type. Must be one of: {valid_auth_types}"

        # Secret required for auth types other than 'none'
        if auth_type != "none" and not config.get("secret"):
            return False, f"Secret is required for auth_type '{auth_type}'"

        # Methods validation
        methods = config.get("methods", ["POST"])
        valid_methods = ["GET", "POST", "PUT", "PATCH", "DELETE"]
        for method in methods:
            if method.upper() not in valid_methods:
                return False, f"Invalid HTTP method: {method}"

        return True, None

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for webhook configuration."""
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
                "endpoint": {
                    "type": "string",
                    "description": "URL path for the webhook (e.g., /webhooks/invoice)",
                    "pattern": "^/.*",
                },
                "auth_type": {
                    "type": "string",
                    "enum": [
                        "none",
                        "api_key",
                        "bearer",
                        "jwt",
                        "hmac_sha256",
                        "hmac_sha1",
                        "hmac_sha384",
                        "hmac_sha512",
                    ],
                    "default": "none",
                    "description": "Authentication method",
                },
                "secret": {
                    "type": "string",
                    "description": "Secret key for authentication or HMAC signing",
                },
                "hmac_header": {
                    "type": "string",
                    "description": "Custom header name for HMAC signature",
                    "default": "X-Webhook-Signature",
                },
                "hmac_provider": {
                    "type": "string",
                    "enum": ["github", "stripe", "generic"],
                    "default": "generic",
                    "description": "HMAC provider format (affects header parsing)",
                },
                "methods": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"],
                    },
                    "default": ["POST"],
                    "description": "Allowed HTTP methods",
                },
                "payload_mapping": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Map payload fields to workflow variables using JSONPath",
                },
                "headers_filter": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Required headers for the request",
                },
            },
            "required": ["name"],
        }
