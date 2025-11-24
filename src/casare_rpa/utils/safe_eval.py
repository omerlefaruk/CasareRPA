"""
Safe expression evaluation for CasareRPA.

This module provides secure expression evaluation without using Python's
dangerous eval() function. Uses simpleeval for safe arithmetic and
comparison expressions.
"""

import ast
import operator
from typing import Any, Dict, Optional
from simpleeval import simple_eval, EvalWithCompoundTypes
from loguru import logger


# Safe operators for simpleeval
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.And: lambda a, b: a and b,
    ast.Or: lambda a, b: a or b,
    ast.Not: operator.not_,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
}

# Safe built-in functions for expressions
SAFE_FUNCTIONS = {
    'len': len,
    'str': str,
    'int': int,
    'float': float,
    'bool': bool,
    'abs': abs,
    'min': min,
    'max': max,
    'sum': sum,
    'round': round,
    'sorted': sorted,
    'list': list,
    'tuple': tuple,
    'set': set,
    'dict': dict,
    'range': range,
    'enumerate': enumerate,
    'zip': zip,
    'any': any,
    'all': all,
    'isinstance': isinstance,
    'type': type,
    'upper': lambda s: s.upper() if isinstance(s, str) else s,
    'lower': lambda s: s.lower() if isinstance(s, str) else s,
    'strip': lambda s: s.strip() if isinstance(s, str) else s,
    'split': lambda s, sep=None: s.split(sep) if isinstance(s, str) else s,
    'join': lambda sep, items: sep.join(items) if isinstance(sep, str) else '',
    'startswith': lambda s, prefix: s.startswith(prefix) if isinstance(s, str) else False,
    'endswith': lambda s, suffix: s.endswith(suffix) if isinstance(s, str) else False,
    'contains': lambda s, sub: sub in s if isinstance(s, str) else False,
    'replace': lambda s, old, new: s.replace(old, new) if isinstance(s, str) else s,
}


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
        self._evaluator = EvalWithCompoundTypes(
            operators=SAFE_OPERATORS,
            functions=SAFE_FUNCTIONS,
            names=self.variables
        )

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
        if not expression or not expression.strip():
            return None

        expression = expression.strip()

        # First, try to parse as a simple literal
        try:
            return ast.literal_eval(expression)
        except (ValueError, SyntaxError):
            pass

        # Try safe evaluation with simpleeval
        try:
            # Update evaluator names with current variables
            self._evaluator.names = self.variables
            result = self._evaluator.eval(expression)
            logger.debug(f"Safe eval: '{expression}' -> {result}")
            return result
        except Exception as e:
            logger.warning(f"Safe evaluation failed for '{expression}': {e}")
            raise ValueError(f"Invalid or unsafe expression: {expression}") from e

    def update_variables(self, variables: Dict[str, Any]) -> None:
        """Update available variables."""
        self.variables.update(variables)
        self._evaluator.names = self.variables


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
    evaluator = SafeExpressionEvaluator(variables)
    return evaluator.evaluate(expression)


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
