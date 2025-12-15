"""
Unit tests for Google Drive download nodes.

Tests the three download nodes:
- DriveDownloadFileNode (single file download)
- DriveDownloadFolderNode (download all files from folder)
- DriveBatchDownloadNode (download list of files)

Note: Values are set via set_input_value() to simulate how visual nodes
pass data through port connections. The config dict is used for design-time
values in the visual layer but the CredentialAwareMixin's get_parameter stub
interferes with direct config access in unit tests.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.google.drive.drive_files import (
    DriveDownloadFileNode,
    DriveDownloadFolderNode,
    DriveBatchDownloadNode,
)

from .conftest import MockDriveFile


# =============================================================================
# DriveDownloadFileNode Tests
# =============================================================================


class TestDriveDownloadFileNode:
    """Tests for DriveDownloadFileNode."""

    @pytest.fixture
    def node(self) -> DriveDownloadFileNode:
        """Create a test node instance."""
        return DriveDownloadFileNode(node_id="test_download_file_001")

    @pytest.mark.asyncio
    async def test_download_file_success(
        self,
        node: DriveDownloadFileNode,
        execution_context: ExecutionContext,
        mock_drive_client: MagicMock,
        tmp_download_dir: Path,
    ) -> None:
        """Test successful file download."""
        # Arrange
        dest_path = tmp_download_dir / "downloaded_file.pdf"
        node.set_input_value("file_id", "file_123")
        node.set_input_value("destination_path", str(dest_path))

        # Act
        result = await node._execute_drive(execution_context, mock_drive_client)

        # Assert
        assert result["success"] is True
        assert result["file_path"] == str(dest_path)
        mock_drive_client.download_file.assert_called_once_with(
            file_id="file_123",
            destination_path=str(dest_path),
        )

    @pytest.mark.asyncio
    async def test_download_file_missing_file_id(
        self,
        node: DriveDownloadFileNode,
        execution_context: ExecutionContext,
        mock_drive_client: MagicMock,
        tmp_download_dir: Path,
    ) -> None:
        """Test download fails when file_id is missing."""
        # Arrange
        dest_path = tmp_download_dir / "downloaded_file.pdf"
        node.set_input_value("file_id", "")  # Empty
        node.set_input_value("destination_path", str(dest_path))

        # Act
        result = await node._execute_drive(execution_context, mock_drive_client)

        # Assert
        assert result["success"] is False
        assert "File ID is required" in result["error"]
        mock_drive_client.download_file.assert_not_called()

    @pytest.mark.asyncio
    async def test_download_file_missing_destination(
        self,
        node: DriveDownloadFileNode,
        execution_context: ExecutionContext,
        mock_drive_client: MagicMock,
    ) -> None:
        """Test download fails when destination_path is missing."""
        # Arrange
        node.set_input_value("file_id", "file_123")
        node.set_input_value("destination_path", "")  # Empty

        # Act
        result = await node._execute_drive(execution_context, mock_drive_client)

        # Assert
        assert result["success"] is False
        assert "Destination path is required" in result["error"]
        mock_drive_client.download_file.assert_not_called()

    @pytest.mark.asyncio
    async def test_download_file_creates_parent_directory(
        self,
        node: DriveDownloadFileNode,
        execution_context: ExecutionContext,
        mock_drive_client: MagicMock,
        tmp_download_dir: Path,
    ) -> None:
        """Test that parent directory is created if it doesn't exist."""
        # Arrange
        nested_path = tmp_download_dir / "nested" / "subdir" / "file.pdf"
        node.set_input_value("file_id", "file_123")
        node.set_input_value("destination_path", str(nested_path))

        # Act
        result = await node._execute_drive(execution_context, mock_drive_client)

        # Assert
        assert result["success"] is True
        assert nested_path.parent.exists()


# =============================================================================
# DriveDownloadFolderNode Tests
# =============================================================================


