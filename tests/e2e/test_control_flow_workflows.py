"""
CasareRPA - E2E Tests for Control Flow Workflows.

Tests conditional and branching workflows including:
- If/Else branching with true and false paths
- Nested If conditions
- Switch/Case statements
- Comparison operations
- Expression evaluation
"""

import pytest

from tests.e2e.helpers import WorkflowBuilder


@pytest.mark.asyncio
@pytest.mark.e2e
class TestIfElseWorkflows:
    """End-to-end tests for If/Else control flow."""

    async def test_if_true_branch(self):
        """
        Test If node taking the true branch.
        Initial: {"x": 10}
        If x > 5 -> true: SetVar("result", "big") / false: SetVar("result", "small")
        Expected: result == "big"
        """
        result = await (
            WorkflowBuilder(name="If True Branch")
            .add_start()
            .add_if("{{x}} > 5")
            .branch_true()
            .add_set_variable("result", "big")
            .branch_false()
            .add_set_variable("result", "small")
            .end_if()
            .add_end()
            .execute(initial_vars={"x": 10})
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["result"] == "big"
        ), "Result should be 'big' when x > 5"

    async def test_if_false_branch(self):
        """
        Test If node taking the false branch.
        Initial: {"x": 2}
        If x > 5 -> true: SetVar("result", "big") / false: SetVar("result", "small")
        Expected: result == "small"
        """
        result = await (
            WorkflowBuilder(name="If False Branch")
            .add_start()
            .add_if("{{x}} > 5")
            .branch_true()
            .add_set_variable("result", "big")
            .branch_false()
            .add_set_variable("result", "small")
            .end_if()
            .add_end()
            .execute(initial_vars={"x": 2})
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["result"] == "small"
        ), "Result should be 'small' when x <= 5"

    async def test_if_equality_check(self):
        """
        Test If node with equality check.
        Initial: {"status": "active"}
        If status == "active" -> true: SetVar("is_active", True) / false: SetVar("is_active", False)
        Expected: is_active == True
        """
        result = await (
            WorkflowBuilder(name="If Equality Check")
            .add_start()
            .add_if("{{status}} == 'active'")
            .branch_true()
            .add_set_variable("is_active", True)
            .branch_false()
            .add_set_variable("is_active", False)
            .end_if()
            .add_end()
            .execute(initial_vars={"status": "active"})
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["is_active"] is True
        ), "is_active should be True when status == 'active'"

    async def test_if_with_boolean_variable(self):
        """
        Test If node with boolean variable directly.
        Initial: {"flag": True}
        If flag -> true: SetVar("result", "yes") / false: SetVar("result", "no")
        Expected: result == "yes"
        """
        result = await (
            WorkflowBuilder(name="If Boolean Variable")
            .add_start()
            .add_if("{{flag}}")
            .branch_true()
            .add_set_variable("result", "yes")
            .branch_false()
            .add_set_variable("result", "no")
            .end_if()
            .add_end()
            .execute(initial_vars={"flag": True})
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["result"] == "yes"
        ), "Result should be 'yes' when flag is True"

    async def test_if_with_false_boolean(self):
        """
        Test If node with false boolean variable.
        Initial: {"flag": False}
        If flag -> true: SetVar("result", "yes") / false: SetVar("result", "no")
        Expected: result == "no"
        """
        result = await (
            WorkflowBuilder(name="If False Boolean")
            .add_start()
            .add_if("{{flag}}")
            .branch_true()
            .add_set_variable("result", "yes")
            .branch_false()
            .add_set_variable("result", "no")
            .end_if()
            .add_end()
            .execute(initial_vars={"flag": False})
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["result"] == "no"
        ), "Result should be 'no' when flag is False"

    async def test_nested_if_conditions(self):
        """
        Test nested If conditions.
        Initial: {"x": 15}
        If x > 10:
            If x > 20 -> "very_big"
            Else -> "medium"
        Else -> "small"
        Expected: result == "medium"
        """
        result = await (
            WorkflowBuilder(name="Nested If Conditions")
            .add_start()
            .add_if("{{x}} > 10")
            .branch_true()
            # Inner if
            .add_if("{{x}} > 20")
            .branch_true()
            .add_set_variable("result", "very_big")
            .branch_false()
            .add_set_variable("result", "medium")
            .end_if()
            .branch_false()
            .add_set_variable("result", "small")
            .end_if()
            .add_end()
            .execute(initial_vars={"x": 15})
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["result"] == "medium"
        ), "Result should be 'medium' for x=15"

    async def test_nested_if_very_big(self):
        """
        Test nested If with very big value.
        Initial: {"x": 25}
        Expected: result == "very_big"
        """
        result = await (
            WorkflowBuilder(name="Nested If Very Big")
            .add_start()
            .add_if("{{x}} > 10")
            .branch_true()
            .add_if("{{x}} > 20")
            .branch_true()
            .add_set_variable("result", "very_big")
            .branch_false()
            .add_set_variable("result", "medium")
            .end_if()
            .branch_false()
            .add_set_variable("result", "small")
            .end_if()
            .add_end()
            .execute(initial_vars={"x": 25})
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["result"] == "very_big"
        ), "Result should be 'very_big' for x=25"

    async def test_nested_if_small(self):
        """
        Test nested If with small value.
        Initial: {"x": 5}
        Expected: result == "small"
        """
        result = await (
            WorkflowBuilder(name="Nested If Small")
            .add_start()
            .add_if("{{x}} > 10")
            .branch_true()
            .add_if("{{x}} > 20")
            .branch_true()
            .add_set_variable("result", "very_big")
            .branch_false()
            .add_set_variable("result", "medium")
            .end_if()
            .branch_false()
            .add_set_variable("result", "small")
            .end_if()
            .add_end()
            .execute(initial_vars={"x": 5})
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["result"] == "small"
        ), "Result should be 'small' for x=5"

    async def test_if_with_multiple_operations_in_branch(self):
        """
        Test If with multiple operations in each branch.
        """
        result = await (
            WorkflowBuilder(name="If Multiple Operations")
            .add_start()
            .add_set_variable("value", 100)
            .add_if("{{value}} > 50")
            .branch_true()
            .add_set_variable("category", "high")
            .add_set_variable("multiplier", 2)
            .branch_false()
            .add_set_variable("category", "low")
            .add_set_variable("multiplier", 1)
            .end_if()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["category"] == "high"
        ), "Category should be 'high' for value > 50"
        assert result["variables"]["multiplier"] == 2, "Multiplier should be 2"

    async def test_if_after_if(self):
        """
        Test sequential If statements (not nested).
        """
        result = await (
            WorkflowBuilder(name="Sequential If Statements")
            .add_start()
            .add_set_variable("a", 10)
            .add_set_variable("b", 20)
            # First If
            .add_if("{{a}} > 5")
            .branch_true()
            .add_set_variable("a_status", "high")
            .branch_false()
            .add_set_variable("a_status", "low")
            .end_if()
            # Second If
            .add_if("{{b}} > 15")
            .branch_true()
            .add_set_variable("b_status", "high")
            .branch_false()
            .add_set_variable("b_status", "low")
            .end_if()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["a_status"] == "high", "a_status should be 'high'"
        assert result["variables"]["b_status"] == "high", "b_status should be 'high'"


@pytest.mark.asyncio
@pytest.mark.e2e
class TestSwitchCaseWorkflows:
    """End-to-end tests for Switch/Case control flow."""

    async def test_switch_case_first_match(self):
        """
        Test Switch with first case match.
        Initial: {"status": "success"}
        Switch on status: success->200, error->500, default->0
        Expected: code == 200
        """
        result = await (
            WorkflowBuilder(name="Switch First Match")
            .add_start()
            .add_switch("{{status}}", ["success", "error", "pending"])
            .add_case("success")
            .add_set_variable("code", 200)
            .add_case("error")
            .add_set_variable("code", 500)
            .add_case("pending")
            .add_set_variable("code", 202)
            .add_default_case()
            .add_set_variable("code", 0)
            .end_switch()
            .add_end()
            .execute(initial_vars={"status": "success"})
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["code"] == 200
        ), "Code should be 200 for status='success'"

    async def test_switch_case_second_match(self):
        """
        Test Switch with second case match.
        Initial: {"status": "error"}
        Expected: code == 500
        """
        result = await (
            WorkflowBuilder(name="Switch Second Match")
            .add_start()
            .add_switch("{{status}}", ["success", "error", "pending"])
            .add_case("success")
            .add_set_variable("code", 200)
            .add_case("error")
            .add_set_variable("code", 500)
            .add_case("pending")
            .add_set_variable("code", 202)
            .add_default_case()
            .add_set_variable("code", 0)
            .end_switch()
            .add_end()
            .execute(initial_vars={"status": "error"})
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["code"] == 500
        ), "Code should be 500 for status='error'"

    async def test_switch_default_case(self):
        """
        Test Switch falling through to default case.
        Initial: {"status": "unknown"}
        Expected: code == 0
        """
        result = await (
            WorkflowBuilder(name="Switch Default Case")
            .add_start()
            .add_switch("{{status}}", ["success", "error", "pending"])
            .add_case("success")
            .add_set_variable("code", 200)
            .add_case("error")
            .add_set_variable("code", 500)
            .add_case("pending")
            .add_set_variable("code", 202)
            .add_default_case()
            .add_set_variable("code", 0)
            .end_switch()
            .add_end()
            .execute(initial_vars={"status": "unknown"})
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["code"] == 0, "Code should be 0 for unknown status"

    async def test_switch_with_numeric_cases(self):
        """
        Test Switch with numeric case values.
        Initial: {"level": "2"}
        """
        result = await (
            WorkflowBuilder(name="Switch Numeric Cases")
            .add_start()
            .add_switch("{{level}}", ["1", "2", "3"])
            .add_case("1")
            .add_set_variable("tier", "bronze")
            .add_case("2")
            .add_set_variable("tier", "silver")
            .add_case("3")
            .add_set_variable("tier", "gold")
            .add_default_case()
            .add_set_variable("tier", "unknown")
            .end_switch()
            .add_end()
            .execute(initial_vars={"level": "2"})
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["tier"] == "silver"
        ), "Tier should be 'silver' for level=2"


@pytest.mark.asyncio
@pytest.mark.e2e
class TestComparisonWorkflows:
    """End-to-end tests for comparison operations."""

    async def test_comparison_equals(self):
        """
        Test comparison node with equals operator.
        Start -> SetVar("a", 5) -> SetVar("b", 5) -> Compare("a", "==", "b") -> End
        Expected: ComparisonNode returns True
        """
        result = await (
            WorkflowBuilder(name="Comparison Equals")
            .add_start()
            .add_set_variable("a", 5)
            .add_set_variable("b", 5)
            .add_comparison(5, 5, "==")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"

    async def test_comparison_not_equals(self):
        """
        Test comparison node with not equals operator.
        Compare 5 != 10
        Expected: result == True
        """
        result = await (
            WorkflowBuilder(name="Comparison Not Equals")
            .add_start()
            .add_comparison(5, 10, "!=")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"

    async def test_comparison_greater_than(self):
        """
        Test comparison with greater than.
        Compare 10 > 5
        Expected: result == True
        """
        result = await (
            WorkflowBuilder(name="Comparison Greater Than")
            .add_start()
            .add_comparison(10, 5, ">")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"

    async def test_comparison_less_than(self):
        """
        Test comparison with less than.
        Compare 3 < 7
        Expected: result == True
        """
        result = await (
            WorkflowBuilder(name="Comparison Less Than")
            .add_start()
            .add_comparison(3, 7, "<")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"

    async def test_comparison_greater_or_equal(self):
        """
        Test comparison with greater or equal.
        Compare 5 >= 5
        Expected: result == True
        """
        result = await (
            WorkflowBuilder(name="Comparison Greater Or Equal")
            .add_start()
            .add_comparison(5, 5, ">=")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"

    async def test_comparison_less_or_equal(self):
        """
        Test comparison with less or equal.
        Compare 3 <= 3
        Expected: result == True
        """
        result = await (
            WorkflowBuilder(name="Comparison Less Or Equal")
            .add_start()
            .add_comparison(3, 3, "<=")
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"


@pytest.mark.asyncio
@pytest.mark.e2e
class TestComplexControlFlow:
    """End-to-end tests for complex control flow scenarios."""

    async def test_if_then_set_then_if(self):
        """
        Test If -> SetVariable -> If pattern.
        """
        result = await (
            WorkflowBuilder(name="If Set If Pattern")
            .add_start()
            .add_set_variable("score", 75)
            # First classification
            .add_if("{{score}} >= 60")
            .branch_true()
            .add_set_variable("passed", True)
            .branch_false()
            .add_set_variable("passed", False)
            .end_if()
            # Second classification based on first result (using score again)
            .add_if("{{score}} >= 90")
            .branch_true()
            .add_set_variable("grade", "A")
            .branch_false()
            .add_if("{{score}} >= 70")
            .branch_true()
            .add_set_variable("grade", "B")
            .branch_false()
            .add_set_variable("grade", "C")
            .end_if()
            .end_if()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert result["variables"]["passed"] is True, "Should have passed with score 75"
        assert result["variables"]["grade"] == "B", "Grade should be 'B' for score 75"

    async def test_modify_variable_in_branch(self):
        """
        Test modifying a variable inside a branch.
        """
        result = await (
            WorkflowBuilder(name="Modify Variable In Branch")
            .add_start()
            .add_set_variable("counter", 0)
            .add_if("True")  # Always true
            .branch_true()
            .add_increment_variable("counter")
            .add_increment_variable("counter")
            .branch_false()
            .add_set_variable("counter", -1)  # Should not execute
            .end_if()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["counter"] == 2
        ), "Counter should be 2 after two increments in true branch"

    async def test_expression_with_arithmetic(self):
        """
        Test If expression with arithmetic.
        Initial: {"a": 10, "b": 5}
        If a + b > 10
        """
        result = await (
            WorkflowBuilder(name="Expression With Arithmetic")
            .add_start()
            .add_if("{{a}} + {{b}} > 10")
            .branch_true()
            .add_set_variable("result", "sum_is_big")
            .branch_false()
            .add_set_variable("result", "sum_is_small")
            .end_if()
            .add_end()
            .execute(initial_vars={"a": 10, "b": 5})
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["result"] == "sum_is_big"
        ), "Result should be 'sum_is_big' when a+b > 10"

    async def test_expression_with_string_length(self):
        """
        Test If expression checking string length.
        Initial: {"text": "hello"}
        If len(text) > 3
        """
        result = await (
            WorkflowBuilder(name="Expression String Length")
            .add_start()
            .add_if("len('{{text}}') > 3")
            .branch_true()
            .add_set_variable("is_long", True)
            .branch_false()
            .add_set_variable("is_long", False)
            .end_if()
            .add_end()
            .execute(initial_vars={"text": "hello"})
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["is_long"] is True
        ), "is_long should be True for 'hello' (length 5)"

    async def test_empty_true_branch(self):
        """
        Test If where true branch has no operations (pass through).
        """
        result = await (
            WorkflowBuilder(name="Empty True Branch")
            .add_start()
            .add_set_variable("value", "initial")
            .add_if("True")
            .branch_true()
            # No operations in true branch
            .branch_false()
            .add_set_variable("value", "changed")
            .end_if()
            .add_end()
            .execute()
        )

        # This tests the merge node behavior with empty branches
        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"]["value"] == "initial"
        ), "Value should remain 'initial'"

    async def test_control_flow_does_not_leak_variables(self):
        """
        Test that variables set in one branch don't affect the other.
        """
        result = await (
            WorkflowBuilder(name="No Variable Leak")
            .add_start()
            .add_if("False")  # Always take false branch
            .branch_true()
            .add_set_variable("only_in_true", "true_value")
            .branch_false()
            .add_set_variable("only_in_false", "false_value")
            .end_if()
            .add_end()
            .execute()
        )

        assert result["success"], f"Workflow failed: {result.get('error')}"
        assert (
            result["variables"].get("only_in_false") == "false_value"
        ), "Should have false branch variable"
        assert (
            result["variables"].get("only_in_true") is None
        ), "Should NOT have true branch variable"
