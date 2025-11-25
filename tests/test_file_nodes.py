"""
Unit tests for File System nodes.

Tests all 16 file operation nodes:
- ReadFileNode, WriteFileNode, AppendFileNode, DeleteFileNode
- CopyFileNode, MoveFileNode, CreateDirectoryNode, ListDirectoryNode
- FileExistsNode, GetFileInfoNode
- ReadCSVNode, WriteCSVNode, ReadJSONFileNode, WriteJSONFileNode
- ZipFilesNode, UnzipFilesNode
"""

import asyncio
import csv
import json
import os
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.casare_rpa.nodes.file_nodes import (
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


@pytest.fixture
def mock_context():
    """Create a mock execution context."""
    context = MagicMock()
    context.variables = {}
    return context


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestReadFileNode:
    """Tests for ReadFileNode."""

    def test_init(self):
        """Test node initialization."""
        node = ReadFileNode("read_1")
        assert node.node_id == "read_1"
        assert node.node_type == "ReadFileNode"

    def test_read_text_file(self, mock_context, temp_dir):
        """Test reading a text file."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!", encoding="utf-8")

        node = ReadFileNode("read_1")
        node.set_input_value("file_path", str(test_file))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert node.get_output_value("content") == "Hello, World!"
        assert node.get_output_value("size") == 13
        assert node.get_output_value("success") is True

    def test_read_binary_file(self, mock_context, temp_dir):
        """Test reading a binary file."""
        test_file = temp_dir / "test.bin"
        test_file.write_bytes(b"\x00\x01\x02\x03")

        node = ReadFileNode("read_1", config={"binary_mode": True})
        node.set_input_value("file_path", str(test_file))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert node.get_output_value("content") == b"\x00\x01\x02\x03"

    def test_read_nonexistent_file(self, mock_context, temp_dir):
        """Test reading a nonexistent file."""
        node = ReadFileNode("read_1")
        node.set_input_value("file_path", str(temp_dir / "nonexistent.txt"))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestWriteFileNode:
    """Tests for WriteFileNode."""

    def test_init(self):
        """Test node initialization."""
        node = WriteFileNode("write_1")
        assert node.node_id == "write_1"
        assert node.node_type == "WriteFileNode"

    def test_write_text_file(self, mock_context, temp_dir):
        """Test writing a text file."""
        test_file = temp_dir / "output.txt"

        node = WriteFileNode("write_1")
        node.set_input_value("file_path", str(test_file))
        node.set_input_value("content", "Test content")

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert test_file.exists()
        assert test_file.read_text() == "Test content"
        assert node.get_output_value("bytes_written") == 12

    def test_write_creates_directories(self, mock_context, temp_dir):
        """Test that writing creates parent directories."""
        test_file = temp_dir / "subdir" / "nested" / "output.txt"

        node = WriteFileNode("write_1", config={"create_dirs": True})
        node.set_input_value("file_path", str(test_file))
        node.set_input_value("content", "Nested content")

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert test_file.exists()

    def test_write_overwrites_existing(self, mock_context, temp_dir):
        """Test that writing overwrites existing file."""
        test_file = temp_dir / "existing.txt"
        test_file.write_text("Original content")

        node = WriteFileNode("write_1")
        node.set_input_value("file_path", str(test_file))
        node.set_input_value("content", "New content")

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert test_file.read_text() == "New content"


class TestAppendFileNode:
    """Tests for AppendFileNode."""

    def test_append_to_existing(self, mock_context, temp_dir):
        """Test appending to an existing file."""
        test_file = temp_dir / "append.txt"
        test_file.write_text("Line 1\n")

        node = AppendFileNode("append_1")
        node.set_input_value("file_path", str(test_file))
        node.set_input_value("content", "Line 2\n")

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert test_file.read_text() == "Line 1\nLine 2\n"

    def test_append_creates_file(self, mock_context, temp_dir):
        """Test appending creates file if missing."""
        test_file = temp_dir / "new_append.txt"

        node = AppendFileNode("append_1", config={"create_if_missing": True})
        node.set_input_value("file_path", str(test_file))
        node.set_input_value("content", "First line\n")

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert test_file.exists()
        assert test_file.read_text() == "First line\n"


class TestDeleteFileNode:
    """Tests for DeleteFileNode."""

    def test_delete_existing_file(self, mock_context, temp_dir):
        """Test deleting an existing file."""
        test_file = temp_dir / "to_delete.txt"
        test_file.write_text("Delete me")

        node = DeleteFileNode("delete_1")
        node.set_input_value("file_path", str(test_file))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert not test_file.exists()

    def test_delete_nonexistent_file_error(self, mock_context, temp_dir):
        """Test deleting a nonexistent file raises error."""
        node = DeleteFileNode("delete_1", config={"ignore_missing": False})
        node.set_input_value("file_path", str(temp_dir / "nonexistent.txt"))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is False

    def test_delete_nonexistent_file_ignore(self, mock_context, temp_dir):
        """Test deleting a nonexistent file with ignore_missing."""
        node = DeleteFileNode("delete_1", config={"ignore_missing": True})
        node.set_input_value("file_path", str(temp_dir / "nonexistent.txt"))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True


class TestCopyFileNode:
    """Tests for CopyFileNode."""

    def test_copy_file(self, mock_context, temp_dir):
        """Test copying a file."""
        source = temp_dir / "source.txt"
        source.write_text("Source content")
        dest = temp_dir / "dest.txt"

        node = CopyFileNode("copy_1")
        node.set_input_value("source_path", str(source))
        node.set_input_value("dest_path", str(dest))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert dest.exists()
        assert dest.read_text() == "Source content"
        assert source.exists()  # Original still exists

    def test_copy_file_no_overwrite(self, mock_context, temp_dir):
        """Test copy fails if dest exists without overwrite."""
        source = temp_dir / "source.txt"
        source.write_text("Source")
        dest = temp_dir / "dest.txt"
        dest.write_text("Existing")

        node = CopyFileNode("copy_1", config={"overwrite": False})
        node.set_input_value("source_path", str(source))
        node.set_input_value("dest_path", str(dest))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is False

    def test_copy_file_with_overwrite(self, mock_context, temp_dir):
        """Test copy succeeds with overwrite."""
        source = temp_dir / "source.txt"
        source.write_text("New content")
        dest = temp_dir / "dest.txt"
        dest.write_text("Old content")

        node = CopyFileNode("copy_1", config={"overwrite": True})
        node.set_input_value("source_path", str(source))
        node.set_input_value("dest_path", str(dest))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert dest.read_text() == "New content"


class TestMoveFileNode:
    """Tests for MoveFileNode."""

    def test_move_file(self, mock_context, temp_dir):
        """Test moving a file."""
        source = temp_dir / "source.txt"
        source.write_text("Move me")
        dest = temp_dir / "dest.txt"

        node = MoveFileNode("move_1")
        node.set_input_value("source_path", str(source))
        node.set_input_value("dest_path", str(dest))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert dest.exists()
        assert not source.exists()  # Original removed
        assert dest.read_text() == "Move me"

    def test_rename_file(self, mock_context, temp_dir):
        """Test renaming a file (same directory move)."""
        source = temp_dir / "original.txt"
        source.write_text("Content")
        dest = temp_dir / "renamed.txt"

        node = MoveFileNode("move_1")
        node.set_input_value("source_path", str(source))
        node.set_input_value("dest_path", str(dest))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert dest.exists()
        assert not source.exists()


class TestCreateDirectoryNode:
    """Tests for CreateDirectoryNode."""

    def test_create_directory(self, mock_context, temp_dir):
        """Test creating a directory."""
        new_dir = temp_dir / "new_folder"

        node = CreateDirectoryNode("mkdir_1")
        node.set_input_value("dir_path", str(new_dir))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_create_nested_directories(self, mock_context, temp_dir):
        """Test creating nested directories."""
        nested = temp_dir / "a" / "b" / "c"

        node = CreateDirectoryNode("mkdir_1", config={"parents": True})
        node.set_input_value("dir_path", str(nested))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert nested.exists()

    def test_create_existing_directory_ok(self, mock_context, temp_dir):
        """Test creating an existing directory with exist_ok."""
        existing = temp_dir / "existing"
        existing.mkdir()

        node = CreateDirectoryNode("mkdir_1", config={"exist_ok": True})
        node.set_input_value("dir_path", str(existing))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True


class TestListDirectoryNode:
    """Tests for ListDirectoryNode."""

    def test_list_directory(self, mock_context, temp_dir):
        """Test listing a directory."""
        # Create test files
        (temp_dir / "file1.txt").write_text("1")
        (temp_dir / "file2.txt").write_text("2")
        (temp_dir / "file3.py").write_text("3")
        (temp_dir / "subdir").mkdir()

        node = ListDirectoryNode("list_1")
        node.set_input_value("dir_path", str(temp_dir))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert node.get_output_value("count") == 4

    def test_list_with_pattern(self, mock_context, temp_dir):
        """Test listing with glob pattern."""
        (temp_dir / "file1.txt").write_text("1")
        (temp_dir / "file2.txt").write_text("2")
        (temp_dir / "file3.py").write_text("3")

        node = ListDirectoryNode("list_1", config={"pattern": "*.txt"})
        node.set_input_value("dir_path", str(temp_dir))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert node.get_output_value("count") == 2

    def test_list_files_only(self, mock_context, temp_dir):
        """Test listing files only."""
        (temp_dir / "file1.txt").write_text("1")
        (temp_dir / "subdir").mkdir()

        node = ListDirectoryNode("list_1", config={"files_only": True})
        node.set_input_value("dir_path", str(temp_dir))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert node.get_output_value("count") == 1

    def test_list_recursive(self, mock_context, temp_dir):
        """Test recursive listing."""
        (temp_dir / "file1.txt").write_text("1")
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "file2.txt").write_text("2")

        node = ListDirectoryNode("list_1", config={"recursive": True, "pattern": "*.txt"})
        node.set_input_value("dir_path", str(temp_dir))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert node.get_output_value("count") == 2


class TestFileExistsNode:
    """Tests for FileExistsNode."""

    def test_file_exists(self, mock_context, temp_dir):
        """Test checking if file exists."""
        test_file = temp_dir / "exists.txt"
        test_file.write_text("I exist")

        node = FileExistsNode("exists_1")
        node.set_input_value("path", str(test_file))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert node.get_output_value("exists") is True
        assert node.get_output_value("is_file") is True
        assert node.get_output_value("is_directory") is False

    def test_directory_exists(self, mock_context, temp_dir):
        """Test checking if directory exists."""
        test_dir = temp_dir / "test_folder"
        test_dir.mkdir()

        node = FileExistsNode("exists_1")
        node.set_input_value("path", str(test_dir))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert node.get_output_value("exists") is True
        assert node.get_output_value("is_file") is False
        assert node.get_output_value("is_directory") is True

    def test_file_not_exists(self, mock_context, temp_dir):
        """Test checking nonexistent path."""
        node = FileExistsNode("exists_1")
        node.set_input_value("path", str(temp_dir / "nonexistent"))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert node.get_output_value("exists") is False


class TestGetFileInfoNode:
    """Tests for GetFileInfoNode."""

    def test_get_file_info(self, mock_context, temp_dir):
        """Test getting file information."""
        test_file = temp_dir / "info.txt"
        test_file.write_text("Test content")

        node = GetFileInfoNode("info_1")
        node.set_input_value("file_path", str(test_file))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert node.get_output_value("size") == 12
        assert node.get_output_value("extension") == ".txt"
        assert node.get_output_value("name") == "info.txt"
        assert node.get_output_value("parent") == str(temp_dir)
        assert node.get_output_value("success") is True

    def test_get_info_nonexistent(self, mock_context, temp_dir):
        """Test getting info of nonexistent file."""
        node = GetFileInfoNode("info_1")
        node.set_input_value("file_path", str(temp_dir / "nonexistent.txt"))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is False


class TestReadCSVNode:
    """Tests for ReadCSVNode."""

    def test_read_csv_with_header(self, mock_context, temp_dir):
        """Test reading CSV with header."""
        csv_file = temp_dir / "data.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["name", "age", "city"])
            writer.writerow(["Alice", "30", "NYC"])
            writer.writerow(["Bob", "25", "LA"])

        node = ReadCSVNode("csv_1", config={"has_header": True})
        node.set_input_value("file_path", str(csv_file))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert node.get_output_value("headers") == ["name", "age", "city"]
        assert node.get_output_value("row_count") == 2
        assert node.get_output_value("data")[0]["name"] == "Alice"

    def test_read_csv_without_header(self, mock_context, temp_dir):
        """Test reading CSV without header."""
        csv_file = temp_dir / "data.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Alice", "30", "NYC"])
            writer.writerow(["Bob", "25", "LA"])

        node = ReadCSVNode("csv_1", config={"has_header": False})
        node.set_input_value("file_path", str(csv_file))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert node.get_output_value("row_count") == 2
        assert node.get_output_value("data")[0] == ["Alice", "30", "NYC"]


class TestWriteCSVNode:
    """Tests for WriteCSVNode."""

    def test_write_csv_from_dicts(self, mock_context, temp_dir):
        """Test writing CSV from dict data."""
        csv_file = temp_dir / "output.csv"
        data = [
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"}
        ]

        node = WriteCSVNode("csv_1")
        node.set_input_value("file_path", str(csv_file))
        node.set_input_value("data", data)

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert csv_file.exists()
        assert node.get_output_value("row_count") == 2

    def test_write_csv_from_lists(self, mock_context, temp_dir):
        """Test writing CSV from list data."""
        csv_file = temp_dir / "output.csv"
        data = [
            ["Alice", "30"],
            ["Bob", "25"]
        ]
        headers = ["name", "age"]

        node = WriteCSVNode("csv_1")
        node.set_input_value("file_path", str(csv_file))
        node.set_input_value("data", data)
        node.set_input_value("headers", headers)

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert node.get_output_value("row_count") == 2


class TestReadJSONFileNode:
    """Tests for ReadJSONFileNode."""

    def test_read_json_object(self, mock_context, temp_dir):
        """Test reading JSON object."""
        json_file = temp_dir / "data.json"
        data = {"name": "Alice", "age": 30, "active": True}
        json_file.write_text(json.dumps(data))

        node = ReadJSONFileNode("json_1")
        node.set_input_value("file_path", str(json_file))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert node.get_output_value("data") == data

    def test_read_json_array(self, mock_context, temp_dir):
        """Test reading JSON array."""
        json_file = temp_dir / "data.json"
        data = [1, 2, 3, "four", {"five": 5}]
        json_file.write_text(json.dumps(data))

        node = ReadJSONFileNode("json_1")
        node.set_input_value("file_path", str(json_file))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert node.get_output_value("data") == data

    def test_read_invalid_json(self, mock_context, temp_dir):
        """Test reading invalid JSON."""
        json_file = temp_dir / "invalid.json"
        json_file.write_text("{invalid json}")

        node = ReadJSONFileNode("json_1")
        node.set_input_value("file_path", str(json_file))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is False
        assert "invalid json" in result["error"].lower()


class TestWriteJSONFileNode:
    """Tests for WriteJSONFileNode."""

    def test_write_json(self, mock_context, temp_dir):
        """Test writing JSON."""
        json_file = temp_dir / "output.json"
        data = {"name": "Alice", "scores": [90, 85, 95]}

        node = WriteJSONFileNode("json_1")
        node.set_input_value("file_path", str(json_file))
        node.set_input_value("data", data)

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert json_file.exists()

        # Verify content
        with open(json_file) as f:
            written = json.load(f)
        assert written == data

    def test_write_json_with_indent(self, mock_context, temp_dir):
        """Test writing JSON with custom indent."""
        json_file = temp_dir / "output.json"
        data = {"key": "value"}

        node = WriteJSONFileNode("json_1", config={"indent": 4})
        node.set_input_value("file_path", str(json_file))
        node.set_input_value("data", data)

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        content = json_file.read_text()
        assert "    " in content  # 4-space indent


class TestZipFilesNode:
    """Tests for ZipFilesNode."""

    def test_zip_files(self, mock_context, temp_dir):
        """Test zipping files."""
        # Create test files
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")

        zip_path = temp_dir / "archive.zip"

        node = ZipFilesNode("zip_1")
        node.set_input_value("zip_path", str(zip_path))
        node.set_input_value("files", [str(file1), str(file2)])

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert zip_path.exists()
        assert node.get_output_value("file_count") == 2

        # Verify contents
        with zipfile.ZipFile(zip_path) as zf:
            assert len(zf.namelist()) == 2

    def test_zip_with_base_dir(self, mock_context, temp_dir):
        """Test zipping with base directory for relative paths."""
        subdir = temp_dir / "data"
        subdir.mkdir()
        file1 = subdir / "file.txt"
        file1.write_text("Content")

        zip_path = temp_dir / "archive.zip"

        node = ZipFilesNode("zip_1")
        node.set_input_value("zip_path", str(zip_path))
        node.set_input_value("files", [str(file1)])
        node.set_input_value("base_dir", str(temp_dir))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True

        with zipfile.ZipFile(zip_path) as zf:
            # Should preserve relative path
            assert "data/file.txt" in zf.namelist() or "data\\file.txt" in zf.namelist()


class TestUnzipFilesNode:
    """Tests for UnzipFilesNode."""

    def test_unzip_files(self, mock_context, temp_dir):
        """Test unzipping files."""
        # Create a test zip
        zip_path = temp_dir / "archive.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("file1.txt", "Content 1")
            zf.writestr("file2.txt", "Content 2")

        extract_dir = temp_dir / "extracted"

        node = UnzipFilesNode("unzip_1")
        node.set_input_value("zip_path", str(zip_path))
        node.set_input_value("extract_to", str(extract_dir))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert (extract_dir / "file1.txt").exists()
        assert (extract_dir / "file2.txt").exists()
        assert node.get_output_value("file_count") == 2

    def test_unzip_nonexistent(self, mock_context, temp_dir):
        """Test unzipping nonexistent file."""
        node = UnzipFilesNode("unzip_1")
        node.set_input_value("zip_path", str(temp_dir / "nonexistent.zip"))
        node.set_input_value("extract_to", str(temp_dir / "output"))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is False


class TestValidation:
    """Test validation for all nodes."""

    def test_read_file_missing_path(self, mock_context):
        """Test ReadFileNode with missing path."""
        node = ReadFileNode("read_1")
        # Don't set file_path

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is False

    def test_write_file_missing_path(self, mock_context):
        """Test WriteFileNode with missing path."""
        node = WriteFileNode("write_1")
        node.set_input_value("content", "test")
        # Don't set file_path

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is False

    def test_copy_file_missing_paths(self, mock_context):
        """Test CopyFileNode with missing paths."""
        node = CopyFileNode("copy_1")

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is False

    def test_zip_files_missing_files(self, mock_context, temp_dir):
        """Test ZipFilesNode with missing files list."""
        node = ZipFilesNode("zip_1")
        node.set_input_value("zip_path", str(temp_dir / "test.zip"))
        # Don't set files

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is False


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_read_empty_file(self, mock_context, temp_dir):
        """Test reading an empty file."""
        empty_file = temp_dir / "empty.txt"
        empty_file.write_text("")

        node = ReadFileNode("read_1")
        node.set_input_value("file_path", str(empty_file))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert node.get_output_value("content") == ""
        assert node.get_output_value("size") == 0

    def test_write_empty_content(self, mock_context, temp_dir):
        """Test writing empty content."""
        test_file = temp_dir / "empty.txt"

        node = WriteFileNode("write_1")
        node.set_input_value("file_path", str(test_file))
        node.set_input_value("content", "")

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert test_file.read_text() == ""

    def test_unicode_content(self, mock_context, temp_dir):
        """Test handling unicode content."""
        test_file = temp_dir / "unicode.txt"
        content = "Hello "

        node = WriteFileNode("write_1")
        node.set_input_value("file_path", str(test_file))
        node.set_input_value("content", content)

        asyncio.run(node.execute(mock_context))

        read_node = ReadFileNode("read_1")
        read_node.set_input_value("file_path", str(test_file))

        result = asyncio.run(read_node.execute(mock_context))

        assert result["success"] is True
        assert read_node.get_output_value("content") == content

    def test_list_empty_directory(self, mock_context, temp_dir):
        """Test listing an empty directory."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()

        node = ListDirectoryNode("list_1")
        node.set_input_value("dir_path", str(empty_dir))

        result = asyncio.run(node.execute(mock_context))

        assert result["success"] is True
        assert node.get_output_value("count") == 0
        assert node.get_output_value("items") == []
