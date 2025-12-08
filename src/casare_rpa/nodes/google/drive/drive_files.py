"""
CasareRPA - Google Drive File Nodes

Nodes for file operations with Google Drive API v3:
- Upload, Download, Copy, Move, Delete, Rename, Get metadata
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    PortType,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.infrastructure.resources.google_drive_client import (
    GoogleDriveClient,
)
from casare_rpa.nodes.google.drive.drive_base import DriveBaseNode


# ============================================================================
# Reusable Property Definitions for Drive Nodes
# ============================================================================

# NOTE: access_token and credential_name are NOT defined here.
# Credential selection is handled by NodeGoogleCredentialWidget in the visual layer.
# The credential_id property is set by the picker widget.

DRIVE_FILE_ID = PropertyDef(
    "file_id",
    PropertyType.STRING,
    default="",
    required=True,
    label="File ID",
    placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    tooltip="Google Drive file ID",
)

DRIVE_FOLDER_ID = PropertyDef(
    "folder_id",
    PropertyType.STRING,
    default="",
    label="Folder ID",
    placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    tooltip="Google Drive folder ID (empty = root)",
)


# ============================================================================
# Drive Upload File Node
# ============================================================================


@node_schema(
    PropertyDef(
        "file_path",
        PropertyType.STRING,
        default="",
        required=True,
        label="File Path",
        placeholder="C:\\Documents\\report.pdf",
        tooltip="Local path to the file to upload",
    ),
    DRIVE_FOLDER_ID,
    PropertyDef(
        "file_name",
        PropertyType.STRING,
        default="",
        label="File Name",
        placeholder="report.pdf",
        tooltip="Name in Drive (default: local filename)",
    ),
    PropertyDef(
        "mime_type",
        PropertyType.STRING,
        default="",
        label="MIME Type",
        placeholder="application/pdf",
        tooltip="File MIME type (auto-detected if empty)",
    ),
    PropertyDef(
        "description",
        PropertyType.TEXT,
        default="",
        label="Description",
        placeholder="Monthly sales report...",
        tooltip="File description in Drive",
    ),
)
@executable_node
class DriveUploadFileNode(DriveBaseNode):
    """
    Upload a file to Google Drive.

    Inputs:
        - file_path: Local path to the file to upload
        - folder_id: Parent folder ID (default: root)
        - file_name: Name in Drive (default: local filename)
        - mime_type: MIME type (auto-detected if empty)
        - description: File description

    Outputs:
        - file_id: Uploaded file's Drive ID
        - name: File name in Drive
        - web_view_link: Link to view the file
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "drive_upload_file"
    NODE_CATEGORY = "google_drive"
    NODE_DISPLAY_NAME = "Drive: Upload File"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Drive Upload File", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Upload-specific inputs
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port(
            "folder_id", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "file_name", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "mime_type", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "description", PortType.INPUT, DataType.STRING, required=False
        )

        # Upload-specific outputs
        self.add_output_port("file_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("name", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("web_view_link", PortType.OUTPUT, DataType.STRING)

    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: GoogleDriveClient,
    ) -> ExecutionResult:
        """Upload a file to Google Drive."""
        # Get parameters
        file_path = self._resolve_value(context, self.get_parameter("file_path"))
        folder_id = self._resolve_value(context, self.get_parameter("folder_id"))
        file_name = self._resolve_value(context, self.get_parameter("file_name"))
        mime_type = self._resolve_value(context, self.get_parameter("mime_type"))
        description = self._resolve_value(context, self.get_parameter("description"))

        if not file_path:
            self._set_error_outputs("File path is required")
            return {
                "success": False,
                "error": "File path is required",
                "next_nodes": [],
            }

        # Validate file exists
        local_path = Path(file_path)
        if not local_path.exists():
            error_msg = f"File not found: {file_path}"
            self._set_error_outputs(error_msg)
            return {"success": False, "error": error_msg, "next_nodes": []}

        logger.debug(f"Uploading file to Drive: {file_path}")

        # Upload file
        result = await client.upload_file(
            file_path=local_path,
            folder_id=folder_id or None,
            name=file_name or None,
            mime_type=mime_type or None,
            description=description or None,
        )

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("file_id", result.id)
        self.set_output_value("name", result.name)
        self.set_output_value("web_view_link", result.web_view_link or "")

        logger.info(f"Uploaded file to Drive: {result.id} ({result.name})")

        return {
            "success": True,
            "file_id": result.id,
            "name": result.name,
            "web_view_link": result.web_view_link,
            "next_nodes": [],
        }


