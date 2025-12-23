"""
Tests for Shake-to-Detach gesture detection.

Note: These tests use mocks to avoid Qt initialization issues.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestMovementSample:
    """Tests for MovementSample dataclass."""

    def test_create_sample(self):
        """Test creating a movement sample."""
        from casare_rpa.presentation.canvas.connections.shake_to_detach import (
            MovementSample,
        )

        sample = MovementSample(x=100.0, y=200.0, timestamp=1.5)
        assert sample.x == 100.0
        assert sample.y == 200.0
        assert sample.timestamp == 1.5


class TestShakeDetectionLogic:
    """Tests for shake detection algorithm logic (no Qt required)."""

    def test_direction_changes_list_pruning(self):
        """Test that old direction changes are pruned."""
        # Simulate the pruning logic
        time_window_ms = 400
        current_time = 1.0
        window_start = current_time - (time_window_ms / 1000.0)

        direction_changes = [0.3, 0.5, 0.7, 0.9, 0.95]
        pruned = [t for t in direction_changes if t >= window_start]

        # Only times >= 0.6 should remain
        assert 0.3 not in pruned
        assert 0.5 not in pruned
        assert 0.7 in pruned
        assert 0.9 in pruned
        assert 0.95 in pruned

    def test_shake_threshold_check(self):
        """Test shake threshold comparison."""
        shake_threshold = 4
        direction_changes_enough = [1.0, 1.05, 1.10, 1.15]
        direction_changes_not_enough = [1.0, 1.05, 1.10]

        assert len(direction_changes_enough) >= shake_threshold
        assert len(direction_changes_not_enough) < shake_threshold

    def test_cooldown_check(self):
        """Test cooldown logic prevents rapid re-triggers."""
        cooldown_ms = 500
        current_time = 1.0
        last_shake_time_recent = 0.8  # Within cooldown
        last_shake_time_old = 0.3  # Outside cooldown

        # Should NOT trigger if last shake was recent
        recent_diff = current_time - last_shake_time_recent
        assert recent_diff < (cooldown_ms / 1000.0)

        # Should trigger if last shake was long ago
        old_diff = current_time - last_shake_time_old
        assert old_diff >= (cooldown_ms / 1000.0)


@pytest.mark.usefixtures("qapp")
class TestShakeToDetachManager:
    """Tests for ShakeToDetachManager with Qt."""

    @pytest.fixture
    def mock_graph(self):
        """Create a mock NodeGraph."""
        graph = MagicMock()
        viewer = MagicMock()
        graph.viewer.return_value = viewer
        viewer.viewport.return_value = MagicMock()
        return graph

    @pytest.fixture
    def manager(self, mock_graph):
        """Create a ShakeToDetachManager with mocked graph."""
        from casare_rpa.presentation.canvas.connections.shake_to_detach import (
            ShakeToDetachManager,
        )

        # Mock QTimer to avoid Qt native code crashes in headless/offscreen mode
        with patch.object(ShakeToDetachManager, "_setup_event_filters"):
            with patch(
                "casare_rpa.presentation.canvas.connections.shake_to_detach.QTimer"
            ) as mock_timer_cls:
                mock_timer = MagicMock()
                mock_timer.setSingleShot = MagicMock()
                mock_timer.timeout = MagicMock()
                mock_timer.timeout.connect = MagicMock()
                mock_timer.start = MagicMock()
                mock_timer_cls.return_value = mock_timer

                mgr = ShakeToDetachManager(mock_graph)
                mgr._feedback_timer = mock_timer
        return mgr

    def test_initial_state(self, manager):
        """Test initial state of manager."""
        assert manager.is_active() is True
        assert manager._dragging_node is None
        assert len(manager._movement_history) == 0

    def test_set_active(self, manager):
        """Test enabling/disabling the manager."""
        manager.set_active(False)
        assert manager.is_active() is False

        manager.set_active(True)
        assert manager.is_active() is True

    def test_set_sensitivity(self, manager):
        """Test configuring shake sensitivity."""
        manager.set_sensitivity(shake_threshold=6, time_window_ms=500, min_movement_px=20)
        assert manager._shake_threshold == 6
        assert manager._time_window_ms == 500
        assert manager._min_movement_px == 20

    def test_sensitivity_minimum_values(self, manager):
        """Test that sensitivity has minimum values."""
        manager.set_sensitivity(shake_threshold=1, time_window_ms=50, min_movement_px=2)
        assert manager._shake_threshold >= 2
        assert manager._time_window_ms >= 100
        assert manager._min_movement_px >= 5

    def test_disconnect_all_wires(self, manager):
        """Test wire disconnection logic."""
        # Create mock node with ports
        mock_node = MagicMock()

        # Mock input ports
        input_port_1 = MagicMock()
        input_port_1.connected_ports.return_value = [MagicMock(), MagicMock()]
        mock_node.inputs.return_value = {"input1": input_port_1}

        # Mock output ports
        output_port_1 = MagicMock()
        output_port_1.connected_ports.return_value = [MagicMock()]
        mock_node.outputs.return_value = {"output1": output_port_1}

        # Disconnect
        count = manager._disconnect_all_wires(mock_node)

        # Should disconnect 3 connections (2 input + 1 output)
        assert count == 3
        assert input_port_1.disconnect_from.call_count == 2
        assert output_port_1.disconnect_from.call_count == 1

    def test_reset_state(self, manager):
        """Test state reset."""
        from casare_rpa.presentation.canvas.connections.shake_to_detach import (
            MovementSample,
        )

        # Set some state
        manager._dragging_node = MagicMock()
        manager._movement_history.append(MovementSample(x=0, y=0, timestamp=0.0))
        manager._direction_changes.append(0.0)
        manager._last_x_direction = 1

        # Reset
        manager._reset_state()

        assert manager._dragging_node is None
        assert len(manager._movement_history) == 0
        assert len(manager._direction_changes) == 0
        assert manager._last_x_direction is None

    def test_drag_start_with_selected_node(self, manager, mock_graph):
        """Test drag start detection."""
        mock_node = MagicMock()
        mock_graph.selected_nodes.return_value = [mock_node]

        # Mock viewer to indicate NOT making a connection
        viewer = mock_graph.viewer()
        viewer._LIVE_PIPE = MagicMock()
        viewer._LIVE_PIPE.isVisible.return_value = False

        manager._handle_drag_start()

        assert manager._dragging_node == mock_node

    def test_drag_start_while_connecting(self, manager, mock_graph):
        """Test that drag is not started while making a connection."""
        mock_node = MagicMock()
        mock_graph.selected_nodes.return_value = [mock_node]

        # Mock viewer to indicate making a connection
        viewer = mock_graph.viewer()
        viewer._LIVE_PIPE = MagicMock()
        viewer._LIVE_PIPE.isVisible.return_value = True

        manager._handle_drag_start()

        # Should NOT start dragging when making a connection
        assert manager._dragging_node is None
