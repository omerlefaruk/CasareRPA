"""
Integration tests for file system nodes.

Tests 11 file system nodes to ensure proper file/directory operations.
"""

import pytest
import tempfile
import csv
from pathlib import Path
from unittest.mock import Mock
from casare_rpa.core.execution_context import ExecutionContext


class TestFileSystemNodes:
    """Integration tests for file system category nodes."""

    @pytest.fixture
    def execution_context(self):
        """Create a mock execution context."""
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Test content\nLine 2\nLine 3")
            temp_path = f.name
        yield temp_path
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)

    # =============================================================================
    # File Operations (6 tests)
    # =============================================================================

    @pytest.mark.asyncio
    async def test_read_file_node(self, execution_context, temp_file):
        """Test ReadFileNode reads file content."""
        from casare_rpa.nodes.file_system_nodes import ReadFileNode

        node = ReadFileNode(node_id="test_read")
        node.set_input_value("file_path", temp_file)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "Test content" in result["data"]["content"]

    @pytest.mark.asyncio
    async def test_write_file_node(self, execution_context, temp_dir):
        """Test WriteFileNode writes content to file."""
        from casare_rpa.nodes.file_system_nodes import WriteFileNode

        output_file = Path(temp_dir) / "output.txt"

        node = WriteFileNode(node_id="test_write")
        node.set_input_value("file_path", str(output_file))
        node.set_input_value("content", "Hello, File System!")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert output_file.exists()
        assert output_file.read_text() == "Hello, File System!"

    @pytest.mark.asyncio
    async def test_file_exists_node_true(self, execution_context, temp_file):
        """Test FileExistsNode returns true for existing file."""
        from casare_rpa.nodes.file_system_nodes import FileExistsNode

        node = FileExistsNode(node_id="test_exists_true")
        node.set_input_value("file_path", temp_file)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["exists"] is True

    @pytest.mark.asyncio
    async def test_file_exists_node_false(self, execution_context):
        """Test FileExistsNode returns false for non-existent file."""
        from casare_rpa.nodes.file_system_nodes import FileExistsNode

        node = FileExistsNode(node_id="test_exists_false")
        node.set_input_value("file_path", "/nonexistent/path/file.txt")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["exists"] is False

    @pytest.mark.asyncio
    async def test_delete_file_node(self, execution_context, temp_dir):
        """Test DeleteFileNode removes file."""
        from casare_rpa.nodes.file_system_nodes import DeleteFileNode

        # Create file to delete
        test_file = Path(temp_dir) / "to_delete.txt"
        test_file.write_text("Delete me")

        node = DeleteFileNode(node_id="test_delete")
        node.set_input_value("file_path", str(test_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert not test_file.exists()

    @pytest.mark.asyncio
    async def test_get_file_size_node(self, execution_context, temp_file):
        """Test GetFileSizeNode returns file size."""
        from casare_rpa.nodes.file_system_nodes import GetFileSizeNode

        node = GetFileSizeNode(node_id="test_size")
        node.set_input_value("file_path", temp_file)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["size"] > 0

    # =============================================================================
    # Directory Operations (3 tests)
    # =============================================================================

    @pytest.mark.asyncio
    async def test_create_directory_node(self, execution_context, temp_dir):
        """Test CreateDirectoryNode creates directory."""
        from casare_rpa.nodes.file_system_nodes import CreateDirectoryNode

        new_dir = Path(temp_dir) / "new_folder"

        node = CreateDirectoryNode(node_id="test_create_dir")
        node.set_input_value("directory_path", str(new_dir))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    @pytest.mark.asyncio
    async def test_delete_directory_node(self, execution_context, temp_dir):
        """Test DeleteDirectoryNode removes directory."""
        from casare_rpa.nodes.file_system_nodes import DeleteDirectoryNode

        # Create directory to delete
        test_dir = Path(temp_dir) / "to_delete"
        test_dir.mkdir()

        node = DeleteDirectoryNode(node_id="test_delete_dir")
        node.set_input_value("directory_path", str(test_dir))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert not test_dir.exists()

    @pytest.mark.asyncio
    async def test_list_files_node(self, execution_context, temp_dir):
        """Test ListFilesNode lists files in directory."""
        from casare_rpa.nodes.file_system_nodes import ListFilesNode

        # Create some test files
        (Path(temp_dir) / "file1.txt").write_text("Test 1")
        (Path(temp_dir) / "file2.txt").write_text("Test 2")
        (Path(temp_dir) / "file3.log").write_text("Log")

        node = ListFilesNode(node_id="test_list")
        node.set_input_value("directory_path", temp_dir)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert len(result["data"]["files"]) >= 3

    # =============================================================================
    # CSV Operations (2 tests)
    # =============================================================================

    @pytest.mark.asyncio
    async def test_read_csv_node(self, execution_context, temp_dir):
        """Test ReadCSVNode reads CSV file."""
        from casare_rpa.nodes.file_system_nodes import ReadCSVNode

        # Create CSV file
        csv_file = Path(temp_dir) / "test.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Age", "City"])
            writer.writerow(["Alice", "30", "NYC"])
            writer.writerow(["Bob", "25", "LA"])

        node = ReadCSVNode(node_id="test_read_csv")
        node.set_input_value("file_path", str(csv_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert len(result["data"]["rows"]) == 3  # Including header
        assert result["data"]["rows"][0] == ["Name", "Age", "City"]

    @pytest.mark.asyncio
    async def test_write_csv_node(self, execution_context, temp_dir):
        """Test WriteCSVNode writes CSV file."""
        from casare_rpa.nodes.file_system_nodes import WriteCSVNode

        csv_file = Path(temp_dir) / "output.csv"

        node = WriteCSVNode(node_id="test_write_csv")
        node.set_input_value("file_path", str(csv_file))
        node.set_input_value(
            "rows",
            [
                ["Name", "Age"],
                ["Alice", "30"],
                ["Bob", "25"],
            ],
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert csv_file.exists()

        # Verify content
        with open(csv_file, "r") as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) == 3
            assert rows[0] == ["Name", "Age"]


class TestFileSystemNodesIntegration:
    """Integration tests for file system nodes visual layer."""

    def test_read_file_visual_integration(self):
        """Test ReadFileNode logic-to-visual connection."""
        from casare_rpa.nodes.file_system_nodes import ReadFileNode
        from casare_rpa.presentation.canvas.visual_nodes.file_system import (
            VisualReadFileNode,
        )

        visual_node = VisualReadFileNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == ReadFileNode

        node = ReadFileNode(node_id="test_read")
        assert node.node_type == "ReadFileNode"

    def test_write_file_visual_integration(self):
        """Test WriteFileNode logic-to-visual connection."""
        from casare_rpa.nodes.file_system_nodes import WriteFileNode
        from casare_rpa.presentation.canvas.visual_nodes.file_system import (
            VisualWriteFileNode,
        )

        visual_node = VisualWriteFileNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == WriteFileNode

        node = WriteFileNode(node_id="test_write")
        assert node.node_type == "WriteFileNode"

    def test_list_files_visual_integration(self):
        """Test ListFilesNode logic-to-visual connection."""
        from casare_rpa.nodes.file_system_nodes import ListFilesNode
        from casare_rpa.presentation.canvas.visual_nodes.file_system import (
            VisualListFilesNode,
        )

        visual_node = VisualListFilesNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == ListFilesNode

        node = ListFilesNode(node_id="test_list")
        assert node.node_type == "ListFilesNode"

    def test_read_csv_visual_integration(self):
        """Test ReadCSVNode logic-to-visual connection."""
        from casare_rpa.nodes.file_system_nodes import ReadCSVNode
        from casare_rpa.presentation.canvas.visual_nodes.file_system import (
            VisualReadCSVNode,
        )

        visual_node = VisualReadCSVNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == ReadCSVNode

        node = ReadCSVNode(node_id="test_read_csv")
        assert node.node_type == "ReadCSVNode"
