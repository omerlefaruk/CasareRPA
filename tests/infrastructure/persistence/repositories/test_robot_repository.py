"""
Tests for RobotRepository PostgreSQL implementation.

Tests cover:
- CRUD operations (save, get_by_id, delete)
- Query methods (get_all, get_by_status, get_available, get_by_capability)
- Status updates (update_heartbeat, update_status, update_metrics)
- Job management (add_current_job, remove_current_job)
- Entity-to-row and row-to-entity mapping
- Error handling

All database operations are mocked using AsyncMock.
"""

from datetime import datetime
from typing import Set
from unittest.mock import AsyncMock, patch
import pytest

from casare_rpa.domain.orchestrator.entities.robot import (
    Robot,
    RobotCapability,
    RobotStatus,
)
from casare_rpa.infrastructure.persistence.repositories.robot_repository import (
    RobotRepository,
)

from .conftest import create_mock_record


class TestRobotRepositoryRowConversion:
    """Tests for row-to-entity and entity-to-row conversion."""

    def test_row_to_robot_full_data(self, sample_robot_row):
        """Test converting database row with all fields to Robot entity."""
        repo = RobotRepository(pool_manager=AsyncMock())
        robot = repo._row_to_robot(dict(sample_robot_row))

        assert robot.id == "robot-uuid-1234"
        assert robot.name == "Test Robot"
        assert robot.status == RobotStatus.ONLINE
        assert robot.environment == "production"
        assert robot.max_concurrent_jobs == 3
        assert robot.last_seen == datetime(2024, 1, 15, 10, 30, 0)
        assert RobotCapability.BROWSER in robot.capabilities
        assert RobotCapability.DESKTOP in robot.capabilities
        assert "tag1" in robot.tags
        assert robot.metrics["cpu"] == 45
        assert "wf-1" in robot.assigned_workflows
        assert "job-1" in robot.current_job_ids

    def test_row_to_robot_minimal_data(self):
        """Test converting row with minimal/default values."""
        row = create_mock_record(
            {
                "robot_id": "robot-min",
                "name": "Minimal Robot",
                "status": "offline",
                "environment": "default",
                "max_concurrent_jobs": 1,
                "last_seen": None,
                "last_heartbeat": None,
                "created_at": None,
                "capabilities": "[]",
                "tags": "[]",
                "metrics": "{}",
                "assigned_workflows": "[]",
                "current_job_ids": "[]",
            }
        )

        repo = RobotRepository(pool_manager=AsyncMock())
        robot = repo._row_to_robot(dict(row))

        assert robot.id == "robot-min"
        assert robot.status == RobotStatus.OFFLINE
        assert robot.capabilities == set()
        assert robot.tags == []

    def test_row_to_robot_unknown_status_defaults_offline(self):
        """Test that unknown status defaults to offline."""
        row = create_mock_record(
            {
                "robot_id": "robot-1",
                "name": "Robot",
                "status": "unknown_status",
                "environment": "default",
                "max_concurrent_jobs": 1,
                "capabilities": "[]",
                "tags": "[]",
                "metrics": "{}",
                "assigned_workflows": "[]",
                "current_job_ids": "[]",
            }
        )

        repo = RobotRepository(pool_manager=AsyncMock())
        robot = repo._row_to_robot(dict(row))

        assert robot.status == RobotStatus.OFFLINE

    def test_row_to_robot_unknown_capability_skipped(self):
        """Test that unknown capabilities are logged and skipped."""
        row = create_mock_record(
            {
                "robot_id": "robot-1",
                "name": "Robot",
                "status": "online",
                "environment": "default",
                "max_concurrent_jobs": 1,
                "capabilities": '["browser", "unknown_cap", "desktop"]',
                "tags": "[]",
                "metrics": "{}",
                "assigned_workflows": "[]",
                "current_job_ids": "[]",
            }
        )

        repo = RobotRepository(pool_manager=AsyncMock())
        robot = repo._row_to_robot(dict(row))

        # Should have browser and desktop, unknown_cap skipped
        assert robot.capabilities == {RobotCapability.BROWSER, RobotCapability.DESKTOP}

    def test_robot_to_params_conversion(self):
        """Test converting Robot entity to database parameters."""
        robot = Robot(
            id="robot-123",
            name="Test Robot",
            status=RobotStatus.ONLINE,
            environment="production",
            max_concurrent_jobs=5,
            tags=["fast", "reliable"],
            metrics={"cpu": 30},
            capabilities={RobotCapability.BROWSER, RobotCapability.GPU},
            assigned_workflows=["wf-1"],
            current_job_ids=["job-1"],
        )

        repo = RobotRepository(pool_manager=AsyncMock())
        params = repo._robot_to_params(robot)

        assert params["robot_id"] == "robot-123"
        assert params["name"] == "Test Robot"
        assert params["status"] == "online"
        assert params["environment"] == "production"
        assert params["max_concurrent_jobs"] == 5
        assert "fast" in params["tags"]
        # orjson serializes without spaces
        assert "cpu" in params["metrics"]
        assert "30" in params["metrics"]


