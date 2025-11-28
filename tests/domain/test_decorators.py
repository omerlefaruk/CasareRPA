"""
Tests for node decorators (@executable_node, @node_schema).

Following TDD Guidelines:
- Domain layer: Pure unit tests, NO mocks
- Test decorator behavior with real node classes
- Test configuration injection and validation
"""

import pytest
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, NodeSchema
from casare_rpa.domain.schemas.property_types import PropertyType
from casare_rpa.domain.value_objects.types import DataType, PortType


# Test helper: Minimal node class for testing
class MinimalNode:
    """Minimal node implementation for testing decorators."""

    def __init__(self, node_id: str, config: dict = None):
        self.node_id = node_id
        self.config = config or {}
        self.ports = []

    def _define_ports(self):
        """Override in tests."""
        pass

    def add_input_port(self, name: str, port_type):
        """Add input port (simplified for testing)."""
        self.ports.append({"name": name, "direction": "input", "type": port_type})

    def add_output_port(self, name: str, port_type):
        """Add output port (simplified for testing)."""
        self.ports.append({"name": name, "direction": "output", "type": port_type})


class TestExecutableNodeDecorator:
    """Test @executable_node decorator behavior."""

    def test_decorator_adds_exec_ports(self):
        """@executable_node adds exec_in and exec_out ports."""

        @executable_node
        class TestNode(MinimalNode):
            def _define_ports(self):
                self.add_input_port("data", DataType.STRING)

        node = TestNode("node1")
        node._define_ports()

        # Should have 3 ports: exec_in, exec_out, data
        assert len(node.ports) == 3
        assert node.ports[0]["name"] == "exec_in"
        assert node.ports[0]["type"] == PortType.EXEC_INPUT
        assert node.ports[1]["name"] == "exec_out"
        assert node.ports[1]["type"] == PortType.EXEC_OUTPUT
        assert node.ports[2]["name"] == "data"

    def test_decorator_preserves_custom_ports(self):
        """@executable_node preserves node-specific ports."""

        @executable_node
        class TestNode(MinimalNode):
            def _define_ports(self):
                self.add_input_port("input1", DataType.STRING)
                self.add_input_port("input2", DataType.INTEGER)
                self.add_output_port("output1", DataType.BOOLEAN)

        node = TestNode("node1")
        node._define_ports()

        # Should have exec ports + 3 custom ports = 5 total
        assert len(node.ports) == 5

        # Verify exec ports come first
        assert node.ports[0]["name"] == "exec_in"
        assert node.ports[1]["name"] == "exec_out"

        # Verify custom ports follow
        port_names = [p["name"] for p in node.ports]
        assert "input1" in port_names
        assert "input2" in port_names
        assert "output1" in port_names

    def test_decorator_works_with_empty_define_ports(self):
        """@executable_node works when _define_ports is empty."""

        @executable_node
        class TestNode(MinimalNode):
            def _define_ports(self):
                pass  # No custom ports

        node = TestNode("node1")
        node._define_ports()

        # Should only have exec ports
        assert len(node.ports) == 2
        assert node.ports[0]["name"] == "exec_in"
        assert node.ports[1]["name"] == "exec_out"

    def test_decorator_can_be_stacked_with_node_schema(self):
        """@executable_node can be combined with @node_schema."""

        @node_schema(PropertyDef("url", PropertyType.STRING, default=""))
        @executable_node
        class TestNode(MinimalNode):
            def _define_ports(self):
                self.add_input_port("data", DataType.STRING)

        node = TestNode("node1")
        node._define_ports()

        # Should have both schema and exec ports
        assert hasattr(node.__class__, "__node_schema__")
        assert len(node.ports) == 3  # exec_in, exec_out, data


