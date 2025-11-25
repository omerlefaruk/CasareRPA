"""
Tree navigation panel - Left sidebar with Jobs/Robots hierarchy.
Inspired by Deadline Monitor's navigation tree.
"""
from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QLabel, QComboBox, QPushButton, QLineEdit, QFrame, QButtonGroup,
    QToolButton, QSizePolicy, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QBrush, QFont, QIcon

from ..theme import THEME, get_status_color
from ..models import JobStatus, RobotStatus, JobPriority


class FilterBar(QWidget):
    """Quick filter bar with search and dropdowns."""

    filter_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Search box
        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter...")
        self._search.textChanged.connect(self.filter_changed.emit)
        self._search.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME.bg_dark};
                border: 1px solid {THEME.border};
                border-radius: 3px;
                padding: 4px 8px;
                font-size: 11px;
            }}
        """)
        layout.addWidget(self._search)

        # Status filter
        status_row = QHBoxLayout()
        status_row.setSpacing(4)

        status_label = QLabel("Status:")
        status_label.setStyleSheet(f"color: {THEME.text_muted}; font-size: 10px;")
        status_row.addWidget(status_label)

        self._status_combo = QComboBox()
        self._status_combo.addItems(["All", "Active", "Queued", "Completed", "Failed"])
        self._status_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {THEME.bg_dark};
                border: 1px solid {THEME.border};
                border-radius: 3px;
                padding: 2px 6px;
                font-size: 10px;
                min-height: 20px;
            }}
        """)
        self._status_combo.currentIndexChanged.connect(self.filter_changed.emit)
        status_row.addWidget(self._status_combo, 1)
        layout.addLayout(status_row)

    @property
    def search_text(self) -> str:
        return self._search.text()

    @property
    def status_filter(self) -> str:
        return self._status_combo.currentText()