class TestDriveDownloadFolderNode:
    """Tests for DriveDownloadFolderNode."""

    @pytest.fixture
    def node(self) -> DriveDownloadFolderNode:
        """Create a test node instance."""
        return DriveDownloadFolderNode(node_id="test_download_folder_001")

    @pytest.mark.asyncio
    async def test_download_folder_success(
        self,
        node: DriveDownloadFolderNode,
        execution_context: ExecutionContext,
        mock_drive_client: MagicMock,
        sample_drive_files: list[MockDriveFile],
        tmp_download_dir: Path,
    ) -> None:
        """Test successful folder download."""
        # Arrange
        node.set_input_value("folder_id", "folder_123")
        node.set_input_value("destination_folder", str(tmp_download_dir))
        mock_drive_client.list_files.return_value = (sample_drive_files, None)

        # Act
        result = await node._execute_drive(execution_context, mock_drive_client)

        # Assert
        assert result["success"] is True
        assert result["downloaded_count"] == 3
        assert len(result["file_paths"]) == 3
        mock_drive_client.list_files.assert_called_once()
        assert mock_drive_client.download_file.call_count == 3

    @pytest.mark.asyncio
    async def test_download_folder_empty(
        self,
        node: DriveDownloadFolderNode,
        execution_context: ExecutionContext,
        mock_drive_client: MagicMock,
        tmp_download_dir: Path,
    ) -> None:
        """Test download from empty folder."""
        # Arrange
        node.set_input_value("folder_id", "empty_folder")
        node.set_input_value("destination_folder", str(tmp_download_dir))
        mock_drive_client.list_files.return_value = ([], None)

        # Act
        result = await node._execute_drive(execution_context, mock_drive_client)

        # Assert
        assert result["success"] is True
        assert result["downloaded_count"] == 0
        assert result["file_paths"] == []
        mock_drive_client.download_file.assert_not_called()

    @pytest.mark.asyncio
    async def test_download_folder_skips_google_workspace_files(
        self,
        node: DriveDownloadFolderNode,
        execution_context: ExecutionContext,
        mock_drive_client: MagicMock,
        sample_google_workspace_files: list[MockDriveFile],
        tmp_download_dir: Path,
    ) -> None:
        """Test that Google Workspace files are skipped."""
        # Arrange
        node.set_input_value("folder_id", "folder_with_gdocs")
        node.set_input_value("destination_folder", str(tmp_download_dir))
        mock_drive_client.list_files.return_value = (
            sample_google_workspace_files,
            None,
        )

        # Act
        result = await node._execute_drive(execution_context, mock_drive_client)

        # Assert
        assert result["success"] is True
        assert result["downloaded_count"] == 0
        mock_drive_client.download_file.assert_not_called()

    @pytest.mark.asyncio
    async def test_download_folder_missing_folder_id(
        self,
        node: DriveDownloadFolderNode,
        execution_context: ExecutionContext,
        mock_drive_client: MagicMock,
        tmp_download_dir: Path,
    ) -> None:
        """Test download fails when folder_id is missing."""
        # Arrange
        node.set_input_value("folder_id", "")
        node.set_input_value("destination_folder", str(tmp_download_dir))

        # Act
        result = await node._execute_drive(execution_context, mock_drive_client)

        # Assert
        assert result["success"] is False
        assert "Folder ID is required" in result["error"]

    @pytest.mark.asyncio
    async def test_download_folder_list_files_error(
        self,
        node: DriveDownloadFolderNode,
        execution_context: ExecutionContext,
        mock_drive_client: MagicMock,
        tmp_download_dir: Path,
    ) -> None:
        """Test download handles list_files API error."""
        # Arrange
        node.set_input_value("folder_id", "folder_123")
        node.set_input_value("destination_folder", str(tmp_download_dir))
        mock_drive_client.list_files.side_effect = Exception("API Error: 403 Forbidden")

        # Act
        result = await node._execute_drive(execution_context, mock_drive_client)

        # Assert
        assert result["success"] is False
        assert "Failed to list files" in result["error"]

    @pytest.mark.asyncio
    async def test_download_folder_partial_failure(
        self,
        node: DriveDownloadFolderNode,
        execution_context: ExecutionContext,
        mock_drive_client: MagicMock,
        sample_drive_files: list[MockDriveFile],
        tmp_download_dir: Path,
    ) -> None:
        """Test download continues even if some files fail."""
        # Arrange
        node.set_input_value("folder_id", "folder_123")
        node.set_input_value("destination_folder", str(tmp_download_dir))
        mock_drive_client.list_files.return_value = (sample_drive_files, None)

        # Make second file fail
        call_count = [0]

        async def download_with_error(file_id: str, destination_path: str) -> Path:
            call_count[0] += 1
            if call_count[0] == 2:  # Second file fails
                raise Exception("Download failed")
            return Path(destination_path)

        mock_drive_client.download_file = AsyncMock(side_effect=download_with_error)

        # Act
        result = await node._execute_drive(execution_context, mock_drive_client)

        # Assert
        assert result["success"] is True  # Overall success
        assert result["downloaded_count"] == 2  # 2 succeeded
        assert len(result.get("errors", [])) == 1  # 1 failed


