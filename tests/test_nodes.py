"""
Tests for Phase 4 Node implementations.

Tests all node types: basic, browser, navigation, interaction, data, wait, and variable nodes.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.core.types import NodeStatus
from casare_rpa.nodes import (
    # Basic
    StartNode,
    EndNode,
    CommentNode,
    # Browser
    LaunchBrowserNode,
    CloseBrowserNode,
    NewTabNode,
    # Navigation
    GoToURLNode,
    GoBackNode,
    GoForwardNode,
    RefreshPageNode,
    # Interaction
    ClickElementNode,
    TypeTextNode,
    SelectDropdownNode,
    # Data
    ExtractTextNode,
    GetAttributeNode,
    ScreenshotNode,
    # Wait
    WaitNode,
    WaitForElementNode,
    WaitForNavigationNode,
    # Variable
    SetVariableNode,
    GetVariableNode,
    IncrementVariableNode,
)


# Test Basic Nodes

class TestStartNode:
    """Tests for StartNode."""
    
    def test_initialization(self):
        """Test node initialization."""
        node = StartNode("start_1", "Start")
        assert node.node_id == "start_1"
        assert node.name == "Start"
        assert node.node_type == "StartNode"
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test node execution."""
        node = StartNode("start_1")
        context = ExecutionContext()
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert "exec_out" in result["next_nodes"]
        assert node.status == NodeStatus.SUCCESS


class TestEndNode:
    """Tests for EndNode."""
    
    def test_initialization(self):
        """Test node initialization."""
        node = EndNode("end_1", "End")
        assert node.node_id == "end_1"
        assert node.name == "End"
        assert node.node_type == "EndNode"
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test node execution."""
        node = EndNode("end_1")
        context = ExecutionContext()
        context.set_variable("test_var", "test_value")
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert "summary" in result["data"]
        assert node.status == NodeStatus.SUCCESS


class TestCommentNode:
    """Tests for CommentNode."""
    
    def test_initialization(self):
        """Test node initialization."""
        node = CommentNode("comment_1", "Comment", "This is a comment")
        assert node.node_id == "comment_1"
        assert node.name == "Comment"
        assert node.node_type == "CommentNode"
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test node execution (should be skipped)."""
        node = CommentNode("comment_1", comment="Test comment")
        context = ExecutionContext()
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert node.status == NodeStatus.SKIPPED
        assert len(result["next_nodes"]) == 0


# Test Browser Nodes

class TestLaunchBrowserNode:
    """Tests for LaunchBrowserNode."""
    
    def test_initialization(self):
        """Test node initialization."""
        node = LaunchBrowserNode("browser_1", "Launch Browser")
        assert node.node_id == "browser_1"
        assert node.name == "Launch Browser"
        assert node.node_type == "LaunchBrowserNode"
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test browser launch."""
        node = LaunchBrowserNode("browser_1", browser_type="chromium", headless=True)
        context = ExecutionContext()
        
        with patch("playwright.async_api.async_playwright") as mock_playwright:
            # Setup mock
            mock_instance = AsyncMock()
            mock_browser = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_playwright.return_value = mock_instance
            
            result = await node.execute(context)
            
            assert result["success"] is True
            assert "browser" in result["data"]
            assert node.status == NodeStatus.SUCCESS


class TestCloseBrowserNode:
    """Tests for CloseBrowserNode."""
    
    def test_initialization(self):
        """Test node initialization."""
        node = CloseBrowserNode("close_1", "Close Browser")
        assert node.node_id == "close_1"
        assert node.name == "Close Browser"
    
    @pytest.mark.asyncio
    async def test_execute_with_browser(self):
        """Test closing browser."""
        node = CloseBrowserNode("close_1")
        context = ExecutionContext()
        
        # Create mock browser
        mock_browser = AsyncMock()
        mock_browser.close = AsyncMock()
        context.set_browser(mock_browser)
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        mock_browser.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_without_browser(self):
        """Test error when no browser."""
        node = CloseBrowserNode("close_1")
        context = ExecutionContext()
        
        result = await node.execute(context)
        
        assert result["success"] is False
        assert node.status == NodeStatus.ERROR


class TestNewTabNode:
    """Tests for NewTabNode."""
    
    def test_initialization(self):
        """Test node initialization."""
        node = NewTabNode("tab_1", "New Tab")
        assert node.node_id == "tab_1"
        assert node.name == "New Tab"
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test creating new tab."""
        node = NewTabNode("tab_1")
        context = ExecutionContext()
        
        # Create mock browser and context
        mock_page = AsyncMock()
        mock_context_obj = AsyncMock()
        mock_context_obj.new_page = AsyncMock(return_value=mock_page)
        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context_obj)
        context.set_browser(mock_browser)
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS


