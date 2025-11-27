"""
Visual Nodes - File Operations
"""

from .nodes import (
    # Basic file operations
    VisualReadFileNode,
    VisualWriteFileNode,
    VisualAppendFileNode,
    VisualDeleteFileNode,
    VisualCopyFileNode,
    VisualMoveFileNode,
    VisualFileExistsNode,
    VisualGetFileSizeNode,
    VisualGetFileInfoNode,
    VisualListFilesNode,
    # CSV operations
    VisualReadCsvNode,
    VisualWriteCsvNode,
    # JSON operations
    VisualReadJsonNode,
    VisualWriteJsonNode,
    # ZIP operations
    VisualZipFilesNode,
    VisualUnzipFileNode,
    # XML operations
    VisualParseXMLNode,
    VisualReadXMLFileNode,
    VisualWriteXMLFileNode,
    VisualXPathQueryNode,
    VisualGetXMLElementNode,
    VisualGetXMLAttributeNode,
    VisualXMLToJsonNode,
    VisualJsonToXMLNode,
    # PDF operations
    VisualReadPDFTextNode,
    VisualGetPDFInfoNode,
    VisualMergePDFsNode,
    VisualSplitPDFNode,
    VisualExtractPDFPagesNode,
    VisualPDFToImagesNode,
    # FTP operations
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
    # Basic file operations
    "VisualReadFileNode",
    "VisualWriteFileNode",
    "VisualAppendFileNode",
    "VisualDeleteFileNode",
    "VisualCopyFileNode",
    "VisualMoveFileNode",
    "VisualFileExistsNode",
    "VisualGetFileSizeNode",
    "VisualGetFileInfoNode",
    "VisualListFilesNode",
    # CSV operations
    "VisualReadCsvNode",
    "VisualWriteCsvNode",
    # JSON operations
    "VisualReadJsonNode",
    "VisualWriteJsonNode",
    # ZIP operations
    "VisualZipFilesNode",
    "VisualUnzipFileNode",
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
