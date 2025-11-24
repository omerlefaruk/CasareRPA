"""
CasareRPA - Core Architecture Tests
Tests for Phase 2: BaseNode, WorkflowSchema, ExecutionContext, Events, Types
"""

import sys
from pathlib import Path
import pytest
from typing import Any, Optional

# Add src directory to path
PROJECT_ROOT = Path(__file__).parent.parent
SRC_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_ROOT))

from casare_rpa.core import (
    BaseNode,
    Port,
    DataType,
    NodeStatus,
    PortType,
    ExecutionContext,
    ExecutionMode,
    WorkflowSchema,
    WorkflowMetadata,
    NodeConnection,
    Event,
    EventBus,
    EventType,
    EventLogger,
    EventRecorder,
    get_event_bus,
    reset_event_bus,
)


# ============================================================================
# TEST FIXTURES
# ============================================================================


class DemoNode(BaseNode):
    """Simple demo node for testing BaseNode functionality."""

    def _define_ports(self) -> None:
        self.add_input_port("input_text", DataType.STRING, "Input text")
        self.add_output_port("output_text", DataType.STRING, "Output text")

    async def execute(self, context: ExecutionContext) -> dict[str, Any]:
        input_val = self.get_input_value("input_text", "")
        output_val = f"Processed: {input_val}"
        self.set_output_value("output_text", output_val)
        return {"output_text": output_val}


# ============================================================================
# TYPE TESTS
# ============================================================================


class TestTypes:
    """Test core type definitions and enums."""

    def test_node_status_enum(self) -> None:
        """Test NodeStatus enum values."""
        assert NodeStatus.IDLE
        assert NodeStatus.RUNNING
        assert NodeStatus.SUCCESS
        assert NodeStatus.ERROR
        assert NodeStatus.SKIPPED
        assert NodeStatus.CANCELLED

    def test_port_type_enum(self) -> None:
        """Test PortType enum values."""
        assert PortType.INPUT
        assert PortType.OUTPUT
        assert PortType.EXEC_INPUT
        assert PortType.EXEC_OUTPUT

    def test_data_type_enum(self) -> None:
        """Test DataType enum values."""
        assert DataType.STRING
        assert DataType.INTEGER
        assert DataType.FLOAT
        assert DataType.BOOLEAN
        assert DataType.LIST
        assert DataType.DICT
        assert DataType.ANY
        assert DataType.ELEMENT
        assert DataType.PAGE
        assert DataType.BROWSER

    def test_execution_mode_enum(self) -> None:
        """Test ExecutionMode enum values."""
        assert ExecutionMode.NORMAL
        assert ExecutionMode.DEBUG
        assert ExecutionMode.VALIDATE

    def test_event_type_enum(self) -> None:
        """Test EventType enum values."""
        assert EventType.NODE_STARTED
        assert EventType.NODE_COMPLETED
        assert EventType.NODE_ERROR
        assert EventType.WORKFLOW_STARTED
        assert EventType.WORKFLOW_COMPLETED


# ============================================================================
# PORT TESTS
# ============================================================================


class TestPort:
    """Test Port class functionality."""

    def test_port_creation(self) -> None:
        """Test creating a port."""
        port = Port("test_port", PortType.INPUT, DataType.STRING)
        assert port.name == "test_port"
        assert port.port_type == PortType.INPUT
        assert port.data_type == DataType.STRING
        assert port.required is True

    def test_port_set_get_value(self) -> None:
        """Test setting and getting port values."""
        port = Port("test_port", PortType.INPUT, DataType.STRING)
        port.set_value("test value")
        assert port.get_value() == "test value"

    def test_port_to_dict(self) -> None:
        """Test port serialization."""
        port = Port("test_port", PortType.OUTPUT, DataType.INTEGER, "Test Port", False)
        port_dict = port.to_dict()
        assert port_dict["name"] == "test_port"
        assert port_dict["port_type"] == "OUTPUT"
        assert port_dict["data_type"] == "INTEGER"
        assert port_dict["label"] == "Test Port"
        assert port_dict["required"] is False


# ============================================================================
# BASE NODE TESTS
# ============================================================================


