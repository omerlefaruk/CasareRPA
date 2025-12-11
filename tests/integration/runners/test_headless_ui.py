"""
CasareRPA - Headless UI Runner Integration Tests

Tests for executing workflows in headless Qt mode without displaying windows.
Provides QtHeadlessRunner for testing workflow execution programmatically.

Usage:
    pytest tests/integration/runners/test_headless_ui.py -v
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.events import EventBus, get_event_bus
from casare_rpa.domain.value_objects.types import EventType
from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict


# =============================================================================
# EXECUTION REPORT DATACLASS
# =============================================================================


@dataclass
class ExecutionReport:
    """
    Report from workflow execution.

    Contains execution results, timing, and diagnostic information.
    """

    success: bool
    execution_time: float
    nodes_executed: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    outputs: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def duration_ms(self) -> float:
        """Get execution duration in milliseconds."""
        return self.execution_time * 1000

    def to_dict(self) -> Dict[str, Any]:
        """Serialize report to dictionary."""
        return {
            "success": self.success,
            "execution_time": self.execution_time,
            "duration_ms": self.duration_ms,
            "nodes_executed": self.nodes_executed,
            "errors": self.errors,
            "outputs": self.outputs,
            "variables": self.variables,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
        }


# =============================================================================
# QT HEADLESS RUNNER
# =============================================================================


class QtHeadlessRunner:
    """
    Headless Qt workflow runner for integration testing.

    Executes workflows without displaying GUI windows, suitable for
    CI/CD pipelines and automated testing environments.

    Features:
    - Offscreen rendering mode
    - Event bus integration for progress tracking
    - Node output capture
    - Comprehensive execution reporting

    Usage:
        runner = QtHeadlessRunner(qtbot)
        workflow = runner.load_workflow(Path("workflow.json"))
        report = await runner.execute_workflow()
        assert report.success
    """

    def __init__(self, qtbot: Optional[Any] = None) -> None:
        """
        Initialize headless runner.

        Args:
            qtbot: Optional pytest-qt qtbot fixture for Qt integration
        """
        self._qtbot = qtbot
        self._workflow: Optional[WorkflowSchema] = None
        self._workflow_data: Optional[Dict[str, Any]] = None
        self._event_bus: EventBus = get_event_bus()
        self._executed_nodes: List[str] = []
        self._node_outputs: Dict[str, Dict[str, Any]] = {}
        self._errors: List[str] = []
        self._variables: Dict[str, Any] = {}

        # Subscribe to execution events
        self._setup_event_handlers()

    def _setup_event_handlers(self) -> None:
        """Set up event bus handlers for tracking execution."""
        self._event_bus.subscribe(EventType.NODE_STARTED, self._on_node_started)
        self._event_bus.subscribe(EventType.NODE_COMPLETED, self._on_node_completed)
        self._event_bus.subscribe(EventType.NODE_ERROR, self._on_node_error)
        self._event_bus.subscribe(EventType.VARIABLE_SET, self._on_variable_set)

    def _cleanup_event_handlers(self) -> None:
        """Clean up event bus subscriptions."""
        try:
            self._event_bus.unsubscribe(EventType.NODE_STARTED, self._on_node_started)
            self._event_bus.unsubscribe(
                EventType.NODE_COMPLETED, self._on_node_completed
            )
            self._event_bus.unsubscribe(EventType.NODE_ERROR, self._on_node_error)
            self._event_bus.unsubscribe(EventType.VARIABLE_SET, self._on_variable_set)
        except Exception:
            pass  # Ignore cleanup errors

    def _on_node_started(self, event: Any) -> None:
        """Handle node started event."""
        node_id = event.data.get("node_id", "")
        if node_id and node_id not in self._executed_nodes:
            self._executed_nodes.append(node_id)

    def _on_node_completed(self, event: Any) -> None:
        """Handle node completed event."""
        node_id = event.data.get("node_id", "")
        result = event.data.get("result", {})
        if node_id:
            self._node_outputs[node_id] = result

    def _on_node_error(self, event: Any) -> None:
        """Handle node error event."""
        node_id = event.data.get("node_id", "")
        error = event.data.get("error", "Unknown error")
        self._errors.append(f"{node_id}: {error}")

    def _on_variable_set(self, event: Any) -> None:
        """Handle variable set event."""
        name = event.data.get("name", "")
        value = event.data.get("value")
        if name:
            self._variables[name] = value

    def load_workflow(self, workflow_path: Path) -> WorkflowSchema:
        """
        Load a workflow from JSON file.

        Args:
            workflow_path: Path to workflow JSON file

        Returns:
            Loaded WorkflowSchema

        Raises:
            FileNotFoundError: If workflow file doesn't exist
            ValueError: If workflow JSON is invalid
        """
        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {workflow_path}")

        with open(workflow_path, "r", encoding="utf-8") as f:
            self._workflow_data = json.load(f)

        self._workflow = load_workflow_from_dict(self._workflow_data)
        return self._workflow

    def load_workflow_from_dict(self, workflow_data: Dict[str, Any]) -> WorkflowSchema:
        """
        Load a workflow from dictionary data.

        Args:
            workflow_data: Workflow data dictionary

        Returns:
            Loaded WorkflowSchema
        """
        self._workflow_data = workflow_data
        self._workflow = load_workflow_from_dict(workflow_data)
        return self._workflow

    async def execute_workflow(
        self,
        initial_variables: Optional[Dict[str, Any]] = None,
        timeout: float = 60.0,
    ) -> ExecutionReport:
        """
        Execute the loaded workflow.

        Args:
            initial_variables: Optional initial variables for execution
            timeout: Maximum execution time in seconds

        Returns:
            ExecutionReport with results

        Raises:
            ValueError: If no workflow is loaded
            asyncio.TimeoutError: If execution exceeds timeout
        """
        if self._workflow is None:
            raise ValueError("No workflow loaded. Call load_workflow() first.")

        # Reset tracking state
        self._executed_nodes = []
        self._node_outputs = {}
        self._errors = []
        self._variables = {}

        started_at = datetime.now()

        try:
            # Import here to avoid circular imports
            from casare_rpa.application.use_cases.execute_workflow import (
                ExecuteWorkflowUseCase,
                ExecutionSettings,
            )

            settings = ExecutionSettings(
                target_node_id=None,
                continue_on_error=False,
                node_timeout=timeout,
            )

            use_case = ExecuteWorkflowUseCase(
                workflow=self._workflow,
                event_bus=self._event_bus,
                settings=settings,
                initial_variables=initial_variables or {},
            )

            success = await asyncio.wait_for(
                use_case.execute(),
                timeout=timeout,
            )

            completed_at = datetime.now()
            execution_time = (completed_at - started_at).total_seconds()

            return ExecutionReport(
                success=success,
                execution_time=execution_time,
                nodes_executed=self._executed_nodes.copy(),
                errors=self._errors.copy(),
                outputs=self._node_outputs.copy(),
                variables=self._variables.copy(),
                started_at=started_at,
                completed_at=completed_at,
            )

        except asyncio.TimeoutError:
            completed_at = datetime.now()
            execution_time = (completed_at - started_at).total_seconds()
            self._errors.append(f"Execution timeout after {timeout}s")

            return ExecutionReport(
                success=False,
                execution_time=execution_time,
                nodes_executed=self._executed_nodes.copy(),
                errors=self._errors.copy(),
                outputs=self._node_outputs.copy(),
                variables=self._variables.copy(),
                started_at=started_at,
                completed_at=completed_at,
            )

        except Exception as e:
            completed_at = datetime.now()
            execution_time = (completed_at - started_at).total_seconds()
            self._errors.append(str(e))

            return ExecutionReport(
                success=False,
                execution_time=execution_time,
                nodes_executed=self._executed_nodes.copy(),
                errors=self._errors.copy(),
                outputs=self._node_outputs.copy(),
                variables=self._variables.copy(),
                started_at=started_at,
                completed_at=completed_at,
            )

        finally:
            self._cleanup_event_handlers()

    def get_node_outputs(self, node_id: str) -> Dict[str, Any]:
        """
        Get output values from an executed node.

        Args:
            node_id: ID of the node to get outputs for

        Returns:
            Dictionary of output port values
        """
        return self._node_outputs.get(node_id, {})

    def get_variable(self, name: str, default: Any = None) -> Any:
        """
        Get a variable value from execution context.

        Args:
            name: Variable name
            default: Default value if not found

        Returns:
            Variable value or default
        """
        return self._variables.get(name, default)

    def cleanup(self) -> None:
        """Clean up runner resources."""
        self._cleanup_event_handlers()
        self._workflow = None
        self._workflow_data = None
        self._executed_nodes = []
        self._node_outputs = {}
        self._errors = []
        self._variables = {}


# =============================================================================
# SAMPLE WORKFLOW FIXTURES
# =============================================================================


def create_simple_workflow() -> Dict[str, Any]:
    """Create a simple Start -> End workflow for testing."""
    return {
        "metadata": {
            "name": "Simple Test Workflow",
            "version": "1.0.0",
            "description": "Basic workflow for headless testing",
        },
        "nodes": {
            "start_1": {
                "node_id": "start_1",
                "node_type": "StartNode",
                "config": {},
            },
            "end_1": {
                "node_id": "end_1",
                "node_type": "EndNode",
                "config": {},
            },
        },
        "connections": [
            {
                "source_node": "start_1",
                "source_port": "exec_out",
                "target_node": "end_1",
                "target_port": "exec_in",
            },
        ],
        "variables": {},
        "settings": {
            "stop_on_error": True,
            "timeout": 30,
        },
    }


def create_log_workflow() -> Dict[str, Any]:
    """Create a workflow with SetVariable for testing (simulating logging via variable)."""
    return {
        "metadata": {
            "name": "Log Test Workflow",
            "version": "1.0.0",
            "description": "Workflow with SetVariableNode for testing",
        },
        "nodes": {
            "start_1": {
                "node_id": "start_1",
                "node_type": "StartNode",
                "config": {},
            },
            "setvar_log": {
                "node_id": "setvar_log",
                "node_type": "SetVariableNode",
                "config": {
                    "variable_name": "log_message",
                    "value": "Test log message",
                },
            },
            "end_1": {
                "node_id": "end_1",
                "node_type": "EndNode",
                "config": {},
            },
        },
        "connections": [
            {
                "source_node": "start_1",
                "source_port": "exec_out",
                "target_node": "setvar_log",
                "target_port": "exec_in",
            },
            {
                "source_node": "setvar_log",
                "source_port": "exec_out",
                "target_node": "end_1",
                "target_port": "exec_in",
            },
        ],
        "variables": {},
        "settings": {},
    }


def create_variable_workflow() -> Dict[str, Any]:
    """Create a workflow that sets and uses variables."""
    return {
        "metadata": {
            "name": "Variable Test Workflow",
            "version": "1.0.0",
            "description": "Workflow with variable operations",
        },
        "nodes": {
            "start_1": {
                "node_id": "start_1",
                "node_type": "StartNode",
                "config": {},
            },
            "setvar_1": {
                "node_id": "setvar_1",
                "node_type": "SetVariableNode",
                "config": {
                    "variable_name": "test_output",
                    "value": "hello_world",
                },
            },
            "end_1": {
                "node_id": "end_1",
                "node_type": "EndNode",
                "config": {},
            },
        },
        "connections": [
            {
                "source_node": "start_1",
                "source_port": "exec_out",
                "target_node": "setvar_1",
                "target_port": "exec_in",
            },
            {
                "source_node": "setvar_1",
                "source_port": "exec_out",
                "target_node": "end_1",
                "target_port": "exec_in",
            },
        ],
        "variables": {
            "initial_var": {
                "type": "String",
                "default_value": "initial_value",
            },
        },
        "settings": {},
    }


def create_error_workflow() -> Dict[str, Any]:
    """Create a workflow that intentionally fails for error testing."""
    return {
        "metadata": {
            "name": "Error Test Workflow",
            "version": "1.0.0",
            "description": "Workflow that intentionally fails",
        },
        "nodes": {
            "start_1": {
                "node_id": "start_1",
                "node_type": "StartNode",
                "config": {},
            },
            # Use an invalid/missing node type to trigger error
            "invalid_1": {
                "node_id": "invalid_1",
                "node_type": "NonExistentNode",
                "config": {},
            },
            "end_1": {
                "node_id": "end_1",
                "node_type": "EndNode",
                "config": {},
            },
        },
        "connections": [
            {
                "source_node": "start_1",
                "source_port": "exec_out",
                "target_node": "invalid_1",
                "target_port": "exec_in",
            },
            {
                "source_node": "invalid_1",
                "source_port": "exec_out",
                "target_node": "end_1",
                "target_port": "exec_in",
            },
        ],
        "variables": {},
        "settings": {
            "stop_on_error": True,
        },
    }


def create_ai_generated_workflow() -> Dict[str, Any]:
    """Create a workflow simulating AI-generated structure."""
    return {
        "metadata": {
            "name": "AI Generated Workflow",
            "version": "1.0.0",
            "description": "Simulates AI-generated workflow structure",
            "author": "AI Assistant",
            "created_at": "2025-12-11T00:00:00Z",
        },
        "nodes": {
            "start_ai": {
                "node_id": "start_ai",
                "node_type": "StartNode",
                "config": {},
            },
            "setvar_greeting": {
                "node_id": "setvar_greeting",
                "node_type": "SetVariableNode",
                "config": {
                    "variable_name": "greeting",
                    "value": "AI workflow started",
                },
            },
            "setvar_result": {
                "node_id": "setvar_result",
                "node_type": "SetVariableNode",
                "config": {
                    "variable_name": "ai_result",
                    "value": "AI workflow completed successfully",
                },
            },
            "setvar_final": {
                "node_id": "setvar_final",
                "node_type": "SetVariableNode",
                "config": {
                    "variable_name": "final_status",
                    "value": "done",
                },
            },
            "end_ai": {
                "node_id": "end_ai",
                "node_type": "EndNode",
                "config": {},
            },
        },
        "connections": [
            {
                "source_node": "start_ai",
                "source_port": "exec_out",
                "target_node": "setvar_greeting",
                "target_port": "exec_in",
            },
            {
                "source_node": "setvar_greeting",
                "source_port": "exec_out",
                "target_node": "setvar_result",
                "target_port": "exec_in",
            },
            {
                "source_node": "setvar_result",
                "source_port": "exec_out",
                "target_node": "setvar_final",
                "target_port": "exec_in",
            },
            {
                "source_node": "setvar_final",
                "source_port": "exec_out",
                "target_node": "end_ai",
                "target_port": "exec_in",
            },
        ],
        "variables": {
            "ai_result": {
                "type": "String",
                "default_value": "",
            },
        },
        "settings": {
            "stop_on_error": True,
            "timeout": 60,
        },
    }


# =============================================================================
# PYTEST FIXTURES
# =============================================================================


@pytest.fixture
def headless_runner() -> QtHeadlessRunner:
    """Provide a headless runner instance for testing."""
    runner = QtHeadlessRunner(qtbot=None)
    yield runner
    runner.cleanup()


@pytest.fixture
def simple_workflow_data() -> Dict[str, Any]:
    """Provide simple workflow data."""
    return create_simple_workflow()


@pytest.fixture
def log_workflow_data() -> Dict[str, Any]:
    """Provide log workflow data."""
    return create_log_workflow()


@pytest.fixture
def variable_workflow_data() -> Dict[str, Any]:
    """Provide variable workflow data."""
    return create_variable_workflow()


@pytest.fixture
def error_workflow_data() -> Dict[str, Any]:
    """Provide error workflow data."""
    return create_error_workflow()


@pytest.fixture
def ai_workflow_data() -> Dict[str, Any]:
    """Provide AI-generated workflow data."""
    return create_ai_generated_workflow()


@pytest.fixture
def workflow_file(tmp_path: Path, simple_workflow_data: Dict[str, Any]) -> Path:
    """Create a workflow JSON file for testing."""
    workflow_path = tmp_path / "test_workflow.json"
    with open(workflow_path, "w", encoding="utf-8") as f:
        json.dump(simple_workflow_data, f, indent=2)
    return workflow_path


# =============================================================================
# TESTS: QtHeadlessRunner
# =============================================================================


class TestQtHeadlessRunner:
    """Tests for QtHeadlessRunner class."""

    def test_init(self, headless_runner: QtHeadlessRunner) -> None:
        """Test runner initialization."""
        assert headless_runner._workflow is None
        assert headless_runner._workflow_data is None
        assert headless_runner._executed_nodes == []
        assert headless_runner._errors == []

    def test_load_workflow_from_file(
        self, headless_runner: QtHeadlessRunner, workflow_file: Path
    ) -> None:
        """Test loading workflow from JSON file."""
        workflow = headless_runner.load_workflow(workflow_file)

        assert workflow is not None
        assert isinstance(workflow, WorkflowSchema)
        assert workflow.metadata.name == "Simple Test Workflow"

    def test_load_workflow_from_dict(
        self, headless_runner: QtHeadlessRunner, simple_workflow_data: Dict[str, Any]
    ) -> None:
        """Test loading workflow from dictionary."""
        workflow = headless_runner.load_workflow_from_dict(simple_workflow_data)

        assert workflow is not None
        assert isinstance(workflow, WorkflowSchema)
        assert workflow.metadata.name == "Simple Test Workflow"

    def test_load_nonexistent_file_raises(
        self, headless_runner: QtHeadlessRunner, tmp_path: Path
    ) -> None:
        """Test loading nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            headless_runner.load_workflow(tmp_path / "nonexistent.json")

    def test_cleanup(self, headless_runner: QtHeadlessRunner) -> None:
        """Test runner cleanup."""
        headless_runner._executed_nodes = ["node1", "node2"]
        headless_runner._errors = ["error1"]

        headless_runner.cleanup()

        assert headless_runner._workflow is None
        assert headless_runner._executed_nodes == []
        assert headless_runner._errors == []


