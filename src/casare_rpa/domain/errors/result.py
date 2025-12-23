"""
CasareRPA - Result Type System

Rust-inspired Result<T, E> pattern for explicit error handling.
Replaces silent None returns with typed success/error wrappers.

Usage:
    from casare_rpa.domain.errors.result import Result, Ok, Err

    def get_element(selector: str) -> Result[Element, NodeExecutionError]:
        try:
            element = page.query_selector(selector)
            if element is None:
                return Err(NodeExecutionError("Element not found"))
            return Ok(element)
        except Exception as e:
            return Err(NodeExecutionError(str(e), original_error=e))

    # Caller handles result explicitly:
    result = get_element(".button")
    if result.is_ok():
        element = result.unwrap()
    else:
        error = result.error  # Access error details

Design Pattern: Railway-Oriented Programming
- Ok track: Success path with value transformation via map()
- Err track: Error path with context preservation
- Forces explicit handling at call sites (no silent failures)
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    NoReturn,
    TypeVar,
    Union,
)

if TYPE_CHECKING:
    pass

# Type variables for generic Result
T = TypeVar("T")  # Success value type
U = TypeVar("U")  # Transformed value type
E = TypeVar("E", bound=Exception)  # Error type (must be Exception subclass)
F = TypeVar("F", bound=Exception)  # Transformed error type


@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    """
    Success result wrapper.

    Wraps a successful computation result with the value.
    Immutable and hashable for use in sets/dicts.

    Attributes:
        value: The successful result value

    Example:
        result = Ok(42)
        assert result.is_ok()
        assert result.unwrap() == 42
    """

    value: T

    def is_ok(self) -> bool:
        """Check if this is a success result."""
        return True

    def is_err(self) -> bool:
        """Check if this is an error result."""
        return False

    def unwrap(self) -> T:
        """
        Extract the success value.

        Returns:
            The wrapped value

        Note:
            Safe to call on Ok - always returns the value.
        """
        return self.value

    def unwrap_or(self, default: T) -> T:
        """
        Extract value or return default.

        For Ok, always returns the wrapped value (ignores default).

        Args:
            default: Unused for Ok results

        Returns:
            The wrapped value
        """
        return self.value

    def unwrap_or_else(self, fn: Callable[[Any], T]) -> T:
        """
        Extract value or compute from error.

        For Ok, always returns the wrapped value (ignores fn).

        Args:
            fn: Unused for Ok results

        Returns:
            The wrapped value
        """
        return self.value

    def map(self, fn: Callable[[T], U]) -> Result[U, E]:
        """
        Transform the success value.

        Applies fn to the wrapped value if Ok.
        Preserves the Ok wrapper around the transformed value.

        Args:
            fn: Transformation function

        Returns:
            Ok with transformed value

        Example:
            Ok(5).map(lambda x: x * 2)  # Ok(10)
        """
        return Ok(fn(self.value))

    def map_err(self, fn: Callable[[Any], Any]) -> Result[T, E]:
        """
        Transform the error (no-op for Ok).

        Args:
            fn: Unused for Ok results

        Returns:
            Self unchanged
        """
        return self

    def and_then(self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        """
        Chain computations that may fail.

        Applies fn to the value, which returns another Result.
        Used for sequencing operations that each may fail.

        Args:
            fn: Function that takes T and returns Result[U, E]

        Returns:
            The result of applying fn to the value

        Example:
            Ok(5).and_then(lambda x: Ok(x * 2) if x > 0 else Err(...))
        """
        return fn(self.value)

    def or_else(self, fn: Callable[[Any], Result[T, E]]) -> Result[T, E]:
        """
        Provide fallback on error (no-op for Ok).

        Args:
            fn: Unused for Ok results

        Returns:
            Self unchanged
        """
        return self


@dataclass(frozen=True, slots=True)
class Err(Generic[E]):
    """
    Error result wrapper.

    Wraps a failed computation with the error details.
    Immutable and hashable for use in sets/dicts.

    Attributes:
        error: The error that occurred (must be Exception subclass)

    Example:
        result = Err(ValueError("Invalid input"))
        assert result.is_err()
        # result.unwrap()  # Would raise ValueError
    """

    error: E

    def is_ok(self) -> bool:
        """Check if this is a success result."""
        return False

    def is_err(self) -> bool:
        """Check if this is an error result."""
        return True

    def unwrap(self) -> NoReturn:
        """
        Attempt to extract value (always raises for Err).

        Raises:
            The wrapped error

        Note:
            Use is_err() check or unwrap_or() to avoid raising.
        """
        raise self.error

    def unwrap_or(self, default: T) -> T:
        """
        Extract value or return default.

        For Err, always returns the default (error is discarded).

        Args:
            default: Value to return

        Returns:
            The default value
        """
        return default

    def unwrap_or_else(self, fn: Callable[[E], T]) -> T:
        """
        Extract value or compute from error.

        For Err, calls fn with the error to produce a value.

        Args:
            fn: Function that takes error and produces a value

        Returns:
            Result of fn(error)

        Example:
            Err(e).unwrap_or_else(lambda e: f"Failed: {e}")
        """
        return fn(self.error)

    def map(self, fn: Callable[[Any], Any]) -> Result[T, E]:
        """
        Transform success value (no-op for Err).

        Args:
            fn: Unused for Err results

        Returns:
            Self unchanged
        """
        return self  # type: ignore

    def map_err(self, fn: Callable[[E], F]) -> Result[T, F]:
        """
        Transform the error.

        Applies fn to the wrapped error.
        Useful for converting error types between layers.

        Args:
            fn: Transformation function for errors

        Returns:
            Err with transformed error

        Example:
            Err(IOError()).map_err(lambda e: DomainError(str(e)))
        """
        return Err(fn(self.error))

    def and_then(self, fn: Callable[[Any], Result[U, E]]) -> Result[U, E]:
        """
        Chain computations (no-op for Err).

        Args:
            fn: Unused for Err results

        Returns:
            Self unchanged
        """
        return self  # type: ignore

    def or_else(self, fn: Callable[[E], Result[T, F]]) -> Result[T, F]:
        """
        Provide fallback on error.

        Applies fn to the error, which may recover with a new Result.

        Args:
            fn: Recovery function that takes error and returns Result

        Returns:
            Result of fn(error)

        Example:
            Err(e).or_else(lambda e: Ok(default_value))
        """
        return fn(self.error)


# Type alias for Result - union of Ok and Err
# Usage: def func() -> Result[int, ValueError]
Result = Union[Ok[T], Err[E]]


# ============================================================================
# Utility functions for working with Results
# ============================================================================


def is_ok(result: Result[T, E]) -> bool:
    """Check if result is Ok."""
    return result.is_ok()


def is_err(result: Result[T, E]) -> bool:
    """Check if result is Err."""
    return result.is_err()


def unwrap_or_default(result: Result[T, E], default: T) -> T:
    """Unwrap result or return default on error."""
    return result.unwrap_or(default)


def collect_results(results: list[Result[T, E]]) -> Result[list[T], E]:
    """
    Collect a list of Results into a Result of list.

    If all results are Ok, returns Ok with list of values.
    If any result is Err, returns the first Err encountered.

    Args:
        results: List of Result objects

    Returns:
        Ok(list of values) or first Err

    Example:
        collect_results([Ok(1), Ok(2), Ok(3)])  # Ok([1, 2, 3])
        collect_results([Ok(1), Err(e), Ok(3)])  # Err(e)
    """
    values: list[T] = []
    for result in results:
        if result.is_err():
            return result  # type: ignore
        values.append(result.unwrap())
    return Ok(values)
