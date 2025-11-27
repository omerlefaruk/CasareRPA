"""
CasareRPA - Trigger Schema

Defines the data models for trigger configurations stored in scenarios.
These dataclasses mirror the trigger system's configuration format
and are used for persistence and serialization.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


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


def generate_trigger_id() -> str:
    """Generate unique trigger ID."""
    return f"trig_{uuid.uuid4().hex[:8]}"


@dataclass
class TriggerConfiguration:
    """
    Trigger configuration stored in Scenario.

    This dataclass represents the persistent configuration for a trigger,
    which is stored in the scenario JSON file. When a scenario is loaded,
    these configurations are used to create actual trigger instances.

    Attributes:
        id: Unique trigger identifier
        type: Trigger type (webhook, scheduled, etc.)
        name: Human-readable trigger name
        enabled: Whether the trigger is active
        priority: Execution priority (low, normal, high, critical)
        config: Type-specific configuration dictionary
        description: Optional description
        created_at: Creation timestamp
        last_triggered: Last time the trigger fired
        trigger_count: Total number of times fired
        success_count: Number of successful executions
        error_count: Number of failed executions
    """

    id: str
    type: str  # TriggerType value as string
    name: str
    enabled: bool = True
    priority: str = "normal"  # low, normal, high, critical
    config: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    created_at: Optional[str] = None
    last_triggered: Optional[str] = None
    trigger_count: int = 0
    success_count: int = 0
    error_count: int = 0

    def __post_init__(self):
        if not self.id:
            self.id = generate_trigger_id()
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON storage."""
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "enabled": self.enabled,
            "priority": self.priority,
            "config": self.config,
            "description": self.description,
            "created_at": self.created_at,
            "last_triggered": self.last_triggered,
            "trigger_count": self.trigger_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TriggerConfiguration":
        """Create from dictionary."""
        return cls(
            id=data.get("id", ""),
            type=data.get("type", "manual"),
            name=data.get("name", "Untitled Trigger"),
            enabled=data.get("enabled", True),
            priority=data.get("priority", "normal"),
            config=data.get("config", {}),
            description=data.get("description", ""),
            created_at=data.get("created_at"),
            last_triggered=data.get("last_triggered"),
            trigger_count=data.get("trigger_count", 0),
            success_count=data.get("success_count", 0),
            error_count=data.get("error_count", 0),
        )

    @classmethod
    def create_new(
        cls,
        trigger_type: str,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> "TriggerConfiguration":
        """
        Factory method to create a new trigger configuration.

        Args:
            trigger_type: Type of trigger (e.g., "webhook", "scheduled")
            name: Display name for the trigger
            config: Type-specific configuration
            **kwargs: Additional fields

        Returns:
            New TriggerConfiguration instance
        """
        return cls(
            id=generate_trigger_id(),
            type=trigger_type,
            name=name,
            config=config or {},
            **kwargs,
        )

    def get_priority_value(self) -> int:
        """Convert priority string to numeric value."""
        priority_map = {
            "low": 0,
            "normal": 1,
            "high": 2,
            "critical": 3,
        }
        return priority_map.get(self.priority.lower(), 1)

    def update_stats(self, success: bool) -> None:
        """Update trigger statistics after execution."""
        self.trigger_count += 1
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        self.last_triggered = datetime.utcnow().isoformat()

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.trigger_count == 0:
            return 0.0
        return (self.success_count / self.trigger_count) * 100

    @property
    def trigger_type_enum(self) -> TriggerType:
        """Get TriggerType enum value."""
        try:
            return TriggerType(self.type)
        except ValueError:
            return TriggerType.MANUAL

    def __repr__(self) -> str:
        """String representation."""
        return f"TriggerConfiguration(id='{self.id}', name='{self.name}', type='{self.type}')"


# ============================================================================
# TYPE-SPECIFIC CONFIGURATION HELPERS
# ============================================================================


def create_webhook_config(
    name: str,
    endpoint: str,
    auth_type: str = "none",
    secret: Optional[str] = None,
    methods: Optional[List[str]] = None,
    payload_mapping: Optional[Dict[str, str]] = None,
    **kwargs,
) -> TriggerConfiguration:
    """
    Create a webhook trigger configuration.

    Args:
        name: Trigger name
        endpoint: URL path for the webhook
        auth_type: Authentication type (none, api_key, bearer, jwt)
        secret: Secret for authentication
        methods: Allowed HTTP methods (default: ["POST"])
        payload_mapping: JSONPath mappings for payload data
        **kwargs: Additional TriggerConfiguration fields

    Returns:
        Configured TriggerConfiguration
    """
    config = {
        "endpoint": endpoint,
        "auth_type": auth_type,
        "secret": secret,
        "methods": methods or ["POST"],
        "payload_mapping": payload_mapping or {},
    }
    return TriggerConfiguration.create_new("webhook", name, config, **kwargs)


def create_scheduled_config(
    name: str,
    frequency: str = "daily",
    cron_expression: Optional[str] = None,
    time_hour: int = 9,
    time_minute: int = 0,
    timezone: str = "UTC",
    **kwargs,
) -> TriggerConfiguration:
    """
    Create a scheduled trigger configuration.

    Args:
        name: Trigger name
        frequency: Frequency type (once, hourly, daily, weekly, monthly, cron)
        cron_expression: Cron expression (for frequency="cron")
        time_hour: Hour of day (0-23)
        time_minute: Minute of hour (0-59)
        timezone: Timezone name
        **kwargs: Additional TriggerConfiguration fields

    Returns:
        Configured TriggerConfiguration
    """
    config = {
        "frequency": frequency,
        "cron_expression": cron_expression,
        "time_hour": time_hour,
        "time_minute": time_minute,
        "timezone": timezone,
    }
    return TriggerConfiguration.create_new("scheduled", name, config, **kwargs)


def create_file_watch_config(
    name: str,
    watch_path: str,
    patterns: Optional[List[str]] = None,
    recursive: bool = False,
    events: Optional[List[str]] = None,
    debounce_ms: int = 1000,
    **kwargs,
) -> TriggerConfiguration:
    """
    Create a file watch trigger configuration.

    Args:
        name: Trigger name
        watch_path: Directory path to watch
        patterns: File patterns to match (e.g., ["*.pdf", "*.csv"])
        recursive: Watch subdirectories
        events: Event types to watch (created, modified, deleted)
        debounce_ms: Debounce time in milliseconds
        **kwargs: Additional TriggerConfiguration fields

    Returns:
        Configured TriggerConfiguration
    """
    config = {
        "watch_path": watch_path,
        "patterns": patterns or ["*"],
        "recursive": recursive,
        "events": events or ["created", "modified"],
        "debounce_ms": debounce_ms,
    }
    return TriggerConfiguration.create_new("file_watch", name, config, **kwargs)


def create_email_config(
    name: str,
    provider: str = "imap",
    server: Optional[str] = None,
    port: int = 993,
    username: Optional[str] = None,
    password_credential: Optional[str] = None,
    folder: str = "INBOX",
    from_filter: Optional[str] = None,
    subject_filter: Optional[str] = None,
    poll_interval: int = 60,
    **kwargs,
) -> TriggerConfiguration:
    """
    Create an email trigger configuration.

    Args:
        name: Trigger name
        provider: Email provider (imap, graph, gmail)
        server: IMAP server hostname
        port: Server port
        username: Email username
        password_credential: Credential alias for password
        folder: Folder to monitor
        from_filter: Filter by sender
        subject_filter: Filter by subject
        poll_interval: Polling interval in seconds
        **kwargs: Additional TriggerConfiguration fields

    Returns:
        Configured TriggerConfiguration
    """
    config = {
        "provider": provider,
        "server": server,
        "port": port,
        "username": username,
        "password_credential": password_credential,
        "folder": folder,
        "from_filter": from_filter,
        "subject_filter": subject_filter,
        "poll_interval": poll_interval,
    }
    return TriggerConfiguration.create_new("email", name, config, **kwargs)


def create_error_config(
    name: str,
    source_scenario_ids: Optional[List[str]] = None,
    error_types: Optional[List[str]] = None,
    error_pattern: Optional[str] = None,
    **kwargs,
) -> TriggerConfiguration:
    """
    Create an error trigger configuration.

    Args:
        name: Trigger name
        source_scenario_ids: Scenarios to monitor for errors
        error_types: Types of errors to catch
        error_pattern: Regex pattern for error messages
        **kwargs: Additional TriggerConfiguration fields

    Returns:
        Configured TriggerConfiguration
    """
    config = {
        "source_scenario_ids": source_scenario_ids or [],
        "error_types": error_types or [],
        "error_pattern": error_pattern,
    }
    return TriggerConfiguration.create_new("error", name, config, **kwargs)


def create_workflow_call_config(
    name: str,
    call_alias: str,
    synchronous: bool = True,
    input_schema: Optional[Dict[str, Any]] = None,
    output_mapping: Optional[Dict[str, str]] = None,
    **kwargs,
) -> TriggerConfiguration:
    """
    Create a workflow call trigger configuration.

    Args:
        name: Trigger name
        call_alias: Alias for invoking this workflow
        synchronous: Wait for completion
        input_schema: Expected input parameters schema
        output_mapping: Mapping of output variables
        **kwargs: Additional TriggerConfiguration fields

    Returns:
        Configured TriggerConfiguration
    """
    config = {
        "call_alias": call_alias,
        "synchronous": synchronous,
        "input_schema": input_schema or {},
        "output_mapping": output_mapping or {},
    }
    return TriggerConfiguration.create_new("workflow_call", name, config, **kwargs)
