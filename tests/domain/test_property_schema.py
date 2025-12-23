"""
Tests for PropertySchema and should_display() method.

This test suite covers the property schema system for declarative node configuration:
- PropertyDef: Property definition dataclass
- NodeSchema: Schema for node configuration properties
- should_display(): Conditional property visibility

Test Philosophy:
- Pure domain tests - NO mocks needed
- Focus on should_display() logic for Super Node widget filtering
- Test display_when and hidden_when conditions

Run: pytest tests/domain/test_property_schema.py -v
"""

import pytest
from casare_rpa.domain.schemas.property_schema import (
    PropertyDef,
    NodeSchema,
    PropertyType,
)


# =============================================================================
# PropertyDef Tests
# =============================================================================


class TestPropertyDef:
    """Tests for PropertyDef dataclass."""

    def test_create_minimal_property(self) -> None:
        """Test creating PropertyDef with minimal arguments."""
        prop = PropertyDef(name="test", type=PropertyType.STRING)

        assert prop.name == "test"
        assert prop.type == PropertyType.STRING
        assert prop.default is None
        assert prop.label == "Test"  # Auto-generated
        assert prop.essential is False
        assert prop.visibility == "normal"

    def test_auto_label_generation(self) -> None:
        """Test that snake_case names are converted to Title Case labels."""
        prop = PropertyDef(name="my_long_property_name", type=PropertyType.STRING)
        assert prop.label == "My Long Property Name"

    def test_essential_syncs_visibility(self) -> None:
        """Test that essential=True sets visibility to 'essential'."""
        prop = PropertyDef(
            name="action",
            type=PropertyType.CHOICE,
            essential=True,
        )

        assert prop.essential is True
        assert prop.visibility == "essential"

    def test_visibility_essential_syncs_essential(self) -> None:
        """Test that visibility='essential' sets essential=True."""
        prop = PropertyDef(
            name="action",
            type=PropertyType.CHOICE,
            visibility="essential",
        )

        assert prop.visibility == "essential"
        assert prop.essential is True

    def test_display_when_property(self) -> None:
        """Test PropertyDef with display_when condition."""
        prop = PropertyDef(
            name="file_path",
            type=PropertyType.FILE_PATH,
            display_when={"action": ["Read File", "Write File"]},
        )

        assert prop.display_when is not None
        assert "action" in prop.display_when
        assert prop.display_when["action"] == ["Read File", "Write File"]

    def test_hidden_when_property(self) -> None:
        """Test PropertyDef with hidden_when condition."""
        prop = PropertyDef(
            name="binary_mode",
            type=PropertyType.BOOLEAN,
            hidden_when={"action": ["Delete File"]},
        )

        assert prop.hidden_when is not None
        assert "action" in prop.hidden_when


# =============================================================================
# NodeSchema Tests
# =============================================================================


