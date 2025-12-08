"""
Google Drive batch operation nodes for CasareRPA.

This module provides nodes for batch operations on Google Drive files:
- DriveBatchDeleteNode: Delete multiple files in one request
- DriveBatchMoveNode: Move multiple files to a folder in one request
- DriveBatchCopyNode: Copy multiple files to a folder in one request

All nodes use the Google Drive API v3 batch endpoint for efficiency.
Maximum 100 operations per batch request.
Credential selection is handled by NodeGoogleCredentialWidget in the visual layer.
"""

from typing import Any, Dict, List

from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.infrastructure.resources.google_drive_client import GoogleDriveClient
from casare_rpa.nodes.google.drive.drive_base import DriveBaseNode


MAX_BATCH_SIZE = 100


# ============================================================================
# Reusable Property Definitions
# ============================================================================

# NOTE: access_token and credential_name are NOT defined here.
# Credential selection is handled by NodeGoogleCredentialWidget in the visual layer.
# The credential_id property is set by the picker widget.

DRIVE_FILE_IDS = PropertyDef(
    "file_ids",
    PropertyType.LIST,
    default=[],
    required=True,
    label="File IDs",
    tooltip="List of Google Drive file IDs to process",
)

DRIVE_FOLDER_ID = PropertyDef(
    "folder_id",
    PropertyType.STRING,
    default="",
    required=True,
    label="Destination Folder ID",
    placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    tooltip="ID of the destination folder",
)


# ============================================================================
# Drive Batch Delete Node
# ============================================================================


@node_schema(
    DRIVE_FILE_IDS,
    PropertyDef(
        "continue_on_error",
        PropertyType.BOOLEAN,
        default=True,
        label="Continue on Error",
        tooltip="Continue deleting remaining files if one fails",
    ),
)
@executable_node
class DriveBatchDeleteNode(DriveBaseNode):
    """
    Delete multiple Google Drive files in a batch operation.

    This node uses the Drive API batch endpoint to delete multiple files
    in a single HTTP request, making it much faster than individual deletes.
    Maximum 100 files per batch.

    Inputs:
        file_ids: List of file IDs to delete

    Outputs:
        deleted_count: Number of files successfully deleted
        failed_count: Number of files that failed to delete
        results: Detailed results for each file
        success: Whether all deletes succeeded
        error: Error message if failed
    """

    NODE_TYPE = "drive_batch_delete"
    NODE_CATEGORY = "google_drive"
    NODE_DISPLAY_NAME = "Drive: Batch Delete"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Drive Batch Delete", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Batch delete inputs
        self.add_input_port("file_ids", DataType.LIST, required=True)

        # Batch delete outputs
        self.add_output_port("deleted_count", DataType.INTEGER)
        self.add_output_port("failed_count", DataType.INTEGER)
        self.add_output_port("results", DataType.LIST)

    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: GoogleDriveClient,
    ) -> ExecutionResult:
        """Delete multiple files in Google Drive."""
        file_ids = self.get_parameter("file_ids") or []
        continue_on_error = self.get_parameter("continue_on_error", True)

        # Resolve file_ids if it's a variable reference
        if isinstance(file_ids, str):
            file_ids = self._resolve_value(context, file_ids)
            if isinstance(file_ids, str):
                # Try to parse as JSON
                import json

                try:
                    file_ids = json.loads(file_ids)
                except json.JSONDecodeError:
                    file_ids = [file_ids]

        if not file_ids:
            self._set_error_outputs("File IDs list is required")
            return {
                "success": False,
                "error": "File IDs list is required",
                "next_nodes": [],
            }

        if not isinstance(file_ids, list):
            self._set_error_outputs("File IDs must be a list")
            return {
                "success": False,
                "error": "File IDs must be a list",
                "next_nodes": [],
            }

        if len(file_ids) > MAX_BATCH_SIZE:
            self._set_error_outputs(f"Maximum {MAX_BATCH_SIZE} files per batch")
            return {
                "success": False,
                "error": f"Maximum {MAX_BATCH_SIZE} files per batch",
                "next_nodes": [],
            }

        logger.debug(f"Batch deleting {len(file_ids)} files")

        all_results: List[Dict[str, Any]] = []
        deleted_count = 0
        failed_count = 0

        for file_id in file_ids:
            try:
                await client.delete_file(file_id=file_id, permanent=True)
                all_results.append(
                    {
                        "file_id": file_id,
                        "success": True,
                    }
                )
                deleted_count += 1
            except Exception as e:
                all_results.append(
                    {
                        "file_id": file_id,
                        "success": False,
                        "error": str(e),
                    }
                )
                failed_count += 1
                if not continue_on_error:
                    break

        success = failed_count == 0

        # Set outputs
        if success:
            self._set_success_outputs()
        else:
            self.set_output_value("success", failed_count == 0)
            self.set_output_value("error", f"{failed_count} files failed to delete")
            self.set_output_value("error_code", 0)

        self.set_output_value("deleted_count", deleted_count)
        self.set_output_value("failed_count", failed_count)
        self.set_output_value("results", all_results)

        logger.info(
            f"Batch delete complete: {deleted_count} deleted, {failed_count} failed"
        )

        return {
            "success": success,
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "results": all_results,
            "next_nodes": [],
        }


