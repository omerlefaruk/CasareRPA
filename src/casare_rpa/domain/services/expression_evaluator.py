"""
Expression evaluator for runtime expressions in property values.

Supports two syntaxes:
- Legacy: {{variable_name}} - Simple variable substitution
- New: @{expression} - Full expression evaluation (Power Automate style)

Security Note:
    This evaluator does NOT use eval() or exec(). All expression parsing
    is done through safe regex-based tokenization and explicit function dispatch.
"""

import json
import re
import threading
from collections.abc import Callable
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

from loguru import logger


class ExpressionError(Exception):
    """Raised when expression evaluation fails."""

    def __init__(self, message: str, expression: str | None = None):
        self.expression = expression
        super().__init__(f"{message}" + (f" in expression: {expression}" if expression else ""))


class ExpressionEvaluator:
    """
    Evaluates runtime expressions in property values.

    Thread-safe singleton pattern for consistent function registry across the application.

    Built-in functions:
    - String: concat, upper, lower, trim, split, join, replace, substring, startswith, endswith
    - Logic: if, coalesce, equals, not, and, or, gt, lt, gte, lte
    - Type: int, float, string, len, bool, type
    - Date: now, today, format_date, add_days, parse_date
    - JSON: json, parse_json
    - Collection: first, last, contains, length, range, slice
    - Math: abs, min, max, round, sum

    Examples:
        >>> evaluator = ExpressionEvaluator()
        >>> evaluator.evaluate("@{concat(upper(name), '!')}", {"name": "world"})
        'WORLD!'
        >>> evaluator.evaluate("Hello {{name}}", {"name": "World"})
        'Hello World'
        >>> evaluator.evaluate("@{if(gt(count, 10), 'many', 'few')}", {"count": 15})
        'many'
    """

    # Regex patterns for expression detection
    LEGACY_VAR_PATTERN = re.compile(
        r"\{\{\s*(\$?[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*|\[\d+\])*)\s*\}\}"
    )
    NEW_EXPR_PATTERN = re.compile(r"@\{([^}]+)\}")

    # Pattern for function call detection
    FUNCTION_CALL_PATTERN = re.compile(r"^(\w+)\((.*)\)$", re.DOTALL)

    # Pattern for variable reference
    VARIABLE_REF_PATTERN = re.compile(r"^\w+(?:\.\w+|\[\d+\])*$")

    def __init__(self) -> None:
        """Initialize the expression evaluator with built-in functions."""
        self._lock = threading.Lock()
        self._functions: dict[str, Callable[..., Any]] = self._build_function_registry()

    def _build_function_registry(self) -> dict[str, Callable[..., Any]]:
        """Build the registry of built-in functions."""
        return {
            # String functions
            "concat": lambda *args: "".join(str(a) for a in args),
            "upper": lambda s: str(s).upper(),
            "lower": lambda s: str(s).lower(),
            "trim": lambda s: str(s).strip(),
            "split": lambda s, d=",": str(s).split(d),
            "join": lambda lst, d=",": d.join(str(x) for x in lst) if lst else "",
            "replace": lambda s, old, new: str(s).replace(old, new),
            "substring": self._safe_substring,
            "startswith": lambda s, prefix: str(s).startswith(str(prefix)),
            "endswith": lambda s, suffix: str(s).endswith(str(suffix)),
            # Logic functions
            "if": lambda cond, then, else_=None: then if cond else else_,
            "coalesce": lambda *args: next((a for a in args if a is not None), None),
            "equals": lambda a, b: a == b,
            "not": lambda x: not x,
            "and": lambda *args: all(args),
            "or": lambda *args: any(args),
            "gt": lambda a, b: a > b,
            "lt": lambda a, b: a < b,
            "gte": lambda a, b: a >= b,
            "lte": lambda a, b: a <= b,
            # Type conversion
            "int": self._safe_int,
            "float": self._safe_float,
            "string": lambda x: str(x) if x is not None else "",
            "bool": lambda x: bool(x),
            "len": lambda x: len(x) if x is not None else 0,
            "length": lambda x: len(x) if x is not None else 0,
            "type": lambda x: type(x).__name__,
            # Date functions
            "now": datetime.now,
            "today": date.today,
            "format_date": self._format_date,
            "add_days": self._add_days,
            "parse_date": self._parse_date,
            # JSON functions
            "json": lambda x: json.dumps(x, default=str, ensure_ascii=False),
            "parse_json": self._safe_parse_json,
            # Collection functions
            "first": lambda lst: lst[0] if lst else None,
            "last": lambda lst: lst[-1] if lst else None,
            "contains": lambda lst, item: item in lst if lst else False,
            "range": lambda *args: list(range(*args)),
            "slice": lambda lst, start, end=None: lst[start:end] if lst else [],
            # Math functions
            "abs": lambda x: abs(x) if x is not None else 0,
            "min": lambda *args: min(args) if args else None,
            "max": lambda *args: max(args) if args else None,
            "round": lambda x, n=0: round(x, n) if x is not None else 0,
            "sum": lambda lst: sum(lst) if lst else 0,
        }

    @staticmethod
    def _safe_substring(s: str, start: int, end: int | None = None) -> str:
        """Safe substring extraction with bounds checking."""
        s = str(s)
        if end is None:
            return s[start:]
        return s[start:end]

    @staticmethod
    def _safe_int(x: Any) -> int:
        """Safe integer conversion."""
        if x is None:
            return 0
        if isinstance(x, bool):
            return 1 if x else 0
        try:
            return int(x)
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _safe_float(x: Any) -> float:
        """Safe float conversion."""
        if x is None:
            return 0.0
        if isinstance(x, bool):
            return 1.0 if x else 0.0
        try:
            return float(x)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _format_date(dt: datetime | date | str, fmt: str = "%Y-%m-%d") -> str:
        """Format a date/datetime object or ISO string."""
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt)
            except ValueError:
                return dt
        return dt.strftime(fmt)

    @staticmethod
    def _add_days(dt: datetime | date | str, days: int) -> datetime | date:
        """Add days to a date/datetime."""
        from datetime import timedelta

        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)
        return dt + timedelta(days=days)

    @staticmethod
    def _parse_date(s: str, fmt: str | None = None) -> datetime:
        """Parse a date string into datetime."""
        if fmt:
            return datetime.strptime(s, fmt)
        return datetime.fromisoformat(s)

    @staticmethod
    def _safe_parse_json(s: Any) -> Any:
        """Safe JSON parsing."""
        if not isinstance(s, str):
            return s
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return s

    def evaluate(self, expression: str, variables: dict[str, Any]) -> Any:
        """
        Evaluate an expression string.

        Supports both legacy {{variable}} and new @{expression} syntax.
        Non-string values are returned unchanged.

        Args:
            expression: Expression like "@{concat(a, b)}" or "{{var}}" or plain text
            variables: Variable context for resolution

        Returns:
            Evaluated result. Type preservation:
            - Pure @{expr} returns the expression result type
            - Pure {{var}} returns the variable's original type
            - Mixed content returns string

        Raises:
            ExpressionError: When expression evaluation fails critically
        """
        if not isinstance(expression, str):
            return expression

        # Fast path: no expressions to evaluate
        if "@{" not in expression and "{{" not in expression:
            return expression

        # Pure @{expression} - evaluate and return typed result
        if expression.startswith("@{") and expression.endswith("}") and expression.count("@{") == 1:
            inner = expression[2:-1]
            try:
                return self._evaluate_expression(inner, variables)
            except Exception as e:
                logger.warning(f"Expression evaluation failed: {e}")
                raise ExpressionError(str(e), expression) from e

        # Mixed content processing
        result = expression

        # Handle @{} expressions in mixed content
        def replace_new_expr(match: re.Match) -> str:
            try:
                val = self._evaluate_expression(match.group(1), variables)
                return str(val) if val is not None else ""
            except Exception as e:
                logger.warning(f"Expression error in '{match.group(0)}': {e}")
                return match.group(0)

        result = self.NEW_EXPR_PATTERN.sub(replace_new_expr, result)

        # Handle legacy {{variable}} syntax
        def replace_legacy_var(match: re.Match) -> str:
            var_path = match.group(1)
            try:
                # Check system variables first
                if var_path.startswith("$"):
                    val = self._resolve_system_variable(var_path)
                else:
                    val = self._resolve_variable_path(var_path, variables)
                return str(val) if val is not None else ""
            except Exception:
                return match.group(0)

        result = self.LEGACY_VAR_PATTERN.sub(replace_legacy_var, result)

        return result

    def _resolve_system_variable(self, name: str) -> Any:
        """Resolve built-in system variables that start with $."""
        now = datetime.now()
        system_vars = {
            "$currentDate": now.strftime("%Y-%m-%d"),
            "$currentTime": now.strftime("%H:%M:%S"),
            "$currentDateTime": now.isoformat(),
            "$timestamp": int(now.timestamp()),
        }
        return system_vars.get(name)

    def _resolve_variable_path(self, path: str, variables: dict[str, Any]) -> Any:
        """
        Resolve a dotted variable path like 'user.name' or 'items[0].value'.

        Args:
            path: Variable path (e.g., "user", "user.name", "items[0]")
            variables: Variable context

        Returns:
            Resolved value or None if not found
        """
        if not path:
            return None

        # Handle array index access
        parts = []
        current = ""
        i = 0
        while i < len(path):
            char = path[i]
            if char == ".":
                if current:
                    parts.append(("key", current))
                    current = ""
            elif char == "[":
                if current:
                    parts.append(("key", current))
                    current = ""
                # Find closing bracket
                j = i + 1
                while j < len(path) and path[j] != "]":
                    j += 1
                if j < len(path):
                    index_str = path[i + 1 : j]
                    try:
                        parts.append(("index", int(index_str)))
                    except ValueError:
                        parts.append(("key", index_str))
                    i = j
            else:
                current += char
            i += 1

        if current:
            parts.append(("key", current))

        if not parts:
            return None

        # Navigate the path
        first_type, first_key = parts[0]
        if first_type == "key":
            value = variables.get(first_key)
        else:
            return None  # Can't start with index

        for part_type, part_key in parts[1:]:
            if value is None:
                return None
            if part_type == "key":
                if isinstance(value, dict):
                    value = value.get(part_key)
                elif hasattr(value, part_key):
                    value = getattr(value, part_key)
                else:
                    return None
            elif part_type == "index":
                if isinstance(value, (list, tuple)) and 0 <= part_key < len(value):
                    value = value[part_key]
                else:
                    return None

        return value

    def _evaluate_expression(self, expr: str, variables: dict[str, Any]) -> Any:
        """
        Evaluate a single expression (without @{} wrapper).

        Args:
            expr: Expression string like "concat(a, b)" or "variable.path"
            variables: Variable context

        Returns:
            Evaluated result
        """
        expr = expr.strip()

        if not expr:
            return None

        # Check if it's a function call
        func_match = self.FUNCTION_CALL_PATTERN.match(expr)
        if func_match:
            func_name = func_match.group(1)
            args_str = func_match.group(2)
            return self._call_function(func_name, args_str, variables)

        # Check if it's a variable reference
        if self.VARIABLE_REF_PATTERN.match(expr):
            # Check system variables first
            if expr.startswith("$"):
                result = self._resolve_system_variable(expr)
                if result is not None:
                    return result
            return self._resolve_variable_path(expr, variables)

        # Try to evaluate as literal
        return self._parse_literal(expr)

    def _call_function(self, name: str, args_str: str, variables: dict[str, Any]) -> Any:
        """
        Call a built-in function with parsed arguments.

        Args:
            name: Function name
            args_str: Raw argument string
            variables: Variable context

        Returns:
            Function result

        Raises:
            ExpressionError: If function is unknown or call fails
        """
        if name not in self._functions:
            raise ExpressionError(f"Unknown function: {name}")

        args = self._parse_arguments(args_str, variables)
        try:
            return self._functions[name](*args)
        except TypeError as e:
            raise ExpressionError(f"Invalid arguments for {name}: {e}") from e
        except Exception as e:
            raise ExpressionError(f"Error calling {name}: {e}") from e

    def _parse_arguments(self, args_str: str, variables: dict[str, Any]) -> list[Any]:
        """
        Parse function arguments string into list of evaluated values.

        Handles nested function calls, string literals, and variable references.

        Args:
            args_str: Raw argument string like "a, 'hello', concat(b, c)"
            variables: Variable context

        Returns:
            List of evaluated argument values
        """
        if not args_str.strip():
            return []

        args = []
        current = ""
        depth = 0
        in_string = False
        string_char: str | None = None
        escape_next = False

        for char in args_str:
            if escape_next:
                current += char
                escape_next = False
                continue

            if char == "\\" and in_string:
                escape_next = True
                current += char
                continue

            if char in ('"', "'") and not in_string:
                in_string = True
                string_char = char
                current += char
            elif char == string_char and in_string:
                in_string = False
                string_char = None
                current += char
            elif char == "(" and not in_string:
                depth += 1
                current += char
            elif char == ")" and not in_string:
                depth -= 1
                current += char
            elif char == "," and depth == 0 and not in_string:
                args.append(self._evaluate_argument(current.strip(), variables))
                current = ""
            else:
                current += char

        if current.strip():
            args.append(self._evaluate_argument(current.strip(), variables))

        return args

    def _evaluate_argument(self, arg: str, variables: dict[str, Any]) -> Any:
        """
        Evaluate a single argument value.

        Args:
            arg: Argument string (function call, literal, or variable reference)
            variables: Variable context

        Returns:
            Evaluated argument value
        """
        arg = arg.strip()

        if not arg:
            return None

        # Nested function call
        if self.FUNCTION_CALL_PATTERN.match(arg):
            return self._evaluate_expression(arg, variables)

        # String literal (double or single quotes)
        if (arg.startswith('"') and arg.endswith('"')) or (
            arg.startswith("'") and arg.endswith("'")
        ):
            # Handle escape sequences
            inner = arg[1:-1]
            return inner.replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")

        # Boolean literals
        if arg.lower() == "true":
            return True
        if arg.lower() == "false":
            return False
        if arg.lower() in ("null", "none"):
            return None

        # Number literals
        try:
            if "." in arg:
                return float(arg)
            return int(arg)
        except ValueError:
            pass

        # Variable reference (including system variables)
        if arg.startswith("$"):
            result = self._resolve_system_variable(arg)
            if result is not None:
                return result
        return self._resolve_variable_path(arg, variables)

    def _parse_literal(self, expr: str) -> Any:
        """
        Parse a literal value from expression string.

        Args:
            expr: Expression that might be a literal value

        Returns:
            Parsed literal or original string
        """
        expr = expr.strip()

        if expr.lower() == "true":
            return True
        if expr.lower() == "false":
            return False
        if expr.lower() in ("null", "none"):
            return None

        try:
            if "." in expr:
                return float(expr)
            return int(expr)
        except ValueError:
            pass

        if (expr.startswith('"') and expr.endswith('"')) or (
            expr.startswith("'") and expr.endswith("'")
        ):
            return expr[1:-1]

        return expr

    def register_function(self, name: str, func: Callable[..., Any]) -> None:
        """
        Register a custom function for use in expressions.

        Thread-safe function registration.

        Args:
            name: Function name (must be valid identifier)
            func: Callable to invoke when function is called

        Raises:
            ValueError: If name is not a valid identifier
        """
        if not name.isidentifier():
            raise ValueError(f"Invalid function name: {name}")

        with self._lock:
            self._functions[name] = func
        logger.debug(f"Registered expression function: {name}")

    def unregister_function(self, name: str) -> bool:
        """
        Unregister a custom function.

        Args:
            name: Function name to remove

        Returns:
            True if function was removed, False if not found
        """
        with self._lock:
            if name in self._functions:
                del self._functions[name]
                logger.debug(f"Unregistered expression function: {name}")
                return True
        return False

    def has_expressions(self, value: str) -> bool:
        """
        Check if a string contains any expression syntax.

        Args:
            value: String to check

        Returns:
            True if string contains @{} or {{}} expressions
        """
        if not isinstance(value, str):
            return False
        return bool(self.LEGACY_VAR_PATTERN.search(value) or self.NEW_EXPR_PATTERN.search(value))

    def list_functions(self) -> list[str]:
        """
        Get list of all available function names.

        Returns:
            Sorted list of function names
        """
        with self._lock:
            return sorted(self._functions.keys())


# Thread-safe singleton implementation
_evaluator_lock = threading.Lock()
_default_evaluator: ExpressionEvaluator | None = None


def get_expression_evaluator() -> ExpressionEvaluator:
    """
    Get the default expression evaluator singleton instance.

    Thread-safe lazy initialization.

    Returns:
        The shared ExpressionEvaluator instance
    """
    global _default_evaluator
    if _default_evaluator is None:
        with _evaluator_lock:
            # Double-check locking
            if _default_evaluator is None:
                _default_evaluator = ExpressionEvaluator()
    return _default_evaluator


def evaluate_expression(expression: str, variables: dict[str, Any]) -> Any:
    """
    Convenience function to evaluate an expression using the default evaluator.

    Args:
        expression: Expression string to evaluate
        variables: Variable context for resolution

    Returns:
        Evaluated result
    """
    return get_expression_evaluator().evaluate(expression, variables)


def has_expressions(value: str) -> bool:
    """
    Check if a string contains any expression syntax.

    Args:
        value: String to check

    Returns:
        True if string contains @{} or {{}} expressions
    """
    return get_expression_evaluator().has_expressions(value)
