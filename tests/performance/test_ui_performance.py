"""
UI Performance Baseline Tests.

Tests the performance of UI components:
- SignalCoordinator initialization time
- PanelManager initialization time
- Action dispatch latency
- Panel toggle latency

These tests mock heavy Qt components to focus on Python logic performance.

Run with: pytest tests/performance/test_ui_performance.py -v
"""

import time
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch, PropertyMock

import pytest


# Performance thresholds
MAX_COORDINATOR_INIT_TIME_MS = 50.0
MAX_PANEL_MANAGER_INIT_TIME_MS = 50.0
MAX_ACTION_DISPATCH_TIME_MS = 5.0
MAX_PANEL_TOGGLE_TIME_MS = 10.0


def create_mock_main_window():
    """Create a comprehensive mock MainWindow for testing."""
    mock_mw = MagicMock()

    # Mock controllers
    mock_mw._workflow_controller = MagicMock()
    mock_mw._execution_controller = MagicMock()
    mock_mw._node_controller = MagicMock()
    mock_mw._viewport_controller = MagicMock()
    mock_mw._menu_controller = MagicMock()
    mock_mw._selector_controller = MagicMock()
    mock_mw._panel_controller = MagicMock()
    mock_mw._ui_state_controller = MagicMock()
    mock_mw._project_controller = MagicMock()

    # Mock panels
    mock_mw._bottom_panel = MagicMock()
    mock_mw._side_panel = MagicMock()
    mock_mw._debug_panel = MagicMock()
    mock_mw._process_mining_panel = MagicMock()
    mock_mw._robot_picker_panel = MagicMock()
    mock_mw._analytics_panel = MagicMock()

    # Mock other components
    mock_mw._central_widget = MagicMock()
    mock_mw._auto_connect_enabled = False
    mock_mw._quick_node_manager = MagicMock()
    mock_mw._status_bar_manager = MagicMock()
    mock_mw._fleet_dashboard_manager = MagicMock()
    mock_mw.graph = MagicMock()

    # Mock actions
    mock_mw.action_record_workflow = MagicMock()
    mock_mw.action_start_listening = MagicMock()
    mock_mw.action_stop_listening = MagicMock()

    # Mock methods
    mock_mw.show_status = MagicMock()
    mock_mw.set_modified = MagicMock()
    mock_mw.get_graph = MagicMock(return_value=mock_mw.graph)
    mock_mw.validate_current_workflow = MagicMock()
    mock_mw.show_minimap = MagicMock()
    mock_mw.hide_minimap = MagicMock()
    mock_mw.save_as_scenario_requested = MagicMock()

    return mock_mw


