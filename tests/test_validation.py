"""
Tests for CasareRPA Workflow Validation Module.

Tests schema validation, node validation, connection validation,
and semantic validation of workflow structures.
"""

import pytest
from casare_rpa.core.validation import (
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
    validate_workflow,
    validate_node,
    validate_connections,
    quick_validate,
)


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_default_valid(self):
        """Test default result is valid."""
        result = ValidationResult()
        assert result.is_valid is True
        assert result.error_count == 0
        assert result.warning_count == 0

    def test_add_error_invalidates(self):
        """Test adding error marks result as invalid."""
        result = ValidationResult()
        result.add_error("TEST_ERROR", "Test error message")
        assert result.is_valid is False
        assert result.error_count == 1

    def test_add_warning_keeps_valid(self):
        """Test adding warning keeps result valid."""
        result = ValidationResult()
        result.add_warning("TEST_WARNING", "Test warning")
        assert result.is_valid is True
        assert result.warning_count == 1

    def test_errors_property(self):
        """Test errors property returns only errors."""
        result = ValidationResult()
        result.add_error("ERR1", "Error 1")
        result.add_warning("WARN1", "Warning 1")
        result.add_error("ERR2", "Error 2")

        assert len(result.errors) == 2
        assert all(e.severity == ValidationSeverity.ERROR for e in result.errors)

    def test_warnings_property(self):
        """Test warnings property returns only warnings."""
        result = ValidationResult()
        result.add_error("ERR1", "Error 1")
        result.add_warning("WARN1", "Warning 1")
        result.add_warning("WARN2", "Warning 2")

        assert len(result.warnings) == 2
        assert all(w.severity == ValidationSeverity.WARNING for w in result.warnings)

    def test_merge_results(self):
        """Test merging validation results."""
        result1 = ValidationResult()
        result1.add_error("ERR1", "Error from result 1")

        result2 = ValidationResult()
        result2.add_warning("WARN1", "Warning from result 2")

        result1.merge(result2)

        assert result1.error_count == 1
        assert result1.warning_count == 1
        assert result1.is_valid is False

    def test_to_dict(self):
        """Test serialization to dictionary."""
        result = ValidationResult()
        result.add_error("ERR1", "Test error", location="node:123")

        data = result.to_dict()

        assert data["is_valid"] is False
        assert data["error_count"] == 1
        assert len(data["issues"]) == 1
        assert data["issues"][0]["code"] == "ERR1"

    def test_format_summary(self):
        """Test human-readable summary formatting."""
        result = ValidationResult()
        summary = result.format_summary()
        assert "passed" in summary.lower()

        result.add_error("ERR1", "Test error")
        summary = result.format_summary()
        assert "FAILED" in summary
        assert "ERR1" in summary


class TestValidationIssue:
    """Tests for ValidationIssue class."""

    def test_to_dict(self):
        """Test serialization to dictionary."""
        issue = ValidationIssue(
            severity=ValidationSeverity.ERROR,
            code="TEST_CODE",
            message="Test message",
            location="node:abc",
            suggestion="Fix it",
        )

        data = issue.to_dict()

        assert data["severity"] == "ERROR"
        assert data["code"] == "TEST_CODE"
        assert data["message"] == "Test message"
        assert data["location"] == "node:abc"
        assert data["suggestion"] == "Fix it"


class TestValidateWorkflowStructure:
    """Tests for top-level workflow structure validation."""

    def test_empty_dict_fails(self):
        """Test empty dictionary fails validation."""
        result = validate_workflow({})
        assert result.is_valid is False
        assert any("nodes" in i.message.lower() for i in result.errors)

    def test_non_dict_fails(self):
        """Test non-dictionary input fails."""
        result = validate_workflow([])  # List instead of dict
        assert result.is_valid is False
        assert any("dictionary" in i.message.lower() for i in result.errors)

    def test_nodes_must_be_dict(self):
        """Test nodes field must be dictionary."""
        result = validate_workflow({"nodes": []})
        assert result.is_valid is False
        assert any("dictionary" in i.message.lower() for i in result.errors)

    def test_connections_must_be_list(self):
        """Test connections field must be list."""
        result = validate_workflow({
            "nodes": {},
            "connections": {},
        })
        assert result.is_valid is False
        assert any("list" in i.message.lower() for i in result.errors)

    def test_minimal_valid_workflow(self):
        """Test minimal valid workflow structure."""
        result = validate_workflow({
            "nodes": {
                "start": {
                    "node_id": "start",
                    "node_type": "StartNode",
                },
                "end": {
                    "node_id": "end",
                    "node_type": "EndNode",
                },
            },
            "connections": [
                {
                    "source_node": "start",
                    "source_port": "exec_out",
                    "target_node": "end",
                    "target_port": "exec_in",
                },
            ],
        })
        assert result.is_valid is True


