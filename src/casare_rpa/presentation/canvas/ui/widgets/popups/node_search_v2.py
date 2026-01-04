"""
NodeSearchV2 - Node search dialog using v2 design system.

Epic 5.3: Node search with:
- PopupWindowBase for consistent popup behavior
- THEME_V2/TOKENS_V2 styling (dark-only, compact)
- Fuzzy search by node name
- Filter by node type
- Navigate to selected node
- Keyboard navigation

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.popups import NodeSearchV2

    search = NodeSearchV2(graph=graph, parent=main_window)
    search.show_search()

Signals:
    node_selected: Signal(str) - Emitted when node selected (node_id)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from loguru import logger
from PySide6.QtCore import QPoint, Qt, Signal, Slot
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.primitives.inputs import SearchInput

from .popup_utils import get_scrollbar_style_v2
from .popup_window_base import PopupWindowBase

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


@dataclass(frozen=True)
class NodeSearchResult:
    """Search result item."""

    node_id: str
    name: str
    node_type: str
    category: str


class NodeItemWidget(QFrame):
    """
    Custom widget for displaying a node in the search list.

    Shows:
    - Node name (left)
    - Category badge (middle)
    - Node type (right, muted)
    """

    def __init__(
        self,
        item: NodeSearchResult,
        is_selected: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize node item widget.

        Args:
            item: NodeSearchResult data
            is_selected: Whether this item is selected
            parent: Parent widget
        """
        super().__init__(parent)
        self._item = item
        self._is_selected = is_selected

        self._setup_ui()
        self._update_style()

    def _setup_ui(self) -> None:
        """Setup the UI layout."""
        self.setFixedHeight(TOKENS_V2.sizes.row_height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.xs,
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.xs,
        )
        layout.setSpacing(TOKENS_V2.spacing.md)

        # Node name
        name_label = QLabel(self._item.name)
        name_label.setStyleSheet(f"""
            color: {THEME_V2.text_primary};
            font-size: {TOKENS_V2.typography.body}px;
            font-weight: {TOKENS_V2.typography.weight_medium};
        """)
        layout.addWidget(name_label)

        # Category badge
        category_color = self._category_color()
        category_label = QLabel(self._item.category)
        category_label.setStyleSheet(f"""
            background-color: {category_color};
            color: {THEME_V2.text_on_primary};
            border-radius: {TOKENS_V2.radius.xs}px;
            padding: 2px {TOKENS_V2.spacing.sm}px;
            font-size: {TOKENS_V2.typography.caption}px;
        """)
        layout.addWidget(category_label)

        layout.addStretch()

        # Node type (muted)
        type_label = QLabel(self._item.node_type)
        type_label.setStyleSheet(f"""
            color: {THEME_V2.text_muted};
            font-size: {TOKENS_V2.typography.caption}px;
        """)
        layout.addWidget(type_label)

    def _category_color(self) -> str:
        """Get color for category badge."""
        colors = {
            "Browser": THEME_V2.info,
            "Desktop": THEME_V2.success,
            "Control Flow": THEME_V2.warning,
            "Data": THEME_V2.primary,
            "Variable": THEME_V2.primary,
            "System": THEME_V2.secondary,
            "HTTP": THEME_V2.primary,
        }
        return colors.get(self._item.category, THEME_V2.text_muted)

    def _update_style(self) -> None:
        """Update style based on selection state."""
        bg = THEME_V2.bg_selected if self._is_selected else "transparent"

        self.setStyleSheet(f"""
            NodeItemWidget {{
                background-color: {bg};
                border: none;
                border-radius: {TOKENS_V2.radius.xs}px;
            }}
        """)

    def set_selected(self, selected: bool) -> None:
        """Set selection state."""
        if self._is_selected != selected:
            self._is_selected = selected
            self._update_style()


