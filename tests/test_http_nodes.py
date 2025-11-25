"""
Tests for HTTP/REST API nodes.

This module tests all HTTP nodes including GET, POST, PUT, PATCH, DELETE,
authentication, headers, JSON parsing, file upload/download, and URL building.
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.core.types import NodeStatus
from casare_rpa.nodes.http_nodes import (
    HttpRequestNode,
    HttpGetNode,
    HttpPostNode,
    HttpPutNode,
    HttpPatchNode,
    HttpDeleteNode,
    SetHttpHeadersNode,
    HttpAuthNode,
    ParseJsonResponseNode,
    HttpDownloadFileNode,
    HttpUploadFileNode,
    BuildUrlNode,
)


@pytest.fixture
def context():
    """Create a mock execution context."""
    ctx = MagicMock(spec=ExecutionContext)
    ctx.variables = {}
    ctx.get_variable = MagicMock(side_effect=lambda k, d=None: ctx.variables.get(k, d))
    ctx.set_variable = MagicMock(side_effect=lambda k, v: ctx.variables.update({k: v}))
    return ctx


@pytest.fixture
def temp_dir():
    """Create a temporary directory for file tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# =============================================================================
# HttpRequestNode Tests
# =============================================================================

class TestHttpRequestNode:
    """Tests for HttpRequestNode."""

    def test_init_default_config(self):
        """Test node initialization with default config."""
        node = HttpRequestNode("test_id")
        assert node.node_type == "HttpRequestNode"
        assert node.config.get("method") == "GET"
        assert node.config.get("timeout") == 30.0
        assert node.config.get("verify_ssl") is True

    def test_init_custom_config(self):
        """Test node initialization with custom config."""
        node = HttpRequestNode(
            "test_id",
            config={
                "method": "POST",
                "url": "https://api.example.com",
                "timeout": 60.0,
            }
        )
        assert node.config.get("method") == "POST"
        assert node.config.get("url") == "https://api.example.com"
        assert node.config.get("timeout") == 60.0

    def test_ports_defined(self):
        """Test that all required ports are defined."""
        node = HttpRequestNode("test_id")

        # Check input ports
        assert "exec_in" in node.input_ports
        assert "url" in node.input_ports
        assert "method" in node.input_ports
        assert "headers" in node.input_ports
        assert "body" in node.input_ports
        assert "params" in node.input_ports

        # Check output ports
        assert "exec_out" in node.output_ports
        assert "response_body" in node.output_ports
        assert "response_json" in node.output_ports
        assert "status_code" in node.output_ports
        assert "success" in node.output_ports
        assert "error" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_missing_url(self, context):
        """Test execution fails without URL."""
        node = HttpRequestNode("test_id")
        result = await node.execute(context)

        assert result["success"] is False
        assert "URL is required" in result["error"]
        assert node.status == NodeStatus.ERROR

    @pytest.mark.asyncio
    async def test_execute_get_success(self, context):
        """Test successful GET request."""
        node = HttpRequestNode("test_id")
        node.set_input_value("url", "https://httpbin.org/get")

        # Mock aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"success": true}')
        mock_response.headers = {"Content-Type": "application/json"}

        mock_session = AsyncMock()
        mock_session.request = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))

        with patch('aiohttp.ClientSession') as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await node.execute(context)

        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        assert node.get_output_value("status_code") == 200
        assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_execute_post_with_body(self, context):
        """Test POST request with JSON body."""
        node = HttpRequestNode("test_id", config={"method": "POST"})
        node.set_input_value("url", "https://httpbin.org/post")
        node.set_input_value("body", {"name": "test", "value": 123})

        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.text = AsyncMock(return_value='{"id": 1}')
        mock_response.headers = {"Content-Type": "application/json"}

        mock_session = AsyncMock()
        mock_session.request = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))

        with patch('aiohttp.ClientSession') as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("status_code") == 201


# =============================================================================
# HttpGetNode Tests
# =============================================================================