class TestNodeSchema:
    """Tests for NodeSchema."""

    def test_empty_schema(self) -> None:
        """Test creating empty schema."""
        schema = NodeSchema()
        assert schema.properties == []
        assert schema.get_default_config() == {}

    def test_schema_with_properties(self) -> None:
        """Test schema with multiple properties."""
        schema = NodeSchema(
            properties=[
                PropertyDef("name", PropertyType.STRING, default="default_name"),
                PropertyDef("count", PropertyType.INTEGER, default=10),
                PropertyDef("enabled", PropertyType.BOOLEAN, default=True),
            ]
        )

        assert len(schema.properties) == 3

    def test_get_default_config(self) -> None:
        """Test generating default config from schema."""
        schema = NodeSchema(
            properties=[
<<<<<<< HEAD
                PropertyDef(
                    "file_path", PropertyType.FILE_PATH, default="/tmp/test.txt"
                ),
=======
                PropertyDef("file_path", PropertyType.FILE_PATH, default="/tmp/test.txt"),
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
                PropertyDef("encoding", PropertyType.STRING, default="utf-8"),
                PropertyDef("max_size", PropertyType.INTEGER, default=1024),
            ]
        )

        config = schema.get_default_config()

        assert config["file_path"] == "/tmp/test.txt"
        assert config["encoding"] == "utf-8"
        assert config["max_size"] == 1024

    def test_get_property_existing(self) -> None:
        """Test getting property by name."""
        schema = NodeSchema(
            properties=[
                PropertyDef("test_prop", PropertyType.STRING),
            ]
        )

        prop = schema.get_property("test_prop")

        assert prop is not None
        assert prop.name == "test_prop"

    def test_get_property_missing(self) -> None:
        """Test getting non-existent property returns None."""
        schema = NodeSchema(
            properties=[
                PropertyDef("existing", PropertyType.STRING),
            ]
        )

        prop = schema.get_property("non_existent")

        assert prop is None

    def test_get_essential_properties(self) -> None:
        """Test getting essential property names."""
        schema = NodeSchema(
            properties=[
                PropertyDef("action", PropertyType.CHOICE, essential=True),
                PropertyDef("file_path", PropertyType.FILE_PATH, essential=False),
                PropertyDef("encoding", PropertyType.STRING, essential=False),
                PropertyDef("timeout", PropertyType.INTEGER, essential=True),
            ]
        )

        essential = schema.get_essential_properties()

        assert len(essential) == 2
        assert "action" in essential
        assert "timeout" in essential

    def test_get_collapsible_properties(self) -> None:
        """Test getting non-essential (collapsible) property names."""
        schema = NodeSchema(
            properties=[
                PropertyDef("action", PropertyType.CHOICE, essential=True),
                PropertyDef("file_path", PropertyType.FILE_PATH, essential=False),
                PropertyDef("encoding", PropertyType.STRING, essential=False),
            ]
        )

        collapsible = schema.get_collapsible_properties()

        assert len(collapsible) == 2
        assert "file_path" in collapsible
        assert "encoding" in collapsible
        assert "action" not in collapsible

    def test_get_sorted_properties(self) -> None:
        """Test properties sorted by order field."""
        schema = NodeSchema(
            properties=[
                PropertyDef("third", PropertyType.STRING, order=30),
                PropertyDef("first", PropertyType.STRING, order=10),
                PropertyDef("second", PropertyType.STRING, order=20),
            ]
        )

        sorted_props = schema.get_sorted_properties()

        assert sorted_props[0].name == "first"
        assert sorted_props[1].name == "second"
        assert sorted_props[2].name == "third"


# =============================================================================
# should_display() Tests - CRITICAL for Super Node filtering
# =============================================================================


class TestShouldDisplay:
    """Tests for NodeSchema.should_display() method."""

    def test_should_display_no_conditions(self) -> None:
        """Test property with no display conditions is always visible."""
        schema = NodeSchema(
            properties=[
                PropertyDef("always_visible", PropertyType.STRING),
            ]
        )

        result = schema.should_display("always_visible", {})

        assert result is True

    def test_should_display_internal_always_hidden(self) -> None:
        """Test internal visibility properties are always hidden."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    "internal_prop",
                    PropertyType.STRING,
                    visibility="internal",
                ),
            ]
        )

        result = schema.should_display("internal_prop", {})

        assert result is False

    def test_should_display_missing_property(self) -> None:
        """Test non-existent property returns False."""
        schema = NodeSchema(properties=[])

        result = schema.should_display("non_existent", {})

        assert result is False

    # -------------------------------------------------------------------------
    # display_when Tests (Single Value)
    # -------------------------------------------------------------------------

    def test_display_when_single_value_match(self) -> None:
        """Test display_when with single value that matches."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    "file_path",
                    PropertyType.FILE_PATH,
                    display_when={"action": "Read File"},
                ),
            ]
        )

        result = schema.should_display("file_path", {"action": "Read File"})

        assert result is True

    def test_display_when_single_value_no_match(self) -> None:
        """Test display_when with single value that doesn't match."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    "file_path",
                    PropertyType.FILE_PATH,
                    display_when={"action": "Read File"},
                ),
            ]
        )

        result = schema.should_display("file_path", {"action": "Write File"})

        assert result is False

    # -------------------------------------------------------------------------
    # display_when Tests (List of Values)
    # -------------------------------------------------------------------------

    def test_display_when_list_match(self) -> None:
        """Test display_when with list of allowed values - matching."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    "file_path",
                    PropertyType.FILE_PATH,
                    display_when={"action": ["Read File", "Write File", "Delete File"]},
                ),
            ]
        )

        # Should match when action is any of the allowed values
        assert schema.should_display("file_path", {"action": "Read File"}) is True
        assert schema.should_display("file_path", {"action": "Write File"}) is True
        assert schema.should_display("file_path", {"action": "Delete File"}) is True

    def test_display_when_list_no_match(self) -> None:
        """Test display_when with list of allowed values - not matching."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    "file_path",
                    PropertyType.FILE_PATH,
                    display_when={"action": ["Read File", "Write File"]},
                ),
            ]
        )

        result = schema.should_display("file_path", {"action": "Copy File"})

        assert result is False

    def test_display_when_list_empty_config(self) -> None:
        """Test display_when when config key is missing."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    "file_path",
                    PropertyType.FILE_PATH,
                    display_when={"action": ["Read File", "Write File"]},
                ),
            ]
        )

        # When config doesn't have the key, actual value is None
        result = schema.should_display("file_path", {})

        assert result is False

    # -------------------------------------------------------------------------
    # hidden_when Tests
    # -------------------------------------------------------------------------

    def test_hidden_when_single_value_match(self) -> None:
        """Test hidden_when hides property when condition matches."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    "encoding",
                    PropertyType.STRING,
                    hidden_when={"binary_mode": True},
                ),
            ]
        )

        result = schema.should_display("encoding", {"binary_mode": True})

        assert result is False

    def test_hidden_when_single_value_no_match(self) -> None:
        """Test hidden_when shows property when condition doesn't match."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    "encoding",
                    PropertyType.STRING,
                    hidden_when={"binary_mode": True},
                ),
            ]
        )

        result = schema.should_display("encoding", {"binary_mode": False})

        assert result is True

    def test_hidden_when_list_match(self) -> None:
        """Test hidden_when with list of values that trigger hiding."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    "source_path",
                    PropertyType.FILE_PATH,
                    hidden_when={"action": ["Read File", "Delete File"]},
                ),
            ]
        )

        # Should be hidden when action is in the list
        assert schema.should_display("source_path", {"action": "Read File"}) is False
        assert schema.should_display("source_path", {"action": "Delete File"}) is False

        # Should be visible for other actions
        assert schema.should_display("source_path", {"action": "Copy File"}) is True

    # -------------------------------------------------------------------------
    # Combined display_when and hidden_when Tests
    # -------------------------------------------------------------------------

    def test_display_when_and_hidden_when_both_pass(self) -> None:
        """Test property visible when display_when passes and hidden_when doesn't match."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    "encoding",
                    PropertyType.STRING,
                    display_when={"action": ["Read File", "Write File"]},
                    hidden_when={"binary_mode": True},
                ),
            ]
        )

        # Both conditions favorable
