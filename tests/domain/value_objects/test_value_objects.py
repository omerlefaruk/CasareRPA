"""
Tests for domain value objects.
Covers Port, types (enums, type aliases), and constants.
"""

import pytest
from typing import Any

from casare_rpa.domain.value_objects.port import Port
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    PortType,
    DataType,
    ExecutionMode,
    EventType,
    ErrorCode,
    SCHEMA_VERSION,
    DEFAULT_TIMEOUT,
    MAX_RETRIES,
    EXEC_IN_PORT,
    EXEC_OUT_PORT,
)


# ============================================================================
# Port Tests
# ============================================================================


class TestPortCreation:
    """Tests for Port initialization."""

    def test_create_input_port(self) -> None:
        """Create input data port."""
        port = Port(
            name="data_in",
            port_type=PortType.INPUT,
            data_type=DataType.STRING,
        )
        assert port.name == "data_in"
        assert port.port_type == PortType.INPUT
        assert port.data_type == DataType.STRING
        assert port.required is True

    def test_create_output_port(self) -> None:
        """Create output data port."""
        port = Port(
            name="result",
            port_type=PortType.OUTPUT,
            data_type=DataType.ANY,
        )
        assert port.port_type == PortType.OUTPUT

    def test_create_exec_input_port(self) -> None:
        """Create execution input port."""
        port = Port(
            name="exec_in",
            port_type=PortType.EXEC_INPUT,
            data_type=DataType.ANY,
        )
        assert port.port_type == PortType.EXEC_INPUT

    def test_create_exec_output_port(self) -> None:
        """Create execution output port."""
        port = Port(
            name="exec_out",
            port_type=PortType.EXEC_OUTPUT,
            data_type=DataType.ANY,
        )
        assert port.port_type == PortType.EXEC_OUTPUT

    def test_create_with_label(self) -> None:
        """Create port with custom label."""
        port = Port(
            name="input_1",
            port_type=PortType.INPUT,
            data_type=DataType.STRING,
            label="Input 1",
        )
        assert port.label == "Input 1"

    def test_default_label_is_name(self) -> None:
        """Default label is port name."""
        port = Port(
            name="my_port",
            port_type=PortType.INPUT,
            data_type=DataType.ANY,
        )
        assert port.label == "my_port"

    def test_create_optional_port(self) -> None:
        """Create optional (non-required) port."""
        port = Port(
            name="optional_in",
            port_type=PortType.INPUT,
            data_type=DataType.STRING,
            required=False,
        )
        assert port.required is False


class TestPortProperties:
    """Tests for Port property accessors."""

    def test_name_immutable(self) -> None:
        """Name property is read-only."""
        port = Port("test", PortType.INPUT, DataType.ANY)
        assert port.name == "test"
        # No setter, so cannot modify

    def test_port_type_immutable(self) -> None:
        """Port type is read-only."""
        port = Port("test", PortType.INPUT, DataType.ANY)
        assert port.port_type == PortType.INPUT

    def test_data_type_immutable(self) -> None:
        """Data type is read-only."""
        port = Port("test", PortType.INPUT, DataType.STRING)
        assert port.data_type == DataType.STRING

    def test_label_immutable(self) -> None:
        """Label is read-only."""
        port = Port("test", PortType.INPUT, DataType.ANY, label="Test")
        assert port.label == "Test"

    def test_required_immutable(self) -> None:
        """Required flag is read-only."""
        port = Port("test", PortType.INPUT, DataType.ANY, required=True)
        assert port.required is True


class TestPortValue:
    """Tests for Port value get/set."""

    def test_initial_value_none(self) -> None:
        """Initial value is None."""
        port = Port("test", PortType.INPUT, DataType.ANY)
        assert port.value is None

    def test_set_value(self) -> None:
        """Set port value."""
        port = Port("test", PortType.OUTPUT, DataType.STRING)
        port.set_value("hello")
        assert port.value == "hello"

    def test_get_value(self) -> None:
        """Get port value."""
        port = Port("test", PortType.OUTPUT, DataType.INTEGER)
        port.value = 42
        assert port.get_value() == 42

    def test_value_any_type(self) -> None:
        """Value can be any Python type."""
        port = Port("test", PortType.OUTPUT, DataType.ANY)
        port.set_value([1, 2, 3])
        assert port.get_value() == [1, 2, 3]

        port.set_value({"key": "value"})
        assert port.get_value() == {"key": "value"}