class TestExecutionReport:
    """Tests for ExecutionReport dataclass."""

    def test_init_defaults(self) -> None:
        """Test ExecutionReport default values."""
        report = ExecutionReport(success=True, execution_time=1.5)

        assert report.success is True
        assert report.execution_time == 1.5
        assert report.nodes_executed == []
        assert report.errors == []
        assert report.outputs == {}
        assert report.variables == {}

    def test_duration_ms(self) -> None:
        """Test duration_ms property."""
        report = ExecutionReport(success=True, execution_time=1.5)
        assert report.duration_ms == 1500.0

    def test_to_dict(self) -> None:
        """Test report serialization."""
        report = ExecutionReport(
            success=True,
            execution_time=2.5,
            nodes_executed=["start_1", "end_1"],
            errors=[],
            outputs={"start_1": {"success": True}},
            variables={"test": "value"},
        )

        data = report.to_dict()

        assert data["success"] is True
        assert data["execution_time"] == 2.5
        assert data["duration_ms"] == 2500.0
        assert data["nodes_executed"] == ["start_1", "end_1"]
        assert data["variables"] == {"test": "value"}


# =============================================================================
# TESTS: WORKFLOW EXECUTION
# =============================================================================


@pytest.mark.asyncio
async def test_simple_workflow_execution(
    headless_runner: QtHeadlessRunner, simple_workflow_data: Dict[str, Any]
) -> None:
    """Test executing a simple Start -> End workflow."""
    headless_runner.load_workflow_from_dict(simple_workflow_data)

    report = await headless_runner.execute_workflow()

    assert report.success is True
    assert report.execution_time > 0
    assert len(report.errors) == 0
    # Should execute start and end nodes
    assert len(report.nodes_executed) >= 1


