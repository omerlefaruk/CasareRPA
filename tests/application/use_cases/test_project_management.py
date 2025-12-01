"""Tests for project management use cases."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from casare_rpa.domain.entities.project import (
    Project,
    Scenario,
    ProjectsIndex,
    ProjectIndexEntry,
    VariablesFile,
    CredentialBindingsFile,
    VariableScope,
)
from casare_rpa.domain.repositories import ProjectRepository
from casare_rpa.application.use_cases import (
    CreateProjectUseCase,
    LoadProjectUseCase,
    SaveProjectUseCase,
    ListProjectsUseCase,
    DeleteProjectUseCase,
    CreateScenarioUseCase,
    LoadScenarioUseCase,
    SaveScenarioUseCase,
    DeleteScenarioUseCase,
    ListScenariosUseCase,
    ProjectResult,
    ScenarioResult,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_repository():
    """Create a mock project repository."""
    repo = AsyncMock(spec=ProjectRepository)
    repo.get_projects_index = AsyncMock(return_value=ProjectsIndex())
    repo.save_projects_index = AsyncMock()
    return repo


@pytest.fixture
def sample_project():
    """Create a sample project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Project.create_new(
            name="Test Project",
            path=Path(tmpdir),
            description="A test project",
            author="Test Author",
            tags=["test", "sample"],
        )
        yield project


@pytest.fixture
def sample_scenario():
    """Create a sample scenario."""
    return Scenario.create_new(
        name="Test Scenario",
        project_id="proj_12345678",
        workflow={"nodes": [], "connections": []},
        tags=["test"],
    )


# =============================================================================
# CreateProjectUseCase Tests
# =============================================================================


