"""
CasareRPA Orchestrator Failover Module.

Provides robot failure detection and job recovery mechanisms.
"""

from casare_rpa.infrastructure.orchestrator.resilience.robot_recovery import (
    RecoveryAction,
    RecoveryResult,
    RobotFailureEvent,
    RobotRecoveryConfig,
    RobotRecoveryManager,
)

__all__ = [
    "RobotRecoveryManager",
    "RobotRecoveryConfig",
    "RobotFailureEvent",
    "RecoveryResult",
    "RecoveryAction",
]
