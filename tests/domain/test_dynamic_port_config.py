"""
Tests for DynamicPortConfig value objects.

This test suite covers the domain value objects for Super Node dynamic port management:
- PortDef: Immutable port definition
- ActionPortConfig: Port configuration for a specific action
- DynamicPortSchema: Schema mapping actions to port configs

Test Philosophy:
- Pure domain tests - NO mocks needed (value objects)
- Focus on immutability, validation, and behavior
- Test edge cases like empty configs, missing actions

Run: pytest tests/domain/test_dynamic_port_config.py -v
"""

import pytest
from casare_rpa.domain.value_objects.dynamic_port_config import (
    PortDef,
    ActionPortConfig,
    DynamicPortSchema,
)
from casare_rpa.domain.value_objects.types import DataType


# =============================================================================
# PortDef Tests
# =============================================================================


class TestPortDef:
    """Tests for PortDef value object."""

    def test_create_port_def_minimal(self) -> None:
        """Test creating PortDef with minimal arguments."""
        port = PortDef("test_port", DataType.STRING)

        assert port.name == "test_port"
        assert port.data_type == DataType.STRING
        assert port.required is False
        # Label should be auto-generated from name
        assert port.label == "Test Port"

    def test_create_port_def_all_args(self) -> None:
        """Test creating PortDef with all arguments."""
        port = PortDef(
            name="file_path",
            data_type=DataType.STRING,
            required=True,
            label="Custom Label",
        )

        assert port.name == "file_path"
        assert port.data_type == DataType.STRING
        assert port.required is True
        assert port.label == "Custom Label"

    def test_port_def_auto_label_snake_case(self) -> None:
        """Test that snake_case names are converted to Title Case labels."""
        port = PortDef("my_long_port_name", DataType.INTEGER)
        assert port.label == "My Long Port Name"

    def test_port_def_immutability(self) -> None:
        """Test that PortDef is immutable (frozen dataclass)."""
        port = PortDef("test", DataType.STRING)

        with pytest.raises(AttributeError):
            port.name = "modified"  # type: ignore

        with pytest.raises(AttributeError):
            port.data_type = DataType.INTEGER  # type: ignore

    def test_port_def_equality(self) -> None:
        """Test PortDef equality based on values."""
        port1 = PortDef("test", DataType.STRING)
        port2 = PortDef("test", DataType.STRING)
        port3 = PortDef("different", DataType.STRING)

        assert port1 == port2
        assert port1 != port3

    def test_port_def_hash(self) -> None:
        """Test that PortDef is hashable (can be used in sets/dicts)."""
        port1 = PortDef("test", DataType.STRING)
        port2 = PortDef("test", DataType.STRING)

        # Same value PortDefs should have same hash
        assert hash(port1) == hash(port2)

        # Can be added to set
        port_set = {port1, port2}
        assert len(port_set) == 1  # Duplicates removed

    def test_port_def_various_data_types(self) -> None:
        """Test PortDef with various DataType values."""
        types_to_test = [
            DataType.STRING,
            DataType.INTEGER,
            DataType.FLOAT,
            DataType.BOOLEAN,
            DataType.LIST,
            DataType.ANY,
        ]

        for data_type in types_to_test:
            port = PortDef(f"port_{data_type.value}", data_type)
            assert port.data_type == data_type


# =============================================================================
# ActionPortConfig Tests
# =============================================================================


class TestActionPortConfig:
    """Tests for ActionPortConfig value object."""

    def test_create_empty_config(self) -> None:
        """Test creating ActionPortConfig with no ports."""
        config = ActionPortConfig()

        assert config.inputs == ()
        assert config.outputs == ()

    def test_create_config_with_factory(self) -> None:
        """Test creating ActionPortConfig using factory method."""
        config = ActionPortConfig.create(
            inputs=[PortDef("file_path", DataType.STRING)],
            outputs=[
                PortDef("content", DataType.STRING),
                PortDef("success", DataType.BOOLEAN),
            ],
        )

        assert len(config.inputs) == 1
        assert len(config.outputs) == 2
        assert config.inputs[0].name == "file_path"
        assert config.outputs[0].name == "content"

    def test_create_config_with_none_inputs(self) -> None:
        """Test factory handles None inputs gracefully."""
        config = ActionPortConfig.create(
            inputs=None,
            outputs=[PortDef("result", DataType.ANY)],
        )

        assert config.inputs == ()
        assert len(config.outputs) == 1

    def test_create_config_with_none_outputs(self) -> None:
        """Test factory handles None outputs gracefully."""
        config = ActionPortConfig.create(
            inputs=[PortDef("input", DataType.STRING)],
            outputs=None,
        )

        assert len(config.inputs) == 1
        assert config.outputs == ()

    def test_config_immutability(self) -> None:
        """Test that ActionPortConfig is immutable."""
        config = ActionPortConfig.create(
            inputs=[PortDef("test", DataType.STRING)],
        )

        # Tuple is immutable, so this test verifies the structure
        assert isinstance(config.inputs, tuple)
        assert isinstance(config.outputs, tuple)

    def test_config_equality(self) -> None:
        """Test ActionPortConfig equality."""
        config1 = ActionPortConfig.create(
            inputs=[PortDef("path", DataType.STRING)],
            outputs=[PortDef("success", DataType.BOOLEAN)],
        )
        config2 = ActionPortConfig.create(
            inputs=[PortDef("path", DataType.STRING)],
            outputs=[PortDef("success", DataType.BOOLEAN)],
        )
        config3 = ActionPortConfig.create(
            inputs=[PortDef("different", DataType.STRING)],
        )

        assert config1 == config2
        assert config1 != config3


# =============================================================================
# DynamicPortSchema Tests
# =============================================================================