class TestHttpGetNode:
    """Tests for HttpGetNode."""

    def test_init(self):
        """Test node initialization."""
        node = HttpGetNode("test_id")
        assert node.node_type == "HttpGetNode"
        assert node.name == "HTTP GET"

    def test_ports_defined(self):
        """Test that required ports are defined."""
        node = HttpGetNode("test_id")

        assert "url" in node.input_ports
        assert "params" in node.input_ports
        assert "headers" in node.input_ports
        assert "response_body" in node.output_ports
        assert "response_json" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_with_params(self, context):
        """Test GET request with query parameters."""
        node = HttpGetNode("test_id")
        node.set_input_value("url", "https://httpbin.org/get")
        node.set_input_value("params", {"key": "value", "page": "1"})

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"args": {"key": "value"}}')

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))

        with patch('aiohttp.ClientSession') as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("success") is True


# =============================================================================
# HttpPostNode Tests
# =============================================================================

class TestHttpPostNode:
    """Tests for HttpPostNode."""

    def test_init(self):
        """Test node initialization."""
        node = HttpPostNode("test_id")
        assert node.node_type == "HttpPostNode"
        assert node.config.get("content_type") == "application/json"

    def test_ports_defined(self):
        """Test that required ports are defined."""
        node = HttpPostNode("test_id")

        assert "url" in node.input_ports
        assert "body" in node.input_ports
        assert "response_body" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_json_body(self, context):
        """Test POST request with JSON body."""
        node = HttpPostNode("test_id")
        node.set_input_value("url", "https://httpbin.org/post")
        node.set_input_value("body", {"test": "data"})

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"received": true}')

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))

        with patch('aiohttp.ClientSession') as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await node.execute(context)

        assert result["success"] is True


# =============================================================================
# HttpPutNode Tests
# =============================================================================

class TestHttpPutNode:
    """Tests for HttpPutNode."""

    def test_init(self):
        """Test node initialization."""
        node = HttpPutNode("test_id")
        assert node.node_type == "HttpPutNode"

    @pytest.mark.asyncio
    async def test_execute_update_resource(self, context):
        """Test PUT request for updating resource."""
        node = HttpPutNode("test_id")
        node.set_input_value("url", "https://httpbin.org/put")
        node.set_input_value("body", {"id": 1, "name": "updated"})

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"updated": true}')

        mock_session = AsyncMock()
        mock_session.put = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))

        with patch('aiohttp.ClientSession') as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await node.execute(context)

        assert result["success"] is True


# =============================================================================
# HttpPatchNode Tests
# =============================================================================

class TestHttpPatchNode:
    """Tests for HttpPatchNode."""

    def test_init(self):
        """Test node initialization."""
        node = HttpPatchNode("test_id")
        assert node.node_type == "HttpPatchNode"

    @pytest.mark.asyncio
    async def test_execute_partial_update(self, context):
        """Test PATCH request for partial update."""
        node = HttpPatchNode("test_id")
        node.set_input_value("url", "https://httpbin.org/patch")
        node.set_input_value("body", {"name": "new_name"})

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value='{"patched": true}')

        mock_session = AsyncMock()
        mock_session.patch = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))

        with patch('aiohttp.ClientSession') as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await node.execute(context)

        assert result["success"] is True


# =============================================================================
# HttpDeleteNode Tests
# =============================================================================

class TestHttpDeleteNode:
    """Tests for HttpDeleteNode."""

    def test_init(self):
        """Test node initialization."""
        node = HttpDeleteNode("test_id")
        assert node.node_type == "HttpDeleteNode"

    def test_ports_defined(self):
        """Test that required ports are defined."""
        node = HttpDeleteNode("test_id")

        assert "url" in node.input_ports
        # DELETE typically doesn't have a body input
        assert "response_body" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_delete_resource(self, context):
        """Test DELETE request for removing resource."""
        node = HttpDeleteNode("test_id")
        node.set_input_value("url", "https://httpbin.org/delete")

        mock_response = AsyncMock()
        mock_response.status = 204
        mock_response.text = AsyncMock(return_value='')

        mock_session = AsyncMock()
        mock_session.delete = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))

        with patch('aiohttp.ClientSession') as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("status_code") == 204


