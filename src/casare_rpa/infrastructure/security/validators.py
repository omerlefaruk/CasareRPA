"""
Security validators for input sanitization.

Provides validation functions to prevent injection attacks and ensure
input data meets security requirements.
"""

import re
from typing import Any

# SQL identifier validation (table names, column names)
SQL_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,62}$")
SQL_KEYWORDS = {
    "DROP",
    "ALTER",
    "EXECUTE",
    "DELETE",
    "TRUNCATE",
    "CREATE",
    "INSERT",
    "UPDATE",
    "SELECT",
    "UNION",
    "OR",
    "AND",
    ";",
    "--",
}

# Robot ID validation (alphanumeric, hyphen, underscore only)
ROBOT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9\-_]{1,64}$")

# Workflow ID validation
WORKFLOW_ID_PATTERN = re.compile(r"^[a-zA-Z0-9\-_]{1,128}$")


class ValidationError(ValueError):
    """Raised when validation fails."""

    pass


def validate_sql_identifier(value: str, name: str = "identifier") -> str:
    """
    Validate SQL identifier (table name, column name).

    Prevents SQL injection by enforcing strict naming rules:
    - Must start with lowercase letter
    - Can only contain lowercase letters, digits, underscores
    - Maximum 63 characters (PostgreSQL limit)
    - Cannot contain SQL keywords

    Args:
        value: Identifier to validate
        name: Name of the field being validated (for error messages)

    Returns:
        The validated identifier

    Raises:
        ValidationError: If validation fails

    Examples:
        >>> validate_sql_identifier("workflow_checkpoints")
        'workflow_checkpoints'
        >>> validate_sql_identifier("users")
        'users'
        >>> validate_sql_identifier("DROP TABLE")  # Raises ValidationError
    """
    if not value:
        raise ValidationError(f"{name} cannot be empty")

    if not isinstance(value, str):
        raise ValidationError(f"{name} must be a string")

    # Check pattern
    if not SQL_IDENTIFIER_PATTERN.match(value):
        raise ValidationError(
            f"Invalid {name}: '{value}'. Must start with lowercase letter and "
            f"contain only lowercase letters, digits, and underscores (max 63 chars)"
        )

    # Check for SQL keywords (as whole words to avoid false positives like "or" in "workflow")
    import re

    value_upper = value.upper()
    for keyword in SQL_KEYWORDS:
        # Match whole words only (not partial matches)
        if re.search(rf"\b{re.escape(keyword)}\b", value_upper):
            raise ValidationError(
                f"Invalid {name}: '{value}' contains SQL keyword '{keyword}'"
            )

    return value


def validate_robot_id(value: str) -> str:
    """
    Validate robot ID for database safety.

    Enforces strict format to prevent:
    - SQL injection via robot_id
    - Robot impersonation attacks
    - Database integrity violations

    Args:
        value: Robot ID to validate

    Returns:
        The validated robot ID

    Raises:
        ValidationError: If validation fails

    Examples:
        >>> validate_robot_id("robot-worker-01")
        'robot-worker-01'
        >>> validate_robot_id("robot_123")
        'robot_123'
        >>> validate_robot_id("'; DROP TABLE robots--")  # Raises ValidationError
    """
    if not value:
        raise ValidationError("robot_id cannot be empty")

    if not isinstance(value, str):
        raise ValidationError("robot_id must be a string")

    if not ROBOT_ID_PATTERN.match(value):
        raise ValidationError(
            f"Invalid robot_id: '{value}'. Must contain only alphanumeric "
            f"characters, hyphens, and underscores (1-64 chars)"
        )

    return value


def validate_workflow_id(value: str) -> str:
    """
    Validate workflow ID.

    Args:
        value: Workflow ID to validate

    Returns:
        The validated workflow ID

    Raises:
        ValidationError: If validation fails
    """
    if not value:
        raise ValidationError("workflow_id cannot be empty")

    if not isinstance(value, str):
        raise ValidationError("workflow_id must be a string")

    if not WORKFLOW_ID_PATTERN.match(value):
        raise ValidationError(
            f"Invalid workflow_id: '{value}'. Must contain only alphanumeric "
            f"characters, hyphens, and underscores (1-128 chars)"
        )

    return value


def sanitize_log_value(value: Any, mask_patterns: list[str] = None) -> str:
    """
    Sanitize a value for safe logging (mask credentials).

    Args:
        value: Value to sanitize
        mask_patterns: Additional regex patterns to mask

    Returns:
        Sanitized string safe for logging
    """
    if value is None:
        return "None"

    value_str = str(value)

    # Default patterns to mask
    patterns = [
        (r"postgresql://[^@]+@[^/]+/[^\s]+", "postgresql://***@***/***"),
        (r"postgres://[^@]+@[^/]+/[^\s]+", "postgres://***@***/***"),
        (r'password["\']?\s*[:=]\s*["\']?[^\s"\']+', "password=***"),
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?[^\s"\']+', "api_key=***"),
        (r'secret["\']?\s*[:=]\s*["\']?[^\s"\']+', "secret=***"),
        (r'token["\']?\s*[:=]\s*["\']?[^\s"\']+', "token=***"),
    ]

    if mask_patterns:
        patterns.extend((p, "***") for p in mask_patterns)

    sanitized = value_str
    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

    return sanitized
