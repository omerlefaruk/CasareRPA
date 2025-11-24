"""
Tests for canvas/visual_nodes.py - Visual node wrappers for NodeGraphQt.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestVisualNodeClasses:
    """Test VISUAL_NODE_CLASSES discovery."""

    def test_visual_node_classes_list_exists(self):
        """Test that VISUAL_NODE_CLASSES is defined."""
        from casare_rpa.canvas.visual_nodes import VISUAL_NODE_CLASSES

        assert isinstance(VISUAL_NODE_CLASSES, list)
        assert len(VISUAL_NODE_CLASSES) > 0

    def test_all_classes_are_visual_nodes(self):
        """Test that all discovered classes are VisualNode subclasses."""
        from casare_rpa.canvas.visual_nodes import VISUAL_NODE_CLASSES, VisualNode

        for cls in VISUAL_NODE_CLASSES:
            assert issubclass(cls, VisualNode), f"{cls.__name__} is not a VisualNode"

    def test_all_classes_have_node_name(self):
        """Test that all visual node classes have NODE_NAME."""
        from casare_rpa.canvas.visual_nodes import VISUAL_NODE_CLASSES

        for cls in VISUAL_NODE_CLASSES:
            assert hasattr(cls, 'NODE_NAME'), f"{cls.__name__} missing NODE_NAME"
            assert cls.NODE_NAME, f"{cls.__name__} has empty NODE_NAME"

    def test_all_classes_have_category(self):
        """Test that all visual node classes have NODE_CATEGORY."""
        from casare_rpa.canvas.visual_nodes import VISUAL_NODE_CLASSES

        for cls in VISUAL_NODE_CLASSES:
            assert hasattr(cls, 'NODE_CATEGORY'), f"{cls.__name__} missing NODE_CATEGORY"
            assert cls.NODE_CATEGORY, f"{cls.__name__} has empty NODE_CATEGORY"

    def test_all_classes_have_identifier(self):
        """Test that all visual node classes have __identifier__."""
        from casare_rpa.canvas.visual_nodes import VISUAL_NODE_CLASSES

        for cls in VISUAL_NODE_CLASSES:
            assert hasattr(cls, '__identifier__'), f"{cls.__name__} missing __identifier__"


class TestBasicVisualNodes:
    """Test basic visual node classes."""

    def test_visual_start_node(self):
        """Test VisualStartNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualStartNode

        assert VisualStartNode.NODE_NAME == "Start"
        assert VisualStartNode.NODE_CATEGORY == "basic"
        assert "basic" in VisualStartNode.__identifier__

    def test_visual_end_node(self):
        """Test VisualEndNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualEndNode

        assert VisualEndNode.NODE_NAME == "End"
        assert VisualEndNode.NODE_CATEGORY == "basic"

    def test_visual_comment_node(self):
        """Test VisualCommentNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualCommentNode

        assert VisualCommentNode.NODE_NAME == "Comment"
        assert VisualCommentNode.NODE_CATEGORY == "basic"


