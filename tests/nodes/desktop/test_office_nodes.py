"""
Comprehensive tests for Office automation nodes.

Tests Excel, Word, and Outlook automation nodes with mocked win32com.
All tests use mocked COM objects to avoid requiring Office installation.

Node coverage:
- Excel: ExcelOpenNode, ExcelReadCellNode, ExcelWriteCellNode, ExcelGetRangeNode, ExcelCloseNode
- Word: WordOpenNode, WordGetTextNode, WordReplaceTextNode, WordCloseNode
- Outlook: OutlookSendEmailNode, OutlookReadEmailsNode, OutlookGetInboxCountNode
"""

import sys
import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from typing import Any, Dict, List

# Skip all tests if not on Windows
pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="Office automation only available on Windows"
)


# =============================================================================
# Mock COM Objects
# =============================================================================


class MockExcelWorkbook:
    """Mock Excel workbook object."""

    def __init__(self, path: str = None):
        self._path = path
        self._sheets = MockSheets()
        self._saved = False

    @property
    def Sheets(self):
        return self._sheets

    def Save(self):
        self._saved = True

    def SaveAs(self, path: str):
        self._path = path
        self._saved = True

    def Close(self, SaveChanges: bool = False):
        if SaveChanges:
            self.Save()


class MockExcelWorksheet:
    """Mock Excel worksheet object."""

    def __init__(self, name: str = "Sheet1"):
        self._name = name
        self._cells: Dict[str, Any] = {}

    def Range(self, ref: str):
        return MockExcelRange(self, ref)


class MockExcelRange:
    """Mock Excel range object."""

    def __init__(self, sheet: MockExcelWorksheet, ref: str):
        self._sheet = sheet
        self._ref = ref

    @property
    def Value(self):
        return self._sheet._cells.get(self._ref, None)

    @Value.setter
    def Value(self, value):
        self._sheet._cells[self._ref] = value


class MockSheets:
    """Mock Excel Sheets collection."""

    def __init__(self):
        self._sheets = {"Sheet1": MockExcelWorksheet("Sheet1")}

    def __call__(self, name_or_index):
        if isinstance(name_or_index, int):
            sheets_list = list(self._sheets.values())
            if 1 <= name_or_index <= len(sheets_list):
                return sheets_list[name_or_index - 1]
            raise Exception(f"Sheet index {name_or_index} out of range")
        if name_or_index in self._sheets:
            return self._sheets[name_or_index]
        raise Exception(f"Sheet '{name_or_index}' not found")


class MockExcelWorkbooks:
    """Mock Excel Workbooks collection."""

    def __init__(self, excel_app):
        self._excel = excel_app
        self._workbooks: List[MockExcelWorkbook] = []

    def Open(self, path: str):
        wb = MockExcelWorkbook(path)
        self._workbooks.append(wb)
        return wb

    def Add(self):
        wb = MockExcelWorkbook()
        self._workbooks.append(wb)
        return wb


class MockExcelApplication:
    """Mock Excel.Application COM object."""

    def __init__(self):
        self.Visible = False
        self.DisplayAlerts = True
        self._workbooks = MockExcelWorkbooks(self)
        self._quit = False

    @property
    def Workbooks(self):
        return self._workbooks

    def Quit(self):
        self._quit = True


class MockWordDocument:
    """Mock Word document object."""

    def __init__(self, path: str = None):
        self._path = path
        self._text = "Sample document text."
        self._word_count = 4
        self._saved = False
        self._content = MockWordContent(self)
        self._words = MockWordWords(self)

    @property
    def Content(self):
        return self._content

    @property
    def Words(self):
        return self._words

    def Save(self):
        self._saved = True

    def SaveAs(self, path: str):
        self._path = path
        self._saved = True

    def Close(self, SaveChanges: bool = False):
        if SaveChanges:
            self.Save()


class MockWordContent:
    """Mock Word Content object."""

    def __init__(self, doc: MockWordDocument):
        self._doc = doc

    @property
    def Text(self):
        return self._doc._text

    @property
    def Find(self):
        return MockWordFind(self._doc)


class MockWordFind:
    """Mock Word Find object."""

    def __init__(self, doc: MockWordDocument):
        self._doc = doc
        self._replacements = 0
        self.Replacement = MockWordReplacement()

    def ClearFormatting(self):
        pass

    def Execute(
        self,
        FindText: str = "",
        MatchCase: bool = False,
        ReplaceWith: str = "",
        Replace: int = 1,
    ) -> bool:
        if self._replacements == 0 and FindText in self._doc._text:
            self._doc._text = self._doc._text.replace(FindText, ReplaceWith, 1)
            self._replacements += 1
            return True
        return False


class MockWordReplacement:
    """Mock Word Replacement object."""

    def ClearFormatting(self):
        pass


class MockWordWords:
    """Mock Word Words collection."""

    def __init__(self, doc: MockWordDocument):
        self._doc = doc

    @property
    def Count(self):
        return self._doc._word_count


class MockWordDocuments:
    """Mock Word Documents collection."""

    def __init__(self, word_app):
        self._word = word_app
        self._documents: List[MockWordDocument] = []

    def Open(self, path: str):
        doc = MockWordDocument(path)
        self._documents.append(doc)
        return doc

    def Add(self):
        doc = MockWordDocument()
        self._documents.append(doc)
        return doc


class MockWordApplication:
    """Mock Word.Application COM object."""

    def __init__(self):
        self.Visible = False
        self._documents = MockWordDocuments(self)
        self._quit = False

    @property
    def Documents(self):
        return self._documents

    def Quit(self):
        self._quit = True


class MockOutlookMailItem:
    """Mock Outlook mail item."""

    def __init__(self):
        self.To = ""
        self.Subject = ""
        self.Body = ""
        self.HTMLBody = ""
        self.CC = ""
        self.BCC = ""
        self.Attachments = MockAttachments()
        self._sent = False

    def Send(self):
        self._sent = True


class MockAttachments:
    """Mock Outlook Attachments collection."""

    def __init__(self):
        self._items: List[str] = []

    def Add(self, path: str):
        self._items.append(path)

    @property
    def Count(self):
        return len(self._items)


class MockOutlookMessage:
    """Mock Outlook inbox message."""

    def __init__(
        self,
        subject: str = "Test Email",
        sender: str = "test@example.com",
        body: str = "Email body",
        unread: bool = True,
    ):
        self.Subject = subject
        self.SenderEmailAddress = sender
        self.SenderName = "Test Sender"
        self.ReceivedTime = "2024-01-15 10:30:00"
        self.Body = body
        self.UnRead = unread
        self.Attachments = MockAttachments()


