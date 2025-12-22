"""
Fixtures for HTTP node tests.
"""

from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from casare_rpa.domain.value_objects.types import ExecutionMode
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.http.http_base import HTTP_CLIENT_RESOURCE_KEY
from casare_rpa.infrastructure.http.unified_http_client import UnifiedHttpClient


@pytest.fixture
def execution_context() -> ExecutionContext:
    """Create a test execution context."""
    return ExecutionContext(
        workflow_name="TestWorkflow",
        mode=ExecutionMode.NORMAL,
        initial_variables={},
    )


@pytest.fixture
def mock_http_response() -> MagicMock:
    """Create a mock aiohttp-like response."""
    response = MagicMock()
    response.status = 200
    response.headers = {"Content-Type": "application/json"}
    response.json = AsyncMock(return_value={"success": True, "data": "test"})
    response.text = AsyncMock(return_value='{"success": True, "data": "test"}')
    response.read = AsyncMock(return_value=b'{"success": True, "data": "test"}')
    response.release = AsyncMock()
    response.__aenter__ = AsyncMock(return_value=response)
    response.__aexit__ = AsyncMock(return_value=None)
    return response


@pytest.fixture
async def mock_http_client(mock_http_response) -> MagicMock:
    """Create a mock UnifiedHttpClient and inject it into context."""
    client = MagicMock(spec=UnifiedHttpClient)

    # Mock request method to return our mock response
    client.request = AsyncMock(return_value=mock_http_response)
    client.start = AsyncMock()
    client.close = AsyncMock()

    # Shortcut methods
    client.get = AsyncMock(return_value=mock_http_response)
    client.post = AsyncMock(return_value=mock_http_response)
    client.put = AsyncMock(return_value=mock_http_response)
    client.patch = AsyncMock(return_value=mock_http_response)
    client.delete = AsyncMock(return_value=mock_http_response)
    client.head = AsyncMock(return_value=mock_http_response)
    client.options = AsyncMock(return_value=mock_http_response)

    return client


@pytest.fixture
async def context_with_client(execution_context, mock_http_client) -> ExecutionContext:
    """Provide an ExecutionContext with a pre-injected mock HTTP client."""
    execution_context.resources[HTTP_CLIENT_RESOURCE_KEY] = mock_http_client
    return execution_context
