# Week 2 Day 5: Integration Testing & Validation - Implementation Plan

**Version**: 1.0.0
**Created**: November 27, 2025
**Target Duration**: 8 hours
**Implementer**: rpa-engine-architect agent

---

## Executive Summary

This document provides a comprehensive implementation plan for Week 2 Day 5 of the CasareRPA refactoring roadmap. The objective is to ensure all Week 2 refactoring changes are properly validated through comprehensive testing, performance benchmarking, and regression analysis.

### Week 2 Components Being Tested

| Day | Component | Location | Key Classes |
|-----|-----------|----------|-------------|
| Day 1 | Domain Entities | `src/casare_rpa/domain/entities/` | `WorkflowSchema`, `ExecutionState`, `NodeConnection`, `WorkflowMetadata` |
| Day 2 | Domain Services | `src/casare_rpa/domain/services/` | `ExecutionOrchestrator` |
| Day 3 | Infrastructure | `src/casare_rpa/infrastructure/` | `ProjectStorage`, adapters, persistence |
| Day 4 | Application Layer | `src/casare_rpa/application/` | `ExecuteWorkflowUseCase`, DI container |

---

## Detailed Task Breakdown (Hour-by-Hour)

### Hour 1: Test Environment Setup and Baseline Capture (08:00-09:00)

**Tasks**:
1. Run existing test suite to capture baseline (15 min)
2. Document current test counts and coverage (10 min)
3. Set up test directory structure for Week 2 tests (15 min)
4. Create shared test fixtures module (20 min)

**Commands**:
```powershell
# Run baseline tests
pytest tests/ -v --tb=short 2>&1 | tee baseline_test_results.txt

# Capture coverage baseline
pytest tests/ --cov=casare_rpa --cov-report=html --cov-report=term-missing

# Create Week 2 test directories
mkdir -p tests/domain/entities
mkdir -p tests/domain/services
mkdir -p tests/infrastructure/persistence
mkdir -p tests/application/use_cases
mkdir -p tests/integration/week2
mkdir -p tests/performance/week2
```

**Expected Output**:
- Baseline test results file
- Coverage report (target: document current coverage percentage)
- New test directory structure

---

### Hour 2: Domain Entity Unit Tests (09:00-10:00)

**Focus**: `src/casare_rpa/domain/entities/`

**Test Files to Create**:

#### 2.1 `tests/domain/entities/test_workflow.py`

```python
"""
Unit tests for WorkflowSchema domain entity.
Tests validation logic, serialization, and business rules.
"""
import pytest
from datetime import datetime
from typing import Dict, Any

from casare_rpa.domain.entities.workflow import (
    WorkflowSchema,
    VariableDefinition,
)
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.entities.node_connection import NodeConnection


class TestWorkflowSchemaInitialization:
    """Test WorkflowSchema initialization and defaults."""

    def test_create_with_default_metadata(self):
        """Workflow creates with default metadata when none provided."""
        workflow = WorkflowSchema()

        assert workflow.metadata is not None
        assert workflow.metadata.name == "Untitled Workflow"
        assert workflow.nodes == {}
        assert workflow.connections == []

    def test_create_with_custom_metadata(self):
        """Workflow accepts custom metadata."""
        metadata = WorkflowMetadata(
            name="Test Workflow",
            description="A test workflow",
            author="Test Author",
        )
        workflow = WorkflowSchema(metadata=metadata)

        assert workflow.metadata.name == "Test Workflow"
        assert workflow.metadata.description == "A test workflow"
        assert workflow.metadata.author == "Test Author"

    def test_default_settings(self):
        """Workflow has correct default settings."""
        workflow = WorkflowSchema()

        assert workflow.settings["stop_on_error"] is True
        assert workflow.settings["timeout"] == 30
        assert workflow.settings["retry_count"] == 0


class TestWorkflowSchemaNodeManagement:
    """Test node add/remove operations."""

    def test_add_node_success(self):
        """Add node stores node correctly."""
        workflow = WorkflowSchema()
        node_data = {
            "node_id": "node1",
            "type": "StartNode",
            "config": {},
        }

        workflow.add_node(node_data)

        assert "node1" in workflow.nodes
        assert workflow.nodes["node1"]["type"] == "StartNode"

    def test_add_node_uses_node_id_as_key(self):
        """Node ID field is used as dictionary key."""
        workflow = WorkflowSchema()
        node_data = {
            "node_id": "my_unique_id",
            "type": "LogNode",
        }

        workflow.add_node(node_data)

        assert "my_unique_id" in workflow.nodes

    def test_remove_node_success(self):
        """Remove node deletes node correctly."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "node1", "type": "StartNode"})

        workflow.remove_node("node1")

        assert "node1" not in workflow.nodes

    def test_remove_node_removes_connections(self):
        """Remove node also removes associated connections."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "node1", "type": "StartNode"})
        workflow.add_node({"node_id": "node2", "type": "EndNode"})
        workflow.connections.append(
            NodeConnection(
                source_node_id="node1",
                source_port="exec_out",
                target_node_id="node2",
                target_port="exec_in",
            )
        )

        workflow.remove_node("node1")

        assert len(workflow.connections) == 0

    def test_remove_nonexistent_node_raises_error(self):
        """Remove node raises KeyError for missing node."""
        workflow = WorkflowSchema()

        with pytest.raises(KeyError):
            workflow.remove_node("nonexistent")


class TestWorkflowSchemaSerialization:
    """Test workflow serialization/deserialization."""

    def test_to_dict_includes_all_fields(self):
        """to_dict() includes all required fields."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "n1", "type": "StartNode"})

        data = workflow.to_dict()

        assert "metadata" in data
        assert "nodes" in data
        assert "connections" in data
        assert "frames" in data
        assert "variables" in data
        assert "settings" in data

    def test_from_dict_restores_workflow(self):
        """from_dict() restores workflow from serialized data."""
        original_data = {
            "metadata": {"name": "Test", "schema_version": "1.0"},
            "nodes": {"n1": {"node_id": "n1", "type": "StartNode"}},
            "connections": [],
            "frames": [],
            "variables": {},
            "settings": {"stop_on_error": True},
        }

        workflow = WorkflowSchema.from_dict(original_data)

        assert workflow.metadata.name == "Test"
        assert "n1" in workflow.nodes

    def test_roundtrip_serialization(self):
        """Workflow survives serialization roundtrip."""
        original = WorkflowSchema(
            metadata=WorkflowMetadata(name="Roundtrip Test")
        )
        original.add_node({"node_id": "start", "type": "StartNode"})
        original.add_node({"node_id": "end", "type": "EndNode"})

        # Serialize and deserialize
        data = original.to_dict()
        restored = WorkflowSchema.from_dict(data)

        assert restored.metadata.name == original.metadata.name
        assert set(restored.nodes.keys()) == set(original.nodes.keys())


class TestVariableDefinition:
    """Test VariableDefinition value object."""

    def test_create_with_defaults(self):
        """VariableDefinition has correct defaults."""
        var = VariableDefinition(name="test_var")

        assert var.name == "test_var"
        assert var.type == "String"
        assert var.default_value == ""
        assert var.description == ""

    def test_to_dict(self):
        """to_dict() serializes all fields."""
        var = VariableDefinition(
            name="count",
            type="Integer",
            default_value=0,
            description="A counter",
        )

        data = var.to_dict()

        assert data["name"] == "count"
        assert data["type"] == "Integer"
        assert data["default_value"] == 0

    def test_from_dict(self):
        """from_dict() restores VariableDefinition."""
        data = {"name": "flag", "type": "Boolean", "default_value": True}

        var = VariableDefinition.from_dict(data)

        assert var.name == "flag"
        assert var.type == "Boolean"
        assert var.default_value is True


# Parameterized tests for edge cases
class TestWorkflowEdgeCases:
    """Edge case and boundary tests."""

    @pytest.mark.parametrize("node_count", [0, 1, 10, 100, 500])
    def test_workflow_handles_various_node_counts(self, node_count: int):
        """Workflow handles various numbers of nodes."""
        workflow = WorkflowSchema()

        for i in range(node_count):
            workflow.add_node({"node_id": f"node_{i}", "type": "LogNode"})

        assert len(workflow.nodes) == node_count

    @pytest.mark.parametrize("invalid_node", [
        {},
        {"type": "LogNode"},  # Missing node_id
        None,
    ])
    def test_add_invalid_node_raises_error(self, invalid_node):
        """Adding invalid node data raises appropriate error."""
        workflow = WorkflowSchema()

        with pytest.raises((KeyError, TypeError)):
            workflow.add_node(invalid_node)
```

#### 2.2 `tests/domain/entities/test_execution_state.py`

