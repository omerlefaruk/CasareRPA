"""
CasareRPA Infrastructure Layer - Supabase Realtime Integration

Provides event-driven coordination for distributed robot agents using
Supabase Realtime channels:
- Postgres Changes (CDC for job inserts)
- Broadcast (control commands: cancel_job, shutdown)
- Presence (robot health tracking)

Implements a hybrid poll+subscribe model for resilience.
"""

from .supabase_realtime import (
    # Client
    RealtimeClient,
    RealtimeConfig,
    RealtimeConnectionState,
    # Channel types
    ChannelType,
    ChannelState,
    # Handlers
    JobInsertedPayload,
    ControlCommandPayload,
    PresenceState,
    RobotPresenceInfo,
    # Subscription manager
    SubscriptionManager,
    # Errors
    RealtimeConnectionError,
    RealtimeSubscriptionError,
)

__all__ = [
    # Client
    "RealtimeClient",
    "RealtimeConfig",
    "RealtimeConnectionState",
    # Channel types
    "ChannelType",
    "ChannelState",
    # Handlers
    "JobInsertedPayload",
    "ControlCommandPayload",
    "PresenceState",
    "RobotPresenceInfo",
    # Subscription manager
    "SubscriptionManager",
    # Errors
    "RealtimeConnectionError",
    "RealtimeSubscriptionError",
]
