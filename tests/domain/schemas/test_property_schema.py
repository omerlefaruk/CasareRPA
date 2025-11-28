"""
Tests for PropertySchema validation system.

Following TDD Guidelines:
- Domain layer: Pure unit tests, NO mocks
- Test immutability, validation, equality
- Use real domain objects
"""

import pytest
from casare_rpa.domain.schemas.property_schema import (
    PropertyDef,
    NodeSchema,
)
from casare_rpa.domain.schemas.property_types import PropertyType


class TestPropertyDef:
    """Test PropertyDef value object behavior."""

    def test_create_property_with_minimal_args(self):
        """PropertyDef can be created with just name and type."""
        prop = PropertyDef(name="test_prop", type=PropertyType.STRING)

        assert prop.name == "test_prop"
        assert prop.type == PropertyType.STRING
        assert prop.default is None

    def test_auto_generates_label_from_name(self):
        """PropertyDef auto-generates label from snake_case name."""
        prop = PropertyDef(name="my_test_property", type=PropertyType.STRING)

        assert prop.label == "My Test Property"

    def test_custom_label_overrides_auto_generation(self):
        """Custom label is preserved when provided."""
        prop = PropertyDef(
            name="timeout_ms", type=PropertyType.INTEGER, label="Timeout (milliseconds)"
        )

        assert prop.label == "Timeout (milliseconds)"

    def test_property_with_all_attributes(self):
        """PropertyDef stores all provided attributes correctly."""
        prop = PropertyDef(
            name="retry_count",
            type=PropertyType.INTEGER,
            default=3,
            label="Retry Count",
            placeholder="Enter number of retries",
            tab="advanced",
            readonly=False,
            tooltip="Number of times to retry on failure",
            required=True,
            min_value=0,
            max_value=10,
        )

        assert prop.name == "retry_count"
        assert prop.type == PropertyType.INTEGER
        assert prop.default == 3
        assert prop.label == "Retry Count"
        assert prop.placeholder == "Enter number of retries"
        assert prop.tab == "advanced"
        assert prop.readonly is False
        assert prop.tooltip == "Number of times to retry on failure"
        assert prop.required is True
        assert prop.min_value == 0
        assert prop.max_value == 10

    def test_choice_property_with_options(self):
        """PropertyDef can define CHOICE type with options."""
        prop = PropertyDef(
            name="log_level",
            type=PropertyType.CHOICE,
            default="INFO",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        )

        assert prop.type == PropertyType.CHOICE
        assert prop.choices == ["DEBUG", "INFO", "WARNING", "ERROR"]
        assert prop.default == "INFO"

    def test_multi_choice_property(self):
        """PropertyDef can define MULTI_CHOICE type."""
        prop = PropertyDef(
            name="selected_columns",
            type=PropertyType.MULTI_CHOICE,
            default=[],
            choices=["id", "name", "email", "created_at"],
        )

        assert prop.type == PropertyType.MULTI_CHOICE
        assert prop.choices is not None
        assert len(prop.choices) == 4


