"""Orchestrator view pages."""
from .dashboard_view import DashboardView
from .robots_view import RobotsView
from .jobs_view import JobsView
from .workflows_view import WorkflowsView
from .schedules_view import SchedulesView
from .metrics_view import MetricsView

__all__ = [
    "DashboardView",
    "RobotsView",
    "JobsView",
    "WorkflowsView",
    "SchedulesView",
    "MetricsView",
]
