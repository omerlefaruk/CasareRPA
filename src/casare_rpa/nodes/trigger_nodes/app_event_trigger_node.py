"""
CasareRPA - App Event Trigger Node

Trigger node that fires on application/system events.
"""

from typing import Any

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.trigger_nodes.base_trigger_node import BaseTriggerNode
from casare_rpa.triggers.base import TriggerType


@properties(
    PropertyDef(
        "event_source",
        PropertyType.CHOICE,
        default="windows",
        choices=["windows", "browser", "rpa"],
        label="Event Source",
        tooltip="Source of events to monitor",
    ),
    # Windows events
    PropertyDef(
        "window_event",
        PropertyType.CHOICE,
        default="focus",
        choices=["focus", "open", "close", "minimize", "maximize"],
        label="Window Event",
        tooltip="Type of window event",
    ),
    PropertyDef(
        "window_title_pattern",
        PropertyType.STRING,
        default="",
        label="Window Title Pattern",
        placeholder=".*Notepad.*",
        tooltip="Regex pattern for window title",
    ),
    PropertyDef(
        "process_name",
        PropertyType.STRING,
        default="",
        label="Process Name",
        placeholder="notepad.exe",
        tooltip="Process name to match",
    ),
    # Browser events
    PropertyDef(
        "browser_event",
        PropertyType.CHOICE,
        default="tab_open",
        choices=["tab_open", "tab_close", "url_change", "page_load"],
        label="Browser Event",
        tooltip="Type of browser event",
    ),
    PropertyDef(
        "url_pattern",
        PropertyType.STRING,
        default="",
        label="URL Pattern",
        placeholder="https://.*\\.example\\.com/.*",
        tooltip="Regex pattern for URL",
    ),
    # RPA events
    PropertyDef(
        "rpa_event",
        PropertyType.CHOICE,
        default="workflow_complete",
        choices=["workflow_complete", "workflow_error", "node_error", "custom"],
        label="RPA Event",
        tooltip="Type of RPA event",
    ),
    PropertyDef(
        "custom_event_name",
        PropertyType.STRING,
        default="",
        label="Custom Event Name",
        placeholder="my_custom_event",
        tooltip="Name of custom RPA event",
    ),
)
@node(category="triggers", exec_inputs=[])
class AppEventTriggerNode(BaseTriggerNode):
    """
    App event trigger node that fires on system/application events.

    Outputs:
    - event_data: Full event data object
    - event_type: Type of event that fired
    - window_title: Window title (if applicable)
    - process_name: Process name (if applicable)
    - url: URL (for browser events)
    - timestamp: When the event occurred
    """

    # @category: trigger
    # @requires: none
    # @ports: none -> none

    trigger_display_name = "App Event"
    trigger_description = "Trigger on application events"
    trigger_icon = "app"
    trigger_category = "triggers"

    def __init__(self, node_id: str, config: dict | None = None) -> None:
        super().__init__(node_id, config)
        self.name = "App Event Trigger"
        self.node_type = "AppEventTriggerNode"

    def _define_payload_ports(self) -> None:
        """Define app event-specific output ports."""
        self.add_output_port("event_data", DataType.DICT, "Event Data")
        self.add_output_port("event_type", DataType.STRING, "Event Type")
        self.add_output_port("window_title", DataType.STRING, "Window Title")
        self.add_output_port("process_name", DataType.STRING, "Process Name")
        self.add_output_port("url", DataType.STRING, "URL")
        self.add_output_port("timestamp", DataType.STRING, "Timestamp")

    def get_trigger_type(self) -> TriggerType:
        return TriggerType.APP_EVENT

    def get_trigger_config(self) -> dict[str, Any]:
        """Get app event-specific configuration."""
        return {
            "event_source": self.get_parameter("event_source", "windows"),
            # Windows
            "window_event": self.get_parameter("window_event", "focus"),
            "window_title_pattern": self.get_parameter("window_title_pattern", ""),
            "process_name": self.get_parameter("process_name", ""),
            # Browser
            "browser_event": self.get_parameter("browser_event", "tab_open"),
            "url_pattern": self.get_parameter("url_pattern", ""),
            # RPA
            "rpa_event": self.get_parameter("rpa_event", "workflow_complete"),
            "custom_event_name": self.get_parameter("custom_event_name", ""),
        }