class TestNodeSchema:
    """Test NodeSchema validation and configuration."""

    def test_empty_schema_has_no_properties(self):
        """Empty NodeSchema has empty properties list."""
        schema = NodeSchema()

        assert schema.properties == []

    def test_schema_with_single_property(self):
        """NodeSchema can contain a single property."""
        prop = PropertyDef(name="url", type=PropertyType.STRING, default="")
        schema = NodeSchema(properties=[prop])

        assert len(schema.properties) == 1
        assert schema.properties[0].name == "url"

    def test_get_default_config_returns_empty_dict_for_no_properties(self):
        """get_default_config returns empty dict when no properties defined."""
        schema = NodeSchema()

        config = schema.get_default_config()

        assert config == {}

    def test_get_default_config_returns_property_defaults(self):
        """get_default_config returns dict with all property defaults."""
        schema = NodeSchema(
            properties=[
                PropertyDef(name="url", type=PropertyType.STRING, default=""),
                PropertyDef(name="timeout", type=PropertyType.INTEGER, default=5000),
                PropertyDef(name="enabled", type=PropertyType.BOOLEAN, default=True),
            ]
        )

        config = schema.get_default_config()

        assert config == {"url": "", "timeout": 5000, "enabled": True}

    def test_validate_config_passes_for_valid_types(self):
        """validate_config returns True for correctly typed values."""
        schema = NodeSchema(
            properties=[
                PropertyDef(name="name", type=PropertyType.STRING),
                PropertyDef(name="count", type=PropertyType.INTEGER),
                PropertyDef(name="ratio", type=PropertyType.FLOAT),
                PropertyDef(name="active", type=PropertyType.BOOLEAN),
            ]
        )

        config = {"name": "test", "count": 42, "ratio": 3.14, "active": True}
        is_valid, error = schema.validate_config(config)

        assert is_valid is True
        assert error == ""

    def test_validate_config_fails_for_wrong_string_type(self):
        """validate_config returns False when STRING property has wrong type."""
        schema = NodeSchema(
            properties=[PropertyDef(name="url", type=PropertyType.STRING)]
        )

        config = {"url": 123}  # Should be string
        is_valid, error = schema.validate_config(config)

        assert is_valid is False
        assert "string" in error.lower()

    def test_validate_config_fails_for_wrong_integer_type(self):
        """validate_config returns False when INTEGER property has wrong type."""
        schema = NodeSchema(
            properties=[PropertyDef(name="count", type=PropertyType.INTEGER)]
        )

        config = {"count": "not an integer"}
        is_valid, error = schema.validate_config(config)

        assert is_valid is False
        assert "integer" in error.lower()

    def test_validate_config_rejects_boolean_as_integer(self):
        """validate_config rejects boolean when integer expected (Python quirk)."""
        schema = NodeSchema(
            properties=[PropertyDef(name="count", type=PropertyType.INTEGER)]
        )

        config = {"count": True}  # In Python, bool is subclass of int
        is_valid, error = schema.validate_config(config)

        assert is_valid is False
        assert "integer" in error.lower()

    def test_validate_config_accepts_int_for_float(self):
        """validate_config accepts integer when float expected."""
        schema = NodeSchema(
            properties=[PropertyDef(name="ratio", type=PropertyType.FLOAT)]
        )

        config = {"ratio": 42}  # int should be accepted for float
        is_valid, error = schema.validate_config(config)

        assert is_valid is True

    def test_validate_config_rejects_boolean_as_float(self):
        """validate_config rejects boolean when float expected."""
        schema = NodeSchema(
            properties=[PropertyDef(name="ratio", type=PropertyType.FLOAT)]
        )

        config = {"ratio": False}
        is_valid, error = schema.validate_config(config)

        assert is_valid is False

    def test_validate_config_enforces_required_fields(self):
        """validate_config fails when required field is missing."""
        schema = NodeSchema(
            properties=[
                PropertyDef(name="url", type=PropertyType.STRING, required=True)
            ]
        )

        config = {"url": None}
        is_valid, error = schema.validate_config(config)

        assert is_valid is False
        assert "required" in error.lower()

    def test_validate_config_enforces_required_non_empty(self):
        """validate_config fails when required field is empty string."""
        schema = NodeSchema(
            properties=[
                PropertyDef(name="url", type=PropertyType.STRING, required=True)
            ]
        )

        config = {"url": ""}
        is_valid, error = schema.validate_config(config)

        assert is_valid is False
        assert "required" in error.lower()

    def test_validate_config_allows_none_for_optional_fields(self):
        """validate_config allows None for non-required fields."""
        schema = NodeSchema(
            properties=[
                PropertyDef(name="url", type=PropertyType.STRING, required=False)
            ]
        )

        config = {"url": None}
        is_valid, error = schema.validate_config(config)

        assert is_valid is True

    def test_validate_config_enforces_min_value_for_integer(self):
        """validate_config fails when integer below min_value."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    name="count", type=PropertyType.INTEGER, min_value=0, max_value=100
                )
            ]
        )

        config = {"count": -1}
        is_valid, error = schema.validate_config(config)

        assert is_valid is False
        assert ">=" in error
        assert "0" in error

    def test_validate_config_enforces_max_value_for_integer(self):
        """validate_config fails when integer above max_value."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    name="count", type=PropertyType.INTEGER, min_value=0, max_value=100
                )
            ]
        )

        config = {"count": 101}
        is_valid, error = schema.validate_config(config)

        assert is_valid is False
        assert "<=" in error
        assert "100" in error

    def test_validate_config_enforces_min_value_for_float(self):
        """validate_config fails when float below min_value."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    name="ratio", type=PropertyType.FLOAT, min_value=0.0, max_value=1.0
                )
            ]
        )

        config = {"ratio": -0.5}
        is_valid, error = schema.validate_config(config)

        assert is_valid is False
        assert ">=" in error

    def test_validate_config_enforces_max_value_for_float(self):
        """validate_config fails when float above max_value."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    name="ratio", type=PropertyType.FLOAT, min_value=0.0, max_value=1.0
                )
            ]
        )

        config = {"ratio": 1.5}
        is_valid, error = schema.validate_config(config)

        assert is_valid is False
        assert "<=" in error

    def test_validate_config_enforces_choice_options(self):
        """validate_config fails when CHOICE value not in choices list."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    name="log_level",
                    type=PropertyType.CHOICE,
                    choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                )
            ]
        )

        config = {"log_level": "INVALID"}
        is_valid, error = schema.validate_config(config)

        assert is_valid is False
        assert "one of" in error.lower()
        assert "DEBUG" in error

    def test_validate_config_allows_valid_choice(self):
        """validate_config passes when CHOICE value is in choices list."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    name="log_level",
                    type=PropertyType.CHOICE,
                    choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                )
            ]
        )

        config = {"log_level": "INFO"}
        is_valid, error = schema.validate_config(config)

        assert is_valid is True

    def test_validate_config_enforces_multi_choice_options(self):
        """validate_config fails when MULTI_CHOICE contains invalid values."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    name="columns",
                    type=PropertyType.MULTI_CHOICE,
                    choices=["id", "name", "email", "created_at"],
                )
            ]
        )

        config = {"columns": ["id", "INVALID", "email"]}
        is_valid, error = schema.validate_config(config)

        assert is_valid is False
        assert "invalid choices" in error.lower()
        assert "INVALID" in error

    def test_validate_config_allows_valid_multi_choice(self):
        """validate_config passes when all MULTI_CHOICE values are valid."""
        schema = NodeSchema(
            properties=[
                PropertyDef(
                    name="columns",
                    type=PropertyType.MULTI_CHOICE,
                    choices=["id", "name", "email", "created_at"],
                )
            ]
        )

        config = {"columns": ["id", "email"]}
        is_valid, error = schema.validate_config(config)

        assert is_valid is True

    def test_validate_config_returns_multiple_errors(self):
        """validate_config returns all validation errors joined with semicolons."""
        schema = NodeSchema(
            properties=[
                PropertyDef(name="url", type=PropertyType.STRING, required=True),
                PropertyDef(
                    name="count", type=PropertyType.INTEGER, min_value=1, max_value=10
                ),
            ]
        )

        config = {"url": "", "count": 20}  # Both invalid
        is_valid, error = schema.validate_config(config)

        assert is_valid is False
        assert "required" in error.lower()
        assert "<=" in error
        # Errors should be separated by semicolon
        assert ";" in error

    def test_get_property_returns_property_by_name(self):
        """get_property returns PropertyDef when name matches."""
        prop1 = PropertyDef(name="url", type=PropertyType.STRING)
        prop2 = PropertyDef(name="timeout", type=PropertyType.INTEGER)
        schema = NodeSchema(properties=[prop1, prop2])

        result = schema.get_property("timeout")

        assert result is not None
        assert result.name == "timeout"
        assert result.type == PropertyType.INTEGER

    def test_get_property_returns_none_when_not_found(self):
        """get_property returns None when property name doesn't exist."""
        schema = NodeSchema(
            properties=[PropertyDef(name="url", type=PropertyType.STRING)]
        )

        result = schema.get_property("nonexistent")

        assert result is None


