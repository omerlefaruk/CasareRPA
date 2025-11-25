"""
Jobs panel - Central table showing job list with Deadline-style rendering.
Dense information display with progress bars and status indicators.
"""
from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView,
    QLabel, QComboBox, QPushButton, QFrame, QAbstractItemView,
    QMenu, QStyledItemDelegate
)
from PySide6.QtCore import (
    Qt, Signal, QSize, QAbstractTableModel, QModelIndex,
    QSortFilterProxyModel
)
from PySide6.QtGui import QColor, QAction

from ..theme import THEME, get_status_color, get_priority_color
from ..delegates import (
    ProgressBarDelegate, StatusDelegate, PriorityDelegate,
    DurationDelegate, IconTextDelegate, TimeDelegate
)
from ..models import Job, JobStatus, JobPriority


class JobsTableModel(QAbstractTableModel):
    """Table model for jobs data."""

    COLUMNS = [
        ("name", "Job Name", 200),
        ("progress", "Progress", 100),
        ("status", "Status", 100),
        ("priority", "Priority", 80),
        ("robot", "Robot", 120),
        ("duration", "Duration", 80),
        ("started", "Started", 80),
        ("current_node", "Current Node", 150),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._jobs: List[Dict] = []

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._jobs)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._jobs):
            return None

        job = self._jobs[index.row()]
        col_key = self.COLUMNS[index.column()][0]

        if role == Qt.ItemDataRole.DisplayRole:
            if col_key == "name":
                return job.get("workflow_name", "Unknown")
            elif col_key == "progress":
                return job.get("progress", 0)
            elif col_key == "status":
                return job.get("status", "pending")
            elif col_key == "priority":
                return job.get("priority", 1)
            elif col_key == "robot":
                return job.get("robot_name", "-")
            elif col_key == "duration":
                return job.get("duration_ms", 0)
            elif col_key == "started":
                return job.get("started_at")
            elif col_key == "current_node":
                return job.get("current_node", "-")

        elif role == Qt.ItemDataRole.UserRole:
            # Return job status for progress bar coloring
            if col_key == "progress":
                return job.get("status", "pending")
            # Return full job data
            return job

        elif role == Qt.ItemDataRole.DecorationRole:
            if col_key == "name":
                return "📋"  # Job icon

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col_key in ("progress", "priority", "duration"):
                return Qt.AlignmentFlag.AlignCenter

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section][1]
        return None

    def set_jobs(self, jobs: List[Dict]):
        self.beginResetModel()
        self._jobs = jobs
        self.endResetModel()

    def get_job(self, row: int) -> Optional[Dict]:
        if 0 <= row < len(self._jobs):
            return self._jobs[row]
        return None

    def get_job_id(self, row: int) -> Optional[str]:
        job = self.get_job(row)
        return job.get("id") if job else None


