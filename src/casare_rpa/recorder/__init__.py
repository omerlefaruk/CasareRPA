"""
Workflow recording module.

This module provides functionality for recording user interactions
and automatically generating workflow nodes from those interactions.
"""

from .recording_session import RecordingSession, RecordedAction, ActionType
from .workflow_generator import WorkflowGenerator

__all__ = [
    'RecordingSession',
    'RecordedAction',
    'ActionType',
    'WorkflowGenerator',
]
