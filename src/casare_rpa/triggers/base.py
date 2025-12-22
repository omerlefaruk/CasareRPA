"""
CasareRPA - Base Trigger Classes

Defines the abstract base classes and enums for the trigger system.
All trigger implementations should inherit from BaseTrigger.

NOTE: TriggerType, TriggerStatus, TriggerPriority are defined in
domain.value_objects.trigger_types (source of truth) and re-exported here.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional
import asyncio
import uuid

from loguru import logger

# Import from domain layer (source of truth)
from casare_rpa.domain.value_objects.trigger_types import (
    TriggerType,
    TriggerStatus,
)


@dataclass
class TriggerEvent:
    """
    Event emitted when a trigger fires.

    This event is passed to the TriggerManager which converts it
    to a job submission for the OrchestratorEngine.

    Attributes:
        trigger_id: Unique identifier of the trigger that fired
        trigger_type: Type of trigger
        workflow_id: ID of the workflow to execute
        scenario_id: ID of the scenario containing the trigger
        timestamp: When the trigger fired
        payload: Trigger-specific data to pass as workflow variables
        metadata: Additional metadata about the trigger event
        priority: Execution priority for the resulting job
    """

    trigger_id: str
    trigger_type: TriggerType
    workflow_id: str
    scenario_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # 0=LOW, 1=NORMAL, 2=HIGH, 3=CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "trigger_id": self.trigger_id,
            "trigger_type": self.trigger_type.value,
            "workflow_id": self.workflow_id,
            "scenario_id": self.scenario_id,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "metadata": self.metadata,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TriggerEvent":
        """Create from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now(timezone.utc)

        return cls(
            trigger_id=data.get("trigger_id", ""),
            trigger_type=TriggerType(data.get("trigger_type", "manual")),
            workflow_id=data.get("workflow_id", ""),
            scenario_id=data.get("scenario_id", ""),
            timestamp=timestamp,
            payload=data.get("payload", {}),
            metadata=data.get("metadata", {}),
            priority=data.get("priority", 1),
        )


