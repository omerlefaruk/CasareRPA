"""
Office Automation Nodes for CasareRPA

Provides nodes for automating Microsoft Office applications:
- Excel: Open, Read, Write, GetRange, Close
- Word: Open, GetText, ReplaceText, Close
- Outlook: SendEmail, ReadEmail, GetInboxCount
"""

from typing import Any, Dict
from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType, NodeStatus


# Try to import win32com for Office automation
try:
    import win32com.client

    HAS_WIN32COM = True
except ImportError:
    HAS_WIN32COM = False
    logger.debug("win32com not available - install pywin32 for Office automation")


# ============================================================================
# Excel Nodes
# ============================================================================


@node_schema(
    PropertyDef(
        "file_path",
        PropertyType.FILE_PATH,
        default="",
        required=True,
        label="File Path",
        placeholder="C:\\path\\to\\file.xlsx",
        tooltip="Path to Excel file (.xlsx, .xls)",
        essential=True,
    ),
    PropertyDef(
        "show_excel",
        PropertyType.BOOLEAN,
        default=False,
        label="Show Excel",
        tooltip="Show Excel window while working",
    ),
    PropertyDef(
        "read_only",
        PropertyType.BOOLEAN,
        default=False,
        label="Read Only",
        tooltip="Open in read-only mode (helps with Protected View)",
    ),
    PropertyDef(
        "create_if_missing",
        PropertyType.BOOLEAN,
        default=False,
        label="Create If Missing",
        tooltip="Create new file if not found",
    ),
)
@executable_node
class ExcelOpenNode(BaseNode):
    """
    Node to open an Excel workbook.

    Inputs:
        - file_path: Path to Excel file (.xlsx, .xls)

    Config:
        - file_path: Path to Excel file (can be set via properties panel)
        - visible: Show Excel window (default: False)
        - read_only: Open in read-only mode (default: False, helps with Protected View)
        - create_if_missing: Create new file if not found

    Outputs:
        - workbook: Excel workbook object
        - app: Excel application object
        - success: Whether operation succeeded
    """

    # @category: desktop
    # @requires: pywin32
    # @ports: file_path -> workbook, app, success

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Excel Open",
    ):
        default_config = {
            "file_path": "",  # Can be set via properties panel or input port
            "visible": False,
            "read_only": False,
            "create_if_missing": False,
        }
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "ExcelOpenNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("file_path", DataType.STRING, "Excel file path")
        self.add_output_port("workbook", DataType.ANY, "Workbook object")
        self.add_output_port("app", DataType.ANY, "Excel application")
        self.add_output_port("success", DataType.BOOLEAN, "Operation succeeded")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute Excel open operation"""
        if not HAS_WIN32COM:
            raise RuntimeError(
                "pywin32 not installed. Install with: pip install pywin32"
            )

        # Use get_parameter to check both port value and config (properties panel)
        file_path = self.get_parameter("file_path")
        # Check multiple possible config keys for visibility
        visible = (
            self.config.get("visible", False)
            or self.config.get("show_window", False)
            or self.config.get("show_excel", False)
        )
        read_only = self.config.get("read_only", False)
        create_if_missing = self.config.get("create_if_missing", False)

        # Resolve {{variable}} patterns
        if hasattr(context, "resolve_value") and file_path:
            file_path = context.resolve_value(file_path)

        try:
            import os

            excel = win32com.client.Dispatch("Excel.Application")
            excel.Visible = visible
            excel.DisplayAlerts = False

            if file_path and os.path.exists(file_path):
                # Open with read_only option - also helps bypass Protected View
                # Parameters: Filename, UpdateLinks, ReadOnly
                workbook = excel.Workbooks.Open(
                    os.path.abspath(file_path),
                    UpdateLinks=0,  # Don't update links
                    ReadOnly=read_only,
                )
            elif create_if_missing or not file_path:
                workbook = excel.Workbooks.Add()
                if file_path:
                    workbook.SaveAs(os.path.abspath(file_path))
            else:
                raise FileNotFoundError(f"Excel file not found: {file_path}")

            self.set_output_value("workbook", workbook)
            self.set_output_value("app", excel)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            logger.info(f"Opened Excel workbook: {file_path}")
            return {"success": True, "file_path": file_path}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to open Excel: {e}")
            raise


@node_schema(
    PropertyDef(
        "sheet",
        PropertyType.STRING,
        default="1",
        label="Sheet",
        placeholder="1 or Sheet1",
        tooltip="Sheet name or index (1-based)",
        essential=True,
    ),
    PropertyDef(
        "cell",
        PropertyType.STRING,
        default="",
        required=True,
        label="Cell",
        placeholder="A1",
        tooltip="Cell reference (e.g., A1, B2)",
        essential=True,
    ),
)
@executable_node
class ExcelReadCellNode(BaseNode):
    """
    Node to read a cell value from Excel.

    Inputs:
        - workbook: Excel workbook object
        - sheet: Sheet name or index (default: 1)
        - cell: Cell reference (e.g., "A1")

    Outputs:
        - value: Cell value
        - success: Whether operation succeeded
    """

    # @category: desktop
    # @requires: pywin32
    # @ports: workbook, sheet, cell -> value, success

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Excel Read Cell",
    ):
        default_config = {"sheet": 1}
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "ExcelReadCellNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("workbook", DataType.ANY, "Workbook object")
        self.add_input_port("sheet", DataType.ANY, "Sheet name or index")
        self.add_input_port("cell", DataType.STRING, "Cell reference (e.g., A1)")
        self.add_output_port("value", DataType.ANY, "Cell value")
        self.add_output_port("success", DataType.BOOLEAN, "Operation succeeded")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute Excel read cell operation"""
        workbook = self.get_input_value("workbook")
        sheet = self.get_input_value("sheet") or self.config.get("sheet", 1)
        cell = self.get_input_value("cell")

        # Resolve {{variable}} patterns
        if hasattr(context, "resolve_value"):
            if isinstance(sheet, str):
                sheet = context.resolve_value(sheet)
            if cell:
                cell = context.resolve_value(cell)

        if not workbook:
            raise ValueError("Workbook is required")
        if not cell:
            raise ValueError("Cell reference is required")

        try:
            # Convert numeric string to int for index-based access
            if isinstance(sheet, str) and sheet.isdigit():
                sheet = int(sheet)

            ws = workbook.Sheets(sheet)
            value = ws.Range(cell).Value

            self.set_output_value("value", value)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            logger.info(f"Read cell {cell}: {value}")
            return {"success": True, "cell": cell, "value": value}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to read cell: {e}")
            raise


