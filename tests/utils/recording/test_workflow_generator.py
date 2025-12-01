"""Tests for Recording Workflow Generator."""

import pytest
from datetime import datetime

from casare_rpa.utils.recording.browser_recorder import (
    BrowserRecordedAction,
    BrowserActionType,
    ElementInfo,
)
from casare_rpa.utils.recording.workflow_generator import RecordingWorkflowGenerator


class TestRecordingWorkflowGenerator:
    """Tests for RecordingWorkflowGenerator class."""

    def test_init_default_name(self):
        """Test initialization with default name."""
        generator = RecordingWorkflowGenerator()
        assert generator.workflow_name is None

    def test_init_custom_name(self):
        """Test initialization with custom name."""
        generator = RecordingWorkflowGenerator(workflow_name="My Workflow")
        assert generator.workflow_name == "My Workflow"

    def test_generate_empty_actions(self):
        """Test generating workflow from empty actions."""
        generator = RecordingWorkflowGenerator()
        workflow = generator.generate([])

        assert "name" in workflow
        assert "nodes" in workflow
        assert "connections" in workflow
        assert len(workflow["nodes"]) == 2  # Start and End

    def test_generate_with_actions(self):
        """Test generating workflow from actions."""
        generator = RecordingWorkflowGenerator(workflow_name="Test Workflow")

        actions = [
            BrowserRecordedAction(
                action_type=BrowserActionType.NAVIGATE,
                url="https://example.com",
            ),
            BrowserRecordedAction(
                action_type=BrowserActionType.CLICK,
                selector="#submit",
            ),
        ]

        workflow = generator.generate(actions)

        assert workflow["name"] == "Test Workflow"
        # Start + 2 actions + End = 4 nodes
        assert len(workflow["nodes"]) == 4
        # 3 connections (sequential)
        assert len(workflow["connections"]) == 3

    def test_generate_without_start_end(self):
        """Test generating workflow without start/end nodes."""
        generator = RecordingWorkflowGenerator()

        actions = [
            BrowserRecordedAction(
                action_type=BrowserActionType.CLICK,
                selector="#btn",
            ),
        ]

        workflow = generator.generate(actions, include_start_end=False)

        assert len(workflow["nodes"]) == 1
        assert workflow["nodes"][0]["type"] == "ClickElementNode"


class TestNodeTypeMapping:
    """Tests for action to node type mapping."""

    def test_navigate_to_goto_url(self):
        """Test navigation maps to GoToURLNode."""
        generator = RecordingWorkflowGenerator()

        actions = [
            BrowserRecordedAction(
                action_type=BrowserActionType.NAVIGATE,
                url="https://example.com",
            ),
        ]

        workflow = generator.generate(actions, include_start_end=False)

        assert workflow["nodes"][0]["type"] == "GoToURLNode"
        assert workflow["nodes"][0]["parameters"]["url"] == "https://example.com"

    def test_click_to_click_element(self):
        """Test click maps to ClickElementNode."""
        generator = RecordingWorkflowGenerator()

        actions = [
            BrowserRecordedAction(
                action_type=BrowserActionType.CLICK,
                selector="#btn",
                coordinates=(100, 200),
            ),
        ]

        workflow = generator.generate(actions, include_start_end=False)

        node = workflow["nodes"][0]
        assert node["type"] == "ClickElementNode"
        assert node["parameters"]["selector"] == "#btn"
        assert node["parameters"]["x"] == 100
        assert node["parameters"]["y"] == 200

    def test_type_to_type_text(self):
        """Test type maps to TypeTextNode."""
        generator = RecordingWorkflowGenerator()

        actions = [
            BrowserRecordedAction(
                action_type=BrowserActionType.TYPE,
                selector="#input",
                value="Hello World",
            ),
        ]

        workflow = generator.generate(actions, include_start_end=False)

        node = workflow["nodes"][0]
        assert node["type"] == "TypeTextNode"
        assert node["parameters"]["selector"] == "#input"
        assert node["parameters"]["text"] == "Hello World"

    def test_select_to_select_dropdown(self):
        """Test select maps to SelectDropdownNode."""
        generator = RecordingWorkflowGenerator()

        actions = [
            BrowserRecordedAction(
                action_type=BrowserActionType.SELECT,
                selector="#country",
                value="US",
            ),
        ]

        workflow = generator.generate(actions, include_start_end=False)

        node = workflow["nodes"][0]
        assert node["type"] == "SelectDropdownNode"
        assert node["parameters"]["value"] == "US"

    def test_wait_to_wait_for_element(self):
        """Test wait maps to WaitForElementNode."""
        generator = RecordingWorkflowGenerator()

        actions = [
            BrowserRecordedAction(
                action_type=BrowserActionType.WAIT,
                selector="#loading",
                value="5000",
            ),
        ]

        workflow = generator.generate(actions, include_start_end=False)

        node = workflow["nodes"][0]
        assert node["type"] == "WaitForElementNode"
        assert node["parameters"]["selector"] == "#loading"
        assert node["parameters"]["timeout"] == 5000

    def test_screenshot_to_screenshot_node(self):
        """Test screenshot maps to ScreenshotNode."""
        generator = RecordingWorkflowGenerator()

        actions = [
            BrowserRecordedAction(
                action_type=BrowserActionType.SCREENSHOT,
                value="test.png",
            ),
        ]

        workflow = generator.generate(actions, include_start_end=False)

        node = workflow["nodes"][0]
        assert node["type"] == "ScreenshotNode"
        assert node["parameters"]["filename"] == "test.png"


