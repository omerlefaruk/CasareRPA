"""Tests for WorkflowBuilder tool."""

import json
import pytest
from pathlib import Path
from casare_rpa.tools.workflow_builder import WorkflowBuilder


class TestWorkflowBuilder:
    @pytest.fixture
    def builder(self):
        return WorkflowBuilder()

    def test_add_node(self, builder):
        """Test adding a node."""
        node_id = builder.add_node("ClickElementNode", {"selector": "#test"}, (100, 100))

        assert node_id in builder.workflow_data["nodes"]
        node = builder.workflow_data["nodes"][node_id]
        assert node["node_type"] == "ClickElementNode"
        assert node["config"]["selector"] == "#test"
        assert node["position"] == [100, 100]

    def test_connect_nodes(self, builder):
        """Test connecting two nodes."""
        n1 = builder.add_node("StartNode")
        n2 = builder.add_node("ClickElementNode")

        builder.connect(n1, "exec_out", n2, "exec_in")

        assert len(builder.workflow_data["connections"]) == 1
        conn = builder.workflow_data["connections"][0]
        assert conn["source_node"] == n1
        assert conn["target_node"] == n2

    def test_inject_script_escaping(self, builder):
        """Test safe script injection with newline escaping."""
        n1 = builder.add_node("BrowserRunScriptNode")

        # Script with newlines
        script = "import os\nprint('hello')\n"

        builder.inject_script(n1, script)

        config = builder.workflow_data["nodes"][n1]["config"]
        # The internal storage should have the string.
        # The key is that when saved to JSON, it should be escaped properly.
        assert config["script"] == script

        # Verify JSON dump behavior
        json_str = json.dumps(builder.workflow_data)
        # In JSON string, newline becomes \n
        assert r"import os\nprint('hello')\n" in json_str

    def test_circular_dependency_prevention(self, builder):
        """Test that circular dependencies are blocked."""
        # Create a loop: n1 -> n2 -> n1
        n1 = builder.add_node("IfNode")
        n2 = builder.add_node("WaitNode")

        builder.connect(n1, "true", n2, "exec_in")

        # This connection creates a cycle and should fail
        # Note: IfNode 'true' is an exec port, WaitNode 'exec_in' is exec input
        with pytest.raises(ValueError, match="circular dependency"):
            builder.connect(n2, "exec_out", n1, "exec_in")

    def test_delete_node(self, builder):
        """Test deleting a node cleans up connections."""
        n1 = builder.add_node("StartNode")
        n2 = builder.add_node("ClickElementNode")
        builder.connect(n1, "exec_out", n2, "exec_in")

        builder.delete_node(n2)

        assert n2 not in builder.workflow_data["nodes"]
        assert len(builder.workflow_data["connections"]) == 0

    def test_save_workflow(self, builder, tmp_path):
        """Test saving workflow to file."""
        n1 = builder.add_node("StartNode")
        path = tmp_path / "test_workflow.json"

        builder.save(str(path))

        assert path.exists()
        with open(path) as f:
            data = json.load(f)
            assert n1 in data["nodes"]
