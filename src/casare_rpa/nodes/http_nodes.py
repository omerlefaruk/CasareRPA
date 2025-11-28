"""
HTTP/REST API Nodes for CasareRPA.

DEPRECATED: This module is deprecated and will be removed in v3.0.
Import from casare_rpa.nodes.http instead:

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
"""

from __future__ import annotations

import warnings

warnings.warn(
    "casare_rpa.nodes.http_nodes is deprecated. "
    "Import from casare_rpa.nodes.http instead. "
    "This module will be removed in v3.0.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export all nodes from the http package for backwards compatibility
from .http import (
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

__all__ = [
    "HttpRequestNode",
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