@node_schema(
    PropertyDef(
        "sheet",
        PropertyType.STRING,
        default="1",
        label="Sheet",
        placeholder="1 or Sheet1",
        tooltip="Sheet name or index (1-based)",
        essential=True,
    ),
    PropertyDef(
        "cell",
        PropertyType.STRING,
        default="",
        required=True,
        label="Cell",
        placeholder="A1",
        tooltip="Cell reference (e.g., A1, B2)",
        essential=True,
    ),
    PropertyDef(
        "value",
        PropertyType.STRING,
        default="",
        label="Value",
        placeholder="Value to write",
        tooltip="Value to write to the cell",
    ),
)
@executable_node
class ExcelWriteCellNode(BaseNode):
    """
    Node to write a value to an Excel cell.

    Inputs:
        - workbook: Excel workbook object
        - sheet: Sheet name or index (default: 1)
        - cell: Cell reference (e.g., "A1")
        - value: Value to write

    Outputs:
        - success: Whether operation succeeded
    """

    # @category: desktop
    # @requires: pywin32
    # @ports: workbook, sheet, cell, value -> success

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Excel Write Cell",
    ):
        default_config = {"sheet": 1}
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "ExcelWriteCellNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("workbook", DataType.ANY, "Workbook object")
        self.add_input_port("sheet", DataType.ANY, "Sheet name or index")
        self.add_input_port("cell", DataType.STRING, "Cell reference (e.g., A1)")
        self.add_input_port("value", DataType.ANY, "Value to write")
        self.add_output_port("success", DataType.BOOLEAN, "Operation succeeded")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute Excel write cell operation"""
        workbook = self.get_input_value("workbook")
        sheet = self.get_input_value("sheet") or self.config.get("sheet", 1)
        cell = self.get_input_value("cell")
        value = self.get_input_value("value")

        # Resolve {{variable}} patterns
        if hasattr(context, "resolve_value"):
            if isinstance(sheet, str):
                sheet = context.resolve_value(sheet)
            if cell:
                cell = context.resolve_value(cell)

        if not workbook:
            raise ValueError("Workbook is required")
        if not cell:
            raise ValueError("Cell reference is required")

        try:
            # Convert numeric string to int for index-based access
            if isinstance(sheet, str) and sheet.isdigit():
                sheet = int(sheet)

            ws = workbook.Sheets(sheet)
            ws.Range(cell).Value = value

            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            logger.info(f"Wrote to cell {cell}: {value}")
            return {"success": True, "cell": cell, "value": value}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to write cell: {e}")
            raise


@node_schema(
    PropertyDef(
        "sheet",
        PropertyType.STRING,
        default="1",
        label="Sheet",
        placeholder="1 or Sheet1",
        tooltip="Sheet name or index (1-based)",
        essential=True,
    ),
    PropertyDef(
        "range",
        PropertyType.STRING,
        default="",
        required=True,
        label="Range",
        placeholder="A1:G11",
        tooltip="Range reference (e.g., A1:C10, A:C for entire columns)",
        essential=True,
    ),
)
@executable_node
class ExcelGetRangeNode(BaseNode):
    """
    Node to read a range of cells from Excel.

    Inputs:
        - workbook: Excel workbook object
        - sheet: Sheet name or index
        - range: Range reference (e.g., "A1:C10")

    Outputs:
        - data: 2D list of values
        - rows: Number of rows
        - columns: Number of columns
        - success: Whether operation succeeded
    """

    # @category: desktop
    # @requires: pywin32
    # @ports: workbook, sheet, range -> data, rows, columns, success

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Excel Get Range",
    ):
        default_config = {"sheet": 1, "range": ""}
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "ExcelGetRangeNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("workbook", DataType.ANY, "Workbook object")
        self.add_input_port("sheet", DataType.ANY, "Sheet name or index")
        self.add_input_port("range", DataType.STRING, "Range reference (e.g., A1:C10)")
        self.add_output_port("data", DataType.ANY, "2D list of values")
        self.add_output_port("rows", DataType.INTEGER, "Number of rows")
        self.add_output_port("columns", DataType.INTEGER, "Number of columns")
        self.add_output_port("success", DataType.BOOLEAN, "Operation succeeded")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute Excel get range operation"""
        workbook = self.get_input_value("workbook")
        sheet = self.get_input_value("sheet") or self.config.get("sheet", 1)
        range_ref = self.get_parameter("range")  # Check both port and config

        # Resolve {{variable}} patterns
        if hasattr(context, "resolve_value"):
            if isinstance(sheet, str):
                sheet = context.resolve_value(sheet)
            if range_ref:
                range_ref = context.resolve_value(range_ref)

        if not workbook:
            raise ValueError("Workbook is required")
        if not range_ref:
            raise ValueError("Range reference is required")

        try:
            # Convert numeric string to int for index-based access
            if isinstance(sheet, str) and sheet.isdigit():
                sheet = int(sheet)

            ws = workbook.Sheets(sheet)
            rng = ws.Range(range_ref)
            data = rng.Value

            # Convert to list if single row/column
            if data is None:
                data = [[]]
            elif not isinstance(data, tuple):
                data = [[data]]
            else:
                data = [list(row) if isinstance(row, tuple) else [row] for row in data]

            rows = len(data)
            cols = len(data[0]) if data else 0

            self.set_output_value("data", data)
            self.set_output_value("rows", rows)
            self.set_output_value("columns", cols)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            logger.info(f"Read range {range_ref}: {rows}x{cols}")
            return {"success": True, "range": range_ref, "rows": rows, "columns": cols}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to get range: {e}")
            raise