class NodeSearchV2(PopupWindowBase):
    """
    Node search dialog for finding nodes in the canvas.

    Features:
    - Fuzzy search by node name
    - Filter by node type
    - Navigate to selected node
    - Keyboard navigation
    - THEME_V2/TOKENS_V2 styling

    Signals:
        node_selected: Signal(str) - Emitted with node_id
    """

    node_selected = Signal(str)

    # Default dimensions
    DEFAULT_WIDTH = 450
    DEFAULT_HEIGHT = 400
    MIN_WIDTH = 350
    MIN_HEIGHT = 250

    # Max visible items
    MAX_VISIBLE_ITEMS = 8

    def __init__(
        self,
        graph: Any,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize the node search dialog.

        Args:
            graph: The NodeGraph instance to search
            parent: Parent widget
        """
        super().__init__(
            title="Find Node",
            parent=parent,
            resizable=False,
            pin_button=False,
            close_button=True,
            min_width=self.MIN_WIDTH,
            min_height=self.MIN_HEIGHT,
        )

        # Graph reference
        self._graph = graph

        # State
        self._all_nodes: list[NodeSearchResult] = []
        self._filtered_nodes: list[NodeSearchResult] = []
        self._selected_index: int = -1
        self._case_sensitive: bool = False

        # UI components
        self._search_input: SearchInput | None = None
        self._results_list: QListWidget | None = None
        self._status_label: QLabel | None = None
        self._case_checkbox: QCheckBox | None = None

        # Setup content
        self._setup_content()
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

        # Nodes are loaded on-demand (tests call `_load_nodes()` explicitly).

    def _setup_content(self) -> None:
        """Setup the content widget."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Search header
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_V2.bg_elevated};
                border-bottom: 1px solid {THEME_V2.border};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.sm,
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.sm,
        )
        header_layout.setSpacing(TOKENS_V2.spacing.sm)

        # Search input
        self._search_input = SearchInput(
            placeholder="Search nodes by name...",
            search_delay=0,
            size="md",
        )
        self._search_input.text_changed.connect(self._on_search_changed)
        header_layout.addWidget(self._search_input)

        # Case sensitive checkbox
        self._case_checkbox = QCheckBox("Aa")
        self._case_checkbox.setToolTip("Case sensitive")
        self._case_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {THEME_V2.text_secondary};
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.xs}px;
                background: {THEME_V2.bg_component};
            }}
            QCheckBox::indicator:checked {{
                background: {THEME_V2.primary};
                border-color: {THEME_V2.primary};
            }}
        """)
        self._case_checkbox.toggled.connect(self._on_case_toggled)
        header_layout.addWidget(self._case_checkbox)

        layout.addWidget(header)

        # Results list
        self._results_list = QListWidget()
        self._results_list.setObjectName("nodeSearchList")
        self._results_list.setFrameShape(QFrame.Shape.NoFrame)
        self._results_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._results_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._results_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._results_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._results_list.setStyleSheet(f"""
            QListWidget#nodeSearchList {{
                background-color: transparent;
                border: none;
                outline: none;
            }}
            {get_scrollbar_style_v2()}
        """)

        self._results_list.itemClicked.connect(self._on_item_clicked)
        self._results_list.itemDoubleClicked.connect(self._on_item_activated)
        layout.addWidget(self._results_list)

        # Status bar
        self._status_label = QLabel("0 nodes found")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet(f"""
            color: {THEME_V2.text_muted};
            font-size: {TOKENS_V2.typography.caption}px;
            padding: {TOKENS_V2.spacing.xs}px;
            background-color: {THEME_V2.bg_elevated};
            border-top: 1px solid {THEME_V2.border};
        """)
        layout.addWidget(self._status_label)

        self.set_content_widget(container)

    def show_search(self) -> None:
        """
        Show the search dialog.

        Reloads nodes and positions at center-top of parent.
        """
        self._load_nodes()
        if self._search_input:
            self._search_input.set_value("")
        self._filter_nodes("")

        # Position at center-top of parent or screen
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + 80
        else:
            from PySide6.QtWidgets import QApplication

            screen = QApplication.primaryScreen().availableGeometry()
            x = (screen.width() - self.width()) // 2
            y = screen.top() + 80

        self.show_at_position(QPoint(x, y))

        if self._search_input:
            self._search_input._input.setFocus()

    def _load_nodes(self) -> None:
        """Load all nodes from the graph."""
        self._all_nodes.clear()

        if not self._graph:
            return

        try:
            # Handle both NodeGraphQt and custom graph implementations
            if hasattr(self._graph, "all_nodes"):
                nodes = self._graph.all_nodes()
            elif hasattr(self._graph, "nodes"):
                nodes = self._graph.nodes()
            else:
                logger.warning("Unsupported graph type for node search")
                return

            for node in nodes:
                node_id = (
                    node.get_property("node_id") if hasattr(node, "get_property") else node.id()
                )
                name = node.name() if hasattr(node, "name") else "Unknown"
                node_type = node.__class__.__name__

                # Determine category
                category = self._get_category_for_type(node_type)

                self._all_nodes.append(
                    NodeSearchResult(
                        node_id=node_id,
                        name=name,
                        node_type=node_type,
                        category=category,
                    ),
                )

        except Exception as e:
            logger.error(f"Error loading nodes for search: {e}")

    def _get_category_for_type(self, node_type: str) -> str:
        """Get category for node type."""
        type_lower = node_type.lower()

        if "browser" in type_lower:
            return "Browser"
        if "desktop" in type_lower:
            return "Desktop"
        if "control" in type_lower or "flow" in type_lower or "loop" in type_lower:
            return "Control Flow"
        if "variable" in type_lower:
            return "Variable"
        if "data" in type_lower or "set" in type_lower:
            return "Data"
        if "http" in type_lower or "request" in type_lower or "api" in type_lower:
            return "HTTP"
        if "system" in type_lower or "message" in type_lower or "tooltip" in type_lower:
            return "System"

        return "General"

    @Slot(str)
    def _on_search_changed(self, text: str) -> None:
        """Handle search text changes."""
        self._filter_nodes(text)

    @Slot(bool)
    def _on_case_toggled(self, checked: bool) -> None:
        """Handle case sensitivity toggle."""
        self._case_sensitive = checked
        self._filter_nodes(self._search_input.get_value() if self._search_input else "")

    def _filter_nodes(self, query: str) -> None:
        """Filter nodes by query and refresh results list."""
        scored: list[tuple[int, NodeSearchResult]] = []
        for node in self._all_nodes:
            is_match, score = self._calculate_match_score(query, node)
            if is_match:
                scored.append((score, node))

        scored.sort(key=lambda item: item[0])
        self._filtered_nodes = [node for _, node in scored]
        self._refresh_results_list()

    def _refresh_results_list(self) -> None:
        """Render `_filtered_nodes` into the list widget."""
        if not self._results_list:
            return

        self._results_list.clear()
        for node in self._filtered_nodes[: self.MAX_VISIBLE_ITEMS]:
            list_item = QListWidgetItem()
            widget = NodeItemWidget(node)
            list_item.setSizeHint(widget.sizeHint())
            list_item.setData(Qt.ItemDataRole.UserRole, node.node_id)
            self._results_list.addItem(list_item)
            self._results_list.setItemWidget(list_item, widget)

        # Update status
        total = len(self._filtered_nodes)
        shown = min(total, self.MAX_VISIBLE_ITEMS)
        if self._status_label:
            if total > self.MAX_VISIBLE_ITEMS:
                self._status_label.setText(f"Showing {shown} of {total} nodes")
            else:
                self._status_label.setText(f"{total} node(s) found")

        # Auto-select first item
        if self._filtered_nodes:
            self._select_row(0)
        else:
            self._selected_index = -1
            self._results_list.setCurrentRow(-1)

        # Adjust height
        self._adjust_height()

    def _calculate_match_score(
        self,
        query: str,
        node: NodeSearchResult,
    ) -> tuple[bool, int]:
        """
        Calculate fuzzy match score.

        Returns:
            Tuple of (is_match, score) where lower score = better match
        """
        if not query:
            return True, 0

        # Apply case sensitivity
        name = node.name if self._case_sensitive else node.name.lower()
        query_check = query if self._case_sensitive else query.lower()
        node_type = node.node_type if self._case_sensitive else node.node_type.lower()

        # Exact match (best)
        if query_check == name:
            return True, 0

        # Prefix match (good)
        if name.startswith(query_check):
            return True, 10

        # Contains match (ok)
        if query_check in name:
            return True, 20 + name.index(query_check)

        # Node type match
        if query_check in node_type:
            return True, 50

        # Fuzzy match
        query_idx = 0
        consecutive_bonus = 0
        for char in name:
            if query_idx < len(query_check) and char == query_check[query_idx]:
                query_idx += 1
                consecutive_bonus += 5

        if query_idx == len(query_check):
            return True, 60 - consecutive_bonus

        return False, 0

    def _select_row(self, row: int) -> None:
        """Select a row by index."""
        if not self._results_list or not self._filtered_nodes:
            return

        # Clear previous selection
        if 0 <= self._selected_index < self._results_list.count():
            prev_item = self._results_list.item(self._selected_index)
            if prev_item:
                prev_widget = self._results_list.itemWidget(prev_item)
                if isinstance(prev_widget, NodeItemWidget):
                    prev_widget.set_selected(False)

        # Set new selection
        self._selected_index = row
        self._results_list.setCurrentRow(row)
        if 0 <= row < self._results_list.count():
            new_item = self._results_list.item(row)
            if new_item:
                new_widget = self._results_list.itemWidget(new_item)
                if isinstance(new_widget, NodeItemWidget):
                    new_widget.set_selected(True)
                    # Preview the node
                    node_id = new_item.data(Qt.ItemDataRole.UserRole)
                    if node_id:
                        self._select_and_center_node(node_id)
                self._results_list.scrollToItem(new_item)

    def _adjust_height(self) -> None:
        """Adjust popup height based on visible items."""
        if not self._results_list:
            return

        item_count = min(len(self._filtered_nodes), self.MAX_VISIBLE_ITEMS)
        item_height = TOKENS_V2.sizes.row_height

        # Calculate content height
        header_height = 44  # Approximate
        status_height = 28  # Approximate
        content_height = item_count * item_height

        total_height = header_height + content_height + status_height

        # Clamp
        total_height = max(self.MIN_HEIGHT, min(total_height, self.DEFAULT_HEIGHT))

        self.resize(self.DEFAULT_WIDTH, total_height)

    def _select_and_center_node(self, node_id: str) -> None:
        """Select a node and center view on it."""
        if not self._graph:
            return

        try:
            if hasattr(self._graph, "clear_selection"):
                self._graph.clear_selection()

            # Find and select the node
            if hasattr(self._graph, "all_nodes"):
                nodes = self._graph.all_nodes()
            elif hasattr(self._graph, "nodes"):
                nodes = self._graph.nodes()
            else:
                return

            for node in nodes:
                node_id_check = (
                    node.get_property("node_id") if hasattr(node, "get_property") else node.id()
                )
                if node_id_check == node_id:
                    if hasattr(node, "set_selected"):
                        node.set_selected(True)
                    if hasattr(self._graph, "fit_to_selection"):
                        self._graph.fit_to_selection()
                    break
        except Exception as e:
            logger.debug(f"Could not select node: {e}")

    def _confirm_selection(self) -> None:
        """Execute action on selected item."""
        if not self._results_list:
            return

        item = self._results_list.item(self._selected_index) if self._selected_index >= 0 else None
        if item:
            node_id = item.data(Qt.ItemDataRole.UserRole)
            if node_id:
                self._select_and_center_node(node_id)
                self.node_selected.emit(node_id)
                self.close()

    def _move_selection(self, delta: int) -> None:
        """Move selection by delta."""
        if not self._results_list or not self._filtered_nodes:
            return

        count = self._results_list.count()
        if count <= 0:
            return

        current = self._results_list.currentRow()
        if current < 0:
            current = 0

        new_index = max(0, min(current + delta, count - 1))
        self._select_row(new_index)

    @Slot()
    def _on_item_clicked(self, list_item: QListWidgetItem) -> None:
        """Handle item click - select only."""
        row = self._results_list.row(list_item) if self._results_list else -1
        if row >= 0:
            self._select_row(row)

    @Slot()
    def _on_item_activated(self, list_item: QListWidgetItem) -> None:
        """Handle item double-click - select and close."""
        row = self._results_list.row(list_item) if self._results_list else -1
        if row >= 0:
            self._select_row(row)
            self._confirm_selection()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events for navigation."""
        key = event.key()

        match key:
            case Qt.Key.Key_Up | Qt.Key.Key_K:
                event.accept()
                self._move_selection(-1)
                return

            case Qt.Key.Key_Down | Qt.Key.Key_J:
                event.accept()
                self._move_selection(1)
                return

            case Qt.Key.Key_Return | Qt.Key.Key_Enter:
                event.accept()
                self._confirm_selection()
                return

            case Qt.Key.Key_Escape:
                event.accept()
                self.close()
                return

        # Pass other keys to search input
        if self._search_input:
            if event.text() and not event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                self._search_input._input.setFocus()
                self._search_input._input.keyPressEvent(event)
                return

        super().keyPressEvent(event)

    def showEvent(self, event) -> None:
        """Handle show event - ensure first item selected."""
        super().showEvent(event)
        if self._filtered_nodes and self._selected_index < 0:
            self._select_row(0)
        if self._search_input:
            self._search_input._input.setFocus()


__all__ = ["NodeItemWidget", "NodeSearchResult", "NodeSearchV2"]
