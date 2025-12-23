"""
Tests for FileSystemSuperNode.

This test suite covers all 12 file system operations:
- Read File, Write File, Append File
- Delete File, Copy File, Move File
- File Exists, Get File Size, Get File Info
- Create Directory, List Files, List Directory

Test Philosophy:
- Happy path: Normal operation with valid inputs
- Sad path: Expected failures (file not found, permission errors)
- Edge cases: Boundary conditions (empty files, special characters)

Run: pytest tests/nodes/file/test_file_system_super_node.py -v
"""

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.file.file_security import PathSecurityError
from casare_rpa.nodes.file.super_node import (
    FILE_SYSTEM_PORT_SCHEMA,
    FileSystemAction,
    FileSystemSuperNode,
)


def setup_action_ports(node: FileSystemSuperNode, action: str) -> None:
    """
    Setup output ports for a specific action.

    In production, the visual layer handles dynamic port management.
    For testing, we manually add the required ports.
    """
    config = FILE_SYSTEM_PORT_SCHEMA.get_config(action)
    if config:
        for port_def in config.outputs:
            if port_def.name not in node.output_ports:
                node.add_output_port(port_def.name, port_def.data_type)
        for port_def in config.inputs:
            if port_def.name not in node.input_ports:
                node.add_input_port(port_def.name, port_def.data_type)


# =============================================================================
# FileSystemSuperNode Instantiation Tests
# =============================================================================


class TestFileSystemSuperNodeInstantiation:
    """Test node creation and configuration."""

    def test_create_node_with_default_config(self) -> None:
        """Test creating node with default configuration."""
        node = FileSystemSuperNode("test_node")
        assert node.node_id == "test_node"
        assert node.node_type == "FileSystemSuperNode"
        assert node.name == "File System"

    def test_create_node_with_custom_name(self) -> None:
        """Test creating node with custom name."""
        node = FileSystemSuperNode("test_node", name="Custom File Op")
        assert node.name == "Custom File Op"

    def test_create_node_with_action_config(self) -> None:
        """Test creating node with specific action."""
        node = FileSystemSuperNode("test_node", config={"action": FileSystemAction.WRITE.value})
        assert node.get_parameter("action") == "Write File"

    def test_node_has_exec_ports(self) -> None:
        """Test that node has exec input/output ports."""
        node = FileSystemSuperNode("test_node")
        assert "exec_in" in node.input_ports
        assert "exec_out" in node.output_ports

    def test_node_default_ports_for_read_action(self) -> None:
        """Test default ports match Read File action."""
        node = FileSystemSuperNode("test_node")
        assert "file_path" in node.input_ports
        assert "content" in node.output_ports
        assert "size" in node.output_ports
        assert "success" in node.output_ports


# =============================================================================
# Read File Action Tests
# =============================================================================


