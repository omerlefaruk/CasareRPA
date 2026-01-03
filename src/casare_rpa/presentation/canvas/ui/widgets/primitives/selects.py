"""
Select/Combobox Primitive Components v2 - Epic 5.1 Component Library.

Provides dropdown selection widgets following the v2 design system:
- Compact sizing (sm/md/lg)
- THEME_V2 colors (dark-only, Cursor blue accent)
- icon_v2 for icons and clear button
- Proper @Slot decorators
- Type hints throughout

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.primitives.selects import (
        Select,
        ComboBox,
        ItemList,
    )

    # Basic select dropdown
    status_select = Select(
        items=[
            {"value": "pending", "label": "Pending", "icon": "clock"},
            {"value": "active", "label": "Active", "icon": "play"},
            {"value": "completed", "label": "Completed", "icon": "check"},
        ],
        placeholder="Select status...",
        value="pending",
        clearable=True,
    )
    status_select.current_changed.connect(lambda val: print(f"Status: {val}"))

    # Editable combobox
    search_combo = ComboBox(
        items=["Apple", "Banana", "Cherry"],
        placeholder="Search or type...",
    )
    search_combo.edit_text_changed.connect(lambda text: print(f"Typing: {text}"))

    # Item list for multi-select
    items = [
        {"value": "1", "label": "Option 1", "icon": "file"},
        {"value": "2", "label": "Option 2", "icon": "folder"},
    ]
    list_widget = ItemList(items=items, selected="1", icons_enabled=True)
    list_widget.selection_changed.connect(lambda vals: print(f"Selected: {vals}"))

See: docs/UX_REDESIGN_PLAN.md Phase 5 Epic 5.1
"""

from __future__ import annotations

from typing import Any, Literal

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QStyle,
    QToolButton,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.theme.icons_v2 import get_icon

# =============================================================================
# TYPE ALIASES
# =============================================================================

InputSize = Literal["sm", "md", "lg"]
SelectItem = dict[str, Any]  # {"value": ..., "label": ..., "icon": ...}


# =============================================================================
# SIZE HELPERS
# =============================================================================


def _get_input_height(size: InputSize) -> int:
    """Get input height for size variant."""
    return {
        "sm": TOKENS_V2.sizes.input_sm,
        "md": TOKENS_V2.sizes.input_md,
        "lg": TOKENS_V2.sizes.input_lg,
    }[size]


def _get_icon_size(size: InputSize) -> int:
    """Get icon size for input size variant."""
    return {
        "sm": 14,
        "md": 16,
        "lg": 18,
    }[size]


# =============================================================================
# STYLESHEET GENERATORS
# =============================================================================


def _get_combobox_stylesheet(size: InputSize = "md") -> str:
    """
    Generate QSS stylesheet for Select/ComboBox.

    Args:
        size: Input size variant ("sm", "md", "lg")

    Returns:
        QSS stylesheet string
    """
    height = _get_input_height(size)

    return f"""
        QComboBox {{
            background-color: {THEME_V2.input_bg};
            color: {THEME_V2.text_primary};
            border: 1px solid {THEME_V2.border};
            border-radius: {TOKENS_V2.radius.sm}px;
            padding: {TOKENS_V2.spacing.xxs}px {TOKENS_V2.spacing.xs}px;
            min-height: {height}px;
            font-size: {TOKENS_V2.typography.body}px;
        }}
        QComboBox:hover {{
            border-color: {THEME_V2.border_light};
        }}
        QComboBox:focus {{
            border-color: {THEME_V2.border_focus};
        }}
        QComboBox::drop-down {{
            border: none;
            width: {TOKENS_V2.spacing.md}px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid {THEME_V2.text_secondary};
            margin-right: {TOKENS_V2.spacing.xxs}px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {THEME_V2.bg_elevated};
            border: 1px solid {THEME_V2.border_light};
            border-radius: {TOKENS_V2.radius.sm}px;
            padding: {TOKENS_V2.spacing.xxs}px;
            selection-background-color: {THEME_V2.bg_selected};
            selection-color: {THEME_V2.text_primary};
            outline: none;
        }}
        QComboBox QAbstractItemView::item {{
            padding: {TOKENS_V2.spacing.xxs}px {TOKENS_V2.spacing.xs}px;
            min-height: 24px;
            color: {THEME_V2.text_primary};
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {THEME_V2.bg_hover};
        }}
        QComboBox::disabled {{
            background-color: {THEME_V2.bg_surface};
            color: {THEME_V2.text_disabled};
            border-color: transparent;
        }}
    """


