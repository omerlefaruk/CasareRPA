"""Test visual node to logic node mappings."""

import pytest

from casare_rpa.presentation.canvas.visual_nodes.file_operations.nodes import (
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
    VisualReadCsvNode,
    VisualWriteCsvNode,
    VisualReadJsonNode,
    VisualWriteJsonNode,
    VisualZipFilesNode,
    VisualUnzipFileNode,
)
from casare_rpa.presentation.canvas.visual_nodes.email.nodes import (
    VisualSendEmailNode,
    VisualReadEmailsNode,
    VisualGetEmailContentNode,
    VisualSaveAttachmentNode,
    VisualFilterEmailsNode,
    VisualMarkEmailNode,
    VisualDeleteEmailNode,
    VisualMoveEmailNode,
)
from casare_rpa.nodes.file import (
    ReadFileNode,
    WriteFileNode,
    AppendFileNode,
    DeleteFileNode,
    CopyFileNode,
    MoveFileNode,
    FileExistsNode,
    GetFileSizeNode,
    GetFileInfoNode,
    ListFilesNode,
    ReadCSVNode,
    WriteCSVNode,
    ReadJSONFileNode,
    WriteJSONFileNode,
    ZipFilesNode,
    UnzipFilesNode,
)
from casare_rpa.nodes.email_nodes import (
    SendEmailNode,
    ReadEmailsNode,
    GetEmailContentNode,
    SaveAttachmentNode,
    FilterEmailsNode,
    MarkEmailNode,
    DeleteEmailNode,
    MoveEmailNode,
)


class TestFileOperationsVisualNodeMappings:
    """Test visual node to logic node mappings for file operations."""

    @pytest.mark.parametrize(
        "visual_node_class,expected_node_class,expected_class_name",
        [
            (VisualReadFileNode, ReadFileNode, "ReadFileNode"),
            (VisualWriteFileNode, WriteFileNode, "WriteFileNode"),
            (VisualAppendFileNode, AppendFileNode, "AppendFileNode"),
            (VisualDeleteFileNode, DeleteFileNode, "DeleteFileNode"),
            (VisualCopyFileNode, CopyFileNode, "CopyFileNode"),
            (VisualMoveFileNode, MoveFileNode, "MoveFileNode"),
            (VisualFileExistsNode, FileExistsNode, "FileExistsNode"),
            (VisualGetFileSizeNode, GetFileSizeNode, "GetFileSizeNode"),
            (VisualGetFileInfoNode, GetFileInfoNode, "GetFileInfoNode"),
            (VisualListFilesNode, ListFilesNode, "ListFilesNode"),
            (VisualReadCsvNode, ReadCSVNode, "ReadCSVNode"),
            (VisualWriteCsvNode, WriteCSVNode, "WriteCSVNode"),
            (VisualReadJsonNode, ReadJSONFileNode, "ReadJSONFileNode"),
            (VisualWriteJsonNode, WriteJSONFileNode, "WriteJSONFileNode"),
            (VisualZipFilesNode, ZipFilesNode, "ZipFilesNode"),
            (VisualUnzipFileNode, UnzipFilesNode, "UnzipFilesNode"),
        ],
    )
    def test_file_operations_node_class_mapping(
        self, visual_node_class, expected_node_class, expected_class_name
    ) -> None:
        """Test visual node correctly maps to logic node."""
        assert hasattr(visual_node_class, "CASARE_NODE_CLASS")
        assert visual_node_class.CASARE_NODE_CLASS == expected_class_name
        assert hasattr(visual_node_class, "get_node_class")


class TestEmailVisualNodeMappings:
    """Test visual node to logic node mappings for email operations."""

    @pytest.mark.parametrize(
        "visual_node_class,expected_node_class,expected_class_name",
        [
            (VisualSendEmailNode, SendEmailNode, "SendEmailNode"),
            (VisualReadEmailsNode, ReadEmailsNode, "ReadEmailsNode"),
            (VisualGetEmailContentNode, GetEmailContentNode, "GetEmailContentNode"),
            (VisualSaveAttachmentNode, SaveAttachmentNode, "SaveAttachmentNode"),
            (VisualFilterEmailsNode, FilterEmailsNode, "FilterEmailsNode"),
            (VisualMarkEmailNode, MarkEmailNode, "MarkEmailNode"),
            (VisualDeleteEmailNode, DeleteEmailNode, "DeleteEmailNode"),
            (VisualMoveEmailNode, MoveEmailNode, "MoveEmailNode"),
        ],
    )
    def test_email_node_class_mapping(
        self, visual_node_class, expected_node_class, expected_class_name
    ) -> None:
        """Test visual node correctly maps to logic node."""
        assert hasattr(visual_node_class, "CASARE_NODE_CLASS")
        assert visual_node_class.CASARE_NODE_CLASS == expected_class_name
        assert hasattr(visual_node_class, "get_node_class")
