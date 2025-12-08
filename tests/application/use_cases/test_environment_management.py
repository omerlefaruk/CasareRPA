"""Tests for environment management use cases."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch, MagicMock

from casare_rpa.domain.entities.project import (
    Environment,
    EnvironmentType,
    Project,
)
from casare_rpa.domain.entities.project.environment import generate_environment_id
from casare_rpa.application.use_cases.environment_management import (
    CreateEnvironmentUseCase,
    CreateDefaultEnvironmentsUseCase,
    UpdateEnvironmentUseCase,
    DeleteEnvironmentUseCase,
    SwitchEnvironmentUseCase,
    CloneEnvironmentUseCase,
    ResolveEnvironmentVariablesUseCase,
    ListEnvironmentsUseCase,
    EnvironmentResult,
    EnvironmentListResult,
    VariablesResult,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_project():
    """Create a sample project with temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Project.create_new(
            name="Test Project",
            path=Path(tmpdir),
            description="A test project",
        )
        # Create environments directory
        project.environments_dir.mkdir(parents=True, exist_ok=True)
        yield project


@pytest.fixture
def sample_environment():
    """Create a sample environment."""
    return Environment(
        id=generate_environment_id(),
        name="Development",
        env_type=EnvironmentType.DEVELOPMENT,
        description="Test development environment",
        variables={"API_URL": "http://localhost:8000"},
        is_default=True,
    )


# =============================================================================
# CreateEnvironmentUseCase Tests
# =============================================================================


class TestCreateEnvironmentUseCase:
    """Tests for CreateEnvironmentUseCase."""

    @pytest.mark.asyncio
    async def test_create_environment_success(self, sample_project):
        """Test successful environment creation."""
        with patch(
            "casare_rpa.application.use_cases.environment_management.EnvironmentStorage"
        ) as mock_storage:
            mock_storage.load_environment_by_type.return_value = None
            mock_storage.save_environment.return_value = None

            use_case = CreateEnvironmentUseCase()
            result = await use_case.execute(
                project=sample_project,
                name="Custom Env",
                env_type=EnvironmentType.CUSTOM,
                description="A custom environment",
                variables={"DEBUG": "true"},
            )

            assert result.success is True
            assert result.environment is not None
            assert result.environment.name == "Custom Env"
            assert result.environment.env_type == EnvironmentType.CUSTOM
            assert result.error is None
            mock_storage.save_environment.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_environment_no_project_path(self):
        """Test creating environment when project path is not set."""
        # Create project without path
        project = Mock(spec=Project)
        project.path = None

        use_case = CreateEnvironmentUseCase()
        result = await use_case.execute(
            project=project,
            name="Test Env",
        )

        assert result.success is False
        assert "path not set" in result.error

    @pytest.mark.asyncio
    async def test_create_environment_type_already_exists(self, sample_project):
        """Test creating environment when type already exists."""
        existing_env = Environment(
            id="env_existing",
            name="Development",
            env_type=EnvironmentType.DEVELOPMENT,
        )

        with patch(
            "casare_rpa.application.use_cases.environment_management.EnvironmentStorage"
        ) as mock_storage:
            mock_storage.load_environment_by_type.return_value = existing_env

            use_case = CreateEnvironmentUseCase()
            result = await use_case.execute(
                project=sample_project,
                name="New Dev",
                env_type=EnvironmentType.DEVELOPMENT,
            )

            assert result.success is False
            assert "already exists" in result.error

    @pytest.mark.asyncio
    async def test_create_environment_with_default_flag(self, sample_project):
        """Test creating environment as default."""
        with patch(
            "casare_rpa.application.use_cases.environment_management.EnvironmentStorage"
        ) as mock_storage:
            mock_storage.load_environment_by_type.return_value = None
            mock_storage.save_environment.return_value = None

            use_case = CreateEnvironmentUseCase()
            result = await use_case.execute(
                project=sample_project,
                name="Default Env",
                env_type=EnvironmentType.CUSTOM,
                is_default=True,
            )

            assert result.success is True
            assert result.environment.is_default is True
            assert sample_project.active_environment_id == result.environment.id

    @pytest.mark.asyncio
    async def test_create_environment_exception_handling(self, sample_project):
        """Test error handling when storage save fails."""
        with patch(
            "casare_rpa.application.use_cases.environment_management.EnvironmentStorage"
        ) as mock_storage:
            # First call succeeds (checking if type exists)
            mock_storage.load_environment_by_type.return_value = None
            # But save fails
            mock_storage.save_environment.side_effect = Exception("Storage error")

            use_case = CreateEnvironmentUseCase()
            result = await use_case.execute(
                project=sample_project,
                name="Failing Env",
                env_type=EnvironmentType.CUSTOM,
            )

            assert result.success is False
            assert "Storage error" in result.error


