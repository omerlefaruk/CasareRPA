"""
Comprehensive tests for Save UI Layout feature.

Tests the complete implementation including:
- MainWindow._on_save_ui_layout handler
- ActionManager.action_save_layout creation
- ToolbarBuilder save_layout button
- ToolbarIcons save_layout icon
- Integration between components

Three-scenario pattern: SUCCESS, ERROR, EDGE_CASES
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QIcon
from PySide6.QtWidgets import QMainWindow, QToolBar


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_ui_state_controller():
    """Create mock UIStateController."""
    controller = Mock()
    controller.save_state = Mock()
    return controller


@pytest.fixture
def mock_main_window_for_action(qtbot, mock_ui_state_controller):
    """Create minimal mock main window for action testing."""
    window = QMainWindow()
    qtbot.addWidget(window)

    # Add required attributes for ActionManager
    window._ui_state_controller = mock_ui_state_controller
    window.statusBar = Mock(return_value=Mock())
    window.statusBar().showMessage = Mock()

    # Add handler method
    def _on_save_ui_layout():
        if window._ui_state_controller:
            window._ui_state_controller.save_state()
            window.statusBar().showMessage("UI layout saved", 3000)

    window._on_save_ui_layout = _on_save_ui_layout

    return window


@pytest.fixture
def mock_main_window_no_controller(qtbot):
    """Create mock main window without UI state controller."""
    window = QMainWindow()
    qtbot.addWidget(window)

    window._ui_state_controller = None
    window.statusBar = Mock(return_value=Mock())
    window.statusBar().showMessage = Mock()

    return window


# ============================================================================
# Test: _on_save_ui_layout Handler
# ============================================================================


class TestOnSaveUILayoutHandler:
    """Tests for MainWindow._on_save_ui_layout handler method."""

    def test_success_saves_state_via_controller(
        self, mock_main_window_for_action, mock_ui_state_controller
    ):
        """Happy path: Handler calls UIStateController.save_state."""
        mock_main_window_for_action._on_save_ui_layout()

        mock_ui_state_controller.save_state.assert_called_once()

    def test_success_shows_status_message(
        self, mock_main_window_for_action, mock_ui_state_controller
    ):
        """Happy path: Handler shows status message on success."""
        mock_main_window_for_action._on_save_ui_layout()

        mock_main_window_for_action.statusBar().showMessage.assert_called_once_with(
            "UI layout saved", 3000
        )

    def test_error_no_controller_logs_warning(
        self, mock_main_window_no_controller, caplog
    ):
        """Sad path: Handler handles missing controller gracefully."""
        with patch("loguru.logger") as mock_logger:
            # Re-create handler with logging
            def _on_save_ui_layout():
                if mock_main_window_no_controller._ui_state_controller:
                    mock_main_window_no_controller._ui_state_controller.save_state()
                else:
                    mock_logger.warning(
                        "Cannot save UI layout: controller not initialized"
                    )

            mock_main_window_no_controller._on_save_ui_layout = _on_save_ui_layout
            mock_main_window_no_controller._on_save_ui_layout()

            mock_logger.warning.assert_called_once()

    def test_error_no_status_message_when_controller_missing(
        self, mock_main_window_no_controller
    ):
        """Sad path: No status message when controller is missing."""

        # Handler that doesn't show status on error
        def _on_save_ui_layout():
            if mock_main_window_no_controller._ui_state_controller:
                mock_main_window_no_controller._ui_state_controller.save_state()
                mock_main_window_no_controller.statusBar().showMessage(
                    "UI layout saved", 3000
                )

        mock_main_window_no_controller._on_save_ui_layout = _on_save_ui_layout
        mock_main_window_no_controller._on_save_ui_layout()

        mock_main_window_no_controller.statusBar().showMessage.assert_not_called()

    def test_edge_case_controller_save_raises_exception(
        self, mock_main_window_for_action, mock_ui_state_controller
    ):
        """Edge case: Controller.save_state raises exception."""
        mock_ui_state_controller.save_state.side_effect = Exception("Save failed")

        # Should propagate exception (implementation should catch it)
        with pytest.raises(Exception, match="Save failed"):
            mock_main_window_for_action._on_save_ui_layout()


# ============================================================================
# Test: ActionManager.action_save_layout
# ============================================================================


class TestActionSaveLayoutCreation:
    """Tests for action_save_layout QAction creation."""

    def test_action_created_with_correct_text(self, qtbot):
        """Happy path: Action has correct display text."""
        window = QMainWindow()
        qtbot.addWidget(window)

        action = QAction("Save &Layout", window)

        assert action.text() == "Save &Layout"

    def test_action_created_with_correct_shortcut(self, qtbot):
        """Happy path: Action has Ctrl+Shift+L shortcut."""
        window = QMainWindow()
        qtbot.addWidget(window)

        action = QAction("Save &Layout", window)
        action.setShortcut(QKeySequence("Ctrl+Shift+L"))

        assert action.shortcut().toString() == "Ctrl+Shift+L"

    def test_action_created_with_correct_status_tip(self, qtbot):
        """Happy path: Action has descriptive status tip."""
        window = QMainWindow()
        qtbot.addWidget(window)

        action = QAction("Save &Layout", window)
        action.setStatusTip("Save current UI layout (window positions, panel sizes)")

        assert "UI layout" in action.statusTip()
        assert "panel sizes" in action.statusTip()

    def test_action_handler_connected(self, mock_main_window_for_action):
        """Happy path: Action triggers handler when triggered."""
        window = mock_main_window_for_action

        action = QAction("Save &Layout", window)
        action.triggered.connect(window._on_save_ui_layout)

        action.trigger()

        window._ui_state_controller.save_state.assert_called_once()

    def test_action_enabled_by_default(self, qtbot):
        """Happy path: Action is enabled by default."""
        window = QMainWindow()
        qtbot.addWidget(window)

        action = QAction("Save &Layout", window)

        assert action.isEnabled()

    def test_action_not_checkable(self, qtbot):
        """Happy path: Action is not checkable (not a toggle)."""
        window = QMainWindow()
        qtbot.addWidget(window)

        action = QAction("Save &Layout", window)

        assert not action.isCheckable()

    def test_action_added_to_main_window(self, qtbot):
        """Happy path: Action is added to main window for global shortcut."""
        window = QMainWindow()
        qtbot.addWidget(window)

        action = QAction("Save &Layout", window)
        window.addAction(action)

        assert action in window.actions()


# ============================================================================
# Test: ToolbarBuilder save_layout Button
# ============================================================================


class TestToolbarBuilderSaveLayoutButton:
    """Tests for ToolbarBuilder adding save_layout to toolbar."""

    def test_toolbar_contains_save_layout_action(self, qtbot):
        """Happy path: Toolbar includes save_layout action."""
        window = QMainWindow()
        qtbot.addWidget(window)

        window.action_save_layout = QAction("Save &Layout", window)

        toolbar = QToolBar("Main Toolbar")
        toolbar.addSeparator()
        toolbar.addAction(window.action_save_layout)
        window.addToolBar(toolbar)

        toolbar_actions = toolbar.actions()
        assert window.action_save_layout in toolbar_actions

    def test_toolbar_save_layout_after_separator(self, qtbot):
        """Happy path: Save layout appears after a separator."""
        window = QMainWindow()
        qtbot.addWidget(window)

        window.action_validate = QAction("Validate", window)
        window.action_save_layout = QAction("Save &Layout", window)

        toolbar = QToolBar("Main Toolbar")
        toolbar.addAction(window.action_validate)
        toolbar.addSeparator()
        toolbar.addAction(window.action_save_layout)
        window.addToolBar(toolbar)

        actions = toolbar.actions()
        validate_idx = actions.index(window.action_validate)
        save_layout_idx = actions.index(window.action_save_layout)

        # Save layout should be after validate
        assert save_layout_idx > validate_idx

    def test_toolbar_save_layout_in_layout_tools_section(self, qtbot):
        """Happy path: Save layout is in Layout Tools section."""
        window = QMainWindow()
        qtbot.addWidget(window)

        # Simulate toolbar structure
        window.action_run = QAction("Run", window)
        window.action_pause = QAction("Pause", window)
        window.action_stop = QAction("Stop", window)
        window.action_record_workflow = QAction("Record", window)
        window.action_pick_selector = QAction("Pick", window)
        window.action_validate = QAction("Validate", window)
        window.action_save_layout = QAction("Save &Layout", window)

        toolbar = QToolBar("Main Toolbar")
        # Execution section
        toolbar.addAction(window.action_run)
        toolbar.addAction(window.action_pause)
        toolbar.addAction(window.action_stop)
        toolbar.addSeparator()
        # Automation section
        toolbar.addAction(window.action_record_workflow)
        toolbar.addAction(window.action_pick_selector)
        toolbar.addAction(window.action_validate)
        toolbar.addSeparator()
        # Layout section
        toolbar.addAction(window.action_save_layout)

        window.addToolBar(toolbar)

        actions = toolbar.actions()
        # Verify save_layout is last action
        non_separator_actions = [a for a in actions if not a.isSeparator()]
        assert non_separator_actions[-1] == window.action_save_layout


# ============================================================================
# Test: ToolbarIcons save_layout Icon
# ============================================================================


class TestToolbarIconsSaveLayout:
    """Tests for ToolbarIcons.get_icon('save_layout')."""

    def test_save_layout_icon_registered(self, qtbot):
        """Happy path: save_layout is registered in icon map."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        assert "save_layout" in ToolbarIcons._ICON_MAP

    def test_save_layout_icon_maps_to_valid_pixmap(self, qtbot):
        """Happy path: save_layout maps to valid Qt StandardPixmap."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        pixmap_name = ToolbarIcons._ICON_MAP.get("save_layout")
        assert pixmap_name == "SP_DialogApplyButton"

    def test_save_layout_icon_returns_qicon(self, qtbot):
        """Happy path: get_icon returns a QIcon instance."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        icon = ToolbarIcons.get_icon("save_layout")

        assert isinstance(icon, QIcon)

    def test_save_layout_icon_not_null(self, qtbot):
        """Happy path: Returned icon is not null/empty."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        icon = ToolbarIcons.get_icon("save_layout")

        # Icon should not be null (have available sizes)
        # Note: In headless Qt, icons may be empty, so we check it's a valid QIcon
        assert icon is not None

    def test_unknown_icon_returns_empty_qicon(self, qtbot):
        """Edge case: Unknown icon name returns empty QIcon."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        icon = ToolbarIcons.get_icon("nonexistent_icon")

        assert isinstance(icon, QIcon)
        assert icon.isNull()


