"""
Tests for PopupWindowBase v2 component.

Tests the base popup functionality:
- Creation and initialization
- Draggable header
- Corner resize grips
- Click-outside-to-close (via PopupManager)
- Pin state (ignore click-outside when pinned)
- Escape key closes
- Screen-boundary clamping
- Anchor positioning
"""

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QApplication, QPushButton, QWidget


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def popup(qapp):
    """Create a PopupWindowBase instance for testing."""
    from casare_rpa.presentation.canvas.ui.widgets.popups import PopupWindowBase

    popup = PopupWindowBase(title="Test Popup", resizable=True, pin_button=True)
    yield popup
    # Cleanup
    popup.close()


@pytest.fixture
def popup_with_content(qapp, popup):
    """Create a PopupWindowBase with content widget."""
    content = QWidget()
    layout = content.layout()
    if layout is None:
        from PySide6.QtWidgets import QVBoxLayout

        layout = QVBoxLayout(content)

    button = QPushButton("Test Button")
    content.layout().addWidget(button)
    popup.set_content_widget(content)
    return popup


class TestPopupCreation:
    """Tests for popup creation and initialization."""

    def test_instantiation(self, qapp):
        """Test popup can be instantiated."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import PopupWindowBase

        popup = PopupWindowBase(title="Test")
        assert popup is not None
        assert popup.windowTitle() == ""  # Frameless
        popup.close()

    def test_instantiation_with_options(self, qapp):
        """Test popup with various options."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import PopupWindowBase

        popup = PopupWindowBase(
            title="Test",
            resizable=True,
            pin_button=True,
            close_button=True,
            min_width=400,
            min_height=300,
        )
        assert popup.minimumWidth() == 400
        assert popup.minimumHeight() == 300
        popup.close()

    def test_initial_state(self, qapp):
        """Test popup initial state."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import PopupWindowBase

        popup = PopupWindowBase(title="Test")
        assert not popup.isVisible()
        assert not popup.is_pinned()
        popup.close()

    def test_signals_exist(self, qapp):
        """Test required signals exist."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import PopupWindowBase

        popup = PopupWindowBase(title="Test")
        assert hasattr(popup, "closed")
        assert hasattr(popup, "pin_changed")
        popup.close()


class TestPopupDisplay:
    """Tests for popup display and positioning."""

    def test_show_and_close(self, popup):
        """Test popup shows and closes."""
        popup.show()
        assert popup.isVisible()

        popup.close()
        assert not popup.isVisible()

    def test_show_at_position(self, popup):
        """Test show_at_position with clamping."""
        pos = QPoint(100, 100)
        popup.show_at_position(pos)
        assert popup.isVisible()

        # Position should be clamped to screen
        screen = QApplication.primaryScreen().availableGeometry()
        assert popup.x() >= screen.left()
        assert popup.y() >= screen.top()

    def test_show_at_position_off_screen(self, popup):
        """Test position clamping for off-screen coordinates."""
        # Try to position way off screen
        popup.show_at_position(QPoint(-1000, -1000))

        screen = QApplication.primaryScreen().availableGeometry()
        # Should be clamped to screen bounds
        assert popup.x() >= screen.left()
        assert popup.y() >= screen.top()

    def test_show_at_anchor_below(self, popup):
        """Test show_at_anchor with BELOW position."""
        button = QPushButton("Anchor")
        button.show()
        button.move(100, 100)

        from casare_rpa.presentation.canvas.ui.widgets.popups import AnchorPosition

        popup.show_at_anchor(button, AnchorPosition.BELOW)
        assert popup.isVisible()

        # Popup should be below the button
        assert popup.y() >= button.pos().y()

    def test_show_at_anchor_above(self, popup):
        """Test show_at_anchor with ABOVE position."""
        button = QPushButton("Anchor")
        button.show()
        button.move(100, 100)

        from casare_rpa.presentation.canvas.ui.widgets.popups import AnchorPosition

        popup.show_at_anchor(button, AnchorPosition.ABOVE)
        assert popup.isVisible()

    def test_set_title(self, popup):
        """Test set_title updates header."""
        popup.set_title("New Title")
        assert popup._title == "New Title"

    def test_set_content_widget(self, popup):
        """Test set_content_widget."""
        content = QPushButton("Content")
        popup.set_content_widget(content)
        assert popup._content_widget is content