# =============================================================================
# CreateDefaultEnvironmentsUseCase Tests
# =============================================================================


class TestCreateDefaultEnvironmentsUseCase:
    """Tests for CreateDefaultEnvironmentsUseCase."""

    @pytest.mark.asyncio
    async def test_create_default_environments_success(self, sample_project):
        """Test creating default dev/staging/prod environments."""
        with patch(
            "casare_rpa.application.use_cases.environment_management.EnvironmentStorage"
        ) as mock_storage:
            # Mock the create_default_environments to return three environments
            mock_envs = [
                Environment(
                    id="env_dev",
                    name="Development",
                    env_type=EnvironmentType.DEVELOPMENT,
                ),
                Environment(
                    id="env_staging", name="Staging", env_type=EnvironmentType.STAGING
                ),
                Environment(
                    id="env_prod",
                    name="Production",
                    env_type=EnvironmentType.PRODUCTION,
                ),
            ]
            mock_storage.create_default_environments.return_value = mock_envs

            use_case = CreateDefaultEnvironmentsUseCase()
            result = await use_case.execute(project=sample_project)

            assert result.success is True
            assert len(result.environments) == 3
            assert sample_project.active_environment_id == "env_dev"
            mock_storage.create_default_environments.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_default_environments_no_path(self):
        """Test creating default environments when project has no path."""
        project = Mock(spec=Project)
        project.path = None

        use_case = CreateDefaultEnvironmentsUseCase()
        result = await use_case.execute(project=project)

        assert result.success is False
        assert "path not set" in result.error


# =============================================================================
# UpdateEnvironmentUseCase Tests
# =============================================================================


class TestUpdateEnvironmentUseCase:
    """Tests for UpdateEnvironmentUseCase."""

    @pytest.mark.asyncio
    async def test_update_environment_success(self, sample_project, sample_environment):
        """Test successful environment update."""
        with patch(
            "casare_rpa.application.use_cases.environment_management.EnvironmentStorage"
        ) as mock_storage:
            mock_storage.load_environment.return_value = sample_environment
            mock_storage.save_environment.return_value = None

            use_case = UpdateEnvironmentUseCase()
            result = await use_case.execute(
                project=sample_project,
                environment_id=sample_environment.id,
                name="Updated Name",
                description="Updated description",
                variables={"NEW_VAR": "value"},
            )

            assert result.success is True
            assert result.environment.name == "Updated Name"
            assert result.environment.description == "Updated description"
            assert result.environment.variables == {"NEW_VAR": "value"}

    @pytest.mark.asyncio
    async def test_update_environment_not_found(self, sample_project):
        """Test updating non-existent environment."""
        with patch(
            "casare_rpa.application.use_cases.environment_management.EnvironmentStorage"
        ) as mock_storage:
            mock_storage.load_environment.return_value = None

            use_case = UpdateEnvironmentUseCase()
            result = await use_case.execute(
                project=sample_project,
                environment_id="env_nonexistent",
                name="New Name",
            )

            assert result.success is False
            assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_update_environment_partial_update(
        self, sample_project, sample_environment
    ):
        """Test updating only specific fields."""
        original_description = sample_environment.description
        original_variables = sample_environment.variables.copy()

        with patch(
            "casare_rpa.application.use_cases.environment_management.EnvironmentStorage"
        ) as mock_storage:
            mock_storage.load_environment.return_value = sample_environment
            mock_storage.save_environment.return_value = None

            use_case = UpdateEnvironmentUseCase()
            result = await use_case.execute(
                project=sample_project,
                environment_id=sample_environment.id,
                name="Only Name Changed",
            )

            assert result.success is True
            assert result.environment.name == "Only Name Changed"
            # Other fields should remain unchanged
            assert result.environment.description == original_description


# =============================================================================
# DeleteEnvironmentUseCase Tests
# =============================================================================