class TestBaseNode:
    """Test BaseNode abstract class functionality."""

    def test_node_creation(self) -> None:
        """Test creating a node instance."""
        node = DemoNode("test_node_1")
        assert node.node_id == "test_node_1"
        assert node.node_type == "DemoNode"
        assert node.status == NodeStatus.IDLE

    def test_node_ports(self) -> None:
        """Test node port management."""
        node = DemoNode("test_node_1")
        assert "input_text" in node.input_ports
        assert "output_text" in node.output_ports
        assert len(node.input_ports) == 1
        assert len(node.output_ports) == 1

    def test_set_get_input_value(self) -> None:
        """Test setting and getting input values."""
        node = DemoNode("test_node_1")
        node.set_input_value("input_text", "Hello World")
        assert node.get_input_value("input_text") == "Hello World"

    def test_set_get_output_value(self) -> None:
        """Test setting and getting output values."""
        node = DemoNode("test_node_1")
        node.set_output_value("output_text", "Result")
        assert node.get_output_value("output_text") == "Result"

    def test_node_validation(self) -> None:
        """Test node validation."""
        node = DemoNode("test_node_1")
        # Should fail - required input not set
        is_valid, error = node.validate()
        assert not is_valid
        assert "input_text" in error

        # Should pass - required input set
        node.set_input_value("input_text", "test")
        is_valid, error = node.validate()
        assert is_valid
        assert error is None

    @pytest.mark.asyncio
    async def test_node_execution(self) -> None:
        """Test node execution."""
        node = DemoNode("test_node_1")
        node.set_input_value("input_text", "Test")
        
        context = ExecutionContext("test_workflow")
        result = await node.execute(context)
        
        assert result["output_text"] == "Processed: Test"
        assert node.get_output_value("output_text") == "Processed: Test"

    def test_node_serialization(self) -> None:
        """Test node serialization."""
        node = DemoNode("test_node_1", {"setting": "value"})
        serialized = node.serialize()
        
        assert serialized["node_id"] == "test_node_1"
        assert serialized["node_type"] == "DemoNode"
        assert serialized["config"]["setting"] == "value"
        assert "input_ports" in serialized
        assert "output_ports" in serialized

    def test_node_status_management(self) -> None:
        """Test node status management."""
        node = DemoNode("test_node_1")
        assert node.get_status() == NodeStatus.IDLE
        
        node.set_status(NodeStatus.RUNNING)
        assert node.get_status() == NodeStatus.RUNNING
        
        node.set_status(NodeStatus.SUCCESS)
        assert node.get_status() == NodeStatus.SUCCESS

    def test_node_reset(self) -> None:
        """Test node reset functionality."""
        node = DemoNode("test_node_1")
        node.set_input_value("input_text", "Test")
        node.set_output_value("output_text", "Result")
        node.set_status(NodeStatus.SUCCESS)
        
        node.reset()
        
        assert node.status == NodeStatus.IDLE
        assert node.get_input_value("input_text") is None
        assert node.get_output_value("output_text") is None


# ============================================================================
# WORKFLOW SCHEMA TESTS
# ============================================================================


class TestWorkflowMetadata:
    """Test WorkflowMetadata class."""

    def test_metadata_creation(self) -> None:
        """Test creating workflow metadata."""
        metadata = WorkflowMetadata(
            name="Test Workflow",
            description="Test description",
            author="Test Author"
        )
        assert metadata.name == "Test Workflow"
        assert metadata.description == "Test description"
        assert metadata.author == "Test Author"

    def test_metadata_serialization(self) -> None:
        """Test metadata serialization."""
        metadata = WorkflowMetadata("Test", "Desc", "Author", "1.0.0", ["tag1", "tag2"])
        data = metadata.to_dict()
        
        assert data["name"] == "Test"
        assert data["description"] == "Desc"
        assert data["author"] == "Author"
        assert data["version"] == "1.0.0"
        assert data["tags"] == ["tag1", "tag2"]

    def test_metadata_deserialization(self) -> None:
        """Test metadata deserialization."""
        data = {
            "name": "Test",
            "description": "Desc",
            "author": "Author",
            "version": "2.0.0",
            "tags": ["tag"],
        }
        metadata = WorkflowMetadata.from_dict(data)
        assert metadata.name == "Test"
        assert metadata.version == "2.0.0"


class TestNodeConnection:
    """Test NodeConnection class."""

    def test_connection_creation(self) -> None:
        """Test creating a connection."""
        conn = NodeConnection("node1", "output", "node2", "input")
        assert conn.source_node == "node1"
        assert conn.source_port == "output"
        assert conn.target_node == "node2"
        assert conn.target_port == "input"

    def test_connection_ids(self) -> None:
        """Test connection port IDs."""
        conn = NodeConnection("node1", "output", "node2", "input")
        assert conn.source_id == "node1.output"
        assert conn.target_id == "node2.input"

    def test_connection_serialization(self) -> None:
        """Test connection serialization."""
        conn = NodeConnection("node1", "out", "node2", "in")
        data = conn.to_dict()
        assert data["source_node"] == "node1"
        assert data["target_node"] == "node2"

    def test_connection_deserialization(self) -> None:
        """Test connection deserialization."""
        data = {
            "source_node": "n1",
            "source_port": "out",
            "target_node": "n2",
            "target_port": "in"
        }
        conn = NodeConnection.from_dict(data)
        assert conn.source_node == "n1"
        assert conn.target_port == "in"


