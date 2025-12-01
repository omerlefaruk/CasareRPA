"""
Tests for workflow JSON schema validation.

Verifies protection against malicious workflow injection and resource exhaustion.
"""

import pytest
from pydantic import ValidationError

from casare_rpa.infrastructure.security.workflow_schema import (
    WorkflowNodeSchema,
    WorkflowSchema,
    validate_workflow_json,
)


def create_valid_workflow(num_nodes=1):
    """Helper to create a valid workflow for testing."""
    return {
        "metadata": {
            "name": "Test Workflow",
            "description": "Test",
            "version": "1.0",
        },
        "nodes": {
            f"node_{i}": {
                "node_id": f"node_{i}",
                "node_type": "StartNode",
                "position": [0.0, 0.0],
                "config": {},
            }
            for i in range(num_nodes)
        },
        "connections": [],
        "variables": {},
    }


class TestWorkflowSchemaValidation:
    """Test workflow schema validation."""

    def test_valid_workflow(self):
        """Valid workflow should pass validation."""
        workflow = create_valid_workflow()
        validated = validate_workflow_json(workflow)
        assert validated.metadata.name == "Test Workflow"
        assert len(validated.nodes) == 1

    def test_reject_dangerous_node_type_import(self):
        """Should reject node type with __import__."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["node_type"] = "__import__('os').system('evil')"

        with pytest.raises(ValidationError, match="dangerous pattern"):
            validate_workflow_json(workflow)

    def test_reject_dangerous_node_type_eval(self):
        """Should reject node type with eval."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["node_type"] = "eval('malicious_code')"

        with pytest.raises(ValidationError, match="dangerous pattern"):
            validate_workflow_json(workflow)

    def test_reject_dangerous_node_type_exec(self):
        """Should reject node type with exec."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["node_type"] = "exec('bad_code')"

        with pytest.raises(ValidationError, match="dangerous pattern"):
            validate_workflow_json(workflow)

    def test_reject_dangerous_node_type_subprocess(self):
        """Should reject node type with subprocess."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["node_type"] = "subprocess.call(['rm', '-rf', '/'])"

        with pytest.raises(ValidationError, match="dangerous pattern"):
            validate_workflow_json(workflow)

    def test_reject_dangerous_config_import(self):
        """Should reject config with __import__."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["config"] = {
            "code": "__import__('os').system('evil')"
        }

        with pytest.raises(ValidationError, match="dangerous pattern"):
            validate_workflow_json(workflow)

    def test_reject_dangerous_config_eval(self):
        """Should reject config with eval(."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["config"] = {"script": "eval('malicious')"}

        with pytest.raises(ValidationError, match="dangerous pattern"):
            validate_workflow_json(workflow)

    def test_reject_too_many_nodes(self):
        """Should reject workflow with more than 1000 nodes."""
        workflow = create_valid_workflow(num_nodes=1001)

        with pytest.raises(ValidationError, match="1000"):
            validate_workflow_json(workflow)

    def test_reject_too_many_connections(self):
        """Should reject workflow with more than 5000 connections."""
        workflow = create_valid_workflow()
        workflow["connections"] = [
            {
                "source_node": "node_0",
                "source_port": "out",
                "target_node": "node_0",
                "target_port": "in",
            }
            for _ in range(5001)
        ]

        with pytest.raises(ValidationError, match="at most 5000"):
            validate_workflow_json(workflow)

    def test_reject_empty_workflow(self):
        """Should reject workflow with no nodes."""
        workflow = create_valid_workflow()
        workflow["nodes"] = {}

        with pytest.raises(ValidationError, match="at least one node"):
            validate_workflow_json(workflow)

    def test_reject_invalid_node_id(self):
        """Should reject node with invalid ID."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["node_id"] = ""

        with pytest.raises(ValidationError, match="at least 1 character"):
            validate_workflow_json(workflow)

    def test_reject_too_long_node_type(self):
        """Should reject node type longer than 128 chars."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["node_type"] = "x" * 129

        with pytest.raises(ValidationError, match="at most 128"):
            validate_workflow_json(workflow)

    def test_reject_too_long_workflow_name(self):
        """Should reject workflow name longer than 256 chars."""
        workflow = create_valid_workflow()
        workflow["metadata"]["name"] = "x" * 257

        with pytest.raises(ValidationError, match="at most 256"):
            validate_workflow_json(workflow)

    def test_accept_safe_config(self):
        """Should accept config without dangerous patterns."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["config"] = {
            "url": "https://example.com",
            "timeout": 30,
            "retry_count": 3,
        }

        validated = validate_workflow_json(workflow)
        assert validated.nodes["node_0"].config["url"] == "https://example.com"

    def test_accept_max_nodes(self):
        """Should accept workflow with exactly 1000 nodes."""
        workflow = create_valid_workflow(num_nodes=1000)
        validated = validate_workflow_json(workflow)
        assert len(validated.nodes) == 1000

    def test_accept_max_connections(self):
        """Should accept workflow with exactly 5000 connections."""
        workflow = create_valid_workflow()
        workflow["connections"] = [
            {
                "source_node": "node_0",
                "source_port": "out",
                "target_node": "node_0",
                "target_port": "in",
            }
            for _ in range(5000)
        ]

        validated = validate_workflow_json(workflow)
        assert len(validated.connections) == 5000


class TestWorkflowSchemaEdgeCases:
    """Test edge cases for workflow schema validation."""

    def test_position_with_two_elements(self):
        """Should accept position with exactly two elements [x, y]."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["position"] = [100.5, 200.3]
        validated = validate_workflow_json(workflow)
        assert validated.nodes["node_0"].position == [100.5, 200.3]

    def test_position_with_integer_values(self):
        """Should accept position with integer values (auto-converted to float)."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["position"] = [100, 200]
        validated = validate_workflow_json(workflow)
        assert validated.nodes["node_0"].position == [100, 200]

    def test_position_with_negative_values(self):
        """Should accept position with negative coordinates."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["position"] = [-500.0, -300.0]
        validated = validate_workflow_json(workflow)
        assert validated.nodes["node_0"].position == [-500.0, -300.0]

    def test_missing_optional_metadata_fields(self):
        """Should accept workflow with only required metadata fields."""
        workflow = {
            "metadata": {"name": "Minimal Workflow"},
            "nodes": {
                "n1": {
                    "node_id": "n1",
                    "node_type": "StartNode",
                    "position": [0.0, 0.0],
                }
            },
            "connections": [],
        }
        validated = validate_workflow_json(workflow)
        assert validated.metadata.name == "Minimal Workflow"
        assert validated.metadata.description is None
        assert validated.metadata.version is None

    def test_optional_frames_field(self):
        """Should accept workflow with frames field."""
        workflow = create_valid_workflow()
        workflow["frames"] = [
            {"title": "Group1", "position": [0, 0], "size": [400, 300], "node_ids": []}
        ]
        validated = validate_workflow_json(workflow)
        assert len(validated.frames) == 1

    def test_optional_settings_field(self):
        """Should accept workflow with settings field."""
        workflow = create_valid_workflow()
        workflow["settings"] = {"stop_on_error": True, "timeout": 120}
        validated = validate_workflow_json(workflow)
        assert validated.settings["stop_on_error"] is True

    def test_node_with_empty_config(self):
        """Should accept node with empty config dict."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["config"] = {}
        validated = validate_workflow_json(workflow)
        assert validated.nodes["node_0"].config == {}

    def test_node_with_complex_config(self):
        """Should accept node with nested config values."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["config"] = {
            "selector": "#main > .button",
            "options": {"timeout": 5000, "visible": True},
            "variables": ["var1", "var2"],
        }
        validated = validate_workflow_json(workflow)
        assert validated.nodes["node_0"].config["options"]["timeout"] == 5000

    def test_metadata_with_created_and_modified_timestamps(self):
        """Should accept metadata with timestamp fields."""
        workflow = create_valid_workflow()
        workflow["metadata"]["created_at"] = "2024-01-01T12:00:00Z"
        workflow["metadata"]["modified_at"] = "2024-01-02T15:30:00Z"
        validated = validate_workflow_json(workflow)
        assert validated.metadata.created_at == "2024-01-01T12:00:00Z"

    def test_metadata_with_tags(self):
        """Should accept metadata with tags list."""
        workflow = create_valid_workflow()
        workflow["metadata"]["tags"] = ["automation", "browser", "testing"]
        validated = validate_workflow_json(workflow)
        assert len(validated.metadata.tags) == 3

    def test_multiple_nodes_with_connections(self):
        """Should accept workflow with multiple connected nodes."""
        workflow = {
            "metadata": {"name": "Connected Workflow"},
            "nodes": {
                "start": {
                    "node_id": "start",
                    "node_type": "StartNode",
                    "position": [0.0, 0.0],
                },
                "process": {
                    "node_id": "process",
                    "node_type": "LogNode",
                    "position": [200.0, 0.0],
                    "config": {"message": "Processing"},
                },
                "end": {
                    "node_id": "end",
                    "node_type": "EndNode",
                    "position": [400.0, 0.0],
                },
            },
            "connections": [
                {
                    "source_node": "start",
                    "source_port": "exec_out",
                    "target_node": "process",
                    "target_port": "exec_in",
                },
                {
                    "source_node": "process",
                    "source_port": "exec_out",
                    "target_node": "end",
                    "target_port": "exec_in",
                },
            ],
        }
        validated = validate_workflow_json(workflow)
        assert len(validated.nodes) == 3
        assert len(validated.connections) == 2


