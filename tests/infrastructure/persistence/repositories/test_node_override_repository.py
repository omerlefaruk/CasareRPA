"""
Tests for NodeOverrideRepository PostgreSQL implementation.

Tests cover:
- CRUD operations (save, get_by_node, delete)
- Query methods (get_by_workflow, get_active_for_workflow, get_by_robot, get_by_capability)
- Activation management (activate, deactivate)
- Bulk operations (delete_all_for_workflow, delete_all_for_robot)
- Override map generation (get_override_map)
- Value object-to-row and row-to-value object mapping
- Error handling

All database operations are mocked using AsyncMock.
"""

from datetime import datetime
from unittest.mock import AsyncMock
import pytest

from casare_rpa.domain.orchestrator.entities.robot import RobotCapability
from casare_rpa.domain.orchestrator.value_objects.node_robot_override import (
    NodeRobotOverride,
)
from casare_rpa.infrastructure.persistence.repositories.node_override_repository import (
    NodeOverrideRepository,
)

from .conftest import create_mock_record


class TestNodeOverrideRepositoryRowConversion:
    """Tests for row-to-value-object and value-object-to-row conversion."""

    def test_row_to_override_full_data(self, sample_override_row):
        """Test converting database row with all fields to NodeRobotOverride."""
        repo = NodeOverrideRepository(pool_manager=AsyncMock())
        override = repo._row_to_override(dict(sample_override_row))

        assert override.workflow_id == "wf-uuid-5678"
        assert override.node_id == "node-gpu-processing"
        assert override.robot_id == "robot-gpu-1234"
        assert RobotCapability.GPU in override.required_capabilities
        assert RobotCapability.HIGH_MEMORY in override.required_capabilities
        assert override.reason == "Node requires GPU for ML inference"
        assert override.created_by == "ml-team"
        assert override.is_active is True

    def test_row_to_override_capability_only(self):
        """Test converting row with capability-based routing (no robot_id)."""
        row = create_mock_record(
            {
                "workflow_id": "wf-123",
                "node_id": "node-browser",
                "robot_id": None,
                "required_capabilities": '["browser", "desktop"]',
                "reason": "Needs browser and desktop automation",
                "created_at": datetime(2024, 1, 15, 10, 0, 0),
                "created_by": "admin",
                "is_active": True,
            }
        )

        repo = NodeOverrideRepository(pool_manager=AsyncMock())
        override = repo._row_to_override(dict(row))

        assert override.robot_id is None
        assert RobotCapability.BROWSER in override.required_capabilities
        assert RobotCapability.DESKTOP in override.required_capabilities
        assert override.is_capability_based is True
        assert override.is_specific_robot is False

    def test_row_to_override_specific_robot(self):
        """Test converting row with specific robot targeting."""
        row = create_mock_record(
            {
                "workflow_id": "wf-123",
                "node_id": "node-secure",
                "robot_id": "robot-secure-1",
                "required_capabilities": "[]",
                "reason": "Must run on secure robot",
                "created_at": datetime(2024, 1, 15, 10, 0, 0),
                "created_by": "security",
                "is_active": True,
            }
        )

        repo = NodeOverrideRepository(pool_manager=AsyncMock())
        override = repo._row_to_override(dict(row))

        assert override.robot_id == "robot-secure-1"
        assert override.is_specific_robot is True
        assert override.is_capability_based is False

    def test_row_to_override_unknown_capability_skipped(self):
        """Test that unknown capabilities are logged and skipped."""
        row = create_mock_record(
            {
                "workflow_id": "wf-123",
                "node_id": "node-1",
                "robot_id": None,
                "required_capabilities": '["gpu", "unknown_cap", "browser"]',
                "reason": "",
                "created_at": None,
                "created_by": "",
                "is_active": True,
            }
        )

        repo = NodeOverrideRepository(pool_manager=AsyncMock())
        override = repo._row_to_override(dict(row))

        # Should have gpu and browser, unknown_cap skipped
        assert override.required_capabilities == frozenset(
            {RobotCapability.GPU, RobotCapability.BROWSER}
        )

    def test_row_to_override_inactive(self):
        """Test converting inactive override row."""
        row = create_mock_record(
            {
                "workflow_id": "wf-123",
                "node_id": "node-disabled",
                "robot_id": "robot-1",
                "required_capabilities": "[]",
                "reason": "Temporarily disabled",
                "created_at": datetime(2024, 1, 1, 0, 0, 0),
                "created_by": "admin",
                "is_active": False,
            }
        )

        repo = NodeOverrideRepository(pool_manager=AsyncMock())
        override = repo._row_to_override(dict(row))

        assert override.is_active is False

    def test_override_to_params_conversion(self):
        """Test converting NodeRobotOverride to database parameters."""
        override = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-gpu",
            robot_id="robot-456",
            required_capabilities=frozenset({RobotCapability.GPU}),
            reason="GPU processing required",
            created_at=datetime(2024, 2, 1, 12, 0, 0),
            created_by="ml-team",
            is_active=True,
        )

        repo = NodeOverrideRepository(pool_manager=AsyncMock())
        params = repo._override_to_params(override)

        assert params["workflow_id"] == "wf-123"
        assert params["node_id"] == "node-gpu"
        assert params["robot_id"] == "robot-456"
        assert "gpu" in params["required_capabilities"]
        assert params["reason"] == "GPU processing required"
        assert params["is_active"] is True


