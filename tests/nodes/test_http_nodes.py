"""
Comprehensive tests for HTTP/REST API nodes.

Tests all 12 HTTP nodes:
- HttpRequestNode, HttpGetNode, HttpPostNode, HttpPutNode, HttpPatchNode, HttpDeleteNode
- SetHttpHeadersNode, HttpAuthNode, ParseJsonResponseNode
- HttpDownloadFileNode, HttpUploadFileNode, BuildUrlNode

Fixtures and helpers defined in tests/nodes/conftest.py:
- create_mock_response: Create mock aiohttp response
- create_mock_session: Create mock aiohttp ClientSession
- mock_aiohttp_response: Fixture providing mock response
- mock_aiohttp_session: Fixture providing mock session

The create_mock_response and create_mock_session functions are defined locally
but moved to conftest.py to avoid duplication. Test code remains unchanged.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio
import json
import base64
from pathlib import Path
import tempfile
import os

# Uses execution_context fixture from conftest.py - no import needed
from casare_rpa.domain.value_objects.types import NodeStatus
from casare_rpa.infrastructure.execution import ExecutionContext


# Define mock helpers locally (from conftest.py in tests/nodes/)
def create_mock_response(
    status: int = 200, body: str = '{"status": "ok"}', headers: dict = None
):
    """Create a mock aiohttp response."""
    mock_response = AsyncMock()
    mock_response.status = status
    mock_response.text = AsyncMock(return_value=body)
    mock_response.headers = headers or {"Content-Type": "application/json"}
    return mock_response


def create_mock_session(response):
    """Create a mock aiohttp ClientSession."""
    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=response)
    mock_context.__aexit__ = AsyncMock(return_value=None)

    mock_session.get = MagicMock(return_value=mock_context)
    mock_session.post = MagicMock(return_value=mock_context)
    mock_session.put = MagicMock(return_value=mock_context)
    mock_session.patch = MagicMock(return_value=mock_context)
    mock_session.delete = MagicMock(return_value=mock_context)
    mock_session.request = MagicMock(return_value=mock_context)

    return mock_session


class TestHttpRequestNode:
    """Tests for generic HttpRequestNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_http_request_get(self, execution_context) -> None:
        """Test HttpRequestNode with GET method."""
        from casare_rpa.nodes.http import HttpRequestNode

        node = HttpRequestNode(
            node_id="test_request_get",
            config={"url": "https://api.example.com/data", "method": "GET"},
        )

        mock_response = create_mock_response(200, '{"data": "value"}')
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["status_code"] == 200
        assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_http_request_post_with_body(self, execution_context) -> None:
        """Test HttpRequestNode POST with JSON body."""
        from casare_rpa.nodes.http import HttpRequestNode

        node = HttpRequestNode(
            node_id="test_request_post",
            config={"url": "https://api.example.com/create", "method": "POST"},
        )
        node.set_input_value("body", {"name": "test", "value": 123})

        mock_response = create_mock_response(201, '{"id": 1}')
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["status_code"] == 201

    @pytest.mark.asyncio
    async def test_http_request_missing_url(self, execution_context) -> None:
        """Test HttpRequestNode fails without URL."""
        from casare_rpa.nodes.http import HttpRequestNode

        node = HttpRequestNode(node_id="test_request_no_url")
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "URL is required" in result["error"]

    @pytest.mark.asyncio
    async def test_http_request_error_status(self, execution_context) -> None:
        """Test HttpRequestNode handles error status codes."""
        from casare_rpa.nodes.http import HttpRequestNode

        node = HttpRequestNode(
            node_id="test_request_error",
            config={"url": "https://api.example.com/notfound"},
        )

        mock_response = create_mock_response(404, '{"error": "Not found"}')
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await node.execute(execution_context)

        assert result["success"] is True  # Node succeeded
        assert node.get_output_value("success") is False  # HTTP failed
        assert node.get_output_value("status_code") == 404