class ViewToggle(QWidget):
    """Toggle between Jobs and Robots view."""

    view_changed = Signal(str)  # "jobs" or "robots"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        self._btn_group = QButtonGroup(self)

        self._jobs_btn = QToolButton()
        self._jobs_btn.setText("Jobs")
        self._jobs_btn.setCheckable(True)
        self._jobs_btn.setChecked(True)
        self._jobs_btn.clicked.connect(lambda: self.view_changed.emit("jobs"))
        self._setup_toggle_button(self._jobs_btn)
        layout.addWidget(self._jobs_btn)
        self._btn_group.addButton(self._jobs_btn)

        self._robots_btn = QToolButton()
        self._robots_btn.setText("Robots")
        self._robots_btn.setCheckable(True)
        self._robots_btn.clicked.connect(lambda: self.view_changed.emit("robots"))
        self._setup_toggle_button(self._robots_btn)
        layout.addWidget(self._robots_btn)
        self._btn_group.addButton(self._robots_btn)

        self._pools_btn = QToolButton()
        self._pools_btn.setText("Pools")
        self._pools_btn.setCheckable(True)
        self._pools_btn.clicked.connect(lambda: self.view_changed.emit("pools"))
        self._setup_toggle_button(self._pools_btn)
        layout.addWidget(self._pools_btn)
        self._btn_group.addButton(self._pools_btn)

    def _setup_toggle_button(self, btn: QToolButton):
        btn.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                color: {THEME.text_secondary};
                border: none;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 500;
            }}
            QToolButton:hover {{
                background-color: {THEME.bg_hover};
            }}
            QToolButton:checked {{
                background-color: {THEME.accent_primary};
                color: {THEME.text_primary};
            }}
        """)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


class TreeNavigationPanel(QWidget):
    """
    Left navigation panel with hierarchical tree view.
    Shows Jobs by status/priority or Robots by pool/status.
    """

    job_selected = Signal(str)      # job_id
    robot_selected = Signal(str)    # robot_id
    pool_selected = Signal(str)     # pool_name
    filter_changed = Signal(dict)   # filter params

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_view = "jobs"
        self._jobs_data: List[Dict] = []
        self._robots_data: List[Dict] = []
        self._pools_data: List[str] = []
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

        # View toggle (Jobs | Robots | Pools)
        self._view_toggle = ViewToggle()
        self._view_toggle.view_changed.connect(self._on_view_changed)
        layout.addWidget(self._view_toggle)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {THEME.border_dark};")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # Filter bar
        self._filter_bar = FilterBar()
        self._filter_bar.filter_changed.connect(self._apply_filter)
        layout.addWidget(self._filter_bar)

        # Tree widget
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setRootIsDecorated(True)
        self._tree.setIndentation(16)
        self._tree.setAnimated(True)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tree.setExpandsOnDoubleClick(True)
        self._tree.itemClicked.connect(self._on_item_clicked)
        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {THEME.bg_panel};
                border: none;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 4px 4px;
                border-bottom: 1px solid {THEME.border_dark};
            }}
            QTreeWidget::item:hover {{
                background-color: {THEME.bg_hover};
            }}
            QTreeWidget::item:selected {{
                background-color: {THEME.bg_selected};
            }}
            QTreeWidget::branch {{
                background-color: transparent;
            }}
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {{
                border-image: none;
                image: none;
            }}
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {{
                border-image: none;
                image: none;
            }}
        """)
        layout.addWidget(self._tree, 1)

        # Stats footer
        self._stats_label = QLabel()
        self._stats_label.setStyleSheet(f"""
            QLabel {{
                background-color: {THEME.bg_header};
                color: {THEME.text_muted};
                padding: 6px 8px;
                font-size: 10px;
                border-top: 1px solid {THEME.border_dark};
            }}
        """)
        self._update_stats()
        layout.addWidget(self._stats_label)

        # Initial view
        self._build_jobs_tree()

    def _on_view_changed(self, view: str):
        self._current_view = view
        self._tree.clear()
        if view == "jobs":
            self._build_jobs_tree()
        elif view == "robots":
            self._build_robots_tree()
        else:
            self._build_pools_tree()
        self._update_stats()

    def _build_jobs_tree(self):
        """Build job tree organized by status."""
        self._tree.clear()

        # Group by status
        status_groups = {
            "Active": {"icon": "▶", "color": THEME.job_running, "statuses": ["running"]},
            "Queued": {"icon": "⏳", "color": THEME.job_queued, "statuses": ["pending", "queued"]},
            "Completed": {"icon": "✓", "color": THEME.job_completed, "statuses": ["completed"]},
            "Failed": {"icon": "✗", "color": THEME.job_failed, "statuses": ["failed", "timeout"]},
            "Suspended": {"icon": "⏸", "color": THEME.job_suspended, "statuses": ["cancelled", "suspended"]},
        }

        for group_name, group_info in status_groups.items():
            jobs_in_group = [
                j for j in self._jobs_data
                if j.get("status", "").lower() in group_info["statuses"]
            ]
            count = len(jobs_in_group)

            # Group header
            group_item = QTreeWidgetItem()
            group_item.setText(0, f"{group_info['icon']} {group_name} ({count})")
            group_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "group", "name": group_name})
            group_item.setForeground(0, QBrush(QColor(group_info["color"])))
            font = group_item.font(0)
            font.setBold(True)
            group_item.setFont(0, font)
            self._tree.addTopLevelItem(group_item)

            # Jobs in group
            for job in jobs_in_group:
                job_item = QTreeWidgetItem()
                job_name = job.get("workflow_name", "Unknown")
                progress = job.get("progress", 0)
                job_item.setText(0, f"  {job_name} [{progress}%]")
                job_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "job", "id": job.get("id")})
                job_item.setForeground(0, QBrush(QColor(THEME.text_primary)))
                group_item.addChild(job_item)

            # Expand active/running by default
            if group_name in ("Active", "Queued"):
                group_item.setExpanded(True)

    def _build_robots_tree(self):
        """Build robots tree organized by status."""
        self._tree.clear()

        # Group by status
        status_groups = {
            "Online": {"icon": "●", "color": THEME.status_online},
            "Busy": {"icon": "●", "color": THEME.status_busy},
            "Offline": {"icon": "○", "color": THEME.status_offline},
            "Error": {"icon": "●", "color": THEME.status_error},
        }

        for status_name, status_info in status_groups.items():
            robots_in_group = [
                r for r in self._robots_data
                if r.get("status", "").lower() == status_name.lower()
            ]
            count = len(robots_in_group)

            if count == 0:
                continue

            # Group header
            group_item = QTreeWidgetItem()
            group_item.setText(0, f"{status_info['icon']} {status_name} ({count})")
            group_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "group", "status": status_name})
            group_item.setForeground(0, QBrush(QColor(status_info["color"])))
            font = group_item.font(0)
            font.setBold(True)
            group_item.setFont(0, font)
            self._tree.addTopLevelItem(group_item)

            # Robots in group
            for robot in robots_in_group:
                robot_item = QTreeWidgetItem()
                robot_name = robot.get("name", "Unknown")
                current = robot.get("current_jobs", 0)
                max_jobs = robot.get("max_concurrent_jobs", 1)
                robot_item.setText(0, f"  {robot_name} [{current}/{max_jobs}]")
                robot_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "robot", "id": robot.get("id")})
                robot_item.setForeground(0, QBrush(QColor(THEME.text_primary)))
                group_item.addChild(robot_item)

            group_item.setExpanded(True)

    def _build_pools_tree(self):
        """Build pools tree showing robot groups."""
        self._tree.clear()

        # Group robots by pool/environment
        pools: Dict[str, List[Dict]] = {}
        for robot in self._robots_data:
            pool = robot.get("environment", "default")
            if pool not in pools:
                pools[pool] = []
            pools[pool].append(robot)

        for pool_name, robots in pools.items():
            online_count = sum(1 for r in robots if r.get("status", "").lower() == "online")
            total_count = len(robots)

            # Pool header
            pool_item = QTreeWidgetItem()
            pool_item.setText(0, f"📁 {pool_name} ({online_count}/{total_count} online)")
            pool_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "pool", "name": pool_name})
            font = pool_item.font(0)
            font.setBold(True)
            pool_item.setFont(0, font)
            self._tree.addTopLevelItem(pool_item)

            # Robots in pool
            for robot in robots:
                status = robot.get("status", "offline").lower()
                status_color = get_status_color(status)
                status_icon = "●" if status in ("online", "busy") else "○"

                robot_item = QTreeWidgetItem()
                robot_item.setText(0, f"  {status_icon} {robot.get('name', 'Unknown')}")
                robot_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "robot", "id": robot.get("id")})
                robot_item.setForeground(0, QBrush(QColor(status_color)))
                pool_item.addChild(robot_item)

            pool_item.setExpanded(True)

    def _apply_filter(self):
        """Apply search/status filter."""
        search_text = self._filter_bar.search_text.lower()
        status_filter = self._filter_bar.status_filter.lower()

        # Rebuild with filter
        if self._current_view == "jobs":
            self._build_jobs_tree()
        elif self._current_view == "robots":
            self._build_robots_tree()
        else:
            self._build_pools_tree()

        # Apply text filter
        if search_text:
            for i in range(self._tree.topLevelItemCount()):
                group_item = self._tree.topLevelItem(i)
                for j in range(group_item.childCount()):
                    child = group_item.child(j)
                    visible = search_text in child.text(0).lower()
                    child.setHidden(not visible)

        self.filter_changed.emit({
            "search": search_text,
            "status": status_filter
        })

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        item_type = data.get("type")
        if item_type == "job":
            self.job_selected.emit(data.get("id", ""))
        elif item_type == "robot":
            self.robot_selected.emit(data.get("id", ""))
        elif item_type == "pool":
            self.pool_selected.emit(data.get("name", ""))

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        # Toggle expand/collapse for group items
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data.get("type") == "group":
            item.setExpanded(not item.isExpanded())

    def _update_stats(self):
        if self._current_view == "jobs":
            total = len(self._jobs_data)
            active = sum(1 for j in self._jobs_data if j.get("status", "").lower() == "running")
            self._stats_label.setText(f"Jobs: {total} total, {active} active")
        elif self._current_view in ("robots", "pools"):
            total = len(self._robots_data)
            online = sum(1 for r in self._robots_data if r.get("status", "").lower() == "online")
            self._stats_label.setText(f"Robots: {total} total, {online} online")

    def set_jobs(self, jobs: List[Dict]):
        """Update jobs data."""
        self._jobs_data = jobs
        if self._current_view == "jobs":
            self._build_jobs_tree()
            self._update_stats()

    def set_robots(self, robots: List[Dict]):
        """Update robots data."""
        self._robots_data = robots
        if self._current_view in ("robots", "pools"):
            if self._current_view == "robots":
                self._build_robots_tree()
            else:
                self._build_pools_tree()
            self._update_stats()

    def refresh(self):
        """Rebuild current view."""
        self._on_view_changed(self._current_view)
