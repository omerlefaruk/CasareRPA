"""Orchestrator domain value objects.

Value objects are immutable objects defined by their attributes rather than identity.
"""

from .robot_assignment import RobotAssignment
from .node_robot_override import NodeRobotOverride

__all__ = [
    "RobotAssignment",
    "NodeRobotOverride",
]