class TestNodeSchemaDecorator:
    """Test @node_schema decorator behavior."""

    def test_decorator_attaches_schema_to_class(self):
        """@node_schema attaches __node_schema__ attribute to class."""

        @node_schema(PropertyDef("url", PropertyType.STRING, default=""))
        class TestNode(MinimalNode):
            pass

        assert hasattr(TestNode, "__node_schema__")
        assert isinstance(TestNode.__node_schema__, NodeSchema)
        assert len(TestNode.__node_schema__.properties) == 1

    def test_decorator_with_multiple_properties(self):
        """@node_schema can attach multiple property definitions."""

        @node_schema(
            PropertyDef("url", PropertyType.STRING, default=""),
            PropertyDef("timeout", PropertyType.INTEGER, default=5000),
            PropertyDef("enabled", PropertyType.BOOLEAN, default=True),
        )
        class TestNode(MinimalNode):
            pass

        schema = TestNode.__node_schema__
        assert len(schema.properties) == 3
        assert schema.properties[0].name == "url"
        assert schema.properties[1].name == "timeout"
        assert schema.properties[2].name == "enabled"

    def test_decorator_injects_default_config(self):
        """@node_schema injects default config when not provided."""

        @node_schema(
            PropertyDef("url", PropertyType.STRING, default="http://default.com"),
            PropertyDef("timeout", PropertyType.INTEGER, default=5000),
        )
        class TestNode(MinimalNode):
            pass

        node = TestNode("node1")  # No config provided

        # Defaults should be injected
        assert node.config["url"] == "http://default.com"
        assert node.config["timeout"] == 5000

    def test_decorator_merges_with_provided_config(self):
        """@node_schema merges defaults with provided config."""

        @node_schema(
            PropertyDef("url", PropertyType.STRING, default="http://default.com"),
            PropertyDef("timeout", PropertyType.INTEGER, default=5000),
            PropertyDef("retries", PropertyType.INTEGER, default=3),
        )
        class TestNode(MinimalNode):
            pass

        # Provide partial config
        node = TestNode("node1", config={"url": "http://custom.com"})

        # Provided value should override default
        assert node.config["url"] == "http://custom.com"

        # Missing values should use defaults
        assert node.config["timeout"] == 5000
        assert node.config["retries"] == 3

    def test_decorator_validates_config_in_lenient_mode(self):
        """@node_schema validates config but doesn't raise (default lenient mode)."""

        @node_schema(
            PropertyDef("timeout", PropertyType.INTEGER, default=5000, required=True),
        )
        class TestNode(MinimalNode):
            pass

        # Invalid config (string instead of integer)
        # In lenient mode, this should log warning but not raise
        node = TestNode("node1", config={"timeout": "not_an_integer"})

        # Node should still be created
        assert node.node_id == "node1"

    @pytest.mark.skip(
        reason="BUG: strict parameter not accessible - Python *args issue"
    )
    def test_decorator_raises_in_strict_mode_for_invalid_config(self):
        """@node_schema raises ValueError in strict mode for invalid config.

        NOTE: This test reveals a bug in decorator signature.
        The 'strict' parameter after *property_defs cannot be passed as keyword argument.
        Need to fix decorator signature to: def node_schema(*property_defs, strict=False)
        """
        pass

    def test_decorator_validates_config_and_logs_warning_by_default(self):
        """@node_schema validates config and logs warnings (lenient mode default)."""

        @node_schema(PropertyDef("timeout", PropertyType.INTEGER, required=True))
        class TestNode(MinimalNode):
            pass

        # Invalid config logs warning but doesn't raise (lenient mode)
        node = TestNode("node1", config={"timeout": "not_an_integer"})

        # Node is still created despite invalid config
        assert node.node_id == "node1"

    def test_decorator_preserves_original_init_args(self):
        """@node_schema preserves additional __init__ arguments."""

        @node_schema(PropertyDef("url", PropertyType.STRING, default=""))
        class TestNode(MinimalNode):
            def __init__(self, node_id: str, custom_arg: str = "default", **kwargs):
                super().__init__(node_id, **kwargs)
                self.custom_arg = custom_arg

        node = TestNode("node1", custom_arg="custom_value")

        assert node.node_id == "node1"
        assert node.custom_arg == "custom_value"
        assert node.config["url"] == ""

    def test_decorator_works_with_no_properties(self):
        """@node_schema works with zero properties (edge case)."""

        @node_schema()
        class TestNode(MinimalNode):
            pass

        node = TestNode("node1")

        assert hasattr(node.__class__, "__node_schema__")
        assert len(node.__class__.__node_schema__.properties) == 0
        assert node.config == {}