<<<<<<< HEAD
        result = schema.should_display(
            "encoding", {"action": "Read File", "binary_mode": False}
        )
=======
        result = schema.should_display("encoding", {"action": "Read File", "binary_mode": False})
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e

        assert result is True

    def test_display_when_fails_hidden_when_would_pass(self) -> None:
        """Test property hidden when display_when fails (even if hidden_when would pass)."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    "encoding",
                    PropertyType.STRING,
                    display_when={"action": ["Read File", "Write File"]},
                    hidden_when={"binary_mode": True},
                ),
            ]
        )

        # display_when fails (action not in list)
<<<<<<< HEAD
        result = schema.should_display(
            "encoding", {"action": "Delete File", "binary_mode": False}
        )
=======
        result = schema.should_display("encoding", {"action": "Delete File", "binary_mode": False})
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e

        assert result is False

    def test_hidden_when_triggers_even_with_display_when_pass(self) -> None:
        """Test property hidden when hidden_when matches (even if display_when passes)."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    "encoding",
                    PropertyType.STRING,
                    display_when={"action": ["Read File", "Write File"]},
                    hidden_when={"binary_mode": True},
                ),
            ]
        )

        # display_when passes but hidden_when triggers
<<<<<<< HEAD
        result = schema.should_display(
            "encoding", {"action": "Read File", "binary_mode": True}
        )
=======
        result = schema.should_display("encoding", {"action": "Read File", "binary_mode": True})
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e

        assert result is False

    # -------------------------------------------------------------------------
    # Multiple Conditions Tests
    # -------------------------------------------------------------------------

    def test_display_when_multiple_keys_all_must_match(self) -> None:
        """Test display_when with multiple keys - all must match."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    "advanced_option",
                    PropertyType.BOOLEAN,
                    display_when={
                        "action": "Write File",
                        "mode": "advanced",
                    },
                ),
            ]
        )

        # Both conditions must match
        assert (
<<<<<<< HEAD
            schema.should_display(
                "advanced_option", {"action": "Write File", "mode": "advanced"}
            )
=======
            schema.should_display("advanced_option", {"action": "Write File", "mode": "advanced"})
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
            is True
        )

        # One condition fails
        assert (
<<<<<<< HEAD
            schema.should_display(
                "advanced_option", {"action": "Write File", "mode": "simple"}
            )
=======
            schema.should_display("advanced_option", {"action": "Write File", "mode": "simple"})
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
            is False
        )

        assert (
<<<<<<< HEAD
            schema.should_display(
                "advanced_option", {"action": "Read File", "mode": "advanced"}
            )
=======
            schema.should_display("advanced_option", {"action": "Read File", "mode": "advanced"})
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
            is False
        )

    def test_hidden_when_multiple_keys_any_triggers_hide(self) -> None:
        """Test hidden_when with multiple keys - any match triggers hide."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    "option",
                    PropertyType.BOOLEAN,
                    hidden_when={
                        "disabled": True,
                        "readonly": True,
                    },
                ),
            ]
        )

        # Either condition triggers hide