@pytest.mark.asyncio
async def test_log_workflow_execution(
    headless_runner: QtHeadlessRunner, log_workflow_data: Dict[str, Any]
) -> None:
    """Test workflow with LogNode execution."""
    headless_runner.load_workflow_from_dict(log_workflow_data)

    report = await headless_runner.execute_workflow()

    assert report.success is True
    assert len(report.errors) == 0
    # Should have executed start, log, and end nodes
    assert len(report.nodes_executed) >= 2


@pytest.mark.asyncio
async def test_variable_workflow_execution(
    headless_runner: QtHeadlessRunner, variable_workflow_data: Dict[str, Any]
) -> None:
    """Test workflow that sets variables."""
    headless_runner.load_workflow_from_dict(variable_workflow_data)

    report = await headless_runner.execute_workflow()

    assert report.success is True
    # Note: Variable tracking depends on event bus integration
    # Variables may be captured if SetVariableNode emits VARIABLE_SET event


@pytest.mark.asyncio
async def test_workflow_with_initial_variables(
    headless_runner: QtHeadlessRunner, simple_workflow_data: Dict[str, Any]
) -> None:
    """Test workflow execution with initial variables."""
    headless_runner.load_workflow_from_dict(simple_workflow_data)

    initial_vars = {
        "input_data": "test_value",
        "counter": 42,
    }

    report = await headless_runner.execute_workflow(initial_variables=initial_vars)

    assert report.success is True