class TestRobotRepositorySave:
    """Tests for save operation."""

    @pytest.mark.asyncio
    async def test_save_robot_success(
        self, mock_pool_manager, mock_connection, sample_robot_row
    ):
        """Test successful robot save (upsert)."""
        mock_connection.execute.return_value = "INSERT 1"
        robot = Robot(
            id="robot-new",
            name="New Robot",
            status=RobotStatus.ONLINE,
            max_concurrent_jobs=2,
        )

        repo = RobotRepository(pool_manager=mock_pool_manager)
        result = await repo.save(robot)

        assert result.id == "robot-new"
        mock_connection.execute.assert_awaited_once()

        # Verify SQL contains INSERT with ON CONFLICT
        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]
        assert "INSERT INTO robots" in sql
        assert "ON CONFLICT (robot_id) DO UPDATE" in sql

    @pytest.mark.asyncio
    async def test_save_robot_with_capabilities(
        self, mock_pool_manager, mock_connection
    ):
        """Test saving robot with capabilities serializes to JSONB."""
        robot = Robot(
            id="robot-cap",
            name="Capable Robot",
            capabilities={RobotCapability.BROWSER, RobotCapability.DESKTOP},
        )

        repo = RobotRepository(pool_manager=mock_pool_manager)
        await repo.save(robot)

        call_args = mock_connection.execute.call_args
        # Capabilities should be passed as JSON string
        params = call_args[0]
        # Find the capabilities param (position 10 based on SQL)
        capabilities_param = params[10]
        assert "browser" in capabilities_param or "desktop" in capabilities_param

    @pytest.mark.asyncio
    async def test_save_robot_database_error(self, mock_pool_manager, mock_connection):
        """Test save handles database errors properly."""
        mock_connection.execute.side_effect = Exception("Database connection lost")
        robot = Robot(id="robot-err", name="Error Robot")

        repo = RobotRepository(pool_manager=mock_pool_manager)

        with pytest.raises(Exception) as exc_info:
            await repo.save(robot)

        assert "Database connection lost" in str(exc_info.value)


class TestRobotRepositoryGetById:
    """Tests for get_by_id operation."""

    @pytest.mark.asyncio
    async def test_get_by_id_found(
        self, mock_pool_manager, mock_connection, sample_robot_row
    ):
        """Test getting existing robot by ID."""
        mock_connection.fetchrow.return_value = sample_robot_row

        repo = RobotRepository(pool_manager=mock_pool_manager)
        robot = await repo.get_by_id("robot-uuid-1234")

        assert robot is not None
        assert robot.id == "robot-uuid-1234"
        assert robot.name == "Test Robot"
        mock_connection.fetchrow.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, mock_pool_manager, mock_connection):
        """Test getting non-existent robot returns None."""
        mock_connection.fetchrow.return_value = None

        repo = RobotRepository(pool_manager=mock_pool_manager)
        robot = await repo.get_by_id("nonexistent-id")

        assert robot is None

    @pytest.mark.asyncio
    async def test_get_by_id_database_error(self, mock_pool_manager, mock_connection):
        """Test get_by_id handles database errors."""
        mock_connection.fetchrow.side_effect = Exception("Query timeout")

        repo = RobotRepository(pool_manager=mock_pool_manager)

        with pytest.raises(Exception) as exc_info:
            await repo.get_by_id("robot-id")

        assert "Query timeout" in str(exc_info.value)


