"""
CommandPaletteV2 - command palette / command launcher popup (Epic 2.3).

This module provides:
- `CommandPaletteV2`: lightweight command palette widget
- `CommandItem`: normalized representation of a QAction
- `CommandCategory`: simple category enum for filtering
- `fuzzy_match`: minimal fuzzy matcher with scoring

The implementation is intentionally small: it supports the public API used by
tests and provides a stable surface for future UI improvements.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QLineEdit, QListWidget, QListWidgetItem, QWidget

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2


def fuzzy_match(query: str, text: str) -> tuple[bool, int]:
    """
    Very small fuzzy matcher with a simple score.

    - If `query` is a substring of `text`, score is the substring start index.
    - Otherwise, score is `len(text) - matched_char_count` when at least one
      character from `query` appears in order within `text`.
    - Returns (-1) score when no match.
    """

    query = (query or "").lower().strip()
    text = (text or "").lower()

    if not query:
        return True, 0

    idx = text.find(query)
    if idx >= 0:
        return True, idx

    matched = 0
    query_index = 0
    for ch in text:
        if query_index >= len(query):
            break
        if ch == query[query_index]:
            matched += 1
            query_index += 1

    if matched <= 0:
        return False, -1

    return True, max(0, len(text) - matched)


class CommandCategory(str, Enum):
    ALL = "ALL"
    FILE = "FILE"
    RUN = "RUN"
    VIEW = "VIEW"

    @classmethod
    def from_action_category(cls, category: object) -> CommandCategory:
        name = ""
        if isinstance(category, str):
            name = category
        else:
            raw_name = getattr(category, "name", "")
            if isinstance(raw_name, str):
                name = raw_name
            else:
                mock_name = getattr(category, "_mock_name", "")
                name = mock_name if isinstance(mock_name, str) else ""

        name = name.upper().strip()
        return cls.__members__.get(name, cls.ALL)

    def badge_text(self) -> str:
        return self.value[:4]

    def badge_color(self) -> str:
        return {
            CommandCategory.ALL: THEME_V2.text_secondary,
            CommandCategory.FILE: THEME_V2.primary,
            CommandCategory.RUN: THEME_V2.success,
            CommandCategory.VIEW: THEME_V2.warning,
        }.get(self, THEME_V2.text_secondary)


@dataclass(slots=True)
class CommandItem:
    id: str
    label: str
    shortcut: str
    category: str
    description: str
    action: QAction

    is_enabled: bool = True
    is_checkable: bool = False
    is_checked: bool = False

    def __post_init__(self) -> None:
        self.is_enabled = bool(self.action.isEnabled())
        self.is_checkable = bool(self.action.isCheckable())
        self.is_checked = bool(self.action.isChecked()) if self.is_checkable else False


class CommandPaletteV2(QWidget):
    DEFAULT_WIDTH = 600
    DEFAULT_HEIGHT = 400
    MIN_WIDTH = 400
    MIN_HEIGHT = 200

    command_executed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._commands: list[CommandItem] = []
        self._filtered_commands: list[tuple[int, CommandItem]] = []
        self._current_filter = ""
        self._category_filter = CommandCategory.ALL
        self._selected_index = -1

        self._search_input: QLineEdit | None = None
        self._list_widget: QListWidget | None = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle("")
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)

        self._search_input = QLineEdit(self)
        self._search_input.setPlaceholderText("Type a command…")
        self._search_input.textChanged.connect(self._on_filter_changed)
        self._search_input.setStyleSheet(self._get_input_style())

        self._list_widget = QListWidget(self)
        self._list_widget.setStyleSheet(self._get_list_style())
        self._list_widget.itemActivated.connect(lambda _: self._confirm_selection())

        # Manual layout (keeps dependencies light)
        self._search_input.setGeometry(12, 12, self.DEFAULT_WIDTH - 24, 36)
        self._list_widget.setGeometry(12, 56, self.DEFAULT_WIDTH - 24, self.DEFAULT_HEIGHT - 68)

    def _on_filter_changed(self, text: str) -> None:
        self._current_filter = text or ""
        self._apply_filter()

    def load_from_action_manager(self, action_manager: object) -> None:
        actions = getattr(action_manager, "get_all_actions", lambda: {})()
        categories = getattr(action_manager, "_categories", {}) or {}

        self._commands = []
        for action_id, action in actions.items():
            if not isinstance(action, QAction):
                continue

            category_obj = categories.get(action_id)
            category = CommandCategory.from_action_category(category_obj).value

            shortcut = action.shortcut().toString() if not action.shortcut().isEmpty() else ""
            item = CommandItem(
                id=str(action_id),
                label=str(action.text() or action_id),
                shortcut=shortcut,
                category=category,
                description=str(action.statusTip() or ""),
                action=action,
            )
            self._commands.append(item)

        self._apply_filter()

    def set_category_filter(self, category: CommandCategory) -> None:
        self._category_filter = category

    def cycle_category_filter(self) -> None:
        order = [
            CommandCategory.ALL,
            CommandCategory.FILE,
            CommandCategory.RUN,
            CommandCategory.VIEW,
        ]
        try:
            idx = order.index(self._category_filter)
        except ValueError:
            idx = 0
        self._category_filter = order[(idx + 1) % len(order)]

    def show_palette(self) -> None:
        self.show()
        if self._search_input is not None:
            self._search_input.setFocus(Qt.FocusReason.PopupFocusReason)

    def _apply_filter(self) -> None:
        query = (self._current_filter or "").strip().lower()

        filtered: list[tuple[int, CommandItem]] = []
        for cmd in self._commands:
            if (
                self._category_filter != CommandCategory.ALL
                and cmd.category != self._category_filter.value
            ):
                continue

            if not query:
                filtered.append((0, cmd))
                continue

            label_l = cmd.label.lower()
            desc_l = cmd.description.lower()
            if query in label_l:
                score = label_l.find(query)
            elif query in desc_l:
                score = desc_l.find(query)
            else:
                continue
            filtered.append((score, cmd))

        filtered.sort(key=lambda t: (t[0], t[1].label.lower()))
        self._filtered_commands = filtered
        self._selected_index = 0 if self._filtered_commands else -1
        self._render_list()

    def _render_list(self) -> None:
        if self._list_widget is None:
            return

        self._list_widget.clear()
        for _, cmd in self._filtered_commands:
            label = cmd.label
            if cmd.shortcut:
                label = f"{label}    {cmd.shortcut}"
            item = QListWidgetItem(label)
            if not cmd.action.isEnabled():
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self._list_widget.addItem(item)

        if self._selected_index >= 0 and self._selected_index < self._list_widget.count():
            self._list_widget.setCurrentRow(self._selected_index)

    def _move_selection(self, delta: int) -> None:
        if not self._filtered_commands:
            return
        count = len(self._filtered_commands)
        if self._selected_index < 0:
            self._selected_index = 0
        else:
            self._selected_index = (self._selected_index + delta) % count

        if self._list_widget is not None:
            self._list_widget.setCurrentRow(self._selected_index)

    def _select_row(self, row: int) -> None:
        if not self._filtered_commands:
            self._selected_index = -1
            return
        self._selected_index = max(0, min(row, len(self._filtered_commands) - 1))
        if self._list_widget is not None:
            self._list_widget.setCurrentRow(self._selected_index)

    def _confirm_selection(self) -> None:
        if self._selected_index < 0 or self._selected_index >= len(self._filtered_commands):
            return

        _, cmd = self._filtered_commands[self._selected_index]
        if not cmd.action.isEnabled():
            return

        self.command_executed.emit(cmd.id)
        cmd.action.trigger()
        self.close()

    def _get_input_style(self) -> str:
        return f"""
        /* THEME_V2 / TOKENS_V2 */
        QLineEdit {{
            background: {THEME_V2.bg_component};
            color: {THEME_V2.text_primary};
            border: 1px solid {THEME_V2.border};
            border-radius: {TOKENS_V2.radius.md}px;
            padding: {TOKENS_V2.spacing.sm}px;
        }}
        QLineEdit:focus {{
            border-color: {THEME_V2.border_focus};
        }}
        """

    def _get_list_style(self) -> str:
        return f"""
        /* THEME_V2 / TOKENS_V2 */
        QListWidget {{
            background: {THEME_V2.bg_surface};
            color: {THEME_V2.text_primary};
            border: 1px solid {THEME_V2.border};
            border-radius: {TOKENS_V2.radius.md}px;
        }}
        QListWidget::item:selected {{
            background: {THEME_V2.bg_selected};
        }}
        """


__all__ = [
    "CommandCategory",
    "CommandItem",
    "CommandPaletteV2",
    "fuzzy_match",
]
