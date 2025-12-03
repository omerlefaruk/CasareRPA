"""
CasareRPA Infrastructure Layer - Supabase Realtime Integration

Provides event-driven coordination for distributed robot agents using
Supabase Realtime channels:
- Postgres Changes (CDC for job inserts)
- Broadcast (control commands: cancel_job, shutdown)
- Presence (robot health tracking)

Implements a hybrid poll+subscribe model for resilience.
"""

from casare_rpa.infrastructure.realtime.supabase_realtime import (
    # Channel types
    ChannelState,
    ChannelType,
    # Handlers
    ControlCommandPayload,
    JobInsertedPayload,
    PresenceState,
    # Client
    RealtimeClient,
    RealtimeConfig,
    # Errors
    RealtimeConnectionError,
    RealtimeConnectionState,
    RealtimeSubscriptionError,
    RobotPresenceInfo,
    # Subscription manager
    SubscriptionManager,
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
