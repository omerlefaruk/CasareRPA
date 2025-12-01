"""
CasareRPA - Execution Context (Infrastructure Layer)

Refactored to use domain ExecutionState + infrastructure BrowserResourceManager.

Delegates to:
- ExecutionState (domain) for variables and execution tracking
- BrowserResourceManager (infrastructure) for Playwright resources
"""

import asyncio
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from datetime import datetime
from loguru import logger

from casare_rpa.domain.value_objects.types import ExecutionMode, NodeId
from casare_rpa.domain.entities.execution_state import ExecutionState
from casare_rpa.infrastructure.resources.browser_resource_manager import (
    BrowserResourceManager,
)

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page
    from casare_rpa.domain.services.project_context import ProjectContext


class ExecutionContext:
    """
    Execution context composing domain state and infrastructure resources.

    This class serves as a facade that delegates to:
    - ExecutionState (domain) for variables, execution flow, and business logic
    - BrowserResourceManager (infrastructure) for Playwright browser/page management
    - Desktop context for Windows desktop automation (lazy-initialized)

    Design Pattern: Composition over Inheritance
    This allows clear separation of concerns while maintaining backward compatibility.
    """

    def __init__(
        self,
        workflow_name: str = "Untitled",
        mode: ExecutionMode = ExecutionMode.NORMAL,
        initial_variables: Optional[Dict[str, Any]] = None,
        project_context: Optional["ProjectContext"] = None,
        pause_event: Optional[asyncio.Event] = None,
    ) -> None:
        """
        Initialize execution context.

        Args:
            workflow_name: Name of the workflow being executed
            mode: Execution mode (NORMAL, DEBUG, VALIDATE)
            initial_variables: Optional dict of variables to initialize (from Variables Tab)
            project_context: Optional project context for project-scoped resources
            pause_event: Optional event for pause/resume coordination
        """
        # Domain state (pure business logic)
        self._state = ExecutionState(
            workflow_name=workflow_name,
            mode=mode,
            initial_variables=initial_variables,
            project_context=project_context,
        )

        # Infrastructure resources (Playwright)
        self._resources = BrowserResourceManager()

        # Desktop context (lazy-initialized, not managed by domain or infrastructure layers)
        self.desktop_context: Any = None

        # Pause/resume support for mid-node operations
        self.pause_event = pause_event or asyncio.Event()
        self.pause_event.set()  # Initially not paused

    # ========================================================================
    # VARIABLE MANAGEMENT - Delegate to ExecutionState (domain)
    # ========================================================================

    def set_variable(self, name: str, value: Any) -> None:
        """
        Set a variable in the context.

        Args:
            name: Variable name
            value: Variable value
        """
        self._state.set_variable(name, value)

    def get_variable(self, name: str, default: Any = None) -> Any:
        """
        Get a variable from the context.

        Args:
            name: Variable name
            default: Default value if variable not found

        Returns:
            Variable value or default
        """
        return self._state.get_variable(name, default)

    def has_variable(self, name: str) -> bool:
        """Check if a variable exists."""
        return self._state.has_variable(name)

    def delete_variable(self, name: str) -> None:
        """Delete a variable from the context."""
        self._state.delete_variable(name)

    def clear_variables(self) -> None:
        """Clear all variables."""
        self._state.clear_variables()

    def resolve_value(self, value: Any) -> Any:
        """
        Resolve {{variable_name}} patterns in a value.

        Args:
            value: The value to resolve (only strings are processed)

        Returns:
            The resolved value with all {{variable}} patterns replaced.
        """
        return self._state.resolve_value(value)

    def resolve_credential_path(self, alias: str) -> Optional[str]:
        """
        Resolve a credential alias to its Vault path.

        Args:
            alias: Credential alias to resolve

        Returns:
            Vault path if found, None otherwise
        """
        return self._state.resolve_credential_path(alias)

    # ========================================================================
    # EXECUTION FLOW - Delegate to ExecutionState (domain)
    # ========================================================================

    def set_current_node(self, node_id: NodeId) -> None:
        """Set the currently executing node."""
        self._state.set_current_node(node_id)

    def add_error(self, node_id: NodeId, error_message: str) -> None:
        """Record an error during execution."""
        self._state.add_error(node_id, error_message)

    def stop_execution(self) -> None:
        """Signal that execution should stop."""
        self._state.stop()

    def is_stopped(self) -> bool:
        """Check if execution has been stopped."""
        return self._state.is_stopped()

    def mark_completed(self) -> None:
        """Mark the execution as completed."""
        self._state.mark_completed()

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the execution.

        Returns:
            Dictionary with execution statistics
        """
        return self._state.get_execution_summary()

    # ========================================================================
    # BROWSER MANAGEMENT - Delegate to BrowserResourceManager (infrastructure)
    # ========================================================================

    def set_browser(self, browser: "Browser") -> None:
        """Set the active browser instance."""
        self._resources.set_browser(browser)

    def get_browser(self) -> Optional["Browser"]:
        """Get the active browser instance."""
        return self._resources.get_browser()

    def add_browser_context(self, context: "BrowserContext") -> None:
        """
        Track a browser context for cleanup.

        Args:
            context: Playwright browser context object
        """
        self._resources.add_browser_context(context)

    def set_active_page(self, page: "Page", name: str = "default") -> None:
        """
        Set the active page and store it with a name.

        Args:
            page: Playwright page object
            name: Page identifier (for multiple tabs)
        """
        self._resources.set_active_page(page, name)

    def get_active_page(self) -> Optional["Page"]:
        """Get the currently active page."""
        return self._resources.get_active_page()

    def get_page(self, name: str = "default") -> Optional["Page"]:
        """Get a page by name."""
        return self._resources.get_page(name)

    def add_page(self, page: "Page", name: str) -> None:
        """
        Add a page to the context.

        Args:
            page: Playwright page object
            name: Page identifier
        """
        self._resources.add_page(page, name)

    def close_page(self, name: str) -> None:
        """Close and remove a named page."""
        self._resources.close_page(name)

    def clear_pages(self) -> None:
        """Clear all pages from the context."""
        self._resources.clear_pages()

    # ========================================================================
    # PROPERTY DELEGATION - Expose internal state for backward compatibility
    # ========================================================================

    @property
    def workflow_name(self) -> str:
        """Get workflow name."""
        return self._state.workflow_name

    @property
    def mode(self) -> ExecutionMode:
        """Get execution mode."""
        return self._state.mode

    @property
    def started_at(self) -> datetime:
        """Get execution start time."""
        return self._state.started_at

    @property
    def completed_at(self) -> Optional[datetime]:
        """Get execution completion time."""
        return self._state.completed_at

    @property
    def variables(self) -> Dict[str, Any]:
        """Get variables dict (direct access for backward compatibility)."""
        return self._state.variables

    @property
    def current_node_id(self) -> Optional[NodeId]:
        """Get current node ID."""
        return self._state.current_node_id

    @property
    def execution_path(self) -> List[NodeId]:
        """Get execution path."""
        return self._state.execution_path

    @property
    def errors(self) -> List[tuple[NodeId, str]]:
        """Get errors list."""
        return self._state.errors

    @property
    def stopped(self) -> bool:
        """Check if execution is stopped."""
        return self._state.stopped

    @property
    def browser(self) -> Optional["Browser"]:
        """Get browser instance."""
        return self._resources.browser

    @browser.setter
    def browser(self, value: Optional["Browser"]) -> None:
        """Set browser instance."""
        if value is None:
            self._resources.browser = None
        else:
            self._resources.set_browser(value)

    @property
    def browser_contexts(self) -> List["BrowserContext"]:
        """Get browser contexts list."""
        return self._resources.browser_contexts

    @property
    def pages(self) -> Dict[str, "Page"]:
        """Get pages dict."""
        return self._resources.pages

    @property
    def active_page(self) -> Optional["Page"]:
        """Get active page."""
        return self._resources.active_page

    @active_page.setter
    def active_page(self, value: Optional["Page"]) -> None:
        """Set active page."""
        self._resources.active_page = value

    @property
    def project_context(self) -> Optional["ProjectContext"]:
        """Get the project context (if any)."""
        return self._state.project_context

    @property
    def has_project_context(self) -> bool:
        """Check if a project context is available."""
        return self._state.has_project_context

    # ========================================================================
    # PAUSE/RESUME SUPPORT
    # ========================================================================

    async def pause_checkpoint(self) -> None:
        """
        Pause checkpoint for mid-node operations.

        Nodes can call this during long operations (e.g., page.goto, file downloads)
        to allow pausing mid-execution. Waits if pause_event is cleared.
        """
        if not self.pause_event.is_set():
            logger.debug("Paused at mid-node checkpoint")
            await self.pause_event.wait()
            logger.debug("Resumed from mid-node checkpoint")

    # ========================================================================
    # CLEANUP - Coordinate domain and infrastructure cleanup
    # ========================================================================

    async def cleanup(self) -> None:
        """
        Clean up resources (close browser, pages, browser contexts, desktop context, etc.).
        Should be called when execution completes or fails.
        """
        # Check if browser should be kept open
        skip_browser_close = self.get_variable("_browser_do_not_close", False)
        if skip_browser_close:
            logger.info("Skipping browser cleanup - 'do_not_close' flag is set")

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

        # Clean up Playwright resources (infrastructure)
        await self._resources.cleanup(skip_browser=skip_browser_close)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ExecutionContext(workflow='{self._state.workflow_name}', "
            f"mode={self._state.mode.name}, "
            f"nodes_executed={len(self._state.execution_path)})"
        )

    # ========================================================================
    # ASYNC CONTEXT MANAGER (preferred)
    # ========================================================================

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

    # ========================================================================
    # SYNC CONTEXT MANAGER - DEPRECATED
    # ========================================================================

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
