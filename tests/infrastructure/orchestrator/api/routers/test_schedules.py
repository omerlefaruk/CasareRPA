"""
Tests for schedules REST API router.

Tests cover:
- Schedule creation and validation
- Cron expression validation
- Schedule listing and filtering
- Enable/disable operations
- Schedule deletion
- Manual trigger execution
"""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from casare_rpa.infrastructure.orchestrator.api.routers.schedules import (
    ScheduleRequest,
    ScheduleResponse,
    calculate_next_run,
    create_schedule,
    get_schedule,
    enable_schedule,
    disable_schedule,
    delete_schedule,
    trigger_schedule_now,
    _schedules,
    router,
)
from casare_rpa.infrastructure.orchestrator.api.auth import (
    get_current_user,
    AuthenticatedUser,
)


# ============================================================================
# Test UUIDs (valid format)
# ============================================================================

TEST_WORKFLOW_ID = "12345678-1234-5678-1234-567812345678"
TEST_WORKFLOW_ID_2 = "22222222-2222-2222-2222-222222222222"
TEST_WORKFLOW_ID_3 = "33333333-3333-3333-3333-333333333333"
TEST_SCHEDULE_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


# ============================================================================
# Mock Authentication
# ============================================================================


def get_mock_current_user() -> AuthenticatedUser:
    """Return a mock authenticated user for testing."""
    return AuthenticatedUser(
        user_id="test-user-001",
        roles=["admin", "developer"],
        tenant_id="test-tenant",
        dev_mode=True,
    )


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_user() -> AuthenticatedUser:
    """Mock authenticated user for direct function calls."""
    return get_mock_current_user()


@pytest.fixture(autouse=True)
def clear_schedules():
    """Clear in-memory schedules before and after each test.

    NOTE: This clears the module-level dict directly since we import it.
    """
    # Import fresh reference from module
    import casare_rpa.infrastructure.orchestrator.api.routers.schedules as schedules_module

    schedules_module._schedules.clear()
    yield
    schedules_module._schedules.clear()


