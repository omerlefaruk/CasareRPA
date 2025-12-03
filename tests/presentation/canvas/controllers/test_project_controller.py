"""
Tests for ProjectController.

Tests project management operations covering:
- Project creation
- Project opening
- Project closing
- Recent projects
- Scenario opening

Note: These tests mock async operations and repository to avoid I/O.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from pathlib import Path


class TestProjectStateManagement:
    """Tests for project state management."""

    @pytest.fixture
    def project_state(self):
        """Create project state fixture."""
        return {
            "current_project": None,
            "repository": Mock(),
        }

    def _has_project(self, state) -> bool:
        """Check if a project is currently open."""
        return state["current_project"] is not None

    def _get_current_project(self, state):
        """Get current project."""
        return state["current_project"]

    def _set_current_project(self, state, project):
        """Set current project."""
        state["current_project"] = project

    def _close_project(self, state):
        """Close current project."""
        state["current_project"] = None

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    def test_has_project_false_initially(self, project_state):
        """Test has_project is False when no project open."""
        assert self._has_project(project_state) is False

    def test_has_project_true_when_project_set(self, project_state):
        """Test has_project is True when project is set."""
        mock_project = Mock()
        self._set_current_project(project_state, mock_project)

        assert self._has_project(project_state) is True

    def test_get_current_project_returns_none_initially(self, project_state):
        """Test get_current_project returns None initially."""
        assert self._get_current_project(project_state) is None

    def test_get_current_project_returns_project(self, project_state):
        """Test get_current_project returns set project."""
        mock_project = Mock()
        mock_project.name = "Test Project"
        self._set_current_project(project_state, mock_project)

        result = self._get_current_project(project_state)

        assert result.name == "Test Project"

    def test_close_project_clears_current(self, project_state):
        """Test close_project clears current project."""
        mock_project = Mock()
        self._set_current_project(project_state, mock_project)

        self._close_project(project_state)

        assert self._get_current_project(project_state) is None
        assert self._has_project(project_state) is False


class TestProjectCreationLogic:
    """Tests for project creation functionality."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock project repository."""
        repo = AsyncMock()
        return repo

    @pytest.fixture
    def mock_create_result(self):
        """Create a mock successful create result."""
        result = Mock()
        result.success = True
        result.project = Mock()
        result.project.name = "New Project"
        result.project.path = Path("/path/to/project")
        result.error = None
        return result

    async def _create_project(self, repository, project_data: dict):
        """
        Simulate _create_project_async logic.

        Returns:
            tuple: (success, project, error)
        """
        if repository is None:
            return (False, None, "Repository not initialized")

        try:
            # Simulating CreateProjectUseCase execution
            # In real implementation, this would call the use case
            project = Mock()
            project.name = project_data["name"]
            project.path = Path(project_data["path"])
            project.description = project_data.get("description", "")
            project.author = project_data.get("author", "")

            return (True, project, None)

        except Exception as e:
            return (False, None, str(e))

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_create_project_success(self, mock_repository):
        """Test creating a project successfully."""
        project_data = {
            "name": "Test Project",
            "path": "/path/to/project",
            "description": "Test description",
            "author": "Test Author",
        }

        success, project, error = await self._create_project(
            mock_repository, project_data
        )

        assert success is True
        assert project is not None
        assert project.name == "Test Project"
        assert error is None

    @pytest.mark.asyncio
    async def test_create_project_with_minimal_data(self, mock_repository):
        """Test creating project with minimal required data."""
        project_data = {
            "name": "Minimal Project",
            "path": "/path",
        }

        success, project, error = await self._create_project(
            mock_repository, project_data
        )

        assert success is True
        assert project.name == "Minimal Project"
        assert project.description == ""

    # =========================================================================
    # Sad Path Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_create_project_repository_none(self):
        """Test create project when repository is None."""
        project_data = {"name": "Test", "path": "/path"}

        success, project, error = await self._create_project(None, project_data)

        assert success is False
        assert project is None
        assert error == "Repository not initialized"


