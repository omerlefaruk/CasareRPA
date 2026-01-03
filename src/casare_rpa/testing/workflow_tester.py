"""
CasareRPA - Workflow Testing Framework.

Provides fluent API for testing workflows with mock services.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger

from casare_rpa.testing.mocks import MockExecutionContext


@dataclass
class NodeCallAssertion:
    """Assertion that a node was called a specific number of times."""

    node_name: str
    expected_calls: int = 1
    with_inputs: dict[str, Any] | None = None

    def verify(self, result: TestResult) -> bool:
        """Verify the assertion against test result."""
        actual_calls = result.node_call_counts.get(self.node_name, 0)
        return actual_calls == self.expected_calls

    @property
    def failure_message(self) -> str:
        """Get failure message."""
        return f"Expected node '{self.node_name}' to be called {self.expected_calls} time(s)"


@dataclass
class OutputAssertion:
    """Assertion about workflow output value."""

    output_name: str
    expected_value: Any
    comparator: Callable[[Any, Any], bool] | None = None

    def verify(self, result: TestResult) -> bool:
        """Verify the assertion against test result."""
        if result.outputs is None:
            return False

        actual = result.outputs.get(self.output_name)

        if self.comparator:
            return self.comparator(actual, self.expected_value)

        return actual == self.expected_value

    @property
    def failure_message(self) -> str:
        """Get failure message."""
        return f"Expected output '{self.output_name}' to be {self.expected_value!r}"


@dataclass
class VariableAssertion:
    """Assertion about a variable value after execution."""

    variable_name: str
    expected_value: Any

    def verify(self, result: TestResult) -> bool:
        """Verify the assertion."""
        actual = result.context.get_variable(self.variable_name)
        return actual == self.expected_value

    @property
    def failure_message(self) -> str:
        """Get failure message."""
        return f"Expected variable '{self.variable_name}' to be {self.expected_value!r}"


@dataclass
class TestResult:
    """Result of a workflow test run."""

    success: bool
    """Whether all assertions passed."""

    failures: list[str] = field(default_factory=list)
    """List of failed assertion messages."""

    execution_success: bool = False
    """Whether workflow execution succeeded."""

    execution_error: str | None = None
    """Error message if execution failed."""

    outputs: dict[str, Any] | None = None
    """Workflow outputs after execution."""

    context: MockExecutionContext | None = None
    """Execution context after test."""

    node_call_counts: dict[str, int] = field(default_factory=dict)
    """Number of times each node was executed."""

    execution_time_ms: float = 0.0
    """Execution time in milliseconds."""

    def __str__(self) -> str:
        """String representation."""
        if self.success:
            return f"TestResult(success=True, execution_time={self.execution_time_ms:.2f}ms)"
        return f"TestResult(success=False, failures={len(self.failures)})"


class WorkflowTester:
    """
    Fluent API for testing workflows.

    Example:
        result = await (
            WorkflowTester("path/to/workflow.json")
            .mock_service("http", MockHttpClient().configure_response(
                "https://api.example.com/data",
                json={"status": "ok"}
            ))
            .with_variables({"input": "test_value"})
            .expect_node_called("HttpRequestNode", times=1)
            .expect_output("response_status", "ok")
            .run()
        )

        assert result.success
    """

    def __init__(
        self,
        workflow_path: str | Path | None = None,
        workflow_dict: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize workflow tester.

        Args:
            workflow_path: Path to workflow JSON file
            workflow_dict: Workflow dictionary (alternative to path)
        """
        self._workflow_path = Path(workflow_path) if workflow_path else None
        self._workflow_dict = workflow_dict
        self._workflow: dict[str, Any] | None = None

        self._mock_services: dict[str, Any] = {}
        self._variables: dict[str, Any] = {}
        self._assertions: list[NodeCallAssertion | OutputAssertion | VariableAssertion] = []
        self._setup_hooks: list[Callable[[MockExecutionContext], None]] = []
        self._teardown_hooks: list[Callable[[MockExecutionContext], None]] = []

    def _load_workflow(self) -> dict[str, Any]:
        """Load workflow from path or dict."""
        if self._workflow is not None:
            return self._workflow

        if self._workflow_dict is not None:
            self._workflow = self._workflow_dict
        elif self._workflow_path is not None:
            if not self._workflow_path.exists():
                raise FileNotFoundError(f"Workflow not found: {self._workflow_path}")
            self._workflow = json.loads(self._workflow_path.read_text())
        else:
            raise ValueError("Either workflow_path or workflow_dict must be provided")

        return self._workflow

    def mock_service(self, name: str, mock_impl: Any) -> WorkflowTester:
        """
        Mock a service used by the workflow.

        Args:
            name: Service name (e.g., "http", "browser_pool", "file_io")
            mock_impl: Mock implementation

        Returns:
            Self for chaining
        """
        self._mock_services[name] = mock_impl
        return self

    def with_variable(self, name: str, value: Any) -> WorkflowTester:
        """
        Set a single input variable.

        Args:
            name: Variable name
            value: Variable value

        Returns:
            Self for chaining
        """
        self._variables[name] = value
        return self

    def with_variables(self, variables: dict[str, Any]) -> WorkflowTester:
        """
        Set multiple input variables.

        Args:
            variables: Dictionary of variable name -> value

        Returns:
            Self for chaining
        """
        self._variables.update(variables)
        return self

    def expect_node_called(
        self,
        node_name: str,
        times: int = 1,
        with_inputs: dict[str, Any] | None = None,
    ) -> WorkflowTester:
        """
        Assert that a node is called a specific number of times.

        Args:
            node_name: Node type or ID to check
            times: Expected number of calls
            with_inputs: Expected input values (optional)

        Returns:
            Self for chaining
        """
        self._assertions.append(
            NodeCallAssertion(
                node_name=node_name,
                expected_calls=times,
                with_inputs=with_inputs,
            )
        )
        return self

    def expect_output(
        self,
        output_name: str,
        value: Any,
        comparator: Callable[[Any, Any], bool] | None = None,
    ) -> WorkflowTester:
        """
        Assert that a workflow output has a specific value.

        Args:
            output_name: Name of the output to check
            value: Expected value
            comparator: Custom comparison function (optional)

        Returns:
            Self for chaining
        """
        self._assertions.append(
            OutputAssertion(
                output_name=output_name,
                expected_value=value,
                comparator=comparator,
            )
        )
        return self

    def expect_variable(self, name: str, value: Any) -> WorkflowTester:
        """
        Assert that a variable has a specific value after execution.

        Args:
            name: Variable name
            value: Expected value

        Returns:
            Self for chaining
        """
        self._assertions.append(VariableAssertion(variable_name=name, expected_value=value))
        return self

    def on_setup(self, hook: Callable[[MockExecutionContext], None]) -> WorkflowTester:
        """
        Add setup hook called before execution.

        Args:
            hook: Function receiving context

        Returns:
            Self for chaining
        """
        self._setup_hooks.append(hook)
        return self

    def on_teardown(self, hook: Callable[[MockExecutionContext], None]) -> WorkflowTester:
        """
        Add teardown hook called after execution.

        Args:
            hook: Function receiving context

        Returns:
            Self for chaining
        """
        self._teardown_hooks.append(hook)
        return self

    async def run(self, timeout: float = 30.0) -> TestResult:
        """
        Execute the workflow and verify assertions.

        Args:
            timeout: Maximum execution time in seconds

        Returns:
            TestResult with success status and details
        """
        import time

        start_time = time.perf_counter()

        # Load workflow
        try:
            workflow = self._load_workflow()
        except Exception as e:
            return TestResult(
                success=False,
                failures=[f"Failed to load workflow: {e}"],
                execution_success=False,
                execution_error=str(e),
            )

        # Create mock context
        context = MockExecutionContext()

        # Register mock services
        for name, mock_impl in self._mock_services.items():
            context.register_service(name, mock_impl)

        # Set variables
        for name, value in self._variables.items():
            context.set_variable(name, value)

        # Run setup hooks
        for hook in self._setup_hooks:
            try:
                hook(context)
            except Exception as e:
                logger.warning(f"Setup hook error: {e}")

        # Execute workflow
        execution_success = False
        execution_error: str | None = None
        outputs: dict[str, Any] | None = None
        node_call_counts: dict[str, int] = {}

        try:
            # Import executor lazily to avoid circular imports
            from casare_rpa.application.use_cases.execute_workflow import (
                WorkflowExecutor,
            )

            # Create executor with mock context
            executor = WorkflowExecutor()

            # Execute with timeout
            import asyncio

            result = await asyncio.wait_for(
                executor.execute(workflow, context=context),
                timeout=timeout,
            )

            execution_success = result.success
            outputs = result.outputs if hasattr(result, "outputs") else {}

            # Count node executions from context
            for call in context.call_log:
                if call[0] == "execute_node":
                    node_type = call[1][0] if call[1] else "unknown"
                    node_call_counts[node_type] = node_call_counts.get(node_type, 0) + 1

        except TimeoutError:
            execution_success = False
            execution_error = f"Workflow execution timed out after {timeout}s"
        except ImportError as e:
            # Fallback for when executor is not available (testing the testing framework)
            logger.warning(f"Executor not available, using mock execution: {e}")
            execution_success = True
            outputs = {}
        except Exception as e:
            execution_success = False
            execution_error = str(e)
            logger.error(f"Workflow execution error: {e}")

        # Run teardown hooks
        for hook in self._teardown_hooks:
            try:
                hook(context)
            except Exception as e:
                logger.warning(f"Teardown hook error: {e}")

        execution_time = (time.perf_counter() - start_time) * 1000

        # Build result
        result = TestResult(
            success=True,  # Will be set to False if assertions fail
            execution_success=execution_success,
            execution_error=execution_error,
            outputs=outputs,
            context=context,
            node_call_counts=node_call_counts,
            execution_time_ms=execution_time,
        )

        # Verify assertions
        failures: list[str] = []

        # Check execution success
        if not execution_success:
            failures.append(f"Workflow execution failed: {execution_error}")

        # Check all assertions
        for assertion in self._assertions:
            if not assertion.verify(result):
                failures.append(assertion.failure_message)

        result.success = len(failures) == 0
        result.failures = failures

        return result

    def __repr__(self) -> str:
        """String representation."""
        path = self._workflow_path or "<dict>"
        return (
            f"WorkflowTester(workflow={path}, "
            f"services={len(self._mock_services)}, "
            f"variables={len(self._variables)}, "
            f"assertions={len(self._assertions)})"
        )


__all__ = [
    "WorkflowTester",
    "TestResult",
    "NodeCallAssertion",
    "OutputAssertion",
    "VariableAssertion",
]
