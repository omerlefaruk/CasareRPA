"""
HTTP/REST API Nodes for CasareRPA.

This package provides nodes for making HTTP requests and interacting with REST APIs.
Supports all HTTP methods via dropdown, authentication, headers, and response parsing.

Modules:
    - http_base: Base class for all HTTP nodes (HttpBaseNode)
    - http_basic: Unified HttpRequestNode (supports GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS)
    - http_advanced: Advanced operations (headers, JSON parsing, file transfer, URL building)
    - http_auth: Authentication nodes (Bearer, Basic, API Key)
"""

from casare_rpa.nodes.http.http_base import HttpBaseNode
from casare_rpa.nodes.http.http_basic import HttpRequestNode
from casare_rpa.nodes.http.http_advanced import (
    SetHttpHeadersNode,
    ParseJsonResponseNode,
    HttpDownloadFileNode,
    HttpUploadFileNode,
    BuildUrlNode,
)
from casare_rpa.nodes.http.http_auth import HttpAuthNode

__all__ = [
    # Base class
    "HttpBaseNode",
    # HTTP request (all methods via dropdown)
    "HttpRequestNode",
    # Advanced operations
    "SetHttpHeadersNode",
    "ParseJsonResponseNode",
    "HttpDownloadFileNode",
    "HttpUploadFileNode",
    "BuildUrlNode",
    # Authentication
    "HttpAuthNode",
]
