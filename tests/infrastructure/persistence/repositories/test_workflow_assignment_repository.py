"""
Tests for WorkflowAssignmentRepository PostgreSQL implementation.

Tests cover:
- CRUD operations (save, get_assignment, delete)
- Query methods (get_by_workflow, get_by_robot, get_default_for_workflow)
- Default assignment management (set_default, unset others)
- Bulk operations (delete_all_for_workflow, delete_all_for_robot)
- Value object-to-row and row-to-value object mapping
- Error handling

All database operations are mocked using AsyncMock.
"""

from datetime import datetime
from unittest.mock import AsyncMock
import pytest

from casare_rpa.domain.orchestrator.value_objects.robot_assignment import (
    RobotAssignment,
)
from casare_rpa.infrastructure.persistence.repositories.workflow_assignment_repository import (
    WorkflowAssignmentRepository,
)

from .conftest import create_mock_record


class TestWorkflowAssignmentRepositoryRowConversion:
    """Tests for row-to-value-object and value-object-to-row conversion."""

    def test_row_to_assignment_full_data(self, sample_assignment_row):
        """Test converting database row with all fields to RobotAssignment."""
        repo = WorkflowAssignmentRepository(pool_manager=AsyncMock())
        assignment = repo._row_to_assignment(dict(sample_assignment_row))

        assert assignment.workflow_id == "wf-uuid-5678"
        assert assignment.robot_id == "robot-uuid-1234"
        assert assignment.is_default is True
        assert assignment.priority == 10
        assert assignment.created_at == datetime(2024, 1, 10, 8, 0, 0)
        assert assignment.created_by == "admin"
        assert assignment.notes == "Primary assignment for production workflow"

    def test_row_to_assignment_minimal_data(self):
        """Test converting row with minimal/default values."""
        row = create_mock_record(
            {
                "workflow_id": "wf-min",
                "robot_id": "robot-min",
                "is_default": False,
                "priority": 0,
                "created_at": None,
                "created_by": None,
                "notes": None,
            }
        )

        repo = WorkflowAssignmentRepository(pool_manager=AsyncMock())
        assignment = repo._row_to_assignment(dict(row))

        assert assignment.workflow_id == "wf-min"
        assert assignment.robot_id == "robot-min"
        assert assignment.is_default is False
        assert assignment.priority == 0
        # created_at should default to current time when None
        assert assignment.created_at is not None
        assert assignment.created_by == ""
        assert assignment.notes is None

    def test_assignment_to_params_conversion(self):
        """Test converting RobotAssignment to database parameters."""
        assignment = RobotAssignment(
            workflow_id="wf-123",
            robot_id="robot-456",
            is_default=True,
            priority=5,
            created_at=datetime(2024, 2, 1, 12, 0, 0),
            created_by="test-user",
            notes="Test assignment",
        )

        repo = WorkflowAssignmentRepository(pool_manager=AsyncMock())
        params = repo._assignment_to_params(assignment)

        assert params["workflow_id"] == "wf-123"
        assert params["robot_id"] == "robot-456"
        assert params["is_default"] is True
        assert params["priority"] == 5
        assert params["created_at"] == datetime(2024, 2, 1, 12, 0, 0)
        assert params["created_by"] == "test-user"
        assert params["notes"] == "Test assignment"


