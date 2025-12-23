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
# Structured data operations
# XML operations
# PDF operations (not yet consolidated)
# FTP operations (not yet consolidated)
# Directory and path operations
from casare_rpa.presentation.canvas.visual_nodes.file_operations.nodes import (
    VisualCreateDirectoryNode,
    VisualExtractPDFPagesNode,
    VisualFileExistsNode,
    VisualFTPConnectNode,
    VisualFTPDeleteNode,
    VisualFTPDisconnectNode,
    VisualFTPDownloadNode,
    VisualFTPGetSizeNode,
    VisualFTPListNode,
    VisualFTPMakeDirNode,
    VisualFTPRemoveDirNode,
    VisualFTPRenameNode,
    VisualFTPUploadNode,
    VisualGetPDFInfoNode,
    VisualGetXMLAttributeNode,
    VisualGetXMLElementNode,
    VisualImageConvertNode,
    VisualJsonToXMLNode,
    VisualListDirectoryNode,
    VisualMergePDFsNode,
    VisualParseXMLNode,
    VisualPDFToImagesNode,
    VisualReadCSVNode,
    VisualReadJSONFileNode,
    VisualReadPDFTextNode,
    VisualReadXMLFileNode,
    VisualSplitPDFNode,
    VisualUnzipFilesNode,
    VisualWriteCSVNode,
    VisualWriteJSONFileNode,
    VisualWriteXMLFileNode,
    VisualXMLToJsonNode,
    VisualXPathQueryNode,
    VisualZipFilesNode,
)
from casare_rpa.presentation.canvas.visual_nodes.file_operations.super_nodes import (
    VisualFileSystemSuperNode,
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
    # Directory and path operations
    "VisualListDirectoryNode",
    "VisualFileExistsNode",
    "VisualCreateDirectoryNode",
]
