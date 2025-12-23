"""
CasareRPA - Thread-Safe Dependency Injection Container.

Provides lifecycle-aware dependency management with proper thread safety.
Supports singleton, scoped, and transient lifecycles.
"""

from __future__ import annotations

import atexit
import threading
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, Generic, Optional, Type, TypeVar, cast

from loguru import logger

T = TypeVar("T")


class Lifecycle(Enum):
    """Dependency lifecycle types."""

    SINGLETON = auto()  # One instance for entire application
    SCOPED = auto()  # One instance per scope (e.g., workflow execution)
    TRANSIENT = auto()  # New instance each time


@dataclass
class Registration:
    """Represents a registered dependency."""

    name: str
    implementation: type[Any] | None = None
    factory: Callable[..., Any] | None = None
    lifecycle: Lifecycle = Lifecycle.SINGLETON
    instance: Any | None = None
    dependencies: dict[str, str] = field(default_factory=dict)

    def create_instance(self, container: DIContainer) -> Any:
        """Create an instance of the registered type."""
        kwargs = {}
        for param_name, dep_name in self.dependencies.items():
            kwargs[param_name] = container.resolve(dep_name)

        if self.factory:
            return self.factory(**kwargs) if kwargs else self.factory()
        if self.implementation:
            return self.implementation(**kwargs) if kwargs else self.implementation()
        raise ValueError(f"No factory or implementation for {self.name}")


class Scope:
    """
    Represents a scope for scoped dependencies.

    Used to create child containers that share singletons with parent
    but have their own scoped instances.
    """

    def __init__(self, container: DIContainer) -> None:
        """Initialize scope with reference to parent container."""
        self._container = container
        self._scoped_instances: dict[str, Any] = {}
        self._lock = threading.Lock()

    def get_or_create(self, registration: Registration) -> Any:
        """Get or create a scoped instance."""
        with self._lock:
            if registration.name not in self._scoped_instances:
                self._scoped_instances[registration.name] = registration.create_instance(
                    self._container
                )
            return self._scoped_instances[registration.name]

    def dispose(self) -> None:
        """Dispose all scoped instances."""
        with self._lock:
            for name, instance in self._scoped_instances.items():
                try:
                    if hasattr(instance, "dispose"):
                        instance.dispose()
                    elif hasattr(instance, "close"):
                        instance.close()
                    elif hasattr(instance, "stop"):
                        instance.stop()
                except Exception as e:
                    logger.warning(f"Error disposing scoped instance {name}: {e}")
            self._scoped_instances.clear()


