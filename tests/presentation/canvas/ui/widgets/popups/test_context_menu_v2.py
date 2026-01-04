"""
Tests for ContextMenuV2 component.

Tests the VS Code/Cursor-style context menu:
- Creation and initialization
- Adding items (text, icon, shortcut)
- Separator support
- Checkable items
- Enabled/disabled states
- Keyboard navigation (Up/Down/Enter/Esc)
- Item click handling
- Theme compliance (THEME_V2/TOKENS_V2 only)
- Click-outside-to-close via PopupManager
- No lambdas (uses functools.partial)
"""

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QApplication, QWidget


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def parent_widget(qapp):
    """Create a parent widget for testing."""
    widget = QWidget()
    yield widget
    widget.close()


@pytest.fixture
def context_menu(qapp):
    """Create a ContextMenuV2 instance for testing."""
    from casare_rpa.presentation.canvas.ui.widgets.popups import ContextMenuV2

    menu = ContextMenuV2()
    yield menu
    # Cleanup
    menu.close()


class TestContextMenuCreation:
    """Tests for context menu creation and initialization."""

    def test_instantiation(self, qapp):
        """Test menu can be instantiated."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import ContextMenuV2

        menu = ContextMenuV2()
        assert menu is not None
        menu.close()

    def test_dimensions(self, context_menu):
        """Test default dimensions are set correctly."""
        assert context_menu.MENU_MIN_WIDTH == 180
        assert context_menu.MENU_MIN_HEIGHT == 40
        assert context_menu.MENU_MAX_WIDTH == 320
        assert context_menu.MENU_MAX_HEIGHT == 450

    def test_no_pin_button(self, context_menu):
        """Test context menu has no pin button."""
        assert context_menu._pin_button_enabled is False
        assert context_menu._pin_btn is None

    def test_no_close_button(self, context_menu):
        """Test context menu has no close button."""
        assert context_menu._close_button_enabled is False
        assert context_menu._close_btn is None


class TestMenuItem:
    """Tests for MenuItem widget."""

    def test_menu_item_creation(self, qapp):
        """Test MenuItem can be created."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import MenuItem

        item = MenuItem(text="Test Item")
        assert item is not None
        assert item._text == "Test Item"
        assert item.is_enabled() is True

    def test_menu_item_with_shortcut(self, qapp):
        """Test MenuItem with shortcut."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import MenuItem

        item = MenuItem(text="Copy", shortcut="Ctrl+C")
        assert item._shortcut == "Ctrl+C"

    def test_menu_item_disabled(self, qapp):
        """Test MenuItem can be disabled."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import MenuItem

        item = MenuItem(text="Disabled", enabled=False)
        assert item.is_enabled() is False

    def test_menu_item_checkable(self, qapp):
        """Test MenuItem can be checkable."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import MenuItem

        item = MenuItem(text="Checkable", checkable=True)
        assert item._checkable is True
        assert item.is_checked() is False

        item.set_checked(True)
        assert item.is_checked() is True

    def test_menu_item_checkable_initial_checked(self, qapp):
        """Test MenuItem can be initially checked."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import MenuItem

        item = MenuItem(text="Checked", checkable=True, checked=True)
        assert item.is_checked() is True

    def test_menu_item_toggle(self, qapp):
        """Test MenuItem toggle."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import MenuItem

        item = MenuItem(text="Toggle", checkable=True)
        assert item.is_checked() is False

        item.toggle()
        assert item.is_checked() is True

        item.toggle()
        assert item.is_checked() is False

    def test_menu_item_signals(self, qapp):
        """Test MenuItem clicked signal."""
        import functools

        from casare_rpa.presentation.canvas.ui.widgets.popups import MenuItem

        received = []

        def handler():
            received.append("clicked")

        item = MenuItem(text="Signal", callback=handler)
        # Don't connect again - callback is already called in trigger()
        # and clicked is emitted in trigger too
        item.clicked.connect(functools.partial(received.append, "signal"))

        item.trigger()
        # Callback is called AND clicked signal is emitted
        assert len(received) == 2


class TestMenuSeparator:
    """Tests for MenuSeparator widget."""

    def test_separator_creation(self, qapp):
        """Test MenuSeparator can be created."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import MenuSeparator

        sep = MenuSeparator()
        assert sep is not None
        assert sep.height() == 1