class TestPortSerialization:
    """Tests for Port to_dict/from_dict."""

    def test_to_dict(self) -> None:
        """Serialize port to dictionary."""
        port = Port(
            name="data",
            port_type=PortType.INPUT,
            data_type=DataType.STRING,
            label="Data Input",
            required=True,
        )
        data = port.to_dict()
        assert data["name"] == "data"
        assert data["port_type"] == "INPUT"
        assert data["data_type"] == "STRING"
        assert data["label"] == "Data Input"
        assert data["required"] is True

    def test_from_dict(self) -> None:
        """Deserialize port from dictionary."""
        data = {
            "name": "output",
            "port_type": "OUTPUT",
            "data_type": "INTEGER",
            "label": "Result",
            "required": False,
        }
        port = Port.from_dict(data)
        assert port.name == "output"
        assert port.port_type == PortType.OUTPUT
        assert port.data_type == DataType.INTEGER
        assert port.label == "Result"
        assert port.required is False

    def test_roundtrip(self) -> None:
        """Serialize then deserialize preserves data."""
        original = Port("test", PortType.EXEC_INPUT, DataType.ANY, "Test", True)
        data = original.to_dict()
        restored = Port.from_dict(data)
        assert original == restored


class TestPortEquality:
    """Tests for Port equality and hash."""

    def test_equal_ports(self) -> None:
        """Identical ports are equal."""
        port1 = Port("x", PortType.INPUT, DataType.STRING, "X", True)
        port2 = Port("x", PortType.INPUT, DataType.STRING, "X", True)
        assert port1 == port2

    def test_different_name(self) -> None:
        """Different name makes ports unequal."""
        port1 = Port("x", PortType.INPUT, DataType.STRING)
        port2 = Port("y", PortType.INPUT, DataType.STRING)
        assert port1 != port2

    def test_different_type(self) -> None:
        """Different port type makes ports unequal."""
        port1 = Port("x", PortType.INPUT, DataType.STRING)
        port2 = Port("x", PortType.OUTPUT, DataType.STRING)
        assert port1 != port2

    def test_different_data_type(self) -> None:
        """Different data type makes ports unequal."""
        port1 = Port("x", PortType.INPUT, DataType.STRING)
        port2 = Port("x", PortType.INPUT, DataType.INTEGER)
        assert port1 != port2

    def test_not_equal_to_non_port(self) -> None:
        """Port is not equal to non-Port object."""
        port = Port("x", PortType.INPUT, DataType.ANY)
        assert port != "x"
        assert port != {"name": "x"}

    def test_equal_ports_same_hash(self) -> None:
        """Equal ports have same hash."""
        port1 = Port("x", PortType.INPUT, DataType.STRING, "X", True)
        port2 = Port("x", PortType.INPUT, DataType.STRING, "X", True)
        assert hash(port1) == hash(port2)

    def test_usable_in_set(self) -> None:
        """Ports can be used in sets."""
        port1 = Port("x", PortType.INPUT, DataType.STRING)
        port2 = Port("x", PortType.INPUT, DataType.STRING)
        port3 = Port("y", PortType.INPUT, DataType.STRING)
        port_set = {port1, port2, port3}
        assert len(port_set) == 2


class TestPortRepr:
    """Tests for Port __repr__."""

    def test_repr(self) -> None:
        """String representation."""
        port = Port("data_in", PortType.INPUT, DataType.STRING, required=True)
        rep = repr(port)
        assert "Port" in rep
        assert "data_in" in rep
        assert "INPUT" in rep
        assert "STRING" in rep


# ============================================================================
# NodeStatus Enum Tests
# ============================================================================


class TestNodeStatus:
    """Tests for NodeStatus enum."""

    def test_all_statuses_exist(self) -> None:
        """All expected statuses exist."""
        assert NodeStatus.IDLE is not None
        assert NodeStatus.RUNNING is not None
        assert NodeStatus.SUCCESS is not None
        assert NodeStatus.ERROR is not None
        assert NodeStatus.SKIPPED is not None
        assert NodeStatus.CANCELLED is not None

    def test_status_values_unique(self) -> None:
        """All status values are unique."""
        statuses = [s.value for s in NodeStatus]
        assert len(statuses) == len(set(statuses))


# ============================================================================
# PortType Enum Tests
# ============================================================================


