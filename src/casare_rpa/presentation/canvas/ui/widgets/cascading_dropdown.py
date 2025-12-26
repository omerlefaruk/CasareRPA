"""
Cascading Dropdown Base Class for CasareRPA.

Provides a base class for dropdowns that depend on parent values:
- Loading state with spinner
- Cache with configurable TTL
- Parent value dependency
- Async data fetching
- Error handling

Used as base for Google Sheets picker, Drive file picker, etc.
"""

from __future__ import annotations

import asyncio
import time
from abc import abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

from loguru import logger
from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system.helpers import (
    set_fixed_size,
    set_min_size,
    set_min_width,
    set_spacing,
)
from casare_rpa.presentation.canvas.theme_system.tokens import TOKENS
from casare_rpa.presentation.canvas.ui.theme import THEME

# Type variable for item data
T = TypeVar("T")


class GraphicsSceneComboBox(QComboBox):
    """
    QComboBox subclass that works reliably in QGraphicsProxyWidget.

    Ensures popup window flags are set correctly when shown in graphics scenes.
    """

    def showPopup(self):
        """Override to ensure popup appears on top in graphics scene."""
        try:
            popup = self.view().window()
            popup.setWindowFlags(
                Qt.WindowType.Popup
                | Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
            )
        except Exception:
            pass
        super().showPopup()


@dataclass
class DropdownItem:
    """Represents an item in the dropdown."""

    id: str
    label: str
    data: dict[str, Any] | None = None

    def __post_init__(self):
        if self.data is None:
            self.data = {}


@dataclass
class CacheEntry:
    """Cache entry with TTL tracking."""

    items: list[DropdownItem]
    timestamp: float = field(default_factory=time.time)

    def is_expired(self, ttl_seconds: float) -> bool:
        """Check if cache entry is expired."""
        return (time.time() - self.timestamp) > ttl_seconds


class FetchWorker(QObject):
    """Background worker for async data fetching."""

    finished = Signal(object, str)  # items or None, error message
    progress = Signal(str)  # status message

    def __init__(
        self,
        fetch_func: Callable[..., list[DropdownItem]],
        args: tuple = (),
        kwargs: dict | None = None,
    ) -> None:
        super().__init__()
        self.fetch_func = fetch_func
        self.args = args
        self.kwargs = kwargs or {}

    def run(self) -> None:
        """Execute the fetch function."""
        try:
            self.progress.emit("Loading...")

            # Check if fetch_func is a coroutine
            if asyncio.iscoroutinefunction(self.fetch_func):
                # Run async function
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    items = loop.run_until_complete(self.fetch_func(*self.args, **self.kwargs))
                finally:
                    loop.close()
            else:
                # Run sync function
                items = self.fetch_func(*self.args, **self.kwargs)

            self.finished.emit(items, "")

        except Exception as e:
            logger.error(f"Fetch worker error: {e}")
            self.finished.emit(None, str(e))


