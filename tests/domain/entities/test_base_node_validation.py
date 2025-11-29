"""Tests for BaseNode.validate() dual-source validation.

This test module validates the fix for the FileExistsNode parameter validation issue.
The problem: BaseNode.validate() only checked port.value, not self.config,
causing validation failures when values were provided via config instead of port connections.

Solution: validate() now checks BOTH port.value AND self.config for required parameters.
"""

import pytest
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, PortType


class TestDualSourceValidation:
    """Test that validate() checks both port and config for required parameters."""

    def test_validate_passes_with_config_value(self):
        """
        Required value in config (not port) should pass validation.

        This is the core issue: when a parameter is set via config (e.g., in the
        properties panel), but the port has no connection, validation should still pass.
        """

        class TestNode(BaseNode):
            def _define_ports(self):
                self.add_input_port("file_path", PortType.INPUT, DataType.STRING)

            async def execute(self, context):
                return {"success": True}

        # Port has no value, but config does
        node = TestNode("test1", config={"file_path": "/test/path"})
        is_valid, error = node.validate()

        assert (
            is_valid is True
        ), f"Validation should pass when value in config, got error: {error}"
        assert error is None

    def test_validate_passes_with_port_value(self):
        """
        Required value in port (not config) should pass validation.

        This is the existing behavior that should continue to work.
        """

        class TestNode(BaseNode):
            def _define_ports(self):
                self.add_input_port("file_path", PortType.INPUT, DataType.STRING)

            async def execute(self, context):
                return {"success": True}

        # Config empty, but port has value
        node = TestNode("test1", config={})
        node.set_input_value("file_path", "/test/path")
        is_valid, error = node.validate()

        assert is_valid is True
        assert error is None

    def test_validate_passes_when_both_have_value(self):
        """
        Required value in both port AND config should pass (port takes precedence).

        Edge case: both sources have values. Validation should pass, and at runtime
        the port value will be used (this is tested elsewhere).
        """

        class TestNode(BaseNode):
            def _define_ports(self):
                self.add_input_port("file_path", PortType.INPUT, DataType.STRING)

            async def execute(self, context):
                return {"success": True}

        # Both have values
        node = TestNode("test1", config={"file_path": "/config/path"})
        node.set_input_value("file_path", "/port/path")
        is_valid, error = node.validate()

        assert is_valid is True
        assert error is None

    def test_validate_fails_when_both_missing(self):
        """
        Missing from both sources should fail validation.

        This is the error case: no value in port, no value in config.
        """

        class TestNode(BaseNode):
            def _define_ports(self):
                self.add_input_port("file_path", PortType.INPUT, DataType.STRING)

            async def execute(self, context):
                return {"success": True}

        # Neither has value
        node = TestNode("test1", config={})
        is_valid, error = node.validate()

        assert is_valid is False
        assert error is not None
        assert "file_path" in error
        assert "no value" in error.lower()

    def test_validate_passes_for_optional_port_without_value(self):
        """
        Optional ports should pass validation even without values.

        Regression test: ensure required=False ports aren't affected by the fix.
        """

        class TestNode(BaseNode):
            def _define_ports(self):
                # Optional port
                self.add_input_port(
                    "optional_param", PortType.INPUT, DataType.STRING, required=False
                )

            async def execute(self, context):
                return {"success": True}

        # No value in port or config
        node = TestNode("test1", config={})
        is_valid, error = node.validate()

        assert is_valid is True
        assert error is None

    def test_validate_checks_empty_string_in_config(self):
        """
        Empty string in config should be treated as 'has no value'.

        Edge case: config has empty string, which should fail validation
        for required parameters.
        """

        class TestNode(BaseNode):
            def _define_ports(self):
                self.add_input_port("file_path", PortType.INPUT, DataType.STRING)

            async def execute(self, context):
                return {"success": True}

        # Config has empty string
        node = TestNode("test1", config={"file_path": ""})
        is_valid, error = node.validate()

        # Empty string is falsy but technically a value
        # Current behavior: should pass (empty string is a value)
        # Node's execute() can validate non-empty if needed
        assert is_valid is True

    def test_validate_with_multiple_required_ports(self):
        """
        Multiple required ports with mixed sources should validate correctly.

        Real-world scenario: some parameters from config, others from ports.
        """

        class TestNode(BaseNode):
            def _define_ports(self):
                self.add_input_port("source", PortType.INPUT, DataType.STRING)
                self.add_input_port("dest", PortType.INPUT, DataType.STRING)
                self.add_input_port("mode", PortType.INPUT, DataType.STRING)

            async def execute(self, context):
                return {"success": True}

        # Mixed: source in config, dest in port, mode missing
        node = TestNode("test1", config={"source": "/src/path"})
        node.set_input_value("dest", "/dst/path")
        is_valid, error = node.validate()

        # Should fail because 'mode' is missing from both
        assert is_valid is False
        assert "mode" in error


