"""
CasareRPA - Execution Context
Manages runtime state, variables, and shared resources during workflow execution.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from loguru import logger
from playwright.async_api import Browser, BrowserContext, Page

from .types import ExecutionMode, NodeId


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
    ) -> None:
        """
        Initialize execution context.

        Args:
            workflow_name: Name of the workflow being executed
            mode: Execution mode (NORMAL, DEBUG, VALIDATE)
            initial_variables: Optional dict of variables to initialize (from Variables Tab)
        """
        self.workflow_name = workflow_name
        self.mode = mode
        self.started_at = datetime.now()
        self.completed_at: Optional[datetime] = None

        # Variable storage - initialize with provided variables if any
        self.variables: Dict[str, Any] = initial_variables.copy() if initial_variables else {}
        if initial_variables:
            logger.info(f"Initialized with {len(initial_variables)} variables: {list(initial_variables.keys())}")

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

        logger.info(f"Execution context created for workflow: {workflow_name}")

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
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
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
        logger.info("Cleaning up execution context...")

        # Clean up desktop context first (COM objects should be released early)
        if self.desktop_context is not None:
            try:
                # DesktopContext may have a cleanup method
                if hasattr(self.desktop_context, 'cleanup'):
                    self.desktop_context.cleanup()
                elif hasattr(self.desktop_context, 'close'):
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

        logger.info("Context cleanup completed")

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

    # Sync context manager (for backwards compatibility)
    def __enter__(self) -> "ExecutionContext":
        """Sync context manager entry (prefer async with instead)."""
        logger.warning(
            "Using sync context manager with ExecutionContext. "
            "Consider using 'async with' for proper cleanup."
        )
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        """
        Sync context manager exit.

        Note: This attempts to run async cleanup synchronously. For proper
        resource cleanup, use 'async with' instead.
        """
        import asyncio

        try:
            # Try to get the running event loop
            try:
                loop = asyncio.get_running_loop()
                # Loop is running - schedule cleanup as a task
                # This is not ideal as it won't wait for cleanup to complete
                logger.warning(
                    "Sync __exit__ called while event loop is running. "
                    "Cleanup will be scheduled but may not complete before exit."
                )
                loop.create_task(self.cleanup())
            except RuntimeError:
                # No running loop - we can run cleanup synchronously
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(self.cleanup())
                finally:
                    loop.close()
        except Exception as e:
            logger.error(f"Error during sync context cleanup: {e}")

        return False  # Don't suppress exceptions
