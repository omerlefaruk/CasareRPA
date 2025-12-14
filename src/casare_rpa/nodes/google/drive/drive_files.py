"""
CasareRPA - Google Drive File Nodes

Nodes for file operations with Google Drive API v3:
- Upload, Download, Copy, Move, Delete, Rename, Get metadata
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.infrastructure.resources.google_drive_client import (
    GoogleDriveClient,
)
from casare_rpa.nodes.google.google_base import DriveBaseNode


# ============================================================================
# MIME Type to Extension Mapping (for files without extensions)
# ============================================================================

MIME_TO_EXTENSION = {
    # Images
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
    "image/tiff": ".tiff",
    "image/heic": ".heic",
    "image/heif": ".heif",
    "image/svg+xml": ".svg",
    "image/x-icon": ".ico",
    # Videos
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "video/x-msvideo": ".avi",
    "video/x-matroska": ".mkv",
    "video/webm": ".webm",
    "video/mpeg": ".mpeg",
    "video/3gpp": ".3gp",
    # Audio
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
    "audio/ogg": ".ogg",
    "audio/flac": ".flac",
    "audio/aac": ".aac",
    "audio/x-m4a": ".m4a",
    # Documents
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.ms-powerpoint": ".ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "text/plain": ".txt",
    "text/csv": ".csv",
    "text/html": ".html",
    "application/json": ".json",
    "application/xml": ".xml",
    "text/xml": ".xml",
    # Archives
    "application/zip": ".zip",
    "application/x-rar-compressed": ".rar",
    "application/x-7z-compressed": ".7z",
    "application/gzip": ".gz",
    "application/x-tar": ".tar",
}


def _ensure_file_extension(filename: str, mime_type: str) -> str:
    """
    Ensure filename has an appropriate extension based on MIME type.

    Google Photos files often have names like "December 1, 2025 at 1013PM"
    without extensions. This function adds the proper extension based on
    the file's MIME type.

    Args:
        filename: Original filename (may or may not have extension)
        mime_type: MIME type of the file

    Returns:
        Filename with extension (unchanged if already has one)
    """
    if not filename or not mime_type:
        return filename

    # Check if filename already has a recognized extension
    path = Path(filename)
    if path.suffix.lower() in {ext.lower() for ext in MIME_TO_EXTENSION.values()}:
        return filename

    # Also check common extensions not in the mapping
    common_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".mp4",
        ".pdf",
        ".doc",
        ".docx",
    }
    if path.suffix.lower() in common_extensions:
        return filename

    # Add extension based on MIME type
    extension = MIME_TO_EXTENSION.get(mime_type.lower(), "")
    if extension:
        logger.debug(
            f"Adding extension '{extension}' to filename '{filename}' (MIME: {mime_type})"
        )
        return filename + extension

    # Fallback: try to get extension from mimetypes module
    import mimetypes

    ext = mimetypes.guess_extension(mime_type)
    if ext:
        logger.debug(
            f"Adding extension '{ext}' to filename '{filename}' (MIME: {mime_type})"
        )
        return filename + ext

    return filename


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


@node(category="integration")
@properties(
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

    # @category: google
    # @requires: none
    # @ports: file_path, folder_id, file_name, mime_type, description -> file_id, name, web_view_link

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
        self.add_input_port("file_path", DataType.STRING, required=True)
        self.add_input_port("folder_id", DataType.STRING, required=False)
        self.add_input_port("file_name", DataType.STRING, required=False)
        self.add_input_port("mime_type", DataType.STRING, required=False)
        self.add_input_port("description", DataType.STRING, required=False)

        # Upload-specific outputs
        self.add_output_port("file_id", DataType.STRING)
        self.add_output_port("name", DataType.STRING)
        self.add_output_port("web_view_link", DataType.STRING)

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
# Drive Download File Node (Simplified - Single File Only)
# ============================================================================


@node(category="integration")
@properties(
    PropertyDef(
        "file_id",
        PropertyType.STRING,
        default="",
        required=True,
        label="File ID",
        placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
        tooltip="Google Drive file ID to download",
    ),
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
class DriveDownloadFileNode(DriveBaseNode):
    """
    Download a single file from Google Drive by file ID.

    For downloading multiple files, use:
    - DriveDownloadFolderNode: Download all files from a folder
    - DriveBatchDownloadNode: Download a list of files (for use with loops)

    Note: Google Workspace files (Docs, Sheets, Slides) cannot be downloaded
    directly. Use Drive Export File node to export them to a standard format.

    Inputs:
        - file_id: Google Drive file ID (required)
        - destination_path: Local path to save the file (required)

    Outputs:
        - file_path: Path to the downloaded file
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: file_id, destination_path -> file_path

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

        # Single file download inputs
        self.add_input_port("file_id", DataType.STRING, required=True)
        self.add_input_port("destination_path", DataType.STRING, required=True)

        # Single file output
        self.add_output_port("file_path", DataType.STRING)

    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: GoogleDriveClient,
    ) -> ExecutionResult:
        """Download a single file from Google Drive."""
        # Get parameters
        file_id = self.get_parameter("file_id") or self.get_input_value("file_id")
        destination_path = self.get_parameter(
            "destination_path"
        ) or self.get_input_value("destination_path")

        # Resolve variable references
        if file_id:
            file_id = self._resolve_value(context, file_id)
        if destination_path:
            destination_path = self._resolve_value(context, destination_path)

        # Validate inputs
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

        logger.debug(f"Downloading file from Drive: {file_id} -> {destination_path}")

        # Get file info to check MIME type
        file_info = await client.get_file(file_id)

        # Ensure parent directory exists
        dest_path = Path(destination_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure filename has proper extension (Google Photos files often lack them)
        dest_filename = _ensure_file_extension(
            dest_path.name, file_info.mime_type or ""
        )
        dest_path = dest_path.parent / dest_filename

        # Download file
        downloaded_path = await client.download_file(
            file_id=file_id,
            destination_path=str(dest_path),
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
# Drive Download Folder Node (NEW - Downloads all files from a folder)
# ============================================================================


@node(category="integration")
@properties(
    PropertyDef(
        "folder_id",
        PropertyType.STRING,
        default="",
        required=True,
        label="Folder ID",
        placeholder="14gesKQIyRcs98J4v3NOOQccUgRI1kMHy",
        tooltip="Google Drive folder ID to download files from",
    ),
    PropertyDef(
        "destination_folder",
        PropertyType.STRING,
        default="",
        required=True,
        label="Destination Folder",
        placeholder="C:\\Downloads\\",
        tooltip="Local folder to save downloaded files",
    ),
)
class DriveDownloadFolderNode(DriveBaseNode):
    """
    Download all files from a Google Drive folder.

    Downloads all files (not subfolders) from the specified Drive folder
    to a local destination folder, preserving original filenames.

    Note: Google Workspace files (Docs, Sheets, Slides) are skipped.
    Use Drive Export File node to export them to a standard format.

    Inputs:
        - folder_id: Google Drive folder ID (required)
        - destination_folder: Local folder to save files (required)

    Outputs:
        - file_paths: List of downloaded file paths
        - downloaded_count: Number of files successfully downloaded
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: folder_id, destination_folder -> file_paths, downloaded_count

    NODE_TYPE = "drive_download_folder"
    NODE_CATEGORY = "google_drive"
    NODE_DISPLAY_NAME = "Drive: Download Folder"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Drive Download Folder", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Folder download inputs
        self.add_input_port("folder_id", DataType.STRING, required=True)
        self.add_input_port("destination_folder", DataType.STRING, required=True)

        # Folder download outputs
        self.add_output_port("file_paths", DataType.LIST)
        self.add_output_port("downloaded_count", DataType.INTEGER)

    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: GoogleDriveClient,
    ) -> ExecutionResult:
        """Download all files from a Google Drive folder."""
        # Get parameters
        folder_id = self.get_parameter("folder_id") or self.get_input_value("folder_id")
        destination_folder = self.get_parameter(
            "destination_folder"
        ) or self.get_input_value("destination_folder")

        # Resolve variable references
        if folder_id:
            folder_id = self._resolve_value(context, folder_id)
        if destination_folder:
            destination_folder = self._resolve_value(context, destination_folder)

        # Validate inputs
        if not folder_id:
            self._set_error_outputs("Folder ID is required")
            return {
                "success": False,
                "error": "Folder ID is required",
                "next_nodes": [],
            }

        if not destination_folder:
            self._set_error_outputs("Destination folder is required")
            return {
                "success": False,
                "error": "Destination folder is required",
                "next_nodes": [],
            }

        logger.debug(f"Listing files from Drive folder: {folder_id}")

        # List files in folder
        try:
            files, _ = await client.list_files(
                folder_id=folder_id,
                page_size=1000,
                include_trashed=False,
            )
        except Exception as e:
            error_msg = f"Failed to list files from folder: {e}"
            self._set_error_outputs(error_msg)
            return {"success": False, "error": error_msg, "next_nodes": []}

        # Filter out folders and Google Workspace files
        files_to_download = [
            f
            for f in files
            if not f.mime_type.startswith("application/vnd.google-apps.")
        ]

        if not files_to_download:
            self._set_success_outputs()
            self.set_output_value("file_paths", [])
            self.set_output_value("downloaded_count", 0)
            logger.info("No downloadable files found in folder")
            return {
                "success": True,
                "file_paths": [],
                "downloaded_count": 0,
                "next_nodes": [],
            }

        logger.info(f"Found {len(files_to_download)} files to download from folder")

        # Create destination folder
        dest_folder = Path(destination_folder)
        dest_folder.mkdir(parents=True, exist_ok=True)

        # Download files
        downloaded_paths: list[str] = []
        errors: list[str] = []

        for file_info in files_to_download:
            try:
                # Ensure filename has proper extension (Google Photos often lacks them)
                filename = _ensure_file_extension(
                    file_info.name, file_info.mime_type or ""
                )
                dest_path = dest_folder / filename
                logger.debug(
                    f"Downloading file from Drive: {file_info.id} -> {dest_path}"
                )

                downloaded_path = await client.download_file(
                    file_id=file_info.id,
                    destination_path=str(dest_path),
                )
                downloaded_paths.append(str(downloaded_path))
                logger.info(f"Downloaded: {file_info.name}")

            except Exception as e:
                error_msg = f"Failed to download {file_info.name}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("file_paths", downloaded_paths)
        self.set_output_value("downloaded_count", len(downloaded_paths))

        result_msg = f"Downloaded {len(downloaded_paths)} file(s)"
        if errors:
            result_msg += f", {len(errors)} failed"
        logger.info(result_msg)

        return {
            "success": True,
            "file_paths": downloaded_paths,
            "downloaded_count": len(downloaded_paths),
            "errors": errors if errors else None,
            "next_nodes": [],
        }


# ============================================================================
# Drive Batch Download Node (NEW - Downloads a list of files)
# ============================================================================


@node(category="integration")
@properties(
    PropertyDef(
        "destination_folder",
        PropertyType.STRING,
        default="",
        required=True,
        label="Destination Folder",
        placeholder="C:\\Downloads\\",
        tooltip="Local folder to save downloaded files",
    ),
)
class DriveBatchDownloadNode(DriveBaseNode):
    """
    Download a list of files from Google Drive.

    Use this node with DriveListFilesNode or DriveSearchFilesNode
    to download multiple files. Each file object in the input list
    must have 'id' and 'name' fields.

    Note: Google Workspace files (Docs, Sheets, Slides) are skipped.
    Use Drive Export File node to export them to a standard format.

    Inputs:
        - files: List of file objects with 'id' and 'name' fields (required)
        - destination_folder: Local folder to save files (required)

    Outputs:
        - file_paths: List of downloaded file paths
        - downloaded_count: Number of files successfully downloaded
        - failed_count: Number of files that failed to download
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: files, destination_folder -> file_paths, downloaded_count, failed_count

    NODE_TYPE = "drive_batch_download"
    NODE_CATEGORY = "google_drive"
    NODE_DISPLAY_NAME = "Drive: Batch Download"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Drive Batch Download", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Batch download inputs
        self.add_input_port("files", DataType.LIST, required=True)
        self.add_input_port("destination_folder", DataType.STRING, required=True)

        # Batch download outputs
        self.add_output_port("file_paths", DataType.LIST)
        self.add_output_port("downloaded_count", DataType.INTEGER)
        self.add_output_port("failed_count", DataType.INTEGER)

    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: GoogleDriveClient,
    ) -> ExecutionResult:
        """Download a list of files from Google Drive."""
        # Get parameters
        files_list = self.get_input_value("files")
        destination_folder = self.get_parameter(
            "destination_folder"
        ) or self.get_input_value("destination_folder")

        # Resolve variable references
        if destination_folder:
            destination_folder = self._resolve_value(context, destination_folder)

        # Validate inputs
        if not files_list or not isinstance(files_list, list):
            self._set_error_outputs("Files list is required")
            return {
                "success": False,
                "error": "Files list is required",
                "next_nodes": [],
            }

        if not destination_folder:
            self._set_error_outputs("Destination folder is required")
            return {
                "success": False,
                "error": "Destination folder is required",
                "next_nodes": [],
            }

        # Extract file info from list
        # Support both camelCase (from DriveListFilesNode) and snake_case
        files_to_download: list[dict[str, str]] = []
        for f in files_list:
            if isinstance(f, dict) and f.get("id"):
                # Support both mimeType (camelCase) and mime_type (snake_case)
                mime_type = f.get("mimeType") or f.get("mime_type", "")
                files_to_download.append(
                    {
                        "id": f["id"],
                        "name": f.get("name", f["id"]),
                        "mime_type": mime_type,
                    }
                )

        if not files_to_download:
            self._set_success_outputs()
            self.set_output_value("file_paths", [])
            self.set_output_value("downloaded_count", 0)
            self.set_output_value("failed_count", 0)
            logger.info("No valid file objects in input list")
            return {
                "success": True,
                "file_paths": [],
                "downloaded_count": 0,
                "failed_count": 0,
                "next_nodes": [],
            }

        logger.info(f"Batch downloading {len(files_to_download)} files")

        # Create destination folder
        dest_folder = Path(destination_folder)
        dest_folder.mkdir(parents=True, exist_ok=True)

        # Download files
        downloaded_paths: list[str] = []
        errors: list[str] = []

        for file_info in files_to_download:
            # Skip Google Workspace files
            if file_info.get("mime_type", "").startswith(
                "application/vnd.google-apps."
            ):
                logger.debug(f"Skipping Google Workspace file: {file_info['name']}")
                continue

            try:
                # Ensure filename has proper extension (Google Photos often lacks them)
                filename = _ensure_file_extension(
                    file_info["name"], file_info.get("mime_type", "")
                )
                dest_path = dest_folder / filename
                logger.debug(
                    f"Downloading file from Drive: {file_info['id']} -> {dest_path}"
                )

                downloaded_path = await client.download_file(
                    file_id=file_info["id"],
                    destination_path=str(dest_path),
                )
                downloaded_paths.append(str(downloaded_path))
                logger.info(f"Downloaded: {file_info['name']}")

            except Exception as e:
                error_msg = f"Failed to download {file_info['name']}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("file_paths", downloaded_paths)
        self.set_output_value("downloaded_count", len(downloaded_paths))
        self.set_output_value("failed_count", len(errors))

        result_msg = f"Downloaded {len(downloaded_paths)} file(s)"
        if errors:
            result_msg += f", {len(errors)} failed"
        logger.info(result_msg)

        return {
            "success": True,
            "file_paths": downloaded_paths,
            "downloaded_count": len(downloaded_paths),
            "failed_count": len(errors),
            "errors": errors if errors else None,
            "next_nodes": [],
        }


# ============================================================================
# Drive Copy File Node
# ============================================================================


@node(category="integration")
@properties(
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

    # @category: google
    # @requires: none
    # @ports: file_id, new_name, folder_id -> new_file_id, name

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
        self.add_input_port("file_id", DataType.STRING, required=True)
        self.add_input_port("new_name", DataType.STRING, required=False)
        self.add_input_port("folder_id", DataType.STRING, required=False)

        # Copy-specific outputs
        self.add_output_port("new_file_id", DataType.STRING)
        self.add_output_port("name", DataType.STRING)

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


@node(category="integration")
@properties(
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

    # @category: google
    # @requires: none
    # @ports: file_id, folder_id -> file_id, new_parents

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
        self.add_input_port("file_id", DataType.STRING, required=True)
        self.add_input_port("folder_id", DataType.STRING, required=True)

        # Move-specific outputs
        self.add_output_port("file_id", DataType.STRING)
        self.add_output_port("new_parents", DataType.LIST)

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


@node(category="integration")
@properties(
    DRIVE_FILE_ID,
    PropertyDef(
        "permanent",
        PropertyType.BOOLEAN,
        default=False,
        label="Permanent Delete",
        tooltip="If True, permanently delete. If False, move to trash.",
    ),
)
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

    # @category: google
    # @requires: none
    # @ports: file_id, permanent -> file_id

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
        self.add_input_port("file_id", DataType.STRING, required=True)
        self.add_input_port("permanent", DataType.BOOLEAN, required=False)

        # Delete-specific outputs
        self.add_output_port("file_id", DataType.STRING)

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


@node(category="integration")
@properties(
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

    # @category: google
    # @requires: none
    # @ports: file_id, new_name -> file_id, name

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
        self.add_input_port("file_id", DataType.STRING, required=True)
        self.add_input_port("new_name", DataType.STRING, required=True)

        # Rename-specific outputs
        self.add_output_port("file_id", DataType.STRING)
        self.add_output_port("name", DataType.STRING)

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


@node(category="integration")
@properties(
    DRIVE_FILE_ID,
)
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

    # @category: google
    # @requires: none
    # @ports: file_id -> file_id, name, mime_type, size, created_time, modified_time, web_view_link, web_content_link, parents, description, starred, trashed, shared

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
        self.add_input_port("file_id", DataType.STRING, required=True)

        # Get file outputs - comprehensive metadata
        self.add_output_port("file_id", DataType.STRING)
        self.add_output_port("name", DataType.STRING)
        self.add_output_port("mime_type", DataType.STRING)
        self.add_output_port("size", DataType.INTEGER)
        self.add_output_port("created_time", DataType.STRING)
        self.add_output_port("modified_time", DataType.STRING)
        self.add_output_port("web_view_link", DataType.STRING)
        self.add_output_port("web_content_link", DataType.STRING)
        self.add_output_port("parents", DataType.LIST)
        self.add_output_port("description", DataType.STRING)
        self.add_output_port("starred", DataType.BOOLEAN)
        self.add_output_port("trashed", DataType.BOOLEAN)
        self.add_output_port("shared", DataType.BOOLEAN)

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


# ============================================================================
# Drive Export File Node (Export Google Workspace files to standard formats)
# ============================================================================


# Export format choices for Google Workspace files
GOOGLE_WORKSPACE_EXPORT_FORMATS = {
    # Google Docs export formats
    "application/vnd.google-apps.document": [
        ("pdf", "application/pdf"),
        (
            "docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
        ("odt", "application/vnd.oasis.opendocument.text"),
        ("txt", "text/plain"),
        ("html", "text/html"),
        ("rtf", "application/rtf"),
        ("epub", "application/epub+zip"),
    ],
    # Google Sheets export formats
    "application/vnd.google-apps.spreadsheet": [
        ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ("pdf", "application/pdf"),
        ("ods", "application/vnd.oasis.opendocument.spreadsheet"),
        ("csv", "text/csv"),
        ("tsv", "text/tab-separated-values"),
        ("html", "text/html"),
    ],
    # Google Slides export formats
    "application/vnd.google-apps.presentation": [
        (
            "pptx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ),
        ("pdf", "application/pdf"),
        ("odp", "application/vnd.oasis.opendocument.presentation"),
        ("txt", "text/plain"),
    ],
    # Google Drawings export formats
    "application/vnd.google-apps.drawing": [
        ("png", "image/png"),
        ("pdf", "application/pdf"),
        ("svg", "image/svg+xml"),
        ("jpg", "image/jpeg"),
    ],
}

# Default export format per Google Workspace type
DEFAULT_EXPORT_FORMAT = {
    "application/vnd.google-apps.document": "pdf",
    "application/vnd.google-apps.spreadsheet": "xlsx",
    "application/vnd.google-apps.presentation": "pptx",
    "application/vnd.google-apps.drawing": "png",
}

# Format to MIME type mapping
FORMAT_TO_MIME = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "odt": "application/vnd.oasis.opendocument.text",
    "ods": "application/vnd.oasis.opendocument.spreadsheet",
    "odp": "application/vnd.oasis.opendocument.presentation",
    "txt": "text/plain",
    "html": "text/html",
    "csv": "text/csv",
    "tsv": "text/tab-separated-values",
    "rtf": "application/rtf",
    "epub": "application/epub+zip",
    "png": "image/png",
    "jpg": "image/jpeg",
    "svg": "image/svg+xml",
}


@node(category="integration")
@properties(
    PropertyDef(
        "file_id",
        PropertyType.STRING,
        default="",
        required=True,
        label="File ID",
        placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
        tooltip="Google Drive file ID of Google Workspace file (Doc, Sheet, Slide)",
    ),
    PropertyDef(
        "destination_path",
        PropertyType.STRING,
        default="",
        required=True,
        label="Destination Path",
        placeholder="C:\\Documents\\report.pdf",
        tooltip="Local path to save the exported file",
    ),
    PropertyDef(
        "export_format",
        PropertyType.CHOICE,
        default="pdf",
        label="Export Format",
        tooltip="Format to export the file as",
        choices=[
            "pdf",
            "docx",
            "xlsx",
            "pptx",
            "csv",
            "txt",
            "html",
            "odt",
            "ods",
            "odp",
            "rtf",
            "epub",
            "png",
            "jpg",
            "svg",
            "tsv",
        ],
    ),
)
class DriveExportFileNode(DriveBaseNode):
    """
    Export a Google Workspace file (Doc, Sheet, Slide) to a standard format.

    Google Workspace files cannot be downloaded directly - they must be
    exported to a standard format like PDF, DOCX, XLSX, etc.

    Supported file types and their export formats:
    - Google Docs: pdf, docx, odt, txt, html, rtf, epub
    - Google Sheets: xlsx, pdf, ods, csv, tsv, html
    - Google Slides: pptx, pdf, odp, txt
    - Google Drawings: png, pdf, svg, jpg

    Inputs:
        - file_id: Google Drive file ID (required)
        - destination_path: Local path to save the exported file (required)
        - export_format: Format to export as (default: pdf)

    Outputs:
        - file_path: Path to the exported file
        - original_name: Original file name in Drive
        - original_type: Original Google Workspace type
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: file_id, destination_path, export_format -> file_path, original_name, original_type

    NODE_TYPE = "drive_export_file"
    NODE_CATEGORY = "google_drive"
    NODE_DISPLAY_NAME = "Drive: Export File"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Drive Export File", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Export-specific inputs
        self.add_input_port("file_id", DataType.STRING, required=True)
        self.add_input_port("destination_path", DataType.STRING, required=True)
        self.add_input_port("export_format", DataType.STRING, required=False)

        # Export-specific outputs
        self.add_output_port("file_path", DataType.STRING)
        self.add_output_port("original_name", DataType.STRING)
        self.add_output_port("original_type", DataType.STRING)

    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: GoogleDriveClient,
    ) -> ExecutionResult:
        """Export a Google Workspace file to a standard format."""
        # Get parameters
        file_id = self.get_parameter("file_id") or self.get_input_value("file_id")
        destination_path = self.get_parameter(
            "destination_path"
        ) or self.get_input_value("destination_path")
        export_format = (
            self.get_parameter("export_format")
            or self.get_input_value("export_format")
            or "pdf"
        )

        # Resolve variable references
        if file_id:
            file_id = self._resolve_value(context, file_id)
        if destination_path:
            destination_path = self._resolve_value(context, destination_path)
        if export_format:
            export_format = self._resolve_value(context, export_format)

        # Validate inputs
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

        export_format = export_format.lower().strip()

        logger.debug(f"Exporting file from Drive: {file_id} as {export_format}")

        # Get file info to check type
        file_info = await client.get_file(file_id)

        # Validate it's a Google Workspace file
        if not file_info.is_google_doc:
            error_msg = (
                f"File is not a Google Workspace file. "
                f"MIME type: {file_info.mime_type}. "
                f"Use 'Drive Download File' node instead for regular files."
            )
            self._set_error_outputs(error_msg)
            return {"success": False, "error": error_msg, "next_nodes": []}

        # Check if the export format is supported for this file type
        supported_formats = GOOGLE_WORKSPACE_EXPORT_FORMATS.get(file_info.mime_type, [])
        supported_format_names = [f[0] for f in supported_formats]

        if export_format not in supported_format_names:
            # Try to use default format for this type
            default_format = DEFAULT_EXPORT_FORMAT.get(file_info.mime_type)
            if default_format:
                logger.warning(
                    f"Format '{export_format}' not supported for {file_info.mime_type}. "
                    f"Using default format: {default_format}"
                )
                export_format = default_format
            else:
                error_msg = (
                    f"Export format '{export_format}' is not supported for this file type. "
                    f"Supported formats: {', '.join(supported_format_names)}"
                )
                self._set_error_outputs(error_msg)
                return {"success": False, "error": error_msg, "next_nodes": []}

        # Get MIME type for export format
        export_mime_type = FORMAT_TO_MIME.get(export_format)
        if not export_mime_type:
            error_msg = f"Unknown export format: {export_format}"
            self._set_error_outputs(error_msg)
            return {"success": False, "error": error_msg, "next_nodes": []}

        # Ensure destination path has the correct extension
        dest_path = Path(destination_path)
        if not dest_path.suffix or dest_path.suffix.lower() != f".{export_format}":
            dest_path = dest_path.with_suffix(f".{export_format}")

        # Create parent directory
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        logger.debug(
            f"Exporting {file_info.name} ({file_info.mime_type}) -> {dest_path}"
        )

        # Export file
        exported_path = await client.export_file(
            file_id=file_id,
            destination_path=str(dest_path),
            export_mime_type=export_mime_type,
        )

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("file_path", str(exported_path))
        self.set_output_value("original_name", file_info.name)
        self.set_output_value("original_type", file_info.mime_type)

        logger.info(f"Exported {file_info.name} to {exported_path}")

        return {
            "success": True,
            "file_path": str(exported_path),
            "original_name": file_info.name,
            "original_type": file_info.mime_type,
            "next_nodes": [],
        }


__all__ = [
    "DriveUploadFileNode",
    "DriveDownloadFileNode",
    "DriveDownloadFolderNode",
    "DriveBatchDownloadNode",
    "DriveCopyFileNode",
    "DriveMoveFileNode",
    "DriveDeleteFileNode",
    "DriveRenameFileNode",
    "DriveGetFileNode",
    "DriveExportFileNode",
]
