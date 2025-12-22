"""Visual nodes for Google Drive operations.

All nodes use cascading credential pickers:
1. NodeGoogleCredentialWidget - Google account selection
2. NodeGoogleDriveFileWidget - File selection (cascades from credential)
3. NodeGoogleDriveFolderWidget - Folder selection (cascades from credential)
"""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.presentation.canvas.graph.node_widgets import (
    NodeGoogleCredentialWidget,
    NodeGoogleDriveFileWidget,
    NodeGoogleDriveFolderWidget,
    NodeFilePathWidget,
    NodeDirectoryPathWidget,
    NodeTextWidget,
)

# Google Drive API scopes
DRIVE_READONLY_SCOPE = ["https://www.googleapis.com/auth/drive.readonly"]
DRIVE_FULL_SCOPE = ["https://www.googleapis.com/auth/drive"]


class VisualGoogleDriveBaseNode(VisualNode):
    """Base class for Google Drive visual nodes with credential picker integration."""

    # Subclasses should set this to DRIVE_READONLY_SCOPE or DRIVE_FULL_SCOPE
    REQUIRED_SCOPES = DRIVE_FULL_SCOPE

    def __init__(self, qgraphics_item=None) -> None:
        super().__init__(qgraphics_item)

    def setup_widgets(self) -> None:
        """Setup credential picker widget."""
        self._cred_widget = NodeGoogleCredentialWidget(
            name="credential_id",
            label="Google Account",
            scopes=self.REQUIRED_SCOPES,
        )
        if self._cred_widget:
            self.add_custom_widget(self._cred_widget)
            self._cred_widget.setParentItem(self.view)

    def _remove_property_if_exists(self, prop_name: str) -> None:
        """
        Remove existing property and its widget to allow replacement.

        Crucial for preventing 'zombie' widgets from lingering on the node
        when switching from standard to custom widgets.
        """
        # 1. Remove from model to prevent schema conflicts
        if hasattr(self, "model") and prop_name in self.model.custom_properties:
            del self.model.custom_properties[prop_name]

        # 2. Get reference to the widget wrapper
        widget = None
        if hasattr(self, "_widgets") and prop_name in self._widgets:
            widget = self._widgets[prop_name]

        if not widget and hasattr(self, "get_widget"):
            widget = self.get_widget(prop_name)

        if widget:
            # 3. Detach from Qt Graphics Scene immediately
            if hasattr(widget, "setParentItem"):
                widget.setParentItem(None)

            # 4. Remove from NodeGraphQt internal tracking
            if hasattr(self, "view") and hasattr(self.view, "_widgets"):
                if prop_name in self.view._widgets:
                    del self.view._widgets[prop_name]

            # 5. Remove from our local tracking
            if hasattr(self, "_widgets") and prop_name in self._widgets:
                del self._widgets[prop_name]

            # 6. Force Qt deletion
            if hasattr(widget, "deleteLater"):
                widget.deleteLater()
            elif hasattr(widget, "setParent"):
                widget.setParent(None)

    def setup_file_widget(self, mime_types: list = None) -> None:
        """Setup Drive file picker widget (call from subclass if needed)."""
        # Remove existing property to avoid NodePropertyError
        self._remove_property_if_exists("file_id")
        self._file_widget = NodeGoogleDriveFileWidget(
            name="file_id",
            label="File",
            credential_widget=self._cred_widget,
            mime_types=mime_types,
        )
        if self._file_widget:
            self.add_custom_widget(self._file_widget)
            self._file_widget.setParentItem(self.view)

    def setup_folder_widget(self, label: str = "Folder", name: str = "folder_id") -> None:
        """Setup Drive folder navigator widget (call from subclass if needed)."""
        # Remove existing property to avoid NodePropertyError
        self._remove_property_if_exists(name)
        self._folder_widget = NodeGoogleDriveFolderWidget(
            name=name,
            label=label,
            credential_widget=self._cred_widget,
            enhanced=True,  # Use full navigator with browse/search/manual ID
        )
        if self._folder_widget:
            self.add_custom_widget(self._folder_widget)
            self._folder_widget.setParentItem(self.view)


# =============================================================================
# File Operations
# =============================================================================


