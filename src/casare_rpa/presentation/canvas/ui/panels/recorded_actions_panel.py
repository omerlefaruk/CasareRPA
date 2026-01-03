"""
Recorded Actions Panel for CasareRPA.

Provides a dockable panel for viewing, editing, and managing recorded actions
before converting them to workflow nodes.

Epic 6.1: Migrated to v2 design system (THEME_V2, TOKENS_V2).
"""

from typing import Any

from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDockWidget,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.primitives.buttons import PushButton


class RecordedActionsPanel(QDockWidget):
    """
    Dockable panel for managing recorded actions.

    Features:
    - List view of recorded actions with details
    - Edit/delete individual actions
    - Reorder actions via drag-and-drop
    - Preview workflow before insertion
    - Convert to workflow nodes

    Signals:
        action_selected: Emitted when action is selected (int: index)
        action_deleted: Emitted when action is deleted (int: index)
        actions_reordered: Emitted when actions are reordered (int: from_idx, int: to_idx)
        convert_requested: Emitted when user clicks Convert to Workflow
        clear_requested: Emitted when user clicks Clear All
    """

    action_selected = Signal(int)
    action_deleted = Signal(int)
    actions_reordered = Signal(int, int)
    convert_requested = Signal()
    clear_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the recorded actions panel."""
        super().__init__("Recorded Actions", parent)
        self.setObjectName("RecordedActionsDock")

        self._actions: list[dict[str, Any]] = []

        self._setup_dock()
        self._setup_ui()
        self._update_button_states()

        logger.debug("RecordedActionsPanel initialized")

    def _setup_dock(self) -> None:
        """Configure dock widget properties."""
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
            | Qt.DockWidgetArea.BottomDockWidgetArea
        )
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
            # NO DockWidgetFloatable - dock-only enforcement (v2 requirement)
        )
        self.setMinimumWidth(TOKENS_V2.sizes.panel_min_width)
        self.setMinimumHeight(TOKENS_V2.sizes.dialog_min_height)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(*TOKENS_V2.margin.panel)
        main_layout.setSpacing(TOKENS_V2.spacing.md)

        # Header with count
        header_layout = QHBoxLayout()
        header_layout.setSpacing(TOKENS_V2.spacing.md)

        self._count_label = QLabel("0 actions recorded")
        self._count_label.setStyleSheet(f"color: {THEME_V2.text_secondary}; font-weight: bold;")
        header_layout.addWidget(self._count_label)

        header_layout.addStretch()

        # Clear button
        self._clear_btn = PushButton(text="Clear All", variant="secondary", size="md")
        self._clear_btn.clicked.connect(self._on_clear_clicked)
        self._clear_btn.setToolTip("Clear all recorded actions")
        header_layout.addWidget(self._clear_btn)

        main_layout.addLayout(header_layout)

        # Splitter for list and details
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Actions list
        self._action_list = QListWidget()
        self._action_list.setAlternatingRowColors(True)
        self._action_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._action_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._action_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._action_list.itemSelectionChanged.connect(self._on_selection_changed)
        self._action_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._action_list.customContextMenuRequested.connect(self._show_context_menu)
        self._action_list.model().rowsMoved.connect(self._on_rows_moved)
        splitter.addWidget(self._action_list)

        # Details panel
        details_container = QWidget()
        details_layout = QVBoxLayout(details_container)
        details_layout.setContentsMargins(0, 8, 0, 0)

        details_label = QLabel("Action Details")
        details_label.setStyleSheet(f"color: {THEME_V2.text_muted}; font-weight: bold;")
        details_layout.addWidget(details_label)

        self._details_text = QTextEdit()
        self._details_text.setReadOnly(True)
        self._details_text.setMaximumHeight(TOKENS_V2.sizes.dialog_height_sm)
        self._details_text.setFont(QFont(TOKENS_V2.typography.mono, TOKENS_V2.typography.body))
        self._details_text.setPlaceholderText("Select an action to view details...")
        details_layout.addWidget(self._details_text)

        splitter.addWidget(details_container)
        splitter.setSizes([250, 150])

        main_layout.addWidget(splitter, 1)

        # Preview group
        preview_group = QGroupBox("Workflow Preview")
        preview_layout = QVBoxLayout(preview_group)

        self._preview_text = QTextEdit()
        self._preview_text.setReadOnly(True)
        self._preview_text.setMaximumHeight(TOKENS_V2.sizes.dialog_min_height)
        self._preview_text.setFont(QFont(TOKENS_V2.typography.mono, TOKENS_V2.typography.body))
        self._preview_text.setPlaceholderText(
            "Preview of generated workflow nodes will appear here..."
        )
        preview_layout.addWidget(self._preview_text)

        main_layout.addWidget(preview_group)

        # Convert button
        self._convert_btn = PushButton(
            text="Convert to Workflow",
            variant="primary",
            size="md",
        )
        self._convert_btn.clicked.connect(self._on_convert_clicked)
        self._convert_btn.setToolTip("Generate workflow nodes from recorded actions")
        main_layout.addWidget(self._convert_btn)

        # Info label
        info_label = QLabel(
            "Recorded actions will be converted to workflow nodes "
            "that can be edited and connected in the canvas."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            f"color: {THEME_V2.text_muted}; font-size: {TOKENS_V2.typography.caption}pt;"
        )
        main_layout.addWidget(info_label)

        self.setWidget(container)

    def _update_button_states(self) -> None:
        """Update button enabled states."""
        has_actions = len(self._actions) > 0
        self._clear_btn.setEnabled(has_actions)
        self._convert_btn.setEnabled(has_actions)

    def _on_selection_changed(self) -> None:
        """Handle action selection change."""
        selected_items = self._action_list.selectedItems()
        if not selected_items:
            self._details_text.clear()
            return

        item = selected_items[0]
        index = self._action_list.row(item)

        if 0 <= index < len(self._actions):
            self._show_action_details(self._actions[index])
            self.action_selected.emit(index)

    def _show_action_details(self, action: dict[str, Any]) -> None:
        """Display action details in the details panel."""
        details = []

        details.append(f"Type: {action.get('action_type', 'Unknown')}")

        if action.get("timestamp"):
            details.append(f"Time: {action['timestamp']:.2f}s")

        if action.get("selector"):
            details.append(f"Selector: {action['selector']}")

        if action.get("value"):
            details.append(f"Value: {action['value']}")

        if action.get("url"):
            details.append(f"URL: {action['url']}")

        if action.get("coordinates"):
            coords = action["coordinates"]
            details.append(f"Coordinates: ({coords[0]}, {coords[1]})")

        if action.get("keys"):
            details.append(f"Keys: {'+'.join(action['keys'])}")

        element_info = action.get("element_info", {})
        if element_info:
            details.append("")
            details.append("Element Info:")
            if element_info.get("tag"):
                details.append(f"  Tag: {element_info['tag']}")
            if element_info.get("id"):
                details.append(f"  ID: {element_info['id']}")
            if element_info.get("text"):
                text = element_info["text"][:50]
                details.append(f"  Text: {text}")
            if element_info.get("classes"):
                classes = ", ".join(element_info["classes"][:3])
                details.append(f"  Classes: {classes}")

        self._details_text.setText("\n".join(details))

    def _show_context_menu(self, position) -> None:
        """Show context menu for action list."""
        from functools import partial

        item = self._action_list.itemAt(position)
        if not item:
            return

        index = self._action_list.row(item)

        menu = QMenu(self)

        delete_action = menu.addAction("Delete Action")
        delete_action.triggered.connect(partial(self._delete_action, index))

        menu.addSeparator()

        move_up_action = menu.addAction("Move Up")
        move_up_action.setEnabled(index > 0)
        move_up_action.triggered.connect(partial(self._move_action, index, index - 1))

        move_down_action = menu.addAction("Move Down")
        move_down_action.setEnabled(index < len(self._actions) - 1)
        move_down_action.triggered.connect(partial(self._move_action, index, index + 1))

        menu.exec(self._action_list.mapToGlobal(position))

    def _delete_action(self, index: int) -> None:
        """Delete action at index."""
        if 0 <= index < len(self._actions):
            del self._actions[index]
            self._action_list.takeItem(index)
            self._update_count_label()
            self._update_button_states()
            self._update_preview()
            self.action_deleted.emit(index)
            logger.debug(f"Deleted action at index {index}")

    def _move_action(self, from_index: int, to_index: int) -> None:
        """Move action from one index to another."""
        if 0 <= from_index < len(self._actions) and 0 <= to_index < len(self._actions):
            action = self._actions.pop(from_index)
            self._actions.insert(to_index, action)

            item = self._action_list.takeItem(from_index)
            self._action_list.insertItem(to_index, item)
            self._action_list.setCurrentRow(to_index)

            self._update_preview()
            self.actions_reordered.emit(from_index, to_index)
            logger.debug(f"Moved action from {from_index} to {to_index}")

    def _on_rows_moved(self, parent, start, end, dest, row) -> None:
        """Handle drag-drop row move."""
        if start != row:
            action = self._actions.pop(start)
            new_row = row if row < start else row - 1
            self._actions.insert(new_row, action)
            self._update_preview()
            self.actions_reordered.emit(start, new_row)

    def _on_clear_clicked(self) -> None:
        """Handle clear button click."""
        if not self._actions:
            return

        reply = QMessageBox.question(
            self,
            "Clear Actions",
            f"Clear all {len(self._actions)} recorded actions?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.clear_actions()
            self.clear_requested.emit()

    def _on_convert_clicked(self) -> None:
        """Handle convert button click."""
        if not self._actions:
            QMessageBox.information(
                self,
                "No Actions",
                "No actions to convert. Record some actions first.",
            )
            return

        self.convert_requested.emit()

    def _update_count_label(self) -> None:
        """Update the action count label."""
        count = len(self._actions)
        suffix = "action" if count == 1 else "actions"
        self._count_label.setText(f"{count} {suffix} recorded")

    def _update_preview(self) -> None:
        """Update the workflow preview."""
        if not self._actions:
            self._preview_text.clear()
            return

        preview_lines = []
        for idx, action in enumerate(self._actions[:5]):  # Show first 5
            action_type = action.get("action_type", "Unknown")
            selector = action.get("selector", "")
            if selector and len(selector) > 30:
                selector = selector[:30] + "..."
            preview_lines.append(f"{idx + 1}. {action_type}: {selector}")

        if len(self._actions) > 5:
            preview_lines.append(f"... and {len(self._actions) - 5} more")

        self._preview_text.setText("\n".join(preview_lines))

    def add_action(self, action: dict[str, Any]) -> None:
        """
        Add a recorded action to the list.

        Args:
            action: Action data dictionary
        """
        self._actions.append(action)

        # Create list item
        item = QListWidgetItem()
        action_type = action.get("action_type", "Unknown")
        selector = action.get("selector", action.get("value", ""))
        if selector and len(selector) > 40:
            selector = selector[:40] + "..."

        item.setText(f"{action_type}: {selector}")

        # Set color based on action type
        type_colors = {
            "click": THEME_V2.info,
            "type": THEME_V2.success,
            "navigate": THEME_V2.warning,
            "select": THEME_V2.primary,
            "check": THEME_V2.primary,
            "keyboard": THEME_V2.error,
        }
        color = type_colors.get(action_type.lower(), THEME_V2.text_secondary)
        item.setForeground(QColor(color))

        self._action_list.addItem(item)
        self._action_list.scrollToBottom()

        self._update_count_label()
        self._update_button_states()
        self._update_preview()

    def set_actions(self, actions: list[dict[str, Any]]) -> None:
        """
        Set all recorded actions.

        Args:
            actions: List of action data dictionaries
        """
        self.clear_actions()
        for action in actions:
            self.add_action(action)

    def get_actions(self) -> list[dict[str, Any]]:
        """
        Get all recorded actions.

        Returns:
            List of action data dictionaries
        """
        return self._actions.copy()

    def clear_actions(self) -> None:
        """Clear all recorded actions."""
        self._actions.clear()
        self._action_list.clear()
        self._details_text.clear()
        self._preview_text.clear()
        self._update_count_label()
        self._update_button_states()
        logger.debug("Recorded actions cleared")

    def cleanup(self) -> None:
        """Clean up resources."""
        self._actions.clear()
        logger.debug("RecordedActionsPanel cleaned up")


__all__ = ["RecordedActionsPanel"]

