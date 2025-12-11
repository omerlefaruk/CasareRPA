"""
Test Instagram Profile Scraper Workflow

This test validates that the Instagram profile scraper workflow:
1. Loads correctly from the JSON file
2. Has valid node types
3. Has valid connections between nodes
4. Can be validated by the headless runner

Note: This test does NOT actually scrape Instagram - it validates
the workflow structure and can mock browser operations.
"""

import json
import pytest
from pathlib import Path
from typing import Dict, Any

from tests.integration.runners.test_headless_ui import QtHeadlessRunner


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def instagram_workflow_path() -> Path:
    """Get the path to the Instagram workflow file."""
    return Path(__file__).parent.parent / "workflows" / "instagram_profile_scraper.json"


@pytest.fixture
def instagram_workflow_data(instagram_workflow_path: Path) -> Dict[str, Any]:
    """Load the Instagram workflow data."""
    with open(instagram_workflow_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def headless_runner() -> QtHeadlessRunner:
    """Provide a headless runner instance."""
    runner = QtHeadlessRunner(qtbot=None)
    yield runner
    runner.cleanup()


# =============================================================================
# TESTS: WORKFLOW STRUCTURE VALIDATION
# =============================================================================


class TestInstagramWorkflowStructure:
    """Tests for validating the Instagram workflow structure."""

    def test_workflow_file_exists(self, instagram_workflow_path: Path) -> None:
        """Test that the workflow file exists."""
        assert (
            instagram_workflow_path.exists()
        ), f"Workflow file not found: {instagram_workflow_path}"

    def test_workflow_has_metadata(
        self, instagram_workflow_data: Dict[str, Any]
    ) -> None:
        """Test that workflow has required metadata."""
        metadata = instagram_workflow_data.get("metadata", {})

        assert "name" in metadata
        assert "description" in metadata
        assert "version" in metadata
        assert metadata["name"] == "Instagram Profile Post Metadata Scraper"

    def test_workflow_has_nodes(self, instagram_workflow_data: Dict[str, Any]) -> None:
        """Test that workflow has nodes defined."""
        nodes = instagram_workflow_data.get("nodes", {})

        assert len(nodes) > 0, "Workflow has no nodes"

        # Check for essential nodes
        node_types = [n.get("node_type") for n in nodes.values()]
        assert "StartNode" in node_types, "Missing StartNode"
        assert "EndNode" in node_types, "Missing EndNode"

    def test_workflow_has_connections(
        self, instagram_workflow_data: Dict[str, Any]
    ) -> None:
        """Test that workflow has connections defined."""
        connections = instagram_workflow_data.get("connections", [])

        assert len(connections) > 0, "Workflow has no connections"

    def test_all_node_types_are_valid(
        self, instagram_workflow_data: Dict[str, Any]
    ) -> None:
        """Test that all node types used in workflow are recognized."""
        from casare_rpa.nodes import _NODE_REGISTRY

        nodes = instagram_workflow_data.get("nodes", {})

        for node_id, node_data in nodes.items():
            node_type = node_data.get("node_type")
            assert (
                node_type in _NODE_REGISTRY
            ), f"Unknown node type: {node_type} (node_id: {node_id})"

    def test_connections_reference_existing_nodes(
        self, instagram_workflow_data: Dict[str, Any]
    ) -> None:
        """Test that all connections reference existing nodes."""
        nodes = instagram_workflow_data.get("nodes", {})
        connections = instagram_workflow_data.get("connections", [])

        node_ids = set(nodes.keys())

        for conn in connections:
            source = conn.get("source_node")
            target = conn.get("target_node")

            assert (
                source in node_ids
            ), f"Connection references non-existent source node: {source}"
            assert (
                target in node_ids
            ), f"Connection references non-existent target node: {target}"

    def test_instagram_url_is_configured(
        self, instagram_workflow_data: Dict[str, Any]
    ) -> None:
        """Test that Instagram profile URL is configured."""
        nodes = instagram_workflow_data.get("nodes", {})

        # Find GoToURLNode
        goto_node = None
        for node_data in nodes.values():
            if node_data.get("node_type") == "GoToURLNode":
                goto_node = node_data
                break

        assert goto_node is not None, "Missing GoToURLNode"

        url = goto_node.get("config", {}).get("url", "")
        assert "instagram.com" in url, f"URL doesn't point to Instagram: {url}"


# =============================================================================
# TESTS: WORKFLOW LOADING
# =============================================================================


class TestInstagramWorkflowLoading:
    """Tests for loading the Instagram workflow."""

    def test_workflow_loads_in_headless_runner(
        self, headless_runner: QtHeadlessRunner, instagram_workflow_path: Path
    ) -> None:
        """Test that workflow loads successfully in headless runner."""
        workflow = headless_runner.load_workflow(instagram_workflow_path)

        assert workflow is not None
        assert workflow.metadata.name == "Instagram Profile Post Metadata Scraper"

    def test_workflow_loads_from_dict(
        self, headless_runner: QtHeadlessRunner, instagram_workflow_data: Dict[str, Any]
    ) -> None:
        """Test loading workflow from dictionary data."""
        workflow = headless_runner.load_workflow_from_dict(instagram_workflow_data)

        assert workflow is not None
        assert len(workflow.nodes) > 0


# =============================================================================
# TESTS: WORKFLOW VALIDATION (NO EXECUTION)
# =============================================================================


class TestInstagramWorkflowValidation:
    """Tests for validating workflow without execution."""

    def test_workflow_node_count(self, instagram_workflow_data: Dict[str, Any]) -> None:
        """Test that workflow has expected number of nodes."""
        nodes = instagram_workflow_data.get("nodes", {})

        # Should have at least: Start, LaunchBrowser, GoToURL, WaitForElement,
        # Wait, ExtractText, GetAttribute, CloseBrowser, End
        assert len(nodes) >= 9, f"Expected at least 9 nodes, got {len(nodes)}"

    def test_browser_nodes_present(
        self, instagram_workflow_data: Dict[str, Any]
    ) -> None:
        """Test that required browser nodes are present."""
        nodes = instagram_workflow_data.get("nodes", {})
        node_types = [n.get("node_type") for n in nodes.values()]

        assert "LaunchBrowserNode" in node_types, "Missing LaunchBrowserNode"
        assert "GoToURLNode" in node_types, "Missing GoToURLNode"
        assert "CloseBrowserNode" in node_types, "Missing CloseBrowserNode"

    def test_data_extraction_nodes_present(
        self, instagram_workflow_data: Dict[str, Any]
    ) -> None:
        """Test that data extraction nodes are present."""
        nodes = instagram_workflow_data.get("nodes", {})
        node_types = [n.get("node_type") for n in nodes.values()]

        # Should have at least one of these for data extraction
        extraction_nodes = ["ExtractTextNode", "GetAttributeNode", "GetAllImagesNode"]
        has_extraction = any(nt in node_types for nt in extraction_nodes)

        assert has_extraction, f"Missing data extraction node. Found: {node_types}"

    def test_wait_nodes_present(self, instagram_workflow_data: Dict[str, Any]) -> None:
        """Test that wait nodes are present for proper timing."""
        nodes = instagram_workflow_data.get("nodes", {})
        node_types = [n.get("node_type") for n in nodes.values()]

        # Should have WaitForElementNode or WaitNode for proper page loading
        wait_nodes = ["WaitNode", "WaitForElementNode", "WaitForNavigationNode"]
        has_wait = any(nt in node_types for nt in wait_nodes)

        assert has_wait, "Missing wait node for page loading synchronization"


# =============================================================================
# TESTS: EXECUTION FLOW
# =============================================================================


class TestInstagramWorkflowFlow:
    """Tests for workflow execution flow."""

    def test_start_to_end_path_exists(
        self, instagram_workflow_data: Dict[str, Any]
    ) -> None:
        """Test that there's a valid path from Start to End node."""
        nodes = instagram_workflow_data.get("nodes", {})
        connections = instagram_workflow_data.get("connections", [])

        # Build adjacency list
        adjacency: Dict[str, list] = {node_id: [] for node_id in nodes}
        for conn in connections:
            if conn.get("source_port") == "exec_out":
                source = conn.get("source_node")
                target = conn.get("target_node")
                if source in adjacency:
                    adjacency[source].append(target)

        # Find start and end nodes
        start_node = None
        end_node = None
        for node_id, node_data in nodes.items():
            if node_data.get("node_type") == "StartNode":
                start_node = node_id
            elif node_data.get("node_type") == "EndNode":
                end_node = node_id

        assert start_node is not None, "Missing StartNode"
        assert end_node is not None, "Missing EndNode"

        # BFS to check reachability
        visited = set()
        queue = [start_node]

        while queue:
            current = queue.pop(0)
            if current == end_node:
                return  # Found path - test passes

            if current in visited:
                continue
            visited.add(current)

            queue.extend(adjacency.get(current, []))

        pytest.fail("No execution path from StartNode to EndNode")


# =============================================================================
# MAIN
# =============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
