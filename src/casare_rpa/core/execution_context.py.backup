"""
CasareRPA - Execution Context
Manages runtime state, variables, and shared resources during workflow execution.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from datetime import datetime
from loguru import logger
from playwright.async_api import Browser, BrowserContext, Page

from .types import ExecutionMode, NodeId

if TYPE_CHECKING:
    from ..project.project_context import ProjectContext


class ExecutionContext:
    """
    Runtime context for workflow execution.
    Stores variables, shared resources, and execution state.
    """

    def __init__(
        self,
        workflow_name: str = "Untitled",
        mode: ExecutionMode = ExecutionMode.NORMAL,
        initial_variables: Optional[Dict[str, Any]] = None,
        project_context: Optional["ProjectContext"] = None,
    ) -> None:
        """
        Initialize execution context.

        Args:
            workflow_name: Name of the workflow being executed
            mode: Execution mode (NORMAL, DEBUG, VALIDATE)
            initial_variables: Optional dict of variables to initialize (from Variables Tab)
            project_context: Optional project context for project-scoped resources
        """
        self.workflow_name = workflow_name
        self.mode = mode
        self.started_at = datetime.now()
        self.completed_at: Optional[datetime] = None

        # Store project context for credential resolution
        self._project_context = project_context

        # Variable storage - build hierarchy from project context + initial variables
        self.variables: Dict[str, Any] = self._build_variable_hierarchy(
            initial_variables
        )
        if self.variables:
            logger.info(
                f"Initialized with {len(self.variables)} variables: {list(self.variables.keys())}"
            )

        # Shared resources (Playwright instances)
        self.browser: Optional[Browser] = None
        self.browser_contexts: List[BrowserContext] = []  # Track all browser contexts
        self.pages: Dict[str, Page] = {}  # Named pages for multiple tabs
        self.active_page: Optional[Page] = None

        # Execution state
        self.current_node_id: Optional[NodeId] = None
        self.execution_path: list[NodeId] = []  # Track execution order
        self.errors: list[tuple[NodeId, str]] = []  # Track errors
        self.stopped: bool = False

        # Desktop automation context (lazy-initialized)
        self.desktop_context: Any = None

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
        """Check if a variable exists."""
        return name in self.variables

    def delete_variable(self, name: str) -> None:
        """Delete a variable from the context."""
        if name in self.variables:
            del self.variables[name]
            logger.debug(f"Variable deleted: {name}")

    def clear_variables(self) -> None:
        """Clear all variables."""
        self.variables.clear()
        logger.debug("All variables cleared")

    def _build_variable_hierarchy(
        self, runtime_vars: Optional[Dict[str, Any]]
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
            >>> context.set_variable("website", "google.com")
            >>> context.resolve_value("https://{{website}}")
            "https://google.com"
        """
        from .variable_resolver import resolve_variables

        return resolve_variables(value, self.variables)

    def set_browser(self, browser: Browser) -> None:
        """Set the active browser instance."""
        self.browser = browser
        logger.debug("Browser instance set in context")

    def get_browser(self) -> Optional[Browser]:
        """Get the active browser instance."""
        return self.browser

    def set_active_page(self, page: Page, name: str = "default") -> None:
        """
        Set the active page and store it with a name.

        Args:
            page: Playwright page object
            name: Page identifier (for multiple tabs)
        """
        self.active_page = page
        self.pages[name] = page
        logger.debug(f"Active page set: {name}")

    def get_active_page(self) -> Optional[Page]:
        """Get the currently active page."""
        return self.active_page

    def get_page(self, name: str = "default") -> Optional[Page]:
        """Get a page by name."""
        return self.pages.get(name)

    def add_page(self, page: Page, name: str) -> None:
        """
        Add a page to the context.

        Args:
            page: Playwright page object
            name: Page identifier
        """
        self.pages[name] = page
        logger.debug(f"Page added: {name}")

    def clear_pages(self) -> None:
        """Clear all pages from the context."""
        self.pages.clear()
        self.active_page = None
        logger.debug("All pages cleared")

    def add_browser_context(self, context: BrowserContext) -> None:
        """
        Track a browser context for cleanup.

        Args:
            context: Playwright browser context object
        """
        self.browser_contexts.append(context)
        logger.debug(f"Browser context added (total: {len(self.browser_contexts)})")

    def close_page(self, name: str) -> None:
        """Close and remove a named page."""
        if name in self.pages:
            del self.pages[name]
            if self.active_page == self.pages.get(name):
                self.active_page = None
            logger.debug(f"Page closed: {name}")

    def set_current_node(self, node_id: NodeId) -> None:
        """Set the currently executing node."""
        self.current_node_id = node_id
        self.execution_path.append(node_id)
        logger.debug(f"Executing node: {node_id}")

    def add_error(self, node_id: NodeId, error_message: str) -> None:
        """Record an error during execution."""
        self.errors.append((node_id, error_message))
        logger.error(f"Node {node_id} error: {error_message}")

    def stop_execution(self) -> None:
        """Signal that execution should stop."""
        self.stopped = True
        logger.warning("Execution stop requested")

    def is_stopped(self) -> bool:
        """Check if execution has been stopped."""
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
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "duration_seconds": duration,
            "nodes_executed": len(self.execution_path),
            "execution_path": self.execution_path,
            "errors": self.errors,
            "stopped": self.stopped,
            "variables_count": len(self.variables),
        }

    async def cleanup(self) -> None:
        """
        Clean up resources (close browser, pages, browser contexts, desktop context, etc.).
        Should be called when execution completes or fails.
        """
        # Clean up desktop context first (COM objects should be released early)
        if self.desktop_context is not None:
            try:
                # DesktopContext may have a cleanup method
                if hasattr(self.desktop_context, "cleanup"):
                    self.desktop_context.cleanup()
                elif hasattr(self.desktop_context, "close"):
                    self.desktop_context.close()
                logger.debug("Desktop context cleaned up")
            except Exception as e:
                logger.warning(f"Error cleaning up desktop context: {e}")
            finally:
                self.desktop_context = None

        # Close all pages
        for name, page in list(self.pages.items()):
            try:
                await page.close()
                logger.debug(f"Page '{name}' closed")
            except Exception as e:
                logger.warning(f"Error closing page '{name}': {e}")

        self.pages.clear()
        self.active_page = None

        # Close all browser contexts
        for i, context in enumerate(self.browser_contexts):
            try:
                await context.close()
                logger.debug(f"Browser context {i} closed")
            except Exception as e:
                logger.warning(f"Error closing browser context {i}: {e}")

        self.browser_contexts.clear()

        # Close browser
        if self.browser:
            try:
                await self.browser.close()
                logger.debug("Browser closed")
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
            self.browser = None

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ExecutionContext(workflow='{self.workflow_name}', "
            f"mode={self.mode.name}, "
            f"nodes_executed={len(self.execution_path)})"
        )

    # Async context manager (preferred)
    async def __aenter__(self) -> "ExecutionContext":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """Async context manager exit - ensure cleanup happens."""
        try:
            await self.cleanup()
        except Exception as e:
            logger.error(f"Error during async context cleanup: {e}")
        return False  # Don't suppress exceptions

    # Sync context manager - DEPRECATED
    # This is kept for backwards compatibility but should not be used
    def __enter__(self) -> "ExecutionContext":
        """
        DEPRECATED: Sync context manager entry.

        WARNING: Using sync context manager with ExecutionContext is strongly
        discouraged. Resources (browser, pages, desktop context) may not be
        properly cleaned up.

        Use 'async with' instead:
            async with ExecutionContext(...) as ctx:
                # Your code here

        Or call cleanup() manually:
            ctx = ExecutionContext(...)
            try:
                # Your code here
            finally:
                await ctx.cleanup()
        """
        import warnings

        warnings.warn(
            "ExecutionContext sync context manager is deprecated and may leak resources. "
            "Use 'async with ExecutionContext(...)' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        logger.warning(
            "DEPRECATED: Using sync context manager with ExecutionContext. "
            "This may leak browser/page/desktop resources. Use 'async with' instead."
        )
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """
        DEPRECATED: Sync context manager exit.

        WARNING: This method cannot reliably clean up async resources.
        If an event loop is running, cleanup is scheduled but NOT awaited,
        which means resources may leak.

        Always prefer 'async with' for proper resource management.
        """
        import asyncio

        try:
            # Try to get the running event loop
            try:
                loop = asyncio.get_running_loop()
                # Loop is running - we CANNOT reliably clean up
                # Schedule cleanup but warn loudly that it may not complete
                logger.error(
                    "CRITICAL: Sync __exit__ called while event loop is running. "
                    "Cleanup is scheduled but WILL NOT be awaited. "
                    "Resources (browser, pages) may leak! "
                    "Use 'async with ExecutionContext(...)' to prevent this."
                )
                # Create task but also try to give it a chance to run
                cleanup_task = loop.create_task(self.cleanup())
                # We can't await here, but we can at least log when it completes
                cleanup_task.add_done_callback(
                    lambda t: logger.info("Scheduled cleanup task completed")
                    if not t.exception()
                    else logger.error(f"Scheduled cleanup task failed: {t.exception()}")
                )
            except RuntimeError:
                # No running loop - we can run cleanup synchronously
                # This is the "safe" path but still not recommended
                logger.warning(
                    "Running cleanup synchronously (no event loop). "
                    "Consider using 'async with' for better resource management."
                )
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(self.cleanup())
                finally:
                    loop.close()
        except Exception as e:
            logger.error(f"Error during sync context cleanup: {e}")

        return False  # Don't suppress exceptions
