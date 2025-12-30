"""
Tests for StatusBarV2 component.

Epic 4.2: Chrome - Top Toolbar + Status Bar v2

This test suite covers:
- StatusBarV2 creation and initialization
- Execution status updates
- Zoom display updates
- Theme-aware status colors

Run: pytest tests/presentation/canvas/ui/chrome/test_statusbar_v2.py -v
"""


# =============================================================================
# StatusBarV2 Creation Tests
# =============================================================================


class TestStatusBarV2Creation:
    """Tests for StatusBarV2 instantiation."""

    def test_creates_with_qapp(self, qapp) -> None:
        """Test StatusBarV2 can be instantiated."""
        from casare_rpa.presentation.canvas.ui.chrome import StatusBarV2

        bar = StatusBarV2()
        assert bar is not None
        assert bar.objectName() == "StatusBarV2"

    def test_creates_with_parent(self, qapp) -> None:
        """Test StatusBarV2 with parent widget."""
        from PySide6.QtWidgets import QWidget

        from casare_rpa.presentation.canvas.ui.chrome import StatusBarV2

        parent = QWidget()
        bar = StatusBarV2(parent=parent)
        assert bar.parent() == parent


# =============================================================================
# StatusBarV2 Widget Tests
# =============================================================================


class TestStatusBarV2Widgets:
    """Tests for status bar widget creation."""

    def test_has_exec_status_label(self, qapp) -> None:
        """Test execution status label is created."""
        from casare_rpa.presentation.canvas.ui.chrome import StatusBarV2

        bar = StatusBarV2()
        assert bar._exec_status_label is not None
        assert bar._exec_status_label.text() == "Ready"

    def test_has_zoom_label(self, qapp) -> None:
        """Test zoom label is created."""
        from casare_rpa.presentation.canvas.ui.chrome import StatusBarV2

        bar = StatusBarV2()
        assert bar._zoom_label is not None
        assert "100" in bar._zoom_label.text()


# =============================================================================
# StatusBarV2 Execution Status Tests
# =============================================================================


class TestStatusBarV2ExecutionStatus:
    """Tests for execution status updates."""

    def test_ready_status(self, qapp) -> None:
        """Test ready status display."""
        from casare_rpa.presentation.canvas.ui.chrome import StatusBarV2

        bar = StatusBarV2()
        bar.set_execution_status("ready")
        assert "Ready" in bar._exec_status_label.text()

    def test_running_status(self, qapp) -> None:
        """Test running status display."""
        from casare_rpa.presentation.canvas.ui.chrome import StatusBarV2

        bar = StatusBarV2()
        bar.set_execution_status("running")
        assert "Running" in bar._exec_status_label.text()

    def test_paused_status(self, qapp) -> None:
        """Test paused status display."""
        from casare_rpa.presentation.canvas.ui.chrome import StatusBarV2

        bar = StatusBarV2()
        bar.set_execution_status("paused")
        assert "Paused" in bar._exec_status_label.text()

    def test_error_status(self, qapp) -> None:
        """Test error status display."""
        from casare_rpa.presentation.canvas.ui.chrome import StatusBarV2

        bar = StatusBarV2()
        bar.set_execution_status("error")
        assert "Error" in bar._exec_status_label.text()

    def test_success_status(self, qapp) -> None:
        """Test success status display."""
        from casare_rpa.presentation.canvas.ui.chrome import StatusBarV2

        bar = StatusBarV2()
        bar.set_execution_status("success")
        assert "Complete" in bar._exec_status_label.text()

    def test_invalid_status_defaults_to_ready(self, qapp) -> None:
        """Test invalid status defaults to ready."""
        from casare_rpa.presentation.canvas.ui.chrome import StatusBarV2

        bar = StatusBarV2()
        bar.set_execution_status("invalid_status")
        assert "Ready" in bar._exec_status_label.text()