class TestWorkflowStructure:
    """Tests for workflow structure."""

    def test_workflow_has_required_fields(self):
        """Test workflow has all required fields."""
        generator = RecordingWorkflowGenerator()
        workflow = generator.generate([])

        required_fields = [
            "name",
            "description",
            "version",
            "created_at",
            "nodes",
            "connections",
            "variables",
            "metadata",
        ]

        for field in required_fields:
            assert field in workflow

    def test_nodes_have_required_fields(self):
        """Test nodes have required fields."""
        generator = RecordingWorkflowGenerator()

        actions = [
            BrowserRecordedAction(
                action_type=BrowserActionType.CLICK,
                selector="#btn",
            ),
        ]

        workflow = generator.generate(actions, include_start_end=False)
        node = workflow["nodes"][0]

        assert "id" in node
        assert "type" in node
        assert "name" in node
        assert "position" in node
        assert "parameters" in node

    def test_connections_sequential(self):
        """Test connections are sequential."""
        generator = RecordingWorkflowGenerator()

        actions = [
            BrowserRecordedAction(action_type=BrowserActionType.CLICK, selector="#a"),
            BrowserRecordedAction(action_type=BrowserActionType.CLICK, selector="#b"),
            BrowserRecordedAction(action_type=BrowserActionType.CLICK, selector="#c"),
        ]

        workflow = generator.generate(actions)

        # With start/end: Start -> Click1 -> Click2 -> Click3 -> End
        # That's 4 connections
        assert len(workflow["connections"]) == 4

        # Each connection should link consecutive nodes
        for conn in workflow["connections"]:
            assert "from_node" in conn
            assert "to_node" in conn
            assert conn["from_port"] == "exec_out"
            assert conn["to_port"] == "exec_in"

    def test_node_positions_offset(self):
        """Test node positions are offset for visibility."""
        generator = RecordingWorkflowGenerator()

        actions = [
            BrowserRecordedAction(action_type=BrowserActionType.CLICK, selector="#a"),
            BrowserRecordedAction(action_type=BrowserActionType.CLICK, selector="#b"),
        ]

        workflow = generator.generate(actions, include_start_end=False)

        pos1 = workflow["nodes"][0]["position"]
        pos2 = workflow["nodes"][1]["position"]

        # Second node should be to the right of first
        assert pos2["x"] > pos1["x"]


class TestWorkflowNaming:
    """Tests for workflow name generation."""

    def test_custom_name_used(self):
        """Test custom name is used."""
        generator = RecordingWorkflowGenerator(workflow_name="My Test")
        workflow = generator.generate([])
        assert workflow["name"] == "My Test"

    def test_auto_name_from_navigation(self):
        """Test auto-generated name from first navigation."""
        generator = RecordingWorkflowGenerator()

        actions = [
            BrowserRecordedAction(
                action_type=BrowserActionType.NAVIGATE,
                url="https://example.com/page",
            ),
        ]

        workflow = generator.generate(actions)

        assert "example.com" in workflow["name"]

    def test_auto_name_fallback(self):
        """Test fallback name when no navigation."""
        generator = RecordingWorkflowGenerator()

        actions = [
            BrowserRecordedAction(action_type=BrowserActionType.CLICK, selector="#btn"),
        ]

        workflow = generator.generate(actions)

        assert "Recorded_Workflow" in workflow["name"]


class TestMergeWorkflows:
    """Tests for merging workflows."""

    def test_merge_empty_list(self):
        """Test merging empty list returns empty workflow."""
        result = RecordingWorkflowGenerator.merge_workflows([])

        assert "nodes" in result
        assert len(result["nodes"]) == 2  # Start and End

    def test_merge_single_workflow(self):
        """Test merging single workflow returns same workflow."""
        generator = RecordingWorkflowGenerator()
        workflow = generator.generate(
            [BrowserRecordedAction(action_type=BrowserActionType.CLICK, selector="#a")]
        )

        result = RecordingWorkflowGenerator.merge_workflows([workflow])

        assert result == workflow

    def test_merge_multiple_workflows(self):
        """Test merging multiple workflows."""
        generator = RecordingWorkflowGenerator()

        workflow1 = generator.generate(
            [BrowserRecordedAction(action_type=BrowserActionType.CLICK, selector="#a")]
        )
        workflow2 = generator.generate(
            [BrowserRecordedAction(action_type=BrowserActionType.CLICK, selector="#b")]
        )

        result = RecordingWorkflowGenerator.merge_workflows(
            [workflow1, workflow2], name="Merged"
        )

        assert result["name"] == "Merged"
        assert result["metadata"]["merged_count"] == 2
