"""Use cases for orchestrator application layer.

This module provides application-level use cases for the orchestrator:
- ExecuteJobUseCase: Execute a job on a robot
- SubmitJobUseCase: Submit a job for cloud execution
- ExecuteLocalUseCase: Execute workflow locally without orchestrator
- AssignRobotUseCase: Assign robots to workflows and nodes
- ListRobotsUseCase: List and filter robots
"""

from casare_rpa.application.orchestrator.use_cases.execute_job import ExecuteJobUseCase
from casare_rpa.application.orchestrator.use_cases.submit_job import SubmitJobUseCase
from casare_rpa.application.orchestrator.use_cases.execute_local import (
    ExecuteLocalUseCase,
    ExecutionResult,
)
from casare_rpa.application.orchestrator.use_cases.assign_robot import (
    AssignRobotUseCase,
)
from casare_rpa.application.orchestrator.use_cases.list_robots import ListRobotsUseCase

__all__ = [
    "ExecuteJobUseCase",
    "SubmitJobUseCase",
    "ExecuteLocalUseCase",
    "ExecutionResult",
    "AssignRobotUseCase",
    "ListRobotsUseCase",
]
