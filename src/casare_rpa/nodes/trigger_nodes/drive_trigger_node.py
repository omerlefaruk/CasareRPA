"""
CasareRPA - Google Drive Trigger Node

Trigger node that monitors Google Drive for file changes.
Workflow starts when files are created, modified, or deleted.
"""

from typing import Any, Dict, Optional

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.trigger_nodes.base_trigger_node import BaseTriggerNode
from casare_rpa.triggers.base import TriggerType


@properties(
    # Connection settings
    PropertyDef(
        "credential_name",
        PropertyType.STRING,
        default="google",
        label="Credential Name",
        placeholder="google",
        tooltip="Name of stored Google OAuth credential",
        tab="connection",
    ),
    # Monitoring settings
    PropertyDef(
        "polling_interval",
        PropertyType.INTEGER,
        default=60,
        label="Polling Interval (sec)",
        tooltip="Seconds between checks for changes",
    ),
    PropertyDef(
        "folder_id",
        PropertyType.STRING,
        default="",
        label="Folder ID",
        placeholder="1ABC123xyz...",
        tooltip="Google Drive folder ID to monitor (empty = entire drive)",
    ),
    PropertyDef(
        "include_subfolders",
        PropertyType.BOOLEAN,
        default=True,
        label="Include Subfolders",
        tooltip="Monitor subfolders recursively",
    ),
    # Event filters
    PropertyDef(
        "event_types",
        PropertyType.STRING,
        default="created,modified",
        label="Event Types",
        placeholder="created,modified,deleted,moved",
        tooltip="Comma-separated events to trigger on",
    ),
    PropertyDef(
        "file_types",
        PropertyType.STRING,
        default="",
        label="File Types",
        placeholder="pdf,xlsx,docx",
        tooltip="Comma-separated file extensions to filter (empty = all)",
    ),
    PropertyDef(
        "mime_types",
        PropertyType.STRING,
        default="",
        label="MIME Types",
        placeholder="application/pdf,image/*",
        tooltip="Comma-separated MIME types to filter (empty = all)",
        tab="advanced",
    ),
    PropertyDef(
        "name_pattern",
        PropertyType.STRING,
        default="",
        label="Name Pattern",
        placeholder="Invoice_*.pdf",
        tooltip="Glob pattern for file names (empty = all)",
    ),
    # Advanced
    PropertyDef(
        "ignore_own_changes",
        PropertyType.BOOLEAN,
        default=True,
        label="Ignore Own Changes",
        tooltip="Don't trigger on changes made by this automation",
        tab="advanced",
    ),
)
@node(category="triggers", exec_inputs=[])
class DriveTriggerNode(BaseTriggerNode):
    """
    Google Drive trigger node that monitors for file changes.

    Uses Drive API changes feed to detect file modifications.
    Requires Google OAuth credentials with Drive scope.

    Outputs:
    - file_id: Google Drive file ID
    - file_name: Name of the file
    - mime_type: MIME type of the file
    - event_type: Type of change (created, modified, deleted, moved)
    - modified_time: Last modification timestamp
    - size: File size in bytes
    - parent_id: Parent folder ID
    - parent_name: Parent folder name
    - web_view_link: URL to view file in browser
    - download_url: Direct download URL (for non-Google files)
    - changed_by: Email of user who made the change
    - raw_change: Full change object from API
    """

    # @category: trigger
    # @requires: none
    # @ports: none -> none

    trigger_display_name = "Google Drive"
    trigger_description = "Trigger workflow when Google Drive files change"
    trigger_icon = "drive"
    trigger_category = "triggers"

    def __init__(self, node_id: str, config: Optional[Dict] = None) -> None:
        super().__init__(node_id, config)
        self.name = "Drive Trigger"
        self.node_type = "DriveTriggerNode"

    def _define_payload_ports(self) -> None:
        """Define Drive-specific output ports."""
        self.add_output_port("file_id", DataType.STRING, "File ID")
        self.add_output_port("file_name", DataType.STRING, "File Name")
        self.add_output_port("mime_type", DataType.STRING, "MIME Type")
        self.add_output_port("event_type", DataType.STRING, "Event Type")
        self.add_output_port("modified_time", DataType.STRING, "Modified Time")
        self.add_output_port("size", DataType.INTEGER, "Size (bytes)")
        self.add_output_port("parent_id", DataType.STRING, "Parent Folder ID")
        self.add_output_port("parent_name", DataType.STRING, "Parent Folder Name")
        self.add_output_port("web_view_link", DataType.STRING, "Web View Link")
        self.add_output_port("download_url", DataType.STRING, "Download URL")
        self.add_output_port("changed_by", DataType.STRING, "Changed By")
        self.add_output_port("raw_change", DataType.DICT, "Raw Change")

    def get_trigger_type(self) -> TriggerType:
        return TriggerType.DRIVE

    def get_trigger_config(self) -> Dict[str, Any]:
        """Get Drive-specific configuration."""
        # Parse comma-separated lists
        event_types_str = self.get_parameter("event_types", "created,modified")
        event_types = [e.strip() for e in event_types_str.split(",") if e.strip()]

        file_types_str = self.get_parameter("file_types", "")
<<<<<<< HEAD
        file_types = [
            ft.strip().lstrip(".") for ft in file_types_str.split(",") if ft.strip()
        ]
=======
        file_types = [ft.strip().lstrip(".") for ft in file_types_str.split(",") if ft.strip()]
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e

        mime_types_str = self.get_parameter("mime_types", "")
        mime_types = [mt.strip() for mt in mime_types_str.split(",") if mt.strip()]

        return {
            "credential_name": self.get_parameter("credential_name", "google"),
            "polling_interval": self.get_parameter("polling_interval", 60),
            "folder_id": self.get_parameter("folder_id", ""),
            "include_subfolders": self.get_parameter("include_subfolders", True),
            "event_types": event_types,
            "file_types": file_types,
            "mime_types": mime_types,
            "name_pattern": self.get_parameter("name_pattern", ""),
            "ignore_own_changes": self.get_parameter("ignore_own_changes", True),
        }
