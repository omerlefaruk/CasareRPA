"""
Node search dialog for quick node creation.

Provides a fuzzy search interface for finding and creating nodes.

Performance optimizations:
- Uses SearchIndex for pre-computed search data
- Debounced search input (50ms) to reduce UI lag
- Early termination after finding enough good matches
"""

from typing import List, Tuple, Optional, Callable
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QLabel, QWidget, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QKeyEvent

from ..utils.fuzzy_search import SearchIndex, highlight_matches


class NodeSearchDialog(QDialog):
    """
    Dialog for searching and selecting nodes to create.

    Features:
    - Fuzzy search (e.g., "b l" matches "Browser Launch")
    - Keyboard navigation (Up/Down/Enter/Esc)
    - Real-time results filtering with debouncing
    - Category and description display
    - Optimized with pre-computed search index
    """

    node_selected = Signal(str, str)  # category, node_name

    # Debounce delay in milliseconds
    DEBOUNCE_DELAY_MS = 50

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the search dialog."""
        super().__init__(parent)

        self.setWindowTitle("Search Nodes")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # Remove window frame, make it look like a popup
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)

        self._node_items: List[Tuple[str, str, str]] = []  # (category, name, description)
        self._search_index: Optional[SearchIndex] = None  # Pre-computed search index
        self._pending_query: str = ""

        # Debounce timer for search
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._do_search)

        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title label
        title = QLabel("Search Nodes (Tab)")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFA500;")
        layout.addWidget(title)
        
        # Search input
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Type to search... (e.g., 'b l' for Browser Launch)")
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
        
        # Results list
        self._results_list = QListWidget()
        self._results_list.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 3px;
                margin: 2px;
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
        help_text = QLabel("↑↓ Navigate | Enter Select | Esc Cancel")
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
        # Build search index for faster queries
        self._search_index = SearchIndex(items)
        self._update_results("")

    def _on_search_changed(self, text: str):
        """Handle search text changes with debouncing."""
        self._pending_query = text
        # Restart debounce timer
        self._debounce_timer.start(self.DEBOUNCE_DELAY_MS)

    def _do_search(self):
        """Execute the search after debounce delay."""
        self._update_results(self._pending_query)

    def _update_results(self, query: str):
        """Update the results list based on search query."""
        self._results_list.clear()

        if not query.strip():
            # Show all nodes when no query (limit to 10)
            results = [(cat, name, desc, 0, []) for cat, name, desc in self._node_items[:10]]
        elif self._search_index:
            # Use optimized search index
            results = self._search_index.search(query, max_results=10)
        else:
            # Fallback: no items yet
            results = []

        # Display results (already limited to 10)
        for category, name, description, score, positions in results:
            item = QListWidgetItem()

            # Highlight matched characters in name
            highlighted_name = highlight_matches(name, positions)

            # Create rich text for the item
            html = f"""
            <div style='line-height: 1.4;'>
                <span style='color: #888888; font-size: 11px;'>{category}</span><br/>
                <span style='font-size: 13px; font-weight: bold;'>{highlighted_name}</span><br/>
                <span style='color: #aaaaaa; font-size: 11px;'>{description}</span>
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
        category, name = item.data(Qt.ItemDataRole.UserRole)
        self.node_selected.emit(category, name)
        self.accept()
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard events."""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            current_item = self._results_list.currentItem()
            if current_item:
                self._on_item_selected(current_item)
        elif event.key() == Qt.Key.Key_Down:
            current_row = self._results_list.currentRow()
            if current_row < self._results_list.count() - 1:
                self._results_list.setCurrentRow(current_row + 1)
        elif event.key() == Qt.Key.Key_Up:
            current_row = self._results_list.currentRow()
            if current_row > 0:
                self._results_list.setCurrentRow(current_row - 1)
        else:
            # Let search input handle other keys
            super().keyPressEvent(event)
    
    def showEvent(self, event):
        """Focus search input when dialog is shown."""
        super().showEvent(event)
        self._search_input.setFocus()
        self._search_input.clear()