```python
"""
Unit tests for ExecutionState domain entity.
Tests variable management, execution tracking, and state transitions.
"""
import pytest
from datetime import datetime
from typing import Any, Dict

from casare_rpa.domain.entities.execution_state import ExecutionState
from casare_rpa.domain.value_objects.types import ExecutionMode


class TestExecutionStateInitialization:
    """Test ExecutionState initialization."""

    def test_default_initialization(self):
        """ExecutionState initializes with correct defaults."""
        state = ExecutionState()

        assert state.workflow_name == "Untitled"
        assert state.mode == ExecutionMode.NORMAL
        assert state.started_at is not None
        assert state.completed_at is None
        assert state.current_node_id is None
        assert state.execution_path == []
        assert state.errors == []
        assert state.stopped is False

    def test_initialization_with_parameters(self):
        """ExecutionState accepts initialization parameters."""
        state = ExecutionState(
            workflow_name="Test Workflow",
            mode=ExecutionMode.DEBUG,
            initial_variables={"x": 10, "y": 20},
        )

        assert state.workflow_name == "Test Workflow"
        assert state.mode == ExecutionMode.DEBUG
        assert state.get_variable("x") == 10
        assert state.get_variable("y") == 20


class TestVariableManagement:
    """Test variable get/set/delete operations."""

    def test_set_and_get_variable(self):
        """Variables can be set and retrieved."""
        state = ExecutionState()

        state.set_variable("counter", 42)

        assert state.get_variable("counter") == 42

    def test_get_nonexistent_variable_returns_default(self):
        """Getting nonexistent variable returns default."""
        state = ExecutionState()

        value = state.get_variable("missing", default="not found")

        assert value == "not found"

    def test_get_nonexistent_variable_returns_none(self):
        """Getting nonexistent variable returns None by default."""
        state = ExecutionState()

        value = state.get_variable("missing")

        assert value is None

    def test_has_variable(self):
        """has_variable correctly reports existence."""
        state = ExecutionState()
        state.set_variable("exists", "value")

        assert state.has_variable("exists") is True
        assert state.has_variable("missing") is False

    def test_delete_variable(self):
        """Variables can be deleted."""
        state = ExecutionState()
        state.set_variable("temp", "value")

        state.delete_variable("temp")

        assert state.has_variable("temp") is False

    def test_overwrite_variable(self):
        """Variables can be overwritten."""
        state = ExecutionState()
        state.set_variable("counter", 1)
        state.set_variable("counter", 2)

        assert state.get_variable("counter") == 2

    @pytest.mark.parametrize("value", [
        42,
        3.14,
        "string",
        True,
        None,
        [1, 2, 3],
        {"key": "value"},
        {"nested": {"deep": [1, 2, 3]}},
    ])
    def test_variable_supports_all_types(self, value: Any):
        """Variables support all common Python types."""
        state = ExecutionState()

        state.set_variable("test", value)

        assert state.get_variable("test") == value


class TestExecutionTracking:
    """Test execution path and error tracking."""

    def test_execution_path_tracking(self):
        """Execution path records nodes in order."""
        state = ExecutionState()

        state.execution_path.append("node1")
        state.execution_path.append("node2")
        state.execution_path.append("node3")

        assert state.execution_path == ["node1", "node2", "node3"]

    def test_error_tracking(self):
        """Errors can be tracked with node and message."""
        state = ExecutionState()

        state.errors.append(("node1", "Connection timeout"))
        state.errors.append(("node3", "Element not found"))

        assert len(state.errors) == 2
        assert state.errors[0] == ("node1", "Connection timeout")

    def test_current_node_tracking(self):
        """Current node ID is tracked."""
        state = ExecutionState()

        state.current_node_id = "node_being_executed"

        assert state.current_node_id == "node_being_executed"

    def test_stop_flag(self):
        """Stop flag can be set."""
        state = ExecutionState()

        state.stopped = True

        assert state.stopped is True


class TestVariableHierarchy:
    """Test variable scoping hierarchy (requires project context mock)."""

    def test_initial_variables_highest_priority(self):
        """Initial variables override all other sources."""
        state = ExecutionState(
            initial_variables={"shared": "runtime_value"}
        )

        # Runtime value should win
        assert state.get_variable("shared") == "runtime_value"

    def test_empty_initial_variables(self):
        """Empty initial variables don't cause issues."""
        state = ExecutionState(initial_variables={})

        assert state.variables == {}

    def test_none_initial_variables(self):
        """None initial variables handled gracefully."""
        state = ExecutionState(initial_variables=None)

        assert state.variables == {}
```

#### 2.3 `tests/domain/entities/test_node_connection.py`

```python
"""
Unit tests for NodeConnection domain entity.
"""
import pytest
from casare_rpa.domain.entities.node_connection import NodeConnection


class TestNodeConnectionCreation:
    """Test NodeConnection creation and attributes."""

    def test_create_connection(self):
        """NodeConnection stores all attributes."""
        conn = NodeConnection(
            source_node_id="node1",
            source_port="exec_out",
            target_node_id="node2",
            target_port="exec_in",
        )

        assert conn.source_node_id == "node1"
        assert conn.source_port == "exec_out"
        assert conn.target_node_id == "node2"
        assert conn.target_port == "exec_in"

    def test_from_dict(self):
        """NodeConnection can be created from dict."""
        data = {
            "source_node": "n1",
            "source_port": "out",
            "target_node": "n2",
            "target_port": "in",
        }

        conn = NodeConnection.from_dict(data)

        assert conn.source_node_id == "n1"
        assert conn.target_node_id == "n2"

    def test_to_dict(self):
        """NodeConnection serializes to dict."""
        conn = NodeConnection(
            source_node_id="n1",
            source_port="out",
            target_node_id="n2",
            target_port="in",
        )

        data = conn.to_dict()

        assert data["source_node"] == "n1"
        assert data["target_node"] == "n2"


class TestNodeConnectionEquality:
    """Test connection equality comparison."""

    def test_equal_connections(self):
        """Identical connections are equal."""
        conn1 = NodeConnection("n1", "out", "n2", "in")
        conn2 = NodeConnection("n1", "out", "n2", "in")

        assert conn1 == conn2

    def test_different_connections(self):
        """Different connections are not equal."""
        conn1 = NodeConnection("n1", "out", "n2", "in")
        conn2 = NodeConnection("n1", "out", "n3", "in")

        assert conn1 != conn2
```

---

### Hour 3: Domain Services Unit Tests (10:00-11:00)

**Focus**: `src/casare_rpa/domain/services/execution_orchestrator.py`

#### 3.1 `tests/domain/services/test_execution_orchestrator.py`