# ============================================================================
# Drive Download File Node
# ============================================================================


@node_schema(
    DRIVE_FILE_ID,
    PropertyDef(
        "destination_path",
        PropertyType.STRING,
        default="",
        required=True,
        label="Destination Path",
        placeholder="C:\\Downloads\\report.pdf",
        tooltip="Local path to save the downloaded file",
    ),
)
@executable_node
class DriveDownloadFileNode(DriveBaseNode):
    """
    Download a file from Google Drive.

    Note: Google Workspace files (Docs, Sheets, Slides) cannot be downloaded
    directly. Use Drive Export File node to export them to a standard format.

    Inputs:
        - file_id: Google Drive file ID
        - destination_path: Local path to save the file

    Outputs:
        - file_path: Path to the downloaded file
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "drive_download_file"
    NODE_CATEGORY = "google_drive"
    NODE_DISPLAY_NAME = "Drive: Download File"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Drive Download File", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Download-specific inputs
        self.add_input_port("file_id", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port(
            "destination_path", PortType.INPUT, DataType.STRING, required=True
        )

        # Download-specific outputs
        self.add_output_port("file_path", PortType.OUTPUT, DataType.STRING)

    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: GoogleDriveClient,
    ) -> ExecutionResult:
        """Download a file from Google Drive."""
        file_id = self._resolve_value(context, self.get_parameter("file_id"))
        destination_path = self._resolve_value(
            context, self.get_parameter("destination_path")
        )

        if not file_id:
            self._set_error_outputs("File ID is required")
            return {"success": False, "error": "File ID is required", "next_nodes": []}

        if not destination_path:
            self._set_error_outputs("Destination path is required")
            return {
                "success": False,
                "error": "Destination path is required",
                "next_nodes": [],
            }

        logger.debug(f"Downloading file from Drive: {file_id}")

        # Download file
        downloaded_path = await client.download_file(
            file_id=file_id,
            destination_path=destination_path,
        )

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("file_path", str(downloaded_path))

        logger.info(f"Downloaded file from Drive to: {downloaded_path}")

        return {
            "success": True,
            "file_path": str(downloaded_path),
            "next_nodes": [],
        }


# ============================================================================
# Drive Copy File Node
# ============================================================================


@node_schema(
    DRIVE_FILE_ID,
    PropertyDef(
        "new_name",
        PropertyType.STRING,
        default="",
        label="New Name",
        placeholder="report_copy.pdf",
        tooltip="Name for the copy (default: 'Copy of {original}')",
    ),
    DRIVE_FOLDER_ID,
)
@executable_node
class DriveCopyFileNode(DriveBaseNode):
    """
    Create a copy of a file in Google Drive.

    Inputs:
        - file_id: ID of the file to copy
        - new_name: Name for the copy (default: "Copy of {original}")
        - folder_id: Destination folder (default: same as original)

    Outputs:
        - new_file_id: ID of the new copy
        - name: Name of the new copy
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "drive_copy_file"
    NODE_CATEGORY = "google_drive"
    NODE_DISPLAY_NAME = "Drive: Copy File"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Drive Copy File", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Copy-specific inputs
        self.add_input_port("file_id", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port("new_name", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port(
            "folder_id", PortType.INPUT, DataType.STRING, required=False
        )

        # Copy-specific outputs
        self.add_output_port("new_file_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("name", PortType.OUTPUT, DataType.STRING)

    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: GoogleDriveClient,
    ) -> ExecutionResult:
        """Copy a file in Google Drive."""
        file_id = self._resolve_value(context, self.get_parameter("file_id"))
        new_name = self._resolve_value(context, self.get_parameter("new_name"))
        folder_id = self._resolve_value(context, self.get_parameter("folder_id"))

        if not file_id:
            self._set_error_outputs("File ID is required")
            return {"success": False, "error": "File ID is required", "next_nodes": []}

        logger.debug(f"Copying file in Drive: {file_id}")

        # Copy file
        result = await client.copy_file(
            file_id=file_id,
            new_name=new_name or None,
            folder_id=folder_id or None,
        )

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("new_file_id", result.id)
        self.set_output_value("name", result.name)

        logger.info(f"Copied file in Drive: {file_id} -> {result.id}")

        return {
            "success": True,
            "new_file_id": result.id,
            "name": result.name,
            "next_nodes": [],
        }


# ============================================================================
# Drive Move File Node
# ============================================================================


@node_schema(
    DRIVE_FILE_ID,
    PropertyDef(
        "folder_id",
        PropertyType.STRING,
        default="",
        required=True,
        label="Destination Folder ID",
        placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
        tooltip="ID of the destination folder",
    ),
)
@executable_node
class DriveMoveFileNode(DriveBaseNode):
    """
    Move a file to a different folder in Google Drive.

    Inputs:
        - file_id: ID of the file to move
        - folder_id: ID of the destination folder

    Outputs:
        - file_id: ID of the moved file
        - new_parents: List of new parent folder IDs
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "drive_move_file"
    NODE_CATEGORY = "google_drive"
    NODE_DISPLAY_NAME = "Drive: Move File"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Drive Move File", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Move-specific inputs
        self.add_input_port("file_id", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port("folder_id", PortType.INPUT, DataType.STRING, required=True)

        # Move-specific outputs
        self.add_output_port("file_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("new_parents", PortType.OUTPUT, DataType.LIST)

    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: GoogleDriveClient,
    ) -> ExecutionResult:
        """Move a file in Google Drive."""
        file_id = self._resolve_value(context, self.get_parameter("file_id"))
        folder_id = self._resolve_value(context, self.get_parameter("folder_id"))

        if not file_id:
            self._set_error_outputs("File ID is required")
            return {"success": False, "error": "File ID is required", "next_nodes": []}

        if not folder_id:
            self._set_error_outputs("Destination folder ID is required")
            return {
                "success": False,
                "error": "Destination folder ID is required",
                "next_nodes": [],
            }

        logger.debug(f"Moving file in Drive: {file_id} -> {folder_id}")

        # Move file
        result = await client.move_file(
            file_id=file_id,
            new_folder_id=folder_id,
        )

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("file_id", result.id)
        self.set_output_value("new_parents", result.parents)

        logger.info(f"Moved file in Drive: {file_id} to folder {folder_id}")

        return {
            "success": True,
            "file_id": result.id,
            "new_parents": result.parents,
            "next_nodes": [],
        }


# ============================================================================
# Drive Delete File Node
# ============================================================================


@node_schema(
    DRIVE_FILE_ID,
    PropertyDef(
        "permanent",
        PropertyType.BOOLEAN,
        default=False,
        label="Permanent Delete",
        tooltip="If True, permanently delete. If False, move to trash.",
    ),
)
@executable_node
class DriveDeleteFileNode(DriveBaseNode):
    """
    Delete or trash a file in Google Drive.

    Inputs:
        - file_id: ID of the file to delete
        - permanent: If True, permanently delete. If False, move to trash.

    Outputs:
        - file_id: ID of the deleted file
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "drive_delete_file"
    NODE_CATEGORY = "google_drive"
    NODE_DISPLAY_NAME = "Drive: Delete File"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Drive Delete File", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Delete-specific inputs
        self.add_input_port("file_id", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port(
            "permanent", PortType.INPUT, DataType.BOOLEAN, required=False
        )

        # Delete-specific outputs
        self.add_output_port("file_id", PortType.OUTPUT, DataType.STRING)

    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: GoogleDriveClient,
    ) -> ExecutionResult:
        """Delete a file in Google Drive."""
        file_id = self._resolve_value(context, self.get_parameter("file_id"))
        permanent = self.get_parameter("permanent") or False

        if not file_id:
            self._set_error_outputs("File ID is required")
            return {"success": False, "error": "File ID is required", "next_nodes": []}

        action = "permanently deleting" if permanent else "trashing"
        logger.debug(f"{action.capitalize()} file in Drive: {file_id}")

        # Delete file
        await client.delete_file(
            file_id=file_id,
            permanent=permanent,
        )

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("file_id", file_id)

        logger.info(
            f"{'Permanently deleted' if permanent else 'Trashed'} file: {file_id}"
        )

        return {
            "success": True,
            "file_id": file_id,
            "permanent": permanent,
            "next_nodes": [],
        }


# ============================================================================
# Drive Rename File Node
# ============================================================================


@node_schema(
    DRIVE_FILE_ID,
    PropertyDef(
        "new_name",
        PropertyType.STRING,
        default="",
        required=True,
        label="New Name",
        placeholder="renamed_file.pdf",
        tooltip="New name for the file",
    ),
)
@executable_node
class DriveRenameFileNode(DriveBaseNode):
    """
    Rename a file or folder in Google Drive.

    Inputs:
        - file_id: ID of the file to rename
        - new_name: New name for the file

    Outputs:
        - file_id: ID of the renamed file
        - name: New name of the file
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "drive_rename_file"
    NODE_CATEGORY = "google_drive"
    NODE_DISPLAY_NAME = "Drive: Rename File"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Drive Rename File", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Rename-specific inputs
        self.add_input_port("file_id", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port("new_name", PortType.INPUT, DataType.STRING, required=True)

        # Rename-specific outputs
        self.add_output_port("file_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("name", PortType.OUTPUT, DataType.STRING)

    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: GoogleDriveClient,
    ) -> ExecutionResult:
        """Rename a file in Google Drive."""
        file_id = self._resolve_value(context, self.get_parameter("file_id"))
        new_name = self._resolve_value(context, self.get_parameter("new_name"))

        if not file_id:
            self._set_error_outputs("File ID is required")
            return {"success": False, "error": "File ID is required", "next_nodes": []}

        if not new_name:
            self._set_error_outputs("New name is required")
            return {"success": False, "error": "New name is required", "next_nodes": []}

        logger.debug(f"Renaming file in Drive: {file_id} -> {new_name}")

        # Rename file
        result = await client.rename_file(
            file_id=file_id,
            new_name=new_name,
        )

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("file_id", result.id)
        self.set_output_value("name", result.name)

        logger.info(f"Renamed file in Drive: {file_id} to {new_name}")

        return {
            "success": True,
            "file_id": result.id,
            "name": result.name,
            "next_nodes": [],
        }


# ============================================================================
# Drive Get File Node
# ============================================================================


@node_schema(
    DRIVE_FILE_ID,
)
@executable_node
class DriveGetFileNode(DriveBaseNode):
    """
    Get file metadata from Google Drive.

    Inputs:
        - file_id: Google Drive file ID

    Outputs:
        - file_id: File ID
        - name: File name
        - mime_type: MIME type
        - size: File size in bytes
        - created_time: Creation timestamp (ISO 8601)
        - modified_time: Last modification timestamp (ISO 8601)
        - web_view_link: Link to view the file
        - web_content_link: Direct download link (non-Google Workspace files)
        - parents: Parent folder IDs
        - starred: Whether file is starred
        - trashed: Whether file is in trash
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "drive_get_file"
    NODE_CATEGORY = "google_drive"
    NODE_DISPLAY_NAME = "Drive: Get File"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Drive Get File", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Get file inputs
        self.add_input_port("file_id", PortType.INPUT, DataType.STRING, required=True)

        # Get file outputs - comprehensive metadata
        self.add_output_port("file_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("name", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("mime_type", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("size", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("created_time", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("modified_time", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("web_view_link", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("web_content_link", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("parents", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("description", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("starred", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("trashed", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("shared", PortType.OUTPUT, DataType.BOOLEAN)

    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: GoogleDriveClient,
    ) -> ExecutionResult:
        """Get file metadata from Google Drive."""
        file_id = self._resolve_value(context, self.get_parameter("file_id"))

        if not file_id:
            self._set_error_outputs("File ID is required")
            return {"success": False, "error": "File ID is required", "next_nodes": []}

        logger.debug(f"Getting file metadata from Drive: {file_id}")

        # Get file metadata
        result = await client.get_file(file_id=file_id)

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("file_id", result.id)
        self.set_output_value("name", result.name)
        self.set_output_value("mime_type", result.mime_type)
        self.set_output_value("size", result.size or 0)
        self.set_output_value("created_time", result.created_time or "")
        self.set_output_value("modified_time", result.modified_time or "")
        self.set_output_value("web_view_link", result.web_view_link or "")
        self.set_output_value("web_content_link", result.web_content_link or "")
        self.set_output_value("parents", result.parents)
        self.set_output_value("description", result.description or "")
        self.set_output_value("starred", result.starred)
        self.set_output_value("trashed", result.trashed)
        self.set_output_value("shared", result.shared)

        logger.info(f"Got file metadata from Drive: {result.name} ({result.id})")

        return {
            "success": True,
            "file_id": result.id,
            "name": result.name,
            "mime_type": result.mime_type,
            "size": result.size,
            "next_nodes": [],
        }


__all__ = [
    "DriveUploadFileNode",
    "DriveDownloadFileNode",
    "DriveCopyFileNode",
    "DriveMoveFileNode",
    "DriveDeleteFileNode",
    "DriveRenameFileNode",
    "DriveGetFileNode",
]
