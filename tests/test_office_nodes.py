"""
Unit tests for Office Automation Nodes

Tests Excel, Word, and Outlook nodes with mocked win32com.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from casare_rpa.nodes.desktop_nodes.office_nodes import (
    ExcelOpenNode,
    ExcelReadCellNode,
    ExcelWriteCellNode,
    ExcelGetRangeNode,
    ExcelCloseNode,
    WordOpenNode,
    WordGetTextNode,
    WordReplaceTextNode,
    WordCloseNode,
    OutlookSendEmailNode,
    OutlookReadEmailsNode,
    OutlookGetInboxCountNode,
)


# ============================================================================
# Excel Node Tests
# ============================================================================

class TestExcelOpenNode:
    """Tests for ExcelOpenNode"""

    def test_node_creation(self):
        """Test node creation with default config"""
        node = ExcelOpenNode()
        assert node.name == "Excel Open"
        assert node.node_type == "ExcelOpenNode"
        assert node.config.get("visible") is False
        assert node.config.get("create_if_missing") is False

    def test_node_creation_with_config(self):
        """Test node creation with custom config"""
        node = ExcelOpenNode(config={"visible": True, "create_if_missing": True})
        assert node.config.get("visible") is True
        assert node.config.get("create_if_missing") is True

    def test_ports_defined(self):
        """Test input/output ports are defined"""
        node = ExcelOpenNode()
        assert "file_path" in node.input_ports
        assert "workbook" in node.output_ports
        assert "app" in node.output_ports
        assert "success" in node.output_ports


class TestExcelReadCellNode:
    """Tests for ExcelReadCellNode"""

    def test_node_creation(self):
        """Test node creation"""
        node = ExcelReadCellNode()
        assert node.name == "Excel Read Cell"
        assert node.node_type == "ExcelReadCellNode"
        assert node.config.get("sheet") == 1

    def test_ports_defined(self):
        """Test input/output ports are defined"""
        node = ExcelReadCellNode()
        assert "workbook" in node.input_ports
        assert "sheet" in node.input_ports
        assert "cell" in node.input_ports
        assert "value" in node.output_ports
        assert "success" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_requires_workbook(self):
        """Test execute raises error without workbook"""
        node = ExcelReadCellNode()
        node.set_input_value("cell", "A1")
        with pytest.raises(ValueError, match="Workbook is required"):
            await node.execute({})

    @pytest.mark.asyncio
    async def test_execute_requires_cell(self):
        """Test execute raises error without cell reference"""
        node = ExcelReadCellNode()
        node.set_input_value("workbook", Mock())
        with pytest.raises(ValueError, match="Cell reference is required"):
            await node.execute({})


class TestExcelWriteCellNode:
    """Tests for ExcelWriteCellNode"""

    def test_node_creation(self):
        """Test node creation"""
        node = ExcelWriteCellNode()
        assert node.name == "Excel Write Cell"
        assert node.node_type == "ExcelWriteCellNode"

    def test_ports_defined(self):
        """Test input/output ports are defined"""
        node = ExcelWriteCellNode()
        assert "workbook" in node.input_ports
        assert "cell" in node.input_ports
        assert "value" in node.input_ports
        assert "success" in node.output_ports


class TestExcelGetRangeNode:
    """Tests for ExcelGetRangeNode"""

    def test_node_creation(self):
        """Test node creation"""
        node = ExcelGetRangeNode()
        assert node.name == "Excel Get Range"
        assert node.node_type == "ExcelGetRangeNode"

    def test_ports_defined(self):
        """Test input/output ports are defined"""
        node = ExcelGetRangeNode()
        assert "workbook" in node.input_ports
        assert "range" in node.input_ports
        assert "data" in node.output_ports
        assert "rows" in node.output_ports
        assert "columns" in node.output_ports


class TestExcelCloseNode:
    """Tests for ExcelCloseNode"""

    def test_node_creation(self):
        """Test node creation with default config"""
        node = ExcelCloseNode()
        assert node.name == "Excel Close"
        assert node.node_type == "ExcelCloseNode"
        assert node.config.get("save") is True
        assert node.config.get("quit_app") is True

    def test_ports_defined(self):
        """Test input/output ports are defined"""
        node = ExcelCloseNode()
        assert "workbook" in node.input_ports
        assert "app" in node.input_ports
        assert "success" in node.output_ports


# ============================================================================
# Word Node Tests
# ============================================================================

class TestWordOpenNode:
    """Tests for WordOpenNode"""

    def test_node_creation(self):
        """Test node creation"""
        node = WordOpenNode()
        assert node.name == "Word Open"
        assert node.node_type == "WordOpenNode"
        assert node.config.get("visible") is False

    def test_ports_defined(self):
        """Test input/output ports are defined"""
        node = WordOpenNode()
        assert "file_path" in node.input_ports
        assert "document" in node.output_ports
        assert "app" in node.output_ports
        assert "success" in node.output_ports


class TestWordGetTextNode:
    """Tests for WordGetTextNode"""

    def test_node_creation(self):
        """Test node creation"""
        node = WordGetTextNode()
        assert node.name == "Word Get Text"
        assert node.node_type == "WordGetTextNode"

    def test_ports_defined(self):
        """Test input/output ports are defined"""
        node = WordGetTextNode()
        assert "document" in node.input_ports
        assert "text" in node.output_ports
        assert "word_count" in node.output_ports
        assert "success" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_requires_document(self):
        """Test execute raises error without document"""
        node = WordGetTextNode()
        with pytest.raises(ValueError, match="Document is required"):
            await node.execute({})


class TestWordReplaceTextNode:
    """Tests for WordReplaceTextNode"""

    def test_node_creation(self):
        """Test node creation"""
        node = WordReplaceTextNode()
        assert node.name == "Word Replace Text"
        assert node.node_type == "WordReplaceTextNode"
        assert node.config.get("match_case") is False
        assert node.config.get("replace_all") is True

    def test_ports_defined(self):
        """Test input/output ports are defined"""
        node = WordReplaceTextNode()
        assert "document" in node.input_ports
        assert "find_text" in node.input_ports
        assert "replace_text" in node.input_ports
        assert "replacements" in node.output_ports


class TestWordCloseNode:
    """Tests for WordCloseNode"""

    def test_node_creation(self):
        """Test node creation"""
        node = WordCloseNode()
        assert node.name == "Word Close"
        assert node.node_type == "WordCloseNode"
        assert node.config.get("save") is True
        assert node.config.get("quit_app") is True

    def test_ports_defined(self):
        """Test input/output ports are defined"""
        node = WordCloseNode()
        assert "document" in node.input_ports
        assert "app" in node.input_ports
        assert "success" in node.output_ports


# ============================================================================
# Outlook Node Tests
# ============================================================================

class TestOutlookSendEmailNode:
    """Tests for OutlookSendEmailNode"""

    def test_node_creation(self):
        """Test node creation"""
        node = OutlookSendEmailNode()
        assert node.name == "Outlook Send Email"
        assert node.node_type == "OutlookSendEmailNode"
        assert node.config.get("html_body") is False

    def test_ports_defined(self):
        """Test input/output ports are defined"""
        node = OutlookSendEmailNode()
        assert "to" in node.input_ports
        assert "subject" in node.input_ports
        assert "body" in node.input_ports
        assert "cc" in node.input_ports
        assert "bcc" in node.input_ports
        assert "attachments" in node.input_ports
        assert "success" in node.output_ports


class TestOutlookReadEmailsNode:
    """Tests for OutlookReadEmailsNode"""

    def test_node_creation(self):
        """Test node creation"""
        node = OutlookReadEmailsNode()
        assert node.name == "Outlook Read Emails"
        assert node.node_type == "OutlookReadEmailsNode"
        assert node.config.get("folder") == "Inbox"
        assert node.config.get("count") == 10
        assert node.config.get("unread_only") is False

    def test_ports_defined(self):
        """Test input/output ports are defined"""
        node = OutlookReadEmailsNode()
        assert "emails" in node.output_ports
        assert "count" in node.output_ports
        assert "success" in node.output_ports


class TestOutlookGetInboxCountNode:
    """Tests for OutlookGetInboxCountNode"""

    def test_node_creation(self):
        """Test node creation"""
        node = OutlookGetInboxCountNode()
        assert node.name == "Outlook Get Inbox Count"
        assert node.node_type == "OutlookGetInboxCountNode"

    def test_ports_defined(self):
        """Test input/output ports are defined"""
        node = OutlookGetInboxCountNode()
        assert "total_count" in node.output_ports
        assert "unread_count" in node.output_ports
        assert "success" in node.output_ports


# ============================================================================
# Integration-style Tests with Mocked COM
# ============================================================================

class TestExcelWithMockedCOM:
    """Tests with mocked win32com for Excel operations"""

    @pytest.mark.asyncio
    @patch('casare_rpa.nodes.desktop_nodes.office_nodes.HAS_WIN32COM', True)
    @patch('casare_rpa.nodes.desktop_nodes.office_nodes.win32com.client.Dispatch')
    async def test_excel_read_cell(self, mock_dispatch):
        """Test reading a cell value from Excel"""
        # Setup mock workbook
        mock_ws = Mock()
        mock_ws.Range.return_value.Value = "Test Value"
        mock_workbook = Mock()
        mock_workbook.Sheets.return_value = mock_ws

        node = ExcelReadCellNode()
        node.set_input_value("workbook", mock_workbook)
        node.set_input_value("cell", "A1")

        result = await node.execute({})

        assert result["success"] is True
        assert node.get_output_value("value") == "Test Value"

    @pytest.mark.asyncio
    @patch('casare_rpa.nodes.desktop_nodes.office_nodes.HAS_WIN32COM', True)
    @patch('casare_rpa.nodes.desktop_nodes.office_nodes.win32com.client.Dispatch')
    async def test_excel_write_cell(self, mock_dispatch):
        """Test writing a cell value to Excel"""
        mock_ws = Mock()
        mock_range = Mock()
        mock_ws.Range.return_value = mock_range
        mock_workbook = Mock()
        mock_workbook.Sheets.return_value = mock_ws

        node = ExcelWriteCellNode()
        node.set_input_value("workbook", mock_workbook)
        node.set_input_value("cell", "B2")
        node.set_input_value("value", "New Value")

        result = await node.execute({})

        assert result["success"] is True
        mock_range.Value = "New Value"

    @pytest.mark.asyncio
    @patch('casare_rpa.nodes.desktop_nodes.office_nodes.HAS_WIN32COM', True)
    async def test_excel_close(self):
        """Test closing Excel workbook"""
        mock_workbook = Mock()
        mock_app = Mock()

        node = ExcelCloseNode()
        node.set_input_value("workbook", mock_workbook)
        node.set_input_value("app", mock_app)

        result = await node.execute({})

        assert result["success"] is True
        mock_workbook.Save.assert_called_once()
        mock_workbook.Close.assert_called_once_with(SaveChanges=True)
        mock_app.Quit.assert_called_once()


class TestWordWithMockedCOM:
    """Tests with mocked win32com for Word operations"""

    @pytest.mark.asyncio
    @patch('casare_rpa.nodes.desktop_nodes.office_nodes.HAS_WIN32COM', True)
    async def test_word_get_text(self):
        """Test getting text from Word document"""
        mock_doc = Mock()
        mock_doc.Content.Text = "Hello World"
        mock_doc.Words.Count = 2

        node = WordGetTextNode()
        node.set_input_value("document", mock_doc)

        result = await node.execute({})

        assert result["success"] is True
        assert node.get_output_value("text") == "Hello World"
        assert node.get_output_value("word_count") == 2

    @pytest.mark.asyncio
    @patch('casare_rpa.nodes.desktop_nodes.office_nodes.HAS_WIN32COM', True)
    async def test_word_close(self):
        """Test closing Word document"""
        mock_doc = Mock()
        mock_app = Mock()

        node = WordCloseNode()
        node.set_input_value("document", mock_doc)
        node.set_input_value("app", mock_app)

        result = await node.execute({})

        assert result["success"] is True
        mock_doc.Save.assert_called_once()
        mock_doc.Close.assert_called_once()
        mock_app.Quit.assert_called_once()