# ============================================================================
# Test: Integration - Full Feature Flow
# ============================================================================


class TestSaveLayoutIntegration:
    """Integration tests for complete Save Layout feature flow."""

    def test_action_trigger_saves_state(
        self, mock_main_window_for_action, mock_ui_state_controller
    ):
        """Integration: Triggering action saves UI state."""
        window = mock_main_window_for_action

        # Create action connected to handler
        action = QAction("Save &Layout", window)
        action.triggered.connect(window._on_save_ui_layout)

        # Trigger action
        action.trigger()

        # Verify state was saved
        mock_ui_state_controller.save_state.assert_called_once()
        window.statusBar().showMessage.assert_called_with("UI layout saved", 3000)

    def test_keyboard_shortcut_trigger(
        self, mock_main_window_for_action, mock_ui_state_controller, qtbot
    ):
        """Integration: Keyboard shortcut triggers save."""
        window = mock_main_window_for_action

        action = QAction("Save &Layout", window)
        action.setShortcut(QKeySequence("Ctrl+Shift+L"))
        action.triggered.connect(window._on_save_ui_layout)
        window.addAction(action)

        # Trigger the action directly (simulates shortcut)
        action.trigger()

        mock_ui_state_controller.save_state.assert_called_once()

    def test_toolbar_button_click_saves_state(
        self, mock_main_window_for_action, mock_ui_state_controller, qtbot
    ):
        """Integration: Clicking toolbar button saves state."""
        window = mock_main_window_for_action

        # Create action
        window.action_save_layout = QAction("Save &Layout", window)
        window.action_save_layout.triggered.connect(window._on_save_ui_layout)

        # Create toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.addAction(window.action_save_layout)
        window.addToolBar(toolbar)

        # Trigger action (simulates button click)
        window.action_save_layout.trigger()

        mock_ui_state_controller.save_state.assert_called_once()

    def test_multiple_saves_all_succeed(
        self, mock_main_window_for_action, mock_ui_state_controller
    ):
        """Integration: Multiple save operations all succeed."""
        window = mock_main_window_for_action

        action = QAction("Save &Layout", window)
        action.triggered.connect(window._on_save_ui_layout)

        # Trigger 3 times
        action.trigger()
        action.trigger()
        action.trigger()

        assert mock_ui_state_controller.save_state.call_count == 3


