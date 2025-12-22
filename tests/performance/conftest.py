"""
Fixtures for performance tests.

Provides:
- Workflow data fixtures (small, medium, large)
- Mock execution context
- Test node classes
"""

import json
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from casare_rpa.domain.value_objects.types import ExecutionMode
from casare_rpa.infrastructure.execution import ExecutionContext


@pytest.fixture
def execution_context() -> ExecutionContext:
    """Create a test execution context."""
    return ExecutionContext(
        workflow_name="TestWorkflow",
        mode=ExecutionMode.NORMAL,
        initial_variables={},
    )


@pytest.fixture
def mock_context() -> MagicMock:
    """Create a mock execution context."""
    context = MagicMock(spec=ExecutionContext)
    context.resolve_value = MagicMock(side_effect=lambda x: x)
    context.variables = {}
    context.resources = {}
    return context


def _create_node_data(node_id: str, node_type: str, config: Dict = None) -> Dict:
    """Create a node data dictionary."""
    return {
        "node_type": node_type,
        "config": config or {},
        "position": {"x": 100, "y": 100},
    }


def _create_connection_data(
    source_node: str,
    source_port: str,
    target_node: str,
    target_port: str,
) -> Dict:
    """Create a connection data dictionary."""
    return {
        "source_node": source_node,
        "source_port": source_port,
        "target_node": target_node,
        "target_port": target_port,
    }


def _generate_workflow_data(
    node_count: int,
    name: str = "TestWorkflow",
) -> Dict[str, Any]:
    """
    Generate workflow data with specified number of nodes.

    Creates a linear chain of nodes connected via exec ports.
    Uses simple node types that exist in the registry.
    """
    nodes = {}
    connections = []
    variables = {"test_var": "value", "counter": 0}

    # Use node types that are likely to exist in the registry
    # StartNode is always available
    node_types = [
        "StartNode",  # Always first
        "SetVariableNode",
        "LogNode",
        "CommentNode",
    ]

    # Create nodes
    for i in range(node_count):
        node_id = f"node_{i:04d}"
        # Cycle through available node types (skip StartNode for nodes after first)
        if i == 0:
            node_type = "StartNode"
            config = {}
        else:
            node_type = node_types[(i % (len(node_types) - 1)) + 1]
            if node_type == "SetVariableNode":
                config = {"variable_name": f"var_{i}", "value": f"value_{i}"}
            elif node_type == "LogNode":
                config = {"message": f"Log message {i}"}
            else:
                config = {"comment": f"Node {i}"}

        nodes[node_id] = _create_node_data(node_id, node_type, config)

    # Create linear connections (exec flow)
    for i in range(node_count - 1):
        source_id = f"node_{i:04d}"
        target_id = f"node_{i + 1:04d}"
        connections.append(_create_connection_data(source_id, "exec_out", target_id, "exec_in"))

    return {
        "metadata": {
            "name": name,
            "description": f"Test workflow with {node_count} nodes",
            "version": "1.0.0",
            "author": "Test Suite",
            "created_at": "2024-01-01T00:00:00Z",
            "modified_at": "2024-01-01T00:00:00Z",
        },
        "nodes": nodes,
        "connections": connections,
        "variables": variables,
        "settings": {"auto_save": True, "debug_mode": False},
        "frames": [],
    }


@pytest.fixture
def small_workflow_data() -> Dict[str, Any]:
    """Create a small workflow with 10 nodes."""
    return _generate_workflow_data(10, "SmallWorkflow")


@pytest.fixture
def medium_workflow_data() -> Dict[str, Any]:
    """Create a medium workflow with 50 nodes."""
    return _generate_workflow_data(50, "MediumWorkflow")


@pytest.fixture
def large_workflow_data() -> Dict[str, Any]:
    """Create a large workflow with 200 nodes."""
    return _generate_workflow_data(200, "LargeWorkflow")


@pytest.fixture
def minimal_workflow_data() -> Dict[str, Any]:
    """Create minimal valid workflow data."""
    return {
        "metadata": {
            "name": "MinimalWorkflow",
            "description": "Minimal test workflow",
            "version": "1.0.0",
        },
        "nodes": {
            "start": {
                "node_type": "StartNode",
                "config": {},
            },
        },
        "connections": [],
        "variables": {},
        "settings": {},
    }


@pytest.fixture
def workflow_with_aliases() -> Dict[str, Any]:
    """Create workflow with deprecated node type aliases."""
    return {
        "metadata": {
            "name": "AliasWorkflow",
            "description": "Workflow with deprecated node types",
            "version": "1.0.0",
        },
        "nodes": {
            "start": {
                "node_type": "StartNode",
                "config": {},
            },
            "read_file": {
                "node_type": "ReadFileNode",  # Alias for FileSystemSuperNode
                "config": {"file_path": "test.txt"},
            },
            "write_file": {
                "node_type": "WriteFileNode",  # Alias for FileSystemSuperNode
                "config": {"file_path": "output.txt", "content": "data"},
            },
        },
        "connections": [
            {
                "source_node": "start",
                "source_port": "exec_out",
                "target_node": "read_file",
                "target_port": "exec_in",
            },
            {
                "source_node": "read_file",
                "source_port": "exec_out",
                "target_node": "write_file",
                "target_port": "exec_in",
            },
        ],
        "variables": {},
        "settings": {},
    }


@pytest.fixture
def temp_workflow_file(tmp_path: Path, small_workflow_data: Dict) -> Path:
    """Create a temporary workflow JSON file."""
    workflow_file = tmp_path / "test_workflow.json"
    workflow_file.write_text(json.dumps(small_workflow_data, indent=2))
    return workflow_file


@pytest.fixture
def temp_workflow_directory(tmp_path: Path) -> Path:
    """Create a directory with multiple workflow files."""
    workflows_dir = tmp_path / "workflows"
    workflows_dir.mkdir()

    # Create multiple workflow files
    for i in range(5):
        workflow_data = _generate_workflow_data(5 + i * 2, f"Workflow_{i}")
        workflow_file = workflows_dir / f"workflow_{i}.json"
        workflow_file.write_text(json.dumps(workflow_data, indent=2))

    return workflows_dir
