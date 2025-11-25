"""
CasareRPA Orchestrator Main Window.
Modern dashboard with sidebar navigation.
"""
import sys
import asyncio
from typing import Optional, Dict
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame, QSizePolicy,
    QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QFont
import qasync
from loguru import logger
from pathlib import Path

from .styles import MAIN_STYLESHEET, SIDEBAR_STYLESHEET, COLORS
from .services import OrchestratorService
from .views import DashboardView, RobotsView, JobsView, WorkflowsView, SchedulesView, MetricsView


class NavButton(QPushButton):
    """Navigation button for sidebar."""

    def __init__(self, icon: str, text: str, parent: Optional[QWidget] = None):
        super().__init__(f"  {icon}  {text}", parent)
        self.setObjectName("nav_button")
        self.setCheckable(True)
        self.setMinimumHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class Sidebar(QFrame):
    """Sidebar navigation panel."""

    navigation_changed = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(240)
        self.setStyleSheet(SIDEBAR_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(4)

        # Logo/Title
        title = QLabel("CasareRPA")
        title.setObjectName("sidebar_title")
        title.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 20px;
            font-weight: 700;
            padding: 8px 4px;
        """)
        layout.addWidget(title)

        subtitle = QLabel("Orchestrator")
        subtitle.setObjectName("sidebar_subtitle")
        subtitle.setStyleSheet(f"""
            color: {COLORS['accent_primary']};
            font-size: 12px;
            font-weight: 500;
            padding: 0 4px 16px 4px;
        """)
        layout.addWidget(subtitle)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {COLORS['border']};")
        sep.setFixedHeight(1)
        layout.addWidget(sep)
        layout.addSpacing(12)

        # Navigation buttons
        self._buttons: Dict[str, NavButton] = {}
        nav_items = [
            ("dashboard", "📊", "Dashboard"),
            ("robots", "🤖", "Robots"),
            ("jobs", "📋", "Jobs"),
            ("workflows", "⚡", "Workflows"),
            ("schedules", "📅", "Schedules"),
            ("metrics", "📈", "Metrics"),
        ]

        for name, icon, text in nav_items:
            btn = NavButton(icon, text)
            btn.clicked.connect(lambda checked, n=name: self._on_nav_click(n))
            self._buttons[name] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Footer section
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"background-color: {COLORS['border']};")
        sep2.setFixedHeight(1)
        layout.addWidget(sep2)
        layout.addSpacing(8)

        # Connection status
        self._status_label = QLabel("● Offline")
        self._status_label.setStyleSheet(f"""
            color: {COLORS['status_offline']};
            font-size: 12px;
            padding: 4px;
        """)
        layout.addWidget(self._status_label)

        # Version
        version = QLabel("v0.2.0")
        version.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 11px;
            padding: 4px;
        """)
        layout.addWidget(version)

        # Set initial selection
        self.set_active("dashboard")

    def _on_nav_click(self, name: str):
        """Handle navigation button click."""
        self.set_active(name)
        self.navigation_changed.emit(name)

    def set_active(self, name: str):
        """Set the active navigation item."""
        for btn_name, btn in self._buttons.items():
            btn.setChecked(btn_name == name)

    def set_connection_status(self, connected: bool, mode: str = "cloud"):
        """Update connection status indicator."""
        if connected:
            if mode == "local":
                self._status_label.setText("● Local Mode")
                self._status_label.setStyleSheet(f"color: {COLORS['accent_warning']}; font-size: 12px; padding: 4px;")
            else:
                self._status_label.setText("● Connected")
                self._status_label.setStyleSheet(f"color: {COLORS['status_online']}; font-size: 12px; padding: 4px;")
        else:
            self._status_label.setText("● Offline")
            self._status_label.setStyleSheet(f"color: {COLORS['status_offline']}; font-size: 12px; padding: 4px;")


