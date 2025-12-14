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

    def setup_file_widget(self, mime_types: list = None) -> None:
        """Setup Drive file picker widget (call from subclass if needed)."""
        self._file_widget = NodeGoogleDriveFileWidget(
            name="file_id",
            label="File",
            credential_widget=self._cred_widget,
            mime_types=mime_types,
        )
        if self._file_widget:
            self.add_custom_widget(self._file_widget)
            self._file_widget.setParentItem(self.view)

    def setup_folder_widget(
        self, label: str = "Folder", name: str = "folder_id"
    ) -> None:
        """Setup Drive folder navigator widget (call from subclass if needed)."""
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
        self.add_typed_input("file_id", DataType.STRING)
        self.add_typed_input("destination_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("file_path", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_file_widget()
        self.add_text_input(
            "destination_path",
            "Destination Path",
            text="",
            placeholder_text="C:\\Downloads\\file.pdf",
            tab="config",
        )


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
        self.add_text_input(
            "destination_folder",
            "Destination Folder",
            text="",
            placeholder_text="C:\\Downloads\\",
            tab="config",
        )


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
        self.add_typed_input("destination_folder", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("file_paths", DataType.LIST)
        self.add_typed_output("downloaded_count", DataType.INTEGER)
        self.add_typed_output("failed_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.add_text_input(
            "destination_folder",
            "Destination Folder",
            text="",
            placeholder_text="C:\\Downloads\\",
            tab="config",
        )


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
        self.add_text_input(
            "new_name",
            "New Name",
            text="",
            placeholder_text="Enter new filename",
            tab="config",
        )


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
        self.add_typed_output(
            "folder_id", DataType.STRING
        )  # Passthrough for downstream
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
        self.add_text_input(
            "query",
            "Search Query",
            text="",
            placeholder_text="name contains 'report'",
            tab="config",
        )


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
        self.add_text_input(
            "email",
            "Email",
            text="",
            placeholder_text="user@example.com",
            tab="config",
        )
        self.add_combo_menu(
            "role",
            "Role",
            items=["reader", "writer", "commenter", "owner"],
            tab="config",
        )
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
        self.add_text_input(
            "permission_id",
            "Permission ID",
            text="",
            placeholder_text="Permission ID to remove",
            tab="config",
        )


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
        self.add_combo_menu(
            "access_type",
            "Link Access",
            items=["anyone", "anyoneWithLink"],
            tab="config",
        )
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