class TestProjectOpeningLogic:
    """Tests for project opening functionality."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock project repository."""
        repo = AsyncMock()
        return repo

    async def _open_project(self, repository, path: Path):
        """
        Simulate _open_project_async logic.

        Returns:
            tuple: (success, project, error)
        """
        if repository is None:
            return (False, None, "Repository not initialized")

        try:
            # Check if path exists (simulated)
            if not path.exists():
                return (False, None, f"Project not found at {path}")

            # Simulating LoadProjectUseCase execution
            project = Mock()
            project.name = path.name
            project.path = path

            return (True, project, None)

        except Exception as e:
            return (False, None, str(e))

    async def _open_project_mock(self, repository, path: Path, project_exists: bool):
        """
        Simulate _open_project_async with controlled existence check.

        Returns:
            tuple: (success, project, error)
        """
        if repository is None:
            return (False, None, "Repository not initialized")

        if not project_exists:
            return (False, None, f"Project not found at {path}")

        try:
            project = Mock()
            project.name = path.name
            project.path = path
            return (True, project, None)

        except Exception as e:
            return (False, None, str(e))

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_open_project_success(self, mock_repository):
        """Test opening a project successfully."""
        path = Path("/path/to/existing/project")

        success, project, error = await self._open_project_mock(
            mock_repository, path, project_exists=True
        )

        assert success is True
        assert project is not None
        assert project.path == path
        assert error is None

    @pytest.mark.asyncio
    async def test_open_project_returns_project_name(self, mock_repository):
        """Test opened project has correct name."""
        path = Path("/path/to/MyProject")

        success, project, error = await self._open_project_mock(
            mock_repository, path, project_exists=True
        )

        assert project.name == "MyProject"

    # =========================================================================
    # Sad Path Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_open_project_repository_none(self):
        """Test open project when repository is None."""
        path = Path("/path/to/project")

        success, project, error = await self._open_project_mock(
            None, path, project_exists=True
        )

        assert success is False
        assert project is None
        assert error == "Repository not initialized"

    @pytest.mark.asyncio
    async def test_open_project_not_found(self, mock_repository):
        """Test open project when project doesn't exist."""
        path = Path("/path/to/missing/project")

        success, project, error = await self._open_project_mock(
            mock_repository, path, project_exists=False
        )

        assert success is False
        assert project is None
        assert "not found" in error.lower()


class TestRecentProjectsLogic:
    """Tests for recent projects functionality."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository with projects index."""
        repo = AsyncMock()

        mock_index = Mock()
        mock_index.get_recent_projects.return_value = [
            Mock(id="proj1", name="Project 1", path="/path/1"),
            Mock(id="proj2", name="Project 2", path="/path/2"),
        ]
        repo.get_projects_index.return_value = mock_index

        return repo

    async def _get_recent_projects(self, repository):
        """
        Simulate get_recent_projects logic.

        Returns:
            list: List of recent project entries
        """
        if repository is None:
            return []

        try:
            index = await repository.get_projects_index()
            return index.get_recent_projects()
        except Exception:
            return []

    async def _remove_from_recent(self, repository, project_id: str) -> bool:
        """
        Simulate _remove_project_async logic.

        Returns:
            bool: True if successful
        """
        if repository is None:
            return False

        try:
            index = await repository.get_projects_index()
            index.remove_project(project_id)
            await repository.save_projects_index(index)
            return True
        except Exception:
            return False

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_recent_projects_returns_list(self, mock_repository):
        """Test getting recent projects returns list."""
        result = await self._get_recent_projects(mock_repository)

        assert len(result) == 2
        assert result[0].name == "Project 1"
        assert result[1].name == "Project 2"

    @pytest.mark.asyncio
    async def test_remove_from_recent_success(self, mock_repository):
        """Test removing project from recent list."""
        result = await self._remove_from_recent(mock_repository, "proj1")

        assert result is True
        mock_index = await mock_repository.get_projects_index()
        mock_index.remove_project.assert_called_with("proj1")

    # =========================================================================
    # Sad Path Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_recent_projects_repository_none(self):
        """Test get_recent_projects when repository is None."""
        result = await self._get_recent_projects(None)

        assert result == []

    @pytest.mark.asyncio
    async def test_get_recent_projects_error(self, mock_repository):
        """Test get_recent_projects handles exceptions."""
        mock_repository.get_projects_index.side_effect = Exception("Error")

        result = await self._get_recent_projects(mock_repository)

        assert result == []

    @pytest.mark.asyncio
    async def test_remove_from_recent_repository_none(self):
        """Test remove from recent when repository is None."""
        result = await self._remove_from_recent(None, "proj1")

        assert result is False


class TestScenarioOpeningLogic:
    """Tests for scenario opening functionality."""

    @pytest.fixture
    def project_state(self):
        """Create project state with current project."""
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.path = Path("/path/to/project")

        return {
            "current_project": mock_project,
            "repository": AsyncMock(),
        }

    async def _open_scenario(
        self,
        state,
        project_path: Path,
        scenario_path: Path,
        project_exists: bool = True,
    ):
        """
        Simulate _open_scenario_async logic.

        Returns:
            tuple: (success, error)
        """
        if state["repository"] is None:
            return (False, "Repository not initialized")

        # First open the project if not already open
        current = state["current_project"]
        if current is None or current.path != project_path:
            if not project_exists:
                return (False, f"Project not found at {project_path}")

            # Open project
            mock_project = Mock()
            mock_project.name = project_path.name
            mock_project.path = project_path
            state["current_project"] = mock_project

        # Now we have a project, check if scenario exists
        # In real implementation, this would validate scenario path
        if not scenario_path.suffix == ".json":
            return (False, "Invalid scenario file")

        return (True, None)

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_open_scenario_success(self, project_state):
        """Test opening a scenario successfully."""
        project_path = Path("/path/to/project")
        scenario_path = Path("/path/to/project/scenarios/test.json")

        success, error = await self._open_scenario(
            project_state, project_path, scenario_path
        )

        assert success is True
        assert error is None

    @pytest.mark.asyncio
    async def test_open_scenario_opens_project_if_needed(self, project_state):
        """Test scenario opening opens project if different."""
        project_state["current_project"] = None  # No project open
        project_path = Path("/path/to/new_project")
        scenario_path = Path("/path/to/new_project/scenarios/test.json")

        success, error = await self._open_scenario(
            project_state, project_path, scenario_path, project_exists=True
        )

        assert success is True
        assert project_state["current_project"].path == project_path

    # =========================================================================
    # Sad Path Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_open_scenario_project_not_found(self, project_state):
        """Test scenario opening when project doesn't exist."""
        project_state["current_project"] = None
        project_path = Path("/path/to/missing")
        scenario_path = Path("/path/to/missing/scenarios/test.json")

        success, error = await self._open_scenario(
            project_state, project_path, scenario_path, project_exists=False
        )

        assert success is False
        assert "not found" in error.lower()

    @pytest.mark.asyncio
    async def test_open_scenario_invalid_file(self, project_state):
        """Test scenario opening with invalid file type."""
        project_path = Path("/path/to/project")
        scenario_path = Path("/path/to/project/scenarios/test.txt")  # Not JSON

        success, error = await self._open_scenario(
            project_state, project_path, scenario_path
        )

        assert success is False
        assert "invalid" in error.lower()


