"""
Workflow JSON schema validation tests.

Tests for deserialization attack prevention (CWE-502).
"""

import pytest
from pydantic import ValidationError
from casare_rpa.infrastructure.security.workflow_schema import (
    validate_workflow_json,
    WorkflowSchema,
    WorkflowNodeSchema,
    WorkflowMetadataSchema,
)


class TestWorkflowJSONValidation:
    """Test workflow JSON validation to prevent deserialization attacks."""

    def test_valid_workflow_accepted(self):
        """Test that valid workflow JSON passes validation."""
        valid_workflow = {
            "metadata": {
                "name": "Test Workflow",
                "description": "A valid test workflow",
                "version": "1.0.0",
                "author": "test@example.com",
                "tags": ["test", "automation"],
            },
            "nodes": [
                {
                    "node_id": "node_1",
                    "node_type": "browser",
                    "node_name": "Open Browser",
                    "properties": {
                        "url": "https://example.com",
                        "browser_type": "chromium",
                    },
                    "position": {"x": 100.0, "y": 200.0},
                },
                {
                    "node_id": "node_2",
                    "node_type": "control_flow",
                    "node_name": "If Condition",
                    "properties": {
                        "condition": "status == 200",
                    },
                    "position": {"x": 300.0, "y": 200.0},
                },
            ],
            "connections": [
                {
                    "source_node": "node_1",
                    "source_port": "output",
                    "target_node": "node_2",
                    "target_port": "input",
                }
            ],
            "variables": {
                "api_key": "test_key",
                "timeout": 30,
                "enabled": True,
            },
        }

        # Should not raise
        result = validate_workflow_json(valid_workflow)
        assert result == valid_workflow

    def test_code_injection_patterns_rejected(self):
        """Test that dangerous code patterns are rejected."""
        dangerous_patterns = [
            "__import__('os').system('rm -rf /')",
            "eval('malicious_code')",
            "exec('import os; os.system(\"hack\")')",
            "compile('code', 'file', 'exec')",
            "os.system('dangerous')",
            "subprocess.call(['rm', '-rf', '/'])",
            "open('/etc/passwd', 'r').read()",
            "pickle.loads(malicious_data)",
            "marshal.loads(data)",
        ]

        for pattern in dangerous_patterns:
            malicious_workflow = {
                "metadata": {
                    "name": "Malicious Workflow",
                    "description": pattern,  # Try in description
                },
                "nodes": [
                    {
                        "node_id": "node_1",
                        "node_type": "test",
                        "properties": {"code": pattern},  # Try in properties
                    }
                ],
                "connections": [],
                "variables": {},
            }

            with pytest.raises(
                (ValueError, ValidationError), match="dangerous|Potentially dangerous"
            ):
                validate_workflow_json(malicious_workflow)

    def test_duplicate_node_ids_rejected(self):
        """Test that duplicate node IDs are rejected."""
        workflow_with_duplicates = {
            "metadata": {"name": "Test"},
            "nodes": [
                {"node_id": "node_1", "node_type": "test"},
                {"node_id": "node_1", "node_type": "test"},  # Duplicate
            ],
            "connections": [],
            "variables": {},
        }

        with pytest.raises((ValueError, ValidationError), match="Duplicate node IDs"):
            validate_workflow_json(workflow_with_duplicates)

    def test_invalid_connection_references_rejected(self):
        """Test that connections to non-existent nodes are rejected."""
        workflow_with_invalid_connection = {
            "metadata": {"name": "Test"},
            "nodes": [{"node_id": "node_1", "node_type": "test"}],
            "connections": [
                {
                    "source_node": "node_1",
                    "target_node": "non_existent_node",  # Invalid reference
                }
            ],
            "variables": {},
        }

        with pytest.raises(
            (ValueError, ValidationError), match="non-existent|references"
        ):
            validate_workflow_json(workflow_with_invalid_connection)

    def test_resource_exhaustion_limits_enforced(self):
        """Test that resource limits prevent DoS attacks."""
        # Test node count limit (max 10,000)
        workflow_too_many_nodes = {
            "metadata": {"name": "Test"},
            "nodes": [
                {"node_id": f"node_{i}", "node_type": "test"} for i in range(10001)
            ],
            "connections": [],
            "variables": {},
        }

        with pytest.raises((ValueError, ValidationError)):
            validate_workflow_json(workflow_too_many_nodes)

        # Test connection count limit (max 50,000)
        workflow_too_many_connections = {
            "metadata": {"name": "Test"},
            "nodes": [
                {"node_id": "node_1", "node_type": "test"},
                {"node_id": "node_2", "node_type": "test"},
            ],
            "connections": [
                {"source_node": "node_1", "target_node": "node_2"} for _ in range(50001)
            ],
            "variables": {},
        }

        with pytest.raises((ValueError, ValidationError)):
            validate_workflow_json(workflow_too_many_connections)

    def test_property_count_limit_enforced(self):
        """Test that property count limits prevent resource exhaustion."""
        workflow_too_many_properties = {
            "metadata": {"name": "Test"},
            "nodes": [
                {
                    "node_id": "node_1",
                    "node_type": "test",
                    "properties": {f"prop_{i}": "value" for i in range(1001)},
                }
            ],
            "connections": [],
            "variables": {},
        }

        with pytest.raises((ValueError, ValidationError), match="Too many properties"):
            validate_workflow_json(workflow_too_many_properties)

    def test_large_list_rejected(self):
        """Test that excessively large lists are rejected."""
        workflow_with_huge_list = {
            "metadata": {"name": "Test"},
            "nodes": [
                {
                    "node_id": "node_1",
                    "node_type": "test",
                    "properties": {"items": list(range(10001))},  # Too large
                }
            ],
            "connections": [],
            "variables": {},
        }

        with pytest.raises((ValueError, ValidationError), match="List too large"):
            validate_workflow_json(workflow_with_huge_list)

    def test_metadata_string_length_limits(self):
        """Test that metadata string length limits are enforced."""
        # Name too long (max 255)
        with pytest.raises((ValueError, ValidationError)):
            WorkflowMetadataSchema(name="a" * 256)

        # Description too long (max 2000)
        with pytest.raises((ValueError, ValidationError)):
            WorkflowMetadataSchema(name="Test", description="a" * 2001)

    def test_xss_patterns_rejected(self):
        """Test that XSS patterns in metadata are rejected."""
        xss_patterns = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "data:text/html,<script>alert('XSS')</script>",
        ]

        for pattern in xss_patterns:
            with pytest.raises(
                (ValueError, ValidationError), match="dangerous|Potentially dangerous"
            ):
                WorkflowMetadataSchema(name="Test", description=pattern)

    def test_nested_dict_validation(self):
        """Test that nested dictionaries in properties are validated."""
        malicious_nested = {
            "metadata": {"name": "Test"},
            "nodes": [
                {
                    "node_id": "node_1",
                    "node_type": "test",
                    "properties": {
                        "config": {
                            "nested": {
                                "code": "exec('malicious')",  # Nested injection
                            }
                        }
                    },
                }
            ],
            "connections": [],
            "variables": {},
        }

        with pytest.raises(
            (ValueError, ValidationError), match="dangerous|Potentially dangerous"
        ):
            validate_workflow_json(malicious_nested)

    def test_tag_validation(self):
        """Test that tags are validated."""
        # Valid tags
        valid_tags = ["automation", "web-scraping", "data_processing", "tag123"]
        metadata = WorkflowMetadataSchema(name="Test", tags=valid_tags)
        assert metadata.tags == valid_tags

        # Too many tags
        with pytest.raises((ValueError, ValidationError)):
            WorkflowMetadataSchema(name="Test", tags=["tag"] * 51)

        # Tag too long
        with pytest.raises((ValueError, ValidationError)):
            WorkflowMetadataSchema(name="Test", tags=["a" * 101])

        # Invalid characters in tag
        with pytest.raises((ValueError, ValidationError), match="Invalid tag"):
            WorkflowMetadataSchema(name="Test", tags=["tag;injection"])

    def test_empty_workflow_rejected(self):
        """Test that workflow with no nodes is rejected."""
        empty_workflow = {
            "metadata": {"name": "Empty"},
            "nodes": [],  # No nodes
            "connections": [],
            "variables": {},
        }

        with pytest.raises((ValueError, ValidationError), match="min_items"):
            validate_workflow_json(empty_workflow)

    def test_invalid_position_keys_rejected(self):
        """Test that only x and y are allowed in position dict."""
        workflow_with_invalid_position = {
            "metadata": {"name": "Test"},
            "nodes": [
                {
                    "node_id": "node_1",
                    "node_type": "test",
                    "position": {
                        "x": 100.0,
                        "y": 200.0,
                        "z": 300.0,  # Invalid key
                    },
                }
            ],
            "connections": [],
            "variables": {},
        }

        with pytest.raises((ValueError, ValidationError), match="Invalid position key"):
            validate_workflow_json(workflow_with_invalid_position)

    def test_special_characters_in_node_ids_rejected(self):
        """Test that special characters in node IDs are rejected."""
        invalid_node_ids = [
            "node;injection",
            "node'quote",
            'node"doublequote',
            "node<script>",
            "node&amp;",
            "node|pipe",
            "node\\backslash",
            "node/slash",
            "node:colon",
            "node@at",
            "node#hash",
            "node$dollar",
            "node%percent",
            "node^caret",
            "node*asterisk",
            "node+plus",
            "node=equals",
            "node[bracket]",
            "node{brace}",
        ]

        for node_id in invalid_node_ids:
            workflow = {
                "metadata": {"name": "Test"},
                "nodes": [{"node_id": node_id, "node_type": "test"}],
                "connections": [],
                "variables": {},
            }

            with pytest.raises(
                (ValueError, ValidationError), match="Invalid characters"
            ):
                validate_workflow_json(workflow)

    def test_dict_keys_must_be_strings(self):
        """Test that dictionary keys must be strings."""
        # This should be caught by JSON parsing, but test at schema level
        workflow = {
            "metadata": {"name": "Test"},
            "nodes": [
                {
                    "node_id": "node_1",
                    "node_type": "test",
                    "properties": {123: "value"},  # Integer key (invalid)
                }
            ],
            "connections": [],
            "variables": {},
        }

        with pytest.raises((ValueError, ValidationError, TypeError)):
            validate_workflow_json(workflow)


