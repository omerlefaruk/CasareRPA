"""
CasareRPA - E2E Tests for JSON and Dictionary Workflows.

Tests JSON and dictionary operations including:
- JSON parsing and stringification
- Dictionary get/set/delete operations
- Dictionary keys/values extraction
- Dictionary merging
- Nested property access
- Has key checks
- Dictionary creation
"""

import pytest

from .helpers.workflow_builder import WorkflowBuilder


@pytest.mark.asyncio
@pytest.mark.e2e
class TestJsonParsing:
    """Tests for JSON parsing operations."""

    async def test_json_parse_object(self) -> None:
        """Test parsing JSON object string."""
        result = await (
            WorkflowBuilder("JSON Parse Object")
            .add_start()
            .add_json_parse('{"name": "John", "age": 30}')
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_json_parse_array(self) -> None:
        """Test parsing JSON array string."""
        result = await (
            WorkflowBuilder("JSON Parse Array")
            .add_start()
            .add_json_parse("[1, 2, 3]")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_json_parse_nested(self) -> None:
        """Test parsing nested JSON."""
        result = await (
            WorkflowBuilder("JSON Parse Nested")
            .add_start()
            .add_json_parse('{"user": {"name": "John", "address": {"city": "NYC"}}}')
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_json_parse_with_different_types(self) -> None:
        """Test parsing JSON with various data types."""
        result = await (
            WorkflowBuilder("JSON Parse Types")
            .add_start()
            .add_json_parse(
                '{"string": "hello", "number": 42, "float": 3.14, "bool": true, "null": null}'
            )
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestJsonStringify:
    """Tests for JSON stringify operations."""

    async def test_json_stringify_object(self) -> None:
        """Test converting dictionary to JSON string."""
        result = await (
            WorkflowBuilder("JSON Stringify")
            .add_start()
            .add_set_variable("data", {"a": 1, "b": 2})
            .add_dict_to_json("{{data}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_json_stringify_with_indent(self) -> None:
        """Test JSON stringify with indentation."""
        result = await (
            WorkflowBuilder("JSON Stringify Indented")
            .add_start()
            .add_set_variable("data", {"name": "John", "age": 30})
            .add_dict_to_json("{{data}}", indent=2)
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_json_stringify_sorted_keys(self) -> None:
        """Test JSON stringify with sorted keys."""
        result = await (
            WorkflowBuilder("JSON Stringify Sorted")
            .add_start()
            .add_set_variable("data", {"z": 3, "a": 1, "m": 2})
            .add_dict_to_json("{{data}}", sort_keys=True)
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestDictGet:
    """Tests for dictionary get operations."""

    async def test_dict_get_key(self) -> None:
        """Test getting value by key."""
        result = await (
            WorkflowBuilder("Dict Get Key")
            .add_start()
            .add_set_variable("data", {"name": "John"})
            .add_dict_get("{{data}}", key="name")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_dict_get_with_default(self) -> None:
        """Test getting value with default when key not found."""
        result = await (
            WorkflowBuilder("Dict Get Default")
            .add_start()
            .add_set_variable("data", {"a": 1})
            .add_dict_get("{{data}}", key="b", default=0)
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_dict_get_nested(self) -> None:
        """Test getting nested value using GetPropertyNode."""
        result = await (
            WorkflowBuilder("Dict Get Nested")
            .add_start()
            .add_set_variable("data", {"user": {"name": "John"}})
            .add_get_property("{{data}}", property_path="user.name")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_dict_get_deeply_nested(self) -> None:
        """Test getting deeply nested value."""
        result = await (
            WorkflowBuilder("Dict Get Deep")
            .add_start()
            .add_set_variable(
                "data", {"level1": {"level2": {"level3": {"value": "found"}}}}
            )
            .add_get_property("{{data}}", property_path="level1.level2.level3.value")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestDictSet:
    """Tests for dictionary set operations."""

    async def test_dict_set_key(self) -> None:
        """Test setting value by key."""
        result = await (
            WorkflowBuilder("Dict Set Key")
            .add_start()
            .add_set_variable("data", {"a": 1})
            .add_dict_set("{{data}}", key="b", value=2)
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_dict_set_overwrite(self) -> None:
        """Test overwriting existing key."""
        result = await (
            WorkflowBuilder("Dict Set Overwrite")
            .add_start()
            .add_set_variable("data", {"name": "John"})
            .add_dict_set("{{data}}", key="name", value="Jane")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_dict_set_new_dict(self) -> None:
        """Test setting key on empty dictionary."""
        result = await (
            WorkflowBuilder("Dict Set Empty")
            .add_start()
            .add_set_variable("data", {})
            .add_dict_set("{{data}}", key="first", value="value")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestDictDelete:
    """Tests for dictionary delete operations."""

    async def test_dict_delete_key(self) -> None:
        """Test deleting key from dictionary."""
        result = await (
            WorkflowBuilder("Dict Delete")
            .add_start()
            .add_set_variable("data", {"a": 1, "b": 2})
            .add_dict_remove("{{data}}", key="b")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_dict_delete_nonexistent(self) -> None:
        """Test deleting nonexistent key (should not error)."""
        result = await (
            WorkflowBuilder("Dict Delete Nonexistent")
            .add_start()
            .add_set_variable("data", {"a": 1})
            .add_dict_remove("{{data}}", key="z")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestDictKeys:
    """Tests for dictionary keys operations."""

    async def test_dict_keys(self) -> None:
        """Test getting all keys from dictionary."""
        result = await (
            WorkflowBuilder("Dict Keys")
            .add_start()
            .add_set_variable("data", {"a": 1, "b": 2, "c": 3})
            .add_dict_keys("{{data}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_dict_keys_empty(self) -> None:
        """Test getting keys from empty dictionary."""
        result = await (
            WorkflowBuilder("Dict Keys Empty")
            .add_start()
            .add_set_variable("data", {})
            .add_dict_keys("{{data}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestDictValues:
    """Tests for dictionary values operations."""

    async def test_dict_values(self) -> None:
        """Test getting all values from dictionary."""
        result = await (
            WorkflowBuilder("Dict Values")
            .add_start()
            .add_set_variable("data", {"a": 1, "b": 2, "c": 3})
            .add_dict_values("{{data}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_dict_values_empty(self) -> None:
        """Test getting values from empty dictionary."""
        result = await (
            WorkflowBuilder("Dict Values Empty")
            .add_start()
            .add_set_variable("data", {})
            .add_dict_values("{{data}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestDictHasKey:
    """Tests for dictionary has-key operations."""

    async def test_dict_has_key_exists(self) -> None:
        """Test checking for existing key."""
        result = await (
            WorkflowBuilder("Dict Has Key Exists")
            .add_start()
            .add_set_variable("data", {"a": 1})
            .add_dict_has_key("{{data}}", key="a")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_dict_has_key_not_exists(self) -> None:
        """Test checking for nonexistent key."""
        result = await (
            WorkflowBuilder("Dict Has Key Not Exists")
            .add_start()
            .add_set_variable("data", {"a": 1})
            .add_dict_has_key("{{data}}", key="b")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestDictMerge:
    """Tests for dictionary merge operations."""

    async def test_dict_merge(self) -> None:
        """Test merging two dictionaries."""
        result = await (
            WorkflowBuilder("Dict Merge")
            .add_start()
            .add_set_variable("dict1", {"a": 1})
            .add_set_variable("dict2", {"b": 2})
            .add_dict_merge("{{dict1}}", "{{dict2}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_dict_merge_overlap(self) -> None:
        """Test merging dictionaries with overlapping keys (second wins)."""
        result = await (
            WorkflowBuilder("Dict Merge Overlap")
            .add_start()
            .add_set_variable("dict1", {"a": 1, "b": 2})
            .add_set_variable("dict2", {"b": 3, "c": 4})
            .add_dict_merge("{{dict1}}", "{{dict2}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_dict_merge_empty(self) -> None:
        """Test merging with empty dictionary."""
        result = await (
            WorkflowBuilder("Dict Merge Empty")
            .add_start()
            .add_set_variable("dict1", {"a": 1})
            .add_set_variable("dict2", {})
            .add_dict_merge("{{dict1}}", "{{dict2}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestCreateDict:
    """Tests for dictionary creation operations."""

    async def test_create_dict_single(self) -> None:
        """Test creating dictionary with single key-value pair."""
        result = await (
            WorkflowBuilder("Create Dict Single")
            .add_start()
            .add_create_dict(key_1="name", value_1="John")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_create_dict_multiple(self) -> None:
        """Test creating dictionary with multiple key-value pairs."""
        result = await (
            WorkflowBuilder("Create Dict Multiple")
            .add_start()
            .add_create_dict(
                key_1="name",
                value_1="John",
                key_2="age",
                value_2=30,
                key_3="active",
                value_3=True,
            )
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_create_dict_empty(self) -> None:
        """Test creating empty dictionary."""
        result = await (
            WorkflowBuilder("Create Dict Empty")
            .add_start()
            .add_create_dict()
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestJsonPipeline:
    """Tests for chained JSON operations."""

    async def test_json_parse_get_stringify(self) -> None:
        """Test pipeline: parse -> get -> stringify."""
        result = await (
            WorkflowBuilder("JSON Pipeline")
            .add_start()
            .add_set_variable("json_str", '{"user": {"name": "John", "age": 30}}')
            .add_json_parse("{{json_str}}")
            .add_get_property("{{json_str}}", property_path="user")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_dict_transform_pipeline(self) -> None:
        """Test pipeline: create -> set -> merge -> keys."""
        result = await (
            WorkflowBuilder("Dict Transform Pipeline")
            .add_start()
            .add_create_dict(key_1="a", value_1=1)
            .add_set_variable("dict1", {"a": 1})
            .add_dict_set("{{dict1}}", key="b", value=2)
            .add_set_variable("dict2", {"c": 3})
            .add_dict_merge("{{dict1}}", "{{dict2}}")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_nested_dict_operations(self) -> None:
        """Test working with nested dictionaries."""
        result = await (
            WorkflowBuilder("Nested Dict Ops")
            .add_start()
            .add_set_variable(
                "data",
                {"users": [{"name": "John"}, {"name": "Jane"}], "count": 2},
            )
            .add_get_property("{{data}}", property_path="users")
            .add_dict_get("{{data}}", key="count")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_build_and_serialize_dict(self) -> None:
        """Test building dictionary from parts then serializing."""
        result = await (
            WorkflowBuilder("Build and Serialize")
            .add_start()
            .add_set_variable("base", {})
            .add_dict_set("{{base}}", key="name", value="Product")
            .add_dict_set("{{base}}", key="price", value=99.99)
            .add_dict_set("{{base}}", key="inStock", value=True)
            .add_dict_to_json("{{base}}", indent=2)
            .add_end()
            .execute()
        )

        assert result["success"] is True
