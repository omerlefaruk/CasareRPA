"""
Robot Metrics View for Orchestrator.

Displays real-time robot metrics and health information.
"""

import asyncio
from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import QTimer
from loguru import logger

from ..panels.metrics_panel import MetricsPanel
from ..services import OrchestratorService


class MetricsView(QWidget):
    """
    View for displaying robot metrics.

    Shows:
    - Summary metrics (total robots, online, busy)
    - Individual robot cards with CPU/memory usage
    - Job execution statistics per robot
    """

    def __init__(self, service: OrchestratorService, parent=None):
        super().__init__(parent)
        self._service = service
        self._setup_ui()

        # Auto-refresh timer (more frequent for metrics)
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(lambda: asyncio.get_event_loop().create_task(self.refresh()))
        self._refresh_timer.start(5000)  # Refresh every 5 seconds

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._metrics_panel = MetricsPanel()
        layout.addWidget(self._metrics_panel)

    async def refresh(self):
        """Refresh metrics data from service."""
        try:
            robots = await self._service.get_robots()

            # Convert Robot objects to dicts for the panel
            robot_data = []
            for robot in robots:
                robot_dict = {
                    "id": robot.id,
                    "name": robot.name,
                    "status": robot.status.value,
                    "last_seen": robot.last_seen,
                    "metrics": robot.metrics or {},
                    "max_concurrent_jobs": robot.max_concurrent_jobs,
                    "current_jobs": robot.current_jobs,
                }
                robot_data.append(robot_dict)

            self._metrics_panel.set_robots(robot_data)

        except Exception as e:
            logger.error(f"Failed to refresh metrics: {e}")

    def showEvent(self, event):
        """Start refresh timer when view becomes visible."""
        super().showEvent(event)
        if not self._refresh_timer.isActive():
            self._refresh_timer.start(5000)
        asyncio.get_event_loop().create_task(self.refresh())

    def hideEvent(self, event):
        """Stop refresh timer when view is hidden."""
        super().hideEvent(event)
        self._refresh_timer.stop()