class TestRobotRepositoryGetByHostname:
    """Tests for get_by_hostname operation."""

    @pytest.mark.asyncio
    async def test_get_by_hostname_found(
        self, mock_pool_manager, mock_connection, sample_robot_row
    ):
        """Test getting robot by hostname."""
        mock_connection.fetchrow.return_value = sample_robot_row

        repo = RobotRepository(pool_manager=mock_pool_manager)
        robot = await repo.get_by_hostname("test-host")

        assert robot is not None
        assert robot.name == "Test Robot"

        # Verify SQL query
        call_args = mock_connection.fetchrow.call_args
        sql = call_args[0][0]
        assert "hostname = $1" in sql

    @pytest.mark.asyncio
    async def test_get_by_hostname_not_found(self, mock_pool_manager, mock_connection):
        """Test getting non-existent hostname returns None."""
        mock_connection.fetchrow.return_value = None

        repo = RobotRepository(pool_manager=mock_pool_manager)
        robot = await repo.get_by_hostname("unknown-host")

        assert robot is None


class TestRobotRepositoryGetAll:
    """Tests for get_all operation."""

    @pytest.mark.asyncio
    async def test_get_all_returns_list(
        self, mock_pool_manager, mock_connection, sample_robot_row
    ):
        """Test get_all returns list of robots."""
        row2 = create_mock_record(
            {
                "robot_id": "robot-2",
                "name": "Robot 2",
                "status": "offline",
                "environment": "dev",
                "max_concurrent_jobs": 1,
                "capabilities": "[]",
                "tags": "[]",
                "metrics": "{}",
                "assigned_workflows": "[]",
                "current_job_ids": "[]",
            }
        )
        mock_connection.fetch.return_value = [sample_robot_row, row2]

        repo = RobotRepository(pool_manager=mock_pool_manager)
        robots = await repo.get_all()

        assert len(robots) == 2
        assert robots[0].id == "robot-uuid-1234"
        assert robots[1].id == "robot-2"

    @pytest.mark.asyncio
    async def test_get_all_empty(self, mock_pool_manager, mock_connection):
        """Test get_all with no robots returns empty list."""
        mock_connection.fetch.return_value = []

        repo = RobotRepository(pool_manager=mock_pool_manager)
        robots = await repo.get_all()

        assert robots == []


class TestRobotRepositoryGetByStatus:
    """Tests for get_by_status operation."""

    @pytest.mark.asyncio
    async def test_get_by_status_online(
        self, mock_pool_manager, mock_connection, sample_robot_row
    ):
        """Test filtering robots by online status."""
        mock_connection.fetch.return_value = [sample_robot_row]

        repo = RobotRepository(pool_manager=mock_pool_manager)
        robots = await repo.get_by_status(RobotStatus.ONLINE)

        assert len(robots) == 1
        assert robots[0].status == RobotStatus.ONLINE

        # Verify status value passed to query
        call_args = mock_connection.fetch.call_args
        assert call_args[0][1] == "online"


class TestRobotRepositoryGetAvailable:
    """Tests for get_available operation."""

    @pytest.mark.asyncio
    async def test_get_available_returns_robots_with_capacity(
        self, mock_pool_manager, mock_connection, sample_robot_row
    ):
        """Test getting available robots (online with capacity)."""
        mock_connection.fetch.return_value = [sample_robot_row]

        repo = RobotRepository(pool_manager=mock_pool_manager)
        robots = await repo.get_available()

        assert len(robots) == 1

        # Verify SQL checks status and capacity
        call_args = mock_connection.fetch.call_args
        sql = call_args[0][0]
        assert "status = 'online'" in sql
        assert "jsonb_array_length(current_job_ids) < max_concurrent_jobs" in sql


