"""Shared fixtures for orchestrator use case tests.

Provides:
- Mock repositories (AsyncMock)
- Real domain entities (Job, Robot, RobotAssignment, NodeRobotOverride)
- Mock infrastructure services (JobDispatcher)

Following CLAUDE.md Application Layer test rules:
- Mock infrastructure (repos, adapters)
- Use REAL domain objects
- AsyncMock for async infrastructure dependencies
"""

import pytest
from datetime import datetime
from typing import List, Optional, Set
from unittest.mock import AsyncMock, Mock

from casare_rpa.domain.orchestrator.entities.job import Job, JobStatus, JobPriority
from casare_rpa.domain.orchestrator.entities.robot import (
    Robot,
    RobotStatus,
    RobotCapability,
)
from casare_rpa.domain.orchestrator.value_objects.robot_assignment import (
    RobotAssignment,
)
from casare_rpa.domain.orchestrator.value_objects.node_robot_override import (
    NodeRobotOverride,
)
from casare_rpa.domain.orchestrator.services.robot_selection_service import (
    RobotSelectionService,
)


# =============================================================================
# Factory Functions for Real Domain Objects
# =============================================================================


def create_robot(
    robot_id: str = "robot-1",
    name: str = "Test Robot",
    status: RobotStatus = RobotStatus.ONLINE,
    max_concurrent_jobs: int = 5,
    current_job_ids: Optional[List[str]] = None,
    capabilities: Optional[Set[RobotCapability]] = None,
    assigned_workflows: Optional[List[str]] = None,
    environment: str = "default",
    tags: Optional[List[str]] = None,
) -> Robot:
    """Create a real Robot domain entity for testing."""
    return Robot(
        id=robot_id,
        name=name,
        status=status,
        environment=environment,
        max_concurrent_jobs=max_concurrent_jobs,
        current_job_ids=current_job_ids or [],
        capabilities=capabilities or set(),
        assigned_workflows=assigned_workflows or [],
        tags=tags or [],
        last_seen=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )


def create_job(
    job_id: str = "job-1",
    workflow_id: str = "workflow-1",
    workflow_name: str = "Test Workflow",
    robot_id: str = "robot-1",
    robot_name: str = "Test Robot",
    status: JobStatus = JobStatus.PENDING,
    priority: JobPriority = JobPriority.NORMAL,
    workflow_json: str = "{}",
) -> Job:
    """Create a real Job domain entity for testing."""
    return Job(
        id=job_id,
        workflow_id=workflow_id,
        workflow_name=workflow_name,
        robot_id=robot_id,
        robot_name=robot_name,
        status=status,
        priority=priority,
        workflow_json=workflow_json,
        created_at=datetime.utcnow(),
    )


def create_assignment(
    workflow_id: str = "workflow-1",
    robot_id: str = "robot-1",
    is_default: bool = True,
    priority: int = 0,
    notes: Optional[str] = None,
) -> RobotAssignment:
    """Create a real RobotAssignment value object for testing."""
    return RobotAssignment(
        workflow_id=workflow_id,
        robot_id=robot_id,
        is_default=is_default,
        priority=priority,
        created_at=datetime.utcnow(),
        created_by="test",
        notes=notes,
    )


def create_node_override(
    workflow_id: str = "workflow-1",
    node_id: str = "node-1",
    robot_id: Optional[str] = "robot-1",
    required_capabilities: Optional[Set[RobotCapability]] = None,
    reason: Optional[str] = None,
    is_active: bool = True,
) -> NodeRobotOverride:
    """Create a real NodeRobotOverride value object for testing."""
    # Must have either robot_id or required_capabilities
    if robot_id is None and not required_capabilities:
        required_capabilities = {RobotCapability.BROWSER}

    return NodeRobotOverride(
        workflow_id=workflow_id,
        node_id=node_id,
        robot_id=robot_id,
        required_capabilities=frozenset(required_capabilities or set()),
        reason=reason,
        created_at=datetime.utcnow(),
        created_by="test",
        is_active=is_active,
    )


# =============================================================================
# Mock Repository Fixtures
# =============================================================================


@pytest.fixture
def mock_job_repository() -> AsyncMock:
    """Create mock JobRepository with AsyncMock.

    Default behaviors:
    - save(): returns None (successful save)
    - get_by_id(): returns None (not found)
    - get_all(): returns empty list
    """
    mock = AsyncMock()
    mock.save = AsyncMock(return_value=None)
    mock.get_by_id = AsyncMock(return_value=None)
    mock.get_all = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_robot_repository() -> AsyncMock:
    """Create mock RobotRepository with AsyncMock.

    Default behaviors:
    - get_by_id(): returns None (not found)
    - get_all(): returns empty list
    - get_available(): returns empty list
    - get_by_capability(): returns empty list
    - get_by_capabilities(): returns empty list
    - get_by_status(): returns empty list
    - get_by_hostname(): returns None
    """
    mock = AsyncMock()
    mock.get_by_id = AsyncMock(return_value=None)
    mock.get_all = AsyncMock(return_value=[])
    mock.get_available = AsyncMock(return_value=[])
    mock.get_by_capability = AsyncMock(return_value=[])
    mock.get_by_capabilities = AsyncMock(return_value=[])
    mock.get_by_status = AsyncMock(return_value=[])
    mock.get_by_hostname = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def mock_assignment_repository() -> AsyncMock:
    """Create mock WorkflowAssignmentRepository with AsyncMock.

    Default behaviors:
    - get_by_workflow(): returns empty list
    - get_assignment(): returns None
    - get_default_for_workflow(): returns None
    - save(): returns None
    - delete(): returns True
    - set_default(): returns None
    - delete_all_for_robot(): returns 0
    """
    mock = AsyncMock()
    mock.get_by_workflow = AsyncMock(return_value=[])
    mock.get_assignment = AsyncMock(return_value=None)
    mock.get_default_for_workflow = AsyncMock(return_value=None)
    mock.save = AsyncMock(return_value=None)
    mock.delete = AsyncMock(return_value=True)
    mock.set_default = AsyncMock(return_value=None)
    mock.delete_all_for_robot = AsyncMock(return_value=0)
    return mock


