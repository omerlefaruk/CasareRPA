"""
Tests for StructuredDataSuperNode.

This test suite covers all 7 structured data operations:
- Read CSV, Write CSV
- Read JSON, Write JSON
- Zip Files, Unzip Files
- Image Convert

Test Philosophy:
- Happy path: Normal operation with valid inputs
- Sad path: Expected failures (file not found, invalid format)
- Edge cases: Boundary conditions (empty data, special characters)

Run: pytest tests/nodes/file/test_structured_data_super_node.py -v
"""

import json
import os
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from casare_rpa.nodes.file.super_node import (
    StructuredDataSuperNode,
    StructuredDataAction,
    STRUCTURED_DATA_PORT_SCHEMA,
)
from casare_rpa.nodes.file.file_security import PathSecurityError


def setup_action_ports(node: StructuredDataSuperNode, action: str) -> None:
    """
    Setup output ports for a specific action.

    In production, the visual layer handles dynamic port management.
    For testing, we manually add the required ports.
    """
    config = STRUCTURED_DATA_PORT_SCHEMA.get_config(action)
    if config:
        for port_def in config.outputs:
            if port_def.name not in node.output_ports:
                node.add_output_port(port_def.name, port_def.data_type)
        for port_def in config.inputs:
            if port_def.name not in node.input_ports:
                node.add_input_port(port_def.name, port_def.data_type)


# =============================================================================
# StructuredDataSuperNode Instantiation Tests
# =============================================================================


class TestStructuredDataSuperNodeInstantiation:
    """Test node creation and configuration."""

    def test_create_node_with_default_config(self) -> None:
        """Test creating node with default configuration."""
        node = StructuredDataSuperNode("test_node")
        assert node.node_id == "test_node"
        assert node.node_type == "StructuredDataSuperNode"
        assert node.name == "Structured Data"

    def test_create_node_with_custom_name(self) -> None:
        """Test creating node with custom name."""
        node = StructuredDataSuperNode("test_node", name="Data Processor")
        assert node.name == "Data Processor"

    def test_create_node_with_action_config(self) -> None:
        """Test creating node with specific action."""
        node = StructuredDataSuperNode(
            "test_node", config={"action": StructuredDataAction.READ_JSON.value}
        )
        assert node.get_parameter("action") == "Read JSON"

    def test_node_has_exec_ports(self) -> None:
        """Test that node has exec input/output ports."""
        node = StructuredDataSuperNode("test_node")
        assert "exec_in" in node.input_ports
        assert "exec_out" in node.output_ports

    def test_node_default_ports_for_read_csv(self) -> None:
        """Test default ports match Read CSV action."""
        node = StructuredDataSuperNode("test_node")
        assert "file_path" in node.input_ports
        assert "data" in node.output_ports
        assert "headers" in node.output_ports
        assert "row_count" in node.output_ports
        assert "success" in node.output_ports

    def test_node_ports_for_image_convert_init(self) -> None:
        """Test initializing node with Image Convert action sets correct ports."""
        node = StructuredDataSuperNode(
            "test_convert", config={"action": StructuredDataAction.IMAGE_CONVERT.value}
        )
        assert "source_path" in node.input_ports
        assert "output_path" in node.output_ports
        # Should NOT have Read CSV ports
        assert "data" not in node.output_ports


# =============================================================================
# Read CSV Action Tests
# =============================================================================


