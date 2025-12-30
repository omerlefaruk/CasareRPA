"""
List/Tree Primitive Components v2 - Epic 5.1 Component Library.

Provides styled wrappers for Qt list/tree/table widgets following the v2 design system:
- Compact sizing using TOKENS_V2 (row heights: 22px compact, 28px standard)
- THEME_V2 colors (dark-only, Cursor blue accent)
- icon_v2 for sort indicators
- Proper @Slot decorators
- Type hints throughout

Components:
    ListItem: Styled QListWidgetItem wrapper with hover/selected states
    TreeItem: Styled QTreeWidgetItem wrapper with nested support
    TableHeader: Styled table header with sort indicators

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.primitives.lists import (
        ListItem,
        TreeItem,
        TableHeader,
        apply_list_style,
        apply_tree_style,
        apply_table_style,
    )

    # Apply styling to existing widgets
    list_widget = QListWidget()
    apply_list_style(list_widget)

    # Create styled items
    item = ListItem(text="Item 1", value="1", icon="file")
    list_widget.addItem(item)

    # Tree with nested items
    tree = QTreeWidget()
    apply_tree_style(tree)

    parent = TreeItem(text="Folder", value="folder1", icon="folder")
    parent.add_child(TreeItem(text="File.txt", value="file1", icon="file"))
    tree.addTopLevelItem(parent)

    # Table with sortable headers
    table = QTableWidget()
    header = TableHeader(table.horizontalHeader())
    header.add_section("Name", "name", sortable=True)
    header.add_section("Size", "size", sortable=True)

See: docs/UX_REDESIGN_PLAN.md Phase 5 Epic 5.1
"""

from __future__ import annotations

from typing import Any, Literal

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QHeaderView,
    QListWidget,
    QListWidgetItem,
    QTableWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.theme_system.icons_v2 import get_icon

# =============================================================================
# TYPE ALIASES
# =============================================================================

RowSize = Literal["compact", "standard"]
SortOrder = Literal["none", "asc", "desc"]

# =============================================================================
# STYLESHEET GENERATORS
# =============================================================================


def _get_list_stylesheet() -> str:
    """
    Generate QSS stylesheet for QListWidget.

    Returns:
        QSS stylesheet string with v2 styling
    """
    return f"""
        QListWidget {{
            background-color: {THEME_V2.bg_surface};
            border: 1px solid {THEME_V2.border};
            border-radius: {TOKENS_V2.radius.sm}px;
            outline: none;
            padding: 0;
        }}
        QListWidget::item {{
            padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.xs}px;
            color: {THEME_V2.text_primary};
            border-radius: {TOKENS_V2.radius.xs}px;
            margin: 1px;
            min-height: {TOKENS_V2.sizes.row_height}px;
        }}
        QListWidget::item:hover {{
            background-color: {THEME_V2.bg_hover};
        }}
        QListWidget::item:selected {{
            background-color: {THEME_V2.bg_selected};
            color: {THEME_V2.text_primary};
        }}
        QListWidget::item:disabled {{
            color: {THEME_V2.text_disabled};
        }}
    """


def _get_list_compact_stylesheet() -> str:
    """
    Generate compact QSS stylesheet for QListWidget.

    Returns:
        QSS stylesheet string with smaller row height
    """
    return f"""
        QListWidget {{
            background-color: {THEME_V2.bg_surface};
            border: 1px solid {THEME_V2.border};
            border-radius: {TOKENS_V2.radius.sm}px;
            outline: none;
            padding: 0;
        }}
        QListWidget::item {{
            padding: {TOKENS_V2.spacing.xxs}px {TOKENS_V2.spacing.xs}px;
            color: {THEME_V2.text_primary};
            border-radius: {TOKENS_V2.radius.xs}px;
            margin: 1px;
            min-height: {TOKENS_V2.sizes.row_height_compact}px;
        }}
        QListWidget::item:hover {{
            background-color: {THEME_V2.bg_hover};
        }}
        QListWidget::item:selected {{
            background-color: {THEME_V2.bg_selected};
            color: {THEME_V2.text_primary};
        }}
        QListWidget::item:disabled {{
            color: {THEME_V2.text_disabled};
        }}
    """


