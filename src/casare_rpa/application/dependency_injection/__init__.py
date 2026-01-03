"""
CasareRPA - Application Dependency Injection Container.

Provides a thread-safe DI container for managing singleton and scoped dependencies.
Replaces all global variables with proper lifecycle management.

Usage:
    from casare_rpa.application.dependency_injection import DIContainer

    # Register singleton
    container = DIContainer.get_instance()
    container.register_singleton("config", Config, factory=load_config)

    # Resolve
    config = container.resolve("config")

Lifecycle Types:
    - SINGLETON: One instance per application lifetime (e.g., Config, EventBus)
    - SCOPED: One instance per scope/request (e.g., per workflow execution)
    - TRANSIENT: New instance each time (e.g., DTOs)

Singleton Pattern:
    For simpler cases where full DI container is overkill:

    from casare_rpa.application.dependency_injection.singleton import Singleton

    _config_holder = Singleton(lambda: Config.from_env(), name="Config")

    def get_config() -> Config:
        return _config_holder.get()
"""

from casare_rpa.application.dependency_injection.bootstrap import bootstrap_di
from casare_rpa.application.dependency_injection.container import DIContainer, Lifecycle
from casare_rpa.application.dependency_injection.providers import (
    ConfigProvider,
    EventBusProvider,
    InfrastructureProvider,
    StorageProvider,
)
from casare_rpa.application.dependency_injection.singleton import (
    LazySingleton,
    Singleton,
    create_singleton_accessor,
)

__all__ = [
    "DIContainer",
    "Lifecycle",
    "ConfigProvider",
    "EventBusProvider",
    "StorageProvider",
    "InfrastructureProvider",
    "bootstrap_di",
    "Singleton",
    "LazySingleton",
    "create_singleton_accessor",
]
