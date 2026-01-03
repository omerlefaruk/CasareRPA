"""Dependency injection bootstrap.

This module provides a single, idempotent entry point for initializing the
dependency container in runtime entrypoints (Canvas, Orchestrator, Robot).
"""

from __future__ import annotations

from casare_rpa.application.dependency_injection.container import DIContainer
from casare_rpa.application.dependency_injection.providers import (
    ConfigProvider,
    EventBusProvider,
    InfrastructureProvider,
    PresentationProvider,
    StorageProvider,
)


def bootstrap_di(*, include_presentation: bool = True) -> DIContainer:
    """Initialize DI container registrations if not already initialized."""
    container = DIContainer.get_instance()

    if not container.is_registered("config"):
        ConfigProvider.register(container)
        EventBusProvider.register(container)
        StorageProvider.register(container)
        InfrastructureProvider.register(container)
        if include_presentation:
            PresentationProvider.register(container)

    return container
