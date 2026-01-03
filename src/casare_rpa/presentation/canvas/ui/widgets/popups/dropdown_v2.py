"""
DropdownV2 - Single-selection dropdown popup.

A minimal dropdown component with search/filter functionality.
Features:
- Search input in header
- Scrollable item list
- Keyboard navigation (Up/Down/Enter/Esc)
- Selection highlighting with bullet
- Auto-select first match on filter
- Single selection mode

Usage:
    dropdown = DropdownV2(parent=None)
    dropdown.add_item("Option 1", data="opt1")
    dropdown.add_item("Option 2", data="opt2")
    dropdown.set_selected("opt1")
    dropdown.show_at_anchor(button)
    # Or:
    result = dropdown.exec_at_anchor(button)  # Returns selected data
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QPoint, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.popups.popup_items import DropdownItem
from casare_rpa.presentation.canvas.ui.widgets.popups.popup_utils import get_input_style_v2
from casare_rpa.presentation.canvas.ui.widgets.popups.popup_window_base import (
    AnchorPosition,
    PopupWindowBase,
)

if TYPE_CHECKING:
    pass


class DropdownV2(PopupWindowBase):
    """
    Single-selection dropdown popup with search.

    Signals:
        selection_changed: Emitted when selection changes (arg: selected data)
    """

    selection_changed = Signal(object)

    # Default dimensions
    DEFAULT_WIDTH = 280
    DEFAULT_HEIGHT = 320
    MIN_WIDTH = 200
    MIN_HEIGHT = 150

    # Maximum visible items before scrolling
    MAX_VISIBLE_ITEMS = 10

    def __init__(
        self,
        parent: QWidget | None = None,
        placeholder: str = "Search...",
    ) -> None:
        """
        Initialize dropdown.

        Args:
            parent: Parent widget
            placeholder: Search input placeholder text
        """
        # Initialize base with minimal header (no title, no pin, no close button)
        super().__init__(
            title="",
            parent=parent,
            resizable=False,
            pin_button=False,
            close_button=False,
            min_width=self.MIN_WIDTH,
            min_height=self.MIN_HEIGHT,
        )

        self._placeholder = placeholder
        self._items: list[DropdownItem] = []
        self._filtered_items: list[DropdownItem] = []
        self._selected_data: Any = None
        self._focused_index: int = -1

        # UI components
        self._search_input: QLineEdit | None = None
        self._items_container: QWidget | None = None
        self._exec_result: Any = None
        self._exec_waiting: bool = False

        # Override default size
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

        # Setup custom UI
        self._setup_dropdown_ui()

    # =========================================================================
    # UI Setup
    # =========================================================================

    def _setup_dropdown_ui(self) -> None:
        """Setup dropdown-specific UI."""
        # Hide default header (we use custom search header)
        if self._header:
            self._header.hide()

        # Create content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Search input in header area
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText(self._placeholder)
        self._search_input.setFixedHeight(32)
        self._search_input.setStyleSheet(self._get_search_input_style())
        self._search_input.textChanged.connect(self._on_search_changed)
        self._search_input.returnPressed.connect(self._on_search_enter)
        layout.addWidget(self._search_input)

        # Items container (scrollable)
        from PySide6.QtWidgets import QScrollArea

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(self._get_scroll_area_style())

        self._items_container = QWidget()
        self._items_layout = QVBoxLayout(self._items_container)
        self._items_layout.setContentsMargins(0, 0, 0, 0)
        self._items_layout.setSpacing(0)

        scroll_area.setWidget(self._items_container)
        layout.addWidget(scroll_area)

        self.set_content_widget(content)

        # Focus search on show
        self._search_input.setFocus()

    def _get_search_input_style(self) -> str:
        """Get stylesheet for search input."""
        return (
            get_input_style_v2(focused=False)
            + f"""
            QLineEdit {{
                border-top-left-radius: {TOKENS_V2.radius.md}px;
                border-top-right-radius: {TOKENS_V2.radius.md}px;
                border-bottom: none;
                padding: 0px {TOKENS_V2.spacing.sm}px;
            }}
        """
        )

    def _get_scroll_area_style(self) -> str:
        """Get stylesheet for scroll area."""
        return f"""
            QScrollArea {{
                background-color: {THEME_V2.bg_elevated};
                border: none;
                border-bottom-left-radius: {TOKENS_V2.radius.md}px;
                border-bottom-right-radius: {TOKENS_V2.radius.md}px;
            }}
        """ + get_input_style_v2(focused=False)  # For scrollbar

    # =========================================================================
    # Public API
    # =========================================================================

    def add_item(
        self,
        text: str,
        data: Any = None,
        icon: str | None = None,
    ) -> None:
        """
        Add an item to the dropdown.

        Args:
            text: Display text
            data: Associated data value (uses text if None)
            icon: Optional icon
        """
        item = DropdownItem(
            text=text,
            data=data if data is not None else text,
            icon=icon,
            selected=False,
            parent=self._items_container,
        )
        item.clicked.connect(self._on_item_clicked)
        item.hovered.connect(self._on_item_hovered)

        self._items.append(item)
        self._filtered_items.append(item)

        # Add to layout
        self._items_layout.addWidget(item)

    def clear_items(self) -> None:
        """Remove all items."""
        for item in self._items:
            item.clicked.disconnect()
            item.hovered.disconnect()
            item.deleteLater()

        self._items.clear()
        self._filtered_items.clear()
        self._selected_data = None
        self._focused_index = -1

    def set_selected(self, data: Any) -> None:
        """
        Set the selected item by data.

        Args:
            data: Data value of item to select
        """
        self._selected_data = data

        # Update all items' selection state
        for item in self._items:
            item.set_selected(item.get_data() == data)

    def get_selected(self) -> Any:
        """Return the selected data."""
        return self._selected_data

    def get_selected_text(self) -> str | None:
        """Return the selected item's text."""
        for item in self._items:
            if item.is_selected():
                return item._text
        return None

    def set_items(self, items: list[tuple[str, Any]]) -> None:
        """
        Replace all items.

        Args:
            items: List of (text, data) tuples
        """
        self.clear_items()
        for text, data in items:
            self.add_item(text, data)

    def filter_items(self, query: str) -> None:
        """
        Filter visible items by search query.

        Args:
            query: Filter string (case-insensitive partial match)
        """
        query_lower = query.lower().strip()
        self._filtered_items.clear()

        for item in self._items:
            matches = query_lower == "" or query_lower in item._text.lower()
            item.setVisible(matches)
            if matches:
                self._filtered_items.append(item)

        # Auto-select first match on filter
        if query_lower and self._filtered_items:
            self._focused_index = 0
            self._update_focus_highlight()
        else:
            self._focused_index = -1

    def show_at_anchor(
        self,
        widget: QWidget,
        position: AnchorPosition = AnchorPosition.BELOW,
        offset: QPoint | None = None,
    ) -> None:
        """
        Show dropdown anchored to a widget.

        Args:
            widget: Anchor widget
            position: Position relative to anchor
            offset: Optional offset from anchor position
        """
        super().show_at_anchor(widget, position, offset)

        # Focus search input
        if self._search_input:
            self._search_input.setFocus()
            self._search_input.selectAll()

    def exec_at_anchor(
        self,
        widget: QWidget,
        position: AnchorPosition = AnchorPosition.BELOW,
        offset: QPoint | None = None,
    ) -> Any:
        """
        Show dropdown as modal dialog and return selected data.

        Args:
            widget: Anchor widget
            position: Position relative to anchor
            offset: Optional offset from anchor position

        Returns:
            Selected data, or None if cancelled
        """
        self._exec_waiting = True
        self._exec_result = None

        # Clear selection for new exec
        self.set_selected(None)

        self.show_at_anchor(widget, position, offset)

        # Note: In a real modal implementation, you'd use a QEventLoop here
        # For now, this returns immediately and selection comes via signal
        self._exec_waiting = False
        return self._exec_result

    # =========================================================================
    # Event Handlers
    # =========================================================================

    @Slot()
    def _on_search_changed(self, text: str) -> None:
        """Handle search input text change."""
        self.filter_items(text)

    @Slot()
    def _on_search_enter(self) -> None:
        """Handle Enter key in search input."""
        if 0 <= self._focused_index < len(self._filtered_items):
            item = self._filtered_items[self._focused_index]
            self._select_item(item)

    @Slot()
    def _on_item_clicked(self) -> None:
        """Handle item click."""
        sender = self.sender()
        if isinstance(sender, DropdownItem):
            self._select_item(sender)

    @Slot()
    def _on_item_hovered(self) -> None:
        """Handle item hover - update focused index."""
        sender = self.sender()
        if isinstance(sender, DropdownItem) and sender in self._filtered_items:
            self._focused_index = self._filtered_items.index(sender)
            self._update_focus_highlight()

    def _select_item(self, item: DropdownItem) -> None:
        """
        Select an item and emit signal.

        Args:
            item: Item to select
        """
        data = item.get_data()
        self.set_selected(data)
        self.selection_changed.emit(data)

        # Store for exec_at_anchor
        self._exec_result = data

        self.close()

    def _update_focus_highlight(self) -> None:
        """Update keyboard focus highlight on items."""
        for i, item in enumerate(self._filtered_items):
            # Use hover style for focused item
            is_focused = i == self._focused_index
            item._is_hovered = is_focused
            item._update_style()

    # =========================================================================
    # Keyboard Navigation
    # =========================================================================

    def keyPressEvent(self, event) -> None:
        """
        Handle keyboard navigation.

        - Up/Down: Navigate items
        - Enter: Select focused item
        - Escape: Close
        """
        key = event.key()

        if key == Qt.Key.Key_Down:
            self._navigate_down()
            event.accept()
            return
        elif key == Qt.Key.Key_Up:
            self._navigate_up()
            event.accept()
            return
        elif key == Qt.Key.Key_Enter or key == Qt.Key.Key_Return:
            if 0 <= self._focused_index < len(self._filtered_items):
                item = self._filtered_items[self._focused_index]
                self._select_item(item)
                event.accept()
                return

        super().keyPressEvent(event)

    def _navigate_down(self) -> None:
        """Navigate to next item."""
        if not self._filtered_items:
            return

        self._focused_index = (self._focused_index + 1) % len(self._filtered_items)
        self._update_focus_highlight()
        self._scroll_to_item(self._focused_index)

    def _navigate_up(self) -> None:
        """Navigate to previous item."""
        if not self._filtered_items:
            return

        if self._focused_index <= 0:
            self._focused_index = len(self._filtered_items) - 1
        else:
            self._focused_index -= 1

        self._update_focus_highlight()
        self._scroll_to_item(self._focused_index)

    def _scroll_to_item(self, index: int) -> None:
        """
        Scroll to ensure item is visible.

        Args:
            index: Item index in filtered list
        """
        if not (0 <= index < len(self._filtered_items)):
            return

        item = self._filtered_items[index]

        # Find the scroll area
        parent = item.parent()
        while parent:
            if hasattr(parent, "ensureWidgetVisible"):
                parent.ensureWidgetVisible(item, 0, 0)
                break
            parent = parent.parent()

    # =========================================================================
    # Show/Hide
    # =========================================================================

    def showEvent(self, event) -> None:
        """Handle show event - focus search input."""
        super().showEvent(event)

        if self._search_input:
            self._search_input.setFocus()
            self._search_input.selectAll()

    def closeEvent(self, event) -> None:
        """Handle close event."""
        if self._search_input:
            # Disconnect to prevent issues
            try:
                self._search_input.textChanged.disconnect(self._on_search_changed)
                self._search_input.returnPressed.disconnect(self._on_search_enter)
            except RuntimeError:
                pass  # Already disconnected

        super().closeEvent(event)


__all__ = ["DropdownV2"]

