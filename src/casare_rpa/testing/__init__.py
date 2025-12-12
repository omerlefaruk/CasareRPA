"""
CasareRPA - Testing Framework.

Provides utilities for testing workflows and nodes:
- WorkflowTester: Fluent API for testing workflows
- MockExecutionContext: Mock context for isolated testing
- NodeTestGenerator: Generate test stubs for nodes
- VisualRegressionTester: Test UI components for regressions

Usage:
    from casare_rpa.testing import WorkflowTester, MockExecutionContext

    # Test a workflow
    result = await (
        WorkflowTester("path/to/workflow.json")
        .mock_service("http", MockHttpClient())
        .with_variables({"input": "test"})
        .expect_output("result", "expected")
        .run()
    )
    assert result.success
"""

from casare_rpa.testing.workflow_tester import (
    WorkflowTester,
    TestResult,
    NodeCallAssertion,
    OutputAssertion,
)
from casare_rpa.testing.mocks import (
    MockExecutionContext,
    MockHttpClient,
    MockBrowserPool,
    MockService,
)
from casare_rpa.testing.node_test_generator import (
    NodeTestGenerator,
)

__all__ = [
    # Workflow testing
    "WorkflowTester",
    "TestResult",
    "NodeCallAssertion",
    "OutputAssertion",
    # Mocks
    "MockExecutionContext",
    "MockHttpClient",
    "MockBrowserPool",
    "MockService",
    # Test generation
    "NodeTestGenerator",
]
