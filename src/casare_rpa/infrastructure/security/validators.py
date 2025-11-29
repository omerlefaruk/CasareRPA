"""
Security validators for CasareRPA infrastructure.

Provides validation functions to prevent SQL injection, command injection,
and other attack vectors. All user-controlled inputs MUST be validated
before use in sensitive operations.

Security Principles:
- Allowlist validation over blocklist
- Strict regex patterns for identifiers
- Fail closed on invalid input
- No exceptions for convenience

CWE Mitigations:
- CWE-89: SQL Injection via identifier validation
- CWE-20: Improper Input Validation
- CWE-707: Improper Neutralization
"""

import re
from typing import Optional
from loguru import logger


# SQL Identifier validation pattern
# Allows: alphanumeric, underscore, max 63 chars (PostgreSQL limit)
# Prevents: quotes, semicolons, spaces, special chars
SQL_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,62}$")

# Robot ID validation pattern
# Allows: alphanumeric, dash, underscore, 1-64 chars
# Prevents: special chars that could be used in injection
ROBOT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9\-_]{1,64}$")

# Workflow ID pattern (UUIDs or safe identifiers)
WORKFLOW_ID_PATTERN = re.compile(r"^[a-zA-Z0-9\-_]{1,128}$")

# Job ID pattern (UUIDs)
JOB_ID_PATTERN = re.compile(
    r"^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$"
)


def validate_sql_identifier(identifier: str, name: str = "identifier") -> str:
    """
    Validate SQL identifier (table/column name) to prevent SQL injection.

    This prevents CWE-89 (SQL Injection) by ensuring identifiers cannot
    contain quotes, semicolons, or other SQL metacharacters.

    Args:
        identifier: The identifier to validate
        name: Human-readable name for error messages

    Returns:
        The validated identifier (unchanged)

    Raises:
        ValueError: If identifier is invalid

    Example:
        >>> validate_sql_identifier("workflow_checkpoints")
        'workflow_checkpoints'
        >>> validate_sql_identifier("users; DROP TABLE")
        ValueError: Invalid SQL identifier for 'table'
    """
    if not identifier:
        raise ValueError(f"Invalid SQL {name}: empty string")

    if not SQL_IDENTIFIER_PATTERN.match(identifier):
        logger.error(
            f"SQL injection attempt detected: {name}='{identifier}' "
            f"(pattern violation)"
        )
        raise ValueError(
            f"Invalid SQL {name}: must match [a-zA-Z_][a-zA-Z0-9_]{{0,62}}"
        )

    # Additional blocklist for reserved words (defense in depth)
    reserved_keywords = {
        "SELECT",
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "CREATE",
        "ALTER",
        "TRUNCATE",
        "EXEC",
        "EXECUTE",
        "UNION",
        "WHERE",
        "FROM",
        "JOIN",
        "INTO",
        "VALUES",
        "SET",
        "DECLARE",
    }

    if identifier.upper() in reserved_keywords:
        logger.error(
            f"SQL injection attempt detected: {name}='{identifier}' "
            f"(reserved keyword)"
        )
        raise ValueError(
            f"Invalid SQL {name}: cannot use reserved keyword '{identifier}'"
        )

    logger.debug(f"Validated SQL identifier: {name}='{identifier}'")
    return identifier


def validate_robot_id(robot_id: Optional[str]) -> str:
    """
    Validate robot_id to prevent injection attacks in database queries.

    Robot IDs are used in WHERE clauses and must be sanitized to prevent
    SQL injection (CWE-89) and other attacks.

    Args:
        robot_id: The robot identifier to validate

    Returns:
        The validated robot_id

    Raises:
        ValueError: If robot_id is invalid or missing

    Example:
        >>> validate_robot_id("robot-001")
        'robot-001'
        >>> validate_robot_id("'; DROP TABLE robots; --")
        ValueError: Invalid robot_id
    """
    if not robot_id:
        raise ValueError("robot_id is required and cannot be empty")

    if not ROBOT_ID_PATTERN.match(robot_id):
        logger.error(f"Invalid robot_id detected: '{robot_id}' (pattern violation)")
        raise ValueError("Invalid robot_id: must match ^[a-zA-Z0-9\\-_]{1,64}$")

    logger.debug(f"Validated robot_id: '{robot_id}'")
    return robot_id


def validate_workflow_id(workflow_id: str) -> str:
    """
    Validate workflow_id to prevent injection attacks.

    Args:
        workflow_id: The workflow identifier to validate

    Returns:
        The validated workflow_id

    Raises:
        ValueError: If workflow_id is invalid
    """
    if not workflow_id:
        raise ValueError("workflow_id is required and cannot be empty")

    if not WORKFLOW_ID_PATTERN.match(workflow_id):
        logger.error(
            f"Invalid workflow_id detected: '{workflow_id}' (pattern violation)"
        )
        raise ValueError("Invalid workflow_id: must match ^[a-zA-Z0-9\\-_]{1,128}$")

    logger.debug(f"Validated workflow_id: '{workflow_id}'")
    return workflow_id


def validate_job_id(job_id: str) -> str:
    """
    Validate job_id (UUID format) to prevent injection attacks.

    Args:
        job_id: The job identifier to validate

    Returns:
        The validated job_id

    Raises:
        ValueError: If job_id is invalid
    """
    if not job_id:
        raise ValueError("job_id is required and cannot be empty")

    if not JOB_ID_PATTERN.match(job_id):
        logger.error(f"Invalid job_id detected: '{job_id}' (not a valid UUID)")
        raise ValueError("Invalid job_id: must be a valid UUID format")

    logger.debug(f"Validated job_id: '{job_id}'")
    return job_id


def sanitize_for_logging(value: str, max_length: int = 50) -> str:
    """
    Sanitize a string for safe logging (prevent log injection).

    Removes newlines, carriage returns, and truncates to prevent:
    - Log injection (CWE-117)
    - Log forging
    - Excessive log size

    Args:
        value: The string to sanitize
        max_length: Maximum length to truncate to

    Returns:
        Sanitized string safe for logging
    """
    # Remove control characters that could be used for log injection
    sanitized = value.replace("\n", "\\n").replace("\r", "\\r")
    sanitized = sanitized.replace("\t", "\\t")

    # Truncate
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."

    return sanitized
