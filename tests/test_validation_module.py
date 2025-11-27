"""
Integration tests for workflow validation module.

Tests cover:
- Schema validation
- Node validation
- Connection validation
- Workflow semantics
- Circular dependency detection
- Reachability analysis
- Error and warning categorization
"""

import pytest
from typing import Dict, Any, List

from casare_rpa.core.validation import (
    validate_workflow,
    validate_node,
    validate_connections,
    ValidationResult,
    ValidationSeverity,
    ValidationIssue,
    get_valid_node_types,
    quick_validate,
    _has_circular_dependency,
    _find_entry_points_and_reachable,
    _parse_connection,
    _is_exec_port,
    _is_exec_input_port,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def valid_workflow() -> Dict[str, Any]:
    """A valid minimal workflow."""
    return {
        "metadata": {
            "name": "Test Workflow",
            "schema_version": "1.0",
        },
        "nodes": {
            "node1": {
                "node_id": "node1",
                "node_type": "StartNode",
                "position": [0, 0],
                "config": {},
            },
            "node2": {
                "node_id": "node2",
                "node_type": "EndNode",
                "position": [100, 0],
                "config": {},
            },
        },
        "connections": [
            {
                "source_node": "node1",
                "source_port": "exec_out",
                "target_node": "node2",
                "target_port": "exec_in",
            }
        ],
    }


@pytest.fixture
def empty_workflow() -> Dict[str, Any]:
    """An empty workflow with no nodes."""
    return {
        "metadata": {"name": "Empty", "schema_version": "1.0"},
        "nodes": {},
        "connections": [],
    }


@pytest.fixture
def workflow_with_circular_dependency() -> Dict[str, Any]:
    """Workflow with circular execution flow."""
    return {
        "metadata": {"name": "Circular", "schema_version": "1.0"},
        "nodes": {
            "node1": {"node_id": "node1", "node_type": "StartNode"},
            "node2": {"node_id": "node2", "node_type": "IfNode"},
            "node3": {"node_id": "node3", "node_type": "LogNode"},
        },
        "connections": [
            {
                "source_node": "node1",
                "source_port": "exec_out",
                "target_node": "node2",
                "target_port": "exec_in",
            },
            {
                "source_node": "node2",
                "source_port": "true",
                "target_node": "node3",
                "target_port": "exec_in",
            },
            {
                "source_node": "node3",
                "source_port": "exec_out",
                "target_node": "node1",
                "target_port": "exec_in",
            },
        ],
    }


@pytest.fixture
def workflow_with_unreachable_nodes() -> Dict[str, Any]:
    """Workflow with some unreachable nodes."""
    return {
        "metadata": {"name": "Unreachable", "schema_version": "1.0"},
        "nodes": {
            "node1": {"node_id": "node1", "node_type": "StartNode"},
            "node2": {"node_id": "node2", "node_type": "EndNode"},
            "node3": {"node_id": "node3", "node_type": "LogNode"},  # Unreachable
        },
        "connections": [
            {
                "source_node": "node1",
                "source_port": "exec_out",
                "target_node": "node2",
                "target_port": "exec_in",
            }
        ],
    }


# ============================================================================
# Basic Structure Tests
# ============================================================================


class TestWorkflowStructure:
    """Test top-level workflow structure validation."""

    def test_valid_workflow(self, valid_workflow) -> None:
        """Test that a valid workflow passes validation."""
        result = validate_workflow(valid_workflow)
        assert result.is_valid is True
        assert result.error_count == 0

    def test_invalid_type_not_dict(self) -> None:
        """Test that non-dict workflow data fails."""
        result = validate_workflow([])  # List instead of dict
        assert result.is_valid is False
        assert any(issue.code == "INVALID_TYPE" for issue in result.errors)

    def test_missing_nodes_key(self) -> None:
        """Test that missing 'nodes' key fails."""
        data = {"metadata": {}, "connections": []}
        result = validate_workflow(data)
        assert result.is_valid is False
        assert any(issue.code == "MISSING_REQUIRED_KEY" for issue in result.errors)

    def test_nodes_not_dict(self) -> None:
        """Test that non-dict 'nodes' value fails."""
        data = {"nodes": [], "connections": []}
        result = validate_workflow(data)
        assert result.is_valid is False
        assert any(
            issue.code == "INVALID_TYPE" and "nodes" in issue.message
            for issue in result.errors
        )

    def test_connections_not_list(self) -> None:
        """Test that non-list 'connections' value fails."""
        data = {"nodes": {}, "connections": {}}
        result = validate_workflow(data)
        assert result.is_valid is False
        assert any(
            issue.code == "INVALID_TYPE" and "connections" in issue.message
            for issue in result.errors
        )

    def test_metadata_not_dict(self) -> None:
        """Test that non-dict 'metadata' value fails."""
        data = {"nodes": {}, "connections": [], "metadata": "invalid"}
        result = validate_workflow(data)
        assert result.is_valid is False
        assert any(
            issue.code == "INVALID_TYPE" and "metadata" in issue.message
            for issue in result.errors
        )


# ============================================================================
# Metadata Tests
# ============================================================================


class TestMetadataValidation:
    """Test workflow metadata validation."""

    def test_schema_version_mismatch_warning(self) -> None:
        """Test that mismatched schema version generates warning."""
        data = {
            "metadata": {"schema_version": "99.9"},
            "nodes": {"n1": {"node_id": "n1", "node_type": "StartNode"}},
        }
        result = validate_workflow(data)
        # Should pass but with warning
        assert any(issue.code == "SCHEMA_VERSION_MISMATCH" for issue in result.warnings)

    def test_missing_name_warning(self) -> None:
        """Test that missing workflow name generates warning."""
        data = {
            "metadata": {},
            "nodes": {"n1": {"node_id": "n1", "node_type": "StartNode"}},
        }
        result = validate_workflow(data)
        assert any(issue.code == "MISSING_NAME" for issue in result.warnings)

    def test_name_too_long_warning(self) -> None:
        """Test that excessively long workflow name generates warning."""
        long_name = "A" * 101
        data = {
            "metadata": {"name": long_name},
            "nodes": {"n1": {"node_id": "n1", "node_type": "StartNode"}},
        }
        result = validate_workflow(data)
        assert any(issue.code == "NAME_TOO_LONG" for issue in result.warnings)


# ============================================================================
# Node Validation Tests
# ============================================================================


class TestNodeValidation:
    """Test individual node validation."""

    def test_valid_node(self) -> None:
        """Test that a valid node passes validation."""
        node_data = {
            "node_id": "test1",
            "node_type": "StartNode",
            "position": [0, 0],
            "config": {},
        }
        result = validate_node("test1", node_data)
        assert result.is_valid is True
        assert result.error_count == 0

    def test_missing_required_fields(self) -> None:
        """Test that missing required fields fail."""
        node_data = {"position": [0, 0]}  # Missing node_id and node_type
        result = validate_node("test1", node_data)
        assert result.is_valid is False
        assert any(issue.code == "MISSING_REQUIRED_FIELD" for issue in result.errors)

    def test_node_id_mismatch(self) -> None:
        """Test that mismatched node_id fails."""
        node_data = {
            "node_id": "wrong_id",
            "node_type": "StartNode",
        }
        result = validate_node("test1", node_data)
        assert result.is_valid is False
        assert any(issue.code == "NODE_ID_MISMATCH" for issue in result.errors)

    def test_unknown_node_type(self) -> None:
        """Test that unknown node type fails."""
        node_data = {
            "node_id": "test1",
            "node_type": "NonExistentNode",
        }
        result = validate_node("test1", node_data)
        assert result.is_valid is False
        assert any(issue.code == "UNKNOWN_NODE_TYPE" for issue in result.errors)

    def test_invalid_position_format(self) -> None:
        """Test that invalid position format generates warning."""
        # Not a list/tuple
        node_data = {
            "node_id": "test1",
            "node_type": "StartNode",
            "position": "0,0",
        }
        result = validate_node("test1", node_data)
        assert any(issue.code == "INVALID_POSITION" for issue in result.warnings)

        # Wrong length
        node_data["position"] = [0, 0, 0]
        result = validate_node("test1", node_data)
        assert any(issue.code == "INVALID_POSITION" for issue in result.warnings)

        # Non-numeric values
        node_data["position"] = ["x", "y"]
        result = validate_node("test1", node_data)
        assert any(issue.code == "INVALID_POSITION" for issue in result.warnings)

    def test_invalid_config_type(self) -> None:
        """Test that non-dict config fails."""
        node_data = {
            "node_id": "test1",
            "node_type": "StartNode",
            "config": "invalid",
        }
        result = validate_node("test1", node_data)
        assert result.is_valid is False
        assert any(issue.code == "INVALID_CONFIG" for issue in result.errors)


# ============================================================================
# Connection Validation Tests
# ============================================================================


class TestConnectionValidation:
    """Test connection validation."""

    def test_valid_connection(self) -> None:
        """Test that a valid connection passes validation."""
        connections = [
            {
                "source_node": "n1",
                "source_port": "exec_out",
                "target_node": "n2",
                "target_port": "exec_in",
            }
        ]
        node_ids = {"n1", "n2"}
        result = validate_connections(connections, node_ids)
        assert result.is_valid is True
        assert result.error_count == 0

    def test_missing_connection_fields(self) -> None:
        """Test that missing required connection fields fail."""
        connections = [{"source_node": "n1"}]  # Missing other fields
        node_ids = {"n1", "n2"}
        result = validate_connections(connections, node_ids)
        assert result.is_valid is False
        assert any(issue.code == "MISSING_REQUIRED_FIELD" for issue in result.errors)

    def test_orphaned_source_connection(self) -> None:
        """Test that connection to non-existent source node fails."""
        connections = [
            {
                "source_node": "nonexistent",
                "source_port": "exec_out",
                "target_node": "n2",
                "target_port": "exec_in",
            }
        ]
        node_ids = {"n2"}
        result = validate_connections(connections, node_ids)
        assert result.is_valid is False
        assert any(issue.code == "ORPHANED_CONNECTION" for issue in result.errors)

    def test_orphaned_target_connection(self) -> None:
        """Test that connection to non-existent target node fails."""
        connections = [
            {
                "source_node": "n1",
                "source_port": "exec_out",
                "target_node": "nonexistent",
                "target_port": "exec_in",
            }
        ]
        node_ids = {"n1"}
        result = validate_connections(connections, node_ids)
        assert result.is_valid is False
        assert any(issue.code == "ORPHANED_CONNECTION" for issue in result.errors)

    def test_self_connection(self) -> None:
        """Test that self-connection fails."""
        connections = [
            {
                "source_node": "n1",
                "source_port": "exec_out",
                "target_node": "n1",
                "target_port": "exec_in",
            }
        ]
        node_ids = {"n1"}
        result = validate_connections(connections, node_ids)
        assert result.is_valid is False
        assert any(issue.code == "SELF_CONNECTION" for issue in result.errors)

    def test_duplicate_connection_warning(self) -> None:
        """Test that duplicate connections generate warning."""
        connections = [
            {
                "source_node": "n1",
                "source_port": "exec_out",
                "target_node": "n2",
                "target_port": "exec_in",
            },
            {
                "source_node": "n1",
                "source_port": "exec_out",
                "target_node": "n2",
                "target_port": "exec_in",
            },
        ]
        node_ids = {"n1", "n2"}
        result = validate_connections(connections, node_ids)
        assert any(issue.code == "DUPLICATE_CONNECTION" for issue in result.warnings)


# ============================================================================
# Semantic Validation Tests
# ============================================================================


class TestSemanticValidation:
    """Test workflow semantic validation."""

    def test_empty_workflow_error(self, empty_workflow) -> None:
        """Test that empty workflow fails."""
        result = validate_workflow(empty_workflow)
        assert result.is_valid is False
        assert any(issue.code == "EMPTY_WORKFLOW" for issue in result.errors)

    def test_circular_dependency_detection(
        self, workflow_with_circular_dependency
    ) -> None:
        """Test that circular dependencies are detected."""
        result = validate_workflow(workflow_with_circular_dependency)
        assert result.is_valid is False
        assert any(issue.code == "CIRCULAR_DEPENDENCY" for issue in result.errors)

    def test_unreachable_nodes_warning(self, workflow_with_unreachable_nodes) -> None:
        """Test that unreachable nodes generate warning."""
        result = validate_workflow(workflow_with_unreachable_nodes)
        # Workflow is valid but has warnings
        assert any(issue.code == "UNREACHABLE_NODES" for issue in result.warnings)

    def test_no_entry_point_warning(self) -> None:
        """Test that workflows with no clear entry point generate warning."""
        # All nodes have incoming exec connections (circular)
        data = {
            "metadata": {"name": "No Entry"},
            "nodes": {
                "n1": {"node_id": "n1", "node_type": "LogNode"},
                "n2": {"node_id": "n2", "node_type": "LogNode"},
            },
            "connections": [
                {
                    "source_node": "n1",
                    "source_port": "exec_out",
                    "target_node": "n2",
                    "target_port": "exec_in",
                },
                {
                    "source_node": "n2",
                    "source_port": "exec_out",
                    "target_node": "n1",
                    "target_port": "exec_in",
                },
            ],
        }
        result = validate_workflow(data)
        # Should have circular dependency error and possibly no entry point warning
        assert result.is_valid is False


# ============================================================================
# Helper Function Tests
# ============================================================================


class TestHelperFunctions:
    """Test internal helper functions."""

    def test_parse_connection_format1(self) -> None:
        """Test parsing standard connection format."""
        conn = {
            "source_node": "n1",
            "source_port": "out",
            "target_node": "n2",
            "target_port": "in",
        }
        parsed = _parse_connection(conn)
        assert parsed is not None
        assert parsed["source_node"] == "n1"
        assert parsed["target_node"] == "n2"

    def test_parse_connection_format2(self) -> None:
        """Test parsing alternative connection format."""
        conn = {"out": ["n1", "output"], "in": ["n2", "input"]}
        parsed = _parse_connection(conn)
        assert parsed is not None
        assert parsed["source_node"] == "n1"
        assert parsed["source_port"] == "output"
        assert parsed["target_node"] == "n2"
        assert parsed["target_port"] == "input"

    def test_parse_connection_invalid(self) -> None:
        """Test parsing invalid connection format."""
        conn = {"invalid": "format"}
        parsed = _parse_connection(conn)
        assert parsed is None

    def test_is_exec_port_detection(self) -> None:
        """Test execution port name detection."""
        assert _is_exec_port("exec_in") is True
        assert _is_exec_port("exec_out") is True
        assert _is_exec_port("true") is True
        assert _is_exec_port("false") is True
        assert _is_exec_port("loop_body") is True
        assert _is_exec_port("data_out") is False
        assert _is_exec_port("value") is False
        assert _is_exec_port("") is False

    def test_is_exec_input_port_detection(self) -> None:
        """Test execution input port detection."""
        assert _is_exec_input_port("exec_in") is True
        assert _is_exec_input_port("true") is True
        assert _is_exec_input_port("loop_body") is True
        assert _is_exec_input_port("exec_out") is False
        assert _is_exec_input_port("data_in") is False
        assert _is_exec_input_port("") is False

    def test_has_circular_dependency_true(self) -> None:
        """Test circular dependency detection returns True for cycles."""
        nodes = {
            "n1": {"node_id": "n1", "node_type": "StartNode"},
            "n2": {"node_id": "n2", "node_type": "LogNode"},
        }
        connections = [
            {
                "source_node": "n1",
                "source_port": "exec_out",
                "target_node": "n2",
                "target_port": "exec_in",
            },
            {
                "source_node": "n2",
                "source_port": "exec_out",
                "target_node": "n1",
                "target_port": "exec_in",
            },
        ]
        assert _has_circular_dependency(nodes, connections) is True

    def test_has_circular_dependency_false(self) -> None:
        """Test circular dependency detection returns False for acyclic graphs."""
        nodes = {
            "n1": {"node_id": "n1", "node_type": "StartNode"},
            "n2": {"node_id": "n2", "node_type": "EndNode"},
        }
        connections = [
            {
                "source_node": "n1",
                "source_port": "exec_out",
                "target_node": "n2",
                "target_port": "exec_in",
            }
        ]
        assert _has_circular_dependency(nodes, connections) is False

    def test_find_entry_points_single_start(self) -> None:
        """Test finding entry points with single start node."""
        nodes = {
            "n1": {"node_id": "n1", "node_type": "StartNode"},
            "n2": {"node_id": "n2", "node_type": "EndNode"},
        }
        connections = [
            {
                "source_node": "n1",
                "source_port": "exec_out",
                "target_node": "n2",
                "target_port": "exec_in",
            }
        ]
        entry_points, reachable = _find_entry_points_and_reachable(nodes, connections)
        assert "n1" in entry_points
        assert "n2" not in entry_points  # Has incoming exec
        assert reachable == {"n1", "n2"}

    def test_find_entry_points_multiple(self) -> None:
        """Test finding multiple entry points."""
        nodes = {
            "n1": {"node_id": "n1", "node_type": "StartNode"},
            "n2": {"node_id": "n2", "node_type": "StartNode"},
            "n3": {"node_id": "n3", "node_type": "EndNode"},
        }
        connections = []
        entry_points, reachable = _find_entry_points_and_reachable(nodes, connections)
        assert len(entry_points) == 3  # All nodes are entry points (no incoming exec)


# ============================================================================
# ValidationResult Tests
# ============================================================================


class TestValidationResult:
    """Test ValidationResult class functionality."""

    def test_empty_result(self) -> None:
        """Test empty validation result."""
        result = ValidationResult()
        assert result.is_valid is True
        assert result.error_count == 0
        assert result.warning_count == 0
        assert len(result.issues) == 0

    def test_add_error(self) -> None:
        """Test adding error to result."""
        result = ValidationResult()
        result.add_error("TEST_ERROR", "Test error message", location="test:1")
        assert result.is_valid is False
        assert result.error_count == 1
        assert len(result.errors) == 1
        assert result.errors[0].severity == ValidationSeverity.ERROR

    def test_add_warning(self) -> None:
        """Test adding warning to result."""
        result = ValidationResult()
        result.add_warning("TEST_WARNING", "Test warning message")
        assert result.is_valid is True  # Warnings don't invalidate
        assert result.warning_count == 1
        assert len(result.warnings) == 1

    def test_add_info(self) -> None:
        """Test adding info to result."""
        result = ValidationResult()
        result.add_info("TEST_INFO", "Test info message")
        assert result.is_valid is True
        assert len(result.issues) == 1
        assert result.issues[0].severity == ValidationSeverity.INFO

    def test_merge_results(self) -> None:
        """Test merging two validation results."""
        result1 = ValidationResult()
        result1.add_error("ERROR1", "First error")

        result2 = ValidationResult()
        result2.add_warning("WARNING1", "First warning")

        result1.merge(result2)
        assert result1.error_count == 1
        assert result1.warning_count == 1
        assert len(result1.issues) == 2

    def test_to_dict_serialization(self) -> None:
        """Test serialization to dictionary."""
        result = ValidationResult()
        result.add_error("TEST_ERROR", "Test error", location="test:1")
        result.add_warning("TEST_WARNING", "Test warning")

        data = result.to_dict()
        assert data["is_valid"] is False
        assert data["error_count"] == 1
        assert data["warning_count"] == 1
        assert len(data["issues"]) == 2

    def test_format_summary(self) -> None:
        """Test summary formatting."""
        result = ValidationResult()
        result.add_error("E001", "Error message", suggestion="Fix this")
        result.add_warning("W001", "Warning message", location="node:123")

        summary = result.format_summary()
        assert "FAILED" in summary
        assert "1 error(s)" in summary
        assert "1 warning(s)" in summary
        assert "E001" in summary
        assert "W001" in summary


# ============================================================================
# Quick Validate Tests
# ============================================================================


class TestQuickValidate:
    """Test quick_validate helper function."""

    def test_quick_validate_valid(self, valid_workflow) -> None:
        """Test quick_validate with valid workflow."""
        is_valid, errors = quick_validate(valid_workflow)
        assert is_valid is True
        assert len(errors) == 0

    def test_quick_validate_invalid(self) -> None:
        """Test quick_validate with invalid workflow."""
        data = {"nodes": []}  # Invalid: nodes should be dict
        is_valid, errors = quick_validate(data)
        assert is_valid is False
        assert len(errors) > 0
        assert all(isinstance(e, str) for e in errors)


# ============================================================================
# Edge Cases and Boundary Tests
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_workflow_with_only_hidden_nodes(self) -> None:
        """Test workflow with only hidden/internal nodes."""
        data = {
            "metadata": {"name": "Hidden Nodes"},
            "nodes": {
                "__auto_start__": {
                    "node_id": "__auto_start__",
                    "node_type": "StartNode",
                },
                "__internal__": {
                    "node_id": "__internal__",
                    "node_type": "LogNode",
                },
            },
            "connections": [],
        }
        result = validate_workflow(data)
        # Should recognize __auto_start__ as entry point
        # and not complain about unreachable hidden nodes

    def test_workflow_with_data_only_connections(self) -> None:
        """Test workflow with only data connections (no exec flow)."""
        data = {
            "metadata": {"name": "Data Only"},
            "nodes": {
                "n1": {"node_id": "n1", "node_type": "GetVariableNode"},
                "n2": {"node_id": "n2", "node_type": "SetVariableNode"},
            },
            "connections": [
                {
                    "source_node": "n1",
                    "source_port": "value",
                    "target_node": "n2",
                    "target_port": "input",
                }
            ],
        }
        result = validate_workflow(data)
        # Should warn about no entry point or unreachable nodes

    def test_very_large_workflow(self) -> None:
        """Test validation performance with large workflow."""
        # Create a workflow with 1000 nodes
        nodes = {}
        for i in range(1000):
            nodes[f"node{i}"] = {
                "node_id": f"node{i}",
                "node_type": "LogNode",
            }

        data = {"metadata": {"name": "Large"}, "nodes": nodes, "connections": []}
        result = validate_workflow(data)
        # Should complete without crashing

    def test_deeply_nested_connections(self) -> None:
        """Test workflow with deep connection chains."""
        nodes = {}
        connections = []
        for i in range(100):
            nodes[f"node{i}"] = {
                "node_id": f"node{i}",
                "node_type": "LogNode",
            }
            if i > 0:
                connections.append(
                    {
                        "source_node": f"node{i-1}",
                        "source_port": "exec_out",
                        "target_node": f"node{i}",
                        "target_port": "exec_in",
                    }
                )

        data = {
            "metadata": {"name": "Deep Chain"},
            "nodes": nodes,
            "connections": connections,
        }
        result = validate_workflow(data)
        # Should complete and detect single entry point

    def test_unicode_in_workflow_data(self) -> None:
        """Test handling of Unicode characters in workflow data."""
        data = {
            "metadata": {"name": "测试工作流 🚀"},
            "nodes": {
                "node1": {
                    "node_id": "node1",
                    "node_type": "StartNode",
                    "config": {"message": "Hello 世界"},
                }
            },
        }
        result = validate_workflow(data)
        # Should handle Unicode without errors

    def test_none_values_in_workflow(self) -> None:
        """Test handling of None values in workflow data."""
        data = {
            "metadata": {"name": None},
            "nodes": {
                "n1": {
                    "node_id": "n1",
                    "node_type": "StartNode",
                    "position": None,
                    "config": None,
                }
            },
        }
        result = validate_workflow(data)
        # Should handle None gracefully
