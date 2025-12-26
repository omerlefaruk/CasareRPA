"""
VS Code/Cursor-style Context Menu for CasareRPA.

A context menu that replicates the visual style and layout of the VS Code/Cursor
'Selection' menu in Dark Mode.

Design Specifications (uses Theme.colors()):
- Background: menu_bg ({THEME.bg_dark})
- Border: menu_border ({THEME.border}) with drop shadow
- Corner Radius: 6px
- Row Height: 28-30px per item
- Padding: 10-12px horizontal
- Text: menu_text ({THEME.text_muted}), menu_text_shortcut (#858585)
- Hover: menu_hover (#094771), text brightens to white
- Dividers: menu_separator ({THEME.border}) with 4px margin

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.context_menu import (
        ContextMenu,
        ContextMenuItem,
        ContextMenuSeparator,
    )

    # Create menu
    menu = ContextMenu(parent=self)

    # Add items
    menu.add_item("Copy", callback=lambda: print("Copy"), shortcut="Ctrl+C")
    menu.add_item("Paste", callback=lambda: print("Paste"), shortcut="Ctrl+V")
    menu.add_separator()
    menu.add_item("Delete", callback=lambda: print("Delete"), shortcut="Del")

    # Show at position
    menu.show_at_position(global_pos)
"""

from typing import Any, Callable

from loguru import logger
from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.managers.popup_manager import PopupManager
from casare_rpa.presentation.canvas.ui.theme import Theme
from casare_rpa.presentation.canvas.theme_system import TOKENS
from casare_rpa.presentation.canvas.theme_system.helpers import set_fixed_size, set_min_size, set_max_size, set_margins, set_spacing, set_min_width, set_max_width, set_fixed_width, set_fixed_height
from casare_rpa.presentation.canvas.theme import THEME

# =============================================================================
# MENU ITEM WIDGET
# =============================================================================