class TestReadCSVAction:
    """Tests for Read CSV action."""

    @pytest.mark.asyncio
    async def test_read_csv_success(
        self, execution_context, temp_csv_file: Path
    ) -> None:
        """SUCCESS: Read existing CSV file."""
        node = StructuredDataSuperNode(
            "test_read_csv",
            config={
                "action": StructuredDataAction.READ_CSV.value,
                "file_path": str(temp_csv_file),
                "has_header": True,
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        data = node.get_output_value("data")
        headers = node.get_output_value("headers")

        assert headers == ["name", "age", "city"]
        assert len(data) == 3
        # With has_header=True, data is returned as dicts keyed by header
        assert data[0]["name"] == "Alice"
        assert data[0]["age"] == "30"
        assert data[0]["city"] == "New York"

    @pytest.mark.asyncio
    async def test_read_csv_without_header(
        self, execution_context, tmp_path: Path
    ) -> None:
        """SUCCESS: Read CSV without headers."""
        csv_file = tmp_path / "no_header.csv"
        csv_file.write_text("A,B,C\nD,E,F\n")

        node = StructuredDataSuperNode(
            "test_read_csv",
            config={
                "action": StructuredDataAction.READ_CSV.value,
                "file_path": str(csv_file),
                "has_header": False,
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        data = node.get_output_value("data")
        # First row should be in data, not headers - returned as list without header
        assert data[0] == ["A", "B", "C"]

    @pytest.mark.asyncio
    async def test_read_csv_custom_delimiter(
        self, execution_context, tmp_path: Path
    ) -> None:
        """SUCCESS: Read CSV with custom delimiter."""
        csv_file = tmp_path / "semicolon.csv"
        csv_file.write_text("name;age;city\nBob;25;Boston\n")

        node = StructuredDataSuperNode(
            "test_read_csv",
            config={
                "action": StructuredDataAction.READ_CSV.value,
                "file_path": str(csv_file),
                "delimiter": ";",
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        headers = node.get_output_value("headers")
        assert headers == ["name", "age", "city"]

    @pytest.mark.asyncio
    async def test_read_csv_file_not_found(
        self, execution_context, tmp_path: Path
    ) -> None:
        """SAD PATH: CSV file does not exist."""
        non_existent = tmp_path / "missing.csv"

        node = StructuredDataSuperNode(
            "test_read_csv",
            config={
                "action": StructuredDataAction.READ_CSV.value,
                "file_path": str(non_existent),
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_read_csv_max_rows(
        self, execution_context, temp_csv_file: Path
    ) -> None:
        """EDGE CASE: Limit number of rows read."""
        node = StructuredDataSuperNode(
            "test_read_csv",
            config={
                "action": StructuredDataAction.READ_CSV.value,
                "file_path": str(temp_csv_file),
                "max_rows": 2,
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        data = node.get_output_value("data")
        assert len(data) == 2


# =============================================================================
# Write CSV Action Tests
# =============================================================================


class TestWriteCSVAction:
    """Tests for Write CSV action."""

    @pytest.mark.asyncio
    async def test_write_csv_success(self, execution_context, tmp_path: Path) -> None:
        """SUCCESS: Write data to CSV file."""
        output_file = tmp_path / "output.csv"
        test_data = [
            ["Alice", "30"],
            ["Bob", "25"],
        ]

        node = StructuredDataSuperNode(
            "test_write_csv",
            config={
                "action": StructuredDataAction.WRITE_CSV.value,
                "file_path": str(output_file),
                "data": test_data,
                "headers": ["name", "age"],
                "write_header": True,
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, StructuredDataAction.WRITE_CSV.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert output_file.exists()
        content = output_file.read_text()
        assert "name,age" in content
        assert "Alice,30" in content

    @pytest.mark.asyncio
    async def test_write_csv_without_header(
        self, execution_context, tmp_path: Path
    ) -> None:
        """SUCCESS: Write CSV without headers."""
        output_file = tmp_path / "no_header.csv"
        test_data = [["A", "B"], ["C", "D"]]

        node = StructuredDataSuperNode(
            "test_write_csv",
            config={
                "action": StructuredDataAction.WRITE_CSV.value,
                "file_path": str(output_file),
                "data": test_data,
                "write_header": False,
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, StructuredDataAction.WRITE_CSV.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        content = output_file.read_text()
        lines = content.strip().split("\n")
        assert lines[0] == "A,B"


# =============================================================================
# Read JSON Action Tests
# =============================================================================


class TestReadJSONAction:
    """Tests for Read JSON action."""

    @pytest.mark.asyncio
    async def test_read_json_success(
        self, execution_context, temp_json_file: Path
    ) -> None:
        """SUCCESS: Read existing JSON file."""
        node = StructuredDataSuperNode(
            "test_read_json",
            config={
                "action": StructuredDataAction.READ_JSON.value,
                "file_path": str(temp_json_file),
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        data = node.get_output_value("data")
        assert data["name"] == "Test"
        assert data["items"] == [1, 2, 3]
        assert data["nested"]["key"] == "value"

    @pytest.mark.asyncio
    async def test_read_json_array(self, execution_context, tmp_path: Path) -> None:
        """SUCCESS: Read JSON array."""
        json_file = tmp_path / "array.json"
        json_file.write_text('[1, 2, 3, "four"]')

        node = StructuredDataSuperNode(
            "test_read_json",
            config={
                "action": StructuredDataAction.READ_JSON.value,
                "file_path": str(json_file),
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        data = node.get_output_value("data")
        assert data == [1, 2, 3, "four"]

    @pytest.mark.asyncio
    async def test_read_json_file_not_found(
        self, execution_context, tmp_path: Path
    ) -> None:
        """SAD PATH: JSON file does not exist."""
        non_existent = tmp_path / "missing.json"

        node = StructuredDataSuperNode(
            "test_read_json",
            config={
                "action": StructuredDataAction.READ_JSON.value,
                "file_path": str(non_existent),
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "not found" in result["error"].lower()


# =============================================================================
# Write JSON Action Tests
# =============================================================================


class TestWriteJSONAction:
    """Tests for Write JSON action."""

    @pytest.mark.asyncio
    async def test_write_json_success(self, execution_context, tmp_path: Path) -> None:
        """SUCCESS: Write data to JSON file."""
        output_file = tmp_path / "output.json"
        test_data = {"name": "Test", "value": 42}

        node = StructuredDataSuperNode(
            "test_write_json",
            config={
                "action": StructuredDataAction.WRITE_JSON.value,
                "file_path": str(output_file),
                "data": test_data,
                "indent": 2,
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, StructuredDataAction.WRITE_JSON.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert output_file.exists()
        written_data = json.loads(output_file.read_text())
        assert written_data == test_data

    @pytest.mark.asyncio
    async def test_write_json_array(self, execution_context, tmp_path: Path) -> None:
        """SUCCESS: Write array to JSON file."""
        output_file = tmp_path / "array.json"
        test_data = [1, 2, 3, {"key": "value"}]

        node = StructuredDataSuperNode(
            "test_write_json",
            config={
                "action": StructuredDataAction.WRITE_JSON.value,
                "file_path": str(output_file),
                "data": test_data,
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, StructuredDataAction.WRITE_JSON.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        written_data = json.loads(output_file.read_text())
        assert written_data == test_data


# =============================================================================
# Zip Files Action Tests
# =============================================================================


class TestZipFilesAction:
    """Tests for Zip Files action."""

    @pytest.mark.asyncio
    async def test_zip_files_success(
        self, execution_context, temp_directory: Path, tmp_path: Path
    ) -> None:
        """SUCCESS: Create ZIP archive from directory."""
        zip_file = tmp_path / "archive.zip"

        node = StructuredDataSuperNode(
            "test_zip",
            config={
                "action": StructuredDataAction.ZIP.value,
                "zip_path": str(zip_file),
                "source_path": str(temp_directory),
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, StructuredDataAction.ZIP.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert zip_file.exists()
        assert node.get_output_value("file_count") >= 3

        # Verify ZIP contents
        with zipfile.ZipFile(zip_file, "r") as zf:
            names = zf.namelist()
            assert any("file1.txt" in n for n in names)

    @pytest.mark.asyncio
    async def test_zip_from_glob_pattern(
        self, execution_context, temp_directory: Path, tmp_path: Path
    ) -> None:
        """SUCCESS: Create ZIP from glob pattern."""
        zip_file = tmp_path / "txt_only.zip"

        node = StructuredDataSuperNode(
            "test_zip",
            config={
                "action": StructuredDataAction.ZIP.value,
                "zip_path": str(zip_file),
                "source_path": str(temp_directory / "*.txt"),
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, StructuredDataAction.ZIP.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        with zipfile.ZipFile(zip_file, "r") as zf:
            names = zf.namelist()
            # Should only contain .txt files
            assert all(n.endswith(".txt") for n in names)

    @pytest.mark.asyncio
    async def test_zip_no_files_error(self, execution_context, tmp_path: Path) -> None:
        """SAD PATH: No files to zip."""
        zip_file = tmp_path / "empty.zip"

        node = StructuredDataSuperNode(
            "test_zip",
            config={
                "action": StructuredDataAction.ZIP.value,
                "zip_path": str(zip_file),
                # No source_path or files
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, StructuredDataAction.ZIP.value)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "no files" in result["error"].lower()


# =============================================================================
# Unzip Files Action Tests
# =============================================================================


class TestUnzipFilesAction:
    """Tests for Unzip Files action."""

    @pytest.mark.asyncio
    async def test_unzip_files_success(
        self, execution_context, temp_zip_file: Path, tmp_path: Path
    ) -> None:
        """SUCCESS: Extract ZIP archive."""
        extract_dir = tmp_path / "extracted"

        node = StructuredDataSuperNode(
            "test_unzip",
            config={
                "action": StructuredDataAction.UNZIP.value,
                "zip_path": str(temp_zip_file),
                "extract_to": str(extract_dir),
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, StructuredDataAction.UNZIP.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert extract_dir.exists()
        files = node.get_output_value("files")
        assert len(files) >= 3

    @pytest.mark.asyncio
    async def test_unzip_file_not_found(
        self, execution_context, tmp_path: Path
    ) -> None:
        """SAD PATH: ZIP file does not exist."""
        non_existent = tmp_path / "missing.zip"
        extract_dir = tmp_path / "extracted"

        node = StructuredDataSuperNode(
            "test_unzip",
            config={
                "action": StructuredDataAction.UNZIP.value,
                "zip_path": str(non_existent),
                "extract_to": str(extract_dir),
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_unzip_zip_slip_protection(
        self, execution_context, tmp_path: Path
    ) -> None:
        """SECURITY: Block Zip Slip attack."""
        # Create a malicious ZIP with path traversal
        malicious_zip = tmp_path / "malicious.zip"
        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir()

        with zipfile.ZipFile(malicious_zip, "w") as zf:
            # This entry tries to escape the extraction directory
            info = zipfile.ZipInfo("../../../evil.txt")
            zf.writestr(info, "malicious content")

        node = StructuredDataSuperNode(
            "test_unzip",
            config={
                "action": StructuredDataAction.UNZIP.value,
                "zip_path": str(malicious_zip),
                "extract_to": str(extract_dir),
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(execution_context)

        # Should fail due to Zip Slip detection
        assert result["success"] is False
        assert (
            "zip slip" in result["error"].lower()
            or "outside" in result["error"].lower()
        )


# =============================================================================
# Image Convert Action Tests
# =============================================================================


class TestImageConvertAction:
    """Tests for Image Convert action."""

    @pytest.mark.asyncio
    async def test_image_convert_png_to_jpeg(
        self, execution_context, temp_image_file: Path, tmp_path: Path
    ) -> None:
        """SUCCESS: Convert PNG to JPEG."""
        output_file = tmp_path / "converted.jpg"

        node = StructuredDataSuperNode(
            "test_convert",
            config={
                "action": StructuredDataAction.IMAGE_CONVERT.value,
                "source_path": str(temp_image_file),
                "output_path": str(output_file),
                "output_format": "JPEG",
                "quality": 85,
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, StructuredDataAction.IMAGE_CONVERT.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert output_file.exists()
        assert node.get_output_value("format") == "JPEG"

    @pytest.mark.asyncio
    async def test_image_convert_scale_percent(
        self, execution_context, tmp_path: Path
    ) -> None:
        """SUCCESS: scale_percent resizes output dimensions."""
        from PIL import Image

        source_file = tmp_path / "big.png"
        Image.new("RGB", (40, 20), color="red").save(source_file, "PNG")
        output_file = tmp_path / "small.jpg"

        node = StructuredDataSuperNode(
            "test_convert",
            config={
                "action": StructuredDataAction.IMAGE_CONVERT.value,
                "source_path": str(source_file),
                "output_path": str(output_file),
                "output_format": "JPEG",
                "scale_percent": "50%",
                "overwrite": True,
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, StructuredDataAction.IMAGE_CONVERT.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        with Image.open(output_file) as img:
            assert img.size == (20, 10)

    @pytest.mark.asyncio
    async def test_image_convert_auto_output_path(
        self, execution_context, temp_image_file: Path
    ) -> None:
        """SUCCESS: Auto-generate output path."""
        node = StructuredDataSuperNode(
            "test_convert",
            config={
                "action": StructuredDataAction.IMAGE_CONVERT.value,
                "source_path": str(temp_image_file),
                "output_format": "WEBP",
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, StructuredDataAction.IMAGE_CONVERT.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        output_path = node.get_output_value("output_path")
        assert output_path.endswith(".webp")

    @pytest.mark.asyncio
    async def test_image_convert_output_directory(
        self, execution_context, temp_image_file: Path, tmp_path: Path
    ) -> None:
        """SUCCESS: output_path can be a directory (with trailing separator)."""
        output_dir = tmp_path / "converted_images"

        node = StructuredDataSuperNode(
            "test_convert",
            config={
                "action": StructuredDataAction.IMAGE_CONVERT.value,
                "source_path": str(temp_image_file),
                "output_path": f"{output_dir}{os.sep}",
                "output_format": "JPEG",
                "overwrite": True,
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, StructuredDataAction.IMAGE_CONVERT.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        expected = output_dir / f"{temp_image_file.stem}.jpg"
        assert expected.exists()
        assert node.get_output_value("output_path") == str(expected)

    @pytest.mark.asyncio
    async def test_image_convert_batch_folder(
        self, execution_context, tmp_path: Path
    ) -> None:
        """SUCCESS: Convert all images in a folder."""
        from PIL import Image

        source_dir = tmp_path / "images"
        source_dir.mkdir()
        Image.new("RGB", (10, 10), color="red").save(source_dir / "a.png", "PNG")
        Image.new("RGB", (10, 10), color="blue").save(source_dir / "b.png", "PNG")

        node = StructuredDataSuperNode(
            "test_convert",
            config={
                "action": StructuredDataAction.IMAGE_CONVERT.value,
                "source_path": str(source_dir),
                "output_format": "JPEG",
                "overwrite": True,
                "allow_dangerous_paths": True,
            },
        )
        setup_action_ports(node, StructuredDataAction.IMAGE_CONVERT.value)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("file_count") == 2
        files = node.get_output_value("files")
        assert isinstance(files, list)
        assert len(files) == 2

    @pytest.mark.asyncio
    async def test_image_convert_unsupported_format(
        self, execution_context, temp_image_file: Path
    ) -> None:
        """SAD PATH: Unsupported output format."""
        node = StructuredDataSuperNode(
            "test_convert",
            config={
                "action": StructuredDataAction.IMAGE_CONVERT.value,
                "source_path": str(temp_image_file),
                "output_format": "TIFF",  # Not in supported list
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "unsupported" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_image_convert_file_not_found(
        self, execution_context, tmp_path: Path
    ) -> None:
        """SAD PATH: Source image does not exist."""
        non_existent = tmp_path / "missing.png"

        node = StructuredDataSuperNode(
            "test_convert",
            config={
                "action": StructuredDataAction.IMAGE_CONVERT.value,
                "source_path": str(non_existent),
                "output_format": "JPEG",
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_image_convert_destination_exists_no_overwrite(
        self, execution_context, temp_image_file: Path, tmp_path: Path
    ) -> None:
        """SAD PATH: Destination exists and overwrite=False."""
        output_file = tmp_path / "existing.jpg"
        output_file.write_bytes(b"existing content")

        node = StructuredDataSuperNode(
            "test_convert",
            config={
                "action": StructuredDataAction.IMAGE_CONVERT.value,
                "source_path": str(temp_image_file),
                "output_path": str(output_file),
                "output_format": "JPEG",
                "overwrite": False,
                "allow_dangerous_paths": True,
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "exists" in result["error"].lower()


# =============================================================================
# Port Schema Tests
# =============================================================================


class TestStructuredDataPortSchema:
    """Tests for dynamic port schema configuration."""

    def test_port_schema_has_all_actions(self) -> None:
        """Verify all actions have port configurations."""
        for action in StructuredDataAction:
            config = STRUCTURED_DATA_PORT_SCHEMA.get_config(action.value)
            assert config is not None, f"Missing port config for {action.value}"

    def test_read_csv_action_ports(self) -> None:
        """Verify Read CSV action port configuration."""
        config = STRUCTURED_DATA_PORT_SCHEMA.get_config(
            StructuredDataAction.READ_CSV.value
        )
        input_names = [p.name for p in config.inputs]
        output_names = [p.name for p in config.outputs]

        assert "file_path" in input_names
        assert "data" in output_names
        assert "headers" in output_names
        assert "row_count" in output_names
        assert "success" in output_names

    def test_zip_action_ports(self) -> None:
        """Verify Zip action port configuration."""
        config = STRUCTURED_DATA_PORT_SCHEMA.get_config(StructuredDataAction.ZIP.value)
        input_names = [p.name for p in config.inputs]
        output_names = [p.name for p in config.outputs]

        assert "zip_path" in input_names
        assert "source_path" in input_names
        assert "file_count" in output_names
        assert "success" in output_names

    def test_image_convert_action_ports(self) -> None:
        """Verify Image Convert action port configuration."""
        config = STRUCTURED_DATA_PORT_SCHEMA.get_config(
            StructuredDataAction.IMAGE_CONVERT.value
        )
        input_names = [p.name for p in config.inputs]
        output_names = [p.name for p in config.outputs]

        assert "source_path" in input_names
        assert "output_path" in output_names
        assert "files" in output_names
        assert "file_count" in output_names
        assert "format" in output_names
        assert "success" in output_names