class TestHttpGetNode:
    """Tests for HttpGetNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_http_get_basic(self, execution_context) -> None:
        """Test HttpGetNode basic request."""
        from casare_rpa.nodes.http import HttpGetNode

        node = HttpGetNode(
            node_id="test_get", config={"url": "https://api.example.com/users"}
        )

        mock_response = create_mock_response(200, '[{"id": 1, "name": "John"}]')
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("status_code") == 200
        response_json = node.get_output_value("response_json")
        assert response_json[0]["name"] == "John"

    @pytest.mark.asyncio
    async def test_http_get_with_params(self, execution_context) -> None:
        """Test HttpGetNode with query parameters."""
        from casare_rpa.nodes.http import HttpGetNode

        node = HttpGetNode(
            node_id="test_get_params", config={"url": "https://api.example.com/search"}
        )
        node.set_input_value("params", {"q": "test", "limit": "10"})

        mock_response = create_mock_response(200, '{"results": []}')
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_http_get_with_headers(self, execution_context) -> None:
        """Test HttpGetNode with custom headers."""
        from casare_rpa.nodes.http import HttpGetNode

        node = HttpGetNode(
            node_id="test_get_headers",
            config={"url": "https://api.example.com/private"},
        )
        node.set_input_value("headers", {"Authorization": "Bearer token123"})

        mock_response = create_mock_response(200, '{"private": "data"}')
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_http_get_non_json_response(self, execution_context) -> None:
        """Test HttpGetNode handles non-JSON response."""
        from casare_rpa.nodes.http import HttpGetNode

        node = HttpGetNode(
            node_id="test_get_text", config={"url": "https://example.com/text"}
        )

        mock_response = create_mock_response(200, "Plain text response")
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("response_body") == "Plain text response"
        assert node.get_output_value("response_json") is None


class TestHttpPostNode:
    """Tests for HttpPostNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_http_post_json_body(self, execution_context) -> None:
        """Test HttpPostNode with JSON body."""
        from casare_rpa.nodes.http import HttpPostNode

        node = HttpPostNode(
            node_id="test_post_json", config={"url": "https://api.example.com/users"}
        )
        node.set_input_value("body", {"name": "Jane", "email": "jane@example.com"})

        mock_response = create_mock_response(201, '{"id": 123}')
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("status_code") == 201
        assert node.get_output_value("response_json")["id"] == 123

    @pytest.mark.asyncio
    async def test_http_post_string_body(self, execution_context) -> None:
        """Test HttpPostNode with string body."""
        from casare_rpa.nodes.http import HttpPostNode

        node = HttpPostNode(
            node_id="test_post_string",
            config={
                "url": "https://api.example.com/data",
                "content_type": "text/plain",
            },
        )
        node.set_input_value("body", "Raw string data")

        mock_response = create_mock_response(200, "OK")
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_http_post_server_error(self, execution_context) -> None:
        """Test HttpPostNode handles 500 server error."""
        from casare_rpa.nodes.http import HttpPostNode

        node = HttpPostNode(
            node_id="test_post_error", config={"url": "https://api.example.com/fail"}
        )

        mock_response = create_mock_response(500, '{"error": "Internal Server Error"}')
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await node.execute(execution_context)

        assert result["success"] is True  # Node execution succeeded
        assert node.get_output_value("success") is False  # HTTP request failed


class TestHttpPutNode:
    """Tests for HttpPutNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_http_put_update(self, execution_context) -> None:
        """Test HttpPutNode for resource update."""
        from casare_rpa.nodes.http import HttpPutNode

        node = HttpPutNode(
            node_id="test_put", config={"url": "https://api.example.com/users/123"}
        )
        node.set_input_value("body", {"name": "Updated Name"})

        mock_response = create_mock_response(200, '{"id": 123, "name": "Updated Name"}')
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("status_code") == 200


class TestHttpPatchNode:
    """Tests for HttpPatchNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_http_patch_partial_update(self, execution_context) -> None:
        """Test HttpPatchNode for partial update."""
        from casare_rpa.nodes.http import HttpPatchNode

        node = HttpPatchNode(
            node_id="test_patch", config={"url": "https://api.example.com/users/123"}
        )
        node.set_input_value("body", {"email": "newemail@example.com"})

        mock_response = create_mock_response(
            200, '{"id": 123, "email": "newemail@example.com"}'
        )
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("status_code") == 200