class TestDeleteEnvironmentUseCase:
    """Tests for DeleteEnvironmentUseCase."""

    @pytest.mark.asyncio
    async def test_delete_environment_success(self, sample_project, sample_environment):
        """Test successful environment deletion."""
        with patch(
            "casare_rpa.application.use_cases.environment_management.EnvironmentStorage"
        ) as mock_storage:
            # At least 2 environments exist
            mock_storage.load_all_environments.return_value = [
                sample_environment,
                Environment(
                    id="env_second", name="Second", env_type=EnvironmentType.STAGING
                ),
            ]
            mock_storage.delete_environment.return_value = True

            sample_project.environment_ids = [sample_environment.id, "env_second"]

            use_case = DeleteEnvironmentUseCase()
            result = await use_case.execute(
                project=sample_project,
                environment_id=sample_environment.id,
            )

            assert result.success is True
            mock_storage.delete_environment.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_last_environment_fails(
        self, sample_project, sample_environment
    ):
        """Test that deleting the last environment fails."""
        with patch(
            "casare_rpa.application.use_cases.environment_management.EnvironmentStorage"
        ) as mock_storage:
            # Only one environment exists
            mock_storage.load_all_environments.return_value = [sample_environment]

            use_case = DeleteEnvironmentUseCase()
            result = await use_case.execute(
                project=sample_project,
                environment_id=sample_environment.id,
            )

            assert result.success is False
            assert "last environment" in result.error

    @pytest.mark.asyncio
    async def test_delete_environment_not_found(self, sample_project):
        """Test deleting non-existent environment."""
        with patch(
            "casare_rpa.application.use_cases.environment_management.EnvironmentStorage"
        ) as mock_storage:
            mock_storage.load_all_environments.return_value = [
                Environment(id="env_1", name="Env 1"),
                Environment(id="env_2", name="Env 2"),
            ]
            mock_storage.delete_environment.return_value = False

            use_case = DeleteEnvironmentUseCase()
            result = await use_case.execute(
                project=sample_project,
                environment_id="env_nonexistent",
            )

            assert result.success is False
            assert "not found" in result.error


# =============================================================================
# SwitchEnvironmentUseCase Tests
# =============================================================================


class TestSwitchEnvironmentUseCase:
    """Tests for SwitchEnvironmentUseCase."""

    @pytest.mark.asyncio
    async def test_switch_environment_success(self, sample_project, sample_environment):
        """Test successful environment switch."""
        with patch(
            "casare_rpa.application.use_cases.environment_management.EnvironmentStorage"
        ) as mock_storage:
            mock_storage.load_environment.return_value = sample_environment

            use_case = SwitchEnvironmentUseCase()
            result = await use_case.execute(
                project=sample_project,
                environment_id=sample_environment.id,
            )

            assert result.success is True
            assert result.environment.id == sample_environment.id
            assert sample_project.active_environment_id == sample_environment.id

    @pytest.mark.asyncio
    async def test_switch_environment_not_found(self, sample_project):
        """Test switching to non-existent environment."""
        with patch(
            "casare_rpa.application.use_cases.environment_management.EnvironmentStorage"
        ) as mock_storage:
            mock_storage.load_environment.return_value = None

            use_case = SwitchEnvironmentUseCase()
            result = await use_case.execute(
                project=sample_project,
                environment_id="env_nonexistent",
            )

            assert result.success is False
            assert "not found" in result.error


# =============================================================================
# CloneEnvironmentUseCase Tests
# =============================================================================


class TestCloneEnvironmentUseCase:
    """Tests for CloneEnvironmentUseCase."""

    @pytest.mark.asyncio
    async def test_clone_environment_success(self, sample_project, sample_environment):
        """Test successful environment cloning."""
        with patch(
            "casare_rpa.application.use_cases.environment_management.EnvironmentStorage"
        ) as mock_storage:
            mock_storage.load_environment.return_value = sample_environment
            mock_storage.save_environment.return_value = None

            use_case = CloneEnvironmentUseCase()
            result = await use_case.execute(
                project=sample_project,
                source_environment_id=sample_environment.id,
                new_name="Cloned Environment",
            )

            assert result.success is True
            assert result.environment.name == "Cloned Environment"
            assert result.environment.env_type == EnvironmentType.CUSTOM
            assert result.environment.variables == sample_environment.variables
            assert result.environment.id != sample_environment.id
            mock_storage.save_environment.assert_called_once()

    @pytest.mark.asyncio
    async def test_clone_environment_source_not_found(self, sample_project):
        """Test cloning non-existent environment."""
        with patch(
            "casare_rpa.application.use_cases.environment_management.EnvironmentStorage"
        ) as mock_storage:
            mock_storage.load_environment.return_value = None

            use_case = CloneEnvironmentUseCase()
            result = await use_case.execute(
                project=sample_project,
                source_environment_id="env_nonexistent",
                new_name="Cloned",
            )

            assert result.success is False
            assert "not found" in result.error


