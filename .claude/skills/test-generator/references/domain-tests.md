# Domain Testing Reference

Templates for testing pure domain logic (no mocks).

## Domain Entity Test Template

```python
import pytest
from casare_rpa.domain.entities.{entity_name} import {EntityName}

class Test{EntityName}:
    def test_create_entity(self):
        entity = {EntityName}(id="test_id", name="Test")
        assert entity.id == "test_id"
        assert entity.name == "Test"

    def test_entity_validation(self):
        with pytest.raises(ValueError):
            {EntityName}(id="", name="Test")  # Empty ID should fail

    def test_entity_immutability(self):
        entity = {EntityName}(id="test_id", name="Test")
        with pytest.raises(AttributeError):
            entity.id = "new_id"  # Should not allow modification

    def test_entity_equality(self):
        entity1 = {EntityName}(id="test_id", name="Test")
        entity2 = {EntityName}(id="test_id", name="Test")
        entity3 = {EntityName}(id="other_id", name="Test")

        assert entity1 == entity2
        assert entity1 != entity3
```

## Value Object Testing

```python
class TestDataType:
    def test_string_type(self):
        data_type = DataType.STRING
        assert data_type.value == "string"
        assert str(data_type) == "string"

    def test_type_comparison(self):
        assert DataType.STRING == DataType.STRING
        assert DataType.STRING != DataType.INTEGER

    def test_invalid_value_raises_error(self):
        with pytest.raises(ValueError):
            DataType("invalid_type")

class TestPort:
    def test_port_creation(self):
        port = Port(id="port1", name="output", data_type=DataType.STRING)
        assert port.id.value == "port1"
        assert port.name == "output"
        assert port.data_type == DataType.STRING

    def test_port_with_default_value(self):
        port = Port(
            id="port1",
            name="output",
            data_type=DataType.STRING,
            default_value="default"
        )
        assert port.default_value == "default"

    def test_port_equality(self):
        port1 = Port(id="p1", name="out", data_type=DataType.STRING)
        port2 = Port(id="p1", name="out", data_type=DataType.STRING)
        port3 = Port(id="p2", name="out", data_type=DataType.STRING)

        assert port1 == port2
        assert port1 != port3
```

## Aggregate Testing

```python
class TestWorkflowAggregate:
    def test_create_workflow(self):
        workflow = Workflow(id=WorkflowId.generate(), name="Test Flow")
        assert workflow.name == "Test Flow"
        assert len(workflow.nodes) == 0

    def test_add_node_emits_event(self):
        workflow = Workflow(id=WorkflowId.generate(), name="Test Flow")
        position = Position(x=100, y=200)

        node_id = workflow.add_node("ClickNode", position)

        assert node_id in workflow.nodes
        events = workflow.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], NodeAdded)

    def test_add_node_at_position(self):
        workflow = Workflow(id=WorkflowId.generate(), name="Test Flow")
        position = Position(x=100, y=200)

        node_id = workflow.add_node("ClickNode", position)

        node = workflow.nodes[node_id]
        assert node.position == position

    def test_remove_node_emits_event(self):
        workflow = Workflow(id=WorkflowId.generate(), name="Test Flow")
        position = Position(x=100, y=200)
        node_id = workflow.add_node("ClickNode", position)
        workflow.collect_events()  # Clear previous events

        workflow.remove_node(node_id)

        assert node_id not in workflow.nodes
        events = workflow.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], NodeRemoved)

    def test_connect_nodes_emits_event(self):
        workflow = Workflow(id=WorkflowId.generate(), name="Test Flow")
        pos1, pos2 = Position(x=100, y=100), Position(x=300, y=100)
        node1 = workflow.add_node("StartNode", pos1)
        node2 = workflow.add_node("EndNode", pos2)
        workflow.collect_events()  # Clear previous events

        workflow.connect_nodes(node1, "exec_out", node2, "exec_in")

        events = workflow.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], NodeConnected)

    def test_disconnect_nodes_emits_event(self):
        workflow = Workflow(id=WorkflowId.generate(), name="Test Flow")
        pos1, pos2 = Position(x=100, y=100), Position(x=300, y=100)
        node1 = workflow.add_node("StartNode", pos1)
        node2 = workflow.add_node("EndNode", pos2)
        workflow.connect_nodes(node1, "exec_out", node2, "exec_in")
        workflow.collect_events()  # Clear previous events

        workflow.disconnect_nodes(node1, "exec_out", node2, "exec_in")

        events = workflow.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], NodeDisconnected)
```

## Domain Service Testing

```python
class TestExecutionOrchestrator:
    def test_execute_workflow_success(self):
        orchestrator = ExecutionOrchestrator()
        workflow = Workflow(id=WorkflowId.generate(), name="Test")
        # Add nodes...

        result = await orchestrator.execute(workflow)

        assert result.status == ExecutionStatus.COMPLETED
        assert result.execution_time_ms > 0

    def test_execute_workflow_with_failure(self):
        orchestrator = ExecutionOrchestrator()
        workflow = Workflow(id=WorkflowId.generate(), name="Test")
        # Add failing node...

        result = await orchestrator.execute(workflow)

        assert result.status == ExecutionStatus.FAILED
        assert result.error is not None
```
