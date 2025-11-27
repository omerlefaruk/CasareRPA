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
    VisualCreateDirectoryNode,
    VisualListDirectoryNode,
    VisualFileExistsNode,
    VisualGetFileSizeNode,
    VisualGetFileInfoNode,
    VisualListFilesNode,
    # CSV operations
    VisualReadCsvNode,
    VisualWriteCsvNode,
    VisualReadCSVNode,
    VisualWriteCSVNode,
    # JSON operations
    VisualReadJsonNode,
    VisualWriteJsonNode,
    VisualReadJSONFileNode,
    VisualWriteJSONFileNode,
    # ZIP operations
    VisualZipFilesNode,
    VisualUnzipFileNode,
    VisualUnzipFilesNode,
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
    "VisualCreateDirectoryNode",
    "VisualListDirectoryNode",
    "VisualFileExistsNode",
    "VisualGetFileSizeNode",
    "VisualGetFileInfoNode",
    "VisualListFilesNode",
    # CSV operations
    "VisualReadCsvNode",
    "VisualWriteCsvNode",
    "VisualReadCSVNode",
    "VisualWriteCSVNode",
    # JSON operations
    "VisualReadJsonNode",
    "VisualWriteJsonNode",
    "VisualReadJSONFileNode",
    "VisualWriteJSONFileNode",
    # ZIP operations
    "VisualZipFilesNode",
    "VisualUnzipFileNode",
    "VisualUnzipFilesNode",
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