class VisualDriveUploadFileNode(VisualGoogleDriveBaseNode):
    """Visual representation of DriveUploadFileNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Upload File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveUploadFileNode"
    REQUIRED_SCOPES = DRIVE_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_input("file_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("file_id", DataType.STRING)
        self.add_typed_output("file_url", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_folder_widget()


class VisualDriveDownloadFileNode(VisualGoogleDriveBaseNode):
    """Visual representation of DriveDownloadFileNode (single file download)."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Download File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveDownloadFileNode"
    REQUIRED_SCOPES = DRIVE_READONLY_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        # file_id is provided by the file widget from setup_file_widget()
        self.add_typed_input("destination_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("file_path", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_file_widget()
        self._remove_property_if_exists("destination_path")
        widget = NodeFilePathWidget(
            name="destination_path",
            label="Destination Path",
            text="",
            placeholder="C:\\Downloads\\file.pdf",
        )
        self.add_custom_widget(widget)
        widget.setParentItem(self.view)


class VisualDriveDownloadFolderNode(VisualGoogleDriveBaseNode):
    """Visual representation of DriveDownloadFolderNode (download all files from folder)."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Download Folder"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveDownloadFolderNode"
    REQUIRED_SCOPES = DRIVE_READONLY_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("folder_id", DataType.STRING)
        self.add_typed_input("destination_folder", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("file_paths", DataType.LIST)
        self.add_typed_output("downloaded_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_folder_widget(label="Source Folder", name="folder_id")
        self._remove_property_if_exists("destination_folder")
        widget = NodeDirectoryPathWidget(
            name="destination_folder",
            label="Destination Folder",
            text="",
            placeholder="C:\\Downloads\\",
        )
        self.add_custom_widget(widget)
        widget.setParentItem(self.view)


class VisualDriveBatchDownloadNode(VisualGoogleDriveBaseNode):
    """Visual representation of DriveBatchDownloadNode (download list of files)."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Batch Download"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveBatchDownloadNode"
    REQUIRED_SCOPES = DRIVE_READONLY_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("files", DataType.LIST)
        self.add_typed_input("folder_id", DataType.STRING)
        self.add_typed_input("destination_folder", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("file_paths", DataType.LIST)
        self.add_typed_output("downloaded_count", DataType.INTEGER)
        self.add_typed_output("failed_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_folder_widget(label="Folder", name="folder_id")
        self._remove_property_if_exists("destination_folder")
        widget = NodeDirectoryPathWidget(
            name="destination_folder",
            label="Destination Folder",
            text="",
            placeholder="C:\\Downloads\\",
        )
        self.add_custom_widget(widget)
        widget.setParentItem(self.view)


class VisualDriveDeleteFileNode(VisualGoogleDriveBaseNode):
    """Visual representation of DriveDeleteFileNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Delete File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveDeleteFileNode"
    REQUIRED_SCOPES = DRIVE_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_file_widget()


class VisualDriveCopyFileNode(VisualGoogleDriveBaseNode):
    """Visual representation of DriveCopyFileNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Copy File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveCopyFileNode"
    REQUIRED_SCOPES = DRIVE_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("new_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("new_file_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_file_widget()
        self.setup_folder_widget()


class VisualDriveMoveFileNode(VisualGoogleDriveBaseNode):
    """Visual representation of DriveMoveFileNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Move File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveMoveFileNode"
    REQUIRED_SCOPES = DRIVE_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_file_widget()
        self.setup_folder_widget()


class VisualDriveRenameFileNode(VisualGoogleDriveBaseNode):
    """Visual representation of DriveRenameFileNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Rename File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveRenameFileNode"
    REQUIRED_SCOPES = DRIVE_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("new_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()  # credential picker
        self.setup_file_widget()
        self._remove_property_if_exists("new_name")
        widget = NodeTextWidget(
            name="new_name",
            label="New Name",
            text="",
            placeholder_text="Enter new filename",
        )
        self.add_custom_widget(widget)
        widget.setParentItem(self.view)


class VisualDriveGetFileNode(VisualGoogleDriveBaseNode):
    """Visual representation of DriveGetFileNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Get File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveGetFileNode"
    REQUIRED_SCOPES = DRIVE_READONLY_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("name", DataType.STRING)
        self.add_typed_output("mime_type", DataType.STRING)
        self.add_typed_output("size", DataType.INTEGER)
        self.add_typed_output("created_time", DataType.STRING)
        self.add_typed_output("modified_time", DataType.STRING)
        self.add_typed_output("web_view_link", DataType.STRING)
        self.add_typed_output("parents", DataType.LIST)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_file_widget()


# =============================================================================
# Folder Operations
# =============================================================================


class VisualDriveCreateFolderNode(VisualGoogleDriveBaseNode):
    """Visual representation of DriveCreateFolderNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Create Folder"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveCreateFolderNode"
    REQUIRED_SCOPES = DRIVE_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("folder_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("folder_id", DataType.STRING)
        self.add_typed_output("folder_url", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        # Parent folder picker - use enhanced navigator
        self.setup_folder_widget(label="Parent Folder", name="parent_id")


class VisualDriveListFilesNode(VisualGoogleDriveBaseNode):
    """Visual representation of DriveListFilesNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: List Files"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveListFilesNode"
    REQUIRED_SCOPES = DRIVE_READONLY_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("folder_id", DataType.STRING)
        self.add_typed_input("max_results", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("files", DataType.LIST)
        self.add_typed_output("file_count", DataType.INTEGER)
        self.add_typed_output("folder_id", DataType.STRING)  # Passthrough for downstream
        self.add_typed_output("has_more", DataType.BOOLEAN)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_folder_widget()


class VisualDriveSearchFilesNode(VisualGoogleDriveBaseNode):
    """Visual representation of DriveSearchFilesNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Search Files"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveSearchFilesNode"
    REQUIRED_SCOPES = DRIVE_READONLY_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("query", DataType.STRING)
        self.add_typed_input("page_size", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("files", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("next_page_token", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()  # credential picker
        self._remove_property_if_exists("query")
        widget = NodeTextWidget(
            name="query",
            label="Search Query",
            text="",
            placeholder_text="name contains 'report'",
        )
        self.add_custom_widget(widget)
        widget.setParentItem(self.view)


# =============================================================================
# Permissions
# =============================================================================


class VisualDriveShareFileNode(VisualGoogleDriveBaseNode):
    """Visual representation of DriveShareFileNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Share File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveShareFileNode"
    REQUIRED_SCOPES = DRIVE_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("email", DataType.STRING)
        self.add_typed_input("role", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("permission_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_file_widget()
        self._remove_property_if_exists("email")
        widget = NodeTextWidget(
            name="email",
            label="Email",
            text="",
            placeholder_text="user@example.com",
        )
        self.add_custom_widget(widget)
        widget.setParentItem(self.view)
        self._remove_property_if_exists("role")
        self.add_combo_menu(
            "role",
            "Role",
            items=["reader", "writer", "commenter", "owner"],
            tab="config",
        )
        self._remove_property_if_exists("permission_type")
        self.add_combo_menu(
            "permission_type",
            "Type",
            items=["user", "group", "domain", "anyone"],
            tab="config",
        )


class VisualDriveRemoveShareNode(VisualGoogleDriveBaseNode):
    """Visual representation of DriveRemoveShareNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Remove Share"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveRemoveShareNode"
    REQUIRED_SCOPES = DRIVE_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("permission_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_file_widget()
        self._remove_property_if_exists("permission_id")
        widget = NodeTextWidget(
            name="permission_id",
            label="Permission ID",
            text="",
            placeholder_text="Permission ID to remove",
        )
        self.add_custom_widget(widget)
        widget.setParentItem(self.view)


class VisualDriveGetPermissionsNode(VisualGoogleDriveBaseNode):
    """Visual representation of DriveGetPermissionsNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Get Permissions"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveGetPermissionsNode"
    REQUIRED_SCOPES = DRIVE_READONLY_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("permissions", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_file_widget()


class VisualDriveCreateShareLinkNode(VisualGoogleDriveBaseNode):
    """Visual representation of DriveCreateShareLinkNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Create Share Link"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveCreateShareLinkNode"
    REQUIRED_SCOPES = DRIVE_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("share_link", DataType.STRING)
        self.add_typed_output("permission_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_file_widget()
        self._remove_property_if_exists("access_type")
        self.add_combo_menu(
            "access_type",
            "Link Access",
            items=["anyone", "anyoneWithLink"],
            tab="config",
        )
        self._remove_property_if_exists("link_role")
        self.add_combo_menu(
            "link_role",
            "Link Role",
            items=["reader", "writer", "commenter"],
            tab="config",
        )


# =============================================================================
# Export
# =============================================================================


class VisualDriveExportFileNode(VisualGoogleDriveBaseNode):
    """Visual representation of DriveExportFileNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Export File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveExportFileNode"
    REQUIRED_SCOPES = DRIVE_READONLY_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("export_format", DataType.STRING)
        self.add_typed_input("destination", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("file_path", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_file_widget()


# =============================================================================
# Batch Operations
# =============================================================================


class VisualDriveBatchDeleteNode(VisualGoogleDriveBaseNode):
    """Visual representation of DriveBatchDeleteNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Batch Delete"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveBatchDeleteNode"
    REQUIRED_SCOPES = DRIVE_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_ids", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("deleted_count", DataType.INTEGER)
        self.add_typed_output("failed_count", DataType.INTEGER)
        self.add_typed_output("results", DataType.LIST)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()  # credential picker


class VisualDriveBatchMoveNode(VisualGoogleDriveBaseNode):
    """Visual representation of DriveBatchMoveNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Batch Move"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveBatchMoveNode"
    REQUIRED_SCOPES = DRIVE_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_ids", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("moved_count", DataType.INTEGER)
        self.add_typed_output("failed_count", DataType.INTEGER)
        self.add_typed_output("results", DataType.LIST)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_folder_widget()


class VisualDriveBatchCopyNode(VisualGoogleDriveBaseNode):
    """Visual representation of DriveBatchCopyNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Batch Copy"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveBatchCopyNode"
    REQUIRED_SCOPES = DRIVE_FULL_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_ids", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("copied_count", DataType.INTEGER)
        self.add_typed_output("failed_count", DataType.INTEGER)
        self.add_typed_output("results", DataType.LIST)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_folder_widget()