class TestSignalCoordinatorPerformance:
    """Test SignalCoordinator initialization and dispatch performance."""

    def test_initialization_time(self) -> None:
        """Test SignalCoordinator initialization is fast."""
        mock_mw = create_mock_main_window()

        from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
            SignalCoordinator,
        )

        start = time.perf_counter()
        coordinator = SignalCoordinator(mock_mw)
        elapsed = time.perf_counter() - start

        elapsed_ms = elapsed * 1000

        assert elapsed_ms < MAX_COORDINATOR_INIT_TIME_MS, (
            f"SignalCoordinator init took {elapsed_ms:.2f}ms "
            f"(threshold: {MAX_COORDINATOR_INIT_TIME_MS}ms)"
        )

    def test_workflow_action_dispatch_time(self) -> None:
        """Test workflow action dispatch latency."""
        mock_mw = create_mock_main_window()

        from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
            SignalCoordinator,
        )

        coordinator = SignalCoordinator(mock_mw)

        # Warm up
        coordinator.on_new_workflow()

        # Measure dispatch time
        iterations = 100
        start = time.perf_counter()
        for _ in range(iterations):
            coordinator.on_new_workflow()
            coordinator.on_save_workflow()
            coordinator.on_open_workflow()
        elapsed = time.perf_counter() - start

        avg_time_ms = (elapsed / (iterations * 3)) * 1000

        assert avg_time_ms < MAX_ACTION_DISPATCH_TIME_MS, (
            f"Workflow action dispatch took {avg_time_ms:.3f}ms "
            f"(threshold: {MAX_ACTION_DISPATCH_TIME_MS}ms)"
        )

    def test_execution_action_dispatch_time(self) -> None:
        """Test execution action dispatch latency."""
        mock_mw = create_mock_main_window()

        from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
            SignalCoordinator,
        )

        coordinator = SignalCoordinator(mock_mw)

        iterations = 100
        start = time.perf_counter()
        for _ in range(iterations):
            coordinator.on_run_workflow()
            coordinator.on_stop_workflow()
            coordinator.on_pause_workflow(True)
            coordinator.on_pause_workflow(False)
        elapsed = time.perf_counter() - start

        avg_time_ms = (elapsed / (iterations * 4)) * 1000

        assert avg_time_ms < MAX_ACTION_DISPATCH_TIME_MS, (
            f"Execution action dispatch took {avg_time_ms:.3f}ms "
            f"(threshold: {MAX_ACTION_DISPATCH_TIME_MS}ms)"
        )

    def test_debug_action_dispatch_time(self) -> None:
        """Test debug action dispatch latency."""
        mock_mw = create_mock_main_window()

        from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
            SignalCoordinator,
        )

        coordinator = SignalCoordinator(mock_mw)

        iterations = 100
        start = time.perf_counter()
        for _ in range(iterations):
            coordinator.on_debug_workflow()
            coordinator.on_debug_step_over()
            coordinator.on_debug_step_into()
            coordinator.on_debug_step_out()
            coordinator.on_debug_continue()
        elapsed = time.perf_counter() - start

        avg_time_ms = (elapsed / (iterations * 5)) * 1000

        assert avg_time_ms < MAX_ACTION_DISPATCH_TIME_MS, (
            f"Debug action dispatch took {avg_time_ms:.3f}ms "
            f"(threshold: {MAX_ACTION_DISPATCH_TIME_MS}ms)"
        )

    def test_node_action_dispatch_time(self) -> None:
        """Test node action dispatch latency."""
        mock_mw = create_mock_main_window()

        from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
            SignalCoordinator,
        )

        coordinator = SignalCoordinator(mock_mw)

        # Mock QApplication.focusWidget to return None (no text widget)
        with patch(
            "casare_rpa.presentation.canvas.coordinators.signal_coordinator.QApplication"
        ) as mock_app:
            mock_app.focusWidget.return_value = None

            iterations = 100
            start = time.perf_counter()
            for _ in range(iterations):
                coordinator.on_select_nearest_node()
                coordinator.on_toggle_collapse_nearest()
                coordinator.on_toggle_disable_node()
            elapsed = time.perf_counter() - start

            avg_time_ms = (elapsed / (iterations * 3)) * 1000

            assert avg_time_ms < MAX_ACTION_DISPATCH_TIME_MS, (
                f"Node action dispatch took {avg_time_ms:.3f}ms "
                f"(threshold: {MAX_ACTION_DISPATCH_TIME_MS}ms)"
            )