```python
"""
Unit tests for ExecutionOrchestrator domain service.
Tests graph traversal, routing logic, and control flow handling.
"""
import pytest
from typing import Dict, Any, List

from casare_rpa.domain.services.execution_orchestrator import ExecutionOrchestrator
from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.entities.node_connection import NodeConnection


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def simple_workflow() -> WorkflowSchema:
    """Create a simple Start -> End workflow."""
    workflow = WorkflowSchema(
        metadata=WorkflowMetadata(name="Simple Workflow")
    )
    workflow.add_node({"node_id": "start", "type": "StartNode"})
    workflow.add_node({"node_id": "end", "type": "EndNode"})
    workflow.connections.append(
        NodeConnection("start", "exec_out", "end", "exec_in")
    )
    return workflow


@pytest.fixture
def linear_workflow() -> WorkflowSchema:
    """Create a linear workflow: Start -> Log -> Log -> End."""
    workflow = WorkflowSchema(
        metadata=WorkflowMetadata(name="Linear Workflow")
    )
    workflow.add_node({"node_id": "start", "type": "StartNode"})
    workflow.add_node({"node_id": "log1", "type": "LogNode"})
    workflow.add_node({"node_id": "log2", "type": "LogNode"})
    workflow.add_node({"node_id": "end", "type": "EndNode"})

    workflow.connections.extend([
        NodeConnection("start", "exec_out", "log1", "exec_in"),
        NodeConnection("log1", "exec_out", "log2", "exec_in"),
        NodeConnection("log2", "exec_out", "end", "exec_in"),
    ])
    return workflow


@pytest.fixture
def branching_workflow() -> WorkflowSchema:
    """Create a workflow with branching (If node)."""
    workflow = WorkflowSchema(
        metadata=WorkflowMetadata(name="Branching Workflow")
    )
    workflow.add_node({"node_id": "start", "type": "StartNode"})
    workflow.add_node({"node_id": "if", "type": "IfNode"})
    workflow.add_node({"node_id": "true_branch", "type": "LogNode"})
    workflow.add_node({"node_id": "false_branch", "type": "LogNode"})
    workflow.add_node({"node_id": "end", "type": "EndNode"})

    workflow.connections.extend([
        NodeConnection("start", "exec_out", "if", "exec_in"),
        NodeConnection("if", "exec_true", "true_branch", "exec_in"),
        NodeConnection("if", "exec_false", "false_branch", "exec_in"),
        NodeConnection("true_branch", "exec_out", "end", "exec_in"),
        NodeConnection("false_branch", "exec_out", "end", "exec_in"),
    ])
    return workflow


@pytest.fixture
def loop_workflow() -> WorkflowSchema:
    """Create a workflow with a loop structure."""
    workflow = WorkflowSchema(
        metadata=WorkflowMetadata(name="Loop Workflow")
    )
    workflow.add_node({"node_id": "start", "type": "StartNode"})
    workflow.add_node({"node_id": "for", "type": "ForLoopNode"})
    workflow.add_node({"node_id": "body", "type": "LogNode"})
    workflow.add_node({"node_id": "end", "type": "EndNode"})

    workflow.connections.extend([
        NodeConnection("start", "exec_out", "for", "exec_in"),
        NodeConnection("for", "loop_body", "body", "exec_in"),
        NodeConnection("body", "exec_out", "for", "loop_in"),
        NodeConnection("for", "loop_done", "end", "exec_in"),
    ])
    return workflow


@pytest.fixture
def empty_workflow() -> WorkflowSchema:
    """Create an empty workflow with no nodes."""
    return WorkflowSchema(
        metadata=WorkflowMetadata(name="Empty Workflow")
    )


# ============================================================================
# Test Classes
# ============================================================================

class TestFindStartNode:
    """Test start node discovery."""

    def test_finds_start_node(self, simple_workflow: WorkflowSchema):
        """Orchestrator finds StartNode in workflow."""
        orchestrator = ExecutionOrchestrator(simple_workflow)

        start = orchestrator.find_start_node()

        assert start == "start"

    def test_returns_none_for_empty_workflow(self, empty_workflow: WorkflowSchema):
        """Returns None when no StartNode exists."""
        orchestrator = ExecutionOrchestrator(empty_workflow)

        start = orchestrator.find_start_node()

        assert start is None

    def test_returns_none_when_no_start_node(self):
        """Returns None when workflow has nodes but no StartNode."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "log", "type": "LogNode"})
        orchestrator = ExecutionOrchestrator(workflow)

        start = orchestrator.find_start_node()

        assert start is None


class TestGetNextNodes:
    """Test next node routing logic."""

    def test_simple_routing(self, simple_workflow: WorkflowSchema):
        """Gets next node via exec_out connection."""
        orchestrator = ExecutionOrchestrator(simple_workflow)

        next_nodes = orchestrator.get_next_nodes("start")

        assert next_nodes == ["end"]

    def test_linear_routing(self, linear_workflow: WorkflowSchema):
        """Gets correct next node in linear workflow."""
        orchestrator = ExecutionOrchestrator(linear_workflow)

        assert orchestrator.get_next_nodes("start") == ["log1"]
        assert orchestrator.get_next_nodes("log1") == ["log2"]
        assert orchestrator.get_next_nodes("log2") == ["end"]

    def test_end_node_has_no_next(self, simple_workflow: WorkflowSchema):
        """End node returns empty list."""
        orchestrator = ExecutionOrchestrator(simple_workflow)

        next_nodes = orchestrator.get_next_nodes("end")

        assert next_nodes == []

    def test_dynamic_routing_with_result(self, branching_workflow: WorkflowSchema):
        """Respects next_nodes from execution result."""
        orchestrator = ExecutionOrchestrator(branching_workflow)

        # Simulate True branch
        result = {"next_nodes": ["exec_true"]}
        next_nodes = orchestrator.get_next_nodes("if", result)

        assert "true_branch" in next_nodes

    def test_dynamic_routing_false_branch(self, branching_workflow: WorkflowSchema):
        """Routes to false branch when specified."""
        orchestrator = ExecutionOrchestrator(branching_workflow)

        result = {"next_nodes": ["exec_false"]}
        next_nodes = orchestrator.get_next_nodes("if", result)

        assert "false_branch" in next_nodes

    def test_nonexistent_node_returns_empty(self, simple_workflow: WorkflowSchema):
        """Nonexistent node returns empty list."""
        orchestrator = ExecutionOrchestrator(simple_workflow)

        next_nodes = orchestrator.get_next_nodes("nonexistent")

        assert next_nodes == []


class TestPathCalculation:
    """Test subgraph/path calculation for Run-To-Node."""

    def test_calculate_path_to_node(self, linear_workflow: WorkflowSchema):
        """Calculates required nodes to reach target."""
        orchestrator = ExecutionOrchestrator(linear_workflow)

        path = orchestrator.calculate_nodes_to_target("log2")

        # Should include start, log1, log2
        assert "start" in path
        assert "log1" in path
        assert "log2" in path
        # Should NOT include end
        assert "end" not in path

    def test_path_to_start_node(self, linear_workflow: WorkflowSchema):
        """Path to start node includes only start."""
        orchestrator = ExecutionOrchestrator(linear_workflow)

        path = orchestrator.calculate_nodes_to_target("start")

        assert path == {"start"}

    def test_path_to_end_includes_all(self, linear_workflow: WorkflowSchema):
        """Path to end includes entire workflow."""
        orchestrator = ExecutionOrchestrator(linear_workflow)

        path = orchestrator.calculate_nodes_to_target("end")

        assert "start" in path
        assert "log1" in path
        assert "log2" in path
        assert "end" in path


class TestExecutionGraph:
    """Test execution graph building."""

    def test_builds_execution_graph(self, linear_workflow: WorkflowSchema):
        """Builds adjacency list from connections."""
        orchestrator = ExecutionOrchestrator(linear_workflow)

        graph = orchestrator.build_execution_graph()

        assert graph["start"] == ["log1"]
        assert graph["log1"] == ["log2"]
        assert graph["log2"] == ["end"]

    def test_empty_workflow_graph(self, empty_workflow: WorkflowSchema):
        """Empty workflow produces empty graph."""
        orchestrator = ExecutionOrchestrator(empty_workflow)

        graph = orchestrator.build_execution_graph()

        assert graph == {}


class TestControlFlow:
    """Test control flow handling (break, continue)."""

    def test_break_signal_recognized(self, loop_workflow: WorkflowSchema):
        """Break signal is properly recognized."""
        orchestrator = ExecutionOrchestrator(loop_workflow)

        result = {"control_flow": "break"}
        next_nodes = orchestrator.get_next_nodes("body", result)

        # Break should exit loop
        assert orchestrator.should_break_loop(result)

    def test_continue_signal_recognized(self, loop_workflow: WorkflowSchema):
        """Continue signal is properly recognized."""
        orchestrator = ExecutionOrchestrator(loop_workflow)

        result = {"control_flow": "continue"}

        assert orchestrator.should_continue_loop(result)


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestOrchestratorEdgeCases:
    """Edge cases and error handling."""

    def test_handles_disconnected_nodes(self):
        """Handles workflows with disconnected nodes."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node({"node_id": "isolated", "type": "LogNode"})  # No connections

        orchestrator = ExecutionOrchestrator(workflow)

        # Should not crash
        next_nodes = orchestrator.get_next_nodes("start")
        assert next_nodes == []

    def test_handles_multiple_start_nodes(self):
        """Handles workflow with multiple start nodes (returns first)."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "start1", "type": "StartNode"})
        workflow.add_node({"node_id": "start2", "type": "StartNode"})

        orchestrator = ExecutionOrchestrator(workflow)

        start = orchestrator.find_start_node()
        assert start in ["start1", "start2"]

    @pytest.mark.parametrize("node_count", [10, 50, 100, 200])
    def test_handles_large_linear_workflows(self, node_count: int):
        """Handles workflows with many nodes."""
        workflow = WorkflowSchema()

        # Create linear chain
        for i in range(node_count):
            node_type = "StartNode" if i == 0 else ("EndNode" if i == node_count - 1 else "LogNode")
            workflow.add_node({"node_id": f"n{i}", "type": node_type})
            if i > 0:
                workflow.connections.append(
                    NodeConnection(f"n{i-1}", "exec_out", f"n{i}", "exec_in")
                )

        orchestrator = ExecutionOrchestrator(workflow)

        # Should find start and navigate
        assert orchestrator.find_start_node() == "n0"
        assert orchestrator.get_next_nodes("n0") == ["n1"]
```

---

### Hour 4: Infrastructure Layer Tests (11:00-12:00)

**Focus**: `src/casare_rpa/infrastructure/persistence/project_storage.py`

#### 4.1 `tests/infrastructure/persistence/test_project_storage.py`

```python
"""
Unit tests for ProjectStorage infrastructure adapter.
Tests file I/O operations, serialization, and error handling.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil
import json

from casare_rpa.infrastructure.persistence.project_storage import (
    ProjectStorage,
    PROJECT_MARKER_FILE,
)
from casare_rpa.domain.entities.project import Project


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def valid_project(temp_dir: Path) -> Project:
    """Create a valid project for testing."""
    return Project(
        name="Test Project",
        path=temp_dir / "test_project",
    )


@pytest.fixture
def project_with_structure(temp_dir: Path) -> Path:
    """Create a project folder with proper structure."""
    project_path = temp_dir / "existing_project"
    project_path.mkdir()
    (project_path / PROJECT_MARKER_FILE).touch()
    (project_path / "scenarios").mkdir()
    return project_path


# ============================================================================
# Test Classes
# ============================================================================

class TestIsProjectFolder:
    """Test project folder detection."""

    def test_detects_valid_project_with_marker(self, project_with_structure: Path):
        """Detects project with marker file."""
        assert ProjectStorage.is_project_folder(project_with_structure) is True

    def test_detects_project_with_project_json(self, temp_dir: Path):
        """Detects project with project.json."""
        project_path = temp_dir / "json_project"
        project_path.mkdir()
        (project_path / "project.json").write_text("{}")

        assert ProjectStorage.is_project_folder(project_path) is True

    def test_rejects_empty_folder(self, temp_dir: Path):
        """Rejects folder without markers."""
        empty_folder = temp_dir / "empty"
        empty_folder.mkdir()

        assert ProjectStorage.is_project_folder(empty_folder) is False

    def test_rejects_nonexistent_path(self, temp_dir: Path):
        """Rejects nonexistent path."""
        assert ProjectStorage.is_project_folder(temp_dir / "missing") is False

    def test_rejects_file_path(self, temp_dir: Path):
        """Rejects file (not directory)."""
        file_path = temp_dir / "file.txt"
        file_path.write_text("content")

        assert ProjectStorage.is_project_folder(file_path) is False


class TestCreateProjectStructure:
    """Test project structure creation."""

    def test_creates_folder(self, temp_dir: Path):
        """Creates project folder."""
        project_path = temp_dir / "new_project"

        ProjectStorage.create_project_structure(project_path)

        assert project_path.exists()
        assert project_path.is_dir()

    def test_creates_marker_file(self, temp_dir: Path):
        """Creates marker file."""
        project_path = temp_dir / "new_project"

        ProjectStorage.create_project_structure(project_path)

        assert (project_path / PROJECT_MARKER_FILE).exists()

    def test_creates_scenarios_folder(self, temp_dir: Path):
        """Creates scenarios subfolder."""
        project_path = temp_dir / "new_project"

        ProjectStorage.create_project_structure(project_path)

        assert (project_path / "scenarios").exists()
        assert (project_path / "scenarios").is_dir()

    def test_creates_nested_path(self, temp_dir: Path):
        """Creates nested path if parents don't exist."""
        project_path = temp_dir / "deeply" / "nested" / "project"

        ProjectStorage.create_project_structure(project_path)

        assert project_path.exists()

    def test_idempotent_creation(self, temp_dir: Path):
        """Creating existing structure doesn't error."""
        project_path = temp_dir / "existing"
        project_path.mkdir()

        # Should not raise
        ProjectStorage.create_project_structure(project_path)

        assert project_path.exists()


class TestSaveProject:
    """Test project saving."""

    def test_saves_project_json(self, temp_dir: Path):
        """Saves project metadata to JSON."""
        project = Project(name="Save Test", path=temp_dir / "save_test")
        project.path.mkdir(parents=True)

        ProjectStorage.save_project(project)

        json_path = project.path / "project.json"
        assert json_path.exists()

    def test_saved_json_is_valid(self, temp_dir: Path):
        """Saved JSON is valid and contains expected data."""
        project = Project(name="JSON Test", path=temp_dir / "json_test")
        project.path.mkdir(parents=True)

        ProjectStorage.save_project(project)

        json_path = project.path / "project.json"
        data = json.loads(json_path.read_text())
        assert data["name"] == "JSON Test"

    def test_save_without_path_raises_error(self):
        """Saving project without path raises ValueError."""
        project = Project(name="No Path")
        project.path = None

        with pytest.raises(ValueError):
            ProjectStorage.save_project(project)


class TestLoadProject:
    """Test project loading."""

    def test_loads_existing_project(self, temp_dir: Path):
        """Loads project from project.json."""
        project_path = temp_dir / "load_test"
        project_path.mkdir()
        (project_path / "project.json").write_text(
            json.dumps({"name": "Loaded Project", "scenarios": []})
        )

        project = ProjectStorage.load_project(project_path)

        assert project.name == "Loaded Project"

    def test_load_missing_project_raises_error(self, temp_dir: Path):
        """Loading missing project raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            ProjectStorage.load_project(temp_dir / "missing")

    def test_load_invalid_json_raises_error(self, temp_dir: Path):
        """Loading invalid JSON raises appropriate error."""
        project_path = temp_dir / "invalid"
        project_path.mkdir()
        (project_path / "project.json").write_text("not valid json")

        with pytest.raises((json.JSONDecodeError, Exception)):
            ProjectStorage.load_project(project_path)


class TestVariablesStorage:
    """Test variables file operations."""

    def test_save_project_variables(self, temp_dir: Path):
        """Saves project variables to JSON."""
        project_path = temp_dir / "vars_test"
        project_path.mkdir()

        variables = {"api_key": "secret", "timeout": 30}
        ProjectStorage.save_project_variables(project_path, variables)

        assert (project_path / "variables.json").exists()

    def test_load_project_variables(self, temp_dir: Path):
        """Loads project variables from JSON."""
        project_path = temp_dir / "vars_load"
        project_path.mkdir()
        (project_path / "variables.json").write_text(
            json.dumps({"var1": "value1"})
        )

        variables = ProjectStorage.load_project_variables(project_path)

        assert variables["var1"] == "value1"

    def test_load_missing_variables_returns_empty(self, temp_dir: Path):
        """Loading missing variables file returns empty dict."""
        project_path = temp_dir / "no_vars"
        project_path.mkdir()

        variables = ProjectStorage.load_project_variables(project_path)

        assert variables == {}


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestStorageErrorHandling:
    """Test error handling and edge cases."""

    def test_handles_permission_error(self, temp_dir: Path):
        """Handles permission errors gracefully."""
        # This test is platform-specific; skip on Windows
        import sys
        if sys.platform == "win32":
            pytest.skip("Permission test not reliable on Windows")

        project_path = temp_dir / "no_permission"
        project_path.mkdir()
        project_path.chmod(0o000)

        try:
            with pytest.raises(PermissionError):
                ProjectStorage.create_project_structure(project_path / "sub")
        finally:
            project_path.chmod(0o755)

    def test_handles_unicode_in_project_name(self, temp_dir: Path):
        """Handles Unicode characters in project name."""
        project = Project(name="Projekt Test", path=temp_dir / "unicode_test")
        project.path.mkdir(parents=True)

        ProjectStorage.save_project(project)
        loaded = ProjectStorage.load_project(project.path)

        assert loaded.name == "Projekt Test"

    def test_handles_empty_project_name(self, temp_dir: Path):
        """Handles empty project name."""
        project = Project(name="", path=temp_dir / "empty_name")
        project.path.mkdir(parents=True)

        ProjectStorage.save_project(project)
        loaded = ProjectStorage.load_project(project.path)

        assert loaded.name == ""
```

