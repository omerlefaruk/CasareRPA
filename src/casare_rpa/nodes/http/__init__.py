"""
HTTP/REST API Nodes for CasareRPA.

This package provides nodes for making HTTP requests and interacting with REST APIs.
Supports all HTTP methods, authentication, headers, and response parsing.

Modules:
    - http_basic: Basic HTTP method nodes (GET, POST, PUT, PATCH, DELETE)
    - http_advanced: Advanced operations (headers, JSON parsing, file transfer, URL building)
    - http_auth: Authentication nodes (Bearer, Basic, API Key)

Nodes:
    - HttpRequestNode: Generic HTTP request (all methods)
    - HttpGetNode: GET request with query parameters
    - HttpPostNode: POST request with body
    - HttpPutNode: PUT request with body
    - HttpPatchNode: PATCH request with body
    - HttpDeleteNode: DELETE request
    - SetHttpHeadersNode: Configure headers for requests
    - HttpAuthNode: Configure authentication (Bearer, Basic, API Key)
    - ParseJsonResponseNode: Parse JSON response and extract data
    - HttpDownloadFileNode: Download file from URL
    - HttpUploadFileNode: Upload file via HTTP
    - BuildUrlNode: Build URL with query parameters
"""

from .http_basic import (
    HttpRequestNode,
    HttpGetNode,
    HttpPostNode,
    HttpPutNode,
    HttpPatchNode,
    HttpDeleteNode,
)
from .http_advanced import (
    SetHttpHeadersNode,
    ParseJsonResponseNode,
    HttpDownloadFileNode,
    HttpUploadFileNode,
    BuildUrlNode,
)
from .http_auth import (
    HttpAuthNode,
)

__all__ = [
    # Basic HTTP methods
    "HttpRequestNode",
    "HttpGetNode",
    "HttpPostNode",
    "HttpPutNode",
    "HttpPatchNode",
    "HttpDeleteNode",
    # Advanced operations
    "SetHttpHeadersNode",
    "ParseJsonResponseNode",
    "HttpDownloadFileNode",
    "HttpUploadFileNode",
    "BuildUrlNode",
    # Authentication
    "HttpAuthNode",
]