@node_schema(
    PropertyDef(
        "save",
        PropertyType.BOOLEAN,
        default=True,
        label="Save Before Close",
        tooltip="Save the workbook before closing",
        essential=True,
    ),
    PropertyDef(
        "quit_app",
        PropertyType.BOOLEAN,
        default=True,
        label="Quit Excel",
        tooltip="Quit the Excel application after closing workbook",
    ),
)
@executable_node
class ExcelCloseNode(BaseNode):
    """
    Node to close an Excel workbook.

    Inputs:
        - workbook: Excel workbook object
        - app: Excel application (optional)

    Config:
        - save: Save before closing (default: True)
        - quit_app: Quit Excel application (default: True)

    Outputs:
        - success: Whether operation succeeded
    """

    # @category: desktop
    # @requires: pywin32
    # @ports: workbook, app -> success

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Excel Close",
    ):
        default_config = {"save": True, "quit_app": True}
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "ExcelCloseNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("workbook", DataType.ANY, "Workbook object", required=True)
        self.add_input_port("app", DataType.ANY, "Excel application", required=False)
        self.add_output_port("success", DataType.BOOLEAN, "Operation succeeded")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute Excel close operation"""
        workbook = self.get_input_value("workbook")
        app = self.get_input_value("app")
        save = self.config.get("save", True)
        quit_app = self.config.get("quit_app", True)

        try:
            if workbook:
                if save:
                    workbook.Save()
                workbook.Close(SaveChanges=save)

            if quit_app and app:
                app.Quit()

            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            logger.info("Closed Excel workbook")
            return {"success": True}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to close Excel: {e}")
            raise


# ============================================================================
# Word Nodes
# ============================================================================


@executable_node
class WordOpenNode(BaseNode):
    """
    Node to open a Word document.

    Inputs:
        - file_path: Path to Word file (.docx, .doc)

    Config:
        - visible: Show Word window (default: False)
        - create_if_missing: Create new document if not found

    Outputs:
        - document: Word document object
        - app: Word application
        - success: Whether operation succeeded
    """

    # @category: desktop
    # @requires: pywin32
    # @ports: file_path -> document, app, success

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Word Open",
    ):
        default_config = {"visible": False, "create_if_missing": False}
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "WordOpenNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("file_path", DataType.STRING, "Word file path")
        self.add_output_port("document", DataType.ANY, "Document object")
        self.add_output_port("app", DataType.ANY, "Word application")
        self.add_output_port("success", DataType.BOOLEAN, "Operation succeeded")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute Word open operation"""
        if not HAS_WIN32COM:
            raise RuntimeError(
                "pywin32 not installed. Install with: pip install pywin32"
            )

        # Use get_parameter to check both port value and config (properties panel)
        file_path = self.get_parameter("file_path")
        visible = self.config.get("visible", False)
        create_if_missing = self.config.get("create_if_missing", False)

        # Resolve {{variable}} patterns
        if hasattr(context, "resolve_value") and file_path:
            file_path = context.resolve_value(file_path)

        try:
            import os

            word = win32com.client.Dispatch("Word.Application")
            word.Visible = visible

            if file_path and os.path.exists(file_path):
                document = word.Documents.Open(os.path.abspath(file_path))
            elif create_if_missing or not file_path:
                document = word.Documents.Add()
                if file_path:
                    document.SaveAs(os.path.abspath(file_path))
            else:
                raise FileNotFoundError(f"Word file not found: {file_path}")

            self.set_output_value("document", document)
            self.set_output_value("app", word)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            logger.info(f"Opened Word document: {file_path}")
            return {"success": True, "file_path": file_path}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to open Word: {e}")
            raise