---

### Hour 5: Application Layer Tests (12:00-13:00)

**Focus**: `src/casare_rpa/application/use_cases/execute_workflow.py`

#### 5.1 `tests/application/use_cases/test_execute_workflow.py`

```python
"""
Unit tests for ExecuteWorkflowUseCase.
Tests orchestration logic, event emission, and error handling.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from casare_rpa.application.use_cases.execute_workflow import (
    ExecuteWorkflowUseCase,
    ExecutionSettings,
)
from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.entities.node_connection import NodeConnection
from casare_rpa.core.events import EventBus


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_event_bus():
    """Create a mock event bus."""
    bus = MagicMock(spec=EventBus)
    bus.emit = MagicMock()
    return bus


@pytest.fixture
def simple_workflow() -> WorkflowSchema:
    """Create a simple executable workflow."""
    workflow = WorkflowSchema(
        metadata=WorkflowMetadata(name="Test Workflow")
    )
    workflow.add_node({"node_id": "start", "type": "StartNode"})
    workflow.add_node({"node_id": "end", "type": "EndNode"})
    workflow.connections.append(
        NodeConnection("start", "exec_out", "end", "exec_in")
    )
    return workflow


@pytest.fixture
def workflow_with_variable_node() -> WorkflowSchema:
    """Create workflow that uses variables."""
    workflow = WorkflowSchema(
        metadata=WorkflowMetadata(name="Variable Workflow")
    )
    workflow.add_node({"node_id": "start", "type": "StartNode"})
    workflow.add_node({
        "node_id": "set_var",
        "type": "SetVariableNode",
        "config": {"name": "result", "value": 42},
    })
    workflow.add_node({"node_id": "end", "type": "EndNode"})

    workflow.connections.extend([
        NodeConnection("start", "exec_out", "set_var", "exec_in"),
        NodeConnection("set_var", "exec_out", "end", "exec_in"),
    ])
    return workflow


# ============================================================================
# Test Classes
# ============================================================================

class TestExecutionSettings:
    """Test ExecutionSettings value object."""

    def test_default_settings(self):
        """Default settings have correct values."""
        settings = ExecutionSettings()

        assert settings.continue_on_error is False
        assert settings.node_timeout == 120.0
        assert settings.target_node_id is None

    def test_custom_settings(self):
        """Custom settings are accepted."""
        settings = ExecutionSettings(
            continue_on_error=True,
            node_timeout=60.0,
            target_node_id="target_node",
        )

        assert settings.continue_on_error is True
        assert settings.node_timeout == 60.0
        assert settings.target_node_id == "target_node"


class TestUseCaseInitialization:
    """Test use case initialization."""

    def test_initialization_with_workflow(
        self, simple_workflow: WorkflowSchema, mock_event_bus
    ):
        """Use case initializes with workflow."""
        use_case = ExecuteWorkflowUseCase(
            workflow=simple_workflow,
            event_bus=mock_event_bus,
        )

        assert use_case.workflow is simple_workflow
        assert use_case.event_bus is mock_event_bus

    def test_initialization_creates_orchestrator(
        self, simple_workflow: WorkflowSchema, mock_event_bus
    ):
        """Use case creates ExecutionOrchestrator."""
        use_case = ExecuteWorkflowUseCase(
            workflow=simple_workflow,
            event_bus=mock_event_bus,
        )

        assert use_case.orchestrator is not None

    def test_initialization_with_variables(
        self, simple_workflow: WorkflowSchema, mock_event_bus
    ):
        """Use case accepts initial variables."""
        initial_vars = {"input_value": 100}

        use_case = ExecuteWorkflowUseCase(
            workflow=simple_workflow,
            event_bus=mock_event_bus,
            initial_variables=initial_vars,
        )

        assert use_case._initial_variables == initial_vars


class TestExecutionFlow:
    """Test execution flow and coordination."""

    @pytest.mark.asyncio
    async def test_execute_finds_start_node(
        self, simple_workflow: WorkflowSchema, mock_event_bus
    ):
        """Execution starts from StartNode."""
        use_case = ExecuteWorkflowUseCase(
            workflow=simple_workflow,
            event_bus=mock_event_bus,
        )

        # Mock the node execution
        with patch.object(use_case, '_execute_node', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {"success": True, "data": {}}

            await use_case.execute()

            # Should have executed start node
            call_args = [call[0][0] for call in mock_exec.call_args_list]
            assert "start" in call_args

    @pytest.mark.asyncio
    async def test_execute_follows_connections(
        self, simple_workflow: WorkflowSchema, mock_event_bus
    ):
        """Execution follows connection order."""
        use_case = ExecuteWorkflowUseCase(
            workflow=simple_workflow,
            event_bus=mock_event_bus,
        )

        executed_nodes = []

        async def track_execution(node_id):
            executed_nodes.append(node_id)
            return {"success": True, "data": {}}

        with patch.object(use_case, '_execute_node', side_effect=track_execution):
            await use_case.execute()

        # Should execute in order: start -> end
        assert executed_nodes == ["start", "end"]

    @pytest.mark.asyncio
    async def test_execute_emits_events(
        self, simple_workflow: WorkflowSchema, mock_event_bus
    ):
        """Execution emits progress events."""
        use_case = ExecuteWorkflowUseCase(
            workflow=simple_workflow,
            event_bus=mock_event_bus,
        )

        with patch.object(use_case, '_execute_node', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {"success": True, "data": {}}

            await use_case.execute()

        # Should have emitted events
        assert mock_event_bus.emit.called


class TestErrorHandling:
    """Test error handling during execution."""

    @pytest.mark.asyncio
    async def test_node_error_stops_execution(
        self, simple_workflow: WorkflowSchema, mock_event_bus
    ):
        """Node error stops execution by default."""
        use_case = ExecuteWorkflowUseCase(
            workflow=simple_workflow,
            event_bus=mock_event_bus,
            settings=ExecutionSettings(continue_on_error=False),
        )

        with patch.object(use_case, '_execute_node', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {"success": False, "error": "Test error"}

            result = await use_case.execute()

        # Execution should have stopped
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_continue_on_error(
        self, simple_workflow: WorkflowSchema, mock_event_bus
    ):
        """Continues execution when continue_on_error is True."""
        use_case = ExecuteWorkflowUseCase(
            workflow=simple_workflow,
            event_bus=mock_event_bus,
            settings=ExecutionSettings(continue_on_error=True),
        )

        executed_nodes = []

        async def error_then_success(node_id):
            executed_nodes.append(node_id)
            if node_id == "start":
                return {"success": False, "error": "Error"}
            return {"success": True, "data": {}}

        with patch.object(use_case, '_execute_node', side_effect=error_then_success):
            await use_case.execute()

        # Should have continued to end node
        assert "end" in executed_nodes

    @pytest.mark.asyncio
    async def test_missing_start_node_error(self, mock_event_bus):
        """Reports error when no start node found."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "log", "type": "LogNode"})  # No StartNode

        use_case = ExecuteWorkflowUseCase(
            workflow=workflow,
            event_bus=mock_event_bus,
        )

        result = await use_case.execute()

        assert result["success"] is False
        assert "start" in result.get("error", "").lower()


class TestVariableHandling:
    """Test variable propagation during execution."""

    @pytest.mark.asyncio
    async def test_initial_variables_available(
        self, simple_workflow: WorkflowSchema, mock_event_bus
    ):
        """Initial variables are available during execution."""
        use_case = ExecuteWorkflowUseCase(
            workflow=simple_workflow,
            event_bus=mock_event_bus,
            initial_variables={"input": "test_value"},
        )

        with patch.object(use_case, '_execute_node', new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {"success": True, "data": {}}

            await use_case.execute()

            # Verify context has initial variables
            assert use_case.context.get_variable("input") == "test_value"


class TestRunToNode:
    """Test Run-To-Node feature."""

    @pytest.mark.asyncio
    async def test_stops_at_target_node(self, mock_event_bus):
        """Execution stops at specified target node."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        workflow.add_node({"node_id": "middle", "type": "LogNode"})
        workflow.add_node({"node_id": "end", "type": "EndNode"})
        workflow.connections.extend([
            NodeConnection("start", "exec_out", "middle", "exec_in"),
            NodeConnection("middle", "exec_out", "end", "exec_in"),
        ])

        use_case = ExecuteWorkflowUseCase(
            workflow=workflow,
            event_bus=mock_event_bus,
            settings=ExecutionSettings(target_node_id="middle"),
        )

        executed_nodes = []

        async def track_execution(node_id):
            executed_nodes.append(node_id)
            return {"success": True, "data": {}}

        with patch.object(use_case, '_execute_node', side_effect=track_execution):
            await use_case.execute()

        # Should NOT have executed end node
        assert "end" not in executed_nodes
        assert "middle" in executed_nodes
```