class TestRobotRepositoryGetByCapability:
    """Tests for get_by_capability operation."""

    @pytest.mark.asyncio
    async def test_get_by_capability_single(
        self, mock_pool_manager, mock_connection, sample_robot_row
    ):
        """Test getting robots by single capability."""
        mock_connection.fetch.return_value = [sample_robot_row]

        repo = RobotRepository(pool_manager=mock_pool_manager)
        robots = await repo.get_by_capability(RobotCapability.BROWSER)

        assert len(robots) == 1

        # Verify JSONB containment query
        call_args = mock_connection.fetch.call_args
        sql = call_args[0][0]
        assert "capabilities @>" in sql

    @pytest.mark.asyncio
    async def test_get_by_capabilities_multiple(
        self, mock_pool_manager, mock_connection, sample_robot_row
    ):
        """Test getting robots with multiple capabilities."""
        mock_connection.fetch.return_value = [sample_robot_row]

        repo = RobotRepository(pool_manager=mock_pool_manager)
        caps: Set[RobotCapability] = {RobotCapability.BROWSER, RobotCapability.DESKTOP}
        robots = await repo.get_by_capabilities(caps)

        assert len(robots) == 1

    @pytest.mark.asyncio
    async def test_get_by_capabilities_empty_returns_all(
        self, mock_pool_manager, mock_connection, sample_robot_row
    ):
        """Test empty capabilities returns all robots."""
        mock_connection.fetch.return_value = [sample_robot_row]

        repo = RobotRepository(pool_manager=mock_pool_manager)
        robots = await repo.get_by_capabilities(set())

        assert len(robots) == 1
        # Should call get_all, not filter query
        mock_connection.fetch.assert_awaited()


class TestRobotRepositoryUpdateHeartbeat:
    """Tests for update_heartbeat operation."""

    @pytest.mark.asyncio
    async def test_update_heartbeat_success(self, mock_pool_manager, mock_connection):
        """Test updating robot heartbeat timestamp."""
        mock_connection.execute.return_value = "UPDATE 1"

        repo = RobotRepository(pool_manager=mock_pool_manager)
        await repo.update_heartbeat("robot-123")

        mock_connection.execute.assert_awaited_once()

        # Verify SQL updates heartbeat, last_seen, and conditionally status
        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]
        assert "last_heartbeat = $2" in sql
        assert "last_seen = $2" in sql
        # Multi-line SQL so check for presence of status logic
        assert "status = 'offline'" in sql
        assert "'online'" in sql


class TestRobotRepositoryUpdateStatus:
    """Tests for update_status operation."""

    @pytest.mark.asyncio
    async def test_update_status_success(self, mock_pool_manager, mock_connection):
        """Test updating robot status."""
        mock_connection.execute.return_value = "UPDATE 1"

        repo = RobotRepository(pool_manager=mock_pool_manager)
        await repo.update_status("robot-123", RobotStatus.BUSY)

        call_args = mock_connection.execute.call_args
        assert call_args[0][1] == "robot-123"
        assert call_args[0][2] == "busy"


class TestRobotRepositoryUpdateMetrics:
    """Tests for update_metrics operation."""

    @pytest.mark.asyncio
    async def test_update_metrics_success(self, mock_pool_manager, mock_connection):
        """Test updating robot metrics."""
        metrics = {"cpu": 75, "memory": 80, "disk": 50}

        repo = RobotRepository(pool_manager=mock_pool_manager)
        await repo.update_metrics("robot-123", metrics)

        mock_connection.execute.assert_awaited_once()

        # Verify metrics JSON passed
        call_args = mock_connection.execute.call_args
        metrics_param = call_args[0][2]
        assert "cpu" in metrics_param
        assert "75" in metrics_param


