"""
CasareRPA - Validation Types Module

Contains type definitions for validation: enums, dataclasses, and type aliases.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class ValidationSeverity(Enum):
    """Severity level of validation issues."""

    ERROR = auto()  # Prevents workflow execution
    WARNING = auto()  # May cause issues, but execution can proceed
    INFO = auto()  # Informational message


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""

    severity: ValidationSeverity
    code: str
    message: str
    location: str | None = None  # e.g., "node:abc123", "connection:0"
    suggestion: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "severity": self.severity.name,
            "code": self.code,
            "message": self.message,
            "location": self.location,
            "suggestion": self.suggestion,
        }


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool = True
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        """Get only error-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """Get only warning-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]

    @property
    def error_count(self) -> int:
        """Count of errors."""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Count of warnings."""
        return len(self.warnings)

    def add_error(
        self,
        code: str,
        message: str,
        location: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        """Add an error-level issue."""
        self.issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code=code,
                message=message,
                location=location,
                suggestion=suggestion,
            )
        )
        self.is_valid = False

    def add_warning(
        self,
        code: str,
        message: str,
        location: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        """Add a warning-level issue."""
        self.issues.append(
            ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code=code,
                message=message,
                location=location,
                suggestion=suggestion,
            )
        )

    def add_info(
        self,
        code: str,
        message: str,
        location: str | None = None,
    ) -> None:
        """Add an info-level issue."""
        self.issues.append(
            ValidationIssue(
                severity=ValidationSeverity.INFO,
                code=code,
                message=message,
                location=location,
            )
        )

    def merge(self, other: "ValidationResult") -> None:
        """Merge another validation result into this one."""
        self.issues.extend(other.issues)
        if not other.is_valid:
            self.is_valid = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "is_valid": self.is_valid,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues": [i.to_dict() for i in self.issues],
        }

    def format_summary(self) -> str:
        """Format a human-readable summary."""
        if self.is_valid and not self.issues:
            return "Validation passed with no issues."

        lines = []
        if not self.is_valid:
            lines.append(
                f"Validation FAILED: {self.error_count} error(s), {self.warning_count} warning(s)"
            )
        else:
            lines.append(f"Validation passed with {self.warning_count} warning(s)")

        for issue in self.issues:
            prefix = {"ERROR": "E", "WARNING": "W", "INFO": "I"}[issue.severity.name]
            loc = f" [{issue.location}]" if issue.location else ""
            lines.append(f"  [{prefix}] {issue.code}{loc}: {issue.message}")
            if issue.suggestion:
                lines.append(f"       Suggestion: {issue.suggestion}")

        return "\n".join(lines)


__all__ = [
    "ValidationSeverity",
    "ValidationIssue",
    "ValidationResult",
]
