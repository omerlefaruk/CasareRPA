"""
CasareRPA - Thread-Safe Singleton Pattern.

Provides a reusable singleton pattern that replaces the use of the `global` keyword.
This module offers a drop-in replacement for global singleton accessors.

Usage:
    Instead of:
        _instance: Optional[MyClass] = None

        def get_instance() -> MyClass:
            global _instance
            if _instance is None:
                _instance = MyClass()
            return _instance

    Use:
        from casare_rpa.application.dependency_injection.singleton import Singleton

        _my_class_holder = Singleton(MyClass)

        def get_instance() -> MyClass:
            return _my_class_holder.get()

        def reset_instance() -> None:
            _my_class_holder.reset()
"""

from __future__ import annotations

import threading
from typing import Callable, Generic, Optional, TypeVar

from loguru import logger


T = TypeVar("T")


class Singleton(Generic[T]):
    """
    Thread-safe singleton holder.

    Provides lazy initialization and proper cleanup without using globals.

    Type Parameters:
        T: The type of the singleton instance

    Example:
        class ConfigManager:
            pass

        config_holder = Singleton(ConfigManager)

        def get_config() -> ConfigManager:
            return config_holder.get()

        def reset_config() -> None:
            config_holder.reset()
    """

    def __init__(
        self,
        factory: Callable[[], T],
        name: Optional[str] = None,
        on_create: Optional[Callable[[T], None]] = None,
        on_dispose: Optional[Callable[[T], None]] = None,
    ) -> None:
        """
        Initialize the singleton holder.

        Args:
            factory: Callable that creates the instance
            name: Optional name for logging
            on_create: Optional callback after instance creation
            on_dispose: Optional callback before instance disposal
        """
        self._factory = factory
        self._name = name or factory.__name__ if hasattr(factory, "__name__") else "Singleton"
        self._on_create = on_create
        self._on_dispose = on_dispose
        self._instance: Optional[T] = None
        self._lock = threading.Lock()

    def get(self) -> T:
        """
        Get the singleton instance.

        Uses double-checked locking for thread safety and performance.

        Returns:
            The singleton instance
        """
        # First check without lock (fast path)
        instance = self._instance
        if instance is not None:
            return instance

        # Slow path with lock
        with self._lock:
            # Double-check after acquiring lock
            if self._instance is None:
                self._instance = self._factory()
                logger.debug(f"Created singleton: {self._name}")
                if self._on_create:
                    self._on_create(self._instance)
            return self._instance

    def get_optional(self) -> Optional[T]:
        """
        Get the singleton instance if it exists.

        Does not create the instance if it doesn't exist.

        Returns:
            The singleton instance or None
        """
        return self._instance

    def set(self, instance: T) -> None:
        """
        Replace the singleton instance.

        Disposes the old instance if one exists.

        Args:
            instance: New instance to use
        """
        with self._lock:
            if self._instance is not None and self._on_dispose:
                try:
                    self._on_dispose(self._instance)
                except Exception as e:
                    logger.warning(f"Error disposing {self._name}: {e}")
            self._instance = instance
            logger.debug(f"Set singleton: {self._name}")

    def reset(self) -> None:
        """
        Reset the singleton instance.

        Disposes the current instance and clears the reference.
        Next call to get() will create a new instance.
        """
        with self._lock:
            if self._instance is not None:
                if self._on_dispose:
                    try:
                        self._on_dispose(self._instance)
                    except Exception as e:
                        logger.warning(f"Error disposing {self._name}: {e}")
                self._instance = None
                logger.debug(f"Reset singleton: {self._name}")

    def is_initialized(self) -> bool:
        """Check if the singleton has been initialized."""
        return self._instance is not None


class LazySingleton(Generic[T]):
    """
    Lazily-initialized singleton with deferred factory.

    Useful when the factory function depends on other modules
    that may not be imported yet.

    Example:
        def create_event_bus():
            from casare_rpa.domain.events import EventBus
            return EventBus()

        event_bus_holder = LazySingleton(create_event_bus)
    """

    def __init__(
        self,
        factory: Callable[[], T],
        name: Optional[str] = None,
    ) -> None:
        """
        Initialize the lazy singleton holder.

        Args:
            factory: Callable that creates the instance (called lazily)
            name: Optional name for logging
        """
        self._factory = factory
        self._name = name or "LazySingleton"
        self._instance: Optional[T] = None
        self._lock = threading.Lock()

    def get(self) -> T:
        """Get the singleton instance, creating if needed."""
        instance = self._instance
        if instance is not None:
            return instance

        with self._lock:
            if self._instance is None:
                self._instance = self._factory()
                logger.debug(f"Created lazy singleton: {self._name}")
            return self._instance

    def reset(self) -> None:
        """Reset the singleton instance."""
        with self._lock:
            self._instance = None
            logger.debug(f"Reset lazy singleton: {self._name}")


def create_singleton_accessor(
    factory: Callable[[], T],
    name: Optional[str] = None,
) -> tuple[Callable[[], T], Callable[[], None]]:
    """
    Create get and reset functions for a singleton.

    Convenience function that returns a pair of accessor functions.

    Args:
        factory: Callable that creates the instance
        name: Optional name for logging

    Returns:
        Tuple of (get_func, reset_func)

    Example:
        get_config, reset_config = create_singleton_accessor(
            lambda: Config.from_env(),
            name="Config"
        )

        config = get_config()
        reset_config()  # For testing
    """
    holder = Singleton(factory, name)
    return holder.get, holder.reset
