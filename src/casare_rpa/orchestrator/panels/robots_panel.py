"""
Robots panel - Shows robot workers with status and utilization.
Deadline-style worker status display.
"""
from typing import Optional, List, Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView,
    QLabel, QComboBox, QPushButton, QFrame, QAbstractItemView,
    QMenu, QProgressBar
)
from PySide6.QtCore import (
    Qt, Signal, QAbstractTableModel, QModelIndex,
    QSortFilterProxyModel
)
from PySide6.QtGui import QColor

from ..theme import THEME, get_status_color
from ..delegates import StatusDelegate, RobotStatusDelegate, IconTextDelegate


class RobotsTableModel(QAbstractTableModel):
    """Table model for robots data."""

    COLUMNS = [
        ("name", "Robot Name", 180),
        ("status", "Status", 120),
        ("environment", "Pool", 100),
        ("capacity", "Capacity", 120),
        ("utilization", "Utilization", 100),
        ("last_seen", "Last Seen", 100),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._robots: List[Dict] = []

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._robots)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._robots):
            return None

        robot = self._robots[index.row()]
        col_key = self.COLUMNS[index.column()][0]

        if role == Qt.ItemDataRole.DisplayRole:
            if col_key == "name":
                return robot.get("name", "Unknown")
            elif col_key == "status":
                return robot.get("status", "offline")
            elif col_key == "environment":
                return robot.get("environment", "default")
            elif col_key == "capacity":
                current = robot.get("current_jobs", 0)
                max_jobs = robot.get("max_concurrent_jobs", 1)
                return f"{current} / {max_jobs}"
            elif col_key == "utilization":
                current = robot.get("current_jobs", 0)
                max_jobs = robot.get("max_concurrent_jobs", 1)
                return int((current / max_jobs * 100) if max_jobs > 0 else 0)
            elif col_key == "last_seen":
                last_seen = robot.get("last_seen")
                if last_seen and hasattr(last_seen, 'strftime'):
                    return last_seen.strftime("%H:%M:%S")
                return "-"

        elif role == Qt.ItemDataRole.UserRole:
            if col_key == "status":
                return {
                    "status": robot.get("status", "offline"),
                    "utilization": int((robot.get("current_jobs", 0) /
                                       robot.get("max_concurrent_jobs", 1) * 100)
                                      if robot.get("max_concurrent_jobs", 1) > 0 else 0)
                }
            return robot

        elif role == Qt.ItemDataRole.DecorationRole:
            if col_key == "name":
                return "🤖"

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNS[section][1]
        return None

    def set_robots(self, robots: List[Dict]):
        self.beginResetModel()
        self._robots = robots
        self.endResetModel()

    def get_robot(self, row: int) -> Optional[Dict]:
        if 0 <= row < len(self._robots):
            return self._robots[row]
        return None

    def get_robot_id(self, row: int) -> Optional[str]:
        robot = self.get_robot(row)
        return robot.get("id") if robot else None


