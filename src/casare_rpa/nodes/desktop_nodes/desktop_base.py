"""
Desktop Node Base Class

Provides shared functionality for all desktop automation nodes:
- DesktopContext management
- Retry logic
- Standard error handling
- Common patterns
"""

import asyncio
import uuid
from abc import abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import NodeStatus, PortType, DataType
from casare_rpa.desktop import DesktopContext

# Type variable for result types
T = TypeVar("T")


class DesktopNodeBase(BaseNode):
    """
    Base class for all desktop automation nodes.

    Provides:
    - Automatic DesktopContext management
    - Standardized error handling
    - Common port definitions
    - Retry support via execute_with_retry()
    """

    __identifier__ = "casare_rpa.nodes.desktop"

    # Default retry configuration
    DEFAULT_RETRY_COUNT: int = 0
    DEFAULT_RETRY_INTERVAL: float = 1.0
    DEFAULT_TIMEOUT: float = 5.0

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Desktop Node",
    ):
        """
        Initialize desktop node with merged config.

        Args:
            node_id: Unique node identifier
            config: Node configuration (merged with defaults)
            name: Display name for the node
        """
        merged_config = self._get_default_config()
        if config:
            merged_config.update(config)
        # Generate node_id if not provided
        resolved_node_id = node_id if node_id is not None else str(uuid.uuid4())
        super().__init__(resolved_node_id, merged_config)
        self.name = name

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Override in subclasses to provide default configuration.

        Returns:
            Dictionary of default configuration values
        """
        return {}

    def get_desktop_context(self, context: Any) -> DesktopContext:
        """
        Get or create DesktopContext from execution context.

        Args:
            context: Execution context

        Returns:
            DesktopContext instance
        """
        if not hasattr(context, "desktop_context") or context.desktop_context is None:
            context.desktop_context = DesktopContext()
            logger.debug(f"[{self.name}] Created new DesktopContext")
        desktop_ctx: DesktopContext = context.desktop_context
        return desktop_ctx

    def require_desktop_context(self, context: Any) -> DesktopContext:
        """
        Get DesktopContext, raising error if not available.

        Args:
            context: Execution context

        Returns:
            DesktopContext instance

        Raises:
            ValueError: If desktop context cannot be created
        """
        desktop_ctx: Optional[DesktopContext] = getattr(
            context, "desktop_context", None
        )
        if desktop_ctx is None:
            raise ValueError("Desktop context not available")
        return desktop_ctx

    def resolve_variable(self, context: Any, value: Any) -> Any:
        """
        Resolve {{variable}} patterns in value using context.

        Args:
            context: Execution context
            value: Value that may contain variable patterns

        Returns:
            Resolved value
        """
        if value is not None and hasattr(context, "resolve_value"):
            return context.resolve_value(value)
        return value

    async def execute_with_retry(
        self,
        operation: Any,
        context: Any,
        retry_count: Optional[int] = None,
        retry_interval: Optional[float] = None,
        operation_name: str = "operation",
    ) -> Dict[str, Any]:
        """
        Execute an operation with retry logic.

        Args:
            operation: Async callable to execute
            context: Execution context
            retry_count: Number of retries (default from config)
            retry_interval: Delay between retries in seconds
            operation_name: Name for logging

        Returns:
            Operation result dictionary
        """
        if retry_count is None:
            retry_count = int(self.config.get("retry_count", self.DEFAULT_RETRY_COUNT))
        if retry_interval is None:
            retry_interval = float(
                self.config.get("retry_interval", self.DEFAULT_RETRY_INTERVAL)
            )

        max_attempts = retry_count + 1
        last_error: Optional[Exception] = None
        attempts = 0

        while attempts < max_attempts:
            try:
                attempts += 1
                if attempts > 1:
                    logger.info(
                        f"[{self.name}] Retry attempt {attempts - 1}/{retry_count}"
                    )

                result: Dict[str, Any] = await operation()

                logger.info(
                    f"[{self.name}] {operation_name} succeeded (attempt {attempts})"
                )
                self.status = NodeStatus.SUCCESS
                return result

            except Exception as e:
                last_error = e
                if attempts < max_attempts:
                    logger.warning(
                        f"[{self.name}] {operation_name} failed (attempt {attempts}): {e}"
                    )
                    await asyncio.sleep(retry_interval)
                else:
                    break

        error_msg = (
            f"Failed to {operation_name} after {attempts} attempts: {last_error}"
        )
        logger.error(f"[{self.name}] {error_msg}")
        self.status = NodeStatus.ERROR
        raise RuntimeError(error_msg)

    def handle_error(self, error: Exception, operation: str = "execute") -> None:
        """
        Standard error handling for desktop nodes.

        Args:
            error: The exception that occurred
            operation: Name of the failed operation
        """
        error_msg = f"Failed to {operation}: {error}"
        logger.error(f"[{self.name}] {error_msg}")
        self.status = NodeStatus.ERROR
        raise RuntimeError(error_msg) from error

    def success_result(self, **data: Any) -> Dict[str, Any]:
        """
        Create a standard success result dictionary.

        Args:
            **data: Additional data to include in result

        Returns:
            Success result dictionary
        """
        self.status = NodeStatus.SUCCESS
        result = {"success": True, "next_nodes": ["exec_out"]}
        result.update(data)
        return result

    def error_result(self, error: str, **data: Any) -> Dict[str, Any]:
        """
        Create a standard error result dictionary.

        Args:
            error: Error message
            **data: Additional data to include in result

        Returns:
            Error result dictionary
        """
        self.status = NodeStatus.ERROR
        result = {"success": False, "error": error}
        result.update(data)
        return result


class ElementInteractionMixin:
    """
    Mixin providing element finding functionality.

    Use with DesktopNodeBase to add element finding patterns.
    """

    async def find_element_from_inputs(
        self,
        context: Any,
        desktop_ctx: DesktopContext,
        timeout: Optional[float] = None,
    ) -> Any:
        """
        Find element from inputs (element port or window+selector).

        Args:
            context: Execution context
            desktop_ctx: DesktopContext instance
            timeout: Timeout in seconds

        Returns:
            Found element

        Raises:
            ValueError: If required inputs are missing
            RuntimeError: If element not found
        """
        # Try direct element first
        element = self.get_input_value("element")  # type: ignore

        if element:
            return element

        # Fall back to window + selector
        window = self.get_input_value("window")  # type: ignore
        selector = self.get_parameter("selector", context)  # type: ignore

        if not window or not selector:
            raise ValueError("Must provide 'element' or both 'window' and 'selector'")

        if timeout is None:
            timeout = float(self.config.get("timeout", 5.0))  # type: ignore

        logger.info(f"[{self.name}] Finding element with selector: {selector}")  # type: ignore

        element = window.find_child(selector, timeout=timeout)

        if not element:
            raise RuntimeError(f"Element not found with selector: {selector}")

        return element


class WindowOperationMixin:
    """
    Mixin for window-based operations with retry support.
    """

    def get_window_from_input(self, raise_on_missing: bool = True) -> Any:
        """
        Get window from input port.

        Args:
            raise_on_missing: Raise error if window not provided

        Returns:
            Window object or None
        """
        window = self.get_input_value("window")  # type: ignore

        if not window and raise_on_missing:
            raise ValueError("Window input is required")

        return window
