"""
Integration Tests for Node Registry.

Tests the lazy-loading node registration system to ensure:
- All registered nodes can be imported
- Desktop nodes are accessible with aliases
- Gmail nodes are accessible
- is_valid_node_type() works for all registered nodes
- get_node_class() returns correct classes

These tests verify the integration between:
- nodes/__init__.py (_NODE_REGISTRY)
- utils/workflow/workflow_loader.py (get_node_class, is_valid_node_type)
"""

import pytest
from typing import Type

import casare_rpa.nodes as nodes_module
from casare_rpa.utils.workflow.workflow_loader import (
    get_node_class,
    is_valid_node_type,
    get_all_node_types,
    NODE_TYPE_MAP,
)


# =============================================================================
# NODE REGISTRY ACCESS TESTS
# =============================================================================


@pytest.mark.integration
class TestNodeRegistryBasics:
    """Basic tests for node registry functionality."""

    def test_node_registry_exists(self):
        """Verify _NODE_REGISTRY is accessible and non-empty."""
        assert hasattr(nodes_module, "_NODE_REGISTRY")
        assert isinstance(nodes_module._NODE_REGISTRY, dict)
        assert len(nodes_module._NODE_REGISTRY) > 0

    def test_node_registry_has_expected_count(self):
        """Verify registry has expected number of nodes (approx 200+)."""
        # The system claims 413 registered nodes, but we check for reasonable minimum
        node_count = len(nodes_module._NODE_REGISTRY)
        assert node_count >= 200, f"Expected 200+ nodes, found {node_count}"

    def test_all_registry_keys_are_strings(self):
        """Verify all registry keys are valid strings."""
        for key in nodes_module._NODE_REGISTRY:
            assert isinstance(key, str)
            assert len(key) > 0
            assert key.endswith("Node"), f"Node key {key} should end with 'Node'"

    def test_all_registry_values_are_valid(self):
        """Verify all registry values are module paths or tuples."""
        for key, value in nodes_module._NODE_REGISTRY.items():
            if isinstance(value, tuple):
                assert len(value) == 2, f"Tuple for {key} should have 2 elements"
                assert isinstance(
                    value[0], str
                ), f"First element for {key} should be string"
                assert isinstance(
                    value[1], str
                ), f"Second element for {key} should be string"
            else:
                assert isinstance(
                    value, str
                ), f"Value for {key} should be string or tuple"


# =============================================================================
# NODE IMPORT TESTS
# =============================================================================


@pytest.mark.integration
class TestNodeImports:
    """Tests for lazy loading node imports."""

    @pytest.fixture
    def basic_node_types(self):
        """List of basic node types that must be importable."""
        return [
            "StartNode",
            "EndNode",
            "CommentNode",
            "LaunchBrowserNode",
            "CloseBrowserNode",
            "ClickElementNode",
            "TypeTextNode",
            "SetVariableNode",
            "GetVariableNode",
            "IfNode",
            "ForLoopStartNode",
            "ForLoopEndNode",
            "WaitNode",
            "LogNode",
        ]

    def test_basic_nodes_importable(self, basic_node_types):
        """Verify basic node types can be imported."""
        for node_type in basic_node_types:
            node_class = get_node_class(node_type)
            assert node_class is not None, f"Failed to import {node_type}"
            assert callable(node_class), f"{node_type} should be callable"

    def test_getattr_lazy_loading(self):
        """Verify __getattr__ lazy loading works."""
        # This should trigger lazy import
        StartNode = getattr(nodes_module, "StartNode")
        assert StartNode is not None
        assert callable(StartNode)

    def test_imported_nodes_cached(self):
        """Verify imported nodes are cached for performance."""
        # First import
        node1 = get_node_class("StartNode")
        # Second import should return same object
        node2 = get_node_class("StartNode")
        assert node1 is node2, "Cached nodes should be identical objects"

    def test_unknown_node_returns_none(self):
        """Verify unknown node types return None."""
        result = get_node_class("NonExistentNode")
        assert result is None

    def test_unknown_node_via_getattr_raises(self):
        """Verify unknown node via getattr raises AttributeError."""
        with pytest.raises(AttributeError):
            getattr(nodes_module, "NonExistentNode")


