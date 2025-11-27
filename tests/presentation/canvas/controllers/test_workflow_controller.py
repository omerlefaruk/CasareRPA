"""
Comprehensive tests for WorkflowController.

Tests workflow lifecycle operations including:
- New workflow creation
- Opening/loading workflows
- Saving workflows
- Save As functionality
- Import/export operations
- Unsaved changes handling
- Validation before save
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
from PySide6.QtWidgets import QMessageBox

from casare_rpa.presentation.canvas.controllers.workflow_controller import (
    WorkflowController,
)


@pytest.fixture
def mock_main_window():
    """Create a mock MainWindow with all required attributes."""
    mock = Mock()
    mock._central_widget = Mock()
    mock._central_widget.graph = Mock()
    mock._bottom_panel = Mock()
    mock._bottom_panel.get_validation_errors_blocking = Mock(return_value=[])
    mock._bottom_panel.trigger_validation = Mock()
    mock._bottom_panel.show_validation_tab = Mock()

    # Mock status bar
    mock_status = Mock()
    mock.statusBar = Mock(return_value=mock_status)

    # Mock actions
    mock.action_save = Mock()
    mock.action_save.setEnabled = Mock()

    # Mock window title setter
    mock.setWindowTitle = Mock()

    # Mock workflow signals
    mock.workflow_new_from_template = Mock()
    mock.workflow_new_from_template.emit = Mock()

    return mock


@pytest.fixture
def workflow_controller(mock_main_window):
    """Create a WorkflowController instance."""
    controller = WorkflowController(mock_main_window)
    controller.initialize()
    return controller


class TestWorkflowControllerInitialization:
    """Tests for WorkflowController initialization."""

    def test_initialization_success(self, mock_main_window):
        """Test controller initializes correctly."""
        controller = WorkflowController(mock_main_window)

        assert controller.main_window == mock_main_window
        assert controller._current_file is None
        assert controller._is_modified is False
        assert not controller.is_initialized()

    def test_initialize_sets_state(self, mock_main_window):
        """Test initialize() sets initialized state."""
        controller = WorkflowController(mock_main_window)
        controller.initialize()

        assert controller.is_initialized()

    def test_cleanup_resets_state(self, workflow_controller):
        """Test cleanup() resets initialized state."""
        workflow_controller.cleanup()

        assert not workflow_controller.is_initialized()


class TestWorkflowControllerProperties:
    """Tests for WorkflowController properties."""

    def test_current_file_property(self, workflow_controller):
        """Test current_file property getter."""
        assert workflow_controller.current_file is None

        test_path = Path("/test/workflow.json")
        workflow_controller._current_file = test_path
        assert workflow_controller.current_file == test_path

    def test_is_modified_property(self, workflow_controller):
        """Test is_modified property getter."""
        assert workflow_controller.is_modified is False

        workflow_controller._is_modified = True
        assert workflow_controller.is_modified is True


class TestNewWorkflow:
    """Tests for new workflow creation."""

    def test_new_workflow_success(self, workflow_controller, mock_main_window):
        """Test creating new workflow."""
        # Setup signal spy
        signal_emitted = []
        workflow_controller.workflow_created.connect(
            lambda: signal_emitted.append(True)
        )

        workflow_controller.new_workflow()

        assert len(signal_emitted) == 1
        assert workflow_controller.current_file is None
        assert not workflow_controller.is_modified
        mock_main_window.statusBar().showMessage.assert_called_with(
            "New workflow created", 3000
        )

    def test_new_workflow_cancelled_on_unsaved_changes(self, workflow_controller):
        """Test new workflow cancelled when user cancels unsaved changes dialog."""
        workflow_controller.set_modified(True)

        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.StandardButton.Cancel
        ):
            workflow_controller.new_workflow()

        # Should not emit signal or clear state
        assert workflow_controller.is_modified is True

    def test_new_workflow_discards_unsaved_changes(self, workflow_controller):
        """Test new workflow discards unsaved changes when user confirms."""
        workflow_controller.set_modified(True)
        workflow_controller.set_current_file(Path("/test/old.json"))

        signal_emitted = []
        workflow_controller.workflow_created.connect(
            lambda: signal_emitted.append(True)
        )

        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.StandardButton.Discard
        ):
            workflow_controller.new_workflow()

        assert len(signal_emitted) == 1
        assert workflow_controller.current_file is None
        assert not workflow_controller.is_modified

    def test_new_workflow_saves_before_continuing(self, workflow_controller):
        """Test new workflow saves current work when user chooses Save."""
        workflow_controller.set_modified(True)
        workflow_controller.set_current_file(Path("/test/current.json"))

        signal_emitted = []
        workflow_controller.workflow_created.connect(
            lambda: signal_emitted.append(True)
        )

        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.StandardButton.Save
        ):
            # Mock successful save
            workflow_controller.workflow_saved = Mock()
            workflow_controller.workflow_saved.emit = Mock()

            workflow_controller.new_workflow()

        # Should have attempted save
        assert len(signal_emitted) == 1


class TestNewFromTemplate:
    """Tests for new workflow from template."""

    @patch(
        "casare_rpa.presentation.canvas.controllers.workflow_controller.show_template_browser"
    )
    def test_new_from_template_cancelled(
        self, mock_browser, workflow_controller, mock_main_window
    ):
        """Test new from template cancelled when no template selected."""
        mock_browser.return_value = None

        workflow_controller.new_from_template()

        mock_browser.assert_called_once_with(mock_main_window)
        mock_main_window.workflow_new_from_template.emit.assert_not_called()

    @patch(
        "casare_rpa.presentation.canvas.controllers.workflow_controller.show_template_browser"
    )
    def test_new_from_template_success(
        self, mock_browser, workflow_controller, mock_main_window
    ):
        """Test new from template with template selection."""
        mock_template = Mock()
        mock_template.name = "Test Template"
        mock_browser.return_value = mock_template

        workflow_controller.new_from_template()

        mock_browser.assert_called_once_with(mock_main_window)
        mock_main_window.workflow_new_from_template.emit.assert_called_once_with(
            mock_template
        )
        mock_main_window.statusBar().showMessage.assert_called()


class TestOpenWorkflow:
    """Tests for opening workflow files."""

    @patch("casare_rpa.presentation.canvas.controllers.workflow_controller.QFileDialog")
    def test_open_workflow_cancelled(self, mock_dialog, workflow_controller):
        """Test open workflow cancelled when no file selected."""
        mock_dialog.getOpenFileName.return_value = ("", "")

        signal_emitted = []
        workflow_controller.workflow_loaded.connect(
            lambda _: signal_emitted.append(True)
        )

        workflow_controller.open_workflow()

        assert len(signal_emitted) == 0

    @patch("casare_rpa.presentation.canvas.controllers.workflow_controller.QFileDialog")
    def test_open_workflow_success(
        self, mock_dialog, workflow_controller, mock_main_window, tmp_path
    ):
        """Test open workflow with valid file."""
        test_file = tmp_path / "test_workflow.json"
        test_file.write_text('{"nodes": {}, "connections": []}')

        mock_dialog.getOpenFileName.return_value = (str(test_file), "*.json")

        signal_emitted = []
        workflow_controller.workflow_loaded.connect(
            lambda _: signal_emitted.append(True)
        )

        workflow_controller.open_workflow()

        assert len(signal_emitted) == 1
        assert workflow_controller.current_file == test_file
        assert not workflow_controller.is_modified
        mock_main_window.statusBar().showMessage.assert_called()

    @patch("casare_rpa.presentation.canvas.controllers.workflow_controller.QFileDialog")
    def test_open_workflow_checks_unsaved_changes(
        self, mock_dialog, workflow_controller
    ):
        """Test open workflow checks for unsaved changes."""
        workflow_controller.set_modified(True)

        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.StandardButton.Cancel
        ):
            workflow_controller.open_workflow()

        # Should not open file dialog
        mock_dialog.getOpenFileName.assert_not_called()

    @patch("casare_rpa.presentation.canvas.controllers.workflow_controller.QFileDialog")
    @patch("casare_rpa.presentation.canvas.controllers.workflow_controller.QTimer")
    def test_open_workflow_triggers_validation(
        self, mock_timer, mock_dialog, workflow_controller, tmp_path
    ):
        """Test open workflow schedules validation after loading."""
        test_file = tmp_path / "test_workflow.json"
        test_file.write_text('{"nodes": {}, "connections": []}')

        mock_dialog.getOpenFileName.return_value = (str(test_file), "*.json")

        workflow_controller.open_workflow()

        # Should schedule validation
        mock_timer.singleShot.assert_called_once()


class TestSaveWorkflow:
    """Tests for saving workflow files."""

    def test_save_workflow_without_current_file(self, workflow_controller):
        """Test save workflow without current file calls save_as."""
        with patch.object(workflow_controller, "save_workflow_as") as mock_save_as:
            workflow_controller.save_workflow()

        mock_save_as.assert_called_once()

    def test_save_workflow_with_current_file(
        self, workflow_controller, mock_main_window, tmp_path
    ):
        """Test save workflow with existing file."""
        test_file = tmp_path / "existing.json"
        workflow_controller.set_current_file(test_file)
        workflow_controller.set_modified(True)

        signal_emitted = []
        workflow_controller.workflow_saved.connect(
            lambda _: signal_emitted.append(True)
        )

        workflow_controller.save_workflow()

        assert len(signal_emitted) == 1
        assert not workflow_controller.is_modified
        mock_main_window.statusBar().showMessage.assert_called()

    def test_save_workflow_validation_blocks_save(
        self, workflow_controller, mock_main_window
    ):
        """Test save workflow blocked by validation errors."""
        test_file = Path("/test/workflow.json")
        workflow_controller.set_current_file(test_file)

        # Mock validation errors
        mock_main_window._bottom_panel.get_validation_errors_blocking.return_value = [
            {"node_id": "node1", "error": "Missing required field"}
        ]

        with patch.object(
            QMessageBox, "warning", return_value=QMessageBox.StandardButton.No
        ):
            workflow_controller.save_workflow()

        # Validation panel should be shown
        mock_main_window._bottom_panel.show_validation_tab.assert_called_once()

    def test_save_workflow_validation_user_proceeds(
        self, workflow_controller, mock_main_window, tmp_path
    ):
        """Test save workflow proceeds despite validation errors when user confirms."""
        test_file = tmp_path / "workflow.json"
        workflow_controller.set_current_file(test_file)

        # Mock validation errors
        mock_main_window._bottom_panel.get_validation_errors_blocking.return_value = [
            {"node_id": "node1", "error": "Warning"}
        ]

        signal_emitted = []
        workflow_controller.workflow_saved.connect(
            lambda _: signal_emitted.append(True)
        )

        with patch.object(
            QMessageBox, "warning", return_value=QMessageBox.StandardButton.Yes
        ):
            workflow_controller.save_workflow()

        assert len(signal_emitted) == 1


class TestSaveWorkflowAs:
    """Tests for save workflow as functionality."""

    @patch("casare_rpa.presentation.canvas.controllers.workflow_controller.QFileDialog")
    def test_save_as_cancelled(self, mock_dialog, workflow_controller):
        """Test save as cancelled when no file selected."""
        mock_dialog.getSaveFileName.return_value = ("", "")

        signal_emitted = []
        workflow_controller.workflow_saved.connect(
            lambda _: signal_emitted.append(True)
        )

        workflow_controller.save_workflow_as()

        assert len(signal_emitted) == 0

    @patch("casare_rpa.presentation.canvas.controllers.workflow_controller.QFileDialog")
    def test_save_as_success(
        self, mock_dialog, workflow_controller, mock_main_window, tmp_path
    ):
        """Test save as with new file name."""
        test_file = tmp_path / "new_workflow.json"
        mock_dialog.getSaveFileName.return_value = (str(test_file), "*.json")

        workflow_controller.set_modified(True)

        signal_emitted = []
        workflow_controller.workflow_saved.connect(
            lambda _: signal_emitted.append(True)
        )

        workflow_controller.save_workflow_as()

        assert len(signal_emitted) == 1
        assert workflow_controller.current_file == test_file
        assert not workflow_controller.is_modified
        mock_main_window.statusBar().showMessage.assert_called()


class TestImportWorkflow:
    """Tests for importing workflow files."""

    @patch("casare_rpa.presentation.canvas.controllers.workflow_controller.QFileDialog")
    def test_import_workflow_cancelled(self, mock_dialog, workflow_controller):
        """Test import workflow cancelled."""
        mock_dialog.getOpenFileName.return_value = ("", "")

        signal_emitted = []
        workflow_controller.workflow_imported.connect(
            lambda _: signal_emitted.append(True)
        )

        workflow_controller.import_workflow()

        assert len(signal_emitted) == 0

    @patch("casare_rpa.presentation.canvas.controllers.workflow_controller.QFileDialog")
    def test_import_workflow_success(
        self, mock_dialog, workflow_controller, mock_main_window, tmp_path
    ):
        """Test import workflow success."""
        test_file = tmp_path / "import.json"
        test_file.write_text('{"nodes": {}, "connections": []}')

        mock_dialog.getOpenFileName.return_value = (str(test_file), "*.json")

        signal_emitted = []
        workflow_controller.workflow_imported.connect(
            lambda _: signal_emitted.append(True)
        )

        workflow_controller.import_workflow()

        assert len(signal_emitted) == 1
        mock_main_window.statusBar().showMessage.assert_called()


class TestExportSelectedNodes:
    """Tests for exporting selected nodes."""

    def test_export_no_graph_available(self, workflow_controller, mock_main_window):
        """Test export when no graph is available."""
        mock_main_window._central_widget = None

        workflow_controller.export_selected_nodes()

        mock_main_window.statusBar().showMessage.assert_called_with(
            "No graph available", 3000
        )

    def test_export_no_nodes_selected(self, workflow_controller, mock_main_window):
        """Test export when no nodes are selected."""
        mock_main_window._central_widget.graph.selected_nodes.return_value = []

        with patch.object(QMessageBox, "information") as mock_info:
            workflow_controller.export_selected_nodes()

        mock_info.assert_called_once()

    @patch("casare_rpa.presentation.canvas.controllers.workflow_controller.QFileDialog")
    def test_export_selected_nodes_success(
        self, mock_dialog, workflow_controller, mock_main_window
    ):
        """Test export selected nodes success."""
        mock_node1 = Mock()
        mock_node2 = Mock()
        mock_main_window._central_widget.graph.selected_nodes.return_value = [
            mock_node1,
            mock_node2,
        ]

        mock_dialog.getSaveFileName.return_value = ("/test/export.json", "*.json")

        signal_emitted = []
        workflow_controller.workflow_exported.connect(
            lambda _: signal_emitted.append(True)
        )

        workflow_controller.export_selected_nodes()

        assert len(signal_emitted) == 1
        mock_main_window.statusBar().showMessage.assert_called()


class TestCloseWorkflow:
    """Tests for closing workflow."""

    def test_close_workflow_no_changes(self, workflow_controller):
        """Test close workflow with no unsaved changes."""
        signal_emitted = []
        workflow_controller.workflow_closed.connect(lambda: signal_emitted.append(True))

        result = workflow_controller.close_workflow()

        assert result is True
        assert len(signal_emitted) == 1
        assert workflow_controller.current_file is None
        assert not workflow_controller.is_modified

    def test_close_workflow_with_unsaved_cancelled(self, workflow_controller):
        """Test close workflow cancelled on unsaved changes."""
        workflow_controller.set_modified(True)

        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.StandardButton.Cancel
        ):
            result = workflow_controller.close_workflow()

        assert result is False
        assert workflow_controller.is_modified is True


class TestSetters:
    """Tests for setter methods."""

    def test_set_current_file(self, workflow_controller):
        """Test set_current_file updates state and emits signal."""
        signal_values = []
        workflow_controller.current_file_changed.connect(
            lambda val: signal_values.append(val)
        )

        test_path = Path("/test/workflow.json")
        workflow_controller.set_current_file(test_path)

        assert workflow_controller.current_file == test_path
        assert len(signal_values) == 1
        assert signal_values[0] == test_path

    def test_set_current_file_no_change(self, workflow_controller):
        """Test set_current_file doesn't emit signal when value unchanged."""
        signal_values = []
        workflow_controller.current_file_changed.connect(
            lambda val: signal_values.append(val)
        )

        workflow_controller.set_current_file(None)

        assert len(signal_values) == 0

    def test_set_modified(self, workflow_controller):
        """Test set_modified updates state and emits signal."""
        signal_values = []
        workflow_controller.modified_changed.connect(
            lambda val: signal_values.append(val)
        )

        workflow_controller.set_modified(True)

        assert workflow_controller.is_modified is True
        assert len(signal_values) == 1
        assert signal_values[0] is True

    def test_set_modified_no_change(self, workflow_controller):
        """Test set_modified doesn't emit signal when value unchanged."""
        signal_values = []
        workflow_controller.modified_changed.connect(
            lambda val: signal_values.append(val)
        )

        workflow_controller.set_modified(False)

        assert len(signal_values) == 0


