"""
Basic HTTP request nodes for CasareRPA.

This module provides nodes for making standard HTTP requests:
- HttpRequestNode: Generic HTTP request (all methods)
- HttpGetNode: GET request with query parameters
- HttpPostNode: POST request with body
- HttpPutNode: PUT request for updating resources
- HttpPatchNode: PATCH request for partial updates
- HttpDeleteNode: DELETE request for deleting resources

All nodes inherit from HttpBaseNode for common functionality.
"""

from __future__ import annotations

from typing import Any

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType, PortType

from .http_base import HttpBaseNode


# Common property definitions to reduce duplication
URL_PROPERTY = PropertyDef(
    "url",
    PropertyType.STRING,
    required=True,
    label="URL",
    tooltip="Target URL for the HTTP request",
    placeholder="https://api.example.com/endpoint",
)

HEADERS_PROPERTY = PropertyDef(
    "headers",
    PropertyType.JSON,
    default={},
    label="Headers",
    tooltip="Request headers as JSON object",
)

TIMEOUT_PROPERTY = PropertyDef(
    "timeout",
    PropertyType.FLOAT,
    default=30.0,
    min_value=0.1,
    label="Timeout (seconds)",
    tooltip="Request timeout in seconds",
)

VERIFY_SSL_PROPERTY = PropertyDef(
    "verify_ssl",
    PropertyType.BOOLEAN,
    default=True,
    label="Verify SSL",
    tooltip="Verify SSL certificates",
)

RETRY_COUNT_PROPERTY = PropertyDef(
    "retry_count",
    PropertyType.INTEGER,
    default=0,
    min_value=0,
    label="Retry Count",
    tooltip="Number of retry attempts on failure",
)

RETRY_DELAY_PROPERTY = PropertyDef(
    "retry_delay",
    PropertyType.FLOAT,
    default=1.0,
    min_value=0.0,
    label="Retry Delay (seconds)",
    tooltip="Delay between retry attempts",
)

BODY_PROPERTY = PropertyDef(
    "body",
    PropertyType.STRING,
    default="",
    label="Request Body",
    tooltip="Request body (JSON, form data, or string)",
)

CONTENT_TYPE_PROPERTY = PropertyDef(
    "content_type",
    PropertyType.STRING,
    default="application/json",
    label="Content-Type",
    tooltip="Content-Type header for request body",
)

PARAMS_PROPERTY = PropertyDef(
    "params",
    PropertyType.JSON,
    default={},
    label="Query Parameters",
    tooltip="URL query parameters as JSON object",
)


