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
        "nodes": [
            {
                "id": f"node_{i}",
                "type": "StartNode",
                "name": f"Start Node {i}",
                "position": {"x": 0.0, "y": 0.0},
                "properties": {},
                "inputs": [],
                "outputs": [],
            }
            for i in range(num_nodes)
        ],
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
        workflow["nodes"][0]["type"] = "__import__('os').system('evil')"

        with pytest.raises(ValidationError, match="dangerous pattern"):
            validate_workflow_json(workflow)

    def test_reject_dangerous_node_type_eval(self):
        """Should reject node type with eval."""
        workflow = create_valid_workflow()
        workflow["nodes"][0]["type"] = "eval('malicious_code')"

        with pytest.raises(ValidationError, match="dangerous pattern"):
            validate_workflow_json(workflow)

    def test_reject_dangerous_node_type_exec(self):
        """Should reject node type with exec."""
        workflow = create_valid_workflow()
        workflow["nodes"][0]["type"] = "exec('bad_code')"

        with pytest.raises(ValidationError, match="dangerous pattern"):
            validate_workflow_json(workflow)

    def test_reject_dangerous_node_type_subprocess(self):
        """Should reject node type with subprocess."""
        workflow = create_valid_workflow()
        workflow["nodes"][0]["type"] = "subprocess.call(['rm', '-rf', '/'])"

        with pytest.raises(ValidationError, match="dangerous pattern"):
            validate_workflow_json(workflow)

    def test_reject_dangerous_properties_import(self):
        """Should reject properties with __import__."""
        workflow = create_valid_workflow()
        workflow["nodes"][0]["properties"] = {"code": "__import__('os').system('evil')"}

        with pytest.raises(ValidationError, match="dangerous pattern"):
            validate_workflow_json(workflow)

    def test_reject_dangerous_properties_eval(self):
        """Should reject properties with eval(."""
        workflow = create_valid_workflow()
        workflow["nodes"][0]["properties"] = {"script": "eval('malicious')"}

        with pytest.raises(ValidationError, match="dangerous pattern"):
            validate_workflow_json(workflow)

    def test_reject_too_many_nodes(self):
        """Should reject workflow with more than 1000 nodes."""
        workflow = create_valid_workflow(num_nodes=1001)

        with pytest.raises(ValidationError, match="at most 1000"):
            validate_workflow_json(workflow)

    def test_reject_too_many_connections(self):
        """Should reject workflow with more than 5000 connections."""
        workflow = create_valid_workflow()
        workflow["connections"] = [
            {
                "id": f"conn_{i}",
                "source_node": "node_0",
                "source_port": "out",
                "target_node": "node_0",
                "target_port": "in",
            }
            for i in range(5001)
        ]

        with pytest.raises(ValidationError, match="at most 5000"):
            validate_workflow_json(workflow)

    def test_reject_empty_workflow(self):
        """Should reject workflow with no nodes."""
        workflow = create_valid_workflow()
        workflow["nodes"] = []

        with pytest.raises(ValidationError, match="at least one node"):
            validate_workflow_json(workflow)

    def test_reject_invalid_node_id(self):
        """Should reject node with invalid ID."""
        workflow = create_valid_workflow()
        workflow["nodes"][0]["id"] = ""

        with pytest.raises(ValidationError, match="at least 1 character"):
            validate_workflow_json(workflow)

    def test_reject_too_long_node_name(self):
        """Should reject node name longer than 256 chars."""
        workflow = create_valid_workflow()
        workflow["nodes"][0]["name"] = "x" * 257

        with pytest.raises(ValidationError, match="at most 256"):
            validate_workflow_json(workflow)

    def test_reject_too_long_workflow_name(self):
        """Should reject workflow name longer than 256 chars."""
        workflow = create_valid_workflow()
        workflow["metadata"]["name"] = "x" * 257

        with pytest.raises(ValidationError, match="at most 256"):
            validate_workflow_json(workflow)

    def test_accept_safe_properties(self):
        """Should accept properties without dangerous patterns."""
        workflow = create_valid_workflow()
        workflow["nodes"][0]["properties"] = {
            "url": "https://example.com",
            "timeout": 30,
            "retry_count": 3,
        }

        validated = validate_workflow_json(workflow)
        assert validated.nodes[0].properties["url"] == "https://example.com"

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
                "id": f"conn_{i}",
                "source_node": "node_0",
                "source_port": "out",
                "target_node": "node_0",
                "target_port": "in",
            }
            for i in range(5000)
        ]

        validated = validate_workflow_json(workflow)
        assert len(validated.connections) == 5000
