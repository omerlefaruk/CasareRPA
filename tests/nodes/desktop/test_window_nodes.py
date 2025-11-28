"""
Comprehensive tests for desktop window management nodes.

Tests ResizeWindowNode, MoveWindowNode, MaximizeWindowNode, MinimizeWindowNode,
RestoreWindowNode, GetWindowPropertiesNode, SetWindowStateNode from CasareRPA.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

from casare_rpa.domain.value_objects.types import NodeStatus


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_window():
    """Create a mock window element with standard properties."""
    window = Mock()
    window.get_text = Mock(return_value="Test Window")
    window.get_property = Mock(return_value=12345)
    window._control = Mock()
    window._control.ProcessId = 1234
    window._control.NativeWindowHandle = 12345
    return window


@pytest.fixture
def mock_desktop_context():
    """Create a mock desktop context for window operations."""
    ctx = Mock()
    ctx.resize_window = Mock(return_value=True)
    ctx.move_window = Mock(return_value=True)
    ctx.maximize_window = Mock(return_value=True)
    ctx.minimize_window = Mock(return_value=True)
    ctx.restore_window = Mock(return_value=True)
    ctx.bring_to_front = Mock(return_value=True)
    ctx.get_window_properties = Mock(
        return_value={
            "title": "Test Window",
            "x": 100,
            "y": 100,
            "width": 800,
            "height": 600,
            "state": "normal",
            "is_maximized": False,
            "is_minimized": False,
        }
    )
    return ctx


@pytest.fixture
def mock_execution_context(mock_desktop_context):
    """Create execution context with desktop context attached."""
    context = Mock()
    context.variables = {}
    context.resolve_value = lambda x: x
    context.desktop_context = mock_desktop_context
    return context


# =============================================================================
# ResizeWindowNode Tests
# =============================================================================


class TestResizeWindowNode:
    """Tests for ResizeWindowNode - window dimension changes."""

    @pytest.mark.asyncio
    async def test_resize_window_success(self, mock_execution_context, mock_window):
        """Test successful window resize."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import ResizeWindowNode

        node = ResizeWindowNode(node_id="test_resize")
        node.set_input_value("window", mock_window)
        node.set_input_value("width", 1024)
        node.set_input_value("height", 768)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        mock_execution_context.desktop_context.resize_window.assert_called_once_with(
            mock_window, 1024, 768
        )

    @pytest.mark.asyncio
    async def test_resize_window_default_dimensions(
        self, mock_execution_context, mock_window
    ):
        """Test resize with default dimensions from config."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import ResizeWindowNode

        node = ResizeWindowNode(
            node_id="test_default", config={"width": 640, "height": 480}
        )
        node.set_input_value("window", mock_window)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        mock_execution_context.desktop_context.resize_window.assert_called_once_with(
            mock_window, 640, 480
        )

    @pytest.mark.asyncio
    async def test_resize_window_missing_window(self, mock_execution_context):
        """Test error when window input is missing."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import ResizeWindowNode

        node = ResizeWindowNode(node_id="test_missing")

        with pytest.raises(ValueError) as exc_info:
            await node.execute(mock_execution_context)

        assert "Window input is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_resize_window_with_retry(self, mock_execution_context, mock_window):
        """Test resize with retry on failure."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import ResizeWindowNode

        # First call fails, second succeeds
        mock_execution_context.desktop_context.resize_window.side_effect = [
            Exception("Temporary failure"),
            True,
        ]

        node = ResizeWindowNode(
            node_id="test_retry",
            config={"retry_count": 1, "retry_interval": 0.01},
        )
        node.set_input_value("window", mock_window)
        node.set_input_value("width", 800)
        node.set_input_value("height", 600)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["attempts"] == 2

    @pytest.mark.asyncio
    async def test_resize_window_bring_to_front(
        self, mock_execution_context, mock_window
    ):
        """Test resize with bring_to_front option."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import ResizeWindowNode

        node = ResizeWindowNode(node_id="test_front", config={"bring_to_front": True})
        node.set_input_value("window", mock_window)
        node.set_input_value("width", 800)
        node.set_input_value("height", 600)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        mock_execution_context.desktop_context.bring_to_front.assert_called_once()


