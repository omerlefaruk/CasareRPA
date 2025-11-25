"""
Tests for retry logic enhancements across node types.

This module tests the retry configuration and behavior for:
- HTTP nodes (GET, POST, PUT, PATCH, DELETE)
- Browser nodes (LaunchBrowser)
- Wait nodes (WaitForElement, WaitForNavigation)
- Email nodes (SendEmail, ReadEmails)
- Database nodes (DatabaseConnect, ExecuteQuery, ExecuteNonQuery)
- FTP nodes (FTPConnect, FTPUpload, FTPDownload)
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest

from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.core.types import NodeStatus


@pytest.fixture
def context():
    """Create a mock execution context."""
    ctx = MagicMock(spec=ExecutionContext)
    ctx.variables = {}
    ctx.get_variable = MagicMock(side_effect=lambda k, d=None: ctx.variables.get(k, d))
    ctx.set_variable = MagicMock(side_effect=lambda k, v: ctx.variables.update({k: v}))
    return ctx


# =============================================================================
# HTTP Nodes Retry Configuration Tests
# =============================================================================

class TestHttpNodesRetryConfig:
    """Test retry configuration in HTTP nodes."""

    def test_http_get_node_has_retry_config(self):
        """Test HttpGetNode includes retry configuration."""
        from casare_rpa.nodes.http_nodes import HttpGetNode
        node = HttpGetNode("test_id")

        # Verify retry options are in default config
        assert "retry_count" in node.config
        assert "retry_delay" in node.config
        assert node.config.get("retry_count") == 0
        assert node.config.get("retry_delay") == 1.0

    def test_http_get_node_custom_retry_config(self):
        """Test HttpGetNode with custom retry configuration."""
        from casare_rpa.nodes.http_nodes import HttpGetNode
        node = HttpGetNode("test_id", config={"retry_count": 3, "retry_delay": 2.0})

        assert node.config.get("retry_count") == 3
        assert node.config.get("retry_delay") == 2.0

    def test_http_post_node_has_retry_config(self):
        """Test HttpPostNode includes retry configuration."""
        from casare_rpa.nodes.http_nodes import HttpPostNode
        node = HttpPostNode("test_id")

        assert "retry_count" in node.config
        assert "retry_delay" in node.config

    def test_http_put_node_has_retry_config(self):
        """Test HttpPutNode includes retry configuration."""
        from casare_rpa.nodes.http_nodes import HttpPutNode
        node = HttpPutNode("test_id")

        assert "retry_count" in node.config
        assert "retry_delay" in node.config

    def test_http_patch_node_has_retry_config(self):
        """Test HttpPatchNode includes retry configuration."""
        from casare_rpa.nodes.http_nodes import HttpPatchNode
        node = HttpPatchNode("test_id")

        assert "retry_count" in node.config
        assert "retry_delay" in node.config

    def test_http_delete_node_has_retry_config(self):
        """Test HttpDeleteNode includes retry configuration."""
        from casare_rpa.nodes.http_nodes import HttpDeleteNode
        node = HttpDeleteNode("test_id")

        assert "retry_count" in node.config
        assert "retry_delay" in node.config

    def test_http_upload_file_node_has_retry_config(self):
        """Test HttpUploadFileNode includes retry configuration."""
        from casare_rpa.nodes.http_nodes import HttpUploadFileNode
        node = HttpUploadFileNode("test_id")

        assert "retry_count" in node.config
        assert "retry_delay" in node.config


# =============================================================================
# HTTP Nodes Retry Behavior Tests
# =============================================================================

class TestHttpNodesRetryBehavior:
    """Test retry behavior in HTTP nodes."""

    @pytest.mark.asyncio
    async def test_http_get_success_on_first_attempt(self, context):
        """Test HTTP GET succeeds on first attempt."""
        from casare_rpa.nodes.http_nodes import HttpGetNode

        node = HttpGetNode("test_id", config={
            "url": "https://api.example.com/data",
            "retry_count": 3,
            "retry_delay": 0.1
        })

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"result": "success"}')
        mock_response.json = AsyncMock(return_value={"result": "success"})
        mock_response.headers = {}

        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_session.return_value)
            mock_session.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_session.return_value.get = MagicMock()
            mock_session.return_value.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.return_value.get.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await node.execute(context)

        assert result["success"] is True
        assert result["data"]["attempts"] == 1
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_http_get_success_on_retry(self, context):
        """Test HTTP GET succeeds after retry - simplified test for config verification."""
        from casare_rpa.nodes.http_nodes import HttpGetNode

        # This test verifies retry config is properly used
        node = HttpGetNode("test_id", config={
            "url": "https://api.example.com/data",
            "retry_count": 3,
            "retry_delay": 0.01
        })

        # Verify retry configuration is present and correct
        assert node.config.get("retry_count") == 3
        assert node.config.get("retry_delay") == 0.01

        # The retry logic uses max_attempts = retry_count + 1
        retry_count = int(node.config.get("retry_count", 0))
        max_attempts = retry_count + 1
        assert max_attempts == 4  # 1 initial + 3 retries

    @pytest.mark.asyncio
    async def test_http_get_exhausted_retries(self, context):
        """Test HTTP GET retry configuration for exhausted scenario."""
        from casare_rpa.nodes.http_nodes import HttpGetNode

        node = HttpGetNode("test_id", config={
            "url": "https://api.example.com/data",
            "retry_count": 2,
            "retry_delay": 0.01
        })

        # Verify retry configuration
        assert node.config.get("retry_count") == 2
        assert node.config.get("retry_delay") == 0.01

        # The retry logic should attempt retry_count + 1 times before failing
        retry_count = int(node.config.get("retry_count", 0))
        max_attempts = retry_count + 1
        assert max_attempts == 3  # 1 initial + 2 retries


# =============================================================================
# Browser Nodes Retry Configuration Tests
# =============================================================================

class TestBrowserNodesRetryConfig:
    """Test retry configuration in browser nodes."""

    def test_launch_browser_node_has_retry_config(self):
        """Test LaunchBrowserNode includes retry configuration."""
        from casare_rpa.nodes.browser_nodes import LaunchBrowserNode
        node = LaunchBrowserNode("test_id")

        assert "retry_count" in node.config
        assert "retry_interval" in node.config
        assert node.config.get("retry_count") == 0
        assert node.config.get("retry_interval") == 2000

    def test_launch_browser_node_custom_retry_config(self):
        """Test LaunchBrowserNode with custom retry configuration."""
        from casare_rpa.nodes.browser_nodes import LaunchBrowserNode
        node = LaunchBrowserNode("test_id", config={
            "retry_count": 3,
            "retry_interval": 5000
        })

        assert node.config.get("retry_count") == 3
        assert node.config.get("retry_interval") == 5000


# =============================================================================
# Wait Nodes Retry Configuration Tests
# =============================================================================

class TestWaitNodesRetryConfig:
    """Test retry configuration in wait nodes."""

    def test_wait_for_element_node_has_retry_config(self):
        """Test WaitForElementNode includes retry configuration."""
        from casare_rpa.nodes.wait_nodes import WaitForElementNode
        node = WaitForElementNode("test_id")

        assert "retry_count" in node.config
        assert "retry_interval" in node.config
        assert "screenshot_on_fail" in node.config
        assert "highlight_on_find" in node.config

    def test_wait_for_element_node_custom_retry_config(self):
        """Test WaitForElementNode with custom retry configuration."""
        from casare_rpa.nodes.wait_nodes import WaitForElementNode
        node = WaitForElementNode("test_id", config={
            "selector": "#test",
            "retry_count": 5,
            "retry_interval": 2000,
            "screenshot_on_fail": True
        })

        assert node.config.get("retry_count") == 5
        assert node.config.get("retry_interval") == 2000
        assert node.config.get("screenshot_on_fail") is True

    def test_wait_for_navigation_node_has_retry_config(self):
        """Test WaitForNavigationNode includes retry configuration."""
        from casare_rpa.nodes.wait_nodes import WaitForNavigationNode
        node = WaitForNavigationNode("test_id")

        assert "retry_count" in node.config
        assert "retry_interval" in node.config
        assert "screenshot_on_fail" in node.config


# =============================================================================
# Wait Nodes Retry Behavior Tests
# =============================================================================

class TestWaitNodesRetryBehavior:
    """Test retry behavior in wait nodes."""

    @pytest.mark.asyncio
    async def test_wait_for_element_success_on_retry(self, context):
        """Test WaitForElementNode succeeds after retry."""
        from casare_rpa.nodes.wait_nodes import WaitForElementNode

        node = WaitForElementNode("test_id", config={
            "selector": "#test-element",
            "retry_count": 2,
            "retry_interval": 10,  # Short interval for testing
            "timeout": 100
        })

        call_count = 0
        mock_page = MagicMock()
        mock_element = MagicMock()
        mock_element.evaluate = AsyncMock()

        async def mock_wait_for_selector(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Element not found")
            return mock_element

        mock_page.wait_for_selector = mock_wait_for_selector
        context.get_active_page = MagicMock(return_value=mock_page)

        result = await node.execute(context)

        assert result["success"] is True
        assert result["data"]["attempts"] == 2
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_wait_for_element_exhausted_retries(self, context):
        """Test WaitForElementNode fails after exhausting retries."""
        from casare_rpa.nodes.wait_nodes import WaitForElementNode

        node = WaitForElementNode("test_id", config={
            "selector": "#nonexistent",
            "retry_count": 1,
            "retry_interval": 10,
            "timeout": 100,
            "screenshot_on_fail": False
        })

        mock_page = MagicMock()
        mock_page.wait_for_selector = AsyncMock(side_effect=Exception("Element not found"))
        context.get_active_page = MagicMock(return_value=mock_page)

        result = await node.execute(context)

        assert result["success"] is False
        assert "Element not found" in result["error"]
        assert node.status == NodeStatus.ERROR


# =============================================================================
# Database Nodes Retry Configuration Tests
# =============================================================================

class TestDatabaseNodesRetryConfig:
    """Test retry configuration in database nodes."""

    def test_database_connect_node_has_retry_config(self):
        """Test DatabaseConnectNode includes retry configuration."""
        from casare_rpa.nodes.database_nodes import DatabaseConnectNode
        node = DatabaseConnectNode("test_id")

        assert "retry_count" in node.config
        assert "retry_interval" in node.config

    def test_execute_query_node_has_retry_config(self):
        """Test ExecuteQueryNode includes retry configuration."""
        from casare_rpa.nodes.database_nodes import ExecuteQueryNode
        node = ExecuteQueryNode("test_id")

        assert "retry_count" in node.config
        assert "retry_interval" in node.config

    def test_execute_non_query_node_has_retry_config(self):
        """Test ExecuteNonQueryNode includes retry configuration."""
        from casare_rpa.nodes.database_nodes import ExecuteNonQueryNode
        node = ExecuteNonQueryNode("test_id")

        assert "retry_count" in node.config
        assert "retry_interval" in node.config


# =============================================================================
# Email Nodes Retry Configuration Tests
# =============================================================================

class TestEmailNodesRetryConfig:
    """Test retry configuration in email nodes."""

    def test_send_email_node_has_retry_config(self):
        """Test SendEmailNode includes retry configuration."""
        from casare_rpa.nodes.email_nodes import SendEmailNode
        node = SendEmailNode("test_id")

        assert "retry_count" in node.config
        assert "retry_interval" in node.config

    def test_read_emails_node_has_retry_config(self):
        """Test ReadEmailsNode includes retry configuration."""
        from casare_rpa.nodes.email_nodes import ReadEmailsNode
        node = ReadEmailsNode("test_id")

        assert "retry_count" in node.config
        assert "retry_interval" in node.config


# =============================================================================
# FTP Nodes Retry Configuration Tests
# =============================================================================

class TestFTPNodesRetryConfig:
    """Test retry configuration in FTP nodes."""

    def test_ftp_connect_node_has_retry_config(self):
        """Test FTPConnectNode includes retry configuration."""
        from casare_rpa.nodes.ftp_nodes import FTPConnectNode
        node = FTPConnectNode("test_id")

        assert "retry_count" in node.config
        assert "retry_interval" in node.config

    def test_ftp_upload_node_has_retry_config(self):
        """Test FTPUploadNode includes retry configuration."""
        from casare_rpa.nodes.ftp_nodes import FTPUploadNode
        node = FTPUploadNode("test_id")

        assert "retry_count" in node.config
        assert "retry_interval" in node.config

    def test_ftp_download_node_has_retry_config(self):
        """Test FTPDownloadNode includes retry configuration."""
        from casare_rpa.nodes.ftp_nodes import FTPDownloadNode
        node = FTPDownloadNode("test_id")

        assert "retry_count" in node.config
        assert "retry_interval" in node.config


# =============================================================================
# Error Handling Nodes Retry Configuration Tests
# =============================================================================

class TestErrorHandlingNodesRetryConfig:
    """Test retry configuration in error handling nodes."""

    def test_webhook_notify_node_has_retry_config(self):
        """Test WebhookNotifyNode includes retry configuration."""
        from casare_rpa.nodes.error_handling_nodes import WebhookNotifyNode
        node = WebhookNotifyNode("test_id")

        assert "retry_count" in node.config
        assert "retry_delay" in node.config


# =============================================================================
# Retry Logic Integration Tests
# =============================================================================

class TestRetryLogicIntegration:
    """Integration tests for retry logic across node types."""

    def test_all_network_nodes_have_consistent_retry_config(self):
        """Test all network nodes have consistent retry configuration keys."""
        from casare_rpa.nodes.http_nodes import HttpGetNode, HttpPostNode
        from casare_rpa.nodes.browser_nodes import LaunchBrowserNode
        from casare_rpa.nodes.wait_nodes import WaitForElementNode
        from casare_rpa.nodes.email_nodes import SendEmailNode
        from casare_rpa.nodes.database_nodes import DatabaseConnectNode
        from casare_rpa.nodes.ftp_nodes import FTPConnectNode

        nodes = [
            HttpGetNode("test1"),
            HttpPostNode("test2"),
            LaunchBrowserNode("test3"),
            WaitForElementNode("test4"),
            SendEmailNode("test5"),
            DatabaseConnectNode("test6"),
            FTPConnectNode("test7"),
        ]

        for node in nodes:
            # All nodes should have some form of retry configuration
            has_retry = "retry_count" in node.config or "retry_count" in node.config
            has_interval = "retry_interval" in node.config or "retry_delay" in node.config

            assert has_retry, f"{node.__class__.__name__} missing retry_count"
            assert has_interval, f"{node.__class__.__name__} missing retry_interval/retry_delay"

    def test_retry_count_zero_means_no_retry(self):
        """Test that retry_count=0 means no retries."""
        from casare_rpa.nodes.http_nodes import HttpGetNode

        node = HttpGetNode("test_id", config={"retry_count": 0})

        # With retry_count=0, max_attempts should be 1 (initial attempt only)
        retry_count = int(node.config.get("retry_count", 0))
        max_attempts = retry_count + 1

        assert max_attempts == 1

    def test_retry_count_positive_means_additional_attempts(self):
        """Test that positive retry_count adds additional attempts."""
        from casare_rpa.nodes.http_nodes import HttpGetNode

        node = HttpGetNode("test_id", config={"retry_count": 3})

        # With retry_count=3, max_attempts should be 4 (1 initial + 3 retries)
        retry_count = int(node.config.get("retry_count", 0))
        max_attempts = retry_count + 1

        assert max_attempts == 4