@pytest.fixture
def sample_schedule_request() -> ScheduleRequest:
    """Sample valid schedule request."""
    return ScheduleRequest(
        workflow_id=TEST_WORKFLOW_ID,
        schedule_name="Daily Report",
        cron_expression="0 9 * * *",  # Every day at 9 AM
        enabled=True,
        priority=10,
        execution_mode="lan",
    )


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client with mocked authentication."""
    app = FastAPI()
    app.include_router(router)

    # Override authentication dependency
    app.dependency_overrides[get_current_user] = get_mock_current_user

    return TestClient(app)


# ============================================================================
# ScheduleRequest Validation Tests
# ============================================================================


class TestScheduleRequestValidation:
    """Tests for request model validation."""

    def test_valid_request(self) -> None:
        """Test valid request passes validation."""
        request = ScheduleRequest(
            workflow_id=TEST_WORKFLOW_ID,
            schedule_name="Test Schedule",
            cron_expression="0 * * * *",
        )
        assert request.schedule_name == "Test Schedule"
        assert request.enabled is True
        assert request.priority == 10

    def test_invalid_cron_expression(self) -> None:
        """Test invalid cron expression raises error."""
        with pytest.raises(ValueError, match="Invalid cron expression"):
            ScheduleRequest(
                workflow_id=TEST_WORKFLOW_ID,
                schedule_name="Test",
                cron_expression="not a cron",
            )

    def test_valid_cron_expressions(self) -> None:
        """Test various valid cron expressions."""
        valid_crons = [
            "* * * * *",  # Every minute
            "0 * * * *",  # Every hour
            "0 9 * * 1-5",  # Weekdays at 9 AM
            "0 0 1 * *",  # First of every month
            "*/5 * * * *",  # Every 5 minutes
        ]
        for cron in valid_crons:
            request = ScheduleRequest(
                workflow_id=TEST_WORKFLOW_ID,
                schedule_name="Test",
                cron_expression=cron,
            )
            assert request.cron_expression == cron

    def test_invalid_execution_mode(self) -> None:
        """Test invalid execution_mode raises error."""
        with pytest.raises(ValueError, match="execution_mode must be one of"):
            ScheduleRequest(
                workflow_id=TEST_WORKFLOW_ID,
                schedule_name="Test",
                cron_expression="0 * * * *",
                execution_mode="cloud",
            )

    def test_schedule_name_too_long(self) -> None:
        """Test schedule_name exceeding max length raises error."""
        with pytest.raises(ValueError):
            ScheduleRequest(
                workflow_id=TEST_WORKFLOW_ID,
                schedule_name="x" * 256,
                cron_expression="0 * * * *",
            )

    def test_priority_out_of_range(self) -> None:
        """Test priority outside valid range raises error."""
        with pytest.raises(ValueError):
            ScheduleRequest(
                workflow_id=TEST_WORKFLOW_ID,
                schedule_name="Test",
                cron_expression="0 * * * *",
                priority=25,
            )


# ============================================================================
# Utility Function Tests
# ============================================================================


class TestCalculateNextRun:
    """Tests for calculate_next_run function."""

    def test_calculates_next_run(self) -> None:
        """Test next run calculation."""
        base_time = datetime(2024, 1, 15, 8, 0, 0, tzinfo=timezone.utc)
        next_run = calculate_next_run("0 9 * * *", base_time)

        assert next_run.hour == 9
        assert next_run.day == 15  # Same day since it's before 9 AM

    def test_next_run_rolls_to_next_day(self) -> None:
        """Test next run rolls to next day if time passed."""
        base_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)  # 10 AM
        next_run = calculate_next_run("0 9 * * *", base_time)  # 9 AM daily

        assert next_run.day == 16  # Next day

    def test_default_base_time(self) -> None:
        """Test uses current time if no base_time provided."""
        next_run = calculate_next_run("0 * * * *")  # Every hour
        assert next_run is not None
        assert next_run > datetime.now(timezone.utc)


# ============================================================================
# create_schedule Endpoint Tests
# ============================================================================


class TestCreateScheduleEndpoint:
    """Tests for POST /schedules endpoint."""

    @pytest.mark.asyncio
    async def test_create_schedule_success(
        self, sample_schedule_request: ScheduleRequest, mock_user: AuthenticatedUser
    ) -> None:
        """Test successful schedule creation."""
        response = await create_schedule(sample_schedule_request, mock_user)

        assert response.schedule_id is not None
        assert response.workflow_id == TEST_WORKFLOW_ID
        assert response.schedule_name == "Daily Report"
        assert response.enabled is True
        assert response.next_run is not None
        assert response.run_count == 0

    @pytest.mark.asyncio
    async def test_create_schedule_disabled(self, mock_user: AuthenticatedUser) -> None:
        """Test creating disabled schedule has no next_run."""
        request = ScheduleRequest(
            workflow_id=TEST_WORKFLOW_ID,
            schedule_name="Disabled Schedule",
            cron_expression="0 9 * * *",
            enabled=False,
        )

        response = await create_schedule(request, mock_user)

        assert response.enabled is False
        assert response.next_run is None

    @pytest.mark.asyncio
    async def test_create_schedule_stores_in_memory(
        self, sample_schedule_request: ScheduleRequest, mock_user: AuthenticatedUser
    ) -> None:
        """Test schedule is stored in memory."""
        response = await create_schedule(sample_schedule_request, mock_user)

        assert response.schedule_id in _schedules
        assert _schedules[response.schedule_id]["workflow_id"] == TEST_WORKFLOW_ID

    @pytest.mark.asyncio
    async def test_create_schedule_invalid_workflow_id_format(
        self, mock_user: AuthenticatedUser
    ) -> None:
        """Test 400 when workflow_id is not a valid UUID."""
        request = ScheduleRequest(
            workflow_id="invalid-workflow-id",
            schedule_name="Test Schedule",
            cron_expression="0 9 * * *",
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_schedule(request, mock_user)

        assert exc_info.value.status_code == 400
        assert "Invalid workflow_id format" in str(exc_info.value.detail)


# ============================================================================
# list_schedules Endpoint Tests
# ============================================================================


class TestListSchedulesEndpoint:
    """Tests for GET /schedules endpoint using TestClient."""

    def test_list_empty(self, client: TestClient) -> None:
        """Test listing empty schedules."""
        response = client.get("/schedules")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_all_schedules(
        self, client: TestClient, mock_user: AuthenticatedUser
    ) -> None:
        """Test listing all schedules."""
        # Create multiple schedules with valid UUIDs
        workflow_ids = [TEST_WORKFLOW_ID, TEST_WORKFLOW_ID_2, TEST_WORKFLOW_ID_3]
        for i, wf_id in enumerate(workflow_ids):
            await create_schedule(
                ScheduleRequest(
                    workflow_id=wf_id,
                    schedule_name=f"Schedule {i}",
                    cron_expression="0 * * * *",
                ),
                mock_user,
            )

        response = client.get("/schedules")
        assert response.status_code == 200
        assert len(response.json()) == 3

    @pytest.mark.asyncio
    async def test_list_filter_by_workflow_id(
        self, client: TestClient, mock_user: AuthenticatedUser
    ) -> None:
        """Test filtering by workflow_id."""
        await create_schedule(
            ScheduleRequest(
                workflow_id=TEST_WORKFLOW_ID,
                schedule_name="Schedule 1",
                cron_expression="0 * * * *",
            ),
            mock_user,
        )
        await create_schedule(
            ScheduleRequest(
                workflow_id=TEST_WORKFLOW_ID_2,
                schedule_name="Schedule 2",
                cron_expression="0 * * * *",
            ),
            mock_user,
        )

        response = client.get("/schedules", params={"workflow_id": TEST_WORKFLOW_ID})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["workflow_id"] == TEST_WORKFLOW_ID

    @pytest.mark.asyncio
    async def test_list_filter_by_enabled(
        self, client: TestClient, mock_user: AuthenticatedUser
    ) -> None:
        """Test filtering by enabled status."""
        await create_schedule(
            ScheduleRequest(
                workflow_id=TEST_WORKFLOW_ID,
                schedule_name="Enabled",
                cron_expression="0 * * * *",
                enabled=True,
            ),
            mock_user,
        )
        await create_schedule(
            ScheduleRequest(
                workflow_id=TEST_WORKFLOW_ID_2,
                schedule_name="Disabled",
                cron_expression="0 * * * *",
                enabled=False,
            ),
            mock_user,
        )

        enabled_response = client.get("/schedules", params={"enabled": True})
        disabled_response = client.get("/schedules", params={"enabled": False})

        assert enabled_response.status_code == 200
        assert len(enabled_response.json()) == 1
        assert enabled_response.json()[0]["schedule_name"] == "Enabled"
        assert disabled_response.status_code == 200
        assert len(disabled_response.json()) == 1
        assert disabled_response.json()[0]["schedule_name"] == "Disabled"

    @pytest.mark.asyncio
    async def test_list_with_limit(
        self, client: TestClient, mock_user: AuthenticatedUser
    ) -> None:
        """Test limit parameter."""
        # Create 10 schedules with unique workflow IDs
        for i in range(10):
            # Generate valid UUID for each workflow
            wf_id = f"{i:08d}-{i:04d}-{i:04d}-{i:04d}-{i:012d}"
            await create_schedule(
                ScheduleRequest(
                    workflow_id=wf_id,
                    schedule_name=f"Schedule {i}",
                    cron_expression="0 * * * *",
                ),
                mock_user,
            )

        response = client.get("/schedules", params={"limit": 5})
        assert response.status_code == 200
        assert len(response.json()) == 5


# ============================================================================
# get_schedule Endpoint Tests
# ============================================================================


class TestGetScheduleEndpoint:
    """Tests for GET /schedules/{schedule_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_schedule_success(
        self, sample_schedule_request: ScheduleRequest, mock_user: AuthenticatedUser
    ) -> None:
        """Test successful schedule retrieval."""
        created = await create_schedule(sample_schedule_request, mock_user)

        response = await get_schedule(created.schedule_id, mock_user)

        assert response.schedule_id == created.schedule_id
        assert response.schedule_name == "Daily Report"

    @pytest.mark.asyncio
    async def test_get_schedule_not_found(self, mock_user: AuthenticatedUser) -> None:
        """Test 404 when schedule not found."""
        with pytest.raises(HTTPException) as exc_info:
            await get_schedule(TEST_SCHEDULE_ID, mock_user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_schedule_invalid_uuid_format(
        self, mock_user: AuthenticatedUser
    ) -> None:
        """Test 400 when schedule_id is not a valid UUID."""
        with pytest.raises(HTTPException) as exc_info:
            await get_schedule("non-existent-id", mock_user)

        assert exc_info.value.status_code == 400
        assert "Invalid schedule_id format" in str(exc_info.value.detail)


# ============================================================================
# enable_schedule / disable_schedule Endpoint Tests
# ============================================================================


class TestEnableDisableScheduleEndpoints:
    """Tests for enable/disable schedule endpoints."""

    @pytest.mark.asyncio
    async def test_enable_schedule(self, mock_user: AuthenticatedUser) -> None:
        """Test enabling a disabled schedule."""
        created = await create_schedule(
            ScheduleRequest(
                workflow_id=TEST_WORKFLOW_ID,
                schedule_name="Disabled Schedule",
                cron_expression="0 9 * * *",
                enabled=False,
            ),
            mock_user,
        )
        assert created.enabled is False
        assert created.next_run is None

        response = await enable_schedule(created.schedule_id, mock_user)

        assert response.enabled is True
        assert response.next_run is not None

    @pytest.mark.asyncio
    async def test_disable_schedule(self, mock_user: AuthenticatedUser) -> None:
        """Test disabling an enabled schedule."""
        created = await create_schedule(
            ScheduleRequest(
                workflow_id=TEST_WORKFLOW_ID,
                schedule_name="Enabled Schedule",
                cron_expression="0 9 * * *",
                enabled=True,
            ),
            mock_user,
        )
        assert created.enabled is True

        response = await disable_schedule(created.schedule_id, mock_user)

        assert response.enabled is False
        assert response.next_run is None

    @pytest.mark.asyncio
    async def test_enable_not_found(self, mock_user: AuthenticatedUser) -> None:
        """Test 404 when enabling non-existent schedule."""
        with pytest.raises(HTTPException) as exc_info:
            await enable_schedule(TEST_SCHEDULE_ID, mock_user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_disable_not_found(self, mock_user: AuthenticatedUser) -> None:
        """Test 404 when disabling non-existent schedule."""
        with pytest.raises(HTTPException) as exc_info:
            await disable_schedule(TEST_SCHEDULE_ID, mock_user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_enable_invalid_uuid_format(
        self, mock_user: AuthenticatedUser
    ) -> None:
        """Test 400 when enabling with invalid UUID."""
        with pytest.raises(HTTPException) as exc_info:
            await enable_schedule("non-existent-id", mock_user)

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_disable_invalid_uuid_format(
        self, mock_user: AuthenticatedUser
    ) -> None:
        """Test 400 when disabling with invalid UUID."""
        with pytest.raises(HTTPException) as exc_info:
            await disable_schedule("non-existent-id", mock_user)

        assert exc_info.value.status_code == 400


# ============================================================================
# delete_schedule Endpoint Tests
# ============================================================================


class TestDeleteScheduleEndpoint:
    """Tests for DELETE /schedules/{schedule_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_schedule_success(
        self, sample_schedule_request: ScheduleRequest, mock_user: AuthenticatedUser
    ) -> None:
        """Test successful schedule deletion."""
        created = await create_schedule(sample_schedule_request, mock_user)
        schedule_id = created.schedule_id

        response = await delete_schedule(schedule_id, mock_user)

        assert response["status"] == "success"
        assert schedule_id not in _schedules

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_user: AuthenticatedUser) -> None:
        """Test 404 when deleting non-existent schedule."""
        with pytest.raises(HTTPException) as exc_info:
            await delete_schedule(TEST_SCHEDULE_ID, mock_user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_invalid_uuid_format(
        self, mock_user: AuthenticatedUser
    ) -> None:
        """Test 400 when deleting with invalid UUID."""
        with pytest.raises(HTTPException) as exc_info:
            await delete_schedule("non-existent-id", mock_user)

        assert exc_info.value.status_code == 400


# ============================================================================
# trigger_schedule_now Endpoint Tests
# ============================================================================


class TestTriggerScheduleNowEndpoint:
    """Tests for PUT /schedules/{schedule_id}/trigger endpoint."""

    @pytest.mark.asyncio
    async def test_trigger_schedule_success(
        self, sample_schedule_request: ScheduleRequest, mock_user: AuthenticatedUser
    ) -> None:
        """Test successful manual trigger."""
        created = await create_schedule(sample_schedule_request, mock_user)

        response = await trigger_schedule_now(created.schedule_id, mock_user)

        assert response["status"] == "success"
        assert "job_id" in response

    @pytest.mark.asyncio
    async def test_trigger_not_found(self, mock_user: AuthenticatedUser) -> None:
        """Test 404 when triggering non-existent schedule."""
        with pytest.raises(HTTPException) as exc_info:
            await trigger_schedule_now(TEST_SCHEDULE_ID, mock_user)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_trigger_invalid_uuid_format(
        self, mock_user: AuthenticatedUser
    ) -> None:
        """Test 400 when triggering with invalid UUID."""
        with pytest.raises(HTTPException) as exc_info:
            await trigger_schedule_now("non-existent-id", mock_user)

        assert exc_info.value.status_code == 400


# ============================================================================
# Integration Tests via TestClient
# ============================================================================


class TestSchedulesRouterIntegration:
    """Integration tests using FastAPI TestClient with mocked auth."""

    def test_create_schedule_via_client(self, client: TestClient) -> None:
        """Test schedule creation via HTTP client."""
        response = client.post(
            "/schedules",
            json={
                "workflow_id": TEST_WORKFLOW_ID,
                "schedule_name": "Integration Test Schedule",
                "cron_expression": "0 9 * * *",
                "enabled": True,
                "priority": 10,
                "execution_mode": "lan",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["workflow_id"] == TEST_WORKFLOW_ID
        assert data["schedule_name"] == "Integration Test Schedule"

    def test_get_schedule_via_client(
        self, client: TestClient, mock_user: AuthenticatedUser
    ) -> None:
        """Test schedule retrieval via HTTP client."""
        import asyncio

        # Create schedule first
        loop = asyncio.get_event_loop()
        created = loop.run_until_complete(
            create_schedule(
                ScheduleRequest(
                    workflow_id=TEST_WORKFLOW_ID,
                    schedule_name="Test Schedule",
                    cron_expression="0 9 * * *",
                ),
                mock_user,
            )
        )

        response = client.get(f"/schedules/{created.schedule_id}")
        assert response.status_code == 200
        assert response.json()["schedule_name"] == "Test Schedule"

    def test_get_schedule_invalid_uuid_via_client(self, client: TestClient) -> None:
        """Test 400 error for invalid UUID format via HTTP client."""
        response = client.get("/schedules/invalid-schedule-id")
        assert response.status_code == 400
        assert "Invalid schedule_id format" in response.json()["detail"]

    def test_delete_schedule_via_client(
        self, client: TestClient, mock_user: AuthenticatedUser
    ) -> None:
        """Test schedule deletion via HTTP client."""
        import asyncio

        # Create schedule first
        loop = asyncio.get_event_loop()
        created = loop.run_until_complete(
            create_schedule(
                ScheduleRequest(
                    workflow_id=TEST_WORKFLOW_ID,
                    schedule_name="To Delete",
                    cron_expression="0 9 * * *",
                ),
                mock_user,
            )
        )

        response = client.delete(f"/schedules/{created.schedule_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_enable_schedule_via_client(
        self, client: TestClient, mock_user: AuthenticatedUser
    ) -> None:
        """Test schedule enable via HTTP client."""
        import asyncio

        # Create disabled schedule
        loop = asyncio.get_event_loop()
        created = loop.run_until_complete(
            create_schedule(
                ScheduleRequest(
                    workflow_id=TEST_WORKFLOW_ID,
                    schedule_name="Disabled",
                    cron_expression="0 9 * * *",
                    enabled=False,
                ),
                mock_user,
            )
        )

        response = client.put(f"/schedules/{created.schedule_id}/enable")
        assert response.status_code == 200
        assert response.json()["enabled"] is True

    def test_disable_schedule_via_client(
        self, client: TestClient, mock_user: AuthenticatedUser
    ) -> None:
        """Test schedule disable via HTTP client."""
        import asyncio

        # Create enabled schedule
        loop = asyncio.get_event_loop()
        created = loop.run_until_complete(
            create_schedule(
                ScheduleRequest(
                    workflow_id=TEST_WORKFLOW_ID,
                    schedule_name="Enabled",
                    cron_expression="0 9 * * *",
                    enabled=True,
                ),
                mock_user,
            )
        )

        response = client.put(f"/schedules/{created.schedule_id}/disable")
        assert response.status_code == 200
        assert response.json()["enabled"] is False

    def test_trigger_schedule_via_client(
        self, client: TestClient, mock_user: AuthenticatedUser
    ) -> None:
        """Test manual schedule trigger via HTTP client."""
        import asyncio

        # Create schedule
        loop = asyncio.get_event_loop()
        created = loop.run_until_complete(
            create_schedule(
                ScheduleRequest(
                    workflow_id=TEST_WORKFLOW_ID,
                    schedule_name="To Trigger",
                    cron_expression="0 9 * * *",
                ),
                mock_user,
            )
        )

        response = client.put(f"/schedules/{created.schedule_id}/trigger")
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "job_id" in response.json()