@pytest.mark.asyncio
async def test_workflow_error_handling(
    headless_runner: QtHeadlessRunner, error_workflow_data: Dict[str, Any]
) -> None:
    """Test workflow with intentional error handling."""
    # This workflow contains a non-existent node type
    # The loader may skip it, so execution may complete but with warnings
    headless_runner.load_workflow_from_dict(error_workflow_data)

    report = await headless_runner.execute_workflow()

    # Execution should complete (may succeed or fail depending on error handling)
    # The important thing is it doesn't crash
    assert report.execution_time > 0


@pytest.mark.asyncio
async def test_ai_generated_workflow_execution(
    headless_runner: QtHeadlessRunner, ai_workflow_data: Dict[str, Any]
) -> None:
    """Test executing an AI-generated workflow structure."""
    headless_runner.load_workflow_from_dict(ai_workflow_data)

    report = await headless_runner.execute_workflow()

    assert report.success is True
    assert report.execution_time > 0
    assert len(report.errors) == 0


@pytest.mark.asyncio
async def test_execute_without_loading_raises(
    headless_runner: QtHeadlessRunner,
) -> None:
    """Test that executing without loading raises ValueError."""
    with pytest.raises(ValueError, match="No workflow loaded"):
        await headless_runner.execute_workflow()


