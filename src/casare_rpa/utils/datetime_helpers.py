"""
Datetime parsing and formatting utilities for CasareRPA.

Consolidated helper functions for parsing datetime strings from various formats.
Used across domain entities, nodes, and presentation layer.
"""

from datetime import datetime
from typing import List, Optional, Union

# Common datetime formats to try when auto-detecting
DEFAULT_DATETIME_FORMATS: list[str] = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%d",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
    "%Y/%m/%d %H:%M:%S",
]


def parse_datetime(
    value: str | datetime | int | float | None,
    format_string: str | None = None,
) -> datetime | None:
    """Parse a datetime value from various input types.

    Handles:
    - None or empty string: Returns None
    - datetime object: Returns as-is
    - Unix timestamp (int/float): Converts from timestamp
    - ISO 8601 strings: Handles 'Z' suffix for UTC
    - Common date formats: Auto-detects from predefined list

    Args:
        value: The value to parse. Can be:
            - None: Returns None
            - datetime: Returns as-is
            - int/float: Treated as Unix timestamp
            - str: Parsed using format_string or auto-detection
        format_string: Optional strptime format. If provided, only this
            format is tried. If None, auto-detection is used.

    Returns:
        Parsed datetime object, or None if parsing fails or value is empty.

    Examples:
        >>> parse_datetime("2024-01-15T10:30:00Z")
        datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

        >>> parse_datetime(1705312200.0)
        datetime(2024, 1, 15, 10, 30, 0)

        >>> parse_datetime("15/01/2024", "%d/%m/%Y")
        datetime(2024, 1, 15, 0, 0, 0)

        >>> parse_datetime(None)
        None
    """
    # Handle None or empty string
    if value is None or value == "":
        return None

    # Already a datetime
    if isinstance(value, datetime):
        return value

    # Unix timestamp
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value)
        except (ValueError, OSError, OverflowError):
            return None

    # String parsing
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None

        # If explicit format provided, use only that
        if format_string:
            try:
                return datetime.strptime(value, format_string)
            except (ValueError, AttributeError):
                return None

        # Try ISO format with Z suffix (UTC)
        if "Z" in value or "+" in value or value.endswith("-00:00"):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        # Try common formats
        for fmt in DEFAULT_DATETIME_FORMATS:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue

        # Final attempt: fromisoformat without Z handling
        try:
            return datetime.fromisoformat(value)
        except (ValueError, AttributeError):
            pass

    return None


def format_datetime(
    value: datetime | None,
    format_string: str = "%Y-%m-%d %H:%M:%S",
) -> str | None:
    """Format a datetime object to string.

    Args:
        value: The datetime to format. None returns None.
        format_string: strftime format string.

    Returns:
        Formatted string, or None if value is None.
    """
    if value is None:
        return None
    return value.strftime(format_string)


def to_iso_format(value: datetime | None) -> str | None:
    """Convert datetime to ISO 8601 format string.

    Args:
        value: The datetime to format.

    Returns:
        ISO format string (e.g., "2024-01-15T10:30:00"), or None if value is None.
    """
    if value is None:
        return None
    return value.isoformat()