<<<<<<< HEAD
        assert (
            schema.should_display("option", {"disabled": True, "readonly": False})
            is False
        )

        assert (
            schema.should_display("option", {"disabled": False, "readonly": True})
            is False
        )

        # Neither matches - visible
        assert (
            schema.should_display("option", {"disabled": False, "readonly": False})
            is True
        )
=======
        assert schema.should_display("option", {"disabled": True, "readonly": False}) is False

        assert schema.should_display("option", {"disabled": False, "readonly": True}) is False

        # Neither matches - visible
        assert schema.should_display("option", {"disabled": False, "readonly": False}) is True
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e


# =============================================================================
# Realistic Super Node Scenario Tests
# =============================================================================


class TestSuperNodePropertyFiltering:
    """
    Tests simulating realistic Super Node property filtering scenarios.

    These tests mirror the actual FileSystemSuperNode property definitions
    to ensure should_display works correctly for Super Node widget filtering.
    """

    @pytest.fixture
    def file_system_schema(self) -> NodeSchema:
        """Create schema matching FileSystemSuperNode properties."""
        return NodeSchema(
            properties=[
                # Action selector - always visible, essential
                PropertyDef(
                    "action",
                    PropertyType.CHOICE,
                    essential=True,
                    order=0,
                    choices=[
                        "Read File",
                        "Write File",
                        "Append File",
                        "Delete File",
                        "Copy File",
                        "Move File",
                    ],
                ),
                # file_path - shown for most actions
                PropertyDef(
                    "file_path",
                    PropertyType.FILE_PATH,
                    order=10,
                    display_when={
                        "action": [
                            "Read File",
                            "Write File",
                            "Append File",
                            "Delete File",
                            "Get File Size",
                        ]
                    },
                ),
                # source_path - only for copy/move
                PropertyDef(
                    "source_path",
                    PropertyType.FILE_PATH,
                    order=10,
                    display_when={"action": ["Copy File", "Move File"]},
                ),
                # dest_path - only for copy/move
                PropertyDef(
                    "dest_path",
                    PropertyType.FILE_PATH,
                    order=11,
                    display_when={"action": ["Copy File", "Move File"]},
                ),
                # content - only for write/append
                PropertyDef(
                    "content",
                    PropertyType.TEXT,
                    order=20,
                    display_when={"action": ["Write File", "Append File"]},
                ),
                # encoding - for text operations, hidden in binary mode
                PropertyDef(
                    "encoding",
                    PropertyType.STRING,
                    default="utf-8",
                    order=30,
                    display_when={"action": ["Read File", "Write File", "Append File"]},
                ),
                # binary_mode - for read/write
                PropertyDef(
                    "binary_mode",
                    PropertyType.BOOLEAN,
                    order=31,
                    display_when={"action": ["Read File", "Write File"]},
                ),
                # max_size - only for read
                PropertyDef(
                    "max_size",
                    PropertyType.INTEGER,
                    default=0,
                    order=32,
                    display_when={"action": ["Read File"]},
                ),
            ]
        )

    def test_read_file_visible_properties(self, file_system_schema: NodeSchema) -> None:
        """Test which properties are visible for Read File action."""
        config = {"action": "Read File"}

        # Should be visible
        assert file_system_schema.should_display("action", config) is True
        assert file_system_schema.should_display("file_path", config) is True
        assert file_system_schema.should_display("encoding", config) is True
        assert file_system_schema.should_display("binary_mode", config) is True
        assert file_system_schema.should_display("max_size", config) is True

        # Should be hidden
        assert file_system_schema.should_display("source_path", config) is False
        assert file_system_schema.should_display("dest_path", config) is False
        assert file_system_schema.should_display("content", config) is False

<<<<<<< HEAD
    def test_write_file_visible_properties(
        self, file_system_schema: NodeSchema
    ) -> None:
=======
    def test_write_file_visible_properties(self, file_system_schema: NodeSchema) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """Test which properties are visible for Write File action."""
        config = {"action": "Write File"}

        # Should be visible
        assert file_system_schema.should_display("action", config) is True
        assert file_system_schema.should_display("file_path", config) is True
        assert file_system_schema.should_display("content", config) is True
        assert file_system_schema.should_display("encoding", config) is True
        assert file_system_schema.should_display("binary_mode", config) is True

        # Should be hidden
        assert file_system_schema.should_display("source_path", config) is False
        assert file_system_schema.should_display("dest_path", config) is False
        assert file_system_schema.should_display("max_size", config) is False

    def test_copy_file_visible_properties(self, file_system_schema: NodeSchema) -> None:
        """Test which properties are visible for Copy File action."""
        config = {"action": "Copy File"}

        # Should be visible
        assert file_system_schema.should_display("action", config) is True
        assert file_system_schema.should_display("source_path", config) is True
        assert file_system_schema.should_display("dest_path", config) is True

        # Should be hidden
        assert file_system_schema.should_display("file_path", config) is False
        assert file_system_schema.should_display("content", config) is False
        assert file_system_schema.should_display("encoding", config) is False
        assert file_system_schema.should_display("binary_mode", config) is False
        assert file_system_schema.should_display("max_size", config) is False

<<<<<<< HEAD
    def test_delete_file_visible_properties(
        self, file_system_schema: NodeSchema
    ) -> None:
=======
    def test_delete_file_visible_properties(self, file_system_schema: NodeSchema) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """Test which properties are visible for Delete File action."""
        config = {"action": "Delete File"}

        # Should be visible
        assert file_system_schema.should_display("action", config) is True
        assert file_system_schema.should_display("file_path", config) is True

        # Should be hidden (most options not relevant for delete)
        assert file_system_schema.should_display("source_path", config) is False
        assert file_system_schema.should_display("dest_path", config) is False
        assert file_system_schema.should_display("content", config) is False
        assert file_system_schema.should_display("encoding", config) is False
        assert file_system_schema.should_display("binary_mode", config) is False
        assert file_system_schema.should_display("max_size", config) is False

    def test_action_switching(self, file_system_schema: NodeSchema) -> None:
        """Test that switching actions changes property visibility correctly."""
        # Start with Read File
        config = {"action": "Read File"}
        assert file_system_schema.should_display("max_size", config) is True
        assert file_system_schema.should_display("content", config) is False

        # Switch to Write File
        config["action"] = "Write File"
        assert file_system_schema.should_display("max_size", config) is False
        assert file_system_schema.should_display("content", config) is True

        # Switch to Copy File
        config["action"] = "Copy File"
        assert file_system_schema.should_display("file_path", config) is False
        assert file_system_schema.should_display("source_path", config) is True
        assert file_system_schema.should_display("dest_path", config) is True


# =============================================================================
# Validation Tests
# =============================================================================


class TestNodeSchemaValidation:
    """Tests for NodeSchema.validate_config() method."""

    def test_validate_required_field_missing(self) -> None:
        """Test validation fails when required field is missing."""
        schema = NodeSchema(
            properties=[
                PropertyDef("file_path", PropertyType.FILE_PATH, required=True),
            ]
        )

        is_valid, error = schema.validate_config({})

        assert is_valid is False
        assert "required" in error.lower()

    def test_validate_required_field_empty(self) -> None:
        """Test validation fails when required field is empty string."""
        schema = NodeSchema(
            properties=[
                PropertyDef("file_path", PropertyType.FILE_PATH, required=True),
            ]
        )

        is_valid, error = schema.validate_config({"file_path": ""})

        assert is_valid is False
        assert "required" in error.lower()

    def test_validate_required_field_present(self) -> None:
        """Test validation passes when required field is present."""
        schema = NodeSchema(
            properties=[
                PropertyDef("file_path", PropertyType.FILE_PATH, required=True),
            ]
        )

        is_valid, error = schema.validate_config({"file_path": "/tmp/test.txt"})

        assert is_valid is True
        assert error == ""

    def test_validate_integer_range(self) -> None:
        """Test integer range validation."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    "count",
                    PropertyType.INTEGER,
                    min_value=1,
                    max_value=100,
                ),
            ]
        )

        # Valid
        is_valid, _ = schema.validate_config({"count": 50})
        assert is_valid is True

        # Too low
        is_valid, error = schema.validate_config({"count": 0})
        assert is_valid is False
        assert ">= 1" in error

        # Too high
        is_valid, error = schema.validate_config({"count": 101})
        assert is_valid is False
        assert "<= 100" in error

    def test_validate_choice_invalid(self) -> None:
        """Test validation fails for invalid choice."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    "action",
                    PropertyType.CHOICE,
                    choices=["Read", "Write", "Delete"],
                ),
            ]
        )

        is_valid, error = schema.validate_config({"action": "Invalid"})

        assert is_valid is False
        assert "must be one of" in error.lower()