class TestPortTypeEnum:
    """Tests for PortType enum."""

    def test_all_types_exist(self) -> None:
        """All expected port types exist."""
        assert PortType.INPUT is not None
        assert PortType.OUTPUT is not None
        assert PortType.EXEC_INPUT is not None
        assert PortType.EXEC_OUTPUT is not None


# ============================================================================
# DataType Enum Tests
# ============================================================================


class TestDataType:
    """Tests for DataType enum."""

    def test_all_types_exist(self) -> None:
        """All expected data types exist."""
        assert DataType.STRING is not None
        assert DataType.INTEGER is not None
        assert DataType.FLOAT is not None
        assert DataType.BOOLEAN is not None
        assert DataType.LIST is not None
        assert DataType.DICT is not None
        assert DataType.ANY is not None
        assert DataType.ELEMENT is not None
        assert DataType.PAGE is not None
        assert DataType.BROWSER is not None


# ============================================================================
# ExecutionMode Enum Tests
# ============================================================================


class TestExecutionMode:
    """Tests for ExecutionMode enum."""

    def test_all_modes_exist(self) -> None:
        """All expected execution modes exist."""
        assert ExecutionMode.NORMAL is not None
        assert ExecutionMode.DEBUG is not None
        assert ExecutionMode.VALIDATE is not None


# ============================================================================
# EventType Enum Tests
# ============================================================================


class TestEventType:
    """Tests for EventType enum."""

    def test_node_events_exist(self) -> None:
        """Node-related events exist."""
        assert EventType.NODE_STARTED is not None
        assert EventType.NODE_COMPLETED is not None
        assert EventType.NODE_ERROR is not None
        assert EventType.NODE_SKIPPED is not None

    def test_workflow_events_exist(self) -> None:
        """Workflow-related events exist."""
        assert EventType.WORKFLOW_STARTED is not None
        assert EventType.WORKFLOW_COMPLETED is not None
        assert EventType.WORKFLOW_ERROR is not None
        assert EventType.WORKFLOW_STOPPED is not None
        assert EventType.WORKFLOW_PAUSED is not None
        assert EventType.WORKFLOW_RESUMED is not None

    def test_other_events_exist(self) -> None:
        """Other events exist."""
        assert EventType.VARIABLE_SET is not None
        assert EventType.LOG_MESSAGE is not None


# ============================================================================
# ErrorCode Enum Tests
# ============================================================================


class TestErrorCode:
    """Tests for ErrorCode enum."""

    def test_general_errors(self) -> None:
        """General error codes exist."""
        assert ErrorCode.UNKNOWN_ERROR.value < 2000
        assert ErrorCode.TIMEOUT.value < 2000
        assert ErrorCode.CANCELLED.value < 2000

    def test_browser_errors(self) -> None:
        """Browser error codes exist."""
        assert 2000 <= ErrorCode.BROWSER_NOT_FOUND.value < 3000
        assert 2000 <= ErrorCode.ELEMENT_NOT_FOUND.value < 3000

    def test_desktop_errors(self) -> None:
        """Desktop automation error codes exist."""
        assert 3000 <= ErrorCode.WINDOW_NOT_FOUND.value < 4000
        assert 3000 <= ErrorCode.DESKTOP_ELEMENT_NOT_FOUND.value < 4000

    def test_data_errors(self) -> None:
        """Data/validation error codes exist."""
        assert 4000 <= ErrorCode.VALIDATION_FAILED.value < 5000
        assert 4000 <= ErrorCode.PARSE_ERROR.value < 5000

    def test_config_errors(self) -> None:
        """Configuration error codes exist."""
        assert 5000 <= ErrorCode.CONFIG_NOT_FOUND.value < 6000

    def test_network_errors(self) -> None:
        """Network error codes exist."""
        assert 6000 <= ErrorCode.NETWORK_ERROR.value < 7000

    def test_resource_errors(self) -> None:
        """Resource error codes exist."""
        assert ErrorCode.RESOURCE_NOT_FOUND.value >= 7000