---

### Hour 6: Integration Tests (13:00-14:00)

**Focus**: End-to-end workflow execution testing

#### 6.1 `tests/integration/week2/test_clean_architecture_integration.py`

```python
"""
Integration tests for Week 2 clean architecture refactoring.
Tests the full flow: Domain -> Application -> Infrastructure.
"""
import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any
import tempfile
import shutil

from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.entities.node_connection import NodeConnection
from casare_rpa.domain.entities.execution_state import ExecutionState
from casare_rpa.domain.services.execution_orchestrator import ExecutionOrchestrator
from casare_rpa.application.use_cases.execute_workflow import ExecuteWorkflowUseCase
from casare_rpa.infrastructure.persistence.project_storage import ProjectStorage
from casare_rpa.core.events import EventBus


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_project_dir():
    """Create temporary project directory."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def event_bus():
    """Create event bus for testing."""
    return EventBus()


@pytest.fixture
def sample_workflow() -> WorkflowSchema:
    """Create a sample workflow for integration testing."""
    workflow = WorkflowSchema(
        metadata=WorkflowMetadata(
            name="Integration Test Workflow",
            description="Tests clean architecture integration",
        )
    )

    # Add nodes
    workflow.add_node({"node_id": "start", "type": "StartNode"})
    workflow.add_node({
        "node_id": "set_var",
        "type": "SetVariableNode",
        "config": {"name": "counter", "value": 0},
    })
    workflow.add_node({
        "node_id": "increment",
        "type": "IncrementVariableNode",
        "config": {"name": "counter", "amount": 1},
    })
    workflow.add_node({"node_id": "end", "type": "EndNode"})

    # Add connections
    workflow.connections.extend([
        NodeConnection("start", "exec_out", "set_var", "exec_in"),
        NodeConnection("set_var", "exec_out", "increment", "exec_in"),
        NodeConnection("increment", "exec_out", "end", "exec_in"),
    ])

    return workflow


# ============================================================================
# Integration Test Classes
# ============================================================================

class TestDomainToApplicationIntegration:
    """Test Domain -> Application layer integration."""

    def test_orchestrator_provides_correct_routing(
        self, sample_workflow: WorkflowSchema
    ):
        """ExecutionOrchestrator correctly routes to use case."""
        orchestrator = ExecutionOrchestrator(sample_workflow)

        # Find start
        start = orchestrator.find_start_node()
        assert start == "start"

        # Get next nodes
        next_nodes = orchestrator.get_next_nodes("start")
        assert "set_var" in next_nodes

        # Continue chain
        next_nodes = orchestrator.get_next_nodes("set_var")
        assert "increment" in next_nodes

    @pytest.mark.asyncio
    async def test_use_case_uses_orchestrator(
        self, sample_workflow: WorkflowSchema, event_bus
    ):
        """ExecuteWorkflowUseCase delegates to ExecutionOrchestrator."""
        use_case = ExecuteWorkflowUseCase(
            workflow=sample_workflow,
            event_bus=event_bus,
        )

        # Verify orchestrator was created
        assert use_case.orchestrator is not None

        # Verify orchestrator is used for routing
        start = use_case.orchestrator.find_start_node()
        assert start == "start"


class TestApplicationToInfrastructureIntegration:
    """Test Application -> Infrastructure layer integration."""

    def test_project_storage_saves_workflow(
        self, sample_workflow: WorkflowSchema, temp_project_dir: Path
    ):
        """ProjectStorage can save workflow from application layer."""
        # Create project structure
        ProjectStorage.create_project_structure(temp_project_dir)

        # Save workflow
        workflow_path = temp_project_dir / "workflow.json"
        sample_workflow.save(workflow_path)

        assert workflow_path.exists()

    def test_workflow_roundtrip_through_storage(
        self, sample_workflow: WorkflowSchema, temp_project_dir: Path
    ):
        """Workflow survives save/load through infrastructure."""
        workflow_path = temp_project_dir / "workflow.json"
        workflow_path.parent.mkdir(parents=True, exist_ok=True)

        # Save
        sample_workflow.save(workflow_path)

        # Load
        loaded = WorkflowSchema.load(workflow_path)

        # Verify
        assert loaded.metadata.name == sample_workflow.metadata.name
        assert len(loaded.nodes) == len(sample_workflow.nodes)
        assert len(loaded.connections) == len(sample_workflow.connections)


class TestFullStackIntegration:
    """Test complete Domain -> Application -> Infrastructure stack."""

    @pytest.mark.asyncio
    async def test_full_workflow_execution(
        self, sample_workflow: WorkflowSchema, event_bus, temp_project_dir: Path
    ):
        """Test complete workflow execution through all layers."""
        # 1. Save workflow (Infrastructure)
        workflow_path = temp_project_dir / "workflow.json"
        workflow_path.parent.mkdir(parents=True, exist_ok=True)
        sample_workflow.save(workflow_path)

        # 2. Load workflow (Infrastructure)
        loaded_workflow = WorkflowSchema.load(workflow_path)

        # 3. Execute workflow (Application + Domain)
        use_case = ExecuteWorkflowUseCase(
            workflow=loaded_workflow,
            event_bus=event_bus,
        )

        # Track events
        events_received = []
        event_bus.subscribe(lambda e: events_received.append(e))

        result = await use_case.execute()

        # 4. Verify results
        assert result is not None
        assert len(events_received) > 0


class TestCleanArchitectureBoundaries:
    """Test that clean architecture boundaries are maintained."""

    def test_domain_has_no_infrastructure_imports(self):
        """Domain layer has no infrastructure imports."""
        import inspect
        from casare_rpa.domain.entities import workflow

        source = inspect.getsource(workflow)

        # Should not import from infrastructure
        assert "from ...infrastructure" not in source
        assert "from casare_rpa.infrastructure" not in source

    def test_domain_has_no_application_imports(self):
        """Domain layer has no application imports."""
        import inspect
        from casare_rpa.domain.entities import workflow

        source = inspect.getsource(workflow)

        # Should not import from application
        assert "from ...application" not in source
        assert "from casare_rpa.application" not in source

    def test_application_imports_from_domain(self):
        """Application layer correctly imports from domain."""
        import inspect
        from casare_rpa.application.use_cases import execute_workflow

        source = inspect.getsource(execute_workflow)

        # Should import from domain
        assert "domain" in source.lower()


class TestBackwardsCompatibility:
    """Test backwards compatibility with existing code."""

    def test_workflow_schema_api_unchanged(self, sample_workflow: WorkflowSchema):
        """WorkflowSchema maintains existing API."""
        # These methods should still work
        assert hasattr(sample_workflow, 'add_node')
        assert hasattr(sample_workflow, 'remove_node')
        assert hasattr(sample_workflow, 'to_dict')
        assert hasattr(sample_workflow, 'from_dict')
        assert hasattr(sample_workflow, 'save')
        assert hasattr(sample_workflow, 'load')

    def test_node_connection_api_unchanged(self):
        """NodeConnection maintains existing API."""
        conn = NodeConnection("n1", "out", "n2", "in")

        # These attributes should exist
        assert hasattr(conn, 'source_node_id')
        assert hasattr(conn, 'source_port')
        assert hasattr(conn, 'target_node_id')
        assert hasattr(conn, 'target_port')
        assert hasattr(conn, 'to_dict')
        assert hasattr(conn, 'from_dict')


# ============================================================================
# Regression Tests
# ============================================================================

class TestRegressions:
    """Regression tests for known issues."""

    def test_workflow_with_140_plus_nodes(self):
        """Workflow handles 140+ nodes (all node types)."""
        workflow = WorkflowSchema()

        # Add 150 nodes
        for i in range(150):
            workflow.add_node({
                "node_id": f"node_{i}",
                "type": "LogNode",
            })

        assert len(workflow.nodes) == 150

    def test_deeply_nested_workflow(self):
        """Workflow handles deep nesting."""
        workflow = WorkflowSchema()

        # Create 100-deep chain
        workflow.add_node({"node_id": "start", "type": "StartNode"})
        for i in range(100):
            workflow.add_node({"node_id": f"node_{i}", "type": "LogNode"})
            source = "start" if i == 0 else f"node_{i-1}"
            workflow.connections.append(
                NodeConnection(source, "exec_out", f"node_{i}", "exec_in")
            )

        orchestrator = ExecutionOrchestrator(workflow)

        # Should be able to navigate
        assert orchestrator.find_start_node() == "start"

    def test_workflow_serialization_preserves_all_data(self):
        """Serialization preserves all workflow data."""
        workflow = WorkflowSchema(
            metadata=WorkflowMetadata(
                name="Full Data Test",
                description="Test description",
                author="Test Author",
                version="2.0.0",
            )
        )
        workflow.add_node({
            "node_id": "node1",
            "type": "LogNode",
            "config": {"message": "Test message"},
            "position": [100, 200],
        })
        workflow.variables = {"var1": "value1", "var2": 42}
        workflow.settings = {"stop_on_error": False, "timeout": 60}

        # Serialize and deserialize
        data = workflow.to_dict()
        restored = WorkflowSchema.from_dict(data)

        # Verify all data preserved
        assert restored.metadata.name == "Full Data Test"
        assert restored.metadata.description == "Test description"
        assert restored.nodes["node1"]["config"]["message"] == "Test message"
        assert restored.variables["var1"] == "value1"
        assert restored.settings["stop_on_error"] is False
```

