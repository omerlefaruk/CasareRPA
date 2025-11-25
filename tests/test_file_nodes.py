"""
Tests for file system operation nodes.

Tests file reading, writing, copying, moving, deleting, and directory operations.
Uses temporary directories to avoid polluting the file system.
"""

import csv
import json
import zipfile
from pathlib import Path

import pytest

from casare_rpa.nodes.file_nodes import (
    ReadFileNode,
    WriteFileNode,
    AppendFileNode,
    DeleteFileNode,
    CopyFileNode,
    MoveFileNode,
    CreateDirectoryNode,
    ListDirectoryNode,
    FileExistsNode,
    GetFileInfoNode,
    ReadCSVNode,
    WriteCSVNode,
    ReadJSONFileNode,
    WriteJSONFileNode,
    ZipFilesNode,
    UnzipFilesNode,
)
from casare_rpa.core.types import NodeStatus


class TestReadFileNode:
    """Tests for reading files."""

    @pytest.mark.asyncio
    async def test_read_text_file(self, execution_context, temp_test_dir):
        """Test reading a text file."""
        test_file = temp_test_dir / "test.txt"

        node = ReadFileNode(node_id="read_1")
        node.set_input_value("file_path", str(test_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("content") == "Test content"
        assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_read_file_not_found(self, execution_context, temp_test_dir):
        """Test reading a non-existent file."""
        node = ReadFileNode(node_id="read_1")
        node.set_input_value("file_path", str(temp_test_dir / "nonexistent.txt"))

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_read_file_outputs_size(self, execution_context, temp_test_dir):
        """Test that file size is output correctly."""
        test_file = temp_test_dir / "test.txt"

        node = ReadFileNode(node_id="read_1")
        node.set_input_value("file_path", str(test_file))

        await node.execute(execution_context)

        assert node.get_output_value("size") > 0


class TestWriteFileNode:
    """Tests for writing files."""

    @pytest.mark.asyncio
    async def test_write_new_file(self, execution_context, temp_output_dir):
        """Test writing a new file."""
        output_file = temp_output_dir / "output.txt"

        node = WriteFileNode(node_id="write_1")
        node.set_input_value("file_path", str(output_file))
        node.set_input_value("content", "Hello World")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert output_file.exists()
        assert output_file.read_text() == "Hello World"

    @pytest.mark.asyncio
    async def test_write_creates_directories(self, execution_context, temp_output_dir):
        """Test that writing creates parent directories."""
        output_file = temp_output_dir / "subdir" / "nested" / "file.txt"

        node = WriteFileNode(node_id="write_1", config={"create_dirs": True})
        node.set_input_value("file_path", str(output_file))
        node.set_input_value("content", "Nested content")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert output_file.exists()

    @pytest.mark.asyncio
    async def test_write_overwrites_existing(self, execution_context, temp_output_dir):
        """Test that writing overwrites existing file."""
        output_file = temp_output_dir / "existing.txt"
        output_file.write_text("Old content")

        node = WriteFileNode(node_id="write_1")
        node.set_input_value("file_path", str(output_file))
        node.set_input_value("content", "New content")

        await node.execute(execution_context)

        assert output_file.read_text() == "New content"


class TestAppendFileNode:
    """Tests for appending to files."""

    @pytest.mark.asyncio
    async def test_append_to_existing(self, execution_context, temp_output_dir):
        """Test appending to an existing file."""
        output_file = temp_output_dir / "append_test.txt"
        output_file.write_text("Line 1\n")

        node = AppendFileNode(node_id="append_1")
        node.set_input_value("file_path", str(output_file))
        node.set_input_value("content", "Line 2\n")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert output_file.read_text() == "Line 1\nLine 2\n"

    @pytest.mark.asyncio
    async def test_append_creates_new_file(self, execution_context, temp_output_dir):
        """Test appending creates file if doesn't exist."""
        output_file = temp_output_dir / "new_append.txt"

        node = AppendFileNode(node_id="append_1", config={"create_if_missing": True})
        node.set_input_value("file_path", str(output_file))
        node.set_input_value("content", "First line")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert output_file.exists()


class TestDeleteFileNode:
    """Tests for deleting files."""

    @pytest.mark.asyncio
    async def test_delete_existing_file(self, execution_context, temp_output_dir):
        """Test deleting an existing file."""
        test_file = temp_output_dir / "to_delete.txt"
        test_file.write_text("Delete me")

        node = DeleteFileNode(node_id="delete_1")
        node.set_input_value("file_path", str(test_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert not test_file.exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_raises_error(self, execution_context, temp_output_dir):
        """Test deleting non-existent file raises error."""
        node = DeleteFileNode(node_id="delete_1", config={"ignore_missing": False})
        node.set_input_value("file_path", str(temp_output_dir / "nonexistent.txt"))

        result = await node.execute(execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_delete_nonexistent_ignore(self, execution_context, temp_output_dir):
        """Test deleting non-existent file with ignore_missing."""
        node = DeleteFileNode(node_id="delete_1", config={"ignore_missing": True})
        node.set_input_value("file_path", str(temp_output_dir / "nonexistent.txt"))

        result = await node.execute(execution_context)

        assert result["success"] is True


class TestCopyFileNode:
    """Tests for copying files."""

    @pytest.mark.asyncio
    async def test_copy_file(self, execution_context, temp_test_dir, temp_output_dir):
        """Test copying a file."""
        source = temp_test_dir / "test.txt"
        dest = temp_output_dir / "copy.txt"

        node = CopyFileNode(node_id="copy_1")
        node.set_input_value("source_path", str(source))
        node.set_input_value("dest_path", str(dest))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert dest.exists()
        assert source.exists()  # Original still exists
        assert dest.read_text() == source.read_text()

    @pytest.mark.asyncio
    async def test_copy_fails_if_dest_exists(self, execution_context, temp_test_dir, temp_output_dir):
        """Test copy fails if destination exists without overwrite."""
        source = temp_test_dir / "test.txt"
        dest = temp_output_dir / "existing.txt"
        dest.write_text("Existing")

        node = CopyFileNode(node_id="copy_1", config={"overwrite": False})
        node.set_input_value("source_path", str(source))
        node.set_input_value("dest_path", str(dest))

        result = await node.execute(execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_copy_with_overwrite(self, execution_context, temp_test_dir, temp_output_dir):
        """Test copy with overwrite enabled."""
        source = temp_test_dir / "test.txt"
        dest = temp_output_dir / "existing.txt"
        dest.write_text("Old content")

        node = CopyFileNode(node_id="copy_1", config={"overwrite": True})
        node.set_input_value("source_path", str(source))
        node.set_input_value("dest_path", str(dest))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert dest.read_text() == source.read_text()


class TestMoveFileNode:
    """Tests for moving/renaming files."""

    @pytest.mark.asyncio
    async def test_move_file(self, execution_context, temp_output_dir):
        """Test moving a file."""
        source = temp_output_dir / "source.txt"
        source.write_text("Move me")
        dest = temp_output_dir / "moved.txt"

        node = MoveFileNode(node_id="move_1")
        node.set_input_value("source_path", str(source))
        node.set_input_value("dest_path", str(dest))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert dest.exists()
        assert not source.exists()  # Source no longer exists

    @pytest.mark.asyncio
    async def test_rename_file(self, execution_context, temp_output_dir):
        """Test renaming a file (same directory)."""
        source = temp_output_dir / "old_name.txt"
        source.write_text("Rename me")
        dest = temp_output_dir / "new_name.txt"

        node = MoveFileNode(node_id="move_1")
        node.set_input_value("source_path", str(source))
        node.set_input_value("dest_path", str(dest))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert dest.exists()
        assert dest.name == "new_name.txt"


class TestCreateDirectoryNode:
    """Tests for creating directories."""

    @pytest.mark.asyncio
    async def test_create_directory(self, execution_context, temp_output_dir):
        """Test creating a single directory."""
        new_dir = temp_output_dir / "new_folder"

        node = CreateDirectoryNode(node_id="mkdir_1")
        node.set_input_value("dir_path", str(new_dir))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    @pytest.mark.asyncio
    async def test_create_nested_directories(self, execution_context, temp_output_dir):
        """Test creating nested directories."""
        new_dir = temp_output_dir / "level1" / "level2" / "level3"

        node = CreateDirectoryNode(node_id="mkdir_1", config={"parents": True})
        node.set_input_value("dir_path", str(new_dir))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert new_dir.exists()

    @pytest.mark.asyncio
    async def test_create_existing_directory_ok(self, execution_context, temp_output_dir):
        """Test creating existing directory with exist_ok."""
        existing_dir = temp_output_dir / "existing"
        existing_dir.mkdir()

        node = CreateDirectoryNode(node_id="mkdir_1", config={"exist_ok": True})
        node.set_input_value("dir_path", str(existing_dir))

        result = await node.execute(execution_context)

        assert result["success"] is True


class TestListDirectoryNode:
    """Tests for listing directory contents."""

    @pytest.mark.asyncio
    async def test_list_directory(self, execution_context, temp_test_dir):
        """Test listing directory contents."""
        node = ListDirectoryNode(node_id="list_1")
        node.set_input_value("dir_path", str(temp_test_dir))

        result = await node.execute(execution_context)

        assert result["success"] is True
        items = node.get_output_value("items")
        assert len(items) > 0
        assert node.get_output_value("count") > 0

    @pytest.mark.asyncio
    async def test_list_with_pattern(self, execution_context, temp_test_dir):
        """Test listing with glob pattern."""
        node = ListDirectoryNode(node_id="list_1", config={"pattern": "*.txt"})
        node.set_input_value("dir_path", str(temp_test_dir))

        result = await node.execute(execution_context)

        assert result["success"] is True
        items = node.get_output_value("items")
        for item in items:
            assert item.endswith(".txt")

    @pytest.mark.asyncio
    async def test_list_files_only(self, execution_context, temp_test_dir):
        """Test listing files only."""
        node = ListDirectoryNode(node_id="list_1", config={"files_only": True})
        node.set_input_value("dir_path", str(temp_test_dir))

        result = await node.execute(execution_context)

        assert result["success"] is True
        items = node.get_output_value("items")
        for item in items:
            assert Path(item).is_file()


class TestFileExistsNode:
    """Tests for checking file existence."""

    @pytest.mark.asyncio
    async def test_file_exists(self, execution_context, temp_test_dir):
        """Test checking existing file."""
        node = FileExistsNode(node_id="exists_1")
        node.set_input_value("path", str(temp_test_dir / "test.txt"))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("exists") is True
        assert node.get_output_value("is_file") is True

    @pytest.mark.asyncio
    async def test_directory_exists(self, execution_context, temp_test_dir):
        """Test checking existing directory."""
        node = FileExistsNode(node_id="exists_1")
        node.set_input_value("path", str(temp_test_dir / "subdir"))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("exists") is True
        assert node.get_output_value("is_directory") is True

    @pytest.mark.asyncio
    async def test_path_not_exists(self, execution_context, temp_test_dir):
        """Test checking non-existent path."""
        node = FileExistsNode(node_id="exists_1")
        node.set_input_value("path", str(temp_test_dir / "nonexistent"))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("exists") is False


class TestGetFileInfoNode:
    """Tests for getting file information."""

    @pytest.mark.asyncio
    async def test_get_file_info(self, execution_context, temp_test_dir):
        """Test getting file information."""
        test_file = temp_test_dir / "test.txt"

        node = GetFileInfoNode(node_id="info_1")
        node.set_input_value("file_path", str(test_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("name") == "test.txt"
        assert node.get_output_value("extension") == ".txt"
        assert node.get_output_value("size") > 0
        assert node.get_output_value("modified") is not None


class TestReadCSVNode:
    """Tests for reading CSV files."""

    @pytest.mark.asyncio
    async def test_read_csv_with_header(self, execution_context, temp_test_dir):
        """Test reading CSV file with headers."""
        csv_file = temp_test_dir / "numbers.csv"

        node = ReadCSVNode(node_id="csv_1", config={"has_header": True})
        node.set_input_value("file_path", str(csv_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        data = node.get_output_value("data")
        headers = node.get_output_value("headers")

        assert len(data) == 2  # Two data rows
        assert "a" in headers
        assert "b" in headers

    @pytest.mark.asyncio
    async def test_read_csv_without_header(self, execution_context, temp_output_dir):
        """Test reading CSV file without headers."""
        csv_file = temp_output_dir / "no_header.csv"
        csv_file.write_text("1,2,3\n4,5,6")

        node = ReadCSVNode(node_id="csv_1", config={"has_header": False})
        node.set_input_value("file_path", str(csv_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        data = node.get_output_value("data")
        assert len(data) == 2
        assert data[0] == ["1", "2", "3"]


class TestWriteCSVNode:
    """Tests for writing CSV files."""

    @pytest.mark.asyncio
    async def test_write_csv_dict_data(self, execution_context, temp_output_dir):
        """Test writing CSV with dictionary data."""
        csv_file = temp_output_dir / "output.csv"
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]

        node = WriteCSVNode(node_id="csv_1")
        node.set_input_value("file_path", str(csv_file))
        node.set_input_value("data", data)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert csv_file.exists()

        # Verify content
        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 2

    @pytest.mark.asyncio
    async def test_write_csv_list_data(self, execution_context, temp_output_dir):
        """Test writing CSV with list data."""
        csv_file = temp_output_dir / "list_output.csv"
        data = [
            [1, 2, 3],
            [4, 5, 6]
        ]

        node = WriteCSVNode(node_id="csv_1")
        node.set_input_value("file_path", str(csv_file))
        node.set_input_value("data", data)
        node.set_input_value("headers", ["a", "b", "c"])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("row_count") == 2


class TestReadJSONFileNode:
    """Tests for reading JSON files."""

    @pytest.mark.asyncio
    async def test_read_json_file(self, execution_context, temp_test_dir):
        """Test reading JSON file."""
        json_file = temp_test_dir / "data.json"

        node = ReadJSONFileNode(node_id="json_1")
        node.set_input_value("file_path", str(json_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        data = node.get_output_value("data")
        assert data == {"key": "value"}

    @pytest.mark.asyncio
    async def test_read_invalid_json(self, execution_context, temp_output_dir):
        """Test reading invalid JSON file."""
        json_file = temp_output_dir / "invalid.json"
        json_file.write_text("not valid json {")

        node = ReadJSONFileNode(node_id="json_1")
        node.set_input_value("file_path", str(json_file))

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "invalid json" in result["error"].lower()


class TestWriteJSONFileNode:
    """Tests for writing JSON files."""

    @pytest.mark.asyncio
    async def test_write_json_file(self, execution_context, temp_output_dir):
        """Test writing JSON file."""
        json_file = temp_output_dir / "output.json"
        data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}

        node = WriteJSONFileNode(node_id="json_1")
        node.set_input_value("file_path", str(json_file))
        node.set_input_value("data", data)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert json_file.exists()

        # Verify content
        with open(json_file, "r") as f:
            loaded = json.load(f)
        assert loaded == data


class TestZipFilesNode:
    """Tests for creating ZIP archives."""

    @pytest.mark.asyncio
    async def test_zip_files(self, execution_context, temp_test_dir, temp_output_dir):
        """Test creating a ZIP archive."""
        zip_file = temp_output_dir / "archive.zip"
        files = [str(temp_test_dir / "test.txt")]

        node = ZipFilesNode(node_id="zip_1")
        node.set_input_value("zip_path", str(zip_file))
        node.set_input_value("files", files)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert zip_file.exists()
        assert node.get_output_value("file_count") == 1

        # Verify ZIP content
        with zipfile.ZipFile(zip_file, "r") as zf:
            assert len(zf.namelist()) == 1


class TestUnzipFilesNode:
    """Tests for extracting ZIP archives."""

    @pytest.mark.asyncio
    async def test_unzip_files(self, execution_context, temp_test_dir, temp_output_dir):
        """Test extracting a ZIP archive."""
        # Create ZIP first
        zip_file = temp_output_dir / "test.zip"
        with zipfile.ZipFile(zip_file, "w") as zf:
            zf.write(temp_test_dir / "test.txt", "test.txt")

        extract_dir = temp_output_dir / "extracted"

        node = UnzipFilesNode(node_id="unzip_1")
        node.set_input_value("zip_path", str(zip_file))
        node.set_input_value("extract_to", str(extract_dir))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert (extract_dir / "test.txt").exists()


class TestFileOperationScenarios:
    """Integration tests for file operation workflows."""

    @pytest.mark.asyncio
    async def test_read_modify_write_workflow(self, execution_context, temp_test_dir, temp_output_dir):
        """Test reading, modifying, and writing a file."""
        # Read original
        read_node = ReadFileNode(node_id="read_1")
        read_node.set_input_value("file_path", str(temp_test_dir / "test.txt"))
        await read_node.execute(execution_context)

        content = read_node.get_output_value("content")

        # Modify content
        modified = content.upper()

        # Write modified
        write_node = WriteFileNode(node_id="write_1")
        write_node.set_input_value("file_path", str(temp_output_dir / "modified.txt"))
        write_node.set_input_value("content", modified)
        await write_node.execute(execution_context)

        # Verify
        result = (temp_output_dir / "modified.txt").read_text()
        assert result == "TEST CONTENT"

    @pytest.mark.asyncio
    async def test_backup_file_workflow(self, execution_context, temp_output_dir):
        """Test creating a backup before modifying a file."""
        original = temp_output_dir / "important.txt"
        original.write_text("Important data")
        backup = temp_output_dir / "important.txt.bak"

        # Copy to backup
        copy_node = CopyFileNode(node_id="copy_1")
        copy_node.set_input_value("source_path", str(original))
        copy_node.set_input_value("dest_path", str(backup))
        await copy_node.execute(execution_context)

        # Modify original
        write_node = WriteFileNode(node_id="write_1")
        write_node.set_input_value("file_path", str(original))
        write_node.set_input_value("content", "New data")
        await write_node.execute(execution_context)

        # Verify both exist
        assert original.read_text() == "New data"
        assert backup.read_text() == "Important data"

    @pytest.mark.asyncio
    async def test_process_csv_and_save_json(self, execution_context, temp_test_dir, temp_output_dir):
        """Test reading CSV and saving as JSON."""
        # Read CSV
        read_csv = ReadCSVNode(node_id="csv_1", config={"has_header": True})
        read_csv.set_input_value("file_path", str(temp_test_dir / "numbers.csv"))
        await read_csv.execute(execution_context)

        data = read_csv.get_output_value("data")

        # Convert to JSON structure
        json_data = {"rows": data, "count": len(data)}

        # Write JSON
        write_json = WriteJSONFileNode(node_id="json_1")
        write_json.set_input_value("file_path", str(temp_output_dir / "data.json"))
        write_json.set_input_value("data", json_data)
        await write_json.execute(execution_context)

        # Verify
        with open(temp_output_dir / "data.json", "r") as f:
            loaded = json.load(f)
        assert loaded["count"] == 2

    @pytest.mark.asyncio
    async def test_conditional_file_creation(self, execution_context, temp_output_dir):
        """Test creating file only if it doesn't exist."""
        output_file = temp_output_dir / "conditional.txt"

        # Check if exists
        exists_node = FileExistsNode(node_id="exists_1")
        exists_node.set_input_value("path", str(output_file))
        await exists_node.execute(execution_context)

        if not exists_node.get_output_value("exists"):
            # Create file
            write_node = WriteFileNode(node_id="write_1")
            write_node.set_input_value("file_path", str(output_file))
            write_node.set_input_value("content", "Created because it didn't exist")
            await write_node.execute(execution_context)

        assert output_file.exists()