# =============================================================================
# DriveBatchDownloadNode Tests
# =============================================================================


class TestDriveBatchDownloadNode:
    """Tests for DriveBatchDownloadNode."""

    @pytest.fixture
    def node(self) -> DriveBatchDownloadNode:
        """Create a test node instance."""
        return DriveBatchDownloadNode(node_id="test_batch_download_001")

    @pytest.fixture
    def file_list(self) -> list[dict]:
        """Create a list of file dicts for batch download."""
        return [
            {"id": "file_001", "name": "doc1.pdf", "mime_type": "application/pdf"},
            {
                "id": "file_002",
                "name": "doc2.xlsx",
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            },
            {"id": "file_003", "name": "image.png", "mime_type": "image/png"},
        ]

    @pytest.mark.asyncio
    async def test_batch_download_success(
        self,
        node: DriveBatchDownloadNode,
        execution_context: ExecutionContext,
        mock_drive_client: MagicMock,
        file_list: list[dict],
        tmp_download_dir: Path,
    ) -> None:
        """Test successful batch download."""
        # Arrange
        node.set_input_value("files", file_list)
        node.set_input_value("destination_folder", str(tmp_download_dir))

        # Act
        result = await node._execute_drive(execution_context, mock_drive_client)

        # Assert
        assert result["success"] is True
        assert result["downloaded_count"] == 3
        assert result["failed_count"] == 0
        assert len(result["file_paths"]) == 3
        assert mock_drive_client.download_file.call_count == 3

    @pytest.mark.asyncio
    async def test_batch_download_empty_list(
        self,
        node: DriveBatchDownloadNode,
        execution_context: ExecutionContext,
        mock_drive_client: MagicMock,
        tmp_download_dir: Path,
    ) -> None:
        """Test batch download with empty file list."""
        # Arrange
        node.set_input_value("files", [])
        node.set_input_value("destination_folder", str(tmp_download_dir))

        # Act
        result = await node._execute_drive(execution_context, mock_drive_client)

        # Assert
        assert result["success"] is False  # No source provided
        assert "Files list or Folder ID/URL is required" in result["error"]

    @pytest.mark.asyncio
    async def test_batch_download_from_folder_url_recursive(
        self,
        node: DriveBatchDownloadNode,
        execution_context: ExecutionContext,
        mock_drive_client: MagicMock,
        tmp_download_dir: Path,
    ) -> None:
        """Test batch download can download an entire folder from a pasted URL."""
        # Arrange
        node.set_input_value(
            "folder_id",
            "https://drive.google.com/drive/folders/folder_root?usp=sharing",
        )
        node.set_input_value("destination_folder", str(tmp_download_dir))

        folder = MockDriveFile(
            id="sub_001",
            name="Sub:Folder",
            mime_type="application/vnd.google-apps.folder",
        )
        file_1 = MockDriveFile(id="file_001", name="a.txt", mime_type="text/plain")
        file_2 = MockDriveFile(id="file_002", name="b.txt", mime_type="text/plain")

        async def list_files_side_effect(*, folder_id: str | None = None, **kwargs):
            if folder_id == "folder_root":
                return ([folder, file_1], None)
            if folder_id == "sub_001":
                return ([file_2], None)
            return ([], None)

        mock_drive_client.list_files = AsyncMock(side_effect=list_files_side_effect)

        # Act
        result = await node._execute_drive(execution_context, mock_drive_client)

        # Assert
        assert result["success"] is True
        assert result["downloaded_count"] == 2
        assert mock_drive_client.list_files.call_count == 2
        assert mock_drive_client.download_file.call_count == 2

        destination_paths = [
            call.kwargs["destination_path"]
            for call in mock_drive_client.download_file.call_args_list
        ]
        assert str(tmp_download_dir / "a.txt") in destination_paths
        assert str(tmp_download_dir / "Sub_Folder" / "b.txt") in destination_paths

    @pytest.mark.asyncio
    async def test_batch_download_invalid_file_objects(
        self,
        node: DriveBatchDownloadNode,
        execution_context: ExecutionContext,
        mock_drive_client: MagicMock,
        tmp_download_dir: Path,
    ) -> None:
        """Test batch download with invalid file objects (no id field)."""
        # Arrange
        invalid_files = [
            {"name": "no_id.pdf"},  # Missing id
            {"id": "valid_001", "name": "valid.pdf"},
        ]
        node.set_input_value("files", invalid_files)
        node.set_input_value("destination_folder", str(tmp_download_dir))

        # Act
        result = await node._execute_drive(execution_context, mock_drive_client)

        # Assert
        assert result["success"] is True
        assert result["downloaded_count"] == 1  # Only valid file downloaded
        mock_drive_client.download_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_download_skips_google_workspace_files(
        self,
        node: DriveBatchDownloadNode,
        execution_context: ExecutionContext,
        mock_drive_client: MagicMock,
        tmp_download_dir: Path,
    ) -> None:
        """Test that Google Workspace files are skipped in batch."""
        # Arrange
        mixed_files = [
            {"id": "file_001", "name": "doc.pdf", "mime_type": "application/pdf"},
            {
                "id": "gdoc_001",
                "name": "Google Doc",
                "mime_type": "application/vnd.google-apps.document",
            },
            {
                "id": "gsheet_001",
                "name": "Google Sheet",
                "mime_type": "application/vnd.google-apps.spreadsheet",
            },
        ]
        node.set_input_value("files", mixed_files)
        node.set_input_value("destination_folder", str(tmp_download_dir))

        # Act
        result = await node._execute_drive(execution_context, mock_drive_client)

        # Assert
        assert result["success"] is True
        assert result["downloaded_count"] == 1  # Only PDF downloaded
        mock_drive_client.download_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_download_missing_destination_folder(
        self,
        node: DriveBatchDownloadNode,
        execution_context: ExecutionContext,
        mock_drive_client: MagicMock,
        file_list: list[dict],
    ) -> None:
        """Test batch download fails when destination_folder is missing."""
        # Arrange
        node.set_input_value("files", file_list)
        node.set_input_value("destination_folder", "")

        # Act
        result = await node._execute_drive(execution_context, mock_drive_client)

        # Assert
        assert result["success"] is False
        assert "Destination folder is required" in result["error"]

    @pytest.mark.asyncio
    async def test_batch_download_partial_failures(
        self,
        node: DriveBatchDownloadNode,
        execution_context: ExecutionContext,
        mock_drive_client: MagicMock,
        file_list: list[dict],
        tmp_download_dir: Path,
    ) -> None:
        """Test batch download tracks partial failures."""
        # Arrange
        node.set_input_value("files", file_list)
        node.set_input_value("destination_folder", str(tmp_download_dir))

        # Make first and third files succeed, second fails
        call_count = [0]

        async def download_with_error(file_id: str, destination_path: str) -> Path:
            call_count[0] += 1
            if call_count[0] == 2:  # Second file fails
                raise Exception("Network error")
            return Path(destination_path)

        mock_drive_client.download_file = AsyncMock(side_effect=download_with_error)

        # Act
        result = await node._execute_drive(execution_context, mock_drive_client)

        # Assert
        assert result["success"] is True  # Overall success (some files downloaded)
        assert result["downloaded_count"] == 2
        assert result["failed_count"] == 1
        assert result["errors"] is not None
        assert len(result["errors"]) == 1

    @pytest.mark.asyncio
    async def test_batch_download_creates_destination_folder(
        self,
        node: DriveBatchDownloadNode,
        execution_context: ExecutionContext,
        mock_drive_client: MagicMock,
        file_list: list[dict],
        tmp_path: Path,
    ) -> None:
        """Test that destination folder is created if it doesn't exist."""
        # Arrange
        new_folder = tmp_path / "new_folder" / "subdir"
        node.set_input_value("files", file_list)
        node.set_input_value("destination_folder", str(new_folder))

        # Act
        result = await node._execute_drive(execution_context, mock_drive_client)

        # Assert
        assert result["success"] is True
        assert new_folder.exists()

    @pytest.mark.asyncio
    async def test_batch_download_uses_file_id_as_name_fallback(
        self,
        node: DriveBatchDownloadNode,
        execution_context: ExecutionContext,
        mock_drive_client: MagicMock,
        tmp_download_dir: Path,
    ) -> None:
        """Test that file_id is used as filename if name is missing."""
        # Arrange
        files_without_names = [
            {"id": "abc123"},  # No name field
        ]
        node.set_input_value("files", files_without_names)
        node.set_input_value("destination_folder", str(tmp_download_dir))

        # Act
        result = await node._execute_drive(execution_context, mock_drive_client)

        # Assert
        assert result["success"] is True
        # Verify download was called with file_id as filename
        mock_drive_client.download_file.assert_called_once()
        call_args = mock_drive_client.download_file.call_args
        assert "abc123" in call_args.kwargs["destination_path"]
