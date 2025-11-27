"""
Tests for WorkflowSchema domain entity.
Covers workflow creation, validation, node/connection management, serialization.
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from casare_rpa.domain.entities.workflow import (
    WorkflowSchema,
    VariableDefinition,
)
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.entities.node_connection import NodeConnection


# ============================================================================
# VariableDefinition Tests
# ============================================================================


class TestVariableDefinition:
    """Tests for VariableDefinition dataclass."""

    def test_create_default_variable(self) -> None:
        """Create variable with default values."""
        var = VariableDefinition(name="test_var")
        assert var.name == "test_var"
        assert var.type == "String"
        assert var.default_value == ""
        assert var.description == ""

    def test_create_typed_variable(self) -> None:
        """Create variable with specific type."""
        var = VariableDefinition(
            name="count",
            type="Integer",
            default_value=42,
            description="Counter variable",
        )
        assert var.name == "count"
        assert var.type == "Integer"
        assert var.default_value == 42
        assert var.description == "Counter variable"

    def test_variable_to_dict(self) -> None:
        """Serialize variable to dictionary."""
        var = VariableDefinition(
            name="enabled",
            type="Boolean",
            default_value=True,
            description="Feature flag",
        )
        data = var.to_dict()
        assert data["name"] == "enabled"
        assert data["type"] == "Boolean"
        assert data["default_value"] is True
        assert data["description"] == "Feature flag"

    def test_variable_from_dict(self) -> None:
        """Deserialize variable from dictionary."""
        data = {
            "name": "items",
            "type": "List",
            "default_value": [1, 2, 3],
            "description": "Item list",
        }
        var = VariableDefinition.from_dict(data)
        assert var.name == "items"
        assert var.type == "List"
        assert var.default_value == [1, 2, 3]

    def test_variable_from_dict_defaults(self) -> None:
        """Deserialize variable with missing fields uses defaults."""
        var = VariableDefinition.from_dict({"name": "x"})
        assert var.name == "x"
        assert var.type == "String"
        assert var.default_value == ""


# ============================================================================
# WorkflowSchema Creation Tests
# ============================================================================


class TestWorkflowSchemaCreation:
    """Tests for WorkflowSchema initialization."""

    def test_create_default_workflow(self) -> None:
        """Create workflow with default metadata."""
        workflow = WorkflowSchema()
        assert workflow.metadata.name == "Untitled Workflow"
        assert len(workflow.nodes) == 0
        assert len(workflow.connections) == 0
        assert len(workflow.frames) == 0
        assert workflow.settings["stop_on_error"] is True

    def test_create_workflow_with_metadata(self) -> None:
        """Create workflow with custom metadata."""
        metadata = WorkflowMetadata(
            name="Login Flow",
            description="Automates login process",
            author="Test Author",
            version="2.0.0",
        )
        workflow = WorkflowSchema(metadata)
        assert workflow.metadata.name == "Login Flow"
        assert workflow.metadata.description == "Automates login process"
        assert workflow.metadata.author == "Test Author"
        assert workflow.metadata.version == "2.0.0"

    def test_workflow_default_settings(self) -> None:
        """Workflow has expected default settings."""
        workflow = WorkflowSchema()
        assert workflow.settings["stop_on_error"] is True
        assert workflow.settings["timeout"] == 30
        assert workflow.settings["retry_count"] == 0


# ============================================================================
# Node Management Tests
# ============================================================================


class TestWorkflowNodeManagement:
    """Tests for node add/remove/get operations."""

    def test_add_node(self) -> None:
        """Add a node to workflow."""
        workflow = WorkflowSchema()
        node_data = {
            "node_id": "node_001",
            "type": "StartNode",
            "position": [100, 100],
        }
        workflow.add_node(node_data)
        assert "node_001" in workflow.nodes
        assert workflow.nodes["node_001"]["type"] == "StartNode"

    def test_add_multiple_nodes(self) -> None:
        """Add multiple nodes to workflow."""
        workflow = WorkflowSchema()
        for i in range(5):
            workflow.add_node({"node_id": f"node_{i}", "type": "GenericNode"})
        assert len(workflow.nodes) == 5

    def test_get_node_exists(self) -> None:
        """Get existing node by ID."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "test_node", "type": "TestNode"})
        node = workflow.get_node("test_node")
        assert node is not None
        assert node["type"] == "TestNode"

    def test_get_node_not_exists(self) -> None:
        """Get non-existing node returns None."""
        workflow = WorkflowSchema()
        node = workflow.get_node("nonexistent")
        assert node is None

    def test_remove_node(self) -> None:
        """Remove node from workflow."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "to_remove", "type": "TestNode"})
        assert "to_remove" in workflow.nodes
        workflow.remove_node("to_remove")
        assert "to_remove" not in workflow.nodes

    def test_remove_node_removes_connections(self) -> None:
        """Removing node also removes its connections."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "node_a", "type": "NodeA"})
        workflow.add_node({"node_id": "node_b", "type": "NodeB"})
        conn = NodeConnection("node_a", "exec_out", "node_b", "exec_in")
        workflow.connections.append(conn)

        workflow.remove_node("node_a")
        assert len(workflow.connections) == 0

    def test_remove_nonexistent_node_silent(self) -> None:
        """Removing non-existent node does nothing."""
        workflow = WorkflowSchema()
        workflow.remove_node("ghost_node")  # Should not raise