@executable_node
@node_schema(
    URL_PROPERTY,
    PropertyDef(
        "method",
        PropertyType.CHOICE,
        default="GET",
        choices=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
        label="HTTP Method",
        tooltip="HTTP request method",
    ),
    HEADERS_PROPERTY,
    BODY_PROPERTY,
    PARAMS_PROPERTY,
    TIMEOUT_PROPERTY,
    VERIFY_SSL_PROPERTY,
    PropertyDef(
        "follow_redirects",
        PropertyType.BOOLEAN,
        default=True,
        label="Follow Redirects",
        tooltip="Automatically follow HTTP redirects",
    ),
    PropertyDef(
        "max_redirects",
        PropertyType.INTEGER,
        default=10,
        min_value=0,
        label="Max Redirects",
        tooltip="Maximum number of redirects to follow",
    ),
    CONTENT_TYPE_PROPERTY,
    PropertyDef(
        "proxy",
        PropertyType.STRING,
        default="",
        label="Proxy URL",
        tooltip="HTTP proxy URL (optional)",
    ),
    RETRY_COUNT_PROPERTY,
    RETRY_DELAY_PROPERTY,
    PropertyDef(
        "response_encoding",
        PropertyType.STRING,
        default="",
        label="Response Encoding",
        tooltip="Force specific response encoding (optional)",
    ),
)
class HttpRequestNode(HttpBaseNode):
    """
    Generic HTTP request node supporting all HTTP methods.

    Config (via @node_schema):
        url: Target URL (required)
        method: HTTP method (default: GET)
        headers: Request headers as dict
        body: Request body (for POST, PUT, PATCH)
        params: Query parameters as dict
        timeout: Request timeout in seconds
        verify_ssl: Verify SSL certificates
        follow_redirects: Follow HTTP redirects
        max_redirects: Maximum redirects to follow
        content_type: Content-Type header
        proxy: Proxy URL (optional)
        retry_count: Retry attempts on failure
        retry_delay: Delay between retries
        response_encoding: Force response encoding

    Outputs:
        response_body, response_json, status_code, response_headers, success, error
    """

    def __init__(self, node_id: str, name: str = "HTTP Request", **kwargs: Any) -> None:
        super().__init__(node_id, name, **kwargs)
        self.node_type = "HttpRequestNode"

    def _get_http_method(self) -> str:
        return self.get_parameter("method", "GET").upper()

    def _has_request_body(self) -> bool:
        return self._get_http_method() in ("POST", "PUT", "PATCH")

    def _define_ports(self) -> None:
        self.add_input_port("url", PortType.INPUT, DataType.STRING)
        self.add_input_port("method", PortType.INPUT, DataType.STRING)
        self.add_input_port("headers", PortType.INPUT, DataType.DICT)
        self.add_input_port("body", PortType.INPUT, DataType.ANY)
        self.add_input_port("params", PortType.INPUT, DataType.DICT)
        self.add_input_port("timeout", PortType.INPUT, DataType.FLOAT)
        self._define_common_output_ports()


@executable_node
@node_schema(
    URL_PROPERTY,
    PARAMS_PROPERTY,
    HEADERS_PROPERTY,
    TIMEOUT_PROPERTY,
    VERIFY_SSL_PROPERTY,
    RETRY_COUNT_PROPERTY,
    RETRY_DELAY_PROPERTY,
)
class HttpGetNode(HttpBaseNode):
    """
    HTTP GET request node with query parameter support.

    Config (via @node_schema):
        url: Target URL (required)
        params: Query parameters as dict
        headers: Request headers as dict
        timeout: Request timeout in seconds
        verify_ssl: Verify SSL certificates
        retry_count: Retry attempts on failure
        retry_delay: Delay between retries

    Outputs:
        response_body, response_json, status_code, success, error
    """

    def __init__(self, node_id: str, name: str = "HTTP GET", **kwargs: Any) -> None:
        super().__init__(node_id, name, **kwargs)
        self.node_type = "HttpGetNode"

    def _get_http_method(self) -> str:
        return "GET"

    def _define_ports(self) -> None:
        self.add_input_port("url", PortType.INPUT, DataType.STRING)
        self.add_input_port("params", PortType.INPUT, DataType.DICT)
        self.add_input_port("headers", PortType.INPUT, DataType.DICT)
        self.add_input_port("timeout", PortType.INPUT, DataType.FLOAT)
        self._define_common_output_ports()


@executable_node
@node_schema(
    URL_PROPERTY,
    BODY_PROPERTY,
    HEADERS_PROPERTY,
    CONTENT_TYPE_PROPERTY,
    TIMEOUT_PROPERTY,
    VERIFY_SSL_PROPERTY,
    RETRY_COUNT_PROPERTY,
    RETRY_DELAY_PROPERTY,
)
class HttpPostNode(HttpBaseNode):
    """
    HTTP POST request node with body support.

    Config (via @node_schema):
        url: Target URL (required)
        body: Request body
        headers: Request headers as dict
        content_type: Content-Type header
        timeout: Request timeout in seconds
        verify_ssl: Verify SSL certificates
        retry_count: Retry attempts on failure
        retry_delay: Delay between retries

    Outputs:
        response_body, response_json, status_code, success, error
    """

    def __init__(self, node_id: str, name: str = "HTTP POST", **kwargs: Any) -> None:
        super().__init__(node_id, name, **kwargs)
        self.node_type = "HttpPostNode"

    def _get_http_method(self) -> str:
        return "POST"

    def _define_ports(self) -> None:
        self._define_common_input_ports(include_body=True)
        self._define_common_output_ports()


