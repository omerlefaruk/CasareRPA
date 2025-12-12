"""
Fleet Dashboard Tab Widgets.

Contains tab widgets for the Fleet Dashboard dialog:
- RobotsTabWidget: Robot management with real-time status updates
- JobsTabWidget: Job monitoring with progress bars
- SchedulesTabWidget: Schedule management
- QueuesTabWidget: Transaction queue management
- AnalyticsTabWidget: Fleet statistics and charts
- ApiKeysTabWidget: API key management
"""

from casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.constants import (
    ROBOT_STATUS_COLORS,
    JOB_STATUS_COLORS,
    REFRESH_INTERVALS,
    TAB_WIDGET_BASE_STYLE,
)
from casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.base_tab import BaseTabWidget
from casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.robots_tab import (
    RobotsTabWidget,
)
from casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.jobs_tab import JobsTabWidget
from casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.schedules_tab import (
    SchedulesTabWidget,
)
from casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.queues_tab import (
    QueuesTabWidget,
)
from casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.analytics_tab import (
    AnalyticsTabWidget,
)
from casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.api_keys_tab import (
    ApiKeysTabWidget,
)

__all__ = [
    # Constants
    "ROBOT_STATUS_COLORS",
    "JOB_STATUS_COLORS",
    "REFRESH_INTERVALS",
    "TAB_WIDGET_BASE_STYLE",
    # Base class
    "BaseTabWidget",
    # Tab widgets
    "RobotsTabWidget",
    "JobsTabWidget",
    "SchedulesTabWidget",
    "QueuesTabWidget",
    "AnalyticsTabWidget",
    "ApiKeysTabWidget",
]