class TestValidateMetadata:
    """Tests for workflow metadata validation."""

    def test_missing_name_warns(self):
        """Test missing workflow name generates warning."""
        result = validate_workflow({
            "nodes": {"n1": {"node_id": "n1", "node_type": "StartNode"}},
            "metadata": {},
        })
        assert any(
            i.code == "MISSING_NAME"
            for i in result.warnings
        )

    def test_long_name_warns(self):
        """Test excessively long name generates warning."""
        result = validate_workflow({
            "nodes": {"n1": {"node_id": "n1", "node_type": "StartNode"}},
            "metadata": {"name": "A" * 150},
        })
        assert any(
            i.code == "NAME_TOO_LONG"
            for i in result.warnings
        )

    def test_schema_version_mismatch_warns(self):
        """Test mismatched schema version generates warning."""
        result = validate_workflow({
            "nodes": {"n1": {"node_id": "n1", "node_type": "StartNode"}},
            "metadata": {"schema_version": "0.1.0"},
        })
        assert any(
            i.code == "SCHEMA_VERSION_MISMATCH"
            for i in result.warnings
        )


class TestValidateNode:
    """Tests for individual node validation."""

    def test_missing_node_type(self):
        """Test missing node_type fails validation."""
        result = validate_node("test", {"node_id": "test"})
        assert result.is_valid is False
        assert any("node_type" in i.message for i in result.errors)

    def test_missing_node_id(self):
        """Test missing node_id fails validation."""
        result = validate_node("test", {"node_type": "StartNode"})
        assert result.is_valid is False
        assert any("node_id" in i.message for i in result.errors)

    def test_node_id_mismatch(self):
        """Test node_id mismatch with key fails."""
        result = validate_node("key1", {
            "node_id": "key2",
            "node_type": "StartNode",
        })
        assert result.is_valid is False
        assert any(i.code == "NODE_ID_MISMATCH" for i in result.errors)

    def test_unknown_node_type(self):
        """Test unknown node type fails validation."""
        result = validate_node("test", {
            "node_id": "test",
            "node_type": "NonExistentNode",
        })
        assert result.is_valid is False
        assert any(i.code == "UNKNOWN_NODE_TYPE" for i in result.errors)

    def test_valid_node_types(self):
        """Test various valid node types pass."""
        valid_types = ["StartNode", "EndNode", "IfNode", "ForLoopNode", "ClickElementNode"]

        for node_type in valid_types:
            result = validate_node("test", {
                "node_id": "test",
                "node_type": node_type,
            })
            assert result.is_valid is True, f"Node type {node_type} should be valid"

    def test_invalid_position_format_warns(self):
        """Test invalid position format generates warning."""
        result = validate_node("test", {
            "node_id": "test",
            "node_type": "StartNode",
            "position": "invalid",
        })
        assert any(i.code == "INVALID_POSITION" for i in result.warnings)

    def test_valid_position(self):
        """Test valid position passes."""
        result = validate_node("test", {
            "node_id": "test",
            "node_type": "StartNode",
            "position": [100, 200],
        })
        assert not any(i.code == "INVALID_POSITION" for i in result.issues)

    def test_invalid_config_type(self):
        """Test non-dictionary config fails."""
        result = validate_node("test", {
            "node_id": "test",
            "node_type": "StartNode",
            "config": "invalid",
        })
        assert result.is_valid is False
        assert any(i.code == "INVALID_CONFIG" for i in result.errors)