# ============================================================================
# Connection Management Tests
# ============================================================================


class TestWorkflowConnectionManagement:
    """Tests for connection add/remove/query operations."""

    def test_add_connection_valid(self) -> None:
        """Add valid connection between existing nodes."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "src", "type": "SourceNode"})
        workflow.add_node({"node_id": "dst", "type": "DestNode"})

        conn = NodeConnection("src", "output", "dst", "input")
        workflow.add_connection(conn)
        assert len(workflow.connections) == 1

    def test_add_connection_invalid_source(self) -> None:
        """Adding connection with non-existent source raises error."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "dst", "type": "DestNode"})

        conn = NodeConnection("missing_src", "output", "dst", "input")
        with pytest.raises(ValueError, match="Source node missing_src not found"):
            workflow.add_connection(conn)

    def test_add_connection_invalid_target(self) -> None:
        """Adding connection with non-existent target raises error."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "src", "type": "SourceNode"})

        conn = NodeConnection("src", "output", "missing_dst", "input")
        with pytest.raises(ValueError, match="Target node missing_dst not found"):
            workflow.add_connection(conn)

    def test_remove_connection(self) -> None:
        """Remove a specific connection."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "n1", "type": "Node1"})
        workflow.add_node({"node_id": "n2", "type": "Node2"})
        conn = NodeConnection("n1", "out", "n2", "in")
        workflow.connections.append(conn)

        workflow.remove_connection("n1", "out", "n2", "in")
        assert len(workflow.connections) == 0

    def test_remove_connection_partial_match_stays(self) -> None:
        """Connections with partial match are not removed."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "n1", "type": "Node1"})
        workflow.add_node({"node_id": "n2", "type": "Node2"})
        conn = NodeConnection("n1", "out", "n2", "in")
        workflow.connections.append(conn)

        workflow.remove_connection("n1", "out", "n2", "wrong_port")
        assert len(workflow.connections) == 1

    def test_get_connections_from_node(self) -> None:
        """Get all connections originating from a node."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "src", "type": "Source"})
        workflow.add_node({"node_id": "dst1", "type": "Dest1"})
        workflow.add_node({"node_id": "dst2", "type": "Dest2"})
        workflow.connections.append(NodeConnection("src", "out1", "dst1", "in"))
        workflow.connections.append(NodeConnection("src", "out2", "dst2", "in"))

        conns = workflow.get_connections_from("src")
        assert len(conns) == 2

    def test_get_connections_to_node(self) -> None:
        """Get all connections targeting a node."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "src1", "type": "Source1"})
        workflow.add_node({"node_id": "src2", "type": "Source2"})
        workflow.add_node({"node_id": "dst", "type": "Dest"})
        workflow.connections.append(NodeConnection("src1", "out", "dst", "in1"))
        workflow.connections.append(NodeConnection("src2", "out", "dst", "in2"))

        conns = workflow.get_connections_to("dst")
        assert len(conns) == 2


# ============================================================================
# Type Inference Tests
# ============================================================================


class TestWorkflowTypeInference:
    """Tests for _infer_type method."""

    def test_infer_boolean_type(self) -> None:
        """Boolean values inferred correctly."""
        workflow = WorkflowSchema()
        assert workflow._infer_type(True) == "Boolean"
        assert workflow._infer_type(False) == "Boolean"

    def test_infer_integer_type(self) -> None:
        """Integer values inferred correctly."""
        workflow = WorkflowSchema()
        assert workflow._infer_type(42) == "Integer"
        assert workflow._infer_type(-10) == "Integer"

    def test_infer_float_type(self) -> None:
        """Float values inferred correctly."""
        workflow = WorkflowSchema()
        assert workflow._infer_type(3.14) == "Float"

    def test_infer_list_type(self) -> None:
        """List values inferred correctly."""
        workflow = WorkflowSchema()
        assert workflow._infer_type([1, 2, 3]) == "List"

    def test_infer_dict_type(self) -> None:
        """Dict values inferred correctly."""
        workflow = WorkflowSchema()
        assert workflow._infer_type({"key": "value"}) == "Dict"

    def test_infer_string_default(self) -> None:
        """Unknown types default to String."""
        workflow = WorkflowSchema()
        assert workflow._infer_type("hello") == "String"
        assert workflow._infer_type(None) == "String"


# ============================================================================
# Serialization Tests
# ============================================================================


class TestWorkflowSerialization:
    """Tests for to_dict/from_dict serialization."""

    def test_to_dict_empty_workflow(self) -> None:
        """Serialize empty workflow."""
        workflow = WorkflowSchema()
        data = workflow.to_dict()
        assert "metadata" in data
        assert "nodes" in data
        assert "connections" in data
        assert "frames" in data
        assert "variables" in data
        assert "settings" in data
        assert len(data["nodes"]) == 0

    def test_to_dict_with_nodes(self) -> None:
        """Serialize workflow with nodes."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "n1", "type": "TestNode"})
        data = workflow.to_dict()
        assert "n1" in data["nodes"]

    def test_to_dict_with_connections(self) -> None:
        """Serialize workflow with connections."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "a", "type": "A"})
        workflow.add_node({"node_id": "b", "type": "B"})
        workflow.connections.append(NodeConnection("a", "out", "b", "in"))
        data = workflow.to_dict()
        assert len(data["connections"]) == 1

    def test_to_dict_with_variables(self) -> None:
        """Serialize workflow with variables."""
        workflow = WorkflowSchema()
        workflow.variables["counter"] = VariableDefinition(
            name="counter", type="Integer", default_value=0
        )
        data = workflow.to_dict()
        assert "counter" in data["variables"]

    def test_to_dict_plain_value_variables(self) -> None:
        """Serialize workflow with plain value variables."""
        workflow = WorkflowSchema()
        workflow.variables["name"] = "John"
        data = workflow.to_dict()
        assert data["variables"]["name"]["type"] == "String"

    def test_from_dict_basic(self) -> None:
        """Deserialize workflow from dict."""
        data = {
            "metadata": {"name": "Test Flow"},
            "nodes": {"n1": {"node_id": "n1", "type": "Node"}},
            "connections": [],
            "frames": [],
            "variables": {},
            "settings": {"timeout": 60},
        }
        workflow = WorkflowSchema.from_dict(data)
        assert workflow.metadata.name == "Test Flow"
        assert "n1" in workflow.nodes
        assert workflow.settings["timeout"] == 60

    def test_from_dict_with_connections(self) -> None:
        """Deserialize workflow with connections."""
        data = {
            "metadata": {"name": "Connected"},
            "nodes": {
                "a": {"node_id": "a", "type": "A"},
                "b": {"node_id": "b", "type": "B"},
            },
            "connections": [
                {
                    "source_node": "a",
                    "source_port": "o",
                    "target_node": "b",
                    "target_port": "i",
                }
            ],
            "frames": [],
            "variables": {},
            "settings": {},
        }
        workflow = WorkflowSchema.from_dict(data)
        assert len(workflow.connections) == 1

    def test_from_dict_auto_repair_node_id_mismatch(self) -> None:
        """Auto-repair node_id mismatch during deserialization."""
        data = {
            "metadata": {},
            "nodes": {
                "dict_key": {"node_id": "different_id", "type": "Node"},
            },
            "connections": [],
        }
        workflow = WorkflowSchema.from_dict(data)
        # dict_key should be authoritative
        assert "dict_key" in workflow.nodes
        assert workflow.nodes["dict_key"]["node_id"] == "dict_key"

    def test_roundtrip_serialization(self) -> None:
        """Serialize then deserialize preserves data."""
        original = WorkflowSchema(WorkflowMetadata(name="Roundtrip Test"))
        original.add_node({"node_id": "n1", "type": "TestNode"})
        original.add_node({"node_id": "n2", "type": "TestNode"})
        original.connections.append(NodeConnection("n1", "out", "n2", "in"))
        original.variables["x"] = VariableDefinition(name="x", default_value=42)

        data = original.to_dict()
        restored = WorkflowSchema.from_dict(data)

        assert restored.metadata.name == "Roundtrip Test"
        assert len(restored.nodes) == 2
        assert len(restored.connections) == 1
        assert "x" in restored.variables


# ============================================================================
# String Representation Tests
# ============================================================================


class TestWorkflowRepr:
    """Tests for __repr__ method."""

    def test_repr_empty(self) -> None:
        """String representation of empty workflow."""
        workflow = WorkflowSchema()
        rep = repr(workflow)
        assert "Untitled Workflow" in rep
        assert "nodes=0" in rep
        assert "connections=0" in rep

    def test_repr_with_content(self) -> None:
        """String representation with nodes and connections."""
        workflow = WorkflowSchema(WorkflowMetadata(name="My Flow"))
        workflow.add_node({"node_id": "n", "type": "N"})
        rep = repr(workflow)
        assert "My Flow" in rep
        assert "nodes=1" in rep