class TestWorkflowSchema:
    """Test WorkflowSchema class."""

    def test_workflow_creation(self) -> None:
        """Test creating a workflow."""
        workflow = WorkflowSchema()
        assert workflow.metadata.name == "Untitled Workflow"
        assert len(workflow.nodes) == 0
        assert len(workflow.connections) == 0

    def test_add_remove_node(self) -> None:
        """Test adding and removing nodes."""
        workflow = WorkflowSchema()
        node = DemoNode("node1")
        workflow.add_node(node.serialize())
        
        assert "node1" in workflow.nodes
        assert len(workflow.nodes) == 1
        
        workflow.remove_node("node1")
        assert "node1" not in workflow.nodes

    def test_add_connection(self) -> None:
        """Test adding connections."""
        workflow = WorkflowSchema()
        node1 = DemoNode("node1")
        node2 = DemoNode("node2")
        workflow.add_node(node1.serialize())
        workflow.add_node(node2.serialize())
        
        conn = NodeConnection("node1", "output_text", "node2", "input_text")
        workflow.add_connection(conn)
        
        assert len(workflow.connections) == 1

    def test_workflow_validation(self) -> None:
        """Test workflow validation."""
        workflow = WorkflowSchema()
        # Empty workflow should fail
        is_valid, errors = workflow.validate()
        assert not is_valid
        assert len(errors) > 0

        # Add a node
        node = DemoNode("node1")
        workflow.add_node(node.serialize())
        is_valid, errors = workflow.validate()
        assert is_valid

    def test_workflow_serialization(self) -> None:
        """Test workflow serialization."""
        workflow = WorkflowSchema(WorkflowMetadata("Test"))
        node = DemoNode("node1")
        workflow.add_node(node.serialize())
        
        data = workflow.to_dict()
        assert data["metadata"]["name"] == "Test"
        assert "node1" in data["nodes"]

    def test_workflow_deserialization(self) -> None:
        """Test workflow deserialization."""
        data = {
            "metadata": {"name": "Test", "description": "Desc"},
            "nodes": {"node1": {"node_id": "node1", "node_type": "DemoNode"}},
            "connections": [],
            "variables": {},
            "settings": {}
        }
        workflow = WorkflowSchema.from_dict(data)
        assert workflow.metadata.name == "Test"
        assert "node1" in workflow.nodes


# ============================================================================
# EXECUTION CONTEXT TESTS
# ============================================================================


class TestExecutionContext:
    """Test ExecutionContext class."""

    def test_context_creation(self) -> None:
        """Test creating execution context."""
        context = ExecutionContext("test_workflow")
        assert context.workflow_name == "test_workflow"
        assert context.mode == ExecutionMode.NORMAL
        assert not context.stopped

    def test_variable_management(self) -> None:
        """Test variable storage and retrieval."""
        context = ExecutionContext()
        context.set_variable("test_var", "test_value")
        
        assert context.has_variable("test_var")
        assert context.get_variable("test_var") == "test_value"
        assert context.get_variable("nonexistent", "default") == "default"

    def test_delete_variable(self) -> None:
        """Test deleting variables."""
        context = ExecutionContext()
        context.set_variable("var1", "value1")
        assert context.has_variable("var1")
        
        context.delete_variable("var1")
        assert not context.has_variable("var1")

    def test_clear_variables(self) -> None:
        """Test clearing all variables."""
        context = ExecutionContext()
        context.set_variable("var1", "value1")
        context.set_variable("var2", "value2")
        
        context.clear_variables()
        assert not context.has_variable("var1")
        assert not context.has_variable("var2")

    def test_execution_tracking(self) -> None:
        """Test execution path tracking."""
        context = ExecutionContext()
        context.set_current_node("node1")
        context.set_current_node("node2")
        
        assert context.execution_path == ["node1", "node2"]
        assert context.current_node_id == "node2"

    def test_error_tracking(self) -> None:
        """Test error tracking."""
        context = ExecutionContext()
        context.add_error("node1", "Error message")
        
        assert len(context.errors) == 1
        assert context.errors[0] == ("node1", "Error message")

    def test_stop_execution(self) -> None:
        """Test stopping execution."""
        context = ExecutionContext()
        assert not context.is_stopped()
        
        context.stop_execution()
        assert context.is_stopped()

    def test_execution_summary(self) -> None:
        """Test execution summary generation."""
        context = ExecutionContext("test_workflow")
        context.set_current_node("node1")
        context.set_variable("var1", "value1")
        context.add_error("node1", "Test error")
        
        summary = context.get_execution_summary()
        assert summary["workflow_name"] == "test_workflow"
        assert summary["nodes_executed"] == 1
        assert summary["variables_count"] == 1
        assert len(summary["errors"]) == 1


