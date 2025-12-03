"""
Event system for orchestrator API.

Re-exports monitoring events from infrastructure layer for convenient access
within the orchestrator API module.

Usage:
    from casare_rpa.infrastructure.orchestrator.api.events import (
        MonitoringEventType,
        MonitoringEvent,
        MonitoringEventBus,
        get_monitoring_event_bus,
    )
"""

from casare_rpa.infrastructure.events import (
    MonitoringEventType,
    MonitoringEvent,
    MonitoringEventBus,
    get_monitoring_event_bus,
)

# Singleton instance for module-level access
monitoring_event_bus = get_monitoring_event_bus()

__all__ = [
    "MonitoringEventType",
    "MonitoringEvent",
    "MonitoringEventBus",
    "monitoring_event_bus",
    "get_monitoring_event_bus",
]
