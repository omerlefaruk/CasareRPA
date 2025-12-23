"""
Search Widget UI Component.

Provides search functionality with fuzzy matching.
"""

from collections.abc import Callable

from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME
from casare_rpa.presentation.canvas.ui.base_widget import BaseWidget


class SearchWidget(BaseWidget):
    """
    Search widget with fuzzy matching.

    Features:
    - Live search with fuzzy matching
    - Result list with navigation
    - Keyboard shortcuts
    - Clear functionality

    Signals:
        item_selected: Emitted when item is selected (str: item_text, object: item_data)
        search_cleared: Emitted when search is cleared
    """

    item_selected = Signal(str, object)
    search_cleared = Signal()

    def __init__(
        self,
        placeholder: str = "Search...",
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize search widget.

        Args:
            placeholder: Placeholder text for search input
            parent: Optional parent widget
        """
        self._placeholder = placeholder
        self._items: list[tuple] = []  # (text, data)
        self._fuzzy_match_func: Callable | None = None

        super().__init__(parent)

    def setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Search input
        search_row = QHBoxLayout()
        search_row.setSpacing(4)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText(self._placeholder)
        self._search_input.textChanged.connect(self._on_search_changed)
        self._search_input.returnPressed.connect(self._on_return_pressed)
        search_row.addWidget(self._search_input)

        # Clear button
        clear_btn = QPushButton("×")
        clear_btn.setFixedSize(24, 24)
        clear_btn.setToolTip("Clear search")
        clear_btn.clicked.connect(self.clear_search)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                font-size: 16px;
                font-weight: bold;
                background: transparent;
                border: none;
            }}
            QPushButton:hover {{
                background: {THEME.bg_light};
                border-radius: 2px;
            }}
        """)
        search_row.addWidget(clear_btn)

        layout.addLayout(search_row)

        # Results count label
        self._results_label = QLabel("0 results")
        self._results_label.setStyleSheet(
            f"color: {THEME.text_muted}; font-size: 10px; padding: 2px;"
        )
        layout.addWidget(self._results_label)

        # Results list
        self._results_list = QListWidget()
        self._results_list.setAlternatingRowColors(True)
        self._results_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._results_list.itemActivated.connect(self._on_item_activated)
        layout.addWidget(self._results_list)

        # Install event filter for keyboard navigation
        self._search_input.installEventFilter(self)

    def set_items(self, items: list[tuple]) -> None:
        """
        Set searchable items.

        Args:
            items: List of (text, data) tuples
        """
        self._items = items
        self._update_results()

    def add_item(self, text: str, data: object = None) -> None:
        """
        Add a searchable item.

        Args:
            text: Item display text
            data: Optional item data
        """
        self._items.append((text, data))
        if not self._search_input.text():
            self._update_results()

    def clear_items(self) -> None:
        """Clear all items."""
        self._items.clear()
        self._results_list.clear()
        self._update_results_label()

    def set_fuzzy_match_function(self, func: Callable[[str, str], bool]) -> None:
        """
        Set custom fuzzy match function.

        Args:
            func: Function that takes (query, item_text) and returns bool
        """
        self._fuzzy_match_func = func

    def clear_search(self) -> None:
        """Clear search input and show all results."""
        self._search_input.clear()
        self.search_cleared.emit()

    def focus_search(self) -> None:
        """Focus the search input."""
        self._search_input.setFocus()
        self._search_input.selectAll()

    def eventFilter(self, obj, event) -> bool:
        """
        Handle keyboard navigation.

        Args:
            obj: Event object
            event: Event

        Returns:
            True if event was handled
        """
        if obj == self._search_input and event.type() == QKeyEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Down:
                self._results_list.setFocus()
                if self._results_list.count() > 0:
                    self._results_list.setCurrentRow(0)
                return True
            elif event.key() == Qt.Key.Key_Up:
                self._results_list.setFocus()
                if self._results_list.count() > 0:
                    self._results_list.setCurrentRow(self._results_list.count() - 1)
                return True

        return super().eventFilter(obj, event)

    def _on_search_changed(self, text: str) -> None:
        """
        Handle search text change.

        Args:
            text: New search text
        """
        self._update_results()

    def _update_results(self) -> None:
        """Update results list based on search query."""
        query = self._search_input.text().lower()

        self._results_list.clear()

        if not query:
            # Show all items
            for text, data in self._items:
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, data)
                self._results_list.addItem(item)
        else:
            # Filter items
            for text, data in self._items:
                if self._matches(query, text):
                    item = QListWidgetItem(text)
                    item.setData(Qt.ItemDataRole.UserRole, data)
                    self._results_list.addItem(item)

        self._update_results_label()

    def _matches(self, query: str, text: str) -> bool:
        """
        Check if text matches query.

        Args:
            query: Search query
            text: Text to match

        Returns:
            True if text matches query
        """
        if self._fuzzy_match_func:
            return self._fuzzy_match_func(query, text)

        # Default: simple substring match
        return query in text.lower()

    def _update_results_label(self) -> None:
        """Update results count label."""
        count = self._results_list.count()
        self._results_label.setText(f"{count} result{'s' if count != 1 else ''}")

    def _on_return_pressed(self) -> None:
        """Handle return key press in search input."""
        if self._results_list.count() > 0:
            # Select first result
            first_item = self._results_list.item(0)
            self._select_item(first_item)

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """
        Handle item double click.

        Args:
            item: Clicked item
        """
        self._select_item(item)

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        """
        Handle item activation (Enter key).

        Args:
            item: Activated item
        """
        self._select_item(item)

    def _select_item(self, item: QListWidgetItem) -> None:
        """
        Select an item and emit signal.

        Args:
            item: Selected item
        """
        if item:
            text = item.text()
            data = item.data(Qt.ItemDataRole.UserRole)
            self.item_selected.emit(text, data)
            logger.debug(f"Search item selected: {text}")