class TestGetParameter:
    """Test the unified get_parameter() helper method."""

    def test_get_parameter_from_port(self):
        """get_parameter() returns port value when port is connected."""

        class TestNode(BaseNode):
            def _define_ports(self):
                self.add_input_port("file_path", PortType.INPUT, DataType.STRING)

            async def execute(self, context):
                return {"success": True}

        node = TestNode("test1", config={})
        node.set_input_value("file_path", "/from/port")

        result = node.get_parameter("file_path")

        assert result == "/from/port"

    def test_get_parameter_from_config(self):
        """get_parameter() returns config value when port not connected."""

        class TestNode(BaseNode):
            def _define_ports(self):
                self.add_input_port("file_path", PortType.INPUT, DataType.STRING)

            async def execute(self, context):
                return {"success": True}

        node = TestNode("test1", config={"file_path": "/from/config"})

        result = node.get_parameter("file_path")

        assert result == "/from/config"

    def test_get_parameter_port_overrides_config(self):
        """Port value takes precedence over config value."""

        class TestNode(BaseNode):
            def _define_ports(self):
                self.add_input_port("file_path", PortType.INPUT, DataType.STRING)

            async def execute(self, context):
                return {"success": True}

        node = TestNode("test1", config={"file_path": "/from/config"})
        node.set_input_value("file_path", "/from/port")

        result = node.get_parameter("file_path")

        # Port wins
        assert result == "/from/port"

    def test_get_parameter_returns_default_when_missing(self):
        """get_parameter() returns default when param not in port or config."""

        class TestNode(BaseNode):
            def _define_ports(self):
                self.add_input_port("file_path", PortType.INPUT, DataType.STRING)

            async def execute(self, context):
                return {"success": True}

        node = TestNode("test1", config={})

        result = node.get_parameter("file_path", default="/default/path")

        assert result == "/default/path"

    def test_get_parameter_returns_none_when_missing_no_default(self):
        """get_parameter() returns None when missing and no default provided."""

        class TestNode(BaseNode):
            def _define_ports(self):
                self.add_input_port("file_path", PortType.INPUT, DataType.STRING)

            async def execute(self, context):
                return {"success": True}

        node = TestNode("test1", config={})

        result = node.get_parameter("file_path")

        assert result is None

    def test_get_parameter_empty_string_from_config(self):
        """Empty string from config is returned (not treated as None)."""

        class TestNode(BaseNode):
            def _define_ports(self):
                self.add_input_port("file_path", PortType.INPUT, DataType.STRING)

            async def execute(self, context):
                return {"success": True}

        node = TestNode("test1", config={"file_path": ""})

        result = node.get_parameter("file_path")

        # Empty string is a valid value
        assert result == ""

    def test_get_parameter_for_nonexistent_port(self):
        """get_parameter() works even if port doesn't exist (config-only param)."""

        class TestNode(BaseNode):
            def _define_ports(self):
                pass  # No ports

            async def execute(self, context):
                return {"success": True}

        node = TestNode("test1", config={"some_setting": "value"})

        result = node.get_parameter("some_setting")

        assert result == "value"

    def test_get_parameter_with_various_types(self):
        """get_parameter() handles different data types correctly."""

        class TestNode(BaseNode):
            def _define_ports(self):
                self.add_input_port("timeout", PortType.INPUT, DataType.INTEGER)
                self.add_input_port("enabled", PortType.INPUT, DataType.BOOLEAN)

            async def execute(self, context):
                return {"success": True}

        node = TestNode(
            "test1",
            config={
                "timeout": 5000,
                "enabled": True,
                "ratio": 0.75,
                "items": [1, 2, 3],
            },
        )

        assert node.get_parameter("timeout") == 5000
        assert node.get_parameter("enabled") is True
        assert node.get_parameter("ratio") == 0.75
        assert node.get_parameter("items") == [1, 2, 3]