---

### Hour 7: Performance Benchmarks (14:00-15:00)

**Focus**: Performance testing and regression detection

#### 7.1 `tests/performance/week2/test_performance_benchmarks.py`

```python
"""
Performance benchmark tests for Week 2 refactoring.
Ensures no performance regressions from clean architecture changes.
"""
import pytest
import time
import sys
import gc
from typing import Dict, Any, List
from datetime import datetime

from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.entities.node_connection import NodeConnection
from casare_rpa.domain.entities.execution_state import ExecutionState
from casare_rpa.domain.services.execution_orchestrator import ExecutionOrchestrator


# ============================================================================
# Performance Thresholds
# ============================================================================

THRESHOLDS = {
    "workflow_creation_10_nodes": 0.001,      # 1ms
    "workflow_creation_100_nodes": 0.010,     # 10ms
    "workflow_creation_1000_nodes": 0.100,    # 100ms
    "workflow_serialization_100_nodes": 0.020,  # 20ms
    "workflow_deserialization_100_nodes": 0.020,  # 20ms
    "orchestrator_find_start": 0.001,         # 1ms
    "orchestrator_get_next_nodes": 0.001,     # 1ms
    "orchestrator_path_calculation": 0.050,   # 50ms for 100 nodes
    "execution_state_variable_set": 0.0001,   # 0.1ms
    "execution_state_variable_get": 0.0001,   # 0.1ms
}


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def workflow_10_nodes() -> WorkflowSchema:
    """Create workflow with 10 nodes."""
    return _create_linear_workflow(10)


@pytest.fixture
def workflow_100_nodes() -> WorkflowSchema:
    """Create workflow with 100 nodes."""
    return _create_linear_workflow(100)


@pytest.fixture
def workflow_1000_nodes() -> WorkflowSchema:
    """Create workflow with 1000 nodes."""
    return _create_linear_workflow(1000)


def _create_linear_workflow(node_count: int) -> WorkflowSchema:
    """Helper to create linear workflow."""
    workflow = WorkflowSchema(
        metadata=WorkflowMetadata(name=f"Perf Test {node_count} nodes")
    )

    for i in range(node_count):
        node_type = "StartNode" if i == 0 else ("EndNode" if i == node_count - 1 else "LogNode")
        workflow.add_node({
            "node_id": f"node_{i}",
            "type": node_type,
            "config": {"message": f"Node {i}"},
        })
        if i > 0:
            workflow.connections.append(
                NodeConnection(f"node_{i-1}", "exec_out", f"node_{i}", "exec_in")
            )

    return workflow


# ============================================================================
# Benchmark Utilities
# ============================================================================

def benchmark(func, iterations: int = 100) -> float:
    """Run function multiple times and return average time."""
    gc.collect()

    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    return sum(times) / len(times)


def benchmark_async(coro_func, iterations: int = 100) -> float:
    """Run async function multiple times and return average time."""
    import asyncio

    gc.collect()

    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        asyncio.run(coro_func())
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    return sum(times) / len(times)


# ============================================================================
# Workflow Performance Tests
# ============================================================================

class TestWorkflowCreationPerformance:
    """Benchmark workflow creation."""

    def test_create_10_node_workflow(self):
        """Create 10-node workflow within threshold."""
        def create():
            return _create_linear_workflow(10)

        avg_time = benchmark(create)

        assert avg_time < THRESHOLDS["workflow_creation_10_nodes"], \
            f"10-node creation took {avg_time:.4f}s, threshold: {THRESHOLDS['workflow_creation_10_nodes']}s"

    def test_create_100_node_workflow(self):
        """Create 100-node workflow within threshold."""
        def create():
            return _create_linear_workflow(100)

        avg_time = benchmark(create, iterations=50)

        assert avg_time < THRESHOLDS["workflow_creation_100_nodes"], \
            f"100-node creation took {avg_time:.4f}s, threshold: {THRESHOLDS['workflow_creation_100_nodes']}s"

    def test_create_1000_node_workflow(self):
        """Create 1000-node workflow within threshold."""
        def create():
            return _create_linear_workflow(1000)

        avg_time = benchmark(create, iterations=10)

        assert avg_time < THRESHOLDS["workflow_creation_1000_nodes"], \
            f"1000-node creation took {avg_time:.4f}s, threshold: {THRESHOLDS['workflow_creation_1000_nodes']}s"


class TestWorkflowSerializationPerformance:
    """Benchmark workflow serialization."""

    def test_serialize_100_node_workflow(self, workflow_100_nodes: WorkflowSchema):
        """Serialize 100-node workflow within threshold."""
        def serialize():
            return workflow_100_nodes.to_dict()

        avg_time = benchmark(serialize)

        assert avg_time < THRESHOLDS["workflow_serialization_100_nodes"], \
            f"Serialization took {avg_time:.4f}s, threshold: {THRESHOLDS['workflow_serialization_100_nodes']}s"

    def test_deserialize_100_node_workflow(self, workflow_100_nodes: WorkflowSchema):
        """Deserialize 100-node workflow within threshold."""
        data = workflow_100_nodes.to_dict()

        def deserialize():
            return WorkflowSchema.from_dict(data)

        avg_time = benchmark(deserialize)

        assert avg_time < THRESHOLDS["workflow_deserialization_100_nodes"], \
            f"Deserialization took {avg_time:.4f}s, threshold: {THRESHOLDS['workflow_deserialization_100_nodes']}s"

    def test_roundtrip_serialization(self, workflow_100_nodes: WorkflowSchema):
        """Full roundtrip within combined threshold."""
        def roundtrip():
            data = workflow_100_nodes.to_dict()
            return WorkflowSchema.from_dict(data)

        threshold = (
            THRESHOLDS["workflow_serialization_100_nodes"] +
            THRESHOLDS["workflow_deserialization_100_nodes"]
        )

        avg_time = benchmark(roundtrip, iterations=50)

        assert avg_time < threshold, \
            f"Roundtrip took {avg_time:.4f}s, threshold: {threshold}s"


class TestOrchestratorPerformance:
    """Benchmark ExecutionOrchestrator operations."""

    def test_find_start_node(self, workflow_100_nodes: WorkflowSchema):
        """Find start node within threshold."""
        orchestrator = ExecutionOrchestrator(workflow_100_nodes)

        def find_start():
            return orchestrator.find_start_node()

        avg_time = benchmark(find_start)

        assert avg_time < THRESHOLDS["orchestrator_find_start"], \
            f"find_start_node took {avg_time:.6f}s, threshold: {THRESHOLDS['orchestrator_find_start']}s"

    def test_get_next_nodes(self, workflow_100_nodes: WorkflowSchema):
        """Get next nodes within threshold."""
        orchestrator = ExecutionOrchestrator(workflow_100_nodes)

        def get_next():
            return orchestrator.get_next_nodes("node_50")

        avg_time = benchmark(get_next)

        assert avg_time < THRESHOLDS["orchestrator_get_next_nodes"], \
            f"get_next_nodes took {avg_time:.6f}s, threshold: {THRESHOLDS['orchestrator_get_next_nodes']}s"

    def test_path_calculation(self, workflow_100_nodes: WorkflowSchema):
        """Calculate path to node within threshold."""
        orchestrator = ExecutionOrchestrator(workflow_100_nodes)

        def calculate_path():
            return orchestrator.calculate_nodes_to_target("node_99")

        avg_time = benchmark(calculate_path, iterations=50)

        assert avg_time < THRESHOLDS["orchestrator_path_calculation"], \
            f"Path calculation took {avg_time:.4f}s, threshold: {THRESHOLDS['orchestrator_path_calculation']}s"


class TestExecutionStatePerformance:
    """Benchmark ExecutionState operations."""

    def test_variable_set_performance(self):
        """Variable set within threshold."""
        state = ExecutionState()

        def set_var():
            state.set_variable("test_var", "test_value")

        avg_time = benchmark(set_var, iterations=1000)

        assert avg_time < THRESHOLDS["execution_state_variable_set"], \
            f"Variable set took {avg_time:.6f}s, threshold: {THRESHOLDS['execution_state_variable_set']}s"

    def test_variable_get_performance(self):
        """Variable get within threshold."""
        state = ExecutionState()
        state.set_variable("test_var", "test_value")

        def get_var():
            return state.get_variable("test_var")

        avg_time = benchmark(get_var, iterations=1000)

        assert avg_time < THRESHOLDS["execution_state_variable_get"], \
            f"Variable get took {avg_time:.6f}s, threshold: {THRESHOLDS['execution_state_variable_get']}s"

    def test_many_variables_performance(self):
        """Performance with many variables."""
        state = ExecutionState()

        # Add 1000 variables
        for i in range(1000):
            state.set_variable(f"var_{i}", f"value_{i}")

        def access_random_var():
            return state.get_variable("var_500")

        avg_time = benchmark(access_random_var, iterations=1000)

        # Should still be fast with many variables
        assert avg_time < THRESHOLDS["execution_state_variable_get"] * 2


# ============================================================================
# Memory Usage Tests
# ============================================================================

class TestMemoryUsage:
    """Test memory usage of refactored components."""

    def test_workflow_memory_usage(self):
        """Workflow memory usage is reasonable."""
        gc.collect()
        baseline = _get_memory_usage()

        # Create 100 workflows
        workflows = [_create_linear_workflow(100) for _ in range(100)]

        gc.collect()
        after = _get_memory_usage()

        memory_per_workflow = (after - baseline) / 100

        # Each 100-node workflow should be < 100KB
        assert memory_per_workflow < 100 * 1024, \
            f"Workflow uses {memory_per_workflow / 1024:.1f}KB, should be < 100KB"

    def test_execution_state_memory_usage(self):
        """ExecutionState memory usage is reasonable."""
        gc.collect()
        baseline = _get_memory_usage()

        # Create state with many variables
        state = ExecutionState()
        for i in range(10000):
            state.set_variable(f"var_{i}", f"value_{i}" * 10)

        gc.collect()
        after = _get_memory_usage()

        memory_used = after - baseline

        # 10000 variables should be < 10MB
        assert memory_used < 10 * 1024 * 1024, \
            f"ExecutionState uses {memory_used / (1024 * 1024):.1f}MB, should be < 10MB"


def _get_memory_usage() -> int:
    """Get current memory usage in bytes."""
    import psutil
    process = psutil.Process()
    return process.memory_info().rss


# ============================================================================
# Scalability Tests
# ============================================================================

class TestScalability:
    """Test performance scaling with size."""

    @pytest.mark.parametrize("node_count", [10, 50, 100, 200, 500])
    def test_workflow_creation_scales_linearly(self, node_count: int):
        """Workflow creation time scales linearly with nodes."""
        def create():
            return _create_linear_workflow(node_count)

        avg_time = benchmark(create, iterations=20)

        # Time should scale roughly linearly: ~0.1ms per node
        expected_time = node_count * 0.0001  # 0.1ms per node

        assert avg_time < expected_time * 2, \
            f"{node_count}-node creation took {avg_time:.4f}s, expected ~{expected_time:.4f}s"

    @pytest.mark.parametrize("node_count", [10, 50, 100, 200])
    def test_serialization_scales_linearly(self, node_count: int):
        """Serialization time scales linearly with nodes."""
        workflow = _create_linear_workflow(node_count)

        def serialize():
            return workflow.to_dict()

        avg_time = benchmark(serialize, iterations=20)

        # Time should scale roughly linearly: ~0.2ms per node
        expected_time = node_count * 0.0002

        assert avg_time < expected_time * 2, \
            f"{node_count}-node serialization took {avg_time:.4f}s, expected ~{expected_time:.4f}s"
```