@executable_node
class WordGetTextNode(BaseNode):
    """
    Node to get text content from a Word document.

    Inputs:
        - document: Word document object

    Outputs:
        - text: Document text content
        - word_count: Number of words
        - success: Whether operation succeeded
    """

    # @category: desktop
    # @requires: pywin32
    # @ports: document -> text, word_count, success

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Word Get Text",
    ):
        super().__init__(node_id, config or {})
        self.name = name
        self.node_type = "WordGetTextNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("document", DataType.ANY, "Document object")
        self.add_output_port("text", DataType.STRING, "Document text")
        self.add_output_port("word_count", DataType.INTEGER, "Word count")
        self.add_output_port("success", DataType.BOOLEAN, "Operation succeeded")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute Word get text operation"""
        document = self.get_input_value("document")

        if not document:
            raise ValueError("Document is required")

        try:
            text = document.Content.Text
            word_count = document.Words.Count

            self.set_output_value("text", text)
            self.set_output_value("word_count", word_count)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            logger.info(f"Got Word text: {word_count} words")
            return {"success": True, "word_count": word_count}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to get Word text: {e}")
            raise


@executable_node
class WordReplaceTextNode(BaseNode):
    """
    Node to find and replace text in a Word document.

    Inputs:
        - document: Word document object
        - find_text: Text to find
        - replace_text: Replacement text

    Config:
        - match_case: Case-sensitive search
        - replace_all: Replace all occurrences

    Outputs:
        - replacements: Number of replacements made
        - success: Whether operation succeeded
    """

    # @category: desktop
    # @requires: pywin32
    # @ports: document, find_text, replace_text -> replacements, success

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Word Replace Text",
    ):
        default_config = {"match_case": False, "replace_all": True}
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "WordReplaceTextNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("document", DataType.ANY, "Document object")
        self.add_input_port("find_text", DataType.STRING, "Text to find")
        self.add_input_port("replace_text", DataType.STRING, "Replacement text")
        self.add_output_port("replacements", DataType.INTEGER, "Number of replacements")
        self.add_output_port("success", DataType.BOOLEAN, "Operation succeeded")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute Word replace text operation"""
        document = self.get_input_value("document")
        find_text = self.get_input_value("find_text")
        replace_text = self.get_input_value("replace_text")
        match_case = self.config.get("match_case", False)
        replace_all = self.config.get("replace_all", True)

        # Resolve {{variable}} patterns
        if hasattr(context, "resolve_value"):
            if find_text:
                find_text = context.resolve_value(find_text)
            if replace_text:
                replace_text = context.resolve_value(replace_text)

        if not document:
            raise ValueError("Document is required")
        if not find_text:
            raise ValueError("Find text is required")

        try:
            find = document.Content.Find
            find.ClearFormatting()
            find.Replacement.ClearFormatting()

            replace_type = 2 if replace_all else 1  # wdReplaceAll or wdReplaceOne

            count = 0
            while find.Execute(
                FindText=find_text,
                MatchCase=match_case,
                ReplaceWith=replace_text,
                Replace=replace_type,
            ):
                count += 1
                if not replace_all:
                    break

            self.set_output_value("replacements", count)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            logger.info(f"Replaced {count} occurrences")
            return {"success": True, "replacements": count}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to replace text: {e}")
            raise