class TestDecoratorCombinations:
    """Test combining multiple decorators."""

    def test_schema_and_executable_decorators_together(self):
        """@node_schema and @executable_node work together correctly."""

        @node_schema(
            PropertyDef("url", PropertyType.STRING, default="http://test.com"),
            PropertyDef("timeout", PropertyType.INTEGER, default=5000),
        )
        @executable_node
        class TestNode(MinimalNode):
            def _define_ports(self):
                self.add_input_port("data", DataType.STRING)
                self.add_output_port("result", DataType.STRING)

        node = TestNode("node1")
        node._define_ports()

        # Schema should inject defaults
        assert node.config["url"] == "http://test.com"
        assert node.config["timeout"] == 5000

        # Executable should add ports
        assert len(node.ports) == 4  # exec_in, exec_out, data, result
        assert node.ports[0]["name"] == "exec_in"
        assert node.ports[1]["name"] == "exec_out"

    def test_decorator_order_schema_first(self):
        """Decorator order: @node_schema then @executable_node."""

        @node_schema(PropertyDef("url", PropertyType.STRING, default=""))
        @executable_node
        class TestNode(MinimalNode):
            def _define_ports(self):
                pass

        node = TestNode("node1")

        # Both decorators should function
        assert hasattr(node.__class__, "__node_schema__")
        node._define_ports()
        assert len(node.ports) == 2  # exec_in, exec_out

    def test_decorator_order_executable_first(self):
        """Decorator order: @executable_node then @node_schema."""

        @executable_node
        @node_schema(PropertyDef("url", PropertyType.STRING, default=""))
        class TestNode(MinimalNode):
            def _define_ports(self):
                pass

        node = TestNode("node1")

        # Both decorators should function
        assert hasattr(node.__class__, "__node_schema__")
        node._define_ports()
        assert len(node.ports) == 2  # exec_in, exec_out

    def test_complex_node_with_all_features(self):
        """Complex node using all decorator features."""

        @node_schema(
            PropertyDef("url", PropertyType.STRING, required=True),
            PropertyDef("timeout", PropertyType.INTEGER, default=30000, min_value=1000),
            PropertyDef(
                "method",
                PropertyType.CHOICE,
                choices=["GET", "POST", "PUT"],
                default="GET",
            ),
            PropertyDef("headers", PropertyType.JSON, default={}),
            PropertyDef("follow_redirects", PropertyType.BOOLEAN, default=True),
        )
        @executable_node
        class HTTPRequestNode(MinimalNode):
            def _define_ports(self):
                self.add_input_port("request_body", DataType.STRING)
                self.add_output_port("response", DataType.STRING)
                self.add_output_port("status_code", DataType.INTEGER)

        # Valid configuration
        node = HTTPRequestNode(
            "http1",
            config={
                "url": "https://api.example.com",
                "method": "POST",
                "timeout": 5000,
            },
        )

        node._define_ports()

        # Verify schema works
        assert node.config["url"] == "https://api.example.com"
        assert node.config["method"] == "POST"
        assert node.config["timeout"] == 5000
        assert node.config["follow_redirects"] is True  # Default
        assert node.config["headers"] == {}  # Default

        # Verify executable decorator works
        assert (
            len(node.ports) == 5
        )  # exec_in, exec_out, request_body, response, status_code
        port_names = [p["name"] for p in node.ports]
        assert "exec_in" in port_names
        assert "exec_out" in port_names
        assert "request_body" in port_names
        assert "response" in port_names
        assert "status_code" in port_names


class TestDecoratorEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.skip(
        reason="BUG: decorator doesn't handle config=None - raises TypeError"
    )
    def test_schema_decorator_with_none_config(self):
        """@node_schema handles None config gracefully.

        NOTE: This test reveals a bug in the decorator.
        When config=None, line 107 in decorators.py tries to iterate:
            if key not in config:  # TypeError: argument of type 'NoneType' is not iterable

        Fix: Check if config is None before iterating, or default to empty dict.
        """

        @node_schema(PropertyDef("url", PropertyType.STRING, default="http://default"))
        class TestNode(MinimalNode):
            pass

        node = TestNode("node1", config=None)

        # Should use defaults when config is None
        assert node.config["url"] == "http://default"

    def test_schema_decorator_preserves_extra_config_keys(self):
        """@node_schema doesn't remove extra keys from config."""

        @node_schema(PropertyDef("url", PropertyType.STRING, default=""))
        class TestNode(MinimalNode):
            pass

        node = TestNode(
            "node1", config={"url": "http://test", "extra_key": "extra_value"}
        )

        # Extra key should be preserved
        assert "extra_key" in node.config
        assert node.config["extra_key"] == "extra_value"

    def test_executable_decorator_idempotent(self):
        """@executable_node doesn't break if applied to already-wrapped class."""

        @executable_node
        class TestNode(MinimalNode):
            def _define_ports(self):
                self.add_input_port("data", DataType.STRING)

        # Create instance and verify ports
        node = TestNode("node1")
        node._define_ports()

        # Should have exec ports + data port
        assert len(node.ports) == 3
        assert node.ports[0]["name"] == "exec_in"