def _get_tree_stylesheet() -> str:
    """
    Generate QSS stylesheet for QTreeWidget.

    Returns:
        QSS stylesheet string with v2 styling
    """
    return f"""
        QTreeWidget {{
            background-color: {THEME_V2.bg_surface};
            border: 1px solid {THEME_V2.border};
            border-radius: {TOKENS_V2.radius.sm}px;
            outline: none;
            padding: 0;
        }}
        QTreeWidget::item {{
            padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.xs}px;
            color: {THEME_V2.text_primary};
            border-radius: {TOKENS_V2.radius.xs}px;
            min-height: {TOKENS_V2.sizes.row_height}px;
        }}
        QTreeWidget::item:hover {{
            background-color: {THEME_V2.bg_hover};
        }}
        QTreeWidget::item:selected {{
            background-color: {THEME_V2.bg_selected};
            color: {THEME_V2.text_primary};
        }}
        QTreeWidget::item:disabled {{
            color: {THEME_V2.text_disabled};
        }}
        QTreeWidget::branch {{
            background-color: transparent;
        }}
        QTreeWidget::branch:has-children:!has-siblings:closed,
        QTreeWidget::branch:closed:has-children:has-siblings {{
            border-image: none;
            image: none;
        }}
        QTreeWidget::branch:open:has-children:!has-siblings,
        QTreeWidget::branch:open:has-children:has-siblings {{
            border-image: none;
            image: none;
        }}
    """


def _get_table_stylesheet() -> str:
    """
    Generate QSS stylesheet for QTableWidget.

    Returns:
        QSS stylesheet string with v2 styling
    """
    return f"""
        QTableWidget {{
            background-color: {THEME_V2.bg_surface};
            border: 1px solid {THEME_V2.border};
            border-radius: {TOKENS_V2.radius.sm}px;
            gridline-color: {THEME_V2.bg_canvas};
            outline: none;
        }}
        QTableWidget::item {{
            padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.xs}px;
            color: {THEME_V2.text_primary};
            border: none;
            border-bottom: 1px solid {THEME_V2.bg_canvas};
        }}
        QTableWidget::item:selected {{
            background-color: {THEME_V2.bg_selected};
            color: {THEME_V2.text_primary};
        }}
        QTableWidget::item:hover {{
            background-color: {THEME_V2.bg_hover};
        }}
    """


def _get_header_stylesheet() -> str:
    """
    Generate QSS stylesheet for QHeaderView.

    Returns:
        QSS stylesheet string with v2 styling
    """
    return f"""
        QHeaderView {{
            background-color: {THEME_V2.bg_surface};
            color: {THEME_V2.text_secondary};
            border: none;
            border-bottom: 1px solid {THEME_V2.border};
            padding: 0;
            margin: 0;
        }}
        QHeaderView::section {{
            background-color: {THEME_V2.bg_surface};
            color: {THEME_V2.text_secondary};
            padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.xs}px;
            border: none;
            border-right: 1px solid {THEME_V2.bg_canvas};
            font-weight: {TOKENS_V2.typography.weight_semibold};
            font-size: {TOKENS_V2.typography.body_sm}px;
            text-transform: uppercase;
        }}
        QHeaderView::section:hover {{
            background-color: {THEME_V2.bg_hover};
            color: {THEME_V2.text_primary};
        }}
        QHeaderView::down-arrow {{
            image: none;
        }}
        QHeaderView::up-arrow {{
            image: none;
        }}
    """


# =============================================================================
# LIST ITEM
# =============================================================================