# =============================================================================
# StatusBarV2 Zoom Tests
# =============================================================================


class TestStatusBarV2Zoom:
    """Tests for zoom display updates."""

    def test_default_zoom(self, qapp) -> None:
        """Test default zoom is 100%."""
        from casare_rpa.presentation.canvas.ui.chrome import StatusBarV2

        bar = StatusBarV2()
        assert "100" in bar._zoom_label.text()

    def test_set_zoom_150(self, qapp) -> None:
        """Test zoom display updates to 150%."""
        from casare_rpa.presentation.canvas.ui.chrome import StatusBarV2

        bar = StatusBarV2()
        bar.set_zoom(150.0)
        assert "150" in bar._zoom_label.text()

    def test_set_zoom_50(self, qapp) -> None:
        """Test zoom display updates to 50%."""
        from casare_rpa.presentation.canvas.ui.chrome import StatusBarV2

        bar = StatusBarV2()
        bar.set_zoom(50.0)
        assert "50" in bar._zoom_label.text()

    def test_set_zoom_200(self, qapp) -> None:
        """Test zoom display updates to 200%."""
        from casare_rpa.presentation.canvas.ui.chrome import StatusBarV2

        bar = StatusBarV2()
        bar.set_zoom(200.0)
        assert "200" in bar._zoom_label.text()

    def test_set_zoom_float_rounds(self, qapp) -> None:
        """Test zoom percentage is rounded to integer."""
        from casare_rpa.presentation.canvas.ui.chrome import StatusBarV2

        bar = StatusBarV2()
        bar.set_zoom(125.7)
        assert "125" in bar._zoom_label.text()


# =============================================================================
# StatusBarV2 Inheritance Tests
# =============================================================================


class TestStatusBarV2Inheritance:
    """Tests for StatusBarV2 class hierarchy."""

    def test_inherits_from_qstatusbar(self, qapp) -> None:
        """Test StatusBarV2 inherits from QStatusBar."""
        from PySide6.QtWidgets import QStatusBar

        from casare_rpa.presentation.canvas.ui.chrome import StatusBarV2

        assert issubclass(StatusBarV2, QStatusBar)

    def test_has_statusbar_methods(self, qapp) -> None:
        """Test StatusBarV2 has standard QStatusBar methods."""
        from casare_rpa.presentation.canvas.ui.chrome import StatusBarV2

        bar = StatusBarV2()
        assert hasattr(bar, "addPermanentWidget")
        assert hasattr(bar, "showMessage")
        assert hasattr(bar, "clearMessage")


# =============================================================================
# StatusBarV2 Integration Tests
# =============================================================================


class TestStatusBarV2Integration:
    """Integration tests for StatusBarV2 usage patterns."""

    def test_status_and_zoom_independent(self, qapp) -> None:
        """Test status and zoom updates don't interfere."""
        from casare_rpa.presentation.canvas.ui.chrome import StatusBarV2

        bar = StatusBarV2()
        bar.set_execution_status("running")
        bar.set_zoom(150.0)
        assert "Running" in bar._exec_status_label.text()
        assert "150" in bar._zoom_label.text()

    def test_multiple_status_changes(self, qapp) -> None:
        """Test multiple status changes work correctly."""
        from casare_rpa.presentation.canvas.ui.chrome import StatusBarV2

        bar = StatusBarV2()
        states = ["ready", "running", "paused", "success", "error"]
        for state in states:
            bar.set_execution_status(state)
            assert bar._exec_status_label.text() != ""

    def test_multiple_zoom_changes(self, qapp) -> None:
        """Test multiple zoom changes work correctly."""
        from casare_rpa.presentation.canvas.ui.chrome import StatusBarV2

        bar = StatusBarV2()
        zooms = [50.0, 100.0, 150.0, 200.0, 75.0]
        for zoom in zooms:
            bar.set_zoom(zoom)
            assert str(int(zoom)) in bar._zoom_label.text()