class TestWorkflowAssignmentRepositorySave:
    """Tests for save operation."""

    @pytest.mark.asyncio
    async def test_save_assignment_success(self, mock_pool_manager, mock_connection):
        """Test successful assignment save (upsert)."""
        mock_connection.execute.return_value = "INSERT 1"

        assignment = RobotAssignment(
            workflow_id="wf-new",
            robot_id="robot-new",
            is_default=True,
            priority=10,
        )

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)
        result = await repo.save(assignment)

        assert result.workflow_id == "wf-new"
        assert result.robot_id == "robot-new"

        # Verify SQL contains INSERT with ON CONFLICT
        calls = mock_connection.execute.call_args_list
        # Second call is the INSERT (first is UPDATE for is_default)
        insert_call = calls[-1]
        sql = insert_call[0][0]
        assert "INSERT INTO workflow_robot_assignments" in sql
        assert "ON CONFLICT (workflow_id, robot_id) DO UPDATE" in sql

    @pytest.mark.asyncio
    async def test_save_assignment_as_default_unsets_others(
        self, mock_pool_manager, mock_connection
    ):
        """Test saving as default unsets other defaults for same workflow."""
        mock_connection.execute.return_value = "UPDATE 1"

        assignment = RobotAssignment(
            workflow_id="wf-123",
            robot_id="robot-new",
            is_default=True,
        )

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)
        await repo.save(assignment)

        # First call should unset other defaults
        first_call = mock_connection.execute.call_args_list[0]
        sql = first_call[0][0]
        assert "SET is_default = FALSE" in sql
        assert "workflow_id = $1 AND robot_id != $2" in sql

    @pytest.mark.asyncio
    async def test_save_non_default_does_not_unset_others(
        self, mock_pool_manager, mock_connection
    ):
        """Test saving non-default assignment doesn't affect other defaults."""
        mock_connection.execute.return_value = "INSERT 1"

        assignment = RobotAssignment(
            workflow_id="wf-123",
            robot_id="robot-backup",
            is_default=False,
        )

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)
        await repo.save(assignment)

        # Should only have one execute call (the INSERT)
        assert mock_connection.execute.call_count == 1

    @pytest.mark.asyncio
    async def test_save_assignment_database_error(
        self, mock_pool_manager, mock_connection
    ):
        """Test save handles database errors properly."""
        mock_connection.execute.side_effect = Exception("Foreign key violation")

        assignment = RobotAssignment(
            workflow_id="wf-err",
            robot_id="robot-err",
        )

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)

        with pytest.raises(Exception) as exc_info:
            await repo.save(assignment)

        assert "Foreign key violation" in str(exc_info.value)


class TestWorkflowAssignmentRepositoryGetByWorkflow:
    """Tests for get_by_workflow operation."""

    @pytest.mark.asyncio
    async def test_get_by_workflow_returns_list(
        self, mock_pool_manager, mock_connection, sample_assignment_row
    ):
        """Test getting all assignments for a workflow."""
        backup_row = create_mock_record(
            {
                "workflow_id": "wf-uuid-5678",
                "robot_id": "robot-backup",
                "is_default": False,
                "priority": 5,
                "created_at": datetime(2024, 1, 11, 8, 0, 0),
                "created_by": "admin",
                "notes": "Backup robot",
            }
        )
        mock_connection.fetch.return_value = [sample_assignment_row, backup_row]

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)
        assignments = await repo.get_by_workflow("wf-uuid-5678")

        assert len(assignments) == 2
        assert assignments[0].is_default is True  # Default first due to ORDER BY
        assert assignments[1].is_default is False

    @pytest.mark.asyncio
    async def test_get_by_workflow_empty(self, mock_pool_manager, mock_connection):
        """Test getting assignments for workflow with none returns empty list."""
        mock_connection.fetch.return_value = []

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)
        assignments = await repo.get_by_workflow("wf-no-assignments")

        assert assignments == []

    @pytest.mark.asyncio
    async def test_get_by_workflow_ordered_by_default_and_priority(
        self, mock_pool_manager, mock_connection
    ):
        """Test results are ordered by is_default DESC, priority DESC."""
        mock_connection.fetch.return_value = []

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)
        await repo.get_by_workflow("wf-123")

        call_args = mock_connection.fetch.call_args
        sql = call_args[0][0]
        assert "ORDER BY is_default DESC, priority DESC" in sql