class ListItem(QListWidgetItem):
    """
    Styled list item wrapper for QListWidget.

    Provides a convenient interface for creating styled list items
    with optional icons and user data values.

    Features:
    - Optional icon from icon_v2
    - Text label
    - User data value (for tracking selections)
    - Enabled/disabled state
    - Selected state

    Example:
        from casare_rpa.presentation.canvas.ui.widgets.primitives.lists import ListItem

        # Simple item
        item = ListItem(text="Item 1", value="1")
        list_widget.addItem(item)

        # Item with icon
        item = ListItem(text="Document.txt", value="doc1", icon="file")
        list_widget.addItem(item)

        # Disabled item
        item = ListItem(text="Locked", value="locked", enabled=False)
    """

    def __init__(
        self,
        text: str = "",
        value: Any = None,
        *,
        icon: str | None = None,
        icon_size: int = 16,
        enabled: bool = True,
        selected: bool = False,
    ) -> None:
        """
        Initialize ListItem.

        Args:
            text: Display text for the item
            value: User data value (stored in UserRole)
            icon: Optional icon name from icon_v2
            icon_size: Icon size in pixels (default: 16)
            enabled: Whether item is enabled
            selected: Whether item is initially selected
        """
        super().__init__(text)

        self._value = value
        self._icon_name = icon

        # Set icon if provided
        if icon:
            self.set_icon(icon, icon_size)

        # Store value in user role
        if value is not None:
            self.setData(Qt.ItemDataRole.UserRole, value)

        # Set enabled state
        self.set_enabled(enabled)

        # Set selected state (only effective when added to widget)
        if selected:
            self.setSelected(True)

    def set_icon(self, icon_name: str, size: int = 16) -> None:
        """
        Set the icon for this item.

        Args:
            icon_name: Icon name from icon_v2
            size: Icon size in pixels
        """
        self._icon_name = icon_name
        state = "disabled" if not self.is_item_enabled() else "normal"
        qicon = get_icon(icon_name, size=size, state=state)
        self.setIcon(qicon)

    def get_icon_name(self) -> str | None:
        """Get the icon name."""
        return self._icon_name

    def set_value(self, value: Any) -> None:
        """
        Set the user data value.

        Args:
            value: Value to store in UserRole
        """
        self._value = value
        self.setData(Qt.ItemDataRole.UserRole, value)

    def get_value(self) -> Any:
        """Get the user data value."""
        return self._value

    def set_enabled(self, enabled: bool) -> None:
        """
        Set enabled state.

        Args:
            enabled: Whether item should be enabled
        """
        self.setFlags(
            self.flags() | Qt.ItemFlag.ItemIsEnabled
            if enabled
            else self.flags() & ~Qt.ItemFlag.ItemIsEnabled
        )

        # Update icon state if present
        if self._icon_name:
            self.set_icon(self._icon_name, 16)

    def is_item_enabled(self) -> bool:
        """Check if item is enabled."""
        return bool(self.flags() & Qt.ItemFlag.ItemIsEnabled)

    def clone(self) -> ListItem:
        """Create a copy of this item."""
        new_item = ListItem(
            text=self.text(),
            value=self._value,
            icon=self._icon_name,
            enabled=self.is_item_enabled(),
        )
        new_item.setSelected(self.isSelected())
        return new_item


# =============================================================================
# TREE ITEM
# =============================================================================


