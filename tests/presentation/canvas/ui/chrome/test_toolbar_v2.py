"""
Tests for ToolbarV2 component.

Epic 4.2: Chrome - Top Toolbar + Status Bar v2

This test suite covers:
- ToolbarV2 creation and initialization
- Action creation and availability
- Signal emission
- Execution state management
- Undo/Redo state management

Run: pytest tests/presentation/canvas/ui/chrome/test_toolbar_v2.py -v
"""


# =============================================================================
# ToolbarV2 Creation Tests
# =============================================================================


class TestToolbarV2Creation:
    """Tests for ToolbarV2 instantiation."""

    def test_creates_with_qapp(self, qapp) -> None:
        """Test ToolbarV2 can be instantiated."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        assert toolbar is not None
        assert toolbar.windowTitle() == "Main"
        assert not toolbar.isMovable()
        assert not toolbar.isFloatable()

    def test_creates_with_parent(self, qapp) -> None:
        """Test ToolbarV2 with parent widget."""
        from PySide6.QtWidgets import QWidget

        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        parent = QWidget()
        toolbar = ToolbarV2(parent=parent)
        assert toolbar.parent() == parent


# =============================================================================
# ToolbarV2 Action Tests
# =============================================================================


class TestToolbarV2Actions:
    """Tests for toolbar actions."""

    def test_all_actions_exist(self, qapp) -> None:
        """Test all required actions are created."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        required = [
            "action_new",
            "action_open",
            "action_save",
            "action_save_as",
            "action_undo",
            "action_redo",
            "action_run",
            "action_pause",
            "action_stop",
        ]
        for name in required:
            assert hasattr(toolbar, name), f"Missing action: {name}"

    def test_actions_have_icons(self, qapp) -> None:
        """Test all actions have icons set."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        actions = [
            toolbar.action_new,
            toolbar.action_open,
            toolbar.action_save,
            toolbar.action_undo,
            toolbar.action_redo,
            toolbar.action_run,
            toolbar.action_stop,
        ]
        for action in actions:
            assert not action.icon().isNull(), f"Action {action.text()} missing icon"

    def test_actions_have_tooltips(self, qapp) -> None:
        """Test all actions have tooltips set."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        actions = [
            toolbar.action_new,
            toolbar.action_open,
            toolbar.action_save,
            toolbar.action_run,
            toolbar.action_stop,
        ]
        for action in actions:
            assert len(action.toolTip()) > 0, f"Action {action.text()} missing tooltip"


# =============================================================================
# ToolbarV2 Signal Tests
# =============================================================================