class TestPrivateMethods:
    """Tests for private helper methods."""

    def test_check_unsaved_changes_no_changes(self, workflow_controller):
        """Test check_unsaved_changes returns True when no changes."""
        result = workflow_controller.check_unsaved_changes()

        assert result is True

    def test_check_unsaved_changes_user_saves(self, workflow_controller, tmp_path):
        """Test check_unsaved_changes saves when user chooses Save."""
        workflow_controller.set_modified(True)
        test_file = tmp_path / "test.json"
        workflow_controller.set_current_file(test_file)

        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.StandardButton.Save
        ):
            result = workflow_controller.check_unsaved_changes()

        # After successful save, should return True
        assert result is True

    def test_check_unsaved_changes_user_discards(self, workflow_controller):
        """Test check_unsaved_changes discards when user chooses Discard."""
        workflow_controller.set_modified(True)

        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.StandardButton.Discard
        ):
            result = workflow_controller.check_unsaved_changes()

        assert result is True

    def test_check_unsaved_changes_user_cancels(self, workflow_controller):
        """Test check_unsaved_changes cancels when user chooses Cancel."""
        workflow_controller.set_modified(True)

        with patch.object(
            QMessageBox, "question", return_value=QMessageBox.StandardButton.Cancel
        ):
            result = workflow_controller.check_unsaved_changes()

        assert result is False

    def test_update_window_title_untitled(self, workflow_controller, mock_main_window):
        """Test _update_window_title with no file."""
        with patch(
            "casare_rpa.presentation.canvas.controllers.workflow_controller.APP_NAME",
            "CasareRPA",
        ):
            workflow_controller._update_window_title()

        mock_main_window.setWindowTitle.assert_called()
        call_arg = mock_main_window.setWindowTitle.call_args[0][0]
        assert "Untitled" in call_arg
        assert "CasareRPA" in call_arg

    def test_update_window_title_with_file(self, workflow_controller, mock_main_window):
        """Test _update_window_title with file."""
        test_file = Path("/test/myworkflow.json")
        workflow_controller.set_current_file(test_file)

        with patch(
            "casare_rpa.presentation.canvas.controllers.workflow_controller.APP_NAME",
            "CasareRPA",
        ):
            workflow_controller._update_window_title()

        mock_main_window.setWindowTitle.assert_called()
        call_arg = mock_main_window.setWindowTitle.call_args[0][0]
        assert "myworkflow.json" in call_arg

    def test_update_window_title_modified(self, workflow_controller, mock_main_window):
        """Test _update_window_title shows asterisk when modified."""
        workflow_controller.set_modified(True)

        with patch(
            "casare_rpa.presentation.canvas.controllers.workflow_controller.APP_NAME",
            "CasareRPA",
        ):
            workflow_controller._update_window_title()

        mock_main_window.setWindowTitle.assert_called()
        call_arg = mock_main_window.setWindowTitle.call_args[0][0]
        assert "*" in call_arg

    def test_update_save_action(self, workflow_controller, mock_main_window):
        """Test _update_save_action enables/disables save action."""
        workflow_controller.set_modified(True)

        mock_main_window.action_save.setEnabled.assert_called_with(True)

        workflow_controller.set_modified(False)

        mock_main_window.action_save.setEnabled.assert_called_with(False)
