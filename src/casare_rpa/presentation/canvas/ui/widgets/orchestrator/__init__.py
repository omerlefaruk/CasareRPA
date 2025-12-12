"""
Orchestrator UI widgets for queue and schedule management.

This package provides:
- QueueManagementDock: UiPath-style transaction queue management
- ScheduleBuilderDock: Visual schedule builder with calendar
"""

from casare_rpa.presentation.canvas.ui.widgets.orchestrator.queue_dock import (
    QueueManagementDock,
)
from casare_rpa.presentation.canvas.ui.widgets.orchestrator.schedule_dock import (
    ScheduleBuilderDock,
)

__all__ = [
    "QueueManagementDock",
    "ScheduleBuilderDock",
]
