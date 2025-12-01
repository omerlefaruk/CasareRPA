"""Tests for safe_eval module."""

import pytest
from casare_rpa.utils.security.safe_eval import (
    safe_eval,
    SafeExpressionEvaluator,
    is_safe_expression,
    SAFE_FUNCTIONS,
)


class TestSafeEval:
    """Tests for safe_eval function."""

    def test_arithmetic_operations(self):
        """Test basic arithmetic expressions."""
        assert safe_eval("2 + 2") == 4
        assert safe_eval("10 - 3") == 7
        assert safe_eval("5 * 4") == 20
        assert safe_eval("20 / 4") == 5.0
        assert safe_eval("17 // 3") == 5
        assert safe_eval("17 % 3") == 2
        assert safe_eval("2 ** 8") == 256

    def test_comparison_operations(self):
        """Test comparison expressions."""
        assert safe_eval("5 > 3") is True
        assert safe_eval("3 < 2") is False
        assert safe_eval("5 >= 5") is True
        assert safe_eval("4 <= 3") is False
        assert safe_eval("10 == 10") is True
        assert safe_eval("5 != 3") is True

    def test_logical_operations(self):
        """Test logical operators."""
        assert safe_eval("True and True") is True
        assert safe_eval("True and False") is False
        assert safe_eval("False or True") is True
        assert safe_eval("not False") is True

    def test_variable_resolution(self):
        """Test variable substitution in expressions."""
        assert safe_eval("x + y", {"x": 10, "y": 5}) == 15
        assert safe_eval("x > 5", {"x": 10}) is True
        assert safe_eval("name == 'test'", {"name": "test"}) is True

    def test_safe_functions(self):
        """Test allowed built-in functions with variables."""
        # Functions work with variable substitution
        assert safe_eval("len(items)", {"items": [1, 2, 3]}) == 3
        assert safe_eval("abs(x)", {"x": -5}) == 5
        assert safe_eval("min(a, b, c)", {"a": 3, "b": 1, "c": 4}) == 1
        assert safe_eval("max(a, b, c)", {"a": 3, "b": 1, "c": 4}) == 4
        assert safe_eval("sum(items)", {"items": [1, 2, 3, 4]}) == 10
        assert safe_eval("round(x)", {"x": 3.7}) == 4
        assert safe_eval("bool(x)", {"x": 1}) is True
        assert safe_eval("bool(x)", {"x": 0}) is False

    def test_list_and_membership(self):
        """Test list operations and membership tests."""
        assert safe_eval("len(items) > 0", {"items": [1, 2, 3]}) is True
        assert safe_eval("3 in items", {"items": [1, 2, 3]}) is True
        assert safe_eval("5 not in items", {"items": [1, 2, 3]}) is True

    def test_literal_values(self):
        """Test literal value parsing."""
        assert safe_eval("42") == 42
        assert safe_eval("3.14") == 3.14
        assert safe_eval("'hello'") == "hello"
        assert safe_eval("[1, 2, 3]") == [1, 2, 3]
        assert safe_eval("{'a': 1}") == {"a": 1}

    def test_empty_expression(self):
        """Test empty or whitespace-only expressions."""
        assert safe_eval("") is None
        assert safe_eval("   ") is None

    def test_complex_expressions(self):
        """Test more complex expressions."""
        assert safe_eval("(x + y) * 2", {"x": 3, "y": 4}) == 14
        assert safe_eval("x if x > 0 else -x", {"x": -5}) == 5
        assert (
            safe_eval("len(items) > 0 and items[0] == 1", {"items": [1, 2, 3]}) is True
        )

    def test_invalid_expression_raises(self):
        """Test that invalid expressions raise ValueError."""
        with pytest.raises(ValueError):
            safe_eval("undefined_variable")

    def test_dangerous_operations_blocked(self):
        """Test that dangerous operations are blocked."""
        with pytest.raises(ValueError):
            safe_eval("__import__('os')")

        with pytest.raises(ValueError):
            safe_eval("open('file.txt')")


