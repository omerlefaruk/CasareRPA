"""
Shared popup item widgets for v2 popup variants.

Provides reusable components:
- MenuItem: Single menu item with icon, text, shortcut, checkmark
- MenuSeparator: Horizontal divider line
- TypeBadge: Type indicator badge for autocomplete/inspector

All items use THEME_V2 tokens for consistent styling.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from casare_rpa.presentation.canvas.theme_system import THEME_V2, TOKENS_V2

if TYPE_CHECKING:
    from PySide6.QtGui import QMouseEvent


class MenuItemType(Enum):
    """Types of menu items."""
    ACTION = "action"
    SEPARATOR = "separator"
    CHECKABLE = "checkable"
    SUBMENU = "submenu"


@dataclass(frozen=True)
class MenuItemSpec:
    """
    Specification for a menu item.

    Immutable spec that can be passed to create menu items.
    """
    id: str
    text: str
    callback: Callable[[], Any] | None = None
    shortcut: str | None = None
    icon: str | None = None
    enabled: bool = True
    checkable: bool = False
    checked: bool = False


class TypeBadge(QLabel):
    """
    Type indicator badge for autocomplete/inspector.

    Shows type info like:
    - AB for boolean
    - # for number
    - {} for dict
    - [] for list
    - Y/N for yes/no
    - Custom type names
    """

    # Color mapping for types
    TYPE_COLORS = {
        "bool": THEME_V2.primary,
        "number": THEME_V2.success,
        "string": THEME_V2.warning,
        "list": THEME_V2.info,
        "dict": THEME_V2.info,
        "any": THEME_V2.text_secondary,
        "null": THEME_V2.text_muted,
        "yes": THEME_V2.success,
        "no": THEME_V2.error,
    }

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        """
        Initialize type badge.

        Args:
            text: Badge text (e.g., "AB", "#", "{}")
            parent: Parent widget
        """
        super().__init__(text, parent)
        self._apply_style()

    def _apply_style(self) -> None:
        """Apply v2 dark theme styling."""
        self.setStyleSheet(f"""
            TypeBadge {{
                background-color: {THEME_V2.bg_component};
                color: {THEME_V2.text_secondary};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.xs}px;
                padding: 0px {TOKENS_V2.spacing.xs}px;
                font-size: {TOKENS_V2.typography.caption}px;
                font-weight: {TOKENS_V2.typography.weight_medium};
                font-family: {TOKENS_V2.typography.mono};
            }}
        """)

    @staticmethod
    def for_value(value: Any) -> str:
        """
        Get badge text for a Python value.

        Args:
            value: Any Python value

        Returns:
            Badge text representation
        """
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "AB"
        if isinstance(value, int | float):
            return "#"
        if isinstance(value, str):
            return '"'
        if isinstance(value, list):
            return "[]"
        if isinstance(value, dict):
            return "{}"
        return "•"

    @staticmethod
    def color_for_type(type_name: str) -> str:
        """
        Get badge color for a type name.

        Args:
            type_name: Type identifier

        Returns:
            Hex color code
        """
        return TypeBadge.TYPE_COLORS.get(type_name.lower(), THEME_V2.text_secondary)

    @staticmethod
    def badge_for_type(type_name: str) -> str:
        """
        Get badge symbol for a type name.

        Args:
            type_name: Type identifier

        Returns:
            Badge symbol text
        """
        type_lower = type_name.lower()
        symbols = {
            "bool": "AB",
            "int": "#",
            "float": "#",
            "number": "#",
            "str": '"',
            "string": '"',
            "list": "[]",
            "array": "[]",
            "dict": "{}",
            "object": "{}",
            "none": "null",
            "null": "null",
        }
        return symbols.get(type_lower, type_name[:2].upper())


class MenuSeparator(QFrame):
    """
    Horizontal separator line for menus.

    Simple divider with consistent styling.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize separator."""
        super().__init__(parent)
        self.setFixedHeight(1)
        self._apply_style()

    def _apply_style(self) -> None:
        """Apply v2 dark theme styling."""
        self.setStyleSheet(f"""
            MenuSeparator {{
                background-color: {THEME_V2.border};
                border: none;
            }}
        """)


class MenuItem(QWidget):
    """
    Single menu item for ContextMenu and Dropdown.

    Features:
    - Icon (optional)
    - Text label
    - Shortcut display (optional)
    - Checkmark for checkable items
    - Hover state
    - Disabled state
    - Keyboard navigation support

    Signals:
        clicked: Emitted when item is clicked
        hovered: Emitted when item is hovered
    """

    clicked = Signal()
    hovered = Signal()

    def __init__(
        self,
        text: str,
        callback: Callable[[], Any] | None = None,
        shortcut: str | None = None,
        icon: str | None = None,
        enabled: bool = True,
        checkable: bool = False,
        checked: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize menu item.

        Args:
            text: Display text
            callback: Function to call when clicked
            shortcut: Keyboard shortcut to display (e.g., "Ctrl+S")
            icon: Optional icon/text prefix
            enabled: Whether item is enabled
            checkable: Whether item can be checked
            checked: Initial check state
            parent: Parent widget
        """
        super().__init__(parent)

        self._text = text
        self._callback = callback
        self._shortcut = shortcut
        self._icon = icon
        self._checkable = checkable
        self._checked = checked
        self._enabled = enabled
        self._is_hovered = False

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Setup the UI layout."""
        self.setFixedHeight(TOKENS_V2.sizes.menu_item_height)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            TOKENS_V2.spacing.sm,
            0,
            TOKENS_V2.spacing.sm,
            0,
        )
        layout.setSpacing(TOKENS_V2.spacing.sm)

        # Icon / checkmark area
        self._icon_label = QLabel()
        self._icon_label.setFixedWidth(TOKENS_V2.spacing.lg)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if self._checkable and self._checked:
            self._icon_label.setText("✓")
        elif self._icon:
            self._icon_label.setText(self._icon)

        layout.addWidget(self._icon_label)

        # Text label
        self._text_label = QLabel(self._text)
        layout.addWidget(self._text_label)

        layout.addStretch()

        # Shortcut
        self._shortcut_label = QLabel(self._shortcut or "")
        if self._shortcut:
            self._shortcut_label.setStyleSheet(f"""
                color: {THEME_V2.text_muted};
                font-size: {TOKENS_V2.typography.caption}px;
            """)
        layout.addWidget(self._shortcut_label)

    def _apply_style(self) -> None:
        """Apply base styling."""
        self._update_style()

    def _update_style(self) -> None:
        """Update style based on state."""
        bg = THEME_V2.bg_selected if self._is_hovered and self._enabled else "transparent"
        text_color = THEME_V2.text_primary if self._enabled else THEME_V2.text_disabled

        self.setStyleSheet(f"""
            MenuItem {{
                background-color: {bg};
                border: none;
                border-radius: {TOKENS_V2.radius.xs}px;
            }}
            QLabel {{
                color: {text_color};
                font-size: {TOKENS_V2.typography.body}px;
            }}
        """)

    # =========================================================================
    # Public API
    # =========================================================================

    def set_checked(self, checked: bool) -> None:
        """
        Set check state.

        Args:
            checked: True to check, False to uncheck
        """
        if not self._checkable:
            return
        self._checked = checked
        self._icon_label.setText("✓" if checked else "")

    def is_checked(self) -> bool:
        """Return check state."""
        return self._checked

    def toggle(self) -> None:
        """Toggle check state."""
        if self._checkable:
            self.set_checked(not self._checked)

    def set_enabled(self, enabled: bool) -> None:
        """
        Set enabled state.

        Args:
            enabled: True to enable, False to disable
        """
        self._enabled = enabled
        self._update_style()

    def is_enabled(self) -> bool:
        """Return enabled state."""
        return self._enabled

    def trigger(self) -> None:
        """Trigger the item (call callback and emit signal)."""
        if not self._enabled:
            return

        if self._checkable:
            self.toggle()

        if self._callback:
            self._callback()

        self.clicked.emit()

    # =========================================================================
    # Qt Event Handlers
    # =========================================================================

    @Slot()
    def enterEvent(self, event) -> None:
        """Handle mouse enter - hover state."""
        self._is_hovered = True
        self._update_style()
        self.hovered.emit()
        super().enterEvent(event)

    @Slot()
    def leaveEvent(self, event) -> None:
        """Handle mouse leave - clear hover state."""
        self._is_hovered = False
        self._update_style()
        super().leaveEvent(event)

    @Slot()
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse click - trigger item."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.trigger()
            event.accept()
        else:
            super().mousePressEvent(event)


class DropdownItem(MenuItem):
    """
    Dropdown menu item - simplified MenuItem.

    Designed for single-selection dropdowns with:
    - Icon + text
    - Selection state (radio-style)
    - No shortcuts
    """

    def __init__(
        self,
        text: str,
        data: Any = None,
        icon: str | None = None,
        selected: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize dropdown item.

        Args:
            text: Display text
            data: Associated data value
            icon: Optional icon
            selected: Whether this item is selected
            parent: Parent widget
        """
        self._data = data
        self._selected = selected

        super().__init__(
            text=text,
            callback=None,
            shortcut=None,
            icon=icon,
            enabled=True,
            checkable=False,
            checked=False,
            parent=parent,
        )

        # Override icon with selection indicator
        self._update_selection_style()

    def _update_selection_style(self) -> None:
        """Update style for selection state."""
        if self._selected:
            self._icon_label.setText("●")
            self._icon_label.setStyleSheet(f"color: {THEME_V2.primary};")

    def set_selected(self, selected: bool) -> None:
        """
        Set selection state.

        Args:
            selected: True to select, False to deselect
        """
        self._selected = selected
        self._update_selection_style()

    def is_selected(self) -> bool:
        """Return selection state."""
        return self._selected

    def get_data(self) -> Any:
        """Return associated data."""
        return self._data if self._data is not None else self._text


__all__ = [
    "DropdownItem",
    "MenuItem",
    "MenuItemSpec",
    "MenuItemType",
    "MenuSeparator",
    "TypeBadge",
]