class RobotCard(QFrame):
    """Card widget showing robot status summary."""

    clicked = Signal(str)  # robot_id

    def __init__(self, robot: Dict, parent=None):
        super().__init__(parent)
        self._robot = robot
        self._setup_ui()

    def _setup_ui(self):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(80)

        status = self._robot.get("status", "offline").lower()
        status_color = get_status_color(status)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME.bg_light};
                border: 1px solid {THEME.border};
                border-left: 3px solid {status_color};
                border-radius: 3px;
            }}
            QFrame:hover {{
                background-color: {THEME.bg_hover};
                border-color: {THEME.border_light};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # Header row
        header = QHBoxLayout()
        header.setSpacing(8)

        # Status indicator
        status_dot = QLabel("●")
        status_dot.setStyleSheet(f"color: {status_color}; font-size: 14px;")
        header.addWidget(status_dot)

        # Name
        name = QLabel(self._robot.get("name", "Unknown"))
        name.setStyleSheet(f"color: {THEME.text_primary}; font-weight: 600; font-size: 12px;")
        header.addWidget(name)

        header.addStretch()

        # Pool badge
        pool = self._robot.get("environment", "default")
        pool_label = QLabel(pool)
        pool_label.setStyleSheet(f"""
            background-color: {THEME.bg_dark};
            color: {THEME.text_muted};
            padding: 2px 6px;
            border-radius: 2px;
            font-size: 10px;
        """)
        header.addWidget(pool_label)

        layout.addLayout(header)

        # Capacity row
        capacity_row = QHBoxLayout()
        capacity_row.setSpacing(8)

        current = self._robot.get("current_jobs", 0)
        max_jobs = self._robot.get("max_concurrent_jobs", 1)
        utilization = int((current / max_jobs * 100) if max_jobs > 0 else 0)

        capacity_label = QLabel(f"Jobs: {current}/{max_jobs}")
        capacity_label.setStyleSheet(f"color: {THEME.text_secondary}; font-size: 11px;")
        capacity_row.addWidget(capacity_label)

        # Mini progress bar
        util_bar = QProgressBar()
        util_bar.setRange(0, 100)
        util_bar.setValue(utilization)
        util_bar.setTextVisible(False)
        util_bar.setFixedHeight(6)
        util_bar.setFixedWidth(80)
        util_color = THEME.status_online if utilization < 80 else THEME.status_busy
        util_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {THEME.progress_bg};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {util_color};
                border-radius: 3px;
            }}
        """)
        capacity_row.addWidget(util_bar)

        capacity_row.addStretch()

        # Status text
        status_text = QLabel(status.capitalize())
        status_text.setStyleSheet(f"color: {status_color}; font-size: 11px; font-weight: 500;")
        capacity_row.addWidget(status_text)

        layout.addLayout(capacity_row)

    def mousePressEvent(self, event):
        self.clicked.emit(self._robot.get("id", ""))
        super().mousePressEvent(event)


class RobotsPanel(QWidget):
    """
    Robots panel showing worker status.
    Can display as table or card grid.
    """

    robot_selected = Signal(str)  # robot_id
    robot_action = Signal(str, str)  # robot_id, action

    def __init__(self, parent=None):
        super().__init__(parent)
        self._view_mode = "table"  # "table" or "cards"
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

        # Toolbar
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(8, 6, 8, 6)
        toolbar_layout.setSpacing(12)
        toolbar.setStyleSheet(f"""
            background-color: {THEME.bg_header};
            border-bottom: 1px solid {THEME.border_dark};
        """)

        title = QLabel("Robots")
        title.setStyleSheet(f"color: {THEME.text_primary}; font-weight: 600; font-size: 12px;")
        toolbar_layout.addWidget(title)

        toolbar_layout.addSpacing(20)

        # Status filter
        status_label = QLabel("Status:")
        status_label.setStyleSheet(f"color: {THEME.text_secondary}; font-size: 11px;")
        toolbar_layout.addWidget(status_label)

        self._status_combo = QComboBox()
        self._status_combo.addItems(["All", "Online", "Busy", "Offline", "Error"])
        self._status_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {THEME.bg_dark};
                border: 1px solid {THEME.border};
                border-radius: 3px;
                padding: 3px 6px;
                font-size: 11px;
                min-width: 80px;
            }}
        """)
        toolbar_layout.addWidget(self._status_combo)

        # Pool filter
        pool_label = QLabel("Pool:")
        pool_label.setStyleSheet(f"color: {THEME.text_secondary}; font-size: 11px;")
        toolbar_layout.addWidget(pool_label)

        self._pool_combo = QComboBox()
        self._pool_combo.addItems(["All"])
        self._pool_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {THEME.bg_dark};
                border: 1px solid {THEME.border};
                border-radius: 3px;
                padding: 3px 6px;
                font-size: 11px;
                min-width: 80px;
            }}
        """)
        toolbar_layout.addWidget(self._pool_combo)

        toolbar_layout.addStretch()

        # Count
        self._count_label = QLabel("0 robots")
        self._count_label.setStyleSheet(f"color: {THEME.text_muted}; font-size: 11px;")
        toolbar_layout.addWidget(self._count_label)

        layout.addWidget(toolbar)

        # Summary bar
        self._summary = QWidget()
        summary_layout = QHBoxLayout(self._summary)
        summary_layout.setContentsMargins(8, 8, 8, 8)
        summary_layout.setSpacing(16)
        self._summary.setStyleSheet(f"""
            background-color: {THEME.bg_medium};
            border-bottom: 1px solid {THEME.border_dark};
        """)

        self._online_label = self._create_stat_label("Online", "0", THEME.status_online)
        summary_layout.addWidget(self._online_label)

        self._busy_label = self._create_stat_label("Busy", "0", THEME.status_busy)
        summary_layout.addWidget(self._busy_label)

        self._offline_label = self._create_stat_label("Offline", "0", THEME.status_offline)
        summary_layout.addWidget(self._offline_label)

        self._error_label = self._create_stat_label("Error", "0", THEME.status_error)
        summary_layout.addWidget(self._error_label)

        summary_layout.addStretch()

        layout.addWidget(self._summary)

        # Table
        self._table = QTableView()
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setSortingEnabled(True)
        self._table.setShowGrid(False)
        self._table.verticalHeader().setVisible(False)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)

        # Model
        self._model = RobotsTableModel(self)
        self._proxy_model = QSortFilterProxyModel(self)
        self._proxy_model.setSourceModel(self._model)
        self._table.setModel(self._proxy_model)

        # Delegates
        self._table.setItemDelegateForColumn(0, IconTextDelegate(parent=self))
        self._table.setItemDelegateForColumn(1, RobotStatusDelegate(parent=self))

        # Header
        header = self._table.horizontalHeader()
        header.setStretchLastSection(True)
        for i, (_, _, width) in enumerate(RobotsTableModel.COLUMNS):
            self._table.setColumnWidth(i, width)

        self._table.verticalHeader().setDefaultSectionSize(32)

        self._table.setStyleSheet(f"""
            QTableView {{
                background-color: {THEME.bg_panel};
                alternate-background-color: {THEME.bg_row_alt};
                border: none;
            }}
            QTableView::item {{
                padding: 4px;
                border-bottom: 1px solid {THEME.border_dark};
            }}
            QTableView::item:selected {{
                background-color: {THEME.bg_selected};
            }}
        """)

        layout.addWidget(self._table, 1)

        # Selection changed
        self._table.selectionModel().currentChanged.connect(self._on_selection_changed)

    def _create_stat_label(self, label: str, value: str, color: str) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color}; font-size: 10px;")
        layout.addWidget(dot)

        text = QLabel(f"{label}:")
        text.setStyleSheet(f"color: {THEME.text_muted}; font-size: 11px;")
        layout.addWidget(text)

        val = QLabel(value)
        val.setObjectName("value")
        val.setStyleSheet(f"color: {THEME.text_primary}; font-size: 11px; font-weight: 600;")
        layout.addWidget(val)

        return widget

    def _on_selection_changed(self, current: QModelIndex, previous: QModelIndex):
        if current.isValid():
            source_index = self._proxy_model.mapToSource(current)
            robot_id = self._model.get_robot_id(source_index.row())
            if robot_id:
                self.robot_selected.emit(robot_id)

    def _show_context_menu(self, pos):
        index = self._table.indexAt(pos)
        if not index.isValid():
            return

        source_index = self._proxy_model.mapToSource(index)
        robot = self._model.get_robot(source_index.row())
        if not robot:
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

        robot_id = robot.get("id", "")
        status = robot.get("status", "").lower()

        view_action = menu.addAction("View Details")
        view_action.triggered.connect(lambda: self.robot_selected.emit(robot_id))

        menu.addSeparator()

        if status == "online":
            disable_action = menu.addAction("Disable Robot")
            disable_action.triggered.connect(lambda: self.robot_action.emit(robot_id, "disable"))
        elif status == "offline":
            enable_action = menu.addAction("Enable Robot")
            enable_action.triggered.connect(lambda: self.robot_action.emit(robot_id, "enable"))

        menu.exec_(self._table.viewport().mapToGlobal(pos))

    def set_robots(self, robots: List[Dict]):
        """Update robots data."""
        self._model.set_robots(robots)
        self._count_label.setText(f"{len(robots)} robots")

        # Update summary
        online = sum(1 for r in robots if r.get("status", "").lower() == "online")
        busy = sum(1 for r in robots if r.get("status", "").lower() == "busy")
        offline = sum(1 for r in robots if r.get("status", "").lower() == "offline")
        error = sum(1 for r in robots if r.get("status", "").lower() == "error")

        self._online_label.findChild(QLabel, "value").setText(str(online))
        self._busy_label.findChild(QLabel, "value").setText(str(busy))
        self._offline_label.findChild(QLabel, "value").setText(str(offline))
        self._error_label.findChild(QLabel, "value").setText(str(error))

        # Update pool filter
        pools = list(set(r.get("environment", "default") for r in robots))
        current_pool = self._pool_combo.currentText()
        self._pool_combo.clear()
        self._pool_combo.addItem("All")
        self._pool_combo.addItems(sorted(pools))
        if current_pool in pools:
            self._pool_combo.setCurrentText(current_pool)

    def refresh(self):
        """Force refresh."""
        self._model.layoutChanged.emit()
