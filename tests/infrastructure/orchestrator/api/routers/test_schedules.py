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
from fastapi import HTTPException
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


# ============================================================================
# Fixtures
# ============================================================================


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
        workflow_id="wf-001",
        schedule_name="Daily Report",
        cron_expression="0 9 * * *",  # Every day at 9 AM
        enabled=True,
        priority=10,
        execution_mode="lan",
    )


# ============================================================================
# ScheduleRequest Validation Tests
# ============================================================================


class TestScheduleRequestValidation:
    """Tests for request model validation."""

    def test_valid_request(self) -> None:
        """Test valid request passes validation."""
        request = ScheduleRequest(
            workflow_id="wf-001",
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
                workflow_id="wf-001",
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
                workflow_id="wf-001",
                schedule_name="Test",
                cron_expression=cron,
            )
            assert request.cron_expression == cron

    def test_invalid_execution_mode(self) -> None:
        """Test invalid execution_mode raises error."""
        with pytest.raises(ValueError, match="execution_mode must be one of"):
            ScheduleRequest(
                workflow_id="wf-001",
                schedule_name="Test",
                cron_expression="0 * * * *",
                execution_mode="cloud",
            )

    def test_schedule_name_too_long(self) -> None:
        """Test schedule_name exceeding max length raises error."""
        with pytest.raises(ValueError):
            ScheduleRequest(
                workflow_id="wf-001",
                schedule_name="x" * 256,
                cron_expression="0 * * * *",
            )

    def test_priority_out_of_range(self) -> None:
        """Test priority outside valid range raises error."""
        with pytest.raises(ValueError):
            ScheduleRequest(
                workflow_id="wf-001",
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
        self, sample_schedule_request: ScheduleRequest
    ) -> None:
        """Test successful schedule creation."""
        response = await create_schedule(sample_schedule_request)

        assert response.schedule_id is not None
        assert response.workflow_id == "wf-001"
        assert response.schedule_name == "Daily Report"
        assert response.enabled is True
        assert response.next_run is not None
        assert response.run_count == 0

    @pytest.mark.asyncio
    async def test_create_schedule_disabled(self) -> None:
        """Test creating disabled schedule has no next_run."""
        request = ScheduleRequest(
            workflow_id="wf-001",
            schedule_name="Disabled Schedule",
            cron_expression="0 9 * * *",
            enabled=False,
        )

        response = await create_schedule(request)

        assert response.enabled is False
        assert response.next_run is None

    @pytest.mark.asyncio
    async def test_create_schedule_stores_in_memory(
        self, sample_schedule_request: ScheduleRequest
    ) -> None:
        """Test schedule is stored in memory."""
        response = await create_schedule(sample_schedule_request)

        assert response.schedule_id in _schedules
        assert _schedules[response.schedule_id]["workflow_id"] == "wf-001"


# ============================================================================
# list_schedules Endpoint Tests
# ============================================================================