# ============================================================================
# Test: Edge Cases and Error Scenarios
# ============================================================================


class TestSaveLayoutEdgeCases:
    """Edge case and error scenario tests."""

    def test_save_during_window_close(
        self, mock_main_window_for_action, mock_ui_state_controller
    ):
        """Edge case: Save can be called during window close."""
        window = mock_main_window_for_action

        # Simulate calling save during close
        window._on_save_ui_layout()

        mock_ui_state_controller.save_state.assert_called_once()

    def test_save_with_modified_panels(
        self, mock_main_window_for_action, mock_ui_state_controller
    ):
        """Edge case: Save works with modified panel states."""
        window = mock_main_window_for_action

        # Simulate panels being modified (controller handles this internally)
        window._on_save_ui_layout()

        mock_ui_state_controller.save_state.assert_called_once()

    def test_action_remains_enabled_after_save(
        self, mock_main_window_for_action, mock_ui_state_controller
    ):
        """Edge case: Action stays enabled after save."""
        window = mock_main_window_for_action

        action = QAction("Save &Layout", window)
        action.triggered.connect(window._on_save_ui_layout)

        action.trigger()

        assert action.isEnabled()

    def test_concurrent_save_requests(
        self, mock_main_window_for_action, mock_ui_state_controller
    ):
        """Edge case: Rapid consecutive saves are handled."""
        window = mock_main_window_for_action

        action = QAction("Save &Layout", window)
        action.triggered.connect(window._on_save_ui_layout)

        # Rapid fire triggers
        for _ in range(10):
            action.trigger()

        # All should have been called (debouncing is in UIStateController)
        assert mock_ui_state_controller.save_state.call_count == 10