class TestHttpDeleteNode:
    """Tests for HttpDeleteNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_http_delete_resource(self, execution_context) -> None:
        """Test HttpDeleteNode for resource deletion."""
        from casare_rpa.nodes.http import HttpDeleteNode

        node = HttpDeleteNode(
            node_id="test_delete", config={"url": "https://api.example.com/users/123"}
        )

        mock_response = create_mock_response(204, "")
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("status_code") == 204

    @pytest.mark.asyncio
    async def test_http_delete_with_body(self, execution_context) -> None:
        """Test HttpDeleteNode returns response body if present."""
        from casare_rpa.nodes.http import HttpDeleteNode

        node = HttpDeleteNode(
            node_id="test_delete_body",
            config={"url": "https://api.example.com/items/456"},
        )

        mock_response = create_mock_response(200, '{"deleted": true}')
        mock_session = create_mock_session(mock_response)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("response_body") == '{"deleted": true}'


class TestSetHttpHeadersNode:
    """Tests for SetHttpHeadersNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        return context

    @pytest.mark.asyncio
    async def test_set_single_header(self, execution_context) -> None:
        """Test SetHttpHeadersNode adds single header."""
        from casare_rpa.nodes.http import SetHttpHeadersNode

        node = SetHttpHeadersNode(node_id="test_headers_single")
        node.set_input_value("header_name", "X-Custom-Header")
        node.set_input_value("header_value", "custom-value")

        result = await node.execute(execution_context)

        assert result["success"] is True
        headers = node.get_output_value("headers")
        assert headers["X-Custom-Header"] == "custom-value"

    @pytest.mark.asyncio
    async def test_set_headers_from_json(self, execution_context) -> None:
        """Test SetHttpHeadersNode parses JSON headers."""
        from casare_rpa.nodes.http import SetHttpHeadersNode

        node = SetHttpHeadersNode(node_id="test_headers_json")
        node.set_input_value(
            "headers_json", '{"Accept": "application/json", "X-API-Version": "2"}'
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        headers = node.get_output_value("headers")
        assert headers["Accept"] == "application/json"
        assert headers["X-API-Version"] == "2"

    @pytest.mark.asyncio
    async def test_extend_base_headers(self, execution_context) -> None:
        """Test SetHttpHeadersNode extends base headers."""
        from casare_rpa.nodes.http import SetHttpHeadersNode

        node = SetHttpHeadersNode(node_id="test_headers_extend")
        node.set_input_value("base_headers", {"Content-Type": "application/json"})
        node.set_input_value("header_name", "Authorization")
        node.set_input_value("header_value", "Bearer token")

        result = await node.execute(execution_context)

        headers = node.get_output_value("headers")
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer token"


class TestHttpAuthNode:
    """Tests for HttpAuthNode authentication."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_bearer_auth(self, execution_context) -> None:
        """Test HttpAuthNode with Bearer token."""
        from casare_rpa.nodes.http import HttpAuthNode

        node = HttpAuthNode(node_id="test_auth_bearer", config={"auth_type": "Bearer"})
        node.set_input_value("token", "my-secret-token")

        result = await node.execute(execution_context)

        assert result["success"] is True
        headers = node.get_output_value("headers")
        assert headers["Authorization"] == "Bearer my-secret-token"

    @pytest.mark.asyncio
    async def test_basic_auth(self, execution_context) -> None:
        """Test HttpAuthNode with Basic authentication."""
        from casare_rpa.nodes.http import HttpAuthNode

        node = HttpAuthNode(node_id="test_auth_basic", config={"auth_type": "Basic"})
        node.set_input_value("username", "user")
        node.set_input_value("password", "pass")

        result = await node.execute(execution_context)

        assert result["success"] is True
        headers = node.get_output_value("headers")
        expected = base64.b64encode(b"user:pass").decode()
        assert headers["Authorization"] == f"Basic {expected}"

    @pytest.mark.asyncio
    async def test_apikey_auth(self, execution_context) -> None:
        """Test HttpAuthNode with API key."""
        from casare_rpa.nodes.http import HttpAuthNode

        node = HttpAuthNode(
            node_id="test_auth_apikey",
            config={"auth_type": "ApiKey", "api_key_name": "X-API-Key"},
        )
        node.set_input_value("token", "my-api-key-123")

        result = await node.execute(execution_context)

        assert result["success"] is True
        headers = node.get_output_value("headers")
        assert headers["X-API-Key"] == "my-api-key-123"

    @pytest.mark.asyncio
    async def test_bearer_auth_missing_token(self, execution_context) -> None:
        """Test HttpAuthNode fails without token for Bearer."""
        from casare_rpa.nodes.http import HttpAuthNode

        node = HttpAuthNode(
            node_id="test_auth_no_token", config={"auth_type": "Bearer"}
        )
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "Bearer token is required" in result["error"]

    @pytest.mark.asyncio
    async def test_basic_auth_missing_credentials(self, execution_context) -> None:
        """Test HttpAuthNode fails without credentials for Basic."""
        from casare_rpa.nodes.http import HttpAuthNode

        node = HttpAuthNode(node_id="test_auth_no_creds", config={"auth_type": "Basic"})
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "Username and password are required" in result["error"]

    @pytest.mark.asyncio
    async def test_auth_extends_base_headers(self, execution_context) -> None:
        """Test HttpAuthNode preserves base headers."""
        from casare_rpa.nodes.http import HttpAuthNode

        node = HttpAuthNode(node_id="test_auth_extend", config={"auth_type": "Bearer"})
        node.set_input_value("token", "token123")
        node.set_input_value("base_headers", {"Content-Type": "application/json"})

        result = await node.execute(execution_context)

        headers = node.get_output_value("headers")
        assert headers["Content-Type"] == "application/json"
        assert "Authorization" in headers


class TestParseJsonResponseNode:
    """Tests for ParseJsonResponseNode."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        return context

    @pytest.mark.asyncio
    async def test_parse_json_simple_path(self, execution_context) -> None:
        """Test ParseJsonResponseNode with simple path."""
        from casare_rpa.nodes.http import ParseJsonResponseNode

        node = ParseJsonResponseNode(node_id="test_parse_simple")
        node.set_input_value("json_data", {"user": {"name": "John"}})
        node.set_input_value("path", "user.name")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("value") == "John"
        assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_parse_json_array_index(self, execution_context) -> None:
        """Test ParseJsonResponseNode with array index."""
        from casare_rpa.nodes.http import ParseJsonResponseNode

        node = ParseJsonResponseNode(node_id="test_parse_array")
        node.set_input_value("json_data", {"items": [{"id": 1}, {"id": 2}]})
        node.set_input_value("path", "items[1].id")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("value") == 2

    @pytest.mark.asyncio
    async def test_parse_json_string_input(self, execution_context) -> None:
        """Test ParseJsonResponseNode parses JSON string."""
        from casare_rpa.nodes.http import ParseJsonResponseNode

        node = ParseJsonResponseNode(node_id="test_parse_string")
        node.set_input_value("json_data", '{"key": "value"}')
        node.set_input_value("path", "key")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("value") == "value"

    @pytest.mark.asyncio
    async def test_parse_json_path_not_found(self, execution_context) -> None:
        """Test ParseJsonResponseNode handles missing path."""
        from casare_rpa.nodes.http import ParseJsonResponseNode

        node = ParseJsonResponseNode(node_id="test_parse_missing")
        node.set_input_value("json_data", {"a": "b"})
        node.set_input_value("path", "nonexistent.path")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert (
            "not found" in result["error"].lower() or "key" in result["error"].lower()
        )

    @pytest.mark.asyncio
    async def test_parse_json_with_default(self, execution_context) -> None:
        """Test ParseJsonResponseNode uses default for missing path."""
        from casare_rpa.nodes.http import ParseJsonResponseNode

        node = ParseJsonResponseNode(node_id="test_parse_default")
        node.set_input_value("json_data", {"a": "b"})
        node.set_input_value("path", "missing")
        node.set_input_value("default", "default_value")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("value") == "default_value"

    @pytest.mark.asyncio
    async def test_parse_json_invalid_json(self, execution_context) -> None:
        """Test ParseJsonResponseNode handles invalid JSON."""
        from casare_rpa.nodes.http import ParseJsonResponseNode

        node = ParseJsonResponseNode(node_id="test_parse_invalid")
        node.set_input_value("json_data", "not valid json {")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "Invalid JSON" in result["error"]

    @pytest.mark.asyncio
    async def test_parse_json_empty_path(self, execution_context) -> None:
        """Test ParseJsonResponseNode returns whole object for empty path."""
        from casare_rpa.nodes.http import ParseJsonResponseNode

        node = ParseJsonResponseNode(node_id="test_parse_empty_path")
        node.set_input_value("json_data", {"whole": "object"})
        node.set_input_value("path", "")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("value") == {"whole": "object"}


class TestBuildUrlNode:
    """Tests for BuildUrlNode URL construction."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_build_url_base_only(self, execution_context) -> None:
        """Test BuildUrlNode with base URL only."""
        from casare_rpa.nodes.http import BuildUrlNode

        node = BuildUrlNode(node_id="test_build_base")
        node.set_input_value("base_url", "https://api.example.com")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("url") == "https://api.example.com"

    @pytest.mark.asyncio
    async def test_build_url_with_path(self, execution_context) -> None:
        """Test BuildUrlNode with path appended."""
        from casare_rpa.nodes.http import BuildUrlNode

        node = BuildUrlNode(node_id="test_build_path")
        node.set_input_value("base_url", "https://api.example.com")
        node.set_input_value("path", "users/123")

        result = await node.execute(execution_context)

        url = node.get_output_value("url")
        assert "users/123" in url

    @pytest.mark.asyncio
    async def test_build_url_with_params(self, execution_context) -> None:
        """Test BuildUrlNode with query parameters."""
        from casare_rpa.nodes.http import BuildUrlNode

        node = BuildUrlNode(node_id="test_build_params")
        node.set_input_value("base_url", "https://api.example.com/search")
        node.set_input_value("params", {"q": "test", "page": "1"})

        result = await node.execute(execution_context)

        url = node.get_output_value("url")
        assert "q=test" in url
        assert "page=1" in url

    @pytest.mark.asyncio
    async def test_build_url_missing_base(self, execution_context) -> None:
        """Test BuildUrlNode fails without base URL."""
        from casare_rpa.nodes.http import BuildUrlNode

        node = BuildUrlNode(node_id="test_build_no_base")
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "Base URL is required" in result["error"]


class TestHttpDownloadFileNode:
    """Tests for HttpDownloadFileNode file downloading."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_download_missing_url(self, execution_context) -> None:
        """Test HttpDownloadFileNode fails without URL."""
        from casare_rpa.nodes.http import HttpDownloadFileNode

        node = HttpDownloadFileNode(node_id="test_download_no_url")
        node.set_input_value("save_path", "/tmp/file.txt")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "URL is required" in result["error"]

    @pytest.mark.asyncio
    async def test_download_missing_path(self, execution_context) -> None:
        """Test HttpDownloadFileNode fails without save path."""
        from casare_rpa.nodes.http import HttpDownloadFileNode

        node = HttpDownloadFileNode(
            node_id="test_download_no_path",
            config={"url": "https://example.com/file.txt"},
        )

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "Save path is required" in result["error"]


class TestHttpUploadFileNode:
    """Tests for HttpUploadFileNode file uploading."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_upload_missing_url(self, execution_context) -> None:
        """Test HttpUploadFileNode fails without URL."""
        from casare_rpa.nodes.http import HttpUploadFileNode

        node = HttpUploadFileNode(node_id="test_upload_no_url")
        node.set_input_value("file_path", "/tmp/test.txt")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "URL is required" in result["error"]

    @pytest.mark.asyncio
    async def test_upload_missing_file(self, execution_context) -> None:
        """Test HttpUploadFileNode fails without file path."""
        from casare_rpa.nodes.http import HttpUploadFileNode

        node = HttpUploadFileNode(
            node_id="test_upload_no_file", config={"url": "https://example.com/upload"}
        )

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "File path is required" in result["error"]

    @pytest.mark.asyncio
    async def test_upload_file_not_found(self, execution_context) -> None:
        """Test HttpUploadFileNode fails when file doesn't exist."""
        from casare_rpa.nodes.http import HttpUploadFileNode

        node = HttpUploadFileNode(
            node_id="test_upload_not_found",
            config={"url": "https://example.com/upload"},
        )
        node.set_input_value("file_path", "/nonexistent/path/file.txt")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert (
            "File not found" in result["error"]
            or "not found" in result["error"].lower()
        )


class TestHttpNodesRetry:
    """Tests for HTTP nodes retry functionality."""

    @pytest.fixture
    def execution_context(self) -> None:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_http_get_retry_on_failure(self, execution_context) -> None:
        """Test HttpGetNode retries on failure."""
        from casare_rpa.nodes.http import HttpGetNode
        import aiohttp

        node = HttpGetNode(
            node_id="test_get_retry",
            config={
                "url": "https://api.example.com/data",
                "retry_count": 2,
                "retry_delay": 0.01,
            },
        )

        call_count = [0]  # Use list to allow mutation in nested class

        class MockContextManager:
            def __init__(self, response):
                self.response = response

            async def __aenter__(self):
                return self.response

            async def __aexit__(self, *args):
                pass

        class MockSession:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            def request(self, *args, **kwargs):
                call_count[0] += 1
                if call_count[0] < 3:
                    raise aiohttp.ClientError("Simulated failure")
                response = create_mock_response(200, '{"data": "success"}')
                return MockContextManager(response)

        with patch("aiohttp.ClientSession", MockSession):
            result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["attempts"] == 3


class TestHttpNodesIntegration:
    """Integration tests for HTTP nodes with ExecutionResult pattern."""

    def test_all_http_nodes_have_execute(self) -> None:
        """Test all HTTP nodes implement execute method."""
        from casare_rpa.nodes.http import (
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

        node_classes = [
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
        ]

        for cls in node_classes:
            node = cls(node_id=f"test_{cls.__name__}")
            assert hasattr(node, "execute")
            assert callable(node.execute)

    def test_all_http_nodes_have_ports(self) -> None:
        """Test all HTTP nodes define ports correctly."""
        from casare_rpa.nodes.http import (
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

        node_classes = [
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
        ]

        for cls in node_classes:
            node = cls(node_id=f"test_{cls.__name__}")
            assert "exec_in" in node.input_ports
            assert "exec_out" in node.output_ports

    def test_execution_result_pattern(self) -> None:
        """Test ExecutionResult pattern compliance."""
        from casare_rpa.nodes.http import BuildUrlNode

        node = BuildUrlNode(node_id="test_result")
        node.set_input_value("base_url", "https://example.com")

        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x

        result = asyncio.get_event_loop().run_until_complete(node.execute(context))

        assert "success" in result
        assert isinstance(result["success"], bool)
        assert "next_nodes" in result

    def test_http_methods_coverage(self) -> None:
        """Test all HTTP methods have corresponding nodes."""
        from casare_rpa.nodes.http import (
            HttpGetNode,
            HttpPostNode,
            HttpPutNode,
            HttpPatchNode,
            HttpDeleteNode,
        )

        methods_covered = {
            "GET": HttpGetNode,
            "POST": HttpPostNode,
            "PUT": HttpPutNode,
            "PATCH": HttpPatchNode,
            "DELETE": HttpDeleteNode,
        }

        for method, cls in methods_covered.items():
            node = cls(node_id=f"test_{method}")
            assert node is not None
