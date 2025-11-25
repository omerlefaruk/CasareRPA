"""
Variable Resolution Utility for CasareRPA.

Provides functionality to resolve {{variable_name}} patterns in strings
with actual variable values from the execution context.
"""

import re
from typing import Any, Dict

from loguru import logger


# Pattern to match {{variable_name}} with optional whitespace
VARIABLE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def resolve_variables(value: Any, variables: Dict[str, Any]) -> Any:
    """
    Replace {{variable_name}} patterns with actual values from variables dict.

    This function supports the UiPath/Power Automate style variable substitution
    where users can reference global variables in node properties using
    the {{variable_name}} syntax.

    Args:
        value: The value to resolve (only strings are processed)
        variables: Dict of variable name -> value

    Returns:
        The resolved value with all {{variable}} patterns replaced.
        Non-string values are returned unchanged.

    Examples:
        >>> resolve_variables("https://{{website}}", {"website": "google.com"})
        "https://google.com"

        >>> resolve_variables("Hello {{name}}!", {"name": "World"})
        "Hello World!"

        >>> resolve_variables(123, {"x": "y"})  # Non-string unchanged
        123
    """
    if not isinstance(value, str):
        return value

    if "{{" not in value:
        # Fast path: no variables to resolve
        return value

    def replace_match(match: re.Match) -> str:
        var_name = match.group(1)
        if var_name in variables:
            resolved = variables[var_name]
            logger.debug(f"Resolved variable {{{{{{var_name}}}}}} -> {resolved}")
            return str(resolved) if resolved is not None else ""
        else:
            # Keep original if variable not found
            logger.warning(f"Variable '{var_name}' not found, keeping {{{{{{var_name}}}}}}")
            return match.group(0)

    return VARIABLE_PATTERN.sub(replace_match, value)


def resolve_dict_variables(data: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve variables in all string values of a dictionary.

    Args:
        data: Dictionary with potentially templated string values
        variables: Dict of variable name -> value

    Returns:
        New dictionary with all string values resolved
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = resolve_variables(value, variables)
        elif isinstance(value, dict):
            result[key] = resolve_dict_variables(value, variables)
        elif isinstance(value, list):
            result[key] = [
                resolve_variables(item, variables) if isinstance(item, str) else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def extract_variable_names(value: str) -> list:
    """
    Extract all variable names referenced in a string.

    Args:
        value: String potentially containing {{variable}} patterns

    Returns:
        List of variable names found in the string

    Examples:
        >>> extract_variable_names("{{url}}/{{path}}")
        ["url", "path"]
    """
    if not isinstance(value, str):
        return []

    return VARIABLE_PATTERN.findall(value)


def has_variables(value: str) -> bool:
    """
    Check if a string contains any {{variable}} patterns.

    Args:
        value: String to check

    Returns:
        True if the string contains variable references
    """
    if not isinstance(value, str):
        return False

    return bool(VARIABLE_PATTERN.search(value))