class TestNodeOverrideRepositorySave:
    """Tests for save operation."""

    @pytest.mark.asyncio
    async def test_save_override_success(self, mock_pool_manager, mock_connection):
        """Test successful override save (upsert)."""
        mock_connection.execute.return_value = "INSERT 1"

        override = NodeRobotOverride(
            workflow_id="wf-new",
            node_id="node-new",
            robot_id="robot-new",
        )

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        result = await repo.save(override)

        assert result.workflow_id == "wf-new"
        assert result.node_id == "node-new"

        # Verify SQL contains INSERT with ON CONFLICT
        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]
        assert "INSERT INTO node_robot_overrides" in sql
        assert "ON CONFLICT (workflow_id, node_id) DO UPDATE" in sql

    @pytest.mark.asyncio
    async def test_save_override_with_capabilities(
        self, mock_pool_manager, mock_connection
    ):
        """Test saving override with capabilities serializes to JSONB."""
        override = NodeRobotOverride(
            workflow_id="wf-123",
            node_id="node-ml",
            robot_id=None,
            required_capabilities=frozenset(
                {RobotCapability.GPU, RobotCapability.HIGH_MEMORY}
            ),
        )

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        await repo.save(override)

        call_args = mock_connection.execute.call_args
        params = call_args[0]
        # Capabilities should be JSON string
        capabilities_param = params[4]  # Position in SQL
        assert "gpu" in capabilities_param or "high_memory" in capabilities_param

    @pytest.mark.asyncio
    async def test_save_override_database_error(
        self, mock_pool_manager, mock_connection
    ):
        """Test save handles database errors properly."""
        mock_connection.execute.side_effect = Exception("Constraint violation")

        override = NodeRobotOverride(
            workflow_id="wf-err",
            node_id="node-err",
            robot_id="robot-err",
        )

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)

        with pytest.raises(Exception) as exc_info:
            await repo.save(override)

        assert "Constraint violation" in str(exc_info.value)


