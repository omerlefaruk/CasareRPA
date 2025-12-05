"""
CasareRPA - E2E Tests for Math Operation Workflows.

Tests mathematical operations including:
- Basic arithmetic (add, subtract, multiply, divide)
- Integer division and modulo
- Power operations
- Rounding operations (round, floor, ceil)
- Absolute value
- Min/max operations
- Aggregations (sum, average)
- Chained calculations
"""

import pytest

from .helpers.workflow_builder import WorkflowBuilder


@pytest.mark.asyncio
@pytest.mark.e2e
class TestBasicArithmetic:
    """Tests for basic arithmetic operations."""

    async def test_math_add(self) -> None:
        """Test addition operation."""
        result = await (
            WorkflowBuilder("Math Add")
            .add_start()
            .add_math_operation("result", a=5, b=3, operation="add")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_math_subtract(self) -> None:
        """Test subtraction operation."""
        result = await (
            WorkflowBuilder("Math Subtract")
            .add_start()
            .add_math_operation("result", a=10, b=4, operation="subtract")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_math_multiply(self) -> None:
        """Test multiplication operation."""
        result = await (
            WorkflowBuilder("Math Multiply")
            .add_start()
            .add_math_operation("result", a=6, b=7, operation="multiply")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_math_divide(self) -> None:
        """Test division operation."""
        result = await (
            WorkflowBuilder("Math Divide")
            .add_start()
            .add_math_operation("result", a=20, b=4, operation="divide")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_math_divide_float_result(self) -> None:
        """Test division with float result."""
        result = await (
            WorkflowBuilder("Math Divide Float")
            .add_start()
            .add_math_operation("result", a=7, b=2, operation="divide")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestIntegerDivision:
    """Tests for integer division and modulo."""

    async def test_math_integer_divide(self) -> None:
        """Test integer (floor) division."""
        result = await (
            WorkflowBuilder("Math Integer Divide")
            .add_start()
            .add_math_operation("result", a=17, b=5, operation="floor_divide")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_math_modulo(self) -> None:
        """Test modulo operation."""
        result = await (
            WorkflowBuilder("Math Modulo")
            .add_start()
            .add_math_operation("result", a=17, b=5, operation="modulo")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_math_modulo_zero_remainder(self) -> None:
        """Test modulo with zero remainder."""
        result = await (
            WorkflowBuilder("Math Modulo Zero")
            .add_start()
            .add_math_operation("result", a=10, b=5, operation="modulo")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestPowerOperations:
    """Tests for power/exponentiation operations."""

    async def test_math_power(self) -> None:
        """Test power operation."""
        result = await (
            WorkflowBuilder("Math Power")
            .add_start()
            .add_math_operation("result", a=2, b=8, operation="power")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_math_power_fractional(self) -> None:
        """Test power with fractional exponent (square root)."""
        result = await (
            WorkflowBuilder("Math Power Fractional")
            .add_start()
            .add_math_operation("result", a=9, b=0.5, operation="power")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_math_sqrt(self) -> None:
        """Test square root operation."""
        result = await (
            WorkflowBuilder("Math Sqrt")
            .add_start()
            .add_math_operation("result", a=16, operation="sqrt")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestRoundingOperations:
    """Tests for rounding operations."""

    async def test_math_round(self) -> None:
        """Test round operation."""
        result = await (
            WorkflowBuilder("Math Round")
            .add_start()
            .add_math_operation("result", a=3.7, operation="round")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_math_round_down(self) -> None:
        """Test round operation rounding down."""
        result = await (
            WorkflowBuilder("Math Round Down")
            .add_start()
            .add_math_operation("result", a=3.2, operation="round")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_math_floor(self) -> None:
        """Test floor operation."""
        result = await (
            WorkflowBuilder("Math Floor")
            .add_start()
            .add_math_operation("result", a=3.9, operation="floor")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_math_ceil(self) -> None:
        """Test ceiling operation."""
        result = await (
            WorkflowBuilder("Math Ceil")
            .add_start()
            .add_math_operation("result", a=3.1, operation="ceil")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestAbsoluteValue:
    """Tests for absolute value operations."""

    async def test_math_abs_negative(self) -> None:
        """Test absolute value of negative number."""
        result = await (
            WorkflowBuilder("Math Abs Negative")
            .add_start()
            .add_math_operation("result", a=-42, operation="abs")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_math_abs_positive(self) -> None:
        """Test absolute value of positive number (no change)."""
        result = await (
            WorkflowBuilder("Math Abs Positive")
            .add_start()
            .add_math_operation("result", a=42, operation="abs")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_math_negate(self) -> None:
        """Test negation operation."""
        result = await (
            WorkflowBuilder("Math Negate")
            .add_start()
            .add_math_operation("result", a=5, operation="negate")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestMinMaxOperations:
    """Tests for min/max operations."""

    async def test_math_min(self) -> None:
        """Test min of two numbers."""
        result = await (
            WorkflowBuilder("Math Min")
            .add_start()
            .add_math_operation("result", a=5, b=3, operation="min")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_math_max(self) -> None:
        """Test max of two numbers."""
        result = await (
            WorkflowBuilder("Math Max")
            .add_start()
            .add_math_operation("result", a=5, b=3, operation="max")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_reduce_min(self) -> None:
        """Test finding minimum in a list."""
        result = await (
            WorkflowBuilder("List Min")
            .add_start()
            .add_set_variable("numbers", [5, 3, 8, 1, 9])
            .add_list_reduce("{{numbers}}", operation="min")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_reduce_max(self) -> None:
        """Test finding maximum in a list."""
        result = await (
            WorkflowBuilder("List Max")
            .add_start()
            .add_set_variable("numbers", [5, 3, 8, 1, 9])
            .add_list_reduce("{{numbers}}", operation="max")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestFloatOperations:
    """Tests for floating point operations."""

    async def test_math_with_floats(self) -> None:
        """Test math operations with floats."""
        result = await (
            WorkflowBuilder("Math Floats")
            .add_start()
            .add_math_operation("result", a=3.14, b=2, operation="multiply")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_math_negative_numbers(self) -> None:
        """Test math with negative numbers."""
        result = await (
            WorkflowBuilder("Math Negative")
            .add_start()
            .add_math_operation("result", a=-5, b=3, operation="add")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_math_zero_operations(self) -> None:
        """Test math operations involving zero."""
        result = await (
            WorkflowBuilder("Math Zero")
            .add_start()
            .add_math_operation("result", a=0, b=5, operation="add")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestAggregations:
    """Tests for list aggregation operations."""

    async def test_list_sum(self) -> None:
        """Test summing a list of numbers."""
        result = await (
            WorkflowBuilder("List Sum")
            .add_start()
            .add_set_variable("numbers", [1, 2, 3, 4, 5])
            .add_list_reduce("{{numbers}}", operation="sum")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_average(self) -> None:
        """Test averaging a list of numbers."""
        result = await (
            WorkflowBuilder("List Average")
            .add_start()
            .add_set_variable("numbers", [10, 20, 30])
            .add_list_reduce("{{numbers}}", operation="avg")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_product(self) -> None:
        """Test product of a list of numbers."""
        result = await (
            WorkflowBuilder("List Product")
            .add_start()
            .add_set_variable("numbers", [2, 3, 4])
            .add_list_reduce("{{numbers}}", operation="product")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_list_count(self) -> None:
        """Test counting items in a list."""
        result = await (
            WorkflowBuilder("List Count")
            .add_start()
            .add_set_variable("items", ["a", "b", "c", "d", "e"])
            .add_list_reduce("{{items}}", operation="count")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestChainedCalculations:
    """Tests for chained mathematical operations."""

    async def test_math_chain_operations(self) -> None:
        """Test chaining multiple math operations: a + b -> temp1 * c -> result."""
        result = await (
            WorkflowBuilder("Math Chain")
            .add_start()
            .add_set_variable("a", 5)
            .add_set_variable("b", 3)
            .add_set_variable("c", 2)
            .add_math_operation("temp1", a="{{a}}", b="{{b}}", operation="add")
            .add_math_operation(
                "result", a="{{temp1}}", b="{{c}}", operation="multiply"
            )
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_math_with_variables(self) -> None:
        """Test math operations using workflow variables."""
        result = await (
            WorkflowBuilder("Math With Variables")
            .add_start()
            .add_set_variable("x", 10)
            .add_set_variable("y", 5)
            .add_math_operation("sum", a="{{x}}", b="{{y}}", operation="add")
            .add_math_operation("diff", a="{{x}}", b="{{y}}", operation="subtract")
            .add_math_operation("prod", a="{{x}}", b="{{y}}", operation="multiply")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_compound_formula(self) -> None:
        """Test compound formula: (a + b) * (c - d)."""
        result = await (
            WorkflowBuilder("Compound Formula")
            .add_start()
            .add_set_variable("a", 10)
            .add_set_variable("b", 5)
            .add_set_variable("c", 8)
            .add_set_variable("d", 3)
            .add_math_operation("sum_ab", a="{{a}}", b="{{b}}", operation="add")
            .add_math_operation("diff_cd", a="{{c}}", b="{{d}}", operation="subtract")
            .add_math_operation(
                "result", a="{{sum_ab}}", b="{{diff_cd}}", operation="multiply"
            )
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestTrigonometric:
    """Tests for trigonometric operations."""

    async def test_math_sin(self) -> None:
        """Test sine operation."""
        result = await (
            WorkflowBuilder("Math Sin")
            .add_start()
            .add_math_operation("result", a=0, operation="sin")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_math_cos(self) -> None:
        """Test cosine operation."""
        result = await (
            WorkflowBuilder("Math Cos")
            .add_start()
            .add_math_operation("result", a=0, operation="cos")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_math_tan(self) -> None:
        """Test tangent operation."""
        result = await (
            WorkflowBuilder("Math Tan")
            .add_start()
            .add_math_operation("result", a=0, operation="tan")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestLogarithmic:
    """Tests for logarithmic operations."""

    async def test_math_log(self) -> None:
        """Test natural logarithm."""
        result = await (
            WorkflowBuilder("Math Log")
            .add_start()
            .add_math_operation("result", a=2.718281828, operation="log")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_math_log10(self) -> None:
        """Test base-10 logarithm."""
        result = await (
            WorkflowBuilder("Math Log10")
            .add_start()
            .add_math_operation("result", a=100, operation="log10")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_math_exp(self) -> None:
        """Test exponential function (e^x)."""
        result = await (
            WorkflowBuilder("Math Exp")
            .add_start()
            .add_math_operation("result", a=1, operation="exp")
            .add_end()
            .execute()
        )

        assert result["success"] is True


@pytest.mark.asyncio
@pytest.mark.e2e
class TestComparison:
    """Tests for comparison operations."""

    async def test_comparison_equals(self) -> None:
        """Test equality comparison."""
        result = await (
            WorkflowBuilder("Comparison Equals")
            .add_start()
            .add_comparison(a=5, b=5, operator="==")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_comparison_not_equals(self) -> None:
        """Test not-equals comparison."""
        result = await (
            WorkflowBuilder("Comparison Not Equals")
            .add_start()
            .add_comparison(a=5, b=3, operator="!=")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_comparison_greater_than(self) -> None:
        """Test greater than comparison."""
        result = await (
            WorkflowBuilder("Comparison Greater")
            .add_start()
            .add_comparison(a=10, b=5, operator=">")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_comparison_less_than(self) -> None:
        """Test less than comparison."""
        result = await (
            WorkflowBuilder("Comparison Less")
            .add_start()
            .add_comparison(a=3, b=5, operator="<")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_comparison_greater_equal(self) -> None:
        """Test greater than or equal comparison."""
        result = await (
            WorkflowBuilder("Comparison Greater Equal")
            .add_start()
            .add_comparison(a=5, b=5, operator=">=")
            .add_end()
            .execute()
        )

        assert result["success"] is True

    async def test_comparison_less_equal(self) -> None:
        """Test less than or equal comparison."""
        result = await (
            WorkflowBuilder("Comparison Less Equal")
            .add_start()
            .add_comparison(a=5, b=5, operator="<=")
            .add_end()
            .execute()
        )

        assert result["success"] is True
