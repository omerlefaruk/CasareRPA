"""
Hotkey manager dialog for viewing and customizing keyboard shortcuts.

This module provides a dialog for users to view, edit, and customize
all keyboard shortcuts in the application.
"""

from typing import Dict
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QAction
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QPushButton,
    QLabel,
    QHeaderView,
    QMessageBox,
)


class HotkeyEditor(QDialog):
    """Dialog for editing a single hotkey."""

    hotkey_changed = Signal(str)  # Emits the new key sequence as string

    def __init__(self, action_name: str, current_shortcut: str, parent=None):
        """
        Initialize hotkey editor dialog.

        Args:
            action_name: Name of the action being edited
            current_shortcut: Current keyboard shortcut
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(f"Edit Hotkey - {action_name}")
        self.setModal(True)
        self._new_shortcut = current_shortcut

        self._setup_ui()

    def _setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)

        # Instruction label
        label = QLabel("Press the key combination you want to use:")
        layout.addWidget(label)

        # Key sequence display
        self._key_display = QLineEdit()
        self._key_display.setReadOnly(True)
        self._key_display.setPlaceholderText("Press keys...")
        self._key_display.setText(self._new_shortcut)
        layout.addWidget(self._key_display)

        # Info label
        info_label = QLabel("Tip: Press Escape to clear the shortcut")
        info_label.setStyleSheet("color: #888;")
        layout.addWidget(info_label)

        # Buttons
        button_layout = QHBoxLayout()

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_shortcut)
        button_layout.addWidget(clear_btn)

        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._accept)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)

        self.resize(400, 150)

    def keyPressEvent(self, event):
        """Capture key press events."""
        key = event.key()

        # Ignore modifier-only keys
        if key in (
            Qt.Key.Key_Control,
            Qt.Key.Key_Shift,
            Qt.Key.Key_Alt,
            Qt.Key.Key_Meta,
        ):
            return

        # Clear on Escape
        if key == Qt.Key.Key_Escape:
            self._clear_shortcut()
            return

        # Build key sequence from event - use .value to get the integer value
        modifiers = event.modifiers()
        key_sequence = QKeySequence(key | modifiers.value)
        self._new_shortcut = key_sequence.toString()
        self._key_display.setText(self._new_shortcut)

    def _clear_shortcut(self):
        """Clear the shortcut."""
        self._new_shortcut = ""
        self._key_display.setText("")

    def _accept(self):
        """Accept the new shortcut."""
        self.hotkey_changed.emit(self._new_shortcut)
        self.accept()

    def get_shortcut(self) -> str:
        """Get the new shortcut string."""
        return self._new_shortcut


class HotkeyManagerDialog(QDialog):
    """Dialog for managing all application hotkeys."""

    def __init__(self, actions: Dict[str, QAction], parent=None):
        """
        Initialize hotkey manager dialog.

        Args:
            actions: Dictionary mapping action names to QAction objects
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts")
        self.setModal(True)

        self._actions = actions
        self._original_shortcuts = {}

        # Store original shortcuts
        for name, action in actions.items():
            shortcuts = action.shortcuts()
            if shortcuts:
                self._original_shortcuts[name] = [s.toString() for s in shortcuts]
            else:
                self._original_shortcuts[name] = []

        self._setup_ui()
        self._populate_table()

    def _setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)

        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Type to filter commands...")
        self._search_input.textChanged.connect(self._filter_table)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self._search_input)
        layout.addLayout(search_layout)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Command", "Shortcut", "Description"])
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self._table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.doubleClicked.connect(self._edit_hotkey)
        layout.addWidget(self._table)

        # Info label
        info_label = QLabel("Double-click a row to edit its shortcut")
        info_label.setStyleSheet("color: #888;")
        layout.addWidget(info_label)

        # Buttons
        button_layout = QHBoxLayout()

        reset_btn = QPushButton("Reset All")
        reset_btn.clicked.connect(self._reset_all)
        button_layout.addWidget(reset_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.resize(800, 600)

    def _populate_table(self):
        """Populate the table with actions."""
        self._table.setRowCount(0)

        for name, action in sorted(self._actions.items()):
            row = self._table.rowCount()
            self._table.insertRow(row)

            # Command name (cleaned up)
            display_name = action.text().replace("&", "")
            self._table.setItem(row, 0, QTableWidgetItem(display_name))

            # Shortcut
            shortcuts = action.shortcuts()
            if shortcuts:
                shortcut_text = ", ".join([s.toString() for s in shortcuts])
            else:
                shortcut_text = ""
            self._table.setItem(row, 1, QTableWidgetItem(shortcut_text))

            # Description
            description = action.statusTip()
            self._table.setItem(row, 2, QTableWidgetItem(description))

            # Store action name in first column
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, name)

    def _filter_table(self):
        """Filter table based on search input."""
        search_text = self._search_input.text().lower()

        for row in range(self._table.rowCount()):
            command = self._table.item(row, 0).text().lower()
            shortcut = self._table.item(row, 1).text().lower()
            description = self._table.item(row, 2).text().lower()

            matches = (
                search_text in command
                or search_text in shortcut
                or search_text in description
            )

            self._table.setRowHidden(row, not matches)

    def _edit_hotkey(self, index):
        """Edit a hotkey when row is double-clicked."""
        row = index.row()
        action_name = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        action = self._actions[action_name]

        # Get current shortcut
        shortcuts = action.shortcuts()
        current_shortcut = shortcuts[0].toString() if shortcuts else ""

        # Show editor dialog
        display_name = action.text().replace("&", "")
        editor = HotkeyEditor(display_name, current_shortcut, self)

        if editor.exec() == QDialog.DialogCode.Accepted:
            new_shortcut = editor.get_shortcut()

            # Check for conflicts
            if new_shortcut and self._check_conflict(action_name, new_shortcut):
                return

            # Update action
            if new_shortcut:
                action.setShortcut(QKeySequence(new_shortcut))
            else:
                action.setShortcut(QKeySequence())

            # Update table
            self._table.item(row, 1).setText(new_shortcut)

            # Save to persistent storage
            self._save_hotkeys()

    def _check_conflict(self, current_action: str, new_shortcut: str) -> bool:
        """
        Check if the new shortcut conflicts with existing shortcuts.

        Args:
            current_action: Name of action being edited
            new_shortcut: New shortcut string

        Returns:
            True if there's a conflict, False otherwise
        """
        for name, action in self._actions.items():
            if name == current_action:
                continue

            shortcuts = action.shortcuts()
            for shortcut in shortcuts:
                if shortcut.toString() == new_shortcut:
                    display_name = action.text().replace("&", "")
                    QMessageBox.warning(
                        self,
                        "Shortcut Conflict",
                        f"The shortcut '{new_shortcut}' is already used by:\n{display_name}\n\n"
                        f"Please choose a different shortcut.",
                    )
                    return True

        return False

    def _reset_all(self):
        """Reset all shortcuts to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset All Shortcuts",
            "Are you sure you want to reset all keyboard shortcuts to their defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Restore original shortcuts
            for name, action in self._actions.items():
                original = self._original_shortcuts.get(name, [])
                if original:
                    sequences = [QKeySequence(s) for s in original]
                    action.setShortcuts(sequences)
                else:
                    action.setShortcut(QKeySequence())

            # Save to persistent storage
            self._save_hotkeys()

            # Refresh table
            self._populate_table()
            self._filter_table()

    def _save_hotkeys(self):
        """Save current hotkeys to persistent storage."""
        from ...utils.hotkey_settings import get_hotkey_settings

        settings = get_hotkey_settings()

        # Update settings with current shortcuts
        for action_name, action in self._actions.items():
            shortcuts = action.shortcuts()
            shortcut_strings = [s.toString() for s in shortcuts] if shortcuts else []
            settings.set_shortcuts(action_name, shortcut_strings)

        # Save to file
        settings.save()