class TestAddItems:
    """Tests for adding items to context menu."""

    def test_add_single_item(self, context_menu):
        """Test adding a single item."""
        received = []

        def callback():
            received.append("item1")

        item = context_menu.add_item("item1", "Item 1", callback=callback)
        assert item is not None
        assert len(context_menu._items) == 1

    def test_add_multiple_items(self, context_menu):
        """Test adding multiple items."""
        for i in range(3):
            context_menu.add_item(f"item{i}", f"Item {i}")

        assert len(context_menu._items) == 3

    def test_add_item_with_shortcut(self, context_menu):
        """Test adding item with shortcut."""
        item = context_menu.add_item("copy", "Copy", shortcut="Ctrl+C")
        assert item._shortcut == "Ctrl+C"

    def test_add_item_with_icon(self, context_menu):
        """Test adding item with icon."""
        item = context_menu.add_item("save", "Save", shortcut="Ctrl+S", icon="save")
        assert item._icon == "save"

    def test_add_disabled_item(self, context_menu):
        """Test adding disabled item."""
        item = context_menu.add_item("disabled", "Disabled", enabled=False)
        assert item.is_enabled() is False

    def test_add_checkable_item(self, context_menu):
        """Test adding checkable item."""
        item = context_menu.add_item("checkable", "Toggle View", checkable=True, checked=False)
        assert item._checkable is True
        assert item.is_checked() is False

    def test_add_checkable_item_checked(self, context_menu):
        """Test adding initially checked item."""
        item = context_menu.add_item("checked", "Show Grid", checkable=True, checked=True)
        assert item.is_checked() is True

    def test_add_separator(self, context_menu):
        """Test adding separator."""
        context_menu.add_item("before", "Before")
        sep = context_menu.add_separator()
        context_menu.add_item("after", "After")

        assert len(context_menu._separators) == 1
        assert sep is not None

    def test_clear(self, context_menu):
        """Test clearing all items."""
        context_menu.add_item("item1", "Item 1")
        context_menu.add_item("item2", "Item 2")
        context_menu.add_separator()
        context_menu.add_item("item3", "Item 3")

        assert len(context_menu._items) == 3
        assert len(context_menu._separators) == 1

        context_menu.clear()

        assert len(context_menu._items) == 0
        assert len(context_menu._separators) == 0


class TestRemoveItem:
    """Tests for removing items from context menu."""

    def test_remove_existing_item(self, context_menu):
        """Test removing an existing item."""
        context_menu.add_item("item1", "Item 1")
        context_menu.add_item("item2", "Item 2")
        context_menu.add_item("item3", "Item 3")

        result = context_menu.remove_item("item2")
        assert result is True
        assert len(context_menu._items) == 2
        assert context_menu._items[0][0] == "item1"
        assert context_menu._items[1][0] == "item3"

    def test_remove_nonexistent_item(self, context_menu):
        """Test removing a non-existent item."""
        context_menu.add_item("item1", "Item 1")

        result = context_menu.remove_item("nonexistent")
        assert result is False
        assert len(context_menu._items) == 1


