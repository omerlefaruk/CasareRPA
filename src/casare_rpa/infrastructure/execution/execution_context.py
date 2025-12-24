"""
CasareRPA - Execution Context (Infrastructure Layer)

Refactored to use domain ExecutionState + infrastructure BrowserResourceManager.

Delegates to:
- ExecutionState (domain) for variables and execution tracking
- BrowserResourceManager (infrastructure) for Playwright resources
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, Any

from loguru import logger

from casare_rpa.domain.entities.execution_state import ExecutionState
from casare_rpa.domain.value_objects.types import ExecutionMode, NodeId
from casare_rpa.infrastructure.execution.variable_cache import (
    CacheStats,
    VariableResolutionCache,
)
from casare_rpa.infrastructure.resources.browser_resource_manager import (
    BrowserResourceManager,
)

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page

    from casare_rpa.domain.services.project_context import ProjectContext
    from casare_rpa.infrastructure.security.credential_provider import (
        VaultCredentialProvider,
    )


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
        initial_variables: dict[str, Any] | None = None,
        project_context: ProjectContext | None = None,
        pause_event: asyncio.Event | None = None,
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

        # Variable resolution cache for performance
        self._var_cache = VariableResolutionCache(max_size=500)

        # Desktop context (lazy-initialized, not managed by domain or infrastructure layers)
        self.desktop_context: Any = None

        # Pause/resume support for mid-node operations
        self.pause_event = pause_event or asyncio.Event()
        self.pause_event.set()  # Initially not paused

        # Resource registry for nodes (telegram client, credential provider, etc.)
        self.resources: dict[str, Any] = {}

        # Credential provider (lazy-initialized)
        self._credential_provider: VaultCredentialProvider | None = None

    # ========================================================================
    # VARIABLE MANAGEMENT - Delegate to ExecutionState (domain)
    # ========================================================================

    def set_variable(self, name: str, value: Any) -> None:
        """
        Set a variable in the context.

        Publishes VARIABLE_SET event after successfully setting the variable.
        Notifies the resolution cache of the change for invalidation.

        Args:
            name: Variable name
            value: Variable value
        """
        self._state.set_variable(name, value)

        # Notify cache of variable change for invalidation
        self._var_cache.notify_variable_changed(name)

        # Publish VARIABLE_SET event (skip internal variables starting with _)
        if not name.startswith("_"):
            try:
                from casare_rpa.domain.events import VariableSet, get_event_bus

                event_bus = get_event_bus()
                event_bus.publish(
                    VariableSet(
                        variable_name=name,
                        value=value,
                        workflow_id=self._state.workflow_name,
                    )
                )
            except Exception:
                pass  # Don't break execution for event failures

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
        self._var_cache.notify_variable_changed(name)

    def clear_variables(self) -> None:
        """Clear all variables and reset resolution cache."""
        self._state.clear_variables()
        self._var_cache.clear()

    def resolve_value(self, value: Any) -> Any:
        """
        Resolve variable patterns in a value.
        Supports {{var}}, ${var}, %var%, and {{$secret:id}}.
        Handles strings, dictionaries, and lists recursively.

        Uses caching for improved performance on repeated resolutions (strings only).

        Args:
            value: The value to resolve

        Returns:
            The resolved value.
        """
        # Fast path for non-resolvable types
        if not isinstance(value, str | dict | list):
            return value

        # For strings, check for secret patterns first
        if isinstance(value, str):
            # Resolve {{$secret:id}} patterns
            value = self._resolve_secrets(value)

            # No markers? Skip resolution
            if not any(m in value for m in ("{{", "${", "%")):
                return value

            found, cached_result = self._var_cache.get_cached(value, self._state.variables)
            if found:
                return cached_result

        # Resolve using domain state
        result = self._state.resolve_value(value)

        # Cache string results
        if isinstance(value, str):
            self._var_cache.cache_result(value, self._state.variables, result)

        return result

    def _resolve_secrets(self, value: str) -> str:
        """
        Resolve {{$secret:credential_id}} patterns in a string.

        Looks up encrypted secrets from the credential store and replaces
        the pattern with the decrypted value.

        Args:
            value: String potentially containing secret patterns

        Returns:
            String with secret patterns replaced by decrypted values
        """
        import re

        # Fast path: check if secret pattern exists before regex
        if "{{$secret:" not in value:
            return value

        # Pattern: {{$secret:credential_id}}
        secret_pattern = re.compile(r"\{\{\$secret:([^}]+)\}\}")

        def replace_secret(match: re.Match) -> str:
            credential_id = match.group(1).strip()
            try:
                from casare_rpa.infrastructure.security.credential_store import (
                    get_credential_store,
                )

                store = get_credential_store()
                decrypted = store.decrypt_inline_secret(credential_id)
                if decrypted is not None:
                    logger.debug(f"Resolved secret: {credential_id[:8]}...")
                    return decrypted
                else:
                    logger.warning(f"Secret not found: {credential_id}")
                    return match.group(0)  # Keep original if not found
            except Exception as e:
                logger.error(f"Failed to resolve secret {credential_id}: {e}")
                return match.group(0)  # Keep original on error

        return secret_pattern.sub(replace_secret, value)

    def get_resolution_cache_stats(self) -> CacheStats:
        """
        Get statistics from the variable resolution cache.

        Returns:
            CacheStats with hits, misses, invalidations, evictions
        """
        return self._var_cache.get_stats()

    def resolve_credential_path(self, alias: str) -> str | None:
        """
        Resolve a credential alias to its Vault path.

        Args:
            alias: Credential alias to resolve

        Returns:
            Vault path if found, None otherwise
        """
        return self._state.resolve_credential_path(alias)

    # ========================================================================
    # CREDENTIAL MANAGEMENT
    # ========================================================================

    async def get_credential_provider(self) -> VaultCredentialProvider | None:
        """
        Get or create the credential provider.

        Lazy-initializes the provider on first access and registers
        project credential bindings if available.

        Returns:
            VaultCredentialProvider instance or None if unavailable
        """
        if self._credential_provider is not None:
            return self._credential_provider

        # Check if already in resources
        if "credential_provider" in self.resources:
            self._credential_provider = self.resources["credential_provider"]
            return self._credential_provider

        try:
            from casare_rpa.infrastructure.security.credential_provider import (
                VaultCredentialProvider,
            )

            provider = VaultCredentialProvider()
            await provider.initialize()

            # Set execution context for audit logging
            provider.set_execution_context(
                workflow_id=self._state.workflow_name,
                robot_id=None,  # Robot ID set by orchestrator if applicable
            )

            # Register project credential bindings
            if self._state.has_project_context and self._state.project_context:
                bindings = self._state.project_context.get_credential_bindings()
                if bindings:
                    provider.register_bindings(bindings)
                    logger.debug(f"Registered {len(bindings)} credential bindings")

            self._credential_provider = provider
            self.resources["credential_provider"] = provider

            logger.debug("Credential provider initialized")
            return provider

        except Exception as e:
            logger.warning(f"Failed to initialize credential provider: {e}")
            return None

    async def resolve_credential(
        self,
        alias: str,
        required: bool = False,
    ) -> Any | None:
        """
        Resolve a credential by alias from the vault.

        Args:
            alias: Credential alias to resolve
            required: If True, raises error when not found

        Returns:
            ResolvedCredential object or None

        Raises:
            SecretNotFoundError: If required and credential not found
        """
        provider = await self.get_credential_provider()
        if not provider:
            if required:
                raise ValueError(f"Credential provider unavailable, cannot resolve: {alias}")
            return None

        return await provider.get_credential(alias, required=required)

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

    def get_execution_summary(self) -> dict[str, Any]:
        """
        Get a summary of the execution.

        Returns:
            Dictionary with execution statistics
        """
        return self._state.get_execution_summary()

    # ========================================================================
    # BROWSER MANAGEMENT - Delegate to BrowserResourceManager (infrastructure)
    # ========================================================================

    def set_browser(self, browser: Browser) -> None:
        """Set the active browser instance."""
        self._resources.set_browser(browser)

    def get_browser(self) -> Browser | None:
        """Get the active browser instance."""
        return self._resources.get_browser()

    def add_browser_context(self, context: BrowserContext) -> None:
        """
        Track a browser context for cleanup.

        Args:
            context: Playwright browser context object
        """
        self._resources.add_browser_context(context)

    def set_active_page(self, page: Page, name: str = "default") -> None:
        """
        Set the active page and store it with a name.

        Args:
            page: Playwright page object
            name: Page identifier (for multiple tabs)
        """
        logger.info(
            f"ExecutionContext.set_active_page: name={name}, "
            f"page={page is not None}, context_id={id(self)}, "
            f"resources_id={id(self._resources)}"
        )
        self._resources.set_active_page(page, name)

    def get_active_page(self) -> Page | None:
        """Get the currently active page."""
        page = self._resources.get_active_page()
        logger.info(
            f"ExecutionContext.get_active_page: page={page is not None}, "
            f"context_id={id(self)}, resources_id={id(self._resources)}"
        )
        return page

    def get_page(self, name: str = "default") -> Page | None:
        """Get a page by name."""
        return self._resources.get_page(name)

    def add_page(self, page: Page, name: str) -> None:
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
    def completed_at(self) -> datetime | None:
        """Get execution completion time."""
        return self._state.completed_at

    @property
    def variables(self) -> dict[str, Any]:
        """Get variables dict (direct access for backward compatibility)."""
        return self._state.variables

    @property
    def current_node_id(self) -> NodeId | None:
        """Get current node ID."""
        return self._state.current_node_id

    @property
    def execution_path(self) -> list[NodeId]:
        """Get execution path."""
        return self._state.execution_path

    @property
    def errors(self) -> list[tuple[NodeId, str]]:
        """Get errors list."""
        return self._state.errors

    @property
    def stopped(self) -> bool:
        """Check if execution is stopped."""
        return self._state.stopped

    @property
    def browser(self) -> Browser | None:
        """Get browser instance."""
        return self._resources.browser

    @browser.setter
    def browser(self, value: Browser | None) -> None:
        """Set browser instance."""
        if value is None:
            self._resources.browser = None
        else:
            self._resources.set_browser(value)

    @property
    def browser_contexts(self) -> list[BrowserContext]:
        """Get browser contexts list."""
        return self._resources.browser_contexts

    @property
    def pages(self) -> dict[str, Page]:
        """Get pages dict."""
        return self._resources.pages

    @property
    def active_page(self) -> Page | None:
        """Get active page."""
        return self._resources.active_page

    @active_page.setter
    def active_page(self, value: Page | None) -> None:
        """Set active page."""
        self._resources.active_page = value

    @property
    def project_context(self) -> ProjectContext | None:
        """Get the project context (if any)."""
        return self._state.project_context

    @property
    def has_project_context(self) -> bool:
        """Check if a project context is available."""
        return self._state.has_project_context

    # ========================================================================
    # PARALLEL EXECUTION SUPPORT
    # ========================================================================

    def clone_for_branch(self, branch_name: str) -> ExecutionContext:
        """
        Create an isolated context copy for parallel branch execution.

        Each parallel branch gets its own variable namespace to prevent
        conflicts during concurrent execution. Browser resources are shared
        (read-only) but each branch can create new pages.

        Args:
            branch_name: Name of the branch (used for variable namespacing)

        Returns:
            New ExecutionContext with copied variables and shared resources
        """
        # Create new context with copied variables
        branch_context = ExecutionContext(
            workflow_name=f"{self._state.workflow_name}::{branch_name}",
            mode=self._state.mode,
            initial_variables=self._state.variables.copy(),  # Snapshot
            project_context=self._state.project_context,
            pause_event=self.pause_event,  # Share pause/resume control
        )

        # Share browser resources (read-only during parallel execution)
        # Branches can create new pages but shouldn't modify shared state
        branch_context._resources = self._resources

        # Copy desktop context reference (read-only)
        branch_context.desktop_context = self.desktop_context

        # Store branch name for result merging
        branch_context.set_variable("_branch_name", branch_name)

        return branch_context

    def merge_branch_results(self, branch_name: str, branch_variables: dict[str, Any]) -> None:
        """
        Merge variables from a completed branch back to main context.

        Variables are namespaced by branch name to avoid conflicts.
        Special variables (starting with _) are not merged.

        Args:
            branch_name: Name of the branch
            branch_variables: Variables from the branch context
        """
        for key, value in branch_variables.items():
            # Skip internal variables
            if key.startswith("_"):
                continue
            # Namespace by branch name
            namespaced_key = f"{branch_name}_{key}"
            self._state.set_variable(namespaced_key, value)

    def create_workflow_context(self, workflow_name: str) -> ExecutionContext:
        """
        Create context for parallel workflow with SHARED variables but SEPARATE browser.

        Used for multi-workflow parallel execution where multiple StartNodes
        execute concurrently on the same canvas. Unlike clone_for_branch():
        - Variables are SHARED (same dict reference, not a copy)
        - Browser is SEPARATE (new BrowserResourceManager per workflow)

        Args:
            workflow_name: Name identifier for this workflow

        Returns:
            New ExecutionContext with shared variables and separate browser
        """
        # Create new context (will have new BrowserResourceManager)
        workflow_context = ExecutionContext(
            workflow_name=workflow_name,
            mode=self._state.mode,
            initial_variables=None,  # Don't copy - will share reference
            project_context=self._state.project_context,
            pause_event=self.pause_event,  # Share pause/resume control
        )

        # SHARE the same variables dict (not a copy!)
        # This allows workflows to coordinate via shared variables
        workflow_context._state.variables = self._state.variables

        # Browser is SEPARATE - workflow_context already has new BrowserResourceManager

        # Copy desktop context reference (shared, read-only)
        workflow_context.desktop_context = self.desktop_context

        # Store workflow name for identification
        workflow_context.set_variable("_workflow_name", workflow_name)

        logger.debug(
            f"Created workflow context '{workflow_name}' with shared variables, separate browser"
        )

        return workflow_context

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

        # Clean up credential provider (revokes active leases)
        if self._credential_provider is not None:
            try:
                await self._credential_provider.shutdown()
                logger.debug("Credential provider shutdown complete")
            except Exception as e:
                logger.warning(f"Error shutting down credential provider: {e}")
            finally:
                self._credential_provider = None

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

        # Clean up custom resources (telegram clients, etc.)
        for key, resource in list(self.resources.items()):
            try:
                if hasattr(resource, "close"):
                    if asyncio.iscoroutinefunction(resource.close):
                        await resource.close()
                    else:
                        resource.close()
                elif hasattr(resource, "shutdown"):
                    if asyncio.iscoroutinefunction(resource.shutdown):
                        await resource.shutdown()
                    else:
                        resource.shutdown()
            except Exception as e:
                logger.warning(f"Error cleaning up resource '{key}': {e}")
        self.resources.clear()

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

    async def __aenter__(self) -> ExecutionContext:
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

    def __enter__(self) -> ExecutionContext:
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