# =============================================================================
# SetHttpHeadersNode Tests
# =============================================================================

class TestSetHttpHeadersNode:
    """Tests for SetHttpHeadersNode."""

    def test_init(self):
        """Test node initialization."""
        node = SetHttpHeadersNode("test_id")
        assert node.node_type == "SetHttpHeadersNode"

    def test_ports_defined(self):
        """Test that required ports are defined."""
        node = SetHttpHeadersNode("test_id")

        assert "base_headers" in node.input_ports
        assert "header_name" in node.input_ports
        assert "header_value" in node.input_ports
        assert "headers" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_single_header(self, context):
        """Test setting a single header."""
        node = SetHttpHeadersNode("test_id")
        node.set_input_value("header_name", "Authorization")
        node.set_input_value("header_value", "Bearer token123")

        result = await node.execute(context)

        assert result["success"] is True
        headers = node.get_output_value("headers")
        assert headers["Authorization"] == "Bearer token123"

    @pytest.mark.asyncio
    async def test_execute_extend_base_headers(self, context):
        """Test extending base headers."""
        node = SetHttpHeadersNode("test_id")
        node.set_input_value("base_headers", {"Content-Type": "application/json"})
        node.set_input_value("header_name", "X-Custom-Header")
        node.set_input_value("header_value", "custom_value")

        result = await node.execute(context)

        assert result["success"] is True
        headers = node.get_output_value("headers")
        assert headers["Content-Type"] == "application/json"
        assert headers["X-Custom-Header"] == "custom_value"

    @pytest.mark.asyncio
    async def test_execute_json_headers(self, context):
        """Test setting headers from JSON string."""
        node = SetHttpHeadersNode("test_id")
        node.set_input_value("headers_json", '{"Accept": "application/xml", "Cache-Control": "no-cache"}')

        result = await node.execute(context)

        assert result["success"] is True
        headers = node.get_output_value("headers")
        assert headers["Accept"] == "application/xml"
        assert headers["Cache-Control"] == "no-cache"


# =============================================================================
# HttpAuthNode Tests
# =============================================================================

class TestHttpAuthNode:
    """Tests for HttpAuthNode."""

    def test_init(self):
        """Test node initialization."""
        node = HttpAuthNode("test_id")
        assert node.node_type == "HttpAuthNode"
        assert node.config.get("auth_type") == "Bearer"

    def test_ports_defined(self):
        """Test that required ports are defined."""
        node = HttpAuthNode("test_id")

        assert "token" in node.input_ports
        assert "username" in node.input_ports
        assert "password" in node.input_ports
        assert "headers" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_bearer_auth(self, context):
        """Test Bearer token authentication."""
        node = HttpAuthNode("test_id", config={"auth_type": "Bearer"})
        node.set_input_value("token", "my_secret_token")

        result = await node.execute(context)

        assert result["success"] is True
        headers = node.get_output_value("headers")
        assert headers["Authorization"] == "Bearer my_secret_token"

    @pytest.mark.asyncio
    async def test_execute_basic_auth(self, context):
        """Test Basic authentication."""
        node = HttpAuthNode("test_id", config={"auth_type": "Basic"})
        node.set_input_value("username", "user")
        node.set_input_value("password", "pass")

        result = await node.execute(context)

        assert result["success"] is True
        headers = node.get_output_value("headers")
        assert headers["Authorization"].startswith("Basic ")
        # Verify it's base64 encoded
        import base64
        decoded = base64.b64decode(headers["Authorization"].split(" ")[1]).decode()
        assert decoded == "user:pass"

    @pytest.mark.asyncio
    async def test_execute_api_key_auth(self, context):
        """Test API Key authentication."""
        node = HttpAuthNode("test_id", config={"auth_type": "ApiKey"})
        node.set_input_value("token", "api_key_123")
        node.set_input_value("api_key_name", "X-API-Key")

        result = await node.execute(context)

        assert result["success"] is True
        headers = node.get_output_value("headers")
        assert headers["X-API-Key"] == "api_key_123"

    @pytest.mark.asyncio
    async def test_execute_missing_token(self, context):
        """Test error when token is missing for Bearer auth."""
        node = HttpAuthNode("test_id", config={"auth_type": "Bearer"})

        result = await node.execute(context)

        assert result["success"] is False
        assert "token is required" in result["error"].lower()