class TestNodeOverrideRepositoryGetByWorkflow:
    """Tests for get_by_workflow operation."""

    @pytest.mark.asyncio
    async def test_get_by_workflow_returns_list(
        self, mock_pool_manager, mock_connection, sample_override_row
    ):
        """Test getting all overrides for a workflow."""
        row2 = create_mock_record(
            {
                "workflow_id": "wf-uuid-5678",
                "node_id": "node-browser",
                "robot_id": None,
                "required_capabilities": '["browser"]',
                "reason": "Browser automation",
                "created_at": datetime(2024, 1, 13, 10, 0, 0),
                "created_by": "admin",
                "is_active": False,
            }
        )
        mock_connection.fetch.return_value = [sample_override_row, row2]

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        overrides = await repo.get_by_workflow("wf-uuid-5678")

        assert len(overrides) == 2
        assert overrides[0].node_id == "node-gpu-processing"
        assert overrides[1].node_id == "node-browser"

    @pytest.mark.asyncio
    async def test_get_by_workflow_empty(self, mock_pool_manager, mock_connection):
        """Test getting overrides for workflow with none returns empty list."""
        mock_connection.fetch.return_value = []

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        overrides = await repo.get_by_workflow("wf-no-overrides")

        assert overrides == []


class TestNodeOverrideRepositoryGetByNode:
    """Tests for get_by_node operation."""

    @pytest.mark.asyncio
    async def test_get_by_node_found(
        self, mock_pool_manager, mock_connection, sample_override_row
    ):
        """Test getting override for specific node."""
        mock_connection.fetchrow.return_value = sample_override_row

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        override = await repo.get_by_node("wf-uuid-5678", "node-gpu-processing")

        assert override is not None
        assert override.node_id == "node-gpu-processing"

        # Verify SQL query
        call_args = mock_connection.fetchrow.call_args
        sql = call_args[0][0]
        assert "workflow_id = $1 AND node_id = $2" in sql

    @pytest.mark.asyncio
    async def test_get_by_node_not_found(self, mock_pool_manager, mock_connection):
        """Test getting non-existent node override returns None."""
        mock_connection.fetchrow.return_value = None

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        override = await repo.get_by_node("wf-x", "node-y")

        assert override is None


class TestNodeOverrideRepositoryGetActiveForWorkflow:
    """Tests for get_active_for_workflow operation."""

    @pytest.mark.asyncio
    async def test_get_active_only(
        self, mock_pool_manager, mock_connection, sample_override_row
    ):
        """Test getting only active overrides for workflow."""
        mock_connection.fetch.return_value = [sample_override_row]

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        overrides = await repo.get_active_for_workflow("wf-uuid-5678")

        assert len(overrides) == 1
        assert overrides[0].is_active is True

        # Verify SQL filters by is_active
        call_args = mock_connection.fetch.call_args
        sql = call_args[0][0]
        assert "is_active = TRUE" in sql


class TestNodeOverrideRepositoryGetByRobot:
    """Tests for get_by_robot operation."""

    @pytest.mark.asyncio
    async def test_get_by_robot(
        self, mock_pool_manager, mock_connection, sample_override_row
    ):
        """Test getting all overrides targeting a specific robot."""
        mock_connection.fetch.return_value = [sample_override_row]

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        overrides = await repo.get_by_robot("robot-gpu-1234")

        assert len(overrides) == 1
        assert overrides[0].robot_id == "robot-gpu-1234"

        # Verify SQL query
        call_args = mock_connection.fetch.call_args
        sql = call_args[0][0]
        assert "robot_id = $1" in sql


class TestNodeOverrideRepositoryGetByCapability:
    """Tests for get_by_capability operation."""

    @pytest.mark.asyncio
    async def test_get_by_capability(
        self, mock_pool_manager, mock_connection, sample_override_row
    ):
        """Test getting overrides requiring a specific capability."""
        mock_connection.fetch.return_value = [sample_override_row]

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        overrides = await repo.get_by_capability(RobotCapability.GPU)

        assert len(overrides) == 1
        assert RobotCapability.GPU in overrides[0].required_capabilities

        # Verify JSONB containment query
        call_args = mock_connection.fetch.call_args
        sql = call_args[0][0]
        assert "required_capabilities @>" in sql


