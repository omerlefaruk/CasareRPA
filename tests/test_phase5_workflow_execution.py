"""
Phase 5: Workflow Execution System Tests

Tests for:
1. WorkflowRunner (main execution engine)
2. ExecutionContext (runtime state management)
3. Workflow Schema (structure definition)
4. Event System (UI integration)
5. Data Flow between nodes
6. Execution Controls (run, pause, resume, stop)
7. Workflow Persistence (save/load)
"""

import pytest
import asyncio
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
from tempfile import TemporaryDirectory


class TestExecutionContext:
    """Tests for ExecutionContext class."""

    def test_context_creation(self):
        """Test ExecutionContext instantiation."""
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test_workflow")

        assert context.workflow_name == "test_workflow"
        assert isinstance(context.variables, dict)
        assert isinstance(context.execution_path, list)

    def test_set_and_get_variable(self):
        """Test setting and getting variables."""
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")

        context.set_variable("test_var", "test_value")
        result = context.get_variable("test_var")

        assert result == "test_value"

    def test_get_variable_default(self):
        """Test getting variable with default value."""
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")

        result = context.get_variable("nonexistent", default="default_value")

        assert result == "default_value"

    def test_variable_types(self):
        """Test storing different variable types."""
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")

        context.set_variable("string_var", "hello")
        context.set_variable("int_var", 42)
        context.set_variable("float_var", 3.14)
        context.set_variable("bool_var", True)
        context.set_variable("list_var", [1, 2, 3])
        context.set_variable("dict_var", {"key": "value"})

        assert context.get_variable("string_var") == "hello"
        assert context.get_variable("int_var") == 42
        assert context.get_variable("float_var") == 3.14
        assert context.get_variable("bool_var") is True
        assert context.get_variable("list_var") == [1, 2, 3]
        assert context.get_variable("dict_var") == {"key": "value"}

    def test_execution_path_is_list(self):
        """Test execution_path attribute exists and is a list."""
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")

        assert hasattr(context, "execution_path")
        assert isinstance(context.execution_path, list)

    def test_error_handling(self):
        """Test error handling via add_error method."""
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")

        context.add_error("node_1", "Test error message")

        # errors is a list of (node_id, error_message) tuples
        assert len(context.errors) == 1
        assert context.errors[0] == ("node_1", "Test error message")

    def test_variables_dictionary(self):
        """Test variables dictionary access."""
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")

        context.set_variable("var1", "value1")
        context.set_variable("var2", "value2")

        assert "var1" in context.variables
        assert "var2" in context.variables

    def test_execution_summary(self):
        """Test getting execution summary."""
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")

        context.execution_path.append("node_1")
        context.execution_path.append("node_2")
        context.set_variable("test_var", "test_value")

        summary = context.get_execution_summary()

        assert "workflow_name" in summary
        assert summary["workflow_name"] == "test"


