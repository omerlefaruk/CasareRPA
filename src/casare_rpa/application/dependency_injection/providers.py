"""
CasareRPA - Dependency Providers.

Provider classes that encapsulate dependency registration and lifecycle.
Each provider is responsible for a related set of dependencies.

Usage:
    container = DIContainer.get_instance()
    ConfigProvider.register(container)
    EventBusProvider.register(container)
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any, Callable, Optional

from loguru import logger

if TYPE_CHECKING:
    from casare_rpa.application.dependency_injection.container import DIContainer


class BaseProvider:
    """Base class for dependency providers."""

    @classmethod
    def register(cls, container: "DIContainer") -> None:
        """Register all dependencies managed by this provider."""
        raise NotImplementedError


class ConfigProvider(BaseProvider):
    """
    Provider for configuration dependencies.

    Manages:
    - config: Main Config object (singleton, lazy-loaded from environment)
    """

    @classmethod
    def register(cls, container: "DIContainer") -> None:
        """Register configuration dependencies."""

        def config_factory() -> Any:
            from casare_rpa.config.loader import _build_config_internal

            return _build_config_internal()

        container.register_singleton("config", factory=config_factory)
        logger.debug("ConfigProvider registered")


class EventBusProvider(BaseProvider):
    """
    Provider for event system dependencies.

    Manages:
    - event_bus: Main EventBus instance (singleton)
    """

    @classmethod
    def register(cls, container: "DIContainer") -> None:
        """Register event system dependencies."""

        def event_bus_factory() -> Any:
            from casare_rpa.domain.events import EventBus

            bus = EventBus()
            logger.info("Event bus created via DI container")
            return bus

        container.register_singleton("event_bus", factory=event_bus_factory)
        logger.debug("EventBusProvider registered")


class StorageProvider(BaseProvider):
    """
    Provider for storage dependencies.

    Manages:
    - schedule_storage: ScheduleStorage (singleton)
    - recent_files_manager: RecentFilesManager (singleton)
    - settings_manager: SettingsManager (singleton)
    """

    @classmethod
    def register(cls, container: "DIContainer") -> None:
        """Register storage dependencies."""

        def schedule_storage_factory() -> Any:
            from casare_rpa.application.scheduling.schedule_storage import (
                ScheduleStorage,
            )

            return ScheduleStorage()

        def recent_files_factory() -> Any:
            from casare_rpa.application.workflow.recent_files import RecentFilesManager

            return RecentFilesManager()

        def settings_manager_factory() -> Any:
            from casare_rpa.utils.settings_manager import SettingsManager

            return SettingsManager()

        container.register_singleton("schedule_storage", factory=schedule_storage_factory)
        container.register_singleton("recent_files_manager", factory=recent_files_factory)
        container.register_singleton("settings_manager", factory=settings_manager_factory)
        logger.debug("StorageProvider registered")


class InfrastructureProvider(BaseProvider):
    """
    Provider for infrastructure dependencies.

    Manages:
    - update_manager: UpdateManager (singleton)
    - recovery_strategy_registry: RecoveryStrategyRegistry (singleton)
    - metrics_exporter: MetricsExporter (singleton)
    - output_capture: OutputCapture controller (singleton)
    - ui_log_controller: UI log sink controller (singleton)
    - healing_telemetry: Browser healing telemetry (singleton)
    - api_key_store: API key storage (singleton)
    - credential_store: Credential storage (singleton)
    - memory_queue: Memory queue (singleton)
    - log_streaming_service: Log streaming (singleton)
    - log_cleanup_job: Log cleanup scheduler (singleton)
    """

    @classmethod
    def register(cls, container: "DIContainer") -> None:
        """Register infrastructure dependencies."""

        def recovery_registry_factory() -> Any:
            from casare_rpa.infrastructure.execution.recovery_strategies import (
                RecoveryStrategyRegistry,
            )

            return RecoveryStrategyRegistry()

        def healing_telemetry_factory() -> Any:
            from casare_rpa.infrastructure.browser.healing.telemetry import (
                SelectorHealingTelemetry,
            )

            return SelectorHealingTelemetry()

        def api_key_store_factory() -> Any:
            from casare_rpa.infrastructure.security.api_key_store import APIKeyStore

            return APIKeyStore()

        def credential_store_factory() -> Any:
            from casare_rpa.infrastructure.security.credential_store import (
                CredentialStore,
            )

            return CredentialStore()

        def memory_queue_factory() -> Any:
            from casare_rpa.infrastructure.queue.memory_queue import MemoryQueue

            return MemoryQueue()

        def robot_metrics_factory() -> Any:
            from casare_rpa.robot.metrics import RobotMetricsCollector

            return RobotMetricsCollector()

        def error_handler_factory() -> Any:
            from casare_rpa.utils.resilience.error_handler import GlobalErrorHandler

            return GlobalErrorHandler()

        container.register_singleton(
            "recovery_strategy_registry", factory=recovery_registry_factory
        )
        container.register_singleton("healing_telemetry", factory=healing_telemetry_factory)
        container.register_singleton("api_key_store", factory=api_key_store_factory)
        container.register_singleton("credential_store", factory=credential_store_factory)
        container.register_singleton("memory_queue", factory=memory_queue_factory)
        container.register_singleton("robot_metrics", factory=robot_metrics_factory)
        container.register_singleton("error_handler", factory=error_handler_factory)

        logger.debug("InfrastructureProvider registered")


class OutputCaptureController:
    """
    Controller for stdout/stderr capture.

    Manages the output capture lifecycle without using globals.
    Thread-safe: Uses internal lock for state management.
    """

    def __init__(self) -> None:
        """Initialize the controller."""
        self._capture: Optional[Any] = None
        self._lock = threading.Lock()

    def set_callbacks(
        self,
        stdout_callback: Optional[Callable[[str], None]] = None,
        stderr_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        Set output callbacks.

        Args:
            stdout_callback: Called with each line of stdout
            stderr_callback: Called with each line of stderr
        """
        from casare_rpa.infrastructure.observability.stdout_capture import OutputCapture

        with self._lock:
            if self._capture:
                self._capture.stop()

            self._capture = OutputCapture(stdout_callback, stderr_callback)
            self._capture.start()

    def remove_callbacks(self) -> None:
        """Remove callbacks and restore original streams."""
        with self._lock:
            if self._capture:
                self._capture.stop()
                self._capture = None

    def dispose(self) -> None:
        """Cleanup on shutdown."""
        self.remove_callbacks()