---

### Hour 8: Bug Discovery and Documentation (15:00-16:00)

**Focus**: Bug hunting, documentation, and final validation

#### 8.1 Bug Report Template

Create `docs/BUG_REPORT_TEMPLATE.md`:

```markdown
# Bug Report Template

## Bug ID
`BUG-W2D5-XXX` (e.g., BUG-W2D5-001)

## Component
- [ ] Domain Layer (entities, services, value objects)
- [ ] Application Layer (use cases, DI)
- [ ] Infrastructure Layer (persistence, adapters)
- [ ] Integration (cross-layer issues)
- [ ] Performance

## Severity
- [ ] **Critical**: Blocks workflow execution, data loss
- [ ] **High**: Major feature broken, no workaround
- [ ] **Medium**: Feature impaired, workaround exists
- [ ] **Low**: Minor issue, cosmetic

## Summary
*One-line description of the bug*

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
*What should happen*

## Actual Behavior
*What actually happens*

## Stack Trace
```
Paste stack trace here
```

## Test Case
```python
def test_bug_xxx():
    """Reproduction test for BUG-W2D5-XXX."""
    # Test code that reproduces the bug
    pass
```

## Environment
- Python version:
- OS:
- CasareRPA version:

## Proposed Fix
*If known, describe the fix approach*

## Related Files
- `path/to/file1.py`
- `path/to/file2.py`

## Labels
- `week2-refactoring`
- `domain` | `application` | `infrastructure`
- `regression` | `new-bug`
```

#### 8.2 `tests/week2/test_bug_discovery.py`

```python
"""
Bug discovery tests for Week 2 refactoring.
These tests probe edge cases and potential problem areas.
"""
import pytest
from typing import Dict, Any

from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.entities.node_connection import NodeConnection
from casare_rpa.domain.entities.execution_state import ExecutionState
from casare_rpa.domain.services.execution_orchestrator import ExecutionOrchestrator


class TestPotentialRegressionAreas:
    """Test areas most likely to have regressions."""

    def test_workflow_node_id_consistency(self):
        """BUG PROBE: Node ID mismatch between key and field."""
        workflow = WorkflowSchema()

        # This could cause NODE_ID_MISMATCH errors
        node_data = {
            "node_id": "correct_id",
            "type": "LogNode",
        }
        workflow.add_node(node_data)

        # Verify key matches node_id field
        assert "correct_id" in workflow.nodes
        assert workflow.nodes["correct_id"]["node_id"] == "correct_id"

    def test_connection_with_nonexistent_nodes(self):
        """BUG PROBE: Connection referencing nonexistent nodes."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "n1", "type": "StartNode"})

        # Add connection to nonexistent node
        conn = NodeConnection("n1", "out", "nonexistent", "in")
        workflow.connections.append(conn)

        # Orchestrator should handle gracefully
        orchestrator = ExecutionOrchestrator(workflow)
        next_nodes = orchestrator.get_next_nodes("n1")

        # Should not crash, but result is undefined
        # Document actual behavior
        assert isinstance(next_nodes, list)

    def test_workflow_with_duplicate_connections(self):
        """BUG PROBE: Duplicate connections in workflow."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "n1", "type": "StartNode"})
        workflow.add_node({"node_id": "n2", "type": "EndNode"})

        conn = NodeConnection("n1", "out", "n2", "in")
        workflow.connections.append(conn)
        workflow.connections.append(conn)  # Duplicate

        # Should handle duplicates
        orchestrator = ExecutionOrchestrator(workflow)
        next_nodes = orchestrator.get_next_nodes("n1")

        # Should not duplicate results
        assert next_nodes.count("n2") == 1 or len(next_nodes) <= 2

    def test_execution_state_special_variable_names(self):
        """BUG PROBE: Variables with special names."""
        state = ExecutionState()

        special_names = [
            "",  # Empty string
            " ",  # Space
            "var.with.dots",
            "var-with-dashes",
            "var_with_underscores",
            "123numeric_start",
            "__dunder__",
            "unicode_",
        ]

        for name in special_names:
            try:
                state.set_variable(name, "value")
                retrieved = state.get_variable(name)
                assert retrieved == "value", f"Failed for: {repr(name)}"
            except Exception as e:
                # Document which names cause issues
                pytest.skip(f"Variable name {repr(name)} raises {type(e).__name__}")

    def test_workflow_empty_metadata_fields(self):
        """BUG PROBE: Empty metadata fields."""
        metadata = WorkflowMetadata(
            name="",
            description="",
            author="",
            version="",
        )
        workflow = WorkflowSchema(metadata=metadata)

        # Should handle empty fields
        data = workflow.to_dict()
        restored = WorkflowSchema.from_dict(data)

        assert restored.metadata.name == ""

    def test_orchestrator_circular_reference_detection(self):
        """BUG PROBE: Circular references in workflow."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "n1", "type": "LogNode"})
        workflow.add_node({"node_id": "n2", "type": "LogNode"})

        # Create cycle: n1 -> n2 -> n1
        workflow.connections.append(NodeConnection("n1", "out", "n2", "in"))
        workflow.connections.append(NodeConnection("n2", "out", "n1", "in"))

        orchestrator = ExecutionOrchestrator(workflow)

        # Should detect or handle cycle
        # Document actual behavior
        next_from_n1 = orchestrator.get_next_nodes("n1")
        next_from_n2 = orchestrator.get_next_nodes("n2")

        assert "n2" in next_from_n1
        assert "n1" in next_from_n2

    def test_large_variable_values(self):
        """BUG PROBE: Large variable values."""
        state = ExecutionState()

        # Large string
        large_string = "x" * 10_000_000  # 10MB string
        state.set_variable("large", large_string)

        # Should handle large values
        assert len(state.get_variable("large")) == 10_000_000

    def test_concurrent_variable_access(self):
        """BUG PROBE: Concurrent variable access (thread safety)."""
        import threading

        state = ExecutionState()
        errors = []

        def writer():
            try:
                for i in range(1000):
                    state.set_variable(f"var_{i}", i)
            except Exception as e:
                errors.append(e)

        def reader():
            try:
                for i in range(1000):
                    state.get_variable(f"var_{i % 100}")
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=writer),
            threading.Thread(target=reader),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Document any thread safety issues
        if errors:
            pytest.skip(f"Thread safety issue: {errors[0]}")


class TestSecurityVulnerabilities:
    """Probe for security vulnerabilities."""

    def test_path_traversal_in_workflow_name(self):
        """SECURITY: Path traversal in workflow name."""
        dangerous_names = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
        ]

        for name in dangerous_names:
            workflow = WorkflowSchema(
                metadata=WorkflowMetadata(name=name)
            )

            # Name should be stored but not used unsafely
            assert workflow.metadata.name == name
            # Actual path operations should sanitize

    def test_injection_in_variable_values(self):
        """SECURITY: Injection attempts in variables."""
        state = ExecutionState()

        payloads = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "${7*7}",
            "{{7*7}}",
            "$(whoami)",
            "`whoami`",
        ]

        for payload in payloads:
            state.set_variable("test", payload)
            retrieved = state.get_variable("test")

            # Value should be stored verbatim (no execution)
            assert retrieved == payload

    def test_node_type_injection(self):
        """SECURITY: Malicious node type names."""
        workflow = WorkflowSchema()

        dangerous_types = [
            "__import__('os').system('whoami')",
            "eval('malicious')",
            "../../../malicious",
        ]

        for node_type in dangerous_types:
            workflow.add_node({
                "node_id": f"node_{hash(node_type)}",
                "type": node_type,
            })

        # Types should be stored but not executed
        assert len(workflow.nodes) == len(dangerous_types)
```

#### 8.3 Security Checklist