class TestBrowserVisualNodes:
    """Test browser visual node classes."""

    def test_visual_launch_browser_node(self):
        """Test VisualLaunchBrowserNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualLaunchBrowserNode

        assert VisualLaunchBrowserNode.NODE_NAME == "Launch Browser"
        assert VisualLaunchBrowserNode.NODE_CATEGORY == "browser"

    def test_visual_close_browser_node(self):
        """Test VisualCloseBrowserNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualCloseBrowserNode

        assert VisualCloseBrowserNode.NODE_NAME == "Close Browser"
        assert VisualCloseBrowserNode.NODE_CATEGORY == "browser"

    def test_visual_new_tab_node(self):
        """Test VisualNewTabNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualNewTabNode

        assert VisualNewTabNode.NODE_NAME == "New Tab"
        assert VisualNewTabNode.NODE_CATEGORY == "browser"


class TestNavigationVisualNodes:
    """Test navigation visual node classes."""

    def test_visual_goto_url_node(self):
        """Test VisualGoToURLNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualGoToURLNode

        assert VisualGoToURLNode.NODE_NAME == "Go To URL"
        assert VisualGoToURLNode.NODE_CATEGORY == "navigation"

    def test_visual_go_back_node(self):
        """Test VisualGoBackNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualGoBackNode

        assert VisualGoBackNode.NODE_NAME == "Go Back"
        assert VisualGoBackNode.NODE_CATEGORY == "navigation"

    def test_visual_go_forward_node(self):
        """Test VisualGoForwardNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualGoForwardNode

        assert VisualGoForwardNode.NODE_NAME == "Go Forward"
        assert VisualGoForwardNode.NODE_CATEGORY == "navigation"

    def test_visual_refresh_page_node(self):
        """Test VisualRefreshPageNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualRefreshPageNode

        assert VisualRefreshPageNode.NODE_NAME == "Refresh Page"
        assert VisualRefreshPageNode.NODE_CATEGORY == "navigation"


class TestInteractionVisualNodes:
    """Test interaction visual node classes."""

    def test_visual_click_element_node(self):
        """Test VisualClickElementNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualClickElementNode

        assert VisualClickElementNode.NODE_NAME == "Click Element"
        assert VisualClickElementNode.NODE_CATEGORY == "interaction"

    def test_visual_type_text_node(self):
        """Test VisualTypeTextNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualTypeTextNode

        assert VisualTypeTextNode.NODE_NAME == "Type Text"
        assert VisualTypeTextNode.NODE_CATEGORY == "interaction"

    def test_visual_select_dropdown_node(self):
        """Test VisualSelectDropdownNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualSelectDropdownNode

        assert VisualSelectDropdownNode.NODE_NAME == "Select Dropdown"
        assert VisualSelectDropdownNode.NODE_CATEGORY == "interaction"


class TestControlFlowVisualNodes:
    """Test control flow visual node classes."""

    def test_visual_if_node(self):
        """Test VisualIfNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualIfNode

        assert VisualIfNode.NODE_NAME == "If"
        assert VisualIfNode.NODE_CATEGORY == "control_flow"

    def test_visual_for_loop_node(self):
        """Test VisualForLoopNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualForLoopNode

        assert VisualForLoopNode.NODE_NAME == "For Loop"
        assert VisualForLoopNode.NODE_CATEGORY == "control_flow"

    def test_visual_while_loop_node(self):
        """Test VisualWhileLoopNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualWhileLoopNode

        assert VisualWhileLoopNode.NODE_NAME == "While Loop"
        assert VisualWhileLoopNode.NODE_CATEGORY == "control_flow"


class TestErrorHandlingVisualNodes:
    """Test error handling visual node classes."""

    def test_visual_try_node(self):
        """Test VisualTryNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualTryNode

        assert VisualTryNode.NODE_NAME == "Try"
        assert VisualTryNode.NODE_CATEGORY == "error_handling"

    def test_visual_retry_node(self):
        """Test VisualRetryNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualRetryNode

        assert VisualRetryNode.NODE_NAME == "Retry"
        assert VisualRetryNode.NODE_CATEGORY == "error_handling"

    def test_visual_throw_error_node(self):
        """Test VisualThrowErrorNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualThrowErrorNode

        assert VisualThrowErrorNode.NODE_NAME == "Throw Error"
        assert VisualThrowErrorNode.NODE_CATEGORY == "error_handling"


class TestVariableVisualNodes:
    """Test variable visual node classes."""

    def test_visual_set_variable_node(self):
        """Test VisualSetVariableNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualSetVariableNode

        assert VisualSetVariableNode.NODE_NAME == "Set Variable"
        assert VisualSetVariableNode.NODE_CATEGORY == "variable"

    def test_visual_get_variable_node(self):
        """Test VisualGetVariableNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualGetVariableNode

        assert VisualGetVariableNode.NODE_NAME == "Get Variable"
        assert VisualGetVariableNode.NODE_CATEGORY == "variable"


