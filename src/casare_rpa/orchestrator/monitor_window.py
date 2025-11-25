"""
CasareRPA Orchestrator Monitor - Main Window
Deadline Monitor-style interface with dockable panels.
"""
import sys
import asyncio
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import uuid
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QToolButton, QLabel, QMenu, QStatusBar, QApplication,
    QSplitter, QStackedWidget, QMessageBox, QTabWidget
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QSize, QThread, QObject
from PySide6.QtGui import QAction, QKeySequence

try:
    import qasync
    HAS_QASYNC = True
except ImportError:
    HAS_QASYNC = False

from .theme import THEME, get_main_stylesheet
from .panels import (
    TreeNavigationPanel, JobsPanel, DetailPanel,
    RobotsPanel, DashboardPanel
)
from .models import (
    Job, Robot, Workflow, Schedule, JobStatus, RobotStatus,
    JobPriority, DashboardMetrics, JobHistoryEntry
)
from .services import OrchestratorService


def run_async(coro):
    """Run async coroutine in a new event loop (for non-async contexts)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class MainToolbar(QToolBar):
    """Main toolbar with quick actions."""

    refresh_clicked = Signal()
    new_job_clicked = Signal()
    view_changed = Signal(str)  # "jobs", "robots", "dashboard"

    def __init__(self, parent=None):
        super().__init__("Main Toolbar", parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setMovable(False)
        self.setIconSize(QSize(16, 16))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        self.setStyleSheet(f"""
            QToolBar {{
                background-color: {THEME.toolbar_bg};
                border: none;
                border-bottom: 1px solid {THEME.toolbar_border};
                padding: 4px 8px;
                spacing: 4px;
            }}
            QToolBar::separator {{
                background-color: {THEME.toolbar_separator};
                width: 1px;
                margin: 6px 12px;
            }}
            QToolButton {{
                background-color: transparent;
                border: none;
                border-radius: 3px;
                padding: 6px 12px;
                color: {THEME.text_secondary};
                font-weight: 500;
                font-size: 11px;
            }}
            QToolButton:hover {{
                background-color: {THEME.toolbar_button_hover};
                color: {THEME.text_primary};
            }}
            QToolButton:pressed {{
                background-color: {THEME.toolbar_button_pressed};
            }}
            QToolButton:checked {{
                background-color: {THEME.accent_primary};
                color: {THEME.text_primary};
            }}
        """)

        # View buttons (toggleable)
        self._dashboard_btn = self._create_view_button("Dashboard")
        self._dashboard_btn.setChecked(True)
        self.addWidget(self._dashboard_btn)

        self._jobs_btn = self._create_view_button("Jobs")
        self.addWidget(self._jobs_btn)

        self._robots_btn = self._create_view_button("Robots")
        self.addWidget(self._robots_btn)

        self.addSeparator()

        # Action buttons
        self._new_job_btn = QToolButton()
        self._new_job_btn.setText("New Job")
        self._new_job_btn.setToolTip("Create a new job (Ctrl+N)")
        self._new_job_btn.clicked.connect(self.new_job_clicked.emit)
        self.addWidget(self._new_job_btn)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(spacer.sizePolicy().horizontalPolicy(),
                            spacer.sizePolicy().verticalPolicy())
        spacer.setStyleSheet("background: transparent;")
        self.addWidget(spacer)

        # Right side actions
        self._refresh_btn = QToolButton()
        self._refresh_btn.setText("Refresh")
        self._refresh_btn.setToolTip("Refresh data (F5)")
        self._refresh_btn.clicked.connect(self.refresh_clicked.emit)
        self.addWidget(self._refresh_btn)

        # Auto-refresh indicator
        self._auto_refresh = QLabel("Auto: 5s")
        self._auto_refresh.setStyleSheet(f"""
            color: {THEME.text_muted};
            font-size: 10px;
            padding: 0 8px;
        """)
        self.addWidget(self._auto_refresh)

    def _create_view_button(self, text: str) -> QToolButton:
        btn = QToolButton()
        btn.setText(text)
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self._on_view_clicked(text.lower()))
        return btn

    def _on_view_clicked(self, view: str):
        # Uncheck others
        self._dashboard_btn.setChecked(view == "dashboard")
        self._jobs_btn.setChecked(view == "jobs")
        self._robots_btn.setChecked(view == "robots")
        self.view_changed.emit(view)

    def set_view(self, view: str):
        self._dashboard_btn.setChecked(view == "dashboard")
        self._jobs_btn.setChecked(view == "jobs")
        self._robots_btn.setChecked(view == "robots")


class OrchestratorMonitor(QMainWindow):
    """
    Main Orchestrator Monitor window.
    Deadline Monitor-style 3-column layout with dockable panels.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._service = OrchestratorService()
        self._refresh_timer: Optional[QTimer] = None
        self._current_view = "dashboard"
        self._current_job: Optional[Dict] = None
        self._current_robot: Optional[Dict] = None

        # Data caches
        self._jobs_cache: List[Dict] = []
        self._robots_cache: List[Dict] = []
        self._workflows_cache: List[Dict] = []

        # Initialize service connection (will fall back to local storage if no Supabase)
        run_async(self._service.connect())

        self._setup_ui()
        self._setup_connections()
        self._start_refresh_timer()
        self._load_initial_data()

    def _setup_ui(self):
        self.setWindowTitle("CasareRPA Orchestrator")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 850)

        # Apply theme
        self.setStyleSheet(get_main_stylesheet())

        # Central widget with stacked views
        self._central_stack = QStackedWidget()

        # Dashboard view
        self._dashboard_panel = DashboardPanel()
        self._dashboard_panel.navigate_to.connect(self._navigate_to)
        self._central_stack.addWidget(self._dashboard_panel)

        # Jobs view (with splitter for detail panel)
        jobs_widget = QWidget()
        jobs_layout = QHBoxLayout(jobs_widget)
        jobs_layout.setContentsMargins(0, 0, 0, 0)
        jobs_layout.setSpacing(0)

        self._jobs_splitter = QSplitter(Qt.Orientation.Horizontal)

        self._jobs_panel = JobsPanel()
        self._jobs_panel.job_selected.connect(self._on_job_selected)
        self._jobs_panel.job_double_clicked.connect(self._on_job_double_clicked)
        self._jobs_panel.job_action.connect(self._on_job_action)
        self._jobs_splitter.addWidget(self._jobs_panel)

        self._job_detail_panel = DetailPanel()
        self._job_detail_panel.action_requested.connect(self._on_job_action)
        self._jobs_splitter.addWidget(self._job_detail_panel)

        self._jobs_splitter.setSizes([700, 350])
        jobs_layout.addWidget(self._jobs_splitter)
        self._central_stack.addWidget(jobs_widget)

        # Robots view
        robots_widget = QWidget()
        robots_layout = QHBoxLayout(robots_widget)
        robots_layout.setContentsMargins(0, 0, 0, 0)
        robots_layout.setSpacing(0)

        self._robots_splitter = QSplitter(Qt.Orientation.Horizontal)

        self._robots_panel = RobotsPanel()
        self._robots_panel.robot_selected.connect(self._on_robot_selected)
        self._robots_panel.robot_action.connect(self._on_robot_action)
        self._robots_splitter.addWidget(self._robots_panel)

        self._robot_detail_panel = DetailPanel()
        self._robots_splitter.addWidget(self._robot_detail_panel)

        self._robots_splitter.setSizes([700, 350])
        robots_layout.addWidget(self._robots_splitter)
        self._central_stack.addWidget(robots_widget)

        # Main layout with tree navigation
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left tree navigation dock
        self._tree_panel = TreeNavigationPanel()
        self._tree_panel.setMinimumWidth(220)
        self._tree_panel.setMaximumWidth(350)
        self._tree_panel.job_selected.connect(self._on_tree_job_selected)
        self._tree_panel.robot_selected.connect(self._on_tree_robot_selected)
        self._tree_panel.filter_changed.connect(self._on_filter_changed)

        self._tree_dock = QDockWidget("Navigation", self)
        self._tree_dock.setWidget(self._tree_panel)
        self._tree_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._tree_dock)

        # Central content
        self.setCentralWidget(self._central_stack)

        # Toolbar
        self._toolbar = MainToolbar()
        self._toolbar.refresh_clicked.connect(self._refresh_data)
        self._toolbar.new_job_clicked.connect(self._show_new_job_dialog)
        self._toolbar.view_changed.connect(self._on_view_changed)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self._toolbar)

        # Status bar
        self._statusbar = QStatusBar()
        self._statusbar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {THEME.bg_header};
                border-top: 1px solid {THEME.border_dark};
                color: {THEME.text_secondary};
                font-size: 11px;
            }}
        """)
        self.setStatusBar(self._statusbar)

        self._status_label = QLabel("Ready")
        self._statusbar.addWidget(self._status_label)

        self._connection_label = QLabel("Connected")
        self._connection_label.setStyleSheet(f"color: {THEME.status_online};")
        self._statusbar.addPermanentWidget(self._connection_label)

        # Menu bar
        self._setup_menus()

    def _setup_menus(self):
        menubar = self.menuBar()
        menubar.setStyleSheet(f"""
            QMenuBar {{
                background-color: {THEME.bg_header};
                border-bottom: 1px solid {THEME.border_dark};
                padding: 2px;
            }}
            QMenuBar::item {{
                background: transparent;
                padding: 4px 10px;
            }}
            QMenuBar::item:selected {{
                background-color: {THEME.bg_hover};
            }}
        """)

        # File menu
        file_menu = menubar.addMenu("File")
        new_job = file_menu.addAction("New Job")
        new_job.setShortcut(QKeySequence.StandardKey.New)
        new_job.triggered.connect(self._show_new_job_dialog)

        file_menu.addSeparator()

        exit_action = file_menu.addAction("Exit")
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)

        # View menu
        view_menu = menubar.addMenu("View")

        dashboard_action = view_menu.addAction("Dashboard")
        dashboard_action.setShortcut("Ctrl+1")
        dashboard_action.triggered.connect(lambda: self._on_view_changed("dashboard"))

        jobs_action = view_menu.addAction("Jobs")
        jobs_action.setShortcut("Ctrl+2")
        jobs_action.triggered.connect(lambda: self._on_view_changed("jobs"))

        robots_action = view_menu.addAction("Robots")
        robots_action.setShortcut("Ctrl+3")
        robots_action.triggered.connect(lambda: self._on_view_changed("robots"))

        view_menu.addSeparator()

        refresh_action = view_menu.addAction("Refresh")
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._refresh_data)

        # Window menu
        window_menu = menubar.addMenu("Window")

        toggle_nav = window_menu.addAction("Toggle Navigation")
        toggle_nav.setShortcut("Ctrl+B")
        toggle_nav.triggered.connect(lambda: self._tree_dock.setVisible(
            not self._tree_dock.isVisible()))

    def _setup_connections(self):
        pass  # Connections are set up in _setup_ui

    def _start_refresh_timer(self):
        """Start 5-second auto-refresh timer."""
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_data)
        self._refresh_timer.start(5000)  # 5 seconds

    def _load_initial_data(self):
        """Load initial data on startup."""
        # Generate sample data for demo if no data exists
        self._ensure_sample_data()
        self._refresh_data()

    def _ensure_sample_data(self):
        """Generate sample data for demo purposes."""
        try:
            # Check if we have any robots
            robots = run_async(self._service.get_robots())
            if not robots:
                # Create sample robots
                sample_robots = [
                    {"id": str(uuid.uuid4()), "name": "Robot-Alpha", "status": "online",
                     "environment": "Production", "max_concurrent_jobs": 3, "current_jobs": 1},
                    {"id": str(uuid.uuid4()), "name": "Robot-Beta", "status": "busy",
                     "environment": "Production", "max_concurrent_jobs": 2, "current_jobs": 2},
                    {"id": str(uuid.uuid4()), "name": "Robot-Gamma", "status": "online",
                     "environment": "Development", "max_concurrent_jobs": 2, "current_jobs": 0},
                    {"id": str(uuid.uuid4()), "name": "Robot-Delta", "status": "offline",
                     "environment": "Development", "max_concurrent_jobs": 1, "current_jobs": 0},
                ]
                for robot in sample_robots:
                    robot["last_seen"] = datetime.now().isoformat()
                    self._service._local_storage.save_robot(robot)

            # Check if we have any jobs
            jobs = run_async(self._service.get_jobs())
            if not jobs:
                # Create sample jobs
                sample_jobs = [
                    {"id": str(uuid.uuid4()), "workflow_id": "wf1", "workflow_name": "Invoice Processing",
                     "robot_id": "r1", "robot_name": "Robot-Alpha", "status": "running",
                     "priority": 2, "progress": 67, "current_node": "ExtractData",
                     "duration_ms": 45000, "started_at": datetime.now().isoformat()},
                    {"id": str(uuid.uuid4()), "workflow_id": "wf2", "workflow_name": "Data Migration",
                     "robot_id": "r2", "robot_name": "Robot-Beta", "status": "running",
                     "priority": 1, "progress": 34, "current_node": "TransformData",
                     "duration_ms": 120000, "started_at": datetime.now().isoformat()},
                    {"id": str(uuid.uuid4()), "workflow_id": "wf3", "workflow_name": "Report Generation",
                     "robot_id": "", "robot_name": "", "status": "queued",
                     "priority": 1, "progress": 0, "current_node": "",
                     "duration_ms": 0},
                    {"id": str(uuid.uuid4()), "workflow_id": "wf4", "workflow_name": "Email Automation",
                     "robot_id": "", "robot_name": "", "status": "pending",
                     "priority": 3, "progress": 0, "current_node": "",
                     "duration_ms": 0},
                    {"id": str(uuid.uuid4()), "workflow_id": "wf5", "workflow_name": "Customer Onboarding",
                     "robot_id": "r1", "robot_name": "Robot-Alpha", "status": "completed",
                     "priority": 1, "progress": 100, "current_node": "",
                     "duration_ms": 180000, "completed_at": datetime.now().isoformat()},
                    {"id": str(uuid.uuid4()), "workflow_id": "wf6", "workflow_name": "File Sync",
                     "robot_id": "r3", "robot_name": "Robot-Gamma", "status": "failed",
                     "priority": 0, "progress": 45, "current_node": "UploadFiles",
                     "duration_ms": 60000, "error_message": "Connection timeout",
                     "completed_at": datetime.now().isoformat()},
                ]
                for job in sample_jobs:
                    job["created_at"] = datetime.now().isoformat()
                    job["logs"] = f"[INFO] Job started\n[INFO] Processing {job['workflow_name']}\n"
                    if job["status"] == "running":
                        job["logs"] += f"[INFO] Currently at node: {job['current_node']}\n"
                    elif job["status"] == "failed":
                        job["logs"] += f"[ERROR] {job.get('error_message', 'Unknown error')}\n"
                    self._service._local_storage.save_job(job)

        except Exception as e:
            # Silently ignore errors in sample data generation
            pass

    @Slot()
    def _refresh_data(self):
        """Refresh all data from service."""
        try:
            # Get jobs (run async in separate event loop)
            jobs_list = run_async(self._service.get_jobs())
            self._jobs_cache = [self._job_to_dict(j) for j in jobs_list]
            self._jobs_panel.set_jobs(self._jobs_cache)
            self._tree_panel.set_jobs(self._jobs_cache)

            # Get robots
            robots_list = run_async(self._service.get_robots())
            self._robots_cache = [self._robot_to_dict(r) for r in robots_list]
            self._robots_panel.set_robots(self._robots_cache)
            self._tree_panel.set_robots(self._robots_cache)

            # Update dashboard
            metrics = run_async(self._service.get_dashboard_metrics())
            self._dashboard_panel.set_metrics(metrics)

            # Get history for chart
            history = run_async(self._service.get_job_history(days=7))
            self._dashboard_panel.set_history([{
                "date": h.date,
                "total": h.total,
                "completed": h.completed,
                "failed": h.failed
            } for h in history])

            # Update status
            self._status_label.setText(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
            self._connection_label.setText("Connected")
            self._connection_label.setStyleSheet(f"color: {THEME.status_online};")

        except Exception as e:
            self._status_label.setText(f"Error: {str(e)}")
            self._connection_label.setText("Disconnected")
            self._connection_label.setStyleSheet(f"color: {THEME.status_error};")

    def _job_to_dict(self, job: Job) -> Dict:
        """Convert Job model to dict for UI."""
        return {
            "id": job.id,
            "workflow_id": job.workflow_id,
            "workflow_name": job.workflow_name,
            "robot_id": job.robot_id,
            "robot_name": job.robot_name,
            "status": job.status.value if isinstance(job.status, JobStatus) else job.status,
            "priority": job.priority.value if isinstance(job.priority, JobPriority) else job.priority,
            "progress": job.progress,
            "current_node": job.current_node,
            "duration_ms": job.duration_ms,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "logs": job.logs,
            "error_message": job.error_message,
            "result": job.result,
        }

    def _robot_to_dict(self, robot: Robot) -> Dict:
        """Convert Robot model to dict for UI."""
        return {
            "id": robot.id,
            "name": robot.name,
            "status": robot.status.value if isinstance(robot.status, RobotStatus) else robot.status,
            "environment": robot.environment,
            "max_concurrent_jobs": robot.max_concurrent_jobs,
            "current_jobs": robot.current_jobs,
            "last_seen": robot.last_seen,
            "tags": robot.tags,
            "metrics": robot.metrics,
        }

    @Slot(str)
    def _on_view_changed(self, view: str):
        """Handle view change from toolbar."""
        self._current_view = view
        self._toolbar.set_view(view)

        if view == "dashboard":
            self._central_stack.setCurrentIndex(0)
        elif view == "jobs":
            self._central_stack.setCurrentIndex(1)
        elif view == "robots":
            self._central_stack.setCurrentIndex(2)

    @Slot(str)
    def _navigate_to(self, panel: str):
        """Navigate to specific panel."""
        self._on_view_changed(panel)

    @Slot(str)
    def _on_job_selected(self, job_id: str):
        """Handle job selection in jobs panel."""
        job = next((j for j in self._jobs_cache if j.get("id") == job_id), None)
        self._current_job = job
        self._job_detail_panel.set_job(job)

    @Slot(str)
    def _on_job_double_clicked(self, job_id: str):
        """Handle job double-click - show details."""
        self._on_job_selected(job_id)

    @Slot(str)
    def _on_tree_job_selected(self, job_id: str):
        """Handle job selection in tree panel."""
        self._on_view_changed("jobs")
        self._on_job_selected(job_id)

    @Slot(str)
    def _on_robot_selected(self, robot_id: str):
        """Handle robot selection in robots panel."""
        robot = next((r for r in self._robots_cache if r.get("id") == robot_id), None)
        self._current_robot = robot
        self._robot_detail_panel.set_robot(robot)

    @Slot(str)
    def _on_tree_robot_selected(self, robot_id: str):
        """Handle robot selection in tree panel."""
        self._on_view_changed("robots")
        self._on_robot_selected(robot_id)

    @Slot(str, str)
    def _on_job_action(self, job_id: str, action: str):
        """Handle job action (cancel, retry, etc.)."""
        try:
            if action == "cancel":
                run_async(self._service.cancel_job(job_id))
                self._status_label.setText(f"Job {job_id[:8]}... cancelled")
            elif action == "retry":
                run_async(self._service.retry_job(job_id))
                self._status_label.setText(f"Job {job_id[:8]}... retried")
            elif action == "pause":
                # TODO: Implement pause
                pass
            elif action == "start":
                # TODO: Implement start now
                pass

            # Refresh data
            self._refresh_data()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to {action} job: {str(e)}")

    @Slot(str, str)
    def _on_robot_action(self, robot_id: str, action: str):
        """Handle robot action (enable, disable, etc.)."""
        try:
            if action == "disable":
                run_async(self._service.update_robot_status(robot_id, RobotStatus.OFFLINE))
                self._status_label.setText(f"Robot disabled")
            elif action == "enable":
                run_async(self._service.update_robot_status(robot_id, RobotStatus.ONLINE))
                self._status_label.setText(f"Robot enabled")

            self._refresh_data()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to {action} robot: {str(e)}")

    @Slot(dict)
    def _on_filter_changed(self, filters: Dict):
        """Handle filter changes from tree panel."""
        # TODO: Apply filters to jobs/robots panels
        pass

    @Slot()
    def _show_new_job_dialog(self):
        """Show dialog to create new job."""
        # TODO: Implement new job dialog
        QMessageBox.information(self, "New Job", "New job dialog coming soon...")

    def closeEvent(self, event):
        """Handle window close."""
        if self._refresh_timer:
            self._refresh_timer.stop()
        event.accept()


def run_orchestrator():
    """Run the orchestrator monitor application."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    window = OrchestratorMonitor()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(run_orchestrator())
