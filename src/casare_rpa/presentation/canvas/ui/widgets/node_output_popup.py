"""
Node Output Inspector Popup for CasareRPA.

Shows output port values from node execution in a beautiful popup window.
Redesigned to match n8n's simple Schema view style.

Features:
- Middle-click on node to open
- Schema view (default): Simple list with type badges and drag support
- Table view: Key/Value/Type columns
- JSON view: Syntax highlighted JSON
- Drag-and-drop: Drag port names to insert variable references
- Search/filter outputs
- Pin to keep open
- Auto-refresh during execution

Design follows n8n output inspector UX.
"""

import json
from functools import partial
from typing import Any

# ZERO-MOTION POLICY (Epic 8.1):
# Popups appear instantly with no fade or shadow animations.
# Crisp 1px THEME border provides clear visual separation.
# This improves perceived responsiveness and reduces visual fatigue.
from loguru import logger
from PySide6.QtCore import (
    QEvent,
    QMimeData,
    QObject,
    QPoint,
    QSize,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QDrag,
    QFont,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QGraphicsItem,
    QGraphicsView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME
from casare_rpa.presentation.canvas.ui.widgets.json_syntax_highlighter import (
    JsonSyntaxHighlighter,
    get_json_highlighter_stylesheet,
)

# ============================================================================
# COLOR CONSTANTS (Using THEME)
# ============================================================================


class PopupColors:
    """Color constants for the output popup using THEME."""

    # Background colors
    BACKGROUND = QColor(THEME.bg_surface)
    HEADER_BG = QColor(THEME.bg_component)
    BORDER = QColor(THEME.border)

    # Text colors
    TEXT = QColor(THEME.text_primary)
    TEXT_SECONDARY = QColor(THEME.text_secondary)

    # Accent colors
    ACCENT = QColor(THEME.primary)
    ACCENT_HOVER = QColor(THEME.primary_hover)

    # Status colors
    SUCCESS = QColor(THEME.success)
    ERROR = QColor(THEME.error)
    ERROR_BG = QColor(THEME.error_bg)

    # Table colors
    TABLE_ALT_ROW = QColor(THEME.bg_component)
    TABLE_HOVER = QColor(THEME.bg_hover)
    TABLE_SELECTED = QColor(THEME.bg_selected)

    # Type badge colors (using THEME type colors for consistency)
    TYPE_STRING = QColor(THEME.type_string)
    TYPE_NUMBER = QColor(THEME.type_integer)
    TYPE_BOOLEAN = QColor(THEME.type_boolean)
    TYPE_ARRAY = QColor(THEME.type_list)
    TYPE_OBJECT = QColor(THEME.type_dict)
    TYPE_NULL = QColor(THEME.type_any)


# ============================================================================
# TYPE UTILITIES
# ============================================================================


def get_type_badge(value: Any) -> str:
    """Get a short type badge for a value (n8n style)."""
    if isinstance(value, dict):
        return "{}"
    elif isinstance(value, list):
        return "[]"
    elif isinstance(value, str):
        return "AB"
    elif isinstance(value, bool):
        return "Y/N"
    elif isinstance(value, int | float):
        return "#"
    elif value is None:
        return "null"
    else:
        return "?"


def get_type_color(value: Any) -> QColor:
    """Get the badge background color for a value type."""
    if isinstance(value, dict):
        return PopupColors.TYPE_OBJECT
    elif isinstance(value, list):
        return PopupColors.TYPE_ARRAY
    elif isinstance(value, str):
        return PopupColors.TYPE_STRING
    elif isinstance(value, bool):
        return PopupColors.TYPE_BOOLEAN
    elif isinstance(value, int | float):
        return PopupColors.TYPE_NUMBER
    elif value is None:
        return PopupColors.TYPE_NULL
    else:
        return PopupColors.TEXT_SECONDARY


def get_value_preview(value: Any, max_length: int = 40) -> str:
    """Get a truncated preview of a value."""
    if isinstance(value, dict):
        count = len(value)
        return f"({count} key{'s' if count != 1 else ''})"
    elif isinstance(value, list):
        count = len(value)
        return f"({count} item{'s' if count != 1 else ''})"
    elif isinstance(value, str):
        if len(value) > max_length:
            return f'"{value[:max_length]}..."'
        return f'"{value}"'
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif value is None:
        return "null"
    else:
        s = str(value)
        if len(s) > max_length:
            return s[:max_length] + "..."
        return s


def get_type_name(value: Any) -> str:
    """Get a friendly type name for table view."""
    if isinstance(value, dict):
        return f"object ({len(value)} keys)"
    elif isinstance(value, list):
        return f"array ({len(value)} items)"
    elif isinstance(value, str):
        return "string"
    elif isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "float"
    elif value is None:
        return "null"
    else:
        return type(value).__name__


# ============================================================================
# SCHEMA ITEM WIDGET
# ============================================================================


class SchemaItemWidget(QWidget):
    """
    Custom widget for a single row in the Schema view.

    Compact n8n-style layout:
    ┌────────────────────────────────────────────────┐
    │ 6px │ [BADGE] │ 6px │ port_name │ 8px │ value │ flex │
    │     │  22x14  │     │  (bold)   │     │ (gray)│      │
    └────────────────────────────────────────────────┘
    Height: 26px

    - Badge is smaller and more subtle
    - Name and value are close together on the left
    - Stretch is at the end (not between name/value)

    Supports drag-and-drop to insert variable references.
    """

    MIME_TYPE = "application/x-casare-variable"

    # Class-level flag to track if any SchemaItemWidget is currently dragging
    # This prevents the popup from closing during drag operations
    _active_drag_count = 0

    @classmethod
    def is_dragging(cls) -> bool:
        """Check if any SchemaItemWidget is currently being dragged."""
        return cls._active_drag_count > 0

    def __init__(
        self,
        node_id: str,
        node_name: str,
        port_name: str,
        value: Any,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize schema item widget.

        Args:
            node_id: ID of the node
            node_name: Display name of the node
            port_name: Name of the output port
            value: The port value
            parent: Parent widget
        """
        super().__init__(parent)

        self._node_id = node_id
        self._node_name = node_name
        self._port_name = port_name
        self._value = value
        self._drag_start_pos: QPoint | None = None

        self.setFixedHeight(26)  # Compact row height
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setMouseTracking(True)

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Setup the widget UI with compact n8n-style layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 6, 0)  # Tighter margins
        layout.setSpacing(6)  # Reduced spacing

        # Type badge - smaller and more subtle
        self._badge = QLabel(get_type_badge(self._value))
        self._badge.setFixedSize(22, 14)  # Smaller badge
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_color = get_type_color(self._value)
        self._badge.setStyleSheet(f"""
            QLabel {{
                background-color: {badge_color.name()};
                color: #e0e0e0;
                border-radius: 2px;
                font-size: 9px;
                font-weight: 600;
                font-family: "Consolas", "Courier New", monospace;
            }}
        """)
        layout.addWidget(self._badge)

        # Port name (bold white)
        self._name_label = QLabel(self._port_name)
        self._name_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        self._name_label.setStyleSheet(f"color: {PopupColors.TEXT.name()};")
        layout.addWidget(self._name_label)

        # Value preview (gray) - close to name, no max-width constraint
        preview = get_value_preview(self._value, max_length=50)
        self._value_label = QLabel(preview)
        self._value_label.setFont(QFont("Consolas", 9))
        self._value_label.setStyleSheet(f"color: {PopupColors.TEXT_SECONDARY.name()};")
        layout.addWidget(self._value_label)

        # Stretch at the END - keeps name/value together on the left
        layout.addStretch()

    def _apply_styles(self) -> None:
        """Apply hover styles."""
        self.setStyleSheet(f"""
            SchemaItemWidget {{
                background-color: transparent;
                border-radius: 4px;
            }}
            SchemaItemWidget:hover {{
                background-color: {PopupColors.TABLE_HOVER.name()};
            }}
        """)

    def get_variable_reference(self) -> str:
        """Get the variable reference string for this port (uses node_id for resolution)."""
        return f"{{{{{self._node_id}.{self._port_name}}}}}"

    def get_drag_data(self) -> dict:
        """Get the drag data as a dictionary."""
        return {
            "node_id": self._node_id,
            "node_name": self._node_name,
            "port_name": self._port_name,
            "variable": self.get_variable_reference(),
        }

    def mousePressEvent(self, event) -> None:
        """Handle mouse press for drag start."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for drag."""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            super().mouseMoveEvent(event)
            return

        if self._drag_start_pos is None:
            super().mouseMoveEvent(event)
            return

        # Check if moved enough to start drag
        distance = (event.pos() - self._drag_start_pos).manhattanLength()
        if distance < QApplication.startDragDistance():
            super().mouseMoveEvent(event)
            return

        # Start drag
        self.setCursor(Qt.CursorShape.ClosedHandCursor)

        drag = QDrag(self)
        mime_data = QMimeData()

        # Set drag data as JSON
        drag_data = json.dumps(self.get_drag_data())
        mime_data.setData(self.MIME_TYPE, drag_data.encode("utf-8"))

        # Also set as plain text for non-aware targets
        mime_data.setText(self.get_variable_reference())

        drag.setMimeData(mime_data)

        logger.debug(f"Starting drag for variable: {self.get_variable_reference()}")

        # Track active drag to prevent popup from closing
        SchemaItemWidget._active_drag_count += 1

        try:
            # Execute drag
            result = drag.exec(Qt.DropAction.CopyAction)
            logger.debug(f"Drag ended with result: {result}")
        finally:
            # Always decrement drag count
            SchemaItemWidget._active_drag_count = max(0, SchemaItemWidget._active_drag_count - 1)

        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._drag_start_pos = None

    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release."""
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)


# ============================================================================
# OUTPUT SCHEMA VIEW (NEW - n8n style)
# ============================================================================


class OutputSchemaView(QListWidget):
    """
    Schema view showing output ports as a simple list.

    Each row shows:
    - Type badge (AB, #, Y/N, [], {}, null)
    - Port name (bold)
    - Value preview (gray)

    Supports drag-and-drop to insert variable references.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the schema view."""
        super().__init__(parent)

        self._node_id: str = ""
        self._node_name: str = ""

        # Configure list appearance
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setSpacing(1)

        # Enable drag
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)

        self._apply_styles()

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet(f"""
            QListWidget {{
                background-color: {PopupColors.BACKGROUND.name()};
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                background-color: transparent;
                border: none;
                padding: 0px;
            }}
            QListWidget::item:selected {{
                background-color: {PopupColors.TABLE_SELECTED.name()};
            }}
            QListWidget::item:hover {{
                background-color: {PopupColors.TABLE_HOVER.name()};
            }}
            QScrollBar:vertical {{
                background: {PopupColors.BACKGROUND.name()};
                width: 10px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: #424242;
                min-height: 20px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #505050;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

    def set_node_info(self, node_id: str, node_name: str) -> None:
        """
        Set the node info for drag data.

        Args:
            node_id: Node ID
            node_name: Node display name
        """
        self._node_id = node_id
        self._node_name = node_name

    def set_data(self, data: dict[str, Any]) -> None:
        """
        Populate the list with output port data.

        Only shows top-level output ports (not flattened nested data).

        Args:
            data: Dictionary of output port name -> value
        """
        self.clear()

        if not data:
            return

        for port_name, value in data.items():
            # Create list item
            item = QListWidgetItem(self)
            item.setSizeHint(QSize(0, 26))  # Compact row height

            # Create custom widget
            widget = SchemaItemWidget(
                node_id=self._node_id,
                node_name=self._node_name,
                port_name=port_name,
                value=value,
            )

            self.addItem(item)
            self.setItemWidget(item, widget)

    def filter_items(self, search_text: str) -> None:
        """
        Filter items by search text.

        Args:
            search_text: Text to filter by (case-insensitive)
        """
        search_lower = search_text.lower()
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if widget and hasattr(widget, "_port_name"):
                visible = search_lower in widget._port_name.lower()
                item.setHidden(not visible)


# ============================================================================
# OUTPUT TABLE VIEW (Simplified - no index column)
# ============================================================================


class OutputTableView(QTableWidget):
    """
    Table view for output data.

    Displays output as a sortable table with columns:
    - Key: Property name
    - Value: Property value (truncated)
    - Type: Value type
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the table view."""
        super().__init__(parent)

        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Key", "Value", "Type"])

        # Configure table appearance
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSortingEnabled(True)
        self.verticalHeader().setVisible(False)

        # Configure column widths
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.resizeSection(0, 140)

        self._apply_styles()

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {PopupColors.BACKGROUND.name()};
                alternate-background-color: {PopupColors.TABLE_ALT_ROW.name()};
                border: none;
                gridline-color: {PopupColors.BORDER.name()};
                color: {PopupColors.TEXT.name()};
                font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 4px 8px;
                border: none;
            }}
            QTableWidget::item:selected {{
                background-color: {PopupColors.TABLE_SELECTED.name()};
                color: white;
            }}
            QTableWidget::item:hover {{
                background-color: {PopupColors.TABLE_HOVER.name()};
            }}
            QHeaderView::section {{
                background-color: {PopupColors.HEADER_BG.name()};
                color: {PopupColors.TEXT.name()};
                border: none;
                border-bottom: 1px solid {PopupColors.BORDER.name()};
                border-right: 1px solid {PopupColors.BORDER.name()};
                padding: 6px 8px;
                font-weight: bold;
                font-size: 11px;
            }}
            QScrollBar:vertical {{
                background: {PopupColors.BACKGROUND.name()};
                width: 10px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: #424242;
                min-height: 20px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #505050;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

    def set_data(self, data: dict[str, Any]) -> None:
        """
        Populate the table with output data.

        Args:
            data: Dictionary of output port name -> value
        """
        self.setRowCount(0)
        self.setSortingEnabled(False)

        if not data:
            return

        # Flatten the data for table display
        rows = self._flatten_data(data)

        for key, value in rows:
            row = self.rowCount()
            self.insertRow(row)

            # Key column
            key_item = QTableWidgetItem(str(key))
            self.setItem(row, 0, key_item)

            # Value column (truncated)
            value_str = self._format_value(value)
            value_item = QTableWidgetItem(value_str)
            value_item.setToolTip(self._format_value(value, max_length=1000))
            self.setItem(row, 1, value_item)

            # Type column with color
            type_name = get_type_name(value)
            type_item = QTableWidgetItem(type_name)
            type_item.setForeground(get_type_color(value))
            self.setItem(row, 2, type_item)

        self.setSortingEnabled(True)

    def _flatten_data(
        self,
        data: dict[str, Any],
        prefix: str = "",
        max_depth: int = 3,
    ) -> list[tuple]:
        """
        Flatten nested data for table display.

        Args:
            data: Data to flatten
            prefix: Key prefix for nested items
            max_depth: Maximum nesting depth

        Returns:
            List of (key, value) tuples
        """
        rows = []

        if max_depth <= 0:
            rows.append((prefix or "(root)", data))
            return rows

        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict | list) and max_depth > 1:
                    rows.extend(self._flatten_data(value, full_key, max_depth - 1))
                else:
                    rows.append((full_key, value))
        elif isinstance(data, list):
            for idx, value in enumerate(data[:100]):  # Limit to 100 items
                full_key = f"{prefix}[{idx}]" if prefix else f"[{idx}]"
                if isinstance(value, dict | list) and max_depth > 1:
                    rows.extend(self._flatten_data(value, full_key, max_depth - 1))
                else:
                    rows.append((full_key, value))
            if len(data) > 100:
                rows.append((f"{prefix}[...]", f"({len(data) - 100} more items)"))
        else:
            rows.append((prefix or "(value)", data))

        return rows

    def _format_value(self, value: Any, max_length: int = 100) -> str:
        """Format a value for display."""
        if isinstance(value, str):
            if len(value) > max_length:
                return value[:max_length] + "..."
            return value
        elif isinstance(value, dict | list):
            try:
                s = json.dumps(value, ensure_ascii=False)
                if len(s) > max_length:
                    return s[:max_length] + "..."
                return s
            except Exception:
                return str(value)[:max_length]
        else:
            s = str(value)
            if len(s) > max_length:
                return s[:max_length] + "..."
            return s

    def filter_items(self, search_text: str) -> None:
        """
        Filter rows by search text.

        Args:
            search_text: Text to filter by (case-insensitive)
        """
        search_lower = search_text.lower()
        for row in range(self.rowCount()):
            match = False
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item and search_lower in item.text().lower():
                    match = True
                    break
            self.setRowHidden(row, not match)


# ============================================================================
# OUTPUT JSON VIEW
# ============================================================================


class OutputJsonView(QWidget):
    """
    JSON view with syntax highlighting.

    Displays output as formatted JSON with VSCode Dark+ colors.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the JSON view."""
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create text editor
        self._editor = QPlainTextEdit()
        self._editor.setReadOnly(True)
        self._editor.setFont(QFont("Consolas", 11))
        self._editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._editor.setStyleSheet(get_json_highlighter_stylesheet())

        # Create syntax highlighter
        self._highlighter = JsonSyntaxHighlighter(self._editor.document())

        layout.addWidget(self._editor)

    def set_data(self, data: dict[str, Any]) -> None:
        """
        Display data as formatted JSON.

        Args:
            data: Dictionary to display
        """
        try:
            json_str = json.dumps(data, indent=2, ensure_ascii=False, default=str)
            self._editor.setPlainText(json_str)
        except Exception as e:
            self._editor.setPlainText(f"Error formatting JSON: {e}\n\n{data}")

    def get_text(self) -> str:
        """Get the current JSON text."""
        return self._editor.toPlainText()


# ============================================================================
# VARIABLE ITEM WIDGET (for Variables tab)
# ============================================================================


class VariableItemWidget(QFrame):
    """
    Widget for displaying a single variable in the Variables view.

    Supports drag-and-drop to insert variable references into input fields.
    Uses the same MIME type as SchemaItemWidget for compatibility.
    """

    MIME_TYPE = "application/x-casare-variable"
    _active_drag_count = 0

    @classmethod
    def is_dragging(cls) -> bool:
        """Check if any VariableItemWidget is currently being dragged."""
        return cls._active_drag_count > 0

    def __init__(
        self,
        var_name: str,
        var_type: str,
        value: Any,
        source: str = "workflow",
        insertion_text: str = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize variable item widget.

        Args:
            var_name: Variable name
            var_type: Type string (String, Integer, etc.)
            value: Current value (for preview)
            source: Where the variable comes from
            insertion_text: Text to insert when dragged (defaults to {{var_name}})
            parent: Parent widget
        """
        super().__init__(parent)
        self._var_name = var_name
        self._var_type = var_type
        self._value = value
        self._source = source
        self._insertion_text = insertion_text or f"{{{{{var_name}}}}}"
        self._drag_start_pos: QPoint | None = None

        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Setup the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 6, 0)  # Tighter margins like SchemaItemWidget
        layout.setSpacing(6)  # Reduced spacing

        # Type badge - smaller and more subtle
        badge_text = self._get_type_badge()
        badge = QLabel(badge_text)
        badge.setFixedSize(22, 14)  # Smaller badge like SchemaItemWidget
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {self._get_type_color()};
                color: #e0e0e0;
                border-radius: 2px;
                font-size: 9px;
                font-weight: 600;
                font-family: "Consolas", "Courier New", monospace;
            }}
        """)
        layout.addWidget(badge)

        # Variable name (bright white, bold) - stands out
        name_label = QLabel(self._var_name)
        name_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #ffffff;")
        layout.addWidget(name_label)

        # Value preview (muted gray) - distinct from name
        preview = self._get_value_preview()
        if preview:
            preview_label = QLabel(preview)
            preview_label.setFont(QFont("Consolas", 9))
            preview_label.setStyleSheet("color: #888888;")
            layout.addWidget(preview_label)

        # Stretch at the END - keeps name/value together on the left
        layout.addStretch()

    def _apply_styles(self) -> None:
        """Apply hover styles."""
        self.setStyleSheet(f"""
            VariableItemWidget {{
                background-color: transparent;
                border-radius: 4px;
            }}
            VariableItemWidget:hover {{
                background-color: {PopupColors.TABLE_HOVER.name()};
            }}
        """)

    def _get_type_badge(self) -> str:
        """Get the badge text for this type."""
        badges = {
            "String": "AB",
            "Integer": "#",
            "Float": "#.#",
            "Boolean": "Y/N",
            "List": "[]",
            "Dict": "{}",
            "DataTable": "📊",
            "Any": "?",
        }
        return badges.get(self._var_type, "?")

    def _get_type_color(self) -> str:
        """Get the badge color for this type."""
        colors = {
            "String": PopupColors.TYPE_STRING.name(),
            "Integer": PopupColors.TYPE_NUMBER.name(),
            "Float": PopupColors.TYPE_NUMBER.name(),
            "Boolean": PopupColors.TYPE_BOOLEAN.name(),
            "List": PopupColors.TYPE_ARRAY.name(),
            "Dict": PopupColors.TYPE_OBJECT.name(),
            "DataTable": PopupColors.TYPE_OBJECT.name(),
            "Any": PopupColors.TYPE_NULL.name(),
        }
        return colors.get(self._var_type, PopupColors.TYPE_NULL.name())

    def _get_value_preview(self) -> str:
        """Get a truncated preview of the value."""
        if self._value is None:
            return ""
        preview = str(self._value)
        if len(preview) > 30:
            preview = preview[:27] + "..."
        return preview

    def get_insertion_text(self) -> str:
        """Get the text to insert when dragged."""
        return self._insertion_text

    def get_drag_data(self) -> dict:
        """Get the drag data as a dictionary."""
        return {
            "variable": self._insertion_text,
            "var_name": self._var_name,
            "var_type": self._var_type,
            "source": self._source,
        }

    def mousePressEvent(self, event) -> None:
        """Handle mouse press for drag start."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for drag."""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            super().mouseMoveEvent(event)
            return

        if self._drag_start_pos is None:
            super().mouseMoveEvent(event)
            return

        # Check if moved enough to start drag
        distance = (event.pos() - self._drag_start_pos).manhattanLength()
        if distance < QApplication.startDragDistance():
            super().mouseMoveEvent(event)
            return

        # Start drag
        self.setCursor(Qt.CursorShape.ClosedHandCursor)

        drag = QDrag(self)
        mime_data = QMimeData()

        # Set drag data as JSON
        drag_data = json.dumps(self.get_drag_data())
        mime_data.setData(self.MIME_TYPE, drag_data.encode("utf-8"))

        # Also set as plain text for non-aware targets
        mime_data.setText(self._insertion_text)

        drag.setMimeData(mime_data)

        logger.debug(f"Starting drag for variable: {self._insertion_text}")

        # Track active drag
        VariableItemWidget._active_drag_count += 1

        try:
            result = drag.exec(Qt.DropAction.CopyAction)
            logger.debug(f"Drag ended with result: {result}")
        finally:
            VariableItemWidget._active_drag_count = max(
                0, VariableItemWidget._active_drag_count - 1
            )

        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._drag_start_pos = None

    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release."""
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)


# ============================================================================
# VARIABLES VIEW
# ============================================================================


class VariablesView(QWidget):
    """
    View showing all available workflow variables.

    Displays variables from:
    - Workflow variables (from Variables panel)
    - System variables ($currentDate, etc.)

    Each row shows:
    - Type badge
    - Variable name
    - Value preview
    - Drag support for insertion
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the variables view."""
        super().__init__(parent)
        self._main_window = None
        self._items: list[VariableItemWidget] = []

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Setup the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create scrollable list container
        from PySide6.QtWidgets import QScrollArea

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        # Content widget
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(8, 8, 8, 8)
        self._content_layout.setSpacing(2)
        self._content_layout.addStretch()

        scroll.setWidget(self._content)
        layout.addWidget(scroll)

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {PopupColors.BACKGROUND.name()};
            }}
            QScrollArea {{
                background-color: transparent;
            }}
        """)

    def set_main_window(self, main_window) -> None:
        """
        Set the main window reference for variable access.

        Args:
            main_window: MainWindow instance
        """
        self._main_window = main_window

    def refresh(self) -> None:
        """Refresh the variable list from providers."""
        # Clear existing items
        for item in self._items:
            item.deleteLater()
        self._items.clear()

        # Remove stretch and re-add later
        while self._content_layout.count():
            child = self._content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Get variables from provider
        try:
            from casare_rpa.presentation.canvas.ui.widgets.variable_picker import (
                VariableInfo,
                VariableProvider,
            )

            provider = VariableProvider.get_instance()

            # Make sure provider has main_window for panel access
            if self._main_window:
                provider.set_main_window(self._main_window)

            # Get graph from main window
            graph = None
            if self._main_window:
                graph = self._main_window.get_graph()

            variables = provider.get_all_variables(None, graph)

            # Also scan for SetVariable nodes in the graph
            setvariable_vars = []
            if graph:
                try:
                    for node in graph.all_nodes():
                        # Check if this is a SetVariable node
                        node_type = node.type_ if hasattr(node, "type_") else ""
                        if "SetVariable" in node_type or "SetVariableNode" in node_type:
                            # Get variable name from node properties
                            var_name = None
                            var_value = None
                            var_type = "String"

                            if hasattr(node, "get_property"):
                                var_name = node.get_property("variable_name")
                                var_value = node.get_property("default_value")
                                var_type = node.get_property("variable_type") or "String"

                            if not var_name and hasattr(node, "_casare_node"):
                                casare_node = node._casare_node
                                if hasattr(casare_node, "variable_name"):
                                    var_name = casare_node.variable_name
                                if hasattr(casare_node, "default_value"):
                                    var_value = casare_node.default_value
                                if hasattr(casare_node, "variable_type"):
                                    var_type = casare_node.variable_type

                            if var_name:
                                # Get node_id for insertion path
                                node_id = None
                                if hasattr(node, "get_property"):
                                    node_id = node.get_property("node_id")
                                if not node_id and hasattr(node, "id"):
                                    node_id = node.id()

                                insertion_path = f"{node_id}.value" if node_id else var_name
                                var_info = VariableInfo(
                                    name=var_name,
                                    var_type=var_type,
                                    source="setvariable",
                                    value=var_value,
                                    path=var_name,
                                    insertion_path=insertion_path,
                                )
                                setvariable_vars.append(var_info)
                except Exception as e:
                    logger.debug(f"Error scanning SetVariable nodes: {e}")

            # Combine all variables
            all_vars = list(variables) + setvariable_vars

            if not all_vars:
                # Show empty state
                empty_label = QLabel(
                    "No variables defined\n\nCreate variables in the Variables panel\nor use SetVariable nodes"
                )
                empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_label.setStyleSheet(f"""
                    color: {PopupColors.TEXT_SECONDARY.name()};
                    font-size: 12px;
                    padding: 40px;
                """)
                self._content_layout.addWidget(empty_label)
            else:
                # Group by source
                workflow_vars = [v for v in all_vars if v.source == "workflow"]
                setvariable_list = [v for v in all_vars if v.source == "setvariable"]
                node_vars = [v for v in all_vars if v.source.startswith("node:")]
                system_vars = [v for v in all_vars if v.source == "system"]

                # Add workflow variables section
                if workflow_vars:
                    self._add_section_header("WORKFLOW VARIABLES")
                    for var in workflow_vars:
                        self._add_variable_item(var)

                # Add SetVariable nodes section
                if setvariable_list:
                    self._add_section_header("SET VARIABLES")
                    for var in setvariable_list:
                        self._add_variable_item(var)

                # Add node output variables section
                if node_vars:
                    self._add_section_header("NODE OUTPUTS")
                    for var in node_vars:
                        self._add_variable_item(var)

                # Add system variables section
                if system_vars:
                    self._add_section_header("SYSTEM")
                    for var in system_vars:
                        self._add_variable_item(var)

        except Exception as e:
            logger.error(f"Error refreshing variables: {e}")
            error_label = QLabel(f"Error loading variables:\n{e}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet(f"color: {PopupColors.ERROR.name()};")
            self._content_layout.addWidget(error_label)

        self._content_layout.addStretch()

    def _add_section_header(self, text: str) -> None:
        """Add a section header label."""
        header = QLabel(text)
        header.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        header.setStyleSheet(f"""
            color: {PopupColors.TEXT_SECONDARY.name()};
            padding: 6px 6px 2px 6px;
        """)
        self._content_layout.addWidget(header)

    def _add_variable_item(self, var_info) -> None:
        """Add a variable item widget."""
        item = VariableItemWidget(
            var_name=var_info.display_name,
            var_type=var_info.var_type,
            value=var_info.value,
            source=var_info.source,
            insertion_text=var_info.insertion_text,
        )
        self._content_layout.addWidget(item)
        self._items.append(item)

    def filter_items(self, search_text: str) -> None:
        """
        Filter items by search text.

        Args:
            search_text: Text to filter by (case-insensitive)
        """
        search_lower = search_text.lower()
        for item in self._items:
            match = search_lower in item._var_name.lower()
            item.setVisible(match)


# ============================================================================
# HEADER BUTTON (Icon-only)
# ============================================================================


class HeaderButton(QPushButton):
    """Compact icon button for header."""

    def __init__(self, text: str, tooltip: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setFixedSize(24, 24)
        self.setToolTip(tooltip)
        # Use Segoe UI Symbol font for reliable icon rendering
        self.setFont(QFont("Segoe UI Symbol", 12))
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                color: {PopupColors.TEXT_SECONDARY.name()};
            }}
            QPushButton:hover {{
                background-color: {PopupColors.TABLE_HOVER.name()};
                color: {PopupColors.TEXT.name()};
            }}
            QPushButton:pressed {{
                background-color: {PopupColors.TABLE_SELECTED.name()};
            }}
            QPushButton:checked {{
                color: {PopupColors.ACCENT.name()};
            }}
        """)


# ============================================================================
# DRAGGABLE HEADER
# ============================================================================


class DraggableHeader(QFrame):
    """Header that supports dragging to move the parent window."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._drag_pos: QPoint | None = None
        self._parent_window: QWidget | None = None
        self.setCursor(Qt.CursorShape.SizeAllCursor)

    def set_parent_window(self, window: QWidget) -> None:
        """Set the window to be moved when dragging."""
        self._parent_window = window

    def mousePressEvent(self, event) -> None:
        """Start drag on left click."""
        if event.button() == Qt.MouseButton.LeftButton and self._parent_window:
            self._drag_pos = event.globalPos() - self._parent_window.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Move window while dragging."""
        if self._drag_pos is not None and self._parent_window:
            self._parent_window.move(event.globalPos() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """End drag."""
        self._drag_pos = None
        super().mouseReleaseEvent(event)


# ============================================================================
# VIEW MODE TAB BUTTON
# ============================================================================


class ViewModeButton(QPushButton):
    """Compact tab-style button for view mode selection."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setFixedHeight(22)
        self.setFixedWidth(44)  # Fixed width so all buttons are same size
        self._update_style()

    def _update_style(self) -> None:
        """Update style based on checked state."""
        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {PopupColors.ACCENT.name()};
                    border: none;
                    border-radius: 3px;
                    padding: 2px 8px;
                    color: white;
                    font-size: 10px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {PopupColors.ACCENT_HOVER.name()};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: 1px solid {PopupColors.BORDER.name()};
                    border-radius: 3px;
                    padding: 2px 8px;
                    color: {PopupColors.TEXT_SECONDARY.name()};
                    font-size: 10px;
                }}
                QPushButton:hover {{
                    background-color: {PopupColors.TABLE_HOVER.name()};
                    color: {PopupColors.TEXT.name()};
                }}
            """)

    def setChecked(self, checked: bool) -> None:
        """Override to update style when checked state changes."""
        super().setChecked(checked)
        self._update_style()


# ============================================================================
# NODE OUTPUT POPUP
# ============================================================================


class NodeOutputPopup(QFrame):
    """
    Popup window for viewing node output port values.

    Features:
    - Three view modes: Schema (default), Table, JSON
    - Schema view with drag-and-drop variable insertion
    - Search/filter functionality
    - Pin to keep open
    - Resizable from edges/corners
    - Smart positioning near node
    - Fade-in animation

    Signals:
        closed: Emitted when popup is closed
        pin_changed: Emitted when pin state changes (bool: pinned)
    """

    closed = Signal()
    pin_changed = Signal(bool)

    # Default size (wider to fit all tab buttons)
    DEFAULT_WIDTH = 420
    DEFAULT_HEIGHT = 300
    MIN_WIDTH = 380
    MIN_HEIGHT = 200

    # Resize edge margin
    RESIZE_MARGIN = 8

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the popup."""
        super().__init__(parent)

        self._node_id: str | None = None
        self._node_name: str = ""
        self._data: dict[str, Any] = {}
        self._is_pinned: bool = False
        self._is_loading: bool = False
        self._error_message: str | None = None
        self._has_error: bool = False
        self._search_visible: bool = False

        # Resize state
        self._resize_edge: str | None = None  # 'left', 'right', 'top', 'bottom', or corners
        self._resize_start_pos: QPoint | None = None
        self._resize_start_geometry = None

        # Position tracking - to follow node on pan/zoom
        self._tracked_node_item: QGraphicsItem | None = None
        self._tracked_view: QGraphicsView | None = None
        self._position_timer: QTimer | None = None

        # Enable mouse tracking for cursor changes
        self.setMouseTracking(True)

        # Window setup - Tool window without WindowStaysOnTopHint
        # so popup goes behind other apps when switching windows
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(
            Qt.WidgetAttribute.WA_ShowWithoutActivating, False
        )  # Changed to allow key events
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)

        # ZERO-MOTION: No shadow effect - crisp THEME border instead
        # Setup UI
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        # Container for rounded corners
        container = QFrame()
        container.setObjectName("popupContainer")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Header
        header = self._create_header()
        container_layout.addWidget(header)

        # Search bar (hidden by default)
        self._search_bar = self._create_search_bar()
        self._search_bar.setVisible(False)
        container_layout.addWidget(self._search_bar)

        # Stacked widget for views
        self._stack = QStackedWidget()

        # Create views
        self._schema_view = OutputSchemaView()
        self._table_view = OutputTableView()
        self._json_view = OutputJsonView()
        self._variables_view = VariablesView()

        self._stack.addWidget(self._schema_view)  # Index 0 - Schema (default)
        self._stack.addWidget(self._table_view)  # Index 1 - Table
        self._stack.addWidget(self._json_view)  # Index 2 - JSON
        self._stack.addWidget(self._variables_view)  # Index 3 - Variables

        container_layout.addWidget(self._stack, 1)

        # Empty state widget
        self._empty_widget = self._create_empty_state()
        self._stack.addWidget(self._empty_widget)  # Index 4

        # Error state widget
        self._error_widget = self._create_error_state()
        self._stack.addWidget(self._error_widget)  # Index 5

        # Loading state widget
        self._loading_widget = self._create_loading_state()
        self._stack.addWidget(self._loading_widget)  # Index 6

        main_layout.addWidget(container)

        # Install event filters on child widgets to catch Escape key
        # This is needed because child widgets consume key events before parent
        # Also install on viewports since scroll-based widgets use viewport for event handling
        widgets_to_filter = [
            self._search_input,
            self._schema_view,
            self._table_view,
            self._json_view,
            self._variables_view,
        ]
        for widget in widgets_to_filter:
            widget.installEventFilter(self)
            if hasattr(widget, "viewport"):
                widget.viewport().installEventFilter(self)

    def _create_header(self) -> DraggableHeader:
        """
        Create compact draggable header with n8n style.

        Layout: OUTPUT [status] [count]    [Schema][Table][JSON]  [pin][close]
        """
        header = DraggableHeader()
        header.set_parent_window(self)
        header.setObjectName("header")
        header.setFixedHeight(38)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 0, 6, 0)
        layout.setSpacing(4)

        # "OUTPUT" title
        title = QLabel("OUTPUT")
        title.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {PopupColors.TEXT.name()};")
        layout.addWidget(title)

        # Status icon (success/error)
        self._status_label = QLabel()
        self._status_label.setFixedSize(16, 16)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(self._status_label)

        # Item count label
        self._count_label = QLabel()
        self._count_label.setStyleSheet(
            f"color: {PopupColors.TEXT_SECONDARY.name()}; font-size: 10px;"
        )
        layout.addWidget(self._count_label)

        layout.addStretch()

        # View mode buttons (compact)
        self._schema_btn = ViewModeButton("Schema")
        self._schema_btn.setChecked(True)
        self._schema_btn.clicked.connect(partial(self._switch_view, 0))
        layout.addWidget(self._schema_btn)

        self._table_btn = ViewModeButton("Table")
        self._table_btn.clicked.connect(partial(self._switch_view, 1))
        layout.addWidget(self._table_btn)

        self._json_btn = ViewModeButton("JSON")
        self._json_btn.clicked.connect(partial(self._switch_view, 2))
        layout.addWidget(self._json_btn)

        self._variables_btn = ViewModeButton("Vars")
        self._variables_btn.clicked.connect(partial(self._switch_view, 3))
        layout.addWidget(self._variables_btn)

        # Small gap
        layout.addSpacing(8)

        # Pin button (pushpin symbol)
        self._pin_btn = HeaderButton("⊙", "Pin (keep open)")
        self._pin_btn.setCheckable(True)
        self._pin_btn.clicked.connect(self._on_pin_clicked)
        layout.addWidget(self._pin_btn)

        # Close button (multiplication sign renders reliably)
        self._close_btn = HeaderButton("×", "Close")
        self._close_btn.clicked.connect(self.close)
        layout.addWidget(self._close_btn)

        # Hidden search button (accessible via Ctrl+F)
        self._search_btn = QPushButton()
        self._search_btn.setCheckable(True)
        self._search_btn.setVisible(False)
        self._search_btn.clicked.connect(self._toggle_search)

        return header

    def _create_search_bar(self) -> QFrame:
        """Create the search bar."""
        bar = QFrame()
        bar.setFixedHeight(36)
        bar.setStyleSheet(f"background-color: {PopupColors.HEADER_BG.name()};")

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 4, 12, 4)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search ports...")
        self._search_input.textChanged.connect(self._on_search_changed)
        self._search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {PopupColors.BACKGROUND.name()};
                border: 1px solid {PopupColors.BORDER.name()};
                border-radius: 4px;
                padding: 4px 8px;
                color: {PopupColors.TEXT.name()};
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border-color: {PopupColors.ACCENT.name()};
            }}
        """)
        layout.addWidget(self._search_input)

        return bar

    def _create_empty_state(self) -> QWidget:
        """Create the empty state widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel("No output data\n\nRun workflow to see outputs")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"""
            color: {PopupColors.TEXT_SECONDARY.name()};
            font-size: 14px;
        """)
        layout.addWidget(label)

        return widget

    def _create_error_state(self) -> QWidget:
        """Create the error state widget."""
        widget = QWidget()
        widget.setStyleSheet(f"background-color: {PopupColors.ERROR_BG.name()};")
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._error_label = QLabel("Error")
        self._error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_label.setWordWrap(True)
        self._error_label.setStyleSheet(f"""
            color: {PopupColors.ERROR.name()};
            font-size: 13px;
            padding: 20px;
        """)
        layout.addWidget(self._error_label)

        return widget

    def _create_loading_state(self) -> QWidget:
        """Create the loading state widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel("Executing...")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"""
            color: {PopupColors.ACCENT.name()};
            font-size: 14px;
        """)
        layout.addWidget(label)

        return widget

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet(f"""
            QFrame#popupContainer {{
                background-color: {PopupColors.BACKGROUND.name()};
                border: 1px solid {PopupColors.BORDER.name()};
                border-radius: 8px;
            }}
            QFrame#header {{
                background-color: {PopupColors.HEADER_BG.name()};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom: 1px solid {PopupColors.BORDER.name()};
            }}
        """)

    def _update_status_icon(self) -> None:
        """Update status icon based on error state."""
        if self._has_error:
            self._status_label.setText("\u2717")  # Unicode X mark
            self._status_label.setStyleSheet(f"color: {PopupColors.ERROR.name()};")
        elif self._data:
            self._status_label.setText("\u2713")  # Unicode check mark
            self._status_label.setStyleSheet(f"color: {PopupColors.SUCCESS.name()};")
        else:
            self._status_label.setText("")

    def set_node(self, node_id: str, node_name: str) -> None:
        """
        Set the node being inspected.

        Args:
            node_id: Node ID
            node_name: Node display name
        """
        self._node_id = node_id
        self._node_name = node_name
        self._schema_view.set_node_info(node_id, node_name)

    def set_data(self, data: dict[str, Any]) -> None:
        """
        Set the output data to display.

        Args:
            data: Dictionary of output port name -> value
        """
        # Filter out EXEC flow control ports (exec_in, exec_out, etc.)
        filtered_data = {
            k: v
            for k, v in (data or {}).items()
            if not k.startswith("exec_") and k not in ("exec_in", "exec_out")
        }
        self._data = filtered_data
        self._error_message = None
        self._is_loading = False
        self._has_error = False

        if not self._data:
            self._stack.setCurrentWidget(self._empty_widget)
            self._count_label.setText("")
        else:
            # Update all views
            self._schema_view.set_data(self._data)
            self._table_view.set_data(self._data)
            self._json_view.set_data(self._data)

            # Show current view (Schema by default)
            self._switch_view(self._get_current_view_index())

            # Update count
            count = len(self._data)
            self._count_label.setText(f"{count} port{'s' if count != 1 else ''}")

        self._update_status_icon()

    def _get_current_view_index(self) -> int:
        """Get the current view index based on button states."""
        if self._schema_btn.isChecked():
            return 0
        elif self._table_btn.isChecked():
            return 1
        elif self._json_btn.isChecked():
            return 2
        elif self._variables_btn.isChecked():
            return 3
        return 0  # Default to Schema

    def _switch_view(self, index: int) -> None:
        """
        Switch to a specific view.

        Args:
            index: View index (0=Schema, 1=Table, 2=JSON, 3=Variables)
        """
        # Update button states
        self._schema_btn.setChecked(index == 0)
        self._table_btn.setChecked(index == 1)
        self._json_btn.setChecked(index == 2)
        self._variables_btn.setChecked(index == 3)

        # Show Variables view (always available, doesn't depend on node data)
        if index == 3:
            self._variables_view.refresh()
            self._stack.setCurrentWidget(self._variables_view)
            return

        # Show the view if we have data
        if self._data:
            if index == 0:
                self._stack.setCurrentWidget(self._schema_view)
            elif index == 1:
                self._stack.setCurrentWidget(self._table_view)
            elif index == 2:
                self._stack.setCurrentWidget(self._json_view)

    def _toggle_search(self) -> None:
        """Toggle search bar visibility."""
        self._search_visible = not self._search_visible
        self._search_bar.setVisible(self._search_visible)
        self._search_btn.setChecked(self._search_visible)

        if self._search_visible:
            self._search_input.setFocus()
            self._search_input.selectAll()
        else:
            self._search_input.clear()

    def _on_search_changed(self, text: str) -> None:
        """Handle search input change."""
        self._schema_view.filter_items(text)
        self._table_view.filter_items(text)
        self._variables_view.filter_items(text)

    def set_loading(self, loading: bool) -> None:
        """
        Set the loading state.

        Args:
            loading: Whether node is currently executing
        """
        self._is_loading = loading
        if loading:
            self._stack.setCurrentWidget(self._loading_widget)
            self._status_label.setText("")

    def set_error(self, error: str) -> None:
        """
        Show an error message.

        Args:
            error: Error message to display
        """
        self._error_message = error
        self._has_error = True
        self._error_label.setText(f"Error:\n\n{error}")
        self._stack.setCurrentWidget(self._error_widget)
        self._update_status_icon()

    def show_at_position(self, pos: QPoint) -> None:
        """
        Show the popup at the specified position.

        Adjusts position to stay within screen bounds.

        Args:
            pos: Global position to show at
        """
        # Get screen geometry
        screen = QApplication.primaryScreen().availableGeometry()

        # Adjust position to stay on screen
        x = pos.x()
        y = pos.y()

        if x + self.width() > screen.right():
            x = screen.right() - self.width() - 10

        if y + self.height() > screen.bottom():
            y = screen.bottom() - self.height() - 10

        if x < screen.left():
            x = screen.left() + 10

        if y < screen.top():
            y = screen.top() + 10

        self.move(x, y)
        self.show()
        # ZERO-MOTION: Instant show, no fade animation
        # Activate window to ensure keyboard events (Escape) work
        self.activateWindow()
        self.raise_()
        self.setFocus()

    def start_tracking_node(self, node_item: QGraphicsItem, view: QGraphicsView) -> None:
        """
        Start tracking a node item to follow it on pan/zoom.

        Args:
            node_item: The node's graphics item to track
            view: The graphics view containing the node
        """
        self._tracked_node_item = node_item
        self._tracked_view = view

        # Create and start position update timer
        if self._position_timer is None:
            self._position_timer = QTimer(self)
            self._position_timer.timeout.connect(self._update_tracked_position)

        # Update at 60fps for smooth tracking
        self._position_timer.start(16)

    def stop_tracking_node(self) -> None:
        """Stop tracking the node position."""
        if self._position_timer is not None:
            self._position_timer.stop()
        self._tracked_node_item = None
        self._tracked_view = None

    def _update_tracked_position(self) -> None:
        """Update popup position based on tracked node's current screen position."""
        if self._tracked_node_item is None or self._tracked_view is None or not self.isVisible():
            return

        try:
            # Get node's bottom-left in scene coordinates
            node_rect = self._tracked_node_item.sceneBoundingRect()
            scene_pos = node_rect.bottomLeft()

            # Map to view coordinates, then to global screen coordinates
            view_pos = self._tracked_view.mapFromScene(scene_pos)
            global_pos = self._tracked_view.mapToGlobal(view_pos)

            # Add small vertical offset
            x = global_pos.x()
            y = global_pos.y() + 5

            # Apply screen bounds checking
            screen = QApplication.primaryScreen().availableGeometry()

            if x + self.width() > screen.right():
                x = screen.right() - self.width() - 10
            if y + self.height() > screen.bottom():
                y = screen.bottom() - self.height() - 10
            if x < screen.left():
                x = screen.left() + 10
            if y < screen.top():
                y = screen.top() + 10

            self.move(x, y)
        except RuntimeError:
            # Node or view was deleted
            self.stop_tracking_node()

    def _on_pin_clicked(self) -> None:
        """Handle pin button click."""
        self._is_pinned = self._pin_btn.isChecked()
        self.pin_changed.emit(self._is_pinned)

        # Store current position before changing window flags
        current_pos = self.pos()

        if self._is_pinned:
            # Convert to regular window when pinned (no StaysOnTop)
            self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        else:
            # Back to Tool window (closing handled by eventFilter)
            self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        # Restore position and show
        self.move(current_pos)
        self.show()

    @property
    def node_id(self) -> str | None:
        """Get the node ID being inspected."""
        return self._node_id

    @property
    def is_pinned(self) -> bool:
        """Check if popup is pinned."""
        return self._is_pinned

    def closeEvent(self, event) -> None:
        """Handle close event."""
        # Clean up event filters from child widgets
        widgets_to_cleanup = [
            self._search_input,
            self._schema_view,
            self._table_view,
            self._json_view,
            self._variables_view,
        ]
        for widget in widgets_to_cleanup:
            try:
                widget.removeEventFilter(self)
                if hasattr(widget, "viewport"):
                    widget.viewport().removeEventFilter(self)
            except RuntimeError:
                pass  # Widget already deleted

        # Stop position tracking
        self.stop_tracking_node()
        # Reset resize state on close
        self._reset_resize_state()
        self.closed.emit()
        super().closeEvent(event)

    def hideEvent(self, event) -> None:
        """Handle hide event - reset state."""
        self._reset_resize_state()
        super().hideEvent(event)

    def focusOutEvent(self, event) -> None:
        """Handle focus loss - reset resize state only.

        Note: Closing is handled by NodeGraphWidget's eventFilter to avoid
        closing on MMB clicks (which should pan, not close popup).
        """
        self._reset_resize_state()
        super().focusOutEvent(event)

    def _reset_resize_state(self) -> None:
        """Reset all resize-related state."""
        self._resize_edge = None
        self._resize_start_pos = None
        self._resize_start_geometry = None
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def keyPressEvent(self, event) -> None:
        """Handle key press events."""
        # Escape closes popup
        if event.key() == Qt.Key.Key_Escape:
            if self._search_visible:
                self._toggle_search()
            else:
                self.close()
        # Ctrl+F toggles search
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_F:
                self._toggle_search()
            # Ctrl+1/2/3 switches views
            elif event.key() == Qt.Key.Key_1:
                self._switch_view(0)
            elif event.key() == Qt.Key.Key_2:
                self._switch_view(1)
            elif event.key() == Qt.Key.Key_3:
                self._switch_view(2)
        else:
            super().keyPressEvent(event)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        Event filter to catch Escape key from child widgets.

        Child widgets (search input, list/table views) consume key events
        before they reach the popup's keyPressEvent, so we need this filter.

        Args:
            obj: The object receiving the event
            event: The event

        Returns:
            False to let event propagate, True to consume it
        """
        # Check both KeyPress and ShortcutOverride (text widgets consume Escape)
        if event.type() in (QEvent.Type.KeyPress, QEvent.Type.ShortcutOverride):
            key_event = event
            if hasattr(key_event, "key") and key_event.key() == Qt.Key.Key_Escape:
                if self._search_visible:
                    self._toggle_search()
                else:
                    self.close()
                return True  # Consume the event

        return False  # Don't consume other events

    # =========================================================================
    # RESIZE HANDLING
    # =========================================================================

    def _get_resize_edge(self, pos: QPoint) -> str | None:
        """Determine which corner the mouse is near for resizing (corners only)."""
        m = self.RESIZE_MARGIN
        rect = self.rect()
        x, y = pos.x(), pos.y()
        w, h = rect.width(), rect.height()

        left = x < m
        right = x > w - m
        top = y < m
        bottom = y > h - m

        # Only allow corner resizing
        if top and left:
            return "top-left"
        elif top and right:
            return "top-right"
        elif bottom and left:
            return "bottom-left"
        elif bottom and right:
            return "bottom-right"
        return None

    def _update_cursor_for_edge(self, edge: str | None) -> None:
        """Update cursor based on resize corner."""
        if edge in ("top-left", "bottom-right"):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edge in ("top-right", "bottom-left"):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event) -> None:
        """Start resize on edge click."""
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._get_resize_edge(event.pos())
            if edge:
                self._resize_edge = edge
                self._resize_start_pos = event.globalPos()
                self._resize_start_geometry = self.geometry()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Handle resize drag or update cursor."""
        if self._resize_edge and self._resize_start_pos:
            # Resizing in progress
            delta = event.globalPos() - self._resize_start_pos
            geo = self._resize_start_geometry
            new_geo = geo.__class__(geo)  # Copy

            edge = self._resize_edge
            if "left" in edge:
                new_geo.setLeft(geo.left() + delta.x())
            if "right" in edge:
                new_geo.setRight(geo.right() + delta.x())
            if "top" in edge:
                new_geo.setTop(geo.top() + delta.y())
            if "bottom" in edge:
                new_geo.setBottom(geo.bottom() + delta.y())

            # Enforce minimum size
            if new_geo.width() >= self.MIN_WIDTH and new_geo.height() >= self.MIN_HEIGHT:
                try:
                    # Clamp geometry to primary screen available area to avoid
                    # QWindowsWindow::setGeometry warnings when requested geometry
                    # is outside monitor limits or constrained by min/max.
                    screen = QApplication.primaryScreen()
                    if screen is not None:
                        avail = screen.availableGeometry()
                        # Constrain edges
                        if new_geo.left() < avail.left():
                            new_geo.moveLeft(avail.left())
                        if new_geo.top() < avail.top():
                            new_geo.moveTop(avail.top())
                        if new_geo.right() > avail.right():
                            new_geo.setRight(avail.right())
                        if new_geo.bottom() > avail.bottom():
                            new_geo.setBottom(avail.bottom())
                except Exception:
                    # Fall back to original behaviour if anything unexpected
                    pass

                self.setGeometry(new_geo)
            event.accept()
        else:
            # Update cursor based on position
            edge = self._get_resize_edge(event.pos())
            self._update_cursor_for_edge(edge)
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """End resize."""
        # Always reset resize state on mouse release
        self._reset_resize_state()
        super().mouseReleaseEvent(event)
