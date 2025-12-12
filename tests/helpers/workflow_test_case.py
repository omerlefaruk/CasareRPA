"""
CasareRPA - Fluent Workflow Test Case.

Provides a fluent API for testing workflows with minimal boilerplate.

Usage:
    @pytest.mark.asyncio
    async def test_email_workflow():
        await (WorkflowTestCase(email_workflow_json)
            .given_variable('recipient', 'test@example.com')
            .given_variable('subject', 'Test Email')
            .when_executed()
            .then_succeeded()
            .then_variable_equals('email_sent', True))

    @pytest.mark.asyncio
    async def test_loop_workflow():
        await (WorkflowTestCase(loop_workflow_json)
            .given_variable('items', [1, 2, 3])
            .when_executed()
            .then_succeeded()
            .then_variable_contains('results', 'processed')
            .then_node_executed('ForEachNode_1'))
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from unittest.mock import AsyncMock, Mock

from loguru import logger


@dataclass
class ExecutionResult:
    """Result of workflow execution."""

    success: bool
    variables: Dict[str, Any]
    executed_nodes: Set[str]
    errors: List[str]
    duration_ms: float


class WorkflowTestCase:
    """
    Fluent test case builder for workflow testing.

    Provides given/when/then style assertions for clear,
    readable workflow tests.

    Design:
    - given_*: Set up test preconditions
    - when_*: Execute the workflow
    - then_*: Assert outcomes

    All methods return self for chaining.
    """

    def __init__(self, workflow_json: Dict[str, Any]) -> None:
        """
        Initialize test case with workflow definition.

        Args:
            workflow_json: Workflow definition dictionary with
                          'nodes' and 'connections' keys.
        """
        self._workflow = workflow_json
        self._variables: Dict[str, Any] = {}
        self._credentials: Dict[str, Any] = {}
        self._mocked_resources: Dict[str, Any] = {}
        self._result: Optional[ExecutionResult] = None
        self._context: Optional[Any] = None
        self._timeout_ms: int = 30000
        self._skip_cleanup: bool = False

    # =========================================================================
    # GIVEN - Setup preconditions
    # =========================================================================

    def given_variable(self, name: str, value: Any) -> "WorkflowTestCase":
        """
        Set an initial variable for the workflow.

        Args:
            name: Variable name
            value: Variable value

        Returns:
            Self for chaining
        """
        self._variables[name] = value
        return self

    def given_variables(self, variables: Dict[str, Any]) -> "WorkflowTestCase":
        """
        Set multiple initial variables.

        Args:
            variables: Dictionary of variable name -> value

        Returns:
            Self for chaining
        """
        self._variables.update(variables)
        return self

    def given_credential(self, alias: str, value: Any) -> "WorkflowTestCase":
        """
        Mock a credential for the workflow.

        The credential will be returned when the workflow
        requests the given alias from the credential provider.

        Args:
            alias: Credential alias
            value: Credential value (usually a dict with 'username', 'password', etc.)

        Returns:
            Self for chaining
        """
        self._credentials[alias] = value
        return self

    def given_mocked_resource(self, name: str, mock: Any) -> "WorkflowTestCase":
        """
        Provide a mocked resource (page, browser, http_client, etc.).

        Args:
            name: Resource name (e.g., 'page', 'browser', 'http_client')
            mock: Mock object to use

        Returns:
            Self for chaining
        """
        self._mocked_resources[name] = mock
        return self

    def given_timeout(self, timeout_ms: int) -> "WorkflowTestCase":
        """
        Set execution timeout.

        Args:
            timeout_ms: Timeout in milliseconds

        Returns:
            Self for chaining
        """
        self._timeout_ms = timeout_ms
        return self

    def given_skip_cleanup(self) -> "WorkflowTestCase":
        """
        Skip resource cleanup after execution (for debugging).

        Returns:
            Self for chaining
        """
        self._skip_cleanup = True
        return self

    # =========================================================================
    # WHEN - Execute the workflow
    # =========================================================================

    async def when_executed(self) -> "WorkflowTestCase":
        """
        Execute the workflow with the configured preconditions.

        This method:
        1. Creates an ExecutionContext with initial variables
        2. Mocks credentials if provided
        3. Attaches mocked resources
        4. Loads and executes the workflow
        5. Captures the result for assertions

        Returns:
            Self for chaining

        Raises:
            ImportError: If required modules are not available
            RuntimeError: If execution fails unexpectedly
        """
        import time
        from casare_rpa.infrastructure.execution import ExecutionContext
        from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict

        start_time = time.perf_counter()
        executed_nodes: Set[str] = set()
        errors: List[str] = []

        try:
            # Create context with initial variables
            self._context = ExecutionContext(
                workflow_name="Test Workflow",
                initial_variables=self._variables.copy(),
            )

            # Mock credential provider if credentials provided
            if self._credentials:
                mock_provider = AsyncMock()

                async def get_credential(alias: str, required: bool = False) -> Any:
                    if alias in self._credentials:
                        return self._credentials[alias]
                    if required:
                        raise ValueError(f"Credential '{alias}' not found")
                    return None

                mock_provider.get_credential = get_credential
                self._context.resources["credential_provider"] = mock_provider
                self._context._credential_provider = mock_provider

            # Attach mocked resources
            for name, mock in self._mocked_resources.items():
                if name == "page":
                    self._context.set_active_page(mock, "default")
                elif name == "browser":
                    self._context.set_browser(mock)
                else:
                    self._context.resources[name] = mock

            # Load workflow
            workflow = load_workflow_from_dict(self._workflow)

            # Execute workflow
            from casare_rpa.application.use_cases.execute_workflow import (
                ExecuteWorkflowUseCase,
                ExecutionSettings,
            )

            settings = ExecutionSettings(
                node_timeout=self._timeout_ms / 1000.0,
                continue_on_error=False,
            )

            use_case = ExecuteWorkflowUseCase(
                workflow=workflow,
                context=self._context,
                settings=settings,
            )

            result = await use_case.execute()

            # Capture executed nodes
            executed_nodes = set(self._context.execution_path)

            # Capture errors
            for node_id, error_msg in self._context.errors:
                errors.append(f"{node_id}: {error_msg}")

            # Build result
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._result = ExecutionResult(
                success=result.get("success", False),
                variables=self._context.variables.copy(),
                executed_nodes=executed_nodes,
                errors=errors,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            self._result = ExecutionResult(
                success=False,
                variables=self._context.variables.copy() if self._context else {},
                executed_nodes=executed_nodes,
                errors=[str(e)],
                duration_ms=duration_ms,
            )
            logger.error(f"Workflow execution failed: {e}")

        finally:
            # Cleanup unless skipped
            if not self._skip_cleanup and self._context:
                try:
                    await self._context.cleanup()
                except Exception as e:
                    logger.warning(f"Cleanup error: {e}")

        return self

    # =========================================================================
    # THEN - Assertions
    # =========================================================================

    def then_succeeded(self) -> "WorkflowTestCase":
        """
        Assert that the workflow executed successfully.

        Returns:
            Self for chaining

        Raises:
            AssertionError: If workflow did not succeed
        """
        assert (
            self._result is not None
        ), "Workflow not executed - call when_executed() first"
        assert self._result.success, f"Workflow failed. Errors: {self._result.errors}"
        return self

    def then_failed(self) -> "WorkflowTestCase":
        """
        Assert that the workflow failed.

        Returns:
            Self for chaining

        Raises:
            AssertionError: If workflow succeeded
        """
        assert (
            self._result is not None
        ), "Workflow not executed - call when_executed() first"
        assert not self._result.success, "Workflow succeeded but was expected to fail"
        return self

    def then_variable_equals(self, name: str, expected: Any) -> "WorkflowTestCase":
        """
        Assert that a variable has the expected value.

        Args:
            name: Variable name
            expected: Expected value

        Returns:
            Self for chaining

        Raises:
            AssertionError: If variable value doesn't match
        """
        assert (
            self._result is not None
        ), "Workflow not executed - call when_executed() first"
        actual = self._result.variables.get(name)
        assert (
            actual == expected
        ), f"Variable '{name}' expected {expected!r}, got {actual!r}"
        return self

    def then_variable_exists(self, name: str) -> "WorkflowTestCase":
        """
        Assert that a variable exists.

        Args:
            name: Variable name

        Returns:
            Self for chaining

        Raises:
            AssertionError: If variable doesn't exist
        """
        assert (
            self._result is not None
        ), "Workflow not executed - call when_executed() first"
        assert (
            name in self._result.variables
        ), f"Variable '{name}' not found. Available: {list(self._result.variables.keys())}"
        return self

    def then_variable_not_exists(self, name: str) -> "WorkflowTestCase":
        """
        Assert that a variable does not exist.

        Args:
            name: Variable name

        Returns:
            Self for chaining

        Raises:
            AssertionError: If variable exists
        """
        assert (
            self._result is not None
        ), "Workflow not executed - call when_executed() first"
        assert (
            name not in self._result.variables
        ), f"Variable '{name}' exists but should not"
        return self

    def then_variable_contains(self, name: str, substring: str) -> "WorkflowTestCase":
        """
        Assert that a variable contains a substring.

        Args:
            name: Variable name
            substring: Substring to find

        Returns:
            Self for chaining

        Raises:
            AssertionError: If variable doesn't contain substring
        """
        assert (
            self._result is not None
        ), "Workflow not executed - call when_executed() first"
        value = self._result.variables.get(name, "")
        assert substring in str(
            value
        ), f"Variable '{name}' ({value!r}) does not contain '{substring}'"
        return self

    def then_variable_matches(self, name: str, pattern: str) -> "WorkflowTestCase":
        """
        Assert that a variable matches a regex pattern.

        Args:
            name: Variable name
            pattern: Regex pattern

        Returns:
            Self for chaining

        Raises:
            AssertionError: If variable doesn't match pattern
        """
        import re

        assert (
            self._result is not None
        ), "Workflow not executed - call when_executed() first"
        value = str(self._result.variables.get(name, ""))
        assert re.match(
            pattern, value
        ), f"Variable '{name}' ({value!r}) does not match pattern '{pattern}'"
        return self

    def then_variable_type(self, name: str, expected_type: type) -> "WorkflowTestCase":
        """
        Assert that a variable has the expected type.

        Args:
            name: Variable name
            expected_type: Expected Python type

        Returns:
            Self for chaining

        Raises:
            AssertionError: If variable type doesn't match
        """
        assert (
            self._result is not None
        ), "Workflow not executed - call when_executed() first"
        value = self._result.variables.get(name)
        assert isinstance(value, expected_type), (
            f"Variable '{name}' expected type {expected_type.__name__}, "
            f"got {type(value).__name__}"
        )
        return self

    def then_node_executed(self, node_id: str) -> "WorkflowTestCase":
        """
        Assert that a specific node was executed.

        Args:
            node_id: Node identifier

        Returns:
            Self for chaining

        Raises:
            AssertionError: If node was not executed
        """
        assert (
            self._result is not None
        ), "Workflow not executed - call when_executed() first"
        assert node_id in self._result.executed_nodes, (
            f"Node '{node_id}' was not executed. "
            f"Executed nodes: {self._result.executed_nodes}"
        )
        return self

    def then_node_not_executed(self, node_id: str) -> "WorkflowTestCase":
        """
        Assert that a specific node was NOT executed.

        Args:
            node_id: Node identifier

        Returns:
            Self for chaining

        Raises:
            AssertionError: If node was executed
        """
        assert (
            self._result is not None
        ), "Workflow not executed - call when_executed() first"
        assert (
            node_id not in self._result.executed_nodes
        ), f"Node '{node_id}' was executed but should not have been"
        return self

    def then_error_contains(self, substring: str) -> "WorkflowTestCase":
        """
        Assert that an error message contains a substring.

        Args:
            substring: Substring to find in error messages

        Returns:
            Self for chaining

        Raises:
            AssertionError: If no error contains the substring
        """
        assert (
            self._result is not None
        ), "Workflow not executed - call when_executed() first"
        found = any(substring in error for error in self._result.errors)
        assert found, f"No error contains '{substring}'. Errors: {self._result.errors}"
        return self

    def then_no_errors(self) -> "WorkflowTestCase":
        """
        Assert that no errors occurred.

        Returns:
            Self for chaining

        Raises:
            AssertionError: If any errors occurred
        """
        assert (
            self._result is not None
        ), "Workflow not executed - call when_executed() first"
        assert (
            len(self._result.errors) == 0
        ), f"Expected no errors but got: {self._result.errors}"
        return self

    def then_executed_node_count(self, expected: int) -> "WorkflowTestCase":
        """
        Assert the number of nodes executed.

        Args:
            expected: Expected node count

        Returns:
            Self for chaining

        Raises:
            AssertionError: If count doesn't match
        """
        assert (
            self._result is not None
        ), "Workflow not executed - call when_executed() first"
        actual = len(self._result.executed_nodes)
        assert actual == expected, f"Expected {expected} nodes executed, got {actual}"
        return self

    def then_duration_less_than(self, max_ms: float) -> "WorkflowTestCase":
        """
        Assert that execution completed within time limit.

        Args:
            max_ms: Maximum duration in milliseconds

        Returns:
            Self for chaining

        Raises:
            AssertionError: If duration exceeded limit
        """
        assert (
            self._result is not None
        ), "Workflow not executed - call when_executed() first"
        assert self._result.duration_ms < max_ms, (
            f"Execution took {self._result.duration_ms:.1f}ms, "
            f"expected less than {max_ms}ms"
        )
        return self

    # =========================================================================
    # Custom assertions
    # =========================================================================

    def then_custom(
        self, assertion_fn: callable, message: str = "Custom assertion failed"
    ) -> "WorkflowTestCase":
        """
        Run a custom assertion function.

        Args:
            assertion_fn: Function that takes ExecutionResult and returns bool
            message: Error message if assertion fails

        Returns:
            Self for chaining

        Raises:
            AssertionError: If assertion function returns False
        """
        assert (
            self._result is not None
        ), "Workflow not executed - call when_executed() first"
        assert assertion_fn(self._result), message
        return self

    # =========================================================================
    # Accessors for advanced testing
    # =========================================================================

    def get_result(self) -> ExecutionResult:
        """
        Get the execution result for advanced assertions.

        Returns:
            ExecutionResult with success, variables, executed_nodes, errors

        Raises:
            AssertionError: If workflow not executed
        """
        assert (
            self._result is not None
        ), "Workflow not executed - call when_executed() first"
        return self._result

    def get_variable(self, name: str, default: Any = None) -> Any:
        """
        Get a variable value from the execution result.

        Args:
            name: Variable name
            default: Default value if not found

        Returns:
            Variable value

        Raises:
            AssertionError: If workflow not executed
        """
        assert (
            self._result is not None
        ), "Workflow not executed - call when_executed() first"
        return self._result.variables.get(name, default)

    def get_context(self) -> Any:
        """
        Get the execution context (for advanced inspection).

        Returns:
            ExecutionContext instance

        Raises:
            AssertionError: If workflow not executed
        """
        assert (
            self._context is not None
        ), "Workflow not executed - call when_executed() first"
        return self._context