class TestReadFileAction:
    """Tests for Read File action."""

    @pytest.mark.asyncio
    async def test_read_file_success(self, execution_context, temp_test_file: Path) -> None:
        """SUCCESS: Read existing text file."""
        node = FileSystemSuperNode(
            "test_read",
            config={
                "action": FileSystemAction.READ.value,
                "file_path": str(temp_test_file),
                "encoding": "utf-8",
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("content") == "Hello, World!"
        assert node.get_output_value("size") == 13
        assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_read_file_not_found(self, execution_context, tmp_path: Path) -> None:
        """SAD PATH: File does not exist."""
        non_existent = tmp_path / "does_not_exist.txt"
        node = FileSystemSuperNode(
            "test_read",
            config={
                "action": FileSystemAction.READ.value,
                "file_path": str(non_existent),
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_read_file_missing_path(self, execution_context) -> None:
        """SAD PATH: No file path provided."""
        node = FileSystemSuperNode(
            "test_read",
            config={
                "action": FileSystemAction.READ.value,
                "file_path": "",
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_read_file_max_size_exceeded(self, execution_context, tmp_path: Path) -> None:
        """EDGE CASE: File exceeds max size limit."""
        # Create file larger than limit
        large_file = tmp_path / "large.txt"
        large_file.write_text("x" * 1000, encoding="utf-8")

        node = FileSystemSuperNode(
            "test_read",
            config={
                "action": FileSystemAction.READ.value,
                "file_path": str(large_file),
                "max_size": 100,  # Set limit to 100 bytes
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "exceeds limit" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_read_file_empty(self, execution_context, tmp_path: Path) -> None:
        """EDGE CASE: Empty file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("", encoding="utf-8")

        node = FileSystemSuperNode(
            "test_read",
            config={
                "action": FileSystemAction.READ.value,
                "file_path": str(empty_file),
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("content") == ""
        assert node.get_output_value("size") == 0


# =============================================================================
# Write File Action Tests
# =============================================================================


class TestWriteFileAction:
    """Tests for Write File action."""

    @pytest.mark.asyncio
    async def test_write_file_success(self, execution_context, tmp_path: Path) -> None:
        """SUCCESS: Write content to new file."""
        output_file = tmp_path / "output.txt"

        node = FileSystemSuperNode(
            "test_write",
            config={
                "action": FileSystemAction.WRITE.value,
                "file_path": str(output_file),
                "content": "Test content",
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.WRITE.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert output_file.exists()
        assert output_file.read_text() == "Test content"
        assert node.get_output_value("bytes_written") == 12

    @pytest.mark.asyncio
    async def test_write_file_creates_directories(self, execution_context, tmp_path: Path) -> None:
        """SUCCESS: Creates parent directories when create_dirs=True."""
        nested_file = tmp_path / "new" / "nested" / "dir" / "file.txt"

        node = FileSystemSuperNode(
            "test_write",
            config={
                "action": FileSystemAction.WRITE.value,
                "file_path": str(nested_file),
                "content": "Nested content",
                "create_dirs": True,
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.WRITE.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert nested_file.exists()
        assert nested_file.read_text() == "Nested content"

    @pytest.mark.asyncio
    async def test_write_file_overwrites_existing(
        self, execution_context, temp_test_file: Path
    ) -> None:
        """SUCCESS: Overwrites existing file content."""
        original_content = temp_test_file.read_text()

        node = FileSystemSuperNode(
            "test_write",
            config={
                "action": FileSystemAction.WRITE.value,
                "file_path": str(temp_test_file),
                "content": "New content",
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.WRITE.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert temp_test_file.read_text() == "New content"
        assert temp_test_file.read_text() != original_content


# =============================================================================
# Append File Action Tests
# =============================================================================


class TestAppendFileAction:
    """Tests for Append File action."""

    @pytest.mark.asyncio
    async def test_append_file_success(self, execution_context, temp_test_file: Path) -> None:
        """SUCCESS: Append content to existing file."""
        node = FileSystemSuperNode(
            "test_append",
            config={
                "action": FileSystemAction.APPEND.value,
                "file_path": str(temp_test_file),
                "content": " - Appended!",
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.APPEND.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert temp_test_file.read_text() == "Hello, World! - Appended!"

    @pytest.mark.asyncio
    async def test_append_creates_file_if_missing(self, execution_context, tmp_path: Path) -> None:
        """SUCCESS: Creates file if it doesn't exist and create_if_missing=True."""
        new_file = tmp_path / "new_append.txt"

        node = FileSystemSuperNode(
            "test_append",
            config={
                "action": FileSystemAction.APPEND.value,
                "file_path": str(new_file),
                "content": "New content",
                "create_if_missing": True,
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.APPEND.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert new_file.exists()
        assert new_file.read_text() == "New content"

    @pytest.mark.asyncio
    async def test_append_fails_if_file_missing_and_create_disabled(
        self, execution_context, tmp_path: Path
    ) -> None:
        """SAD PATH: Fails when file missing and create_if_missing=False."""
        missing_file = tmp_path / "missing.txt"

        node = FileSystemSuperNode(
            "test_append",
            config={
                "action": FileSystemAction.APPEND.value,
                "file_path": str(missing_file),
                "content": "Content",
                "create_if_missing": False,
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.APPEND.value)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "not found" in result["error"].lower()


# =============================================================================
# Delete File Action Tests
# =============================================================================


class TestDeleteFileAction:
    """Tests for Delete File action."""

    @pytest.mark.asyncio
    async def test_delete_file_success(self, execution_context, temp_test_file: Path) -> None:
        """SUCCESS: Delete existing file."""
        assert temp_test_file.exists()

        node = FileSystemSuperNode(
            "test_delete",
            config={
                "action": FileSystemAction.DELETE.value,
                "file_path": str(temp_test_file),
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.DELETE.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert not temp_test_file.exists()

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, execution_context, tmp_path: Path) -> None:
        """SAD PATH: File does not exist and ignore_missing=False."""
        non_existent = tmp_path / "does_not_exist.txt"

        node = FileSystemSuperNode(
            "test_delete",
            config={
                "action": FileSystemAction.DELETE.value,
                "file_path": str(non_existent),
                "ignore_missing": False,
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.DELETE.value)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_delete_file_ignore_missing(self, execution_context, tmp_path: Path) -> None:
        """SUCCESS: Ignore missing file when ignore_missing=True."""
        non_existent = tmp_path / "does_not_exist.txt"

        node = FileSystemSuperNode(
            "test_delete",
            config={
                "action": FileSystemAction.DELETE.value,
                "file_path": str(non_existent),
                "ignore_missing": True,
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.DELETE.value)

        result = await node.execute(execution_context)

        assert result["success"] is True


# =============================================================================
# Copy File Action Tests
# =============================================================================


class TestCopyFileAction:
    """Tests for Copy File action."""

    @pytest.mark.asyncio
    async def test_copy_file_success(
        self, execution_context, temp_test_file: Path, tmp_path: Path
    ) -> None:
        """SUCCESS: Copy file to new location."""
        dest_file = tmp_path / "copied.txt"

        node = FileSystemSuperNode(
            "test_copy",
            config={
                "action": FileSystemAction.COPY.value,
                "source_path": str(temp_test_file),
                "dest_path": str(dest_file),
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.COPY.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert dest_file.exists()
        assert dest_file.read_text() == temp_test_file.read_text()
        assert temp_test_file.exists()  # Source still exists

    @pytest.mark.asyncio
    async def test_copy_file_destination_exists_no_overwrite(
        self, execution_context, temp_test_file: Path, tmp_path: Path
    ) -> None:
        """SAD PATH: Destination exists and overwrite=False."""
        existing_dest = tmp_path / "existing.txt"
        existing_dest.write_text("Existing content")

        node = FileSystemSuperNode(
            "test_copy",
            config={
                "action": FileSystemAction.COPY.value,
                "source_path": str(temp_test_file),
                "dest_path": str(existing_dest),
                "overwrite": False,
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.COPY.value)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "exists" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_copy_file_source_not_found(self, execution_context, tmp_path: Path) -> None:
        """SAD PATH: Source file does not exist."""
        non_existent = tmp_path / "missing.txt"
        dest = tmp_path / "dest.txt"

        node = FileSystemSuperNode(
            "test_copy",
            config={
                "action": FileSystemAction.COPY.value,
                "source_path": str(non_existent),
                "dest_path": str(dest),
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.COPY.value)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "not found" in result["error"].lower()


# =============================================================================
# Move File Action Tests
# =============================================================================


class TestMoveFileAction:
    """Tests for Move File action."""

    @pytest.mark.asyncio
    async def test_move_file_success(
        self, execution_context, temp_test_file: Path, tmp_path: Path
    ) -> None:
        """SUCCESS: Move file to new location."""
        dest_file = tmp_path / "moved.txt"
        original_content = temp_test_file.read_text()

        node = FileSystemSuperNode(
            "test_move",
            config={
                "action": FileSystemAction.MOVE.value,
                "source_path": str(temp_test_file),
                "dest_path": str(dest_file),
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.MOVE.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert dest_file.exists()
        assert dest_file.read_text() == original_content
        assert not temp_test_file.exists()  # Source should be removed

    @pytest.mark.asyncio
    async def test_move_file_rename(self, execution_context, temp_test_file: Path) -> None:
        """SUCCESS: Rename file in same directory."""
        dest_file = temp_test_file.parent / "renamed.txt"

        node = FileSystemSuperNode(
            "test_move",
            config={
                "action": FileSystemAction.MOVE.value,
                "source_path": str(temp_test_file),
                "dest_path": str(dest_file),
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.MOVE.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert dest_file.exists()
        assert not temp_test_file.exists()


# =============================================================================
# File Exists Action Tests
# =============================================================================


class TestFileExistsAction:
    """Tests for File Exists action."""

    @pytest.mark.asyncio
    async def test_file_exists_true(self, execution_context, temp_test_file: Path) -> None:
        """SUCCESS: File exists."""
        node = FileSystemSuperNode(
            "test_exists",
            config={
                "action": FileSystemAction.EXISTS.value,
                "path": str(temp_test_file),
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.EXISTS.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("exists") is True
        assert node.get_output_value("is_file") is True
        assert node.get_output_value("is_dir") is False

    @pytest.mark.asyncio
    async def test_file_exists_false(self, execution_context, tmp_path: Path) -> None:
        """SUCCESS: File does not exist."""
        non_existent = tmp_path / "missing.txt"

        node = FileSystemSuperNode(
            "test_exists",
            config={
                "action": FileSystemAction.EXISTS.value,
                "path": str(non_existent),
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.EXISTS.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("exists") is False

    @pytest.mark.asyncio
    async def test_directory_exists(self, execution_context, temp_directory: Path) -> None:
        """SUCCESS: Directory exists."""
        node = FileSystemSuperNode(
            "test_exists",
            config={
                "action": FileSystemAction.EXISTS.value,
                "path": str(temp_directory),
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.EXISTS.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("exists") is True
        assert node.get_output_value("is_file") is False
        assert node.get_output_value("is_dir") is True

    @pytest.mark.asyncio
    async def test_exists_check_type_file(self, execution_context, temp_directory: Path) -> None:
        """SUCCESS: Check type 'file' returns False for directory."""
        node = FileSystemSuperNode(
            "test_exists",
            config={
                "action": FileSystemAction.EXISTS.value,
                "path": str(temp_directory),
                "check_type": "file",
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.EXISTS.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("exists") is False  # Because it's a dir, not file


# =============================================================================
# Get File Size Action Tests
# =============================================================================


class TestGetFileSizeAction:
    """Tests for Get File Size action."""

    @pytest.mark.asyncio
    async def test_get_file_size_success(self, execution_context, temp_test_file: Path) -> None:
        """SUCCESS: Get file size."""
        node = FileSystemSuperNode(
            "test_size",
            config={
                "action": FileSystemAction.GET_SIZE.value,
                "file_path": str(temp_test_file),
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.GET_SIZE.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("size") == 13  # "Hello, World!" is 13 bytes

    @pytest.mark.asyncio
    async def test_get_file_size_not_found(self, execution_context, tmp_path: Path) -> None:
        """SAD PATH: File not found."""
        non_existent = tmp_path / "missing.txt"

        node = FileSystemSuperNode(
            "test_size",
            config={
                "action": FileSystemAction.GET_SIZE.value,
                "file_path": str(non_existent),
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.GET_SIZE.value)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "not found" in result["error"].lower()


# =============================================================================
# Get File Info Action Tests
# =============================================================================


class TestGetFileInfoAction:
    """Tests for Get File Info action."""

    @pytest.mark.asyncio
    async def test_get_file_info_success(self, execution_context, temp_test_file: Path) -> None:
        """SUCCESS: Get detailed file information."""
        node = FileSystemSuperNode(
            "test_info",
            config={
                "action": FileSystemAction.GET_INFO.value,
                "file_path": str(temp_test_file),
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.GET_INFO.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("size") == 13
        assert node.get_output_value("name") == "test_file.txt"
        assert node.get_output_value("extension") == ".txt"
        assert node.get_output_value("created") is not None
        assert node.get_output_value("modified") is not None


# =============================================================================
# Create Directory Action Tests
# =============================================================================


class TestCreateDirectoryAction:
    """Tests for Create Directory action."""

    @pytest.mark.asyncio
    async def test_create_directory_success(self, execution_context, tmp_path: Path) -> None:
        """SUCCESS: Create new directory."""
        new_dir = tmp_path / "new_directory"

        node = FileSystemSuperNode(
            "test_mkdir",
            config={
                "action": FileSystemAction.CREATE_DIR.value,
                "directory_path": str(new_dir),
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.CREATE_DIR.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    @pytest.mark.asyncio
    async def test_create_nested_directories(self, execution_context, tmp_path: Path) -> None:
        """SUCCESS: Create nested directories with parents=True."""
        nested_dir = tmp_path / "a" / "b" / "c"

        node = FileSystemSuperNode(
            "test_mkdir",
            config={
                "action": FileSystemAction.CREATE_DIR.value,
                "directory_path": str(nested_dir),
                "parents": True,
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.CREATE_DIR.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert nested_dir.exists()

    @pytest.mark.asyncio
    async def test_create_directory_exist_ok(self, execution_context, temp_directory: Path) -> None:
        """SUCCESS: No error when directory exists and exist_ok=True."""
        node = FileSystemSuperNode(
            "test_mkdir",
            config={
                "action": FileSystemAction.CREATE_DIR.value,
                "directory_path": str(temp_directory),
                "exist_ok": True,
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.CREATE_DIR.value)

        result = await node.execute(execution_context)

        assert result["success"] is True


# =============================================================================
# List Files Action Tests
# =============================================================================


class TestListFilesAction:
    """Tests for List Files action."""

    @pytest.mark.asyncio
    async def test_list_files_success(self, execution_context, temp_directory: Path) -> None:
        """SUCCESS: List files in directory."""
        node = FileSystemSuperNode(
            "test_list",
            config={
                "action": FileSystemAction.LIST_FILES.value,
                "directory_path": str(temp_directory),
                "pattern": "*",
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.LIST_FILES.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        files = node.get_output_value("files")
        assert len(files) >= 3  # file1.txt, file2.txt, data.json
        assert node.get_output_value("count") >= 3

    @pytest.mark.asyncio
    async def test_list_files_with_pattern(self, execution_context, temp_directory: Path) -> None:
        """SUCCESS: List files matching pattern."""
        node = FileSystemSuperNode(
            "test_list",
            config={
                "action": FileSystemAction.LIST_FILES.value,
                "directory_path": str(temp_directory),
                "pattern": "*.txt",
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.LIST_FILES.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        files = node.get_output_value("files")
        assert all(f.endswith(".txt") for f in files)

    @pytest.mark.asyncio
    async def test_list_files_recursive(self, execution_context, temp_directory: Path) -> None:
        """SUCCESS: List files recursively."""
        node = FileSystemSuperNode(
            "test_list",
            config={
                "action": FileSystemAction.LIST_FILES.value,
                "directory_path": str(temp_directory),
                "pattern": "*.txt",
                "recursive": True,
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.LIST_FILES.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        files = node.get_output_value("files")
        # Should include nested.txt from subdir
        assert any("nested.txt" in f for f in files)

    @pytest.mark.asyncio
    async def test_list_files_not_directory(self, execution_context, temp_test_file: Path) -> None:
        """SAD PATH: Path is a file, not directory."""
        node = FileSystemSuperNode(
            "test_list",
            config={
                "action": FileSystemAction.LIST_FILES.value,
                "directory_path": str(temp_test_file),
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.LIST_FILES.value)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "not a directory" in result["error"].lower()


# =============================================================================
# List Directory Action Tests
# =============================================================================


class TestListDirectoryAction:
    """Tests for List Directory action."""

    @pytest.mark.asyncio
    async def test_list_directory_success(self, execution_context, temp_directory: Path) -> None:
        """SUCCESS: List all items in directory."""
        node = FileSystemSuperNode(
            "test_listdir",
            config={
                "action": FileSystemAction.LIST_DIR.value,
                "dir_path": str(temp_directory),
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.LIST_DIR.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        items = node.get_output_value("items")
        assert len(items) >= 4  # 3 files + 1 subdir

    @pytest.mark.asyncio
    async def test_list_directory_files_only(self, execution_context, temp_directory: Path) -> None:
        """SUCCESS: List only files."""
        node = FileSystemSuperNode(
            "test_listdir",
            config={
                "action": FileSystemAction.LIST_DIR.value,
                "dir_path": str(temp_directory),
                "files_only": True,
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.LIST_DIR.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        items = node.get_output_value("items")
        # All items should be files
        assert all(Path(item).is_file() for item in items)

    @pytest.mark.asyncio
    async def test_list_directory_dirs_only(self, execution_context, temp_directory: Path) -> None:
        """SUCCESS: List only directories."""
        node = FileSystemSuperNode(
            "test_listdir",
            config={
                "action": FileSystemAction.LIST_DIR.value,
                "dir_path": str(temp_directory),
                "dirs_only": True,
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, FileSystemAction.LIST_DIR.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        items = node.get_output_value("items")
        # All items should be directories
        assert all(Path(item).is_dir() for item in items)


# =============================================================================
# Security Tests
# =============================================================================


class TestFileSystemSecurity:
    """Tests for path security validation."""

    @pytest.mark.asyncio
    async def test_path_traversal_blocked(self, execution_context) -> None:
        """SECURITY: Block path traversal attempts."""
        node = FileSystemSuperNode(
            "test_security",
            config={
                "action": FileSystemAction.READ.value,
                "file_path": "C:\\Users\\..\\..\\Windows\\System32\\config\\SAM",
                "allow_dangerous_paths": False,
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is False
        # Should fail due to path traversal detection

    @pytest.mark.asyncio
    async def test_null_byte_injection_blocked(self, execution_context) -> None:
        """SECURITY: Block null byte injection."""
        node = FileSystemSuperNode(
            "test_security",
            config={
                "action": FileSystemAction.READ.value,
                "file_path": "test.txt\x00.exe",
                "allow_dangerous_paths": False,
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "null byte" in result["error"].lower() or "security" in result["error"].lower()


# =============================================================================
# Port Schema Tests
# =============================================================================


class TestDynamicPortSchema:
    """Tests for dynamic port schema configuration."""

    def test_port_schema_has_all_actions(self) -> None:
        """Verify all actions have port configurations."""
        for action in FileSystemAction:
            config = FILE_SYSTEM_PORT_SCHEMA.get_config(action.value)
            assert config is not None, f"Missing port config for {action.value}"

    def test_read_action_ports(self) -> None:
        """Verify Read action port configuration."""
        config = FILE_SYSTEM_PORT_SCHEMA.get_config(FileSystemAction.READ.value)
        input_names = [p.name for p in config.inputs]
        output_names = [p.name for p in config.outputs]

        assert "file_path" in input_names
        assert "content" in output_names
        assert "size" in output_names
        assert "success" in output_names

    def test_copy_action_ports(self) -> None:
        """Verify Copy action port configuration."""
        config = FILE_SYSTEM_PORT_SCHEMA.get_config(FileSystemAction.COPY.value)
        input_names = [p.name for p in config.inputs]
        output_names = [p.name for p in config.outputs]

        assert "source_path" in input_names
        assert "dest_path" in input_names
        assert "bytes_copied" in output_names
        assert "success" in output_names