class MockOutlookFolder:
    """Mock Outlook folder."""

    def __init__(self, messages: List[MockOutlookMessage] = None):
        self._messages = messages or []
        self._items = MockOutlookItems(self._messages)

    @property
    def Items(self):
        return self._items

    @property
    def UnReadItemCount(self):
        return sum(1 for m in self._messages if m.UnRead)


class MockOutlookItems:
    """Mock Outlook Items collection."""

    def __init__(self, messages: List[MockOutlookMessage]):
        self._messages = messages
        self._sorted = False

    def __iter__(self):
        return iter(self._messages)

    def Sort(self, field: str, descending: bool = False):
        self._sorted = True

    @property
    def Count(self):
        return len(self._messages)


class MockOutlookNamespace:
    """Mock Outlook MAPI namespace."""

    def __init__(self, inbox: MockOutlookFolder = None):
        self._inbox = inbox or MockOutlookFolder()
        self._folders = MockOutlookFolders()

    def GetDefaultFolder(self, folder_type: int):
        if folder_type == 6:  # olFolderInbox
            return self._inbox
        raise Exception(f"Unknown folder type: {folder_type}")

    @property
    def Folders(self):
        return self._folders


class MockOutlookFolders:
    """Mock Outlook Folders collection."""

    def Item(self, index: int):
        return MockOutlookFolderItem()


class MockOutlookFolderItem:
    """Mock Outlook folder item."""

    @property
    def Folders(self):
        return MockOutlookSubFolders()


class MockOutlookSubFolders:
    """Mock Outlook subfolders."""

    def Item(self, name: str):
        return MockOutlookFolder()


class MockOutlookApplication:
    """Mock Outlook.Application COM object."""

    def __init__(self, namespace: MockOutlookNamespace = None):
        self._namespace = namespace or MockOutlookNamespace()
        self._mail_items: List[MockOutlookMailItem] = []

    def CreateItem(self, item_type: int):
        if item_type == 0:  # olMailItem
            item = MockOutlookMailItem()
            self._mail_items.append(item)
            return item
        raise Exception(f"Unknown item type: {item_type}")

    def GetNamespace(self, namespace: str):
        if namespace == "MAPI":
            return self._namespace
        raise Exception(f"Unknown namespace: {namespace}")


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_excel_app():
    """Create mock Excel application."""
    return MockExcelApplication()


@pytest.fixture
def mock_word_app():
    """Create mock Word application."""
    return MockWordApplication()


@pytest.fixture
def mock_outlook_app():
    """Create mock Outlook application."""
    return MockOutlookApplication()


@pytest.fixture
def mock_win32com(monkeypatch, mock_excel_app, mock_word_app, mock_outlook_app):
    """
    Mock win32com.client.Dispatch for all Office applications.

    Returns dict with mock app instances for verification.
    """

    def mock_dispatch(app_name: str):
        apps = {
            "Excel.Application": mock_excel_app,
            "Word.Application": mock_word_app,
            "Outlook.Application": mock_outlook_app,
        }
        if app_name in apps:
            return apps[app_name]
        raise Exception(f"Unknown application: {app_name}")

    # Patch the module-level HAS_WIN32COM flag and Dispatch
    monkeypatch.setattr(
        "casare_rpa.nodes.desktop_nodes.office_nodes.HAS_WIN32COM", True
    )
    monkeypatch.setattr(
        "casare_rpa.nodes.desktop_nodes.office_nodes.win32com.client.Dispatch",
        mock_dispatch,
    )

    return {
        "excel": mock_excel_app,
        "word": mock_word_app,
        "outlook": mock_outlook_app,
    }


@pytest.fixture
def execution_context():
    """Create mock execution context."""
    context = Mock()
    context.resolve_value = lambda x: x
    context.variables = {}
    context.get_variable = lambda name, default=None: context.variables.get(
        name, default
    )
    context.set_variable = lambda name, value: context.variables.__setitem__(
        name, value
    )
    return context


@pytest.fixture
def temp_excel_file(tmp_path):
    """Create path for temp Excel file."""
    return str(tmp_path / "test.xlsx")


@pytest.fixture
def temp_word_file(tmp_path):
    """Create path for temp Word file."""
    return str(tmp_path / "test.docx")


# =============================================================================
# Excel Node Tests
# =============================================================================


