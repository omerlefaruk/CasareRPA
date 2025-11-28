"""
Component factory for lazy component creation with singleton caching.

Implements singleton pattern for deferred component initialization,
supporting the 3-tier loading strategy for startup optimization.

Tier 1 (CRITICAL): Immediate - NodeGraphWidget, WorkflowController
Tier 2 (NORMAL): showEvent - PropertiesPanel, DebugPanel, VariablesPanel
Tier 3 (DEFERRED): Lazy factory - OutputConsole, dialogs
"""

from typing import Callable, Dict, Optional, TypeVar
from PySide6.QtWidgets import QWidget
from loguru import logger

T = TypeVar("T", bound=QWidget)


class ComponentFactory:
    """
    Lazy component creation with singleton caching.

    Provides factory methods for deferred component creation, ensuring
    each component is only instantiated once and reused on subsequent
    access. Supports the 3-tier loading strategy for startup optimization.

    Thread Safety:
        This class is NOT thread-safe. All component creation should
        happen on the main Qt thread.

    Usage:
        # Get or create a component
        console = ComponentFactory.get_or_create(
            "output_console",
            lambda: OutputConsole(parent)
        )

        # Clear cache (for tests or cleanup)
        ComponentFactory.clear()
    """

    _instances: Dict[str, QWidget] = {}
    _creation_times: Dict[str, float] = {}

    @classmethod
    def get_or_create(cls, component_name: str, factory: Callable[[], T]) -> T:
        """
        Get existing component or create new one using factory.

        Args:
            component_name: Unique identifier for the component.
            factory: Callable that creates the component if not cached.

        Returns:
            The cached or newly created component instance.

        Raises:
            RuntimeError: If factory fails to create component.
        """
        if component_name not in cls._instances:
            import time

            start_time = time.perf_counter()

            try:
                instance = factory()
                if instance is None:
                    raise RuntimeError(
                        f"Factory returned None for component '{component_name}'"
                    )
                cls._instances[component_name] = instance

                elapsed = (time.perf_counter() - start_time) * 1000
                cls._creation_times[component_name] = elapsed

                logger.debug(
                    f"ComponentFactory: Created '{component_name}' in {elapsed:.2f}ms"
                )
            except Exception as e:
                logger.error(
                    f"ComponentFactory: Failed to create '{component_name}': {e}"
                )
                raise RuntimeError(
                    f"Failed to create component '{component_name}': {e}"
                ) from e

        return cls._instances[component_name]  # type: ignore

    @classmethod
    def has(cls, component_name: str) -> bool:
        """
        Check if component exists in cache.

        Args:
            component_name: Unique identifier for the component.

        Returns:
            True if component is cached, False otherwise.
        """
        return component_name in cls._instances

    @classmethod
    def get(cls, component_name: str) -> Optional[QWidget]:
        """
        Get component from cache without creating.

        Args:
            component_name: Unique identifier for the component.

        Returns:
            Cached component or None if not found.
        """
        return cls._instances.get(component_name)

    @classmethod
    def remove(cls, component_name: str) -> Optional[QWidget]:
        """
        Remove component from cache.

        Args:
            component_name: Unique identifier for the component.

        Returns:
            Removed component or None if not found.
        """
        cls._creation_times.pop(component_name, None)
        return cls._instances.pop(component_name, None)

    @classmethod
    def clear(cls) -> None:
        """
        Clear all cached components.

        Should be called during cleanup or in tests to reset state.
        Does NOT destroy the widgets - caller must handle widget cleanup.
        """
        logger.debug(
            f"ComponentFactory: Clearing cache ({len(cls._instances)} components)"
        )
        cls._instances.clear()
        cls._creation_times.clear()

    @classmethod
    def get_stats(cls) -> Dict[str, float]:
        """
        Get creation time statistics for cached components.

        Returns:
            Dict mapping component names to creation times in milliseconds.
        """
        return cls._creation_times.copy()

    @classmethod
    def get_cached_count(cls) -> int:
        """
        Get number of cached components.

        Returns:
            Number of components currently in cache.
        """
        return len(cls._instances)