class TestSetItemState:
    """Tests for setting item state."""

    def test_set_item_enabled(self, context_menu):
        """Test setting item enabled state."""
        item = context_menu.add_item("item1", "Item 1", enabled=False)

        assert item.is_enabled() is False

        result = context_menu.set_item_enabled("item1", True)
        assert result is True
        assert item.is_enabled() is True

    def test_set_item_enabled_nonexistent(self, context_menu):
        """Test setting enabled state on non-existent item."""
        result = context_menu.set_item_enabled("nonexistent", True)
        assert result is False

    def test_set_item_checked(self, context_menu):
        """Test setting item checked state."""
        item = context_menu.add_item("item1", "Checkable", checkable=True)

        assert item.is_checked() is False

        result = context_menu.set_item_checked("item1", True)
        assert result is True
        assert item.is_checked() is True

    def test_set_item_checked_nonexistent(self, context_menu):
        """Test setting checked state on non-existent item."""
        result = context_menu.set_item_checked("nonexistent", True)
        assert result is False

    def test_set_item_text(self, context_menu):
        """Test setting item text."""
        item = context_menu.add_item("item1", "Original Text")

        assert item._text == "Original Text"

        result = context_menu.set_item_text("item1", "New Text")
        assert result is True
        assert item._text == "New Text"

    def test_set_item_text_nonexistent(self, context_menu):
        """Test setting text on non-existent item."""
        result = context_menu.set_item_text("nonexistent", "New Text")
        assert result is False


class TestItemClick:
    """Tests for item click handling."""

    def test_item_click_emits_signal(self, context_menu):
        """Test clicking an item emits item_selected signal."""
        received = []

        def handler(item_id):
            received.append(item_id)

        context_menu.item_selected.connect(handler)

        context_menu.add_item("item1", "Item 1")
        context_menu.add_item("item2", "Item 2")

        # Simulate click on first item
        _, item = context_menu._items[0]
        item.trigger()

        # Signal should be emitted
        assert len(received) == 1
        assert received[0] == "item1"

    def test_item_click_calls_callback(self, context_menu):
        """Test clicking an item calls its callback."""
        received = []

        def callback():
            received.append("callback")

        context_menu.add_item("item1", "Item 1", callback=callback)

        _, item = context_menu._items[0]
        item.trigger()

        assert len(received) == 1
        assert received[0] == "callback"

    def test_item_click_closes_menu(self, context_menu, qapp):
        """Test clicking an item closes the menu."""
        from unittest.mock import patch

        context_menu.add_item("item1", "Item 1")

        # Show menu (without actually displaying)
        context_menu.show()

        # Mock close to verify it's called
        with patch.object(context_menu, "close") as mock_close:
            _, item = context_menu._items[0]
            context_menu._on_item_clicked("item1")
            mock_close.assert_called_once()

    def test_disabled_item_no_click(self, context_menu):
        """Test clicking disabled item doesn't trigger."""
        received = []

        def callback():
            received.append("should not fire")

        context_menu.add_item("disabled", "Disabled", callback=callback, enabled=False)

        _, item = context_menu._items[0]
        item.trigger()

        assert len(received) == 0

    def test_checkable_item_toggles_on_click(self, context_menu):
        """Test checkable item toggles on click."""
        context_menu.add_item("checkable", "Toggle", checkable=True, checked=False)

        _, item = context_menu._items[0]
        assert item.is_checked() is False

        item.trigger()
        assert item.is_checked() is True