# =============================================================================
# ParseJsonResponseNode Tests
# =============================================================================

class TestParseJsonResponseNode:
    """Tests for ParseJsonResponseNode."""

    def test_init(self):
        """Test node initialization."""
        node = ParseJsonResponseNode("test_id")
        assert node.node_type == "ParseJsonResponseNode"

    def test_ports_defined(self):
        """Test that required ports are defined."""
        node = ParseJsonResponseNode("test_id")

        assert "json_data" in node.input_ports
        assert "path" in node.input_ports
        assert "value" in node.output_ports
        assert "success" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_simple_path(self, context):
        """Test extracting value with simple path."""
        node = ParseJsonResponseNode("test_id")
        node.set_input_value("json_data", {"name": "John", "age": 30})
        node.set_input_value("path", "name")

        result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("value") == "John"

    @pytest.mark.asyncio
    async def test_execute_nested_path(self, context):
        """Test extracting value with nested path."""
        node = ParseJsonResponseNode("test_id")
        node.set_input_value("json_data", {
            "data": {
                "user": {
                    "name": "Alice"
                }
            }
        })
        node.set_input_value("path", "data.user.name")

        result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("value") == "Alice"

    @pytest.mark.asyncio
    async def test_execute_array_index(self, context):
        """Test extracting value from array by index."""
        node = ParseJsonResponseNode("test_id")
        node.set_input_value("json_data", {
            "users": [
                {"name": "First"},
                {"name": "Second"},
                {"name": "Third"}
            ]
        })
        node.set_input_value("path", "users[1].name")

        result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("value") == "Second"

    @pytest.mark.asyncio
    async def test_execute_from_json_string(self, context):
        """Test parsing from JSON string."""
        node = ParseJsonResponseNode("test_id")
        node.set_input_value("json_data", '{"status": "ok", "count": 42}')
        node.set_input_value("path", "count")

        result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("value") == 42

    @pytest.mark.asyncio
    async def test_execute_with_default(self, context):
        """Test using default value when path not found."""
        node = ParseJsonResponseNode("test_id")
        node.set_input_value("json_data", {"name": "John"})
        node.set_input_value("path", "missing_key")
        node.set_input_value("default", "default_value")

        result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("value") == "default_value"

    @pytest.mark.asyncio
    async def test_execute_invalid_json(self, context):
        """Test error with invalid JSON string."""
        node = ParseJsonResponseNode("test_id")
        node.set_input_value("json_data", "not valid json")
        node.set_input_value("path", "key")

        result = await node.execute(context)

        assert result["success"] is False
        assert "Invalid JSON" in result["error"]


# =============================================================================
# HttpDownloadFileNode Tests
# =============================================================================

