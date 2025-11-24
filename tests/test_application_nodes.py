# tests/test_application_nodes.py
"""Unit tests for Desktop Application Management Nodes.

These tests mock the `DesktopContext` used by the nodes to avoid real UI interactions.
"""
import pytest
from unittest.mock import MagicMock, patch

from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.nodes.desktop_nodes.application_nodes import (
    LaunchApplicationNode,
    CloseApplicationNode,
    ActivateWindowNode,
    GetWindowListNode,
)

@pytest.fixture
def exec_context():
    """Provide a fresh ExecutionContext for each test."""
    return ExecutionContext(workflow_name="test_workflow")

@pytest.fixture
def mock_window():
    """Create a mock window object with required attributes/methods."""
    window = MagicMock()
    # Simulate the underlying control with ProcessId and GetWindowPattern
    control = MagicMock()
    control.ProcessId = 1234
    control.GetWindowPattern.return_value = MagicMock()
    window._control = control
    window.get_text.return_value = "Mock Window Title"
    return window

@pytest.mark.asyncio
async def test_launch_application_success(exec_context, mock_window):
    # Mock DesktopContext and its launch_application method (sync, not async)
    mock_desktop = MagicMock()
    mock_desktop.launch_application = MagicMock(return_value=mock_window)
    exec_context.desktop_context = mock_desktop

    node = LaunchApplicationNode(node_id="launch1")
    # Provide required inputs via config
    node.config["application_path"] = "C:/Program Files/MockApp/app.exe"
    node.config["arguments"] = ""
    node.config["working_directory"] = None

    result = await node.execute(exec_context)
    assert result["success"] is True
    assert result["window"] == mock_window
    assert result["process_id"] == 1234
    assert result["window_title"] == "Mock Window Title"
    assert "exec_out" in result["next_nodes"]

@pytest.mark.asyncio
async def test_launch_application_missing_path(exec_context):
    node = LaunchApplicationNode(node_id="launch_missing")
    # No application_path provided
    with pytest.raises(ValueError):
        await node.execute(exec_context)

@pytest.mark.asyncio
async def test_close_application_success(exec_context, mock_window):
    mock_desktop = MagicMock()
    mock_desktop.close_application = MagicMock(return_value=True)
    exec_context.desktop_context = mock_desktop

    node = CloseApplicationNode(node_id="close1")
    # Provide window input via config (node reads from input ports, but we can set directly)
    node.config["force_close"] = False
    # Set input value directly through the port
    node.input_ports["window"].value = mock_window

    result = await node.execute(exec_context)
    assert result["success"] is True
    assert "exec_out" in result["next_nodes"]

@pytest.mark.asyncio
async def test_activate_window_success(exec_context, mock_window):
    mock_desktop = MagicMock()
    mock_desktop.find_window = MagicMock(return_value=mock_window)
    exec_context.desktop_context = mock_desktop

    node = ActivateWindowNode(node_id="activate1")
    # Provide window title hint via config
    node.config["window_title_hint"] = "Mock Window Title"
    # Set input value directly
    node.input_ports["window_title"].value = "Mock Window Title"

    result = await node.execute(exec_context)
    assert result["success"] is True
    assert result["window"] == mock_window
    assert "exec_out" in result["next_nodes"]

@pytest.mark.asyncio
async def test_get_window_list_success(exec_context):
    mock_desktop = MagicMock()
    # Create two mock windows
    win1 = MagicMock()
    win1.get_text.return_value = "Window One"
    win1.get_property.side_effect = lambda prop: {"ProcessId": 1111, "AutomationId": "auto1"}.get(prop)
    win1.is_enabled.return_value = True
    win1.is_visible.return_value = True
    win1.get_bounding_rect.return_value = (0, 0, 100, 100)
    win2 = MagicMock()
    win2.get_text.return_value = "Window Two"
    win2.get_property.side_effect = lambda prop: {"ProcessId": 2222, "AutomationId": "auto2"}.get(prop)
    win2.is_enabled.return_value = False
    win2.is_visible.return_value = True
    win2.get_bounding_rect.return_value = (10, 10, 200, 200)
    mock_desktop.get_all_windows = MagicMock(return_value=[win1, win2])
    exec_context.desktop_context = mock_desktop

    node = GetWindowListNode(node_id="list1")
    result = await node.execute(exec_context)
    assert result["success"] is True
    assert result["window_count"] == 2
    assert len(result["window_list"]) == 2
    assert "exec_out" in result["next_nodes"]