class FilterToolbar(QWidget):
    """Filter toolbar with dropdowns and quick filters."""

    filter_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(12)

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {THEME.bg_header};
                border-bottom: 1px solid {THEME.border_dark};
            }}
        """)

        # Title
        title = QLabel("Jobs")
        title.setStyleSheet(f"""
            color: {THEME.text_primary};
            font-size: 12px;
            font-weight: 600;
        """)
        layout.addWidget(title)

        layout.addSpacing(20)

        # Status filter
        status_label = QLabel("Status:")
        status_label.setStyleSheet(f"color: {THEME.text_secondary}; font-size: 11px;")
        layout.addWidget(status_label)

        self._status_combo = QComboBox()
        self._status_combo.addItems(["All", "Running", "Queued", "Completed", "Failed"])
        self._status_combo.currentIndexChanged.connect(self._emit_filter)
        self._style_combo(self._status_combo)
        layout.addWidget(self._status_combo)

        # Priority filter
        priority_label = QLabel("Priority:")
        priority_label.setStyleSheet(f"color: {THEME.text_secondary}; font-size: 11px;")
        layout.addWidget(priority_label)

        self._priority_combo = QComboBox()
        self._priority_combo.addItems(["All", "Critical", "High", "Normal", "Low"])
        self._priority_combo.currentIndexChanged.connect(self._emit_filter)
        self._style_combo(self._priority_combo)
        layout.addWidget(self._priority_combo)

        # Robot filter
        robot_label = QLabel("Robot:")
        robot_label.setStyleSheet(f"color: {THEME.text_secondary}; font-size: 11px;")
        layout.addWidget(robot_label)

        self._robot_combo = QComboBox()
        self._robot_combo.addItems(["All"])
        self._robot_combo.currentIndexChanged.connect(self._emit_filter)
        self._style_combo(self._robot_combo)
        layout.addWidget(self._robot_combo)

        layout.addStretch()

        # Count label
        self._count_label = QLabel("0 jobs")
        self._count_label.setStyleSheet(f"color: {THEME.text_muted}; font-size: 11px;")
        layout.addWidget(self._count_label)

    def _style_combo(self, combo: QComboBox):
        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {THEME.bg_dark};
                border: 1px solid {THEME.border};
                border-radius: 3px;
                padding: 3px 6px;
                font-size: 11px;
                min-width: 80px;
                min-height: 22px;
            }}
        """)

    def _emit_filter(self):
        self.filter_changed.emit(self.get_filters())

    def get_filters(self) -> Dict[str, str]:
        return {
            "status": self._status_combo.currentText().lower(),
            "priority": self._priority_combo.currentText().lower(),
            "robot": self._robot_combo.currentText(),
        }

    def set_job_count(self, count: int):
        self._count_label.setText(f"{count} jobs")

    def set_robots(self, robot_names: List[str]):
        current = self._robot_combo.currentText()
        self._robot_combo.clear()
        self._robot_combo.addItem("All")
        self._robot_combo.addItems(robot_names)
        if current in robot_names:
            self._robot_combo.setCurrentText(current)