class TestDynamicPortSchema:
    """Tests for DynamicPortSchema."""

    def test_create_empty_schema(self) -> None:
        """Test creating empty schema."""
        schema = DynamicPortSchema()

        assert schema.action_configs == {}
        assert schema.get_actions() == []

    def test_register_action(self) -> None:
        """Test registering action configuration."""
        schema = DynamicPortSchema()
        config = ActionPortConfig.create(
            inputs=[PortDef("file_path", DataType.STRING)],
            outputs=[PortDef("content", DataType.STRING)],
        )

        schema.register("Read File", config)

        assert schema.has_action("Read File")
        assert not schema.has_action("Write File")

    def test_get_config_existing(self) -> None:
        """Test getting config for existing action."""
        schema = DynamicPortSchema()
        config = ActionPortConfig.create(
            outputs=[PortDef("success", DataType.BOOLEAN)],
        )
        schema.register("Delete", config)

        result = schema.get_config("Delete")

        assert result is not None
        assert result == config

    def test_get_config_missing(self) -> None:
        """Test getting config for non-existent action returns None."""
        schema = DynamicPortSchema()
        schema.register("Existing", ActionPortConfig())

        result = schema.get_config("NonExistent")

        assert result is None

    def test_get_actions_returns_all(self) -> None:
        """Test get_actions returns all registered actions."""
        schema = DynamicPortSchema()
        schema.register("Action A", ActionPortConfig())
        schema.register("Action B", ActionPortConfig())
        schema.register("Action C", ActionPortConfig())

        actions = schema.get_actions()

        assert len(actions) == 3
        assert "Action A" in actions
        assert "Action B" in actions
        assert "Action C" in actions

    def test_has_action(self) -> None:
        """Test has_action method."""
        schema = DynamicPortSchema()
        schema.register("Exists", ActionPortConfig())

        assert schema.has_action("Exists") is True
        assert schema.has_action("DoesNotExist") is False

    def test_register_overwrites_existing(self) -> None:
        """Test that registering same action twice overwrites config."""
        schema = DynamicPortSchema()
        config1 = ActionPortConfig.create(
            inputs=[PortDef("old", DataType.STRING)],
        )
        config2 = ActionPortConfig.create(
            inputs=[PortDef("new", DataType.INTEGER)],
        )

        schema.register("Action", config1)
        schema.register("Action", config2)

        result = schema.get_config("Action")
        assert result is not None
        assert result.inputs[0].name == "new"
        assert result.inputs[0].data_type == DataType.INTEGER

    def test_schema_with_multiple_actions(self) -> None:
        """Test schema with multiple action configurations (realistic use case)."""
        schema = DynamicPortSchema()

        # Register multiple file system actions
        schema.register(
            "Read File",
            ActionPortConfig.create(
                inputs=[PortDef("file_path", DataType.STRING)],
                outputs=[
                    PortDef("content", DataType.STRING),
                    PortDef("size", DataType.INTEGER),
                    PortDef("success", DataType.BOOLEAN),
                ],
            ),
        )
        schema.register(
            "Write File",
            ActionPortConfig.create(
                inputs=[
                    PortDef("file_path", DataType.STRING),
                    PortDef("content", DataType.STRING),
                ],
                outputs=[
                    PortDef("bytes_written", DataType.INTEGER),
                    PortDef("success", DataType.BOOLEAN),
                ],
            ),
        )
        schema.register(
            "Delete File",
            ActionPortConfig.create(
                inputs=[PortDef("file_path", DataType.STRING)],
                outputs=[PortDef("success", DataType.BOOLEAN)],
            ),
        )

        # Verify all actions registered
        assert len(schema.get_actions()) == 3

        # Verify Read File config
        read_config = schema.get_config("Read File")
        assert read_config is not None
        assert len(read_config.inputs) == 1
        assert len(read_config.outputs) == 3

        # Verify Write File config
        write_config = schema.get_config("Write File")
        assert write_config is not None
        assert len(write_config.inputs) == 2
        assert len(write_config.outputs) == 2

        # Verify Delete File config
        delete_config = schema.get_config("Delete File")
        assert delete_config is not None
        assert len(delete_config.inputs) == 1
        assert len(delete_config.outputs) == 1


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestDynamicPortConfigEdgeCases:
    """Edge case tests for dynamic port configuration."""

    def test_port_def_with_empty_name(self) -> None:
        """Test PortDef with empty name (edge case - should work)."""
        port = PortDef("", DataType.STRING)
        assert port.name == ""
        assert port.label == ""  # Empty name produces empty label

    def test_port_def_with_special_characters(self) -> None:
        """Test PortDef with special characters in name."""
        port = PortDef("file_path_1", DataType.STRING)
        assert port.name == "file_path_1"
        assert port.label == "File Path 1"

    def test_schema_case_sensitive_actions(self) -> None:
        """Test that action names are case-sensitive."""
        schema = DynamicPortSchema()
        schema.register("Read", ActionPortConfig())
        schema.register(
            "read", ActionPortConfig.create(inputs=[PortDef("x", DataType.STRING)])
        )

        # Both should exist as separate entries
        assert schema.has_action("Read")
        assert schema.has_action("read")
        assert len(schema.get_actions()) == 2

        # They should have different configs
        upper_config = schema.get_config("Read")
        lower_config = schema.get_config("read")
        assert upper_config is not None
        assert lower_config is not None
        assert len(upper_config.inputs) == 0
        assert len(lower_config.inputs) == 1

    def test_port_def_preserves_explicit_label(self) -> None:
        """Test that explicit label is not overwritten by auto-generation."""
        port = PortDef(
            name="file_path",
            data_type=DataType.STRING,
            label="My Custom Label",
        )
        assert port.label == "My Custom Label"
