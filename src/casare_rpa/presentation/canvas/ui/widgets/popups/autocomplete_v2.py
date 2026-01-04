"""
AutocompleteV2 - Fuzzy search autocomplete popup.

Text field autocomplete popup with fuzzy search, type badges,
and value preview. Designed for variable/function completion in
node property editors.

Features:
- Fuzzy search input (hidden, captures typing from parent)
- Filtered list with match scores
- Keyboard: Up/Down/Enter/Esc/Tab navigation
- Type badges for variables (bool, number, string, etc.)
- Value preview in secondary column
- Auto-select first match
- Debounced filter (150ms)

Usage:
    autocomplete = AutocompleteV2(parent=None)
    autocomplete.set_items([
        ("variable1", "Variable 1", "number", "42"),
        ("variable2", "Variable 2", "string", '"hello"'),
    ])
    autocomplete.set_filter_text("var")  # Filters items
    autocomplete.show_below_cursor()

Signals:
    item_selected: Signal(str)  # Emitted with insertion_text
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import QPoint, Qt, Signal, Slot
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.popups.popup_items import TypeBadge
from casare_rpa.presentation.canvas.ui.widgets.popups.popup_utils import (
    Debounce,
    get_scrollbar_style_v2,
)
from casare_rpa.presentation.canvas.ui.widgets.popups.popup_window_base import (
    PopupWindowBase,
)

if TYPE_CHECKING:
    from PySide6.QtGui import QKeyEvent


# =============================================================================
# Fuzzy Match
# =============================================================================


def fuzzy_match(query: str, text: str) -> tuple[bool, int]:
    """
    Simple fuzzy matching for autocomplete.

    Args:
        query: Search query (lowercased)
        text: Text to search in (lowercased)

    Returns:
        Tuple of (is_match, score) where lower score = better match
    """
    if not query:
        return True, 0

    query = query.lower()
    text = text.lower()

    # Exact prefix match (best)
    if text.startswith(query):
        return True, 0

    # Contains match (good)
    if query in text:
        return True, len(text.split(query)[0])

    # Simple character-by-character match
    query_idx = 0
    score = 0
    for char in text:
        if query_idx < len(query) and char == query[query_idx]:
            query_idx += 1
            score += 2  # Penalty for gaps

    if query_idx == len(query):
        return True, score

    return False, -1


# =============================================================================
# Item Data
# =============================================================================


@dataclass(frozen=True)
class AutocompleteItem:
    """
    Single autocomplete item.

    Attributes:
        key: Unique identifier (e.g., variable name)
        label: Display label
        type_name: Type for badge (e.g., "number", "string", "bool")
        value_preview: Optional value preview text
        insertion_text: Text to insert on selection (defaults to key)
    """

    key: str
    label: str
    type_name: str = "any"
    value_preview: str = ""
    insertion_text: str = ""

    def __post_init__(self) -> None:
        """Set insertion_text to key if not provided."""
        if not self.insertion_text:
            object.__setattr__(self, "insertion_text", self.key)


# =============================================================================
# List Item Widget
# =============================================================================


class AutocompleteListItem(QFrame):
    """
    Single item in the autocomplete list.

    Displays:
    - Type badge (left)
    - Label (middle)
    - Value preview (right, optional)
    """

    def __init__(
        self,
        item: AutocompleteItem,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize list item.

        Args:
            item: AutocompleteItem data
            parent: Parent widget
        """
        super().__init__(parent)
        self._item = item
        self._is_selected = False

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Setup the UI layout."""
        self.setFixedHeight(TOKENS_V2.sizes.row_height_compact)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            TOKENS_V2.spacing.sm,
            0,
            TOKENS_V2.spacing.sm,
            0,
        )
        layout.setSpacing(TOKENS_V2.spacing.sm)

        # Type badge
        badge_text = TypeBadge.badge_for_type(self._item.type_name)
        self._badge = TypeBadge(badge_text, self)
        badge_color = TypeBadge.color_for_type(self._item.type_name)
        self._badge.setStyleSheet(
            self._badge.styleSheet().replace(
                THEME_V2.text_secondary,
                badge_color,
            )
        )
        layout.addWidget(self._badge)

        # Label
        self._label = QLabel(self._item.label)
        self._label.setStyleSheet(f"""
            color: {THEME_V2.text_primary};
            font-size: {TOKENS_V2.typography.body}px;
        """)
        layout.addWidget(self._label)

        layout.addStretch()

        # Value preview (optional)
        if self._item.value_preview:
            self._preview = QLabel(self._item.value_preview)
            self._preview.setStyleSheet(f"""
                color: {THEME_V2.text_muted};
                font-size: {TOKENS_V2.typography.caption}px;
                font-family: {TOKENS_V2.typography.mono};
            """)
            layout.addWidget(self._preview)

    def _apply_style(self) -> None:
        """Apply base styling."""
        self._update_style()

    def _update_style(self) -> None:
        """Update style based on selection state."""
        bg = THEME_V2.bg_selected if self._is_selected else "transparent"

        self.setStyleSheet(f"""
            AutocompleteListItem {{
                background-color: {bg};
                border: none;
                border-radius: {TOKENS_V2.radius.xs}px;
            }}
        """)

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


# =============================================================================
# Autocomplete Popup
# =============================================================================


class AutocompleteV2(PopupWindowBase):
    """
    Fuzzy search autocomplete popup.

    Provides variable/function completion with:
    - Fuzzy filtering
    - Keyboard navigation (Up/Down/Enter/Esc/Tab)
    - Type badges
    - Value preview
    - Auto-select first match

    Signals:
        item_selected: Signal(str) - Emitted with insertion_text
    """

    item_selected = Signal(str)

    # Default dimensions
    DEFAULT_WIDTH = 320
    DEFAULT_HEIGHT = 240
    MIN_WIDTH = 200
    MIN_HEIGHT = 120

    # Max visible items before scrolling
    MAX_VISIBLE_ITEMS = 8

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize autocomplete popup.

        Args:
            parent: Parent widget
        """
        super().__init__(
            title="",
            parent=parent,
            resizable=False,
            pin_button=False,
            close_button=False,
            min_width=self.MIN_WIDTH,
            min_height=self.MIN_HEIGHT,
        )

        # Items state
        self._items: list[AutocompleteItem] = []
        self._filtered_items: list[tuple[int, AutocompleteItem]] = []  # (score, item)
        self._current_filter: str = ""
        self._selected_index: int = -1

        # Debounce for filter updates
        self._debounce = Debounce(delay_ms=150, parent=self)

        # List widget
        self._list: QListWidget | None = None

        # Hidden input for capturing keystrokes
        self._hidden_input: QWidget | None = None

        # Setup content
        self._setup_content()

    def _setup_content(self) -> None:
        """Setup the list content widget."""
        # Create list widget
        self._list = QListWidget()
        self._list.setObjectName("autocompleteList")
        self._list.setFrameShape(QFrame.Shape.NoFrame)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self._list.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Apply scrollbar style
        self._list.setStyleSheet(f"""
            QListWidget#autocompleteList {{
                background-color: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                height: {TOKENS_V2.sizes.row_height_compact}px;
            }}
            QListWidget::item:selected {{
                background: transparent;
            }}
            {get_scrollbar_style_v2()}
        """)

        # Connect signals
        self._list.itemClicked.connect(self._on_item_clicked)
        self._list.itemDoubleClicked.connect(self._on_item_activated)

        # Set as content
        self.set_content_widget(self._list)

        # Set size
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

    # =========================================================================
    # Public API
    # =========================================================================

    def set_items(self, items: list[tuple[str, str, str, str] | AutocompleteItem]) -> None:
        """
        Set autocomplete items.

        Args:
            items: List of tuples (key, label, type_name, value_preview)
                   or AutocompleteItem instances
        """
        self._items = []
        for item in items:
            if isinstance(item, AutocompleteItem):
                self._items.append(item)
            else:
                key, label, type_name, value_preview = item
                self._items.append(
                    AutocompleteItem(
                        key=key,
                        label=label,
                        type_name=type_name,
                        value_preview=value_preview,
                    )
                )

        # Re-apply current filter
        if self._current_filter:
            self._apply_filter()

    def clear_items(self) -> None:
        """Clear all items."""
        self._items.clear()
        self._filtered_items.clear()
        self._selected_index = -1
        if self._list:
            self._list.clear()

    def set_filter_text(self, text: str, immediate: bool = False) -> None:
        """
        Set filter text (with debouncing).

        Args:
            text: Filter query
            immediate: If True, apply immediately without debounce
        """
        self._current_filter = text

        if immediate:
            self._debounce.cancel()
            self._apply_filter()
        else:
            self._debounce.call(self._apply_filter)

    def show_below_cursor(self, offset: QPoint | None = None) -> None:
        """
        Show popup below cursor.

        Args:
            offset: Optional offset from cursor position
        """
        if offset is None:
            offset = QPoint(0, TOKENS_V2.spacing.sm)

        pos = QCursor.pos() + offset
        self.show_at_position(pos)

    def show_below_widget(
        self,
        widget: QWidget,
        offset: QPoint | None = None,
    ) -> None:
        """
        Show popup below a widget.

        Args:
            widget: Anchor widget
            offset: Optional offset from widget
        """
        if offset is None:
            offset = QPoint(0, TOKENS_V2.spacing.xs)

        from casare_rpa.presentation.canvas.ui.widgets.popups.popup_utils import (
            position_below_widget,
        )

        pos = position_below_widget(
            widget,
            self.width(),
            min(self.height(), self._calculate_height()),
            offset,
        )
        self.show_at_position(pos)

    def get_selected_item(self) -> AutocompleteItem | None:
        """
        Get currently selected item.

        Returns:
            Selected AutocompleteItem or None
        """
        if 0 <= self._selected_index < len(self._filtered_items):
            return self._filtered_items[self._selected_index][1]
        return None

    # =========================================================================
    # Filter Logic
    # =========================================================================

    def _apply_filter(self) -> None:
        """Apply fuzzy filter and update list."""
        if not self._list:
            return

        # Filter and score items
        self._filtered_items = []
        for item in self._items:
            is_match, score = fuzzy_match(self._current_filter, item.label)
            if is_match:
                self._filtered_items.append((score, item))

        # Sort by score (lower is better)
        self._filtered_items.sort(key=lambda x: x[0])

        # Update list widget
        self._list.clear()
        for score, item in self._filtered_items:
            list_item = QListWidgetItem()
            widget = AutocompleteListItem(item)
            list_item.setSizeHint(widget.sizeHint())
            self._list.addItem(list_item)
            self._list.setItemWidget(list_item, widget)

        # Auto-select first item
        if self._filtered_items:
            self._select_row(0)
        else:
            self._selected_index = -1

        # Adjust height based on item count
        self._adjust_height()

    def _select_row(self, row: int) -> None:
        """
        Select a row by index.

        Args:
            row: Row index to select
        """
        if not self._list or not self._filtered_items:
            return

        # Clear previous selection
        if 0 <= self._selected_index < self._list.count():
            prev_item = self._list.item(self._selected_index)
            if prev_item:
                prev_widget = self._list.itemWidget(prev_item)
                if isinstance(prev_widget, AutocompleteListItem):
                    prev_widget.set_selected(False)

        # Set new selection
        self._selected_index = row
        if 0 <= row < self._list.count():
            new_item = self._list.item(row)
            if new_item:
                new_widget = self._list.itemWidget(new_item)
                if isinstance(new_widget, AutocompleteListItem):
                    new_widget.set_selected(True)

                # Scroll into view
                self._list.scrollToItem(new_item)

    def _adjust_height(self) -> None:
        """Adjust popup height based on visible items."""
        if not self._list:
            return

        item_count = min(len(self._filtered_items), self.MAX_VISIBLE_ITEMS)
        item_height = TOKENS_V2.sizes.row_height_compact

        # Calculate content height
        content_height = item_count * item_height

        # Add padding
        total_height = content_height + TOKENS_V2.spacing.md * 2

        # Clamp between min and max
        total_height = max(self.MIN_HEIGHT, min(total_height, self.DEFAULT_HEIGHT))

        # Calculate height for clamping
        self._target_height = total_height

    def _calculate_height(self) -> int:
        """Calculate target height for positioning."""
        return getattr(self, "_target_height", self.DEFAULT_HEIGHT)

    # =========================================================================
    # Selection
    # =========================================================================

    def _confirm_selection(self) -> None:
        """Confirm selection and emit signal."""
        item = self.get_selected_item()
        if item:
            logger.debug(f"Autocomplete selected: {item.insertion_text}")
            self.item_selected.emit(item.insertion_text)
            self.close()

    def _move_selection(self, delta: int) -> None:
        """
        Move selection by delta.

        Args:
            delta: Amount to move (-1 for up, 1 for down)
        """
        if not self._filtered_items:
            return

        new_index = self._selected_index + delta

        # Wrap around
        if new_index < 0:
            new_index = len(self._filtered_items) - 1
        elif new_index >= len(self._filtered_items):
            new_index = 0

        self._select_row(new_index)

    # =========================================================================
    # Qt Event Handlers
    # =========================================================================

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Handle key press events for navigation.

        Args:
            event: Key event
        """
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

            case Qt.Key.Key_Tab:
                event.accept()
                self._confirm_selection()
                return

            case Qt.Key.Key_Escape:
                event.accept()
                self.close()
                return

        # Pass other keys to parent
        super().keyPressEvent(event)

    @Slot()
    def _on_item_clicked(self, list_item: QListWidgetItem) -> None:
        """
        Handle item click - select only.

        Args:
            list_item: Clicked list item
        """
        row = self._list.row(list_item) if self._list else -1
        if row >= 0:
            self._select_row(row)

    @Slot()
    def _on_item_activated(self, list_item: QListWidgetItem) -> None:
        """
        Handle item double-click - confirm selection.

        Args:
            list_item: Activated list item
        """
        row = self._list.row(list_item) if self._list else -1
        if row >= 0:
            self._select_row(row)
            self._confirm_selection()

    def showEvent(self, event) -> None:
        """Handle show event - ensure first item is selected."""
        super().showEvent(event)
        if self._filtered_items and self._selected_index < 0:
            self._select_row(0)


__all__ = ["AutocompleteItem", "AutocompleteListItem", "AutocompleteV2"]
