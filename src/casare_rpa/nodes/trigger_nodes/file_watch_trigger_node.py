"""
CasareRPA - File Watch Trigger Node

Trigger node that fires when files change in a watched directory.
"""

from typing import Any, Dict, Optional

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.trigger_nodes.base_trigger_node import BaseTriggerNode
from casare_rpa.triggers.base import TriggerType


@properties(
    PropertyDef(
        "watch_path",
        PropertyType.DIRECTORY_PATH,
        required=True,
        label="Watch Path",
        placeholder="C:\\Documents\\Inbox",
        tooltip="Directory to watch for changes",
    ),
    PropertyDef(
        "patterns",
        PropertyType.STRING,
        default="*",
        label="File Patterns",
        placeholder="*.pdf,*.xlsx",
        tooltip="Comma-separated glob patterns to match",
    ),
    PropertyDef(
        "events",
        PropertyType.STRING,
        default="created,modified",
        label="Events",
        placeholder="created,modified,deleted,moved",
        tooltip="Comma-separated events to watch",
    ),
    PropertyDef(
        "recursive",
        PropertyType.BOOLEAN,
        default=True,
        label="Recursive",
        tooltip="Watch subdirectories",
    ),
    PropertyDef(
        "ignore_patterns",
        PropertyType.STRING,
        default="*.tmp,~*",
        label="Ignore Patterns",
        placeholder="*.tmp,~*",
        tooltip="Patterns to ignore",
    ),
    PropertyDef(
        "debounce_ms",
        PropertyType.INTEGER,
        default=500,
        label="Debounce (ms)",
        tooltip="Minimum time between events for same file",
    ),
    PropertyDef(
        "include_hidden",
        PropertyType.BOOLEAN,
        default=False,
        label="Include Hidden Files",
        tooltip="Include hidden files and directories",
    ),
)
@node(category="triggers", exec_inputs=[])
class FileWatchTriggerNode(BaseTriggerNode):
    """
    File watch trigger node that fires when files change.

    Outputs:
    - file_path: Full path to the changed file
    - file_name: Name of the file
    - event_type: Type of event (created/modified/deleted/moved)
    - directory: Parent directory path
    - old_path: Previous path (for moved events)
    """

    # @category: trigger
    # @requires: none
    # @ports: none -> none

    trigger_display_name = "File Watch"
    trigger_description = "Trigger when files change"
    trigger_icon = "folder"
    trigger_category = "triggers"

    def __init__(self, node_id: str, config: Optional[Dict] = None) -> None:
        super().__init__(node_id, config)
        self.name = "File Watch Trigger"
        self.node_type = "FileWatchTriggerNode"

    def _define_payload_ports(self) -> None:
        """Define file watch-specific output ports."""
        self.add_output_port("file_path", DataType.STRING, "File Path")
        self.add_output_port("file_name", DataType.STRING, "File Name")
        self.add_output_port("event_type", DataType.STRING, "Event Type")
        self.add_output_port("directory", DataType.STRING, "Directory")
        self.add_output_port("old_path", DataType.STRING, "Old Path (moved)")

    def get_trigger_type(self) -> TriggerType:
        return TriggerType.FILE_WATCH

    def get_trigger_config(self) -> Dict[str, Any]:
        """Get file watch-specific configuration."""
        patterns_str = self.get_parameter("patterns", "*")
        patterns = [p.strip() for p in patterns_str.split(",") if p.strip()]

        events_str = self.get_parameter("events", "created,modified")
        events = [e.strip() for e in events_str.split(",") if e.strip()]

        ignore_str = self.get_parameter("ignore_patterns", "*.tmp,~*")
        ignore_patterns = [p.strip() for p in ignore_str.split(",") if p.strip()]

        return {
            "watch_path": self.get_parameter("watch_path", ""),
            "patterns": patterns,
            "events": events,
            "recursive": self.get_parameter("recursive", True),
            "ignore_patterns": ignore_patterns,
            "debounce_ms": self.get_parameter("debounce_ms", 500),
            "include_hidden": self.get_parameter("include_hidden", False),
        }
