"""Loguru adapter for domain logging interface.

Adapts loguru to the domain ILogger protocol, allowing domain layer
to use logging without depending directly on loguru.
"""

from loguru import logger as _logger

from casare_rpa.domain.interfaces.logger import ILogger, LoggerService


class LoguruLogger(ILogger):
    """Loguru implementation of the ILogger protocol.

    Bridges the domain logging interface to loguru's actual logging,
    preserving all of loguru's capabilities including structured binding.
    """

    def debug(self, msg: str, **kwargs) -> None:
        """Log a debug message with optional bound context."""
        if kwargs:
            _logger.bind(**kwargs).debug(msg)
        else:
            _logger.debug(msg)

    def info(self, msg: str, **kwargs) -> None:
        """Log an info message with optional bound context."""
        if kwargs:
            _logger.bind(**kwargs).info(msg)
        else:
            _logger.info(msg)

    def warning(self, msg: str, **kwargs) -> None:
        """Log a warning message with optional bound context."""
        if kwargs:
            _logger.bind(**kwargs).warning(msg)
        else:
            _logger.warning(msg)

    def error(self, msg: str, **kwargs) -> None:
        """Log an error message with optional bound context."""
        if kwargs:
            _logger.bind(**kwargs).error(msg)
        else:
            _logger.error(msg)

    def critical(self, msg: str, **kwargs) -> None:
        """Log a critical message with optional bound context."""
        if kwargs:
            _logger.bind(**kwargs).critical(msg)
        else:
            _logger.critical(msg)


# Auto-configure on module import
# This ensures the logger is available when domain code is first loaded
LoggerService.configure(LoguruLogger())