class TestCreateProjectUseCase:
    """Tests for CreateProjectUseCase."""

    @pytest.mark.asyncio
    async def test_create_project_success(self, mock_repository):
        """Test successful project creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "new_project"

            mock_repository.get_by_path = AsyncMock(return_value=None)
            mock_repository.save = AsyncMock()

            use_case = CreateProjectUseCase(mock_repository)
            result = await use_case.execute(
                name="New Project",
                path=project_path,
                description="A new project",
                author="Test Author",
            )

            assert result.success is True
            assert result.project is not None
            assert result.project.name == "New Project"
            assert result.error is None
            mock_repository.save.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_project_already_exists(self, mock_repository):
        """Test creating project in existing project folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a project path that exists and has content
            project_path = Path(tmpdir)
            # Add a file so the directory is not empty
            (project_path / "project.json").touch()

            existing_project = Project.create_new(name="Existing", path=project_path)

            mock_repository.get_by_path = AsyncMock(return_value=existing_project)

            use_case = CreateProjectUseCase(mock_repository)
            result = await use_case.execute(
                name="New Project",
                path=project_path,
            )

            assert result.success is False
            assert "already exists" in result.error

    @pytest.mark.asyncio
    async def test_create_project_directory_not_empty(self, mock_repository):
        """Test creating project in non-empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file to make directory non-empty
            (Path(tmpdir) / "existing_file.txt").touch()

            mock_repository.get_by_path = AsyncMock(return_value=None)

            use_case = CreateProjectUseCase(mock_repository)
            result = await use_case.execute(
                name="New Project",
                path=Path(tmpdir),
            )

            assert result.success is False
            assert "not empty" in result.error


# =============================================================================
# LoadProjectUseCase Tests
# =============================================================================


class TestLoadProjectUseCase:
    """Tests for LoadProjectUseCase."""

    @pytest.mark.asyncio
    async def test_load_project_by_id_success(self, mock_repository, sample_project):
        """Test loading project by ID."""
        mock_repository.get_by_id = AsyncMock(return_value=sample_project)
        mock_repository.update_project_opened = AsyncMock()

        use_case = LoadProjectUseCase(mock_repository)
        result = await use_case.execute(project_id=sample_project.id)

        assert result.success is True
        assert result.project.id == sample_project.id
        mock_repository.update_project_opened.assert_awaited_once_with(
            sample_project.id
        )

    @pytest.mark.asyncio
    async def test_load_project_by_path_success(self, mock_repository, sample_project):
        """Test loading project by path."""
        mock_repository.get_by_path = AsyncMock(return_value=sample_project)
        mock_repository.update_project_opened = AsyncMock()

        use_case = LoadProjectUseCase(mock_repository)
        result = await use_case.execute(path=sample_project.path)

        assert result.success is True
        assert result.project.name == sample_project.name

    @pytest.mark.asyncio
    async def test_load_project_not_found(self, mock_repository):
        """Test loading non-existent project."""
        mock_repository.get_by_id = AsyncMock(return_value=None)

        use_case = LoadProjectUseCase(mock_repository)
        result = await use_case.execute(project_id="proj_nonexistent")

        assert result.success is False
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_load_project_no_identifier(self, mock_repository):
        """Test loading without ID or path."""
        use_case = LoadProjectUseCase(mock_repository)
        result = await use_case.execute()

        assert result.success is False
        assert "must be provided" in result.error


# =============================================================================
# SaveProjectUseCase Tests
# =============================================================================


class TestSaveProjectUseCase:
    """Tests for SaveProjectUseCase."""

    @pytest.mark.asyncio
    async def test_save_project_success(self, mock_repository, sample_project):
        """Test saving project."""
        mock_repository.save = AsyncMock()

        use_case = SaveProjectUseCase(mock_repository)
        result = await use_case.execute(sample_project)

        assert result.success is True
        assert result.project == sample_project
        mock_repository.save.assert_awaited_once_with(sample_project)

    @pytest.mark.asyncio
    async def test_save_project_error(self, mock_repository, sample_project):
        """Test save with error."""
        mock_repository.save = AsyncMock(side_effect=Exception("Write error"))

        use_case = SaveProjectUseCase(mock_repository)
        result = await use_case.execute(sample_project)

        assert result.success is False
        assert "Write error" in result.error


# =============================================================================
# ListProjectsUseCase Tests
# =============================================================================


class TestListProjectsUseCase:
    """Tests for ListProjectsUseCase."""

    @pytest.mark.asyncio
    async def test_list_projects_empty(self, mock_repository):
        """Test listing empty projects."""
        mock_repository.get_all = AsyncMock(return_value=[])

        use_case = ListProjectsUseCase(mock_repository)
        result = await use_case.execute()

        assert result.success is True
        assert result.projects == []

    @pytest.mark.asyncio
    async def test_list_projects_with_results(self, mock_repository):
        """Test listing multiple projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            projects = [
                Project.create_new(name="Project A", path=Path(tmpdir) / "a"),
                Project.create_new(name="Project B", path=Path(tmpdir) / "b"),
            ]
            mock_repository.get_all = AsyncMock(return_value=projects)

            # Mock index for sorting - use the correct API
            index = ProjectsIndex()
            for p in projects:
                index.add_project(p)
            mock_repository.get_projects_index = AsyncMock(return_value=index)

            use_case = ListProjectsUseCase(mock_repository)
            result = await use_case.execute()

            assert result.success is True
            assert len(result.projects) == 2

    @pytest.mark.asyncio
    async def test_list_projects_with_limit(self, mock_repository):
        """Test listing with limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            projects = [
                Project.create_new(name=f"Project {i}", path=Path(tmpdir) / str(i))
                for i in range(5)
            ]
            mock_repository.get_all = AsyncMock(return_value=projects)
            mock_repository.get_projects_index = AsyncMock(return_value=ProjectsIndex())

            use_case = ListProjectsUseCase(mock_repository)
            result = await use_case.execute(limit=2)

            assert result.success is True
            assert len(result.projects) == 2


# =============================================================================
# DeleteProjectUseCase Tests
# =============================================================================


class TestDeleteProjectUseCase:
    """Tests for DeleteProjectUseCase."""

    @pytest.mark.asyncio
    async def test_delete_project_success(self, mock_repository, sample_project):
        """Test deleting project."""
        mock_repository.get_by_id = AsyncMock(return_value=sample_project)
        mock_repository.delete = AsyncMock()

        use_case = DeleteProjectUseCase(mock_repository)
        result = await use_case.execute(sample_project.id)

        assert result.success is True
        mock_repository.delete.assert_awaited_once_with(
            sample_project.id, remove_files=False
        )

    @pytest.mark.asyncio
    async def test_delete_project_with_files(self, mock_repository, sample_project):
        """Test deleting project with file removal."""
        mock_repository.get_by_id = AsyncMock(return_value=sample_project)
        mock_repository.delete = AsyncMock()

        use_case = DeleteProjectUseCase(mock_repository)
        result = await use_case.execute(sample_project.id, remove_files=True)

        assert result.success is True
        mock_repository.delete.assert_awaited_once_with(
            sample_project.id, remove_files=True
        )

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, mock_repository):
        """Test deleting non-existent project."""
        mock_repository.get_by_id = AsyncMock(return_value=None)
        mock_repository.delete = AsyncMock()

        use_case = DeleteProjectUseCase(mock_repository)
        result = await use_case.execute("proj_nonexistent")

        # Should still succeed (idempotent)
        assert result.success is True


# =============================================================================
# CreateScenarioUseCase Tests
# =============================================================================


class TestCreateScenarioUseCase:
    """Tests for CreateScenarioUseCase."""

    @pytest.mark.asyncio
    async def test_create_scenario_success(self, mock_repository, sample_project):
        """Test creating scenario."""
        mock_repository.get_by_id = AsyncMock(return_value=sample_project)
        mock_repository.save_scenario = AsyncMock()

        use_case = CreateScenarioUseCase(mock_repository)
        result = await use_case.execute(
            project_id=sample_project.id,
            name="New Scenario",
            workflow={"nodes": []},
        )

        assert result.success is True
        assert result.scenario is not None
        assert result.scenario.name == "New Scenario"
        mock_repository.save_scenario.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_scenario_project_not_found(self, mock_repository):
        """Test creating scenario in non-existent project."""
        mock_repository.get_by_id = AsyncMock(return_value=None)

        use_case = CreateScenarioUseCase(mock_repository)
        result = await use_case.execute(
            project_id="proj_nonexistent",
            name="New Scenario",
        )

        assert result.success is False
        assert "not found" in result.error


# =============================================================================
# LoadScenarioUseCase Tests
# =============================================================================


class TestLoadScenarioUseCase:
    """Tests for LoadScenarioUseCase."""

    @pytest.mark.asyncio
    async def test_load_scenario_success(self, mock_repository, sample_scenario):
        """Test loading scenario."""
        mock_repository.get_scenario = AsyncMock(return_value=sample_scenario)

        use_case = LoadScenarioUseCase(mock_repository)
        result = await use_case.execute(
            project_id="proj_12345678",
            scenario_id=sample_scenario.id,
        )

        assert result.success is True
        assert result.scenario.name == sample_scenario.name

    @pytest.mark.asyncio
    async def test_load_scenario_not_found(self, mock_repository):
        """Test loading non-existent scenario."""
        mock_repository.get_scenario = AsyncMock(return_value=None)

        use_case = LoadScenarioUseCase(mock_repository)
        result = await use_case.execute(
            project_id="proj_12345678",
            scenario_id="scen_nonexistent",
        )

        assert result.success is False
        assert "not found" in result.error


# =============================================================================
# SaveScenarioUseCase Tests
# =============================================================================


class TestSaveScenarioUseCase:
    """Tests for SaveScenarioUseCase."""

    @pytest.mark.asyncio
    async def test_save_scenario_success(self, mock_repository, sample_scenario):
        """Test saving scenario."""
        mock_repository.save_scenario = AsyncMock()

        use_case = SaveScenarioUseCase(mock_repository)
        result = await use_case.execute(
            project_id="proj_12345678",
            scenario=sample_scenario,
        )

        assert result.success is True
        mock_repository.save_scenario.assert_awaited_once()


# =============================================================================
# DeleteScenarioUseCase Tests
# =============================================================================


class TestDeleteScenarioUseCase:
    """Tests for DeleteScenarioUseCase."""

    @pytest.mark.asyncio
    async def test_delete_scenario_success(self, mock_repository):
        """Test deleting scenario."""
        mock_repository.delete_scenario = AsyncMock()

        use_case = DeleteScenarioUseCase(mock_repository)
        result = await use_case.execute(
            project_id="proj_12345678",
            scenario_id="scen_12345678",
        )

        assert result.success is True
        mock_repository.delete_scenario.assert_awaited_once()


# =============================================================================
# ListScenariosUseCase Tests
# =============================================================================


class TestListScenariosUseCase:
    """Tests for ListScenariosUseCase."""

    @pytest.mark.asyncio
    async def test_list_scenarios_success(self, mock_repository, sample_scenario):
        """Test listing scenarios."""
        mock_repository.get_scenarios = AsyncMock(return_value=[sample_scenario])

        use_case = ListScenariosUseCase(mock_repository)
        result = await use_case.execute(project_id="proj_12345678")

        assert len(result) == 1
        assert result[0].name == sample_scenario.name

    @pytest.mark.asyncio
    async def test_list_scenarios_empty(self, mock_repository):
        """Test listing empty scenarios."""
        mock_repository.get_scenarios = AsyncMock(return_value=[])

        use_case = ListScenariosUseCase(mock_repository)
        result = await use_case.execute(project_id="proj_12345678")

        assert result == []