@executable_node
class WordCloseNode(BaseNode):
    """
    Node to close a Word document.

    Inputs:
        - document: Word document object
        - app: Word application (optional)

    Config:
        - save: Save before closing (default: True)
        - quit_app: Quit Word application (default: True)

    Outputs:
        - success: Whether operation succeeded
    """

    # @category: desktop
    # @requires: pywin32
    # @ports: document, app -> success

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Word Close",
    ):
        default_config = {"save": True, "quit_app": True}
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "WordCloseNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("document", DataType.ANY, "Document object")
        self.add_input_port("app", DataType.ANY, "Word application")
        self.add_output_port("success", DataType.BOOLEAN, "Operation succeeded")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute Word close operation"""
        document = self.get_input_value("document")
        app = self.get_input_value("app")
        save = self.config.get("save", True)
        quit_app = self.config.get("quit_app", True)

        try:
            if document:
                if save:
                    document.Save()
                document.Close(SaveChanges=save)

            if quit_app and app:
                app.Quit()

            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            logger.info("Closed Word document")
            return {"success": True}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to close Word: {e}")
            raise


# ============================================================================
# Outlook Nodes
# ============================================================================


@executable_node
class OutlookSendEmailNode(BaseNode):
    """
    Node to send an email via Outlook.

    Inputs:
        - to: Recipient email address(es)
        - subject: Email subject
        - body: Email body
        - cc: CC recipients (optional)
        - bcc: BCC recipients (optional)
        - attachments: List of file paths (optional)

    Config:
        - html_body: Body is HTML format

    Outputs:
        - success: Whether email was sent
    """

    # @category: desktop
    # @requires: pywin32
    # @ports: to, subject, body, cc, bcc, attachments -> success

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Outlook Send Email",
    ):
        default_config = {"html_body": False}
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "OutlookSendEmailNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("to", DataType.STRING, "Recipient(s)")
        self.add_input_port("subject", DataType.STRING, "Subject")
        self.add_input_port("body", DataType.STRING, "Body")
        self.add_input_port("cc", DataType.STRING, "CC recipients")
        self.add_input_port("bcc", DataType.STRING, "BCC recipients")
        self.add_input_port("attachments", DataType.ANY, "Attachment paths")
        self.add_output_port("success", DataType.BOOLEAN, "Email sent")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute Outlook send email operation"""
        if not HAS_WIN32COM:
            raise RuntimeError(
                "pywin32 not installed. Install with: pip install pywin32"
            )

        to = self.get_input_value("to")
        subject = self.get_input_value("subject")
        body = self.get_input_value("body")
        cc = self.get_input_value("cc")
        bcc = self.get_input_value("bcc")
        attachments = self.get_input_value("attachments")
        html_body = self.config.get("html_body", False)

        # Resolve {{variable}} patterns
        if hasattr(context, "resolve_value"):
            if to:
                to = context.resolve_value(to)
            if subject:
                subject = context.resolve_value(subject)
            if body:
                body = context.resolve_value(body)
            if cc:
                cc = context.resolve_value(cc)
            if bcc:
                bcc = context.resolve_value(bcc)

        if not to:
            raise ValueError("Recipient is required")

        try:
            outlook = win32com.client.Dispatch("Outlook.Application")
            mail = outlook.CreateItem(0)  # olMailItem

            mail.To = to
            mail.Subject = subject or ""

            if html_body:
                mail.HTMLBody = body or ""
            else:
                mail.Body = body or ""

            if cc:
                mail.CC = cc
            if bcc:
                mail.BCC = bcc

            if attachments:
                if isinstance(attachments, str):
                    attachments = [attachments]
                for attachment in attachments:
                    mail.Attachments.Add(attachment)

            mail.Send()

            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            logger.info(f"Sent email to: {to}")
            return {"success": True, "to": to, "subject": subject}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to send email: {e}")
            raise


