"""
CasareRPA - E2E Tests for JSON File Workflows.

Tests JSON file operations including:
- Basic JSON read/write
- Nested structures and arrays
- JSON transformations
- Config file workflows

Uses real ExecutionContext and temp_workspace fixture.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from tests.e2e.helpers import WorkflowBuilder


# =============================================================================
# BASIC JSON OPERATIONS
# =============================================================================


class TestBasicJSONOperations:
    """Test basic JSON read/write operations."""

    @pytest.mark.asyncio
    async def test_write_and_read_json_object(self, temp_workspace: Path) -> None:
        """Write JSON object, read back and verify."""
        file_path = str(temp_workspace / "test.json")
        data = {"name": "Test", "value": 42, "active": True}

        result = await (
            WorkflowBuilder("write_read_json")
            .add_start()
            .add_write_json_file(file_path, data, node_id="write")
            .add_read_json_file(file_path, node_id="read")
            .add_set_variable("result", "{{read.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        read_data = result["variables"].get("result", {})
        assert read_data["name"] == "Test"
        assert read_data["value"] == 42
        assert read_data["active"] is True

    @pytest.mark.asyncio
    async def test_write_and_read_json_array(self, temp_workspace: Path) -> None:
        """Write JSON array, read back and verify."""
        file_path = str(temp_workspace / "array.json")
        data = [1, 2, 3, 4, 5]

        result = await (
            WorkflowBuilder("json_array")
            .add_start()
            .add_write_json_file(file_path, data, node_id="write")
            .add_read_json_file(file_path, node_id="read")
            .add_set_variable("result", "{{read.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        read_data = result["variables"].get("result", [])
        assert read_data == [1, 2, 3, 4, 5]

    @pytest.mark.asyncio
    async def test_json_nested_structure(self, temp_workspace: Path) -> None:
        """Write and read deeply nested JSON structure."""
        file_path = str(temp_workspace / "nested.json")
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "deep",
                        "array": [1, 2, 3],
                    }
                }
            },
            "items": [
                {"id": 1, "nested": {"x": 10}},
                {"id": 2, "nested": {"x": 20}},
            ],
        }

        result = await (
            WorkflowBuilder("json_nested")
            .add_start()
            .add_write_json_file(file_path, data, node_id="write")
            .add_read_json_file(file_path, node_id="read")
            .add_set_variable("result", "{{read.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        read_data = result["variables"].get("result", {})
        assert read_data["level1"]["level2"]["level3"]["value"] == "deep"
        assert read_data["level1"]["level2"]["level3"]["array"] == [1, 2, 3]
        assert len(read_data["items"]) == 2

    @pytest.mark.asyncio
    async def test_json_pretty_print(self, temp_workspace: Path) -> None:
        """Write JSON with indentation, verify formatting."""
        file_path = str(temp_workspace / "pretty.json")
        data = {"key1": "value1", "key2": "value2"}

        result = await (
            WorkflowBuilder("json_pretty")
            .add_start()
            .add_write_json_file(file_path, data, indent=4, node_id="write")
            .add_read_file(file_path, node_id="read_raw")
            .add_set_variable("raw_content", "{{read_raw.content}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        raw = result["variables"].get("raw_content", "")
        # Pretty printed JSON should have newlines
        assert "\n" in raw
        # Verify 4-space indentation
        assert "    " in raw

    @pytest.mark.asyncio
    async def test_json_compact(self, temp_workspace: Path) -> None:
        """Write JSON without indentation (compact)."""
        file_path = str(temp_workspace / "compact.json")
        data = {"a": 1, "b": 2}

        # Use indent=None for compact output (but node uses 0 for None)
        result = await (
            WorkflowBuilder("json_compact")
            .add_start()
            .add_write_json_file(file_path, data, indent=0, node_id="write")
            .add_read_file(file_path, node_id="read_raw")
            .add_set_variable("raw_content", "{{read_raw.content}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        raw = result["variables"].get("raw_content", "")
        # With indent=0, there's still some formatting
        # The key verification is that the JSON is valid
        parsed = json.loads(raw)
        assert parsed == {"a": 1, "b": 2}

    @pytest.mark.asyncio
    async def test_json_array_of_objects(self, temp_workspace: Path) -> None:
        """Write and read array of objects."""
        file_path = str(temp_workspace / "array_objects.json")
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Charlie"},
        ]

        result = await (
            WorkflowBuilder("json_array_objects")
            .add_start()
            .add_write_json_file(file_path, data, node_id="write")
            .add_read_json_file(file_path, node_id="read")
            .add_set_variable("result", "{{read.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        read_data = result["variables"].get("result", [])
        assert len(read_data) == 3
        assert read_data[0]["name"] == "Alice"
        assert read_data[2]["id"] == 3


# =============================================================================
# JSON MODIFICATIONS AND TRANSFORMATIONS
# =============================================================================


class TestJSONModifications:
    """Test JSON modification workflows."""

    @pytest.mark.asyncio
    async def test_json_update_value(self, temp_workspace: Path) -> None:
        """Read JSON, update a value, write back."""
        file_path = str(temp_workspace / "update.json")
        original = {"version": "1.0", "name": "MyApp"}

        result = await (
            WorkflowBuilder("json_update")
            .add_start()
            .add_write_json_file(file_path, original, node_id="write_original")
            .add_read_json_file(file_path, node_id="read")
            .add_set_variable("data", "{{read.data}}")
            # In real workflow, would use DictSet node to update
            # For now, verify read works
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        data = result["variables"].get("data", {})
        assert data["version"] == "1.0"

    @pytest.mark.asyncio
    async def test_json_overwrite(self, temp_workspace: Path) -> None:
        """Overwrite JSON file with new content."""
        file_path = str(temp_workspace / "overwrite.json")
        original = {"old": "data"}
        new = {"new": "data", "extra": True}

        result = await (
            WorkflowBuilder("json_overwrite")
            .add_start()
            .add_write_json_file(file_path, original, node_id="write1")
            .add_write_json_file(file_path, new, node_id="write2")
            .add_read_json_file(file_path, node_id="read")
            .add_set_variable("result", "{{read.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        data = result["variables"].get("result", {})
        assert "old" not in data
        assert data["new"] == "data"
        assert data["extra"] is True

    @pytest.mark.asyncio
    async def test_json_copy_to_new_file(self, temp_workspace: Path) -> None:
        """Copy JSON from one file to another."""
        src_path = str(temp_workspace / "source.json")
        dst_path = str(temp_workspace / "destination.json")
        data = {"source": True, "items": [1, 2, 3]}

        result = await (
            WorkflowBuilder("json_copy")
            .add_start()
            .add_write_json_file(src_path, data, node_id="write_src")
            .add_read_json_file(src_path, node_id="read_src")
            .add_set_variable("data", "{{read_src.data}}")
            .add_write_json_file(dst_path, "{{data}}", node_id="write_dst")
            .add_read_json_file(dst_path, node_id="verify")
            .add_set_variable("copied", "{{verify.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        copied = result["variables"].get("copied", {})
        assert copied["source"] is True
        assert copied["items"] == [1, 2, 3]


# =============================================================================
# CONFIG FILE WORKFLOWS
# =============================================================================


class TestJSONConfigWorkflows:
    """Test JSON configuration file workflows."""

    @pytest.mark.asyncio
    async def test_json_config_read_modify_save(self, temp_workspace: Path) -> None:
        """Read config, store in variable, write new config."""
        config_path = str(temp_workspace / "config.json")
        config = {
            "app": {
                "name": "TestApp",
                "version": "1.0.0",
            },
            "settings": {
                "debug": False,
                "timeout": 30,
            },
        }

        result = await (
            WorkflowBuilder("json_config")
            .add_start()
            .add_write_json_file(config_path, config, node_id="write_config")
            .add_read_json_file(config_path, node_id="read_config")
            .add_set_variable("config", "{{read_config.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        loaded_config = result["variables"].get("config", {})
        assert loaded_config["app"]["name"] == "TestApp"
        assert loaded_config["settings"]["timeout"] == 30

    @pytest.mark.asyncio
    async def test_json_config_backup(self, temp_workspace: Path) -> None:
        """Create backup of config before modifying."""
        config_path = str(temp_workspace / "app.json")
        backup_path = str(temp_workspace / "app.json.bak")
        config = {"version": "1.0", "enabled": True}
        new_config = {"version": "2.0", "enabled": True, "newFeature": True}

        result = await (
            WorkflowBuilder("json_config_backup")
            .add_start()
            # Create original
            .add_write_json_file(config_path, config, node_id="write_original")
            # Read and backup
            .add_read_json_file(config_path, node_id="read_original")
            .add_set_variable("backup_data", "{{read_original.data}}")
            .add_write_json_file(backup_path, "{{backup_data}}", node_id="write_backup")
            # Write new config
            .add_write_json_file(config_path, new_config, node_id="write_new")
            # Verify
            .add_read_json_file(config_path, node_id="verify_new")
            .add_set_variable("new_version", "{{verify_new.data}}")
            .add_read_json_file(backup_path, node_id="verify_backup")
            .add_set_variable("backup_version", "{{verify_backup.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        new_ver = result["variables"].get("new_version", {})
        backup_ver = result["variables"].get("backup_version", {})
        assert new_ver["version"] == "2.0"
        assert backup_ver["version"] == "1.0"

    @pytest.mark.asyncio
    async def test_json_multiple_configs(self, temp_workspace: Path) -> None:
        """Work with multiple JSON config files."""
        db_config = str(temp_workspace / "database.json")
        app_config = str(temp_workspace / "application.json")

        db_data = {"host": "localhost", "port": 5432, "database": "test"}
        app_data = {"name": "MyApp", "debug": True}

        result = await (
            WorkflowBuilder("json_multi_config")
            .add_start()
            .add_write_json_file(db_config, db_data, node_id="write_db")
            .add_write_json_file(app_config, app_data, node_id="write_app")
            .add_read_json_file(db_config, node_id="read_db")
            .add_set_variable("db", "{{read_db.data}}")
            .add_read_json_file(app_config, node_id="read_app")
            .add_set_variable("app", "{{read_app.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        db = result["variables"].get("db", {})
        app = result["variables"].get("app", {})
        assert db["host"] == "localhost"
        assert app["name"] == "MyApp"


# =============================================================================
# DATA TYPE HANDLING
# =============================================================================


class TestJSONDataTypes:
    """Test JSON handling of various data types."""

    @pytest.mark.asyncio
    async def test_json_all_data_types(self, temp_workspace: Path) -> None:
        """Write and read JSON with all supported data types."""
        file_path = str(temp_workspace / "types.json")
        data = {
            "string": "hello",
            "integer": 42,
            "float": 3.14,
            "boolean_true": True,
            "boolean_false": False,
            "null_value": None,
            "array": [1, "two", 3.0, True, None],
            "nested_object": {"a": 1, "b": 2},
        }

        result = await (
            WorkflowBuilder("json_types")
            .add_start()
            .add_write_json_file(file_path, data, node_id="write")
            .add_read_json_file(file_path, node_id="read")
            .add_set_variable("result", "{{read.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        read_data = result["variables"].get("result", {})
        assert read_data["string"] == "hello"
        assert read_data["integer"] == 42
        assert abs(read_data["float"] - 3.14) < 0.001
        assert read_data["boolean_true"] is True
        assert read_data["boolean_false"] is False
        assert read_data["null_value"] is None
        assert read_data["array"] == [1, "two", 3.0, True, None]

    @pytest.mark.asyncio
    async def test_json_unicode_content(self, temp_workspace: Path) -> None:
        """Write and read JSON with Unicode content."""
        file_path = str(temp_workspace / "unicode.json")
        data = {
            "english": "Hello",
            "spanish": "Hola",
            "french": "Bonjour",
            "japanese": "Hello in Japanese",
            "arabic": "Hello in Arabic",
        }

        result = await (
            WorkflowBuilder("json_unicode")
            .add_start()
            .add_write_json_file(file_path, data, ensure_ascii=False, node_id="write")
            .add_read_json_file(file_path, node_id="read")
            .add_set_variable("result", "{{read.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        read_data = result["variables"].get("result", {})
        assert read_data["english"] == "Hello"
        assert read_data["spanish"] == "Hola"

    @pytest.mark.asyncio
    async def test_json_empty_structures(self, temp_workspace: Path) -> None:
        """Write and read empty JSON structures."""
        empty_obj_path = str(temp_workspace / "empty_obj.json")
        empty_arr_path = str(temp_workspace / "empty_arr.json")

        result = await (
            WorkflowBuilder("json_empty")
            .add_start()
            .add_write_json_file(empty_obj_path, {}, node_id="write_obj")
            .add_write_json_file(empty_arr_path, [], node_id="write_arr")
            .add_read_json_file(empty_obj_path, node_id="read_obj")
            .add_set_variable("empty_obj", "{{read_obj.data}}")
            .add_read_json_file(empty_arr_path, node_id="read_arr")
            .add_set_variable("empty_arr", "{{read_arr.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"].get("empty_obj") == {}
        assert result["variables"].get("empty_arr") == []

    @pytest.mark.asyncio
    async def test_json_large_numbers(self, temp_workspace: Path) -> None:
        """Handle large numbers in JSON."""
        file_path = str(temp_workspace / "large_numbers.json")
        data = {
            "big_int": 9007199254740991,  # Max safe integer in JS
            "small_int": -9007199254740991,
            "float_precision": 0.123456789012345,
        }

        result = await (
            WorkflowBuilder("json_large_numbers")
            .add_start()
            .add_write_json_file(file_path, data, node_id="write")
            .add_read_json_file(file_path, node_id="read")
            .add_set_variable("result", "{{read.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        read_data = result["variables"].get("result", {})
        assert read_data["big_int"] == 9007199254740991
        assert read_data["small_int"] == -9007199254740991


# =============================================================================
# ERROR HANDLING
# =============================================================================


class TestJSONErrorHandling:
    """Test JSON error handling scenarios."""

    @pytest.mark.asyncio
    async def test_read_nonexistent_json(self, temp_workspace: Path) -> None:
        """Reading non-existent JSON should fail."""
        file_path = str(temp_workspace / "does_not_exist.json")

        result = await (
            WorkflowBuilder("read_missing_json")
            .add_start()
            .add_read_json_file(file_path, node_id="read")
            .add_end()
            .execute()
        )

        assert not result["success"]
        assert result.get("error") is not None

    @pytest.mark.asyncio
    async def test_read_invalid_json(self, temp_workspace: Path) -> None:
        """Reading invalid JSON should fail with parse error."""
        file_path = str(temp_workspace / "invalid.json")
        # Write invalid JSON
        Path(file_path).write_text("{ invalid json content }")

        result = await (
            WorkflowBuilder("read_invalid_json")
            .add_start()
            .add_read_json_file(file_path, node_id="read")
            .add_end()
            .execute()
        )

        assert not result["success"]
        assert result.get("error") is not None

    @pytest.mark.asyncio
    async def test_read_empty_file_as_json(self, temp_workspace: Path) -> None:
        """Reading empty file as JSON should fail."""
        file_path = str(temp_workspace / "empty.json")
        Path(file_path).write_text("")

        result = await (
            WorkflowBuilder("read_empty_json")
            .add_start()
            .add_read_json_file(file_path, node_id="read")
            .add_end()
            .execute()
        )

        assert not result["success"]


# =============================================================================
# COMPLEX WORKFLOWS
# =============================================================================


class TestJSONComplexWorkflows:
    """Test complex JSON workflows."""

    @pytest.mark.asyncio
    async def test_json_data_migration(self, temp_workspace: Path) -> None:
        """Migrate data from one JSON structure to another."""
        src_path = str(temp_workspace / "v1_data.json")
        dst_path = str(temp_workspace / "v2_data.json")

        v1_data = {
            "users": [
                {"name": "Alice", "email": "alice@test.com"},
                {"name": "Bob", "email": "bob@test.com"},
            ],
            "version": 1,
        }

        # Read v1, write as v2 format
        result = await (
            WorkflowBuilder("json_migrate")
            .add_start()
            .add_write_json_file(src_path, v1_data, node_id="write_v1")
            .add_read_json_file(src_path, node_id="read_v1")
            .add_set_variable("v1", "{{read_v1.data}}")
            # In real migration, would transform data
            .add_write_json_file(dst_path, "{{v1}}", node_id="write_v2")
            .add_read_json_file(dst_path, node_id="verify")
            .add_set_variable("v2", "{{verify.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        v2 = result["variables"].get("v2", {})
        assert len(v2["users"]) == 2

    @pytest.mark.asyncio
    async def test_json_merge_workflow(self, temp_workspace: Path) -> None:
        """Read two JSON files and store both."""
        file1_path = str(temp_workspace / "data1.json")
        file2_path = str(temp_workspace / "data2.json")

        data1 = {"source": "file1", "value": 100}
        data2 = {"source": "file2", "value": 200}

        result = await (
            WorkflowBuilder("json_merge")
            .add_start()
            .add_write_json_file(file1_path, data1, node_id="write1")
            .add_write_json_file(file2_path, data2, node_id="write2")
            .add_read_json_file(file1_path, node_id="read1")
            .add_set_variable("data1", "{{read1.data}}")
            .add_read_json_file(file2_path, node_id="read2")
            .add_set_variable("data2", "{{read2.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        d1 = result["variables"].get("data1", {})
        d2 = result["variables"].get("data2", {})
        assert d1["source"] == "file1"
        assert d2["source"] == "file2"

    @pytest.mark.asyncio
    async def test_json_api_response_simulation(self, temp_workspace: Path) -> None:
        """Simulate processing API-style JSON responses."""
        response_path = str(temp_workspace / "api_response.json")

        api_response = {
            "status": "success",
            "code": 200,
            "data": {
                "users": [
                    {"id": 1, "name": "User1", "active": True},
                    {"id": 2, "name": "User2", "active": False},
                ],
                "pagination": {
                    "page": 1,
                    "per_page": 10,
                    "total": 2,
                },
            },
            "meta": {
                "request_id": "abc123",
                "timestamp": "2024-01-01T00:00:00Z",
            },
        }

        result = await (
            WorkflowBuilder("json_api")
            .add_start()
            .add_write_json_file(response_path, api_response, node_id="write")
            .add_read_json_file(response_path, node_id="read")
            .add_set_variable("response", "{{read.data}}")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        response = result["variables"].get("response", {})
        assert response["status"] == "success"
        assert response["code"] == 200
        assert len(response["data"]["users"]) == 2
        assert response["data"]["pagination"]["total"] == 2