# =============================================================================
# MoveWindowNode Tests
# =============================================================================


class TestMoveWindowNode:
    """Tests for MoveWindowNode - window positioning."""

    @pytest.mark.asyncio
    async def test_move_window_success(self, mock_execution_context, mock_window):
        """Test successful window move."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import MoveWindowNode

        node = MoveWindowNode(node_id="test_move")
        node.set_input_value("window", mock_window)
        node.set_input_value("x", 200)
        node.set_input_value("y", 150)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        mock_execution_context.desktop_context.move_window.assert_called_once_with(
            mock_window, 200, 150
        )

    @pytest.mark.asyncio
    async def test_move_window_default_position(
        self, mock_execution_context, mock_window
    ):
        """Test move with default position from config."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import MoveWindowNode

        node = MoveWindowNode(node_id="test_default", config={"x": 50, "y": 50})
        node.set_input_value("window", mock_window)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        mock_execution_context.desktop_context.move_window.assert_called_once_with(
            mock_window, 50, 50
        )

    @pytest.mark.asyncio
    async def test_move_window_missing_window(self, mock_execution_context):
        """Test error when window input is missing."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import MoveWindowNode

        node = MoveWindowNode(node_id="test_missing")
        node.set_input_value("x", 100)
        node.set_input_value("y", 100)

        with pytest.raises(ValueError) as exc_info:
            await node.execute(mock_execution_context)

        assert "Window input is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_move_window_failure_all_retries(
        self, mock_execution_context, mock_window
    ):
        """Test move fails after all retries exhausted."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import MoveWindowNode

        mock_execution_context.desktop_context.move_window.side_effect = Exception(
            "Move failed"
        )

        node = MoveWindowNode(
            node_id="test_fail",
            config={"retry_count": 2, "retry_interval": 0.01},
        )
        node.set_input_value("window", mock_window)
        node.set_input_value("x", 100)
        node.set_input_value("y", 100)

        with pytest.raises(RuntimeError) as exc_info:
            await node.execute(mock_execution_context)

        assert "Failed to move window after 3 attempts" in str(exc_info.value)


# =============================================================================
# MaximizeWindowNode Tests
# =============================================================================