# Test Navigation Nodes

class TestGoToURLNode:
    """Tests for GoToURLNode."""
    
    def test_initialization(self):
        """Test node initialization."""
        node = GoToURLNode("goto_1", "Go To URL", url="https://example.com")
        assert node.node_id == "goto_1"
        assert node.name == "Go To URL"
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test navigation."""
        node = GoToURLNode("goto_1", url="https://example.com")
        context = ExecutionContext()
        
        # Create mock page
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        context.set_active_page(mock_page)
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        mock_page.goto.assert_called_once()


class TestGoBackNode:
    """Tests for GoBackNode."""
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test go back."""
        node = GoBackNode("back_1")
        context = ExecutionContext()
        
        # Create mock page
        mock_page = AsyncMock()
        mock_page.go_back = AsyncMock()
        context.set_active_page(mock_page)
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        mock_page.go_back.assert_called_once()


class TestGoForwardNode:
    """Tests for GoForwardNode."""
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test go forward."""
        node = GoForwardNode("forward_1")
        context = ExecutionContext()
        
        # Create mock page
        mock_page = AsyncMock()
        mock_page.go_forward = AsyncMock()
        context.set_active_page(mock_page)
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        mock_page.go_forward.assert_called_once()


class TestRefreshPageNode:
    """Tests for RefreshPageNode."""
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test page refresh."""
        node = RefreshPageNode("refresh_1")
        context = ExecutionContext()
        
        # Create mock page
        mock_page = AsyncMock()
        mock_page.reload = AsyncMock()
        context.set_active_page(mock_page)
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        mock_page.reload.assert_called_once()


# Test Interaction Nodes

class TestClickElementNode:
    """Tests for ClickElementNode."""
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test clicking element."""
        node = ClickElementNode("click_1", selector="#button")
        context = ExecutionContext()
        
        # Create mock page
        mock_page = AsyncMock()
        mock_page.click = AsyncMock()
        context.set_active_page(mock_page)
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        mock_page.click.assert_called_once()


class TestTypeTextNode:
    """Tests for TypeTextNode."""
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test typing text."""
        node = TypeTextNode("type_1", selector="#input", text="test")
        context = ExecutionContext()
        
        # Create mock page
        mock_page = AsyncMock()
        mock_page.fill = AsyncMock()
        context.set_active_page(mock_page)
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        mock_page.fill.assert_called_once()


class TestSelectDropdownNode:
    """Tests for SelectDropdownNode."""
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test selecting dropdown."""
        node = SelectDropdownNode("select_1", selector="#dropdown", value="option1")
        context = ExecutionContext()
        
        # Create mock page
        mock_page = AsyncMock()
        mock_page.select_option = AsyncMock()
        context.set_active_page(mock_page)
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        mock_page.select_option.assert_called_once()


# Test Data Extraction Nodes

class TestExtractTextNode:
    """Tests for ExtractTextNode."""
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test extracting text."""
        node = ExtractTextNode("extract_1", selector="#content", variable_name="content_text")
        context = ExecutionContext()
        
        # Create mock page and element
        mock_element = AsyncMock()
        mock_element.text_content = AsyncMock(return_value="Test content")
        mock_page = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=mock_element)
        context.set_active_page(mock_page)
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        assert context.get_variable("content_text") == "Test content"


class TestGetAttributeNode:
    """Tests for GetAttributeNode."""
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test getting attribute."""
        node = GetAttributeNode("attr_1", selector="#link", attribute="href", variable_name="link_href")
        context = ExecutionContext()
        
        # Create mock page
        mock_page = AsyncMock()
        mock_page.get_attribute = AsyncMock(return_value="https://example.com")
        context.set_active_page(mock_page)
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        assert context.get_variable("link_href") == "https://example.com"


class TestScreenshotNode:
    """Tests for ScreenshotNode."""
    
    @pytest.mark.asyncio
    async def test_execute(self, tmp_path):
        """Test taking screenshot."""
        screenshot_path = tmp_path / "screenshot.png"
        node = ScreenshotNode("screenshot_1", file_path=str(screenshot_path))
        context = ExecutionContext()
        
        # Create mock page
        mock_page = AsyncMock()
        mock_page.screenshot = AsyncMock()
        context.set_active_page(mock_page)
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        mock_page.screenshot.assert_called_once()


# Test Wait Nodes

class TestWaitNode:
    """Tests for WaitNode."""
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test waiting."""
        node = WaitNode("wait_1", duration=0.1)  # Short duration for testing
        context = ExecutionContext()
        
        import time
        start = time.time()
        result = await node.execute(context)
        elapsed = time.time() - start
        
        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        assert elapsed >= 0.1  # At least the duration


