"""
ContextMenuV2 - VS Code/Cursor-style context menu popup.

Lightweight context menu for right-click actions:
- Scrollable list of items with icons, shortcuts, separators
- Keyboard navigation (Up/Down/Enter/Esc)
- Item hover states
- Checkable items support
- No pin button, minimal header
- Click-outside-to-close

Usage:
    menu = ContextMenuV2(parent=None)
    menu.add_item(text="Copy", callback=copy_func, shortcut="Ctrl+C", icon="C")
    menu.add_separator()
    menu.add_item(text="Paste", callback=paste_func, shortcut="Ctrl+V", enabled=False)
    menu.show_at_position(QPoint(x, y))

Signals:
    item_selected: Emitted when item is clicked (str: item_id)
    closed: Emitted when popup is closed
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any

from loguru import logger
from PySide6.QtCore import QPoint, Qt, Signal, Slot
from PySide6.QtWidgets import QFrame, QScrollArea, QVBoxLayout, QWidget

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.theme.icons_v2 import icon_v2
from casare_rpa.presentation.canvas.ui.widgets.popups.popup_items import (
    MenuItem,
    MenuSeparator,
)
from casare_rpa.presentation.canvas.ui.widgets.popups.popup_window_base import (
    PopupWindowBase,
)

if TYPE_CHECKING:
    from collections.abc import Callable


class MinimalHeader(QFrame):
    """
    Minimal header for context menus (no title, no pin button).

    Provides drag handle only - no visible UI elements.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._drag_pos: QPoint | None = None
        self._parent_window: QWidget | None = None
        self._is_dragging: bool = False
        self.setCursor(Qt.CursorShape.SizeAllCursor)

    def set_parent_window(self, window: QWidget) -> None:
        """Set the window to be moved when dragging."""
        self._parent_window = window

    def is_dragging(self) -> bool:
        """Check if currently dragging."""
        return self._is_draging

    @Slot()
    def mousePressEvent(self, event) -> None:
        """Start drag on left click."""
        if event.button() == Qt.MouseButton.LeftButton and self._parent_window:
            self._drag_pos = event.globalPos() - self._parent_window.pos()
            self._is_dragging = True
            event.accept()
        else:
            super().mousePressEvent(event)

    @Slot()
    def mouseMoveEvent(self, event) -> None:
        """Move window while dragging."""
        if self._drag_pos is not None and self._parent_window:
            self._parent_window.move(event.globalPos() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    @Slot()
    def mouseReleaseEvent(self, event) -> None:
        """End drag."""
        self._drag_pos = None
        self._is_dragging = False
        super().mouseReleaseEvent(event)


class ScrollAreaNoScroll(QScrollArea):
    """
    ScrollArea that only shows scrollbar when needed.

    Hides scrollbar for short menus, shows for long menus.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._apply_style()

    def _apply_style(self) -> None:
        """Apply v2 dark theme styling."""
        self.setStyleSheet(f"""
            ScrollAreaNoScroll {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {THEME_V2.scrollbar_bg};
                width: {TOKENS_V2.sizes.scrollbar_width}px;
                border-radius: {TOKENS_V2.radius.xs}px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {THEME_V2.scrollbar_handle};
                border-radius: {TOKENS_V2.radius.xs}px;
                min-height: {TOKENS_V2.sizes.scrollbar_min_height}px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {THEME_V2.scrollbar_hover};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)


class ContextMenuV2(PopupWindowBase):
    """
    VS Code/Cursor-style context menu popup.

    Features:
    - Scrollable item list
    - Icons, shortcuts, separators
    - Keyboard navigation (Up/Down/Enter/Esc)
    - Item hover states
    - Checkable items
    - No pin button (minimal header)

    Signals:
        item_selected: Emitted when item is clicked (str: item_id)
    """

    item_selected = Signal(str)

    # Menu-specific dimensions
    MENU_MIN_WIDTH = 180
    MENU_MIN_HEIGHT = 40
    MENU_MAX_WIDTH = 320
    MENU_MAX_HEIGHT = 450

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize context menu.

        Args:
            parent: Parent widget
        """
        # Initialize base with minimal settings (no title, no pin button)
        super().__init__(
            title="",
            parent=parent,
            resizable=False,
            pin_button=False,
            close_button=False,
            min_width=self.MENU_MIN_WIDTH,
            min_height=self.MENU_MIN_HEIGHT,
        )

        # Menu items storage
        self._items: list[tuple[str, MenuItem]] = []  # (item_id, widget)
        self._separators: list[MenuSeparator] = []
        self._current_index: int = -1  # For keyboard navigation

        # Content layout
        self._menu_container: QWidget
        self._menu_layout: QVBoxLayout

        # Override header with minimal drag handle
        self._setup_minimal_header()

        # Setup menu content area
        self._setup_menu_content()

    def _setup_minimal_header(self) -> None:
        """Override base header with minimal drag-only header."""
        # Remove the default header if it exists
        if self._header:
            self._header.deleteLater()

        # Create minimal drag handle (invisible but functional)
        self._header = MinimalHeader()
        self._header.set_parent_window(self)
        self._header.setFixedHeight(4)  # Minimal drag handle at top

        # Replace header in container layout
        container = self.findChild(QFrame, "popupContainer")
        if container and container.layout():
            # Remove old header (first item)
            old_header = container.layout().itemAt(0)
            if old_header:
                old_header.widget().deleteLater()

            # Insert minimal header at top
            container.layout().insertWidget(0, self._header)

            # Hide it completely (still functional for drag)
            self._header.hide()

    def _setup_menu_content(self) -> None:
        """Setup scrollable menu content area."""
        # Clear default content area styling
        self._content_area.setObjectName("menuArea")
        self._content_area.setStyleSheet("""
            QFrame#menuArea {
                background-color: transparent;
                border: none;
                border-radius: 0px;
            }
        """)

        # Reset margins for tight fit
        self._content_area.layout().setContentsMargins(
            TOKENS_V2.spacing.xs,
            TOKENS_V2.spacing.xs,
            TOKENS_V2.spacing.xs,
            TOKENS_V2.spacing.xs,
        )

        # Create scroll area
        scroll = ScrollAreaNoScroll(self._content_area)
        self._content_area.layout().addWidget(scroll)

        # Menu container
        self._menu_container = QWidget()
        self._menu_layout = QVBoxLayout(self._menu_container)
        self._menu_layout.setContentsMargins(0, 0, 0, 0)
        self._menu_layout.setSpacing(0)
        self._menu_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self._menu_container)

        # Set container style
        self._menu_container.setStyleSheet(f"""
            QWidget {{
                background-color: {THEME_V2.bg_elevated};
            }}
        """)

    # =========================================================================
    # Public API - Item Management
    # =========================================================================

    def add_item(
        self,
        item_id: str,
        text: str,
        callback: Callable[[], Any] | None = None,
        shortcut: str | None = None,
        icon: str | None = None,
        enabled: bool = True,
        checkable: bool = False,
        checked: bool = False,
    ) -> MenuItem:
        """
        Add a menu item.

        Args:
            item_id: Unique identifier for the item
            text: Display text
            callback: Function to call when clicked
            shortcut: Keyboard shortcut to display (e.g., "Ctrl+S")
            icon: Optional icon name from IconProviderV2 (e.g., "copy", "paste")
                  or text/emoji prefix
            enabled: Whether item is enabled
            checkable: Whether item can be checked
            checked: Initial check state

        Returns:
            The created MenuItem widget
        """
        # Convert icon name to themed icon/pixmap if available
        icon_display = icon
        if icon and icon_v2.has_icon(icon):
            # Icon exists in IconProviderV2 - use it
            pixmap = icon_v2.get_pixmap(icon, size=16, state="normal" if enabled else "disabled")
            if pixmap:
                icon_display = ""  # MenuItem will handle QIcon display
                # Store icon reference for MenuItem
                icon_display = icon  # Keep name for MenuItem to render

        item = MenuItem(
            text=text,
            callback=callback,
            shortcut=shortcut,
            icon=icon_display,
            enabled=enabled,
            checkable=checkable,
            checked=checked,
            parent=self._menu_container,
        )

        # Apply icon pixmap if using IconProviderV2
        if icon and icon_v2.has_icon(icon) and hasattr(item, "_icon_label"):
            pixmap = icon_v2.get_pixmap(icon, size=16, state="normal" if enabled else "disabled")
            if pixmap:
                item._icon_label.setPixmap(pixmap)

        # Connect signals using partial (no lambdas)
        item.clicked.connect(partial(self._on_item_clicked, item_id))
        item.hovered.connect(partial(self._on_item_hovered, item))

        # Store item widget reference for partial callback
        item._menu_widget_ref = item

        # Add to layout
        self._menu_layout.addWidget(item)
        self._items.append((item_id, item))

        # Update width if needed
        self._update_width()

        return item

    def add_separator(self) -> MenuSeparator:
        """
        Add a separator line.

        Returns:
            The created MenuSeparator widget
        """
        # Add margin for separator spacing
        separator = MenuSeparator(self._menu_container)
        separator.setStyleSheet(f"""
            MenuSeparator {{
                background-color: {THEME_V2.border};
                border: none;
                margin: {TOKENS_V2.spacing.xs}px 0px;
            }}
        """)

        self._menu_layout.addWidget(separator)
        self._separators.append(separator)

        return separator

    def clear(self) -> None:
        """Remove all items and separators."""
        for item_id, item in self._items:
            item.deleteLater()
        for sep in self._separators:
            sep.deleteLater()

        self._items.clear()
        self._separators.clear()
        self._current_index = -1

    def remove_item(self, item_id: str) -> bool:
        """
        Remove an item by ID.

        Args:
            item_id: ID of item to remove

        Returns:
            True if item was found and removed
        """
        for i, (id_, item) in enumerate(self._items):
            if id_ == item_id:
                self._menu_layout.removeWidget(item)
                item.deleteLater()
                self._items.pop(i)
                return True
        return False

    def set_item_enabled(self, item_id: str, enabled: bool) -> bool:
        """
        Set enabled state of an item.

        Args:
            item_id: ID of item to update
            enabled: New enabled state

        Returns:
            True if item was found and updated
        """
        for id_, item in self._items:
            if id_ == item_id:
                item.set_enabled(enabled)
                return True
        return False

    def set_item_checked(self, item_id: str, checked: bool) -> bool:
        """
        Set checked state of a checkable item.

        Args:
            item_id: ID of item to update
            checked: New checked state

        Returns:
            True if item was found and updated
        """
        for id_, item in self._items:
            if id_ == item_id:
                item.set_checked(checked)
                return True
        return False

    def set_item_text(self, item_id: str, text: str) -> bool:
        """
        Update text of an item.

        Args:
            item_id: ID of item to update
            text: New text

        Returns:
            True if item was found and updated
        """
        for id_, item in self._items:
            if id_ == item_id:
                # Access internal text label
                if hasattr(item, "_text_label"):
                    item._text_label.setText(text)
                    item._text = text
                return True
        return False

    # =========================================================================
    # Display Helpers
    # =========================================================================

    def show_at_position(self, global_pos: QPoint) -> None:
        """
        Show menu at global position with screen clamping.

        Args:
            global_pos: Global screen position for menu top-left
        """
        # Update size before showing
        self._update_size()

        super().show_at_position(global_pos)

        # Focus first enabled item for keyboard nav
        self._focus_first_enabled()

    def show_at_anchor(
        self,
        widget: QWidget,
        position: Any = None,  # AnchorPosition or None
        offset: QPoint | None = None,
    ) -> None:
        """
        Show menu anchored to a widget.

        Args:
            widget: Anchor widget
            position: Position relative to anchor (default: below)
            offset: Optional offset from anchor position
        """
        from casare_rpa.presentation.canvas.ui.widgets.popups.popup_window_base import (
            AnchorPosition,
        )

        if position is None:
            position = AnchorPosition.BELOW

        self._update_size()
        super().show_at_anchor(widget, position, offset)
        self._focus_first_enabled()

    def popup(self, global_pos: QPoint) -> None:
        """
        Alias for show_at_position - Qt-style naming.

        Args:
            global_pos: Global screen position
        """
        self.show_at_position(global_pos)

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    def _update_width(self) -> None:
        """Update menu width based on item contents."""
        max_width = 0

        for item_id, item in self._items:
            # Calculate item width
            item_width = item.sizeHint().width()
            max_width = max(max_width, item_width)

        # Constrain to min/max
        width = max(self.MENU_MIN_WIDTH, min(max_width + TOKENS_V2.spacing.md, self.MENU_MAX_WIDTH))

        # Only expand, don't shrink (user may have resized)
        if width > self.width():
            self.setFixedWidth(width)

    def _update_size(self) -> None:
        """Update menu size before showing."""
        # Calculate total height
        total_height = TOKENS_V2.spacing.xs * 2  # Top/bottom padding

        for item_id, item in self._items:
            total_height += item.height()

        for sep in self._separators:
            total_height += sep.height() + TOKENS_V2.spacing.xs * 2

        # Constrain to max height
        height = min(total_height, self.MENU_MAX_HEIGHT)

        # Update container size
        self._menu_container.setFixedHeight(total_height)

        # Set menu size
        self.setFixedSize(self.width(), height)

    def _focus_first_enabled(self) -> None:
        """Set keyboard focus to first enabled item."""
        for i, (item_id, item) in enumerate(self._items):
            if item.is_enabled():
                self._current_index = i
                return

    def _get_enabled_items(self) -> list[tuple[int, str, MenuItem]]:
        """Get list of (index, item_id, item) for enabled items only."""
        return [
            (i, item_id, item) for i, (item_id, item) in enumerate(self._items) if item.is_enabled()
        ]

    # =========================================================================
    # Event Handlers
    # =========================================================================

    @Slot()
    def _on_item_clicked(self, item_id: str) -> None:
        """
        Handle item click.

        Args:
            item_id: ID of clicked item
        """
        logger.debug(f"ContextMenu item clicked: {item_id}")
        self.item_selected.emit(item_id)
        self.close()

    @Slot()
    def _on_item_hovered(self, item: MenuItem) -> None:
        """
        Handle item hover - update keyboard nav index.

        Args:
            item: The hovered MenuItem
        """
        for i, (item_id, existing_item) in enumerate(self._items):
            if existing_item is item:
                self._current_index = i
                break

    def keyPressEvent(self, event) -> None:
        """
        Handle keyboard navigation.

        - Up/Down: Navigate items
        - Enter: Select current item
        - Escape: Close menu
        """
        enabled_items = self._get_enabled_items()

        if not enabled_items:
            super().keyPressEvent(event)
            return

        match event.key():
            case Qt.Key.Key_Down | Qt.Key.Key_Tab:
                # Move to next enabled item
                current_enabled_indices = [i for i, _, _ in enabled_items]
                if self._current_index in current_enabled_indices:
                    current_pos = current_enabled_indices.index(self._current_index)
                    next_pos = (current_pos + 1) % len(enabled_items)
                    self._current_index = enabled_items[next_pos][0]
                else:
                    self._current_index = enabled_items[0][0]

            case Qt.Key.Key_Up | Qt.Key.Key_Backtab:
                # Move to previous enabled item
                current_enabled_indices = [i for i, _, _ in enabled_items]
                if self._current_index in current_enabled_indices:
                    current_pos = current_enabled_indices.index(self._current_index)
                    next_pos = (current_pos - 1) % len(enabled_items)
                    self._current_index = enabled_items[next_pos][0]
                else:
                    self._current_index = enabled_items[-1][0]

            case Qt.Key.Key_Return | Qt.Key.Key_Enter:
                # Trigger current item
                if 0 <= self._current_index < len(self._items):
                    item_id, item = self._items[self._current_index]
                    if item.is_enabled():
                        item.trigger()
                event.accept()
                return

            case Qt.Key.Key_Escape:
                self.close()
                event.accept()
                return

            case _:
                super().keyPressEvent(event)
                return


__all__ = ["ContextMenuV2"]

