"""Tests for LocalWorkflowRepository."""

import pytest
from pathlib import Path
import tempfile

from casare_rpa.domain.orchestrator.entities import Workflow, WorkflowStatus
from casare_rpa.infrastructure.orchestrator.persistence import (
    LocalStorageRepository,
    LocalWorkflowRepository,
)


@pytest.fixture
def temp_storage_dir():
    """Create temporary storage directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage(temp_storage_dir):
    """Create LocalStorageRepository with temp directory."""
    return LocalStorageRepository(storage_dir=temp_storage_dir)


@pytest.fixture
def workflow_repository(storage):
    """Create LocalWorkflowRepository."""
    return LocalWorkflowRepository(storage)


@pytest.fixture
def sample_workflow():
    """Create sample workflow entity."""
    return Workflow(
        id="wf-1",
        name="Test Workflow",
        description="A test workflow",
        json_definition='{"nodes": []}',
        status=WorkflowStatus.DRAFT,
    )


@pytest.mark.asyncio
async def test_save_workflow(workflow_repository, sample_workflow):
    """Test saving a workflow."""
    await workflow_repository.save(sample_workflow)

    # Verify workflow was saved
    retrieved = await workflow_repository.get_by_id("wf-1")
    assert retrieved is not None
    assert retrieved.id == "wf-1"
    assert retrieved.name == "Test Workflow"
    assert retrieved.status == WorkflowStatus.DRAFT


@pytest.mark.asyncio
async def test_get_by_id_not_found(workflow_repository):
    """Test getting non-existent workflow returns None."""
    result = await workflow_repository.get_by_id("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_get_all(workflow_repository):
    """Test getting all workflows."""
    wf1 = Workflow(
        id="wf-1", name="Workflow 1", description="", status=WorkflowStatus.DRAFT
    )
    wf2 = Workflow(
        id="wf-2", name="Workflow 2", description="", status=WorkflowStatus.PUBLISHED
    )

    await workflow_repository.save(wf1)
    await workflow_repository.save(wf2)

    all_workflows = await workflow_repository.get_all()
    assert len(all_workflows) == 2
    assert {w.id for w in all_workflows} == {"wf-1", "wf-2"}


@pytest.mark.asyncio
async def test_get_by_status(workflow_repository):
    """Test getting workflows by status."""
    wf1 = Workflow(
        id="wf-1", name="Workflow 1", description="", status=WorkflowStatus.DRAFT
    )
    wf2 = Workflow(
        id="wf-2", name="Workflow 2", description="", status=WorkflowStatus.PUBLISHED
    )
    wf3 = Workflow(
        id="wf-3", name="Workflow 3", description="", status=WorkflowStatus.DRAFT
    )

    await workflow_repository.save(wf1)
    await workflow_repository.save(wf2)
    await workflow_repository.save(wf3)

    draft_workflows = await workflow_repository.get_by_status(WorkflowStatus.DRAFT)
    assert len(draft_workflows) == 2
    assert {w.id for w in draft_workflows} == {"wf-1", "wf-3"}


@pytest.mark.asyncio
async def test_update_workflow(workflow_repository, sample_workflow):
    """Test updating a workflow."""
    await workflow_repository.save(sample_workflow)

    # Update workflow
    sample_workflow.status = WorkflowStatus.PUBLISHED
    sample_workflow.version = 2
    await workflow_repository.save(sample_workflow)

    # Verify updates
    updated = await workflow_repository.get_by_id("wf-1")
    assert updated.status == WorkflowStatus.PUBLISHED
    assert updated.version == 2


@pytest.mark.asyncio
async def test_delete_workflow(workflow_repository, sample_workflow):
    """Test deleting a workflow."""
    await workflow_repository.save(sample_workflow)

    # Verify workflow exists
    assert await workflow_repository.get_by_id("wf-1") is not None

    # Delete workflow
    await workflow_repository.delete("wf-1")

    # Verify workflow is gone
    assert await workflow_repository.get_by_id("wf-1") is None