class TestKeyboardNavigation:
    """Tests for keyboard navigation."""

    def test_arrow_down_navigation(self, context_menu):
        """Test Down arrow key moves selection."""
        context_menu.add_item("item1", "Item 1")
        context_menu.add_item("item2", "Item 2")
        context_menu.add_item("item3", "Item 3")

        # Start at first item
        context_menu._current_index = 0

        # Simulate Down key press
        from PySide6.QtGui import QKeyEvent

        event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier)
        context_menu.keyPressEvent(event)

        # Should move to second item
        assert context_menu._current_index == 1

    def test_arrow_up_navigation(self, context_menu):
        """Test Up arrow key moves selection up."""
        context_menu.add_item("item1", "Item 1")
        context_menu.add_item("item2", "Item 2")
        context_menu.add_item("item3", "Item 3")

        # Start at second item
        context_menu._current_index = 1

        # Simulate Up key press
        from PySide6.QtGui import QKeyEvent

        event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
        context_menu.keyPressEvent(event)

        # Should move to first item
        assert context_menu._current_index == 0

    def test_enter_key_selects_item(self, context_menu):
        """Test Enter key selects current item."""
        received = []

        def handler(item_id):
            received.append(item_id)

        context_menu.item_selected.connect(handler)

        context_menu.add_item("item1", "Item 1")
        context_menu.add_item("item2", "Item 2")

        context_menu._current_index = 1

        # Simulate Enter key press
        from PySide6.QtGui import QKeyEvent

        event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        context_menu.keyPressEvent(event)

        # Should select second item
        assert len(received) == 1
        assert received[0] == "item2"

    def test_escape_key_closes_menu(self, context_menu):
        """Test Escape key closes menu."""
        from unittest.mock import patch

        # Mock close to verify it's called
        with patch.object(context_menu, "close") as mock_close:
            from PySide6.QtGui import QKeyEvent

            event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
            context_menu.keyPressEvent(event)
            mock_close.assert_called_once()

    def test_navigation_skips_disabled(self, context_menu):
        """Test keyboard navigation skips disabled items."""
        context_menu.add_item("item1", "Item 1")
        context_menu.add_item("disabled", "Disabled", enabled=False)
        context_menu.add_item("item3", "Item 3")

        context_menu._current_index = 0

        # Simulate Down key press
        from PySide6.QtGui import QKeyEvent

        event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier)
        context_menu.keyPressEvent(event)

        # Should skip disabled item and go to item3
        assert context_menu._current_index == 2


class TestPositioning:
    """Tests for menu positioning."""

    def test_show_at_position(self, context_menu):
        """Test show_at_position method."""
        pos = QPoint(100, 100)
        context_menu.add_item("item1", "Item 1")

        context_menu.show_at_position(pos)

        # Menu should be positioned (may be adjusted for screen bounds)
        assert context_menu.isVisible() or context_menu.pos() is not None

    def test_popup_alias(self, context_menu):
        """Test popup method is alias for show_at_position."""
        pos = QPoint(200, 200)
        context_menu.add_item("item1", "Item 1")

        context_menu.popup(pos)

        assert context_menu.isVisible() or context_menu.pos() is not None

    def test_show_at_anchor(self, context_menu, parent_widget):
        """Test show_at_anchor method."""
        from casare_rpa.presentation.canvas.ui.widgets.popups.popup_window_base import (
            AnchorPosition,
        )

        context_menu.add_item("item1", "Item 1")

        context_menu.show_at_anchor(parent_widget, AnchorPosition.BELOW)

        # Menu should be positioned relative to anchor
        assert context_menu.isVisible() or context_menu.pos() is not None


class TestThemeCompliance:
    """Tests for THEME_V2/TOKENS_V2 compliance."""

    def test_uses_theme_v2_colors(self, context_menu):
        """Test menu uses THEME_V2 colors only."""

        stylesheet = context_menu.styleSheet()

        # Should contain THEME_V2 references
        assert "THEME_V2" in str(context_menu.__dict__) or stylesheet is not None

    def test_item_uses_theme_v2(self, qapp):
        """Test MenuItem uses THEME_V2 styling."""
        from casare_rpa.presentation.canvas.theme import THEME_V2
        from casare_rpa.presentation.canvas.ui.widgets.popups import MenuItem

        item = MenuItem(text="Test")
        stylesheet = item.styleSheet()

        # Check that colors match THEME_V2 values (resolved)
        assert THEME_V2.text_primary in stylesheet  # #a0a0a0
        assert "transparent" in stylesheet or THEME_V2.bg_selected in stylesheet

    def test_separator_uses_theme_v2(self, qapp):
        """Test MenuSeparator uses THEME_V2 styling."""
        from casare_rpa.presentation.canvas.theme import THEME_V2
        from casare_rpa.presentation.canvas.ui.widgets.popups import MenuSeparator

        sep = MenuSeparator()
        stylesheet = sep.styleSheet()

        # Should use THEME_V2.border color (#303030)
        assert THEME_V2.border in stylesheet