@dataclass
class BaseTriggerConfig:
    """
    Base configuration for all triggers.

    Trigger-specific configurations should extend this class
    with additional fields.

    Attributes:
        id: Unique trigger identifier
        name: Human-readable trigger name
        trigger_type: Type of trigger
        scenario_id: ID of the scenario this trigger belongs to
        workflow_id: ID of the workflow to execute
        enabled: Whether the trigger is active
        priority: Execution priority (0-3)
        cooldown_seconds: Minimum time between trigger firings
        description: Optional description
        config: Type-specific configuration dictionary
    """

    id: str
    name: str
    trigger_type: TriggerType
    scenario_id: str
    workflow_id: str
    enabled: bool = True
    priority: int = 1  # TriggerPriority.NORMAL
    cooldown_seconds: int = 0
    description: str = ""
    config: Dict[str, Any] = field(default_factory=dict)

    # Tracking
    created_at: Optional[datetime] = None
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    success_count: int = 0
    error_count: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if not self.id:
            self.id = f"trig_{uuid.uuid4().hex[:8]}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "trigger_type": self.trigger_type.value,
            "scenario_id": self.scenario_id,
            "workflow_id": self.workflow_id,
            "enabled": self.enabled,
            "priority": self.priority,
            "cooldown_seconds": self.cooldown_seconds,
            "description": self.description,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None,
            "trigger_count": self.trigger_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseTriggerConfig":
        """Create from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        last_triggered = data.get("last_triggered")
        if isinstance(last_triggered, str):
            last_triggered = datetime.fromisoformat(last_triggered)

        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Untitled Trigger"),
            trigger_type=TriggerType(data.get("trigger_type", "manual")),
            scenario_id=data.get("scenario_id", ""),
            workflow_id=data.get("workflow_id", ""),
            enabled=data.get("enabled", True),
            priority=data.get("priority", 1),
            cooldown_seconds=data.get("cooldown_seconds", 0),
            description=data.get("description", ""),
            config=data.get("config", {}),
            created_at=created_at,
            last_triggered=last_triggered,
            trigger_count=data.get("trigger_count", 0),
            success_count=data.get("success_count", 0),
            error_count=data.get("error_count", 0),
        )


# Type alias for event callback
TriggerEventCallback = Callable[[TriggerEvent], Any]


class BaseTrigger(ABC):
    """
    Abstract base class for all triggers.

    Triggers are responsible for:
    1. Monitoring a specific condition or event source
    2. Emitting TriggerEvent when conditions are met
    3. Managing their own lifecycle (start/stop/pause)
    4. Validating their configuration

    Subclasses must implement:
    - start(): Begin monitoring
    - stop(): Stop monitoring
    - validate_config(): Validate trigger configuration

    Class attributes to override in subclasses:
    - trigger_type: The TriggerType enum value
    - display_name: Human-readable name for UI
    - description: Description of what this trigger does
    - icon: Icon name for UI
    - category: Category for grouping in UI
    """

    # Class-level metadata (override in subclasses)
    trigger_type: TriggerType = TriggerType.MANUAL
    display_name: str = "Base Trigger"
    description: str = "Abstract base trigger"
    icon: str = "trigger"
    category: str = "General"

    def __init__(
        self,
        config: BaseTriggerConfig,
        event_callback: Optional[TriggerEventCallback] = None,
    ) -> None:
        """
        Initialize the trigger.

        Args:
            config: Trigger configuration
            event_callback: Callback to invoke when trigger fires
        """
        self.config = config
        self._event_callback = event_callback
        self._status = TriggerStatus.INACTIVE
        self._error_message: Optional[str] = None
        self._task: Optional[asyncio.Task] = None

        logger.debug(f"Trigger initialized: {self.config.name} ({self.trigger_type.value})")

    @abstractmethod
    async def start(self) -> bool:
        """
        Start the trigger monitoring.

        Returns:
            True if started successfully, False otherwise
        """
        pass

    @abstractmethod
    async def stop(self) -> bool:
        """
        Stop the trigger monitoring.

        Returns:
            True if stopped successfully, False otherwise
        """
        pass

    async def pause(self) -> bool:
        """
        Pause the trigger (optional override).

        Returns:
            True if paused successfully
        """
        self._status = TriggerStatus.PAUSED
        logger.debug(f"Trigger paused: {self.config.name}")
        return True

    async def resume(self) -> bool:
        """
        Resume a paused trigger (optional override).

        Returns:
            True if resumed successfully
        """
        self._status = TriggerStatus.ACTIVE
        logger.debug(f"Trigger resumed: {self.config.name}")
        return True

    @abstractmethod
    def validate_config(self) -> tuple[bool, Optional[str]]:
        """
        Validate trigger configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    async def emit(
        self, payload: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Emit a trigger event.

        This method handles cooldown checking and event emission.

        Args:
            payload: Data to pass to the workflow
            metadata: Additional metadata about the trigger event

        Returns:
            True if event was emitted, False if blocked (e.g., cooldown)
        """
        # Check cooldown
        if self.config.cooldown_seconds > 0 and self.config.last_triggered:
            elapsed = (datetime.now(timezone.utc) - self.config.last_triggered).total_seconds()
            if elapsed < self.config.cooldown_seconds:
                logger.debug(
                    f"Trigger {self.config.name} in cooldown "
                    f"({self.config.cooldown_seconds - elapsed:.1f}s remaining)"
                )
                return False

        # Create trigger event
        event = TriggerEvent(
            trigger_id=self.config.id,
            trigger_type=self.trigger_type,
            workflow_id=self.config.workflow_id,
            scenario_id=self.config.scenario_id,
            payload=payload,
            metadata=metadata or {},
            priority=self.config.priority,
        )

        # Update tracking
        self.config.last_triggered = datetime.now(timezone.utc)
        self.config.trigger_count += 1

        logger.info(f"Trigger fired: {self.config.name} ({self.trigger_type.value})")

        # Invoke callback
        if self._event_callback:
            try:
                result = self._event_callback(event)
                if asyncio.iscoroutine(result):
                    await result
                self.config.success_count += 1
                return True
            except Exception as e:
                self.config.error_count += 1
                self._error_message = str(e)
                logger.error(f"Trigger callback error for {self.config.name}: {e}")
                return False

        return True

    @property
    def status(self) -> TriggerStatus:
        """Get current trigger status."""
        return self._status

    @property
    def is_active(self) -> bool:
        """Check if trigger is actively monitoring."""
        return self._status == TriggerStatus.ACTIVE

    @property
    def error_message(self) -> Optional[str]:
        """Get last error message if any."""
        return self._error_message

    def get_info(self) -> Dict[str, Any]:
        """
        Get trigger information for UI/API.

        Returns:
            Dictionary with trigger details
        """
        return {
            "id": self.config.id,
            "name": self.config.name,
            "type": self.trigger_type.value,
            "display_name": self.display_name,
            "description": self.description,
            "icon": self.icon,
            "category": self.category,
            "status": self._status.value,
            "enabled": self.config.enabled,
            "scenario_id": self.config.scenario_id,
            "workflow_id": self.config.workflow_id,
            "priority": self.config.priority,
            "cooldown_seconds": self.config.cooldown_seconds,
            "last_triggered": (
                self.config.last_triggered.isoformat() if self.config.last_triggered else None
            ),
            "trigger_count": self.config.trigger_count,
            "success_count": self.config.success_count,
            "error_count": self.config.error_count,
            "error_message": self._error_message,
            "config": self.config.config,
        }

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """
        Get JSON schema for trigger configuration.

        Override in subclasses to provide type-specific schema.

        Returns:
            JSON schema dictionary
        """
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Trigger name"},
                "enabled": {"type": "boolean", "default": True},
                "priority": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 3,
                    "default": 1,
                },
                "cooldown_seconds": {"type": "integer", "minimum": 0, "default": 0},
                "description": {"type": "string", "default": ""},
            },
            "required": ["name"],
        }

    @classmethod
    def get_display_info(cls) -> Dict[str, Any]:
        """
        Get display information for UI trigger type selector.

        Returns:
            Dictionary with display info
        """
        return {
            "type": cls.trigger_type.value,
            "display_name": cls.display_name,
            "description": cls.description,
            "icon": cls.icon,
            "category": cls.category,
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"{self.__class__.__name__}("
            f"name='{self.config.name}', "
            f"type={self.trigger_type.value}, "
            f"status={self._status.value})"
        )