class TestNodeOverrideRepositoryDelete:
    """Tests for delete operation."""

    @pytest.mark.asyncio
    async def test_delete_success(self, mock_pool_manager, mock_connection):
        """Test deleting existing override returns True."""
        mock_connection.execute.return_value = "DELETE 1"

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        result = await repo.delete("wf-123", "node-456")

        assert result is True

        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]
        assert "DELETE FROM node_robot_overrides" in sql
        assert "workflow_id = $1 AND node_id = $2" in sql

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_pool_manager, mock_connection):
        """Test deleting non-existent override returns False."""
        mock_connection.execute.return_value = "DELETE 0"

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        result = await repo.delete("wf-x", "node-y")

        assert result is False


class TestNodeOverrideRepositoryActivateDeactivate:
    """Tests for activate and deactivate operations."""

    @pytest.mark.asyncio
    async def test_deactivate_success(self, mock_pool_manager, mock_connection):
        """Test deactivating (soft delete) an override."""
        mock_connection.execute.return_value = "UPDATE 1"

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        result = await repo.deactivate("wf-123", "node-456")

        assert result is True

        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]
        assert "SET is_active = FALSE" in sql

    @pytest.mark.asyncio
    async def test_deactivate_not_found(self, mock_pool_manager, mock_connection):
        """Test deactivating non-existent override returns False."""
        mock_connection.execute.return_value = "UPDATE 0"

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        result = await repo.deactivate("wf-x", "node-y")

        assert result is False

    @pytest.mark.asyncio
    async def test_activate_success(self, mock_pool_manager, mock_connection):
        """Test reactivating an override."""
        mock_connection.execute.return_value = "UPDATE 1"

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        result = await repo.activate("wf-123", "node-456")

        assert result is True

        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]
        assert "SET is_active = TRUE" in sql

    @pytest.mark.asyncio
    async def test_activate_not_found(self, mock_pool_manager, mock_connection):
        """Test activating non-existent override returns False."""
        mock_connection.execute.return_value = "UPDATE 0"

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        result = await repo.activate("wf-x", "node-y")

        assert result is False


class TestNodeOverrideRepositoryDeleteAllForWorkflow:
    """Tests for delete_all_for_workflow operation."""

    @pytest.mark.asyncio
    async def test_delete_all_for_workflow(self, mock_pool_manager, mock_connection):
        """Test deleting all overrides for a workflow."""
        mock_connection.execute.return_value = "DELETE 5"

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        count = await repo.delete_all_for_workflow("wf-123")

        assert count == 5

        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]
        assert "DELETE FROM node_robot_overrides" in sql
        assert "workflow_id = $1" in sql

    @pytest.mark.asyncio
    async def test_delete_all_for_workflow_none(
        self, mock_pool_manager, mock_connection
    ):
        """Test deleting when no overrides exist returns 0."""
        mock_connection.execute.return_value = "DELETE 0"

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        count = await repo.delete_all_for_workflow("wf-empty")

        assert count == 0


class TestNodeOverrideRepositoryDeleteAllForRobot:
    """Tests for delete_all_for_robot operation."""

    @pytest.mark.asyncio
    async def test_delete_all_for_robot(self, mock_pool_manager, mock_connection):
        """Test deleting all overrides targeting a robot (decommissioning)."""
        mock_connection.execute.return_value = "DELETE 3"

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        count = await repo.delete_all_for_robot("robot-123")

        assert count == 3

        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]
        assert "DELETE FROM node_robot_overrides" in sql
        assert "robot_id = $1" in sql