class JobsPanel(QWidget):
    """
    Main jobs table panel with Deadline-style dense display.
    Shows progress bars, status indicators, and priority badges inline.
    """

    job_selected = Signal(str)              # job_id
    job_double_clicked = Signal(str)        # job_id
    job_action = Signal(str, str)           # job_id, action

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {THEME.bg_panel};
            }}
        """)

        # Filter toolbar
        self._filter_toolbar = FilterToolbar()
        self._filter_toolbar.filter_changed.connect(self._apply_filters)
        layout.addWidget(self._filter_toolbar)

        # Table
        self._table = QTableView()
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table.setSortingEnabled(True)
        self._table.setShowGrid(False)
        self._table.verticalHeader().setVisible(False)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.doubleClicked.connect(self._on_double_click)

        # Model
        self._model = JobsTableModel(self)
        self._proxy_model = QSortFilterProxyModel(self)
        self._proxy_model.setSourceModel(self._model)
        self._proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._table.setModel(self._proxy_model)

        # Set delegates
        self._table.setItemDelegateForColumn(0, IconTextDelegate(parent=self))  # Name
        self._table.setItemDelegateForColumn(1, ProgressBarDelegate(parent=self))  # Progress
        self._table.setItemDelegateForColumn(2, StatusDelegate(parent=self))  # Status
        self._table.setItemDelegateForColumn(3, PriorityDelegate(parent=self))  # Priority
        self._table.setItemDelegateForColumn(5, DurationDelegate(parent=self))  # Duration
        self._table.setItemDelegateForColumn(6, TimeDelegate(parent=self))  # Started

        # Header
        header = self._table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setDefaultSectionSize(100)

        # Set column widths
        for i, (_, _, width) in enumerate(JobsTableModel.COLUMNS):
            self._table.setColumnWidth(i, width)

        # Row height
        self._table.verticalHeader().setDefaultSectionSize(28)

        self._table.setStyleSheet(f"""
            QTableView {{
                background-color: {THEME.bg_panel};
                alternate-background-color: {THEME.bg_row_alt};
                border: none;
                gridline-color: transparent;
            }}
            QTableView::item {{
                padding: 2px;
                border-bottom: 1px solid {THEME.border_dark};
            }}
            QTableView::item:selected {{
                background-color: {THEME.bg_selected};
            }}
        """)

        layout.addWidget(self._table, 1)

        # Selection changed signal
        self._table.selectionModel().currentChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self, current: QModelIndex, previous: QModelIndex):
        if current.isValid():
            source_index = self._proxy_model.mapToSource(current)
            job_id = self._model.get_job_id(source_index.row())
            if job_id:
                self.job_selected.emit(job_id)

    def _on_double_click(self, index: QModelIndex):
        if index.isValid():
            source_index = self._proxy_model.mapToSource(index)
            job_id = self._model.get_job_id(source_index.row())
            if job_id:
                self.job_double_clicked.emit(job_id)

    def _show_context_menu(self, pos):
        index = self._table.indexAt(pos)
        if not index.isValid():
            return

        source_index = self._proxy_model.mapToSource(index)
        job = self._model.get_job(source_index.row())
        if not job:
            return

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {THEME.bg_light};
                border: 1px solid {THEME.border};
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px 6px 12px;
            }}
            QMenu::item:selected {{
                background-color: {THEME.accent_primary};
            }}
        """)

        job_id = job.get("id", "")
        status = job.get("status", "").lower()

        # Actions based on status
        if status in ("running",):
            pause_action = menu.addAction("Pause Job")
            pause_action.triggered.connect(lambda: self.job_action.emit(job_id, "pause"))
            cancel_action = menu.addAction("Cancel Job")
            cancel_action.triggered.connect(lambda: self.job_action.emit(job_id, "cancel"))
        elif status in ("pending", "queued"):
            start_action = menu.addAction("Start Now")
            start_action.triggered.connect(lambda: self.job_action.emit(job_id, "start"))
            cancel_action = menu.addAction("Cancel Job")
            cancel_action.triggered.connect(lambda: self.job_action.emit(job_id, "cancel"))
        elif status in ("failed", "cancelled", "timeout"):
            retry_action = menu.addAction("Retry Job")
            retry_action.triggered.connect(lambda: self.job_action.emit(job_id, "retry"))

        menu.addSeparator()

        # Common actions
        view_logs = menu.addAction("View Logs")
        view_logs.triggered.connect(lambda: self.job_action.emit(job_id, "logs"))

        view_details = menu.addAction("View Details")
        view_details.triggered.connect(lambda: self.job_action.emit(job_id, "details"))

        menu.addSeparator()

        delete_action = menu.addAction("Delete Job")
        delete_action.triggered.connect(lambda: self.job_action.emit(job_id, "delete"))

        menu.exec_(self._table.viewport().mapToGlobal(pos))

    def _apply_filters(self, filters: Dict[str, str]):
        # Apply filters through proxy model
        status = filters.get("status", "all")
        if status == "all":
            self._proxy_model.setFilterRegularExpression("")
        else:
            self._proxy_model.setFilterKeyColumn(2)  # Status column
            self._proxy_model.setFilterRegularExpression(f"^{status}$")

    def set_jobs(self, jobs: List[Dict]):
        """Update jobs data."""
        self._model.set_jobs(jobs)
        self._filter_toolbar.set_job_count(len(jobs))

        # Collect robot names for filter dropdown
        robot_names = list(set(j.get("robot_name", "") for j in jobs if j.get("robot_name")))
        self._filter_toolbar.set_robots(sorted(robot_names))

    def get_selected_job_ids(self) -> List[str]:
        """Get IDs of selected jobs."""
        job_ids = []
        for index in self._table.selectionModel().selectedRows():
            source_index = self._proxy_model.mapToSource(index)
            job_id = self._model.get_job_id(source_index.row())
            if job_id:
                job_ids.append(job_id)
        return job_ids

    def refresh(self):
        """Force table refresh."""
        self._model.layoutChanged.emit()
