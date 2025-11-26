"""
CasareRPA - Project Management Module

This module provides project management functionality including:
- Project creation, loading, and saving
- Scenario management
- Variable scope resolution
- Credential binding resolution
"""

from .project_storage import ProjectStorage
from .scenario_storage import ScenarioStorage
from .project_manager import ProjectManager
from .project_context import ProjectContext

__all__ = [
    "ProjectStorage",
    "ScenarioStorage",
    "ProjectManager",
    "ProjectContext",
]
