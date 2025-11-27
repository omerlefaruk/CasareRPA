"""
CasareRPA - Triggers Tab

Bottom panel tab for managing workflow triggers.
Displays trigger list with status, allows enable/disable, and provides
access to trigger configuration dialogs.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QAbstractItemView,
    QMenu,
    QLabel,
    QComboBox,
    QFrame,
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor
from loguru import logger

if TYPE_CHECKING:
    pass


# Trigger type display names and icons
TRIGGER_TYPE_INFO = {
    "manual": {"name": "Manual", "icon": "play"},
    "scheduled": {"name": "Scheduled", "icon": "clock"},
    "webhook": {"name": "Webhook", "icon": "globe"},
    "file_watch": {"name": "File Watch", "icon": "folder"},
    "email": {"name": "Email", "icon": "mail"},
    "app_event": {"name": "App Event", "icon": "monitor"},
    "form": {"name": "Form", "icon": "clipboard"},
    "chat": {"name": "Chat", "icon": "message-square"},
    "error": {"name": "Error", "icon": "alert-triangle"},
    "workflow_call": {"name": "Workflow Call", "icon": "link"},
}


class TriggersTab(QWidget):
    """
    Tab widget for managing workflow triggers.

    Displays a table of configured triggers with their status,
    and provides controls for adding, editing, and managing triggers.

    Signals:
        trigger_added: Emitted when a new trigger is added
        trigger_updated: Emitted when a trigger is updated
        trigger_deleted: Emitted when a trigger is deleted (trigger_id)
        trigger_toggled: Emitted when trigger enabled state changes (trigger_id, enabled)
        trigger_run_requested: Emitted when user wants to run a trigger (trigger_id)
        add_trigger_requested: Emitted when user clicks Add Trigger button
    """

    trigger_added = Signal(dict)  # TriggerConfiguration as dict
    trigger_updated = Signal(dict)  # TriggerConfiguration as dict
    trigger_deleted = Signal(str)  # trigger_id
    trigger_toggled = Signal(str, bool)  # trigger_id, enabled
    trigger_run_requested = Signal(str)  # trigger_id
    add_trigger_requested = Signal()
    triggers_start_requested = Signal()  # User wants to start triggers
    triggers_stop_requested = Signal()  # User wants to stop triggers

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the triggers tab."""
        super().__init__(parent)

        self._triggers: List[Dict[str, Any]] = []
        self._setup_ui()
        self._apply_styles()

        logger.debug("TriggersTab initialized")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        # Filter combo
        self._filter_label = QLabel("Filter:")
        self._filter_combo = QComboBox()
        self._filter_combo.addItems(
            [
                "All Types",
                "Scheduled",
                "Webhook",
                "File Watch",
                "Email",
                "Error",
                "Other",
            ]
        )
        self._filter_combo.currentIndexChanged.connect(self._on_filter_changed)

        # Status filter
        self._status_combo = QComboBox()
        self._status_combo.addItems(["All Status", "Enabled", "Disabled"])
        self._status_combo.currentIndexChanged.connect(self._on_filter_changed)

        # Spacer
        toolbar.addWidget(self._filter_label)
        toolbar.addWidget(self._filter_combo)
        toolbar.addWidget(self._status_combo)
        toolbar.addStretch()

        # Start/Stop triggers button
        self._start_btn = QPushButton("Start Triggers")
        self._start_btn.setCheckable(True)
        self._start_btn.clicked.connect(self._on_toggle_triggers)
        self._start_btn.setToolTip(
            "Start all enabled triggers to run the workflow automatically"
        )
        toolbar.addWidget(self._start_btn)

        # Add trigger button
        self._add_btn = QPushButton("+ Add Trigger")
        self._add_btn.clicked.connect(self._on_add_trigger)
        toolbar.addWidget(self._add_btn)

        layout.addLayout(toolbar)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # Triggers table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(
            [
                "Status",
                "Name",
                "Type",
                "Last Triggered",
                "Count",
                "Actions",
            ]
        )

        # Table settings
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(True)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        self._table.doubleClicked.connect(self._on_row_double_clicked)

        # Column widths
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Status
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Type
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Last Triggered
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Count
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Actions

        self._table.setColumnWidth(0, 60)
        self._table.setColumnWidth(2, 100)
        self._table.setColumnWidth(3, 150)
        self._table.setColumnWidth(4, 60)
        self._table.setColumnWidth(5, 180)

        layout.addWidget(self._table)

        # Empty state message
        self._empty_label = QLabel(
            "No triggers configured.\nClick '+ Add Trigger' to create a new trigger."
        )
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setVisible(False)
        layout.addWidget(self._empty_label)

    def _apply_styles(self) -> None:
        """Apply VSCode Dark+ theme styling."""
        from ..theme import THEME

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {THEME.bg_panel};
                color: {THEME.text_primary};
            }}
            QTableWidget {{
                background-color: {THEME.bg_darkest};
                alternate-background-color: {THEME.bg_medium};
                border: 1px solid {THEME.border_dark};
                gridline-color: {THEME.border_dark};
            }}
            QTableWidget::item {{
                padding: 4px 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {THEME.selection_bg};
            }}
            QHeaderView::section {{
                background-color: {THEME.bg_medium};
                color: {THEME.text_secondary};
                border: none;
                border-bottom: 1px solid {THEME.border_dark};
                padding: 6px 8px;
                font-weight: 500;
            }}
            QPushButton {{
                background-color: {THEME.accent_primary};
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {THEME.accent_hover};
            }}
            QComboBox {{
                background-color: {THEME.input_bg};
                border: 1px solid {THEME.border_dark};
                border-radius: 3px;
                padding: 4px 8px;
                min-width: 100px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QLabel {{
                color: {THEME.text_secondary};
            }}
        """)

    def set_triggers(self, triggers: List[Dict[str, Any]]) -> None:
        """
        Set the list of triggers to display.

        Args:
            triggers: List of trigger configurations as dictionaries
        """
        self._triggers = triggers
        self._refresh_table()

    def add_trigger(self, trigger: Dict[str, Any]) -> None:
        """Add a trigger to the list."""
        self._triggers.append(trigger)
        self._refresh_table()

    def update_trigger(self, trigger: Dict[str, Any]) -> None:
        """Update an existing trigger."""
        trigger_id = trigger.get("id", "")
        for i, t in enumerate(self._triggers):
            if t.get("id") == trigger_id:
                self._triggers[i] = trigger
                break
        self._refresh_table()

    def remove_trigger(self, trigger_id: str) -> None:
        """Remove a trigger from the list."""
        self._triggers = [t for t in self._triggers if t.get("id") != trigger_id]
        self._refresh_table()

    def get_triggers(self) -> List[Dict[str, Any]]:
        """Get the list of triggers."""
        return self._triggers.copy()

    def get_trigger_count(self) -> int:
        """Get the number of triggers."""
        return len(self._triggers)

    @Slot(str, int, str)
    def update_trigger_stats(
        self, trigger_id: str, count: int, last_triggered: str
    ) -> None:
        """
        Update statistics for a specific trigger.

        Args:
            trigger_id: The ID of the trigger to update
            count: The new trigger count
            last_triggered: ISO timestamp of last trigger time
        """
        logger.debug(f"Updating trigger stats: id={trigger_id}, count={count}")
        for trigger in self._triggers:
            if trigger.get("id") == trigger_id:
                trigger["trigger_count"] = count
                trigger["last_triggered"] = last_triggered
                logger.debug(f"Updated trigger {trigger_id}: count={count}")
                break
        self._refresh_table()

    def _refresh_table(self) -> None:
        """Refresh the table display."""
        # Apply filters
        filtered = self._get_filtered_triggers()

        # Update empty state
        self._empty_label.setVisible(len(self._triggers) == 0)
        self._table.setVisible(len(self._triggers) > 0)

        if not filtered and self._triggers:
            # No matches for filter
            self._table.setRowCount(0)
            return

        # Populate table
        self._table.setRowCount(len(filtered))

        for row, trigger in enumerate(filtered):
            # Status toggle
            enabled = trigger.get("enabled", True)
            status_item = QTableWidgetItem("ON" if enabled else "OFF")
            status_item.setForeground(
                QColor("#89D185") if enabled else QColor("#808080")
            )
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item.setData(Qt.ItemDataRole.UserRole, trigger.get("id"))
            self._table.setItem(row, 0, status_item)

            # Name
            name_item = QTableWidgetItem(trigger.get("name", "Untitled"))
            name_item.setData(Qt.ItemDataRole.UserRole, trigger.get("id"))
            self._table.setItem(row, 1, name_item)

            # Type
            trigger_type = trigger.get("type", "manual")
            type_info = TRIGGER_TYPE_INFO.get(
                trigger_type, {"name": trigger_type.title()}
            )
            type_item = QTableWidgetItem(type_info.get("name", trigger_type))
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 2, type_item)

            # Last triggered
            last_triggered = trigger.get("last_triggered", "")
            if last_triggered:
                try:
                    dt = datetime.fromisoformat(last_triggered)
                    last_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    last_str = (
                        last_triggered[:16]
                        if len(last_triggered) > 16
                        else last_triggered
                    )
            else:
                last_str = "-"
            last_item = QTableWidgetItem(last_str)
            last_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 3, last_item)

            # Count
            count = trigger.get("trigger_count", 0)
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 4, count_item)

            # Actions - create widget with buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            # Button style for table cells
            btn_style = """
                QPushButton {
                    background-color: #0E639C;
                    color: white;
                    border: none;
                    padding: 2px 8px;
                    border-radius: 3px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #1177BB;
                }
            """

            # Run button
            run_btn = QPushButton("Run")
            run_btn.setFixedSize(50, 22)
            run_btn.setStyleSheet(btn_style)
            run_btn.setProperty("trigger_id", trigger.get("id"))
            run_btn.clicked.connect(self._on_run_trigger)
            actions_layout.addWidget(run_btn)

            # Edit button
            edit_btn = QPushButton("Edit")
            edit_btn.setFixedSize(50, 22)
            edit_btn.setStyleSheet(btn_style)
            edit_btn.setProperty("trigger_id", trigger.get("id"))
            edit_btn.clicked.connect(self._on_edit_trigger)
            actions_layout.addWidget(edit_btn)

            # Delete button
            del_btn_style = """
                QPushButton {
                    background-color: #6E2C2C;
                    color: white;
                    border: none;
                    padding: 2px 8px;
                    border-radius: 3px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #8B3A3A;
                }
            """
            del_btn = QPushButton("Del")
            del_btn.setFixedSize(40, 22)
            del_btn.setStyleSheet(del_btn_style)
            del_btn.setProperty("trigger_id", trigger.get("id"))
            del_btn.clicked.connect(self._on_delete_trigger)
            actions_layout.addWidget(del_btn)

            self._table.setCellWidget(row, 5, actions_widget)

    def _get_filtered_triggers(self) -> List[Dict[str, Any]]:
        """Get triggers filtered by current filter settings."""
        triggers = self._triggers

        # Type filter
        type_filter = self._filter_combo.currentText()
        if type_filter != "All Types":
            type_map = {
                "Scheduled": "scheduled",
                "Webhook": "webhook",
                "File Watch": "file_watch",
                "Email": "email",
                "Error": "error",
            }
            filter_type = type_map.get(type_filter)
            if filter_type:
                triggers = [t for t in triggers if t.get("type") == filter_type]
            elif type_filter == "Other":
                other_types = {"form", "chat", "app_event", "workflow_call", "manual"}
                triggers = [t for t in triggers if t.get("type") in other_types]

        # Status filter
        status_filter = self._status_combo.currentText()
        if status_filter == "Enabled":
            triggers = [t for t in triggers if t.get("enabled", True)]
        elif status_filter == "Disabled":
            triggers = [t for t in triggers if not t.get("enabled", True)]

        return triggers

    def _on_filter_changed(self) -> None:
        """Handle filter change."""
        self._refresh_table()

    def _on_add_trigger(self) -> None:
        """Handle Add Trigger button click."""
        self.add_trigger_requested.emit()

    def _on_toggle_triggers(self, checked: bool) -> None:
        """Handle Start/Stop Triggers button click."""
        if checked:
            self._start_btn.setText("Stop Triggers")
            self._start_btn.setStyleSheet("background-color: #cc4444;")
            self.triggers_start_requested.emit()
        else:
            self._start_btn.setText("Start Triggers")
            self._start_btn.setStyleSheet("")
            self.triggers_stop_requested.emit()

    def set_triggers_running(self, running: bool) -> None:
        """Update the button state to reflect trigger running status."""
        self._start_btn.setChecked(running)
        if running:
            self._start_btn.setText("Stop Triggers")
            self._start_btn.setStyleSheet("background-color: #cc4444;")
        else:
            self._start_btn.setText("Start Triggers")
            self._start_btn.setStyleSheet("")

    def _on_run_trigger(self) -> None:
        """Handle Run button click."""
        btn = self.sender()
        if btn:
            trigger_id = btn.property("trigger_id")
            if trigger_id:
                self.trigger_run_requested.emit(trigger_id)

    def _on_edit_trigger(self) -> None:
        """Handle Edit button click."""
        btn = self.sender()
        if btn:
            trigger_id = btn.property("trigger_id")
            if trigger_id:
                trigger = self._get_trigger_by_id(trigger_id)
                if trigger:
                    self.trigger_updated.emit(trigger)

    def _on_delete_trigger(self) -> None:
        """Handle Delete button click."""
        btn = self.sender()
        if btn:
            trigger_id = btn.property("trigger_id")
            if trigger_id:
                self.remove_trigger(trigger_id)
                self.trigger_deleted.emit(trigger_id)

    def _on_row_double_clicked(self, index) -> None:
        """Handle row double-click (edit trigger)."""
        row = index.row()
        if row >= 0:
            item = self._table.item(row, 0)
            if item:
                trigger_id = item.data(Qt.ItemDataRole.UserRole)
                trigger = self._get_trigger_by_id(trigger_id)
                if trigger:
                    self.trigger_updated.emit(trigger)

    def _on_context_menu(self, pos) -> None:
        """Show context menu."""
        item = self._table.itemAt(pos)
        if not item:
            return

        trigger_id = item.data(Qt.ItemDataRole.UserRole)
        if not trigger_id:
            # Try to get from first column of same row
            row = item.row()
            first_item = self._table.item(row, 0)
            if first_item:
                trigger_id = first_item.data(Qt.ItemDataRole.UserRole)

        if not trigger_id:
            return

        trigger = self._get_trigger_by_id(trigger_id)
        if not trigger:
            return

        menu = QMenu(self)

        # Run action
        run_action = menu.addAction("Run Now")
        run_action.triggered.connect(
            lambda: self.trigger_run_requested.emit(trigger_id)
        )

        menu.addSeparator()

        # Toggle enabled
        enabled = trigger.get("enabled", True)
        toggle_action = menu.addAction("Disable" if enabled else "Enable")
        toggle_action.triggered.connect(
            lambda: self.trigger_toggled.emit(trigger_id, not enabled)
        )

        # Edit action
        edit_action = menu.addAction("Edit")
        edit_action.triggered.connect(lambda: self.trigger_updated.emit(trigger))

        menu.addSeparator()

        # Delete action
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self.trigger_deleted.emit(trigger_id))

        menu.exec(self._table.mapToGlobal(pos))

    def _get_trigger_by_id(self, trigger_id: str) -> Optional[Dict[str, Any]]:
        """Get a trigger by its ID."""
        for trigger in self._triggers:
            if trigger.get("id") == trigger_id:
                return trigger
        return None

    def clear(self) -> None:
        """Clear all triggers."""
        self._triggers.clear()
        self._refresh_table()
