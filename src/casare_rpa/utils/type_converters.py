"""Type conversion utilities for safe value transformations.

These utilities handle None, empty strings, and invalid values gracefully,
making them ideal for processing user input and configuration values.
"""

from typing import Any


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to integer.

    Handles None, empty strings, and invalid values gracefully.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Integer value or default
    """
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float.

    Handles None, empty strings, and invalid values gracefully.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Float value or default
    """
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_str(value: Any, default: str = "") -> str:
    """Safely convert value to string.

    Handles None and invalid values gracefully.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        String value or default
    """
    if value is None:
        return default
    try:
        return str(value)
    except (ValueError, TypeError):
        return default


def safe_bool(value: Any, default: bool = False) -> bool:
    """Safely convert value to boolean.

    Handles string representations like "true", "false", "1", "0".

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Boolean value or default
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lower_val = value.lower().strip()
        if lower_val in ("true", "1", "yes", "on"):
            return True
        if lower_val in ("false", "0", "no", "off", ""):
            return False
    try:
        return bool(value)
    except (ValueError, TypeError):
        return default
