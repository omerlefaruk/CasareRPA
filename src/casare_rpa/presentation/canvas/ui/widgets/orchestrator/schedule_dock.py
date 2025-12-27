"""
Schedule Builder Dock for CasareRPA.

Visual schedule builder dock widget with calendar view.
Provides schedule management, creation, and monitoring.
"""

from typing import Any

from loguru import logger
from PySide6.QtCore import QSize, Qt, QTime, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDockWidget,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS
from casare_rpa.presentation.canvas.ui.widgets.orchestrator.calendar_widget import (
    ScheduleCalendarWidget,
)


class ScheduleBuilderDock(QDockWidget):
    """
    Dockable schedule builder panel.

    Provides visual schedule management with:
    - Calendar view with schedule markers
    - Schedule list with filtering
    - Quick schedule creation form
    - Cron expression builder

    Signals:
        schedule_created: Emitted when schedule is created (schedule_dict)
        schedule_edited: Emitted when schedule is edited (schedule_id, schedule_dict)
        schedule_deleted: Emitted when schedule is deleted (schedule_id)
        schedule_enabled_changed: Emitted when enabled toggled (schedule_id, enabled)
        schedule_run_now: Emitted when run now clicked (schedule_id)
    """

    schedule_created = Signal(dict)
    schedule_edited = Signal(str, dict)
    schedule_deleted = Signal(str)
    schedule_enabled_changed = Signal(str, bool)
    schedule_run_now = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the schedule builder dock.

        Args:
            parent: Optional parent widget
        """
        super().__init__("Schedule Builder", parent)
        self.setObjectName("ScheduleBuilderDock")

        self._schedules: list[dict[str, Any]] = []
        self._workflows: list[dict[str, Any]] = []
        self._selected_schedule_id: str | None = None

        self._setup_dock()
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

        logger.debug("ScheduleBuilderDock initialized")

    def _setup_dock(self) -> None:
        """Configure dock widget properties."""
        self.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
            | Qt.DockWidgetArea.LeftDockWidgetArea
        )

        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )

        self.setMinimumHeight(300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def sizeHint(self) -> QSize:
        """Return preferred size for dock widget."""
        return QSize(900, 450)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Calendar
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        calendar_label = QLabel("Schedule Calendar")
        calendar_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        left_layout.addWidget(calendar_label)

        self._calendar = ScheduleCalendarWidget()
        left_layout.addWidget(self._calendar)

        splitter.addWidget(left_panel)

        # Right panel - Schedule list and creation
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # Schedule list header
        header = QHBoxLayout()
        list_label = QLabel("Schedules")
        list_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header.addWidget(list_label)

        header.addStretch()

        self._filter_combo = QComboBox()
        self._filter_combo.addItems(["All", "Active", "Disabled"])
        self._filter_combo.setFixedWidth(100)
        header.addWidget(self._filter_combo)

        self._add_btn = QPushButton("+ New Schedule")
        self._add_btn.setObjectName("AddScheduleButton")
        header.addWidget(self._add_btn)

        right_layout.addLayout(header)

        # Schedule table
        self._schedule_table = QTableWidget()
        self._schedule_table.setColumnCount(5)
        self._schedule_table.setHorizontalHeaderLabels(
            ["Name", "Workflow", "Frequency", "Next Run", "Enabled"]
        )
        self._schedule_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._schedule_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._schedule_table.setAlternatingRowColors(True)
        self._schedule_table.verticalHeader().setVisible(False)
        self._schedule_table.horizontalHeader().setStretchLastSection(True)
        self._schedule_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        right_layout.addWidget(self._schedule_table)

        # Action buttons
        action_bar = QHBoxLayout()
        action_bar.setSpacing(8)

        self._run_now_btn = QPushButton("Run Now")
        self._run_now_btn.setEnabled(False)
        action_bar.addWidget(self._run_now_btn)

        self._edit_btn = QPushButton("Edit")
        self._edit_btn.setEnabled(False)
        action_bar.addWidget(self._edit_btn)

        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setEnabled(False)
        self._delete_btn.setObjectName("DeleteButton")
        action_bar.addWidget(self._delete_btn)

        action_bar.addStretch()

        self._refresh_btn = QPushButton("Refresh")
        action_bar.addWidget(self._refresh_btn)

        right_layout.addLayout(action_bar)

        # Quick create form (collapsible)
        self._create_form = self._create_schedule_form()
        self._create_form.setVisible(False)
        right_layout.addWidget(self._create_form)

        splitter.addWidget(right_panel)

        # Set splitter sizes (40% calendar, 60% list)
        splitter.setSizes([400, 600])

        main_layout.addWidget(splitter)
        self.setWidget(container)

    def _create_schedule_form(self) -> QGroupBox:
        """Create the quick schedule creation form."""
        group = QGroupBox("Create New Schedule")
        layout = QFormLayout(group)
        layout.setSpacing(8)

        self._form_name = QLineEdit()
        self._form_name.setPlaceholderText("Schedule name")
        layout.addRow("Name:", self._form_name)

        self._form_workflow = QComboBox()
        self._form_workflow.setPlaceholderText("Select workflow")
        layout.addRow("Workflow:", self._form_workflow)

        self._form_frequency = QComboBox()
        self._form_frequency.addItems(
            ["Once", "Hourly", "Daily", "Weekly", "Monthly", "Custom (Cron)"]
        )
        layout.addRow("Frequency:", self._form_frequency)

        time_layout = QHBoxLayout()
        self._form_time = QTimeEdit()
        self._form_time.setDisplayFormat("HH:mm")
        self._form_time.setTime(QTime(9, 0))
        time_layout.addWidget(self._form_time)

        self._form_interval = QSpinBox()
        self._form_interval.setMinimum(1)
        self._form_interval.setMaximum(24)
        self._form_interval.setValue(1)
        self._form_interval.setSuffix(" hour(s)")
        self._form_interval.setVisible(False)
        time_layout.addWidget(self._form_interval)

        layout.addRow("Time:", time_layout)

        self._form_cron = QLineEdit()
        self._form_cron.setPlaceholderText("0 9 * * * (min hour day month weekday)")
        self._form_cron.setVisible(False)
        layout.addRow("Cron:", self._form_cron)

        self._form_enabled = QCheckBox("Enabled")
        self._form_enabled.setChecked(True)
        layout.addRow("", self._form_enabled)

        btn_layout = QHBoxLayout()
        self._form_cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self._form_cancel_btn)

        self._form_save_btn = QPushButton("Create Schedule")
        self._form_save_btn.setObjectName("PrimaryButton")
        btn_layout.addWidget(self._form_save_btn)

        layout.addRow("", btn_layout)

        return group

    def _apply_styles(self) -> None:
        """Apply theme styles."""
        c = THEME
        r = Theme.get_border_radius()

        self.setStyleSheet(f"""
            QDockWidget {{
                background-color: {c.bg_elevated};
            }}
            QDockWidget::title {{
                background-color: {c.bg_header};
                padding: 8px;
                font-weight: bold;
            }}
            QTableWidget {{
                background-color: {c.bg_elevated};
                gridline-color: {c.border_dark};
                border: 1px solid {c.border};
            }}
            QTableWidget::item {{
                padding: 6px 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {c.bg_selected};
            }}
            QHeaderView::section {{
                background-color: {c.bg_header};
                padding: 8px;
                border: none;
                border-right: 1px solid {c.border_dark};
                font-weight: bold;
            }}
            QPushButton {{
                background-color: {c.bg_surface};
                border: 1px solid {c.border};
                border-radius: {r.sm}px;
                padding: 6px 12px;
                color: {c.text_primary};
            }}
            QPushButton:hover {{
                background-color: {c.bg_hover};
                border-color: {c.border_light};
            }}
            QPushButton:pressed {{
                background-color: {c.bg_surface};
            }}
            QPushButton:disabled {{
                color: {c.text_disabled};
                background-color: {c.bg_surface};
            }}
            #AddScheduleButton {{
                background-color: {c.accent};
                color: white;
                border: none;
            }}
            #AddScheduleButton:hover {{
                background-color: {c.accent_hover};
            }}
            #PrimaryButton {{
                background-color: {c.accent};
                color: white;
                border: none;
            }}
            #PrimaryButton:hover {{
                background-color: {c.accent_hover};
            }}
            #DeleteButton {{
                background-color: {c.error};
                color: white;
                border: none;
            }}
            #DeleteButton:hover {{
                background-color: THEME.error;
            }}
            QGroupBox {{
                background-color: {c.surface};
                border: 1px solid {c.border};
                border-radius: {r.md}px;
                margin-top: 12px;
                padding: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: {c.text_primary};
                font-weight: bold;
            }}
            QLineEdit, QComboBox, QSpinBox, QTimeEdit {{
                background-color: {c.background};
                border: 1px solid {c.border};
                border-radius: {r.sm}px;
                padding: 6px 8px;
                color: {c.text_primary};
            }}
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTimeEdit:focus {{
                border-color: {c.accent};
            }}
            QLabel {{
                color: {c.text_primary};
            }}
        """)

    def _connect_signals(self) -> None:
        """Connect UI signals."""
        self._add_btn.clicked.connect(self._on_add_clicked)
        self._edit_btn.clicked.connect(self._on_edit_clicked)
        self._delete_btn.clicked.connect(self._on_delete_clicked)
        self._run_now_btn.clicked.connect(self._on_run_now_clicked)
        self._refresh_btn.clicked.connect(self._on_refresh_clicked)

        self._schedule_table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self._schedule_table.cellChanged.connect(self._on_cell_changed)

        self._filter_combo.currentIndexChanged.connect(self._apply_filter)

        self._form_cancel_btn.clicked.connect(self._hide_form)
        self._form_save_btn.clicked.connect(self._on_form_save)
        self._form_frequency.currentIndexChanged.connect(self._on_frequency_changed)

        self._calendar.schedule_clicked.connect(self._on_calendar_schedule_clicked)

    def _on_add_clicked(self) -> None:
        """Handle add schedule button click."""
        self._create_form.setVisible(True)
        self._form_name.clear()
        self._form_name.setFocus()

    def _hide_form(self) -> None:
        """Hide the creation form."""
        self._create_form.setVisible(False)

    def _on_edit_clicked(self) -> None:
        """Handle edit button click."""
        if self._selected_schedule_id:
            schedule = self._get_schedule_by_id(self._selected_schedule_id)
            if schedule:
                self.schedule_edited.emit(self._selected_schedule_id, schedule)

    def _on_delete_clicked(self) -> None:
        """Handle delete button click."""
        if self._selected_schedule_id:
            self.schedule_deleted.emit(self._selected_schedule_id)

    def _on_run_now_clicked(self) -> None:
        """Handle run now button click."""
        if self._selected_schedule_id:
            self.schedule_run_now.emit(self._selected_schedule_id)

    def _on_refresh_clicked(self) -> None:
        """Handle refresh button click."""
        # Emit a signal or call refresh
        logger.debug("Schedule refresh requested")

    def _on_selection_changed(self) -> None:
        """Handle table selection change."""
        selected = self._schedule_table.selectedItems()
        if selected:
            row = selected[0].row()
            schedule_id = self._schedule_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            self._selected_schedule_id = schedule_id
            self._edit_btn.setEnabled(True)
            self._delete_btn.setEnabled(True)
            self._run_now_btn.setEnabled(True)
        else:
            self._selected_schedule_id = None
            self._edit_btn.setEnabled(False)
            self._delete_btn.setEnabled(False)
            self._run_now_btn.setEnabled(False)

    def _on_cell_changed(self, row: int, column: int) -> None:
        """Handle cell value change (for enabled checkbox)."""
        if column == 4:  # Enabled column
            item = self._schedule_table.item(row, 0)
            if item:
                schedule_id = item.data(Qt.ItemDataRole.UserRole)
                enabled_item = self._schedule_table.item(row, 4)
                if enabled_item and schedule_id:
                    enabled = enabled_item.checkState() == Qt.CheckState.Checked
                    self.schedule_enabled_changed.emit(schedule_id, enabled)

    def _on_frequency_changed(self, index: int) -> None:
        """Handle frequency combo change."""
        freq = self._form_frequency.currentText()

        # Show/hide relevant fields
        self._form_interval.setVisible(freq == "Hourly")
        self._form_cron.setVisible(freq == "Custom (Cron)")
        self._form_time.setVisible(freq not in ["Hourly", "Custom (Cron)"])

        # Update interval suffix
        if freq == "Hourly":
            self._form_interval.setSuffix(" hour(s)")

    def _on_form_save(self) -> None:
        """Handle form save button click."""
        name = self._form_name.text().strip()
        if not name:
            return

        workflow_idx = self._form_workflow.currentIndex()
        workflow_id = None
        if workflow_idx >= 0 and workflow_idx < len(self._workflows):
            workflow_id = self._workflows[workflow_idx].get("id")

        freq_text = self._form_frequency.currentText().lower().replace(" ", "_")
        if freq_text == "custom_(cron)":
            freq_text = "cron"

        schedule_data = {
            "name": name,
            "workflow_id": workflow_id,
            "frequency": freq_text,
            "time": self._form_time.time().toString("HH:mm"),
            "enabled": self._form_enabled.isChecked(),
        }

        if freq_text == "hourly":
            schedule_data["interval"] = self._form_interval.value()
        elif freq_text == "cron":
            schedule_data["cron_expression"] = self._form_cron.text().strip()

        self.schedule_created.emit(schedule_data)
        self._hide_form()

    def _on_calendar_schedule_clicked(self, schedule_id: str) -> None:
        """Handle schedule click from calendar."""
        # Find and select in table
        for row in range(self._schedule_table.rowCount()):
            item = self._schedule_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == schedule_id:
                self._schedule_table.selectRow(row)
                break

    def _apply_filter(self) -> None:
        """Apply the current filter to the table."""
        filter_text = self._filter_combo.currentText()

        for row in range(self._schedule_table.rowCount()):
            enabled_item = self._schedule_table.item(row, 4)
            if not enabled_item:
                continue

            is_enabled = enabled_item.checkState() == Qt.CheckState.Checked

            show = True
            if filter_text == "Active" and not is_enabled:
                show = False
            elif filter_text == "Disabled" and is_enabled:
                show = False

            self._schedule_table.setRowHidden(row, not show)

    def _get_schedule_by_id(self, schedule_id: str) -> dict[str, Any] | None:
        """Get schedule data by ID."""
        for schedule in self._schedules:
            if schedule.get("id") == schedule_id:
                return schedule
        return None

    # =========================================================================
    # Public API
    # =========================================================================

    def update_schedules(self, schedules: list[dict[str, Any]]) -> None:
        """
        Update the schedules list.

        Args:
            schedules: List of schedule dictionaries
        """
        self._schedules = schedules
        self._refresh_table()

        # Update calendar
        try:
            schedule_entities = []
            for s in schedules:
                # Convert dict to entity if needed
                if isinstance(s, dict):
                    # Basic conversion - calendar handles gracefully
                    entity = type("Schedule", (), s)()
                    schedule_entities.append(entity)
                else:
                    schedule_entities.append(s)

            self._calendar.set_schedules(schedule_entities)
        except Exception as e:
            logger.debug(f"Could not update calendar: {e}")

    def update_workflows(self, workflows: list[dict[str, Any]]) -> None:
        """
        Update available workflows for schedule creation.

        Args:
            workflows: List of workflow dictionaries with 'id' and 'name'
        """
        self._workflows = workflows
        self._form_workflow.clear()
        for wf in workflows:
            self._form_workflow.addItem(wf.get("name", wf.get("id", "Unknown")))

    def _refresh_table(self) -> None:
        """Refresh the schedule table."""
        self._schedule_table.blockSignals(True)
        self._schedule_table.setRowCount(0)

        for schedule in self._schedules:
            row = self._schedule_table.rowCount()
            self._schedule_table.insertRow(row)

            # Name
            name_item = QTableWidgetItem(schedule.get("name", ""))
            name_item.setData(Qt.ItemDataRole.UserRole, schedule.get("id"))
            self._schedule_table.setItem(row, 0, name_item)

            # Workflow
            workflow_name = schedule.get("workflow_name", schedule.get("workflow_id", "-"))
            self._schedule_table.setItem(row, 1, QTableWidgetItem(workflow_name))

            # Frequency
            freq = schedule.get("frequency", "-")
            if isinstance(freq, str):
                freq_display = freq.replace("_", " ").title()
            else:
                freq_display = str(freq)
            self._schedule_table.setItem(row, 2, QTableWidgetItem(freq_display))

            # Next Run
            next_run = schedule.get("next_run", "-")
            if hasattr(next_run, "strftime"):
                next_run = next_run.strftime("%Y-%m-%d %H:%M")
            self._schedule_table.setItem(row, 3, QTableWidgetItem(str(next_run)))

            # Enabled (checkbox)
            enabled_item = QTableWidgetItem()
            enabled_item.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
            )
            enabled = schedule.get("enabled", True)
            enabled_item.setCheckState(
                Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked
            )
            self._schedule_table.setItem(row, 4, enabled_item)

        self._schedule_table.blockSignals(False)
        self._apply_filter()

    def get_selected_schedule_id(self) -> str | None:
        """Get currently selected schedule ID."""
        return self._selected_schedule_id

    def show_create_form(self) -> None:
        """Show the schedule creation form."""
        self._on_add_clicked()
