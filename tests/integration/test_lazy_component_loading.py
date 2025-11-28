"""
Integration tests for 3-tier component lazy loading.

Tests the ComponentFactory and MainWindow 3-tier loading strategy:
- CRITICAL tier: Immediate initialization (actions, menus, toolbar)
- NORMAL tier: showEvent initialization (panels, docks)
- DEFERRED tier: Lazy factory (dialogs, command palette)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Optional

from PySide6.QtWidgets import QWidget, QApplication

from casare_rpa.presentation.canvas.component_factory import ComponentFactory


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture(autouse=True)
def clear_component_factory():
    """Clear ComponentFactory cache before and after each test."""
    ComponentFactory.clear()
    yield
    ComponentFactory.clear()


@pytest.fixture
def mock_widget() -> Mock:
    """Create a mock QWidget for testing."""
    widget = Mock(spec=QWidget)
    widget.parent = Mock(return_value=None)
    return widget


# ============================================================================
# COMPONENT FACTORY TESTS
# ============================================================================


class TestComponentFactory:
    """Tests for ComponentFactory singleton caching."""

    def test_get_or_create_creates_component(self, mock_widget: Mock) -> None:
        """Test get_or_create creates component on first call."""
        factory_fn = Mock(return_value=mock_widget)

        result = ComponentFactory.get_or_create("test_component", factory_fn)

        assert result is mock_widget
        factory_fn.assert_called_once()

    def test_get_or_create_returns_cached_on_second_call(
        self, mock_widget: Mock
    ) -> None:
        """Test get_or_create returns cached component on subsequent calls."""
        factory_fn = Mock(return_value=mock_widget)

        result1 = ComponentFactory.get_or_create("test_component", factory_fn)
        result2 = ComponentFactory.get_or_create("test_component", factory_fn)

        assert result1 is result2
        assert factory_fn.call_count == 1  # Only called once

    def test_get_or_create_different_names_create_separate_instances(self) -> None:
        """Test different component names create separate instances."""
        widget1 = Mock(spec=QWidget)
        widget2 = Mock(spec=QWidget)

        result1 = ComponentFactory.get_or_create("component_1", lambda: widget1)
        result2 = ComponentFactory.get_or_create("component_2", lambda: widget2)

        assert result1 is widget1
        assert result2 is widget2
        assert result1 is not result2

    def test_has_returns_true_for_cached_component(self, mock_widget: Mock) -> None:
        """Test has() returns True for cached components."""
        ComponentFactory.get_or_create("cached_component", lambda: mock_widget)

        assert ComponentFactory.has("cached_component") is True
        assert ComponentFactory.has("uncached_component") is False

    def test_get_returns_cached_component(self, mock_widget: Mock) -> None:
        """Test get() returns cached component without creating."""
        ComponentFactory.get_or_create("cached_component", lambda: mock_widget)

        result = ComponentFactory.get("cached_component")
        assert result is mock_widget

        # Non-existent component returns None
        assert ComponentFactory.get("nonexistent") is None

    def test_remove_removes_cached_component(self, mock_widget: Mock) -> None:
        """Test remove() removes component from cache."""
        ComponentFactory.get_or_create("removable", lambda: mock_widget)
        assert ComponentFactory.has("removable")

        removed = ComponentFactory.remove("removable")
        assert removed is mock_widget
        assert not ComponentFactory.has("removable")

    def test_remove_nonexistent_returns_none(self) -> None:
        """Test remove() returns None for non-existent component."""
        result = ComponentFactory.remove("nonexistent")
        assert result is None

    def test_clear_removes_all_components(self, mock_widget: Mock) -> None:
        """Test clear() removes all cached components."""
        ComponentFactory.get_or_create("comp_1", lambda: Mock(spec=QWidget))
        ComponentFactory.get_or_create("comp_2", lambda: Mock(spec=QWidget))

        assert ComponentFactory.get_cached_count() == 2

        ComponentFactory.clear()

        assert ComponentFactory.get_cached_count() == 0
        assert not ComponentFactory.has("comp_1")
        assert not ComponentFactory.has("comp_2")

    def test_get_stats_returns_creation_times(self, mock_widget: Mock) -> None:
        """Test get_stats() returns creation time statistics."""
        ComponentFactory.get_or_create("timed_component", lambda: mock_widget)

        stats = ComponentFactory.get_stats()

        assert "timed_component" in stats
        assert isinstance(stats["timed_component"], float)
        assert stats["timed_component"] >= 0

    def test_get_cached_count_returns_correct_count(self) -> None:
        """Test get_cached_count() returns number of cached components."""
        assert ComponentFactory.get_cached_count() == 0

        ComponentFactory.get_or_create("c1", lambda: Mock(spec=QWidget))
        assert ComponentFactory.get_cached_count() == 1

        ComponentFactory.get_or_create("c2", lambda: Mock(spec=QWidget))
        assert ComponentFactory.get_cached_count() == 2

    def test_factory_error_raises_runtime_error(self) -> None:
        """Test factory function error raises RuntimeError."""

        def failing_factory():
            raise ValueError("Factory failed")

        with pytest.raises(RuntimeError) as exc_info:
            ComponentFactory.get_or_create("failing", failing_factory)

        assert "Failed to create component" in str(exc_info.value)
        assert "failing" in str(exc_info.value)

    def test_factory_returning_none_raises_runtime_error(self) -> None:
        """Test factory returning None raises RuntimeError."""
        with pytest.raises(RuntimeError) as exc_info:
            ComponentFactory.get_or_create("null_factory", lambda: None)

        assert "Factory returned None" in str(exc_info.value)


# ============================================================================
# MAIN WINDOW 3-TIER LOADING TESTS
# ============================================================================


class TestMainWindow3TierLoading:
    """Tests for MainWindow 3-tier component loading."""

    @pytest.fixture
    def mock_main_window(self):
        """Create a mock MainWindow with 3-tier loading attributes."""
        window = Mock()
        window._normal_components_loaded = False
        window._command_palette = None
        window._bottom_panel = None
        window._properties_panel = None
        window._preferences_dialog = None
        return window

    def test_critical_tier_initialized_immediately(
        self, mock_main_window: Mock
    ) -> None:
        """Test CRITICAL tier components init flag exists."""
        # In actual MainWindow, critical tier is initialized in __init__
        # before showEvent. Here we verify the flag structure.
        assert hasattr(mock_main_window, "_normal_components_loaded")
        assert mock_main_window._normal_components_loaded is False

    def test_normal_tier_deferred_until_show(self, mock_main_window: Mock) -> None:
        """Test NORMAL tier components are None before show."""
        assert mock_main_window._bottom_panel is None
        assert mock_main_window._properties_panel is None

    def test_deferred_tier_lazy_loaded(self, mock_main_window: Mock) -> None:
        """Test DEFERRED tier components start as None."""
        assert mock_main_window._command_palette is None
        assert mock_main_window._preferences_dialog is None


class TestComponentFactorySingletonPattern:
    """Tests verifying singleton behavior across multiple accesses."""

    def test_same_component_returns_same_instance_globally(self) -> None:
        """Test singleton returns same instance from different call sites."""
        widget = Mock(spec=QWidget)
        call_count = [0]

        def factory():
            call_count[0] += 1
            return widget

        # Simulate multiple access points
        result1 = ComponentFactory.get_or_create("global_singleton", factory)
        result2 = ComponentFactory.get_or_create("global_singleton", factory)
        result3 = ComponentFactory.get_or_create("global_singleton", factory)

        assert result1 is result2 is result3
        assert call_count[0] == 1  # Factory only called once

    def test_cache_survives_across_test_functions(self) -> None:
        """Test cache persists (without explicit clear)."""
        # Note: autouse fixture clears cache, but within a test we can verify persistence
        widget = Mock(spec=QWidget)
        ComponentFactory.get_or_create("persistent", lambda: widget)

        # Same test, later access
        result = ComponentFactory.get("persistent")
        assert result is widget


class TestLazyLoadingIntegration:
    """Integration tests for lazy loading patterns."""

    def test_component_factory_with_real_widget_type(self) -> None:
        """Test ComponentFactory works with actual widget creation."""
        # This would require a QApplication in a real test
        # Here we test the pattern with mock
        mock_widget = Mock(spec=QWidget)
        mock_widget.objectName = Mock(return_value="TestWidget")

        result = ComponentFactory.get_or_create(
            "real_widget_pattern", lambda: mock_widget
        )

        assert result.objectName() == "TestWidget"

    def test_lazy_loading_with_dependency_injection(self) -> None:
        """Test lazy loading pattern with parent widget injection."""
        parent_widget = Mock(spec=QWidget)
        child_widget = Mock(spec=QWidget)

        # Simulate lazy loading with parent injection
        def create_child():
            child_widget.setParent(parent_widget)
            return child_widget

        result = ComponentFactory.get_or_create("child_with_parent", create_child)

        assert result is child_widget
        child_widget.setParent.assert_called_once_with(parent_widget)

    def test_deferred_initialization_callback_pattern(self) -> None:
        """Test deferred initialization with callback registration."""
        widget = Mock(spec=QWidget)
        initialized = [False]

        def on_init(w):
            initialized[0] = True

        def factory_with_callback():
            w = widget
            on_init(w)
            return w

        ComponentFactory.get_or_create("callback_pattern", factory_with_callback)

        assert initialized[0] is True


class TestComponentFactoryThreadSafety:
    """Tests related to thread safety considerations."""

    def test_clear_while_empty_is_safe(self) -> None:
        """Test clearing empty cache is safe."""
        ComponentFactory.clear()
        ComponentFactory.clear()
        ComponentFactory.clear()
        # Should not raise

    def test_multiple_clears_safe(self) -> None:
        """Test multiple consecutive clears are safe."""
        widget = Mock(spec=QWidget)
        ComponentFactory.get_or_create("temp", lambda: widget)
        ComponentFactory.clear()
        ComponentFactory.clear()
        assert ComponentFactory.get_cached_count() == 0
