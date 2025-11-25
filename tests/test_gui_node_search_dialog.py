"""
Tests for CasareRPA Node Search Dialog.

Tests fuzzy search functionality, keyboard navigation, and node selection.
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem


class TestNodeSearchDialogCreation:
    """Tests for NodeSearchDialog creation and UI."""

    def test_dialog_created(self, node_search_dialog):
        """Test dialog is created successfully."""
        assert node_search_dialog is not None

    def test_dialog_title(self, node_search_dialog):
        """Test dialog has correct title."""
        assert node_search_dialog.windowTitle() == "Search Nodes"

    def test_dialog_has_search_input(self, node_search_dialog):
        """Test dialog has search input field."""
        assert node_search_dialog._search_input is not None

    def test_dialog_has_results_list(self, node_search_dialog):
        """Test dialog has results list widget."""
        assert node_search_dialog._results_list is not None

    def test_dialog_is_modal(self, node_search_dialog):
        """Test dialog is modal."""
        assert node_search_dialog.isModal()


class TestNodeSearchDialogSetItems:
    """Tests for setting node items."""

    def test_set_node_items(self, node_search_dialog):
        """Test setting node items creates search index."""
        items = [
            ("Browser", "Open Browser", "Opens a browser window"),
            ("Browser", "Navigate", "Navigates to a URL"),
        ]
        node_search_dialog.set_node_items(items)
        assert node_search_dialog._search_index is not None

    def test_set_node_items_populates_results(self, node_search_dialog):
        """Test setting items shows results in list."""
        items = [
            ("Browser", "Open Browser", "Opens a browser window"),
            ("Control Flow", "If Condition", "Branches based on condition"),
        ]
        node_search_dialog.set_node_items(items)
        # Empty query shows all results (limited by max_results)
        assert node_search_dialog._results_list.count() > 0

    def test_empty_items(self, node_search_dialog):
        """Test setting empty items list."""
        node_search_dialog.set_node_items([])
        assert node_search_dialog._results_list.count() == 0


class TestNodeSearchDialogSearch:
    """Tests for search functionality."""

    def test_search_filters_results(self, node_search_dialog):
        """Test search filters results correctly."""
        items = [
            ("Browser", "Open Browser", "Opens a browser window"),
            ("Browser", "Navigate", "Navigates to a URL"),
            ("Control Flow", "If Condition", "Branches based on condition"),
        ]
        node_search_dialog.set_node_items(items)
        initial_count = node_search_dialog._results_list.count()

        # Search for "browser"
        node_search_dialog._search_input.setText("browser")
        node_search_dialog._do_search()

        # Should find fewer or same results
        assert node_search_dialog._results_list.count() <= initial_count

    def test_fuzzy_search(self, node_search_dialog):
        """Test fuzzy search matches partial input."""
        items = [
            ("Browser", "Open Browser", "Opens a browser window"),
            ("Control Flow", "Loop While", "Loops while condition is true"),
        ]
        node_search_dialog.set_node_items(items)

        # Search with abbreviation-like query
        node_search_dialog._search_input.setText("ob")
        node_search_dialog._do_search()

        # Should find "Open Browser"
        assert node_search_dialog._results_list.count() > 0

    def test_search_no_results(self, node_search_dialog):
        """Test search with no matching results."""
        items = [
            ("Browser", "Open Browser", "Opens a browser window"),
        ]
        node_search_dialog.set_node_items(items)

        node_search_dialog._search_input.setText("zzzzzzz")
        node_search_dialog._do_search()

        assert node_search_dialog._results_list.count() == 0

    def test_search_clears_on_empty(self, node_search_dialog):
        """Test clearing search restores results."""
        items = [
            ("Browser", "Open Browser", "Opens a browser window"),
            ("Browser", "Navigate", "Navigates to a URL"),
        ]
        node_search_dialog.set_node_items(items)

        # Search then clear
        node_search_dialog._search_input.setText("open")
        node_search_dialog._do_search()
        node_search_dialog._search_input.setText("")
        node_search_dialog._do_search()

        # Should show results again
        assert node_search_dialog._results_list.count() > 0


class TestNodeSearchDialogSelection:
    """Tests for result selection."""

    def test_first_item_selected_by_default(self, node_search_dialog):
        """Test first result is selected by default."""
        items = [
            ("Browser", "Open Browser", "Opens a browser window"),
            ("Browser", "Navigate", "Navigates to a URL"),
        ]
        node_search_dialog.set_node_items(items)

        assert node_search_dialog._results_list.currentRow() == 0

    def test_item_data_stored(self, node_search_dialog):
        """Test item data contains category and name."""
        items = [
            ("Browser", "Open Browser", "Opens a browser window"),
        ]
        node_search_dialog.set_node_items(items)

        item = node_search_dialog._results_list.item(0)
        data = item.data(Qt.ItemDataRole.UserRole)
        assert data is not None
        assert data[0] == "Browser"
        assert data[1] == "Open Browser"

    def test_node_selected_signal(self, node_search_dialog, qtbot):
        """Test node_selected signal is emitted on selection."""
        items = [
            ("Browser", "Open Browser", "Opens a browser window"),
        ]
        node_search_dialog.set_node_items(items)

        with qtbot.waitSignal(node_search_dialog.node_selected, timeout=1000) as blocker:
            item = node_search_dialog._results_list.item(0)
            node_search_dialog._on_item_selected(item)

        assert blocker.args == ["Browser", "Open Browser"]


class TestNodeSearchDialogKeyboard:
    """Tests for keyboard navigation."""

    def test_down_key_navigates(self, node_search_dialog, qtbot):
        """Test Down key navigates to next item."""
        items = [
            ("Browser", "Open Browser", "Opens a browser window"),
            ("Browser", "Navigate", "Navigates to a URL"),
            ("Browser", "Click", "Clicks an element"),
        ]
        node_search_dialog.set_node_items(items)

        # Initial row is 0
        assert node_search_dialog._results_list.currentRow() == 0

        # Simulate Down key
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier)
        node_search_dialog.keyPressEvent(event)

        assert node_search_dialog._results_list.currentRow() == 1

    def test_up_key_navigates(self, node_search_dialog, qtbot):
        """Test Up key navigates to previous item."""
        items = [
            ("Browser", "Open Browser", "Opens a browser window"),
            ("Browser", "Navigate", "Navigates to a URL"),
            ("Browser", "Click", "Clicks an element"),
        ]
        node_search_dialog.set_node_items(items)

        # Move to row 1 first
        node_search_dialog._results_list.setCurrentRow(1)

        # Simulate Up key
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
        node_search_dialog.keyPressEvent(event)

        assert node_search_dialog._results_list.currentRow() == 0

    def test_up_key_stays_at_top(self, node_search_dialog, qtbot):
        """Test Up key at top stays at top."""
        items = [
            ("Browser", "Open Browser", "Opens a browser window"),
            ("Browser", "Navigate", "Navigates to a URL"),
        ]
        node_search_dialog.set_node_items(items)

        # Already at row 0
        assert node_search_dialog._results_list.currentRow() == 0

        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier)
        node_search_dialog.keyPressEvent(event)

        # Should stay at 0
        assert node_search_dialog._results_list.currentRow() == 0

    def test_down_key_stays_at_bottom(self, node_search_dialog, qtbot):
        """Test Down key at bottom stays at bottom."""
        items = [
            ("Browser", "Open Browser", "Opens a browser window"),
            ("Browser", "Navigate", "Navigates to a URL"),
        ]
        node_search_dialog.set_node_items(items)

        # Move to last row
        last_row = node_search_dialog._results_list.count() - 1
        node_search_dialog._results_list.setCurrentRow(last_row)

        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier)
        node_search_dialog.keyPressEvent(event)

        # Should stay at last row
        assert node_search_dialog._results_list.currentRow() == last_row

    def test_tab_key_cycles(self, node_search_dialog, qtbot):
        """Test Tab key cycles through results."""
        items = [
            ("Browser", "Open Browser", "Opens a browser window"),
            ("Browser", "Navigate", "Navigates to a URL"),
        ]
        node_search_dialog.set_node_items(items)

        # Move to last row
        last_row = node_search_dialog._results_list.count() - 1
        node_search_dialog._results_list.setCurrentRow(last_row)

        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Tab, Qt.KeyboardModifier.NoModifier)
        node_search_dialog.keyPressEvent(event)

        # Should cycle to row 0
        assert node_search_dialog._results_list.currentRow() == 0

    def test_enter_key_selects(self, node_search_dialog, qtbot):
        """Test Enter key selects current item."""
        items = [
            ("Browser", "Open Browser", "Opens a browser window"),
        ]
        node_search_dialog.set_node_items(items)

        with qtbot.waitSignal(node_search_dialog.node_selected, timeout=1000) as blocker:
            from PySide6.QtGui import QKeyEvent
            from PySide6.QtCore import QEvent
            event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
            node_search_dialog.keyPressEvent(event)

        assert blocker.args == ["Browser", "Open Browser"]


class TestNodeSearchDialogDebounce:
    """Tests for search debounce behavior."""

    def test_debounce_timer_exists(self, node_search_dialog):
        """Test debounce timer is created."""
        assert node_search_dialog._debounce_timer is not None

    def test_short_query_immediate(self, node_search_dialog):
        """Test short queries search immediately."""
        items = [
            ("Browser", "Open Browser", "Opens a browser window"),
        ]
        node_search_dialog.set_node_items(items)

        # Single character should search immediately
        node_search_dialog._on_search_changed("o")

        # Timer should be stopped (immediate search)
        assert not node_search_dialog._debounce_timer.isActive()

    def test_backspace_immediate(self, node_search_dialog):
        """Test backspace searches immediately."""
        items = [
            ("Browser", "Open Browser", "Opens a browser window"),
        ]
        node_search_dialog.set_node_items(items)

        # Type then backspace
        node_search_dialog._on_search_changed("open")
        node_search_dialog._pending_query = "ope"
        node_search_dialog._on_search_changed("ope")

        # Should search immediately on backspace
        assert not node_search_dialog._debounce_timer.isActive()


class TestNodeSearchDialogCategories:
    """Tests for category handling in results."""

    def test_multiple_categories(self, node_search_dialog):
        """Test results from multiple categories."""
        items = [
            ("Browser", "Open Browser", "Opens a browser window"),
            ("Control Flow", "If Condition", "Branches based on condition"),
            ("Variables", "Set Variable", "Sets a variable value"),
        ]
        node_search_dialog.set_node_items(items)

        # Should have items from all categories
        assert node_search_dialog._results_list.count() == 3

    def test_category_in_item_data(self, node_search_dialog):
        """Test category is preserved in item data."""
        items = [
            ("Control Flow", "If Condition", "Branches based on condition"),
        ]
        node_search_dialog.set_node_items(items)

        item = node_search_dialog._results_list.item(0)
        category, name = item.data(Qt.ItemDataRole.UserRole)
        assert category == "Control Flow"
        assert name == "If Condition"