class TestHttpDownloadFileNode:
    """Tests for HttpDownloadFileNode."""

    def test_init(self):
        """Test node initialization."""
        node = HttpDownloadFileNode("test_id")
        assert node.node_type == "HttpDownloadFileNode"
        assert node.config.get("timeout") == 300.0

    def test_ports_defined(self):
        """Test that required ports are defined."""
        node = HttpDownloadFileNode("test_id")

        assert "url" in node.input_ports
        assert "save_path" in node.input_ports
        assert "file_path" in node.output_ports
        assert "file_size" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_missing_url(self, context):
        """Test error when URL is missing."""
        node = HttpDownloadFileNode("test_id")
        node.set_input_value("save_path", "/tmp/file.txt")

        result = await node.execute(context)

        assert result["success"] is False
        assert "URL is required" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_missing_save_path(self, context):
        """Test error when save path is missing."""
        node = HttpDownloadFileNode("test_id")
        node.set_input_value("url", "https://example.com/file.txt")

        result = await node.execute(context)

        assert result["success"] is False
        assert "Save path is required" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_download_success(self, context, temp_dir):
        """Test successful file download."""
        node = HttpDownloadFileNode("test_id")
        save_path = temp_dir / "downloaded.txt"
        node.set_input_value("url", "https://example.com/file.txt")
        node.set_input_value("save_path", str(save_path))

        # Mock response with chunked content
        mock_content = AsyncMock()
        mock_content.iter_chunked = MagicMock(return_value=async_iter([b"Hello, ", b"World!"]))

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.content = mock_content

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_response)))

        with patch('aiohttp.ClientSession') as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await node.execute(context)

        assert result["success"] is True
        assert save_path.exists()
        assert save_path.read_text() == "Hello, World!"


# =============================================================================
# HttpUploadFileNode Tests
# =============================================================================

class TestHttpUploadFileNode:
    """Tests for HttpUploadFileNode."""

    def test_init(self):
        """Test node initialization."""
        node = HttpUploadFileNode("test_id")
        assert node.node_type == "HttpUploadFileNode"
        assert node.config.get("field_name") == "file"

    def test_ports_defined(self):
        """Test that required ports are defined."""
        node = HttpUploadFileNode("test_id")

        assert "url" in node.input_ports
        assert "file_path" in node.input_ports
        assert "field_name" in node.input_ports
        assert "response_body" in node.output_ports
        assert "status_code" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_missing_url(self, context):
        """Test error when URL is missing."""
        node = HttpUploadFileNode("test_id")
        node.set_input_value("file_path", "/tmp/file.txt")

        result = await node.execute(context)

        assert result["success"] is False
        assert "URL is required" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_missing_file(self, context):
        """Test error when file doesn't exist."""
        node = HttpUploadFileNode("test_id")
        node.set_input_value("url", "https://example.com/upload")
        node.set_input_value("file_path", "/nonexistent/file.txt")

        result = await node.execute(context)

        assert result["success"] is False
        assert "not found" in result["error"].lower() or "File path is required" in result["error"]


# =============================================================================
# BuildUrlNode Tests
# =============================================================================

class TestBuildUrlNode:
    """Tests for BuildUrlNode."""

    def test_init(self):
        """Test node initialization."""
        node = BuildUrlNode("test_id")
        assert node.node_type == "BuildUrlNode"

    def test_ports_defined(self):
        """Test that required ports are defined."""
        node = BuildUrlNode("test_id")

        assert "base_url" in node.input_ports
        assert "path" in node.input_ports
        assert "params" in node.input_ports
        assert "url" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_base_url_only(self, context):
        """Test building URL with base URL only."""
        node = BuildUrlNode("test_id")
        node.set_input_value("base_url", "https://api.example.com")

        result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("url") == "https://api.example.com"

    @pytest.mark.asyncio
    async def test_execute_with_path(self, context):
        """Test building URL with path."""
        node = BuildUrlNode("test_id")
        node.set_input_value("base_url", "https://api.example.com")
        node.set_input_value("path", "users/123")

        result = await node.execute(context)

        assert result["success"] is True
        assert node.get_output_value("url") == "https://api.example.com/users/123"

    @pytest.mark.asyncio
    async def test_execute_with_params(self, context):
        """Test building URL with query parameters."""
        node = BuildUrlNode("test_id")
        node.set_input_value("base_url", "https://api.example.com")
        node.set_input_value("path", "search")
        node.set_input_value("params", {"q": "test", "page": "1"})

        result = await node.execute(context)

        assert result["success"] is True
        url = node.get_output_value("url")
        assert "https://api.example.com/search?" in url
        assert "q=test" in url
        assert "page=1" in url

    @pytest.mark.asyncio
    async def test_execute_missing_base_url(self, context):
        """Test error when base URL is missing."""
        node = BuildUrlNode("test_id")

        result = await node.execute(context)

        assert result["success"] is False
        assert "Base URL is required" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_trailing_slash_handling(self, context):
        """Test proper handling of trailing slashes."""
        node = BuildUrlNode("test_id")
        node.set_input_value("base_url", "https://api.example.com/")
        node.set_input_value("path", "/users")

        result = await node.execute(context)

        assert result["success"] is True
        # Should not have double slashes
        url = node.get_output_value("url")
        assert "//" not in url.replace("https://", "")


