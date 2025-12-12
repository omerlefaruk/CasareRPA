"""
CasareRPA - Workflow Assertion Helpers.

Provides static assertion methods for workflow testing.
Can be used standalone or with WorkflowTestCase.

Usage:
    # Standalone
    WorkflowAssertions.assert_variable_contains(context, 'result', 'success')
    WorkflowAssertions.assert_variable_matches(context, 'email', r'.+@.+\..+')
    WorkflowAssertions.assert_list_length(context, 'items', 5)

    # With context from test
    @pytest.mark.asyncio
    async def test_workflow(execution_context):
        await execute_workflow(workflow, execution_context)
        WorkflowAssertions.assert_variable_equals(execution_context, 'status', 'done')
"""

import re
from typing import Any, Callable, Dict, List, Optional, Sequence, Type


class WorkflowAssertions:
    """
    Static assertion methods for workflow testing.

    All methods raise AssertionError with descriptive messages on failure.
    Methods are designed for use with ExecutionContext or any object
    with variables dict/get_variable method.
    """

    # =========================================================================
    # Variable Assertions
    # =========================================================================

    @staticmethod
    def assert_variable_equals(context: Any, name: str, expected: Any) -> None:
        """
        Assert that a variable equals the expected value.

        Args:
            context: ExecutionContext or object with variables
            name: Variable name
            expected: Expected value

        Raises:
            AssertionError: If variable doesn't equal expected
        """
        actual = WorkflowAssertions._get_variable(context, name)
        assert (
            actual == expected
        ), f"Variable '{name}' expected {expected!r}, got {actual!r}"

    @staticmethod
    def assert_variable_not_equals(context: Any, name: str, unexpected: Any) -> None:
        """
        Assert that a variable does NOT equal a value.

        Args:
            context: ExecutionContext or object with variables
            name: Variable name
            unexpected: Value that should not match

        Raises:
            AssertionError: If variable equals unexpected
        """
        actual = WorkflowAssertions._get_variable(context, name)
        assert (
            actual != unexpected
        ), f"Variable '{name}' should not equal {unexpected!r}"

    @staticmethod
    def assert_variable_contains(context: Any, name: str, substring: str) -> None:
        """
        Assert that a variable contains a substring.

        Works with strings and lists.

        Args:
            context: ExecutionContext or object with variables
            name: Variable name
            substring: Substring or item to find

        Raises:
            AssertionError: If variable doesn't contain substring
        """
        value = WorkflowAssertions._get_variable(context, name)
        if isinstance(value, str):
            assert (
                substring in value
            ), f"Variable '{name}' does not contain '{substring}'"
        elif isinstance(value, (list, tuple)):
            assert (
                substring in value
            ), f"Variable '{name}' list does not contain '{substring}'"
        else:
            assert substring in str(value), (
                f"Variable '{name}' ({type(value).__name__}) "
                f"does not contain '{substring}'"
            )

    @staticmethod
    def assert_variable_not_contains(context: Any, name: str, substring: str) -> None:
        """
        Assert that a variable does NOT contain a substring.

        Args:
            context: ExecutionContext or object with variables
            name: Variable name
            substring: Substring or item that should not be present

        Raises:
            AssertionError: If variable contains substring
        """
        value = WorkflowAssertions._get_variable(context, name)
        if isinstance(value, str):
            assert (
                substring not in value
            ), f"Variable '{name}' should not contain '{substring}'"
        elif isinstance(value, (list, tuple)):
            assert (
                substring not in value
            ), f"Variable '{name}' list should not contain '{substring}'"
        else:
            assert substring not in str(
                value
            ), f"Variable '{name}' should not contain '{substring}'"

    @staticmethod
    def assert_variable_matches(context: Any, name: str, pattern: str) -> None:
        """
        Assert that a variable matches a regex pattern.

        Args:
            context: ExecutionContext or object with variables
            name: Variable name
            pattern: Regex pattern to match

        Raises:
            AssertionError: If variable doesn't match pattern
        """
        value = str(WorkflowAssertions._get_variable(context, name) or "")
        assert re.match(
            pattern, value
        ), f"Variable '{name}' ({value!r}) does not match pattern '{pattern}'"

    @staticmethod
    def assert_variable_type(context: Any, name: str, expected_type: Type) -> None:
        """
        Assert that a variable has the expected type.

        Args:
            context: ExecutionContext or object with variables
            name: Variable name
            expected_type: Expected Python type

        Raises:
            AssertionError: If variable type doesn't match
        """
        value = WorkflowAssertions._get_variable(context, name)
        assert isinstance(value, expected_type), (
            f"Variable '{name}' expected type {expected_type.__name__}, "
            f"got {type(value).__name__}"
        )

    @staticmethod
    def assert_variable_exists(context: Any, name: str) -> None:
        """
        Assert that a variable exists (is not None).

        Args:
            context: ExecutionContext or object with variables
            name: Variable name

        Raises:
            AssertionError: If variable doesn't exist
        """
        variables = WorkflowAssertions._get_variables(context)
        assert (
            name in variables
        ), f"Variable '{name}' not found. Available: {list(variables.keys())}"

    @staticmethod
    def assert_variable_not_exists(context: Any, name: str) -> None:
        """
        Assert that a variable does NOT exist.

        Args:
            context: ExecutionContext or object with variables
            name: Variable name

        Raises:
            AssertionError: If variable exists
        """
        variables = WorkflowAssertions._get_variables(context)
        assert name not in variables, f"Variable '{name}' exists but should not"

    # =========================================================================
    # Numeric Assertions
    # =========================================================================

    @staticmethod
    def assert_variable_greater_than(context: Any, name: str, threshold: float) -> None:
        """
        Assert that a numeric variable is greater than threshold.

        Args:
            context: ExecutionContext or object with variables
            name: Variable name
            threshold: Minimum value (exclusive)

        Raises:
            AssertionError: If variable is not greater than threshold
        """
        value = WorkflowAssertions._get_variable(context, name)
        assert (
            value > threshold
        ), f"Variable '{name}' ({value}) is not greater than {threshold}"

    @staticmethod
    def assert_variable_less_than(context: Any, name: str, threshold: float) -> None:
        """
        Assert that a numeric variable is less than threshold.

        Args:
            context: ExecutionContext or object with variables
            name: Variable name
            threshold: Maximum value (exclusive)

        Raises:
            AssertionError: If variable is not less than threshold
        """
        value = WorkflowAssertions._get_variable(context, name)
        assert (
            value < threshold
        ), f"Variable '{name}' ({value}) is not less than {threshold}"

    @staticmethod
    def assert_variable_in_range(
        context: Any, name: str, min_val: float, max_val: float
    ) -> None:
        """
        Assert that a numeric variable is within a range (inclusive).

        Args:
            context: ExecutionContext or object with variables
            name: Variable name
            min_val: Minimum value (inclusive)
            max_val: Maximum value (inclusive)

        Raises:
            AssertionError: If variable is outside range
        """
        value = WorkflowAssertions._get_variable(context, name)
        assert (
            min_val <= value <= max_val
        ), f"Variable '{name}' ({value}) is not in range [{min_val}, {max_val}]"

    # =========================================================================
    # Collection Assertions
    # =========================================================================

    @staticmethod
    def assert_list_length(context: Any, name: str, expected_length: int) -> None:
        """
        Assert that a list variable has expected length.

        Args:
            context: ExecutionContext or object with variables
            name: Variable name
            expected_length: Expected list length

        Raises:
            AssertionError: If list length doesn't match
        """
        value = WorkflowAssertions._get_variable(context, name)
        assert isinstance(
            value, (list, tuple)
        ), f"Variable '{name}' is not a list/tuple"
        assert (
            len(value) == expected_length
        ), f"Variable '{name}' has length {len(value)}, expected {expected_length}"

    @staticmethod
    def assert_list_not_empty(context: Any, name: str) -> None:
        """
        Assert that a list variable is not empty.

        Args:
            context: ExecutionContext or object with variables
            name: Variable name

        Raises:
            AssertionError: If list is empty
        """
        value = WorkflowAssertions._get_variable(context, name)
        assert isinstance(
            value, (list, tuple)
        ), f"Variable '{name}' is not a list/tuple"
        assert len(value) > 0, f"Variable '{name}' is empty"

    @staticmethod
    def assert_list_empty(context: Any, name: str) -> None:
        """
        Assert that a list variable is empty.

        Args:
            context: ExecutionContext or object with variables
            name: Variable name

        Raises:
            AssertionError: If list is not empty
        """
        value = WorkflowAssertions._get_variable(context, name)
        assert isinstance(
            value, (list, tuple)
        ), f"Variable '{name}' is not a list/tuple"
        assert (
            len(value) == 0
        ), f"Variable '{name}' is not empty (has {len(value)} items)"

    @staticmethod
    def assert_dict_has_key(context: Any, name: str, key: str) -> None:
        """
        Assert that a dict variable has a specific key.

        Args:
            context: ExecutionContext or object with variables
            name: Variable name
            key: Expected key

        Raises:
            AssertionError: If dict doesn't have key
        """
        value = WorkflowAssertions._get_variable(context, name)
        assert isinstance(value, dict), f"Variable '{name}' is not a dict"
        assert key in value, (
            f"Variable '{name}' does not have key '{key}'. "
            f"Keys: {list(value.keys())}"
        )

    @staticmethod
    def assert_dict_has_keys(context: Any, name: str, keys: Sequence[str]) -> None:
        """
        Assert that a dict variable has all specified keys.

        Args:
            context: ExecutionContext or object with variables
            name: Variable name
            keys: Expected keys

        Raises:
            AssertionError: If dict is missing any key
        """
        value = WorkflowAssertions._get_variable(context, name)
        assert isinstance(value, dict), f"Variable '{name}' is not a dict"
        missing = [k for k in keys if k not in value]
        assert not missing, (
            f"Variable '{name}' missing keys: {missing}. "
            f"Available: {list(value.keys())}"
        )

    # =========================================================================
    # Boolean Assertions
    # =========================================================================

    @staticmethod
    def assert_variable_true(context: Any, name: str) -> None:
        """
        Assert that a variable is truthy.

        Args:
            context: ExecutionContext or object with variables
            name: Variable name

        Raises:
            AssertionError: If variable is falsy
        """
        value = WorkflowAssertions._get_variable(context, name)
        assert value, f"Variable '{name}' is not truthy: {value!r}"

    @staticmethod
    def assert_variable_false(context: Any, name: str) -> None:
        """
        Assert that a variable is falsy.

        Args:
            context: ExecutionContext or object with variables
            name: Variable name

        Raises:
            AssertionError: If variable is truthy
        """
        value = WorkflowAssertions._get_variable(context, name)
        assert not value, f"Variable '{name}' is not falsy: {value!r}"

    @staticmethod
    def assert_variable_is_none(context: Any, name: str) -> None:
        """
        Assert that a variable is None.

        Args:
            context: ExecutionContext or object with variables
            name: Variable name

        Raises:
            AssertionError: If variable is not None
        """
        value = WorkflowAssertions._get_variable(context, name)
        assert value is None, f"Variable '{name}' is not None: {value!r}"

    @staticmethod
    def assert_variable_is_not_none(context: Any, name: str) -> None:
        """
        Assert that a variable is not None.

        Args:
            context: ExecutionContext or object with variables
            name: Variable name

        Raises:
            AssertionError: If variable is None
        """
        value = WorkflowAssertions._get_variable(context, name)
        assert value is not None, f"Variable '{name}' is None"

    # =========================================================================
    # Custom Assertions
    # =========================================================================

    @staticmethod
    def assert_custom(
        context: Any,
        name: str,
        predicate: Callable[[Any], bool],
        message: str = "Custom assertion failed",
    ) -> None:
        """
        Assert using a custom predicate function.

        Args:
            context: ExecutionContext or object with variables
            name: Variable name
            predicate: Function that takes value and returns bool
            message: Error message on failure

        Raises:
            AssertionError: If predicate returns False
        """
        value = WorkflowAssertions._get_variable(context, name)
        assert predicate(value), f"{message}: variable '{name}' = {value!r}"

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    @staticmethod
    def _get_variables(context: Any) -> Dict[str, Any]:
        """Get variables dict from context."""
        if hasattr(context, "variables"):
            return context.variables
        elif isinstance(context, dict):
            return context
        else:
            raise TypeError(f"Cannot get variables from {type(context)}")

    @staticmethod
    def _get_variable(context: Any, name: str, default: Any = None) -> Any:
        """Get a variable from context."""
        if hasattr(context, "get_variable"):
            return context.get_variable(name, default)
        elif hasattr(context, "variables"):
            return context.variables.get(name, default)
        elif isinstance(context, dict):
            return context.get(name, default)
        else:
            raise TypeError(f"Cannot get variable from {type(context)}")
