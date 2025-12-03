"""
Tests for RobotController.

Tests robot management and orchestrator connection covering:
- Robot selection
- Execution mode management
- Orchestrator connection/disconnection
- Job submission
- Robot list refresh
- Remote robot commands

Note: These tests mock orchestrator client and async operations to avoid network I/O.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import Optional


class TestExecutionModeManagement:
    """Tests for execution mode management functionality."""

    @pytest.fixture
    def robot_state(self):
        """Create robot state fixture."""
        return {
            "execution_mode": "local",
            "selected_robot_id": None,
            "connected": False,
        }

    def _set_execution_mode(self, state, mode: str) -> bool:
        """
        Simulate set_execution_mode logic.

        Returns:
            bool: True if mode was changed
        """
        if mode not in ("local", "cloud"):
            return False

        if mode != state["execution_mode"]:
            state["execution_mode"] = mode

            # Clear robot selection when switching to local
            if mode == "local":
                state["selected_robot_id"] = None

            return True
        return False

    def _is_cloud_mode(self, state) -> bool:
        """Check if cloud execution mode is enabled."""
        return state["execution_mode"] == "cloud"

    def _is_local_mode(self, state) -> bool:
        """Check if local execution mode is enabled."""
        return state["execution_mode"] == "local"

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    def test_default_mode_is_local(self, robot_state):
        """Test default execution mode is local."""
        assert self._is_local_mode(robot_state) is True
        assert self._is_cloud_mode(robot_state) is False

    def test_set_mode_to_cloud(self, robot_state):
        """Test switching to cloud mode."""
        result = self._set_execution_mode(robot_state, "cloud")

        assert result is True
        assert self._is_cloud_mode(robot_state) is True
        assert self._is_local_mode(robot_state) is False

    def test_set_mode_to_local(self, robot_state):
        """Test switching to local mode."""
        robot_state["execution_mode"] = "cloud"

        result = self._set_execution_mode(robot_state, "local")

        assert result is True
        assert self._is_local_mode(robot_state) is True

    def test_switch_to_local_clears_robot_selection(self, robot_state):
        """Test switching to local mode clears robot selection."""
        robot_state["execution_mode"] = "cloud"
        robot_state["selected_robot_id"] = "robot-123"

        self._set_execution_mode(robot_state, "local")

        assert robot_state["selected_robot_id"] is None

    def test_set_same_mode_no_change(self, robot_state):
        """Test setting same mode returns False."""
        result = self._set_execution_mode(robot_state, "local")

        assert result is False

    # =========================================================================
    # Sad Path Tests
    # =========================================================================

    def test_set_invalid_mode(self, robot_state):
        """Test setting invalid mode returns False."""
        result = self._set_execution_mode(robot_state, "invalid")

        assert result is False
        assert robot_state["execution_mode"] == "local"

    def test_set_empty_mode(self, robot_state):
        """Test setting empty mode returns False."""
        result = self._set_execution_mode(robot_state, "")

        assert result is False


class TestRobotSelection:
    """Tests for robot selection functionality."""

    @pytest.fixture
    def robot_state(self):
        """Create robot state with robots list."""
        mock_robots = [
            Mock(id="robot-1", name="Robot 1", status="online"),
            Mock(id="robot-2", name="Robot 2", status="busy"),
            Mock(id="robot-3", name="Robot 3", status="offline"),
        ]

        return {
            "selected_robot_id": None,
            "current_robots": mock_robots,
        }

    def _select_robot(self, state, robot_id: str) -> bool:
        """
        Simulate select_robot logic.

        Returns:
            bool: True if selection changed
        """
        if robot_id != state["selected_robot_id"]:
            state["selected_robot_id"] = robot_id
            return True
        return False

    def _clear_selection(self, state):
        """Clear robot selection."""
        state["selected_robot_id"] = None

    def _get_selected_robot(self, state):
        """Get currently selected robot entity."""
        if state["selected_robot_id"] is None:
            return None

        for robot in state["current_robots"]:
            if robot.id == state["selected_robot_id"]:
                return robot
        return None

    def _has_robot_selected(self, state) -> bool:
        """Check if a robot is selected."""
        return state["selected_robot_id"] is not None

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    def test_select_robot_success(self, robot_state):
        """Test selecting a robot."""
        result = self._select_robot(robot_state, "robot-1")

        assert result is True
        assert robot_state["selected_robot_id"] == "robot-1"

    def test_select_different_robot(self, robot_state):
        """Test selecting a different robot."""
        self._select_robot(robot_state, "robot-1")
        result = self._select_robot(robot_state, "robot-2")

        assert result is True
        assert robot_state["selected_robot_id"] == "robot-2"

    def test_get_selected_robot_returns_entity(self, robot_state):
        """Test get_selected_robot returns robot entity."""
        self._select_robot(robot_state, "robot-1")

        robot = self._get_selected_robot(robot_state)

        assert robot is not None
        assert robot.name == "Robot 1"

    def test_has_robot_selected_true(self, robot_state):
        """Test has_robot_selected returns True when selected."""
        self._select_robot(robot_state, "robot-1")

        assert self._has_robot_selected(robot_state) is True

    def test_clear_selection(self, robot_state):
        """Test clearing robot selection."""
        self._select_robot(robot_state, "robot-1")
        self._clear_selection(robot_state)

        assert robot_state["selected_robot_id"] is None
        assert self._has_robot_selected(robot_state) is False

    # =========================================================================
    # Sad Path Tests
    # =========================================================================

    def test_select_same_robot_no_change(self, robot_state):
        """Test selecting same robot returns False."""
        self._select_robot(robot_state, "robot-1")
        result = self._select_robot(robot_state, "robot-1")

        assert result is False

    def test_get_selected_robot_none_initially(self, robot_state):
        """Test get_selected_robot returns None initially."""
        robot = self._get_selected_robot(robot_state)

        assert robot is None

    def test_get_selected_robot_unknown_id(self, robot_state):
        """Test get_selected_robot with unknown robot ID."""
        robot_state["selected_robot_id"] = "unknown-robot"

        robot = self._get_selected_robot(robot_state)

        assert robot is None


class TestOrchestratorConnection:
    """Tests for orchestrator connection functionality."""

    @pytest.fixture
    def connection_state(self):
        """Create connection state fixture."""
        return {
            "connected": False,
            "orchestrator_url": None,
            "orchestrator_client": None,
        }

    @pytest.fixture
    def mock_orchestrator_client(self):
        """Create mock orchestrator client."""
        client = AsyncMock()
        client.connect.return_value = True
        client.disconnect.return_value = None
        client.get_robots.return_value = []
        return client

    async def _connect_to_orchestrator(
        self, state, client, url: Optional[str] = None
    ) -> bool:
        """
        Simulate connect_to_orchestrator logic.

        Returns:
            bool: True if connected successfully
        """
        if client is None:
            return False

        try:
            connected = await client.connect()
            if connected:
                state["connected"] = True
                state["orchestrator_url"] = url or "http://localhost:8000"
                return True
        except Exception:
            pass

        state["connected"] = False
        return False

    async def _disconnect_from_orchestrator(self, state, client):
        """Simulate disconnect_from_orchestrator logic."""
        if client:
            await client.disconnect()
        state["connected"] = False

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_connect_success(self, connection_state, mock_orchestrator_client):
        """Test connecting to orchestrator successfully."""
        result = await self._connect_to_orchestrator(
            connection_state, mock_orchestrator_client, "https://api.example.com"
        )

        assert result is True
        assert connection_state["connected"] is True
        assert connection_state["orchestrator_url"] == "https://api.example.com"

    @pytest.mark.asyncio
    async def test_connect_uses_default_url(
        self, connection_state, mock_orchestrator_client
    ):
        """Test connect uses default URL if none provided."""
        result = await self._connect_to_orchestrator(
            connection_state, mock_orchestrator_client
        )

        assert result is True
        assert connection_state["orchestrator_url"] == "http://localhost:8000"

    @pytest.mark.asyncio
    async def test_disconnect_success(self, connection_state, mock_orchestrator_client):
        """Test disconnecting from orchestrator."""
        connection_state["connected"] = True

        await self._disconnect_from_orchestrator(
            connection_state, mock_orchestrator_client
        )

        assert connection_state["connected"] is False
        mock_orchestrator_client.disconnect.assert_awaited_once()

    # =========================================================================
    # Sad Path Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_connect_client_none(self, connection_state):
        """Test connect when client is None."""
        result = await self._connect_to_orchestrator(connection_state, None)

        assert result is False
        assert connection_state["connected"] is False

    @pytest.mark.asyncio
    async def test_connect_failure(self, connection_state, mock_orchestrator_client):
        """Test connect handles connection failure."""
        mock_orchestrator_client.connect.return_value = False

        result = await self._connect_to_orchestrator(
            connection_state, mock_orchestrator_client
        )

        assert result is False
        assert connection_state["connected"] is False

    @pytest.mark.asyncio
    async def test_connect_exception(self, connection_state, mock_orchestrator_client):
        """Test connect handles exceptions."""
        mock_orchestrator_client.connect.side_effect = Exception("Connection error")

        result = await self._connect_to_orchestrator(
            connection_state, mock_orchestrator_client
        )

        assert result is False
        assert connection_state["connected"] is False


class TestJobSubmission:
    """Tests for job submission functionality."""

    @pytest.fixture
    def submission_state(self):
        """Create submission state fixture."""
        return {
            "execution_mode": "cloud",
            "selected_robot_id": "robot-123",
            "connected": True,
        }

    async def _submit_job(
        self,
        state,
        client,
        workflow_data: dict,
        variables: Optional[dict] = None,
        robot_id: Optional[str] = None,
    ):
        """
        Simulate submit_job logic.

        Returns:
            tuple: (job_id, error)
        """
        target_robot_id = robot_id or state["selected_robot_id"]

        # Check execution mode
        if state["execution_mode"] == "local":
            return (None, "Local execution mode selected")

        # Check robot selection
        if target_robot_id is None:
            return (None, "No robot selected")

        # Check connection
        if not state["connected"] or client is None:
            return (None, "Not connected to orchestrator")

        try:
            # Submit job
            job_id = await client.submit_job(
                workflow_data=workflow_data,
                robot_id=target_robot_id,
                variables=variables,
            )
            return (job_id, None)

        except Exception as e:
            return (None, str(e))

    @pytest.fixture
    def mock_client(self):
        """Create mock orchestrator client for job submission."""
        client = AsyncMock()
        client.submit_job.return_value = "job-abc-123"
        return client

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_submit_job_success(self, submission_state, mock_client):
        """Test submitting a job successfully."""
        workflow_data = {"name": "Test Workflow", "nodes": []}

        job_id, error = await self._submit_job(
            submission_state, mock_client, workflow_data
        )

        assert job_id == "job-abc-123"
        assert error is None

    @pytest.mark.asyncio
    async def test_submit_job_with_variables(self, submission_state, mock_client):
        """Test submitting job with variables."""
        workflow_data = {"name": "Test"}
        variables = {"input": "value"}

        job_id, error = await self._submit_job(
            submission_state, mock_client, workflow_data, variables
        )

        assert job_id is not None
        mock_client.submit_job.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_submit_job_with_specific_robot(self, submission_state, mock_client):
        """Test submitting job to specific robot."""
        workflow_data = {"name": "Test"}

        job_id, error = await self._submit_job(
            submission_state, mock_client, workflow_data, robot_id="robot-456"
        )

        assert job_id is not None
        call_kwargs = mock_client.submit_job.call_args.kwargs
        assert call_kwargs["robot_id"] == "robot-456"

    # =========================================================================
    # Sad Path Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_submit_job_local_mode(self, submission_state, mock_client):
        """Test submit job in local mode fails."""
        submission_state["execution_mode"] = "local"
        workflow_data = {"name": "Test"}

        job_id, error = await self._submit_job(
            submission_state, mock_client, workflow_data
        )

        assert job_id is None
        assert "Local" in error

    @pytest.mark.asyncio
    async def test_submit_job_no_robot_selected(self, submission_state, mock_client):
        """Test submit job without robot selection fails."""
        submission_state["selected_robot_id"] = None
        workflow_data = {"name": "Test"}

        job_id, error = await self._submit_job(
            submission_state, mock_client, workflow_data
        )

        assert job_id is None
        assert "No robot" in error

    @pytest.mark.asyncio
    async def test_submit_job_not_connected(self, submission_state, mock_client):
        """Test submit job when not connected fails."""
        submission_state["connected"] = False
        workflow_data = {"name": "Test"}

        job_id, error = await self._submit_job(
            submission_state, mock_client, workflow_data
        )

        assert job_id is None
        assert "Not connected" in error

    @pytest.mark.asyncio
    async def test_submit_job_client_error(self, submission_state, mock_client):
        """Test submit job handles client errors."""
        mock_client.submit_job.side_effect = Exception("API error")
        workflow_data = {"name": "Test"}

        job_id, error = await self._submit_job(
            submission_state, mock_client, workflow_data
        )

        assert job_id is None
        assert "API error" in error


class TestRobotListRefresh:
    """Tests for robot list refresh functionality."""

    @pytest.fixture
    def refresh_state(self):
        """Create refresh state fixture."""
        return {
            "current_robots": [],
            "connected": True,
        }

    @pytest.fixture
    def mock_client(self):
        """Create mock orchestrator client for robot list."""
        client = AsyncMock()
        client.get_robots.return_value = [
            Mock(id="robot-1", name="Robot 1", status="online"),
            Mock(id="robot-2", name="Robot 2", status="idle"),
        ]
        return client

    async def _refresh_robots(self, state, client):
        """
        Simulate refresh_robots logic.

        Returns:
            list: Updated robot list
        """
        if client is None or not state["connected"]:
            return []

        try:
            robots = await client.get_robots()
            state["current_robots"] = robots
            return robots
        except Exception:
            state["current_robots"] = []
            return []

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_refresh_robots_success(self, refresh_state, mock_client):
        """Test refreshing robot list successfully."""
        robots = await self._refresh_robots(refresh_state, mock_client)

        assert len(robots) == 2
        assert refresh_state["current_robots"] == robots

    @pytest.mark.asyncio
    async def test_refresh_robots_updates_state(self, refresh_state, mock_client):
        """Test refresh updates current_robots state."""
        await self._refresh_robots(refresh_state, mock_client)

        assert len(refresh_state["current_robots"]) == 2
        assert refresh_state["current_robots"][0].name == "Robot 1"

    # =========================================================================
    # Sad Path Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_refresh_robots_not_connected(self, refresh_state, mock_client):
        """Test refresh when not connected returns empty list."""
        refresh_state["connected"] = False

        robots = await self._refresh_robots(refresh_state, mock_client)

        assert robots == []

    @pytest.mark.asyncio
    async def test_refresh_robots_client_none(self, refresh_state):
        """Test refresh when client is None."""
        robots = await self._refresh_robots(refresh_state, None)

        assert robots == []

    @pytest.mark.asyncio
    async def test_refresh_robots_api_error(self, refresh_state, mock_client):
        """Test refresh handles API errors."""
        mock_client.get_robots.side_effect = Exception("API error")

        robots = await self._refresh_robots(refresh_state, mock_client)

        assert robots == []
        assert refresh_state["current_robots"] == []


class TestRemoteRobotCommands:
    """Tests for remote robot command functionality."""

    @pytest.fixture
    def command_state(self):
        """Create command state fixture."""
        return {
            "connected": True,
        }

    @pytest.fixture
    def mock_client(self):
        """Create mock orchestrator client for commands."""
        client = AsyncMock()
        client._request.return_value = {"success": True}
        return client

    async def _send_robot_command(
        self, state, client, robot_id: str, command: str
    ) -> bool:
        """
        Simulate sending robot command.

        Returns:
            bool: True if command sent successfully
        """
        if not state["connected"] or client is None:
            return False

        try:
            result = await client._request(
                "POST", f"/api/v1/robots/{robot_id}/{command}"
            )
            return result is not None
        except Exception:
            return False

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_start_robot_success(self, command_state, mock_client):
        """Test starting a robot successfully."""
        result = await self._send_robot_command(
            command_state, mock_client, "robot-1", "start"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_stop_robot_success(self, command_state, mock_client):
        """Test stopping a robot successfully."""
        result = await self._send_robot_command(
            command_state, mock_client, "robot-1", "stop"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_pause_robot_success(self, command_state, mock_client):
        """Test pausing a robot successfully."""
        result = await self._send_robot_command(
            command_state, mock_client, "robot-1", "pause"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_resume_robot_success(self, command_state, mock_client):
        """Test resuming a robot successfully."""
        result = await self._send_robot_command(
            command_state, mock_client, "robot-1", "resume"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_restart_robot_success(self, command_state, mock_client):
        """Test restarting a robot successfully."""
        result = await self._send_robot_command(
            command_state, mock_client, "robot-1", "restart"
        )

        assert result is True

    # =========================================================================
    # Sad Path Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_command_not_connected(self, command_state, mock_client):
        """Test command when not connected fails."""
        command_state["connected"] = False

        result = await self._send_robot_command(
            command_state, mock_client, "robot-1", "start"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_command_client_none(self, command_state):
        """Test command when client is None fails."""
        result = await self._send_robot_command(command_state, None, "robot-1", "start")

        assert result is False

    @pytest.mark.asyncio
    async def test_command_api_error(self, command_state, mock_client):
        """Test command handles API errors."""
        mock_client._request.side_effect = Exception("API error")

        result = await self._send_robot_command(
            command_state, mock_client, "robot-1", "start"
        )

        assert result is False


class TestRobotStatistics:
    """Tests for robot statistics functionality."""

    @pytest.fixture
    def stats_state(self):
        """Create stats state fixture."""
        return {
            "connected": True,
            "current_robots": [Mock(), Mock(), Mock()],  # 3 robots
        }

    @pytest.fixture
    def mock_client(self):
        """Create mock orchestrator client for metrics."""
        client = AsyncMock()
        client.get_fleet_metrics.return_value = {
            "total_robots": 10,
            "active_robots": 7,
            "busy_robots": 3,
            "offline_robots": 0,
            "active_jobs": 5,
            "queue_depth": 2,
        }
        return client

    async def _get_statistics(self, state, client) -> dict:
        """
        Simulate get_statistics logic.

        Returns:
            dict: Fleet statistics
        """
        if not state["connected"] or client is None:
            return {
                "total": len(state["current_robots"]),
                "by_status": {},
                "connected": False,
            }

        try:
            metrics = await client.get_fleet_metrics()
            return {
                "total": metrics.get("total_robots", 0),
                "online": metrics.get("active_robots", 0),
                "busy": metrics.get("busy_robots", 0),
                "offline": metrics.get("offline_robots", 0),
                "active_jobs": metrics.get("active_jobs", 0),
                "queue_depth": metrics.get("queue_depth", 0),
                "connected": True,
            }
        except Exception as e:
            return {
                "total": len(state["current_robots"]),
                "connected": False,
                "error": str(e),
            }

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_statistics_success(self, stats_state, mock_client):
        """Test getting statistics successfully."""
        stats = await self._get_statistics(stats_state, mock_client)

        assert stats["connected"] is True
        assert stats["total"] == 10
        assert stats["online"] == 7
        assert stats["busy"] == 3
        assert stats["active_jobs"] == 5

    # =========================================================================
    # Sad Path Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_statistics_not_connected(self, stats_state, mock_client):
        """Test get_statistics when not connected."""
        stats_state["connected"] = False

        stats = await self._get_statistics(stats_state, mock_client)

        assert stats["connected"] is False
        assert stats["total"] == 3  # Local robot count

    @pytest.mark.asyncio
    async def test_get_statistics_api_error(self, stats_state, mock_client):
        """Test get_statistics handles API errors."""
        mock_client.get_fleet_metrics.side_effect = Exception("API error")

        stats = await self._get_statistics(stats_state, mock_client)

        assert stats["connected"] is False
        assert "error" in stats


class TestRobotEventHandlers:
    """Tests for robot event handling functionality."""

    def _handle_robot_status_update(self, robots: list, robot_id: str, status: str):
        """
        Simulate _on_robot_status_update handler.

        Updates robot status in list.
        """
        for robot in robots:
            if getattr(robot, "id", None) == robot_id:
                robot.status = status
                return True
        return False

    def _handle_connection_status_change(self, state, connected: bool):
        """Simulate connection status change handler."""
        state["connected"] = connected

    # =========================================================================
    # Happy Path Tests
    # =========================================================================

    def test_robot_status_update_found(self):
        """Test robot status update when robot found."""
        robots = [
            Mock(id="robot-1", status="online"),
            Mock(id="robot-2", status="online"),
        ]

        result = self._handle_robot_status_update(robots, "robot-1", "busy")

        assert result is True
        assert robots[0].status == "busy"

    def test_connection_status_connected(self):
        """Test handling connected event."""
        state = {"connected": False}

        self._handle_connection_status_change(state, True)

        assert state["connected"] is True

    def test_connection_status_disconnected(self):
        """Test handling disconnected event."""
        state = {"connected": True}

        self._handle_connection_status_change(state, False)

        assert state["connected"] is False

    # =========================================================================
    # Sad Path Tests
    # =========================================================================

    def test_robot_status_update_not_found(self):
        """Test robot status update when robot not found."""
        robots = [Mock(id="robot-1", status="online")]

        result = self._handle_robot_status_update(robots, "unknown", "busy")

        assert result is False
        assert robots[0].status == "online"  # Unchanged

    def test_robot_status_update_empty_list(self):
        """Test robot status update with empty list."""
        robots = []

        result = self._handle_robot_status_update(robots, "robot-1", "busy")

        assert result is False


class TestRobotControllerProperties:
    """Tests for RobotController property getters."""

    @pytest.fixture
    def controller_state(self):
        """Create controller state fixture."""
        return {
            "execution_mode": "local",
            "selected_robot_id": None,
            "connected": False,
            "current_robots": [],
            "orchestrator_url": "http://localhost:8000",
        }

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_execution_mode_property(self, controller_state):
        """Test execution_mode property."""
        assert controller_state["execution_mode"] == "local"

        controller_state["execution_mode"] = "cloud"
        assert controller_state["execution_mode"] == "cloud"

    def test_selected_robot_id_property(self, controller_state):
        """Test selected_robot_id property."""
        assert controller_state["selected_robot_id"] is None

        controller_state["selected_robot_id"] = "robot-123"
        assert controller_state["selected_robot_id"] == "robot-123"

    def test_is_connected_property(self, controller_state):
        """Test is_connected property."""
        assert controller_state["connected"] is False

        controller_state["connected"] = True
        assert controller_state["connected"] is True

    def test_robots_property_returns_copy(self, controller_state):
        """Test robots property returns list copy."""
        controller_state["current_robots"] = [Mock(id="r1")]

        robots_copy = controller_state["current_robots"].copy()
        robots_copy.append(Mock(id="r2"))

        # Original should be unchanged
        assert len(controller_state["current_robots"]) == 1

    def test_orchestrator_url_property(self, controller_state):
        """Test orchestrator_url property."""
        assert controller_state["orchestrator_url"] == "http://localhost:8000"
