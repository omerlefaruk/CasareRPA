"""
Command Palette for CasareRPA.

A VS Code-style command palette for quick access to all actions via keyboard.
"""

from collections.abc import Callable
from dataclasses import dataclass

from loguru import logger
from PySide6.QtCore import QEvent, Qt, Signal, Slot
from PySide6.QtGui import QAction, QKeyEvent
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS
from casare_rpa.presentation.canvas.theme_system.helpers import (
    margin_none,
    set_fixed_width,
    set_spacing,
)


@dataclass
class CommandItem:
    """Represents a command in the palette."""

    name: str
    description: str
    shortcut: str
    action: QAction | None
    callback: Callable | None
    category: str = "General"


class CommandPalette(QDialog):
    """
    VS Code-style command palette for quick action access.

    Features:
    - Fuzzy search through all commands
    - Keyboard navigation (Up/Down/Enter/Escape)
    - Shows shortcuts for each command
    - Categorized commands

    Signals:
        command_executed: Emitted when a command is executed (command_name: str)
    """

    command_executed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the command palette.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self._commands: list[CommandItem] = []
        self._filtered_commands: list[CommandItem] = []

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle("Command Palette")
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup
        )
        self.setModal(True)
        set_fixed_width(self, TOKENS.sizes.dialog_md_width)
        self.setMaximumHeight(TOKENS.sizes.dialog_height_md)

        layout = QVBoxLayout(self)
        margin_none(layout)
        set_spacing(layout, TOKENS.spacing.xs)

        # Search input
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Type to search commands...")
        self._search_input.textChanged.connect(self._on_search_changed)
        self._search_input.installEventFilter(self)
        layout.addWidget(self._search_input)

        # Results list
        self._results_list = QListWidget()
        self._results_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._results_list.itemClicked.connect(self._on_item_clicked)
        self._results_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._results_list)

        # Hint label
        self._hint_label = QLabel("Enter to execute | Esc to close")
        self._hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._hint_label)

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet(
            f"""
            QDialog {{
                background: {THEME.bg_surface};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.md}px;
            }}
            QLineEdit {{
                background: {THEME.bg_canvas};
                border: none;
                border-bottom: 1px solid {THEME.border};
                color: {THEME.text_primary};
                padding: {TOKENS.spacing.lg}px 16px;
                font-size: {TOKENS.typography.display_m}px;
            }}
            QLineEdit:focus {{
                border-bottom: 2px solid {THEME.border_focus};
            }}
            QListWidget {{
                background: {THEME.bg_surface};
                border: none;
                color: {THEME.text_secondary};
                font-size: {TOKENS.typography.body}px;
                outline: none;
            }}
            QListWidget::item {{
                padding: {TOKENS.spacing.md}px 16px;
                border: none;
            }}
            QListWidget::item:selected {{
                background: {THEME.bg_selected};
                color: {THEME.text_primary};
            }}
            QListWidget::item:hover:!selected {{
                background: {THEME.bg_hover};
            }}
            QLabel {{
                background: {THEME.bg_surface};
                color: {THEME.text_muted};
                padding: {TOKENS.spacing.sm}px;
                font-size: {TOKENS.typography.caption}px;
            }}
            """
        )

    def eventFilter(self, obj, event) -> bool:
        """Handle keyboard navigation in search input."""
        if obj == self._search_input and event.type() == QEvent.Type.KeyPress:
            key_event = event
            key = key_event.key()

            if key == Qt.Key.Key_Down:
                self._move_selection(1)
                return True
            elif key == Qt.Key.Key_Up:
                self._move_selection(-1)
                return True
            elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                self._execute_selected()
                return True
            elif key == Qt.Key.Key_Escape:
                self.close()
                return True

        return super().eventFilter(obj, event)

    def _move_selection(self, delta: int) -> None:
        """Move the selection up or down."""
        current = self._results_list.currentRow()
        count = self._results_list.count()
        if count == 0:
            return

        new_row = (current + delta) % count
        self._results_list.setCurrentRow(new_row)

    @Slot(str)
    def _on_search_changed(self, text: str) -> None:
        """Handle search text changes."""
        self._filter_commands(text)
        self._update_results_list()

    def _filter_commands(self, query: str) -> None:
        """Filter commands based on search query."""
        if not query:
            self._filtered_commands = self._commands.copy()
            return

        query_lower = query.lower()
        scored_commands = []

        for cmd in self._commands:
            # Calculate score based on fuzzy matching
            score = self._calculate_match_score(query_lower, cmd.name.lower())
            if score > 0:
                scored_commands.append((score, cmd))
            elif query_lower in cmd.description.lower():
                scored_commands.append((50, cmd))  # Lower score for description match
            elif query_lower in cmd.category.lower():
                scored_commands.append((30, cmd))  # Even lower for category match

        # Sort by score (highest first)
        scored_commands.sort(key=lambda x: x[0], reverse=True)
        self._filtered_commands = [cmd for _, cmd in scored_commands]

    def _calculate_match_score(self, query: str, text: str) -> int:
        """
        Calculate a fuzzy match score.

        Returns:
            Score (higher = better match), 0 if no match
        """
        if query == text:
            return 100  # Exact match
        if text.startswith(query):
            return 90  # Prefix match
        if query in text:
            return 70  # Substring match

        # Fuzzy matching - check if all query chars appear in order
        query_idx = 0
        consecutive_bonus = 0
        last_match_idx = -1

        for i, char in enumerate(text):
            if query_idx < len(query) and char == query[query_idx]:
                if i == last_match_idx + 1:
                    consecutive_bonus += 10
                last_match_idx = i
                query_idx += 1

        if query_idx == len(query):
            # All chars found in order
            return 40 + consecutive_bonus
        return 0

    def _update_results_list(self) -> None:
        """Update the results list with filtered commands."""
        self._results_list.clear()

        for cmd in self._filtered_commands[:20]:  # Limit to 20 results
            item = QListWidgetItem()

            # Create custom widget for the item
            widget = QWidget()
            layout = QHBoxLayout(widget)
            set_margins(layout, (4, 2, 4, 2))
            set_spacing(layout, 8)

            # Command name
            name_label = QLabel(cmd.name)
            name_label.setStyleSheet(f"color: {THEME.text_primary}; font-weight: bold;")
            layout.addWidget(name_label)

            # Description
            if cmd.description:
                desc_label = QLabel(f"- {cmd.description}")
                desc_label.setStyleSheet(f"color: {THEME.text_muted};")
                layout.addWidget(desc_label)

            layout.addStretch()

            # Shortcut
            if cmd.shortcut:
                shortcut_label = QLabel(cmd.shortcut)
                shortcut_label.setStyleSheet(
                    f"""
                    background: {THEME.bg_component};
                    color: {THEME.text_secondary};
                    border: 1px solid {THEME.border};
                    padding: 2px 6px;
                    border-radius: {TOKENS.radius.sm}px;
                    font-family: monospace;
                    """
                )
                layout.addWidget(shortcut_label)

            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, cmd)

            self._results_list.addItem(item)
            self._results_list.setItemWidget(item, widget)

        # Select first item
        if self._results_list.count() > 0:
            self._results_list.setCurrentRow(0)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle item click - select but don't execute."""
        pass

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle item double-click - execute command."""
        self._execute_selected()

    def _execute_selected(self) -> None:
        """Execute the currently selected command."""
        current_item = self._results_list.currentItem()
        if not current_item:
            return

        cmd = current_item.data(Qt.ItemDataRole.UserRole)
        if not cmd:
            return

        self.close()

        # Execute the command
        try:
            if cmd.action and cmd.action.isEnabled():
                cmd.action.trigger()
                self.command_executed.emit(cmd.name)
                logger.debug(f"Command palette executed: {cmd.name}")
            elif cmd.callback:
                cmd.callback()
                self.command_executed.emit(cmd.name)
                logger.debug(f"Command palette callback executed: {cmd.name}")
        except Exception as e:
            logger.error(f"Command palette execution error: {e}")

    # ==================== Public API ====================

    def register_action(
        self, action: QAction, category: str = "General", description: str = ""
    ) -> None:
        """
        Register a QAction with the command palette.

        Args:
            action: The action to register
            category: Category for grouping
            description: Optional description override
        """
        # Get shortcut text
        shortcuts = action.shortcuts()
        shortcut_text = shortcuts[0].toString() if shortcuts else ""

        cmd = CommandItem(
            name=action.text().replace("&", ""),  # Remove mnemonic
            description=description or action.statusTip(),
            shortcut=shortcut_text,
            action=action,
            callback=None,
            category=category,
        )
        self._commands.append(cmd)

    def register_callback(
        self,
        name: str,
        callback: Callable,
        shortcut: str = "",
        description: str = "",
        category: str = "General",
    ) -> None:
        """
        Register a custom callback with the command palette.

        Args:
            name: Command name
            callback: Function to call
            shortcut: Display shortcut text
            description: Command description
            category: Category for grouping
        """
        cmd = CommandItem(
            name=name,
            description=description,
            shortcut=shortcut,
            action=None,
            callback=callback,
            category=category,
        )
        self._commands.append(cmd)

    def clear_commands(self) -> None:
        """Clear all registered commands."""
        self._commands.clear()
        self._filtered_commands.clear()

    def show_palette(self) -> None:
        """Show the command palette."""
        # Reset search
        self._search_input.clear()
        self._filter_commands("")
        self._update_results_list()

        # Position at center-top of parent
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + 100  # 100px from top
            self.move(x, y)

        self.show()
        self._search_input.setFocus()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