class TestToolbarV2Signals:
    """Tests for toolbar signal emission."""

    def test_signals_exist(self, qapp) -> None:
        """Test all required signals are defined."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        required_signals = [
            "new_requested",
            "open_requested",
            "save_requested",
            "save_as_requested",
            "run_requested",
            "pause_requested",
            "stop_requested",
            "undo_requested",
            "redo_requested",
        ]
        for name in required_signals:
            assert hasattr(toolbar, name), f"Missing signal: {name}"

    def test_new_emits_signal(self, qapp, signal_capture) -> None:
        """Test new action emits new_requested signal."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        toolbar.new_requested.connect(signal_capture.slot)
        toolbar.action_new.trigger()
        assert signal_capture.called

    def test_open_emits_signal(self, qapp, signal_capture) -> None:
        """Test open action emits open_requested signal."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        toolbar.open_requested.connect(signal_capture.slot)
        toolbar.action_open.trigger()
        assert signal_capture.called

    def test_save_emits_signal(self, qapp, signal_capture) -> None:
        """Test save action emits save_requested signal."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        toolbar.save_requested.connect(signal_capture.slot)
        toolbar.action_save.trigger()
        assert signal_capture.called

    def test_run_emits_signal(self, qapp, signal_capture) -> None:
        """Test run action emits run_requested signal."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        toolbar.run_requested.connect(signal_capture.slot)
        toolbar.action_run.trigger()
        assert signal_capture.called

    def test_pause_emits_signal(self, qapp, signal_capture) -> None:
        """Test pause action emits pause_requested signal."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        toolbar.pause_requested.connect(signal_capture.slot)
        toolbar.action_pause.setEnabled(True)  # Pause needs to be enabled
        toolbar.action_pause.trigger()
        assert signal_capture.called

    def test_stop_emits_signal(self, qapp, signal_capture) -> None:
        """Test stop action emits stop_requested signal."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        toolbar.stop_requested.connect(signal_capture.slot)
        toolbar.action_stop.setEnabled(True)  # Stop needs to be enabled
        toolbar.action_stop.trigger()
        assert signal_capture.called

    def test_undo_emits_signal(self, qapp, signal_capture) -> None:
        """Test undo action emits undo_requested signal."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        toolbar.undo_requested.connect(signal_capture.slot)
        toolbar.action_undo.trigger()
        assert signal_capture.called

    def test_redo_emits_signal(self, qapp, signal_capture) -> None:
        """Test redo action emits redo_requested signal."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        toolbar.redo_requested.connect(signal_capture.slot)
        toolbar.action_redo.trigger()
        assert signal_capture.called


# =============================================================================
# ToolbarV2 Execution State Tests
# =============================================================================


class TestToolbarV2ExecutionState:
    """Tests for execution state management."""

    def test_running_state_disables_run(self, qapp) -> None:
        """Test run button disabled during execution."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        toolbar.set_execution_state(is_running=True)
        assert not toolbar.action_run.isEnabled()
        assert toolbar.action_stop.isEnabled()

    def test_ready_state_enables_run(self, qapp) -> None:
        """Test run button enabled when not running."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        toolbar.set_execution_state(is_running=False)
        assert toolbar.action_run.isEnabled()
        assert not toolbar.action_stop.isEnabled()

    def test_paused_state_disables_pause(self, qapp) -> None:
        """Test pause button disabled when paused."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        toolbar.set_execution_state(is_running=True, is_paused=True)
        assert not toolbar.action_pause.isEnabled()

    def test_running_pause_enabled(self, qapp) -> None:
        """Test pause button enabled when running and not paused."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        toolbar.set_execution_state(is_running=True, is_paused=False)
        assert toolbar.action_pause.isEnabled()

    def test_file_operations_disabled_during_run(self, qapp) -> None:
        """Test file operations disabled during execution."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        toolbar.set_execution_state(is_running=True)
        assert not toolbar.action_new.isEnabled()
        assert not toolbar.action_open.isEnabled()

    def test_file_operations_enabled_when_idle(self, qapp) -> None:
        """Test file operations enabled when idle."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        toolbar.set_execution_state(is_running=False)
        assert toolbar.action_new.isEnabled()
        assert toolbar.action_open.isEnabled()


# =============================================================================
# ToolbarV2 Undo/Redo Tests
# =============================================================================


class TestToolbarV2UndoRedo:
    """Tests for undo/redo state management."""

    def test_undo_enabled(self, qapp) -> None:
        """Test set_undo_enabled enables undo action."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        toolbar.set_undo_enabled(True)
        assert toolbar.action_undo.isEnabled()

    def test_undo_disabled(self, qapp) -> None:
        """Test set_undo_enabled with False disables undo action."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        toolbar.set_undo_enabled(False)
        assert not toolbar.action_undo.isEnabled()

    def test_redo_enabled(self, qapp) -> None:
        """Test set_redo_enabled enables redo action."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        toolbar.set_redo_enabled(True)
        assert toolbar.action_redo.isEnabled()

    def test_redo_disabled(self, qapp) -> None:
        """Test set_redo_enabled with False disables redo action."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        toolbar.set_redo_enabled(False)
        assert not toolbar.action_redo.isEnabled()


# =============================================================================
# ToolbarV2 Inheritance Tests
# =============================================================================


class TestToolbarV2Inheritance:
    """Tests for ToolbarV2 class hierarchy."""

    def test_inherits_from_qtoolbar(self, qapp) -> None:
        """Test ToolbarV2 inherits from QToolBar."""
        from PySide6.QtWidgets import QToolBar

        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        assert issubclass(ToolbarV2, QToolBar)

    def test_has_toolbar_methods(self, qapp) -> None:
        """Test ToolbarV2 has standard QToolBar methods."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        assert hasattr(toolbar, "addAction")
        assert hasattr(toolbar, "addSeparator")
        assert hasattr(toolbar, "setMovable")
        assert hasattr(toolbar, "setFloatable")


# =============================================================================
# ToolbarV2 Integration Tests
# =============================================================================


class TestToolbarV2Integration:
    """Integration tests for ToolbarV2 usage patterns."""

    def test_multiple_signal_connections(self, qapp, signal_capture) -> None:
        """Test multiple handlers can connect to same signal."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        handler1_calls = []
        handler2_calls = []

        def handler1():
            handler1_calls.append(True)

        def handler2():
            handler2_calls.append(True)

        toolbar.run_requested.connect(handler1)
        toolbar.run_requested.connect(handler2)
        toolbar.action_run.trigger()

        assert len(handler1_calls) == 1
        assert len(handler2_calls) == 1

    def test_state_changes_without_crash(self, qapp) -> None:
        """Test multiple state changes don't cause crashes."""
        from casare_rpa.presentation.canvas.ui.chrome import ToolbarV2

        toolbar = ToolbarV2()
        for _ in range(100):
            toolbar.set_execution_state(True, False)
            toolbar.set_execution_state(False, False)
            toolbar.set_undo_enabled(True)
            toolbar.set_redo_enabled(False)
        # Should not crash
