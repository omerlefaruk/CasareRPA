"""
Infrastructure event system for real-time monitoring.

Provides event bus for monitoring dashboard updates (job status, robot heartbeats, queue metrics).
"""

from casare_rpa.infrastructure.events.monitoring_events import (
    MonitoringEvent,
    MonitoringEventBus,
    MonitoringEventType,
    get_monitoring_event_bus,
)

__all__ = [
    "MonitoringEventType",
    "MonitoringEvent",
    "MonitoringEventBus",
    "get_monitoring_event_bus",
]