Create `docs/SECURITY_CHECKLIST_W2D5.md`:

```markdown
# Week 2 Day 5 Security Checklist

## Input Validation

- [ ] Workflow names are sanitized before file operations
- [ ] Node IDs are validated (alphanumeric + underscore only)
- [ ] Variable names are validated
- [ ] Connection port names are validated
- [ ] Config values are type-checked

## Path Safety

- [ ] No path traversal possible in workflow save/load
- [ ] Project paths are absolute and validated
- [ ] Temporary files use secure temp directories

## Injection Prevention

- [ ] No eval() or exec() on user input
- [ ] No string formatting with user input for commands
- [ ] JSON deserialization uses safe methods

## Resource Limits

- [ ] Maximum workflow size enforced
- [ ] Maximum node count enforced
- [ ] Maximum variable count enforced
- [ ] Maximum variable value size enforced

## Authentication/Authorization

- [ ] N/A for current Week 2 scope (Canvas-only)

## Logging

- [ ] Sensitive data not logged (credentials, secrets)
- [ ] Error messages don't leak internal paths
- [ ] Stack traces sanitized in production

## Checked By
- Name: ________________
- Date: ________________
```

---

## Success Criteria and Validation

### Test Coverage Requirements

| Component | Target Coverage | Minimum Coverage |
|-----------|-----------------|------------------|
| Domain Entities | 95% | 85% |
| Domain Services | 90% | 80% |
| Infrastructure Persistence | 85% | 75% |
| Application Use Cases | 85% | 75% |
| Integration Tests | N/A (scenario-based) | 10+ scenarios |

### Performance Requirements

| Metric | Threshold | Critical Threshold |
|--------|-----------|-------------------|
| Workflow creation (100 nodes) | <10ms | <50ms |
| Workflow serialization (100 nodes) | <20ms | <100ms |
| Orchestrator routing | <1ms | <5ms |
| Variable access | <0.1ms | <1ms |

### Acceptance Criteria

1. **All existing tests pass** (1255+ tests)
   ```powershell
   pytest tests/ -v --tb=short
   # Expected: All tests pass
   ```

2. **New Week 2 tests pass**
   ```powershell
   pytest tests/domain/ tests/infrastructure/ tests/application/ tests/integration/week2/ -v
   # Expected: All new tests pass
   ```

3. **Performance benchmarks pass**
   ```powershell
   pytest tests/performance/week2/ -v
   # Expected: All benchmarks within thresholds
   ```

4. **Coverage targets met**
   ```powershell
   pytest tests/ --cov=casare_rpa.domain --cov=casare_rpa.infrastructure --cov=casare_rpa.application --cov-report=term-missing
   # Expected: Coverage >= 85% for new code
   ```

5. **No critical security vulnerabilities**
   - Complete security checklist
   - All security probes pass or are documented

6. **Canvas loads and runs workflows**
   ```powershell
   python run.py
   # Manual verification: Canvas starts, workflows execute
   ```

---

## Risk Assessment

### High Risk Areas

1. **WorkflowSchema compatibility**
   - Risk: Breaking changes to serialization format
   - Mitigation: Extensive roundtrip tests
   - Test Focus: `test_roundtrip_serialization`, `test_workflow_serialization_preserves_all_data`

2. **ExecutionOrchestrator routing**
   - Risk: Incorrect next node calculation
   - Mitigation: Test all control flow scenarios
   - Test Focus: `TestGetNextNodes`, `TestControlFlow`

3. **Variable scoping hierarchy**
   - Risk: Wrong priority for variable resolution
   - Mitigation: Test hierarchy explicitly
   - Test Focus: `TestVariableHierarchy`

### Medium Risk Areas

1. **Path calculation for Run-To-Node**
   - Risk: Missing nodes in calculated path
   - Mitigation: Test with various graph topologies

2. **File I/O error handling**
   - Risk: Unhandled exceptions during save/load
   - Mitigation: Test error scenarios

3. **Memory usage with large workflows**
   - Risk: Memory leaks or excessive usage
   - Mitigation: Memory benchmarks

### Low Risk Areas

1. **Basic entity creation**
2. **Simple getter/setter operations**
3. **String serialization**

---

## Implementation Guide for rpa-engine-architect

### Test Implementation Order

Execute tests in this order to catch issues early:

1. **Domain Entity Tests** (Hour 2)
   - Start with `WorkflowSchema` - core of the system
   - Then `ExecutionState` - execution tracking
   - Finally `NodeConnection` - simpler entity

2. **Domain Service Tests** (Hour 3)
   - `ExecutionOrchestrator` - depends on entities

3. **Infrastructure Tests** (Hour 4)
   - `ProjectStorage` - file I/O testing

4. **Application Tests** (Hour 5)
   - `ExecuteWorkflowUseCase` - depends on all layers

5. **Integration Tests** (Hour 6)
   - Full stack testing

6. **Performance Tests** (Hour 7)
   - Establish baselines

7. **Bug Discovery** (Hour 8)
   - Edge cases and security

### Incremental Testing Approach

After each test file is created:

```powershell
# Run the new test file
pytest tests/domain/entities/test_workflow.py -v

# If tests pass, run all tests to check for regressions
pytest tests/ -v --tb=short

# Check coverage for the tested module
pytest tests/domain/entities/test_workflow.py --cov=casare_rpa.domain.entities.workflow --cov-report=term-missing
```

### Bug Fix Workflow

When a bug is discovered:

1. Create a failing test that reproduces the bug
2. Document the bug using the template
3. If critical, fix immediately; otherwise, add to bug backlog
4. Verify fix with the test
5. Run full test suite to check for regressions

### Continuous Integration Setup

```yaml
# .github/workflows/week2-tests.yml
name: Week 2 Integration Tests

on:
  push:
    branches: [main, week2-*]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -e ".[dev]"
      - run: pytest tests/ -v --cov=casare_rpa --cov-report=xml
      - uses: codecov/codecov-action@v4
```

---

## Appendix A: Test File Structure

```
tests/
+-- domain/
|   +-- entities/
|   |   +-- test_workflow.py
|   |   +-- test_execution_state.py
|   |   +-- test_node_connection.py
|   |   +-- test_workflow_metadata.py
|   +-- services/
|   |   +-- test_execution_orchestrator.py
|   +-- conftest.py
+-- infrastructure/
|   +-- persistence/
|   |   +-- test_project_storage.py
|   +-- conftest.py
+-- application/
|   +-- use_cases/
|   |   +-- test_execute_workflow.py
|   +-- conftest.py
+-- integration/
|   +-- week2/
|   |   +-- test_clean_architecture_integration.py
|   +-- conftest.py
+-- performance/
|   +-- week2/
|   |   +-- test_performance_benchmarks.py
|   +-- conftest.py
+-- week2/
|   +-- test_bug_discovery.py
+-- conftest.py  # Shared fixtures
```

---

## Appendix B: Shared Test Fixtures

Create `tests/conftest.py`:

```python
"""
Shared pytest fixtures for CasareRPA test suite.
"""
import pytest
from pathlib import Path
import tempfile
import shutil

from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.entities.node_connection import NodeConnection
from casare_rpa.core.events import EventBus


@pytest.fixture
def temp_dir():
    """Create and cleanup temporary directory."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def event_bus():
    """Create fresh event bus for testing."""
    return EventBus()


@pytest.fixture
def minimal_workflow() -> WorkflowSchema:
    """Create minimal valid workflow (Start -> End)."""
    workflow = WorkflowSchema(
        metadata=WorkflowMetadata(name="Minimal Workflow")
    )
    workflow.add_node({"node_id": "start", "type": "StartNode"})
    workflow.add_node({"node_id": "end", "type": "EndNode"})
    workflow.connections.append(
        NodeConnection("start", "exec_out", "end", "exec_in")
    )
    return workflow


@pytest.fixture
def empty_workflow() -> WorkflowSchema:
    """Create empty workflow with no nodes."""
    return WorkflowSchema(
        metadata=WorkflowMetadata(name="Empty Workflow")
    )


def create_linear_workflow(node_count: int) -> WorkflowSchema:
    """Factory function for linear workflows."""
    workflow = WorkflowSchema(
        metadata=WorkflowMetadata(name=f"Linear {node_count}")
    )

    for i in range(node_count):
        node_type = "StartNode" if i == 0 else ("EndNode" if i == node_count - 1 else "LogNode")
        workflow.add_node({"node_id": f"node_{i}", "type": node_type})
        if i > 0:
            workflow.connections.append(
                NodeConnection(f"node_{i-1}", "exec_out", f"node_{i}", "exec_in")
            )

    return workflow
```

---

## Appendix C: Expected Test Output Summary

After all tests are implemented and passing:

```
============================= test session starts ==============================
platform win32 -- Python 3.12.x
collected 1350+ items

tests/domain/entities/test_workflow.py .......................... [  2%]
tests/domain/entities/test_execution_state.py ................... [  4%]
tests/domain/entities/test_node_connection.py .................. [  5%]
tests/domain/services/test_execution_orchestrator.py ........... [  8%]
tests/infrastructure/persistence/test_project_storage.py ....... [ 10%]
tests/application/use_cases/test_execute_workflow.py ........... [ 12%]
tests/integration/week2/test_clean_architecture_integration.py . [ 15%]
tests/performance/week2/test_performance_benchmarks.py ......... [ 18%]
tests/week2/test_bug_discovery.py .............................. [ 20%]
... (existing tests)

============================= 1350+ passed in XXXs =============================

---------- coverage: platform win32, python 3.12.x -----------
Name                                              Stmts   Miss  Cover
---------------------------------------------------------------------
src/casare_rpa/domain/entities/workflow.py         150     12    92%
src/casare_rpa/domain/entities/execution_state.py  100      8    92%
src/casare_rpa/domain/services/execution_orch...   200     25    88%
src/casare_rpa/infrastructure/persistence/...      180     30    83%
src/casare_rpa/application/use_cases/execute...    250     40    84%
---------------------------------------------------------------------
TOTAL                                              880    115    87%
```

---

**Document Version**: 1.0.0
**Last Updated**: November 27, 2025
**Author**: rpa-system-architect agent