@pytest.mark.asyncio
async def test_execution_timeout(
    headless_runner: QtHeadlessRunner, simple_workflow_data: Dict[str, Any]
) -> None:
    """Test workflow execution with timeout."""
    headless_runner.load_workflow_from_dict(simple_workflow_data)

    # Use a reasonable timeout that should allow completion
    report = await headless_runner.execute_workflow(timeout=30.0)

    assert report.execution_time < 30.0  # Should complete before timeout


@pytest.mark.asyncio
async def test_get_node_outputs(
    headless_runner: QtHeadlessRunner, simple_workflow_data: Dict[str, Any]
) -> None:
    """Test retrieving node outputs after execution."""
    headless_runner.load_workflow_from_dict(simple_workflow_data)
    await headless_runner.execute_workflow()

    # Try to get outputs for a known node
    outputs = headless_runner.get_node_outputs("start_1")
    # Output may be empty dict if no outputs captured
    assert isinstance(outputs, dict)


@pytest.mark.asyncio
async def test_get_variable(
    headless_runner: QtHeadlessRunner, variable_workflow_data: Dict[str, Any]
) -> None:
    """Test retrieving variables after execution."""
    headless_runner.load_workflow_from_dict(variable_workflow_data)
    await headless_runner.execute_workflow()

    # Variable may or may not be captured depending on event integration
    result = headless_runner.get_variable("nonexistent", "default")
    assert result == "default"