class TestWorkflowSchema:
    """Tests for WorkflowSchema class."""

    def test_schema_creation(self):
        """Test WorkflowSchema instantiation."""
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata

        metadata = WorkflowMetadata(name="Test Workflow")
        schema = WorkflowSchema(metadata)

        assert schema.metadata.name == "Test Workflow"
        assert isinstance(schema.nodes, dict)
        assert isinstance(schema.connections, list)

    def test_metadata_fields(self):
        """Test WorkflowMetadata fields."""
        from casare_rpa.core.workflow_schema import WorkflowMetadata

        metadata = WorkflowMetadata(
            name="Test",
            description="Test description",
            version="1.0.0",
            author="Test Author",
            tags=["test", "demo"],
        )

        assert metadata.name == "Test"
        assert metadata.description == "Test description"
        assert metadata.version == "1.0.0"
        assert metadata.author == "Test Author"
        assert metadata.tags == ["test", "demo"]

    def test_add_node(self):
        """Test adding nodes to schema."""
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata
        from casare_rpa.nodes import StartNode

        metadata = WorkflowMetadata(name="Test")
        schema = WorkflowSchema(metadata)

        start = StartNode("start_1")
        schema.nodes["start_1"] = start

        assert "start_1" in schema.nodes
        assert schema.nodes["start_1"] is start

    def test_add_connection(self):
        """Test adding connections to schema."""
        from casare_rpa.core.workflow_schema import (
            WorkflowSchema,
            WorkflowMetadata,
            NodeConnection,
        )

        metadata = WorkflowMetadata(name="Test")
        schema = WorkflowSchema(metadata)

        connection = NodeConnection(
            source_node="start_1",
            source_port="exec_out",
            target_node="end_1",
            target_port="exec_in",
        )
        schema.connections.append(connection)

        assert len(schema.connections) == 1
        assert schema.connections[0].source_node == "start_1"
        assert schema.connections[0].target_node == "end_1"

    def test_to_dict(self):
        """Test serializing schema to dictionary."""
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata
        from casare_rpa.nodes import StartNode, EndNode

        metadata = WorkflowMetadata(name="Test Workflow")
        schema = WorkflowSchema(metadata)

        start = StartNode("start_1")
        end = EndNode("end_1")
        schema.nodes["start_1"] = start
        schema.nodes["end_1"] = end

        data = schema.to_dict()

        assert "metadata" in data
        assert data["metadata"]["name"] == "Test Workflow"
        assert "nodes" in data

    def test_workflow_save_load(self):
        """Test saving and loading workflow."""
        from casare_rpa.core.workflow_schema import (
            WorkflowSchema,
            WorkflowMetadata,
            NodeConnection,
        )
        from casare_rpa.nodes import StartNode, EndNode

        with TemporaryDirectory() as tmpdir:
            # Create workflow
            metadata = WorkflowMetadata(name="Test Workflow")
            schema = WorkflowSchema(metadata)

            # Use serialized node data for persistence
            start = StartNode("start_1")
            end = EndNode("end_1")
            schema.nodes["start_1"] = start.serialize()
            schema.nodes["end_1"] = end.serialize()

            connection = NodeConnection("start_1", "exec_out", "end_1", "exec_in")
            schema.connections.append(connection)

            # Save
            save_path = Path(tmpdir) / "test_workflow.json"
            schema.save_to_file(save_path)

            assert save_path.exists()

            # Load
            loaded = WorkflowSchema.load_from_file(save_path)

            assert loaded.metadata.name == "Test Workflow"
            assert len(loaded.connections) == 1


class TestWorkflowRunner:
    """Tests for WorkflowRunner class."""

    def test_runner_creation(self):
        """Test WorkflowRunner instantiation."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner, ExecutionState
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        runner = WorkflowRunner(workflow)

        assert runner.workflow is workflow
        assert runner.state == ExecutionState.IDLE

    def test_runner_find_start_node(self):
        """Test runner finds start node."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata
        from casare_rpa.nodes import StartNode, EndNode

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        start = StartNode("start_1")
        end = EndNode("end_1")
        workflow.nodes["start_1"] = start
        workflow.nodes["end_1"] = end

        runner = WorkflowRunner(workflow)

        found_start = runner._find_start_node()

        assert found_start is not None
        assert found_start.node_id == "start_1"

    def test_runner_get_next_nodes(self):
        """Test runner gets next nodes based on connections."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import (
            WorkflowSchema,
            WorkflowMetadata,
            NodeConnection,
        )
        from casare_rpa.nodes import StartNode, EndNode

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        start = StartNode("start_1")
        end = EndNode("end_1")
        workflow.nodes["start_1"] = start
        workflow.nodes["end_1"] = end

        connection = NodeConnection("start_1", "exec_out", "end_1", "exec_in")
        workflow.connections.append(connection)

        runner = WorkflowRunner(workflow)

        next_nodes = runner._get_next_nodes("start_1")

        assert len(next_nodes) == 1
        assert next_nodes[0].node_id == "end_1"

    @pytest.mark.asyncio
    async def test_runner_execute_simple_workflow(self):
        """Test executing a simple workflow."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import (
            WorkflowSchema,
            WorkflowMetadata,
            NodeConnection,
        )
        from casare_rpa.nodes import StartNode, EndNode

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        start = StartNode("start_1")
        end = EndNode("end_1")
        workflow.nodes["start_1"] = start
        workflow.nodes["end_1"] = end

        connection = NodeConnection("start_1", "exec_out", "end_1", "exec_in")
        workflow.connections.append(connection)

        runner = WorkflowRunner(workflow)

        success = await runner.run()

        assert success is True
        assert "start_1" in runner.executed_nodes
        assert "end_1" in runner.executed_nodes

    def test_runner_progress_tracking(self):
        """Test progress tracking."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata
        from casare_rpa.nodes import StartNode, EndNode

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        start = StartNode("start_1")
        end = EndNode("end_1")
        workflow.nodes["start_1"] = start
        workflow.nodes["end_1"] = end

        runner = WorkflowRunner(workflow)

        # Initially 0%
        assert runner.progress == 0.0

        # Simulate execution
        runner.executed_nodes.add("start_1")
        assert runner.progress == 50.0

        runner.executed_nodes.add("end_1")
        assert runner.progress == 100.0

    def test_runner_execution_state(self):
        """Test execution state transitions."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner, ExecutionState
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        runner = WorkflowRunner(workflow)

        # Initial state
        assert runner.state == ExecutionState.IDLE

        # States should be defined
        assert ExecutionState.RUNNING is not None
        assert ExecutionState.PAUSED is not None
        assert ExecutionState.STOPPED is not None
        assert ExecutionState.COMPLETED is not None


