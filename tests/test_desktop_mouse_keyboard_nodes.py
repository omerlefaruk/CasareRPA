"""
Unit tests for Desktop Mouse & Keyboard Control Nodes

Tests MoveMouseNode, MouseClickNode, SendKeysNode, SendHotKeyNode,
GetMousePositionNode, DragMouseNode
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from casare_rpa.nodes.desktop_nodes import (
    MoveMouseNode,
    MouseClickNode,
    SendKeysNode,
    SendHotKeyNode,
    GetMousePositionNode,
    DragMouseNode,
)
from casare_rpa.desktop import DesktopContext
from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.core.types import NodeStatus


class TestMoveMouseNode:
    """Test suite for MoveMouseNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = MoveMouseNode("move_1", name="Move Mouse")
        assert node.node_id == "move_1"
        assert node.name == "Move Mouse"
        assert node.node_type == "MoveMouseNode"

    @pytest.mark.asyncio
    async def test_missing_x_coordinate_raises_error(self):
        """Test that missing X coordinate raises ValueError"""
        node = MoveMouseNode("move_2")
        context = ExecutionContext()

        node.set_input_value("y", 100)

        with pytest.raises(ValueError, match="X coordinate is required"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_missing_y_coordinate_raises_error(self):
        """Test that missing Y coordinate raises ValueError"""
        node = MoveMouseNode("move_3")
        context = ExecutionContext()

        node.set_input_value("x", 100)

        with pytest.raises(ValueError, match="Y coordinate is required"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_missing_desktop_context_raises_error(self):
        """Test that missing desktop context raises ValueError"""
        node = MoveMouseNode("move_4")
        context = ExecutionContext()

        node.set_input_value("x", 100)
        node.set_input_value("y", 200)

        with pytest.raises(ValueError, match="Desktop context not available"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_successful_move_with_mock(self):
        """Test successful mouse movement using mocked context"""
        node = MoveMouseNode("move_5")
        context = ExecutionContext()

        node.set_input_value("x", 500)
        node.set_input_value("y", 300)
        node.set_input_value("duration", 0.5)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.move_mouse.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['x'] == 500
        assert result['y'] == 300
        assert node.status == NodeStatus.SUCCESS
        mock_desktop_ctx.move_mouse.assert_called_once_with(500, 300, 0.5)

    @pytest.mark.asyncio
    async def test_instant_move_no_duration(self):
        """Test instant mouse movement without duration"""
        node = MoveMouseNode("move_6")
        context = ExecutionContext()

        node.set_input_value("x", 100)
        node.set_input_value("y", 100)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.move_mouse.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        mock_desktop_ctx.move_mouse.assert_called_once_with(100, 100, 0.0)


class TestMouseClickNode:
    """Test suite for MouseClickNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = MouseClickNode("click_1", name="Mouse Click")
        assert node.node_id == "click_1"
        assert node.name == "Mouse Click"
        assert node.node_type == "MouseClickNode"

    def test_default_config(self):
        """Test default configuration"""
        node = MouseClickNode("click_2")
        assert node.config.get("button") == "left"
        assert node.config.get("click_type") == "single"

    @pytest.mark.asyncio
    async def test_missing_desktop_context_raises_error(self):
        """Test that missing desktop context raises ValueError"""
        node = MouseClickNode("click_3")
        context = ExecutionContext()

        with pytest.raises(ValueError, match="Desktop context not available"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_left_click_with_mock(self):
        """Test left click using mocked context"""
        node = MouseClickNode("click_4", config={"button": "left", "click_type": "single"})
        context = ExecutionContext()

        node.set_input_value("x", 100)
        node.set_input_value("y", 200)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.click_mouse.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['button'] == "left"
        assert result['click_type'] == "single"
        assert node.status == NodeStatus.SUCCESS
        mock_desktop_ctx.click_mouse.assert_called_once_with(
            x=100, y=200, button="left", click_type="single"
        )

    @pytest.mark.asyncio
    async def test_right_click_with_mock(self):
        """Test right click using mocked context"""
        node = MouseClickNode("click_5", config={"button": "right", "click_type": "single"})
        context = ExecutionContext()

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.click_mouse.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['button'] == "right"
        mock_desktop_ctx.click_mouse.assert_called_once_with(
            x=None, y=None, button="right", click_type="single"
        )

    @pytest.mark.asyncio
    async def test_double_click_with_mock(self):
        """Test double click using mocked context"""
        node = MouseClickNode("click_6", config={"button": "left", "click_type": "double"})
        context = ExecutionContext()

        node.set_input_value("x", 300)
        node.set_input_value("y", 400)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.click_mouse.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['click_type'] == "double"
        mock_desktop_ctx.click_mouse.assert_called_once_with(
            x=300, y=400, button="left", click_type="double"
        )

    @pytest.mark.asyncio
    async def test_middle_click_with_mock(self):
        """Test middle click using mocked context"""
        node = MouseClickNode("click_7", config={"button": "middle", "click_type": "single"})
        context = ExecutionContext()

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.click_mouse.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['button'] == "middle"


class TestSendKeysNode:
    """Test suite for SendKeysNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = SendKeysNode("keys_1", name="Send Keys")
        assert node.node_id == "keys_1"
        assert node.name == "Send Keys"
        assert node.node_type == "SendKeysNode"

    def test_default_config(self):
        """Test default configuration"""
        node = SendKeysNode("keys_2")
        assert node.config.get("interval") == 0.0

    @pytest.mark.asyncio
    async def test_missing_keys_raises_error(self):
        """Test that missing keys raises ValueError"""
        node = SendKeysNode("keys_3")
        context = ExecutionContext()

        mock_desktop_ctx = Mock(spec=DesktopContext)
        context.desktop_context = mock_desktop_ctx

        with pytest.raises(ValueError, match="Keys to send are required"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_send_keys_with_mock(self):
        """Test sending keys using mocked context"""
        node = SendKeysNode("keys_4")
        context = ExecutionContext()

        node.set_input_value("keys", "Hello World")
        node.set_input_value("interval", 0.05)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.send_keys.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['keys'] == "Hello World"
        assert node.status == NodeStatus.SUCCESS
        mock_desktop_ctx.send_keys.assert_called_once_with("Hello World", 0.05)

    @pytest.mark.asyncio
    async def test_send_special_keys_with_mock(self):
        """Test sending special keys using mocked context"""
        node = SendKeysNode("keys_5")
        context = ExecutionContext()

        node.set_input_value("keys", "{Enter}")

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.send_keys.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        mock_desktop_ctx.send_keys.assert_called_once_with("{Enter}", 0.0)


class TestSendHotKeyNode:
    """Test suite for SendHotKeyNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = SendHotKeyNode("hotkey_1", name="Send Hotkey")
        assert node.node_id == "hotkey_1"
        assert node.name == "Send Hotkey"
        assert node.node_type == "SendHotKeyNode"

    @pytest.mark.asyncio
    async def test_missing_keys_raises_error(self):
        """Test that missing hotkey raises ValueError"""
        node = SendHotKeyNode("hotkey_2")
        context = ExecutionContext()

        mock_desktop_ctx = Mock(spec=DesktopContext)
        context.desktop_context = mock_desktop_ctx

        with pytest.raises(ValueError, match="Hotkey combination is required"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_send_ctrl_c_with_mock(self):
        """Test sending Ctrl+C using mocked context"""
        node = SendHotKeyNode("hotkey_3")
        context = ExecutionContext()

        node.set_input_value("keys", "Ctrl,C")

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.send_hotkey.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['keys'] == ["Ctrl", "C"]
        assert node.status == NodeStatus.SUCCESS
        mock_desktop_ctx.send_hotkey.assert_called_once_with("Ctrl", "C")

    @pytest.mark.asyncio
    async def test_send_alt_tab_with_mock(self):
        """Test sending Alt+Tab using mocked context"""
        node = SendHotKeyNode("hotkey_4")
        context = ExecutionContext()

        node.set_input_value("keys", "Alt,Tab")

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.send_hotkey.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        mock_desktop_ctx.send_hotkey.assert_called_once_with("Alt", "Tab")

    @pytest.mark.asyncio
    async def test_send_ctrl_shift_s_with_mock(self):
        """Test sending Ctrl+Shift+S using mocked context"""
        node = SendHotKeyNode("hotkey_5")
        context = ExecutionContext()

        node.set_input_value("keys", "Ctrl,Shift,S")

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.send_hotkey.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['keys'] == ["Ctrl", "Shift", "S"]
        mock_desktop_ctx.send_hotkey.assert_called_once_with("Ctrl", "Shift", "S")


class TestGetMousePositionNode:
    """Test suite for GetMousePositionNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = GetMousePositionNode("pos_1", name="Get Mouse Position")
        assert node.node_id == "pos_1"
        assert node.name == "Get Mouse Position"
        assert node.node_type == "GetMousePositionNode"

    @pytest.mark.asyncio
    async def test_missing_desktop_context_raises_error(self):
        """Test that missing desktop context raises ValueError"""
        node = GetMousePositionNode("pos_2")
        context = ExecutionContext()

        with pytest.raises(ValueError, match="Desktop context not available"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_get_position_with_mock(self):
        """Test getting mouse position using mocked context"""
        node = GetMousePositionNode("pos_3")
        context = ExecutionContext()

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.get_mouse_position.return_value = (500, 300)
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['x'] == 500
        assert result['y'] == 300
        assert node.status == NodeStatus.SUCCESS
        mock_desktop_ctx.get_mouse_position.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_position_at_origin_with_mock(self):
        """Test getting mouse position at origin"""
        node = GetMousePositionNode("pos_4")
        context = ExecutionContext()

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.get_mouse_position.return_value = (0, 0)
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['x'] == 0
        assert result['y'] == 0


class TestDragMouseNode:
    """Test suite for DragMouseNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = DragMouseNode("drag_1", name="Drag Mouse")
        assert node.node_id == "drag_1"
        assert node.name == "Drag Mouse"
        assert node.node_type == "DragMouseNode"

    def test_default_config(self):
        """Test default configuration"""
        node = DragMouseNode("drag_2")
        assert node.config.get("button") == "left"
        assert node.config.get("duration") == 0.5

    @pytest.mark.asyncio
    async def test_missing_start_coordinates_raises_error(self):
        """Test that missing start coordinates raises ValueError"""
        node = DragMouseNode("drag_3")
        context = ExecutionContext()

        node.set_input_value("end_x", 200)
        node.set_input_value("end_y", 200)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        context.desktop_context = mock_desktop_ctx

        with pytest.raises(ValueError, match="Start coordinates are required"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_missing_end_coordinates_raises_error(self):
        """Test that missing end coordinates raises ValueError"""
        node = DragMouseNode("drag_4")
        context = ExecutionContext()

        node.set_input_value("start_x", 100)
        node.set_input_value("start_y", 100)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        context.desktop_context = mock_desktop_ctx

        with pytest.raises(ValueError, match="End coordinates are required"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_drag_with_mock(self):
        """Test dragging using mocked context"""
        node = DragMouseNode("drag_5")
        context = ExecutionContext()

        node.set_input_value("start_x", 100)
        node.set_input_value("start_y", 100)
        node.set_input_value("end_x", 300)
        node.set_input_value("end_y", 300)
        node.set_input_value("duration", 1.0)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.drag_mouse.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['start_x'] == 100
        assert result['start_y'] == 100
        assert result['end_x'] == 300
        assert result['end_y'] == 300
        assert node.status == NodeStatus.SUCCESS
        mock_desktop_ctx.drag_mouse.assert_called_once_with(
            100, 100, 300, 300, button="left", duration=1.0
        )

    @pytest.mark.asyncio
    async def test_drag_right_button_with_mock(self):
        """Test dragging with right button using mocked context"""
        node = DragMouseNode("drag_6", config={"button": "right", "duration": 0.5})
        context = ExecutionContext()

        node.set_input_value("start_x", 50)
        node.set_input_value("start_y", 50)
        node.set_input_value("end_x", 150)
        node.set_input_value("end_y", 150)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.drag_mouse.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['button'] == "right"
        mock_desktop_ctx.drag_mouse.assert_called_once_with(
            50, 50, 150, 150, button="right", duration=0.5
        )
