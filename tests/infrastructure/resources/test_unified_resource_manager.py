"""Tests for UnifiedResourceManager workflow analysis."""

import pytest

from casare_rpa.infrastructure.resources.unified_resource_manager import (
    UnifiedResourceManager,
)


class TestAnalyzeWorkflowNeeds:
    """Test analyze_workflow_needs method."""

    @pytest.fixture
    def manager(self):
        """Create a resource manager instance."""
        return UnifiedResourceManager()

    def test_handles_dict_format_nodes(self, manager):
        """Test dict-format nodes (keyed by node_id)."""
        workflow = {
            "nodes": {
                "node1": {"node_type": "OpenBrowserNode"},
                "node2": {"node_type": "NavigateNode"},
            }
        }

        needs = manager.analyze_workflow_needs(workflow)

        assert needs["needs_browser"] is True
        assert needs["needs_database"] is False
        assert needs["needs_http"] is False

    def test_handles_list_format_nodes(self, manager):
        """Test list-format nodes."""
        workflow = {
            "nodes": [
                {"node_type": "OpenBrowserNode"},
                {"node_type": "HTTPRequestNode"},
            ]
        }

        needs = manager.analyze_workflow_needs(workflow)

        assert needs["needs_browser"] is True
        assert needs["needs_http"] is True
        assert needs["needs_database"] is False

    def test_handles_legacy_type_field(self, manager):
        """Test legacy 'type' field name (backward compatibility)."""
        workflow = {
            "nodes": {
                "node1": {"type": "OpenBrowserNode"},  # Legacy format
                "node2": {"type": "SQLQueryNode"},
            }
        }

        needs = manager.analyze_workflow_needs(workflow)

        assert needs["needs_browser"] is True
        assert needs["needs_database"] is True

    def test_handles_mixed_field_names(self, manager):
        """Test mix of node_type and type fields."""
        workflow = {
            "nodes": {
                "node1": {"node_type": "OpenBrowserNode"},
                "node2": {"type": "HTTPRequestNode"},  # Legacy
            }
        }

        needs = manager.analyze_workflow_needs(workflow)

        assert needs["needs_browser"] is True
        assert needs["needs_http"] is True

    def test_handles_string_json_input(self, manager):
        """Test JSON string input (from API)."""
        workflow_str = '{"nodes": {"node1": {"node_type": "OpenBrowserNode"}}}'

        needs = manager.analyze_workflow_needs(workflow_str)

        assert needs["needs_browser"] is True

    def test_handles_empty_nodes_dict(self, manager):
        """Test empty nodes dict."""
        workflow = {"nodes": {}}

        needs = manager.analyze_workflow_needs(workflow)

        assert needs["needs_browser"] is False
        assert needs["needs_database"] is False
        assert needs["needs_http"] is False

    def test_handles_empty_nodes_list(self, manager):
        """Test empty nodes list."""
        workflow = {"nodes": []}

        needs = manager.analyze_workflow_needs(workflow)

        assert needs["needs_browser"] is False
        assert needs["needs_database"] is False
        assert needs["needs_http"] is False

    def test_handles_none_nodes(self, manager):
        """Test None nodes value."""
        workflow = {"nodes": None}

        needs = manager.analyze_workflow_needs(workflow)

        assert needs["needs_browser"] is False
        assert needs["needs_database"] is False
        assert needs["needs_http"] is False

    def test_handles_missing_nodes_key(self, manager):
        """Test missing nodes key entirely."""
        workflow = {"name": "test"}

        needs = manager.analyze_workflow_needs(workflow)

        assert needs["needs_browser"] is False
        assert needs["needs_database"] is False
        assert needs["needs_http"] is False

    def test_detects_all_resource_types(self, manager):
        """Test detection of all resource types."""
        workflow = {
            "nodes": {
                "n1": {"node_type": "OpenBrowserNode"},
                "n2": {"node_type": "SQLQueryNode"},
                "n3": {"node_type": "HTTPRequestNode"},
            }
        }

        needs = manager.analyze_workflow_needs(workflow)

        assert needs["needs_browser"] is True
        assert needs["needs_database"] is True
        assert needs["needs_http"] is True

    def test_invalid_json_returns_conservative_defaults(self, manager):
        """Test invalid JSON returns conservative defaults (browser=True)."""
        invalid_json = "not valid json {"

        needs = manager.analyze_workflow_needs(invalid_json)

        # Conservative default: assume browser needed
        assert needs["needs_browser"] is True
        assert needs["needs_database"] is False
        assert needs["needs_http"] is False
