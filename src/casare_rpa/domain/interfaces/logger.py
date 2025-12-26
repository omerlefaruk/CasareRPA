"""Domain-agnostic logging interface.

Provides protocol-based logger injection to keep domain layer pure.
"""

from typing import Protocol


class ILogger(Protocol):
    """Domain-agnostic logger protocol.

    Defines the logging interface that domain services can use without
    depending on external logging implementations like loguru.
    """

    def debug(self, msg: str, **kwargs) -> None:
        """Log a debug message."""

    def info(self, msg: str, **kwargs) -> None:
        """Log an info message."""

    def warning(self, msg: str, **kwargs) -> None:
        """Log a warning message."""

    def error(self, msg: str, **kwargs) -> None:
        """Log an error message."""

    def critical(self, msg: str, **kwargs) -> None:
        """Log a critical message."""


class _NoOpLogger(ILogger):
    """Default no-op logger used before configuration."""

    def debug(self, msg: str, **kwargs) -> None:
        pass

    def info(self, msg: str, **kwargs) -> None:
        pass

    def warning(self, msg: str, **kwargs) -> None:
        pass

    def error(self, msg: str, **kwargs) -> None:
        pass

    def critical(self, msg: str, **kwargs) -> None:
        pass


class LoggerService:
    """Domain logger service for dependency injection.

    Provides a singleton accessor for the configured logger implementation.
    Falls back to a no-op logger if not configured, allowing domain code
    to work safely in tests or during early initialization.
    """

    _instance: ILogger = _NoOpLogger()

    @classmethod
    def get(cls) -> ILogger:
        """Get the configured logger instance.

        Returns:
            The configured ILogger implementation, or a no-op logger if
            not yet configured.
        """
        return cls._instance

    @classmethod
    def configure(cls, logger: ILogger) -> None:
        """Configure the global logger instance.

        Args:
            logger: An implementation of the ILogger protocol.
        """
        cls._instance = logger

    @classmethod
    def is_configured(cls) -> bool:
        """Check if the logger has been configured with a real implementation."""
        return not isinstance(cls._instance, _NoOpLogger)