class TestMaximizeWindowNode:
    """Tests for MaximizeWindowNode - window maximization."""

    @pytest.mark.asyncio
    async def test_maximize_window_success(self, mock_execution_context, mock_window):
        """Test successful window maximize."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import MaximizeWindowNode

        node = MaximizeWindowNode(node_id="test_maximize")
        node.set_input_value("window", mock_window)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        mock_execution_context.desktop_context.maximize_window.assert_called_once_with(
            mock_window
        )

    @pytest.mark.asyncio
    async def test_maximize_window_missing_window(self, mock_execution_context):
        """Test error when window input is missing."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import MaximizeWindowNode

        node = MaximizeWindowNode(node_id="test_missing")

        with pytest.raises(ValueError) as exc_info:
            await node.execute(mock_execution_context)

        assert "Window input is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_maximize_window_with_retry(
        self, mock_execution_context, mock_window
    ):
        """Test maximize with retry configuration."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import MaximizeWindowNode

        mock_execution_context.desktop_context.maximize_window.side_effect = [
            Exception("Temp"),
            True,
        ]

        node = MaximizeWindowNode(
            node_id="test_retry", config={"retry_count": 1, "retry_interval": 0.01}
        )
        node.set_input_value("window", mock_window)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["attempts"] == 2


# =============================================================================
# MinimizeWindowNode Tests
# =============================================================================


class TestMinimizeWindowNode:
    """Tests for MinimizeWindowNode - window minimization."""

    @pytest.mark.asyncio
    async def test_minimize_window_success(self, mock_execution_context, mock_window):
        """Test successful window minimize."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import MinimizeWindowNode

        node = MinimizeWindowNode(node_id="test_minimize")
        node.set_input_value("window", mock_window)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        mock_execution_context.desktop_context.minimize_window.assert_called_once_with(
            mock_window
        )

    @pytest.mark.asyncio
    async def test_minimize_window_missing_window(self, mock_execution_context):
        """Test error when window input is missing."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import MinimizeWindowNode

        node = MinimizeWindowNode(node_id="test_missing")

        with pytest.raises(ValueError) as exc_info:
            await node.execute(mock_execution_context)

        assert "Window input is required" in str(exc_info.value)


# =============================================================================
# RestoreWindowNode Tests
# =============================================================================


class TestRestoreWindowNode:
    """Tests for RestoreWindowNode - window restoration."""

    @pytest.mark.asyncio
    async def test_restore_window_success(self, mock_execution_context, mock_window):
        """Test successful window restore."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import RestoreWindowNode

        node = RestoreWindowNode(node_id="test_restore")
        node.set_input_value("window", mock_window)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        mock_execution_context.desktop_context.restore_window.assert_called_once_with(
            mock_window
        )

    @pytest.mark.asyncio
    async def test_restore_window_missing_window(self, mock_execution_context):
        """Test error when window input is missing."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import RestoreWindowNode

        node = RestoreWindowNode(node_id="test_missing")

        with pytest.raises(ValueError) as exc_info:
            await node.execute(mock_execution_context)

        assert "Window input is required" in str(exc_info.value)


# =============================================================================
# GetWindowPropertiesNode Tests
# =============================================================================


class TestGetWindowPropertiesNode:
    """Tests for GetWindowPropertiesNode - window property retrieval."""

    @pytest.mark.asyncio
    async def test_get_properties_success(self, mock_execution_context, mock_window):
        """Test successful property retrieval."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import GetWindowPropertiesNode

        node = GetWindowPropertiesNode(node_id="test_properties")
        node.set_input_value("window", mock_window)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["title"] == "Test Window"
        assert result["x"] == 100
        assert result["y"] == 100
        assert result["width"] == 800
        assert result["height"] == 600
        assert result["state"] == "normal"
        assert result["is_maximized"] is False
        assert result["is_minimized"] is False
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_get_properties_missing_window(self, mock_execution_context):
        """Test error when window input is missing."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import GetWindowPropertiesNode

        node = GetWindowPropertiesNode(node_id="test_missing")

        with pytest.raises(ValueError) as exc_info:
            await node.execute(mock_execution_context)

        assert "Window input is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_properties_failure(self, mock_execution_context, mock_window):
        """Test property retrieval failure."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import GetWindowPropertiesNode

        mock_execution_context.desktop_context.get_window_properties.side_effect = (
            Exception("Access denied")
        )

        node = GetWindowPropertiesNode(node_id="test_fail")
        node.set_input_value("window", mock_window)

        with pytest.raises(RuntimeError) as exc_info:
            await node.execute(mock_execution_context)

        assert "Failed to get window properties" in str(exc_info.value)


# =============================================================================
# SetWindowStateNode Tests
# =============================================================================


