"""
Variable Resolution Utility for CasareRPA.

Provides functionality to resolve {{variable_name}} patterns in strings
with actual variable values from the execution context.
"""

import re
from typing import Any, Dict

from loguru import logger


# Pattern to match {{variable_name}} or {{node.output}} with optional whitespace
# Supports: {{variable}}, {{node.output}}, {{data.nested.path}}, {{list[0]}}, {{dict.key[0].nested}}
VARIABLE_PATTERN = re.compile(
    r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*|\[\d+\])*)\s*\}\}"
)

# Pattern to parse path segments (handles both .key and [index])
PATH_SEGMENT_PATTERN = re.compile(r"\.([a-zA-Z_][a-zA-Z0-9_]*)|\[(\d+)\]")


def _resolve_nested_path(path: str, variables: Dict[str, Any]) -> Any:
    """
    Resolve a nested path like "node.output" or "data.field[0].name".

    Args:
        path: Path string like "read.content" or "users[0].name"
        variables: Dict of variable name -> value

    Returns:
        The resolved value, or None if not found
    """
    if "." not in path and "[" not in path:
        # Simple variable, no nesting
        return variables.get(path)

    # Split the path into root and remainder
    # For "read.content", root = "read", remainder = ".content"
    first_dot = path.find(".")
    first_bracket = path.find("[")

    if first_dot == -1 and first_bracket == -1:
        return variables.get(path)

    # Find the first separator
    if first_dot == -1:
        split_pos = first_bracket
    elif first_bracket == -1:
        split_pos = first_dot
    else:
        split_pos = min(first_dot, first_bracket)

    root = path[:split_pos]
    remainder = path[split_pos:]

    # Get the root object
    if root not in variables:
        return None

    current = variables[root]

    # Navigate the path
    for match in PATH_SEGMENT_PATTERN.finditer(remainder):
        if current is None:
            return None

        key = match.group(1)  # .key accessor
        index = match.group(2)  # [index] accessor

        if key is not None:
            # Dict access
            if isinstance(current, dict):
                current = current.get(key)
            elif hasattr(current, key):
                current = getattr(current, key)
            else:
                return None
        elif index is not None:
            # List access
            idx = int(index)
            if isinstance(current, (list, tuple)) and 0 <= idx < len(current):
                current = current[idx]
            else:
                return None

    return current


def resolve_variables(value: Any, variables: Dict[str, Any]) -> Any:
    """
    Replace {{variable_name}} patterns with actual values from variables dict.

    This function supports the UiPath/Power Automate style variable substitution
    where users can reference global variables in node properties using
    the {{variable_name}} syntax.

    Type Preservation:
    - If the entire value is a single {{variable}} reference, returns the
      original type (bool, int, dict, list, etc.)
    - If the value contains text around the variable (like "Value: {{x}}"),
      returns a string with the variable value interpolated

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

        >>> resolve_variables("{{is_valid}}", {"is_valid": True})  # Type preserved
        True

        >>> resolve_variables(123, {"x": "y"})  # Non-string unchanged
        123
    """
    if not isinstance(value, str):
        return value

    if "{{" not in value:
        # Fast path: no variables to resolve
        return value

    # Check if the entire value is a single variable reference
    # This allows preserving the original type (bool, int, dict, etc.)
    stripped = value.strip()
    single_var_match = re.match(
        r"^\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*|\[\d+\])*)\s*\}\}$",
        stripped,
    )
    if single_var_match:
        var_path = single_var_match.group(1)

        # Try direct lookup first
        if var_path in variables:
            resolved = variables[var_path]
            logger.debug(
                f"Resolved variable {{{{{var_path}}}}} -> {resolved} (type preserved)"
            )
            return resolved

        # Try nested path resolution
        resolved = _resolve_nested_path(var_path, variables)
        if resolved is not None:
            logger.debug(
                f"Resolved nested path {{{{{var_path}}}}} -> {resolved} (type preserved)"
            )
            return resolved

        # Variable not found - return original string
        logger.warning(f"Variable '{var_path}' not found, keeping {{{{{var_path}}}}}")
        return value

    # Multiple variables or text around variable - do string replacement
    def replace_match(match: re.Match) -> str:
        var_path = match.group(1)

        # Try direct lookup first (for simple variables like "count")
        if var_path in variables:
            resolved = variables[var_path]
            logger.debug(f"Resolved variable {{{{{var_path}}}}} -> {resolved}")
            return str(resolved) if resolved is not None else ""

        # Try nested path resolution (for "node.output" or "data.field.nested")
        resolved = _resolve_nested_path(var_path, variables)
        if resolved is not None:
            logger.debug(f"Resolved nested path {{{{{var_path}}}}} -> {resolved}")
            return str(resolved)

        # Keep original if variable not found
        logger.warning(f"Variable '{var_path}' not found, keeping {{{{{var_path}}}}}")
        return match.group(0)

    return VARIABLE_PATTERN.sub(replace_match, value)


def resolve_dict_variables(
    data: Dict[str, Any], variables: Dict[str, Any]
) -> Dict[str, Any]:
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