class FetchThread(QThread):
    """Thread wrapper for fetch worker."""

    finished = Signal(object, str)
    progress = Signal(str)

    def __init__(
        self,
        fetch_func: Callable[..., list[DropdownItem]],
        args: tuple = (),
        kwargs: dict | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._worker = FetchWorker(fetch_func, args, kwargs)

    def run(self):
        self._worker.finished.connect(self.finished.emit)
        self._worker.progress.connect(self.progress.emit)
        self._worker.run()


# Styles - Using THEME and TOKENS
DROPDOWN_STYLE = f"""
QComboBox {{
    background: {THEME.input_bg};
    border: 1px solid {THEME.border_light};
    border-radius: {TOKENS.radii.sm}px;
    padding: {TOKENS.spacing.xs}px {TOKENS.spacing.md}px;
    padding-right: 24px;
    color: {THEME.text_primary};
    min-width: 140px;
    min-height: {TOKENS.sizes.combo_height}px;
}}
QComboBox:hover {{
    border-color: {THEME.accent};
    background: {THEME.hover};
}}
QComboBox:focus {{
    border-color: {THEME.accent};
}}
QComboBox:disabled {{
    background: {THEME.bg_medium};
    color: {THEME.text_disabled};
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: {TOKENS.sizes.combo_dropdown_width}px;
    border-left: none;
    background: transparent;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {THEME.text_primary};
    margin-right: {TOKENS.spacing.xs}px;
}}
QComboBox::down-arrow:hover {{
    border-top-color: #ffffff;
}}
QComboBox QAbstractItemView {{
    background: {THEME.bg_dark};
    border: 1px solid {THEME.border};
    selection-background-color: {THEME.selected};
    outline: none;
    padding: {TOKENS.spacing.xs}px;
}}
QComboBox QAbstractItemView::item {{
    padding: {TOKENS.spacing.sm}px {TOKENS.spacing.md}px;
    min-height: {TOKENS.sizes.row_height_compact}px;
}}
QComboBox QAbstractItemView::item:hover {{
    background: {THEME.hover};
}}
QComboBox QAbstractItemView::item:selected {{
    background: {THEME.selected};
}}
"""

REFRESH_BUTTON_STYLE = f"""
QPushButton {{
    background: {THEME.input_bg};
    border: 1px solid {THEME.border_light};
    border-radius: {TOKENS.radii.sm}px;
    padding: 0px;
    color: {THEME.text_primary};
    font-size: {TOKENS.fonts.xl}px;
    font-weight: bold;
    min-width: {TOKENS.sizes.button_height_md}px;
    min-height: {TOKENS.sizes.button_height_md}px;
}}
QPushButton:hover {{
    background: {THEME.hover};
    border-color: {THEME.accent};
    color: #ffffff;
}}
QPushButton:pressed {{
    background: {THEME.bg_medium};
}}
QPushButton:disabled {{
    background: {THEME.bg_medium};
    color: {THEME.text_disabled};
}}
"""

LOADING_STYLE = f"""
QLabel {{
    color: {THEME.text_secondary};
    font-style: italic;
}}
"""


class CascadingDropdownBase(QWidget):
    """
    Base class for cascading dropdown widgets.

    Features:
    - Loading state with visual indicator
    - Cache with configurable TTL (default 5 minutes)
    - Parent value dependency via set_parent_value()
    - Abstract _fetch_items() method for subclasses
    - Async data fetching in background thread
    - Error handling with retry option

    Signals:
        selection_changed(str): Emitted when selection changes, passes item ID
        loading_started(): Emitted when loading begins
        loading_finished(): Emitted when loading completes
        error_occurred(str): Emitted when an error occurs
    """

    selection_changed = Signal(str)
    loading_started = Signal()
    loading_finished = Signal()
    error_occurred = Signal(str)

    # Cache settings
    DEFAULT_CACHE_TTL = 300.0  # 5 minutes in seconds

    def __init__(
        self,
        parent: QWidget | None = None,
        cache_ttl: float = DEFAULT_CACHE_TTL,
        show_refresh_button: bool = True,
    ) -> None:
        super().__init__(parent)

        self._cache_ttl = cache_ttl
        self._show_refresh_button = show_refresh_button

        self._cache: dict[str, CacheEntry] = {}
        self._parent_value: str | None = None
        self._current_item_id: str | None = None
        self._items: list[DropdownItem] = []
        self._loading = False
        self._fetch_thread: FetchThread | None = None

        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the widget layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(*TOKENS.margins.none)
        set_spacing(layout, TOKENS.spacing.sm)

        # Dropdown - using GraphicsSceneComboBox for proper event handling
        self._combo = GraphicsSceneComboBox()
        set_min_width(self._combo, 140)
        set_min_size(self._combo, 140, TOKENS.sizes.combo_height)
        self._combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        layout.addWidget(self._combo, 1)

        # Loading indicator (replaces combo when loading)
        self._loading_label = QLabel("Loading...")
        set_min_size(self._loading_label, 0, TOKENS.sizes.combo_height)
        self._loading_label.setVisible(False)
        layout.addWidget(self._loading_label)

        # Refresh button with proper alignment
        if self._show_refresh_button:
            self._refresh_btn = QPushButton()
            self._refresh_btn.setToolTip("Refresh items")
            self._refresh_btn.setText("\u21bb")  # Unicode refresh symbol
            btn_size = TOKENS.sizes.button_height_md
            set_fixed_size(self._refresh_btn, btn_size, btn_size)
            self._refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(self._refresh_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        else:
            self._refresh_btn = None

        # Set widget height constraints for consistent appearance
        set_min_size(self, 0, TOKENS.sizes.input_height_md)

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self._combo.setStyleSheet(DROPDOWN_STYLE)
        self._loading_label.setStyleSheet(LOADING_STYLE)
        if self._refresh_btn:
            self._refresh_btn.setStyleSheet(REFRESH_BUTTON_STYLE)

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self._combo.currentIndexChanged.connect(self._on_selection_changed)
        if self._refresh_btn:
            self._refresh_btn.clicked.connect(self._force_refresh)

    # =========================================================================
    # Abstract Methods
    # =========================================================================

    @abstractmethod
    async def _fetch_items(self) -> list[DropdownItem]:
        """
        Fetch items for the dropdown.

        Override this method in subclasses to fetch data from APIs.
        Use self._parent_value to access the parent dropdown's value.

        Returns:
            List of DropdownItem objects.

        Raises:
            Exception: If fetching fails.
        """
        pass

    def _get_cache_key(self) -> str:
        """
        Get the cache key for current state.

        Override if additional context affects the cache key.

        Returns:
            Cache key string.
        """
        return self._parent_value or "__no_parent__"

    # =========================================================================
    # Loading State
    # =========================================================================

    def _set_loading(self, loading: bool) -> None:
        """Set loading state."""
        self._loading = loading
        self._combo.setEnabled(not loading)
        self._loading_label.setVisible(loading)

        if self._refresh_btn:
            self._refresh_btn.setEnabled(not loading)

        if loading:
            self.loading_started.emit()
        else:
            self.loading_finished.emit()

    def is_loading(self) -> bool:
        """Check if currently loading."""
        return self._loading

    # =========================================================================
    # Data Loading
    # =========================================================================

    def _load_items(self, force_refresh: bool = False) -> None:
        """Load items, using cache if available."""
        cache_key = self._get_cache_key()

        # Check cache
        if not force_refresh and cache_key in self._cache:
            entry = self._cache[cache_key]
            if not entry.is_expired(self._cache_ttl):
                self._populate_combo(entry.items)
                return

        # Fetch in background
        self._start_fetch()

    def _start_fetch(self) -> None:
        """Start background fetch."""
        if self._loading:
            return

        self._set_loading(True)

        self._fetch_thread = FetchThread(
            fetch_func=self._fetch_items,
            parent=self,
        )
        self._fetch_thread.finished.connect(self._on_fetch_complete)
        self._fetch_thread.progress.connect(self._on_fetch_progress)
        self._fetch_thread.start()

    def _on_fetch_complete(self, items: list[DropdownItem] | None, error: str) -> None:
        """Handle fetch completion."""
        self._set_loading(False)
        self._fetch_thread = None

        if error:
            logger.error(f"Fetch failed: {error}")
            self._show_error(error)
            self.error_occurred.emit(error)
            return

        if items is None:
            items = []

        # Update cache
        cache_key = self._get_cache_key()
        self._cache[cache_key] = CacheEntry(items=items)

        self._populate_combo(items)

    def _on_fetch_progress(self, message: str) -> None:
        """Handle fetch progress."""
        self._loading_label.setText(message)

    def _populate_combo(self, items: list[DropdownItem]) -> None:
        """Populate combo box with items."""
        self._items = items

        self._combo.blockSignals(True)
        self._combo.clear()

        if not items:
            self._combo.addItem("No items available", "")
            self._combo.setToolTip("No items found. Select a credential first or refresh.")
        else:
            for item in items:
                self._combo.addItem(item.label, item.id)
            self._combo.setToolTip(f"{len(items)} items available")

        # Restore selection
        if self._current_item_id:
            index = self._combo.findData(self._current_item_id)
            if index >= 0:
                self._combo.setCurrentIndex(index)

        self._combo.blockSignals(False)

    def _show_error(self, error: str) -> None:
        """Show error in combo box."""
        self._combo.blockSignals(True)
        self._combo.clear()
        self._combo.addItem(f"Error: {error[:30]}...", "")
        self._combo.setToolTip(error)
        self._combo.blockSignals(False)

    def _force_refresh(self) -> None:
        """Force refresh, bypassing cache."""
        self._load_items(force_refresh=True)

    # =========================================================================
    # Selection Handling
    # =========================================================================

    def _on_selection_changed(self, index: int) -> None:
        """Handle combo box selection change."""
        if index < 0:
            return

        item_id = self._combo.itemData(index)

        # Skip empty/error items
        if not item_id:
            return

        self._current_item_id = item_id
        self.selection_changed.emit(item_id)

    # =========================================================================
    # Public API
    # =========================================================================

    def set_parent_value(self, value: str | None) -> None:
        """
        Set the parent dropdown's value.

        This triggers a reload of items based on the new parent value.

        Args:
            value: Parent value (e.g., credential_id, spreadsheet_id)
        """
        if value == self._parent_value:
            return

        self._parent_value = value
        self._current_item_id = None

        if value:
            self._load_items()
        else:
            # Clear if no parent value
            self._combo.blockSignals(True)
            self._combo.clear()
            self._combo.addItem("Select credential first...", "")
            self._combo.setToolTip("Select a Google account to load items")
            self._combo.blockSignals(False)

    def get_parent_value(self) -> str | None:
        """Get the parent dropdown's value."""
        return self._parent_value

    def get_selected_id(self) -> str | None:
        """Get the currently selected item ID."""
        return self._current_item_id

    def set_selected_id(self, item_id: str) -> None:
        """
        Set the selected item by ID.

        Args:
            item_id: ID of the item to select
        """
        index = self._combo.findData(item_id)
        if index >= 0:
            self._combo.setCurrentIndex(index)
            self._current_item_id = item_id
        else:
            # Item not found, store for later
            self._current_item_id = item_id

    def get_selected_item(self) -> DropdownItem | None:
        """Get the currently selected DropdownItem."""
        if not self._current_item_id:
            return None

        for item in self._items:
            if item.id == self._current_item_id:
                return item
        return None

    def get_selected_label(self) -> str:
        """Get the display label of the selected item."""
        return self._combo.currentText()

    def refresh(self) -> None:
        """Refresh the dropdown items (uses cache if valid)."""
        self._load_items()

    def clear_cache(self) -> None:
        """Clear the item cache."""
        self._cache.clear()

    def is_valid(self) -> bool:
        """Check if a valid item is selected."""
        return self._current_item_id is not None and self._current_item_id != ""

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the widget."""
        self._combo.setEnabled(enabled)
        if self._refresh_btn:
            self._refresh_btn.setEnabled(enabled)


class CascadingDropdownWithLabel(QWidget):
    """
    Wrapper that adds a label to any CascadingDropdownBase.

    Usage:
        picker = CascadingDropdownWithLabel(
            label="Sheet:",
            dropdown_class=GoogleSheetPicker,
        )
    """

    selection_changed = Signal(str)

    def __init__(
        self,
        label: str,
        dropdown_class: type,
        parent: QWidget | None = None,
        **dropdown_kwargs,
    ) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(*TOKENS.margins.none)
        set_spacing(layout, TOKENS.spacing.md)

        self._label = QLabel(label)
        self._label.setStyleSheet(f"color: {THEME.text_primary};")
        layout.addWidget(self._label)

        self._dropdown = dropdown_class(**dropdown_kwargs)
        self._dropdown.selection_changed.connect(self.selection_changed.emit)
        layout.addWidget(self._dropdown, 1)

    @property
    def dropdown(self) -> CascadingDropdownBase:
        """Get the underlying dropdown widget."""
        return self._dropdown

    def set_parent_value(self, value: str | None) -> None:
        """Set the parent value."""
        self._dropdown.set_parent_value(value)

    def get_selected_id(self) -> str | None:
        """Get the selected item ID."""
        return self._dropdown.get_selected_id()

    def set_selected_id(self, item_id: str) -> None:
        """Set the selected item ID."""
        self._dropdown.set_selected_id(item_id)

    def refresh(self) -> None:
        """Refresh the dropdown."""
        self._dropdown.refresh()

    def is_valid(self) -> bool:
        """Check if selection is valid."""
        return self._dropdown.is_valid()


__all__ = [
    "CascadingDropdownBase",
    "CascadingDropdownWithLabel",
    "DropdownItem",
    "CacheEntry",
    "GraphicsSceneComboBox",
    "FetchThread",
]
