"""
Shared fixtures for node tests across all categories.

Provides:
- HTTP/REST mock helpers (create_mock_response, create_mock_session)
- Common mock utilities for node testing

Category-specific fixtures should be in subdirectories (e.g., desktop/conftest.py).
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock
from typing import Optional, Dict, Any


def create_mock_response(
    status: int = 200,
    body: str = '{"status": "ok"}',
    headers: Optional[Dict[str, str]] = None,
) -> AsyncMock:
    """
    Create a mock aiohttp response object.

    Useful for testing HTTP node fixtures without making real network requests.

    Args:
        status: HTTP status code (default: 200).
        body: Response body as string (default: JSON '{"status": "ok"}').
        headers: Response headers dict (default: {"Content-Type": "application/json"}).

    Returns:
        AsyncMock object configured as aiohttp.ClientResponse.

    Usage:
        mock_response = create_mock_response(200, '{"data": "value"}')
        mock_session = create_mock_session(mock_response)
        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await http_node.execute(context)
    """
    mock_response = AsyncMock()
    mock_response.status = status
    mock_response.text = AsyncMock(return_value=body)
    mock_response.headers = headers or {"Content-Type": "application/json"}
    mock_response.json = AsyncMock(return_value=body if isinstance(body, dict) else {})
    return mock_response


def create_mock_session(response: AsyncMock) -> MagicMock:
    """
    Create a mock aiohttp ClientSession configured with a mock response.

    Configures async context managers for session and HTTP operations.
    Supports all HTTP methods: get, post, put, patch, delete, request.

    Args:
        response: Mock response object (from create_mock_response or similar).

    Returns:
        MagicMock object configured as aiohttp.ClientSession.

    Usage:
        mock_response = create_mock_response(200)
        mock_session = create_mock_session(mock_response)
        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await node.execute(context)
    """
    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    # Create mock context manager for HTTP operations
    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=response)
    mock_context.__aexit__ = AsyncMock(return_value=None)

    # Configure HTTP methods
    mock_session.get = MagicMock(return_value=mock_context)
    mock_session.post = MagicMock(return_value=mock_context)
    mock_session.put = MagicMock(return_value=mock_context)
    mock_session.patch = MagicMock(return_value=mock_context)
    mock_session.delete = MagicMock(return_value=mock_context)
    mock_session.request = MagicMock(return_value=mock_context)
    mock_session.head = MagicMock(return_value=mock_context)
    mock_session.options = MagicMock(return_value=mock_context)

    return mock_session


@pytest.fixture
def mock_aiohttp_response() -> AsyncMock:
    """
    Create a default mock aiohttp response fixture.

    Returns:
        Mock response with status=200 and JSON body.

    Usage:
        def test_http_get(mock_aiohttp_response):
            # Response already created with sensible defaults
            mock_aiohttp_response.status = 404  # Override as needed
    """
    return create_mock_response(200, '{"status": "ok"}')


@pytest.fixture
def mock_aiohttp_session(mock_aiohttp_response) -> MagicMock:
    """
    Create a mock aiohttp ClientSession fixture.

    Pre-configured with a default mock response.

    Args:
        mock_aiohttp_response: Default response fixture.

    Returns:
        Mock session ready for patching aiohttp.ClientSession.

    Usage:
        def test_http_request(mock_aiohttp_session):
            with patch("aiohttp.ClientSession", return_value=mock_aiohttp_session):
                result = await node.execute(context)
    """
    return create_mock_session(mock_aiohttp_response)