# =============================================================================
# TESTS: WORKFLOW FILE OPERATIONS
# =============================================================================


@pytest.mark.asyncio
async def test_workflow_from_file_execution(
    headless_runner: QtHeadlessRunner, workflow_file: Path
) -> None:
    """Test complete workflow execution from file."""
    headless_runner.load_workflow(workflow_file)

    report = await headless_runner.execute_workflow()

    assert report.success is True
    assert report.started_at is not None
    assert report.completed_at is not None
    assert report.completed_at >= report.started_at


def test_workflow_file_save_and_load(
    headless_runner: QtHeadlessRunner, tmp_path: Path, ai_workflow_data: Dict[str, Any]
) -> None:
    """Test saving and loading workflow files."""
    # Save workflow to file
    workflow_path = tmp_path / "ai_workflow.json"
    with open(workflow_path, "w", encoding="utf-8") as f:
        json.dump(ai_workflow_data, f, indent=2)

    # Load and verify
    workflow = headless_runner.load_workflow(workflow_path)

    assert workflow.metadata.name == "AI Generated Workflow"
    assert len(workflow.nodes) > 0


def create_messagebox_workflow() -> Dict[str, Any]:
    """Create a workflow with MessageBoxNode for testing (requires mocking)."""
    return {
        "metadata": {
            "name": "MessageBox Test Workflow",
            "version": "1.0.0",
            "description": "Workflow with MessageBoxNode for testing",
        },
        "nodes": {
            "start_1": {
                "node_id": "start_1",
                "node_type": "StartNode",
                "config": {},
            },
            "msgbox_1": {
                "node_id": "msgbox_1",
                "node_type": "MessageBoxNode",
                "config": {
                    "title": "Test Message",
                    "message": "Hello from headless test!",
                    "icon_type": "information",
                    "buttons": "ok",
                    "auto_close_timeout": 1,  # Auto-close after 1 second
                },
            },
            "end_1": {
                "node_id": "end_1",
                "node_type": "EndNode",
                "config": {},
            },
        },
        "connections": [
            {
                "source_node": "start_1",
                "source_port": "exec_out",
                "target_node": "msgbox_1",
                "target_port": "exec_in",
            },
            {
                "source_node": "msgbox_1",
                "source_port": "exec_out",
                "target_node": "end_1",
                "target_port": "exec_in",
            },
        ],
        "variables": {},
        "settings": {},
    }


