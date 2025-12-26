"""
Domain entities for agent coordination and shared state management.

This module defines entities for real-time communication and
state sharing between parallel agents.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class SharedState:
    """Thread-safe shared state update from an agent."""

    agent_id: str
    state: dict[str, Any]
    timestamp: float
    phase_index: int = 0
    subtask_id: str | None = None


@dataclass
class StateSubscription:
    """A subscription to state updates from an agent."""

    subscriber_id: str
    target_agent_id: str
    filter_keys: list[str] | None = None
    timeout_seconds: float = 30.0


@dataclass
class ConditionEvent:
    """A condition that agents can wait for."""

    condition_id: str
    creator_agent_id: str
    is_set: bool = False


@dataclass
class ResourceAllocation:
    """Allocation of a resource to an agent."""

    agent_id: str
    resource_type: str
    allocation_id: str
    partition_id: str | None = None
    acquired_at: float = 0.0