class TestDataOperationVisualNodes:
    """Test data operation visual node classes."""

    def test_visual_concatenate_node(self):
        """Test VisualConcatenateNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualConcatenateNode

        assert "Concatenate" in VisualConcatenateNode.NODE_NAME
        assert "data" in VisualConcatenateNode.NODE_CATEGORY.lower()

    def test_visual_regex_match_node(self):
        """Test VisualRegexMatchNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualRegexMatchNode

        assert VisualRegexMatchNode.NODE_NAME == "Regex Match"
        assert "data" in VisualRegexMatchNode.NODE_CATEGORY.lower()

    def test_visual_math_operation_node(self):
        """Test VisualMathOperationNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualMathOperationNode

        assert VisualMathOperationNode.NODE_NAME == "Math Operation"
        assert "data" in VisualMathOperationNode.NODE_CATEGORY.lower()


class TestDesktopVisualNodes:
    """Test desktop automation visual node classes."""

    def test_visual_launch_application_node(self):
        """Test VisualLaunchApplicationNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualLaunchApplicationNode

        assert VisualLaunchApplicationNode.NODE_NAME == "Launch Application"
        assert "desktop" in VisualLaunchApplicationNode.NODE_CATEGORY.lower()

    def test_visual_close_application_node(self):
        """Test VisualCloseApplicationNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualCloseApplicationNode

        assert VisualCloseApplicationNode.NODE_NAME == "Close Application"
        assert "desktop" in VisualCloseApplicationNode.NODE_CATEGORY.lower()

    def test_visual_activate_window_node(self):
        """Test VisualActivateWindowNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualActivateWindowNode

        assert VisualActivateWindowNode.NODE_NAME == "Activate Window"
        assert "desktop" in VisualActivateWindowNode.NODE_CATEGORY.lower()

    def test_visual_find_element_node(self):
        """Test VisualFindElementNode attributes."""
        from casare_rpa.canvas.visual_nodes import VisualFindElementNode

        assert VisualFindElementNode.NODE_NAME == "Find Element"
        assert "desktop" in VisualFindElementNode.NODE_CATEGORY.lower()


class TestNodeColors:
    """Test node color configuration."""

    def test_node_colors_dict_exists(self):
        """Test that NODE_COLORS is defined."""
        from casare_rpa.canvas.visual_nodes import NODE_COLORS

        assert isinstance(NODE_COLORS, dict)

    def test_all_categories_have_colors(self):
        """Test that common categories have colors defined."""
        from casare_rpa.canvas.visual_nodes import NODE_COLORS

        categories = ["basic", "browser", "navigation", "interaction", "data", "wait", "variable"]
        for cat in categories:
            assert cat in NODE_COLORS, f"Missing color for category: {cat}"


class TestVisualNodeCoverage:
    """Test that all expected nodes are present."""

    def test_expected_node_count(self):
        """Test that we have a reasonable number of visual nodes."""
        from casare_rpa.canvas.visual_nodes import VISUAL_NODE_CLASSES

        # Should have a good number of nodes
        assert len(VISUAL_NODE_CLASSES) >= 30, "Expected at least 30 visual node types"

    def test_node_names_are_unique(self):
        """Test that all node names are unique."""
        from casare_rpa.canvas.visual_nodes import VISUAL_NODE_CLASSES

        names = [cls.NODE_NAME for cls in VISUAL_NODE_CLASSES]
        assert len(names) == len(set(names)), "Duplicate node names found"

    def test_categories_are_valid(self):
        """Test that all categories are from expected set."""
        from casare_rpa.canvas.visual_nodes import VISUAL_NODE_CLASSES

        # Category names may have different casing/formatting
        valid_category_keywords = [
            "basic", "browser", "navigation", "interaction",
            "data", "wait", "variable", "control", "flow",
            "error", "handling", "desktop", "automation"
        ]

        for cls in VISUAL_NODE_CLASSES:
            category_lower = cls.NODE_CATEGORY.lower().replace("_", " ")
            has_valid_keyword = any(kw in category_lower for kw in valid_category_keywords)
            assert has_valid_keyword, \
                f"Unknown category: {cls.NODE_CATEGORY} for {cls.__name__}"
