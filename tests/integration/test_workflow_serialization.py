"""
Integration tests for Workflow Serialization/Deserialization.

Tests the complete workflow save/load roundtrip using real serializers
and file I/O (no mocks).
"""

from pathlib import Path

import orjson
import pytest

from casare_rpa.presentation.canvas.serialization import write_workflow_file
from tests.integration.conftest import create_sample_workflow_data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_workflow_save_to_file(
    sandbox_config: dict,
    sample_workflow: dict,
):
    """Test saving workflow data to disk via write_workflow_file."""
    # Arrange
    target_path = sandbox_config["workflows_dir"] / "test_save.json"

    # Act: Write workflow to disk
    result_path = write_workflow_file(target_path, sample_workflow)

    # Assert: File was created
    assert result_path.exists()
    assert result_path == target_path

    # Assert: JSON is valid and contains expected data
    content = orjson.loads(result_path.read_bytes())
    assert content["metadata"]["name"] == "TestWorkflow"
    assert "nodes" in content
    assert "connections" in content
    assert len(content["nodes"]) == 2
    assert content["nodes"]["node_start"]["node_type"] == "StartNode"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_workflow_roundtrip_preserves_data(
    sandbox_config: dict,
    sample_workflow: dict,
):
    """Test that save/load roundtrip preserves all workflow data."""
    # Arrange: Save workflow
    workflow_path = sandbox_config["workflows_dir"] / "roundtrip_test.json"
    write_workflow_file(workflow_path, sample_workflow)

    # Act: Load workflow back
    loaded_data = orjson.loads(workflow_path.read_bytes())

    # Assert: Metadata preserved
    assert loaded_data["metadata"] == sample_workflow["metadata"]

    # Assert: Nodes preserved
    assert len(loaded_data["nodes"]) == len(sample_workflow["nodes"])
    for node_id, node_data in sample_workflow["nodes"].items():
        assert node_id in loaded_data["nodes"]
        assert loaded_data["nodes"][node_id]["node_type"] == node_data["node_type"]
        assert loaded_data["nodes"][node_id]["config"] == node_data["config"]

    # Assert: Connections preserved
    assert len(loaded_data["connections"]) == len(sample_workflow["connections"])
    assert loaded_data["connections"][0]["source_node"] == "node_start"
    assert loaded_data["connections"][0]["target_node"] == "node_log"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_workflow_save_creates_parent_directories(
    sandbox_config: dict,
    sample_workflow: dict,
):
    """Test that save creates parent directories if they don't exist."""
    # Arrange: Path with non-existent subdirectories
    nested_path = sandbox_config["workflows_dir"] / "nested" / "folder" / "workflow.json"

    # Act: Save to nested path
    result_path = write_workflow_file(nested_path, sample_workflow)

    # Assert: File exists at nested path
    assert result_path.exists()
    assert result_path.parent.name == "folder"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_workflow_json_format_is_valid(
    sandbox_config: dict,
    sample_workflow: dict,
):
    """Test that saved workflow JSON is properly formatted and readable."""
    # Arrange: Save workflow
    workflow_path = sandbox_config["workflows_dir"] / "format_test.json"
    write_workflow_file(workflow_path, sample_workflow)

    # Act: Read raw bytes
    raw_content = workflow_path.read_bytes()

    # Assert: Valid JSON (orjson can parse it back)
    parsed = orjson.loads(raw_content)
    assert parsed is not None

    # Assert: Contains indentation (OPT_INDENT_2)
    # Note: orjson uses 2-space indentation
    text_content = raw_content.decode("utf-8")
    assert "  " in text_content  # Has indentation
    assert "{\n" in text_content or "{\r" in text_content  # Has newlines