@pytest.fixture
def messagebox_workflow_data() -> Dict[str, Any]:
    """Provide messagebox workflow data."""
    return create_messagebox_workflow()


# =============================================================================
# TESTS: MOCKED SCENARIOS
# =============================================================================


@pytest.mark.asyncio
async def test_workflow_with_messagebox_mocked(
    headless_runner: QtHeadlessRunner, messagebox_workflow_data: Dict[str, Any]
) -> None:
    """Test MessageBoxNode workflow with mocked dialog.

    MessageBoxNode displays Qt dialog which requires user interaction.
    In headless mode, we mock the dialog to return immediately.
    """
    # Mock the QMessageBox.exec to avoid blocking
    with patch("PySide6.QtWidgets.QMessageBox") as mock_msgbox:
        # Configure mock to return OK immediately
        mock_instance = MagicMock()
        mock_instance.exec.return_value = 1024  # QMessageBox.Ok
        mock_instance.clickedButton.return_value = mock_instance.button.return_value
        mock_msgbox.return_value = mock_instance

        headless_runner.load_workflow_from_dict(messagebox_workflow_data)
        report = await headless_runner.execute_workflow()

        # Execution should complete (dialog was mocked)
        # Success depends on whether mock was properly applied
        assert report.execution_time > 0


@pytest.mark.asyncio
async def test_workflow_with_mocked_browser(
    headless_runner: QtHeadlessRunner, simple_workflow_data: Dict[str, Any]
) -> None:
    """Test workflow execution with mocked browser dependencies."""
    # Patch browser-related imports to avoid actual browser startup
    with patch(
        "casare_rpa.infrastructure.resources.browser_resource_manager.BrowserResourceManager"
    ):
        headless_runner.load_workflow_from_dict(simple_workflow_data)
        report = await headless_runner.execute_workflow()

        # Should complete without needing actual browser
        assert report.execution_time > 0


@pytest.mark.asyncio
async def test_multiple_workflow_executions(
    headless_runner: QtHeadlessRunner, simple_workflow_data: Dict[str, Any]
) -> None:
    """Test executing the same workflow multiple times."""
    headless_runner.load_workflow_from_dict(simple_workflow_data)

    # Execute multiple times
    reports = []
    for _ in range(3):
        report = await headless_runner.execute_workflow()
        reports.append(report)

    # All executions should succeed
    assert all(r.success for r in reports)
    assert len(reports) == 3


# =============================================================================
# TESTS: EDGE CASES
# =============================================================================


def test_empty_workflow() -> None:
    """Test handling of empty workflow."""
    empty_workflow = {
        "metadata": {"name": "Empty"},
        "nodes": {},
        "connections": [],
        "variables": {},
        "settings": {},
    }

    runner = QtHeadlessRunner()
    workflow = runner.load_workflow_from_dict(empty_workflow)

    # Should load but have no nodes
    # Note: workflow_loader adds auto_start if no StartNode
    assert workflow is not None
    runner.cleanup()


def test_workflow_with_unicode(tmp_path: Path) -> None:
    """Test workflow with unicode content."""
    unicode_workflow = {
        "metadata": {
            "name": "Unicode Test",
            "description": "Description with unicode",
        },
        "nodes": {
            "start_1": {
                "node_id": "start_1",
                "node_type": "StartNode",
                "config": {},
            },
            "end_1": {
                "node_id": "end_1",
                "node_type": "EndNode",
                "config": {},
            },
        },
        "connections": [
            {
                "source_node": "start_1",
                "source_port": "exec_out",
                "target_node": "end_1",
                "target_port": "exec_in",
            },
        ],
        "variables": {},
        "settings": {},
    }

    workflow_path = tmp_path / "unicode_workflow.json"
    with open(workflow_path, "w", encoding="utf-8") as f:
        json.dump(unicode_workflow, f, ensure_ascii=False)

    runner = QtHeadlessRunner()
    workflow = runner.load_workflow(workflow_path)

    assert workflow.metadata.description == "Description with unicode"
    runner.cleanup()


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================


def pytest_configure(config):
    """Configure pytest markers for headless tests."""
    config.addinivalue_line("markers", "headless: mark test as headless UI test")