def _get_listitem_stylesheet() -> str:
    """
    Generate QSS stylesheet for ItemList.

    Returns:
        QSS stylesheet string
    """
    return f"""
        QListWidget {{
            background-color: {THEME_V2.input_bg};
            border: 1px solid {THEME_V2.border};
            border-radius: {TOKENS_V2.radius.sm}px;
            outline: none;
        }}
        QListWidget::item {{
            padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.xs}px;
            color: {THEME_V2.text_primary};
            border-radius: {TOKENS_V2.radius.xs}px;
            margin: 1px;
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
        QListWidget::indicator {{
            width: 16px;
            height: 16px;
        }}
    """


# =============================================================================
# SELECT (Dropdown)
# =============================================================================


class Select(QWidget):
    """
    Dropdown select widget with v2 styling.

    Wraps QComboBox (non-editable) with optional clear button.

    Features:
    - Size variants (sm/md/lg) using TOKENS_V2
    - Items with value, label, and optional icon
    - Optional clear button (x icon) when value is set
    - Placeholder text support
    - THEME_V2 colors throughout

    Signals:
        current_changed(value): Emitted when selection changes (value or None)

    Example:
        from casare_rpa.presentation.canvas.ui.widgets.primitives.selects import Select

        # Basic select
        language = Select(
            items=[
                {"value": "en", "label": "English"},
                {"value": "es", "label": "Spanish"},
                {"value": "fr", "label": "French"},
            ],
            placeholder="Select language...",
            value="en",
        )
        language.current_changed.connect(lambda val: print(f"Language: {val}"))

        # With icons and clear button
        status = Select(
            items=[
                {"value": "pending", "label": "Pending", "icon": "clock"},
                {"value": "active", "label": "Active", "icon": "play"},
                {"value": "completed", "label": "Completed", "icon": "check"},
            ],
            placeholder="Select status...",
            clearable=True,
        )
    """

    current_changed = Signal(object)

    def __init__(
        self,
        items: list[SelectItem] | None = None,
        placeholder: str = "",
        value: Any = None,
        *,
        clearable: bool = False,
        size: InputSize = "md",
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize Select.

        Args:
            items: List of item dicts with keys: value, label, icon (optional)
            placeholder: Placeholder text shown when no selection
            value: Initial selected value (must match an item's value)
            clearable: Show clear button when value is set
            size: Input height: "sm" (22px), "md" (28px), "lg" (34px)
            parent: Parent widget
        """
        super().__init__(parent)

        self._size = size
        self._clearable = clearable
        self._placeholder_text = placeholder
        self._items: list[SelectItem] = items or []
        self._is_clearing = False

        self._setup_ui()
        self._connect_signals()
        self._apply_stylesheet()

        # Load items
        self._load_items()

        # Set initial value
        if value is not None:
            self.set_value(value)

    def _setup_ui(self) -> None:
        """Set up the UI elements."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create combo box
        self._combo = QComboBox()
        self._combo.setEditable(False)
        self._combo.setFixedHeight(_get_input_height(self._size))
        layout.addWidget(self._combo)

        # Add clear button if clearable
        if self._clearable:
            self._clear_btn = QToolButton(self)
            self._clear_btn.setCursor(Qt.PointingHandCursor)
            self._clear_btn.setIcon(
                get_icon("close", size=_get_icon_size(self._size), state="normal")
            )
            self._clear_btn.setStyleSheet("QToolButton { border: none; background: transparent; }")
            self._clear_btn.setVisible(False)
            self._update_clear_button_position()
        else:
            self._clear_btn = None

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self._combo.currentIndexChanged.connect(self._on_current_index_changed)
        if self._clear_btn:
            self._clear_btn.clicked.connect(self._on_clear_clicked)

    def _apply_stylesheet(self) -> None:
        """Apply stylesheet based on current configuration."""
        self._combo.setStyleSheet(_get_combobox_stylesheet(size=self._size))

    def _load_items(self) -> None:
        """Load items into the combo box."""
        self._combo.clear()

        # Add placeholder as first item if specified
        if self._placeholder_text:
            self._combo.addItem(self._placeholder_text, None)

        # Add items
        for item in self._items:
            label = item.get("label", str(item.get("value", "")))
            value = item.get("value")
            icon_name = item.get("icon")

            if icon_name:
                icon = get_icon(icon_name, size=_get_icon_size(self._size), state="normal")
                self._combo.addItem(icon, label, value)
            else:
                self._combo.addItem(label, value)

    def _update_clear_button_position(self) -> None:
        """Position clear button on the right side of the combo box."""
        if self._clear_btn:
            frame_width = self._combo.style().pixelMetric(QStyle.PixelMetric.PM_DefaultFrameWidth)
            button_size = self._clear_btn.iconSize().width() + TOKENS_V2.spacing.xs
            self._set_combo_margins(right=button_size)

            # Move button to right side
            btn_y = (self._combo.height() - self._clear_btn.height()) // 2
            self._clear_btn.move(
                self._combo.width() - frame_width - button_size + TOKENS_V2.spacing.xxs,
                btn_y,
            )

    def _set_combo_margins(self, right: int = 0) -> None:
        """Set combo box text margins to account for clear button."""
        # Note: QComboBox doesn't have setTextMargins, so we use view margins
        # The clear button is positioned visually but doesn't affect internal layout
        pass

    @Slot(int)
    def _on_current_index_changed(self, index: int) -> None:
        """
        Handle current index change.

        Args:
            index: New current index
        """
        if self._is_clearing:
            return

        # Get value from item data
        if index >= 0:
            value = self._combo.itemData(index)
            self._update_clear_button_visibility()
            self.current_changed.emit(value)
        else:
            self.current_changed.emit(None)

    @Slot()
    def _on_clear_clicked(self) -> None:
        """Handle clear button click."""
        self._is_clearing = True
        try:
            # Reset to placeholder (index 0)
            if self._placeholder_text:
                self._combo.setCurrentIndex(0)
            else:
                self._combo.setCurrentIndex(-1)
            self._update_clear_button_visibility()
        finally:
            self._is_clearing = False

    def _update_clear_button_visibility(self) -> None:
        """Update clear button visibility based on current selection."""
        if self._clear_btn:
            # Show if value is not None (not placeholder)
            current_value = self.get_value()
            self._clear_btn.setVisible(current_value is not None)

    def resizeEvent(self, event) -> None:
        """Handle resize event to reposition clear button."""
        super().resizeEvent(event)
        if self._clear_btn:
            self._update_clear_button_position()

    def set_items(self, items: list[SelectItem]) -> None:
        """
        Set the items list.

        Args:
            items: List of item dicts with keys: value, label, icon (optional)
        """
        current_value = self.get_value()
        self._items = items
        self._load_items()

        # Try to restore previous value
        if current_value is not None:
            self.set_value(current_value)

    def get_items(self) -> list[SelectItem]:
        """Get the items list."""
        return self._items.copy()

    def set_minimum_width(self, width: int) -> None:
        """Set a minimum width so the current selection text isn't truncated."""
        self.setMinimumWidth(width)
        self._combo.setMinimumWidth(width)
        if self._clear_btn:
            self._update_clear_button_position()

    def set_value(self, value: Any) -> None:
        """
        Set the selected value programmatically.

        Args:
            value: Value to select (must match an item's value)
        """
        # Find index for this value
        for i in range(self._combo.count()):
            item_data = self._combo.itemData(i)
            if item_data == value:
                self._combo.setCurrentIndex(i)
                self._update_clear_button_visibility()
                return

        # Value not found, select placeholder
        if self._placeholder_text:
            self._combo.setCurrentIndex(0)
        else:
            self._combo.setCurrentIndex(-1)
        self._update_clear_button_visibility()

    def get_value(self) -> Any:
        """Get current selected value (None if no selection)."""
        index = self._combo.currentIndex()
        if index >= 0:
            return self._combo.itemData(index)
        return None

    def set_placeholder(self, text: str) -> None:
        """
        Set placeholder text.

        Args:
            text: Placeholder text
        """
        self._placeholder_text = text
        current_value = self.get_value()
        self._load_items()
        if current_value is not None:
            self.set_value(current_value)

    def get_placeholder(self) -> str:
        """Get placeholder text."""
        return self._placeholder_text

    def set_size(self, size: InputSize) -> None:
        """
        Change the input size.

        Args:
            size: New size variant ("sm", "md", "lg")
        """
        if self._size != size:
            self._size = size
            self._combo.setFixedHeight(_get_input_height(size))
            if self._clear_btn:
                self._clear_btn.setIcon(
                    get_icon("close", size=_get_icon_size(size), state="normal")
                )
                self._update_clear_button_position()
            self._load_items()  # Reload icons with new size
            self._apply_stylesheet()

    def get_size(self) -> InputSize:
        """Get current size variant."""
        return self._size

    def set_clearable(self, clearable: bool) -> None:
        """
        Set whether the select has a clear button.

        Args:
            clearable: Whether to show clear button
        """
        self._clearable = clearable
        if clearable and not self._clear_btn:
            # Add clear button
            self._setup_ui()
            self._connect_signals()
            self._apply_stylesheet()
            self._update_clear_button_position()
        elif not clearable and self._clear_btn:
            # Remove clear button
            self._clear_btn.deleteLater()
            self._clear_btn = None

    def set_enabled(self, enabled: bool) -> None:
        """
        Set enabled state.

        Args:
            enabled: Whether widget is enabled
        """
        self._combo.setEnabled(enabled)
        if self._clear_btn:
            self._clear_btn.setEnabled(enabled)

    def is_enabled(self) -> bool:
        """Check if widget is enabled."""
        return self._combo.isEnabled()

    def add_items(self, items: list[SelectItem] | list[str]) -> None:
        """
        Add items to existing items list.

        Convenience method for appending items.
        Handles both dictionary items and simple strings.

        Args:
            items: List of item dicts or strings to add
        """
        normalized_items = []
        for item in items:
            if isinstance(item, str):
                normalized_items.append({"value": item, "label": item})
            else:
                normalized_items.append(item)

        current_items = list(self._items)  # Copy list
        current_items.extend(normalized_items)
        self.set_items(current_items)


# =============================================================================
# COMBOBOX (Editable Dropdown)
# =============================================================================


class ComboBox(QWidget):
    """
    Editable combobox widget with v2 styling.

    Wraps QComboBox (editable=True) for text input with dropdown suggestions.

    Features:
    - Size variants (sm/md/lg) using TOKENS_V2
    - Items list for suggestions
    - Placeholder text support
    - THEME_V2 colors throughout

    Signals:
        current_changed(value): Emitted when selection changes from dropdown
        edit_text_changed(str): Emitted when text is edited

    Example:
        from casare_rpa.presentation.canvas.ui.widgets.primitives.selects import ComboBox

        # Basic combobox with string items
        fruit = ComboBox(
            items=["Apple", "Banana", "Cherry"],
            placeholder="Select or type fruit...",
        )
        fruit.edit_text_changed.connect(lambda text: print(f"Typing: {text}"))
        fruit.current_changed.connect(lambda val: print(f"Selected: {val}"))

        # With dict items
        options = ComboBox(
            items=[
                {"value": "1", "label": "Option 1"},
                {"value": "2", "label": "Option 2"},
            ],
            placeholder="Choose option...",
        )
    """

    current_changed = Signal(object)
    edit_text_changed = Signal(str)

    def __init__(
        self,
        items: list[SelectItem] | list[str] | None = None,
        placeholder: str = "",
        value: Any = None,
        *,
        size: InputSize = "md",
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize ComboBox.

        Args:
            items: List of item dicts or strings for dropdown suggestions
            placeholder: Placeholder text shown when empty
            value: Initial text value
            size: Input height: "sm" (22px), "md" (28px), "lg" (34px)
            parent: Parent widget
        """
        super().__init__(parent)

        self._size = size
        self._placeholder_text = placeholder
        self._items: list[SelectItem] = self._normalize_items(items or [])

        self._setup_ui()
        self._connect_signals()
        self._apply_stylesheet()

        # Load items
        self._load_items()

        # Set initial value
        if value is not None:
            self.set_value(str(value))

    def _normalize_items(self, items: list[SelectItem] | list[str]) -> list[SelectItem]:
        """Convert string items to dict format."""
        normalized = []
        for item in items:
            if isinstance(item, str):
                normalized.append({"value": item, "label": item})
            else:
                normalized.append(item)
        return normalized

    def _setup_ui(self) -> None:
        """Set up the UI elements."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create editable combo box
        self._combo = QComboBox()
        self._combo.setEditable(True)
        self._combo.setFixedHeight(_get_input_height(self._size))
        layout.addWidget(self._combo)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self._combo.currentTextChanged.connect(self._on_text_changed)
        self._combo.currentIndexChanged.connect(self._on_current_index_changed)

    def _apply_stylesheet(self) -> None:
        """Apply stylesheet based on current configuration."""
        self._combo.setStyleSheet(_get_combobox_stylesheet(size=self._size))

    def _load_items(self) -> None:
        """Load items into the combo box."""
        self._combo.clear()

        for item in self._items:
            label = item.get("label", str(item.get("value", "")))
            value = item.get("value")
            icon_name = item.get("icon")

            if icon_name:
                icon = get_icon(icon_name, size=_get_icon_size(self._size), state="normal")
                self._combo.addItem(icon, label, value)
            else:
                self._combo.addItem(label, value)

    @Slot(str)
    def _on_text_changed(self, text: str) -> None:
        """
        Handle text change.

        Args:
            text: New text value
        """
        self.edit_text_changed.emit(text)

    @Slot(int)
    def _on_current_index_changed(self, index: int) -> None:
        """
        Handle current index change from dropdown selection.

        Args:
            index: New current index
        """
        if index >= 0:
            value = self._combo.itemData(index)
            self.current_changed.emit(value)
        else:
            # User typed custom text
            self.current_changed.emit(self._combo.currentText())

    def set_items(self, items: list[SelectItem] | list[str]) -> None:
        """
        Set the items list.

        Args:
            items: List of item dicts or strings for dropdown
        """
        current_text = self.get_value()
        self._items = self._normalize_items(items)
        self._load_items()

        # Restore text
        if current_text:
            self.set_value(current_text)

    def get_items(self) -> list[SelectItem]:
        """Get the items list."""
        return self._items.copy()

    def set_value(self, value: str) -> None:
        """
        Set the text value programmatically.

        Args:
            value: Text value to set
        """
        self._combo.setCurrentText(value)

    def get_value(self) -> str:
        """Get current text value."""
        return self._combo.currentText()

    def set_placeholder(self, text: str) -> None:
        """
        Set placeholder text.

        Args:
            text: Placeholder text
        """
        self._combo.setPlaceholderText(text)

    def get_placeholder(self) -> str:
        """Get placeholder text."""
        return self._placeholder_text

    def set_size(self, size: InputSize) -> None:
        """
        Change the input size.

        Args:
            size: New size variant ("sm", "md", "lg")
        """
        if self._size != size:
            self._size = size
            self._combo.setFixedHeight(_get_input_height(size))
            self._load_items()  # Reload icons with new size
            self._apply_stylesheet()

    def get_size(self) -> InputSize:
        """Get current size variant."""
        return self._size

    def set_enabled(self, enabled: bool) -> None:
        """
        Set enabled state.

        Args:
            enabled: Whether widget is enabled
        """
        self._combo.setEnabled(enabled)

    def is_enabled(self) -> bool:
        """Check if widget is enabled."""
        return self._combo.isEnabled()


# =============================================================================
# ITEM LIST
# =============================================================================


class ItemList(QListWidget):
    """
    List widget with v2 styling and optional icons.

    Wraps QListWidget with support for icons and multi-select.

    Features:
    - Items with value, label, and optional icon
    - Single or multi-select mode
    - THEME_V2 colors throughout
    - Selection tracking by value

    Signals:
        selection_changed(list): Emitted when selection changes (list of selected values)

    Example:
        from casare_rpa.presentation.canvas.ui.widgets.primitives.selects import ItemList

        # Single select with icons
        files = ItemList(
            items=[
                {"value": "file1", "label": "Document.txt", "icon": "file"},
                {"value": "file2", "label": "Image.png", "icon": "image"},
            ],
            selected="file1",
            icons_enabled=True,
        )
        files.selection_changed.connect(lambda vals: print(f"Selected: {vals}"))

        # Multi-select
        options = ItemList(
            items=[
                {"value": "1", "label": "Option 1"},
                {"value": "2", "label": "Option 2"},
                {"value": "3", "label": "Option 3"},
            ],
            selected=["1", "3"],
            multi_select=True,
        )
    """

    selection_changed = Signal(list)

    def __init__(
        self,
        items: list[SelectItem] | None = None,
        selected: Any | list[Any] | None = None,
        *,
        icons_enabled: bool = False,
        multi_select: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize ItemList.

        Args:
            items: List of item dicts with keys: value, label, icon (optional)
            selected: Initial selected value(s) - single value or list for multi-select
            icons_enabled: Whether to show icons for items
            multi_select: Enable multi-selection mode
            parent: Parent widget
        """
        super().__init__(parent)

        self._items: list[SelectItem] = items or []
        self._icons_enabled = icons_enabled
        self._multi_select = multi_select
        self._is_updating_selection = False

        # Configure selection mode
        self.setSelectionMode(
            QListWidget.SelectionMode.MultiSelection
            if multi_select
            else QListWidget.SelectionMode.SingleSelection
        )

        self._setup_ui()
        self._connect_signals()
        self._apply_stylesheet()

        # Load items
        self._load_items()

        # Set initial selection
        if selected is not None:
            self.set_selected(selected)

    def _setup_ui(self) -> None:
        """Set up the UI elements."""
        # Set alternating row colors for better readability
        self.setAlternatingRowColors(False)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self.itemSelectionChanged.connect(self._on_selection_changed)

    def _apply_stylesheet(self) -> None:
        """Apply v2 stylesheet."""
        self.setStyleSheet(_get_listitem_stylesheet())

    def _load_items(self) -> None:
        """Load items into the list widget."""
        self.clear()

        for item in self._items:
            label = item.get("label", str(item.get("value", "")))
            value = item.get("value")
            icon_name = item.get("icon")

            list_item = QListWidgetItem(label)
            list_item.setData(Qt.ItemDataRole.UserRole, value)

            # Set icon if enabled and available
            if self._icons_enabled and icon_name:
                icon = get_icon(icon_name, size=16, state="normal")
                list_item.setIcon(icon)

            self.addItem(list_item)

    def _on_selection_changed(self) -> None:
        """Handle selection change."""
        if self._is_updating_selection:
            return

        selected_values = self.get_selected()
        self.selection_changed.emit(selected_values)

    def set_items(self, items: list[SelectItem]) -> None:
        """
        Set the items list.

        Args:
            items: List of item dicts with keys: value, label, icon (optional)
        """
        current_selected = self.get_selected()
        self._items = items
        self._load_items()

        # Try to restore previous selection
        if current_selected:
            self.set_selected(current_selected)

    def get_items(self) -> list[SelectItem]:
        """Get the items list."""
        return self._items.copy()

    def set_selected(self, selected: Any | list[Any] | None) -> None:
        """
        Set selected item(s).

        Args:
            selected: Single value or list of values to select
        """
        self._is_updating_selection = True

        # Clear current selection
        self.clearSelection()

        if selected is None:
            self._is_updating_selection = False
            return

        # Normalize to list
        values_to_select = [selected] if not isinstance(selected, list) else selected

        # Find and select items
        for i in range(self.count()):
            item = self.item(i)
            item_value = item.data(Qt.ItemDataRole.UserRole)
            if item_value in values_to_select:
                item.setSelected(True)

        self._is_updating_selection = False

    def get_selected(self) -> list[Any]:
        """
        Get list of selected values.

        Returns:
            List of selected values (empty if none selected)
        """
        selected_items = self.selectedItems()
        return [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]

    def add_item(self, item: SelectItem) -> None:
        """
        Add a single item to the list.

        Args:
            item: Item dict with keys: value, label, icon (optional)
        """
        self._items.append(item)

        label = item.get("label", str(item.get("value", "")))
        value = item.get("value")
        icon_name = item.get("icon")

        list_item = QListWidgetItem(label)
        list_item.setData(Qt.ItemDataRole.UserRole, value)

        if self._icons_enabled and icon_name:
            icon = get_icon(icon_name, size=16, state="normal")
            list_item.setIcon(icon)

        self.addItem(list_item)

    def remove_item(self, value: Any) -> None:
        """
        Remove an item by value.

        Args:
            value: Value of item to remove
        """
        # Find and remove item
        for i in range(self.count()):
            item = self.item(i)
            item_value = item.data(Qt.ItemDataRole.UserRole)
            if item_value == value:
                self.takeItem(i)
                # Remove from internal list
                self._items = [it for it in self._items if it.get("value") != value]
                break

    def clear_items(self) -> None:
        """Clear all items."""
        self._items.clear()
        self.clear()

    def set_multi_select(self, multi: bool) -> None:
        """
        Set multi-select mode.

        Args:
            multi: Whether to enable multi-selection
        """
        if self._multi_select != multi:
            self._multi_select = multi
            self.setSelectionMode(
                QListWidget.SelectionMode.MultiSelection
                if multi
                else QListWidget.SelectionMode.SingleSelection
            )

    def is_multi_select(self) -> bool:
        """Check if multi-select mode is enabled."""
        return self._multi_select

    def set_icons_enabled(self, enabled: bool) -> None:
        """
        Set whether icons are shown for items.

        Args:
            enabled: Whether to show icons
        """
        if self._icons_enabled != enabled:
            self._icons_enabled = enabled
            self._load_items()

    def is_icons_enabled(self) -> bool:
        """Check if icons are enabled."""
        return self._icons_enabled


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "InputSize",
    "SelectItem",
    "Select",
    "ComboBox",
    "ItemList",
]

