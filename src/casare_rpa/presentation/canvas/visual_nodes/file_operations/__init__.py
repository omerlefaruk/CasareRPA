"""
Visual Nodes - File Operations

Super Nodes (consolidated operations):
- VisualFileSystemSuperNode: 12 file system operations in one node
- VisualStructuredDataSuperNode: 7 structured data operations in one node

Remaining atomic nodes (not yet consolidated):
- XML operations (8 nodes)
- PDF operations (6 nodes)
- FTP operations (10 nodes)

NOTE: Legacy atomic nodes for basic file ops, CSV, JSON, ZIP, and Image
have been removed. Old workflows will be automatically migrated to Super
Nodes via NODE_TYPE_ALIASES in workflow_loader.
"""

# Super Nodes (consolidated operations)
from casare_rpa.presentation.canvas.visual_nodes.file_operations.super_nodes import (
    VisualFileSystemSuperNode,
    VisualStructuredDataSuperNode,
)

# XML operations (not yet consolidated)
from casare_rpa.presentation.canvas.visual_nodes.file_operations.nodes import (
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
    "VisualStructuredDataSuperNode",
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