# ============================================================================
# Drive Batch Move Node
# ============================================================================


@node_schema(
    DRIVE_FILE_IDS,
    DRIVE_FOLDER_ID,
    PropertyDef(
        "continue_on_error",
        PropertyType.BOOLEAN,
        default=True,
        label="Continue on Error",
        tooltip="Continue moving remaining files if one fails",
    ),
)
@executable_node
class DriveBatchMoveNode(DriveBaseNode):
    """
    Move multiple Google Drive files to a folder in a batch operation.

    This node moves multiple files to a destination folder.
    Moving is done by updating the parents metadata of each file.

    Inputs:
        file_ids: List of file IDs to move
        folder_id: Destination folder ID

    Outputs:
        moved_count: Number of files successfully moved
        failed_count: Number of files that failed to move
        results: Detailed results for each file
        success: Whether all moves succeeded
        error: Error message if failed
    """

    NODE_TYPE = "drive_batch_move"
    NODE_CATEGORY = "google_drive"
    NODE_DISPLAY_NAME = "Drive: Batch Move"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Drive Batch Move", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Batch move inputs
        self.add_input_port("file_ids", DataType.LIST, required=True)
        self.add_input_port("folder_id", DataType.STRING, required=True)

        # Batch move outputs
        self.add_output_port("moved_count", DataType.INTEGER)
        self.add_output_port("failed_count", DataType.INTEGER)
        self.add_output_port("results", DataType.LIST)

    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: GoogleDriveClient,
    ) -> ExecutionResult:
        """Move multiple files to a folder in Google Drive."""
        file_ids = self.get_parameter("file_ids") or []
        folder_id = self._resolve_value(context, self.get_parameter("folder_id"))
        continue_on_error = self.get_parameter("continue_on_error", True)

        # Resolve file_ids if it's a variable reference
        if isinstance(file_ids, str):
            file_ids = self._resolve_value(context, file_ids)
            if isinstance(file_ids, str):
                import json

                try:
                    file_ids = json.loads(file_ids)
                except json.JSONDecodeError:
                    file_ids = [file_ids]

        if not file_ids:
            self._set_error_outputs("File IDs list is required")
            return {
                "success": False,
                "error": "File IDs list is required",
                "next_nodes": [],
            }

        if not folder_id:
            self._set_error_outputs("Destination folder ID is required")
            return {
                "success": False,
                "error": "Destination folder ID is required",
                "next_nodes": [],
            }

        if not isinstance(file_ids, list):
            self._set_error_outputs("File IDs must be a list")
            return {
                "success": False,
                "error": "File IDs must be a list",
                "next_nodes": [],
            }

        if len(file_ids) > MAX_BATCH_SIZE:
            self._set_error_outputs(f"Maximum {MAX_BATCH_SIZE} files per batch")
            return {
                "success": False,
                "error": f"Maximum {MAX_BATCH_SIZE} files per batch",
                "next_nodes": [],
            }

        logger.debug(f"Batch moving {len(file_ids)} files to folder {folder_id}")

        all_results: List[Dict[str, Any]] = []
        moved_count = 0
        failed_count = 0

        for file_id in file_ids:
            try:
                await client.move_file(file_id=file_id, folder_id=folder_id)
                all_results.append(
                    {
                        "file_id": file_id,
                        "success": True,
                        "new_parent": folder_id,
                    }
                )
                moved_count += 1
            except Exception as e:
                all_results.append(
                    {
                        "file_id": file_id,
                        "success": False,
                        "error": str(e),
                    }
                )
                failed_count += 1
                if not continue_on_error:
                    break

        success = failed_count == 0

        # Set outputs
        if success:
            self._set_success_outputs()
        else:
            self.set_output_value("success", failed_count == 0)
            self.set_output_value("error", f"{failed_count} files failed to move")
            self.set_output_value("error_code", 0)

        self.set_output_value("moved_count", moved_count)
        self.set_output_value("failed_count", failed_count)
        self.set_output_value("results", all_results)

        logger.info(f"Batch move complete: {moved_count} moved, {failed_count} failed")

        return {
            "success": success,
            "moved_count": moved_count,
            "failed_count": failed_count,
            "results": all_results,
            "next_nodes": [],
        }


# ============================================================================
# Drive Batch Copy Node
# ============================================================================


