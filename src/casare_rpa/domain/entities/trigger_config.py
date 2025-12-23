"""
Domain Trigger Configuration Entity.

Defines the interface for trigger configurations without implementation details.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Protocol
import uuid

from casare_rpa.domain.value_objects.trigger_types import TriggerType


class TriggerConfigProtocol(Protocol):
    """Protocol defining trigger configuration interface."""

    id: str
    name: str
    trigger_type: TriggerType
    scenario_id: str
    workflow_id: str
    enabled: bool
    priority: int
    cooldown_seconds: int
    description: str
    config: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TriggerConfigProtocol":
        """Create from dictionary."""
        ...


@dataclass
class TriggerConfig:
    """
    Domain entity for trigger configuration.

    This is the domain-layer representation. Infrastructure layer
    may extend or adapt this for persistence needs.
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
            "last_triggered": (self.last_triggered.isoformat() if self.last_triggered else None),
            "trigger_count": self.trigger_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TriggerConfig":
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


__all__ = [
    "TriggerConfigProtocol",
    "TriggerConfig",
]