class TestWorkflowAssignmentRepositoryGetDefaultForWorkflow:
    """Tests for get_default_for_workflow operation."""

    @pytest.mark.asyncio
    async def test_get_default_found(
        self, mock_pool_manager, mock_connection, sample_assignment_row
    ):
        """Test getting default assignment for workflow."""
        mock_connection.fetchrow.return_value = sample_assignment_row

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)
        assignment = await repo.get_default_for_workflow("wf-uuid-5678")

        assert assignment is not None
        assert assignment.is_default is True
        assert assignment.robot_id == "robot-uuid-1234"

        # Verify SQL filters by is_default
        call_args = mock_connection.fetchrow.call_args
        sql = call_args[0][0]
        assert "is_default = TRUE" in sql

    @pytest.mark.asyncio
    async def test_get_default_not_found(self, mock_pool_manager, mock_connection):
        """Test getting default when none set returns None."""
        mock_connection.fetchrow.return_value = None

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)
        assignment = await repo.get_default_for_workflow("wf-no-default")

        assert assignment is None


class TestWorkflowAssignmentRepositoryGetByRobot:
    """Tests for get_by_robot operation."""

    @pytest.mark.asyncio
    async def test_get_by_robot(
        self, mock_pool_manager, mock_connection, sample_assignment_row
    ):
        """Test getting all workflow assignments for a robot."""
        mock_connection.fetch.return_value = [sample_assignment_row]

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)
        assignments = await repo.get_by_robot("robot-uuid-1234")

        assert len(assignments) == 1
        assert assignments[0].robot_id == "robot-uuid-1234"

        # Verify SQL query
        call_args = mock_connection.fetch.call_args
        sql = call_args[0][0]
        assert "robot_id = $1" in sql


class TestWorkflowAssignmentRepositoryGetAssignment:
    """Tests for get_assignment operation (specific workflow-robot pair)."""

    @pytest.mark.asyncio
    async def test_get_assignment_found(
        self, mock_pool_manager, mock_connection, sample_assignment_row
    ):
        """Test getting specific workflow-robot assignment."""
        mock_connection.fetchrow.return_value = sample_assignment_row

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)
        assignment = await repo.get_assignment("wf-uuid-5678", "robot-uuid-1234")

        assert assignment is not None
        assert assignment.workflow_id == "wf-uuid-5678"
        assert assignment.robot_id == "robot-uuid-1234"

        # Verify SQL query
        call_args = mock_connection.fetchrow.call_args
        sql = call_args[0][0]
        assert "workflow_id = $1 AND robot_id = $2" in sql

    @pytest.mark.asyncio
    async def test_get_assignment_not_found(self, mock_pool_manager, mock_connection):
        """Test getting non-existent assignment returns None."""
        mock_connection.fetchrow.return_value = None

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)
        assignment = await repo.get_assignment("wf-x", "robot-y")

        assert assignment is None


class TestWorkflowAssignmentRepositorySetDefault:
    """Tests for set_default operation."""

    @pytest.mark.asyncio
    async def test_set_default_success(self, mock_pool_manager, mock_connection):
        """Test setting a robot as default for workflow."""
        mock_connection.execute.return_value = "UPDATE 1"

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)
        await repo.set_default("wf-123", "robot-456")

        # Should have two UPDATE calls within transaction
        calls = mock_connection.execute.call_args_list
        assert len(calls) >= 2

        # First: unset all defaults
        first_sql = calls[0][0][0]
        assert "is_default = FALSE" in first_sql
        assert "workflow_id = $1" in first_sql

        # Second: set new default
        second_sql = calls[1][0][0]
        assert "is_default = TRUE" in second_sql
        assert "robot_id = $2" in second_sql

    @pytest.mark.asyncio
    async def test_set_default_performs_two_updates(
        self, mock_pool_manager, mock_connection
    ):
        """Test set_default performs both unset and set operations."""
        mock_connection.execute.return_value = "UPDATE 1"

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)
        await repo.set_default("wf-123", "robot-456")

        # Verify both execute calls were made (within transaction)
        assert mock_connection.execute.call_count == 2