class TestValidateConnections:
    """Tests for connection validation."""

    def test_missing_required_fields(self):
        """Test connection missing required fields fails."""
        result = validate_connections(
            [{"source_node": "n1"}],  # Missing other fields
            {"n1", "n2"},
        )
        assert result.is_valid is False
        assert any(i.code == "MISSING_REQUIRED_FIELD" for i in result.errors)

    def test_orphaned_source_node(self):
        """Test connection to non-existent source node fails."""
        result = validate_connections(
            [{
                "source_node": "missing",
                "source_port": "exec_out",
                "target_node": "n2",
                "target_port": "exec_in",
            }],
            {"n1", "n2"},
        )
        assert result.is_valid is False
        assert any(i.code == "ORPHANED_CONNECTION" for i in result.errors)

    def test_orphaned_target_node(self):
        """Test connection to non-existent target node fails."""
        result = validate_connections(
            [{
                "source_node": "n1",
                "source_port": "exec_out",
                "target_node": "missing",
                "target_port": "exec_in",
            }],
            {"n1", "n2"},
        )
        assert result.is_valid is False
        assert any(i.code == "ORPHANED_CONNECTION" for i in result.errors)

    def test_self_connection(self):
        """Test self-connection fails."""
        result = validate_connections(
            [{
                "source_node": "n1",
                "source_port": "exec_out",
                "target_node": "n1",
                "target_port": "exec_in",
            }],
            {"n1"},
        )
        assert result.is_valid is False
        assert any(i.code == "SELF_CONNECTION" for i in result.errors)

    def test_duplicate_connection_warns(self):
        """Test duplicate connections generate warning."""
        result = validate_connections(
            [
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
            ],
            {"n1", "n2"},
        )
        assert any(i.code == "DUPLICATE_CONNECTION" for i in result.warnings)

    def test_valid_connection(self):
        """Test valid connection passes."""
        result = validate_connections(
            [{
                "source_node": "n1",
                "source_port": "exec_out",
                "target_node": "n2",
                "target_port": "exec_in",
            }],
            {"n1", "n2"},
        )
        assert result.is_valid is True


class TestValidateWorkflowSemantics:
    """Tests for workflow-level semantic validation."""

    def test_empty_workflow_fails(self):
        """Test workflow with no nodes fails."""
        result = validate_workflow({"nodes": {}})
        assert result.is_valid is False
        assert any(i.code == "EMPTY_WORKFLOW" for i in result.errors)

    def test_no_start_node_warns(self):
        """Test workflow without StartNode generates warning."""
        result = validate_workflow({
            "nodes": {
                "n1": {"node_id": "n1", "node_type": "IfNode"},
            },
        })
        assert any(i.code == "NO_START_NODE" for i in result.warnings)

    def test_multiple_start_nodes_fails(self):
        """Test workflow with multiple StartNodes fails."""
        result = validate_workflow({
            "nodes": {
                "s1": {"node_id": "s1", "node_type": "StartNode"},
                "s2": {"node_id": "s2", "node_type": "StartNode"},
            },
        })
        assert result.is_valid is False
        assert any(i.code == "MULTIPLE_START_NODES" for i in result.errors)

    def test_no_end_node_warns(self):
        """Test workflow without EndNode generates warning."""
        result = validate_workflow({
            "nodes": {
                "n1": {"node_id": "n1", "node_type": "StartNode"},
            },
        })
        assert any(i.code == "NO_END_NODE" for i in result.warnings)

    def test_circular_dependency_fails(self):
        """Test workflow with circular exec flow fails."""
        result = validate_workflow({
            "nodes": {
                "n1": {"node_id": "n1", "node_type": "StartNode"},
                "n2": {"node_id": "n2", "node_type": "IfNode"},
                "n3": {"node_id": "n3", "node_type": "ForLoopNode"},
            },
            "connections": [
                {"source_node": "n1", "source_port": "exec_out", "target_node": "n2", "target_port": "exec_in"},
                {"source_node": "n2", "source_port": "exec_out", "target_node": "n3", "target_port": "exec_in"},
                {"source_node": "n3", "source_port": "exec_out", "target_node": "n2", "target_port": "exec_in"},
            ],
        })
        assert result.is_valid is False
        assert any(i.code == "CIRCULAR_DEPENDENCY" for i in result.errors)

    def test_unreachable_nodes_warns(self):
        """Test unreachable nodes generate warning."""
        result = validate_workflow({
            "nodes": {
                "start": {"node_id": "start", "node_type": "StartNode"},
                "connected": {"node_id": "connected", "node_type": "IfNode"},
                "disconnected": {"node_id": "disconnected", "node_type": "ForLoopNode"},
            },
            "connections": [
                {"source_node": "start", "source_port": "exec_out", "target_node": "connected", "target_port": "exec_in"},
            ],
        })
        assert any(
            i.code == "UNREACHABLE_NODES" and "disconnected" in i.message
            for i in result.warnings
        )


