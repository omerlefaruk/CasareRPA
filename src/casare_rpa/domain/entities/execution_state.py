"""
CasareRPA - Domain Entity: Execution State
Manages runtime state and variables during workflow execution (pure domain logic).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from loguru import logger

from ..value_objects.types import NodeId, ExecutionMode

if TYPE_CHECKING:
    from ...project.project_context import ProjectContext


class ExecutionState:
    """
    Execution state entity - manages runtime state during workflow execution.

    This is a pure domain entity that tracks:
    - Variables and their values
    - Execution flow (current node, execution path, errors)
    - Execution metadata (workflow name, mode, timestamps)

    It contains NO infrastructure concerns (no Playwright, no async resources).
    """

    def __init__(
        self,
        workflow_name: str = "Untitled",
        mode: ExecutionMode = ExecutionMode.NORMAL,
        initial_variables: Optional[Dict[str, Any]] = None,
        project_context: Optional["ProjectContext"] = None,
    ) -> None:
        """
        Initialize execution state.

        Args:
            workflow_name: Name of the workflow being executed
            mode: Execution mode (NORMAL, DEBUG, VALIDATE)
            initial_variables: Optional dict of variables to initialize
            project_context: Optional project context for variable scoping
        """
        # Execution metadata
        self.workflow_name = workflow_name
        self.mode = mode
        self.started_at = datetime.now()
        self.completed_at: Optional[datetime] = None

        # Project context for credential resolution
        self._project_context = project_context

        # Variable storage - build hierarchy from project context + initial variables
        self.variables: Dict[str, Any] = self._build_variable_hierarchy(initial_variables)
        if self.variables:
            logger.info(f"Initialized with {len(self.variables)} variables: {list(self.variables.keys())}")

        # Execution flow tracking
        self.current_node_id: Optional[NodeId] = None
        self.execution_path: List[NodeId] = []  # Track execution order
        self.errors: List[tuple[NodeId, str]] = []  # Track errors
        self.stopped: bool = False

    def _build_variable_hierarchy(
        self,
        runtime_vars: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build variables dict with proper scoping hierarchy.

        Priority (highest to lowest):
        - Runtime variables (from Variables Tab)
        - Scenario variable values
        - Project variable defaults
        - Global variable defaults

        Args:
            runtime_vars: Variables from the Variables Tab

        Returns:
            Merged dictionary of variable name -> value
        """
        merged: Dict[str, Any] = {}

        if self._project_context:
            # Add global variables (lowest priority)
            merged.update(self._project_context.get_global_variables())

            # Add project variables (overrides global)
            merged.update(self._project_context.get_project_variables())

            # Add scenario variables (overrides project)
            merged.update(self._project_context.get_scenario_variables())

        # Add runtime variables (highest priority)
        if runtime_vars:
            merged.update(runtime_vars)

        return merged

    @property
    def project_context(self) -> Optional["ProjectContext"]:
        """Get the project context (if any)."""
        return self._project_context

    @property
    def has_project_context(self) -> bool:
        """Check if a project context is available."""
        return self._project_context is not None

    def set_variable(self, name: str, value: Any) -> None:
        """
        Set a variable in the context.

        Args:
            name: Variable name
            value: Variable value
        """
        self.variables[name] = value
        logger.debug(f"Variable set: {name} = {value}")

    def get_variable(self, name: str, default: Any = None) -> Any:
        """
        Get a variable from the context.

        Args:
            name: Variable name
            default: Default value if variable not found

        Returns:
            Variable value or default
        """
        return self.variables.get(name, default)

    def has_variable(self, name: str) -> bool:
        """
        Check if a variable exists.

        Args:
            name: Variable name

        Returns:
            True if variable exists, False otherwise
        """
        return name in self.variables

    def delete_variable(self, name: str) -> None:
        """
        Delete a variable from the context.

        Args:
            name: Variable name
        """
        if name in self.variables:
            del self.variables[name]
            logger.debug(f"Variable deleted: {name}")

    def clear_variables(self) -> None:
        """Clear all variables."""
        self.variables.clear()
        logger.debug("All variables cleared")

    def resolve_credential_path(self, alias: str) -> Optional[str]:
        """
        Resolve a credential alias to its Vault path.

        Uses the project context's credential binding resolution.

        Args:
            alias: Credential alias to resolve

        Returns:
            Vault path if found, None otherwise
        """
        if self._project_context:
            return self._project_context.resolve_credential_path(alias)
        return None

    def resolve_value(self, value: Any) -> Any:
        """
        Resolve {{variable_name}} patterns in a value.

        This enables UiPath/Power Automate style variable substitution
        where users can reference global variables in node properties
        using the {{variable_name}} syntax.

        Args:
            value: The value to resolve (only strings are processed)

        Returns:
            The resolved value with all {{variable}} patterns replaced.
            Non-string values are returned unchanged.

        Examples:
            >>> state.set_variable("website", "google.com")
            >>> state.resolve_value("https://{{website}}")
            "https://google.com"
        """
        from ...core.variable_resolver import resolve_variables
        return resolve_variables(value, self.variables)

    def set_current_node(self, node_id: NodeId) -> None:
        """
        Set the currently executing node.

        Args:
            node_id: ID of node being executed
        """
        self.current_node_id = node_id
        self.execution_path.append(node_id)
        logger.debug(f"Executing node: {node_id}")

    def get_execution_path(self) -> List[NodeId]:
        """
        Get the execution path (list of executed node IDs).

        Returns:
            List of node IDs in execution order
        """
        return self.execution_path.copy()

    def add_error(self, node_id: NodeId, error_message: str) -> None:
        """
        Record an error during execution.

        Args:
            node_id: ID of node that encountered the error
            error_message: Error message
        """
        self.errors.append((node_id, error_message))
        logger.error(f"Node {node_id} error: {error_message}")

    def get_errors(self) -> List[tuple[NodeId, str]]:
        """
        Get all recorded errors.

        Returns:
            List of (node_id, error_message) tuples
        """
        return self.errors.copy()

    def stop(self) -> None:
        """Signal that execution should stop."""
        self.stopped = True
        logger.warning("Execution stop requested")

    def is_stopped(self) -> bool:
        """
        Check if execution has been stopped.

        Returns:
            True if execution is stopped, False otherwise
        """
        return self.stopped

    def mark_completed(self) -> None:
        """Mark the execution as completed."""
        self.completed_at = datetime.now()
        duration = (self.completed_at - self.started_at).total_seconds()
        logger.info(f"Workflow completed in {duration:.2f} seconds")

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the execution.

        Returns:
            Dictionary with execution statistics
        """
        duration = None
        if self.completed_at:
            duration = (self.completed_at - self.started_at).total_seconds()

        return {
            "workflow_name": self.workflow_name,
            "mode": self.mode.name,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": duration,
            "nodes_executed": len(self.execution_path),
            "execution_path": self.execution_path,
            "errors": self.errors,
            "stopped": self.stopped,
            "variables_count": len(self.variables),
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ExecutionState(workflow='{self.workflow_name}', "
            f"mode={self.mode.name}, "
            f"nodes_executed={len(self.execution_path)})"
        )
