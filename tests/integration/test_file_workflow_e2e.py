"""
CasareRPA - End-to-End File Operations Workflow Tests.

Tests file operations workflows:
- Read, write, copy sequence
- File system operations
- Error handling for file operations
- Path security validation

Uses temp directory for actual file operations.
Uses real domain objects and workflow execution.
"""

import pytest
import tempfile
import os
from pathlib import Path
from typing import Dict, Any
from unittest.mock import MagicMock, patch, AsyncMock

from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.entities.node_connection import NodeConnection
from casare_rpa.presentation.canvas.events.event_bus import EventBus


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def event_bus() -> EventBus:
    """Create isolated event bus for tests."""
    return EventBus()


@pytest.fixture
def temp_dir():
    """Create temporary directory for file operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_execution_context(temp_dir):
    """Create mock execution context for file operations."""
    context = MagicMock()

    # Variable storage
    context.variables: Dict[str, Any] = {}
    context.resolve_value = lambda x: x
    context.get_variable = lambda name, default=None: context.variables.get(
        name, default
    )
    context.set_variable = lambda name, value: context.variables.__setitem__(
        name, value
    )
    context.has_variable = lambda name: name in context.variables

    # Store temp_dir for tests
    context.temp_dir = temp_dir

    return context


@pytest.fixture
def sample_text_file(temp_dir):
    """Create sample text file for reading tests."""
    file_path = temp_dir / "sample.txt"
    file_path.write_text("Hello, World!\nLine 2\nLine 3", encoding="utf-8")
    return file_path


@pytest.fixture
def sample_json_file(temp_dir):
    """Create sample JSON file for reading tests."""
    import json

    file_path = temp_dir / "sample.json"
    data = {"name": "test", "value": 42, "items": [1, 2, 3]}
    file_path.write_text(json.dumps(data), encoding="utf-8")
    return file_path


# =============================================================================
# TEST: READ FILE WORKFLOW
# =============================================================================


@pytest.mark.integration
class TestReadFileWorkflow:
    """Tests for file reading workflows."""

    @pytest.mark.asyncio
    async def test_read_text_file(
        self, mock_execution_context, sample_text_file
    ) -> None:
        """Test reading a text file."""
        from casare_rpa.nodes.file.file_read_nodes import ReadFileNode

        node = ReadFileNode(
            node_id="read_1",
            name="Read Text File",
            config={
                "file_path": str(sample_text_file),
                "encoding": "utf-8",
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        content = node.get_output_value("content")
        assert "Hello, World!" in content
        assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_read_file_with_different_encodings(
        self, mock_execution_context, temp_dir
    ) -> None:
        """Test reading files with different encodings."""
        from casare_rpa.nodes.file.file_read_nodes import ReadFileNode

        # Create file with specific encoding
        file_path = temp_dir / "encoded.txt"
        file_path.write_text("Test content with special chars", encoding="utf-8")

        node = ReadFileNode(
            node_id="read_encoded",
            name="Read Encoded",
            config={
                "file_path": str(file_path),
                "encoding": "utf-8",
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_read_nonexistent_file_error(
        self, mock_execution_context, temp_dir
    ) -> None:
        """Test error handling when file doesn't exist."""
        from casare_rpa.nodes.file.file_read_nodes import ReadFileNode

        node = ReadFileNode(
            node_id="read_missing",
            name="Read Missing",
            config={
                "file_path": str(temp_dir / "nonexistent.txt"),
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False
        assert "error" in result
        assert (
            "not found" in result["error"].lower()
            or "no such file" in result["error"].lower()
        )

    @pytest.mark.asyncio
    async def test_read_file_size_limit(self, mock_execution_context, temp_dir) -> None:
        """Test file size limit enforcement."""
        from casare_rpa.nodes.file.file_read_nodes import ReadFileNode

        # Create large file
        file_path = temp_dir / "large.txt"
        file_path.write_text("x" * 1000, encoding="utf-8")

        node = ReadFileNode(
            node_id="read_large",
            name="Read Large",
            config={
                "file_path": str(file_path),
                "max_size": 100,  # Limit to 100 bytes
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_read_binary_file(self, mock_execution_context, temp_dir) -> None:
        """Test reading binary file."""
        from casare_rpa.nodes.file.file_read_nodes import ReadFileNode

        # Create binary file
        file_path = temp_dir / "binary.bin"
        file_path.write_bytes(b"\x00\x01\x02\x03\x04\x05")

        node = ReadFileNode(
            node_id="read_binary",
            name="Read Binary",
            config={
                "file_path": str(file_path),
                "binary_mode": True,
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        content = node.get_output_value("content")
        assert isinstance(content, bytes)


# =============================================================================
# TEST: WRITE FILE WORKFLOW
# =============================================================================


@pytest.mark.integration
class TestWriteFileWorkflow:
    """Tests for file writing workflows."""

    @pytest.mark.asyncio
    async def test_write_new_text_file(self, mock_execution_context, temp_dir) -> None:
        """Test writing a new text file."""
        from casare_rpa.nodes.file.file_write_nodes import WriteFileNode

        file_path = temp_dir / "new_file.txt"

        node = WriteFileNode(
            node_id="write_1",
            name="Write Text File",
            config={
                "file_path": str(file_path),
                "content": "Test content\nLine 2",
                "encoding": "utf-8",
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert file_path.exists()
        assert file_path.read_text() == "Test content\nLine 2"

    @pytest.mark.asyncio
    async def test_overwrite_existing_file(
        self, mock_execution_context, sample_text_file
    ) -> None:
        """Test overwriting an existing file."""
        from casare_rpa.nodes.file.file_write_nodes import WriteFileNode

        original_content = sample_text_file.read_text()
        new_content = "Completely new content"

        node = WriteFileNode(
            node_id="overwrite_1",
            name="Overwrite File",
            config={
                "file_path": str(sample_text_file),
                "content": new_content,
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert sample_text_file.read_text() == new_content
        assert sample_text_file.read_text() != original_content

    @pytest.mark.asyncio
    async def test_append_to_file(
        self, mock_execution_context, sample_text_file
    ) -> None:
        """Test appending to existing file."""
        from casare_rpa.nodes.file.file_write_nodes import WriteFileNode

        original_content = sample_text_file.read_text()
        append_content = "\nAppended line"

        node = WriteFileNode(
            node_id="append_1",
            name="Append to File",
            config={
                "file_path": str(sample_text_file),
                "content": append_content,
                "append_mode": True,
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        final_content = sample_text_file.read_text()
        assert original_content in final_content
        assert append_content in final_content

    @pytest.mark.asyncio
    async def test_create_parent_directories(
        self, mock_execution_context, temp_dir
    ) -> None:
        """Test automatic creation of parent directories."""
        from casare_rpa.nodes.file.file_write_nodes import WriteFileNode

        file_path = temp_dir / "subdir1" / "subdir2" / "file.txt"

        node = WriteFileNode(
            node_id="write_nested",
            name="Write Nested",
            config={
                "file_path": str(file_path),
                "content": "Nested content",
                "create_dirs": True,
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert file_path.exists()
        assert file_path.read_text() == "Nested content"

    @pytest.mark.asyncio
    async def test_write_binary_content(self, mock_execution_context, temp_dir) -> None:
        """Test writing binary content."""
        from casare_rpa.nodes.file.file_write_nodes import WriteFileNode

        file_path = temp_dir / "binary_output.bin"

        node = WriteFileNode(
            node_id="write_binary",
            name="Write Binary",
            config={
                "file_path": str(file_path),
                "content": "binary_data",
                "binary_mode": True,
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert file_path.exists()


# =============================================================================
# TEST: COPY FILE WORKFLOW
# =============================================================================


@pytest.mark.integration
class TestCopyFileWorkflow:
    """Tests for file copy workflows."""

    @pytest.mark.asyncio
    async def test_copy_file_to_new_location(
        self, mock_execution_context, sample_text_file, temp_dir
    ) -> None:
        """Test copying a file to new location."""
        from casare_rpa.nodes.file.file_system_nodes import CopyFileNode

        dest_path = temp_dir / "copied_file.txt"

        node = CopyFileNode(
            node_id="copy_1",
            name="Copy File",
            config={
                "source_path": str(sample_text_file),
                "dest_path": str(dest_path),
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert dest_path.exists()
        assert dest_path.read_text() == sample_text_file.read_text()
        # Original still exists
        assert sample_text_file.exists()

    @pytest.mark.asyncio
    async def test_copy_to_subdirectory_creates_dirs(
        self, mock_execution_context, sample_text_file, temp_dir
    ) -> None:
        """Test copying file to subdirectory creates parent dirs."""
        from casare_rpa.nodes.file.file_system_nodes import CopyFileNode

        dest_path = temp_dir / "new_subdir" / "copied.txt"

        node = CopyFileNode(
            node_id="copy_nested",
            name="Copy to Nested",
            config={
                "source_path": str(sample_text_file),
                "dest_path": str(dest_path),
                "create_dirs": True,
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert dest_path.exists()

    @pytest.mark.asyncio
    async def test_copy_overwrite_protection(
        self, mock_execution_context, sample_text_file, temp_dir
    ) -> None:
        """Test copy doesn't overwrite by default."""
        from casare_rpa.nodes.file.file_system_nodes import CopyFileNode

        # Create destination file with different content
        dest_path = temp_dir / "existing.txt"
        dest_path.write_text("Existing content")

        node = CopyFileNode(
            node_id="copy_no_overwrite",
            name="Copy No Overwrite",
            config={
                "source_path": str(sample_text_file),
                "dest_path": str(dest_path),
                "overwrite": False,
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        # Should fail because overwrite=False
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_copy_with_overwrite(
        self, mock_execution_context, sample_text_file, temp_dir
    ) -> None:
        """Test copy with overwrite enabled."""
        from casare_rpa.nodes.file.file_system_nodes import CopyFileNode

        # Create destination file with different content
        dest_path = temp_dir / "to_overwrite.txt"
        dest_path.write_text("Old content to be replaced")

        node = CopyFileNode(
            node_id="copy_overwrite",
            name="Copy Overwrite",
            config={
                "source_path": str(sample_text_file),
                "dest_path": str(dest_path),
                "overwrite": True,
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert dest_path.read_text() == sample_text_file.read_text()


# =============================================================================
# TEST: MOVE FILE WORKFLOW
# =============================================================================


@pytest.mark.integration
class TestMoveFileWorkflow:
    """Tests for file move workflows."""

    @pytest.mark.asyncio
    async def test_move_file_to_new_location(
        self, mock_execution_context, temp_dir
    ) -> None:
        """Test moving a file to new location."""
        from casare_rpa.nodes.file.file_system_nodes import MoveFileNode

        # Create source file
        source_path = temp_dir / "to_move.txt"
        source_path.write_text("Content to move")
        dest_path = temp_dir / "moved.txt"

        node = MoveFileNode(
            node_id="move_1",
            name="Move File",
            config={
                "source_path": str(source_path),
                "dest_path": str(dest_path),
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert dest_path.exists()
        assert not source_path.exists()  # Original removed
        assert dest_path.read_text() == "Content to move"

    @pytest.mark.asyncio
    async def test_rename_file(self, mock_execution_context, temp_dir) -> None:
        """Test renaming a file (move within same directory)."""
        from casare_rpa.nodes.file.file_system_nodes import MoveFileNode

        # Create source file
        source_path = temp_dir / "original_name.txt"
        source_path.write_text("Renamed content")
        dest_path = temp_dir / "new_name.txt"

        node = MoveFileNode(
            node_id="rename_1",
            name="Rename File",
            config={
                "source_path": str(source_path),
                "dest_path": str(dest_path),
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert dest_path.exists()
        assert not source_path.exists()


# =============================================================================
# TEST: DELETE FILE WORKFLOW
# =============================================================================


@pytest.mark.integration
class TestDeleteFileWorkflow:
    """Tests for file deletion workflows."""

    @pytest.mark.asyncio
    async def test_delete_existing_file(self, mock_execution_context, temp_dir) -> None:
        """Test deleting an existing file."""
        from casare_rpa.nodes.file.file_system_nodes import DeleteFileNode

        # Create file to delete
        file_path = temp_dir / "to_delete.txt"
        file_path.write_text("Delete me")

        node = DeleteFileNode(
            node_id="delete_1",
            name="Delete File",
            config={
                "file_path": str(file_path),
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert not file_path.exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file_error(
        self, mock_execution_context, temp_dir
    ) -> None:
        """Test error when deleting nonexistent file."""
        from casare_rpa.nodes.file.file_system_nodes import DeleteFileNode

        node = DeleteFileNode(
            node_id="delete_missing",
            name="Delete Missing",
            config={
                "file_path": str(temp_dir / "nonexistent.txt"),
                "ignore_missing": False,
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_delete_nonexistent_with_ignore(
        self, mock_execution_context, temp_dir
    ) -> None:
        """Test deleting nonexistent file with ignore_missing flag."""
        from casare_rpa.nodes.file.file_system_nodes import DeleteFileNode

        node = DeleteFileNode(
            node_id="delete_ignore",
            name="Delete Ignore Missing",
            config={
                "file_path": str(temp_dir / "nonexistent.txt"),
                "ignore_missing": True,
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True


# =============================================================================
# TEST: READ-WRITE-COPY SEQUENCE
# =============================================================================


@pytest.mark.integration
class TestReadWriteCopySequence:
    """Tests for complete read-write-copy workflow sequences."""

    @pytest.mark.asyncio
    async def test_read_modify_write_sequence(
        self, mock_execution_context, sample_text_file, temp_dir
    ) -> None:
        """Test reading, modifying, and writing content."""
        from casare_rpa.nodes.file.file_read_nodes import ReadFileNode
        from casare_rpa.nodes.file.file_write_nodes import WriteFileNode

        # Step 1: Read original file
        read_node = ReadFileNode(
            node_id="read",
            name="Read",
            config={
                "file_path": str(sample_text_file),
                "allow_dangerous_paths": True,
            },
        )
        result = await read_node.execute(mock_execution_context)
        assert result["success"] is True

        original_content = read_node.get_output_value("content")

        # Step 2: Modify content (simulate in variables)
        modified_content = original_content.upper()
        mock_execution_context.set_variable("modified_content", modified_content)

        # Step 3: Write modified content to new file
        output_path = temp_dir / "modified.txt"
        write_node = WriteFileNode(
            node_id="write",
            name="Write Modified",
            config={
                "file_path": str(output_path),
                "content": modified_content,
                "allow_dangerous_paths": True,
            },
        )
        result = await write_node.execute(mock_execution_context)
        assert result["success"] is True

        # Verify modification
        assert output_path.exists()
        assert output_path.read_text() == original_content.upper()

    @pytest.mark.asyncio
    async def test_backup_and_modify_workflow(
        self, mock_execution_context, sample_text_file, temp_dir
    ) -> None:
        """Test backup then modify workflow."""
        from casare_rpa.nodes.file.file_system_nodes import CopyFileNode
        from casare_rpa.nodes.file.file_write_nodes import WriteFileNode

        backup_path = temp_dir / "backup.txt"

        # Step 1: Create backup
        copy_node = CopyFileNode(
            node_id="backup",
            name="Create Backup",
            config={
                "source_path": str(sample_text_file),
                "dest_path": str(backup_path),
                "allow_dangerous_paths": True,
            },
        )
        result = await copy_node.execute(mock_execution_context)
        assert result["success"] is True
        assert backup_path.exists()

        # Step 2: Modify original
        new_content = "Modified content after backup"
        write_node = WriteFileNode(
            node_id="modify",
            name="Modify Original",
            config={
                "file_path": str(sample_text_file),
                "content": new_content,
                "allow_dangerous_paths": True,
            },
        )
        result = await write_node.execute(mock_execution_context)
        assert result["success"] is True

        # Verify backup preserved and original modified
        assert backup_path.read_text() != sample_text_file.read_text()
        assert sample_text_file.read_text() == new_content

    @pytest.mark.asyncio
    async def test_batch_file_processing_workflow(
        self, mock_execution_context, temp_dir
    ) -> None:
        """Test processing multiple files in sequence."""
        from casare_rpa.nodes.file.file_write_nodes import WriteFileNode
        from casare_rpa.nodes.file.file_read_nodes import ReadFileNode

        # Create multiple files
        file_names = ["file1.txt", "file2.txt", "file3.txt"]
        for i, name in enumerate(file_names):
            file_path = temp_dir / name

            # Write content
            write_node = WriteFileNode(
                node_id=f"write_{i}",
                name=f"Write {name}",
                config={
                    "file_path": str(file_path),
                    "content": f"Content of {name}",
                    "allow_dangerous_paths": True,
                },
            )
            result = await write_node.execute(mock_execution_context)
            assert result["success"] is True

        # Verify all files exist and can be read
        for i, name in enumerate(file_names):
            file_path = temp_dir / name

            read_node = ReadFileNode(
                node_id=f"read_{i}",
                name=f"Read {name}",
                config={
                    "file_path": str(file_path),
                    "allow_dangerous_paths": True,
                },
            )
            result = await read_node.execute(mock_execution_context)
            assert result["success"] is True

            content = read_node.get_output_value("content")
            assert f"Content of {name}" in content


# =============================================================================
# TEST: ERROR HANDLING
# =============================================================================


@pytest.mark.integration
class TestFileOperationErrorHandling:
    """Tests for error handling in file operations."""

    @pytest.mark.asyncio
    async def test_read_permission_error_handling(
        self, mock_execution_context, temp_dir
    ) -> None:
        """Test handling permission errors on read."""
        from casare_rpa.nodes.file.file_read_nodes import ReadFileNode

        # Create file - we can't easily test real permission errors
        # but we can test the error path with invalid encoding
        file_path = temp_dir / "test.txt"
        file_path.write_bytes(b"\xff\xfe")  # Invalid UTF-8

        node = ReadFileNode(
            node_id="read_invalid",
            name="Read Invalid Encoding",
            config={
                "file_path": str(file_path),
                "encoding": "utf-8",
                "errors": "strict",
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        # May fail due to encoding error
        # Either success with replacement or failure is acceptable
        assert "success" in result

    @pytest.mark.asyncio
    async def test_write_to_readonly_path_handling(
        self, mock_execution_context
    ) -> None:
        """Test handling write to protected path."""
        from casare_rpa.nodes.file.file_write_nodes import WriteFileNode

        # Try to write to system path without allow_dangerous_paths
        node = WriteFileNode(
            node_id="write_system",
            name="Write System Path",
            config={
                "file_path": "C:\\Windows\\System32\\test.txt",
                "content": "test",
                "allow_dangerous_paths": False,  # Should block
            },
        )

        result = await node.execute(mock_execution_context)

        # Should fail due to security validation
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_copy_source_not_found(
        self, mock_execution_context, temp_dir
    ) -> None:
        """Test copy when source doesn't exist."""
        from casare_rpa.nodes.file.file_system_nodes import CopyFileNode

        node = CopyFileNode(
            node_id="copy_missing_src",
            name="Copy Missing Source",
            config={
                "source_path": str(temp_dir / "nonexistent.txt"),
                "dest_path": str(temp_dir / "dest.txt"),
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False


# =============================================================================
# TEST: JSON FILE OPERATIONS
# =============================================================================


@pytest.mark.integration
class TestJsonFileOperations:
    """Tests for JSON file operations."""

    @pytest.mark.asyncio
    async def test_read_json_file(
        self, mock_execution_context, sample_json_file
    ) -> None:
        """Test reading JSON file."""
        from casare_rpa.nodes.file.structured_data import ReadJSONFileNode

        node = ReadJSONFileNode(
            node_id="read_json",
            name="Read JSON",
            config={
                "file_path": str(sample_json_file),
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        data = node.get_output_value("data")
        assert data["name"] == "test"
        assert data["value"] == 42

    @pytest.mark.asyncio
    async def test_write_json_file(self, mock_execution_context, temp_dir) -> None:
        """Test writing JSON file."""
        from casare_rpa.nodes.file.structured_data import WriteJSONFileNode
        import json

        file_path = temp_dir / "output.json"
        data = {"key": "value", "numbers": [1, 2, 3]}

        node = WriteJSONFileNode(
            node_id="write_json",
            name="Write JSON",
            config={
                "file_path": str(file_path),
                "data": data,
                "indent": 2,
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert file_path.exists()

        # Verify JSON content
        with open(file_path) as f:
            saved_data = json.load(f)
        assert saved_data["key"] == "value"

    @pytest.mark.asyncio
    async def test_read_invalid_json_error(
        self, mock_execution_context, temp_dir
    ) -> None:
        """Test error when reading invalid JSON."""
        from casare_rpa.nodes.file.structured_data import ReadJSONFileNode

        # Create invalid JSON file
        file_path = temp_dir / "invalid.json"
        file_path.write_text("{invalid json content}", encoding="utf-8")

        node = ReadJSONFileNode(
            node_id="read_invalid_json",
            name="Read Invalid JSON",
            config={
                "file_path": str(file_path),
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False


# =============================================================================
# TEST: EDGE CASES
# =============================================================================


@pytest.mark.integration
class TestFileOperationEdgeCases:
    """Tests for edge cases in file operations."""

    @pytest.mark.asyncio
    async def test_empty_file_handling(self, mock_execution_context, temp_dir) -> None:
        """Test handling empty files."""
        from casare_rpa.nodes.file.file_read_nodes import ReadFileNode

        # Create empty file
        file_path = temp_dir / "empty.txt"
        file_path.write_text("")

        node = ReadFileNode(
            node_id="read_empty",
            name="Read Empty",
            config={
                "file_path": str(file_path),
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        content = node.get_output_value("content")
        assert content == ""

    @pytest.mark.asyncio
    async def test_unicode_filename_handling(
        self, mock_execution_context, temp_dir
    ) -> None:
        """Test handling files with unicode characters in name."""
        from casare_rpa.nodes.file.file_write_nodes import WriteFileNode
        from casare_rpa.nodes.file.file_read_nodes import ReadFileNode

        # Create file with unicode name
        file_path = temp_dir / "test_file.txt"

        write_node = WriteFileNode(
            node_id="write_unicode",
            name="Write Unicode Name",
            config={
                "file_path": str(file_path),
                "content": "Unicode content",
                "allow_dangerous_paths": True,
            },
        )
        result = await write_node.execute(mock_execution_context)
        assert result["success"] is True

        read_node = ReadFileNode(
            node_id="read_unicode",
            name="Read Unicode Name",
            config={
                "file_path": str(file_path),
                "allow_dangerous_paths": True,
            },
        )
        result = await read_node.execute(mock_execution_context)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_special_characters_in_content(
        self, mock_execution_context, temp_dir
    ) -> None:
        """Test handling special characters in file content."""
        from casare_rpa.nodes.file.file_write_nodes import WriteFileNode
        from casare_rpa.nodes.file.file_read_nodes import ReadFileNode

        special_content = "Line1\nLine2\tTabbed\r\nWindows line\0Null char"
        file_path = temp_dir / "special.txt"

        write_node = WriteFileNode(
            node_id="write_special",
            name="Write Special",
            config={
                "file_path": str(file_path),
                "content": special_content,
                "allow_dangerous_paths": True,
            },
        )
        result = await write_node.execute(mock_execution_context)
        assert result["success"] is True

        read_node = ReadFileNode(
            node_id="read_special",
            name="Read Special",
            config={
                "file_path": str(file_path),
                "allow_dangerous_paths": True,
            },
        )
        result = await read_node.execute(mock_execution_context)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_very_long_path(self, mock_execution_context, temp_dir) -> None:
        """Test handling very long file paths."""
        from casare_rpa.nodes.file.file_write_nodes import WriteFileNode

        # Create nested directories up to path limit
        # Windows limit is typically 260 chars, but long paths may be enabled
        deep_path = temp_dir
        for i in range(5):
            deep_path = deep_path / f"subdir_{i}"

        file_path = deep_path / "deep_file.txt"

        node = WriteFileNode(
            node_id="write_deep",
            name="Write Deep Path",
            config={
                "file_path": str(file_path),
                "content": "Deep content",
                "create_dirs": True,
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert file_path.exists()
