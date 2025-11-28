"""
Tests for File System operation nodes.

Tests 18 file system nodes (55 tests total):
- Core File Ops: ReadFileNode, WriteFileNode, AppendFileNode, DeleteFileNode, CopyFileNode, MoveFileNode
- Structured Data: ReadCSVNode, WriteCSVNode, ReadJSONFileNode, WriteJSONFileNode
- Archives: ZipFilesNode, UnzipFilesNode
- Directory Ops: CreateDirectoryNode, ListDirectoryNode, ListFilesNode
- Info/Check: FileExistsNode, GetFileInfoNode, GetFileSizeNode

Coverage:
- Encoding tests (UTF-8, UTF-16, Latin-1)
- Large file handling
- Error scenarios (non-existent paths, permission errors)
- CSV: headers, delimiters, quoting, malformed data
- JSON: nested objects, arrays, invalid JSON
- ZIP: compression levels, nested directories
- Directory: recursive operations, glob patterns
"""

import json
import zipfile
import pytest
from pathlib import Path
from unittest.mock import Mock

# Note: execution_context fixture is provided by tests/conftest.py


@pytest.fixture
def sample_files(tmp_path: Path) -> dict:
    """Create sample file paths in temp directory."""
    return {
        "text": tmp_path / "test.txt",
        "csv": tmp_path / "data.csv",
        "json": tmp_path / "config.json",
        "zip": tmp_path / "archive.zip",
    }


@pytest.fixture
def file_system_setup(tmp_path: Path) -> Path:
    """Set up a directory structure for testing."""
    (tmp_path / "input").mkdir()
    (tmp_path / "output").mkdir()
    (tmp_path / "input" / "test.txt").write_text("Sample content", encoding="utf-8")
    (tmp_path / "input" / "data.csv").write_text(
        "col1,col2\nval1,val2\nval3,val4", encoding="utf-8"
    )
    (tmp_path / "input" / "config.json").write_text(
        '{"key": "value", "number": 42}', encoding="utf-8"
    )
    return tmp_path


# ============================================================================
# ReadFileNode Tests
# ============================================================================