class TestNodeSchemaValidation:
    """Test individual node schema validation."""

    def test_node_id_length_limits(self):
        """Test node ID length limits."""
        # Max 128 characters
        valid_node = WorkflowNodeSchema(
            node_id="a" * 128, node_type="test", properties={}
        )
        assert valid_node.node_id == "a" * 128

        # 129 is too long
        with pytest.raises((ValueError, ValidationError)):
            WorkflowNodeSchema(node_id="a" * 129, node_type="test", properties={})

    def test_node_type_length_limits(self):
        """Test node type length limits."""
        # Max 100 characters
        valid_node = WorkflowNodeSchema(
            node_id="test", node_type="a" * 100, properties={}
        )
        assert valid_node.node_type == "a" * 100

        # 101 is too long
        with pytest.raises((ValueError, ValidationError)):
            WorkflowNodeSchema(node_id="test", node_type="a" * 101, properties={})

    def test_node_name_length_limits(self):
        """Test node name length limits."""
        # Max 255 characters
        valid_node = WorkflowNodeSchema(
            node_id="test", node_type="test", node_name="a" * 255, properties={}
        )
        assert valid_node.node_name == "a" * 255

        # 256 is too long
        with pytest.raises((ValueError, ValidationError)):
            WorkflowNodeSchema(
                node_id="test", node_type="test", node_name="a" * 256, properties={}
            )