class OrchestratorMainWindow(QMainWindow):
    """Main Orchestrator window with modern dashboard UI."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CasareRPA Orchestrator")
        self.resize(1400, 900)
        self.setMinimumSize(1200, 700)

        # Apply global stylesheet
        self.setStyleSheet(MAIN_STYLESHEET)

        # Initialize service
        self._service = OrchestratorService()

        # Setup UI
        self._setup_ui()

        # Connect to backend
        asyncio.get_event_loop().create_task(self._connect())

        # Auto-refresh timer
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(lambda: asyncio.get_event_loop().create_task(self._refresh_current_view()))
        self._refresh_timer.start(10000)  # Refresh every 10 seconds

    def _setup_ui(self):
        """Setup the main UI layout."""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar()
        self._sidebar.navigation_changed.connect(self._on_navigation)
        main_layout.addWidget(self._sidebar)

        # Content area
        content_container = QWidget()
        content_container.setStyleSheet(f"background-color: {COLORS['bg_dark']};")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Stacked widget for views
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background-color: {COLORS['bg_dark']};")

        # Create views
        self._dashboard_view = DashboardView(self._service)
        self._dashboard_view.navigate_to.connect(self._navigate_to)
        self._stack.addWidget(self._dashboard_view)

        self._robots_view = RobotsView(self._service)
        self._robots_view.dispatch_requested.connect(self._on_dispatch_request)
        self._stack.addWidget(self._robots_view)

        self._jobs_view = JobsView(self._service)
        self._stack.addWidget(self._jobs_view)

        self._workflows_view = WorkflowsView(self._service)
        self._stack.addWidget(self._workflows_view)

        self._schedules_view = SchedulesView(self._service)
        self._stack.addWidget(self._schedules_view)

        self._metrics_view = MetricsView(self._service)
        self._stack.addWidget(self._metrics_view)

        content_layout.addWidget(self._stack)
        main_layout.addWidget(content_container, stretch=1)

        # Map view names to indices
        self._view_map = {
            "dashboard": 0,
            "robots": 1,
            "jobs": 2,
            "workflows": 3,
            "schedules": 4,
            "metrics": 5,
        }

    def _on_navigation(self, name: str):
        """Handle navigation change."""
        if name in self._view_map:
            self._stack.setCurrentIndex(self._view_map[name])
            asyncio.get_event_loop().create_task(self._refresh_current_view())

    def _navigate_to(self, name: str):
        """Navigate to a specific view."""
        self._sidebar.set_active(name)
        self._on_navigation(name)

    def _on_dispatch_request(self, robot_id: str):
        """Handle dispatch request from robots view."""
        asyncio.get_event_loop().create_task(self._dispatch_to_robot(robot_id))

    async def _dispatch_to_robot(self, robot_id: str):
        """Open file dialog and dispatch workflow to robot."""
        workflows_dir = Path("workflows")
        if not workflows_dir.exists():
            workflows_dir = Path.cwd()

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Workflow to Dispatch",
            str(workflows_dir),
            "Workflow Files (*.json)"
        )

        if file_path:
            from .models import JobPriority
            job = await self._service.dispatch_workflow_file(
                Path(file_path),
                robot_id,
                JobPriority.NORMAL
            )
            if job:
                QMessageBox.information(
                    self, "Success",
                    f"Workflow dispatched successfully!\nJob ID: {job.id[:8]}..."
                )
                # Navigate to jobs view
                self._navigate_to("jobs")
            else:
                QMessageBox.warning(self, "Error", "Failed to dispatch workflow")

    async def _connect(self):
        """Connect to backend service."""
        success = await self._service.connect()
        mode = "local" if self._service._use_local else "cloud"
        self._sidebar.set_connection_status(success, mode)

        if success:
            # Initial data load
            await self._refresh_current_view()

    async def _refresh_current_view(self):
        """Refresh the currently visible view."""
        current_index = self._stack.currentIndex()

        if current_index == 0:
            await self._dashboard_view.refresh()
        elif current_index == 1:
            await self._robots_view.refresh()
        elif current_index == 2:
            await self._jobs_view.refresh()
        elif current_index == 3:
            await self._workflows_view.refresh()
        elif current_index == 4:
            await self._schedules_view.refresh()
        elif current_index == 5:
            await self._metrics_view.refresh()

    def closeEvent(self, event):
        """Handle window close."""
        self._refresh_timer.stop()
        event.accept()


def main():
    """Main entry point for Orchestrator."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Set application font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Setup async event loop
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Create and show main window
    window = OrchestratorMainWindow()
    window.show()

    # Run event loop
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