class TreeItem(QTreeWidgetItem):
    """
    Styled tree item wrapper for QTreeWidget.

    Provides a convenient interface for creating styled tree items
    with optional icons and nested children.

    Features:
    - Optional icon from icon_v2
    - Text label
    - User data value
    - Nested children support
    - Expanded/collapsed state tracking
    - Signals for expand/collapse changes

    Signals:
        expanded_changed(bool): Emitted when expand state changes

    Example:
        from casare_rpa.presentation.canvas.ui.widgets.primitives.lists import TreeItem

        # Parent item with children
        parent = TreeItem(text="Folder", value="folder1", icon="folder")
        parent.add_child(TreeItem(text="File1.txt", value="file1", icon="file"))
        parent.add_child(TreeItem(text="File2.txt", value="file2", icon="file"))
        tree.addTopLevelItem(parent)

        # Auto-expand
        parent.set_expanded(True)
    """

    expanded_changed = Signal(bool)

    def __init__(
        self,
        text: str = "",
        value: Any = None,
        *,
        icon: str | None = None,
        icon_size: int = 16,
        enabled: bool = True,
        expanded: bool = False,
        parent: QTreeWidgetItem | None = None,
    ) -> None:
        """
        Initialize TreeItem.

        Args:
            text: Display text for the item
            value: User data value (stored in UserRole)
            icon: Optional icon name from icon_v2
            icon_size: Icon size in pixels (default: 16)
            enabled: Whether item is enabled
            expanded: Whether item is initially expanded (if has children)
            parent: Parent tree item (for QTreeWidgetItem constructor)
        """
        super().__init__(parent)

        self._value = value
        self._icon_name = icon
        self._is_expanded = expanded
        self._children: list[TreeItem] = []
        self._expansion_blocked = False

        # Set columns (default single column)
        self.setText(0, text)

        # Set icon if provided
        if icon:
            self.set_icon(icon, icon_size)

        # Store value in user role
        if value is not None:
            self.setData(0, Qt.ItemDataRole.UserRole, value)

        # Set enabled state
        self.set_enabled(enabled)

    def set_icon(self, icon_name: str, size: int = 16) -> None:
        """
        Set the icon for this item.

        Args:
            icon_name: Icon name from icon_v2
            size: Icon size in pixels
        """
        self._icon_name = icon_name
        state = "disabled" if not self.is_item_enabled() else "normal"
        qicon = get_icon(icon_name, size=size, state=state)
        self.setIcon(0, qicon)

    def get_icon_name(self) -> str | None:
        """Get the icon name."""
        return self._icon_name

    def set_value(self, value: Any) -> None:
        """
        Set the user data value.

        Args:
            value: Value to store in UserRole
        """
        self._value = value
        self.setData(0, Qt.ItemDataRole.UserRole, value)

    def get_value(self) -> Any:
        """Get the user data value."""
        return self._value

    def set_enabled(self, enabled: bool) -> None:
        """
        Set enabled state.

        Args:
            enabled: Whether item should be enabled
        """
        self.setFlags(
            self.flags() | Qt.ItemFlag.ItemIsEnabled
            if enabled
            else self.flags() & ~Qt.ItemFlag.ItemIsEnabled
        )

        # Update icon state if present
        if self._icon_name:
            self.set_icon(self._icon_name, 16)

    def is_item_enabled(self) -> bool:
        """Check if item is enabled."""
        return bool(self.flags() & Qt.ItemFlag.ItemIsEnabled)

    def add_child(self, child: TreeItem) -> None:
        """
        Add a child item.

        Args:
            child: TreeItem to add as child
        """
        self._children.append(child)
        self.addChild(child)

        # Expand if set
        if self._is_expanded and not self.isExpanded():
            self._set_expanded(True, internal=True)

    def insert_child(self, index: int, child: TreeItem) -> None:
        """
        Insert a child item at specific position.

        Args:
            index: Position to insert at
            child: TreeItem to insert
        """
        if 0 <= index <= len(self._children):
            self._children.insert(index, child)
            self.insertChild(index, child)

    def remove_child(self, child: TreeItem) -> None:
        """
        Remove a child item.

        Args:
            child: TreeItem to remove
        """
        if child in self._children:
            self._children.remove(child)
            self.removeChild(child)

    def get_children(self) -> list[TreeItem]:
        """Get list of child items."""
        return self._children.copy()

    def child_count(self) -> int:
        """Get number of children."""
        return len(self._children)

    def has_children_items(self) -> bool:
        """Check if item has children."""
        return len(self._children) > 0

    def set_expanded(self, expanded: bool) -> None:
        """
        Set expanded state.

        Args:
            expanded: Whether to expand the item
        """
        self._is_expanded = expanded
        if self.has_children_items():
            self.setExpanded(expanded)
        self._set_expanded(expanded, internal=True)

    def _set_expanded(self, expanded: bool, internal: bool) -> None:
        """Internal expanded state setter with signal control."""
        if not internal:
            self._is_expanded = expanded

        if not self._expansion_blocked:
            self._expansion_blocked = True
            self.expanded_changed.emit(expanded)
            self._expansion_blocked = False

    def is_expanded(self) -> bool:
        """Check if item is expanded."""
        return self._is_expanded or self.isExpanded()

    def clone(self) -> TreeItem:
        """Create a shallow copy of this item (without children)."""
        new_item = TreeItem(
            text=self.text(0),
            value=self._value,
            icon=self._icon_name,
            enabled=self.is_item_enabled(),
            expanded=self._is_expanded,
        )
        new_item.setSelected(self.isSelected())
        return new_item

    def clone_with_children(self) -> TreeItem:
        """Create a deep copy of this item including all children."""
        new_item = self.clone()
        for child in self._children:
            new_item.add_child(child.clone_with_children())
        return new_item


# =============================================================================
# TABLE HEADER
# =============================================================================


