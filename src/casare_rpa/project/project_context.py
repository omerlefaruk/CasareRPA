"""
CasareRPA - Project Context (DEPRECATED)

DEPRECATED: This module is a compatibility wrapper.
The implementation has been moved to domain.services.project_context

For new code, import from:
- casare_rpa.domain.services.project_context

This module will be removed in v3.0.
"""

import warnings
from typing import TYPE_CHECKING

# Re-export from domain layer for backward compatibility
from ..domain.services.project_context import ProjectContext as _ProjectContext
from ..infrastructure.persistence.project_storage import ProjectStorage

if TYPE_CHECKING:
    from ..project.project_manager import ProjectManager


class ProjectContext(_ProjectContext):
    """
    DEPRECATED: Compatibility wrapper around domain.services.ProjectContext.

    Use casare_rpa.domain.services.ProjectContext instead.
    This class will be removed in v3.0.
    """

    @classmethod
    def from_project_manager(cls, manager: "ProjectManager") -> "ProjectContext":
        """
        Create ProjectContext from a ProjectManager instance.

        DEPRECATED: For backward compatibility only.

        Args:
            manager: ProjectManager with current project/scenario loaded

        Returns:
            ProjectContext instance

        Raises:
            ValueError: If no project is open
        """
        if manager.current_project is None:
            raise ValueError("No project is currently open")

        return cls(
            project=manager.current_project,
            scenario=manager.current_scenario,
            project_variables=manager._project_variables,
            project_credentials=manager._project_credentials,
            global_variables=manager._global_variables,
            global_credentials=manager._global_credentials,
        )

    @classmethod
    def from_project(cls, project):  # type: ignore
        """
        Create ProjectContext by loading resources from a project.

        DEPRECATED: For backward compatibility only.

        Args:
            project: Project to create context from

        Returns:
            ProjectContext instance
        """
        project_vars = ProjectStorage.load_project_variables(project)
        project_creds = ProjectStorage.load_project_credentials(project)
        global_vars = ProjectStorage.load_global_variables()
        global_creds = ProjectStorage.load_global_credentials()

        return cls(
            project=project,
            scenario=None,
            project_variables=project_vars,
            project_credentials=project_creds,
            global_variables=global_vars,
            global_credentials=global_creds,
        )


# Emit deprecation warning when module is imported
warnings.warn(
    "casare_rpa.project.project_context is deprecated. "
    "Use casare_rpa.domain.services.ProjectContext instead. "
    "This module will be removed in v3.0.",
    DeprecationWarning,
    stacklevel=2
)


__all__ = [
    "ProjectContext",
]
