"""
Fleet Dashboard Tab Widgets.

Contains tab widgets for the Fleet Dashboard dialog:
- RobotsTabWidget: Robot management with real-time status updates
- JobsTabWidget: Job monitoring with progress bars
- SchedulesTabWidget: Schedule management
- AnalyticsTabWidget: Fleet statistics and charts
- ApiKeysTabWidget: API key management
"""

from .constants import (
    ROBOT_STATUS_COLORS,
    JOB_STATUS_COLORS,
    REFRESH_INTERVALS,
    TAB_WIDGET_BASE_STYLE,
)
from .base_tab import BaseTabWidget
from .robots_tab import RobotsTabWidget
from .jobs_tab import JobsTabWidget
from .schedules_tab import SchedulesTabWidget
from .analytics_tab import AnalyticsTabWidget
from .api_keys_tab import ApiKeysTabWidget

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
    "AnalyticsTabWidget",
    "ApiKeysTabWidget",
]
