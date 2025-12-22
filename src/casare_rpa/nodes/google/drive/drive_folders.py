"""
CasareRPA - Google Drive Folder Nodes

Nodes for folder operations with Google Drive API v3:
- Create Folder, List Files, Search Files
"""

from __future__ import annotations

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
# Reusable Property Definitions
# ============================================================================

# NOTE: access_token and credential_name are NOT defined here.
# Credential selection is handled by NodeGoogleCredentialWidget in the visual layer.
# The credential_id property is set by the picker widget.

DRIVE_FOLDER_ID = PropertyDef(
    "folder_id",
    PropertyType.STRING,
    default="",
    label="Folder ID",
    placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    tooltip="Google Drive folder ID (empty = root)",
)

DRIVE_QUERY = PropertyDef(
    "query",
    PropertyType.TEXT,
    default="",
    label="Query",
    placeholder="name contains 'report' and mimeType = 'application/pdf'",
    tooltip="Google Drive API query syntax",
)

DRIVE_MAX_RESULTS = PropertyDef(
    "max_results",
    PropertyType.INTEGER,
    default=100,
    label="Max Results",
    tooltip="Maximum number of files to return (1-1000)",
)


# ============================================================================
# Drive Create Folder Node
# ============================================================================


@properties(
    PropertyDef(
        "folder_name",
        PropertyType.STRING,
        default="",
        required=True,
        label="Folder Name",
        placeholder="My New Folder",
        tooltip="Name for the new folder",
    ),
    PropertyDef(
        "parent_id",
        PropertyType.STRING,
        default="",
        label="Parent Folder ID",
        placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
        tooltip="Parent folder ID (empty = root)",
    ),
    PropertyDef(
        "description",
        PropertyType.TEXT,
        default="",
        label="Description",
        placeholder="Folder for quarterly reports...",
        tooltip="Folder description",
    ),
)
@node(category="google")
class DriveCreateFolderNode(DriveBaseNode):
    """
    Create a new folder in Google Drive.

    Inputs:
        - name: Name for the new folder
        - parent_id: Parent folder ID (default: root)
        - description: Optional folder description

    Outputs:
        - folder_id: ID of the created folder
        - name: Name of the created folder
        - web_view_link: Link to view the folder
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: folder_name, parent_id, description -> folder_id, folder_name, web_view_link

    NODE_TYPE = "drive_create_folder"
    NODE_CATEGORY = "google_drive"
    NODE_DISPLAY_NAME = "Drive: Create Folder"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Drive Create Folder", **kwargs)
        # Note: _define_ports() is called by BaseNode.__init__

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Create folder inputs
        self.add_input_port("folder_name", DataType.STRING, required=True)
        self.add_input_port("parent_id", DataType.STRING, required=False)
        self.add_input_port("description", DataType.STRING, required=False)

        # Create folder outputs
        self.add_output_port("folder_id", DataType.STRING)
        self.add_output_port("folder_name", DataType.STRING)
        self.add_output_port("web_view_link", DataType.STRING)

    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: GoogleDriveClient,
    ) -> ExecutionResult:
        """Create a folder in Google Drive."""
        name = self._resolve_value(context, self.get_parameter("folder_name"))
        parent_id = self._resolve_value(context, self.get_parameter("parent_id"))
        description = self._resolve_value(context, self.get_parameter("description"))

        if not name:
            self._set_error_outputs("Folder name is required")
            return {
                "success": False,
                "error": "Folder name is required",
                "next_nodes": [],
            }

        logger.debug(f"Creating folder in Drive: {name}")

        # Create folder
        result = await client.create_folder(
            name=name,
            parent_id=parent_id or None,
            description=description or None,
        )

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("folder_id", result.id)
        self.set_output_value("folder_name", result.name)
        self.set_output_value("web_view_link", result.web_view_link or "")

        logger.info(f"Created folder in Drive: {result.name} ({result.id})")

        return {
            "success": True,
            "folder_id": result.id,
            "name": result.name,
            "web_view_link": result.web_view_link,
            "next_nodes": [],
        }


# ============================================================================
# Drive List Files Node
# ============================================================================


@properties(
    DRIVE_FOLDER_ID,
    DRIVE_QUERY,
    PropertyDef(
        "mime_type",
        PropertyType.CHOICE,
        default="",
        choices=[
            "",
            "application/vnd.google-apps.folder",
            "application/vnd.google-apps.document",
            "application/vnd.google-apps.spreadsheet",
            "application/vnd.google-apps.presentation",
            "application/pdf",
            "image/jpeg",
            "image/png",
            "application/zip",
        ],
        label="MIME Type Filter",
        tooltip="Filter by MIME type (empty = all types)",
    ),
    DRIVE_MAX_RESULTS,
    PropertyDef(
        "order_by",
        PropertyType.CHOICE,
        default="name",
        choices=[
            "name",
            "name desc",
            "modifiedTime",
            "modifiedTime desc",
            "createdTime",
            "createdTime desc",
        ],
        label="Order By",
        tooltip="Sort order for results",
    ),
    PropertyDef(
        "include_trashed",
        PropertyType.BOOLEAN,
        default=False,
        label="Include Trashed",
        tooltip="Include files in trash",
    ),
)
@node(category="google")
class DriveListFilesNode(DriveBaseNode):
    """
    List files in a Google Drive folder.

    Inputs:
        - folder_id: Folder to list (empty = all accessible files)
        - query: Additional query filter (Drive API query syntax)
        - mime_type: Filter by MIME type
        - max_results: Maximum number of files to return
        - order_by: Sort order
        - include_trashed: Include trashed files

    Outputs:
        - files: Array of file objects with id, name, mimeType, size, etc.
        - file_count: Number of files returned
        - has_more: Whether there are more results available
        - folder_id: The folder ID being listed (passthrough for downstream nodes)
        - success: Boolean
        - error: Error message if failed

    Query Examples:
        - "name contains 'report'"
        - "mimeType = 'application/pdf'"
        - "modifiedTime > '2024-01-01T00:00:00'"
    """

    # @category: google
    # @requires: none
    # @ports: folder_id, query, mime_type, max_results, order_by, include_trashed -> files, file_count, has_more

    NODE_TYPE = "drive_list_files"
    NODE_CATEGORY = "google_drive"
    NODE_DISPLAY_NAME = "Drive: List Files"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Drive List Files", **kwargs)
        # Note: _define_ports() is called by BaseNode.__init__

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # List files inputs
        self.add_input_port("folder_id", DataType.STRING, required=False)
        self.add_input_port("query", DataType.STRING, required=False)
        self.add_input_port("mime_type", DataType.STRING, required=False)
        self.add_input_port("max_results", DataType.INTEGER, required=False)
        self.add_input_port("order_by", DataType.STRING, required=False)
        self.add_input_port("include_trashed", DataType.BOOLEAN, required=False)

        # List files outputs
        self.add_output_port("files", DataType.LIST)
        self.add_output_port("file_count", DataType.INTEGER)
        self.add_output_port("has_more", DataType.BOOLEAN)
        self.add_output_port("folder_id", DataType.STRING)

    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: GoogleDriveClient,
    ) -> ExecutionResult:
        """List files in Google Drive."""
        folder_id = self._resolve_value(context, self.get_parameter("folder_id"))
        query = self._resolve_value(context, self.get_parameter("query"))
        mime_type = self._resolve_value(context, self.get_parameter("mime_type"))
        max_results = self.get_parameter("max_results") or 100
        order_by = self._resolve_value(context, self.get_parameter("order_by")) or "name"
        include_trashed = self.get_parameter("include_trashed") or False

        logger.debug(f"Listing files in Drive folder: {folder_id or 'all'}")

        # List files
        files, next_page_token = await client.list_files(
            folder_id=folder_id or None,
            query=query or None,
            mime_type=mime_type or None,
            page_size=min(max_results, 1000),
            order_by=order_by,
            include_trashed=include_trashed,
        )

        # Convert to serializable format
        files_data = []
        for f in files[:max_results]:
            files_data.append(
                {
                    "id": f.id,
                    "name": f.name,
                    "mimeType": f.mime_type,
                    "size": f.size,
                    "createdTime": f.created_time,
                    "modifiedTime": f.modified_time,
                    "parents": f.parents,
                    "webViewLink": f.web_view_link,
                    "starred": f.starred,
                    "trashed": f.trashed,
                }
            )

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("files", files_data)
        self.set_output_value("file_count", len(files_data))
        self.set_output_value("has_more", next_page_token is not None)
        self.set_output_value("folder_id", folder_id or "")

        logger.info(f"Listed {len(files_data)} files from Drive")

        return {
            "success": True,
            "files": files_data,
            "file_count": len(files_data),
            "has_more": next_page_token is not None,
            "next_nodes": ["exec_out"],
        }


# ============================================================================
# Drive Search Files Node
# ============================================================================


@properties(
    PropertyDef(
        "query",
        PropertyType.TEXT,
        default="",
        required=True,
        label="Search Query",
        placeholder="name contains 'report' and mimeType = 'application/pdf'",
        tooltip="Google Drive API query syntax",
    ),
    PropertyDef(
        "mime_type",
        PropertyType.CHOICE,
        default="",
        choices=[
            "",
            "application/vnd.google-apps.folder",
            "application/vnd.google-apps.document",
            "application/vnd.google-apps.spreadsheet",
            "application/vnd.google-apps.presentation",
            "application/pdf",
            "image/jpeg",
            "image/png",
            "application/zip",
        ],
        label="MIME Type Filter",
        tooltip="Additional MIME type filter (empty = all types)",
    ),
    DRIVE_MAX_RESULTS,
    PropertyDef(
        "include_trashed",
        PropertyType.BOOLEAN,
        default=False,
        label="Include Trashed",
        tooltip="Include files in trash",
    ),
)
@node(category="google")
class DriveSearchFilesNode(DriveBaseNode):
    """
    Search for files in Google Drive using query syntax.

    Inputs:
        - query: Search query using Drive API query syntax
        - mime_type: Additional MIME type filter
        - max_results: Maximum number of results
        - include_trashed: Include trashed files

    Outputs:
        - files: Array of matching file objects
        - file_count: Number of files found
        - success: Boolean
        - error: Error message if failed

    Query Syntax Examples:
        - "name contains 'report'"
        - "fullText contains 'quarterly report'"
        - "name = 'Budget 2024.xlsx'"
        - "mimeType = 'application/pdf'"
        - "modifiedTime > '2024-01-01T00:00:00'"
        - "'1234567890' in parents" (files in specific folder)
        - "sharedWithMe" (files shared with current user)
        - "starred" (starred files)
        - "name contains 'report' and mimeType = 'application/pdf'"
    """

    # @category: google
    # @requires: none
    # @ports: query, mime_type, max_results, include_trashed -> files, file_count

    NODE_TYPE = "drive_search_files"
    NODE_CATEGORY = "google_drive"
    NODE_DISPLAY_NAME = "Drive: Search Files"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Drive Search Files", **kwargs)
        # Note: _define_ports() is called by BaseNode.__init__

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Search inputs
        self.add_input_port("query", DataType.STRING, required=True)
        self.add_input_port("mime_type", DataType.STRING, required=False)
        self.add_input_port("max_results", DataType.INTEGER, required=False)
        self.add_input_port("include_trashed", DataType.BOOLEAN, required=False)

        # Search outputs
        self.add_output_port("files", DataType.LIST)
        self.add_output_port("file_count", DataType.INTEGER)

    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: GoogleDriveClient,
    ) -> ExecutionResult:
        """Search for files in Google Drive."""
        query = self._resolve_value(context, self.get_parameter("query"))
        mime_type = self._resolve_value(context, self.get_parameter("mime_type"))
        max_results = self.get_parameter("max_results") or 100
        include_trashed = self.get_parameter("include_trashed") or False

        if not query:
            self._set_error_outputs("Search query is required")
            return {
                "success": False,
                "error": "Search query is required",
                "next_nodes": [],
            }

        logger.debug(f"Searching files in Drive: {query}")

        # Search files
        files = await client.search_files(
            query=query,
            mime_type=mime_type or None,
            max_results=max_results,
            include_trashed=include_trashed,
        )

        # Convert to serializable format
        files_data = []
        for f in files:
            files_data.append(
                {
                    "id": f.id,
                    "name": f.name,
                    "mimeType": f.mime_type,
                    "size": f.size,
                    "createdTime": f.created_time,
                    "modifiedTime": f.modified_time,
                    "parents": f.parents,
                    "webViewLink": f.web_view_link,
                    "webContentLink": f.web_content_link,
                    "description": f.description,
                    "starred": f.starred,
                    "trashed": f.trashed,
                    "shared": f.shared,
                }
            )

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("files", files_data)
        self.set_output_value("file_count", len(files_data))

        logger.info(f"Found {len(files_data)} files matching query: {query}")

        return {
            "success": True,
            "files": files_data,
            "file_count": len(files_data),
            "next_nodes": [],
        }


__all__ = [
    "DriveCreateFolderNode",
    "DriveListFilesNode",
    "DriveSearchFilesNode",
]
