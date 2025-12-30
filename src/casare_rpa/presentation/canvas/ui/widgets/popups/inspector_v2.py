"""
InspectorV2 - Property/Value Inspector Popup.

A table-like key-value inspector popover with:
- Search/filter functionality
- Type badges for values
- Optional inline editing (double-click)
- Collapsible sections
- THEME_V2 styling

Usage:
    inspector = InspectorV2(title="Properties", parent=None)
    inspector.add_property("Name", "Workflow1", type="string")
    inspector.add_property("Count", 42, type="number")
    inspector.add_property("Enabled", True, type="bool", editable=True)
    inspector.show_at_anchor(button)

Signals:
    value_changed: Emitted when a value is edited (key, new_value)
    property_selected: Emitted when a row is selected (key)
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.popups.popup_items import TypeBadge
from casare_rpa.presentation.canvas.ui.widgets.popups.popup_window_base import PopupWindowBase

if TYPE_CHECKING:
    from PySide6.QtGui import QMouseEvent


class PropertyRow(QFrame):
    """
    Single property row in InspectorV2.

    Displays key-value pair with type badge and optional inline editing.
    """

    clicked = Signal()
    double_clicked = Signal()

    def __init__(
        self,
        key: str,
        value: Any,
        type_name: str = "",
        editable: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize property row.

        Args:
            key: Property name/key
            value: Property value
            type_name: Type identifier for badge
            editable: Whether value can be edited inline
            parent: Parent widget
        """
        super().__init__(parent)
        self._key = key
        self._value = value
        self._type_name = type_name or self._infer_type(value)
        self._editable = editable
        self._is_hovered = False
        self._is_selected = False

        self._setup_ui()
        self._apply_style()

    def _infer_type(self, value: Any) -> str:
        """Infer type name from value."""
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int | float):
            return "number"
        if isinstance(value, str):
            return "string"
        if isinstance(value, list):
            return "list"
        if isinstance(value, dict):
            return "dict"
        return "any"

    def _setup_ui(self) -> None:
        """Setup the UI layout."""
        self.setFixedHeight(TOKENS_V2.sizes.row_height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            TOKENS_V2.spacing.sm,
            TOKENS_V2.spacing.xs,
            TOKENS_V2.spacing.sm,
            TOKENS_V2.spacing.xs,
        )
        layout.setSpacing(TOKENS_V2.spacing.md)

        # Key label
        self._key_label = QLabel(self._key)
        self._key_label.setStyleSheet(f"""
            color: {THEME_V2.text_secondary};
            font-size: {TOKENS_V2.typography.body}px;
            font-weight: {TOKENS_V2.typography.weight_medium};
        """)
        layout.addWidget(self._key_label)

        layout.addStretch()

        # Type badge
        badge_text = TypeBadge.badge_for_type(self._type_name)
        self._type_badge = TypeBadge(badge_text)
        badge_color = TypeBadge.color_for_type(self._type_name)
        self._type_badge.setStyleSheet(self._type_badge.styleSheet().replace(
            THEME_V2.text_secondary,
            badge_color
        ))
        layout.addWidget(self._type_badge)

        # Value label (or editor)
        self._value_widget: QLabel | QLineEdit

        if self._editable:
            self._value_editor = QLineEdit()
            self._value_editor.setText(self._format_value(self._value))
            self._value_editor.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {THEME_V2.bg_component};
                    color: {THEME_V2.text_primary};
                    border: 1px solid {THEME_V2.border};
                    border-radius: {TOKENS_V2.radius.xs}px;
                    padding: 0px {TOKENS_V2.spacing.xs}px;
                    font-size: {TOKENS_V2.typography.body}px;
                    min-width: 80px;
                }}
                QLineEdit:focus {{
                    border-color: {THEME_V2.border_focus};
                }}
            """)
            self._value_editor.editingFinished.connect(self._on_edit_finished)
            layout.addWidget(self._value_editor)
            self._value_widget = self._value_editor
        else:
            self._value_label = QLabel(self._format_value(self._value))
            self._value_label.setStyleSheet(f"""
                color: {THEME_V2.text_primary};
                font-size: {TOKENS_V2.typography.body}px;
                font-family: {TOKENS_V2.typography.mono};
            """)
            layout.addWidget(self._value_label)
            self._value_widget = self._value_label

    def _format_value(self, value: Any) -> str:
        """Format value for display."""
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, str):
            return value if len(value) <= 30 else f"{value[:27]}..."
        if isinstance(value, list):
            return f"[{len(value)} items]"
        if isinstance(value, dict):
            return f"{{{len(value)} keys}}"
        return str(value)

    def _apply_style(self) -> None:
        """Apply base styling."""
        self._update_style()

    def _update_style(self) -> None:
        """Update style based on state."""
        bg = "transparent"
        if self._is_selected:
            bg = THEME_V2.bg_selected
        elif self._is_hovered:
            bg = THEME_V2.bg_hover

        self.setStyleSheet(f"""
            PropertyRow {{
                background-color: {bg};
                border-radius: {TOKENS_V2.radius.xs}px;
            }}
        """)

    def _on_edit_finished(self) -> None:
        """Handle edit completion."""
        if self._editable and hasattr(self, "_value_editor"):
            new_text = self._value_editor.text()
            # Parse back to appropriate type
            new_value = self._parse_value(new_text)
            self._value = new_value
            # Parent InspectorV2 will handle signal

    def _parse_value(self, text: str) -> Any:
        """Parse text back to appropriate type."""
        if self._type_name == "bool":
            return text.lower() in ("true", "yes", "1", "on")
        if self._type_name == "number":
            try:
                if "." in text:
                    return float(text)
                return int(text)
            except ValueError:
                return text
        return text

    # =========================================================================
    # Public API
    # =========================================================================

    def get_key(self) -> str:
        """Return property key."""
        return self._key

    def get_value(self) -> Any:
        """Return property value."""
        return self._value

    def set_value(self, value: Any) -> None:
        """
        Update property value.

        Args:
            value: New value
        """
        self._value = value
        if hasattr(self, "_value_label"):
            self._value_label.setText(self._format_value(value))
        elif hasattr(self, "_value_editor") and not self._value_editor.hasFocus():
            self._value_editor.setText(self._format_value(value))

    def set_selected(self, selected: bool) -> None:
        """
        Set selection state.

        Args:
            selected: True to select, False to deselect
        """
        self._is_selected = selected
        self._update_style()

    def is_selected(self) -> bool:
        """Return selection state."""
        return self._is_selected

    # =========================================================================
    # Qt Event Handlers
    # =========================================================================

    @Slot()
    def enterEvent(self, event) -> None:
        """Handle mouse enter - hover state."""
        self._is_hovered = True
        self._update_style()
        super().enterEvent(event)

    @Slot()
    def leaveEvent(self, event) -> None:
        """Handle mouse leave - clear hover state."""
        self._is_hovered = False
        self._update_style()
        super().leaveEvent(event)

    @Slot()
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse click - emit signal."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)

    @Slot()
    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Handle double-click - enable inline edit if editable."""
        if event.button() == Qt.MouseButton.LeftButton and self._editable:
            self.double_clicked.emit()
            if hasattr(self, "_value_editor"):
                self._value_editor.setFocus()
                self._value_editor.selectAll()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)