# =============================================================================
# ResolveEnvironmentVariablesUseCase Tests
# =============================================================================


class TestResolveEnvironmentVariablesUseCase:
    """Tests for ResolveEnvironmentVariablesUseCase."""

    @pytest.mark.asyncio
    async def test_resolve_variables_success(self, sample_project, sample_environment):
        """Test successful variable resolution."""
        with patch(
            "casare_rpa.application.use_cases.environment_management.EnvironmentStorage"
        ) as mock_storage:
            mock_storage.load_environment.return_value = sample_environment
            mock_storage.resolve_variables_with_inheritance.return_value = {
                "API_URL": "http://localhost:8000",
                "INHERITED_VAR": "inherited_value",
            }

            sample_project.active_environment_id = sample_environment.id

            use_case = ResolveEnvironmentVariablesUseCase()
            result = await use_case.execute(project=sample_project)

            assert result.success is True
            assert "API_URL" in result.variables
            assert "INHERITED_VAR" in result.variables

    @pytest.mark.asyncio
    async def test_resolve_variables_no_environment_specified(self, sample_project):
        """Test resolving when no environment is specified or active."""
        sample_project.active_environment_id = None

        use_case = ResolveEnvironmentVariablesUseCase()
        result = await use_case.execute(project=sample_project)

        assert result.success is False
        assert "No environment" in result.error

    @pytest.mark.asyncio
    async def test_resolve_variables_environment_not_found(self, sample_project):
        """Test resolving with non-existent environment."""
        with patch(
            "casare_rpa.application.use_cases.environment_management.EnvironmentStorage"
        ) as mock_storage:
            mock_storage.load_environment.return_value = None

            use_case = ResolveEnvironmentVariablesUseCase()
            result = await use_case.execute(
                project=sample_project,
                environment_id="env_nonexistent",
            )

            assert result.success is False
            assert "not found" in result.error


# =============================================================================
# ListEnvironmentsUseCase Tests
# =============================================================================


class TestListEnvironmentsUseCase:
    """Tests for ListEnvironmentsUseCase."""

    @pytest.mark.asyncio
    async def test_list_environments_success(self, sample_project):
        """Test listing all environments."""
        mock_envs = [
            Environment(
                id="env_dev", name="Development", env_type=EnvironmentType.DEVELOPMENT
            ),
            Environment(
                id="env_staging", name="Staging", env_type=EnvironmentType.STAGING
            ),
            Environment(
                id="env_prod", name="Production", env_type=EnvironmentType.PRODUCTION
            ),
        ]

        with patch(
            "casare_rpa.application.use_cases.environment_management.EnvironmentStorage"
        ) as mock_storage:
            mock_storage.load_all_environments.return_value = mock_envs

            use_case = ListEnvironmentsUseCase()
            result = await use_case.execute(project=sample_project)

            assert result.success is True
            assert len(result.environments) == 3
            mock_storage.load_all_environments.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_environments_empty(self, sample_project):
        """Test listing when no environments exist."""
        with patch(
            "casare_rpa.application.use_cases.environment_management.EnvironmentStorage"
        ) as mock_storage:
            mock_storage.load_all_environments.return_value = []

            use_case = ListEnvironmentsUseCase()
            result = await use_case.execute(project=sample_project)

            assert result.success is True
            assert result.environments == []

    @pytest.mark.asyncio
    async def test_list_environments_exception(self, sample_project):
        """Test error handling when listing fails."""
        with patch(
            "casare_rpa.application.use_cases.environment_management.EnvironmentStorage"
        ) as mock_storage:
            mock_storage.load_all_environments.side_effect = Exception("Load error")

            use_case = ListEnvironmentsUseCase()
            result = await use_case.execute(project=sample_project)

            assert result.success is False
            assert "Load error" in result.error