class TestSafeExpressionEvaluator:
    """Tests for SafeExpressionEvaluator class."""

    def test_basic_evaluation(self):
        """Test basic expression evaluation."""
        evaluator = SafeExpressionEvaluator()
        assert evaluator.evaluate("2 + 2") == 4

    def test_with_initial_variables(self):
        """Test evaluator with initial variables."""
        evaluator = SafeExpressionEvaluator({"x": 10, "y": 20})
        assert evaluator.evaluate("x + y") == 30

    def test_update_variables(self):
        """Test updating variables."""
        evaluator = SafeExpressionEvaluator({"x": 10})
        assert evaluator.evaluate("x") == 10

        evaluator.update_variables({"y": 5})
        assert evaluator.evaluate("x + y") == 15

    def test_variable_override(self):
        """Test overriding existing variables."""
        evaluator = SafeExpressionEvaluator({"x": 10})
        assert evaluator.evaluate("x") == 10

        evaluator.update_variables({"x": 20})
        assert evaluator.evaluate("x") == 20


class TestIsSafeExpression:
    """Tests for is_safe_expression function."""

    def test_safe_expressions(self):
        """Test that safe expressions return True."""
        assert is_safe_expression("2 + 2") is True
        assert is_safe_expression("x > 5") is True
        assert is_safe_expression("len(items) > 0") is True
        assert is_safe_expression("name == 'test'") is True

    def test_dangerous_patterns_detected(self):
        """Test that dangerous patterns are detected."""
        assert is_safe_expression("__import__('os')") is False
        assert is_safe_expression("exec('print(1)')") is False
        assert is_safe_expression("eval('2+2')") is False
        assert is_safe_expression("open('file.txt')") is False
        assert is_safe_expression("globals()") is False
        assert is_safe_expression("locals()") is False
        assert is_safe_expression("getattr(x, 'y')") is False
        assert is_safe_expression("setattr(x, 'y', 1)") is False
        assert is_safe_expression("lambda x: x") is False
        assert is_safe_expression("def foo(): pass") is False
        assert is_safe_expression("class Foo: pass") is False

    def test_dunder_methods_blocked(self):
        """Test that dunder methods are blocked."""
        assert is_safe_expression("x.__class__") is False
        assert is_safe_expression("x.__dict__") is False
        assert is_safe_expression("x.__module__") is False

    def test_empty_expression(self):
        """Test empty expressions return False."""
        assert is_safe_expression("") is False
        assert is_safe_expression(None) is False

    def test_case_insensitive_detection(self):
        """Test that pattern detection is case insensitive."""
        assert is_safe_expression("IMPORT os") is False
        assert is_safe_expression("Exec('code')") is False
        assert is_safe_expression("EVAL('x')") is False


class TestSafeFunctions:
    """Tests for the SAFE_FUNCTIONS dict."""

    def test_all_safe_functions_available(self):
        """Test that expected safe functions are available."""
        expected_functions = {
            "len",
            "bool",
            "abs",
            "min",
            "max",
            "sum",
            "round",
            "sorted",
            "list",
            "tuple",
            "range",
            "any",
            "all",
        }
        for func_name in expected_functions:
            assert (
                func_name in SAFE_FUNCTIONS
            ), f"{func_name} should be in SAFE_FUNCTIONS"

    def test_safe_functions_work_in_eval(self):
        """Test that safe functions work in expressions with variables."""
        assert safe_eval("any(items)", {"items": [False, True, False]}) is True
        assert safe_eval("all(items)", {"items": [True, True, True]}) is True
        assert safe_eval("sorted(items)", {"items": [3, 1, 2]}) == [1, 2, 3]
        assert safe_eval("list(items)", {"items": range(3)}) == [0, 1, 2]
        assert safe_eval("tuple(items)", {"items": [1, 2, 3]}) == (1, 2, 3)