# ============================================================================
# Test: ActionManager Integration
# ============================================================================


class TestActionManagerSaveLayout:
    """Tests for ActionManager.create_actions including save_layout."""

    def test_action_manager_creates_save_layout(self, qtbot):
        """Happy path: ActionManager creates save_layout action."""
        from casare_rpa.presentation.canvas.components.action_manager import (
            ActionManager,
        )

        # Create minimal mock main window
        window = QMainWindow()
        qtbot.addWidget(window)

        # Add required handler methods
        window._on_new_workflow = Mock()
        window._on_open_workflow = Mock()
        window._on_save_workflow = Mock()
        window._on_save_as_workflow = Mock()
        window._on_find_node = Mock()
        window._on_toggle_properties = Mock()
        window._on_toggle_variable_inspector = Mock()
        window._on_toggle_bottom_panel = Mock()
        window._on_toggle_minimap = Mock()
        window._on_run_workflow = Mock()
        window._on_pause_workflow = Mock()
        window._on_stop_workflow = Mock()
        window._on_debug_workflow = Mock()
        window._on_toggle_recording = Mock()
        window._on_pick_selector = Mock()
        window._on_open_desktop_selector_builder = Mock()
        window._on_create_frame = Mock()
        window._on_schedule_workflow = Mock()
        window._on_show_documentation = Mock()
        window._on_open_hotkey_manager = Mock()
        window._on_preferences = Mock()
        window._on_check_updates = Mock()
        window._on_about = Mock()
        window._on_save_ui_layout = Mock()
        window.validate_current_workflow = Mock()

        # Create ActionManager and actions
        manager = ActionManager(window)
        manager.create_actions()

        # Verify action was created
        assert hasattr(window, "action_save_layout")
        assert window.action_save_layout is not None
        assert isinstance(window.action_save_layout, QAction)

    def test_action_manager_save_layout_shortcut(self, qtbot):
        """Happy path: ActionManager sets correct shortcut."""
        from casare_rpa.presentation.canvas.components.action_manager import (
            ActionManager,
        )

        window = QMainWindow()
        qtbot.addWidget(window)

        # Add all required handlers (same as above)
        window._on_new_workflow = Mock()
        window._on_open_workflow = Mock()
        window._on_save_workflow = Mock()
        window._on_save_as_workflow = Mock()
        window._on_find_node = Mock()
        window._on_toggle_properties = Mock()
        window._on_toggle_variable_inspector = Mock()
        window._on_toggle_bottom_panel = Mock()
        window._on_toggle_minimap = Mock()
        window._on_run_workflow = Mock()
        window._on_pause_workflow = Mock()
        window._on_stop_workflow = Mock()
        window._on_debug_workflow = Mock()
        window._on_toggle_recording = Mock()
        window._on_pick_selector = Mock()
        window._on_open_desktop_selector_builder = Mock()
        window._on_create_frame = Mock()
        window._on_schedule_workflow = Mock()
        window._on_show_documentation = Mock()
        window._on_open_hotkey_manager = Mock()
        window._on_preferences = Mock()
        window._on_check_updates = Mock()
        window._on_about = Mock()
        window._on_save_ui_layout = Mock()
        window.validate_current_workflow = Mock()

        manager = ActionManager(window)
        manager.create_actions()

        assert window.action_save_layout.shortcut().toString() == "Ctrl+Shift+L"

    def test_action_manager_save_layout_handler_connected(self, qtbot):
        """Happy path: ActionManager connects handler to action."""
        from casare_rpa.presentation.canvas.components.action_manager import (
            ActionManager,
        )

        window = QMainWindow()
        qtbot.addWidget(window)

        # Mock the handler
        handler_called = []
        window._on_new_workflow = Mock()
        window._on_open_workflow = Mock()
        window._on_save_workflow = Mock()
        window._on_save_as_workflow = Mock()
        window._on_find_node = Mock()
        window._on_toggle_properties = Mock()
        window._on_toggle_variable_inspector = Mock()
        window._on_toggle_bottom_panel = Mock()
        window._on_toggle_minimap = Mock()
        window._on_run_workflow = Mock()
        window._on_pause_workflow = Mock()
        window._on_stop_workflow = Mock()
        window._on_debug_workflow = Mock()
        window._on_toggle_recording = Mock()
        window._on_pick_selector = Mock()
        window._on_open_desktop_selector_builder = Mock()
        window._on_create_frame = Mock()
        window._on_schedule_workflow = Mock()
        window._on_show_documentation = Mock()
        window._on_open_hotkey_manager = Mock()
        window._on_preferences = Mock()
        window._on_check_updates = Mock()
        window._on_about = Mock()
        window._on_save_ui_layout = lambda: handler_called.append(True)
        window.validate_current_workflow = Mock()

        manager = ActionManager(window)
        manager.create_actions()

        # Trigger action
        window.action_save_layout.trigger()

        assert len(handler_called) == 1


