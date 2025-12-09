"""
Domain Trigger Value Objects.

Pure domain definitions for trigger types - no external dependencies.
These are the canonical definitions; triggers.base re-exports for convenience.
"""

from enum import Enum


class TriggerType(Enum):
    """Types of workflow triggers."""

    MANUAL = "manual"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"
    FILE_WATCH = "file_watch"
    EMAIL = "email"
    APP_EVENT = "app_event"
    FORM = "form"
    CHAT = "chat"
    ERROR = "error"
    WORKFLOW_CALL = "workflow_call"
    RSS_FEED = "rss_feed"
    SSE = "sse"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    GMAIL = "gmail"
    SHEETS = "sheets"
    DRIVE = "drive"
    CALENDAR = "calendar"


class TriggerStatus(Enum):
    """Trigger lifecycle states."""

    INACTIVE = "inactive"
    STARTING = "starting"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


class TriggerPriority(Enum):
    """Trigger priority levels."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


__all__ = [
    "TriggerType",
    "TriggerStatus",
    "TriggerPriority",
]