class TestWorkflowAssignmentRepositoryDelete:
    """Tests for delete operation."""

    @pytest.mark.asyncio
    async def test_delete_success(self, mock_pool_manager, mock_connection):
        """Test deleting existing assignment returns True."""
        mock_connection.execute.return_value = "DELETE 1"

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)
        result = await repo.delete("wf-123", "robot-456")

        assert result is True

        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]
        assert "DELETE FROM workflow_robot_assignments" in sql
        assert "workflow_id = $1 AND robot_id = $2" in sql

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_pool_manager, mock_connection):
        """Test deleting non-existent assignment returns False."""
        mock_connection.execute.return_value = "DELETE 0"

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)
        result = await repo.delete("wf-x", "robot-y")

        assert result is False


class TestWorkflowAssignmentRepositoryDeleteAllForWorkflow:
    """Tests for delete_all_for_workflow operation."""

    @pytest.mark.asyncio
    async def test_delete_all_for_workflow(self, mock_pool_manager, mock_connection):
        """Test deleting all assignments for a workflow."""
        mock_connection.execute.return_value = "DELETE 3"

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)
        count = await repo.delete_all_for_workflow("wf-123")

        assert count == 3

        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]
        assert "DELETE FROM workflow_robot_assignments" in sql
        assert "workflow_id = $1" in sql

    @pytest.mark.asyncio
    async def test_delete_all_for_workflow_none(
        self, mock_pool_manager, mock_connection
    ):
        """Test deleting when no assignments exist returns 0."""
        mock_connection.execute.return_value = "DELETE 0"

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)
        count = await repo.delete_all_for_workflow("wf-empty")

        assert count == 0


class TestWorkflowAssignmentRepositoryDeleteAllForRobot:
    """Tests for delete_all_for_robot operation."""

    @pytest.mark.asyncio
    async def test_delete_all_for_robot(self, mock_pool_manager, mock_connection):
        """Test deleting all assignments for a robot (decommissioning)."""
        mock_connection.execute.return_value = "DELETE 5"

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)
        count = await repo.delete_all_for_robot("robot-123")

        assert count == 5

        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]
        assert "DELETE FROM workflow_robot_assignments" in sql
        assert "robot_id = $1" in sql


class TestWorkflowAssignmentRepositoryGetWorkflowsForRobot:
    """Tests for get_workflows_for_robot operation."""

    @pytest.mark.asyncio
    async def test_get_workflows_for_robot(self, mock_pool_manager, mock_connection):
        """Test getting workflow IDs assigned to a robot."""
        mock_connection.fetch.return_value = [
            create_mock_record({"workflow_id": "wf-1"}),
            create_mock_record({"workflow_id": "wf-2"}),
            create_mock_record({"workflow_id": "wf-3"}),
        ]

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)
        workflow_ids = await repo.get_workflows_for_robot("robot-123")

        assert len(workflow_ids) == 3
        assert "wf-1" in workflow_ids
        assert "wf-2" in workflow_ids
        assert "wf-3" in workflow_ids

    @pytest.mark.asyncio
    async def test_get_workflows_for_robot_empty(
        self, mock_pool_manager, mock_connection
    ):
        """Test getting workflows for robot with no assignments."""
        mock_connection.fetch.return_value = []

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)
        workflow_ids = await repo.get_workflows_for_robot("robot-no-workflows")

        assert workflow_ids == []


class TestWorkflowAssignmentRepositoryConnectionManagement:
    """Tests for connection pool management."""

    @pytest.mark.asyncio
    async def test_connection_released_after_success(
        self, mock_pool_manager, mock_pool, mock_connection, sample_assignment_row
    ):
        """Test connection is released after successful operation."""
        mock_connection.fetchrow.return_value = sample_assignment_row

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)
        await repo.get_assignment("wf-123", "robot-456")

        mock_pool.release.assert_awaited_once_with(mock_connection)

    @pytest.mark.asyncio
    async def test_connection_released_after_error(
        self, mock_pool_manager, mock_pool, mock_connection
    ):
        """Test connection is released even after error."""
        mock_connection.fetchrow.side_effect = Exception("DB error")

        repo = WorkflowAssignmentRepository(pool_manager=mock_pool_manager)

        with pytest.raises(Exception):
            await repo.get_assignment("wf-123", "robot-456")

        mock_pool.release.assert_awaited_once_with(mock_connection)
