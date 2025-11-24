"""
Unit tests for Desktop Application Management Nodes

Tests LaunchApplicationNode, CloseApplicationNode, ActivateWindowNode, GetWindowListNode
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from casare_rpa.nodes.desktop_nodes import (
    LaunchApplicationNode,
    CloseApplicationNode,
    ActivateWindowNode,
    GetWindowListNode,
)
from casare_rpa.desktop import DesktopContext, DesktopElement
from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.core.types import NodeStatus


class TestLaunchApplicationNode:
    """Test suite for LaunchApplicationNode"""
    
    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = LaunchApplicationNode("launch_1", name="Launch App")
        assert node.node_id == "launch_1"
        assert node.name == "Launch App"
        assert node.node_type == "LaunchApplicationNode"
    
    @pytest.mark.asyncio
    async def test_launch_calculator(self):
        """Test launching Calculator application"""
        node = LaunchApplicationNode("launch_1", config={"timeout": 10.0})
        context = ExecutionContext()
        
        # Set inputs
        node.set_input_value("application_path", "calc.exe")
        
        try:
            # Execute node
            result = await node.execute(context)
            
            assert result["success"] is True
            assert "window" in result
            assert "process_id" in result
            assert "window_title" in result
            
            # Verify window is valid
            window = result['window']
            assert isinstance(window, DesktopElement)
            assert window.exists()
            
            # Verify process ID
            assert isinstance(result['process_id'], int)
            assert result['process_id'] > 0
            
            # Verify window title
            assert 'Calculator' in result['window_title'] or 'Calc' in result['window_title']
            
            assert node.status == NodeStatus.SUCCESS
            
        finally:
            # Cleanup
            if hasattr(context, 'desktop_context'):
                context.desktop_context.cleanup()
    
    @pytest.mark.asyncio
    async def test_launch_with_arguments(self):
        """Test launching application with arguments"""
        node = LaunchApplicationNode("launch_2", config={"timeout": 10.0})
        context = ExecutionContext()
        
        node.set_input_value("application_path", "notepad.exe")
        node.set_input_value("arguments", "")
        
        try:
            result = await node.execute(context)
            
            assert result["success"] is True
            assert 'window' in result
            assert result['window'].exists()
            
        finally:
            if hasattr(context, 'desktop_context'):
                context.desktop_context.cleanup()
    
    @pytest.mark.asyncio
    async def test_launch_invalid_application(self):
        """Test that launching invalid application raises error"""
        node = LaunchApplicationNode("launch_3", config={"timeout": 5.0})
        context = ExecutionContext()
        
        node.set_input_value("application_path", "nonexistent_app_12345.exe")
        
        with pytest.raises(Exception):
            await node.execute(context)


class TestCloseApplicationNode:
    """Test suite for CloseApplicationNode"""
    
    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = CloseApplicationNode("close_1", name="Close App")
        assert node.node_id == "close_1"
        assert node.name == "Close App"
        assert node.node_type == "CloseApplicationNode"
    
    @pytest.mark.asyncio
    async def test_close_by_window(self):
        """Test closing application by window object"""
        # Launch calc first
        context = ExecutionContext()
        context.desktop_context = DesktopContext()
        window = context.desktop_context.launch_application("calc.exe", timeout=10.0, window_title="Calculator")
        
        try:
            # Now close it
            node = CloseApplicationNode("close_1", config={"force_close": False})
            node.set_input_value("window", window)
            
            result = await node.execute(context)
            
            assert result['success'] is True
            assert node.status == NodeStatus.SUCCESS
            
        finally:
            context.desktop_context.cleanup()
    
    @pytest.mark.asyncio
    async def test_close_by_window_title(self):
        """Test closing application by window title"""
        # Launch calc first
        context = ExecutionContext()
        context.desktop_context = DesktopContext()
        window = context.desktop_context.launch_application("calc.exe", timeout=10.0, window_title="Calculator")
        
        try:
            # Close by title
            node = CloseApplicationNode("close_2", config={"force_close": False})
            node.set_input_value("window_title", "Calculator")
            
            result = await node.execute(context)
            
            assert result['success'] is True
            
        finally:
            context.desktop_context.cleanup()
    
    @pytest.mark.asyncio
    async def test_close_without_inputs(self):
        """Test that closing without inputs raises error"""
        node = CloseApplicationNode("close_3")
        context = ExecutionContext()
        
        with pytest.raises(ValueError, match="Must provide either"):
            await node.execute(context)


class TestActivateWindowNode:
    """Test suite for ActivateWindowNode"""
    
    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = ActivateWindowNode("activate_1", name="Activate Window")
        assert node.node_id == "activate_1"
        assert node.name == "Activate Window"
        assert node.node_type == "ActivateWindowNode"
    
    @pytest.mark.asyncio
    async def test_activate_by_window(self):
        """Test activating window by window object"""
        # Launch calc first
        context = ExecutionContext()
        context.desktop_context = DesktopContext()
        window = context.desktop_context.launch_application("calc.exe", timeout=10.0, window_title="Calculator")
        
        try:
            # Activate it
            node = ActivateWindowNode("activate_1", config={"match_partial": True})
            node.set_input_value("window", window)
            
            result = await node.execute(context)
            
            assert result['success'] is True
            assert result['window'] is not None
            assert node.status == NodeStatus.SUCCESS
            
        finally:
            context.desktop_context.cleanup()
    
    @pytest.mark.asyncio
    async def test_activate_by_title(self):
        """Test activating window by title"""
        # Launch calc first
        context = ExecutionContext()
        context.desktop_context = DesktopContext()
        window = context.desktop_context.launch_application("calc.exe", timeout=10.0, window_title="Calculator")
        
        try:
            # Activate by title
            node = ActivateWindowNode("activate_2", config={"match_partial": True})
            node.set_input_value("window_title", "Calculator")
            
            result = await node.execute(context)
            
            assert result['success'] is True
            
        finally:
            context.desktop_context.cleanup()
    
    @pytest.mark.asyncio
    async def test_activate_without_inputs(self):
        """Test that activating without inputs raises error"""
        node = ActivateWindowNode("activate_3")
        context = ExecutionContext()
        
        with pytest.raises(ValueError, match="Must provide either"):
            await node.execute(context)


class TestGetWindowListNode:
    """Test suite for GetWindowListNode"""
    
    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = GetWindowListNode("list_1", name="Get Windows")
        assert node.node_id == "list_1"
        assert node.name == "Get Windows"
        assert node.node_type == "GetWindowListNode"
    
    @pytest.mark.asyncio
    async def test_get_all_windows(self):
        """Test getting all windows"""
        # Launch calc to ensure at least one window exists
        context = ExecutionContext()
        context.desktop_context = DesktopContext()
        window = context.desktop_context.launch_application("calc.exe", timeout=10.0, window_title="Calculator")
        
        try:
            node = GetWindowListNode("list_1", config={"include_invisible": False})
            
            result = await node.execute(context)
            
            assert result['success'] is True
            assert 'window_list' in result
            assert 'window_count' in result
            assert isinstance(result['window_list'], list)
            assert result['window_count'] > 0
            assert node.status == NodeStatus.SUCCESS
            
        finally:
            context.desktop_context.cleanup()
    
    @pytest.mark.asyncio
    async def test_get_windows_with_filter(self):
        """Test getting windows with title filter"""
        # Launch calc
        context = ExecutionContext()
        context.desktop_context = DesktopContext()
        window = context.desktop_context.launch_application("calc.exe", timeout=10.0, window_title="Calculator")
        
        try:
            node = GetWindowListNode("list_2", config={"filter_title": "Calculator"})
            
            result = await node.execute(context)
            
            assert result['success'] is True
            assert result['window_count'] >= 1
            
            # Check that filtered results contain Calculator
            window_titles = [w['title'] for w in result['window_list']]
            assert any('Calculator' in title for title in window_titles)
            
        finally:
            context.desktop_context.cleanup()