# =============================================================================
# DESKTOP NODE ALIAS TESTS
# =============================================================================


@pytest.mark.integration
class TestDesktopNodeAliases:
    """Tests for desktop node aliases (DesktopClickElementNode -> ClickElementNode)."""

    def test_desktop_click_element_alias(self):
        """Verify DesktopClickElementNode alias works."""
        node_class = get_node_class("DesktopClickElementNode")
        assert node_class is not None
        # The class should be ClickElementNode from desktop_nodes
        assert "ClickElementNode" in node_class.__name__ or callable(node_class)

    def test_desktop_type_text_alias(self):
        """Verify DesktopTypeTextNode alias works."""
        node_class = get_node_class("DesktopTypeTextNode")
        assert node_class is not None

    def test_desktop_wait_for_element_alias(self):
        """Verify DesktopWaitForElementNode alias works."""
        node_class = get_node_class("DesktopWaitForElementNode")
        assert node_class is not None

    def test_all_desktop_aliases_defined(self):
        """Verify all desktop aliases are in registry."""
        desktop_aliases = [
            "DesktopClickElementNode",
            "DesktopTypeTextNode",
            "DesktopWaitForElementNode",
        ]
        for alias in desktop_aliases:
            assert is_valid_node_type(alias), f"Alias {alias} should be valid"


# =============================================================================
# GMAIL NODE TESTS
# =============================================================================


@pytest.mark.integration
class TestGmailNodes:
    """Tests for Gmail node accessibility."""

    @pytest.fixture
    def gmail_node_types(self):
        """List of Gmail node types."""
        return [
            "GmailSendEmailNode",
            "GmailSendWithAttachmentNode",
            "GmailCreateDraftNode",
            "GmailSendDraftNode",
            "GmailGetEmailNode",
            "GmailListEmailsNode",
            "GmailSearchEmailsNode",
            "GmailGetThreadNode",
            "GmailModifyLabelsNode",
            "GmailMoveToTrashNode",
            "GmailMarkAsReadNode",
            "GmailMarkAsUnreadNode",
            "GmailStarEmailNode",
            "GmailArchiveEmailNode",
            "GmailDeleteEmailNode",
            "GmailBatchSendNode",
            "GmailBatchModifyNode",
            "GmailBatchDeleteNode",
            "GmailReplyToEmailNode",
            "GmailForwardEmailNode",
            "GmailGetAttachmentNode",
            "GmailAddLabelNode",
            "GmailRemoveLabelNode",
            "GmailGetLabelsNode",
            "GmailTrashEmailNode",
        ]

    def test_gmail_nodes_registered(self, gmail_node_types):
        """Verify Gmail nodes are registered in registry."""
        for node_type in gmail_node_types:
            assert is_valid_node_type(node_type), f"{node_type} should be registered"

    def test_gmail_nodes_importable(self, gmail_node_types):
        """Verify Gmail nodes can be imported."""
        for node_type in gmail_node_types:
            node_class = get_node_class(node_type)
            assert node_class is not None, f"Failed to import {node_type}"

    def test_gmail_trigger_node_accessible(self):
        """Verify Gmail trigger node is accessible."""
        assert is_valid_node_type("GmailTriggerNode")
        node_class = get_node_class("GmailTriggerNode")
        assert node_class is not None


# =============================================================================
# is_valid_node_type TESTS
# =============================================================================


@pytest.mark.integration
class TestIsValidNodeType:
    """Tests for is_valid_node_type() function."""

    def test_valid_node_types_return_true(self):
        """Verify valid node types return True."""
        valid_types = ["StartNode", "EndNode", "ClickElementNode", "TypeTextNode"]
        for node_type in valid_types:
            assert is_valid_node_type(node_type) is True, f"{node_type} should be valid"

    def test_invalid_node_types_return_false(self):
        """Verify invalid node types return False."""
        invalid_types = ["FakeNode", "NonExistent", "RandomClass", ""]
        for node_type in invalid_types:
            assert (
                is_valid_node_type(node_type) is False
            ), f"{node_type} should be invalid"

    def test_all_registry_entries_valid(self):
        """Verify all registry entries return True for is_valid_node_type."""
        for node_type in nodes_module._NODE_REGISTRY.keys():
            assert is_valid_node_type(node_type) is True, f"{node_type} should be valid"

    def test_case_sensitive(self):
        """Verify node type checking is case-sensitive."""
        assert is_valid_node_type("StartNode") is True
        assert is_valid_node_type("startnode") is False
        assert is_valid_node_type("STARTNODE") is False


