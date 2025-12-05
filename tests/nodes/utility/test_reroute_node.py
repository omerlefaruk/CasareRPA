"""
Tests for RerouteNode - Houdini-style passthrough dot node.

Tests cover:
- SUCCESS: Basic passthrough behavior for various data types
- ERROR: Exception handling during execution
- EDGE_CASES: Exec flow mode, None values, type configuration

RerouteNode acts as a passthrough waypoint for organizing workflow connections.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from casare_rpa.nodes.utility_nodes import RerouteNode
from casare_rpa.domain.value_objects.types import DataType, NodeStatus


class TestRerouteNodeInitialization:
    """Tests for RerouteNode initialization."""

    def test_init_with_node_id(self) -> None:
        """RerouteNode initializes with node_id."""
        node = RerouteNode(node_id="reroute_1")
        assert node.node_id == "reroute_1"
        assert node.name == "Reroute"
        assert node.node_type == "RerouteNode"
        assert node.category == "utility"

    def test_init_with_custom_name(self) -> None:
        """RerouteNode accepts custom name."""
        node = RerouteNode(node_id="reroute_1", name="My Reroute")
        assert node.name == "My Reroute"

    def test_init_default_config(self) -> None:
        """RerouteNode has correct default config."""
        node = RerouteNode(node_id="reroute_1")
        assert node.config.get("data_type") == "ANY"
        assert node.config.get("is_exec_reroute") is False

    def test_init_with_data_type_config(self) -> None:
        """RerouteNode accepts data_type in config."""
        node = RerouteNode(
            node_id="reroute_1",
            config={"data_type": "STRING"},
        )
        assert node.config.get("data_type") == "STRING"

    def test_init_with_exec_mode_config(self) -> None:
        """RerouteNode accepts is_exec_reroute in config."""
        node = RerouteNode(
            node_id="reroute_1",
            config={"is_exec_reroute": True},
        )
        assert node.config.get("is_exec_reroute") is True

    def test_description_set(self) -> None:
        """RerouteNode has description."""
        node = RerouteNode(node_id="reroute_1")
        assert node.description == "Passthrough dot for organizing connections"


class TestRerouteNodePorts:
    """Tests for RerouteNode port definitions."""

    def test_has_input_port(self) -> None:
        """RerouteNode has 'in' input port."""
        node = RerouteNode(node_id="reroute_1")
        # Check input_ports dict
        assert "in" in node.input_ports

    def test_has_output_port(self) -> None:
        """RerouteNode has 'out' output port."""
        node = RerouteNode(node_id="reroute_1")
        # Check output_ports dict
        assert "out" in node.output_ports

    def test_input_port_accepts_any(self) -> None:
        """Input port accepts ANY data type."""
        node = RerouteNode(node_id="reroute_1")
        in_port = node.input_ports.get("in")
        assert in_port is not None
        assert in_port.data_type == DataType.ANY

    def test_output_port_any_type(self) -> None:
        """Output port is ANY data type."""
        node = RerouteNode(node_id="reroute_1")
        out_port = node.output_ports.get("out")
        assert out_port is not None
        assert out_port.data_type == DataType.ANY


class TestRerouteNodeExecuteSuccess:
    """Tests for RerouteNode successful execution (happy path)."""

    @pytest.mark.asyncio
    async def test_passthrough_string_value(self, execution_context) -> None:
        """RerouteNode passes through string values unchanged."""
        node = RerouteNode(node_id="reroute_1")
        # Use set_input_value to set the port value
        node.set_input_value("in", "test string")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["value"] == "test string"
        assert node.get_output_value("out") == "test string"
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_passthrough_integer_value(self, execution_context) -> None:
        """RerouteNode passes through integer values unchanged."""
        node = RerouteNode(node_id="reroute_1")
        node.set_input_value("in", 42)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["value"] == 42
        assert node.get_output_value("out") == 42

    @pytest.mark.asyncio
    async def test_passthrough_dict_value(self, execution_context) -> None:
        """RerouteNode passes through dict values unchanged."""
        node = RerouteNode(node_id="reroute_1")
        test_dict = {"key": "value", "nested": {"a": 1}}
        node.set_input_value("in", test_dict)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["value"] == test_dict
        assert node.get_output_value("out") == test_dict

    @pytest.mark.asyncio
    async def test_passthrough_list_value(self, execution_context) -> None:
        """RerouteNode passes through list values unchanged."""
        node = RerouteNode(node_id="reroute_1")
        test_list = [1, "two", 3.0, {"four": 4}]
        node.set_input_value("in", test_list)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["value"] == test_list
        assert node.get_output_value("out") == test_list

    @pytest.mark.asyncio
    async def test_passthrough_boolean_value(self, execution_context) -> None:
        """RerouteNode passes through boolean values unchanged."""
        node = RerouteNode(node_id="reroute_1")
        node.set_input_value("in", True)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["value"] is True
        assert node.get_output_value("out") is True

    @pytest.mark.asyncio
    async def test_passthrough_none_value(self, execution_context) -> None:
        """RerouteNode passes through None unchanged."""
        node = RerouteNode(node_id="reroute_1")
        node.set_input_value("in", None)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["value"] is None
        assert node.get_output_value("out") is None

    @pytest.mark.asyncio
    async def test_data_reroute_next_nodes(self, execution_context) -> None:
        """Data reroute returns 'out' as next node."""
        node = RerouteNode(node_id="reroute_1")
        node.set_input_value("in", "test")

        result = await node.execute(execution_context)

        assert result["next_nodes"] == ["out"]

    @pytest.mark.asyncio
    async def test_exec_reroute_next_nodes(self, execution_context) -> None:
        """Exec reroute returns 'exec_out' as next node."""
        node = RerouteNode(node_id="reroute_1", config={"is_exec_reroute": True})
        node.set_input_value("in", "test")

        result = await node.execute(execution_context)

        assert result["next_nodes"] == ["exec_out"]


class TestRerouteNodeDataType:
    """Tests for RerouteNode data type configuration."""

    def test_set_data_type_string(self) -> None:
        """set_data_type updates config for STRING."""
        node = RerouteNode(node_id="reroute_1")
        node.set_data_type(DataType.STRING)
        # DataType.STRING.value is an int, but set_data_type stores the name
        assert node.config["data_type"] == DataType.STRING.value

    def test_set_data_type_integer(self) -> None:
        """set_data_type updates config for INTEGER."""
        node = RerouteNode(node_id="reroute_1")
        node.set_data_type(DataType.INTEGER)
        assert node.config["data_type"] == DataType.INTEGER.value

    def test_set_data_type_none_sets_any(self) -> None:
        """set_data_type with None sets ANY."""
        node = RerouteNode(node_id="reroute_1")
        node.set_data_type(None)
        assert node.config["data_type"] == "ANY"

    def test_get_data_type_returns_correct_type(self) -> None:
        """get_data_type returns correct DataType enum."""
        node = RerouteNode(node_id="reroute_1")
        node.config["data_type"] = DataType.BOOLEAN.value
        assert node.get_data_type() == DataType.BOOLEAN

    def test_get_data_type_default_any(self) -> None:
        """get_data_type returns ANY by default."""
        node = RerouteNode(node_id="reroute_1")
        assert node.get_data_type() == DataType.ANY

    def test_get_data_type_invalid_string_returns_any(self) -> None:
        """get_data_type returns ANY for invalid type string."""
        node = RerouteNode(node_id="reroute_1")
        node.config["data_type"] = "INVALID_TYPE"
        assert node.get_data_type() == DataType.ANY


class TestRerouteNodeExecMode:
    """Tests for RerouteNode execution flow mode."""

    def test_set_exec_mode_true(self) -> None:
        """set_exec_mode updates config to True."""
        node = RerouteNode(node_id="reroute_1")
        node.set_exec_mode(True)
        assert node.config["is_exec_reroute"] is True

    def test_set_exec_mode_false(self) -> None:
        """set_exec_mode updates config to False."""
        node = RerouteNode(node_id="reroute_1", config={"is_exec_reroute": True})
        node.set_exec_mode(False)
        assert node.config["is_exec_reroute"] is False

    @pytest.mark.asyncio
    async def test_exec_mode_affects_next_nodes(self, execution_context) -> None:
        """Exec mode changes next_nodes in result."""
        node = RerouteNode(node_id="reroute_1")
        node.set_input_value("in", "test")

        # Data mode
        result_data = await node.execute(execution_context)
        assert result_data["next_nodes"] == ["out"]

        # Switch to exec mode
        node.set_exec_mode(True)
        node.status = None  # Reset status
        result_exec = await node.execute(execution_context)
        assert result_exec["next_nodes"] == ["exec_out"]


class TestRerouteNodeError:
    """Tests for RerouteNode error handling (sad path)."""

    @pytest.mark.asyncio
    async def test_execution_error_handling(self, execution_context) -> None:
        """RerouteNode handles execution errors gracefully."""
        node = RerouteNode(node_id="reroute_1")

        # Force an error by making get_input_value raise an exception
        original_get = node.get_input_value
        node.get_input_value = Mock(side_effect=RuntimeError("Test error"))

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result
        assert "Test error" in result["error"]
        assert node.status == NodeStatus.ERROR

        # Restore original method
        node.get_input_value = original_get


class TestRerouteNodeEdgeCases:
    """Tests for RerouteNode edge cases."""

    @pytest.mark.asyncio
    async def test_passthrough_complex_object(self, execution_context) -> None:
        """RerouteNode passes through complex objects."""
        node = RerouteNode(node_id="reroute_1")
        complex_obj = {
            "data": [1, 2, 3],
            "nested": {"level1": {"level2": "deep"}},
            "mixed": [{"a": 1}, {"b": 2}],
        }
        node.set_input_value("in", complex_obj)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["value"] == complex_obj

    @pytest.mark.asyncio
    async def test_passthrough_empty_string(self, execution_context) -> None:
        """RerouteNode passes through empty string."""
        node = RerouteNode(node_id="reroute_1")
        node.set_input_value("in", "")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["value"] == ""

    @pytest.mark.asyncio
    async def test_passthrough_empty_list(self, execution_context) -> None:
        """RerouteNode passes through empty list."""
        node = RerouteNode(node_id="reroute_1")
        node.set_input_value("in", [])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["value"] == []

    @pytest.mark.asyncio
    async def test_passthrough_empty_dict(self, execution_context) -> None:
        """RerouteNode passes through empty dict."""
        node = RerouteNode(node_id="reroute_1")
        node.set_input_value("in", {})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["value"] == {}

    @pytest.mark.asyncio
    async def test_passthrough_zero(self, execution_context) -> None:
        """RerouteNode passes through zero correctly."""
        node = RerouteNode(node_id="reroute_1")
        node.set_input_value("in", 0)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["value"] == 0

    @pytest.mark.asyncio
    async def test_passthrough_false_boolean(self, execution_context) -> None:
        """RerouteNode passes through False correctly."""
        node = RerouteNode(node_id="reroute_1")
        node.set_input_value("in", False)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["value"] is False

    def test_node_has_correct_category(self) -> None:
        """RerouteNode has 'utility' category."""
        node = RerouteNode(node_id="reroute_1")
        assert node.category == "utility"

    @pytest.mark.asyncio
    async def test_status_transitions(self, execution_context) -> None:
        """RerouteNode correctly transitions through RUNNING to SUCCESS."""
        node = RerouteNode(node_id="reroute_1")
        node.set_input_value("in", "test")

        # Before execution
        initial_status = node.status

        # After execution
        await node.execute(execution_context)

        assert node.status == NodeStatus.SUCCESS
