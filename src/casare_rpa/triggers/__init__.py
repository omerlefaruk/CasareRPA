"""
CasareRPA - Trigger System

Provides event-driven workflow triggers including webhooks, scheduled tasks,
file watchers, email triggers, and more.
"""

from casare_rpa.triggers.base import (
    BaseTrigger,
    BaseTriggerConfig,
    TriggerEvent,
    TriggerStatus,
    TriggerType,
)
from casare_rpa.triggers.registry import (
    TriggerRegistry,
    get_trigger_registry,
    register_trigger,
)

__all__ = [
    # Base classes
    "TriggerType",
    "TriggerStatus",
    "TriggerEvent",
    "BaseTriggerConfig",
    "BaseTrigger",
    # Registry
    "TriggerRegistry",
    "register_trigger",
    "get_trigger_registry",
]
