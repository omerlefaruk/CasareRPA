"""
Node Search Dialog for CasareRPA.

Provides Ctrl+F search functionality to find and navigate to nodes in the canvas.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import QEvent, Qt, Signal, Slot
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME
from casare_rpa.presentation.canvas.theme_system.helpers import (
    margin_none,
    set_fixed_width,
    set_spacing,
)
from casare_rpa.presentation.canvas.theme_system.tokens import TOKENS

if TYPE_CHECKING:
    from NodeGraphQt import NodeGraph


@dataclass
class NodeSearchResult:
    """Search result item."""

    node_id: str
    name: str
    node_type: str
    category: str


class NodeSearchDialog(QDialog):
    """
    Node search dialog for finding nodes in the canvas.

    Features:
    - Fuzzy search by node name
    - Filter by node type
    - Navigate to selected node
    - Highlight matches

    Signals:
        node_selected: Emitted when user selects a node (node_id: str)
    """

    node_selected = Signal(str)

    def __init__(self, graph: "NodeGraph", parent: QWidget | None = None) -> None:
        """
        Initialize the node search dialog.

        Args:
            graph: The NodeGraph instance to search
            parent: Parent widget
        """
        super().__init__(parent)
        self._graph = graph
        self._all_nodes: list[NodeSearchResult] = []
        self._filtered_nodes: list[NodeSearchResult] = []

        self._setup_ui()
        self._apply_styles()
        self._load_nodes()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle("Find Node")
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup
        )
        self.setModal(True)
        # Node search is slightly narrower than command palette
        set_fixed_width(self, TOKENS.sizes.panel_max_width)
        self.setMaximumHeight(TOKENS.sizes.dialog_height_md)

        layout = QVBoxLayout(self)
        margin_none(layout)
        set_spacing(layout, TOKENS.spacing.xs)

        # Search header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        set_margins(header_layout, (12, 8, 12, 8))

        search_icon = QLabel("🔍")
        header_layout.addWidget(search_icon)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search nodes by name...")
        self._search_input.textChanged.connect(self._on_search_text_changed)
        self._search_input.installEventFilter(self)
        header_layout.addWidget(self._search_input)

        # Match case checkbox
        self._case_sensitive = QCheckBox("Aa")
        self._case_sensitive.setToolTip("Case sensitive")
        self._case_sensitive.toggled.connect(self._on_case_sensitive_toggled)
        header_layout.addWidget(self._case_sensitive)

        layout.addWidget(header)

        # Results list
        self._results_list = QListWidget()
        self._results_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._results_list.itemClicked.connect(self._on_item_clicked)
        self._results_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._results_list)

        # Status bar
        self._status_label = QLabel("0 nodes found")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet(
            f"""
            QDialog {{
                background: {THEME.bg_panel};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.md}px;
            }}
            QLineEdit {{
                background: {THEME.bg_darkest};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.md}px;
                color: {THEME.text_primary};
                padding: {TOKENS.spacing.md}px;
                font-size: {TOKENS.typography.body}px;
            }}
            QLineEdit:focus {{
                border: 1px solid {THEME.border_focus};
            }}
            QListWidget {{
                background: {THEME.bg_panel};
                border: none;
                border-top: 1px solid {THEME.border};
                color: {THEME.text_secondary};
                font-size: {TOKENS.typography.body}px;
                outline: none;
            }}
            QListWidget::item {{
                padding: {TOKENS.spacing.md}px 12px;
                border: none;
            }}
            QListWidget::item:selected {{
                background: {THEME.bg_selected};
                color: {THEME.text_primary};
            }}
            QListWidget::item:hover:!selected {{
                background: {THEME.bg_hover};
            }}
            QLabel {{
                color: {THEME.text_muted};
                padding: {TOKENS.spacing.sm}px;
                font-size: {TOKENS.typography.body}px;
            }}
            QCheckBox {{
                color: {THEME.text_muted};
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
            }}
            """
        )

    def _load_nodes(self) -> None:
        """Load all nodes from the graph."""
        self._all_nodes.clear()

        for node in self._graph.all_nodes():
            node_id = node.get_property("node_id") or node.id()
            name = node.name() if hasattr(node, "name") else "Unknown"
            node_type = node.__class__.__name__

            # Get category from node type
            category = "General"
            if "Browser" in node_type:
                category = "Browser"
            elif "Desktop" in node_type:
                category = "Desktop"
            elif "Control" in node_type or "Flow" in node_type:
                category = "Control Flow"
            elif "Data" in node_type:
                category = "Data"

            self._all_nodes.append(
                NodeSearchResult(node_id=node_id, name=name, node_type=node_type, category=category)
            )

        self._filter_nodes("")
        self._update_results()

    def _filter_nodes(self, query: str) -> None:
        """Filter nodes based on search query."""
        if not query:
            self._filtered_nodes = self._all_nodes.copy()
            return

        case_sensitive = self._case_sensitive.isChecked()
        if not case_sensitive:
            query = query.lower()

        self._filtered_nodes = []
        for node in self._all_nodes:
            name = node.name if case_sensitive else node.name.lower()
            node_type = node.node_type if case_sensitive else node.node_type.lower()

            if query in name or query in node_type:
                self._filtered_nodes.append(node)

    def _update_results(self) -> None:
        """Update the results list."""
        self._results_list.clear()

        for node in self._filtered_nodes[:50]:  # Limit to 50 results
            item = QListWidgetItem()

            # Create display text
            display_text = f"{node.name}"
            item.setText(display_text)
            item.setToolTip(f"Type: {node.node_type}\nID: {node.node_id}")
            item.setData(Qt.ItemDataRole.UserRole, node.node_id)

            self._results_list.addItem(item)

        # Update status
        total = len(self._filtered_nodes)
        shown = min(total, 50)
        if total > 50:
            self._status_label.setText(f"Showing {shown} of {total} nodes")
        else:
            self._status_label.setText(f"{total} node(s) found")

        # Select first item
        if self._results_list.count() > 0:
            self._results_list.setCurrentRow(0)

    @Slot(str)
    def _on_search_text_changed(self, text: str) -> None:
        """Handle search text change."""
        self._filter_nodes(text)
        self._update_results()

    @Slot(bool)
    def _on_case_sensitive_toggled(self, checked: bool) -> None:
        """Handle case sensitivity toggle."""
        _ = checked
        self._on_search_text_changed(self._search_input.text())

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle item click - preview node."""
        node_id = item.data(Qt.ItemDataRole.UserRole)
        if node_id:
            self._select_and_center_node(node_id)

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle item double-click - select and close."""
        node_id = item.data(Qt.ItemDataRole.UserRole)
        if node_id:
            self._select_and_center_node(node_id)
            self.node_selected.emit(node_id)
            self.close()

    def _select_and_center_node(self, node_id: str) -> None:
        """Select a node and center view on it."""
        try:
            self._graph.clear_selection()
            for node in self._graph.all_nodes():
                if node.get_property("node_id") == node_id or node.id() == node_id:
                    node.set_selected(True)
                    self._graph.fit_to_selection()
                    break
        except Exception as e:
            logger.debug(f"Could not select node: {e}")

    def eventFilter(self, obj, event) -> bool:
        """Handle keyboard navigation."""
        if obj == self._search_input and event.type() == QEvent.Type.KeyPress:
            key = event.key()

            if key == Qt.Key.Key_Down:
                self._move_selection(1)
                return True
            elif key == Qt.Key.Key_Up:
                self._move_selection(-1)
                return True
            elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                self._execute_selected()
                return True
            elif key == Qt.Key.Key_Escape:
                self.close()
                return True

        return super().eventFilter(obj, event)

    def _move_selection(self, delta: int) -> None:
        """Move selection in the list."""
        current = self._results_list.currentRow()
        count = self._results_list.count()
        if count == 0:
            return

        new_row = max(0, min(count - 1, current + delta))
        self._results_list.setCurrentRow(new_row)

        # Preview the node
        item = self._results_list.currentItem()
        if item:
            node_id = item.data(Qt.ItemDataRole.UserRole)
            if node_id:
                self._select_and_center_node(node_id)

    def _execute_selected(self) -> None:
        """Execute action on selected item."""
        item = self._results_list.currentItem()
        if item:
            node_id = item.data(Qt.ItemDataRole.UserRole)
            if node_id:
                self._select_and_center_node(node_id)
                self.node_selected.emit(node_id)
                self.close()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press."""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def show_search(self) -> None:
        """Show the search dialog."""
        self._load_nodes()
        self._search_input.clear()
        self._search_input.setFocus()

        # Position at center-top of parent
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + 100
            self.move(x, y)

        self.show()