class TestQuickValidate:
    """Tests for quick_validate backward compatibility function."""

    def test_valid_workflow(self):
        """Test quick_validate returns True for valid workflow."""
        is_valid, errors = quick_validate({
            "nodes": {
                "start": {"node_id": "start", "node_type": "StartNode"},
                "end": {"node_id": "end", "node_type": "EndNode"},
            },
            "connections": [],
        })
        assert is_valid is True
        assert errors == []

    def test_invalid_workflow(self):
        """Test quick_validate returns False and errors for invalid workflow."""
        is_valid, errors = quick_validate({
            "nodes": {
                "n1": {"node_id": "n1", "node_type": "InvalidType"},
            },
        })
        assert is_valid is False
        assert len(errors) > 0
        assert any("UNKNOWN_NODE_TYPE" in e for e in errors)


class TestComplexWorkflowValidation:
    """Tests for complex workflow scenarios."""

    def test_complete_valid_workflow(self):
        """Test a complete valid workflow passes all checks."""
        result = validate_workflow({
            "metadata": {
                "name": "Test Workflow",
                "description": "A complete test workflow",
                "schema_version": "1.0.0",
            },
            "nodes": {
                "start": {"node_id": "start", "node_type": "StartNode", "position": [0, 0]},
                "browser": {"node_id": "browser", "node_type": "LaunchBrowserNode", "position": [100, 0], "config": {"headless": False}},
                "goto": {"node_id": "goto", "node_type": "GoToURLNode", "position": [200, 0], "config": {"url": "https://example.com"}},
                "click": {"node_id": "click", "node_type": "ClickElementNode", "position": [300, 0], "config": {"selector": "#button"}},
                "end": {"node_id": "end", "node_type": "EndNode", "position": [400, 0]},
            },
            "connections": [
                {"source_node": "start", "source_port": "exec_out", "target_node": "browser", "target_port": "exec_in"},
                {"source_node": "browser", "source_port": "exec_out", "target_node": "goto", "target_port": "exec_in"},
                {"source_node": "goto", "source_port": "exec_out", "target_node": "click", "target_port": "exec_in"},
                {"source_node": "click", "source_port": "exec_out", "target_node": "end", "target_port": "exec_in"},
            ],
            "variables": {"test_var": "value"},
            "settings": {"stop_on_error": True},
        })

        assert result.is_valid is True
        assert result.error_count == 0
        # May have informational warnings but no blocking issues

    def test_workflow_with_control_flow(self):
        """Test workflow with branching control flow."""
        result = validate_workflow({
            "nodes": {
                "start": {"node_id": "start", "node_type": "StartNode"},
                "if": {"node_id": "if", "node_type": "IfNode"},
                "then_branch": {"node_id": "then_branch", "node_type": "LogNode"},
                "else_branch": {"node_id": "else_branch", "node_type": "LogNode"},
                "end": {"node_id": "end", "node_type": "EndNode"},
            },
            "connections": [
                {"source_node": "start", "source_port": "exec_out", "target_node": "if", "target_port": "exec_in"},
                {"source_node": "if", "source_port": "then", "target_node": "then_branch", "target_port": "exec_in"},
                {"source_node": "if", "source_port": "else", "target_node": "else_branch", "target_port": "exec_in"},
                {"source_node": "then_branch", "source_port": "exec_out", "target_node": "end", "target_port": "exec_in"},
                {"source_node": "else_branch", "source_port": "exec_out", "target_node": "end", "target_port": "exec_in"},
            ],
        })

        assert result.is_valid is True
