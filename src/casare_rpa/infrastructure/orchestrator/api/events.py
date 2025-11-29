"""
⚠️ DEPRECATED: Event system moved to infrastructure layer.

This module is deprecated as of v3.0. Use the infrastructure event system instead:

OLD:
    from casare_rpa.orchestrator.api.events import MonitoringEventBus

NEW:
    from casare_rpa.infrastructure.events import get_monitoring_event_bus

Migration path:
- Replace `MonitoringEventBus()` with `get_monitoring_event_bus()`
- Event types remain the same
- All functionality preserved in new location

This file will be removed in v4.0.
"""

import warnings

# Re-export from infrastructure layer for backward compatibility
from casare_rpa.infrastructure.events import (
    MonitoringEventType,
    MonitoringEvent,
    MonitoringEventBus,
    get_monitoring_event_bus,
)

# Issue deprecation warning when imported
warnings.warn(
    "casare_rpa.orchestrator.api.events is deprecated. "
    "Use casare_rpa.infrastructure.events instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Legacy singleton instance (for backward compatibility)
monitoring_event_bus = get_monitoring_event_bus()

__all__ = [
    "MonitoringEventType",
    "MonitoringEvent",
    "MonitoringEventBus",
    "monitoring_event_bus",
    "get_monitoring_event_bus",
]
