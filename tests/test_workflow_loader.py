"""
Tests for utils/workflow_loader.py - Workflow loading and deserialization.
"""

import pytest
from typing import Dict, Any


class TestNodeTypeMap:
    """Test NODE_TYPE_MAP registry."""

    def test_node_type_map_exists(self):
        """Test that NODE_TYPE_MAP is defined."""
        from casare_rpa.utils.workflow_loader import NODE_TYPE_MAP

        assert isinstance(NODE_TYPE_MAP, dict)
        assert len(NODE_TYPE_MAP) > 0

    def test_basic_nodes_registered(self):
        """Test that basic nodes are in the type map."""
        from casare_rpa.utils.workflow_loader import NODE_TYPE_MAP
        from casare_rpa.nodes.basic_nodes import StartNode, EndNode

        assert "StartNode" in NODE_TYPE_MAP
        assert "EndNode" in NODE_TYPE_MAP
        assert NODE_TYPE_MAP["StartNode"] == StartNode
        assert NODE_TYPE_MAP["EndNode"] == EndNode

    def test_control_flow_nodes_registered(self):
        """Test that control flow nodes are registered."""
        from casare_rpa.utils.workflow_loader import NODE_TYPE_MAP

        assert "IfNode" in NODE_TYPE_MAP
        assert "ForLoopNode" in NODE_TYPE_MAP
        assert "WhileLoopNode" in NODE_TYPE_MAP

    def test_browser_nodes_registered(self):
        """Test that browser nodes are registered."""
        from casare_rpa.utils.workflow_loader import NODE_TYPE_MAP

        assert "LaunchBrowserNode" in NODE_TYPE_MAP
        assert "CloseBrowserNode" in NODE_TYPE_MAP
        assert "GoToURLNode" in NODE_TYPE_MAP

    def test_variable_nodes_registered(self):
        """Test that variable nodes are registered."""
        from casare_rpa.utils.workflow_loader import NODE_TYPE_MAP

        assert "SetVariableNode" in NODE_TYPE_MAP
        assert "GetVariableNode" in NODE_TYPE_MAP
        assert "IncrementVariableNode" in NODE_TYPE_MAP

    def test_desktop_nodes_registered(self):
        """Test that desktop nodes are registered."""
        from casare_rpa.utils.workflow_loader import NODE_TYPE_MAP

        assert "LaunchApplicationNode" in NODE_TYPE_MAP
        assert "CloseApplicationNode" in NODE_TYPE_MAP
        assert "ActivateWindowNode" in NODE_TYPE_MAP
        assert "GetWindowListNode" in NODE_TYPE_MAP


