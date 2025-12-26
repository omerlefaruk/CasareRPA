"""
Agent coordination infrastructure.

Provides real-time state sharing and resource coordination for parallel agents.
"""

from casare_rpa.infrastructure.coordination.state_coordinator import (
    ResourceCoordinator,
    StateCoordinator,
)

__all__ = [
    "StateCoordinator",
    "ResourceCoordinator",
]