@executable_node
class OutlookReadEmailsNode(BaseNode):
    """
    Node to read emails from Outlook inbox.

    Config:
        - folder: Folder name (default: Inbox)
        - count: Number of emails to read (default: 10)
        - unread_only: Only read unread emails

    Outputs:
        - emails: List of email dictionaries
        - count: Number of emails read
        - success: Whether operation succeeded
    """

    # @category: desktop
    # @requires: pywin32
    # @ports: none -> emails, count, success

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Outlook Read Emails",
    ):
        default_config = {"folder": "Inbox", "count": 10, "unread_only": False}
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "OutlookReadEmailsNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_output_port("emails", DataType.ANY, "List of emails")
        self.add_output_port("count", DataType.INTEGER, "Number of emails")
        self.add_output_port("success", DataType.BOOLEAN, "Operation succeeded")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute Outlook read emails operation"""
        if not HAS_WIN32COM:
            raise RuntimeError(
                "pywin32 not installed. Install with: pip install pywin32"
            )

        folder_name = self.config.get("folder", "Inbox")
        max_count = self.config.get("count", 10)
        unread_only = self.config.get("unread_only", False)

        try:
            outlook = win32com.client.Dispatch("Outlook.Application")
            namespace = outlook.GetNamespace("MAPI")

            # Get folder (6 = olFolderInbox)
            if folder_name.lower() == "inbox":
                folder = namespace.GetDefaultFolder(6)
            else:
                folder = namespace.Folders.Item(1).Folders.Item(folder_name)

            messages = folder.Items
            messages.Sort("[ReceivedTime]", True)  # Sort by received time, descending

            emails = []
            count = 0

            for message in messages:
                if count >= max_count:
                    break

                if unread_only and message.UnRead is False:
                    continue

                email_data = {
                    "subject": message.Subject,
                    "sender": message.SenderEmailAddress,
                    "sender_name": message.SenderName,
                    "received": str(message.ReceivedTime),
                    "body": message.Body[:500]
                    if message.Body
                    else "",  # First 500 chars
                    "unread": message.UnRead,
                    "has_attachments": message.Attachments.Count > 0,
                }
                emails.append(email_data)
                count += 1

            self.set_output_value("emails", emails)
            self.set_output_value("count", count)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            logger.info(f"Read {count} emails from {folder_name}")
            return {"success": True, "count": count, "folder": folder_name}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to read emails: {e}")
            raise


@executable_node
class OutlookGetInboxCountNode(BaseNode):
    """
    Node to get the count of emails in Outlook inbox.

    Config:
        - unread_only: Only count unread emails

    Outputs:
        - total_count: Total email count
        - unread_count: Unread email count
        - success: Whether operation succeeded
    """

    # @category: desktop
    # @requires: pywin32
    # @ports: none -> total_count, unread_count, success

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Outlook Get Inbox Count",
    ):
        default_config = {}
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "OutlookGetInboxCountNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_output_port("total_count", DataType.INTEGER, "Total emails")
        self.add_output_port("unread_count", DataType.INTEGER, "Unread emails")
        self.add_output_port("success", DataType.BOOLEAN, "Operation succeeded")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute Outlook get inbox count operation"""
        if not HAS_WIN32COM:
            raise RuntimeError(
                "pywin32 not installed. Install with: pip install pywin32"
            )

        try:
            outlook = win32com.client.Dispatch("Outlook.Application")
            namespace = outlook.GetNamespace("MAPI")
            inbox = namespace.GetDefaultFolder(6)  # olFolderInbox

            total_count = inbox.Items.Count
            unread_count = inbox.UnReadItemCount

            self.set_output_value("total_count", total_count)
            self.set_output_value("unread_count", unread_count)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            logger.info(f"Inbox: {total_count} total, {unread_count} unread")
            return {
                "success": True,
                "total_count": total_count,
                "unread_count": unread_count,
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to get inbox count: {e}")
            raise
