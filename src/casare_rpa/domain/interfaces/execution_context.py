"""
Domain Layer - Execution Context Interface.

This module defines the IExecutionContext protocol that allows the Application
layer to work with execution contexts without importing from Infrastructure.

The Infrastructure layer provides the concrete ExecutionContext implementation
that fulfills this protocol.

Design Pattern: Dependency Inversion Principle
- Application depends on this abstraction (IExecutionContext)
- Infrastructure implements this abstraction (ExecutionContext)
- No direct Application -> Infrastructure imports

Usage:
    from casare_rpa.domain.interfaces import IExecutionContext

    class MyUseCase:
        def __init__(self, context: IExecutionContext):
            self.context = context
"""

from typing import Any, Dict, List, Optional, Protocol, TYPE_CHECKING
from abc import abstractmethod

if TYPE_CHECKING:
    from casare_rpa.domain.value_objects.types import ExecutionMode, NodeId


class IExecutionContext(Protocol):
    """
    Protocol defining the execution context interface.

    This protocol enables Application layer code to work with execution
    contexts without importing the concrete Infrastructure implementation.

    The Infrastructure ExecutionContext class implements this protocol.

    Attributes:
        workflow_name: Name of the workflow being executed
        mode: Execution mode (NORMAL, DEBUG, VALIDATE)
        variables: Direct access to variables dict
        resources: Resource registry for nodes
    """

    # ========================================================================
    # PROPERTIES - Read-only access to execution state
    # ========================================================================

    @property
    def workflow_name(self) -> str:
        """Get workflow name."""
        ...

    @property
    def mode(self) -> "ExecutionMode":
        """Get execution mode."""
        ...

    @property
    def variables(self) -> Dict[str, Any]:
        """Get variables dict (direct access for backward compatibility)."""
        ...

    @property
    def resources(self) -> Dict[str, Any]:
        """Get resources dictionary for storing/retrieving resources."""
        ...

    @property
    def has_project_context(self) -> bool:
        """Check if a project context is available."""
        ...

    @property
    def project_context(self) -> Optional[Any]:
        """Get the project context (if any)."""
        ...

    @property
    def current_node_id(self) -> Optional["NodeId"]:
        """Get current node ID."""
        ...

    @property
    def execution_path(self) -> List["NodeId"]:
        """Get execution path (list of executed node IDs)."""
        ...

    @property
    def stopped(self) -> bool:
        """Check if execution is stopped."""
        ...

    # ========================================================================
    # VARIABLE MANAGEMENT
    # ========================================================================

    def set_variable(self, name: str, value: Any) -> None:
        """
        Set a variable in the context.

        Args:
            name: Variable name
            value: Variable value
        """
        ...

    def get_variable(self, name: str, default: Any = None) -> Any:
        """
        Get a variable from the context.

        Args:
            name: Variable name
            default: Default value if variable not found

        Returns:
            Variable value or default
        """
        ...

    def has_variable(self, name: str) -> bool:
        """Check if a variable exists."""
        ...

    def delete_variable(self, name: str) -> None:
        """Delete a variable from the context."""
        ...

    def resolve_value(self, value: Any) -> Any:
        """
        Resolve {{variable_name}} patterns in a value.

        Args:
            value: The value to resolve (only strings are processed)

        Returns:
            The resolved value with all {{variable}} patterns replaced.
        """
        ...

    # ========================================================================
    # EXECUTION FLOW CONTROL
    # ========================================================================

    def set_current_node(self, node_id: "NodeId") -> None:
        """Set the currently executing node."""
        ...

    def add_error(self, node_id: "NodeId", error_message: str) -> None:
        """Record an error during execution."""
        ...

    def stop_execution(self) -> None:
        """Signal that execution should stop."""
        ...

    def is_stopped(self) -> bool:
        """Check if execution has been stopped."""
        ...

    def mark_completed(self) -> None:
        """Mark the execution as completed."""
        ...

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the execution.

        Returns:
            Dictionary with execution statistics
        """
        ...

    # ========================================================================
    # BROWSER MANAGEMENT (Optional - for browser workflows)
    # ========================================================================

    def get_active_page(self) -> Optional[Any]:
        """Get the currently active page (Playwright Page object)."""
        ...

    def set_active_page(self, page: Any, name: str = "default") -> None:
        """
        Set the active page and store it with a name.

        Args:
            page: Playwright page object
            name: Page identifier (for multiple tabs)
        """
        ...

    def get_page(self, name: str = "default") -> Optional[Any]:
        """Get a page by name."""
        ...

    def add_page(self, page: Any, name: str) -> None:
        """
        Add a page to the context.

        Args:
            page: Playwright page object
            name: Page identifier
        """
        ...

    # ========================================================================
    # PARALLEL EXECUTION SUPPORT
    # ========================================================================

    def clone_for_branch(self, branch_name: str) -> "IExecutionContext":
        """
        Create an isolated context copy for parallel branch execution.

        Each parallel branch gets its own variable namespace to prevent
        conflicts during concurrent execution.

        Args:
            branch_name: Name of the branch (used for variable namespacing)

        Returns:
            New IExecutionContext with copied variables and shared resources
        """
        ...

    def create_workflow_context(self, workflow_name: str) -> "IExecutionContext":
        """
        Create context for parallel workflow with SHARED variables but SEPARATE browser.

        Used for multi-workflow parallel execution.

        Args:
            workflow_name: Name identifier for this workflow

        Returns:
            New IExecutionContext with shared variables and separate browser
        """
        ...

    def merge_branch_results(
        self, branch_name: str, branch_variables: Dict[str, Any]
    ) -> None:
        """
        Merge variables from a completed branch back to main context.

        Args:
            branch_name: Name of the branch
            branch_variables: Variables from the branch context
        """
        ...

    # ========================================================================
    # LIFECYCLE MANAGEMENT
    # ========================================================================

    async def cleanup(self) -> None:
        """
        Clean up resources (close browser, pages, desktop context, etc.).
        Should be called when execution completes or fails.
        """
        ...

    async def pause_checkpoint(self) -> None:
        """
        Pause checkpoint for mid-node operations.

        Nodes can call this during long operations to allow pausing mid-execution.
        """
        ...


__all__ = ["IExecutionContext"]