class ContextMenuItem(QWidget):
    """
    A single item in the context menu.

    Layout:
    ┌─────────────────────────────────────────────────────────┐
    │ Action Name              (flex)        Keyboard Shortcut │
    │ (left-aligned)                         (right-aligned)  │
    └─────────────────────────────────────────────────────────┘
    height: {TOKENS.sizes.input_height_md}px
    padding: {TOKENS.spacing.md}px horizontal (0 in widget, handled by parent)

    The shortcut text is displayed in a dimmed color (#858585) to
    create visual hierarchy, while the action name is brighter ({THEME.text_muted}).
    """

    clicked = Signal()

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
        Initialize a context menu item.

        Args:
            text: Display text for the action
            callback: Function to call when clicked
            shortcut: Keyboard shortcut text to display (e.g., "Ctrl+C")
            icon: Optional icon/text to show before the action name
            enabled: Whether the item is enabled/clickable
            checkable: Whether the item shows a checkmark when clicked
            checked: Initial checked state (for checkable items)
            parent: Parent widget
        """
        super().__init__(parent)

        self._text = text
        self._callback = callback
        self._shortcut_text = shortcut or ""
        self._enabled = enabled
        self._checkable = checkable
        self._checked = checked

        set_fixed_height(self, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.ArrowCursor)

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Setup the widget UI with action name and shortcut."""
        layout = QHBoxLayout(self)
        # No margins - padding is handled by parent menu container
        set_margins(layout, (12, 0, 12, 0))
        set_spacing(layout, 0)

        # Optional checkmark for checkable items
        if self._checkable:
            self._check_label = QLabel("✓" if self._checked else "")
            self.set_fixed_width(_check_label, 16)
            self._check_label.setAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            layout.addWidget(self._check_label)
        else:
            # Spacer for alignment when some items are checkable
            layout.addSpacing(16)

        # Optional icon
        if self._shortcut_text:
            # Add spacing between icon and text
            layout.addSpacing(4)

        # Action name (left-aligned)
        self._text_label = QLabel(self._text)
        self._text_label.setFont(QFont("Segoe UI", 13))
        layout.addWidget(self._text_label)

        # Stretch to push shortcut to the right
        layout.addStretch()

        # Keyboard shortcut (right-aligned, dimmed)
        if self._shortcut_text:
            self._shortcut_label = QLabel(self._shortcut_text)
            self._shortcut_label.setFont(QFont("Segoe UI", 13))
            self._shortcut_label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            layout.addWidget(self._shortcut_label)

    def _apply_styles(self) -> None:
        """Apply VS Code/Cursor dark theme styling."""
        c = Theme.get_colors()

        # Text colors
        text_color = c.menu_text if self._enabled else c.menu_text_disabled
        shortcut_color = c.menu_text_shortcut if self._enabled else c.menu_text_disabled

        # Base style
        style = """
            QWidget {
                background-color: transparent;
                border-radius: {TOKENS.radii.sm}px;
            }
        """

        if self._enabled:
            style += f"""
                QLabel {{
                    color: {text_color};
                }}
                QWidget:hover {{
                    background-color: {c.menu_hover};
                }}
                QWidget:hover QLabel {{
                    color: #FFFFFF;  /* Brighten to white on hover */
                }}
            """
        else:
            style += f"""
                QLabel {{
                    color: {text_color};
                }}
            """

        self.setStyleSheet(style)

        # Apply shortcut color separately (dimmed)
        if self._enabled and hasattr(self, "_shortcut_label"):
            self._shortcut_label.setStyleSheet(f"color: {shortcut_color};")
        elif not self._enabled and hasattr(self, "_shortcut_label"):
            self._shortcut_label.setStyleSheet(f"color: {c.menu_text_disabled};")

    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse click."""
        if self._enabled and event.button() == Qt.MouseButton.LeftButton:
            # Toggle checked state for checkable items
            if self._checkable:
                self._checked = not self._checked
                self._check_label.setText("✓" if self._checked else "")

            self.clicked.emit()
            if self._callback:
                try:
                    self._callback()
                except Exception as e:
                    logger.error(f"Error in context menu callback: {e}")
        super().mouseReleaseEvent(event)

    def set_checked(self, checked: bool) -> None:
        """Set the checked state (for checkable items)."""
        if self._checkable:
            self._checked = checked
            if hasattr(self, "_check_label"):
                self._check_label.setText("✓" if checked else "")

    def is_checked(self) -> bool:
        """Get the checked state."""
        return self._checked

    def set_enabled(self, enabled: bool) -> None:
        """Set the enabled state."""
        self._enabled = enabled
        self.setCursor(Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.ArrowCursor)
        self._apply_styles()

    def is_enabled(self) -> bool:
        """Get the enabled state."""
        return self._enabled


# =============================================================================
# MENU SEPARATOR
# =============================================================================


class ContextMenuSeparator(QWidget):
    """
    A horizontal separator line between menu sections.

    Visual:
    ──────────────────────────────────────────────────────────
    Height: 1px line + 4px margins top/bottom = 9px total
    Color: Theme.menu_separator
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the separator."""
        super().__init__(parent)
        set_fixed_height(self, 9)  # 4px margin + 1px line + 4px margin

        layout = QVBoxLayout(self)
        set_margins(layout, (0, 4, 0, 4))
        set_spacing(layout, 0)

        # The separator line
        line = QWidget()
        line.setFixedHeight(1)
        c = Theme.get_colors()
        line.setStyleSheet(f"background-color: {c.menu_separator};")
        line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(line)


# =============================================================================
# CONTEXT MENU
# =============================================================================


class ContextMenu(QWidget):
    """
    VS Code/Cursor-style context menu popup.

    Features:
    - Dark theme matching VS Code/Cursor selection menu
    - Action name on left, keyboard shortcut on right
    - Hover state with blue highlight
    - Separator support with proper spacing
    - Click-outside-to-close via PopupManager
    - Escape key to close
    - Drop shadow for elevation
    - Scrollable for long menus

    Example:
        menu = ContextMenu(parent=main_window)

        menu.add_item("Copy", callback=copy_func, shortcut="Ctrl+C")
        menu.add_item("Cut", callback=cut_func, shortcut="Ctrl+X")
        menu.add_separator()
        menu.add_item("Paste", callback=paste_func, shortcut="Ctrl+V")

        menu.show_at_position(global_mouse_pos)
    """

    # Menu closed signal
    closed = Signal()

    # Default dimensions
    DEFAULT_WIDTH = 280
    MIN_WIDTH = TOKENS.sizes.panel_width_min
    MAX_WIDTH = TOKENS.sizes.dialog_width_sm
    ITEM_HEIGHT = 28
    SEPARATOR_HEIGHT = 9

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the context menu."""
        super().__init__(parent)

        self._items: list[ContextMenuItem] = []
        self._separators: list[ContextMenuSeparator] = []

        # Window setup - frameless tool window
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)  # Allow key events

        # Drop shadow effect using Theme color
        c = Theme.get_colors()
        shadow_color = QColor(c.menu_shadow)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(shadow_color)
        self.setGraphicsEffect(shadow)

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Setup the menu UI with scrollable content."""
        main_layout = QVBoxLayout(self)
        set_margins(main_layout, (1, 1, 1, 1))
        set_spacing(main_layout, 0)

        # Container for rounded corners and border
        container = QWidget()
        container.setObjectName("menuContainer")
        container_layout = QVBoxLayout(container)
        set_margins(container_layout, (0, 0, 0, 0))
        set_spacing(container_layout, 0)

        # Scroll area for long menus
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        # Content widget
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self.set_margins(_content_layout, (0, 6, 0, 6))  # Top/bottom padding
        self.set_spacing(_content_layout, 0)
        self._content_layout.addStretch()  # Push items to top

        scroll.setWidget(self._content)
        container_layout.addWidget(scroll)

        main_layout.addWidget(container)

        # Apply scroll area styles
        c = Theme.get_colors()
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 10px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {c.border_light};
                border-radius: {TOKENS.radii.md}px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {c.text_secondary};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

    def _apply_styles(self) -> None:
        """Apply VS Code/Cursor dark theme styling."""
        c = Theme.get_colors()

        self.setStyleSheet(f"""
            QWidget#menuContainer {{
                background-color: {c.menu_bg};
                border: 1px solid {c.menu_border};
                border-radius: {TOKENS.radii.md}px;
            }}
            QWidget {{
                background-color: transparent;
            }}
        """)

    def add_item(
        self,
        text: str,
        callback: Callable[[], Any] | None = None,
        shortcut: str | None = None,
        icon: str | None = None,
        enabled: bool = True,
        checkable: bool = False,
        checked: bool = False,
    ) -> ContextMenuItem:
        """
        Add a menu item.

        Args:
            text: Display text for the action
            callback: Function to call when clicked
            shortcut: Keyboard shortcut text to display (e.g., "Ctrl+C")
            icon: Optional icon to show before the action name
            enabled: Whether the item is enabled/clickable
            checkable: Whether the item shows a checkmark when clicked
            checked: Initial checked state (for checkable items)

        Returns:
            The created ContextMenuItem instance
        """
        item = ContextMenuItem(
            text=text,
            callback=callback,
            shortcut=shortcut,
            icon=icon,
            enabled=enabled,
            checkable=checkable,
            checked=checked,
        )
        item.clicked.connect(self._on_item_clicked)

        self._items.append(item)

        # Insert before the stretch
        if self._content_layout.count() > 0:
            stretch_index = self._content_layout.count() - 1
            self._content_layout.insertWidget(stretch_index, item)
        else:
            self._content_layout.insertWidget(0, item)

        # Update menu width based on content
        self._update_width()

        return item

    def add_separator(self) -> ContextMenuSeparator:
        """
        Add a separator line.

        Returns:
            The created ContextMenuSeparator instance
        """
        separator = ContextMenuSeparator()
        self._separators.append(separator)

        # Insert before the stretch
        if self._content_layout.count() > 0:
            stretch_index = self._content_layout.count() - 1
            self._content_layout.insertWidget(stretch_index, separator)
        else:
            self._content_layout.insertWidget(0, separator)

        return separator

    def _update_width(self) -> None:
        """Update menu width based on content."""
        # Calculate required width
        max_width = self.DEFAULT_WIDTH

        # Measure each item's text width
        font = QFont("Segoe UI", 13)
        fm = QFontMetrics(font)

        for item in self._items:
            # Text width
            text_width = fm.horizontalAdvance(item._text)
            # Shortcut width (if any)
            shortcut_width = fm.horizontalAdvance(item._shortcut_text) if item._shortcut_text else 0
            # Padding and spacing
            item_width = 24 + text_width + 16 + shortcut_width + 12  # margins + spacing

            max_width = max(max_width, item_width)

        # Clamp to min/max
        width = max(self.MIN_WIDTH, min(self.MAX_WIDTH, max_width))

        self.setFixedWidth(width)

    def _on_item_clicked(self) -> None:
        """Handle item click - close menu after action."""
        # Close the menu after a short delay to allow the callback to execute
        QApplication.processEvents()
        self.close()

    def clear(self) -> None:
        """Remove all items and separators."""
        for item in self._items:
            item.deleteLater()
        for sep in self._separators:
            sep.deleteLater()

        self._items.clear()
        self._separators.clear()

        # Recreate layout
        while self._content_layout.count():
            child = self._content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self._content_layout.addStretch()

    def show_at_position(self, pos: QPoint) -> None:
        """
        Show the menu at the specified global position.

        Adjusts position to stay within screen bounds.

        Args:
            pos: Global screen position to show the menu at
        """
        # Get screen geometry
        screen = QApplication.primaryScreen().availableGeometry()

        # Calculate height based on content
        content_height = (
            len(self._items) * self.ITEM_HEIGHT
            + len(self._separators) * self.SEPARATOR_HEIGHT
            + 12  # top/bottom padding
        )

        # Limit max height to screen
        max_height = min(TOKENS.sizes.dialog_width_sm, screen.height() - 20)
        height = min(content_height, max_height)

        self.resize(self.width(), height)

        # Adjust position to stay on screen
        x = pos.x()
        y = pos.y()

        if x + self.width() > screen.right():
            x = screen.right() - self.width() - 10

        if y + height > screen.bottom():
            y = screen.bottom() - height - 10

        if x < screen.left():
            x = screen.left() + 10

        if y < screen.top():
            y = screen.top() + 10

        self.move(x, y)
        self.show()

        # Activate window to ensure keyboard events (Escape) work
        self.activateWindow()
        self.raise_()

    def showEvent(self, event) -> None:
        """Handle show event - register with PopupManager."""
        super().showEvent(event)
        PopupManager.register(self)

    def closeEvent(self, event) -> None:
        """Handle close event - unregister from PopupManager."""
        PopupManager.unregister(self)
        self.closed.emit()
        super().closeEvent(event)

    def keyPressEvent(self, event) -> None:
        """Handle key press events - Escape closes menu."""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            event.accept()
            return
        super().keyPressEvent(event)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def show_context_menu(
    parent: QWidget,
    position: QPoint,
    items: list[dict[str, Any]],
) -> ContextMenu:
    """
    Show a context menu at the given position.

    Convenience function for quickly creating and showing a menu.

    Args:
        parent: Parent widget
        position: Global position to show menu at
        items: List of item dicts with keys:
            - text: str (required)
            - callback: Callable (optional)
            - shortcut: str (optional)
            - enabled: bool (default True)
            - separator: bool (default False) - if True, inserts a separator

    Returns:
        The created ContextMenu instance

    Example:
        show_context_menu(
            parent=self,
            position=global_pos,
            items=[
                {"text": "Copy", "callback": copy_func, "shortcut": "Ctrl+C"},
                {"text": "Cut", "callback": cut_func, "shortcut": "Ctrl+X"},
                {"separator": True},
                {"text": "Paste", "callback": paste_func, "shortcut": "Ctrl+V"},
            ]
        )
    """
    menu = ContextMenu(parent)

    for item_spec in items:
        if item_spec.get("separator", False):
            menu.add_separator()
        else:
            menu.add_item(
                text=item_spec["text"],
                callback=item_spec.get("callback"),
                shortcut=item_spec.get("shortcut"),
                enabled=item_spec.get("enabled", True),
            )

    menu.show_at_position(position)
    return menu