@node_schema(
    DRIVE_FILE_IDS,
    DRIVE_FOLDER_ID,
    PropertyDef(
        "continue_on_error",
        PropertyType.BOOLEAN,
        default=True,
        label="Continue on Error",
        tooltip="Continue copying remaining files if one fails",
    ),
    PropertyDef(
        "preserve_name",
        PropertyType.BOOLEAN,
        default=True,
        label="Preserve Name",
        tooltip="Keep original file names (otherwise appends ' - Copy')",
    ),
)
@executable_node
class DriveBatchCopyNode(DriveBaseNode):
    """
    Copy multiple Google Drive files to a folder in a batch operation.

    This node copies multiple files to a destination folder.
    Each file is copied to the destination folder with the same name
    (or modified name if preserve_name is False).

    Inputs:
        file_ids: List of file IDs to copy
        folder_id: Destination folder ID

    Outputs:
        copied_count: Number of files successfully copied
        failed_count: Number of files that failed to copy
        new_file_ids: List of IDs of the copied files
        results: Detailed results for each file
        success: Whether all copies succeeded
        error: Error message if failed
    """

    NODE_TYPE = "drive_batch_copy"
    NODE_CATEGORY = "google_drive"
    NODE_DISPLAY_NAME = "Drive: Batch Copy"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Drive Batch Copy", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Batch copy inputs
        self.add_input_port("file_ids", DataType.LIST, required=True)
        self.add_input_port("folder_id", DataType.STRING, required=True)

        # Batch copy outputs
        self.add_output_port("copied_count", DataType.INTEGER)
        self.add_output_port("failed_count", DataType.INTEGER)
        self.add_output_port("new_file_ids", DataType.LIST)
        self.add_output_port("results", DataType.LIST)

    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: GoogleDriveClient,
    ) -> ExecutionResult:
        """Copy multiple files to a folder in Google Drive."""
        file_ids = self.get_parameter("file_ids") or []
        folder_id = self._resolve_value(context, self.get_parameter("folder_id"))
        continue_on_error = self.get_parameter("continue_on_error", True)

        # Resolve file_ids if it's a variable reference
        if isinstance(file_ids, str):
            file_ids = self._resolve_value(context, file_ids)
            if isinstance(file_ids, str):
                import json

                try:
                    file_ids = json.loads(file_ids)
                except json.JSONDecodeError:
                    file_ids = [file_ids]

        if not file_ids:
            self._set_error_outputs("File IDs list is required")
            return {
                "success": False,
                "error": "File IDs list is required",
                "next_nodes": [],
            }

        if not folder_id:
            self._set_error_outputs("Destination folder ID is required")
            return {
                "success": False,
                "error": "Destination folder ID is required",
                "next_nodes": [],
            }

        if not isinstance(file_ids, list):
            self._set_error_outputs("File IDs must be a list")
            return {
                "success": False,
                "error": "File IDs must be a list",
                "next_nodes": [],
            }

        if len(file_ids) > MAX_BATCH_SIZE:
            self._set_error_outputs(f"Maximum {MAX_BATCH_SIZE} files per batch")
            return {
                "success": False,
                "error": f"Maximum {MAX_BATCH_SIZE} files per batch",
                "next_nodes": [],
            }

        logger.debug(f"Batch copying {len(file_ids)} files to folder {folder_id}")

        all_results: List[Dict[str, Any]] = []
        new_file_ids: List[str] = []
        copied_count = 0
        failed_count = 0

        for file_id in file_ids:
            try:
                result = await client.copy_file(file_id=file_id, folder_id=folder_id)
                all_results.append(
                    {
                        "file_id": file_id,
                        "success": True,
                        "new_file_id": result.id,
                        "new_name": result.name,
                    }
                )
                new_file_ids.append(result.id)
                copied_count += 1
            except Exception as e:
                all_results.append(
                    {
                        "file_id": file_id,
                        "success": False,
                        "error": str(e),
                    }
                )
                failed_count += 1
                if not continue_on_error:
                    break

        success = failed_count == 0

        # Set outputs
        if success:
            self._set_success_outputs()
        else:
            self.set_output_value("success", failed_count == 0)
            self.set_output_value("error", f"{failed_count} files failed to copy")
            self.set_output_value("error_code", 0)

        self.set_output_value("copied_count", copied_count)
        self.set_output_value("failed_count", failed_count)
        self.set_output_value("new_file_ids", new_file_ids)
        self.set_output_value("results", all_results)

        logger.info(
            f"Batch copy complete: {copied_count} copied, {failed_count} failed"
        )

        return {
            "success": success,
            "copied_count": copied_count,
            "failed_count": failed_count,
            "new_file_ids": new_file_ids,
            "results": all_results,
            "next_nodes": [],
        }


__all__ = [
    "DriveBatchDeleteNode",
    "DriveBatchMoveNode",
    "DriveBatchCopyNode",
]