class TestWaitForElementNode:
    """Tests for WaitForElementNode."""
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test waiting for element."""
        node = WaitForElementNode("wait_elem_1", selector="#button")
        context = ExecutionContext()
        
        # Create mock page
        mock_page = AsyncMock()
        mock_page.wait_for_selector = AsyncMock()
        context.set_active_page(mock_page)
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        mock_page.wait_for_selector.assert_called_once()


class TestWaitForNavigationNode:
    """Tests for WaitForNavigationNode."""
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test waiting for navigation."""
        node = WaitForNavigationNode("wait_nav_1")
        context = ExecutionContext()
        
        # Create mock page
        mock_page = AsyncMock()
        mock_page.url = "https://example.com"
        mock_page.wait_for_load_state = AsyncMock()
        context.set_active_page(mock_page)
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        mock_page.wait_for_load_state.assert_called_once()


# Test Variable Nodes

class TestSetVariableNode:
    """Tests for SetVariableNode."""
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test setting variable."""
        node = SetVariableNode("set_1", variable_name="test_var", default_value="test_value")
        context = ExecutionContext()
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        assert context.get_variable("test_var") == "test_value"
    
    @pytest.mark.asyncio
    async def test_execute_with_input(self):
        """Test setting variable with input value."""
        node = SetVariableNode("set_1", variable_name="test_var")
        node.set_input_value("value", "input_value")
        context = ExecutionContext()
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert context.get_variable("test_var") == "input_value"


class TestGetVariableNode:
    """Tests for GetVariableNode."""
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test getting variable."""
        node = GetVariableNode("get_1", variable_name="test_var")
        context = ExecutionContext()
        context.set_variable("test_var", "test_value")
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        assert node.get_output_value("value") == "test_value"
    
    @pytest.mark.asyncio
    async def test_execute_with_default(self):
        """Test getting variable with default."""
        node = GetVariableNode("get_1", variable_name="missing_var", default_value="default")
        context = ExecutionContext()
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert node.get_output_value("value") == "default"


class TestIncrementVariableNode:
    """Tests for IncrementVariableNode."""
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test incrementing variable."""
        node = IncrementVariableNode("inc_1", variable_name="counter", increment=1.0)
        context = ExecutionContext()
        context.set_variable("counter", 5)
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        assert context.get_variable("counter") == 6.0
    
    @pytest.mark.asyncio
    async def test_execute_from_zero(self):
        """Test incrementing from zero (new variable)."""
        node = IncrementVariableNode("inc_1", variable_name="new_counter", increment=2.0)
        context = ExecutionContext()
        
        result = await node.execute(context)
        
        assert result["success"] is True
        assert context.get_variable("new_counter") == 2.0


# Integration tests

class TestNodeIntegration:
    """Integration tests for node workflows."""
    
    @pytest.mark.asyncio
    async def test_variable_flow(self):
        """Test setting and getting variables."""
        context = ExecutionContext()
        
        # Set variable
        set_node = SetVariableNode("set_1", variable_name="msg", default_value="Hello")
        result1 = await set_node.execute(context)
        assert result1["success"] is True
        
        # Get variable
        get_node = GetVariableNode("get_1", variable_name="msg")
        result2 = await get_node.execute(context)
        assert result2["success"] is True
        assert get_node.get_output_value("value") == "Hello"
    
    @pytest.mark.asyncio
    async def test_increment_loop(self):
        """Test incrementing in a loop."""
        context = ExecutionContext()
        context.set_variable("counter", 0)
        
        inc_node = IncrementVariableNode("inc_1", variable_name="counter", increment=1.0)
        
        # Simulate loop
        for _ in range(5):
            result = await inc_node.execute(context)
            assert result["success"] is True
        
        assert context.get_variable("counter") == 5.0