class TestErrorCodeFromException:
    """Tests for ErrorCode.from_exception classmethod."""

    def test_timeout_exception(self) -> None:
        """Timeout exceptions map correctly."""
        exc = TimeoutError("Operation timed out")
        code = ErrorCode.from_exception(exc)
        assert code == ErrorCode.TIMEOUT

    def test_value_error(self) -> None:
        """ValueError maps to INVALID_INPUT."""
        exc = ValueError("Invalid value")
        code = ErrorCode.from_exception(exc)
        assert code == ErrorCode.INVALID_INPUT

    def test_type_error(self) -> None:
        """TypeError maps to TYPE_MISMATCH."""
        exc = TypeError("Wrong type")
        code = ErrorCode.from_exception(exc)
        assert code == ErrorCode.TYPE_MISMATCH

    def test_file_not_found(self) -> None:
        """FileNotFoundError maps correctly."""
        exc = FileNotFoundError("No such file")
        code = ErrorCode.from_exception(exc)
        assert code == ErrorCode.FILE_NOT_FOUND

    def test_permission_error(self) -> None:
        """PermissionError maps correctly."""
        exc = PermissionError("Access denied")
        code = ErrorCode.from_exception(exc)
        assert code == ErrorCode.PERMISSION_DENIED

    def test_memory_error(self) -> None:
        """MemoryError maps correctly."""
        exc = MemoryError("Out of memory")
        code = ErrorCode.from_exception(exc)
        assert code == ErrorCode.MEMORY_ERROR

    def test_unknown_exception(self) -> None:
        """Unknown exceptions map to UNKNOWN_ERROR."""
        exc = RuntimeError("Some random error")
        code = ErrorCode.from_exception(exc)
        assert code == ErrorCode.UNKNOWN_ERROR

    def test_connection_refused(self) -> None:
        """Connection refused in message maps correctly."""
        exc = Exception("Connection refused by server")
        code = ErrorCode.from_exception(exc)
        assert code == ErrorCode.CONNECTION_REFUSED

    def test_ssl_error(self) -> None:
        """SSL error in message maps correctly."""
        exc = Exception("SSL certificate verification failed")
        code = ErrorCode.from_exception(exc)
        assert code == ErrorCode.SSL_ERROR


class TestErrorCodeProperties:
    """Tests for ErrorCode properties."""

    def test_category_general(self) -> None:
        """General category detection."""
        assert ErrorCode.UNKNOWN_ERROR.category == "General"
        assert ErrorCode.TIMEOUT.category == "General"

    def test_category_browser(self) -> None:
        """Browser category detection."""
        assert ErrorCode.BROWSER_NOT_FOUND.category == "Browser/Web"
        assert ErrorCode.ELEMENT_NOT_FOUND.category == "Browser/Web"

    def test_category_desktop(self) -> None:
        """Desktop category detection."""
        assert ErrorCode.WINDOW_NOT_FOUND.category == "Desktop"

    def test_category_data(self) -> None:
        """Data category detection."""
        assert ErrorCode.VALIDATION_FAILED.category == "Data/Validation"

    def test_category_config(self) -> None:
        """Config category detection."""
        assert ErrorCode.CONFIG_NOT_FOUND.category == "Configuration"

    def test_category_network(self) -> None:
        """Network category detection."""
        assert ErrorCode.NETWORK_ERROR.category == "Network"

    def test_category_resource(self) -> None:
        """Resource category detection."""
        assert ErrorCode.RESOURCE_NOT_FOUND.category == "Resource"

    def test_is_retryable_true(self) -> None:
        """Retryable errors are identified."""
        assert ErrorCode.TIMEOUT.is_retryable is True
        assert ErrorCode.NETWORK_ERROR.is_retryable is True
        assert ErrorCode.CONNECTION_TIMEOUT.is_retryable is True
        assert ErrorCode.ELEMENT_STALE.is_retryable is True

    def test_is_retryable_false(self) -> None:
        """Non-retryable errors are identified."""
        assert ErrorCode.INVALID_INPUT.is_retryable is False
        assert ErrorCode.CONFIG_NOT_FOUND.is_retryable is False
        assert ErrorCode.PERMISSION_DENIED.is_retryable is False


# ============================================================================
# Constants Tests
# ============================================================================


class TestConstants:
    """Tests for module constants."""

    def test_schema_version(self) -> None:
        """Schema version is defined."""
        assert SCHEMA_VERSION == "1.0.0"

    def test_default_timeout(self) -> None:
        """Default timeout is defined."""
        assert DEFAULT_TIMEOUT == 30

    def test_max_retries(self) -> None:
        """Max retries is defined."""
        assert MAX_RETRIES == 3

    def test_exec_port_names(self) -> None:
        """Execution port names are defined."""
        assert EXEC_IN_PORT == "exec_in"
        assert EXEC_OUT_PORT == "exec_out"
