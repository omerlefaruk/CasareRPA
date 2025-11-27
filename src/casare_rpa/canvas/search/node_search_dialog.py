"""
Node search dialog for quick node creation.

Provides a blazingly fast fuzzy search interface for finding and creating nodes.

Performance optimizations:
- Uses SearchIndex for pre-computed search data
- Near-instant search (5ms debounce only to batch rapid keystrokes)
- Incremental result caching
- Lightweight UI updates
"""

from typing import List, Tuple, Optional, Callable
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QLabel, QWidget, QHBoxLayout, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QKeyEvent

from ...utils.fuzzy_search import SearchIndex, highlight_matches


class NodeSearchDialog(QDialog):
    """
    Dialog for searching and selecting nodes to create.

    Features:
    - Blazingly fast fuzzy search
    - Abbreviation matching (e.g., "lf" -> "List Filter")
    - Keyboard navigation (Up/Down/Enter/Esc)
    - Real-time results with minimal latency
    """

    node_selected = Signal(str, str)  # category, node_name

    # Minimal debounce - just enough to batch rapid keystrokes
    DEBOUNCE_DELAY_MS = 5

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the search dialog."""
        super().__init__(parent)

        self.setWindowTitle("Search Nodes")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # Remove window frame, make it look like a popup
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)

        self._node_items: List[Tuple[str, str, str]] = []
        self._search_index: Optional[SearchIndex] = None
        self._pending_query: str = ""
        self._last_query: str = ""

        # Debounce timer - very short for responsiveness
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._do_search)

        self._setup_ui()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Title label
        title = QLabel("Search Nodes (Tab)")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFA500;")
        layout.addWidget(title)

        # Search input
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Type to search... (lf = List Filter, dm = Dict Merge)")
        self._search_input.textChanged.connect(self._on_search_changed)
        self._search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 2px solid #3d3d3d;
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #FFA500;
            }
        """)
        layout.addWidget(self._search_input)

        # Results list - optimized for fast updates
        self._results_list = QListWidget()
        self._results_list.setUniformItemSizes(True)  # Faster rendering
        self._results_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._results_list.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 4px;
                outline: none;
            }
            QListWidget::item {
                padding: 6px 8px;
                border-radius: 3px;
                margin: 1px;
            }
            QListWidget::item:selected {
                background-color: #3d3d3d;
                border: 1px solid #FFA500;
            }
            QListWidget::item:hover {
                background-color: #353535;
            }
        """)
        self._results_list.itemDoubleClicked.connect(self._on_item_selected)
        layout.addWidget(self._results_list)

        # Help text
        help_text = QLabel("↑↓ Navigate | Enter Select | Esc Cancel | Try: lf, dm, ce")
        help_text.setStyleSheet("color: #888888; font-size: 11px;")
        help_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(help_text)

        # Style the dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
            }
        """)

    def set_node_items(self, items: List[Tuple[str, str, str]]):
        """
        Set the available node items and build the search index.

        Args:
            items: List of (category, name, description) tuples
        """
        self._node_items = items
        # Build search index for instant queries
        self._search_index = SearchIndex(items)
        self._last_query = ""
        self._update_results("")

    def _on_search_changed(self, text: str):
        """Handle search text changes - near instant with minimal debounce."""
        self._pending_query = text

        # For very short queries or backspace, search immediately
        if len(text) <= 1 or len(text) < len(self._last_query):
            self._debounce_timer.stop()
            self._do_search()
        else:
            # Tiny debounce to batch rapid typing
            self._debounce_timer.start(self.DEBOUNCE_DELAY_MS)

    def _do_search(self):
        """Execute the search."""
        query = self._pending_query
        if query == self._last_query:
            return  # No change

        self._last_query = query
        self._update_results(query)

    def _update_results(self, query: str):
        """Update the results list based on search query."""
        self._results_list.clear()

        if self._search_index is None:
            return

        # Get search results (SearchIndex handles caching internally)
        results = self._search_index.search(query, max_results=15)

        # Batch add items for performance
        for category, name, description, score, positions in results:
            item = QListWidgetItem()

            # Highlight matched characters in name
            highlighted_name = highlight_matches(name, positions)

            # Create rich text for the item
            html = f"""
            <div style='line-height: 1.3;'>
                <span style='color: #888888; font-size: 10px;'>{category}</span><br/>
                <span style='font-size: 12px; font-weight: bold;'>{highlighted_name}</span><br/>
                <span style='color: #aaaaaa; font-size: 10px;'>{description[:60]}{'...' if len(description) > 60 else ''}</span>
            </div>
            """

            item.setText(html)
            item.setData(Qt.ItemDataRole.UserRole, (category, name))
            self._results_list.addItem(item)

        # Select first item
        if self._results_list.count() > 0:
            self._results_list.setCurrentRow(0)

    def _on_item_selected(self, item: QListWidgetItem):
        """Handle item selection (double-click or Enter)."""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            category, name = data
            self.node_selected.emit(category, name)
            self.accept()

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard events."""
        key = event.key()

        if key == Qt.Key.Key_Escape:
            self.reject()
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            current_item = self._results_list.currentItem()
            if current_item:
                self._on_item_selected(current_item)
        elif key == Qt.Key.Key_Down:
            current_row = self._results_list.currentRow()
            if current_row < self._results_list.count() - 1:
                self._results_list.setCurrentRow(current_row + 1)
        elif key == Qt.Key.Key_Up:
            current_row = self._results_list.currentRow()
            if current_row > 0:
                self._results_list.setCurrentRow(current_row - 1)
        elif key == Qt.Key.Key_Tab:
            # Tab cycles through results
            current_row = self._results_list.currentRow()
            next_row = (current_row + 1) % max(1, self._results_list.count())
            self._results_list.setCurrentRow(next_row)
        else:
            # Let search input handle other keys
            super().keyPressEvent(event)

    def showEvent(self, event):
        """Focus search input when dialog is shown."""
        super().showEvent(event)
        self._search_input.setFocus()
        self._search_input.clear()
        # Clear cache when dialog reopens for fresh results
        if self._search_index:
            self._search_index.clear_cache()
        self._last_query = ""
