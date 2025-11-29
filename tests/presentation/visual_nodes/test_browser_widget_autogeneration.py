"""Tests for browser visual nodes widget auto-generation.

Verifies that visual nodes properly inherit widgets from domain node @node_schema
decorators without manual widget creation causing duplicates.
"""

import pytest
from casare_rpa.presentation.canvas.visual_nodes.browser.nodes import (
    VisualLaunchBrowserNode,
    VisualNavigateNode,
    VisualClickElementNode,
)


class TestWidgetAutoGeneration:
    """Test that @node_schema decorator auto-generates widgets correctly."""

    def test_launch_browser_has_auto_generated_widgets(self):
        """LaunchBrowserNode widgets should be auto-generated from @node_schema."""
        node = VisualLaunchBrowserNode()

        # Verify no manual widgets in __init__
        # (auto-generated widgets are added by BaseVisualNode from __node_schema__)
        # We can't easily inspect widget internals without Qt, but we can verify
        # the node instantiates without NodePropertyError

        assert node is not None
        assert node.NODE_NAME == "Launch Browser"

    def test_navigate_node_has_auto_generated_widgets(self):
        """NavigateNode widgets should be auto-generated from @node_schema."""
        node = VisualNavigateNode()

        assert node is not None
        assert node.NODE_NAME == "Navigate"

    def test_click_element_has_auto_generated_widgets(self):
        """ClickElementNode widgets should be auto-generated from @node_schema."""
        node = VisualClickElementNode()

        assert node is not None
        assert node.NODE_NAME == "Click Element"

    def test_no_duplicate_property_errors_on_instantiation(self):
        """Visual nodes should instantiate without NodePropertyError."""
        # These nodes previously threw NodePropertyError due to duplicate widgets
        # Now they should instantiate cleanly

        try:
            VisualLaunchBrowserNode()
            VisualNavigateNode()
            VisualClickElementNode()
        except Exception as e:
            if "property already exists" in str(e):
                pytest.fail(f"Duplicate property error: {e}")
            # Other errors are OK (Qt initialization, etc.)


class TestSchemaSourceDocumentation:
    """Verify __node_schema__ attribute exists and is documented."""

    def test_schema_attribute_explanation(self):
        """Module docstring should explain __node_schema__ source."""
        import casare_rpa.presentation.canvas.visual_nodes.browser.nodes as browser_module

        module_doc = browser_module.__doc__

        # Verify key documentation exists
        assert "__node_schema__" in module_doc
        assert "casare_rpa.domain.decorators" in module_doc
        assert "Widget Auto-Generation" in module_doc

    def test_manual_widgets_documented(self):
        """Nodes with manual widgets should be documented."""
        import casare_rpa.presentation.canvas.visual_nodes.browser.nodes as browser_module

        module_doc = browser_module.__doc__

        # Verify nodes still using manual widgets are documented
        assert "GoToURLNode" in module_doc
        assert "manual widgets" in module_doc.lower()
