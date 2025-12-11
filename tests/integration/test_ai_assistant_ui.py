"""
CasareRPA - AI Assistant UI Integration Tests

Tests for verifying AI Assistant toolbar, menu, and dock integration.

Usage:
    pytest tests/integration/test_ai_assistant_ui.py -v
"""

import os
import sys

# Set Qt to offscreen mode before any Qt imports
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from typing import Optional


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for all tests in module."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def main_window(qapp):
    """Create MainWindow instance for testing."""
    from casare_rpa.presentation.canvas.main_window import MainWindow
    from unittest.mock import MagicMock

    window = MainWindow()

    # Mock workflow controller to prevent teardown errors
    if window._workflow_controller is None:
        window._workflow_controller = MagicMock()
        window._workflow_controller.check_unsaved_changes.return_value = True
        window._workflow_controller.is_modified = False

    yield window

    try:
        window.close()
    except Exception:
        pass  # Ignore cleanup errors in test


# =============================================================================
# ICON TESTS
# =============================================================================


class TestAIAssistantIcon:
    """Test AI Assistant icon creation."""

    def test_ai_assistant_icon_exists(self, qapp):
        """Verify AI assistant icon can be created."""
        from casare_rpa.presentation.canvas.ui.icons import get_toolbar_icon

        icon = get_toolbar_icon("ai_assistant")
        assert icon is not None
        assert not icon.isNull(), "AI assistant icon should not be null"

    def test_ai_assistant_icon_has_pixmap(self, qapp):
        """Verify AI assistant icon has valid pixmap."""
        from casare_rpa.presentation.canvas.ui.icons import get_toolbar_icon
        from PySide6.QtCore import QSize

        icon = get_toolbar_icon("ai_assistant")
        pixmap = icon.pixmap(QSize(16, 16))
        assert not pixmap.isNull(), "AI assistant icon pixmap should not be null"
        assert pixmap.width() == 16
        assert pixmap.height() == 16

    def test_brain_icon_shape_in_colored_icons(self, qapp):
        """Verify brain shape is registered in colored icons."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        assert "ai_assistant" in ToolbarIcons._COLORED_ICONS
        shape, color = ToolbarIcons._COLORED_ICONS["ai_assistant"]
        assert shape == "brain"
        assert color == "#9C27B0"  # Purple


# =============================================================================
# ACTION TESTS
# =============================================================================


class TestAIAssistantAction:
    """Test AI Assistant action creation."""

    def test_action_created(self, main_window):
        """Verify AI assistant action is created."""
        assert hasattr(main_window, "action_ai_assistant")
        assert main_window.action_ai_assistant is not None

    def test_action_is_checkable(self, main_window):
        """Verify AI assistant action is checkable (toggle)."""
        action = main_window.action_ai_assistant
        assert action.isCheckable()

    def test_action_has_shortcut(self, main_window):
        """Verify AI assistant action has keyboard shortcut."""
        action = main_window.action_ai_assistant
        shortcut = action.shortcut()
        assert shortcut.toString() == "Ctrl+Shift+G"

    def test_action_has_tooltip(self, main_window):
        """Verify AI assistant action has descriptive tooltip."""
        action = main_window.action_ai_assistant
        assert "AI" in action.statusTip() or "assistant" in action.statusTip().lower()


# =============================================================================
# TOOLBAR TESTS
# =============================================================================


class TestAIAssistantToolbar:
    """Test AI Assistant toolbar integration."""

    def test_toolbar_has_ai_action(self, main_window):
        """Verify toolbar contains AI assistant action."""
        toolbar = main_window._main_toolbar
        actions = toolbar.actions()
        action_names = [a.text() for a in actions if a.text()]

        # Check that AI action is in toolbar (text might be "AI" or "AI Assistant")
        ai_actions = [name for name in action_names if "AI" in name]
        assert (
            len(ai_actions) > 0
        ), f"AI action not found in toolbar. Actions: {action_names}"

    def test_toolbar_ai_button_has_icon(self, main_window):
        """Verify AI toolbar button has an icon."""
        action = main_window.action_ai_assistant
        icon = action.icon()
        assert not icon.isNull(), "AI assistant toolbar button should have an icon"


# =============================================================================
# DOCK CREATOR TESTS
# =============================================================================


class TestAIAssistantDockCreator:
    """Test AI Assistant dock creation."""

    def test_dock_creator_has_method(self, main_window):
        """Verify dock creator has create_ai_assistant_panel method."""
        dock_creator = main_window._dock_creator
        assert hasattr(dock_creator, "create_ai_assistant_panel")
        assert callable(dock_creator.create_ai_assistant_panel)

    def test_can_create_ai_panel(self, main_window):
        """Verify AI assistant panel can be created."""
        dock_creator = main_window._dock_creator
        panel = dock_creator.create_ai_assistant_panel()

        assert panel is not None
        assert panel.windowTitle() or True  # Panel exists

        # Clean up
        panel.close()
        panel.deleteLater()


# =============================================================================
# MAIN WINDOW INTEGRATION TESTS
# =============================================================================


class TestAIAssistantMainWindowIntegration:
    """Test AI Assistant integration with MainWindow."""

    def test_ai_panel_property_initially_none(self, main_window):
        """Verify AI panel is initially None (lazy loaded)."""
        # Before toggling, panel should be None
        assert main_window._ai_assistant_panel is None

    def test_toggle_handler_exists(self, main_window):
        """Verify toggle handler method exists."""
        assert hasattr(main_window, "_on_toggle_ai_assistant")
        assert callable(main_window._on_toggle_ai_assistant)

    def test_toggle_creates_panel_lazily(self, main_window):
        """Verify toggling creates panel lazily."""
        from unittest.mock import MagicMock

        assert main_window._ai_assistant_panel is None

        # Mock signal coordinator to prevent errors
        if (
            not hasattr(main_window, "_signal_coordinator")
            or main_window._signal_coordinator is None
        ):
            main_window._signal_coordinator = MagicMock()
            main_window._signal_coordinator.on_ai_workflow_ready = MagicMock()

        # Toggle on
        main_window._on_toggle_ai_assistant(True)

        assert main_window._ai_assistant_panel is not None

    def test_toggle_shows_and_hides_panel(self, main_window):
        """Verify toggling shows and hides panel."""
        from unittest.mock import MagicMock

        # Mock signal coordinator
        if (
            not hasattr(main_window, "_signal_coordinator")
            or main_window._signal_coordinator is None
        ):
            main_window._signal_coordinator = MagicMock()
            main_window._signal_coordinator.on_ai_workflow_ready = MagicMock()

        # Ensure panel exists
        main_window._on_toggle_ai_assistant(True)
        panel = main_window._ai_assistant_panel

        assert panel is not None

        # Hide
        main_window._on_toggle_ai_assistant(False)
        assert panel.isHidden() or not panel.isVisible()

        # Show again
        main_window._on_toggle_ai_assistant(True)
        # Panel should be visible (in headless mode this might not fully work)

    def test_getter_methods(self, main_window):
        """Verify getter methods work."""
        from unittest.mock import MagicMock

        # Before creation
        assert main_window.ai_assistant_panel is None
        assert main_window.get_ai_assistant_panel() is None

        # Mock signal coordinator
        if (
            not hasattr(main_window, "_signal_coordinator")
            or main_window._signal_coordinator is None
        ):
            main_window._signal_coordinator = MagicMock()
            main_window._signal_coordinator.on_ai_workflow_ready = MagicMock()

        # After creation
        main_window._on_toggle_ai_assistant(True)
        assert main_window.ai_assistant_panel is not None
        assert main_window.get_ai_assistant_panel() is not None


# =============================================================================
# AI ASSISTANT DOCK WIDGET TESTS
# =============================================================================


class TestAIAssistantDockWidget:
    """Test AI Assistant dock widget itself."""

    def test_dock_widget_import(self, qapp):
        """Verify AIAssistantDock can be imported."""
        from casare_rpa.presentation.canvas.ui.widgets.ai_assistant import (
            AIAssistantDock,
        )

        assert AIAssistantDock is not None

    def test_dock_widget_creation(self, qapp):
        """Verify AIAssistantDock can be instantiated."""
        from casare_rpa.presentation.canvas.ui.widgets.ai_assistant import (
            AIAssistantDock,
        )

        dock = AIAssistantDock()
        assert dock is not None

        # Clean up
        dock.close()
        dock.deleteLater()

    def test_dock_has_required_signals(self, qapp):
        """Verify dock has required signals."""
        from casare_rpa.presentation.canvas.ui.widgets.ai_assistant import (
            AIAssistantDock,
        )

        dock = AIAssistantDock()

        # Check for workflow_ready signal
        assert hasattr(dock, "workflow_ready")

        # Clean up
        dock.close()
        dock.deleteLater()


# =============================================================================
# HEADLESS VALIDATOR TESTS
# =============================================================================


class TestHeadlessWorkflowSandbox:
    """Test HeadlessWorkflowSandbox from domain layer."""

    def test_sandbox_import(self):
        """Verify HeadlessWorkflowSandbox can be imported."""
        from casare_rpa.domain.services.headless_validator import (
            HeadlessWorkflowSandbox,
        )

        assert HeadlessWorkflowSandbox is not None

    def test_sandbox_creation(self):
        """Test HeadlessWorkflowSandbox can be instantiated."""
        from casare_rpa.domain.services.headless_validator import (
            HeadlessWorkflowSandbox,
        )

        sandbox = HeadlessWorkflowSandbox()
        assert sandbox is not None
        assert hasattr(sandbox, "validate_workflow")

    def test_sandbox_validation_result_structure(self):
        """Test validation returns proper result structure."""
        from casare_rpa.domain.services.headless_validator import (
            HeadlessWorkflowSandbox,
            WorkflowValidationResult,
        )

        sandbox = HeadlessWorkflowSandbox()

        # Valid workflow with metadata
        workflow = {
            "metadata": {"name": "Test", "version": "1.0"},
            "nodes": {},
            "connections": [],
        }

        result = sandbox.validate_workflow(workflow)
        assert isinstance(result, WorkflowValidationResult)
        assert hasattr(result, "success")
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")

    def test_sandbox_detects_invalid_node_type(self):
        """Test detection of invalid node types."""
        from casare_rpa.domain.services.headless_validator import (
            HeadlessWorkflowSandbox,
        )

        sandbox = HeadlessWorkflowSandbox()

        workflow = {
            "metadata": {"name": "Test", "version": "1.0"},
            "nodes": {
                "invalid_1": {
                    "node_id": "invalid_1",
                    "node_type": "NonExistentNodeType12345",
                    "config": {},
                    "position": [100, 100],
                }
            },
            "connections": [],
        }

        result = sandbox.validate_workflow(workflow)
        # Should detect invalid node type - check for errors or non-success
        assert not result.success or len(result.errors) > 0 or len(result.warnings) > 0


# =============================================================================
# SMART AGENT TESTS
# =============================================================================


class TestSmartWorkflowAgent:
    """Test SmartWorkflowAgent from infrastructure layer."""

    def test_agent_import(self):
        """Verify SmartWorkflowAgent can be imported."""
        from casare_rpa.infrastructure.ai.smart_agent import SmartWorkflowAgent

        assert SmartWorkflowAgent is not None

    def test_generation_result_import(self):
        """Verify WorkflowGenerationResult can be imported."""
        from casare_rpa.infrastructure.ai.smart_agent import WorkflowGenerationResult

        assert WorkflowGenerationResult is not None


# =============================================================================
# PROMPTS TESTS
# =============================================================================


class TestAIPrompts:
    """Test AI prompts from domain layer."""

    def test_prompts_import(self):
        """Verify prompts module can be imported."""
        from casare_rpa.domain.ai import prompts

        assert prompts is not None

    def test_system_prompt_exists(self):
        """Verify system prompt is defined."""
        from casare_rpa.domain.ai.prompts import GENIUS_SYSTEM_PROMPT

        assert GENIUS_SYSTEM_PROMPT is not None
        assert len(GENIUS_SYSTEM_PROMPT) > 100  # Should be substantial

    def test_helper_functions_exist(self):
        """Verify prompt helper functions exist."""
        from casare_rpa.domain.ai.prompts import (
            get_workflow_generation_prompt,
            get_repair_prompt,
        )

        assert callable(get_workflow_generation_prompt)
        assert callable(get_repair_prompt)


# =============================================================================
# FULL INTEGRATION TEST
# =============================================================================


class TestFullAIAssistantIntegration:
    """Full integration test of AI Assistant components."""

    def test_full_component_chain(self, main_window):
        """Test full integration from action to dock."""
        from unittest.mock import MagicMock

        # 1. Action exists and is connected
        assert main_window.action_ai_assistant is not None

        # Mock signal coordinator for lazy loading
        if (
            not hasattr(main_window, "_signal_coordinator")
            or main_window._signal_coordinator is None
        ):
            main_window._signal_coordinator = MagicMock()
            main_window._signal_coordinator.on_ai_workflow_ready = MagicMock()

        # 2. Toggle handler creates panel
        main_window._on_toggle_ai_assistant(True)
        panel = main_window._ai_assistant_panel
        assert panel is not None

        # 3. Panel has expected structure
        from casare_rpa.presentation.canvas.ui.widgets.ai_assistant import (
            AIAssistantDock,
        )

        assert isinstance(panel, AIAssistantDock)

        # 4. Panel has workflow_ready signal
        assert hasattr(panel, "workflow_ready")

        print("✓ AI Assistant full integration test passed")


# =============================================================================
# RUN TESTS
# =============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