class InspectorContent(QWidget):
    """
    Content widget for InspectorV2.

    Contains search bar and scrollable property list.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize inspector content."""
        super().__init__(parent)

        self._rows: list[PropertyRow] = []
        self._selected_row: PropertyRow | None = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.sm)

        # Search input
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Filter properties...")
        self._search_input.setFixedHeight(TOKENS_V2.sizes.input_sm)
        self._search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME_V2.bg_component};
                color: {THEME_V2.text_primary};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.xs}px;
                padding: 0px {TOKENS_V2.spacing.xs}px;
                font-size: {TOKENS_V2.typography.body_sm}px;
            }}
            QLineEdit:focus {{
                border-color: {THEME_V2.border_focus};
            }}
        """)
        self._search_input.textChanged.connect(self._on_search_changed)
        layout.addWidget(self._search_input)

        # Scrollable property list
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: {TOKENS_V2.sizes.scrollbar_width}px;
            }}
            QScrollBar::handle:vertical {{
                background: {THEME_V2.scrollbar_handle};
                border-radius: {TOKENS_V2.radius.xs}px;
                min-height: {TOKENS_V2.sizes.scrollbar_min_height}px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)

        self._property_container = QWidget()
        self._property_layout = QVBoxLayout(self._property_container)
        self._property_layout.setContentsMargins(0, 0, TOKENS_V2.spacing.xs, 0)
        self._property_layout.setSpacing(TOKENS_V2.spacing.xs)
        self._property_layout.addStretch()

        self._scroll_area.setWidget(self._property_container)
        layout.addWidget(self._scroll_area)

    @Slot()
    def _on_search_changed(self, text: str) -> None:
        """
        Filter rows by search text.

        Args:
            text: Search query (filters key and value)
        """
        search_lower = text.lower().strip()

        for row in self._rows:
            if not search_lower:
                row.setVisible(True)
            else:
                key = row.get_key().lower()
                value = str(row.get_value()).lower()
                row.setVisible(search_lower in key or search_lower in value)

    # =========================================================================
    # Public API
    # =========================================================================

    def add_property(
        self,
        key: str,
        value: Any,
        type_name: str = "",
        editable: bool = False,
    ) -> PropertyRow:
        """
        Add a property row.

        Args:
            key: Property name/key
            value: Property value
            type_name: Type identifier for badge (auto-inferred if empty)
            editable: Whether value can be edited inline

        Returns:
            The created PropertyRow instance
        """
        row = PropertyRow(key, value, type_name, editable, self._property_container)
        row.clicked.connect(partial(self._on_row_clicked, row))
        row.double_clicked.connect(partial(self._on_row_double_clicked, row))

        # Insert before the stretch
        self._property_layout.insertWidget(self._property_layout.count() - 1, row)
        self._rows.append(row)

        return row

    def clear_properties(self) -> None:
        """Remove all property rows."""
        for row in self._rows:
            self._property_layout.removeWidget(row)
            row.deleteLater()
        self._rows.clear()
        self._selected_row = None

    def get_property(self, key: str) -> PropertyRow | None:
        """
        Get a property row by key.

        Args:
            key: Property key to find

        Returns:
            PropertyRow if found, None otherwise
        """
        for row in self._rows:
            if row.get_key() == key:
                return row
        return None

    def get_value(self, key: str) -> Any | None:
        """
        Get a property value by key.

        Args:
            key: Property key to find

        Returns:
            Property value if found, None otherwise
        """
        row = self.get_property(key)
        return row.get_value() if row else None

    def set_value(self, key: str, value: Any) -> None:
        """
        Update a property value by key.

        Args:
            key: Property key to update
            value: New value
        """
        row = self.get_property(key)
        if row:
            row.set_value(value)

    def set_filter(self, text: str) -> None:
        """
        Set the search filter text.

        Args:
            text: Filter query
        """
        self._search_input.setText(text)

    def get_filter(self) -> str:
        """Return current filter text."""
        return self._search_input.text()

    @Slot()
    def _on_row_clicked(self, row: PropertyRow) -> None:
        """Handle row click - selection management."""
        # Deselect previous
        if self._selected_row and self._selected_row != row:
            self._selected_row.set_selected(False)

        # Select new
        row.set_selected(True)
        self._selected_row = row

    @Slot()
    def _on_row_double_clicked(self, row: PropertyRow) -> None:
        """Handle row double-click - trigger inline edit."""
        pass  # Handled by PropertyRow itself


class InspectorV2(PopupWindowBase):
    """
    Property/Value Inspector Popup V2.

    A table-like inspector popover with search, type badges, and inline editing.

    Features:
    - Search/filter in header
    - Key-value rows with type badges
    - Optional inline editing (double-click)
    - Collapsible via pin button
    - THEME_V2 styling

    Signals:
        value_changed: Emitted when a value is edited (key, new_value)
        property_selected: Emitted when a row is selected (key)

    Example:
        inspector = InspectorV2(title="Properties", parent=None)
        inspector.add_property("Name", "Workflow1", type="string")
        inspector.add_property("Count", 42, type="number")
        inspector.add_property("Enabled", True, type="bool", editable=True)
        inspector.show_at_anchor(button)
    """

    value_changed = Signal(str, object)
    property_selected = Signal(str)

    # Default dimensions
    DEFAULT_WIDTH = 320
    DEFAULT_HEIGHT = 400
    MIN_WIDTH = 200
    MIN_HEIGHT = 150

    def __init__(
        self,
        title: str = "Inspector",
        parent: QWidget | None = None,
        resizable: bool = True,
        pin_button: bool = True,
    ) -> None:
        """
        Initialize inspector popup.

        Args:
            title: Header title text
            parent: Parent widget
            resizable: Enable corner resize
            pin_button: Show pin button in header
        """
        super().__init__(
            title=title,
            parent=parent,
            resizable=resizable,
            pin_button=pin_button,
            close_button=True,
            min_width=self.MIN_WIDTH,
            min_height=self.MIN_HEIGHT,
        )

        # Initialize content
        self._content = InspectorContent()
        self.set_content_widget(self._content)

    # =========================================================================
    # Public API
    # =========================================================================

    def add_property(
        self,
        key: str,
        value: Any,
        type_name: str = "",
        editable: bool = False,
    ) -> None:
        """
        Add a property to display.

        Args:
            key: Property name/key
            value: Property value
            type_name: Type identifier for badge (auto-inferred if empty)
            editable: Whether value can be edited inline
        """
        row = self._content.add_property(key, value, type_name, editable)

        # Connect to value change signal for tracking
        if editable:
            # Note: Value changes are tracked via the row's internal edit handler
            # Connect to parent's signal via a closure
            original_handler = row._on_edit_finished

            def wrapped_handler() -> None:
                original_handler()
                new_value = row.get_value()
                self.value_changed.emit(key, new_value)

            # Replace the edit finished handler
            if hasattr(row, "_value_editor"):
                try:
                    row._value_editor.editingFinished.disconnect()
                except RuntimeError:
                    pass
                row._value_editor.editingFinished.connect(wrapped_handler)

    def clear_properties(self) -> None:
        """Remove all properties."""
        self._content.clear_properties()

    def get_property(self, key: str) -> Any | None:
        """
        Get a property value by key.

        Args:
            key: Property key to find

        Returns:
            Property value if found, None otherwise
        """
        return self._content.get_value(key)

    def set_property(self, key: str, value: Any) -> None:
        """
        Update a property value by key.

        Args:
            key: Property key to update
            value: New value
        """
        self._content.set_value(key, value)

    def set_filter(self, text: str) -> None:
        """
        Set the search filter text.

        Args:
            text: Filter query for properties
        """
        self._content.set_filter(text)

    def get_filter(self) -> str:
        """Return current filter text."""
        return self._content.get_filter()

    def properties(self) -> dict[str, Any]:
        """
        Get all properties as a dictionary.

        Returns:
            Dictionary mapping keys to values
        """
        result: dict[str, Any] = {}
        for row in self._content._rows:
            if row.isVisible():
                result[row.get_key()] = row.get_value()
        return result

    def set_properties(self, props: dict[str, Any]) -> None:
        """
        Replace all properties with a dictionary.

        Args:
            props: Dictionary of key-value pairs
        """
        self.clear_properties()
        for key, value in props.items():
            self.add_property(key, value)


__all__ = ["InspectorContent", "InspectorV2", "PropertyRow"]