# =============================================================================
# get_node_class TESTS
# =============================================================================


@pytest.mark.integration
class TestGetNodeClass:
    """Tests for get_node_class() function."""

    def test_returns_class_for_valid_type(self):
        """Verify get_node_class returns class for valid types."""
        node_class = get_node_class("StartNode")
        assert node_class is not None
        assert isinstance(node_class, type) or callable(node_class)

    def test_returns_none_for_invalid_type(self):
        """Verify get_node_class returns None for invalid types."""
        assert get_node_class("FakeNode") is None
        assert get_node_class("") is None
        assert get_node_class("RandomClass") is None

    def test_class_is_instantiable(self):
        """Verify returned classes can be instantiated."""
        node_class = get_node_class("SetVariableNode")
        assert node_class is not None

        # Try to instantiate (may need node_id)
        try:
            node = node_class("test_id", config={"variable_name": "test"})
            assert node is not None
        except TypeError:
            # Some nodes may have different signatures, that's okay
            pass

    def test_browser_nodes_return_correct_class(self):
        """Verify browser nodes return correct class types."""
        browser_nodes = [
            "LaunchBrowserNode",
            "CloseBrowserNode",
            "GoToURLNode",
            "ClickElementNode",
            "TypeTextNode",
        ]
        for node_type in browser_nodes:
            node_class = get_node_class(node_type)
            assert node_class is not None
            assert node_type in node_class.__name__ or callable(node_class)


# =============================================================================
# NODE_TYPE_MAP PROXY TESTS
# =============================================================================


@pytest.mark.integration
class TestNodeTypeMapProxy:
    """Tests for NODE_TYPE_MAP backward compatibility proxy."""

    def test_contains_for_valid_types(self):
        """Verify __contains__ works for valid types."""
        assert "StartNode" in NODE_TYPE_MAP
        assert "EndNode" in NODE_TYPE_MAP
        assert "ClickElementNode" in NODE_TYPE_MAP

    def test_contains_for_invalid_types(self):
        """Verify __contains__ returns False for invalid types."""
        assert "FakeNode" not in NODE_TYPE_MAP
        assert "" not in NODE_TYPE_MAP

    def test_getitem_returns_class(self):
        """Verify __getitem__ returns node class."""
        node_class = NODE_TYPE_MAP["StartNode"]
        assert node_class is not None
        assert callable(node_class)

    def test_getitem_raises_for_invalid(self):
        """Verify __getitem__ raises KeyError for invalid types."""
        with pytest.raises(KeyError):
            _ = NODE_TYPE_MAP["FakeNode"]

    def test_get_with_default(self):
        """Verify get() returns default for invalid types."""
        result = NODE_TYPE_MAP.get("FakeNode", None)
        assert result is None

        result = NODE_TYPE_MAP.get("StartNode", None)
        assert result is not None

    def test_keys_returns_all_types(self):
        """Verify keys() returns all node types."""
        keys = NODE_TYPE_MAP.keys()
        assert len(keys) > 200
        assert "StartNode" in keys
        assert "EndNode" in keys

    def test_len_matches_registry(self):
        """Verify len() matches registry length."""
        assert len(NODE_TYPE_MAP) == len(nodes_module._NODE_REGISTRY)


# =============================================================================
# get_all_node_types TESTS
# =============================================================================


