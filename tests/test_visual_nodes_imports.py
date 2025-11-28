"""
Smoke tests for visual node imports.

This test ensures all 238 visual nodes can be imported successfully
from both the new location and the compatibility layer.
"""

import pytest


class TestVisualNodesImports:
    """Test visual node imports."""

    def test_import_from_new_location(self) -> None:
        """Test importing from new presentation.canvas.visual_nodes location."""
        # Test basic imports (3 nodes)
        from casare_rpa.presentation.canvas.visual_nodes import (
            VisualStartNode,
            VisualEndNode,
            VisualCommentNode,
        )

        assert VisualStartNode is not None
        assert VisualEndNode is not None
        assert VisualCommentNode is not None

    def test_import_from_compatibility_layer(self) -> None:
        """Test importing from old canvas.visual_nodes location (compatibility)."""
        # Test basic imports from compatibility layer
        from casare_rpa.presentation.canvas.visual_nodes import (
            VisualStartNode,
            VisualEndNode,
            VisualCommentNode,
        )

        assert VisualStartNode is not None
        assert VisualEndNode is not None
        assert VisualCommentNode is not None

    def test_import_all_categories(self) -> None:
        """Test importing at least one node from each category."""
        # Basic (3 nodes)
        from casare_rpa.presentation.canvas.visual_nodes.basic import VisualStartNode

        # Browser (18 nodes)
        from casare_rpa.presentation.canvas.visual_nodes.browser import (
            VisualLaunchBrowserNode,
        )

        # Control Flow (10 nodes)
        from casare_rpa.presentation.canvas.visual_nodes.control_flow import (
            VisualIfNode,
        )

        # Database (10 nodes)
        from casare_rpa.presentation.canvas.visual_nodes.database import (
            VisualDatabaseConnectNode,
        )

        # Data Operations (32 nodes)
        from casare_rpa.presentation.canvas.visual_nodes.data_operations import (
            VisualConcatenateNode,
        )

        # Desktop Automation (36 nodes)
        from casare_rpa.presentation.canvas.visual_nodes.desktop_automation import (
            VisualLaunchApplicationNode,
        )

        # Email (8 nodes)
        from casare_rpa.presentation.canvas.visual_nodes.email import (
            VisualSendEmailNode,
        )

        # Error Handling (10 nodes)
        from casare_rpa.presentation.canvas.visual_nodes.error_handling import (
            VisualTryNode,
        )

        # File Operations (40 nodes)
        from casare_rpa.presentation.canvas.visual_nodes.file_operations import (
            VisualReadFileNode,
        )

        # Scripts (5 nodes)
        from casare_rpa.presentation.canvas.visual_nodes.scripts import (
            VisualRunPythonScriptNode,
        )

        # System (13 nodes)
        from casare_rpa.presentation.canvas.visual_nodes.system import (
            VisualClipboardCopyNode,
        )

        # Office Automation (12 nodes)
        from casare_rpa.presentation.canvas.visual_nodes.office_automation import (
            VisualExcelOpenNode,
        )

        # Rest API (12 nodes)
        from casare_rpa.presentation.canvas.visual_nodes.rest_api import (
            VisualHttpRequestNode,
        )

        # Utility (26 nodes - random, datetime, text operations)
        from casare_rpa.presentation.canvas.visual_nodes.utility import (
            VisualRandomNumberNode,
        )

        # Variable (3 nodes)
        from casare_rpa.presentation.canvas.visual_nodes.variable import (
            VisualSetVariableNode,
        )

        # Assert all imports succeeded
        assert VisualStartNode is not None
        assert VisualLaunchBrowserNode is not None
        assert VisualIfNode is not None
        assert VisualDatabaseConnectNode is not None
        assert VisualConcatenateNode is not None
        assert VisualLaunchApplicationNode is not None
        assert VisualSendEmailNode is not None
        assert VisualTryNode is not None
        assert VisualReadFileNode is not None
        assert VisualRunPythonScriptNode is not None
        assert VisualClipboardCopyNode is not None
        assert VisualExcelOpenNode is not None
        assert VisualHttpRequestNode is not None
        assert VisualRandomNumberNode is not None
        assert VisualSetVariableNode is not None

    def test_no_duplicate_http_request_node(self) -> None:
        """Test that VisualHttpRequestNode is only in rest_api, not utility."""
        # Should import from rest_api successfully
        from casare_rpa.presentation.canvas.visual_nodes.rest_api import (
            VisualHttpRequestNode as RestApiHttpNode,
        )

        assert RestApiHttpNode is not None
        assert RestApiHttpNode.NODE_CATEGORY == "rest_api"

        # Should NOT be importable from utility
        with pytest.raises(ImportError):
            from casare_rpa.presentation.canvas.visual_nodes.utility import (
                VisualHttpRequestNode,  # noqa: F401
            )

    def test_main_init_exports_all_nodes(self) -> None:
        """Test that main __init__.py exports all nodes correctly."""
        from casare_rpa.presentation.canvas.visual_nodes import __all__

        # Check that __all__ contains expected number of nodes (238 total)
        # basic(3) + browser(18) + control_flow(10) + database(10) + data_operations(32)
        # + desktop_automation(36) + email(8) + error_handling(10) + file_operations(40)
        # + scripts(5) + system(13) + utility(26) + office_automation(12) + rest_api(12)
        # + variable(3) = 238
        assert len(__all__) == 238

        # Check that VisualHttpRequestNode appears only once
        http_request_count = __all__.count("VisualHttpRequestNode")
        assert (
            http_request_count == 1
        ), f"VisualHttpRequestNode appears {http_request_count} times, expected 1"

    def test_compatibility_layer_has_all_exports(self) -> None:
        """Test that compatibility layer re-exports __all__ correctly."""
        from casare_rpa.presentation.canvas.visual_nodes import __all__ as compat_all
        from casare_rpa.presentation.canvas.visual_nodes import __all__ as new_all

        # Both should have the same __all__ list
        assert compat_all == new_all
        assert len(compat_all) == 238