@pytest.fixture
def mock_override_repository() -> AsyncMock:
    """Create mock NodeOverrideRepository with AsyncMock.

    Default behaviors:
    - get_by_workflow(): returns empty list
    - get_active_for_workflow(): returns empty list
    - save(): returns None
    - delete(): returns True
    - deactivate(): returns True
    - activate(): returns True
    - delete_all_for_robot(): returns 0
    """
    mock = AsyncMock()
    mock.get_by_workflow = AsyncMock(return_value=[])
    mock.get_active_for_workflow = AsyncMock(return_value=[])
    mock.save = AsyncMock(return_value=None)
    mock.delete = AsyncMock(return_value=True)
    mock.deactivate = AsyncMock(return_value=True)
    mock.activate = AsyncMock(return_value=True)
    mock.delete_all_for_robot = AsyncMock(return_value=0)
    return mock


# =============================================================================
# Mock Service Fixtures
# =============================================================================


@pytest.fixture
def mock_dispatcher() -> Mock:
    """Create mock JobDispatcher.

    Default behaviors:
    - get_robot(): returns None
    - register_robot(): returns None
    - select_robot(): returns robot_id
    """
    mock = Mock()
    mock.get_robot = Mock(return_value=None)
    mock.register_robot = Mock(return_value=None)
    mock.select_robot = Mock(return_value="robot-1")
    return mock


@pytest.fixture
def robot_selection_service() -> RobotSelectionService:
    """Create REAL RobotSelectionService (domain service - no mocking)."""
    return RobotSelectionService()


# =============================================================================
# Convenience Fixtures with Pre-configured Data
# =============================================================================


@pytest.fixture
def available_robot() -> Robot:
    """Create an available robot (online, with capacity)."""
    return create_robot(
        robot_id="robot-available",
        name="Available Robot",
        status=RobotStatus.ONLINE,
        max_concurrent_jobs=5,
        current_job_ids=[],
        capabilities={RobotCapability.BROWSER, RobotCapability.DESKTOP},
    )


@pytest.fixture
def busy_robot() -> Robot:
    """Create a busy robot (online but at capacity)."""
    return create_robot(
        robot_id="robot-busy",
        name="Busy Robot",
        status=RobotStatus.ONLINE,
        max_concurrent_jobs=1,
        current_job_ids=["existing-job"],
    )


@pytest.fixture
def offline_robot() -> Robot:
    """Create an offline robot."""
    return create_robot(
        robot_id="robot-offline",
        name="Offline Robot",
        status=RobotStatus.OFFLINE,
    )


@pytest.fixture
def robot_with_gpu() -> Robot:
    """Create a robot with GPU capability."""
    return create_robot(
        robot_id="robot-gpu",
        name="GPU Robot",
        status=RobotStatus.ONLINE,
        capabilities={RobotCapability.GPU, RobotCapability.BROWSER},
    )


@pytest.fixture
def sample_workflow_data() -> dict:
    """Create sample workflow data for testing."""
    return {
        "metadata": {
            "name": "Test Workflow",
            "description": "Test workflow for unit tests",
            "version": "1.0",
        },
        "nodes": {
            "node-1": {
                "type": "StartNode",
                "position": {"x": 0, "y": 0},
            },
            "node-2": {
                "type": "BrowserNavigateNode",
                "position": {"x": 100, "y": 0},
            },
            "node-3": {
                "type": "EndNode",
                "position": {"x": 200, "y": 0},
            },
        },
        "connections": [
            {"source": "node-1", "target": "node-2"},
            {"source": "node-2", "target": "node-3"},
        ],
        "variables": {},
    }


@pytest.fixture
def sample_workflow_data_with_desktop() -> dict:
    """Create sample workflow with desktop automation nodes."""
    return {
        "metadata": {
            "name": "Desktop Workflow",
            "description": "Workflow requiring desktop capability",
            "version": "1.0",
        },
        "nodes": {
            "node-1": {
                "type": "StartNode",
                "position": {"x": 0, "y": 0},
            },
            "node-2": {
                "type": "DesktopClickNode",
                "position": {"x": 100, "y": 0},
            },
        },
        "connections": [
            {"source": "node-1", "target": "node-2"},
        ],
        "variables": {},
    }


@pytest.fixture
def sample_workflow_data_with_ml() -> dict:
    """Create sample workflow with ML/AI nodes requiring GPU."""
    return {
        "metadata": {
            "name": "ML Workflow",
            "description": "Workflow requiring GPU capability",
            "version": "1.0",
        },
        "nodes": {
            "node-1": {
                "type": "LLMPromptNode",
                "position": {"x": 0, "y": 0},
            },
        },
        "connections": [],
        "variables": {},
    }
