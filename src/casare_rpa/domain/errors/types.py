"""
CasareRPA - Error Types and Enumerations.

Defines error classification types, categories, severity levels, and recovery actions.
"""

from enum import Enum, auto


class ErrorCategory(Enum):
    """
    High-level error categories for classification.

    Categories help determine recovery strategy:
    - BROWSER: Web automation errors (Playwright)
    - DESKTOP: Windows UI automation errors
    - NETWORK: Connection, timeout, SSL errors
    - DATA: Validation, parsing, type errors
    - RESOURCE: File, memory, permission errors
    - CONFIGURATION: Node/workflow config errors
    - EXECUTION: Runtime execution errors
    - UNKNOWN: Unclassified errors
    """

    BROWSER = auto()
    DESKTOP = auto()
    NETWORK = auto()
    DATA = auto()
    RESOURCE = auto()
    CONFIGURATION = auto()
    EXECUTION = auto()
    UNKNOWN = auto()


class ErrorSeverity(Enum):
    """
    Error severity levels.

    Severity affects:
    - Logging level
    - Recovery strategy aggressiveness
    - Human escalation threshold
    """

    LOW = 1  # Minor, easily recoverable
    MEDIUM = 2  # Significant, may need retry
    HIGH = 3  # Severe, may need human intervention
    CRITICAL = 4  # Fatal, workflow should abort


class ErrorClassification(Enum):
    """
    Error classification for recovery decisions.

    TRANSIENT: Temporary errors that may succeed on retry
        - Network timeouts
        - Element temporarily not visible
        - Application busy/not responding

    PERMANENT: Errors that will not resolve with retry
        - Invalid selector (element doesn't exist)
        - Permission denied
        - Configuration errors

    UNKNOWN: Cannot determine if transient or permanent
        - First occurrence of new error
        - Generic exceptions
    """

    TRANSIENT = auto()
    PERMANENT = auto()
    UNKNOWN = auto()


class RecoveryAction(Enum):
    """
    Recommended recovery actions.

    Actions the recovery system can take:
    - RETRY: Attempt the operation again
    - SKIP: Skip this node and continue
    - FALLBACK: Use alternative path/value
    - COMPENSATE: Run rollback operations
    - ABORT: Stop workflow execution
    - ESCALATE: Request human intervention
    """

    RETRY = auto()
    SKIP = auto()
    FALLBACK = auto()
    COMPENSATE = auto()
    ABORT = auto()
    ESCALATE = auto()


__all__ = [
    "ErrorCategory",
    "ErrorSeverity",
    "ErrorClassification",
    "RecoveryAction",
]
