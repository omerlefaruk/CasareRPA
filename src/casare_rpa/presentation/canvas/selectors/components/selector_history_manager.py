"""
Selector History Manager Component.

Handles selector history management:
- Loading recent selectors
- Saving used selectors
- History dropdown population
- Selector persistence
"""

from dataclasses import dataclass
from typing import Any

from loguru import logger
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QComboBox

from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS


@dataclass
class HistoryEntry:
    """A selector history entry."""

    selector: str
    selector_type: str
    element_tag: str | None = None
    timestamp: float | None = None
    metadata: dict[str, Any] | None = None

    def display_text(self, max_length: int = 50) -> str:
        """Get display text for dropdown."""
        display_selector = self.selector
        if len(display_selector) > max_length:
            display_selector = display_selector[:max_length] + "..."

        tag = self.element_tag or "element"
        return f"{display_selector} ({tag}, {self.selector_type})"


class SelectorHistoryManager(QObject):
    """
    Manages selector history and persistence.

    Provides:
    - Loading recent selectors from persistent storage
    - Saving newly used selectors
    - Populating combo boxes with history
    - History entry retrieval

    Signals:
        history_loaded: Emitted when history is loaded (List[HistoryEntry])
        selector_selected: Emitted when history item is selected (str selector)
        history_saved: Emitted when selector is saved to history
    """

    history_loaded = Signal(list)
    selector_selected = Signal(str)
    history_saved = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._history: list[HistoryEntry] = []
        self._combo_box: QComboBox | None = None
        self._max_entries: int = 15

    def set_combo_box(self, combo_box: QComboBox) -> None:
        """
        Bind a combo box for history display.

        Args:
            combo_box: QComboBox to populate with history
        """
        self._combo_box = combo_box
        combo_box.currentIndexChanged.connect(self._on_combo_index_changed)

    def set_max_entries(self, count: int) -> None:
        """Set maximum number of history entries to display."""
        self._max_entries = max(1, count)

    def load_history(self) -> list[HistoryEntry]:
        """
        Load selector history from persistent storage.

        Returns:
            List of history entries
        """
        try:
            from casare_rpa.presentation.canvas.selectors.selector_history import (
                get_selector_history)

            history = get_selector_history()
            recent = history.get_recent(limit=self._max_entries)

            self._history = [
                HistoryEntry(
                    selector=entry.selector,
                    selector_type=entry.selector_type,
                    element_tag=entry.element_tag,
                    timestamp=getattr(entry, "timestamp", None))
                for entry in recent
            ]

            self._update_combo_box()
            self.history_loaded.emit(self._history)

            logger.debug(f"Loaded {len(self._history)} selectors into history")
            return self._history

        except Exception as e:
            logger.warning(f"Failed to load selector history: {e}")
            return []

    def save_selector(
        self,
        selector: str,
        selector_type: str,
        element_tag: str | None = None,
        metadata: dict[str, Any] | None = None) -> None:
        """
        Save a selector to history.

        Args:
            selector: The selector value
            selector_type: Type of selector
            element_tag: Optional HTML tag name
            metadata: Optional additional metadata
        """
        try:
            from casare_rpa.presentation.canvas.selectors.selector_history import (
                get_selector_history)

            history = get_selector_history()
            history.add(
                selector=selector,
                selector_type=selector_type,
                element_tag=element_tag)

            # Reload to update display
            self.load_history()
            self.history_saved.emit()

            logger.debug(f"Saved selector to history: {selector[:50]}...")

        except Exception as e:
            logger.warning(f"Failed to save selector to history: {e}")

    def get_selector_at_index(self, index: int) -> str | None:
        """
        Get selector value at specified history index.

        Args:
            index: Index in history (0-based, skipping placeholder)

        Returns:
            Selector string or None
        """
        # Account for empty placeholder at index 0
        actual_index = index - 1
        if 0 <= actual_index < len(self._history):
            return self._history[actual_index].selector
        return None

    def get_entry_at_index(self, index: int) -> HistoryEntry | None:
        """
        Get history entry at specified index.

        Args:
            index: Index in combo box

        Returns:
            HistoryEntry or None
        """
        actual_index = index - 1
        if 0 <= actual_index < len(self._history):
            return self._history[actual_index]
        return None

    def clear_history(self) -> None:
        """Clear all history entries."""
        try:
            from casare_rpa.presentation.canvas.selectors.selector_history import (
                get_selector_history)

            history = get_selector_history()
            history.clear()

            self._history = []
            self._update_combo_box()

            logger.info("Cleared selector history")

        except Exception as e:
            logger.warning(f"Failed to clear history: {e}")

    def _update_combo_box(self) -> None:
        """Update the bound combo box with current history."""
        if not self._combo_box:
            return

        self._combo_box.blockSignals(True)
        self._combo_box.clear()

        # Add empty placeholder
        self._combo_box.addItem("")

        for entry in self._history:
            display_text = entry.display_text()
            self._combo_box.addItem(display_text, entry.selector)

        self._combo_box.blockSignals(False)

    def _on_combo_index_changed(self, index: int) -> None:
        """Handle combo box selection change."""
        if index <= 0:
            return

        selector = self.get_selector_at_index(index)
        if selector:
            self.selector_selected.emit(selector)
            logger.debug(f"Selected selector from history: {selector[:50]}...")

    @property
    def history(self) -> list[HistoryEntry]:
        """Get current history entries."""
        return self._history.copy()

    @property
    def count(self) -> int:
        """Get number of history entries."""
        return len(self._history)


def style_history_combo(combo_box: QComboBox) -> None:
    """
    Apply standard styling to a history combo box.

    Args:
        combo_box: The combo box to style
    """
    combo_box.setStyleSheet(f"""
        QComboBox {{
            background: {THEME.bg_surface};
            border: 1px solid {THEME.bg_border};
            border-radius: {TOKENS.radius.sm}px;
            padding: {TOKENS.spacing.xxs}px 24px {TOKENS.spacing.xxs}px {TOKENS.spacing.xs}px;
            color: {THEME.text_primary};
            font-size: {TOKENS.typography.caption}pt;
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: {TOKENS.spacing.xxs}px solid transparent;
            border-right: {TOKENS.spacing.xxs}px solid transparent;
            border-top: 6px solid {THEME.text_muted};
            margin-right: {TOKENS.spacing.xs}px;
        }}
        QComboBox:hover {{
            background: {THEME.bg_elevated};
            border-color: {THEME.bg_component};
        }}
        QComboBox QAbstractItemView {{
            background: {THEME.bg_surface};
            border: 1px solid {THEME.bg_border};
            selection-background-color: {THEME.primary};
            color: {THEME.text_primary};
        }}
    """)