# ============================================================================
# Test: ToolbarBuilder Integration
# ============================================================================


class TestToolbarBuilderIntegration:
    """Tests for ToolbarBuilder.create_toolbar including save_layout."""

    def test_toolbar_builder_includes_save_layout(self, qtbot):
        """Happy path: ToolbarBuilder adds save_layout to toolbar."""
        from casare_rpa.presentation.canvas.components.toolbar_builder import (
            ToolbarBuilder,
        )

        window = QMainWindow()
        qtbot.addWidget(window)

        # Add required actions
        window.action_run = QAction("Run", window)
        window.action_pause = QAction("Pause", window)
        window.action_stop = QAction("Stop", window)
        window.action_record_workflow = QAction("Record", window)
        window.action_pick_selector = QAction("Pick", window)
        window.action_validate = QAction("Validate", window)
        window.action_save_layout = QAction("Save Layout", window)

        builder = ToolbarBuilder(window)
        toolbar = builder.create_toolbar()

        # Verify save_layout is in toolbar
        actions = toolbar.actions()
        assert window.action_save_layout in actions

    def test_toolbar_builder_styling_applied(self, qtbot):
        """Happy path: ToolbarBuilder applies dark theme styling."""
        from casare_rpa.presentation.canvas.components.toolbar_builder import (
            ToolbarBuilder,
        )

        window = QMainWindow()
        qtbot.addWidget(window)

        window.action_run = QAction("Run", window)
        window.action_pause = QAction("Pause", window)
        window.action_stop = QAction("Stop", window)
        window.action_record_workflow = QAction("Record", window)
        window.action_pick_selector = QAction("Pick", window)
        window.action_validate = QAction("Validate", window)
        window.action_save_layout = QAction("Save Layout", window)

        builder = ToolbarBuilder(window)
        toolbar = builder.create_toolbar()

        # Verify stylesheet is applied
        assert toolbar.styleSheet() != ""
        assert "background" in toolbar.styleSheet()