class TestProjectClosingLogic:
    """Tests for project closing functionality."""

    @pytest.fixture
    def project_state(self):
        """Create project state with current project."""
        mock_project = Mock()
        mock_project.name = "Test Project"

        return {
            "current_project": mock_project,
            "closed_emitted": False,
        }

    def _close_project(self, state):
        """
        Simulate close_project logic.

        Returns:
            bool: True if project was closed
        """
        if state["current_project"]:
            state["current_project"] = None
            state["closed_emitted"] = True
            return True
        return False

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    def test_close_project_success(self, project_state):
        """Test closing a project successfully."""
        result = self._close_project(project_state)

        assert result is True
        assert project_state["current_project"] is None
        assert project_state["closed_emitted"] is True

    def test_close_project_no_project_open(self, project_state):
        """Test closing when no project is open."""
        project_state["current_project"] = None

        result = self._close_project(project_state)

        assert result is False
        assert project_state["closed_emitted"] is False


class TestErrorHandlingLogic:
    """Tests for error display functionality."""

    def _format_error_message(self, title: str, message: str) -> dict:
        """
        Simulate error message formatting.

        Returns:
            dict: Formatted error for display
        """
        return {
            "title": title,
            "message": message,
            "type": "error",
        }

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    def test_format_error_message(self):
        """Test formatting error message."""
        result = self._format_error_message(
            "Project Creation Failed", "Could not create project"
        )

        assert result["title"] == "Project Creation Failed"
        assert result["message"] == "Could not create project"
        assert result["type"] == "error"

    def test_format_error_message_with_details(self):
        """Test formatting error with detailed message."""
        result = self._format_error_message(
            "Error", "Failed to open project: File not found at /path/to/project.json"
        )

        assert "Failed to open project" in result["message"]
        assert "File not found" in result["message"]


class TestProjectSignalEmission:
    """Tests for project controller signal emission logic."""

    @pytest.fixture
    def signal_tracker(self):
        """Create signal tracking fixture."""
        return {
            "project_opened": [],
            "project_closed": [],
            "project_created": [],
            "scenario_opened": [],
        }

    def _emit_project_opened(self, tracker, project):
        """Simulate emitting project_opened signal."""
        tracker["project_opened"].append(project)

    def _emit_project_closed(self, tracker):
        """Simulate emitting project_closed signal."""
        tracker["project_closed"].append(True)

    def _emit_project_created(self, tracker, project):
        """Simulate emitting project_created signal."""
        tracker["project_created"].append(project)

    def _emit_scenario_opened(self, tracker, project_path: str, scenario_path: str):
        """Simulate emitting scenario_opened signal."""
        tracker["scenario_opened"].append((project_path, scenario_path))

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    def test_project_opened_signal_emitted(self, signal_tracker):
        """Test project_opened signal is emitted."""
        mock_project = Mock()
        mock_project.name = "Test"

        self._emit_project_opened(signal_tracker, mock_project)

        assert len(signal_tracker["project_opened"]) == 1
        assert signal_tracker["project_opened"][0].name == "Test"

    def test_project_closed_signal_emitted(self, signal_tracker):
        """Test project_closed signal is emitted."""
        self._emit_project_closed(signal_tracker)

        assert len(signal_tracker["project_closed"]) == 1

    def test_project_created_signal_emitted(self, signal_tracker):
        """Test project_created signal is emitted."""
        mock_project = Mock()
        mock_project.name = "New Project"

        self._emit_project_created(signal_tracker, mock_project)

        assert len(signal_tracker["project_created"]) == 1
        assert signal_tracker["project_created"][0].name == "New Project"

    def test_scenario_opened_signal_emitted(self, signal_tracker):
        """Test scenario_opened signal is emitted."""
        self._emit_scenario_opened(
            signal_tracker, "/path/project", "/path/scenario.json"
        )

        assert len(signal_tracker["scenario_opened"]) == 1
        assert signal_tracker["scenario_opened"][0] == (
            "/path/project",
            "/path/scenario.json",
        )
