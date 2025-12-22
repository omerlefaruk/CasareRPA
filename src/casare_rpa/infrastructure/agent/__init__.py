"""
CasareRPA Robot Agent Infrastructure.

Provides execution infrastructure for workflow jobs.

Components:
    JobExecutor: Workflow execution engine with progress tracking
    HeartbeatService: System metrics and heartbeat monitoring

For the main RobotAgent, import from casare_rpa.robot.agent directly:
    from casare_rpa.robot.agent import RobotAgent, RobotConfig
"""

from casare_rpa.infrastructure.agent.heartbeat_service import HeartbeatService
from casare_rpa.infrastructure.agent.job_executor import (
    JobExecutionError,
    JobExecutionResult,
    JobExecutor,
)

__all__ = [
    # Execution
    "JobExecutor",
    "JobExecutionError",
    "JobExecutionResult",
    # Services
    "HeartbeatService",
]