# ============================================================================
# EVENT SYSTEM TESTS
# ============================================================================


class TestEvent:
    """Test Event class."""

    def test_event_creation(self) -> None:
        """Test creating an event."""
        event = Event(EventType.NODE_STARTED, {"key": "value"}, "node1")
        assert event.event_type == EventType.NODE_STARTED
        assert event.data["key"] == "value"
        assert event.node_id == "node1"

    def test_event_serialization(self) -> None:
        """Test event serialization."""
        event = Event(EventType.NODE_COMPLETED, {"result": "success"})
        data = event.to_dict()
        assert data["event_type"] == "NODE_COMPLETED"
        assert data["data"]["result"] == "success"


class TestEventBus:
    """Test EventBus class."""

    def setup_method(self) -> None:
        """Reset event bus before each test."""
        reset_event_bus()

    def test_event_bus_creation(self) -> None:
        """Test creating event bus."""
        bus = EventBus()
        assert bus is not None

    def test_subscribe_and_publish(self) -> None:
        """Test subscribing and publishing events."""
        bus = EventBus()
        received_events = []

        def handler(event: Event) -> None:
            received_events.append(event)

        bus.subscribe(EventType.NODE_STARTED, handler)
        event = Event(EventType.NODE_STARTED, {"test": "data"})
        bus.publish(event)

        assert len(received_events) == 1
        assert received_events[0].event_type == EventType.NODE_STARTED

    def test_emit_convenience_method(self) -> None:
        """Test emit convenience method."""
        bus = EventBus()
        received_events = []

        def handler(event: Event) -> None:
            received_events.append(event)

        bus.subscribe(EventType.WORKFLOW_STARTED, handler)
        bus.emit(EventType.WORKFLOW_STARTED, {"workflow": "test"})

        assert len(received_events) == 1

    def test_unsubscribe(self) -> None:
        """Test unsubscribing handlers."""
        bus = EventBus()
        received_count = [0]

        def handler(event: Event) -> None:
            received_count[0] += 1

        bus.subscribe(EventType.NODE_STARTED, handler)
        bus.emit(EventType.NODE_STARTED)
        assert received_count[0] == 1

        bus.unsubscribe(EventType.NODE_STARTED, handler)
        bus.emit(EventType.NODE_STARTED)
        assert received_count[0] == 1  # Should not increase

    def test_event_history(self) -> None:
        """Test event history."""
        bus = EventBus()
        bus.emit(EventType.NODE_STARTED)
        bus.emit(EventType.NODE_COMPLETED)

        history = bus.get_history()
        assert len(history) == 2
        assert history[0].event_type == EventType.NODE_COMPLETED  # Most recent first

    def test_get_history_with_filter(self) -> None:
        """Test getting filtered history."""
        bus = EventBus()
        bus.emit(EventType.NODE_STARTED)
        bus.emit(EventType.NODE_COMPLETED)
        bus.emit(EventType.NODE_STARTED)

        history = bus.get_history(EventType.NODE_STARTED)
        assert len(history) == 2

    def test_global_event_bus(self) -> None:
        """Test global event bus singleton."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2  # Should be same instance


class TestEventLogger:
    """Test EventLogger class."""

    def test_event_logger_creation(self) -> None:
        """Test creating event logger."""
        logger = EventLogger("DEBUG")
        assert logger.log_level == "DEBUG"

    def test_event_logger_subscribe(self) -> None:
        """Test subscribing event logger."""
        bus = EventBus()
        logger = EventLogger()
        logger.subscribe_all(bus)
        
        # Should not raise errors
        bus.emit(EventType.NODE_STARTED)


class TestEventRecorder:
    """Test EventRecorder class."""

    def test_recorder_creation(self) -> None:
        """Test creating event recorder."""
        recorder = EventRecorder()
        assert not recorder.is_recording
        assert len(recorder.recorded_events) == 0

    def test_recording(self) -> None:
        """Test event recording."""
        bus = EventBus()
        recorder = EventRecorder()
        recorder.subscribe_all(bus)
        
        recorder.start_recording()
        bus.emit(EventType.NODE_STARTED)
        bus.emit(EventType.NODE_COMPLETED)
        recorder.stop_recording()

        events = recorder.get_recorded_events()
        assert len(events) == 2

    def test_export_to_dict(self) -> None:
        """Test exporting recorded events."""
        recorder = EventRecorder()
        recorder.start_recording()
        event = Event(EventType.NODE_STARTED, {"test": "data"})
        recorder.handle_event(event)

        exported = recorder.export_to_dict()
        assert len(exported) == 1
        assert exported[0]["event_type"] == "NODE_STARTED"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