class UILogController:
    """
    Controller for UI log sink.

    Manages the loguru UI sink lifecycle without using globals.
    Thread-safe: Uses internal lock for state management.
    """

    def __init__(self) -> None:
        """Initialize the controller."""
        self._sink: Optional[Any] = None
        self._handler_id: Optional[int] = None
        self._lock = threading.Lock()

    def set_callback(
        self,
        callback: Callable[[str, str, str, str], None],
        min_level: str = "DEBUG",
    ) -> None:
        """
        Set UI log callback.

        Args:
            callback: Function(level, message, module, timestamp)
            min_level: Minimum log level
        """
        from loguru import logger
        from casare_rpa.infrastructure.observability.logging import UILoguruSink

        with self._lock:
            # Remove existing
            if self._handler_id is not None:
                try:
                    logger.remove(self._handler_id)
                except ValueError:
                    pass
                self._handler_id = None

            # Add new
            self._sink = UILoguruSink(callback, min_level)
            self._handler_id = logger.add(
                self._sink,
                format="{message}",
                level=min_level,
            )

    def remove_callback(self) -> None:
        """Remove UI log callback."""
        from loguru import logger

        with self._lock:
            if self._handler_id is not None:
                try:
                    logger.remove(self._handler_id)
                except ValueError:
                    pass
                self._handler_id = None
            self._sink = None

    def dispose(self) -> None:
        """Cleanup on shutdown."""
        self.remove_callback()


class PresentationProvider(BaseProvider):
    """
    Provider for presentation-layer dependencies.

    Manages UI-related singletons that bridge infrastructure and presentation.
    """

    @classmethod
    def register(cls, container: "DIContainer") -> None:
        """Register presentation dependencies."""
        container.register_singleton(
            "output_capture_controller",
            implementation=OutputCaptureController,
        )
        container.register_singleton(
            "ui_log_controller",
            implementation=UILogController,
        )
        logger.debug("PresentationProvider registered")


def register_all_providers(container: "DIContainer") -> None:
    """
    Register all providers with the container.

    Called once at application startup.
    """
    ConfigProvider.register(container)
    EventBusProvider.register(container)
    StorageProvider.register(container)
    InfrastructureProvider.register(container)
    PresentationProvider.register(container)
    logger.info("All dependency providers registered")