# =============================================================================
# Integration Tests
# =============================================================================

class TestHttpNodesIntegration:
    """Integration tests for HTTP nodes working together."""

    @pytest.mark.asyncio
    async def test_auth_then_get_request(self, context):
        """Test using HttpAuthNode output with HttpGetNode."""
        # First, create auth headers
        auth_node = HttpAuthNode("auth_id", config={"auth_type": "Bearer"})
        auth_node.set_input_value("token", "test_token")

        auth_result = await auth_node.execute(context)
        assert auth_result["success"] is True

        # Use headers in GET request
        get_node = HttpGetNode("get_id")
        get_node.set_input_value("url", "https://api.example.com/data")
        get_node.set_input_value("headers", auth_node.get_output_value("headers"))

        # The headers should include Authorization
        headers = get_node.get_input_value("headers")
        assert "Authorization" in headers

    @pytest.mark.asyncio
    async def test_build_url_then_request(self, context):
        """Test using BuildUrlNode output with HttpGetNode."""
        # Build URL
        url_node = BuildUrlNode("url_id")
        url_node.set_input_value("base_url", "https://api.example.com")
        url_node.set_input_value("path", "users")
        url_node.set_input_value("params", {"page": "1", "limit": "10"})

        url_result = await url_node.execute(context)
        assert url_result["success"] is True

        built_url = url_node.get_output_value("url")
        assert "page=1" in built_url
        assert "limit=10" in built_url


# =============================================================================
# Helper Functions
# =============================================================================

async def async_iter(items):
    """Helper to create async iterator from list."""
    for item in items:
        yield item


# =============================================================================
# Node Export Tests
# =============================================================================

class TestHttpNodesExports:
    """Tests for HTTP nodes module exports."""

    def test_all_nodes_importable(self):
        """Test that all HTTP nodes can be imported."""
        from casare_rpa.nodes import (
            HttpGetNode,
            HttpPostNode,
            HttpPutNode,
            HttpPatchNode,
            HttpDeleteNode,
            SetHttpHeadersNode,
            HttpAuthNode,
            ParseJsonResponseNode,
            HttpDownloadFileNode,
            HttpUploadFileNode,
            BuildUrlNode,
        )

        # All imports should succeed
        assert HttpGetNode is not None
        assert HttpPostNode is not None
        assert HttpPutNode is not None
        assert HttpPatchNode is not None
        assert HttpDeleteNode is not None
        assert SetHttpHeadersNode is not None
        assert HttpAuthNode is not None
        assert ParseJsonResponseNode is not None
        assert HttpDownloadFileNode is not None
        assert HttpUploadFileNode is not None
        assert BuildUrlNode is not None

    def test_nodes_in_registry(self):
        """Test that all HTTP nodes are registered."""
        from casare_rpa.nodes import __all__

        http_nodes = [
            "HttpGetNode",
            "HttpPostNode",
            "HttpPutNode",
            "HttpPatchNode",
            "HttpDeleteNode",
            "SetHttpHeadersNode",
            "HttpAuthNode",
            "ParseJsonResponseNode",
            "HttpDownloadFileNode",
            "HttpUploadFileNode",
            "BuildUrlNode",
        ]

        for node_name in http_nodes:
            assert node_name in __all__, f"{node_name} should be in __all__"