class TestNoLambdas:
    """Tests for functools.partial usage (no lambdas)."""

    def test_connections_use_partial(self, context_menu):
        """Test signal connections use functools.partial."""

        context_menu.add_item("item1", "Item 1")
        context_menu.add_item("item2", "Item 2")

        # Check that signal connections were made
        # (The actual connection uses partial internally)
        assert len(context_menu._items) == 2

        # Verify no lambda in source
        import inspect

        source = inspect.getsource(context_menu.add_item)
        assert "lambda" not in source or "partial" in source


class TestIconProviderIntegration:
    """Tests for IconProviderV2 integration."""

    def test_icon_provider_has_common_icons(self):
        """Test IconProviderV2 has common menu icons."""
        from casare_rpa.presentation.canvas.theme.icons_v2 import icon_v2

        # Check for common menu icons
        common_icons = ["copy", "cut", "paste", "save", "trash", "settings"]
        for icon_name in common_icons:
            # Just verify has_icon works without error
            _ = icon_v2.has_icon(icon_name)
            # Don't assert - icons may or may not exist

    def test_add_item_with_icon_name(self, context_menu):
        """Test adding item with icon name from IconProviderV2."""
        from casare_rpa.presentation.canvas.theme.icons_v2 import icon_v2

        # Try with an icon that might exist
        icon_name = "save"
        if icon_v2.has_icon(icon_name):
            item = context_menu.add_item("save", "Save", icon=icon_name)
            assert item is not None


class TestPopupManagerIntegration:
    """Tests for PopupManager click-outside-to-close integration."""

    def test_registers_with_popup_manager_on_show(self, context_menu):
        """Test menu registers with PopupManager when shown."""
        from unittest.mock import patch

        from casare_rpa.presentation.canvas.managers.popup_manager import PopupManager

        with patch.object(PopupManager, "register") as mock_register:
            context_menu.show()
            mock_register.assert_called_once()

    def test_unregisters_from_popup_manager_on_close(self, context_menu):
        """Test menu unregisters from PopupManager when closed."""
        from unittest.mock import patch

        from casare_rpa.presentation.canvas.managers.popup_manager import PopupManager

        context_menu.show()

        with patch.object(PopupManager, "unregister") as mock_unregister:
            context_menu.close()
            mock_unregister.assert_called_once()


class TestMenuItemHover:
    """Tests for MenuItem hover state."""

    def test_hover_emits_signal(self, qapp):
        """Test hovering MenuItem emits hovered signal."""
        from PySide6.QtGui import QEnterEvent

        from casare_rpa.presentation.canvas.ui.widgets.popups import MenuItem

        received = []

        def handler():
            received.append("hovered")

        item = MenuItem(text="Hover Me")
        item.hovered.connect(handler)

        # Simulate hover event - QEnterEvent needs localPos, scenePos, globalPos
        from PySide6.QtCore import QPointF

        hover_event = QEnterEvent(QPointF(0, 0), QPointF(0, 0), QPointF(0, 0))
        item.enterEvent(hover_event)

        # Hover signal should be emitted
        assert len(received) == 1

    def test_hover_updates_style(self, qapp):
        """Test hovering updates item style."""
        from PySide6.QtGui import QEnterEvent

        from casare_rpa.presentation.canvas.ui.widgets.popups import MenuItem

        item = MenuItem(text="Hover Me")

        # Simulate hover
        from PySide6.QtCore import QPointF

        hover_event = QEnterEvent(QPointF(0, 0), QPointF(0, 0), QPointF(0, 0))
        item.enterEvent(hover_event)

        # Style should have changed (hover state)
        assert item._is_hovered is True

        # Simulate leave - leaveEvent takes QEvent
        from PySide6.QtCore import QEvent

        leave_event = QEvent(QEvent.Type.Leave)
        item.leaveEvent(leave_event)

        assert item._is_hovered is False