class TestPanelManagerPerformance:
    """Test PanelManager initialization and operations."""

    def test_initialization_time(self) -> None:
        """Test PanelManager initialization is fast."""
        mock_mw = create_mock_main_window()

        from casare_rpa.presentation.canvas.managers.panel_manager import (
            PanelManager,
        )

        start = time.perf_counter()
        manager = PanelManager(mock_mw)
        elapsed = time.perf_counter() - start

        elapsed_ms = elapsed * 1000

        assert elapsed_ms < MAX_PANEL_MANAGER_INIT_TIME_MS, (
            f"PanelManager init took {elapsed_ms:.2f}ms "
            f"(threshold: {MAX_PANEL_MANAGER_INIT_TIME_MS}ms)"
        )

    def test_panel_toggle_latency(self) -> None:
        """Test panel toggle operations are fast."""
        mock_mw = create_mock_main_window()

        from casare_rpa.presentation.canvas.managers.panel_manager import (
            PanelManager,
        )

        manager = PanelManager(mock_mw)

        iterations = 100
        start = time.perf_counter()
        for _ in range(iterations):
            manager.show_bottom_panel()
            manager.hide_bottom_panel()
            manager.toggle_bottom_panel(True)
            manager.toggle_bottom_panel(False)
        elapsed = time.perf_counter() - start

        avg_time_ms = (elapsed / (iterations * 4)) * 1000

        assert avg_time_ms < MAX_PANEL_TOGGLE_TIME_MS, (
            f"Panel toggle took {avg_time_ms:.3f}ms "
            f"(threshold: {MAX_PANEL_TOGGLE_TIME_MS}ms)"
        )

    def test_side_panel_operations(self) -> None:
        """Test side panel operations performance."""
        mock_mw = create_mock_main_window()

        from casare_rpa.presentation.canvas.managers.panel_manager import (
            PanelManager,
        )

        manager = PanelManager(mock_mw)

        iterations = 100
        start = time.perf_counter()
        for _ in range(iterations):
            manager.show_side_panel()
            manager.hide_side_panel()
            manager.show_debug_tab()
            manager.show_analytics_tab()
        elapsed = time.perf_counter() - start

        avg_time_ms = (elapsed / (iterations * 4)) * 1000

        assert avg_time_ms < MAX_PANEL_TOGGLE_TIME_MS, (
            f"Side panel operations took {avg_time_ms:.3f}ms "
            f"(threshold: {MAX_PANEL_TOGGLE_TIME_MS}ms)"
        )

    def test_panel_tab_toggle_performance(self) -> None:
        """Test toggling between panel tabs."""
        mock_mw = create_mock_main_window()

        from casare_rpa.presentation.canvas.managers.panel_manager import (
            PanelManager,
        )

        manager = PanelManager(mock_mw)

        tab_names = ["variables", "output", "log", "validation", "history"]

        iterations = 50
        start = time.perf_counter()
        for _ in range(iterations):
            for tab in tab_names:
                manager.toggle_panel_tab(tab)
        elapsed = time.perf_counter() - start

        avg_time_ms = (elapsed / (iterations * len(tab_names))) * 1000

        assert avg_time_ms < MAX_PANEL_TOGGLE_TIME_MS, (
            f"Panel tab toggle took {avg_time_ms:.3f}ms "
            f"(threshold: {MAX_PANEL_TOGGLE_TIME_MS}ms)"
        )

    def test_panel_visibility_check_performance(self) -> None:
        """Test panel visibility checks are fast."""
        mock_mw = create_mock_main_window()
        mock_mw._bottom_panel.isVisible.return_value = True
        mock_mw._side_panel.isVisible.return_value = False

        from casare_rpa.presentation.canvas.managers.panel_manager import (
            PanelManager,
        )

        manager = PanelManager(mock_mw)

        iterations = 10000
        start = time.perf_counter()
        for _ in range(iterations):
            _ = manager.is_bottom_panel_visible()
            _ = manager.is_side_panel_visible()
        elapsed = time.perf_counter() - start

        avg_time_us = (elapsed / (iterations * 2)) * 1_000_000

        # Visibility checks should be very fast (< 25 microseconds)
        # Mock overhead can be ~15us on Windows
        assert avg_time_us < 25, (
            f"Visibility check took {avg_time_us:.2f}us " f"(threshold: 25us)"
        )


class TestActionHandlerPerformance:
    """Test action handler performance patterns."""

    def test_multiple_handlers_sequence(self) -> None:
        """Test calling multiple handlers in sequence."""
        mock_mw = create_mock_main_window()

        from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
            SignalCoordinator,
        )

        coordinator = SignalCoordinator(mock_mw)

        # Simulate a typical user workflow
        handlers = [
            coordinator.on_new_workflow,
            coordinator.on_save_workflow,
            coordinator.on_run_workflow,
            coordinator.on_stop_workflow,
            coordinator.on_save_workflow,
        ]

        iterations = 50
        start = time.perf_counter()
        for _ in range(iterations):
            for handler in handlers:
                handler()
        elapsed = time.perf_counter() - start

        avg_time_ms = (elapsed / (iterations * len(handlers))) * 1000

        assert avg_time_ms < MAX_ACTION_DISPATCH_TIME_MS, (
            f"Sequential handler execution took {avg_time_ms:.3f}ms avg "
            f"(threshold: {MAX_ACTION_DISPATCH_TIME_MS}ms)"
        )

    def test_conditional_dispatch_overhead(self) -> None:
        """
        Test overhead of conditional controller checks.

        Most handlers check if controller exists before calling.
        This measures that overhead.
        """
        mock_mw = create_mock_main_window()

        from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
            SignalCoordinator,
        )

        coordinator = SignalCoordinator(mock_mw)

        # Test with controller present
        iterations = 1000
        start = time.perf_counter()
        for _ in range(iterations):
            coordinator.on_new_workflow()
        with_controller_time = time.perf_counter() - start

        # Test with controller absent
        mock_mw._workflow_controller = None
        start = time.perf_counter()
        for _ in range(iterations):
            coordinator.on_new_workflow()
        without_controller_time = time.perf_counter() - start

        # Both should be fast
        with_time_us = (with_controller_time / iterations) * 1_000_000
        without_time_us = (without_controller_time / iterations) * 1_000_000

        assert with_time_us < 100, f"With controller: {with_time_us:.1f}us"
        assert without_time_us < 100, f"Without controller: {without_time_us:.1f}us"