class DIContainer:
    """
    Thread-safe dependency injection container.

    Features:
    - Singleton pattern for container itself
    - Thread-safe registration and resolution
    - Lifecycle management (singleton, scoped, transient)
    - Lazy initialization
    - Proper cleanup on shutdown
    """

    _instance: DIContainer | None = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        """Initialize the container."""
        self._registrations: dict[str, Registration] = {}
        self._lock = threading.RLock()  # Reentrant for nested resolves
        self._current_scope: Scope | None = None
        self._disposed = False

    @classmethod
    def get_instance(cls) -> DIContainer:
        """
        Get the singleton container instance.

        Thread-safe lazy initialization.
        """
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
                    atexit.register(cls._instance._cleanup)
                    logger.debug("DIContainer singleton created")
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the singleton instance (for testing).

        Disposes all registered dependencies before reset.
        """
        with cls._instance_lock:
            if cls._instance is not None:
                cls._instance._cleanup()
                cls._instance = None
                logger.debug("DIContainer singleton reset")

    def register_singleton(
        self,
        name: str,
        implementation: type[T] | None = None,
        factory: Callable[..., T] | None = None,
        dependencies: dict[str, str] | None = None,
    ) -> None:
        """
        Register a singleton dependency.

        Args:
            name: Unique name for the dependency
            implementation: Class to instantiate
            factory: Factory function to create instance
            dependencies: Map of param names to dependency names
        """
        self._register(
            name,
            implementation,
            factory,
            Lifecycle.SINGLETON,
            dependencies,
        )

    def register_scoped(
        self,
        name: str,
        implementation: type[T] | None = None,
        factory: Callable[..., T] | None = None,
        dependencies: dict[str, str] | None = None,
    ) -> None:
        """
        Register a scoped dependency.

        Scoped dependencies are created once per scope (e.g., workflow execution).
        """
        self._register(
            name,
            implementation,
            factory,
            Lifecycle.SCOPED,
            dependencies,
        )

    def register_transient(
        self,
        name: str,
        implementation: type[T] | None = None,
        factory: Callable[..., T] | None = None,
        dependencies: dict[str, str] | None = None,
    ) -> None:
        """
        Register a transient dependency.

        Transient dependencies are created fresh each time they are resolved.
        """
        self._register(
            name,
            implementation,
            factory,
            Lifecycle.TRANSIENT,
            dependencies,
        )

    def register_instance(self, name: str, instance: T) -> None:
        """
        Register an existing instance as a singleton.

        Useful for injecting pre-configured objects.
        """
        with self._lock:
            self._registrations[name] = Registration(
                name=name,
                lifecycle=Lifecycle.SINGLETON,
                instance=instance,
            )
            logger.debug(f"Registered instance: {name}")

    def _register(
        self,
        name: str,
        implementation: type[Any] | None,
        factory: Callable[..., Any] | None,
        lifecycle: Lifecycle,
        dependencies: dict[str, str] | None,
    ) -> None:
        """Internal registration method."""
        if not implementation and not factory:
            raise ValueError(f"Either implementation or factory required for {name}")

        with self._lock:
            self._registrations[name] = Registration(
                name=name,
                implementation=implementation,
                factory=factory,
                lifecycle=lifecycle,
                dependencies=dependencies or {},
            )
            logger.debug(f"Registered {lifecycle.name}: {name}")

    def resolve(self, name: str) -> Any:
        """
        Resolve a dependency by name.

        Thread-safe resolution with proper lifecycle handling.

        Args:
            name: Name of the registered dependency

        Returns:
            The resolved instance

        Raises:
            KeyError: If dependency not registered
        """
        with self._lock:
            if name not in self._registrations:
                raise KeyError(f"Dependency not registered: {name}")

            registration = self._registrations[name]

            if registration.lifecycle == Lifecycle.SINGLETON:
                if registration.instance is None:
                    registration.instance = registration.create_instance(self)
                    logger.debug(f"Created singleton: {name}")
                return registration.instance

            if registration.lifecycle == Lifecycle.SCOPED:
                if self._current_scope is None:
                    raise RuntimeError(
                        f"Cannot resolve scoped dependency {name} outside a scope. "
                        "Use 'with container.create_scope():' first."
                    )
                return self._current_scope.get_or_create(registration)

            # Transient: create new instance each time
            return registration.create_instance(self)

    def resolve_optional(self, name: str) -> Any | None:
        """
        Resolve a dependency, returning None if not registered.

        Useful for optional dependencies.
        """
        try:
            return self.resolve(name)
        except KeyError:
            return None

    def is_registered(self, name: str) -> bool:
        """Check if a dependency is registered."""
        with self._lock:
            return name in self._registrations

    @contextmanager
    def create_scope(self):
        """
        Create a new scope for scoped dependencies.

        Usage:
            with container.create_scope():
                ctx = container.resolve("execution_context")
                # ctx is scoped to this block
        """
        scope = Scope(self)
        previous_scope = self._current_scope
        self._current_scope = scope
        try:
            yield scope
        finally:
            self._current_scope = previous_scope
            scope.dispose()

    def _cleanup(self) -> None:
        """Cleanup all registered singletons on shutdown."""
        if self._disposed:
            return

        with self._lock:
            self._disposed = True
            for name, registration in self._registrations.items():
                if registration.instance is not None:
                    try:
                        instance = registration.instance
                        if hasattr(instance, "dispose"):
                            instance.dispose()
                        elif hasattr(instance, "close"):
                            instance.close()
                        elif hasattr(instance, "stop"):
                            instance.stop()
                    except Exception as e:
                        logger.warning(f"Error disposing {name}: {e}")
            self._registrations.clear()
            logger.debug("DIContainer cleanup complete")

    def clear(self) -> None:
        """Clear all registrations (for testing)."""
        self._cleanup()
        self._disposed = False


class TypedContainer(Generic[T]):
    """
    Type-safe wrapper for accessing specific dependencies.

    Provides compile-time type checking for dependency resolution.

    Usage:
        config_provider = TypedContainer[Config]("config")
        config = config_provider.get()  # Returns Config type
    """

    def __init__(self, name: str) -> None:
        """Initialize with dependency name."""
        self._name = name

    def get(self) -> T:
        """Get the typed dependency instance."""
        container = DIContainer.get_instance()
        return cast(T, container.resolve(self._name))

    def get_optional(self) -> T | None:
        """Get the typed dependency or None."""
        container = DIContainer.get_instance()
        return cast(T | None, container.resolve_optional(self._name))