class TestSetWindowStateNode:
    """Tests for SetWindowStateNode - window state changes."""

    @pytest.mark.asyncio
    async def test_set_state_maximized(self, mock_execution_context, mock_window):
        """Test setting window state to maximized."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import SetWindowStateNode

        node = SetWindowStateNode(node_id="test_maximize")
        node.set_input_value("window", mock_window)
        node.set_input_value("state", "maximized")

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        mock_execution_context.desktop_context.maximize_window.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_state_minimized(self, mock_execution_context, mock_window):
        """Test setting window state to minimized."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import SetWindowStateNode

        node = SetWindowStateNode(node_id="test_minimize")
        node.set_input_value("window", mock_window)
        node.set_input_value("state", "minimized")

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        mock_execution_context.desktop_context.minimize_window.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_state_normal(self, mock_execution_context, mock_window):
        """Test setting window state to normal (restored)."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import SetWindowStateNode

        node = SetWindowStateNode(node_id="test_normal")
        node.set_input_value("window", mock_window)
        node.set_input_value("state", "normal")

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        mock_execution_context.desktop_context.restore_window.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_state_restored(self, mock_execution_context, mock_window):
        """Test setting window state to restored (alias for normal)."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import SetWindowStateNode

        node = SetWindowStateNode(node_id="test_restored")
        node.set_input_value("window", mock_window)
        node.set_input_value("state", "restored")

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        mock_execution_context.desktop_context.restore_window.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_state_invalid(self, mock_execution_context, mock_window):
        """Test error with invalid state value."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import SetWindowStateNode

        node = SetWindowStateNode(node_id="test_invalid")
        node.set_input_value("window", mock_window)
        node.set_input_value("state", "invalid_state")

        with pytest.raises(RuntimeError) as exc_info:
            await node.execute(mock_execution_context)

        assert "Invalid state" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_set_state_missing_window(self, mock_execution_context):
        """Test error when window input is missing."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import SetWindowStateNode

        node = SetWindowStateNode(node_id="test_missing")
        node.set_input_value("state", "maximized")

        with pytest.raises(ValueError) as exc_info:
            await node.execute(mock_execution_context)

        assert "Window input is required" in str(exc_info.value)


# =============================================================================
# ExecutionResult Pattern Compliance Tests
# =============================================================================


class TestExecutionResultCompliance:
    """Tests verifying all nodes follow ExecutionResult pattern."""

    @pytest.mark.asyncio
    async def test_resize_result_structure(self, mock_execution_context, mock_window):
        """Test ResizeWindowNode returns proper structure."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import ResizeWindowNode

        node = ResizeWindowNode(node_id="test_result")
        node.set_input_value("window", mock_window)
        node.set_input_value("width", 800)
        node.set_input_value("height", 600)

        result = await node.execute(mock_execution_context)

        assert "success" in result
        assert isinstance(result["success"], bool)
        assert "attempts" in result
        assert "next_nodes" in result

    @pytest.mark.asyncio
    async def test_move_result_structure(self, mock_execution_context, mock_window):
        """Test MoveWindowNode returns proper structure."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import MoveWindowNode

        node = MoveWindowNode(node_id="test_result")
        node.set_input_value("window", mock_window)
        node.set_input_value("x", 100)
        node.set_input_value("y", 100)

        result = await node.execute(mock_execution_context)

        assert "success" in result
        assert "attempts" in result
        assert "next_nodes" in result

    @pytest.mark.asyncio
    async def test_get_properties_result_structure(
        self, mock_execution_context, mock_window
    ):
        """Test GetWindowPropertiesNode returns proper structure."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import GetWindowPropertiesNode

        node = GetWindowPropertiesNode(node_id="test_result")
        node.set_input_value("window", mock_window)

        result = await node.execute(mock_execution_context)

        assert "success" in result
        assert "properties" in result
        assert "title" in result
        assert "x" in result
        assert "y" in result
        assert "width" in result
        assert "height" in result
        assert "state" in result
        assert "is_maximized" in result
        assert "is_minimized" in result
        assert "next_nodes" in result

    @pytest.mark.asyncio
    async def test_set_state_result_structure(
        self, mock_execution_context, mock_window
    ):
        """Test SetWindowStateNode returns proper structure."""
        from casare_rpa.nodes.desktop_nodes.window_nodes import SetWindowStateNode

        node = SetWindowStateNode(node_id="test_result")
        node.set_input_value("window", mock_window)
        node.set_input_value("state", "normal")

        result = await node.execute(mock_execution_context)

        assert "success" in result
        assert "attempts" in result
        assert "next_nodes" in result