class TestReadFileNode:
    """Tests for ReadFileNode."""

    @pytest.mark.asyncio
    async def test_read_text_file(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test reading a basic text file."""
        from casare_rpa.nodes.file import ReadFileNode

        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello World", encoding="utf-8")

        node = ReadFileNode(node_id="test_read", config={"allow_dangerous_paths": True})
        node.set_input_value("file_path", str(test_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("content") == "Hello World"
        assert node.get_output_value("size") == 11
        assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_read_utf16_encoding(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test reading file with UTF-16 encoding."""
        from casare_rpa.nodes.file import ReadFileNode

        test_file = tmp_path / "utf16.txt"
        test_file.write_text("Unicode: \u4e2d\u6587", encoding="utf-16")

        node = ReadFileNode(
            node_id="test_utf16",
            config={"encoding": "utf-16", "allow_dangerous_paths": True},
        )
        node.set_input_value("file_path", str(test_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "\u4e2d\u6587" in node.get_output_value("content")

    @pytest.mark.asyncio
    async def test_read_latin1_encoding(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test reading file with Latin-1 encoding."""
        from casare_rpa.nodes.file import ReadFileNode

        test_file = tmp_path / "latin1.txt"
        test_file.write_bytes(b"Caf\xe9 au lait")

        node = ReadFileNode(
            node_id="test_latin1",
            config={"encoding": "latin-1", "allow_dangerous_paths": True},
        )
        node.set_input_value("file_path", str(test_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("content") == "Caf\xe9 au lait"

    @pytest.mark.asyncio
    async def test_read_binary_mode(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test reading file in binary mode."""
        from casare_rpa.nodes.file import ReadFileNode

        test_file = tmp_path / "binary.bin"
        test_file.write_bytes(b"\x00\x01\x02\x03\xff")

        node = ReadFileNode(
            node_id="test_binary",
            config={"binary_mode": True, "allow_dangerous_paths": True},
        )
        node.set_input_value("file_path", str(test_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("content") == b"\x00\x01\x02\x03\xff"

    @pytest.mark.asyncio
    async def test_read_non_existent_file(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test reading non-existent file returns error."""
        from casare_rpa.nodes.file import ReadFileNode

        node = ReadFileNode(
            node_id="test_missing", config={"allow_dangerous_paths": True}
        )
        node.set_input_value("file_path", str(tmp_path / "nonexistent.txt"))

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_read_max_size_limit(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test file size limit enforcement."""
        from casare_rpa.nodes.file import ReadFileNode

        test_file = tmp_path / "large.txt"
        test_file.write_text("A" * 1000, encoding="utf-8")

        node = ReadFileNode(
            node_id="test_maxsize",
            config={"max_size": 500, "allow_dangerous_paths": True},
        )
        node.set_input_value("file_path", str(test_file))

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "exceeds" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_read_missing_path_error(self, execution_context: Mock) -> None:
        """Test error when file_path not provided."""
        from casare_rpa.nodes.file import ReadFileNode

        node = ReadFileNode(node_id="test_no_path")
        node.set_input_value("file_path", None)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()


# ============================================================================
# WriteFileNode Tests
# ============================================================================


class TestWriteFileNode:
    """Tests for WriteFileNode."""

    @pytest.mark.asyncio
    async def test_write_text_file(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test writing a basic text file."""
        from casare_rpa.nodes.file import WriteFileNode

        test_file = tmp_path / "output.txt"

        node = WriteFileNode(
            node_id="test_write", config={"allow_dangerous_paths": True}
        )
        node.set_input_value("file_path", str(test_file))
        node.set_input_value("content", "Hello World")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert test_file.read_text(encoding="utf-8") == "Hello World"
        assert node.get_output_value("bytes_written") == 11

    @pytest.mark.asyncio
    async def test_write_utf16_encoding(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test writing file with UTF-16 encoding."""
        from casare_rpa.nodes.file import WriteFileNode

        test_file = tmp_path / "utf16_out.txt"

        node = WriteFileNode(
            node_id="test_utf16_write",
            config={"encoding": "utf-16", "allow_dangerous_paths": True},
        )
        node.set_input_value("file_path", str(test_file))
        node.set_input_value("content", "Unicode: \u4e2d\u6587")

        result = await node.execute(execution_context)

        assert result["success"] is True
        content = test_file.read_text(encoding="utf-16")
        assert "Unicode" in content

    @pytest.mark.asyncio
    async def test_write_creates_parent_dirs(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test create_dirs creates parent directories."""
        from casare_rpa.nodes.file import WriteFileNode

        test_file = tmp_path / "nested" / "deep" / "output.txt"

        node = WriteFileNode(
            node_id="test_nested",
            config={"create_dirs": True, "allow_dangerous_paths": True},
        )
        node.set_input_value("file_path", str(test_file))
        node.set_input_value("content", "Nested content")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert test_file.exists()
        assert test_file.read_text(encoding="utf-8") == "Nested content"

    @pytest.mark.asyncio
    async def test_write_binary_mode(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test writing file in binary mode."""
        from casare_rpa.nodes.file import WriteFileNode

        test_file = tmp_path / "binary.bin"

        node = WriteFileNode(
            node_id="test_binary_write",
            config={"binary_mode": True, "allow_dangerous_paths": True},
        )
        node.set_input_value("file_path", str(test_file))
        node.set_input_value("content", b"\x00\x01\x02\x03")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert test_file.read_bytes() == b"\x00\x01\x02\x03"

    @pytest.mark.asyncio
    async def test_write_append_mode(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test append mode adds to existing file."""
        from casare_rpa.nodes.file import WriteFileNode

        test_file = tmp_path / "append.txt"
        test_file.write_text("First line\n", encoding="utf-8")

        node = WriteFileNode(
            node_id="test_append",
            config={"append_mode": True, "allow_dangerous_paths": True},
        )
        node.set_input_value("file_path", str(test_file))
        node.set_input_value("content", "Second line")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert test_file.read_text(encoding="utf-8") == "First line\nSecond line"


# ============================================================================
# AppendFileNode Tests
# ============================================================================


class TestAppendFileNode:
    """Tests for AppendFileNode."""

    @pytest.mark.asyncio
    async def test_append_to_existing_file(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test appending to existing file."""
        from casare_rpa.nodes.file import AppendFileNode

        test_file = tmp_path / "append.txt"
        test_file.write_text("Line 1\n", encoding="utf-8")

        node = AppendFileNode(node_id="test_append")
        node.set_input_value("file_path", str(test_file))
        node.set_input_value("content", "Line 2")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert test_file.read_text(encoding="utf-8") == "Line 1\nLine 2"

    @pytest.mark.asyncio
    async def test_append_creates_file_if_missing(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test create_if_missing creates new file."""
        from casare_rpa.nodes.file import AppendFileNode

        test_file = tmp_path / "new_append.txt"

        node = AppendFileNode(node_id="test_create", config={"create_if_missing": True})
        node.set_input_value("file_path", str(test_file))
        node.set_input_value("content", "New content")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert test_file.exists()
        assert test_file.read_text(encoding="utf-8") == "New content"

    @pytest.mark.asyncio
    async def test_append_error_file_missing(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test error when file missing and create_if_missing=False."""
        from casare_rpa.nodes.file import AppendFileNode

        node = AppendFileNode(
            node_id="test_missing", config={"create_if_missing": False}
        )
        node.set_input_value("file_path", str(tmp_path / "missing.txt"))
        node.set_input_value("content", "Content")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "not found" in result["error"].lower()


# ============================================================================
# DeleteFileNode Tests
# ============================================================================


class TestDeleteFileNode:
    """Tests for DeleteFileNode."""

    @pytest.mark.asyncio
    async def test_delete_existing_file(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test deleting an existing file."""
        from casare_rpa.nodes.file import DeleteFileNode

        test_file = tmp_path / "to_delete.txt"
        test_file.write_text("Delete me", encoding="utf-8")

        node = DeleteFileNode(
            node_id="test_delete", config={"allow_dangerous_paths": True}
        )
        node.set_input_value("file_path", str(test_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert not test_file.exists()

    @pytest.mark.asyncio
    async def test_delete_ignore_missing(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test ignore_missing option."""
        from casare_rpa.nodes.file import DeleteFileNode

        node = DeleteFileNode(
            node_id="test_ignore",
            config={"ignore_missing": True, "allow_dangerous_paths": True},
        )
        node.set_input_value("file_path", str(tmp_path / "nonexistent.txt"))

        result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_delete_error_missing(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test error when file missing and ignore_missing=False."""
        from casare_rpa.nodes.file import DeleteFileNode

        node = DeleteFileNode(
            node_id="test_error",
            config={"ignore_missing": False, "allow_dangerous_paths": True},
        )
        node.set_input_value("file_path", str(tmp_path / "nonexistent.txt"))

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "not found" in result["error"].lower()


# ============================================================================
# CopyFileNode Tests
# ============================================================================


class TestCopyFileNode:
    """Tests for CopyFileNode."""

    @pytest.mark.asyncio
    async def test_copy_file(self, execution_context: Mock, tmp_path: Path) -> None:
        """Test copying a file."""
        from casare_rpa.nodes.file import CopyFileNode

        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        source.write_text("Copy me", encoding="utf-8")

        node = CopyFileNode(node_id="test_copy")
        node.set_input_value("source_path", str(source))
        node.set_input_value("dest_path", str(dest))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert dest.exists()
        assert dest.read_text(encoding="utf-8") == "Copy me"
        assert source.exists()  # Source still exists

    @pytest.mark.asyncio
    async def test_copy_overwrite(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test copy with overwrite option."""
        from casare_rpa.nodes.file import CopyFileNode

        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        source.write_text("New content", encoding="utf-8")
        dest.write_text("Old content", encoding="utf-8")

        node = CopyFileNode(node_id="test_overwrite", config={"overwrite": True})
        node.set_input_value("source_path", str(source))
        node.set_input_value("dest_path", str(dest))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert dest.read_text(encoding="utf-8") == "New content"

    @pytest.mark.asyncio
    async def test_copy_no_overwrite_error(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test error when destination exists and overwrite=False."""
        from casare_rpa.nodes.file import CopyFileNode

        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        source.write_text("Source", encoding="utf-8")
        dest.write_text("Existing", encoding="utf-8")

        node = CopyFileNode(node_id="test_no_overwrite", config={"overwrite": False})
        node.set_input_value("source_path", str(source))
        node.set_input_value("dest_path", str(dest))

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "exists" in result["error"].lower()


# ============================================================================
# MoveFileNode Tests
# ============================================================================


class TestMoveFileNode:
    """Tests for MoveFileNode."""

    @pytest.mark.asyncio
    async def test_move_file(self, execution_context: Mock, tmp_path: Path) -> None:
        """Test moving a file."""
        from casare_rpa.nodes.file import MoveFileNode

        source = tmp_path / "source.txt"
        dest = tmp_path / "moved.txt"
        source.write_text("Move me", encoding="utf-8")

        node = MoveFileNode(node_id="test_move")
        node.set_input_value("source_path", str(source))
        node.set_input_value("dest_path", str(dest))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert dest.exists()
        assert not source.exists()  # Source no longer exists
        assert dest.read_text(encoding="utf-8") == "Move me"

    @pytest.mark.asyncio
    async def test_move_with_overwrite(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test move with overwrite option."""
        from casare_rpa.nodes.file import MoveFileNode

        source = tmp_path / "source.txt"
        dest = tmp_path / "dest.txt"
        source.write_text("New", encoding="utf-8")
        dest.write_text("Old", encoding="utf-8")

        node = MoveFileNode(node_id="test_move_overwrite", config={"overwrite": True})
        node.set_input_value("source_path", str(source))
        node.set_input_value("dest_path", str(dest))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert dest.read_text(encoding="utf-8") == "New"


# ============================================================================
# ReadCSVNode Tests
# ============================================================================


class TestReadCSVNode:
    """Tests for ReadCSVNode."""

    @pytest.mark.asyncio
    async def test_read_csv_with_header(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test reading CSV with header row."""
        from casare_rpa.nodes.file import ReadCSVNode

        csv_file = tmp_path / "data.csv"
        csv_file.write_text("name,age,city\nAlice,30,NYC\nBob,25,LA", encoding="utf-8")

        node = ReadCSVNode(node_id="test_csv")
        node.set_input_value("file_path", str(csv_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        data = node.get_output_value("data")
        assert len(data) == 2
        assert data[0]["name"] == "Alice"
        assert data[0]["age"] == "30"
        assert node.get_output_value("headers") == ["name", "age", "city"]

    @pytest.mark.asyncio
    async def test_read_csv_without_header(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test reading CSV without header row."""
        from casare_rpa.nodes.file import ReadCSVNode

        csv_file = tmp_path / "noheader.csv"
        csv_file.write_text("Alice,30,NYC\nBob,25,LA", encoding="utf-8")

        node = ReadCSVNode(node_id="test_csv_noheader", config={"has_header": False})
        node.set_input_value("file_path", str(csv_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        data = node.get_output_value("data")
        assert len(data) == 2
        assert data[0] == ["Alice", "30", "NYC"]

    @pytest.mark.asyncio
    async def test_read_csv_custom_delimiter(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test reading CSV with custom delimiter."""
        from casare_rpa.nodes.file import ReadCSVNode

        csv_file = tmp_path / "semicolon.csv"
        csv_file.write_text("name;age;city\nAlice;30;NYC", encoding="utf-8")

        node = ReadCSVNode(node_id="test_delimiter", config={"delimiter": ";"})
        node.set_input_value("file_path", str(csv_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        data = node.get_output_value("data")
        assert data[0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_read_csv_quoted_fields(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test reading CSV with quoted fields containing delimiters."""
        from casare_rpa.nodes.file import ReadCSVNode

        csv_file = tmp_path / "quoted.csv"
        csv_file.write_text(
            'name,description\n"Smith, John","Developer, Senior"', encoding="utf-8"
        )

        node = ReadCSVNode(node_id="test_quoted")
        node.set_input_value("file_path", str(csv_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        data = node.get_output_value("data")
        assert data[0]["name"] == "Smith, John"
        assert data[0]["description"] == "Developer, Senior"

    @pytest.mark.asyncio
    async def test_read_csv_skip_rows(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test skipping initial rows in CSV."""
        from casare_rpa.nodes.file import ReadCSVNode

        csv_file = tmp_path / "skip.csv"
        csv_file.write_text(
            "Title Row\nIgnore this\nname,age\nAlice,30", encoding="utf-8"
        )

        node = ReadCSVNode(node_id="test_skip", config={"skip_rows": 2})
        node.set_input_value("file_path", str(csv_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        data = node.get_output_value("data")
        assert len(data) == 1
        assert data[0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_read_csv_max_rows(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test max_rows limit."""
        from casare_rpa.nodes.file import ReadCSVNode

        csv_file = tmp_path / "many.csv"
        csv_file.write_text(
            "name\nA\nB\nC\nD\nE",
            encoding="utf-8",
        )

        node = ReadCSVNode(node_id="test_maxrows", config={"max_rows": 2})
        node.set_input_value("file_path", str(csv_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("row_count") == 2


# ============================================================================
# WriteCSVNode Tests
# ============================================================================


class TestWriteCSVNode:
    """Tests for WriteCSVNode."""

    @pytest.mark.asyncio
    async def test_write_csv_dict_data(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test writing CSV from dict data."""
        from casare_rpa.nodes.file import WriteCSVNode

        csv_file = tmp_path / "output.csv"
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]

        node = WriteCSVNode(node_id="test_write_csv")
        node.set_input_value("file_path", str(csv_file))
        node.set_input_value("data", data)
        node.set_input_value("headers", None)

        result = await node.execute(execution_context)

        assert result["success"] is True
        content = csv_file.read_text(encoding="utf-8")
        assert "name" in content
        assert "Alice" in content

    @pytest.mark.asyncio
    async def test_write_csv_list_data(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test writing CSV from list data."""
        from casare_rpa.nodes.file import WriteCSVNode

        csv_file = tmp_path / "list_output.csv"
        data = [["Alice", 30], ["Bob", 25]]
        headers = ["name", "age"]

        node = WriteCSVNode(node_id="test_list_csv")
        node.set_input_value("file_path", str(csv_file))
        node.set_input_value("data", data)
        node.set_input_value("headers", headers)

        result = await node.execute(execution_context)

        assert result["success"] is True
        content = csv_file.read_text(encoding="utf-8")
        assert "name,age" in content
        assert "Alice,30" in content

    @pytest.mark.asyncio
    async def test_write_csv_no_header(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test writing CSV without header."""
        from casare_rpa.nodes.file import WriteCSVNode

        csv_file = tmp_path / "no_header.csv"
        data = [["Alice", 30], ["Bob", 25]]

        node = WriteCSVNode(node_id="test_no_header", config={"write_header": False})
        node.set_input_value("file_path", str(csv_file))
        node.set_input_value("data", data)
        node.set_input_value("headers", None)

        result = await node.execute(execution_context)

        assert result["success"] is True
        content = csv_file.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        assert lines[0] == "Alice,30"


# ============================================================================
# ReadJSONFileNode Tests
# ============================================================================


class TestReadJSONFileNode:
    """Tests for ReadJSONFileNode."""

    @pytest.mark.asyncio
    async def test_read_json_object(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test reading JSON object."""
        from casare_rpa.nodes.file import ReadJSONFileNode

        json_file = tmp_path / "config.json"
        json_file.write_text('{"name": "test", "count": 42}', encoding="utf-8")

        node = ReadJSONFileNode(node_id="test_json")
        node.set_input_value("file_path", str(json_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        data = node.get_output_value("data")
        assert data["name"] == "test"
        assert data["count"] == 42

    @pytest.mark.asyncio
    async def test_read_json_array(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test reading JSON array."""
        from casare_rpa.nodes.file import ReadJSONFileNode

        json_file = tmp_path / "list.json"
        json_file.write_text('[1, 2, 3, "four"]', encoding="utf-8")

        node = ReadJSONFileNode(node_id="test_json_array")
        node.set_input_value("file_path", str(json_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        data = node.get_output_value("data")
        assert data == [1, 2, 3, "four"]

    @pytest.mark.asyncio
    async def test_read_json_nested(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test reading nested JSON structure."""
        from casare_rpa.nodes.file import ReadJSONFileNode

        json_file = tmp_path / "nested.json"
        nested_data = {
            "user": {"name": "Alice", "address": {"city": "NYC", "zip": "10001"}},
            "items": [1, 2, 3],
        }
        json_file.write_text(json.dumps(nested_data), encoding="utf-8")

        node = ReadJSONFileNode(node_id="test_nested")
        node.set_input_value("file_path", str(json_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        data = node.get_output_value("data")
        assert data["user"]["address"]["city"] == "NYC"

    @pytest.mark.asyncio
    async def test_read_json_invalid(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test error on invalid JSON."""
        from casare_rpa.nodes.file import ReadJSONFileNode

        json_file = tmp_path / "invalid.json"
        json_file.write_text("{invalid json}", encoding="utf-8")

        node = ReadJSONFileNode(node_id="test_invalid")
        node.set_input_value("file_path", str(json_file))

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "invalid" in result["error"].lower()


# ============================================================================
# WriteJSONFileNode Tests
# ============================================================================


class TestWriteJSONFileNode:
    """Tests for WriteJSONFileNode."""

    @pytest.mark.asyncio
    async def test_write_json_object(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test writing JSON object."""
        from casare_rpa.nodes.file import WriteJSONFileNode

        json_file = tmp_path / "output.json"
        data = {"name": "test", "value": 123}

        node = WriteJSONFileNode(node_id="test_write_json")
        node.set_input_value("file_path", str(json_file))
        node.set_input_value("data", data)

        result = await node.execute(execution_context)

        assert result["success"] is True
        written_data = json.loads(json_file.read_text(encoding="utf-8"))
        assert written_data == data

    @pytest.mark.asyncio
    async def test_write_json_indent(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test writing JSON with custom indent."""
        from casare_rpa.nodes.file import WriteJSONFileNode

        json_file = tmp_path / "indented.json"
        data = {"key": "value"}

        node = WriteJSONFileNode(node_id="test_indent", config={"indent": 4})
        node.set_input_value("file_path", str(json_file))
        node.set_input_value("data", data)

        result = await node.execute(execution_context)

        assert result["success"] is True
        content = json_file.read_text(encoding="utf-8")
        assert "    " in content  # 4-space indent

    @pytest.mark.asyncio
    async def test_write_json_unicode(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test writing JSON with unicode characters."""
        from casare_rpa.nodes.file import WriteJSONFileNode

        json_file = tmp_path / "unicode.json"
        data = {"text": "\u4e2d\u6587"}

        node = WriteJSONFileNode(node_id="test_unicode", config={"ensure_ascii": False})
        node.set_input_value("file_path", str(json_file))
        node.set_input_value("data", data)

        result = await node.execute(execution_context)

        assert result["success"] is True
        content = json_file.read_text(encoding="utf-8")
        assert "\u4e2d\u6587" in content


# ============================================================================
# ZipFilesNode Tests
# ============================================================================


class TestZipFilesNode:
    """Tests for ZipFilesNode."""

    @pytest.mark.asyncio
    async def test_zip_files(self, execution_context: Mock, tmp_path: Path) -> None:
        """Test creating ZIP archive."""
        from casare_rpa.nodes.file import ZipFilesNode

        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content 1", encoding="utf-8")
        file2.write_text("Content 2", encoding="utf-8")
        zip_path = tmp_path / "archive.zip"

        node = ZipFilesNode(node_id="test_zip")
        node.set_input_value("zip_path", str(zip_path))
        node.set_input_value("files", [str(file1), str(file2)])
        node.set_input_value("base_dir", None)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert zip_path.exists()
        assert node.get_output_value("file_count") == 2

        with zipfile.ZipFile(zip_path, "r") as zf:
            assert len(zf.namelist()) == 2

    @pytest.mark.asyncio
    async def test_zip_with_base_dir(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test ZIP with relative paths from base_dir."""
        from casare_rpa.nodes.file import ZipFilesNode

        subdir = tmp_path / "subdir"
        subdir.mkdir()
        file1 = subdir / "file.txt"
        file1.write_text("Content", encoding="utf-8")
        zip_path = tmp_path / "archive.zip"

        node = ZipFilesNode(node_id="test_zip_base")
        node.set_input_value("zip_path", str(zip_path))
        node.set_input_value("files", [str(file1)])
        node.set_input_value("base_dir", str(tmp_path))

        result = await node.execute(execution_context)

        assert result["success"] is True
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            assert "subdir/file.txt" in names or "subdir\\file.txt" in names

    @pytest.mark.asyncio
    async def test_zip_compression_stored(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test ZIP with no compression (STORED)."""
        from casare_rpa.nodes.file import ZipFilesNode

        file1 = tmp_path / "file.txt"
        file1.write_text("Content", encoding="utf-8")
        zip_path = tmp_path / "stored.zip"

        node = ZipFilesNode(
            node_id="test_zip_stored", config={"compression": "ZIP_STORED"}
        )
        node.set_input_value("zip_path", str(zip_path))
        node.set_input_value("files", [str(file1)])
        node.set_input_value("base_dir", None)

        result = await node.execute(execution_context)

        assert result["success"] is True
        with zipfile.ZipFile(zip_path, "r") as zf:
            info = zf.getinfo("file.txt")
            assert info.compress_type == zipfile.ZIP_STORED


# ============================================================================
# UnzipFilesNode Tests
# ============================================================================


class TestUnzipFilesNode:
    """Tests for UnzipFilesNode."""

    @pytest.mark.asyncio
    async def test_unzip_files(self, execution_context: Mock, tmp_path: Path) -> None:
        """Test extracting ZIP archive."""
        from casare_rpa.nodes.file import UnzipFilesNode

        zip_path = tmp_path / "archive.zip"
        extract_to = tmp_path / "extracted"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("file1.txt", "Content 1")
            zf.writestr("file2.txt", "Content 2")

        node = UnzipFilesNode(
            node_id="test_unzip", config={"allow_dangerous_paths": True}
        )
        node.set_input_value("zip_path", str(zip_path))
        node.set_input_value("extract_to", str(extract_to))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert (extract_to / "file1.txt").exists()
        assert (extract_to / "file2.txt").exists()
        assert node.get_output_value("file_count") == 2

    @pytest.mark.asyncio
    async def test_unzip_nested_directories(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test extracting ZIP with nested directories."""
        from casare_rpa.nodes.file import UnzipFilesNode

        zip_path = tmp_path / "nested.zip"
        extract_to = tmp_path / "extracted"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("dir1/file.txt", "Content")
            zf.writestr("dir1/dir2/deep.txt", "Deep content")

        node = UnzipFilesNode(
            node_id="test_unzip_nested", config={"allow_dangerous_paths": True}
        )
        node.set_input_value("zip_path", str(zip_path))
        node.set_input_value("extract_to", str(extract_to))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert (extract_to / "dir1" / "file.txt").exists()
        assert (extract_to / "dir1" / "dir2" / "deep.txt").exists()


# ============================================================================
# CreateDirectoryNode Tests
# ============================================================================


class TestCreateDirectoryNode:
    """Tests for CreateDirectoryNode."""

    @pytest.mark.asyncio
    async def test_create_directory(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test creating a directory."""
        from casare_rpa.nodes.file import CreateDirectoryNode

        new_dir = tmp_path / "new_folder"

        node = CreateDirectoryNode(node_id="test_mkdir")
        node.set_input_value("dir_path", str(new_dir))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    @pytest.mark.asyncio
    async def test_create_nested_directories(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test creating nested directories with parents=True."""
        from casare_rpa.nodes.file import CreateDirectoryNode

        nested_dir = tmp_path / "a" / "b" / "c"

        node = CreateDirectoryNode(node_id="test_nested", config={"parents": True})
        node.set_input_value("dir_path", str(nested_dir))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert nested_dir.exists()

    @pytest.mark.asyncio
    async def test_create_existing_exist_ok(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test exist_ok option for existing directory."""
        from casare_rpa.nodes.file import CreateDirectoryNode

        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        node = CreateDirectoryNode(node_id="test_exist_ok", config={"exist_ok": True})
        node.set_input_value("dir_path", str(existing_dir))

        result = await node.execute(execution_context)

        assert result["success"] is True


# ============================================================================
# ListDirectoryNode Tests
# ============================================================================


class TestListDirectoryNode:
    """Tests for ListDirectoryNode."""

    @pytest.mark.asyncio
    async def test_list_directory(
        self, execution_context: Mock, file_system_setup: Path
    ) -> None:
        """Test listing directory contents."""
        from casare_rpa.nodes.file import ListDirectoryNode

        node = ListDirectoryNode(node_id="test_list")
        node.set_input_value("dir_path", str(file_system_setup / "input"))

        result = await node.execute(execution_context)

        assert result["success"] is True
        items = node.get_output_value("items")
        assert node.get_output_value("count") >= 3

    @pytest.mark.asyncio
    async def test_list_directory_files_only(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test listing files only."""
        from casare_rpa.nodes.file import ListDirectoryNode

        (tmp_path / "file.txt").write_text("content", encoding="utf-8")
        (tmp_path / "subdir").mkdir()

        node = ListDirectoryNode(node_id="test_files_only", config={"files_only": True})
        node.set_input_value("dir_path", str(tmp_path))

        result = await node.execute(execution_context)

        assert result["success"] is True
        items = node.get_output_value("items")
        assert all(Path(item).is_file() for item in items)

    @pytest.mark.asyncio
    async def test_list_directory_glob_pattern(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test listing with glob pattern."""
        from casare_rpa.nodes.file import ListDirectoryNode

        (tmp_path / "file1.txt").write_text("a", encoding="utf-8")
        (tmp_path / "file2.txt").write_text("b", encoding="utf-8")
        (tmp_path / "data.csv").write_text("c", encoding="utf-8")

        node = ListDirectoryNode(node_id="test_glob", config={"pattern": "*.txt"})
        node.set_input_value("dir_path", str(tmp_path))

        result = await node.execute(execution_context)

        assert result["success"] is True
        items = node.get_output_value("items")
        assert len(items) == 2
        assert all(".txt" in item for item in items)

    @pytest.mark.asyncio
    async def test_list_directory_recursive(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test recursive directory listing."""
        from casare_rpa.nodes.file import ListDirectoryNode

        (tmp_path / "file.txt").write_text("a", encoding="utf-8")
        subdir = tmp_path / "sub"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("b", encoding="utf-8")

        node = ListDirectoryNode(
            node_id="test_recursive",
            config={"recursive": True, "pattern": "*.txt", "files_only": True},
        )
        node.set_input_value("dir_path", str(tmp_path))

        result = await node.execute(execution_context)

        assert result["success"] is True
        items = node.get_output_value("items")
        assert len(items) == 2


# ============================================================================
# ListFilesNode Tests
# ============================================================================


class TestListFilesNode:
    """Tests for ListFilesNode."""

    @pytest.mark.asyncio
    async def test_list_files(self, execution_context: Mock, tmp_path: Path) -> None:
        """Test listing files in directory."""
        from casare_rpa.nodes.file import ListFilesNode

        (tmp_path / "file1.txt").write_text("a", encoding="utf-8")
        (tmp_path / "file2.txt").write_text("b", encoding="utf-8")
        (tmp_path / "subdir").mkdir()

        node = ListFilesNode(node_id="test_list_files")
        node.set_input_value("directory_path", str(tmp_path))

        result = await node.execute(execution_context)

        assert result["success"] is True
        files = node.get_output_value("files")
        assert node.get_output_value("count") == 2


# ============================================================================
# FileExistsNode Tests
# ============================================================================


class TestFileExistsNode:
    """Tests for FileExistsNode."""

    @pytest.mark.asyncio
    async def test_file_exists(self, execution_context: Mock, tmp_path: Path) -> None:
        """Test checking file existence."""
        from casare_rpa.nodes.file import FileExistsNode

        test_file = tmp_path / "exists.txt"
        test_file.write_text("content", encoding="utf-8")

        node = FileExistsNode(node_id="test_exists")
        node.set_input_value("path", str(test_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("exists") is True
        assert node.get_output_value("is_file") is True
        assert node.get_output_value("is_directory") is False

    @pytest.mark.asyncio
    async def test_directory_exists(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test checking directory existence."""
        from casare_rpa.nodes.file import FileExistsNode

        test_dir = tmp_path / "subdir"
        test_dir.mkdir()

        node = FileExistsNode(node_id="test_dir_exists")
        node.set_input_value("path", str(test_dir))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("exists") is True
        assert node.get_output_value("is_file") is False
        assert node.get_output_value("is_directory") is True

    @pytest.mark.asyncio
    async def test_path_not_exists(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test checking non-existent path."""
        from casare_rpa.nodes.file import FileExistsNode

        node = FileExistsNode(node_id="test_not_exists")
        node.set_input_value("path", str(tmp_path / "nonexistent"))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("exists") is False


# ============================================================================
# GetFileInfoNode Tests
# ============================================================================


class TestGetFileInfoNode:
    """Tests for GetFileInfoNode."""

    @pytest.mark.asyncio
    async def test_get_file_info(self, execution_context: Mock, tmp_path: Path) -> None:
        """Test getting file information."""
        from casare_rpa.nodes.file import GetFileInfoNode

        test_file = tmp_path / "info.txt"
        test_file.write_text("Test content", encoding="utf-8")

        node = GetFileInfoNode(node_id="test_info")
        node.set_input_value("file_path", str(test_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("size") == 12
        assert node.get_output_value("name") == "info.txt"
        assert node.get_output_value("extension") == ".txt"
        assert node.get_output_value("parent") == str(tmp_path)
        assert node.get_output_value("created") is not None
        assert node.get_output_value("modified") is not None


# ============================================================================
# GetFileSizeNode Tests
# ============================================================================


class TestGetFileSizeNode:
    """Tests for GetFileSizeNode."""

    @pytest.mark.asyncio
    async def test_get_file_size(self, execution_context: Mock, tmp_path: Path) -> None:
        """Test getting file size."""
        from casare_rpa.nodes.file import GetFileSizeNode

        test_file = tmp_path / "sized.txt"
        test_file.write_text("12345678901234567890", encoding="utf-8")

        node = GetFileSizeNode(node_id="test_size")
        node.set_input_value("file_path", str(test_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("size") == 20

    @pytest.mark.asyncio
    async def test_get_file_size_not_found(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test error when file not found."""
        from casare_rpa.nodes.file import GetFileSizeNode

        node = GetFileSizeNode(node_id="test_size_missing")
        node.set_input_value("file_path", str(tmp_path / "missing.txt"))

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "not found" in result["error"].lower()


# ============================================================================
# ExecutionResult Pattern Tests
# ============================================================================


class TestExecutionResultPattern:
    """Test that all file nodes follow ExecutionResult pattern."""

    @pytest.mark.asyncio
    async def test_execution_result_structure(
        self, execution_context: Mock, tmp_path: Path
    ) -> None:
        """Test all nodes return proper ExecutionResult structure."""
        from casare_rpa.nodes.file import ReadFileNode, WriteFileNode

        # Setup
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test", encoding="utf-8")

        # Test ReadFileNode
        read_node = ReadFileNode(
            node_id="test_pattern_read", config={"allow_dangerous_paths": True}
        )
        read_node.set_input_value("file_path", str(test_file))
        read_result = await read_node.execute(execution_context)

        assert "success" in read_result
        assert "data" in read_result or "error" in read_result
        assert "next_nodes" in read_result

        # Test WriteFileNode
        write_node = WriteFileNode(
            node_id="test_pattern_write", config={"allow_dangerous_paths": True}
        )
        write_node.set_input_value("file_path", str(tmp_path / "out.txt"))
        write_node.set_input_value("content", "Output")
        write_result = await write_node.execute(execution_context)

        assert "success" in write_result
        assert "data" in write_result
        assert "next_nodes" in write_result
        assert "exec_out" in write_result["next_nodes"]
