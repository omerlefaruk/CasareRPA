"""
CasareRPA - Trigger System

Provides event-driven workflow triggers including webhooks, scheduled tasks,
file watchers, email triggers, and more.
"""

from .base import (
    TriggerType,
    TriggerStatus,
    TriggerEvent,
    BaseTriggerConfig,
    BaseTrigger,
)
from .registry import (
    TriggerRegistry,
    register_trigger,
    get_trigger_registry,
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