class TestListSchedulesEndpoint:
    """Tests for GET /schedules endpoint using TestClient."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create FastAPI test client for schedules router."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_list_empty(self, client: TestClient) -> None:
        """Test listing empty schedules."""
        response = client.get("/schedules")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_all_schedules(self, client: TestClient) -> None:
        """Test listing all schedules."""
        # Create multiple schedules
        for i in range(3):
            await create_schedule(
                ScheduleRequest(
                    workflow_id=f"wf-{i:03d}",
                    schedule_name=f"Schedule {i}",
                    cron_expression="0 * * * *",
                )
            )

        response = client.get("/schedules")
        assert response.status_code == 200
        assert len(response.json()) == 3

    @pytest.mark.asyncio
    async def test_list_filter_by_workflow_id(self, client: TestClient) -> None:
        """Test filtering by workflow_id."""
        await create_schedule(
            ScheduleRequest(
                workflow_id="wf-001",
                schedule_name="Schedule 1",
                cron_expression="0 * * * *",
            )
        )
        await create_schedule(
            ScheduleRequest(
                workflow_id="wf-002",
                schedule_name="Schedule 2",
                cron_expression="0 * * * *",
            )
        )

        response = client.get("/schedules", params={"workflow_id": "wf-001"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["workflow_id"] == "wf-001"

    @pytest.mark.asyncio
    async def test_list_filter_by_enabled(self, client: TestClient) -> None:
        """Test filtering by enabled status."""
        await create_schedule(
            ScheduleRequest(
                workflow_id="wf-001",
                schedule_name="Enabled",
                cron_expression="0 * * * *",
                enabled=True,
            )
        )
        await create_schedule(
            ScheduleRequest(
                workflow_id="wf-002",
                schedule_name="Disabled",
                cron_expression="0 * * * *",
                enabled=False,
            )
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
    async def test_list_with_limit(self, client: TestClient) -> None:
        """Test limit parameter."""
        for i in range(10):
            await create_schedule(
                ScheduleRequest(
                    workflow_id=f"wf-{i:03d}",
                    schedule_name=f"Schedule {i}",
                    cron_expression="0 * * * *",
                )
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
        self, sample_schedule_request: ScheduleRequest
    ) -> None:
        """Test successful schedule retrieval."""
        created = await create_schedule(sample_schedule_request)

        response = await get_schedule(created.schedule_id)

        assert response.schedule_id == created.schedule_id
        assert response.schedule_name == "Daily Report"

    @pytest.mark.asyncio
    async def test_get_schedule_not_found(self) -> None:
        """Test 404 when schedule not found."""
        with pytest.raises(HTTPException) as exc_info:
            await get_schedule("non-existent-id")

        assert exc_info.value.status_code == 404


# ============================================================================
# enable_schedule / disable_schedule Endpoint Tests
# ============================================================================


class TestEnableDisableScheduleEndpoints:
    """Tests for enable/disable schedule endpoints."""

    @pytest.mark.asyncio
    async def test_enable_schedule(self) -> None:
        """Test enabling a disabled schedule."""
        created = await create_schedule(
            ScheduleRequest(
                workflow_id="wf-001",
                schedule_name="Disabled Schedule",
                cron_expression="0 9 * * *",
                enabled=False,
            )
        )
        assert created.enabled is False
        assert created.next_run is None

        response = await enable_schedule(created.schedule_id)

        assert response.enabled is True
        assert response.next_run is not None

    @pytest.mark.asyncio
    async def test_disable_schedule(self) -> None:
        """Test disabling an enabled schedule."""
        created = await create_schedule(
            ScheduleRequest(
                workflow_id="wf-001",
                schedule_name="Enabled Schedule",
                cron_expression="0 9 * * *",
                enabled=True,
            )
        )
        assert created.enabled is True

        response = await disable_schedule(created.schedule_id)

        assert response.enabled is False
        assert response.next_run is None

    @pytest.mark.asyncio
    async def test_enable_not_found(self) -> None:
        """Test 404 when enabling non-existent schedule."""
        with pytest.raises(HTTPException) as exc_info:
            await enable_schedule("non-existent-id")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_disable_not_found(self) -> None:
        """Test 404 when disabling non-existent schedule."""
        with pytest.raises(HTTPException) as exc_info:
            await disable_schedule("non-existent-id")

        assert exc_info.value.status_code == 404


# ============================================================================
# delete_schedule Endpoint Tests
# ============================================================================


class TestDeleteScheduleEndpoint:
    """Tests for DELETE /schedules/{schedule_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_schedule_success(
        self, sample_schedule_request: ScheduleRequest
    ) -> None:
        """Test successful schedule deletion."""
        created = await create_schedule(sample_schedule_request)
        schedule_id = created.schedule_id

        response = await delete_schedule(schedule_id)

        assert response["status"] == "success"
        assert schedule_id not in _schedules

    @pytest.mark.asyncio
    async def test_delete_not_found(self) -> None:
        """Test 404 when deleting non-existent schedule."""
        with pytest.raises(HTTPException) as exc_info:
            await delete_schedule("non-existent-id")

        assert exc_info.value.status_code == 404


# ============================================================================
# trigger_schedule_now Endpoint Tests
# ============================================================================


class TestTriggerScheduleNowEndpoint:
    """Tests for PUT /schedules/{schedule_id}/trigger endpoint."""

    @pytest.mark.asyncio
    async def test_trigger_schedule_success(
        self, sample_schedule_request: ScheduleRequest
    ) -> None:
        """Test successful manual trigger."""
        created = await create_schedule(sample_schedule_request)

        response = await trigger_schedule_now(created.schedule_id)

        assert response["status"] == "success"
        assert "job_id" in response

    @pytest.mark.asyncio
    async def test_trigger_not_found(self) -> None:
        """Test 404 when triggering non-existent schedule."""
        with pytest.raises(HTTPException) as exc_info:
            await trigger_schedule_now("non-existent-id")

        assert exc_info.value.status_code == 404
