"""
CasareRPA - SSE (Server-Sent Events) Trigger Node

Trigger node that listens to a Server-Sent Events stream.
"""

from typing import Any, Dict, Optional

from casare_rpa.domain.decorators import node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.triggers.base import TriggerType

from .base_trigger_node import BaseTriggerNode, trigger_node


@node_schema(
    PropertyDef(
        "sse_url",
        PropertyType.STRING,
        required=True,
        label="SSE URL",
        placeholder="https://api.example.com/events",
        tooltip="URL of the SSE endpoint",
    ),
    PropertyDef(
        "event_types",
        PropertyType.STRING,
        default="",
        label="Event Types",
        placeholder="message,update,notification",
        tooltip="Comma-separated event types to listen for (empty = all)",
    ),
    PropertyDef(
        "headers",
        PropertyType.JSON,
        default="{}",
        label="Request Headers",
        placeholder='{"Authorization": "Bearer token"}',
        tooltip="JSON object of headers to send with request",
    ),
    PropertyDef(
        "reconnect_delay_seconds",
        PropertyType.INTEGER,
        default=5,
        label="Reconnect Delay (seconds)",
        tooltip="Delay before reconnecting on disconnect",
    ),
    PropertyDef(
        "max_reconnect_attempts",
        PropertyType.INTEGER,
        default=10,
        label="Max Reconnect Attempts",
        tooltip="Maximum reconnection attempts (0 = unlimited)",
    ),
    PropertyDef(
        "timeout_seconds",
        PropertyType.INTEGER,
        default=0,
        label="Connection Timeout (seconds)",
        tooltip="Connection timeout (0 = no timeout)",
    ),
)
@trigger_node
class SSETriggerNode(BaseTriggerNode):
    """
    SSE trigger node that listens to Server-Sent Events.

    Outputs:
    - event_type: Type of SSE event
    - data: Event data (parsed as JSON if possible)
    - raw_data: Raw event data string
    - event_id: Event ID (if provided)
    - retry: Retry value (if provided)
    - timestamp: When the event was received
    """

    trigger_display_name = "SSE"
    trigger_description = "Trigger on Server-Sent Events"
    trigger_icon = "stream"
    trigger_category = "triggers"

    def __init__(self, node_id: str, config: Optional[Dict] = None) -> None:
        super().__init__(node_id, config)
        self.name = "SSE Trigger"
        self.node_type = "SSETriggerNode"

    def _define_payload_ports(self) -> None:
        """Define SSE-specific output ports."""
        self.add_output_port("event_type", DataType.STRING, "Event Type")
        self.add_output_port("data", DataType.ANY, "Data (parsed)")
        self.add_output_port("raw_data", DataType.STRING, "Raw Data")
        self.add_output_port("event_id", DataType.STRING, "Event ID")
        self.add_output_port("retry", DataType.INTEGER, "Retry")
        self.add_output_port("timestamp", DataType.STRING, "Timestamp")

    def get_trigger_type(self) -> TriggerType:
        return TriggerType.SSE

    def get_trigger_config(self) -> Dict[str, Any]:
        """Get SSE-specific configuration."""
        event_types_str = self.config.get("event_types", "")
        event_types = [e.strip() for e in event_types_str.split(",") if e.strip()]

        return {
            "sse_url": self.config.get("sse_url", ""),
            "event_types": event_types,
            "headers": self.config.get("headers", "{}"),
            "reconnect_delay_seconds": self.config.get("reconnect_delay_seconds", 5),
            "max_reconnect_attempts": self.config.get("max_reconnect_attempts", 10),
            "timeout_seconds": self.config.get("timeout_seconds", 0),
            # Mark as SSE for the trigger implementation
            "_trigger_subtype": "sse",
        }
