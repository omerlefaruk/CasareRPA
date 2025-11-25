"""
Safe expression evaluation for CasareRPA.

This module provides secure expression evaluation without using Python's
dangerous eval() function. Uses simpleeval for safe arithmetic and
comparison expressions.
"""

import ast
from typing import Any, Dict, Optional
from simpleeval import simple_eval, DEFAULT_OPERATORS, DEFAULT_FUNCTIONS
from loguru import logger


# Safe built-in functions for expressions
SAFE_FUNCTIONS = {
    **DEFAULT_FUNCTIONS,  # Includes rand, randint, int, float, str
    'len': len,
    'bool': bool,
    'abs': abs,
    'min': min,
    'max': max,
    'sum': sum,
    'round': round,
    'sorted': sorted,
    'list': list,
    'tuple': tuple,
    'range': range,
    'any': any,
    'all': all,
}


def safe_eval(expression: str, variables: Optional[Dict[str, Any]] = None) -> Any:
    """
    Convenience function for safe expression evaluation.

    Args:
        expression: Expression string to evaluate
        variables: Dictionary of variables available in the expression

    Returns:
        Result of the expression

    Raises:
        ValueError: If expression is invalid or contains unsafe operations

    Examples:
        >>> safe_eval("2 + 2")
        4
        >>> safe_eval("x > 5", {"x": 10})
        True
        >>> safe_eval("len(items) > 0", {"items": [1, 2, 3]})
        True
    """
    if not expression or not expression.strip():
        return None

    expression = expression.strip()

    # First, try to parse as a simple literal
    try:
        return ast.literal_eval(expression)
    except (ValueError, SyntaxError):
        pass

    # Try safe evaluation with simpleeval using defaults
    try:
        result = simple_eval(
            expression,
            operators=DEFAULT_OPERATORS,
            functions=SAFE_FUNCTIONS,
            names=variables or {}
        )
        logger.debug(f"Safe eval: '{expression}' -> {result}")
        return result
    except Exception as e:
        logger.warning(f"Safe evaluation failed for '{expression}': {e}")
        raise ValueError(f"Invalid or unsafe expression: {expression}") from e


class SafeExpressionEvaluator:
    """
    Safe expression evaluator that prevents code injection.

    Supports:
    - Arithmetic operations: +, -, *, /, //, %, **
    - Comparisons: ==, !=, <, <=, >, >=
    - Logical operators: and, or, not
    - Membership: in, not in
    - Safe built-in functions
    - Variable references from context
    """

    def __init__(self, variables: Optional[Dict[str, Any]] = None):
        """
        Initialize the evaluator.

        Args:
            variables: Dictionary of variables available in expressions
        """
        self.variables = variables or {}

    def evaluate(self, expression: str) -> Any:
        """
        Safely evaluate an expression.

        Args:
            expression: Expression string to evaluate

        Returns:
            Result of the expression

        Raises:
            ValueError: If expression is invalid or contains unsafe operations
        """
        return safe_eval(expression, self.variables)

    def update_variables(self, variables: Dict[str, Any]) -> None:
        """Update available variables."""
        self.variables.update(variables)


def is_safe_expression(expression: str) -> bool:
    """
    Check if an expression appears to be safe to evaluate.

    This is a preliminary check - actual safety is enforced during evaluation.

    Args:
        expression: Expression string to check

    Returns:
        True if expression appears safe, False otherwise
    """
    if not expression:
        return False

    # Blacklist dangerous patterns
    dangerous_patterns = [
        '__',  # Dunder methods
        'import',
        'exec',
        'eval',
        'compile',
        'open',
        'file',
        'input',
        'raw_input',
        'globals',
        'locals',
        'vars',
        'dir',
        'getattr',
        'setattr',
        'delattr',
        'hasattr',
        'classmethod',
        'staticmethod',
        'property',
        'super',
        'lambda',
        'def ',
        'class ',
        'yield',
        'async',
        'await',
    ]

    expression_lower = expression.lower()
    for pattern in dangerous_patterns:
        if pattern in expression_lower:
            logger.warning(f"Potentially dangerous pattern '{pattern}' found in expression")
            return False

    return True
