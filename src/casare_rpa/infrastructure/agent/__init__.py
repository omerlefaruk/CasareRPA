"""
CasareRPA Robot Agent Infrastructure.

Provides components for standalone robot agents that connect to the
orchestrator and execute workflow jobs.

Components:
    RobotConfig: Configuration management with env/file loading
    RobotAgent: Main agent class for orchestrator connection
    JobExecutor: Workflow execution engine
    HeartbeatService: System metrics and heartbeat monitoring

Usage:
    from casare_rpa.infrastructure.agent import RobotConfig, RobotAgent

    # Load configuration
    config = RobotConfig.from_env()

    # Create and run agent
    agent = RobotAgent(config)
    await agent.start()
"""

from casare_rpa.infrastructure.agent.heartbeat_service import HeartbeatService
from casare_rpa.infrastructure.agent.job_executor import JobExecutionError, JobExecutor
from casare_rpa.infrastructure.agent.robot_agent import RobotAgent, RobotAgentError
from casare_rpa.infrastructure.agent.robot_config import ConfigurationError, RobotConfig

__all__ = [
    # Configuration
    "RobotConfig",
    "ConfigurationError",
    # Agent
    "RobotAgent",
    "RobotAgentError",
    # Execution
    "JobExecutor",
    "JobExecutionError",
    # Services
    "HeartbeatService",
]