@pytest.mark.integration
@pytest.mark.asyncio
async def test_workflow_with_complex_node_configs(
    sandbox_config: dict,
):
    """Test saving workflow with various node configuration types."""
    # Arrange: Workflow with diverse node types and configs
    complex_workflow = {
        "metadata": {
            "name": "ComplexWorkflow",
            "description": "Testing various node types",
            "version": "1.0.0",
        },
        "nodes": {
            "start": {
                "node_id": "start",
                "node_type": "StartNode",
                "config": {},
                "position": {"x": 0, "y": 0},
            },
            "set_var": {
                "node_id": "set_var",
                "node_type": "SetVariableNode",
                "config": {
                    "variable_name": "counter",
                    "value": 42,
                    "variable_scope": "workflow",
                },
                "position": {"x": 200, "y": 0},
            },
            "http_request": {
                "node_id": "http_request",
                "node_type": "HttpRequestNode",
                "config": {
                    "url": "https://api.example.com/test",
                    "method": "POST",
                    "headers": {"Content-Type": "application/json"},
                    "body": '{"test": true}',
                    "timeout": 30000,
                },
                "position": {"x": 400, "y": 0},
            },
            "log": {
                "node_id": "log",
                "node_type": "LogNode",
                "config": {
                    "message": "Done!",
                    "log_level": "info",
                },
                "position": {"x": 600, "y": 0},
            },
        },
        "connections": [
            {
                "source_node": "start",
                "source_port": "exec_out",
                "target_node": "set_var",
                "target_port": "exec_in",
            },
            {
                "source_node": "set_var",
                "source_port": "exec_out",
                "target_node": "http_request",
                "target_port": "exec_in",
            },
            {
                "source_node": "http_request",
                "source_port": "exec_out",
                "target_node": "log",
                "target_port": "exec_in",
            },
        ],
        "variables": {
            "workflow_var_1": "string_value",
            "workflow_var_2": 123,
            "workflow_var_3": True,
            "workflow_var_4": None,
        },
        "frames": [],
        "settings": {
            "timeout": 60,
            "stop_on_error": False,
        },
    }

    workflow_path = sandbox_config["workflows_dir"] / "complex_workflow.json"

    # Act: Save complex workflow
    write_workflow_file(workflow_path, complex_workflow)

    # Act: Load it back
    loaded = orjson.loads(workflow_path.read_bytes())

    # Assert: All data types preserved
    assert loaded["variables"]["workflow_var_1"] == "string_value"
    assert loaded["variables"]["workflow_var_2"] == 123
    assert loaded["variables"]["workflow_var_3"] is True
    assert loaded["variables"]["workflow_var_4"] is None

    # Assert: Nested configs preserved
    assert (
        loaded["nodes"]["http_request"]["config"]["headers"]["Content-Type"] == "application/json"
    )

    # Assert: Settings preserved
    assert loaded["settings"]["timeout"] == 60
    assert loaded["settings"]["stop_on_error"] is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_workflow_unicode_and_special_chars(
    sandbox_config: dict,
):
    """Test that workflow handles Unicode and special characters correctly."""
    # Arrange: Workflow with Unicode content
    unicode_workflow = {
        "metadata": {
            "name": "Unicode测试工作流",
            "description": "Testing emoji 🚀 and unicode: café, naïve, 日本語",
            "version": "1.0.0",
        },
        "nodes": {
            "log_emoji": {
                "node_id": "log_emoji",
                "node_type": "LogNode",
                "config": {
                    "message": "Hello 🌍 World! 🎉 Test: café, naïve, Привет",
                },
                "position": {"x": 0, "y": 0},
            },
        },
        "connections": [],
        "variables": {
            "unicode_var": "日本語 中文 한국어 Ελληνικά",
            "emoji_var": "😀 😃 😄 😁 🎉 🚀",
        },
        "frames": [],
        "settings": {},
    }

    workflow_path = sandbox_config["workflows_dir"] / "unicode_test.json"

    # Act: Save and load
    write_workflow_file(workflow_path, unicode_workflow)
    loaded = orjson.loads(workflow_path.read_bytes())

    # Assert: Unicode preserved
    assert loaded["metadata"]["name"] == "Unicode测试工作流"
    assert "🚀" in loaded["metadata"]["description"]
    assert loaded["variables"]["unicode_var"] == "日本語 中文 한국어 Ελληνικά"
    assert "😀" in loaded["variables"]["emoji_var"]
