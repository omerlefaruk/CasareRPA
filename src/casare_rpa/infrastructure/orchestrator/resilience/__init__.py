"""
CasareRPA Orchestrator Failover Module.

Provides robot failure detection and job recovery mechanisms.
"""

from .robot_recovery import (
    RobotRecoveryManager,
    RobotRecoveryConfig,
    RobotFailureEvent,
    RecoveryResult,
    RecoveryAction,
)

__all__ = [
    "RobotRecoveryManager",
    "RobotRecoveryConfig",
    "RobotFailureEvent",
    "RecoveryResult",
    "RecoveryAction",
]