class TestRobotRepositoryJobManagement:
    """Tests for job assignment operations."""

    @pytest.mark.asyncio
    async def test_add_current_job(self, mock_pool_manager, mock_connection):
        """Test adding job to robot's current jobs."""
        repo = RobotRepository(pool_manager=mock_pool_manager)
        await repo.add_current_job("robot-123", "job-456")

        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]

        # Verify JSONB array concatenation
        assert "current_job_ids = current_job_ids ||" in sql
        # Verify prevents duplicates
        assert "NOT current_job_ids @>" in sql
        # Verify status update when at capacity
        assert "THEN 'busy'" in sql

    @pytest.mark.asyncio
    async def test_remove_current_job(self, mock_pool_manager, mock_connection):
        """Test removing job from robot's current jobs."""
        repo = RobotRepository(pool_manager=mock_pool_manager)
        await repo.remove_current_job("robot-123", "job-456")

        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]

        # Verify JSONB array element removal
        assert "jsonb_array_elements_text" in sql
        assert "elem != $2" in sql
        # Verify status update when no longer busy
        assert "THEN 'online'" in sql


class TestRobotRepositoryDelete:
    """Tests for delete operation."""

    @pytest.mark.asyncio
    async def test_delete_success(self, mock_pool_manager, mock_connection):
        """Test deleting existing robot returns True."""
        mock_connection.execute.return_value = "DELETE 1"

        repo = RobotRepository(pool_manager=mock_pool_manager)
        result = await repo.delete("robot-123")

        assert result is True
        mock_connection.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_pool_manager, mock_connection):
        """Test deleting non-existent robot returns False."""
        mock_connection.execute.return_value = "DELETE 0"

        repo = RobotRepository(pool_manager=mock_pool_manager)
        result = await repo.delete("nonexistent")

        assert result is False


class TestRobotRepositoryMarkStaleOffline:
    """Tests for mark_stale_robots_offline operation."""

    @pytest.mark.asyncio
    async def test_mark_stale_robots_offline(self, mock_pool_manager, mock_connection):
        """Test marking stale robots as offline."""
        mock_connection.execute.return_value = "UPDATE 3"

        repo = RobotRepository(pool_manager=mock_pool_manager)
        count = await repo.mark_stale_robots_offline(timeout_seconds=60)

        assert count == 3

        call_args = mock_connection.execute.call_args
        sql = call_args[0][0]

        # Verify checks status and heartbeat
        assert "status IN ('online', 'busy')" in sql
        assert "last_heartbeat < NOW()" in sql

    @pytest.mark.asyncio
    async def test_mark_stale_robots_offline_none(
        self, mock_pool_manager, mock_connection
    ):
        """Test marking stale robots when none are stale."""
        mock_connection.execute.return_value = "UPDATE 0"

        repo = RobotRepository(pool_manager=mock_pool_manager)
        count = await repo.mark_stale_robots_offline(timeout_seconds=60)

        assert count == 0


class TestRobotRepositoryConnectionManagement:
    """Tests for connection pool management."""

    @pytest.mark.asyncio
    async def test_connection_released_after_success(
        self, mock_pool_manager, mock_pool, mock_connection, sample_robot_row
    ):
        """Test connection is released after successful operation."""
        mock_connection.fetchrow.return_value = sample_robot_row

        repo = RobotRepository(pool_manager=mock_pool_manager)
        await repo.get_by_id("robot-123")

        mock_pool.release.assert_awaited_once_with(mock_connection)

    @pytest.mark.asyncio
    async def test_connection_released_after_error(
        self, mock_pool_manager, mock_pool, mock_connection
    ):
        """Test connection is released even after error."""
        mock_connection.fetchrow.side_effect = Exception("DB error")

        repo = RobotRepository(pool_manager=mock_pool_manager)

        with pytest.raises(Exception):
            await repo.get_by_id("robot-123")

        mock_pool.release.assert_awaited_once_with(mock_connection)

    @pytest.mark.asyncio
    async def test_pool_manager_lazy_initialization(self, mock_pool, mock_connection):
        """Test repository initializes pool manager lazily if not injected."""
        # This test verifies that pool_manager can be None initially
        # and will be fetched from singleton when needed
        repo = RobotRepository(pool_manager=None)

        # Verify pool_manager is None initially
        assert repo._pool_manager is None

        # Note: Full singleton test would require integration testing
        # as it involves the actual get_pool_manager import