class TestExcelOpenNode:
    """Tests for ExcelOpenNode."""

    @pytest.mark.asyncio
    async def test_open_existing_file_success(
        self, mock_win32com, execution_context, tmp_path
    ):
        """Test opening existing Excel file."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelOpenNode

        # Create temp file
        test_file = tmp_path / "test.xlsx"
        test_file.write_bytes(b"dummy")

        node = ExcelOpenNode(node_id="test_open")
        node.set_input_value("file_path", str(test_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["file_path"] == str(test_file)
        assert node.get_output_value("success") is True
        assert node.get_output_value("workbook") is not None
        assert node.get_output_value("app") is not None

    @pytest.mark.asyncio
    async def test_open_with_visible_option(
        self, mock_win32com, execution_context, tmp_path
    ):
        """Test opening Excel with visible window."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelOpenNode

        test_file = tmp_path / "test.xlsx"
        test_file.write_bytes(b"dummy")

        node = ExcelOpenNode(node_id="test_visible", config={"visible": True})
        node.set_input_value("file_path", str(test_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert mock_win32com["excel"].Visible is True

    @pytest.mark.asyncio
    async def test_create_new_workbook_when_missing(
        self, mock_win32com, execution_context, tmp_path
    ):
        """Test creating new workbook when file not found."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelOpenNode

        node = ExcelOpenNode(node_id="test_create", config={"create_if_missing": True})
        node.set_input_value("file_path", str(tmp_path / "new.xlsx"))

        result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_file_not_found_error(self, mock_win32com, execution_context):
        """Test error when file not found and create_if_missing=False."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelOpenNode

        node = ExcelOpenNode(node_id="test_fnf", config={"create_if_missing": False})
        node.set_input_value("file_path", "C:\\nonexistent\\file.xlsx")

        with pytest.raises(FileNotFoundError, match="Excel file not found"):
            await node.execute(execution_context)

    @pytest.mark.asyncio
    async def test_create_without_path(self, mock_win32com, execution_context):
        """Test creating new workbook without path."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelOpenNode

        node = ExcelOpenNode(node_id="test_no_path")
        # No file_path set

        result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_pywin32_not_installed(self, monkeypatch, execution_context):
        """Test error when pywin32 not installed."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelOpenNode

        monkeypatch.setattr(
            "casare_rpa.nodes.desktop_nodes.office_nodes.HAS_WIN32COM", False
        )

        node = ExcelOpenNode(node_id="test_no_win32")
        node.set_input_value("file_path", "test.xlsx")

        with pytest.raises(RuntimeError, match="pywin32 not installed"):
            await node.execute(execution_context)

    @pytest.mark.asyncio
    async def test_variable_resolution(
        self, mock_win32com, execution_context, tmp_path
    ):
        """Test that file path resolves variables."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelOpenNode

        test_file = tmp_path / "test.xlsx"
        test_file.write_bytes(b"dummy")

        # Mock resolve_value to return actual path
        execution_context.resolve_value = Mock(return_value=str(test_file))

        node = ExcelOpenNode(node_id="test_resolve")
        node.set_input_value("file_path", "{{my_path}}")

        result = await node.execute(execution_context)

        assert result["success"] is True
        execution_context.resolve_value.assert_called_with("{{my_path}}")

    @pytest.mark.asyncio
    async def test_display_alerts_disabled(
        self, mock_win32com, execution_context, tmp_path
    ):
        """Test that DisplayAlerts is disabled."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelOpenNode

        test_file = tmp_path / "test.xlsx"
        test_file.write_bytes(b"dummy")

        node = ExcelOpenNode(node_id="test_alerts")
        node.set_input_value("file_path", str(test_file))

        await node.execute(execution_context)

        assert mock_win32com["excel"].DisplayAlerts is False


class TestExcelReadCellNode:
    """Tests for ExcelReadCellNode."""

    @pytest.mark.asyncio
    async def test_read_cell_success(self, mock_win32com, execution_context):
        """Test reading cell value."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelReadCellNode

        workbook = MockExcelWorkbook()
        workbook.Sheets(1)._cells["A1"] = "Test Value"

        node = ExcelReadCellNode(node_id="test_read")
        node.set_input_value("workbook", workbook)
        node.set_input_value("cell", "A1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["value"] == "Test Value"
        assert result["cell"] == "A1"

    @pytest.mark.asyncio
    async def test_read_cell_with_sheet_name(self, mock_win32com, execution_context):
        """Test reading cell from named sheet."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelReadCellNode

        workbook = MockExcelWorkbook()
        workbook.Sheets._sheets["Sheet1"]._cells["B2"] = 42

        node = ExcelReadCellNode(node_id="test_sheet")
        node.set_input_value("workbook", workbook)
        node.set_input_value("sheet", "Sheet1")
        node.set_input_value("cell", "B2")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["value"] == 42

    @pytest.mark.asyncio
    async def test_read_cell_with_sheet_index(self, mock_win32com, execution_context):
        """Test reading cell from sheet by index."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelReadCellNode

        workbook = MockExcelWorkbook()
        workbook.Sheets(1)._cells["C3"] = 3.14

        node = ExcelReadCellNode(node_id="test_index")
        node.set_input_value("workbook", workbook)
        node.set_input_value("sheet", 1)
        node.set_input_value("cell", "C3")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["value"] == 3.14

    @pytest.mark.asyncio
    async def test_read_cell_empty_value(self, mock_win32com, execution_context):
        """Test reading empty cell returns None."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelReadCellNode

        workbook = MockExcelWorkbook()

        node = ExcelReadCellNode(node_id="test_empty")
        node.set_input_value("workbook", workbook)
        node.set_input_value("cell", "Z99")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["value"] is None

    @pytest.mark.asyncio
    async def test_read_cell_missing_workbook(self, mock_win32com, execution_context):
        """Test error when workbook not provided."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelReadCellNode

        node = ExcelReadCellNode(node_id="test_no_wb")
        node.set_input_value("cell", "A1")

        with pytest.raises(ValueError, match="Workbook is required"):
            await node.execute(execution_context)

    @pytest.mark.asyncio
    async def test_read_cell_missing_reference(self, mock_win32com, execution_context):
        """Test error when cell reference not provided."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelReadCellNode

        workbook = MockExcelWorkbook()

        node = ExcelReadCellNode(node_id="test_no_cell")
        node.set_input_value("workbook", workbook)

        with pytest.raises(ValueError, match="Cell reference is required"):
            await node.execute(execution_context)

    @pytest.mark.asyncio
    async def test_read_cell_default_sheet(self, mock_win32com, execution_context):
        """Test default sheet is 1."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelReadCellNode

        workbook = MockExcelWorkbook()
        workbook.Sheets(1)._cells["A1"] = "default"

        node = ExcelReadCellNode(node_id="test_default")
        node.set_input_value("workbook", workbook)
        node.set_input_value("cell", "A1")
        # sheet not set, should default to 1

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["value"] == "default"

    @pytest.mark.asyncio
    async def test_read_cell_variable_resolution(
        self, mock_win32com, execution_context
    ):
        """Test cell reference variable resolution."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelReadCellNode

        workbook = MockExcelWorkbook()
        workbook.Sheets(1)._cells["D4"] = "resolved"

        execution_context.resolve_value = Mock(
            side_effect=lambda x: "D4" if x == "{{cell}}" else x
        )

        node = ExcelReadCellNode(node_id="test_resolve")
        node.set_input_value("workbook", workbook)
        node.set_input_value("cell", "{{cell}}")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["value"] == "resolved"


class TestExcelWriteCellNode:
    """Tests for ExcelWriteCellNode."""

    @pytest.mark.asyncio
    async def test_write_cell_success(self, mock_win32com, execution_context):
        """Test writing value to cell."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelWriteCellNode

        workbook = MockExcelWorkbook()

        node = ExcelWriteCellNode(node_id="test_write")
        node.set_input_value("workbook", workbook)
        node.set_input_value("cell", "A1")
        node.set_input_value("value", "Written Value")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["cell"] == "A1"
        assert result["value"] == "Written Value"
        assert workbook.Sheets(1)._cells["A1"] == "Written Value"

    @pytest.mark.asyncio
    async def test_write_cell_numeric_value(self, mock_win32com, execution_context):
        """Test writing numeric value."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelWriteCellNode

        workbook = MockExcelWorkbook()

        node = ExcelWriteCellNode(node_id="test_num")
        node.set_input_value("workbook", workbook)
        node.set_input_value("cell", "B2")
        node.set_input_value("value", 123.45)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert workbook.Sheets(1)._cells["B2"] == 123.45

    @pytest.mark.asyncio
    async def test_write_cell_with_sheet_name(self, mock_win32com, execution_context):
        """Test writing to named sheet."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelWriteCellNode

        workbook = MockExcelWorkbook()

        node = ExcelWriteCellNode(node_id="test_sheet")
        node.set_input_value("workbook", workbook)
        node.set_input_value("sheet", "Sheet1")
        node.set_input_value("cell", "C3")
        node.set_input_value("value", "sheet1 value")

        result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_write_cell_overwrite_existing(
        self, mock_win32com, execution_context
    ):
        """Test overwriting existing cell value."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelWriteCellNode

        workbook = MockExcelWorkbook()
        workbook.Sheets(1)._cells["A1"] = "old value"

        node = ExcelWriteCellNode(node_id="test_overwrite")
        node.set_input_value("workbook", workbook)
        node.set_input_value("cell", "A1")
        node.set_input_value("value", "new value")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert workbook.Sheets(1)._cells["A1"] == "new value"

    @pytest.mark.asyncio
    async def test_write_cell_missing_workbook(self, mock_win32com, execution_context):
        """Test error when workbook not provided."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelWriteCellNode

        node = ExcelWriteCellNode(node_id="test_no_wb")
        node.set_input_value("cell", "A1")
        node.set_input_value("value", "test")

        with pytest.raises(ValueError, match="Workbook is required"):
            await node.execute(execution_context)

    @pytest.mark.asyncio
    async def test_write_cell_missing_reference(self, mock_win32com, execution_context):
        """Test error when cell reference not provided."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelWriteCellNode

        workbook = MockExcelWorkbook()

        node = ExcelWriteCellNode(node_id="test_no_cell")
        node.set_input_value("workbook", workbook)
        node.set_input_value("value", "test")

        with pytest.raises(ValueError, match="Cell reference is required"):
            await node.execute(execution_context)

    @pytest.mark.asyncio
    async def test_write_cell_none_value(self, mock_win32com, execution_context):
        """Test writing None value clears cell."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelWriteCellNode

        workbook = MockExcelWorkbook()
        workbook.Sheets(1)._cells["A1"] = "existing"

        node = ExcelWriteCellNode(node_id="test_none")
        node.set_input_value("workbook", workbook)
        node.set_input_value("cell", "A1")
        node.set_input_value("value", None)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert workbook.Sheets(1)._cells["A1"] is None

    @pytest.mark.asyncio
    async def test_write_cell_variable_resolution(
        self, mock_win32com, execution_context
    ):
        """Test variable resolution in cell and value."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelWriteCellNode

        workbook = MockExcelWorkbook()

        def resolve(x):
            return {"{{cell}}": "E5", "{{value}}": "resolved"}.get(x, x)

        execution_context.resolve_value = Mock(side_effect=resolve)

        node = ExcelWriteCellNode(node_id="test_resolve")
        node.set_input_value("workbook", workbook)
        node.set_input_value("cell", "{{cell}}")
        node.set_input_value("value", "test")

        result = await node.execute(execution_context)

        assert result["success"] is True


class TestExcelGetRangeNode:
    """Tests for ExcelGetRangeNode."""

    @pytest.mark.asyncio
    async def test_get_range_success(self, mock_win32com, execution_context):
        """Test reading range of cells."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelGetRangeNode

        workbook = MockExcelWorkbook()
        # Mock the range to return tuple data
        sheet = workbook.Sheets(1)
        original_range = sheet.Range

        def mock_range(ref):
            rng = Mock()
            rng.Value = (("A", "B"), ("C", "D"))
            return rng

        sheet.Range = mock_range

        node = ExcelGetRangeNode(node_id="test_range")
        node.set_input_value("workbook", workbook)
        node.set_input_value("range", "A1:B2")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["rows"] == 2
        assert result["columns"] == 2

    @pytest.mark.asyncio
    async def test_get_range_single_cell(self, mock_win32com, execution_context):
        """Test reading single cell as range."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelGetRangeNode

        workbook = MockExcelWorkbook()
        sheet = workbook.Sheets(1)

        def mock_range(ref):
            rng = Mock()
            rng.Value = "single"
            return rng

        sheet.Range = mock_range

        node = ExcelGetRangeNode(node_id="test_single")
        node.set_input_value("workbook", workbook)
        node.set_input_value("range", "A1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["rows"] == 1
        assert result["columns"] == 1

    @pytest.mark.asyncio
    async def test_get_range_empty(self, mock_win32com, execution_context):
        """Test reading empty range."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelGetRangeNode

        workbook = MockExcelWorkbook()
        sheet = workbook.Sheets(1)

        def mock_range(ref):
            rng = Mock()
            rng.Value = None
            return rng

        sheet.Range = mock_range

        node = ExcelGetRangeNode(node_id="test_empty")
        node.set_input_value("workbook", workbook)
        node.set_input_value("range", "Z1:Z10")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["rows"] == 1
        assert result["columns"] == 0

    @pytest.mark.asyncio
    async def test_get_range_missing_workbook(self, mock_win32com, execution_context):
        """Test error when workbook not provided."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelGetRangeNode

        node = ExcelGetRangeNode(node_id="test_no_wb")
        node.set_input_value("range", "A1:C10")

        with pytest.raises(ValueError, match="Workbook is required"):
            await node.execute(execution_context)

    @pytest.mark.asyncio
    async def test_get_range_missing_reference(self, mock_win32com, execution_context):
        """Test error when range reference not provided."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelGetRangeNode

        workbook = MockExcelWorkbook()

        node = ExcelGetRangeNode(node_id="test_no_range")
        node.set_input_value("workbook", workbook)

        with pytest.raises(ValueError, match="Range reference is required"):
            await node.execute(execution_context)


class TestExcelCloseNode:
    """Tests for ExcelCloseNode."""

    @pytest.mark.asyncio
    async def test_close_with_save(self, mock_win32com, execution_context):
        """Test closing workbook with save."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelCloseNode

        workbook = MockExcelWorkbook()
        app = mock_win32com["excel"]

        node = ExcelCloseNode(node_id="test_save", config={"save": True})
        node.set_input_value("workbook", workbook)
        node.set_input_value("app", app)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert workbook._saved is True

    @pytest.mark.asyncio
    async def test_close_without_save(self, mock_win32com, execution_context):
        """Test closing workbook without save."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelCloseNode

        workbook = MockExcelWorkbook()
        app = mock_win32com["excel"]

        node = ExcelCloseNode(node_id="test_nosave", config={"save": False})
        node.set_input_value("workbook", workbook)
        node.set_input_value("app", app)

        result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_close_and_quit_app(self, mock_win32com, execution_context):
        """Test closing workbook and quitting Excel."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelCloseNode

        workbook = MockExcelWorkbook()
        app = mock_win32com["excel"]

        node = ExcelCloseNode(
            node_id="test_quit", config={"save": False, "quit_app": True}
        )
        node.set_input_value("workbook", workbook)
        node.set_input_value("app", app)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert app._quit is True

    @pytest.mark.asyncio
    async def test_close_keep_app_open(self, mock_win32com, execution_context):
        """Test closing workbook but keeping Excel open."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelCloseNode

        workbook = MockExcelWorkbook()
        app = mock_win32com["excel"]

        node = ExcelCloseNode(
            node_id="test_keep", config={"save": False, "quit_app": False}
        )
        node.set_input_value("workbook", workbook)
        node.set_input_value("app", app)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert app._quit is False

    @pytest.mark.asyncio
    async def test_close_without_workbook(self, mock_win32com, execution_context):
        """Test closing when no workbook provided."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelCloseNode

        app = mock_win32com["excel"]

        node = ExcelCloseNode(node_id="test_no_wb", config={"quit_app": True})
        node.set_input_value("app", app)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert app._quit is True


# =============================================================================
# Word Node Tests
# =============================================================================


class TestWordOpenNode:
    """Tests for WordOpenNode."""

    @pytest.mark.asyncio
    async def test_open_existing_file_success(
        self, mock_win32com, execution_context, tmp_path
    ):
        """Test opening existing Word file."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import WordOpenNode

        test_file = tmp_path / "test.docx"
        test_file.write_bytes(b"dummy")

        node = WordOpenNode(node_id="test_open")
        node.set_input_value("file_path", str(test_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("document") is not None
        assert node.get_output_value("app") is not None

    @pytest.mark.asyncio
    async def test_open_with_visible_option(
        self, mock_win32com, execution_context, tmp_path
    ):
        """Test opening Word with visible window."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import WordOpenNode

        test_file = tmp_path / "test.docx"
        test_file.write_bytes(b"dummy")

        node = WordOpenNode(node_id="test_visible", config={"visible": True})
        node.set_input_value("file_path", str(test_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert mock_win32com["word"].Visible is True

    @pytest.mark.asyncio
    async def test_create_new_document_when_missing(
        self, mock_win32com, execution_context, tmp_path
    ):
        """Test creating new document when file not found."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import WordOpenNode

        node = WordOpenNode(node_id="test_create", config={"create_if_missing": True})
        node.set_input_value("file_path", str(tmp_path / "new.docx"))

        result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_file_not_found_error(self, mock_win32com, execution_context):
        """Test error when file not found."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import WordOpenNode

        node = WordOpenNode(node_id="test_fnf", config={"create_if_missing": False})
        node.set_input_value("file_path", "C:\\nonexistent\\file.docx")

        with pytest.raises(FileNotFoundError, match="Word file not found"):
            await node.execute(execution_context)

    @pytest.mark.asyncio
    async def test_pywin32_not_installed(self, monkeypatch, execution_context):
        """Test error when pywin32 not installed."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import WordOpenNode

        monkeypatch.setattr(
            "casare_rpa.nodes.desktop_nodes.office_nodes.HAS_WIN32COM", False
        )

        node = WordOpenNode(node_id="test_no_win32")
        node.set_input_value("file_path", "test.docx")

        with pytest.raises(RuntimeError, match="pywin32 not installed"):
            await node.execute(execution_context)


class TestWordGetTextNode:
    """Tests for WordGetTextNode."""

    @pytest.mark.asyncio
    async def test_get_text_success(self, mock_win32com, execution_context):
        """Test getting document text."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import WordGetTextNode

        document = MockWordDocument()
        document._text = "Hello World Document"
        document._word_count = 3

        node = WordGetTextNode(node_id="test_text")
        node.set_input_value("document", document)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["word_count"] == 3
        assert node.get_output_value("text") == "Hello World Document"

    @pytest.mark.asyncio
    async def test_get_text_empty_document(self, mock_win32com, execution_context):
        """Test getting text from empty document."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import WordGetTextNode

        document = MockWordDocument()
        document._text = ""
        document._word_count = 0

        node = WordGetTextNode(node_id="test_empty")
        node.set_input_value("document", document)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["word_count"] == 0

    @pytest.mark.asyncio
    async def test_get_text_missing_document(self, mock_win32com, execution_context):
        """Test error when document not provided."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import WordGetTextNode

        node = WordGetTextNode(node_id="test_no_doc")

        with pytest.raises(ValueError, match="Document is required"):
            await node.execute(execution_context)

    @pytest.mark.asyncio
    async def test_get_text_output_ports(self, mock_win32com, execution_context):
        """Test output port values are set correctly."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import WordGetTextNode

        document = MockWordDocument()
        document._text = "Test content"
        document._word_count = 2

        node = WordGetTextNode(node_id="test_ports")
        node.set_input_value("document", document)

        await node.execute(execution_context)

        assert node.get_output_value("text") == "Test content"
        assert node.get_output_value("word_count") == 2
        assert node.get_output_value("success") is True


class TestWordReplaceTextNode:
    """Tests for WordReplaceTextNode."""

    @pytest.mark.asyncio
    async def test_replace_text_success(self, mock_win32com, execution_context):
        """Test finding and replacing text."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import WordReplaceTextNode

        document = MockWordDocument()
        document._text = "Hello World"

        node = WordReplaceTextNode(node_id="test_replace")
        node.set_input_value("document", document)
        node.set_input_value("find_text", "World")
        node.set_input_value("replace_text", "Universe")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["replacements"] == 1

    @pytest.mark.asyncio
    async def test_replace_text_not_found(self, mock_win32com, execution_context):
        """Test replacement when text not found."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import WordReplaceTextNode

        document = MockWordDocument()
        document._text = "Hello World"

        node = WordReplaceTextNode(node_id="test_notfound")
        node.set_input_value("document", document)
        node.set_input_value("find_text", "XYZ")
        node.set_input_value("replace_text", "ABC")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["replacements"] == 0

    @pytest.mark.asyncio
    async def test_replace_text_missing_document(
        self, mock_win32com, execution_context
    ):
        """Test error when document not provided."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import WordReplaceTextNode

        node = WordReplaceTextNode(node_id="test_no_doc")
        node.set_input_value("find_text", "test")
        node.set_input_value("replace_text", "replaced")

        with pytest.raises(ValueError, match="Document is required"):
            await node.execute(execution_context)

    @pytest.mark.asyncio
    async def test_replace_text_missing_find_text(
        self, mock_win32com, execution_context
    ):
        """Test error when find_text not provided."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import WordReplaceTextNode

        document = MockWordDocument()

        node = WordReplaceTextNode(node_id="test_no_find")
        node.set_input_value("document", document)
        node.set_input_value("replace_text", "replaced")

        with pytest.raises(ValueError, match="Find text is required"):
            await node.execute(execution_context)

    @pytest.mark.asyncio
    async def test_replace_text_case_sensitive(self, mock_win32com, execution_context):
        """Test case-sensitive replacement."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import WordReplaceTextNode

        document = MockWordDocument()
        document._text = "Hello WORLD"

        node = WordReplaceTextNode(node_id="test_case", config={"match_case": True})
        node.set_input_value("document", document)
        node.set_input_value("find_text", "world")
        node.set_input_value("replace_text", "universe")

        result = await node.execute(execution_context)

        # Case sensitive, so "world" won't match "WORLD"
        assert result["success"] is True


class TestWordCloseNode:
    """Tests for WordCloseNode."""

    @pytest.mark.asyncio
    async def test_close_with_save(self, mock_win32com, execution_context):
        """Test closing document with save."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import WordCloseNode

        document = MockWordDocument()
        app = mock_win32com["word"]

        node = WordCloseNode(node_id="test_save", config={"save": True})
        node.set_input_value("document", document)
        node.set_input_value("app", app)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert document._saved is True

    @pytest.mark.asyncio
    async def test_close_without_save(self, mock_win32com, execution_context):
        """Test closing document without save."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import WordCloseNode

        document = MockWordDocument()
        app = mock_win32com["word"]

        node = WordCloseNode(node_id="test_nosave", config={"save": False})
        node.set_input_value("document", document)
        node.set_input_value("app", app)

        result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_close_and_quit_app(self, mock_win32com, execution_context):
        """Test closing document and quitting Word."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import WordCloseNode

        document = MockWordDocument()
        app = mock_win32com["word"]

        node = WordCloseNode(
            node_id="test_quit", config={"save": False, "quit_app": True}
        )
        node.set_input_value("document", document)
        node.set_input_value("app", app)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert app._quit is True

    @pytest.mark.asyncio
    async def test_close_keep_app_open(self, mock_win32com, execution_context):
        """Test closing document but keeping Word open."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import WordCloseNode

        document = MockWordDocument()
        app = mock_win32com["word"]

        node = WordCloseNode(
            node_id="test_keep", config={"save": False, "quit_app": False}
        )
        node.set_input_value("document", document)
        node.set_input_value("app", app)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert app._quit is False


# =============================================================================
# Outlook Node Tests
# =============================================================================


class TestOutlookSendEmailNode:
    """Tests for OutlookSendEmailNode."""

    @pytest.mark.asyncio
    async def test_send_email_success(self, mock_win32com, execution_context):
        """Test sending email successfully."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookSendEmailNode

        node = OutlookSendEmailNode(node_id="test_send")
        node.set_input_value("to", "recipient@example.com")
        node.set_input_value("subject", "Test Subject")
        node.set_input_value("body", "Test body content")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["to"] == "recipient@example.com"
        assert result["subject"] == "Test Subject"

        mail_items = mock_win32com["outlook"]._mail_items
        assert len(mail_items) == 1
        assert mail_items[0].To == "recipient@example.com"
        assert mail_items[0]._sent is True

    @pytest.mark.asyncio
    async def test_send_email_with_cc_bcc(self, mock_win32com, execution_context):
        """Test sending email with CC and BCC."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookSendEmailNode

        node = OutlookSendEmailNode(node_id="test_cc")
        node.set_input_value("to", "to@example.com")
        node.set_input_value("cc", "cc@example.com")
        node.set_input_value("bcc", "bcc@example.com")
        node.set_input_value("subject", "CC Test")
        node.set_input_value("body", "Body")

        result = await node.execute(execution_context)

        assert result["success"] is True
        mail = mock_win32com["outlook"]._mail_items[0]
        assert mail.CC == "cc@example.com"
        assert mail.BCC == "bcc@example.com"

    @pytest.mark.asyncio
    async def test_send_email_html_body(self, mock_win32com, execution_context):
        """Test sending email with HTML body."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookSendEmailNode

        node = OutlookSendEmailNode(node_id="test_html", config={"html_body": True})
        node.set_input_value("to", "to@example.com")
        node.set_input_value("body", "<h1>HTML Content</h1>")

        result = await node.execute(execution_context)

        assert result["success"] is True
        mail = mock_win32com["outlook"]._mail_items[0]
        assert mail.HTMLBody == "<h1>HTML Content</h1>"

    @pytest.mark.asyncio
    async def test_send_email_with_attachment(self, mock_win32com, execution_context):
        """Test sending email with attachment."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookSendEmailNode

        node = OutlookSendEmailNode(node_id="test_attach")
        node.set_input_value("to", "to@example.com")
        node.set_input_value("attachments", "C:\\file.pdf")

        result = await node.execute(execution_context)

        assert result["success"] is True
        mail = mock_win32com["outlook"]._mail_items[0]
        assert "C:\\file.pdf" in mail.Attachments._items

    @pytest.mark.asyncio
    async def test_send_email_with_multiple_attachments(
        self, mock_win32com, execution_context
    ):
        """Test sending email with multiple attachments."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookSendEmailNode

        node = OutlookSendEmailNode(node_id="test_multi_attach")
        node.set_input_value("to", "to@example.com")
        node.set_input_value("attachments", ["file1.pdf", "file2.docx"])

        result = await node.execute(execution_context)

        assert result["success"] is True
        mail = mock_win32com["outlook"]._mail_items[0]
        assert len(mail.Attachments._items) == 2

    @pytest.mark.asyncio
    async def test_send_email_missing_recipient(self, mock_win32com, execution_context):
        """Test error when recipient not provided."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookSendEmailNode

        node = OutlookSendEmailNode(node_id="test_no_to")
        node.set_input_value("subject", "Subject")
        node.set_input_value("body", "Body")

        with pytest.raises(ValueError, match="Recipient is required"):
            await node.execute(execution_context)

    @pytest.mark.asyncio
    async def test_send_email_pywin32_not_installed(
        self, monkeypatch, execution_context
    ):
        """Test error when pywin32 not installed."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookSendEmailNode

        monkeypatch.setattr(
            "casare_rpa.nodes.desktop_nodes.office_nodes.HAS_WIN32COM", False
        )

        node = OutlookSendEmailNode(node_id="test_no_win32")
        node.set_input_value("to", "to@example.com")

        with pytest.raises(RuntimeError, match="pywin32 not installed"):
            await node.execute(execution_context)


class TestOutlookReadEmailsNode:
    """Tests for OutlookReadEmailsNode."""

    @pytest.mark.asyncio
    async def test_read_emails_success(self, mock_win32com, execution_context):
        """Test reading emails from inbox."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookReadEmailsNode

        messages = [
            MockOutlookMessage("Subject 1", "sender1@example.com"),
            MockOutlookMessage("Subject 2", "sender2@example.com"),
        ]
        mock_win32com["outlook"]._namespace._inbox = MockOutlookFolder(messages)

        node = OutlookReadEmailsNode(node_id="test_read", config={"count": 10})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["count"] == 2
        assert node.get_output_value("count") == 2
        emails = node.get_output_value("emails")
        assert len(emails) == 2
        assert emails[0]["subject"] == "Subject 1"

    @pytest.mark.asyncio
    async def test_read_emails_with_limit(self, mock_win32com, execution_context):
        """Test reading limited number of emails."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookReadEmailsNode

        messages = [MockOutlookMessage(f"Subject {i}") for i in range(20)]
        mock_win32com["outlook"]._namespace._inbox = MockOutlookFolder(messages)

        node = OutlookReadEmailsNode(node_id="test_limit", config={"count": 5})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["count"] == 5

    @pytest.mark.asyncio
    async def test_read_emails_unread_only(self, mock_win32com, execution_context):
        """Test reading only unread emails."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookReadEmailsNode

        messages = [
            MockOutlookMessage("Read", unread=False),
            MockOutlookMessage("Unread 1", unread=True),
            MockOutlookMessage("Unread 2", unread=True),
        ]
        mock_win32com["outlook"]._namespace._inbox = MockOutlookFolder(messages)

        node = OutlookReadEmailsNode(
            node_id="test_unread", config={"unread_only": True, "count": 10}
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_read_emails_empty_inbox(self, mock_win32com, execution_context):
        """Test reading from empty inbox."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookReadEmailsNode

        mock_win32com["outlook"]._namespace._inbox = MockOutlookFolder([])

        node = OutlookReadEmailsNode(node_id="test_empty")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["count"] == 0

    @pytest.mark.asyncio
    async def test_read_emails_email_fields(self, mock_win32com, execution_context):
        """Test that email dictionaries contain expected fields."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookReadEmailsNode

        messages = [MockOutlookMessage("Test", "test@example.com", "Body text")]
        mock_win32com["outlook"]._namespace._inbox = MockOutlookFolder(messages)

        node = OutlookReadEmailsNode(node_id="test_fields")

        result = await node.execute(execution_context)

        assert result["success"] is True
        email = node.get_output_value("emails")[0]
        assert "subject" in email
        assert "sender" in email
        assert "sender_name" in email
        assert "received" in email
        assert "body" in email
        assert "unread" in email
        assert "has_attachments" in email

    @pytest.mark.asyncio
    async def test_read_emails_pywin32_not_installed(
        self, monkeypatch, execution_context
    ):
        """Test error when pywin32 not installed."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookReadEmailsNode

        monkeypatch.setattr(
            "casare_rpa.nodes.desktop_nodes.office_nodes.HAS_WIN32COM", False
        )

        node = OutlookReadEmailsNode(node_id="test_no_win32")

        with pytest.raises(RuntimeError, match="pywin32 not installed"):
            await node.execute(execution_context)


class TestOutlookGetInboxCountNode:
    """Tests for OutlookGetInboxCountNode."""

    @pytest.mark.asyncio
    async def test_get_inbox_count_success(self, mock_win32com, execution_context):
        """Test getting inbox email count."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookGetInboxCountNode

        messages = [
            MockOutlookMessage(unread=True),
            MockOutlookMessage(unread=True),
            MockOutlookMessage(unread=False),
        ]
        mock_win32com["outlook"]._namespace._inbox = MockOutlookFolder(messages)

        node = OutlookGetInboxCountNode(node_id="test_count")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["total_count"] == 3
        assert result["unread_count"] == 2

    @pytest.mark.asyncio
    async def test_get_inbox_count_empty(self, mock_win32com, execution_context):
        """Test getting count from empty inbox."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookGetInboxCountNode

        mock_win32com["outlook"]._namespace._inbox = MockOutlookFolder([])

        node = OutlookGetInboxCountNode(node_id="test_empty")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["total_count"] == 0
        assert result["unread_count"] == 0

    @pytest.mark.asyncio
    async def test_get_inbox_count_all_read(self, mock_win32com, execution_context):
        """Test getting count when all emails are read."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookGetInboxCountNode

        messages = [MockOutlookMessage(unread=False) for _ in range(5)]
        mock_win32com["outlook"]._namespace._inbox = MockOutlookFolder(messages)

        node = OutlookGetInboxCountNode(node_id="test_all_read")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["total_count"] == 5
        assert result["unread_count"] == 0

    @pytest.mark.asyncio
    async def test_get_inbox_count_output_ports(self, mock_win32com, execution_context):
        """Test that output ports are set correctly."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookGetInboxCountNode

        messages = [MockOutlookMessage(unread=True)]
        mock_win32com["outlook"]._namespace._inbox = MockOutlookFolder(messages)

        node = OutlookGetInboxCountNode(node_id="test_ports")

        await node.execute(execution_context)

        assert node.get_output_value("total_count") == 1
        assert node.get_output_value("unread_count") == 1
        assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_get_inbox_count_pywin32_not_installed(
        self, monkeypatch, execution_context
    ):
        """Test error when pywin32 not installed."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookGetInboxCountNode

        monkeypatch.setattr(
            "casare_rpa.nodes.desktop_nodes.office_nodes.HAS_WIN32COM", False
        )

        node = OutlookGetInboxCountNode(node_id="test_no_win32")

        with pytest.raises(RuntimeError, match="pywin32 not installed"):
            await node.execute(execution_context)

    @pytest.mark.asyncio
    async def test_get_inbox_count_large_inbox(self, mock_win32com, execution_context):
        """Test getting count from large inbox."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookGetInboxCountNode

        messages = [MockOutlookMessage(unread=i % 3 == 0) for i in range(1000)]
        mock_win32com["outlook"]._namespace._inbox = MockOutlookFolder(messages)

        node = OutlookGetInboxCountNode(node_id="test_large")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["total_count"] == 1000
        # Every 3rd message (i % 3 == 0) is unread: 0, 3, 6, ... 999
        assert result["unread_count"] == 334  # 1000 // 3 + 1


# =============================================================================
# Node Configuration Tests
# =============================================================================


class TestNodeConfiguration:
    """Test node configuration and defaults."""

    def test_excel_open_default_config(self):
        """Test ExcelOpenNode default configuration."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelOpenNode

        node = ExcelOpenNode(node_id="test")

        assert node.config.get("visible") is False
        assert node.config.get("create_if_missing") is False

    def test_excel_read_cell_default_config(self):
        """Test ExcelReadCellNode default configuration."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelReadCellNode

        node = ExcelReadCellNode(node_id="test")

        assert node.config.get("sheet") == 1

    def test_excel_close_default_config(self):
        """Test ExcelCloseNode default configuration."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelCloseNode

        node = ExcelCloseNode(node_id="test")

        assert node.config.get("save") is True
        assert node.config.get("quit_app") is True

    def test_word_open_default_config(self):
        """Test WordOpenNode default configuration."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import WordOpenNode

        node = WordOpenNode(node_id="test")

        assert node.config.get("visible") is False
        assert node.config.get("create_if_missing") is False

    def test_word_replace_default_config(self):
        """Test WordReplaceTextNode default configuration."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import WordReplaceTextNode

        node = WordReplaceTextNode(node_id="test")

        assert node.config.get("match_case") is False
        assert node.config.get("replace_all") is True

    def test_outlook_send_default_config(self):
        """Test OutlookSendEmailNode default configuration."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookSendEmailNode

        node = OutlookSendEmailNode(node_id="test")

        assert node.config.get("html_body") is False

    def test_outlook_read_default_config(self):
        """Test OutlookReadEmailsNode default configuration."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookReadEmailsNode

        node = OutlookReadEmailsNode(node_id="test")

        assert node.config.get("folder") == "Inbox"
        assert node.config.get("count") == 10
        assert node.config.get("unread_only") is False


# =============================================================================
# Node Metadata Tests
# =============================================================================


class TestNodeMetadata:
    """Test node metadata and type information."""

    def test_excel_open_metadata(self):
        """Test ExcelOpenNode metadata."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelOpenNode

        node = ExcelOpenNode(node_id="test")
        assert node.node_type == "ExcelOpenNode"
        assert node.name == "Excel Open"

    def test_excel_read_cell_metadata(self):
        """Test ExcelReadCellNode metadata."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelReadCellNode

        node = ExcelReadCellNode(node_id="test")
        assert node.node_type == "ExcelReadCellNode"
        assert node.name == "Excel Read Cell"

    def test_excel_write_cell_metadata(self):
        """Test ExcelWriteCellNode metadata."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelWriteCellNode

        node = ExcelWriteCellNode(node_id="test")
        assert node.node_type == "ExcelWriteCellNode"
        assert node.name == "Excel Write Cell"

    def test_word_open_metadata(self):
        """Test WordOpenNode metadata."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import WordOpenNode

        node = WordOpenNode(node_id="test")
        assert node.node_type == "WordOpenNode"
        assert node.name == "Word Open"

    def test_outlook_send_metadata(self):
        """Test OutlookSendEmailNode metadata."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookSendEmailNode

        node = OutlookSendEmailNode(node_id="test")
        assert node.node_type == "OutlookSendEmailNode"
        assert node.name == "Outlook Send Email"


# =============================================================================
# ExecutionResult Compliance Tests
# =============================================================================


class TestExecutionResultCompliance:
    """Verify all nodes return proper ExecutionResult dictionaries."""

    @pytest.mark.asyncio
    async def test_excel_open_returns_expected_keys(
        self, mock_win32com, execution_context, tmp_path
    ):
        """ExcelOpenNode returns all required keys."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import ExcelOpenNode

        test_file = tmp_path / "test.xlsx"
        test_file.write_bytes(b"dummy")

        node = ExcelOpenNode(node_id="test")
        node.set_input_value("file_path", str(test_file))

        result = await node.execute(execution_context)

        assert isinstance(result, dict)
        assert "success" in result
        assert "file_path" in result

    @pytest.mark.asyncio
    async def test_word_get_text_returns_expected_keys(
        self, mock_win32com, execution_context
    ):
        """WordGetTextNode returns all required keys."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import WordGetTextNode

        document = MockWordDocument()
        node = WordGetTextNode(node_id="test")
        node.set_input_value("document", document)

        result = await node.execute(execution_context)

        assert isinstance(result, dict)
        assert "success" in result
        assert "word_count" in result

    @pytest.mark.asyncio
    async def test_outlook_send_returns_expected_keys(
        self, mock_win32com, execution_context
    ):
        """OutlookSendEmailNode returns all required keys."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookSendEmailNode

        node = OutlookSendEmailNode(node_id="test")
        node.set_input_value("to", "test@example.com")

        result = await node.execute(execution_context)

        assert isinstance(result, dict)
        assert "success" in result
        assert "to" in result
        assert "subject" in result

    @pytest.mark.asyncio
    async def test_outlook_read_returns_expected_keys(
        self, mock_win32com, execution_context
    ):
        """OutlookReadEmailsNode returns all required keys."""
        from casare_rpa.nodes.desktop_nodes.office_nodes import OutlookReadEmailsNode

        mock_win32com["outlook"]._namespace._inbox = MockOutlookFolder([])
        node = OutlookReadEmailsNode(node_id="test")

        result = await node.execute(execution_context)

        assert isinstance(result, dict)
        assert "success" in result
        assert "count" in result
        assert "folder" in result