class TestLoadWorkflowFromDict:
    """Test load_workflow_from_dict function."""

    def create_minimal_workflow(self) -> Dict[str, Any]:
        """Create a minimal workflow dictionary for testing."""
        return {
            "metadata": {
                "name": "Test Workflow",
                "description": "A test workflow",
                "version": "1.0.0"
            },
            "nodes": {},
            "connections": [],
            "variables": {},
            "settings": {}
        }

    def test_load_empty_workflow(self):
        """Test loading an empty workflow."""
        from casare_rpa.utils.workflow_loader import load_workflow_from_dict

        workflow_data = self.create_minimal_workflow()
        workflow = load_workflow_from_dict(workflow_data)

        assert workflow is not None
        assert workflow.metadata.name == "Test Workflow"

    def test_load_workflow_with_start_node(self):
        """Test loading workflow that already has a StartNode."""
        from casare_rpa.utils.workflow_loader import load_workflow_from_dict

        workflow_data = self.create_minimal_workflow()
        workflow_data["nodes"] = {
            "start_1": {
                "node_type": "StartNode",
                "config": {}
            }
        }

        workflow = load_workflow_from_dict(workflow_data)

        # Should NOT create auto-start node
        assert "__auto_start__" not in workflow.nodes
        assert "start_1" in workflow.nodes

    def test_load_workflow_without_start_node_adds_auto_start(self):
        """Test that workflows without StartNode get auto-start added."""
        from casare_rpa.utils.workflow_loader import load_workflow_from_dict

        workflow_data = self.create_minimal_workflow()
        workflow_data["nodes"] = {
            "end_1": {
                "node_type": "EndNode",
                "config": {}
            }
        }

        workflow = load_workflow_from_dict(workflow_data)

        # Should create auto-start node
        assert "__auto_start__" in workflow.nodes

    def test_load_workflow_with_node_config(self):
        """Test loading workflow with node configuration."""
        from casare_rpa.utils.workflow_loader import load_workflow_from_dict

        workflow_data = self.create_minimal_workflow()
        workflow_data["nodes"] = {
            "start_1": {
                "node_type": "StartNode",
                "config": {}
            },
            "set_var_1": {
                "node_type": "SetVariableNode",
                "config": {
                    "variable_name": "test_var",
                    "value": "test_value"
                }
            }
        }

        workflow = load_workflow_from_dict(workflow_data)

        assert "set_var_1" in workflow.nodes
        node = workflow.nodes["set_var_1"]
        assert node.config.get("variable_name") == "test_var"

    def test_load_workflow_with_connections(self):
        """Test loading workflow with node connections."""
        from casare_rpa.utils.workflow_loader import load_workflow_from_dict

        workflow_data = self.create_minimal_workflow()
        workflow_data["nodes"] = {
            "start_1": {
                "node_type": "StartNode",
                "config": {}
            },
            "end_1": {
                "node_type": "EndNode",
                "config": {}
            }
        }
        workflow_data["connections"] = [
            {
                "source_node": "start_1",
                "source_port": "exec_out",
                "target_node": "end_1",
                "target_port": "exec_in"
            }
        ]

        workflow = load_workflow_from_dict(workflow_data)

        assert len(workflow.connections) == 1
        conn = workflow.connections[0]
        assert conn.source_node == "start_1"
        assert conn.target_node == "end_1"

    def test_load_workflow_with_variables(self):
        """Test loading workflow with predefined variables."""
        from casare_rpa.utils.workflow_loader import load_workflow_from_dict

        workflow_data = self.create_minimal_workflow()
        workflow_data["variables"] = {
            "url": "https://example.com",
            "timeout": 30
        }

        workflow = load_workflow_from_dict(workflow_data)

        assert workflow.variables["url"] == "https://example.com"
        assert workflow.variables["timeout"] == 30

    def test_load_workflow_unknown_node_type(self):
        """Test that unknown node types are skipped with warning."""
        from casare_rpa.utils.workflow_loader import load_workflow_from_dict

        workflow_data = self.create_minimal_workflow()
        workflow_data["nodes"] = {
            "unknown_1": {
                "node_type": "NonExistentNode",
                "config": {}
            }
        }

        workflow = load_workflow_from_dict(workflow_data)

        # Unknown node should be skipped
        assert "unknown_1" not in workflow.nodes

    def test_load_workflow_metadata(self):
        """Test that workflow metadata is correctly loaded."""
        from casare_rpa.utils.workflow_loader import load_workflow_from_dict

        workflow_data = {
            "metadata": {
                "name": "My Workflow",
                "description": "Description here",
                "version": "2.0.0",
                "author": "Test Author"
            },
            "nodes": {},
            "connections": [],
            "variables": {},
            "settings": {}
        }

        workflow = load_workflow_from_dict(workflow_data)

        assert workflow.metadata.name == "My Workflow"
        assert workflow.metadata.description == "Description here"
        assert workflow.metadata.version == "2.0.0"

    def test_auto_connect_start_to_entry_points(self):
        """Test that auto-start connects to nodes without exec_in connections."""
        from casare_rpa.utils.workflow_loader import load_workflow_from_dict

        workflow_data = self.create_minimal_workflow()
        workflow_data["nodes"] = {
            "set_var_1": {
                "node_type": "SetVariableNode",
                "config": {"variable_name": "x", "value": "1"}
            },
            "end_1": {
                "node_type": "EndNode",
                "config": {}
            }
        }
        # Connection from set_var to end, but nothing to set_var
        workflow_data["connections"] = [
            {
                "source_node": "set_var_1",
                "source_port": "exec_out",
                "target_node": "end_1",
                "target_port": "exec_in"
            }
        ]

        workflow = load_workflow_from_dict(workflow_data)

        # Auto-start should be created and connected to set_var_1
        assert "__auto_start__" in workflow.nodes

        # Find auto-start connection
        auto_connections = [
            c for c in workflow.connections
            if c.source_node == "__auto_start__"
        ]
        assert len(auto_connections) == 1
        assert auto_connections[0].target_node == "set_var_1"


class TestWorkflowIntegration:
    """Integration tests for workflow loading."""

    def test_load_workflow_creates_valid_workflow(self):
        """Test loading workflow creates valid workflow object."""
        from casare_rpa.utils.workflow_loader import load_workflow_from_dict

        workflow_data = {
            "metadata": {"name": "Simple Test"},
            "nodes": {
                "start_1": {"node_type": "StartNode", "config": {}},
                "set_var_1": {
                    "node_type": "SetVariableNode",
                    "config": {"variable_name": "result", "value": "success"}
                },
                "end_1": {"node_type": "EndNode", "config": {}}
            },
            "connections": [
                {"source_node": "start_1", "source_port": "exec_out",
                 "target_node": "set_var_1", "target_port": "exec_in"},
                {"source_node": "set_var_1", "source_port": "exec_out",
                 "target_node": "end_1", "target_port": "exec_in"}
            ],
            "variables": {},
            "settings": {}
        }

        workflow = load_workflow_from_dict(workflow_data)

        # Verify workflow was loaded correctly
        assert workflow is not None
        assert workflow.metadata.name == "Simple Test"
        assert "start_1" in workflow.nodes
        assert "set_var_1" in workflow.nodes
        assert "end_1" in workflow.nodes
        assert len(workflow.connections) == 2
