"""
Exceptions for AI agent workflow generation.
"""

import time
from typing import Any, Dict, List, Optional


class WorkflowGenerationError(Exception):
    """Base exception for workflow generation errors."""

    def __init__(
        self,
        message: str,
        error_type: str = "GENERATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.details = details or {}
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize exception to dictionary."""
        return {
            "error_type": self.error_type,
            "message": str(self),
            "details": self.details,
            "timestamp": self.timestamp,
        }


class LLMCallError(WorkflowGenerationError):
    """Error during LLM API call."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, "LLM_CALL_ERROR", details)


class JSONParseError(WorkflowGenerationError):
    """Error parsing JSON from LLM response."""

    def __init__(self, message: str, response_preview: str = "") -> None:
        super().__init__(
            message,
            "JSON_PARSE_ERROR",
            {"response_preview": response_preview[:500]},
        )


class ValidationError(WorkflowGenerationError):
    """Error during workflow validation."""

    def __init__(self, message: str, validation_errors: List[str]) -> None:
        super().__init__(
            message,
            "VALIDATION_ERROR",
            {"validation_errors": validation_errors},
        )


class MaxRetriesExceededError(WorkflowGenerationError):
    """Maximum retry attempts exceeded."""

    def __init__(self, attempts: int, last_error: Optional[str] = None) -> None:
        super().__init__(
            f"Max retries ({attempts}) exceeded",
            "MAX_RETRIES_EXCEEDED",
            {"attempts": attempts, "last_error": last_error},
        )