class TableHeader(QWidget):
    """
    Styled table header wrapper with sort indicators.

    Provides a managed header interface for QTableWidget with
    sortable columns and visual sort indicators.

    Features:
    - Column sections with text and optional sort
    - Sort indicator icons (asc/desc)
    - Click to sort functionality
    - Multi-column sort state tracking

    Signals:
        sort_requested(column_id, order): Emitted when sort is requested

    Example:
        from casare_rpa.presentation.canvas.ui.widgets.primitives.lists import TableHeader

        table = QTableWidget()
        table.setColumnCount(2)

        header = TableHeader(table.horizontalHeader())
        header.add_section("Name", "name", sortable=True)
        header.add_section("Size", "size", sortable=True)

        # Connect to sort handler
        header.sort_requested.connect(lambda col, order: print(f"Sort {col} {order}"))
    """

    sort_requested = Signal(str, str)  # (column_id, order: "asc"/"desc")

    def __init__(
        self,
        header_view: QHeaderView,
        *,
        clickable: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize TableHeader.

        Args:
            header_view: QHeaderView from QTableWidget
            clickable: Whether header sections are clickable
            parent: Parent widget
        """
        super().__init__(parent)

        self._header = header_view
        self._clickable = clickable
        self._sections: list[dict] = []  # {"id": str, "text": str, "sortable": bool}
        self._sort_states: dict[str, SortOrder] = {}  # column_id -> SortOrder

        self._setup_header()

    def _setup_header(self) -> None:
        """Configure the header view."""
        # Apply styling
        self._header.setStyleSheet(_get_header_stylesheet())

        # Configure header properties
        self._header.setStretchLastSection(True)
        self._header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Connect signals for clickable headers
        if self._clickable:
            self._header.sectionClicked.connect(self._on_section_clicked)

    @Slot(int)
    def _on_section_clicked(self, logical_index: int) -> None:
        """
        Handle header section click.

        Args:
            logical_index: Column index that was clicked
        """
        if logical_index < 0 or logical_index >= len(self._sections):
            return

        section = self._sections[logical_index]
        column_id = section["id"]

        if not section.get("sortable", False):
            return

        # Toggle sort state: none -> asc -> desc -> none
        current_state = self._sort_states.get(column_id, "none")
        if current_state == "none":
            new_state = "asc"
        elif current_state == "asc":
            new_state = "desc"
        else:
            new_state = "none"

        self.set_sort_order(column_id, new_state)
        self.sort_requested.emit(column_id, new_state)

    def add_section(
        self,
        text: str,
        column_id: str,
        *,
        sortable: bool = False,
        width: int | None = None,
    ) -> None:
        """
        Add a header section.

        Args:
            text: Display text for the section
            column_id: Unique identifier for the column
            sortable: Whether column is sortable
            width: Optional fixed width for the column
        """
        self._sections.append({
            "id": column_id,
            "text": text,
            "sortable": sortable,
        })
        self._sort_states[column_id] = "none"

        # Set section text
        index = len(self._sections) - 1
        model = self._header.model()
        if model:
            model.setHeaderData(index, Qt.Orientation.Horizontal, text)

        # Set width if specified
        if width is not None:
            self._header.resizeSection(index, width)

    def remove_section(self, column_id: str) -> None:
        """
        Remove a section by ID.

        Args:
            column_id: ID of section to remove
        """
        self._sections = [s for s in self._sections if s["id"] != column_id]
        if column_id in self._sort_states:
            del self._sort_states[column_id]

    def set_sort_order(self, column_id: str, order: SortOrder) -> None:
        """
        Set sort order for a column.

        Args:
            column_id: Column identifier
            order: Sort order ("none", "asc", "desc")
        """
        if column_id not in self._sort_states:
            return

        # Reset other columns' sort indicators
        for col_id in self._sort_states:
            if col_id != column_id:
                self._sort_states[col_id] = "none"

        self._sort_states[column_id] = order

        # Update visual indicator
        self._update_sort_indicator()

    def get_sort_order(self, column_id: str) -> SortOrder:
        """
        Get current sort order for a column.

        Args:
            column_id: Column identifier

        Returns:
            Current sort order ("none", "asc", or "desc")
        """
        return self._sort_states.get(column_id, "none")

    def get_sorted_column(self) -> tuple[str, SortOrder] | None:
        """
        Get the currently sorted column.

        Returns:
            Tuple of (column_id, sort_order) or None if no sort active
        """
        for col_id, order in self._sort_states.items():
            if order != "none":
                return (col_id, order)
        return None

    def _update_sort_indicator(self) -> None:
        """Update sort indicator icon in header."""
        # Find sorted column
        sorted_info = self.get_sorted_column()
        if not sorted_info:
            # Hide sort indicator on all sections
            self._header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
            return

        column_id, order = sorted_info

        # Find index for this column
        for i, section in enumerate(self._sections):
            if section["id"] == column_id:
                qt_order = Qt.SortOrder.AscendingOrder if order == "asc" else Qt.SortOrder.DescendingOrder
                self._header.setSortIndicator(i, qt_order)
                break

    def get_sections(self) -> list[dict]:
        """Get list of all sections."""
        return self._sections.copy()

    def clear_sort(self) -> None:
        """Clear all sort indicators."""
        for col_id in self._sort_states:
            self._sort_states[col_id] = "none"
        self._header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def apply_list_style(
    widget: QListWidget,
    size: RowSize = "standard",
) -> None:
    """
    Apply v2 styling to a QListWidget.

    Args:
        widget: QListWidget to style
        size: Row size ("compact" or "standard")

    Example:
        list_widget = QListWidget()
        apply_list_style(list_widget, size="compact")
    """
    if size == "compact":
        widget.setStyleSheet(_get_list_compact_stylesheet())
    else:
        widget.setStyleSheet(_get_list_stylesheet())

    # Configure widget behavior
    widget.setAlternatingRowColors(False)
    widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
    widget.setSelectionBehavior(QListWidget.SelectionBehavior.SelectRows)


def apply_tree_style(widget: QTreeWidget) -> None:
    """
    Apply v2 styling to a QTreeWidget.

    Args:
        widget: QTreeWidget to style

    Example:
        tree_widget = QTreeWidget()
        apply_tree_style(tree_widget)
    """
    widget.setStyleSheet(_get_tree_stylesheet())

    # Configure widget behavior
    widget.setAlternatingRowColors(False)
    widget.setIndentation(TOKENS_V2.spacing.lg)
    widget.setHeaderHidden(True)


def apply_table_style(widget: QTableWidget) -> None:
    """
    Apply v2 styling to a QTableWidget.

    Args:
        widget: QTableWidget to style

    Example:
        table_widget = QTableWidget()
        apply_table_style(table_widget)
    """
    widget.setStyleSheet(_get_table_stylesheet())

    # Apply header style
    if widget.horizontalHeader():
        widget.horizontalHeader().setStyleSheet(_get_header_stylesheet())
    if widget.verticalHeader():
        widget.verticalHeader().setStyleSheet(_get_header_stylesheet())
        widget.verticalHeader().setVisible(False)

    # Configure widget behavior
    widget.setAlternatingRowColors(False)
    widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    widget.setShowGrid(False)


def apply_header_style(header: QHeaderView) -> None:
    """
    Apply v2 styling to a QHeaderView.

    Args:
        header: QHeaderView to style

    Example:
        header = table.horizontalHeader()
        apply_header_style(header)
    """
    header.setStyleSheet(_get_header_stylesheet())
    header.setStretchLastSection(True)
    header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)


def create_list_item(
    text: str,
    value: Any = None,
    *,
    icon: str | None = None,
    enabled: bool = True,
) -> ListItem:
    """
    Convenience function to create a ListItem.

    Args:
        text: Display text
        value: User data value
        icon: Optional icon name
        enabled: Whether enabled

    Returns:
        ListItem instance

    Example:
        item = create_list_item("File.txt", value="file1", icon="file")
    """
    return ListItem(text=text, value=value, icon=icon, enabled=enabled)


def create_tree_item(
    text: str,
    value: Any = None,
    *,
    icon: str | None = None,
    children: list[TreeItem] | None = None,
    expanded: bool = False,
) -> TreeItem:
    """
    Convenience function to create a TreeItem with optional children.

    Args:
        text: Display text
        value: User data value
        icon: Optional icon name
        children: Optional list of child TreeItems
        expanded: Whether initially expanded

    Returns:
        TreeItem instance

    Example:
        item = create_tree_item(
            "Folder",
            value="folder1",
            icon="folder",
            children=[
                create_tree_item("File.txt", value="file1", icon="file"),
            ],
            expanded=True,
        )
    """
    item = TreeItem(text=text, value=value, icon=icon, expanded=expanded)
    if children:
        for child in children:
            item.add_child(child)
    return item


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Type aliases
    "RowSize",
    "SortOrder",
    # Components
    "ListItem",
    "TreeItem",
    "TableHeader",
    # Helper functions
    "apply_list_style",
    "apply_tree_style",
    "apply_table_style",
    "apply_header_style",
    "create_list_item",
    "create_tree_item",
]