class TestWorkflowSchemaSecurityValidation:
    """Test security-specific validation patterns."""

    def test_reject_compile_in_node_type(self):
        """Should reject node type with compile."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["node_type"] = "compile('code', 'file', 'exec')"
        with pytest.raises(ValidationError, match="dangerous pattern"):
            validate_workflow_json(workflow)

    def test_reject_os_system_in_node_type(self):
        """Should reject node type with os.system."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["node_type"] = "os.system('rm -rf /')"
        with pytest.raises(ValidationError, match="dangerous pattern"):
            validate_workflow_json(workflow)

    def test_reject_open_in_node_type(self):
        """Should reject node type with open(."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["node_type"] = "open('/etc/passwd', 'r')"
        with pytest.raises(ValidationError, match="dangerous pattern"):
            validate_workflow_json(workflow)

    def test_reject_file_in_node_type(self):
        """Should reject node type with file(."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["node_type"] = "file('/etc/passwd')"
        with pytest.raises(ValidationError, match="dangerous pattern"):
            validate_workflow_json(workflow)

    def test_reject_compile_in_config(self):
        """Should reject config with compile(."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["config"] = {"code": "compile('x=1', '', 'exec')"}
        with pytest.raises(ValidationError, match="dangerous pattern"):
            validate_workflow_json(workflow)

    def test_reject_os_system_in_config(self):
        """Should reject config with os.system."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["config"] = {"cmd": "os.system('whoami')"}
        with pytest.raises(ValidationError, match="dangerous pattern"):
            validate_workflow_json(workflow)

    def test_reject_subprocess_in_config(self):
        """Should reject config with subprocess."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["config"] = {"run": "subprocess.Popen(['ls'])"}
        with pytest.raises(ValidationError, match="dangerous pattern"):
            validate_workflow_json(workflow)

    def test_reject_nested_dangerous_config(self):
        """Should reject dangerous patterns in nested config."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["config"] = {
            "nested": {"deep": {"value": "__import__('os')"}}
        }
        with pytest.raises(ValidationError, match="dangerous pattern"):
            validate_workflow_json(workflow)

    def test_case_insensitive_dangerous_pattern_detection(self):
        """Should detect dangerous patterns regardless of case."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["node_type"] = "EVAL('code')"
        with pytest.raises(ValidationError, match="dangerous pattern"):
            validate_workflow_json(workflow)

    def test_reject_eval_as_substring(self):
        """Should reject 'eval' even as substring (security-first approach).

        Note: This is intentionally strict. Node types containing 'eval' as a
        substring (e.g., 'EvaluationNode') are blocked. If a legitimate node
        needs this name, rename it (e.g., 'AssessmentNode').
        """
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["node_type"] = "EvaluationNode"
        with pytest.raises(ValidationError, match="dangerous pattern"):
            validate_workflow_json(workflow)


class TestWorkflowSchemaStressTests:
    """Stress tests for workflow schema validation."""

    def test_large_workflow_999_nodes(self):
        """Should handle workflow with 999 nodes efficiently."""
        workflow = create_valid_workflow(num_nodes=999)
        validated = validate_workflow_json(workflow)
        assert len(validated.nodes) == 999

    def test_large_workflow_4999_connections(self):
        """Should handle workflow with 4999 connections efficiently."""
        workflow = create_valid_workflow(num_nodes=100)
        workflow["connections"] = [
            {
                "source_node": f"node_{i % 100}",
                "source_port": "out",
                "target_node": f"node_{(i + 1) % 100}",
                "target_port": "in",
            }
            for i in range(4999)
        ]
        validated = validate_workflow_json(workflow)
        assert len(validated.connections) == 4999

    def test_node_with_large_config(self):
        """Should handle node with large config dict."""
        workflow = create_valid_workflow()
        # Create config with many keys
        large_config = {f"key_{i}": f"value_{i}" for i in range(500)}
        workflow["nodes"]["node_0"]["config"] = large_config
        validated = validate_workflow_json(workflow)
        assert len(validated.nodes["node_0"].config) == 500

    def test_workflow_with_long_valid_strings(self):
        """Should accept strings at their maximum allowed length."""
        workflow = create_valid_workflow()
        workflow["metadata"]["name"] = "x" * 256  # Max allowed
        workflow["nodes"]["node_0"]["node_type"] = "y" * 128  # Max allowed
        workflow["nodes"]["node_0"]["node_id"] = "z" * 128  # Max allowed
        validated = validate_workflow_json(workflow)
        assert len(validated.metadata.name) == 256

    def test_deeply_nested_config(self):
        """Should handle deeply nested config structures."""
        workflow = create_valid_workflow()
        nested = {"level": 0}
        current = nested
        for i in range(1, 20):
            current["nested"] = {"level": i}
            current = current["nested"]
        workflow["nodes"]["node_0"]["config"] = nested
        validated = validate_workflow_json(workflow)
        assert validated.nodes["node_0"].config["level"] == 0

    def test_config_with_special_characters(self):
        """Should handle config with special characters."""
        workflow = create_valid_workflow()
        workflow["nodes"]["node_0"]["config"] = {
            "selector": "div[data-id='test'] > span.class-name",
            "xpath": "//div[@class='container']/span[text()='Hello']",
            "regex": r"^\d{3}-\d{2}-\d{4}$",
            "unicode": "Hello World",
        }
        validated = validate_workflow_json(workflow)
        assert "selector" in validated.nodes["node_0"].config

    def test_many_variables(self):
        """Should handle workflow with many variables."""
        workflow = create_valid_workflow()
        workflow["variables"] = {
            f"var_{i}": {"value": i, "type": "integer"} for i in range(200)
        }
        validated = validate_workflow_json(workflow)
        assert len(validated.variables) == 200


class TestWorkflowSchemaValidationErrors:
    """Test validation error messages and edge cases."""

    def test_missing_nodes_field(self):
        """Should reject workflow without nodes field."""
        workflow = {"metadata": {"name": "Test"}, "connections": []}
        with pytest.raises(ValidationError):
            validate_workflow_json(workflow)

    def test_missing_metadata_field(self):
        """Should reject workflow without metadata field."""
        workflow = {
            "nodes": {
                "n1": {"node_id": "n1", "node_type": "StartNode", "position": [0, 0]}
            },
            "connections": [],
        }
        with pytest.raises(ValidationError):
            validate_workflow_json(workflow)

    def test_missing_connections_field(self):
        """Should reject workflow without connections field."""
        workflow = {
            "metadata": {"name": "Test"},
            "nodes": {
                "n1": {"node_id": "n1", "node_type": "StartNode", "position": [0, 0]}
            },
        }
        with pytest.raises(ValidationError):
            validate_workflow_json(workflow)

    def test_missing_node_type_in_node(self):
        """Should reject node without node_type field."""
        workflow = create_valid_workflow()
        del workflow["nodes"]["node_0"]["node_type"]
        with pytest.raises(ValidationError):
            validate_workflow_json(workflow)

    def test_missing_node_id_in_node(self):
        """Should reject node without node_id field."""
        workflow = create_valid_workflow()
        del workflow["nodes"]["node_0"]["node_id"]
        with pytest.raises(ValidationError):
            validate_workflow_json(workflow)

    def test_missing_position_in_node(self):
        """Should reject node without position field."""
        workflow = create_valid_workflow()
        del workflow["nodes"]["node_0"]["position"]
        with pytest.raises(ValidationError):
            validate_workflow_json(workflow)

    def test_missing_metadata_name(self):
        """Should reject metadata without name field."""
        workflow = create_valid_workflow()
        del workflow["metadata"]["name"]
        with pytest.raises(ValidationError):
            validate_workflow_json(workflow)

    def test_invalid_connection_missing_source_node(self):
        """Should reject connection without source_node."""
        workflow = create_valid_workflow()
        workflow["connections"] = [
            {"source_port": "out", "target_node": "node_0", "target_port": "in"}
        ]
        with pytest.raises(ValidationError):
            validate_workflow_json(workflow)

    def test_invalid_connection_missing_target_port(self):
        """Should reject connection without target_port."""
        workflow = create_valid_workflow()
        workflow["connections"] = [
            {"source_node": "node_0", "source_port": "out", "target_node": "node_0"}
        ]
        with pytest.raises(ValidationError):
            validate_workflow_json(workflow)