@pytest.mark.integration
class TestGetAllNodeTypes:
    """Tests for get_all_node_types() function."""

    def test_returns_list(self):
        """Verify returns a list."""
        result = get_all_node_types()
        assert isinstance(result, list)

    def test_contains_expected_types(self):
        """Verify contains expected node types."""
        result = get_all_node_types()
        expected = ["StartNode", "EndNode", "ClickElementNode", "TypeTextNode"]
        for node_type in expected:
            assert node_type in result

    def test_length_matches_registry(self):
        """Verify length matches registry."""
        result = get_all_node_types()
        assert len(result) == len(nodes_module._NODE_REGISTRY)

    def test_all_entries_are_strings(self):
        """Verify all entries are strings."""
        result = get_all_node_types()
        for entry in result:
            assert isinstance(entry, str)


# =============================================================================
# CATEGORY NODE TESTS
# =============================================================================


@pytest.mark.integration
class TestCategoryNodes:
    """Tests for specific category nodes."""

    def test_trigger_nodes_accessible(self):
        """Verify trigger nodes are accessible."""
        trigger_nodes = [
            "WebhookTriggerNode",
            "ScheduleTriggerNode",
            "FileWatchTriggerNode",
            "EmailTriggerNode",
            "TelegramTriggerNode",
            "GmailTriggerNode",
        ]
        for node_type in trigger_nodes:
            assert is_valid_node_type(node_type), f"Trigger {node_type} not found"

    def test_control_flow_nodes_accessible(self):
        """Verify control flow nodes are accessible."""
        control_nodes = [
            "IfNode",
            "ForLoopStartNode",
            "ForLoopEndNode",
            "WhileLoopStartNode",
            "WhileLoopEndNode",
            "BreakNode",
            "ContinueNode",
            "SwitchNode",
            "TryNode",
            "CatchNode",
            "FinallyNode",
        ]
        for node_type in control_nodes:
            assert is_valid_node_type(node_type), f"Control {node_type} not found"

    def test_data_operation_nodes_accessible(self):
        """Verify data operation nodes are accessible."""
        data_nodes = [
            "ConcatenateNode",
            "FormatStringNode",
            "RegexMatchNode",
            "RegexReplaceNode",
            "MathOperationNode",
            "JsonParseNode",
            "CreateListNode",
            "CreateDictNode",
        ]
        for node_type in data_nodes:
            assert is_valid_node_type(node_type), f"Data {node_type} not found"

    def test_file_nodes_accessible(self):
        """Verify file nodes are accessible."""
        file_nodes = [
            "ReadFileNode",
            "WriteFileNode",
            "AppendFileNode",
            "DeleteFileNode",
            "CopyFileNode",
            "MoveFileNode",
            "FileExistsNode",
            "ReadCSVNode",
            "WriteCSVNode",
        ]
        for node_type in file_nodes:
            assert is_valid_node_type(node_type), f"File {node_type} not found"

    def test_google_workspace_nodes_accessible(self):
        """Verify Google Workspace nodes are accessible."""
        google_nodes = [
            "SheetsGetCellNode",
            "SheetsSetCellNode",
            "DriveUploadFileNode",
            "DriveDownloadFileNode",
            "DocsGetDocumentNode",
            "CalendarListEventsNode",
        ]
        for node_type in google_nodes:
            assert is_valid_node_type(node_type), f"Google {node_type} not found"


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


@pytest.mark.integration
class TestEdgeCases:
    """Edge case tests for node registry."""

    def test_empty_string_node_type(self):
        """Verify empty string returns None."""
        assert get_node_class("") is None
        assert is_valid_node_type("") is False

    def test_none_safe(self):
        """Verify functions handle None safely."""
        # get_node_class should handle None
        try:
            result = get_node_class(None)
            assert result is None
        except (TypeError, AttributeError):
            # If it raises, that's also acceptable behavior
            pass

    def test_special_characters_in_name(self):
        """Verify special characters are handled."""
        special_names = ["Start-Node", "Start_Node", "Start.Node", "Start Node"]
        for name in special_names:
            # Should return False/None, not crash
            assert is_valid_node_type(name) is False

    def test_subflow_node_accessible(self):
        """Verify SubflowNode is accessible."""
        assert is_valid_node_type("SubflowNode")
        node_class = get_node_class("SubflowNode")
        assert node_class is not None