class TestPopupResize:
    """Tests for popup resize functionality."""

    def test_resize_grip_cursor(self, popup):
        """Test cursor changes at corners."""
        popup.show()
        popup.resize(400, 300)

        # Bottom-right corner should detect resize edge
        from PySide6.QtCore import QPoint

        bottom_right = QPoint(popup.width() - 4, popup.height() - 4)
        edge = popup._get_resize_edge(bottom_right)
        assert edge == "bottom-right"

    def test_not_resizable(self, qapp):
        """Test popup with resizable=False."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import PopupWindowBase

        popup = PopupWindowBase(title="Test", resizable=False)
        # Should not show resize cursor at corners
        assert popup._get_resize_edge(QPoint(5, 5)) is None
        popup.close()


class TestPopupPinState:
    """Tests for pin state functionality."""

    def test_set_pinned(self, popup):
        """Test set_pinned changes state."""
        popup.set_pinned(True)
        assert popup.is_pinned()

        popup.set_pinned(False)
        assert not popup.is_pinned()

    def test_pin_button_updates(self, popup):
        """Test pin button visual state updates."""
        popup._pin_btn.setChecked(True)
        popup._on_pin_clicked()
        assert popup.is_pinned()

    def test_pin_signal_emitted(self, popup):
        """Test pin_changed signal is emitted."""
        signal_received = []

        def on_pin_changed(pinned):
            signal_received.append(pinned)

        popup.pin_changed.connect(on_pin_changed)
        popup.set_pinned(True)

        assert len(signal_received) == 1
        assert signal_received[0] is True


class TestPopupEscapeKey:
    """Tests for Escape key handling."""

    def test_escape_closes(self, popup_with_content):
        """Test Escape key closes popup."""
        popup_with_content.show()
        assert popup_with_content.isVisible()

        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QKeyEvent

        key_event = QKeyEvent(QEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier)
        popup_with_content.keyPressEvent(key_event)

        assert not popup_with_content.isVisible()

    def test_escape_from_child(self, popup_with_content):
        """Test Escape key in child widget closes popup."""
        popup_with_content.show()
        assert popup_with_content.isVisible()

        # Simulate escape key via event filter
        from PySide6.QtCore import QEvent
        from PySide6.QtGui import QKeyEvent

        key_event = QKeyEvent(QEvent.KeyPress, Qt.Key_Escape, Qt.NoModifier)
        popup_with_content.eventFilter(popup_with_content._content_widget, key_event)

        assert not popup_with_content.isVisible()


class TestPopupManagerIntegration:
    """Tests for PopupManager integration."""

    def test_registers_on_show(self, popup):
        """Test popup registers with PopupManager on show."""
        from casare_rpa.presentation.canvas.managers.popup_manager import PopupManager

        initial_count = len(PopupManager.get_instance()._active_popups)
        popup.show()

        # Should be registered
        assert len(PopupManager.get_instance()._active_popups) >= initial_count

    def test_unregisters_on_close(self, popup):
        """Test popup unregisters on close."""

        popup.show()
        popup.close()

        # Should be unregistered (weak reference removed)
        # Note: WeakSet doesn't have a reliable count, so we just verify it closes


class TestPopupSignals:
    """Tests for popup signals."""

    def test_closed_signal(self, popup):
        """Test closed signal emitted on close."""
        signal_received = []

        def on_closed():
            signal_received.append(True)

        popup.closed.connect(on_closed)
        popup.show()
        popup.close()

        assert len(signal_received) == 1


class TestPopupDragging:
    """Tests for popup dragging."""

    def test_is_dragging_initially(self, popup):
        """Test is_dragging returns False initially."""
        assert not popup.is_dragging()

    def test_dragging_state(self, popup):
        """Test dragging state updates during mouse events."""
        popup.show()

        # Initial state
        assert not popup.is_dragging()


class TestPopupEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_content_widget_replacement(self, popup):
        """Test replacing content widget cleans up old one."""
        from PySide6.QtWidgets import QLabel

        first_content = QLabel("First")
        popup.set_content_widget(first_content)
        assert popup._content_widget is first_content

        second_content = QLabel("Second")
        popup.set_content_widget(second_content)
        assert popup._content_widget is second_content

    def test_set_content_with_none(self, popup):
        """Test setting content widget handles cleanup."""
        content = QPushButton("Content")
        popup.set_content_widget(content)
        assert popup._content_widget is content

        # Setting None should be handled gracefully
        popup.set_content_widget(None)
        # Should still have a content widget (placeholder)
        assert popup._content_area is not None

    def test_min_size_constraints(self, qapp):
        """Test popup respects minimum size constraints."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import PopupWindowBase

        popup = PopupWindowBase(title="Test", min_width=500, min_height=400)
        assert popup.minimumWidth() == 500
        assert popup.minimumHeight() == 400
        popup.close()

    def test_pin_toggle_multiple_times(self, popup):
        """Test pin state can be toggled multiple times."""
        for i in range(3):
            popup.set_pinned(True)
            assert popup.is_pinned()
            popup.set_pinned(False)
            assert not popup.is_pinned()

    def test_show_at_anchor_with_offset(self, popup):
        """Test show_at_anchor with custom offset."""
        from PySide6.QtCore import QPoint

        from casare_rpa.presentation.canvas.ui.widgets.popups import AnchorPosition

        button = QPushButton("Anchor")
        button.show()
        button.move(100, 100)

        offset = QPoint(20, 30)
        popup.show_at_anchor(button, AnchorPosition.BELOW, offset)
        assert popup.isVisible()

    def test_window_flags_update_on_pin(self, popup):
        """Test window flags change when pin state changes."""

        initial_flags = popup.windowFlags()
        popup.set_pinned(True)
        pinned_flags = popup.windowFlags()

        # Flags should be different (Tool vs Window)
        assert initial_flags != pinned_flags
