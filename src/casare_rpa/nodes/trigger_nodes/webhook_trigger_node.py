"""
CasareRPA - Webhook Trigger Node

Trigger node that listens for HTTP webhook requests.
Enhanced with CORS, IP whitelist, authentication, and binary data support.
"""

from typing import Any, Dict, Optional

from casare_rpa.domain.decorators import node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.trigger_nodes.base_trigger_node import (
    BaseTriggerNode,
    trigger_node,
)
from casare_rpa.triggers.base import TriggerType


@node_schema(
    # Basic settings
    PropertyDef(
        "endpoint",
        PropertyType.STRING,
        default="",
        label="Endpoint Path",
        placeholder="/my-webhook",
        tooltip="Custom endpoint path (e.g., /my-webhook). Auto-generated if empty.",
    ),
    PropertyDef(
        "methods",
        PropertyType.STRING,
        default="POST",
        label="HTTP Methods",
        placeholder="POST,GET",
        tooltip="Comma-separated HTTP methods to accept (GET,POST,PUT,DELETE,PATCH)",
    ),
    # Authentication
    PropertyDef(
        "auth_type",
        PropertyType.CHOICE,
        default="none",
        choices=["none", "basic", "header", "jwt"],
        label="Authentication",
        tooltip="Authentication method for webhook requests",
    ),
    PropertyDef(
        "auth_header_name",
        PropertyType.STRING,
        default="X-API-Key",
        label="Auth Header Name",
        tooltip="Header name for header-based auth",
    ),
    PropertyDef(
        "auth_header_value",
        PropertyType.STRING,
        default="",
        label="Auth Header Value",
        tooltip="Expected header value (secret)",
    ),
    PropertyDef(
        "basic_username",
        PropertyType.STRING,
        default="",
        label="Basic Auth Username",
    ),
    PropertyDef(
        "basic_password",
        PropertyType.STRING,
        default="",
        label="Basic Auth Password",
    ),
    PropertyDef(
        "jwt_secret",
        PropertyType.STRING,
        default="",
        label="JWT Secret",
        tooltip="Secret for JWT token validation",
    ),
    # CORS settings
    PropertyDef(
        "cors_enabled",
        PropertyType.BOOLEAN,
        default=False,
        label="Enable CORS",
        tooltip="Allow cross-origin requests",
    ),
    PropertyDef(
        "cors_origins",
        PropertyType.STRING,
        default="*",
        label="Allowed Origins",
        placeholder="https://example.com,https://app.example.com",
        tooltip="Comma-separated allowed origins (* for all)",
    ),
    # IP filtering
    PropertyDef(
        "ip_whitelist",
        PropertyType.STRING,
        default="",
        label="IP Whitelist",
        placeholder="192.168.1.0/24,10.0.0.1",
        tooltip="Comma-separated IPs/CIDRs to allow (empty = all)",
    ),
    PropertyDef(
        "ip_blacklist",
        PropertyType.STRING,
        default="",
        label="IP Blacklist",
        placeholder="1.2.3.4",
        tooltip="Comma-separated IPs/CIDRs to block",
    ),
    # Response settings
    PropertyDef(
        "response_mode",
        PropertyType.CHOICE,
        default="immediate",
        choices=["immediate", "wait_for_workflow", "custom"],
        label="Response Mode",
        tooltip="When to send HTTP response",
    ),
    PropertyDef(
        "response_code",
        PropertyType.INTEGER,
        default=200,
        label="Response Code",
        tooltip="HTTP response code for immediate/custom mode",
    ),
    PropertyDef(
        "response_body",
        PropertyType.STRING,
        default='{"status": "received"}',
        label="Response Body",
        tooltip="JSON response body for immediate/custom mode",
    ),
    # Advanced
    PropertyDef(
        "binary_data_enabled",
        PropertyType.BOOLEAN,
        default=False,
        label="Accept Binary Data",
        tooltip="Accept binary file uploads",
    ),
    PropertyDef(
        "max_payload_size",
        PropertyType.INTEGER,
        default=16777216,  # 16MB
        label="Max Payload Size (bytes)",
    ),
)
@trigger_node
class WebhookTriggerNode(BaseTriggerNode):
    """
    Webhook trigger node that listens for HTTP requests.

    Outputs:
    - payload: Request body (JSON parsed if applicable)
    - headers: Request headers
    - query_params: URL query parameters
    - method: HTTP method used
    - path: Request path
    - client_ip: Client IP address
    """

    # @category: trigger
    # @requires: none
    # @ports: none -> none

    trigger_display_name = "Webhook"
    trigger_description = "Trigger workflow via HTTP webhook"
    trigger_icon = "webhook"
    trigger_category = "triggers"

    def __init__(self, node_id: str, config: Optional[Dict] = None) -> None:
        super().__init__(node_id, config)
        self.name = "Webhook Trigger"
        self.node_type = "WebhookTriggerNode"

    def _define_payload_ports(self) -> None:
        """Define webhook-specific output ports."""
        self.add_output_port("payload", DataType.DICT, "Request Payload")
        self.add_output_port("headers", DataType.DICT, "Request Headers")
        self.add_output_port("query_params", DataType.DICT, "Query Parameters")
        self.add_output_port("method", DataType.STRING, "HTTP Method")
        self.add_output_port("path", DataType.STRING, "Request Path")
        self.add_output_port("client_ip", DataType.STRING, "Client IP")

    def get_trigger_type(self) -> TriggerType:
        return TriggerType.WEBHOOK

    def get_trigger_config(self) -> Dict[str, Any]:
        """Get webhook-specific configuration."""
        methods_str = self.config.get("methods", "POST")
        methods = [m.strip().upper() for m in methods_str.split(",") if m.strip()]

        cors_origins_str = self.config.get("cors_origins", "*")
        cors_origins = [o.strip() for o in cors_origins_str.split(",") if o.strip()]

        ip_whitelist_str = self.config.get("ip_whitelist", "")
        ip_whitelist = [ip.strip() for ip in ip_whitelist_str.split(",") if ip.strip()]

        ip_blacklist_str = self.config.get("ip_blacklist", "")
        ip_blacklist = [ip.strip() for ip in ip_blacklist_str.split(",") if ip.strip()]

        return {
            "endpoint": self.config.get("endpoint", ""),
            "methods": methods,
            # Auth
            "auth_type": self.config.get("auth_type", "none"),
            "auth_header_name": self.config.get("auth_header_name", "X-API-Key"),
            "auth_header_value": self.config.get("auth_header_value", ""),
            "basic_username": self.config.get("basic_username", ""),
            "basic_password": self.config.get("basic_password", ""),
            "jwt_secret": self.config.get("jwt_secret", ""),
            # CORS
            "cors_enabled": self.config.get("cors_enabled", False),
            "cors_origins": cors_origins,
            # IP filtering
            "ip_whitelist": ip_whitelist,
            "ip_blacklist": ip_blacklist,
            # Response
            "response_mode": self.config.get("response_mode", "immediate"),
            "response_code": self.config.get("response_code", 200),
            "response_body": self.config.get("response_body", '{"status": "received"}'),
            # Advanced
            "binary_data_enabled": self.config.get("binary_data_enabled", False),
            "max_payload_size": self.config.get("max_payload_size", 16777216),
        }

    def get_webhook_url(self, base_url: str = "http://localhost:8766") -> str:
        """
        Get the full webhook URL.

        Args:
            base_url: Base URL of the webhook server

        Returns:
            Full webhook URL
        """
        endpoint = self.config.get("endpoint", "")
        if endpoint:
            return f"{base_url}/webhooks{endpoint}"
        # Auto-generated URL based on node ID
        return f"{base_url}/hooks/{self.node_id}"