class TestModeTogglePerformance:
    """Test mode toggle operations performance."""

    def test_auto_connect_toggle_performance(self) -> None:
        """Test auto-connect mode toggle is fast."""
        mock_mw = create_mock_main_window()

        from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
            SignalCoordinator,
        )

        coordinator = SignalCoordinator(mock_mw)

        # Mock settings manager via the utils module
        with patch(
            "casare_rpa.utils.settings_manager.get_settings_manager"
        ) as mock_settings:
            mock_settings.return_value.set = MagicMock()

            iterations = 100
            start = time.perf_counter()
            for _ in range(iterations):
                coordinator.on_toggle_auto_connect(True)
                coordinator.on_toggle_auto_connect(False)
            elapsed = time.perf_counter() - start

            avg_time_ms = (elapsed / (iterations * 2)) * 1000

            assert avg_time_ms < MAX_PANEL_TOGGLE_TIME_MS, (
                f"Auto-connect toggle took {avg_time_ms:.3f}ms "
                f"(threshold: {MAX_PANEL_TOGGLE_TIME_MS}ms)"
            )

    def test_high_performance_mode_toggle(self) -> None:
        """Test high performance mode toggle."""
        mock_mw = create_mock_main_window()

        from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
            SignalCoordinator,
        )

        coordinator = SignalCoordinator(mock_mw)

        iterations = 100
        start = time.perf_counter()
        for _ in range(iterations):
            coordinator.on_toggle_high_performance_mode(True)
            coordinator.on_toggle_high_performance_mode(False)
        elapsed = time.perf_counter() - start

        avg_time_ms = (elapsed / (iterations * 2)) * 1000

        assert avg_time_ms < MAX_PANEL_TOGGLE_TIME_MS, (
            f"High performance mode toggle took {avg_time_ms:.3f}ms "
            f"(threshold: {MAX_PANEL_TOGGLE_TIME_MS}ms)"
        )


class TestPropertyPanelPerformance:
    """Test property panel event handling performance."""

    def test_property_change_handling(self) -> None:
        """Test property panel change event handling."""
        mock_mw = create_mock_main_window()

        # Mock graph with nodes
        mock_node = MagicMock()
        mock_node.get_property.return_value = "test_node_id"
        mock_node.get_casare_node.return_value = MagicMock(config={})
        mock_mw.get_graph.return_value.all_nodes.return_value = [mock_node]

        from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
            SignalCoordinator,
        )

        coordinator = SignalCoordinator(mock_mw)

        iterations = 100
        start = time.perf_counter()
        for i in range(iterations):
            coordinator.on_property_panel_changed(
                "test_node_id", f"property_{i % 10}", f"value_{i}"
            )
        elapsed = time.perf_counter() - start

        avg_time_ms = (elapsed / iterations) * 1000

        assert avg_time_ms < MAX_ACTION_DISPATCH_TIME_MS, (
            f"Property change handling took {avg_time_ms:.3f}ms "
            f"(threshold: {MAX_ACTION_DISPATCH_TIME_MS}ms)"
        )

    def test_variables_change_handling(self) -> None:
        """Test variables panel change event handling."""
        mock_mw = create_mock_main_window()

        from casare_rpa.presentation.canvas.coordinators.signal_coordinator import (
            SignalCoordinator,
        )

        coordinator = SignalCoordinator(mock_mw)

        test_variables = {f"var_{i}": f"value_{i}" for i in range(100)}

        iterations = 100
        start = time.perf_counter()
        for _ in range(iterations):
            coordinator.on_panel_variables_changed(test_variables)
        elapsed = time.perf_counter() - start

        avg_time_ms = (elapsed / iterations) * 1000

        assert avg_time_ms < MAX_ACTION_DISPATCH_TIME_MS, (
            f"Variables change handling took {avg_time_ms:.3f}ms "
            f"(threshold: {MAX_ACTION_DISPATCH_TIME_MS}ms)"
        )
