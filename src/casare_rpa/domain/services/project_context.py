"""
CasareRPA - Domain Service: Project Context
Runtime context for project-scoped resources during workflow execution.

This is a domain service that manages variable and credential scoping
across global, project, and scenario levels.
"""

from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

from casare_rpa.domain.entities.project import (
    CredentialBindingsFile,
    Project,
    Scenario,
    VariablesFile,
)


class ProjectContext:
    """
    Domain service providing runtime context for project-scoped resources.

    Manages variable and credential resolution with proper scoping:
    - Global variables (lowest priority)
    - Project variables
    - Scenario variables (highest priority)

    The context is immutable after creation - it captures a snapshot
    of the project state at the time of workflow execution.
    """

    def __init__(
        self,
        project: Project,
        scenario: Optional[Scenario] = None,
        project_variables: Optional[VariablesFile] = None,
        project_credentials: Optional[CredentialBindingsFile] = None,
        global_variables: Optional[VariablesFile] = None,
        global_credentials: Optional[CredentialBindingsFile] = None,
    ) -> None:
        """
        Initialize project context.

        Args:
            project: The project being executed
            scenario: Optional scenario being executed
            project_variables: Project-scoped variables
            project_credentials: Project-scoped credential bindings
            global_variables: Global variables
            global_credentials: Global credential bindings
        """
        self._project = project
        self._scenario = scenario
        self._project_variables = project_variables
        self._project_credentials = project_credentials
        self._global_variables = global_variables
        self._global_credentials = global_credentials

        logger.debug(
            f"Created ProjectContext for project='{project.name}', "
            f"scenario='{scenario.name if scenario else 'None'}'"
        )

    # =========================================================================
    # Properties
    # =========================================================================

    @property
    def project(self) -> Project:
        """Get the project."""
        return self._project

    @property
    def project_id(self) -> str:
        """Get the project ID."""
        return self._project.id

    @property
    def project_name(self) -> str:
        """Get the project name."""
        return self._project.name

    @property
    def scenario(self) -> Optional[Scenario]:
        """Get the scenario (if any)."""
        return self._scenario

    @property
    def scenario_id(self) -> Optional[str]:
        """Get the scenario ID (if any)."""
        return self._scenario.id if self._scenario else None

    @property
    def scenario_name(self) -> Optional[str]:
        """Get the scenario name (if any)."""
        return self._scenario.name if self._scenario else None

    # =========================================================================
    # Variable Access
    # =========================================================================

    def get_global_variables(self) -> Dict[str, Any]:
        """
        Get global variable default values.

        Returns:
            Dictionary of variable name -> default value
        """
        if self._global_variables is None:
            return {}
        return self._global_variables.get_default_values()

    def get_project_variables(self) -> Dict[str, Any]:
        """
        Get project variable default values.

        Returns:
            Dictionary of variable name -> default value
        """
        if self._project_variables is None:
            return {}
        return self._project_variables.get_default_values()

    def get_scenario_variables(self) -> Dict[str, Any]:
        """
        Get scenario variable values.

        Returns:
            Dictionary of variable name -> value
        """
        if self._scenario is None:
            return {}
        return self._scenario.variable_values.copy()

    def get_merged_variables(self) -> Dict[str, Any]:
        """
        Get merged variables from all scopes.

        Priority (highest to lowest):
        - Scenario variable values
        - Project variable defaults
        - Global variable defaults

        Returns:
            Dictionary of variable name -> value
        """
        merged = {}

        # Start with global defaults (lowest priority)
        merged.update(self.get_global_variables())

        # Override with project defaults
        merged.update(self.get_project_variables())

        # Override with scenario values (highest priority)
        merged.update(self.get_scenario_variables())

        return merged

    def get_variable(self, name: str, default: Any = None) -> Any:
        """
        Get a variable value with scope fallback.

        Checks scenario, project, then global.

        Args:
            name: Variable name
            default: Default value if not found

        Returns:
            Variable value or default
        """
        # Check scenario first
        if self._scenario and name in self._scenario.variable_values:
            return self._scenario.variable_values[name]

        # Check project
        if self._project_variables:
            var = self._project_variables.get_variable(name)
            if var:
                return var.default_value

        # Check global
        if self._global_variables:
            var = self._global_variables.get_variable(name)
            if var:
                return var.default_value

        return default

    # =========================================================================
    # Credential Access
    # =========================================================================

    def resolve_credential_path(self, alias: str) -> Optional[str]:
        """
        Resolve a credential alias to its Vault path.

        Checks scenario, project, then global bindings.

        Args:
            alias: Credential alias to resolve

        Returns:
            Vault path if found, None otherwise
        """
        # Check scenario-level bindings first
        if self._scenario:
            path = self._scenario.credential_bindings.get(alias)
            if path:
                return path

        # Check project bindings
        if self._project_credentials:
            path = self._project_credentials.resolve_vault_path(alias)
            if path:
                return path

        # Check global bindings
        if self._global_credentials:
            path = self._global_credentials.resolve_vault_path(alias)
            if path:
                return path

        return None

    def get_all_credential_aliases(self) -> Dict[str, str]:
        """
        Get all available credential aliases with their Vault paths.

        Merges global, project, and scenario bindings with proper priority.

        Returns:
            Dictionary of alias -> vault_path
        """
        aliases = {}

        # Start with global (lowest priority)
        if self._global_credentials:
            for alias, binding in self._global_credentials.bindings.items():
                aliases[alias] = binding.vault_path

        # Override with project
        if self._project_credentials:
            for alias, binding in self._project_credentials.bindings.items():
                aliases[alias] = binding.vault_path

        # Override with scenario (highest priority)
        if self._scenario:
            aliases.update(self._scenario.credential_bindings)

        return aliases

    # =========================================================================
    # Execution Settings
    # =========================================================================

    def get_timeout(self) -> int:
        """
        Get execution timeout in seconds.

        Returns scenario override if set, otherwise project default.

        Returns:
            Timeout in seconds
        """
        # Check scenario override first
        if self._scenario and self._scenario.execution_settings.timeout_override:
            return self._scenario.execution_settings.timeout_override
        # Fall back to project setting
        return self._project.settings.timeout_seconds

    def get_stop_on_error(self) -> bool:
        """
        Get stop-on-error setting from project.

        Returns:
            True if workflow should stop on error
        """
        return self._project.settings.stop_on_error

    def get_retry_count(self) -> int:
        """
        Get retry count setting from project.

        Returns:
            Number of retries for failed operations
        """
        return self._project.settings.retry_count

    def get_default_browser(self) -> str:
        """
        Get default browser setting from project.

        Returns:
            Browser name (chromium, firefox, webkit)
        """
        return self._project.settings.default_browser

    # =========================================================================
    # String Representation
    # =========================================================================

    def __repr__(self) -> str:
        """String representation."""
        scenario_part = f", scenario='{self._scenario.name}'" if self._scenario else ""
        return f"ProjectContext(project='{self._project.name}'{scenario_part})"
