"""
Tests for StateCoordinator.
"""

import asyncio

import pytest

from casare_rpa.infrastructure.coordination import StateCoordinator


class TestStateCoordinator:
    """Test state coordination between agents."""

    @pytest.fixture
    def coordinator(self):
        """Create a fresh coordinator for each test."""
        return StateCoordinator()

    @pytest.mark.asyncio
    async def test_publish_and_get_state(self, coordinator):
        """Test publishing and retrieving state."""
        await coordinator.publish_state("agent_1", {"key": "value", "count": 42})

        state = await coordinator.get_latest_state("agent_1")

        assert state is not None
        assert state.agent_id == "agent_1"
        assert state.state["key"] == "value"
        assert state.state["count"] == 42

    @pytest.mark.asyncio
    async def test_subscribe_to_state(self, coordinator):
        """Test subscribing to state updates."""
        received_states = []

        async def subscriber():
            async for state in coordinator.subscribe_to("agent_1", timeout=1.0):
                if state is None:  # End signal
                    break
                received_states.append(state)
                if len(received_states) >= 2:
                    break

        # Start subscriber in background
        task = asyncio.create_task(subscriber())

        # Publish some states
        await asyncio.sleep(0.1)
        await coordinator.publish_state("agent_1", {"value": 1})
        await asyncio.sleep(0.1)
        await coordinator.publish_state("agent_1", {"value": 2})

        await task

        assert len(received_states) >= 2
        assert received_states[0].state["value"] == 1

    @pytest.mark.asyncio
    async def test_get_latest_state_none(self, coordinator):
        """Test getting state for non-existent agent."""
        state = await coordinator.get_latest_state("nonexistent")

        assert state is None

    @pytest.mark.asyncio
    async def test_condition_signal(self, coordinator):
        """Test condition signaling."""
        condition_id = "test_condition"

        # Wait for condition in background
        async def waiter():
            return await coordinator.wait_for_condition(condition_id, timeout=1.0)

        task = asyncio.create_task(waiter())

        # Signal the condition
        await asyncio.sleep(0.1)
        coordinator.signal_condition(condition_id)

        result = await task
        assert result is True

    @pytest.mark.asyncio
    async def test_condition_timeout(self, coordinator):
        """Test condition timeout."""
        result = await coordinator.wait_for_condition("nonexistent", timeout=0.1)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_agent_states(self, coordinator):
        """Test getting multiple agent states."""
        await coordinator.publish_state("agent_1", {"data": "a"})
        await coordinator.publish_state("agent_2", {"data": "b"})
        await coordinator.publish_state("agent_3", {"data": "c"})

        states = await coordinator.get_agent_states(["agent_1", "agent_2", "agent_4"])

        assert len(states) == 2  # agent_4 doesn't exist
        assert "agent_1" in states
        assert "agent_2" in states
        assert "agent_4" not in states

    @pytest.mark.asyncio
    async def test_clear_agent_state(self, coordinator):
        """Test clearing agent state."""
        await coordinator.publish_state("agent_1", {"data": "value"})

        # Verify state exists
        state = await coordinator.get_latest_state("agent_1")
        assert state is not None

        # Clear state
        await coordinator.clear_agent_state("agent_1")

        # Verify state is gone
        state = await coordinator.get_latest_state("agent_1")
        assert state is None

    @pytest.mark.asyncio
    async def test_state_includes_phase_and_subtask(self, coordinator):
        """Test state includes phase and subtask information."""
        await coordinator.publish_state(
            "agent_1",
            {"data": "value"},
            phase_index=2,
            subtask_id="subtask_5",
        )

        state = await coordinator.get_latest_state("agent_1")

        assert state.phase_index == 2
        assert state.subtask_id == "subtask_5"

    @pytest.mark.asyncio
    async def test_shutdown_coordinator(self, coordinator):
        """Test coordinator shutdown."""
        await coordinator.publish_state("agent_1", {"data": "value"})

        # Shutdown should not raise
        await coordinator.shutdown()

        # After shutdown, state should be cleared
        state = await coordinator.get_latest_state("agent_1")
        assert state is None


class TestResourceCoordinator:
    """Test resource coordination."""

    @pytest.fixture
    def coordinator(self):
        """Create a fresh resource coordinator."""
        from casare_rpa.infrastructure.coordination import ResourceCoordinator

        return ResourceCoordinator()

    @pytest.mark.asyncio
    async def test_register_resource(self, coordinator):
        """Test registering a resource type."""
        coordinator.register_resource("browser", 3)

        # Should not raise
        await coordinator.acquire_resource("agent_1", "browser", timeout=1.0)

    @pytest.mark.asyncio
    async def test_acquire_and_release(self, coordinator):
        """Test acquiring and releasing resources."""
        coordinator.register_resource("browser", 1)

        allocation = await coordinator.acquire_resource("agent_1", "browser", timeout=1.0)

        assert allocation is not None
        assert allocation.agent_id == "agent_1"
        assert allocation.resource_type == "browser"

        # Release
        await coordinator.release_resource(allocation.allocation_id)

    @pytest.mark.asyncio
    async def test_resource_limit(self, coordinator):
        """Test resource limit enforcement."""
        coordinator.register_resource("browser", 1)

        # First acquisition should succeed
        alloc1 = await coordinator.acquire_resource("agent_1", "browser", timeout=0.5)
        assert alloc1 is not None

        # Second should timeout (only 1 browser allowed)
        alloc2 = await coordinator.acquire_resource("agent_2", "browser", timeout=0.5)
        assert alloc2 is None

        # Release first
        await coordinator.release_resource(alloc1.allocation_id)

        # Now second should succeed
        alloc3 = await coordinator.acquire_resource("agent_2", "browser", timeout=0.5)
        assert alloc3 is not None

    @pytest.mark.asyncio
    async def test_get_active_allocations(self, coordinator):
        """Test getting active allocations."""
        coordinator.register_resource("browser", 3)

        await coordinator.acquire_resource("agent_1", "browser")
        await coordinator.acquire_resource("agent_2", "browser")

        # Get all allocations
        all_allocations = coordinator.get_active_allocations()
        assert len(all_allocations) == 2

        # Get by agent
        agent_1_allocations = coordinator.get_active_allocations("agent_1")
        assert len(agent_1_allocations) == 1
        assert agent_1_allocations[0].agent_id == "agent_1"