class TestNodeOverrideRepositoryGetOverrideMap:
    """Tests for get_override_map operation."""

    @pytest.mark.asyncio
    async def test_get_override_map_returns_dict(
        self, mock_pool_manager, mock_connection, sample_override_row
    ):
        """Test getting node_id to override map for workflow."""
        row2 = create_mock_record(
            {
                "workflow_id": "wf-uuid-5678",
                "node_id": "node-browser",
                "robot_id": None,
                "required_capabilities": '["browser"]',
                "reason": "Browser node",
                "created_at": datetime(2024, 1, 13, 10, 0, 0),
                "created_by": "admin",
                "is_active": True,
            }
        )
        mock_connection.fetch.return_value = [sample_override_row, row2]

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        override_map = await repo.get_override_map("wf-uuid-5678")

        assert isinstance(override_map, dict)
        assert len(override_map) == 2
        assert "node-gpu-processing" in override_map
        assert "node-browser" in override_map
        assert override_map["node-gpu-processing"].robot_id == "robot-gpu-1234"

    @pytest.mark.asyncio
    async def test_get_override_map_empty_workflow(
        self, mock_pool_manager, mock_connection
    ):
        """Test override map for workflow with no overrides."""
        mock_connection.fetch.return_value = []

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        override_map = await repo.get_override_map("wf-no-overrides")

        assert override_map == {}

    @pytest.mark.asyncio
    async def test_get_override_map_only_active(
        self, mock_pool_manager, mock_connection
    ):
        """Test override map only includes active overrides."""
        mock_connection.fetch.return_value = []

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        await repo.get_override_map("wf-123")

        # Should call get_active_for_workflow
        call_args = mock_connection.fetch.call_args
        sql = call_args[0][0]
        assert "is_active = TRUE" in sql


class TestNodeOverrideRepositoryConnectionManagement:
    """Tests for connection pool management."""

    @pytest.mark.asyncio
    async def test_connection_released_after_success(
        self, mock_pool_manager, mock_pool, mock_connection, sample_override_row
    ):
        """Test connection is released after successful operation."""
        mock_connection.fetchrow.return_value = sample_override_row

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        await repo.get_by_node("wf-123", "node-456")

        mock_pool.release.assert_awaited_once_with(mock_connection)

    @pytest.mark.asyncio
    async def test_connection_released_after_error(
        self, mock_pool_manager, mock_pool, mock_connection
    ):
        """Test connection is released even after error."""
        mock_connection.fetchrow.side_effect = Exception("DB error")

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)

        with pytest.raises(Exception):
            await repo.get_by_node("wf-123", "node-456")

        mock_pool.release.assert_awaited_once_with(mock_connection)


class TestNodeOverrideRepositoryEdgeCases:
    """Edge case tests for NodeOverrideRepository."""

    @pytest.mark.asyncio
    async def test_row_with_empty_capabilities_string(
        self, mock_pool_manager, mock_connection
    ):
        """Test handling empty capabilities string."""
        row = create_mock_record(
            {
                "workflow_id": "wf-1",
                "node_id": "node-1",
                "robot_id": "robot-1",
                "required_capabilities": "",
                "reason": None,
                "created_at": None,
                "created_by": None,
                "is_active": True,
            }
        )
        mock_connection.fetchrow.return_value = row

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        override = await repo.get_by_node("wf-1", "node-1")

        assert override is not None
        assert override.required_capabilities == frozenset()

    @pytest.mark.asyncio
    async def test_row_with_list_capabilities(self, mock_pool_manager, mock_connection):
        """Test handling capabilities as list (not JSON string)."""
        row = create_mock_record(
            {
                "workflow_id": "wf-1",
                "node_id": "node-1",
                "robot_id": "robot-1",
                "required_capabilities": ["browser", "desktop"],  # Already parsed list
                "reason": None,
                "created_at": None,
                "created_by": None,
                "is_active": True,
            }
        )
        mock_connection.fetchrow.return_value = row

        repo = NodeOverrideRepository(pool_manager=mock_pool_manager)
        override = await repo.get_by_node("wf-1", "node-1")

        # Should handle list directly
        assert override is not None
        assert RobotCapability.BROWSER in override.required_capabilities
        assert RobotCapability.DESKTOP in override.required_capabilities
