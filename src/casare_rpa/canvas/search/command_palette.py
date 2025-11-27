"""
Command Palette for CasareRPA.

A VS Code-style command palette for quick access to all actions via keyboard.
"""

from typing import Optional, List, Dict, Callable, Any
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QWidget,
    QHBoxLayout,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QKeySequence, QAction, QFont, QKeyEvent
from loguru import logger


@dataclass
class CommandItem:
    """Represents a command in the palette."""
    name: str
    description: str
    shortcut: str
    action: Optional[QAction]
    callback: Optional[Callable]
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

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the command palette.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self._commands: List[CommandItem] = []
        self._filtered_commands: List[CommandItem] = []

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle("Command Palette")
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Popup
        )
        self.setModal(True)
        self.setFixedWidth(600)
        self.setMaximumHeight(400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

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
        self.setStyleSheet("""
            QDialog {
                background: #252525;
                border: 1px solid #4a4a4a;
                border-radius: 8px;
            }
            QLineEdit {
                background: #2b2b2b;
                border: none;
                border-bottom: 1px solid #4a4a4a;
                color: #ffffff;
                padding: 12px 16px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-bottom: 2px solid #4a8aaf;
            }
            QListWidget {
                background: #252525;
                border: none;
                color: #e0e0e0;
                font-size: 12px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 16px;
                border: none;
            }
            QListWidget::item:selected {
                background: #3a5a7a;
            }
            QListWidget::item:hover:!selected {
                background: #303030;
            }
            QLabel {
                background: #2b2b2b;
                color: #666666;
                padding: 6px;
                font-size: 10px;
            }
        """)

    def eventFilter(self, obj, event) -> bool:
        """Handle keyboard navigation in search input."""
        if obj == self._search_input and event.type() == event.Type.KeyPress:
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
            layout.setContentsMargins(4, 2, 4, 2)
            layout.setSpacing(8)

            # Command name
            name_label = QLabel(cmd.name)
            name_label.setStyleSheet("color: #e0e0e0; font-weight: bold;")
            layout.addWidget(name_label)

            # Description
            if cmd.description:
                desc_label = QLabel(f"- {cmd.description}")
                desc_label.setStyleSheet("color: #888888;")
                layout.addWidget(desc_label)

            layout.addStretch()

            # Shortcut
            if cmd.shortcut:
                shortcut_label = QLabel(cmd.shortcut)
                shortcut_label.setStyleSheet("""
                    background: #3a3a3a;
                    color: #a0a0a0;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: monospace;
                """)
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
        self,
        action: QAction,
        category: str = "General",
        description: str = ""
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
            category=category
        )
        self._commands.append(cmd)

    def register_callback(
        self,
        name: str,
        callback: Callable,
        shortcut: str = "",
        description: str = "",
        category: str = "General"
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
            category=category
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
