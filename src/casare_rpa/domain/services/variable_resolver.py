"""
Variable Resolution Utility for CasareRPA.

Provides functionality to resolve {{variable_name}} patterns in strings
with actual variable values from the execution context.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


# Patterns for variable substitution (Standard: {{var}}, Legacy: ${var}, %var%)
# Pattern 1 matches {{variable_name}}
# Pattern 2 matches ${variable_name}
# Pattern 3 matches %variable_name%
# Supports: {{variable}}, {{$systemVar}}, {{node.output}}, {{data.nested.path}}, {{list[0]}}
VARIABLE_PATTERN = re.compile(
    r"\{\{\s*(\$?[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*|\[\d+\])*)\s*\}\}"  # {{var}}
    r"|\$\{\s*(\$?[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*|\[\d+\])*)\s*\}"  # ${var}
    r"|\%([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*|\[\d+\])*)\%"  # %var%
)

# Pattern to parse path segments (handles both .key and [index])
PATH_SEGMENT_PATTERN = re.compile(r"\.([a-zA-Z_][a-zA-Z0-9_]*)|\[(\d+)\]")

# PERFORMANCE: Pre-compiled patterns for single variable detection (type preservation)
SINGLE_VAR_PATTERNS = [
    re.compile(r"^\{\{\s*(\$?[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*|\[\d+\])*)\s*\}\}$"),
    re.compile(r"^\$\{\s*(\$?[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*|\[\d+\])*)\s*\}$"),
    re.compile(r"^\%([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*|\[\d+\])*)\%$"),
]


def _resolve_system_variable(name: str) -> Any:
    """
    Resolve built-in system variables that start with $.

    These are computed dynamically at resolution time.

    Args:
        name: Variable name (e.g., "$currentDate")

    Returns:
        The resolved value, or None if not a recognized system variable
    """
    from datetime import datetime

    now = datetime.now()

    system_vars = {
        "$currentDate": now.strftime("%Y-%m-%d"),
        "$currentTime": now.strftime("%H:%M:%S"),
        "$currentDateTime": now.isoformat(),
        "$timestamp": int(now.timestamp()),
    }

    return system_vars.get(name)


def _resolve_nested_path(path: str, variables: dict[str, Any]) -> Any:
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


def resolve_variables(value: Any, variables: dict[str, Any]) -> Any:
    """
    Replace {{variable_name}}, ${variable_name}, or %variable_name% patterns
    with actual values from variables dict.

    Standard: {{variable_name}}
    Legacy: ${variable_name}, %variable_name% (supported for backward compatibility)

    Type Preservation:
    - If the entire value is a single variable reference, returns the
      original type (bool, int, dict, list, etc.)
    - If the value contains text around the variable (like "Value: {{x}}"),
      returns a string with the variable value interpolated

    Args:
        value: The value to resolve (only strings are processed by this function)
        variables: Dict of variable name -> value

    Returns:
        The resolved value with all variable patterns replaced.
        Non-string values are returned unchanged.
    """
    if not isinstance(value, str):
        return value

    # Fast path check for any of the supported markers
    if not any(marker in value for marker in ("{{", "${", "%")):
        return value

    # Check if the entire value is a single variable reference
    # This allows preserving the original type (bool, int, dict, etc.)
    stripped = value.strip()
    var_path = None

    for pattern in SINGLE_VAR_PATTERNS:
        match = pattern.match(stripped)
        if match:
            var_path = match.group(1)
            break

    if var_path:
        # Check system variables first (e.g., $currentDate)
        if var_path.startswith("$"):
            resolved = _resolve_system_variable(var_path)
            if resolved is not None:
                return resolved

        # Try direct lookup first
        if var_path in variables:
            return variables[var_path]

        # Try nested path resolution
        resolved = _resolve_nested_path(var_path, variables)
        if resolved is not None:
            return resolved

        # Variable not found - return original string
        logger.warning(f"Variable '{var_path}' not found")
        return value

    # Multiple variables or text around variable - do string replacement
    def replace_match(match: re.Match) -> str:
        # Find which group matched (1, 2, or 3)
        var_path = match.group(1) or match.group(2) or match.group(3)
        if not var_path:
            return match.group(0)

        # Check system variables first
        if var_path.startswith("$"):
            resolved = _resolve_system_variable(var_path)
            if resolved is not None:
                return str(resolved)

        # Try direct lookup
        if var_path in variables:
            resolved = variables[var_path]
            return str(resolved) if resolved is not None else ""

        # Try nested path resolution
        resolved = _resolve_nested_path(var_path, variables)
        if resolved is not None:
            return str(resolved)

        # Keep original if variable not found
        return match.group(0)

    return VARIABLE_PATTERN.sub(replace_match, value)


def resolve_any(value: Any, variables: dict[str, Any]) -> Any:
    """
    Recursively resolve variables in any data structure (string, list, dict).

    Args:
        value: Any data structure to resolve
        variables: Dict of variable name -> value

    Returns:
        Resolved data structure
    """
    if isinstance(value, str):
        return resolve_variables(value, variables)
    elif isinstance(value, dict):
        return {k: resolve_any(v, variables) for k, v in value.items()}
    elif isinstance(value, list):
        return [resolve_any(item, variables) for item in value]
    return value


def resolve_dict_variables(data: dict[str, Any], variables: dict[str, Any]) -> dict[str, Any]:
    """
    Resolve variables in all string values of a dictionary.

    DEPRECATED: Use resolve_any() instead.
    """
    return resolve_any(data, variables)


def extract_variable_names(value: str) -> list:
    """
    Extract all variable names referenced in a string across all syntaxes.

    Args:
        value: String potentially containing variable patterns

    Returns:
        List of variable names found in the string
    """
    if not isinstance(value, str):
        return []

    results = []
    for match in VARIABLE_PATTERN.finditer(value):
        var_name = match.group(1) or match.group(2) or match.group(3)
        if var_name:
            results.append(var_name)
    return results


def has_variables(value: str) -> bool:
    """
    Check if a string contains any supported variable patterns.
    """
    if not isinstance(value, str):
        return False

    return bool(VARIABLE_PATTERN.search(value))
