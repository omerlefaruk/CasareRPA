"""Visual nodes for Google Drive operations."""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


# =============================================================================
# File Operations
# =============================================================================


class VisualDriveUploadFileNode(VisualNode):
    """Visual representation of DriveUploadFileNode.

    Widgets are auto-generated from DriveUploadFileNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Upload File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveUploadFileNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_input("file_name", DataType.STRING)
        self.add_typed_input("folder_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("file_id", DataType.STRING)
        self.add_typed_output("file_url", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDriveDownloadFileNode(VisualNode):
    """Visual representation of DriveDownloadFileNode.

    Widgets are auto-generated from DriveDownloadFileNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Download File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveDownloadFileNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_id", DataType.STRING)
        self.add_typed_input("destination", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("file_path", DataType.STRING)
        self.add_typed_output("file_size", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDriveDeleteFileNode(VisualNode):
    """Visual representation of DriveDeleteFileNode.

    Widgets are auto-generated from DriveDeleteFileNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Delete File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveDeleteFileNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDriveCopyFileNode(VisualNode):
    """Visual representation of DriveCopyFileNode.

    Widgets are auto-generated from DriveCopyFileNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Copy File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveCopyFileNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_id", DataType.STRING)
        self.add_typed_input("new_name", DataType.STRING)
        self.add_typed_input("folder_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("new_file_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDriveMoveFileNode(VisualNode):
    """Visual representation of DriveMoveFileNode.

    Widgets are auto-generated from DriveMoveFileNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Move File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveMoveFileNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_id", DataType.STRING)
        self.add_typed_input("folder_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDriveRenameFileNode(VisualNode):
    """Visual representation of DriveRenameFileNode.

    Widgets are auto-generated from DriveRenameFileNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Rename File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveRenameFileNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_id", DataType.STRING)
        self.add_typed_input("new_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDriveGetFileNode(VisualNode):
    """Visual representation of DriveGetFileNode.

    Widgets are auto-generated from DriveGetFileNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Get File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveGetFileNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("name", DataType.STRING)
        self.add_typed_output("mime_type", DataType.STRING)
        self.add_typed_output("size", DataType.INTEGER)
        self.add_typed_output("created_time", DataType.STRING)
        self.add_typed_output("modified_time", DataType.STRING)
        self.add_typed_output("web_view_link", DataType.STRING)
        self.add_typed_output("parents", DataType.ARRAY)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


# =============================================================================
# Folder Operations
# =============================================================================


class VisualDriveCreateFolderNode(VisualNode):
    """Visual representation of DriveCreateFolderNode.

    Widgets are auto-generated from DriveCreateFolderNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Create Folder"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveCreateFolderNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("folder_name", DataType.STRING)
        self.add_typed_input("parent_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("folder_id", DataType.STRING)
        self.add_typed_output("folder_url", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDriveListFilesNode(VisualNode):
    """Visual representation of DriveListFilesNode.

    Widgets are auto-generated from DriveListFilesNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: List Files"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveListFilesNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("folder_id", DataType.STRING)
        self.add_typed_input("page_size", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("files", DataType.ARRAY)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("next_page_token", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDriveSearchFilesNode(VisualNode):
    """Visual representation of DriveSearchFilesNode.

    Widgets are auto-generated from DriveSearchFilesNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Search Files"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveSearchFilesNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("query", DataType.STRING)
        self.add_typed_input("page_size", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("files", DataType.ARRAY)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("next_page_token", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


# =============================================================================
# Permissions
# =============================================================================


class VisualDriveShareFileNode(VisualNode):
    """Visual representation of DriveShareFileNode.

    Widgets are auto-generated from DriveShareFileNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Share File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveShareFileNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_id", DataType.STRING)
        self.add_typed_input("email", DataType.STRING)
        self.add_typed_input("role", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("permission_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDriveRemovePermissionNode(VisualNode):
    """Visual representation of DriveRemovePermissionNode.

    Widgets are auto-generated from DriveRemovePermissionNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Remove Permission"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveRemovePermissionNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_id", DataType.STRING)
        self.add_typed_input("permission_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDriveGetPermissionsNode(VisualNode):
    """Visual representation of DriveGetPermissionsNode.

    Widgets are auto-generated from DriveGetPermissionsNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Get Permissions"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveGetPermissionsNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("permissions", DataType.ARRAY)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


# =============================================================================
# Export
# =============================================================================


class VisualDriveExportFileNode(VisualNode):
    """Visual representation of DriveExportFileNode.

    Widgets are auto-generated from DriveExportFileNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Export File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveExportFileNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_id", DataType.STRING)
        self.add_typed_input("export_format", DataType.STRING)
        self.add_typed_input("destination", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("file_path", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


# =============================================================================
# Batch Operations
# =============================================================================


class VisualDriveBatchDeleteNode(VisualNode):
    """Visual representation of DriveBatchDeleteNode.

    Widgets are auto-generated from DriveBatchDeleteNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Batch Delete"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveBatchDeleteNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_ids", DataType.ARRAY)
        self.add_exec_output("exec_out")
        self.add_typed_output("deleted_count", DataType.INTEGER)
        self.add_typed_output("failed_count", DataType.INTEGER)
        self.add_typed_output("results", DataType.ARRAY)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDriveBatchMoveNode(VisualNode):
    """Visual representation of DriveBatchMoveNode.

    Widgets are auto-generated from DriveBatchMoveNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Batch Move"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveBatchMoveNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_ids", DataType.ARRAY)
        self.add_typed_input("folder_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("moved_count", DataType.INTEGER)
        self.add_typed_output("failed_count", DataType.INTEGER)
        self.add_typed_output("results", DataType.ARRAY)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDriveBatchCopyNode(VisualNode):
    """Visual representation of DriveBatchCopyNode.

    Widgets are auto-generated from DriveBatchCopyNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Batch Copy"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveBatchCopyNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_ids", DataType.ARRAY)
        self.add_typed_input("folder_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("copied_count", DataType.INTEGER)
        self.add_typed_output("failed_count", DataType.INTEGER)
        self.add_typed_output("results", DataType.ARRAY)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)
