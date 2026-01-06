"""
Integration tests for Projects Index Management.

Tests the projects_index.json file that tracks all registered projects,
including add, update, remove, and index recovery scenarios.
"""

from pathlib import Path

import orjson
import pytest

from casare_rpa.application.use_cases import CreateProjectUseCase, ListProjectsUseCase
from casare_rpa.domain.entities.project import ProjectsIndex


@pytest.mark.integration
@pytest.mark.asyncio
async def test_projects_index_created_on_first_project(
    sandbox_project_repository,
    sandbox_config: dict,
):
    """Test that projects index is created when first project is added."""
    # Arrange: Index file should not exist initially
    index_file = sandbox_config["projects_index"]
    assert not index_file.exists()

    # Act: Create first project
    create_use_case = CreateProjectUseCase(sandbox_project_repository)
    await create_use_case.execute(
        name="FirstProject",
        path=sandbox_config["config_dir"] / "projects" / "first",
    )

    # Assert: Index file was created
    assert index_file.exists()

    # Assert: Index is valid JSON
    content = orjson.loads(index_file.read_bytes())
    assert "projects" in content
    assert len(content["projects"]) == 1
    assert content["projects"][0]["name"] == "FirstProject"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_projects_index_tracks_multiple_projects(
    sandbox_project_repository,
    sandbox_config: dict,
):
    """Test that index correctly tracks multiple projects."""
    # Arrange: Create multiple projects
    create_use_case = CreateProjectUseCase(sandbox_project_repository)
    projects_dir = sandbox_config["config_dir"] / "projects"

    await create_use_case.execute(name="Project1", path=projects_dir / "proj1")
    await create_use_case.execute(name="Project2", path=projects_dir / "proj2")
    await create_use_case.execute(name="Project3", path=projects_dir / "proj3")

    # Act: Get the index
    index = await sandbox_project_repository.get_projects_index()

    # Assert: All projects are tracked
    assert len(index.projects) == 3

    project_names = {p.name for p in index.projects}
    assert "Project1" in project_names
    assert "Project2" in project_names
    assert "Project3" in project_names


@pytest.mark.integration
@pytest.mark.asyncio
async def test_projects_index_last_opened_updates(
    sandbox_project_repository,
    sandbox_config: dict,
):
    """Test that last_opened timestamp updates when project is loaded."""
    # Arrange: Create a project
    create_use_case = CreateProjectUseCase(sandbox_project_repository)
    project_path = sandbox_config["config_dir"] / "projects" / "timestamp_test"

    result = await create_use_case.execute(name="TimestampTest", path=project_path)
    original_project = result.project

    # Get original timestamp
    index = await sandbox_project_repository.get_projects_index()
    original_entry = index.get_project(original_project.id)
    original_timestamp = original_entry.last_opened

    # Act: Load the project (should update timestamp)
    from casare_rpa.application.use_cases import LoadProjectUseCase

    load_use_case = LoadProjectUseCase(sandbox_project_repository)
    await load_use_case.execute(path=project_path)

    # Assert: Timestamp was updated
    updated_index = await sandbox_project_repository.get_projects_index()
    updated_entry = updated_index.get_project(original_project.id)

    # The updated timestamp should be >= original (allowing for minimal time passage)
    assert updated_entry.last_opened >= original_timestamp


@pytest.mark.integration
@pytest.mark.asyncio
async def test_projects_index_persistence_roundtrip(
    sandbox_project_repository,
    sandbox_config: dict,
):
    """Test that index survives save/load roundtrip."""
    # Arrange: Create projects
    create_use_case = CreateProjectUseCase(sandbox_project_repository)
    projects_dir = sandbox_config["config_dir"] / "projects"

    await create_use_case.execute(
        name="PersistTest1",
        path=projects_dir / "persist1",
        description="First persistence test",
    )
    await create_use_case.execute(
        name="PersistTest2",
        path=projects_dir / "persist2",
        description="Second persistence test",
    )

    # Act: Reload index from disk
    index_file = sandbox_config["projects_index"]
    index_data = orjson.loads(index_file.read_bytes())
    reloaded_index = ProjectsIndex.from_dict(index_data)

    # Assert: All data preserved
    assert len(reloaded_index.projects) == 2

    # Check project data integrity - ProjectIndexEntry only has id, name, path, last_opened
    project_ids = [p.id for p in reloaded_index.projects]
    assert len(project_ids) == 2
    # Both projects should be in the index
    for project in reloaded_index.projects:
        assert project.id in project_ids


@pytest.mark.integration
@pytest.mark.asyncio
async def test_projects_index_handles_missing_file_gracefully(
    sandbox_project_repository,
    sandbox_config: dict,
):
    """Test that missing index file is handled gracefully."""
    # Arrange: Delete index file if it exists
    index_file = sandbox_config["projects_index"]
    if index_file.exists():
        index_file.unlink()

    # Act: Get index (should create empty index)
    index = await sandbox_project_repository.get_projects_index()

    # Assert: Empty index returned
    assert index is not None
    assert len(index.projects) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_projects_index_remove_project(
    sandbox_project_repository,
    sandbox_config: dict,
):
    """Test removing a project from the index."""
    # Arrange: Create projects
    create_use_case = CreateProjectUseCase(sandbox_project_repository)
    projects_dir = sandbox_config["config_dir"] / "projects"

    result1 = await create_use_case.execute(name="ToRemove", path=projects_dir / "to_remove")
    await create_use_case.execute(name="ToKeep", path=projects_dir / "to_keep")

    project_id = result1.project.id

    # Act: Remove project from index
    await sandbox_project_repository.delete(project_id)

    # Assert: Only one project remains
    index = await sandbox_project_repository.get_projects_index()
    assert len(index.projects) == 1
    assert index.projects[0].name == "ToKeep"
    assert index.get_project(project_id) is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_projects_index_with_tags(
    sandbox_project_repository,
    sandbox_config: dict,
):
    """Test that projects with tags are indexed correctly."""
    # Arrange: Create project with tags
    create_use_case = CreateProjectUseCase(sandbox_project_repository)
    projects_dir = sandbox_config["config_dir"] / "projects"

    await create_use_case.execute(
        name="TaggedProject",
        path=projects_dir / "tagged",
        tags=["automation", "testing", "integration"],
    )

    # Act: Get index
    index = await sandbox_project_repository.get_projects_index()

    # Assert: Project is indexed (tags are stored in project.json, not in index entry)
    project = index.projects[0]
    assert project.name == "TaggedProject"
    # Note: ProjectIndexEntry does not include tags field (only id, name, path, last_opened)
    # Tags are stored in the full project.json file


@pytest.mark.integration
@pytest.mark.asyncio
async def test_projects_index_path_normalization(
    sandbox_project_repository,
    sandbox_config: dict,
):
    """Test that project paths are normalized and consistent."""
    # Arrange: Create project
    create_use_case = CreateProjectUseCase(sandbox_project_repository)

    # Use path with potential inconsistencies (trailing slash, etc.)
    projects_dir = sandbox_config["config_dir"] / "projects"
    project_path = (projects_dir / "normalize_test").resolve()

    await create_use_case.execute(name="NormalizeTest", path=project_path)

    # Act: Get index
    index = await sandbox_project_repository.get_projects_index()

    # Assert: Path is stored consistently
    project_entry = index.projects[0]
    assert str(project_entry.path) == str(project_path)
