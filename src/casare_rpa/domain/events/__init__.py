"""
CasareRPA - Typed Domain Events (DDD 2025)

All events are immutable frozen dataclasses.

Usage:
    from casare_rpa.domain.events import (
        DomainEvent, get_event_bus,
        NodeCompleted, WorkflowStarted,
    )

    bus = get_event_bus()
    bus.subscribe(NodeCompleted, lambda e: print(f"Done: {e.node_id}"))
    bus.publish(NodeCompleted(node_id="x", execution_time_ms=100))
"""

# Base classes
from casare_rpa.domain.events.base import AggregateEvent, DomainEvent

# EventBus
from casare_rpa.domain.events.bus import (
    EventBus,
    EventHandler,
    EventLogger,
    EventRecorder,
    get_event_bus,
    reset_event_bus,
)

# Node events
from casare_rpa.domain.events.node_events import (
    NodeCompleted,
    NodeFailed,
    NodeSkipped,
    NodeStarted,
    NodeStatusChanged,
)

# Workflow events
from casare_rpa.domain.events.workflow_events import (
    NodeAdded,
    NodeConnected,
    NodeDisconnected,
    NodeRemoved,
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowPaused,
    WorkflowProgress,
    WorkflowResumed,
    WorkflowStarted,
    WorkflowStopped,
)

# System events
from casare_rpa.domain.events.system_events import (
    BrowserPageReady,
    DebugBreakpointHit,
    LogMessage,
    ResourceAcquired,
    ResourceReleased,
    VariableSet,
)

__all__ = [
    # Base
    "DomainEvent",
    "AggregateEvent",
    # EventBus
    "EventBus",
    "EventHandler",
    "get_event_bus",
    "reset_event_bus",
    "EventLogger",
    "EventRecorder",
    # Node events
    "NodeStarted",
    "NodeCompleted",
    "NodeFailed",
    "NodeSkipped",
    "NodeStatusChanged",
    # Workflow execution events
    "WorkflowStarted",
    "WorkflowCompleted",
    "WorkflowFailed",
    "WorkflowStopped",
    "WorkflowPaused",
    "WorkflowResumed",
    "WorkflowProgress",
    # Workflow structure events
    "NodeAdded",
    "NodeRemoved",
    "NodeConnected",
    "NodeDisconnected",
    # System events
    "VariableSet",
    "BrowserPageReady",
    "LogMessage",
    "DebugBreakpointHit",
    "ResourceAcquired",
    "ResourceReleased",
]
