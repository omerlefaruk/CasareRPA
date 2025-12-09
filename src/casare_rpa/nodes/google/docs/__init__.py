"""
Google Docs API Nodes

Provides nodes for reading, creating, and modifying Google Documents
via the Google Docs API v1.
"""

from casare_rpa.nodes.google.google_base import DocsBaseNode
from casare_rpa.nodes.google.docs.docs_read import (
    DocsExportNode,
    DocsGetDocumentNode,
    DocsGetTextNode,
)
from casare_rpa.nodes.google.docs.docs_write import (
    DocsAppendTextNode,
    DocsApplyStyleNode,
    DocsCreateDocumentNode,
    DocsInsertImageNode,
    DocsInsertTableNode,
    DocsInsertTextNode,
    DocsReplaceTextNode,
)

__all__ = [
    "DocsBaseNode",
    # Read operations
    "DocsGetDocumentNode",
    "DocsGetTextNode",
    "DocsExportNode",
    # Write operations
    "DocsCreateDocumentNode",
    "DocsInsertTextNode",
    "DocsAppendTextNode",
    "DocsReplaceTextNode",
    "DocsInsertTableNode",
    "DocsInsertImageNode",
    "DocsApplyStyleNode",
]
