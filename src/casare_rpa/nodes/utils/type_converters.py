"""Type conversion utilities for node implementations."""


def safe_int(value, default: int = 0) -> int:
    """Safely convert value to integer.

    Handles None, empty strings, and invalid values gracefully.
    """
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default: float = 0.0) -> float:
    """Safely convert value to float.

    Handles None, empty strings, and invalid values gracefully.
    """
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_str(value, default: str = "") -> str:
    """Safely convert value to string.

    Handles None and invalid values gracefully.
    """
    if value is None:
        return default
    try:
        return str(value)
    except (ValueError, TypeError):
        return default