class TestPropertySchemaEdgeCases:
    """Test edge cases and error conditions."""

    def test_validate_config_with_empty_config_dict(self):
        """validate_config handles empty config dict."""
        schema = NodeSchema(
            properties=[
                PropertyDef(name="url", type=PropertyType.STRING, required=False)
            ]
        )

        is_valid, error = schema.validate_config({})

        # Empty config is valid if all fields are optional
        assert is_valid is True

    def test_validate_config_skips_unknown_properties_in_config(self):
        """validate_config ignores extra properties not in schema."""
        schema = NodeSchema(
            properties=[PropertyDef(name="url", type=PropertyType.STRING)]
        )

        config = {"url": "http://test.com", "extra_field": "ignored"}
        is_valid, error = schema.validate_config(config)

        # Should validate successfully, ignoring extra fields
        assert is_valid is True

    def test_validate_config_handles_none_choices_gracefully(self):
        """validate_config handles CHOICE type with None choices list."""
        schema = NodeSchema(
            properties=[
                PropertyDef(name="level", type=PropertyType.CHOICE, choices=None)
            ]
        )

        config = {"level": "anything"}
        is_valid, error = schema.validate_config(config)

        # Should pass - no choices means any string is valid
        assert is_valid is True

    def test_validate_config_for_json_type_accepts_dict(self):
        """validate_config accepts dict for JSON type."""
        schema = NodeSchema(
            properties=[PropertyDef(name="data", type=PropertyType.JSON)]
        )

        config = {"data": {"key": "value"}}
        is_valid, error = schema.validate_config(config)

        assert is_valid is True

    def test_validate_config_for_json_type_accepts_list(self):
        """validate_config accepts list for JSON type."""
        schema = NodeSchema(
            properties=[PropertyDef(name="data", type=PropertyType.JSON)]
        )

        config = {"data": [1, 2, 3]}
        is_valid, error = schema.validate_config(config)

        assert is_valid is True

    def test_validate_config_for_custom_type_always_passes(self):
        """validate_config always passes for CUSTOM type (widget handles validation)."""
        schema = NodeSchema(
            properties=[PropertyDef(name="custom", type=PropertyType.CUSTOM)]
        )

        config = {"custom": "any value"}
        is_valid, error = schema.validate_config(config)

        assert is_valid is True

    def test_complex_schema_with_multiple_property_types(self):
        """Comprehensive test with all major property types."""
        schema = NodeSchema(
            properties=[
                PropertyDef(name="url", type=PropertyType.STRING, required=True),
                PropertyDef(
                    name="timeout", type=PropertyType.INTEGER, default=5000, min_value=0
                ),
                PropertyDef(name="ratio", type=PropertyType.FLOAT, max_value=1.0),
                PropertyDef(name="enabled", type=PropertyType.BOOLEAN, default=True),
                PropertyDef(
                    name="log_level",
                    type=PropertyType.CHOICE,
                    choices=["DEBUG", "INFO"],
                    default="INFO",
                ),
                PropertyDef(
                    name="columns",
                    type=PropertyType.MULTI_CHOICE,
                    choices=["id", "name", "email"],
                ),
                PropertyDef(name="selector", type=PropertyType.SELECTOR),
                PropertyDef(name="file_path", type=PropertyType.FILE_PATH),
            ]
        )

        # Valid config
        config = {
            "url": "http://test.com",
            "timeout": 3000,
            "ratio": 0.5,
            "enabled": True,
            "log_level": "DEBUG",
            "columns": ["id", "name"],
            "selector": "#button",
            "file_path": "/path/to/file.txt",
        }

        is_valid, error = schema.validate_config(config)

        assert is_valid is True
        assert error == ""
