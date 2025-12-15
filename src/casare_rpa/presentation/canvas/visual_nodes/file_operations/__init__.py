"""
Visual Nodes - File Operations

Super Nodes (consolidated operations):
- VisualFileSystemSuperNode: 12 file system operations in one node

Remaining atomic nodes (not yet consolidated):
- Structured data operations (CSV, JSON, ZIP)
- XML operations (8 nodes)
- PDF operations (6 nodes)
- FTP operations (10 nodes)

NOTE: Structured data (CSV/JSON/ZIP) are available as atomic nodes for clarity.
"""

# Super Nodes (consolidated operations)
from casare_rpa.presentation.canvas.visual_nodes.file_operations.super_nodes import (
    VisualFileSystemSuperNode,
)

# Structured data operations
from casare_rpa.presentation.canvas.visual_nodes.file_operations.nodes import (
    VisualReadCSVNode,
    VisualWriteCSVNode,
    VisualReadJSONFileNode,
    VisualWriteJSONFileNode,
    VisualZipFilesNode,
    VisualUnzipFilesNode,
)

# XML operations
from casare_rpa.presentation.canvas.visual_nodes.file_operations.nodes import (
    VisualImageConvertNode,
    VisualParseXMLNode,
    VisualReadXMLFileNode,
    VisualWriteXMLFileNode,
    VisualXPathQueryNode,
    VisualGetXMLElementNode,
    VisualGetXMLAttributeNode,
    VisualXMLToJsonNode,
    VisualJsonToXMLNode,
)

# PDF operations (not yet consolidated)
from casare_rpa.presentation.canvas.visual_nodes.file_operations.nodes import (
    VisualReadPDFTextNode,
    VisualGetPDFInfoNode,
    VisualMergePDFsNode,
    VisualSplitPDFNode,
    VisualExtractPDFPagesNode,
    VisualPDFToImagesNode,
)

# FTP operations (not yet consolidated)
from casare_rpa.presentation.canvas.visual_nodes.file_operations.nodes import (
    VisualFTPConnectNode,
    VisualFTPUploadNode,
    VisualFTPDownloadNode,
    VisualFTPListNode,
    VisualFTPDeleteNode,
    VisualFTPMakeDirNode,
    VisualFTPRemoveDirNode,
    VisualFTPRenameNode,
    VisualFTPDisconnectNode,
    VisualFTPGetSizeNode,
)

__all__ = [
    # Super Nodes (consolidated operations)
    "VisualFileSystemSuperNode",
    # Structured data
    "VisualReadCSVNode",
    "VisualWriteCSVNode",
    "VisualReadJSONFileNode",
    "VisualWriteJSONFileNode",
    "VisualZipFilesNode",
    "VisualUnzipFilesNode",
    # Image operations
    "VisualImageConvertNode",
    # XML operations
    "VisualParseXMLNode",
    "VisualReadXMLFileNode",
    "VisualWriteXMLFileNode",
    "VisualXPathQueryNode",
    "VisualGetXMLElementNode",
    "VisualGetXMLAttributeNode",
    "VisualXMLToJsonNode",
    "VisualJsonToXMLNode",
    # PDF operations
    "VisualReadPDFTextNode",
    "VisualGetPDFInfoNode",
    "VisualMergePDFsNode",
    "VisualSplitPDFNode",
    "VisualExtractPDFPagesNode",
    "VisualPDFToImagesNode",
    # FTP operations
    "VisualFTPConnectNode",
    "VisualFTPUploadNode",
    "VisualFTPDownloadNode",
    "VisualFTPListNode",
    "VisualFTPDeleteNode",
    "VisualFTPMakeDirNode",
    "VisualFTPRemoveDirNode",
    "VisualFTPRenameNode",
    "VisualFTPDisconnectNode",
    "VisualFTPGetSizeNode",
]
