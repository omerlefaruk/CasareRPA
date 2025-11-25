"""
PDF operation nodes for CasareRPA.

This module provides nodes for PDF operations:
- ReadPDFTextNode: Extract text from PDF
- GetPDFInfoNode: Get PDF metadata and info
- MergePDFsNode: Merge multiple PDFs
- SplitPDFNode: Split PDF into pages
- ExtractPDFPagesNode: Extract specific pages
- PDFToImagesNode: Convert PDF pages to images

Note: These nodes require PyPDF2 and optionally pdf2image for image conversion.
"""

from pathlib import Path
from typing import Any, Optional, List

from ..core.base_node import BaseNode
from ..core.types import NodeStatus, PortType, DataType, ExecutionResult
from ..core.execution_context import ExecutionContext


class ReadPDFTextNode(BaseNode):
    """
    Extract text from a PDF file.

    Config:
        page_separator: Separator between pages (default: newline)
        password: Password for encrypted PDFs (default: None)
        extract_tables: Attempt to extract tables (default: False)
        preserve_layout: Try to preserve text layout (default: False)

    Inputs:
        file_path: Path to PDF file
        start_page: Start page (1-indexed, default: 1)
        end_page: End page (default: all pages)
        password: Password for encrypted PDFs (optional input)

    Outputs:
        text: Extracted text
        page_count: Total number of pages
        pages: List of text per page
        is_encrypted: Whether the PDF is encrypted
        success: Whether extraction succeeded
    """

    def __init__(self, node_id: str, name: str = "Read PDF Text", **kwargs) -> None:
        # Default config with all options
        default_config = {
            "page_separator": "\n\n",
            "password": "",
            "extract_tables": False,
            "preserve_layout": False,
        }
        config = kwargs.get("config", {})
        for key, value in default_config.items():
            if key not in config:
                config[key] = value
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ReadPDFTextNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("start_page", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("end_page", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("password", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("text", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("page_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("pages", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("is_encrypted", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = str(self.get_input_value("file_path", context) or "")
            start_page = self.get_input_value("start_page", context)
            end_page = self.get_input_value("end_page", context)
            page_separator = self.config.get("page_separator", "\n\n")

            # Get password from input or config
            password = self.get_input_value("password", context)
            if password is None:
                password = self.config.get("password", "")

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns in file_path and password
            file_path = context.resolve_value(file_path)
            if password:
                password = context.resolve_value(password)

            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"PDF file not found: {file_path}")

            try:
                from PyPDF2 import PdfReader
            except ImportError:
                raise ImportError("PyPDF2 is required for PDF operations. Install with: pip install PyPDF2")

            reader = PdfReader(path)

            # Handle encrypted PDFs
            is_encrypted = reader.is_encrypted
            self.set_output_value("is_encrypted", is_encrypted)

            if is_encrypted:
                if password:
                    if not reader.decrypt(password):
                        raise ValueError("Invalid password for encrypted PDF")
                else:
                    raise ValueError("PDF is encrypted. Please provide a password.")
            page_count = len(reader.pages)

            # Handle page range
            start_idx = (int(start_page) - 1) if start_page else 0
            end_idx = int(end_page) if end_page else page_count

            start_idx = max(0, min(start_idx, page_count))
            end_idx = max(0, min(end_idx, page_count))

            # Extract text from pages
            pages = []
            for i in range(start_idx, end_idx):
                page_text = reader.pages[i].extract_text() or ""
                pages.append(page_text)

            text = page_separator.join(pages)

            self.set_output_value("text", text)
            self.set_output_value("page_count", page_count)
            self.set_output_value("pages", pages)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"page_count": page_count, "extracted_pages": len(pages)},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("text", "")
            self.set_output_value("page_count", 0)
            self.set_output_value("pages", [])
            self.set_output_value("is_encrypted", False)
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class GetPDFInfoNode(BaseNode):
    """
    Get metadata and information from a PDF file.

    Inputs:
        file_path: Path to PDF file

    Outputs:
        page_count: Number of pages
        title: Document title
        author: Document author
        subject: Document subject
        creator: Creator application
        producer: PDF producer
        creation_date: Creation date
        modification_date: Modification date
        is_encrypted: Whether PDF is encrypted
        success: Whether operation succeeded
    """

    def __init__(self, node_id: str, name: str = "Get PDF Info", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetPDFInfoNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("page_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("title", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("author", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("subject", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("creator", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("producer", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("creation_date", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("modification_date", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("is_encrypted", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = str(self.get_input_value("file_path", context) or "")

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns in file_path
            file_path = context.resolve_value(file_path)

            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"PDF file not found: {file_path}")

            try:
                from PyPDF2 import PdfReader
            except ImportError:
                raise ImportError("PyPDF2 is required for PDF operations")

            reader = PdfReader(path)
            metadata = reader.metadata or {}

            self.set_output_value("page_count", len(reader.pages))
            self.set_output_value("title", str(metadata.get("/Title", "") or ""))
            self.set_output_value("author", str(metadata.get("/Author", "") or ""))
            self.set_output_value("subject", str(metadata.get("/Subject", "") or ""))
            self.set_output_value("creator", str(metadata.get("/Creator", "") or ""))
            self.set_output_value("producer", str(metadata.get("/Producer", "") or ""))
            self.set_output_value("creation_date", str(metadata.get("/CreationDate", "") or ""))
            self.set_output_value("modification_date", str(metadata.get("/ModDate", "") or ""))
            self.set_output_value("is_encrypted", reader.is_encrypted)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"page_count": len(reader.pages)},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class MergePDFsNode(BaseNode):
    """
    Merge multiple PDF files into one.

    Inputs:
        input_files: List of PDF file paths to merge
        output_path: Output file path

    Outputs:
        output_path: Path to merged PDF
        page_count: Total pages in merged PDF
        success: Whether merge succeeded
    """

    def __init__(self, node_id: str, name: str = "Merge PDFs", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "MergePDFsNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("input_files", PortType.INPUT, DataType.LIST)
        self.add_input_port("output_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("output_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("page_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            input_files = self.get_input_value("input_files", context) or []
            output_path = str(self.get_input_value("output_path", context) or "")

            if not input_files:
                raise ValueError("input_files list is required")
            if not output_path:
                raise ValueError("output_path is required")

            # Resolve {{variable}} patterns in output_path
            output_path = context.resolve_value(output_path)

            try:
                from PyPDF2 import PdfReader, PdfWriter
            except ImportError:
                raise ImportError("PyPDF2 is required for PDF operations")

            writer = PdfWriter()
            total_pages = 0

            for file_path in input_files:
                path = Path(file_path)
                if not path.exists():
                    raise FileNotFoundError(f"PDF file not found: {file_path}")

                reader = PdfReader(path)
                for page in reader.pages:
                    writer.add_page(page)
                    total_pages += 1

            out_path = Path(output_path)
            if out_path.parent:
                out_path.parent.mkdir(parents=True, exist_ok=True)

            with open(out_path, "wb") as f:
                writer.write(f)

            self.set_output_value("output_path", str(out_path))
            self.set_output_value("page_count", total_pages)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"page_count": total_pages},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class SplitPDFNode(BaseNode):
    """
    Split a PDF into separate files, one per page.

    Config:
        filename_pattern: Pattern for output files (default: page_{n}.pdf)

    Inputs:
        input_file: Path to PDF file
        output_dir: Output directory

    Outputs:
        output_files: List of created file paths
        page_count: Number of pages split
        success: Whether split succeeded
    """

    def __init__(self, node_id: str, name: str = "Split PDF", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "SplitPDFNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("input_file", PortType.INPUT, DataType.STRING)
        self.add_input_port("output_dir", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("output_files", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("page_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            input_file = str(self.get_input_value("input_file", context) or "")
            output_dir = str(self.get_input_value("output_dir", context) or "")
            filename_pattern = self.config.get("filename_pattern", "page_{n}.pdf")

            if not input_file:
                raise ValueError("input_file is required")
            if not output_dir:
                raise ValueError("output_dir is required")

            # Resolve {{variable}} patterns in paths
            input_file = context.resolve_value(input_file)
            output_dir = context.resolve_value(output_dir)

            input_path = Path(input_file)
            if not input_path.exists():
                raise FileNotFoundError(f"PDF file not found: {input_file}")

            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)

            try:
                from PyPDF2 import PdfReader, PdfWriter
            except ImportError:
                raise ImportError("PyPDF2 is required for PDF operations")

            reader = PdfReader(input_path)
            output_files = []

            for i, page in enumerate(reader.pages, 1):
                writer = PdfWriter()
                writer.add_page(page)

                filename = filename_pattern.replace("{n}", str(i))
                out_path = out_dir / filename

                with open(out_path, "wb") as f:
                    writer.write(f)

                output_files.append(str(out_path))

            self.set_output_value("output_files", output_files)
            self.set_output_value("page_count", len(output_files))
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"page_count": len(output_files)},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("output_files", [])
            self.set_output_value("page_count", 0)
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class ExtractPDFPagesNode(BaseNode):
    """
    Extract specific pages from a PDF.

    Inputs:
        input_file: Path to PDF file
        output_path: Output file path
        pages: List of page numbers to extract (1-indexed)

    Outputs:
        output_path: Path to output PDF
        page_count: Number of pages extracted
        success: Whether extraction succeeded
    """

    def __init__(self, node_id: str, name: str = "Extract PDF Pages", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ExtractPDFPagesNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("input_file", PortType.INPUT, DataType.STRING)
        self.add_input_port("output_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("pages", PortType.INPUT, DataType.LIST)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("output_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("page_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            input_file = str(self.get_input_value("input_file", context) or "")
            output_path = str(self.get_input_value("output_path", context) or "")
            pages = self.get_input_value("pages", context) or []

            if not input_file:
                raise ValueError("input_file is required")
            if not output_path:
                raise ValueError("output_path is required")
            if not pages:
                raise ValueError("pages list is required")

            # Resolve {{variable}} patterns in paths
            input_file = context.resolve_value(input_file)
            output_path = context.resolve_value(output_path)

            input_path = Path(input_file)
            if not input_path.exists():
                raise FileNotFoundError(f"PDF file not found: {input_file}")

            try:
                from PyPDF2 import PdfReader, PdfWriter
            except ImportError:
                raise ImportError("PyPDF2 is required for PDF operations")

            reader = PdfReader(input_path)
            writer = PdfWriter()

            # Convert page numbers to 0-indexed
            page_indices = [int(p) - 1 for p in pages]

            for idx in page_indices:
                if 0 <= idx < len(reader.pages):
                    writer.add_page(reader.pages[idx])

            out_path = Path(output_path)
            if out_path.parent:
                out_path.parent.mkdir(parents=True, exist_ok=True)

            with open(out_path, "wb") as f:
                writer.write(f)

            self.set_output_value("output_path", str(out_path))
            self.set_output_value("page_count", len(writer.pages))
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"page_count": len(writer.pages)},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class PDFToImagesNode(BaseNode):
    """
    Convert PDF pages to images.

    Config:
        dpi: Resolution in DPI (default: 200)
        format: Image format - 'png', 'jpg' (default: png)

    Inputs:
        input_file: Path to PDF file
        output_dir: Output directory for images
        start_page: Start page (default: 1)
        end_page: End page (default: all)

    Outputs:
        output_files: List of created image paths
        page_count: Number of images created
        success: Whether conversion succeeded
    """

    def __init__(self, node_id: str, name: str = "PDF to Images", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "PDFToImagesNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("input_file", PortType.INPUT, DataType.STRING)
        self.add_input_port("output_dir", PortType.INPUT, DataType.STRING)
        self.add_input_port("start_page", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("end_page", PortType.INPUT, DataType.INTEGER)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("output_files", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("page_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            input_file = str(self.get_input_value("input_file", context) or "")
            output_dir = str(self.get_input_value("output_dir", context) or "")
            start_page = self.get_input_value("start_page", context)
            end_page = self.get_input_value("end_page", context)
            dpi = self.config.get("dpi", 200)
            img_format = self.config.get("format", "png")

            if not input_file:
                raise ValueError("input_file is required")
            if not output_dir:
                raise ValueError("output_dir is required")

            # Resolve {{variable}} patterns in paths
            input_file = context.resolve_value(input_file)
            output_dir = context.resolve_value(output_dir)

            input_path = Path(input_file)
            if not input_path.exists():
                raise FileNotFoundError(f"PDF file not found: {input_file}")

            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)

            try:
                from pdf2image import convert_from_path
            except ImportError:
                raise ImportError("pdf2image is required for PDF to image conversion. Install with: pip install pdf2image")

            # Convert pages
            first_page = int(start_page) if start_page else None
            last_page = int(end_page) if end_page else None

            images = convert_from_path(
                input_path,
                dpi=dpi,
                first_page=first_page,
                last_page=last_page
            )

            output_files = []
            for i, image in enumerate(images, 1):
                filename = f"page_{i}.{img_format}"
                out_path = out_dir / filename
                image.save(out_path, img_format.upper())
                output_files.append(str(out_path))

            self.set_output_value("output_files", output_files)
            self.set_output_value("page_count", len(output_files))
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"page_count": len(output_files)},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("output_files", [])
            self.set_output_value("page_count", 0)
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""
