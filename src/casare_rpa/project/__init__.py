"""
CasareRPA - Project Management Module

This module provides project management functionality including:
- Project creation, loading, and saving
- Scenario management
- Variable scope resolution
- Credential binding resolution
"""

# Import from infrastructure layer (canonical location)
from ..infrastructure.persistence.project_storage import ProjectStorage

# Import from domain layer (canonical location)
from ..domain.services.project_context import ProjectContext

# Local modules (not deprecated)
from .scenario_storage import ScenarioStorage
from .project_manager import ProjectManager

__all__ = [
    "ProjectStorage",
    "ScenarioStorage",
    "ProjectManager",
    "ProjectContext",
]
