"""Visual nodes for Google Drive operations."""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


# =============================================================================
# File Operations
# =============================================================================


class VisualDriveUploadFileNode(VisualNode):
    """Visual representation of DriveUploadFileNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Upload File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveUploadFileNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "file_path",
            "File Path",
            text="",
            tab="properties",
            placeholder_text="C:/Documents/file.pdf",
        )
        self.add_text_input(
            "file_name",
            "File Name (optional)",
            text="",
            tab="properties",
            placeholder_text="Leave empty for original name",
        )
        self.add_text_input(
            "folder_id",
            "Folder ID",
            text="",
            tab="properties",
            placeholder_text="Destination folder ID (empty=root)",
        )

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
    """Visual representation of DriveDownloadFileNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Download File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveDownloadFileNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("file_id", "File ID", text="", tab="properties")
        self.add_text_input(
            "destination",
            "Destination Path",
            text="",
            tab="properties",
            placeholder_text="C:/Downloads/file.pdf",
        )

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
    """Visual representation of DriveDeleteFileNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Delete File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveDeleteFileNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("file_id", "File ID", text="", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDriveCopyFileNode(VisualNode):
    """Visual representation of DriveCopyFileNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Copy File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveCopyFileNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("file_id", "File ID", text="", tab="properties")
        self.add_text_input(
            "new_name", "New Name (optional)", text="", tab="properties"
        )
        self.add_text_input(
            "folder_id", "Destination Folder ID", text="", tab="properties"
        )

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
    """Visual representation of DriveMoveFileNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Move File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveMoveFileNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("file_id", "File ID", text="", tab="properties")
        self.add_text_input(
            "folder_id", "Destination Folder ID", text="", tab="properties"
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_id", DataType.STRING)
        self.add_typed_input("folder_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDriveRenameFileNode(VisualNode):
    """Visual representation of DriveRenameFileNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Rename File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveRenameFileNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("file_id", "File ID", text="", tab="properties")
        self.add_text_input("new_name", "New Name", text="", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_id", DataType.STRING)
        self.add_typed_input("new_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDriveGetFileNode(VisualNode):
    """Visual representation of DriveGetFileNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Get File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveGetFileNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("file_id", "File ID", text="", tab="properties")

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
    """Visual representation of DriveCreateFolderNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Create Folder"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveCreateFolderNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "folder_name", "Folder Name", text="New Folder", tab="properties"
        )
        self.add_text_input(
            "parent_id",
            "Parent Folder ID",
            text="",
            tab="properties",
            placeholder_text="Leave empty for root",
        )

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
    """Visual representation of DriveListFilesNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: List Files"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveListFilesNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "folder_id",
            "Folder ID",
            text="",
            tab="properties",
            placeholder_text="Leave empty for root",
        )
        self.add_text_input("page_size", "Page Size", text="100", tab="properties")

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
    """Visual representation of DriveSearchFilesNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Search Files"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveSearchFilesNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "query",
            "Query",
            text="",
            tab="properties",
            placeholder_text="name contains 'report' and mimeType='application/pdf'",
        )
        self.add_text_input("page_size", "Page Size", text="100", tab="properties")

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
    """Visual representation of DriveShareFileNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Share File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveShareFileNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("file_id", "File ID", text="", tab="properties")
        self.add_text_input(
            "email",
            "Email Address",
            text="",
            tab="properties",
            placeholder_text="user@example.com",
        )
        self.add_combo_menu(
            "role", "Role", items=["reader", "writer", "commenter"], tab="properties"
        )
        self.add_checkbox(
            "send_notification", "Send Notification", state=True, tab="properties"
        )

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
    """Visual representation of DriveRemovePermissionNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Remove Permission"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveRemovePermissionNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("file_id", "File ID", text="", tab="properties")
        self.add_text_input("permission_id", "Permission ID", text="", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_id", DataType.STRING)
        self.add_typed_input("permission_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDriveGetPermissionsNode(VisualNode):
    """Visual representation of DriveGetPermissionsNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Get Permissions"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveGetPermissionsNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("file_id", "File ID", text="", tab="properties")

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
    """Visual representation of DriveExportFileNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Export File"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveExportFileNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("file_id", "File ID", text="", tab="properties")
        self.add_combo_menu(
            "export_format",
            "Export Format",
            items=["pdf", "docx", "xlsx", "pptx", "txt", "csv", "html"],
            tab="properties",
        )
        self.add_text_input(
            "destination",
            "Destination Path",
            text="",
            tab="properties",
            placeholder_text="C:/Exports/document.pdf",
        )

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
    """Visual representation of DriveBatchDeleteNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Batch Delete"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveBatchDeleteNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )

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
    """Visual representation of DriveBatchMoveNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Batch Move"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveBatchMoveNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "folder_id", "Destination Folder ID", text="", tab="properties"
        )

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
    """Visual representation of DriveBatchCopyNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Drive: Batch Copy"
    NODE_CATEGORY = "google/drive"
    CASARE_NODE_CLASS = "DriveBatchCopyNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "folder_id",
            "Destination Folder ID",
            text="",
            tab="properties",
            placeholder_text="Leave empty for same folder",
        )

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