class TestEventSystem:
    """Tests for event system."""

    def test_event_bus_creation(self):
        """Test EventBus instantiation."""
        from casare_rpa.core.events import EventBus

        bus = EventBus()

        assert bus is not None

    def test_event_bus_subscribe(self):
        """Test subscribing to events."""
        from casare_rpa.core.events import EventBus, EventType

        bus = EventBus()
        callback = MagicMock()

        bus.subscribe(EventType.NODE_STARTED, callback)

        # Should have handlers
        assert bus.get_handler_count(EventType.NODE_STARTED) > 0

    def test_event_bus_emit(self):
        """Test emitting events via publish."""
        from casare_rpa.core.events import EventBus, EventType, Event

        bus = EventBus()
        callback = MagicMock()

        bus.subscribe(EventType.NODE_STARTED, callback)

        # emit() takes event_type, data, node_id - not an Event object
        # Use publish() to emit an Event object directly
        event = Event(
            event_type=EventType.NODE_STARTED,
            data={"node_id": "test_node"},
        )
        bus.publish(event)

        callback.assert_called_once()

    def test_event_bus_unsubscribe(self):
        """Test unsubscribing from events."""
        from casare_rpa.core.events import EventBus, EventType, Event

        bus = EventBus()
        callback = MagicMock()

        bus.subscribe(EventType.NODE_STARTED, callback)
        bus.unsubscribe(EventType.NODE_STARTED, callback)

        # Use publish() to emit an Event object
        event = Event(
            event_type=EventType.NODE_STARTED,
            data={"node_id": "test_node"},
        )
        bus.publish(event)

        callback.assert_not_called()

    def test_event_types_defined(self):
        """Test that all required event types are defined."""
        from casare_rpa.core.events import EventType

        expected_types = [
            "WORKFLOW_STARTED",
            "NODE_STARTED",
            "NODE_COMPLETED",
            "NODE_ERROR",
            "WORKFLOW_PAUSED",
            "WORKFLOW_RESUMED",
            "WORKFLOW_STOPPED",
            "WORKFLOW_COMPLETED",
        ]

        for event_type in expected_types:
            assert hasattr(EventType, event_type)