@executable_node
@node_schema(
    URL_PROPERTY,
    BODY_PROPERTY,
    HEADERS_PROPERTY,
    CONTENT_TYPE_PROPERTY,
    TIMEOUT_PROPERTY,
    VERIFY_SSL_PROPERTY,
    RETRY_COUNT_PROPERTY,
    RETRY_DELAY_PROPERTY,
)
class HttpPutNode(HttpBaseNode):
    """
    HTTP PUT request node for updating resources.

    Config (via @node_schema):
        url: Target URL (required)
        body: Request body
        headers: Request headers as dict
        content_type: Content-Type header
        timeout: Request timeout in seconds
        verify_ssl: Verify SSL certificates
        retry_count: Retry attempts on failure
        retry_delay: Delay between retries

    Outputs:
        response_body, response_json, status_code, success, error
    """

    def __init__(self, node_id: str, name: str = "HTTP PUT", **kwargs: Any) -> None:
        super().__init__(node_id, name, **kwargs)
        self.node_type = "HttpPutNode"

    def _get_http_method(self) -> str:
        return "PUT"

    def _define_ports(self) -> None:
        self._define_common_input_ports(include_body=True)
        self._define_common_output_ports()


@executable_node
@node_schema(
    URL_PROPERTY,
    BODY_PROPERTY,
    HEADERS_PROPERTY,
    CONTENT_TYPE_PROPERTY,
    TIMEOUT_PROPERTY,
    VERIFY_SSL_PROPERTY,
    RETRY_COUNT_PROPERTY,
    RETRY_DELAY_PROPERTY,
)
class HttpPatchNode(HttpBaseNode):
    """
    HTTP PATCH request node for partial updates.

    Config (via @node_schema):
        url: Target URL (required)
        body: Request body with partial updates
        headers: Request headers as dict
        content_type: Content-Type header
        timeout: Request timeout in seconds
        verify_ssl: Verify SSL certificates
        retry_count: Retry attempts on failure
        retry_delay: Delay between retries

    Outputs:
        response_body, response_json, status_code, success, error
    """

    def __init__(self, node_id: str, name: str = "HTTP PATCH", **kwargs: Any) -> None:
        super().__init__(node_id, name, **kwargs)
        self.node_type = "HttpPatchNode"

    def _get_http_method(self) -> str:
        return "PATCH"

    def _define_ports(self) -> None:
        self._define_common_input_ports(include_body=True)
        self._define_common_output_ports()


@executable_node
@node_schema(
    URL_PROPERTY,
    HEADERS_PROPERTY,
    TIMEOUT_PROPERTY,
    VERIFY_SSL_PROPERTY,
    RETRY_COUNT_PROPERTY,
    RETRY_DELAY_PROPERTY,
)
class HttpDeleteNode(HttpBaseNode):
    """
    HTTP DELETE request node for deleting resources.

    Config (via @node_schema):
        url: Target URL (required)
        headers: Request headers as dict
        timeout: Request timeout in seconds
        verify_ssl: Verify SSL certificates
        retry_count: Retry attempts on failure
        retry_delay: Delay between retries

    Outputs:
        response_body, status_code, success, error
    """

    def __init__(self, node_id: str, name: str = "HTTP DELETE", **kwargs: Any) -> None:
        super().__init__(node_id, name, **kwargs)
        self.node_type = "HttpDeleteNode"

    def _get_http_method(self) -> str:
        return "DELETE"

    def _define_ports(self) -> None:
        self.add_input_port("url", PortType.INPUT, DataType.STRING)
        self.add_input_port("headers", PortType.INPUT, DataType.DICT)
        self.add_input_port("timeout", PortType.INPUT, DataType.FLOAT)
        self._define_common_output_ports()


__all__ = [
    "HttpRequestNode",
    "HttpGetNode",
    "HttpPostNode",
    "HttpPutNode",
    "HttpPatchNode",
    "HttpDeleteNode",
]
