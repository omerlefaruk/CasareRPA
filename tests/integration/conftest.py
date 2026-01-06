"""
Shared fixtures for high-level integration tests.

Provides sandboxed test environments with isolated file systems
and real module instances (not mocks).
"""

import os
import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest

from casare_rpa.application.dependency_injection import DIContainer
from casare_rpa.config import reset_app_config
from casare_rpa.domain.events import EventBus, get_event_bus
from casare_rpa.domain.events.bus import reset_event_bus
from casare_rpa.infrastructure.persistence.file_system_project_repository import (
    FileSystemProjectRepository,
)

# =============================================================================
# Test Sandbox Fixtures
# =============================================================================


@pytest.fixture
def integration_sandbox(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Create an isolated sandbox directory for integration tests.

    All file operations (projects, workflows, settings) are redirected
    to this temporary directory to avoid polluting the user's actual
    config directory.

    Yields:
        Path to sandbox directory
    """
    sandbox = tmp_path / "casare_rpa_sandbox"
    sandbox.mkdir()

    # Create subdirectories matching real structure
    (sandbox / "config").mkdir()
    (sandbox / "config" / "projects").mkdir()
    (sandbox / "workflows").mkdir()
    (sandbox / "logs").mkdir()

    yield sandbox

    # Cleanup is handled by tmp_path fixture


@pytest.fixture
def sandbox_config(integration_sandbox: Path) -> Generator[dict, None, None]:
    """
    Provide sandboxed configuration values.

    Monkey-patch environment variables to redirect paths to sandbox.
    """
    from casare_rpa.config import paths
    from casare_rpa.infrastructure.persistence import project_storage

    # Store original values
    original_project_root = paths.PROJECT_ROOT
    original_config_dir = paths.CONFIG_DIR
    original_projects_dir = paths.PROJECTS_DIR
    original_projects_index = paths.PROJECTS_INDEX_FILE
    original_workflows_dir = paths.WORKFLOWS_DIR
    original_globals = paths.GLOBAL_VARIABLES_FILE
    original_global_creds = paths.GLOBAL_CREDENTIALS_FILE

    # Store original project_storage module references
    original_storage_index = project_storage.PROJECTS_INDEX_FILE
    original_storage_globals = project_storage.GLOBAL_VARIABLES_FILE
    original_storage_creds = project_storage.GLOBAL_CREDENTIALS_FILE

    # Create sandbox config
    config_dir = integration_sandbox / "config"
    projects_dir = config_dir / "projects"
    workflows_dir = integration_sandbox / "workflows"
    projects_index_file = projects_dir / "projects_index.json"

    # Monkey-patch paths module constants
    paths.PROJECT_ROOT = integration_sandbox
    paths.CONFIG_DIR = config_dir
    paths.PROJECTS_DIR = projects_dir
    paths.PROJECTS_INDEX_FILE = projects_index_file
    paths.WORKFLOWS_DIR = workflows_dir
    paths.GLOBAL_VARIABLES_FILE = config_dir / "global_variables.json"
    paths.GLOBAL_CREDENTIALS_FILE = config_dir / "global_credentials.json"

    # Also patch project_storage module references (imported at module level)
    project_storage.PROJECTS_INDEX_FILE = projects_index_file
    project_storage.GLOBAL_VARIABLES_FILE = paths.GLOBAL_VARIABLES_FILE
    project_storage.GLOBAL_CREDENTIALS_FILE = paths.GLOBAL_CREDENTIALS_FILE

    yield {
        "sandbox_root": integration_sandbox,
        "config_dir": config_dir,
        "projects_dir": projects_dir,
        "workflows_dir": workflows_dir,
        "projects_index": projects_index_file,
        "global_variables": paths.GLOBAL_VARIABLES_FILE,
        "global_credentials": paths.GLOBAL_CREDENTIALS_FILE,
    }

    # Restore original values
    paths.PROJECT_ROOT = original_project_root
    paths.CONFIG_DIR = original_config_dir
    paths.PROJECTS_DIR = original_projects_dir
    paths.PROJECTS_INDEX_FILE = original_projects_index
    paths.WORKFLOWS_DIR = original_workflows_dir
    paths.GLOBAL_VARIABLES_FILE = original_globals
    paths.GLOBAL_CREDENTIALS_FILE = original_global_creds

    # Restore project_storage module references
    project_storage.PROJECTS_INDEX_FILE = original_storage_index
    project_storage.GLOBAL_VARIABLES_FILE = original_storage_globals
    project_storage.GLOBAL_CREDENTIALS_FILE = original_storage_creds


# =============================================================================
# Repository Fixtures (Real Instances, Sandbox Storage)
# =============================================================================


@pytest.fixture
def sandbox_project_repository(sandbox_config: dict) -> FileSystemProjectRepository:
    """
    Create a real ProjectRepository with sandboxed storage.

    Uses actual FileSystemProjectRepository which uses global paths.
    The sandbox_config fixture redirects global paths to the sandbox.
    """
    # FileSystemProjectRepository has no-arg __init__ and uses global paths
    # from casare_rpa.config.paths which are redirected by sandbox_config
    return FileSystemProjectRepository()


# =============================================================================
# Event Bus Fixtures
# =============================================================================


@pytest.fixture
def fresh_event_bus() -> Generator[EventBus, None, None]:
    """
    Provide a fresh EventBus for each test.

    Ensures events from previous tests don't leak.
    """
    reset_event_bus()
    bus = get_event_bus()
    yield bus
    reset_event_bus()


# =============================================================================
# Minimal Sample Data Factories
# =============================================================================


def create_sample_workflow_data() -> dict:
    """
    Create minimal valid workflow data for testing.

    Returns:
        Workflow data dict matching WorkflowSchema format
    """
    return {
        "metadata": {
            "name": "TestWorkflow",
            "description": "Integration test workflow",
            "version": "1.0.0",
            "author": "IntegrationTest",
            "created_at": "2025-01-01T00:00:00",
            "modified_at": "2025-01-01T00:00:00",
        },
        "nodes": {
            "node_start": {
                "node_id": "node_start",
                "node_type": "StartNode",
                "config": {},
                "position": {"x": 100, "y": 100},
            },
            "node_log": {
                "node_id": "node_log",
                "node_type": "LogNode",
                "config": {"message": "Hello from integration test!"},
                "position": {"x": 300, "y": 100},
            },
        },
        "connections": [
            {
                "source_node": "node_start",
                "source_port": "exec_out",
                "target_node": "node_log",
                "target_port": "exec_in",
            }
        ],
        "variables": {},
        "frames": [],
        "settings": {
            "timeout": 30,
            "stop_on_error": True,
        },
    }


def create_sample_project_data(name: str = "TestProject") -> dict:
    """
    Create minimal valid project data for testing.

    Args:
        name: Project name

    Returns:
        Project data dict
    """
    return {
        "id": "proj_test_001",
        "name": name,
        "description": "Integration test project",
        "author": "IntegrationTest",
        "tags": ["test", "integration"],
        "created_at": "2025-01-01T00:00:00",
        "modified_at": "2025-01-01T00:00:00",
        "last_opened": "2025-01-01T00:00:00",
        "scenarios": [],
    }


@pytest.fixture
def sample_workflow() -> dict:
    """Provide sample workflow data."""
    return create_sample_workflow_data()


@pytest.fixture
def sample_project() -> dict:
    """Provide sample project data."""
    return create_sample_project_data()


# =============================================================================
# Helper: Write workflow file to sandbox
# =============================================================================


@pytest.fixture
def write_workflow_to_sandbox(sandbox_config: dict):
    """
    Helper function to write workflow JSON to sandbox.

    Returns a function that takes workflow data and filename.
    """

    def _writer(workflow_data: dict, filename: str = "test_workflow.json") -> Path:
        """Write workflow data to sandbox workflows directory."""
        import orjson

        target_path = sandbox_config["workflows_dir"] / filename
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(orjson.dumps(workflow_data, option=orjson.OPT_INDENT_2))
        return target_path

    return _writer


@pytest.fixture(autouse=True)
def clear_validator_cache():
    """
    Clear ValidateWorkflowUseCase cache before each test.

    The validator has a class-level cache that can interfere with tests
    that use similar workflow structures.
    """
    from casare_rpa.application.use_cases import ValidateWorkflowUseCase

    ValidateWorkflowUseCase._cache.clear()
    ValidateWorkflowUseCase._cache_hits = 0
    ValidateWorkflowUseCase._cache_misses = 0
    yield
    # Clear after test as well
    ValidateWorkflowUseCase._cache.clear()
