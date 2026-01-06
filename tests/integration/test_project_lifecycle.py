"""
Integration tests for Project CRUD Lifecycle.

Tests the complete project lifecycle: create → save → load → list → delete.
Uses real persistence (JSON files) and real use cases.
"""

from pathlib import Path

import orjson
import pytest

from casare_rpa.application.use_cases import (
    CreateProjectUseCase,
    DeleteProjectUseCase,
    ListProjectsUseCase,
    LoadProjectUseCase,
    ProjectResult,
)
from casare_rpa.domain.entities.project import Project


@pytest.mark.integration
@pytest.mark.asyncio
async def test_project_create_and_save(
    sandbox_project_repository,
    integration_sandbox: Path,
):
    """Test creating a new project and persisting it to disk."""
    # Arrange
    use_case = CreateProjectUseCase(sandbox_project_repository)
    project_path = integration_sandbox / "my_test_project"

    # Act
    result = await use_case.execute(
        name="MyTestProject",
        path=project_path,
        description="A test project for integration testing",
        author="TestSuite",
        tags=["test", "example"],
    )

    # Assert: Result is successful
    assert result.success is True
    assert result.project is not None
    assert result.project.name == "MyTestProject"
    assert result.project.description == "A test project for integration testing"

    # Assert: Project folder exists with marker
    assert project_path.exists()
    assert (project_path / ".casare_project").exists()
    assert (project_path / "scenarios").exists()

    # Assert: project.json was written
    project_file = project_path / "project.json"
    assert project_file.exists()

    # Assert: JSON content is valid
    data = orjson.loads(project_file.read_bytes())
    assert data["name"] == "MyTestProject"
    assert data["description"] == "A test project for integration testing"
    assert data["tags"] == ["test", "example"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_project_create_duplicate_fails(
    sandbox_project_repository,
    integration_sandbox: Path,
):
    """Test that creating a project in an existing directory fails gracefully."""
    # Arrange: Create first project
    create_use_case = CreateProjectUseCase(sandbox_project_repository)
    project_path = integration_sandbox / "duplicate_test"

    result1 = await create_use_case.execute(
        name="DuplicateTest",
        path=project_path,
    )
    assert result1.success is True

    # Act: Try to create another project in the same directory
    result2 = await create_use_case.execute(
        name="ShouldFail",
        path=project_path,
    )

    # Assert: Second creation fails
    assert result2.success is False
    assert "already exists" in result2.error.lower() or "not empty" in result2.error.lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_project_load_by_path(
    sandbox_project_repository,
    integration_sandbox: Path,
):
    """Test loading a project from disk by path."""
    # Arrange: Create a project
    create_use_case = CreateProjectUseCase(sandbox_project_repository)
    project_path = integration_sandbox / "load_test"

    await create_use_case.execute(
        name="LoadTestProject",
        path=project_path,
        description="Project for loading tests",
    )

    # Act: Load the project by path
    load_use_case = LoadProjectUseCase(sandbox_project_repository)
    result = await load_use_case.execute(path=project_path)

    # Assert
    assert result.success is True
    assert result.project is not None
    assert result.project.name == "LoadTestProject"
    assert result.project.description == "Project for loading tests"
    assert result.project.path == project_path


@pytest.mark.integration
@pytest.mark.asyncio
async def test_project_load_nonexistent_fails(
    sandbox_project_repository,
    integration_sandbox: Path,
):
    """Test that loading a non-existent project fails gracefully."""
    # Arrange
    load_use_case = LoadProjectUseCase(sandbox_project_repository)
    nonexistent_path = integration_sandbox / "does_not_exist"

    # Act
    result = await load_use_case.execute(path=nonexistent_path)

    # Assert
    assert result.success is False
    assert result.project is None
    assert "not found" in result.error.lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_project_list_sorted_by_last_opened(
    sandbox_project_repository,
    integration_sandbox: Path,
):
    """Test that listing projects returns them sorted by last_opened timestamp."""
    # Arrange: Create multiple projects
    create_use_case = CreateProjectUseCase(sandbox_project_repository)

    await create_use_case.execute(name="Project1", path=integration_sandbox / "proj1")
    await create_use_case.execute(name="Project2", path=integration_sandbox / "proj2")
    await create_use_case.execute(name="Project3", path=integration_sandbox / "proj3")

    # Load projects in reverse order to update last_opened
    load_use_case = LoadProjectUseCase(sandbox_project_repository)
    await load_use_case.execute(path=integration_sandbox / "proj3")
    await load_use_case.execute(path=integration_sandbox / "proj1")
    await load_use_case.execute(path=integration_sandbox / "proj2")

    # Act: List all projects
    list_use_case = ListProjectsUseCase(sandbox_project_repository)
    result = await list_use_case.execute()

    # Assert: Projects are returned sorted by last_opened (most recent first)
    assert result.success is True
    assert len(result.projects) == 3

    # Project2 should be first (loaded last)
    assert result.projects[0].name == "Project2"
    assert result.projects[1].name == "Project1"
    assert result.projects[2].name == "Project3"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_project_delete_from_index(
    sandbox_project_repository,
    integration_sandbox: Path,
):
    """Test deleting a project removes it from the index."""
    # Arrange: Create and register a project
    create_use_case = CreateProjectUseCase(sandbox_project_repository)
    project_path = integration_sandbox / "delete_test"

    await create_use_case.execute(name="DeleteTest", path=project_path)

    # Verify it's in the list
    list_use_case = ListProjectsUseCase(sandbox_project_repository)
    before_list = await list_use_case.execute()
    assert len(before_list.projects) == 1

    # Act: Delete the project (index only, not files)
    delete_use_case = DeleteProjectUseCase(sandbox_project_repository)
    result = await delete_use_case.execute(
        project_id=before_list.projects[0].id,
        remove_files=False,
    )

    # Assert: Project is removed from index
    assert result.success is True
    after_list = await list_use_case.execute()
    assert len(after_list.projects) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_project_persistence_roundtrip(
    sandbox_project_repository,
    integration_sandbox: Path,
):
    """Test that project data survives save/load roundtrip."""
    # Arrange: Create project with various fields
    create_use_case = CreateProjectUseCase(sandbox_project_repository)
    project_path = integration_sandbox / "roundtrip_test"

    created = await create_use_case.execute(
        name="RoundtripTest",
        path=project_path,
        description="Testing persistence roundtrip",
        author="IntegrationTester",
        tags=["persistence", "roundtrip", "test"],
    )

    original_project = created.project

    # Act: Load the project fresh from disk
    load_use_case = LoadProjectUseCase(sandbox_project_repository)
    loaded_result = await load_use_case.execute(path=project_path)
    loaded_project = loaded_result.project

    # Assert: All fields match
    assert loaded_project.id == original_project.id
    assert loaded_project.name == original_project.name
    assert loaded_project.description == original_project.description
    assert loaded_project.author == original_project.author
    assert loaded_project.tags == original_project.tags
    assert loaded_project.path == original_project.path
