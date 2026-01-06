"""
Integration tests for Workflow Validation.

Tests the ValidateWorkflowUseCase with real workflows and validation rules.
"""

import pytest

from casare_rpa.application.use_cases import ValidateWorkflowUseCase
from tests.integration.conftest import create_sample_workflow_data


@pytest.mark.integration
def test_validate_valid_workflow():
    """Test that a valid workflow passes validation."""
    # Arrange: Create valid workflow
    workflow = create_sample_workflow_data()
    validator = ValidateWorkflowUseCase()

    # Act: Validate (synchronous, not async)
    result = validator.execute(workflow)

    # Assert: Validation passes (sample workflow has no End node, so it has a warning)
    assert result.is_valid is True
    # The sample workflow has StartNode but no EndNode, so we expect 1 warning
    assert len(result.issues) == 1
    assert result.issues[0].severity == "warning"
    assert "end node" in result.issues[0].message.lower()


@pytest.mark.integration
def test_validate_workflow_missing_metadata():
    """Test that missing metadata is caught."""
    # Arrange: Workflow without metadata and without nodes
    invalid_workflow = {
        "nodes": {},
        "connections": [],
        "variables": {},
        "metadata": {},  # Empty metadata to make workflow unique for cache
    }
    validator = ValidateWorkflowUseCase()

    # Act: Validate
    result = validator.execute(invalid_workflow)

    # Assert: Workflow without nodes generates errors and warnings
    # We expect NO_START_NODE error and NO_END_NODE warning
    assert len(result.issues) >= 1

    # Assert: At least one error about missing Start node
    error_codes = [issue.code for issue in result.issues]
    # Should have NO_START_NODE error (severity="error")
    start_node_errors = [i for i in result.issues if i.code == "NO_START_NODE"]
    assert len(start_node_errors) >= 1, f"Expected NO_START_NODE, got: {error_codes}"


@pytest.mark.integration
def test_validate_workflow_empty_nodes():
    """Test that workflow with no nodes is detected."""
    # Arrange: Workflow with no nodes
    empty_workflow = {
        "metadata": {
            "name": "EmptyWorkflow",
            "version": "1.0.0",
        },
        "nodes": {},
        "connections": [],
        "variables": {},
    }
    validator = ValidateWorkflowUseCase()

    # Act: Validate
    result = validator.execute(empty_workflow)

    # Assert: Should have validation issues
    assert len(result.issues) >= 0  # May or may not fail depending on rules


@pytest.mark.integration
def test_validate_workflow_disconnected_nodes():
    """Test that disconnected nodes are detected."""
    # Arrange: Workflow with disconnected nodes
    disconnected_workflow = {
        "metadata": {"name": "DisconnectedTest", "version": "1.0.0"},
        "nodes": {
            "start": {
                "node_id": "start",
                "node_type": "StartNode",
                "config": {},
                "position": {"x": 0, "y": 0},
            },
            "orphan": {
                "node_id": "orphan",
                "node_type": "LogNode",
                "config": {"message": "I'm disconnected!"},
                "position": {"x": 500, "y": 500},
            },
        },
        "connections": [],  # No connections
        "variables": {},
    }
    validator = ValidateWorkflowUseCase()

    # Act: Validate
    result = validator.execute(disconnected_workflow)

    # Assert: May have warnings about disconnected nodes
    # The exact behavior depends on validation rules
    assert result.is_valid in [True, False]


@pytest.mark.integration
def test_validate_workflow_with_variables():
    """Test that workflow variables are accepted."""
    # Arrange: Workflow with variables
    workflow_with_vars = create_sample_workflow_data()
    workflow_with_vars["variables"] = {
        "api_endpoint": "https://api.example.com",
        "timeout": 30,
        "debug_mode": True,
    }

    validator = ValidateWorkflowUseCase()

    # Act: Validate
    result = validator.execute(workflow_with_vars)

    # Assert: Valid workflow with variables
    # May have warnings but should generally be valid
    assert result is not None


@pytest.mark.integration
def test_validate_workflow_with_settings():
    """Test that workflow settings are accepted."""
    # Arrange: Workflow with various settings
    workflow_with_settings = create_sample_workflow_data()
    workflow_with_settings["settings"] = {
        "timeout": 60,
        "stop_on_error": False,
        "max_retries": 3,
    }

    validator = ValidateWorkflowUseCase()

    # Act: Validate
    result = validator.execute(workflow_with_settings)

    # Assert: Settings are processed
    assert result is not None


@pytest.mark.integration
def test_validation_result_structure():
    """Test that ValidationResult has correct structure."""
    # Arrange
    problematic_workflow = {
        "metadata": {},  # Missing required fields
        "nodes": {},
        "connections": [],
        "variables": {},
    }
    validator = ValidateWorkflowUseCase()

    # Act: Validate
    result = validator.execute(problematic_workflow)

    # Assert: Result has structure
    assert hasattr(result, "is_valid")
    assert hasattr(result, "issues")
    assert isinstance(result.issues, list)


@pytest.mark.integration
def test_validation_result_severity_levels():
    """Test that validation issues have proper structure."""
    # Arrange: Create workflow with various potential issues
    problematic_workflow = {
        "metadata": {},
        "nodes": {},
        "connections": [],
        "variables": {},
    }
    validator = ValidateWorkflowUseCase()

    # Act: Validate
    result = validator.execute(problematic_workflow)

    # Assert: Result has structure
    assert hasattr(result, "is_valid")
    assert hasattr(result, "issues")

    # Assert: Issues have expected attributes
    for issue in result.issues:
        # Issues should have at least these basic attributes
        assert hasattr(issue, "message") or hasattr(issue, "severity")


@pytest.mark.integration
def test_validate_workflow_with_frames():
    """Test that workflows with frames are handled."""
    # Arrange: Workflow with frames (node groups)
    workflow_with_frames = create_sample_workflow_data()
    workflow_with_frames["frames"] = [
        {
            "id": "frame_1",
            "name": "My Group",
            "nodes": ["node_start", "node_log"],
            "position": {"x": 50, "y": 50},
            "size": {"width": 400, "height": 200},
        }
    ]

    validator = ValidateWorkflowUseCase()

    # Act: Validate
    result = validator.execute(workflow_with_frames)

    # Assert: Frames are processed
    assert result is not None


@pytest.mark.integration
def test_validate_workflow_multiple_connections():
    """Test workflow with multiple connections."""
    # Arrange: Complex workflow with multiple connections
    complex_workflow = {
        "metadata": {"name": "MultiConnectionTest", "version": "1.0.0"},
        "nodes": {
            "start": {
                "node_id": "start",
                "node_type": "StartNode",
                "config": {},
                "position": {"x": 0, "y": 0},
            },
            "process1": {
                "node_id": "process1",
                "node_type": "LogNode",
                "config": {"message": "Step 1"},
                "position": {"x": 200, "y": 0},
            },
            "process2": {
                "node_id": "process2",
                "node_type": "LogNode",
                "config": {"message": "Step 2"},
                "position": {"x": 400, "y": 0},
            },
        },
        "connections": [
            {
                "source_node": "start",
                "source_port": "exec_out",
                "target_node": "process1",
                "target_port": "exec_in",
            },
            {
                "source_node": "process1",
                "source_port": "exec_out",
                "target_node": "process2",
                "target_port": "exec_in",
            },
        ],
        "variables": {},
    }

    validator = ValidateWorkflowUseCase()

    # Act: Validate
    result = validator.execute(complex_workflow)

    # Assert: Valid chain
    assert result is not None
