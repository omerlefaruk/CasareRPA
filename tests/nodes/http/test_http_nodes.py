"""
Tests for Basic HTTP nodes.
"""

from unittest.mock import MagicMock, AsyncMock

import pytest

from casare_rpa.nodes.http.http_basic import HttpRequestNode
from casare_rpa.domain.value_objects.types import NodeStatus


@pytest.mark.asyncio
async def test_http_request_get_success(context_with_client, mock_http_client, mock_http_response):
    """Test successful GET request."""
    # Setup node
    node = HttpRequestNode(
        node_id="test_node",
        config={
            "url": "https://api.example.com",
            "method": "GET",
            "headers": {"Accept": "application/json"},
            "params": {"id": "123"},
        },
    )

    # Execute
    result = await node.execute(context_with_client)

    # Assertions
    assert result["success"] is True
    assert node.status == NodeStatus.SUCCESS
    # Node outputs are set via _set_success_outputs after response.text() is awaited
    assert node.get_output_value("status_code") == 200
    assert node.get_output_value("success") is True
    # response_json is parsed from response.text() if valid JSON
    response_json = node.get_output_value("response_json")
    assert response_json is not None or node.get_output_value("response_body") != ""

    # Verify client call
    mock_http_client.request.assert_called_once()


@pytest.mark.asyncio
async def test_http_request_post_success(context_with_client, mock_http_client, mock_http_response):
    """Test successful POST request."""
    # Setup node
    node = HttpRequestNode(
        node_id="test_node",
        config={
            "url": "https://api.example.com",
            "method": "POST",
            "body": '{"name": "test"}',
            "content_type": "application/json",
        },
    )

    # Execute
    result = await node.execute(context_with_client)

    # Assertions
    assert result["success"] is True
    assert node.status == NodeStatus.SUCCESS

    # Verify client was called
    mock_http_client.request.assert_called_once()
    call_kwargs = mock_http_client.request.call_args.kwargs
    # Body should be sent as json parameter when content-type is application/json
    assert "json" in call_kwargs or "data" in call_kwargs


@pytest.mark.asyncio
async def test_http_request_error(context_with_client, mock_http_client):
    """Test HTTP request failure."""
    # Setup mock to raise exception
    mock_http_client.request.side_effect = Exception("Connection Failed")

    node = HttpRequestNode(node_id="test_node", config={"url": "https://bad-api.example.com"})

    # Execute
    result = await node.execute(context_with_client)

    # Assertions
    assert result["success"] is False
    assert "Connection Failed" in result["error"]
    assert node.get_output_value("success") is False
