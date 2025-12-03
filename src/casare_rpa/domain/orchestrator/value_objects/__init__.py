"""Orchestrator domain value objects.

Value objects are immutable objects defined by their attributes rather than identity.
"""

from casare_rpa.domain.orchestrator.value_objects.node_robot_override import (
    NodeRobotOverride,
)
from casare_rpa.domain.orchestrator.value_objects.robot_assignment import (
    RobotAssignment,
)

__all__ = [
    "RobotAssignment",
    "NodeRobotOverride",
]