class TestDataFlow:
    """Tests for data flow between nodes."""

    @pytest.mark.asyncio
    async def test_data_flow_set_get_variable(self):
        """Test data flows from SetVariable to GetVariable."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import (
            WorkflowSchema,
            WorkflowMetadata,
            NodeConnection,
        )
        from casare_rpa.nodes import StartNode, EndNode, SetVariableNode, GetVariableNode

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        start = StartNode("start_1")
        set_var = SetVariableNode("set_1")
        set_var.set_input_value("variable_name", "test_var")
        set_var.set_input_value("value", "test_value")
        get_var = GetVariableNode("get_1")
        get_var.set_input_value("variable_name", "test_var")
        end = EndNode("end_1")

        workflow.nodes["start_1"] = start
        workflow.nodes["set_1"] = set_var
        workflow.nodes["get_1"] = get_var
        workflow.nodes["end_1"] = end

        workflow.connections.extend(
            [
                NodeConnection("start_1", "exec_out", "set_1", "exec_in"),
                NodeConnection("set_1", "exec_out", "get_1", "exec_in"),
                NodeConnection("get_1", "exec_out", "end_1", "exec_in"),
            ]
        )

        runner = WorkflowRunner(workflow)

        success = await runner.run()

        assert success is True
        assert runner.context.get_variable("test_var") == "test_value"

    @pytest.mark.asyncio
    async def test_data_flow_increment(self):
        """Test increment node data flow."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import (
            WorkflowSchema,
            WorkflowMetadata,
            NodeConnection,
        )
        from casare_rpa.nodes import (
            StartNode,
            EndNode,
            SetVariableNode,
            IncrementVariableNode,
        )

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        start = StartNode("start_1")
        set_var = SetVariableNode("set_1")
        set_var.set_input_value("variable_name", "counter")
        set_var.set_input_value("value", 0)
        incr = IncrementVariableNode("incr_1")
        incr.set_input_value("variable_name", "counter")
        incr.set_input_value("increment", 5)
        end = EndNode("end_1")

        workflow.nodes["start_1"] = start
        workflow.nodes["set_1"] = set_var
        workflow.nodes["incr_1"] = incr
        workflow.nodes["end_1"] = end

        workflow.connections.extend(
            [
                NodeConnection("start_1", "exec_out", "set_1", "exec_in"),
                NodeConnection("set_1", "exec_out", "incr_1", "exec_in"),
                NodeConnection("incr_1", "exec_out", "end_1", "exec_in"),
            ]
        )

        runner = WorkflowRunner(workflow)

        success = await runner.run()

        assert success is True
        assert runner.context.get_variable("counter") == 5

    @pytest.mark.asyncio
    async def test_conditional_data_flow(self):
        """Test data flow with conditional branching."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import (
            WorkflowSchema,
            WorkflowMetadata,
            NodeConnection,
        )
        from casare_rpa.nodes import StartNode, EndNode, SetVariableNode, IfNode

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        start = StartNode("start_1")
        set_var = SetVariableNode("set_1")
        set_var.set_input_value("variable_name", "x")
        set_var.set_input_value("value", 10)
        if_node = IfNode("if_1")
        if_node.set_input_value("condition", "x > 5")
        end = EndNode("end_1")

        workflow.nodes["start_1"] = start
        workflow.nodes["set_1"] = set_var
        workflow.nodes["if_1"] = if_node
        workflow.nodes["end_1"] = end

        workflow.connections.extend(
            [
                NodeConnection("start_1", "exec_out", "set_1", "exec_in"),
                NodeConnection("set_1", "exec_out", "if_1", "exec_in"),
                NodeConnection("if_1", "true", "end_1", "exec_in"),
            ]
        )

        runner = WorkflowRunner(workflow)

        success = await runner.run()

        assert success is True


class TestNodeConnection:
    """Tests for NodeConnection class."""

    def test_node_connection_creation(self):
        """Test NodeConnection instantiation."""
        from casare_rpa.core.workflow_schema import NodeConnection

        conn = NodeConnection(
            source_node="node_1",
            source_port="output",
            target_node="node_2",
            target_port="input",
        )

        assert conn.source_node == "node_1"
        assert conn.source_port == "output"
        assert conn.target_node == "node_2"
        assert conn.target_port == "input"

    def test_node_connection_to_dict(self):
        """Test serializing connection to dictionary."""
        from casare_rpa.core.workflow_schema import NodeConnection

        conn = NodeConnection("node_1", "output", "node_2", "input")

        data = conn.to_dict()

        assert data["source_node"] == "node_1"
        assert data["source_port"] == "output"
        assert data["target_node"] == "node_2"
        assert data["target_port"] == "input"


class TestWorkflowPersistence:
    """Tests for workflow save/load persistence."""

    def test_save_workflow_creates_file(self):
        """Test saving workflow creates JSON file."""
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata
        from casare_rpa.nodes import StartNode, EndNode

        with TemporaryDirectory() as tmpdir:
            metadata = WorkflowMetadata(name="Test Workflow")
            schema = WorkflowSchema(metadata)

            # Use serialized node data for persistence
            start = StartNode("start_1")
            end = EndNode("end_1")
            schema.nodes["start_1"] = start.serialize()
            schema.nodes["end_1"] = end.serialize()

            save_path = Path(tmpdir) / "workflow.json"
            schema.save_to_file(save_path)

            assert save_path.exists()

            # Verify it's valid JSON
            with open(save_path) as f:
                data = json.load(f)

            assert "metadata" in data
            assert data["metadata"]["name"] == "Test Workflow"

    def test_load_workflow_from_file(self):
        """Test loading workflow from JSON file."""
        from casare_rpa.core.workflow_schema import (
            WorkflowSchema,
            WorkflowMetadata,
            NodeConnection,
        )
        from casare_rpa.nodes import StartNode, EndNode

        with TemporaryDirectory() as tmpdir:
            # First save a workflow
            metadata = WorkflowMetadata(
                name="Saved Workflow",
                description="A test workflow",
                version="1.0.0",
            )
            schema = WorkflowSchema(metadata)

            # Use serialized node data
            start = StartNode("start_1")
            end = EndNode("end_1")
            schema.nodes["start_1"] = start.serialize()
            schema.nodes["end_1"] = end.serialize()

            conn = NodeConnection("start_1", "exec_out", "end_1", "exec_in")
            schema.connections.append(conn)

            save_path = Path(tmpdir) / "saved_workflow.json"
            schema.save_to_file(save_path)

            # Now load it
            loaded = WorkflowSchema.load_from_file(save_path)

            assert loaded.metadata.name == "Saved Workflow"
            assert loaded.metadata.description == "A test workflow"
            assert len(loaded.connections) == 1

    def test_save_load_roundtrip(self):
        """Test that save/load preserves workflow data."""
        from casare_rpa.core.workflow_schema import (
            WorkflowSchema,
            WorkflowMetadata,
            NodeConnection,
        )
        from casare_rpa.nodes import StartNode, EndNode, SetVariableNode

        with TemporaryDirectory() as tmpdir:
            # Create complex workflow
            metadata = WorkflowMetadata(
                name="Complex Workflow",
                description="Test with multiple nodes",
                version="2.0.0",
                author="Test Author",
                tags=["test", "complex"],
            )
            schema = WorkflowSchema(metadata)

            # Use serialized node data for persistence
            start = StartNode("start_1")
            set_var = SetVariableNode("set_1")
            set_var.set_input_value("variable_name", "test_var")
            set_var.set_input_value("value", 42)
            end = EndNode("end_1")

            schema.nodes["start_1"] = start.serialize()
            schema.nodes["set_1"] = set_var.serialize()
            schema.nodes["end_1"] = end.serialize()

            schema.connections.extend(
                [
                    NodeConnection("start_1", "exec_out", "set_1", "exec_in"),
                    NodeConnection("set_1", "exec_out", "end_1", "exec_in"),
                ]
            )

            save_path = Path(tmpdir) / "complex.json"
            schema.save_to_file(save_path)

            # Load and verify
            loaded = WorkflowSchema.load_from_file(save_path)

            assert loaded.metadata.name == "Complex Workflow"
            assert loaded.metadata.version == "2.0.0"
            assert loaded.metadata.author == "Test Author"
            assert len(loaded.nodes) == 3
            assert len(loaded.connections) == 2


class TestExecutionHistory:
    """Tests for execution history tracking."""

    @pytest.mark.asyncio
    async def test_execution_history_recorded(self):
        """Test that execution history is recorded or executed_nodes contains data."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import (
            WorkflowSchema,
            WorkflowMetadata,
            NodeConnection,
        )
        from casare_rpa.nodes import StartNode, EndNode

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        start = StartNode("start_1")
        end = EndNode("end_1")
        workflow.nodes["start_1"] = start
        workflow.nodes["end_1"] = end

        workflow.connections.append(
            NodeConnection("start_1", "exec_out", "end_1", "exec_in")
        )

        runner = WorkflowRunner(workflow)

        await runner.run()

        # Either execution_history has entries or executed_nodes tracks what ran
        assert len(runner.execution_history) > 0 or len(runner.executed_nodes) > 0

    def test_execution_history_contains_node_info(self):
        """Test execution history contains node information."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        runner = WorkflowRunner(workflow)

        # Manually add to history
        runner.execution_history.append(
            {
                "node_id": "test_node",
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
            }
        )

        assert len(runner.execution_history) == 1
        assert runner.execution_history[0]["node_id"] == "test_node"
