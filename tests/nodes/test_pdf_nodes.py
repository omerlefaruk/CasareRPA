"""
Tests for PDF operation nodes.

Tests 6 PDF nodes for text extraction, merging, splitting, and image conversion.
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from casare_rpa.infrastructure.execution import ExecutionContext


class TestPDFNodes:
    """Tests for PDF category nodes."""

    @pytest.fixture
    def execution_context(self) -> Mock:
        """Create a mock execution context."""
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        context.get_variable = lambda k: context.variables.get(k)
        context.set_variable = lambda k, v: context.variables.__setitem__(k, v)
        return context

    @pytest.fixture
    def mock_pdf_reader(self) -> None:
        """Create a mock PDF reader."""
        reader = MagicMock()
        reader.is_encrypted = False

        # Mock pages
        page1 = MagicMock()
        page1.extract_text.return_value = "Page 1 content"
        page2 = MagicMock()
        page2.extract_text.return_value = "Page 2 content"
        page3 = MagicMock()
        page3.extract_text.return_value = "Page 3 content"

        reader.pages = [page1, page2, page3]
        reader.metadata = {
            "/Title": "Test PDF",
            "/Author": "Test Author",
            "/Subject": "Test Subject",
            "/Creator": "Test Creator",
            "/Producer": "Test Producer",
            "/CreationDate": "D:20240101120000",
            "/ModDate": "D:20240115120000",
        }
        return reader

    @pytest.fixture
    def mock_pypdf2(self, mock_pdf_reader) -> None:
        """Create mock PyPDF2 module."""
        mock_module = MagicMock()
        mock_module.PdfReader = MagicMock(return_value=mock_pdf_reader)
        mock_module.PdfWriter = MagicMock()
        return mock_module

    # =========================================================================
    # ReadPDFTextNode Tests (5 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_read_pdf_text_node_success(
        self, execution_context, mock_pdf_reader, tmp_path
    ) -> None:
        """Test ReadPDFTextNode extracts text from PDF."""
        from casare_rpa.nodes.pdf_nodes import ReadPDFTextNode

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")

        with patch.dict(sys.modules, {"PyPDF2": MagicMock()}):
            with patch("PyPDF2.PdfReader", return_value=mock_pdf_reader):
                node = ReadPDFTextNode(node_id="test_read_pdf")
                node.set_input_value("file_path", str(pdf_file))

                result = await node.execute(execution_context)

                assert result["success"] is True
                assert result["data"]["page_count"] == 3
                assert node.get_output_value("page_count") == 3
                assert "Page 1 content" in node.get_output_value("text")

    @pytest.mark.asyncio
    async def test_read_pdf_text_node_page_range(
        self, execution_context, mock_pdf_reader, tmp_path
    ) -> None:
        """Test ReadPDFTextNode respects page range."""
        from casare_rpa.nodes.pdf_nodes import ReadPDFTextNode

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")

        with patch.dict(sys.modules, {"PyPDF2": MagicMock()}):
            with patch("PyPDF2.PdfReader", return_value=mock_pdf_reader):
                node = ReadPDFTextNode(node_id="test_range")
                node.set_input_value("file_path", str(pdf_file))
                node.set_input_value("start_page", 2)
                node.set_input_value("end_page", 3)

                result = await node.execute(execution_context)

                assert result["success"] is True
                pages = node.get_output_value("pages")
                assert len(pages) == 2  # Pages 2-3 (0-indexed: 1-2, so 2 pages)

    @pytest.mark.asyncio
    async def test_read_pdf_text_node_encrypted(
        self, execution_context, tmp_path
    ) -> None:
        """Test ReadPDFTextNode handles encrypted PDF."""
        from casare_rpa.nodes.pdf_nodes import ReadPDFTextNode

        pdf_file = tmp_path / "encrypted.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 encrypted")

        mock_reader = MagicMock()
        mock_reader.is_encrypted = True
        mock_reader.decrypt.return_value = True
        mock_reader.pages = []

        with patch.dict(sys.modules, {"PyPDF2": MagicMock()}):
            with patch("PyPDF2.PdfReader", return_value=mock_reader):
                node = ReadPDFTextNode(node_id="test_encrypted")
                node.set_input_value("file_path", str(pdf_file))
                node.set_input_value("password", "secret")

                result = await node.execute(execution_context)

                assert result["success"] is True
                mock_reader.decrypt.assert_called_once_with("secret")

    @pytest.mark.asyncio
    async def test_read_pdf_text_node_file_not_found(self, execution_context) -> None:
        """Test ReadPDFTextNode handles missing file."""
        from casare_rpa.nodes.pdf_nodes import ReadPDFTextNode

        node = ReadPDFTextNode(node_id="test_missing")
        node.set_input_value("file_path", "/nonexistent/file.pdf")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_read_pdf_text_node_empty_path(self, execution_context) -> None:
        """Test ReadPDFTextNode handles empty file path."""
        from casare_rpa.nodes.pdf_nodes import ReadPDFTextNode

        node = ReadPDFTextNode(node_id="test_empty")
        node.set_input_value("file_path", "")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    # =========================================================================
    # GetPDFInfoNode Tests (3 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_pdf_info_node_success(
        self, execution_context, mock_pdf_reader, tmp_path
    ) -> None:
        """Test GetPDFInfoNode retrieves PDF metadata."""
        from casare_rpa.nodes.pdf_nodes import GetPDFInfoNode

        pdf_file = tmp_path / "info.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 info test")

        with patch.dict(sys.modules, {"PyPDF2": MagicMock()}):
            with patch("PyPDF2.PdfReader", return_value=mock_pdf_reader):
                node = GetPDFInfoNode(node_id="test_info")
                node.set_input_value("file_path", str(pdf_file))

                result = await node.execute(execution_context)

                assert result["success"] is True
                assert node.get_output_value("page_count") == 3
                assert node.get_output_value("title") == "Test PDF"
                assert node.get_output_value("author") == "Test Author"

    @pytest.mark.asyncio
    async def test_get_pdf_info_node_encrypted(
        self, execution_context, tmp_path
    ) -> None:
        """Test GetPDFInfoNode reports encryption status."""
        from casare_rpa.nodes.pdf_nodes import GetPDFInfoNode

        pdf_file = tmp_path / "encrypted.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 encrypted")

        mock_reader = MagicMock()
        mock_reader.is_encrypted = True
        mock_reader.pages = []
        mock_reader.metadata = {}

        with patch.dict(sys.modules, {"PyPDF2": MagicMock()}):
            with patch("PyPDF2.PdfReader", return_value=mock_reader):
                node = GetPDFInfoNode(node_id="test_enc_info")
                node.set_input_value("file_path", str(pdf_file))

                result = await node.execute(execution_context)

                assert result["success"] is True
                assert node.get_output_value("is_encrypted") is True

    @pytest.mark.asyncio
    async def test_get_pdf_info_node_file_not_found(self, execution_context) -> None:
        """Test GetPDFInfoNode handles missing file."""
        from casare_rpa.nodes.pdf_nodes import GetPDFInfoNode

        node = GetPDFInfoNode(node_id="test_no_file")
        node.set_input_value("file_path", "/nonexistent/info.pdf")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    # =========================================================================
    # MergePDFsNode Tests (4 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_merge_pdfs_node_success(self, execution_context, tmp_path) -> None:
        """Test MergePDFsNode merges PDF files."""
        from casare_rpa.nodes.pdf_nodes import MergePDFsNode

        # Create mock PDF files
        pdf1 = tmp_path / "doc1.pdf"
        pdf2 = tmp_path / "doc2.pdf"
        pdf1.write_bytes(b"%PDF-1.4 doc1")
        pdf2.write_bytes(b"%PDF-1.4 doc2")
        output_path = tmp_path / "merged.pdf"

        mock_reader1 = MagicMock()
        mock_reader1.pages = [MagicMock(), MagicMock()]
        mock_reader2 = MagicMock()
        mock_reader2.pages = [MagicMock()]

        mock_writer = MagicMock()

        with patch.dict(sys.modules, {"PyPDF2": MagicMock()}):
            with (
                patch("PyPDF2.PdfReader") as mock_reader_class,
                patch("PyPDF2.PdfWriter", return_value=mock_writer),
            ):
                mock_reader_class.side_effect = [mock_reader1, mock_reader2]

                node = MergePDFsNode(node_id="test_merge")
                node.set_input_value("input_files", [str(pdf1), str(pdf2)])
                node.set_input_value("output_path", str(output_path))

                result = await node.execute(execution_context)

                assert result["success"] is True
                assert result["data"]["page_count"] == 3
                assert mock_writer.add_page.call_count == 3

    @pytest.mark.asyncio
    async def test_merge_pdfs_node_empty_list(
        self, execution_context, tmp_path
    ) -> None:
        """Test MergePDFsNode handles empty file list."""
        from casare_rpa.nodes.pdf_nodes import MergePDFsNode

        node = MergePDFsNode(node_id="test_empty_merge")
        node.set_input_value("input_files", [])
        node.set_input_value("output_path", str(tmp_path / "output.pdf"))

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_merge_pdfs_node_missing_file(
        self, execution_context, tmp_path
    ) -> None:
        """Test MergePDFsNode handles missing input file."""
        from casare_rpa.nodes.pdf_nodes import MergePDFsNode

        with patch.dict(sys.modules, {"PyPDF2": MagicMock()}):
            with patch("PyPDF2.PdfWriter"):
                node = MergePDFsNode(node_id="test_missing_merge")
                node.set_input_value("input_files", ["/nonexistent/file.pdf"])
                node.set_input_value("output_path", str(tmp_path / "output.pdf"))

                result = await node.execute(execution_context)

                assert result["success"] is False
                assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_merge_pdfs_node_no_output_path(
        self, execution_context, tmp_path
    ) -> None:
        """Test MergePDFsNode handles missing output path."""
        from casare_rpa.nodes.pdf_nodes import MergePDFsNode

        pdf1 = tmp_path / "doc1.pdf"
        pdf1.write_bytes(b"%PDF-1.4")

        node = MergePDFsNode(node_id="test_no_output")
        node.set_input_value("input_files", [str(pdf1)])
        node.set_input_value("output_path", "")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    # =========================================================================
    # SplitPDFNode Tests (4 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_split_pdf_node_success(
        self, execution_context, mock_pdf_reader, tmp_path
    ) -> None:
        """Test SplitPDFNode splits PDF into pages."""
        from casare_rpa.nodes.pdf_nodes import SplitPDFNode

        pdf_file = tmp_path / "tosplit.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 to split")
        output_dir = tmp_path / "split_output"

        mock_writer = MagicMock()

        with patch.dict(sys.modules, {"PyPDF2": MagicMock()}):
            with (
                patch("PyPDF2.PdfReader", return_value=mock_pdf_reader),
                patch("PyPDF2.PdfWriter", return_value=mock_writer),
            ):
                node = SplitPDFNode(node_id="test_split")
                node.set_input_value("input_file", str(pdf_file))
                node.set_input_value("output_dir", str(output_dir))

                result = await node.execute(execution_context)

                assert result["success"] is True
                assert result["data"]["page_count"] == 3
                output_files = node.get_output_value("output_files")
                assert len(output_files) == 3

    @pytest.mark.asyncio
    async def test_split_pdf_node_custom_pattern(
        self, execution_context, mock_pdf_reader, tmp_path
    ) -> None:
        """Test SplitPDFNode uses custom filename pattern."""
        from casare_rpa.nodes.pdf_nodes import SplitPDFNode

        pdf_file = tmp_path / "tosplit.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")
        output_dir = tmp_path / "custom_output"

        mock_writer = MagicMock()

        with patch.dict(sys.modules, {"PyPDF2": MagicMock()}):
            with (
                patch("PyPDF2.PdfReader", return_value=mock_pdf_reader),
                patch("PyPDF2.PdfWriter", return_value=mock_writer),
            ):
                node = SplitPDFNode(
                    node_id="test_pattern", config={"filename_pattern": "doc_{n}.pdf"}
                )
                node.set_input_value("input_file", str(pdf_file))
                node.set_input_value("output_dir", str(output_dir))

                result = await node.execute(execution_context)

                assert result["success"] is True
                output_files = node.get_output_value("output_files")
                assert "doc_1.pdf" in output_files[0]

    @pytest.mark.asyncio
    async def test_split_pdf_node_file_not_found(
        self, execution_context, tmp_path
    ) -> None:
        """Test SplitPDFNode handles missing input file."""
        from casare_rpa.nodes.pdf_nodes import SplitPDFNode

        node = SplitPDFNode(node_id="test_missing_split")
        node.set_input_value("input_file", "/nonexistent/file.pdf")
        node.set_input_value("output_dir", str(tmp_path))

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_split_pdf_node_empty_inputs(self, execution_context) -> None:
        """Test SplitPDFNode handles empty inputs."""
        from casare_rpa.nodes.pdf_nodes import SplitPDFNode

        node = SplitPDFNode(node_id="test_empty_split")
        node.set_input_value("input_file", "")
        node.set_input_value("output_dir", "")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    # =========================================================================
    # ExtractPDFPagesNode Tests (3 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_extract_pdf_pages_node_success(
        self, execution_context, mock_pdf_reader, tmp_path
    ) -> None:
        """Test ExtractPDFPagesNode extracts specific pages."""
        from casare_rpa.nodes.pdf_nodes import ExtractPDFPagesNode

        pdf_file = tmp_path / "source.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")
        output_path = tmp_path / "extracted.pdf"

        mock_writer = MagicMock()
        mock_writer.pages = [MagicMock(), MagicMock()]

        with patch.dict(sys.modules, {"PyPDF2": MagicMock()}):
            with (
                patch("PyPDF2.PdfReader", return_value=mock_pdf_reader),
                patch("PyPDF2.PdfWriter", return_value=mock_writer),
            ):
                node = ExtractPDFPagesNode(node_id="test_extract")
                node.set_input_value("input_file", str(pdf_file))
                node.set_input_value("output_path", str(output_path))
                node.set_input_value("pages", [1, 3])

                result = await node.execute(execution_context)

                assert result["success"] is True
                assert mock_writer.add_page.call_count == 2

    @pytest.mark.asyncio
    async def test_extract_pdf_pages_node_empty_pages(
        self, execution_context, tmp_path
    ) -> None:
        """Test ExtractPDFPagesNode handles empty page list."""
        from casare_rpa.nodes.pdf_nodes import ExtractPDFPagesNode

        pdf_file = tmp_path / "source.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")

        node = ExtractPDFPagesNode(node_id="test_no_pages")
        node.set_input_value("input_file", str(pdf_file))
        node.set_input_value("output_path", str(tmp_path / "out.pdf"))
        node.set_input_value("pages", [])

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_extract_pdf_pages_node_invalid_page(
        self, execution_context, mock_pdf_reader, tmp_path
    ) -> None:
        """Test ExtractPDFPagesNode handles out-of-range pages."""
        from casare_rpa.nodes.pdf_nodes import ExtractPDFPagesNode

        pdf_file = tmp_path / "source.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")
        output_path = tmp_path / "extracted.pdf"

        mock_writer = MagicMock()
        mock_writer.pages = []

        with patch.dict(sys.modules, {"PyPDF2": MagicMock()}):
            with (
                patch("PyPDF2.PdfReader", return_value=mock_pdf_reader),
                patch("PyPDF2.PdfWriter", return_value=mock_writer),
            ):
                node = ExtractPDFPagesNode(node_id="test_invalid_page")
                node.set_input_value("input_file", str(pdf_file))
                node.set_input_value("output_path", str(output_path))
                node.set_input_value("pages", [100])  # Out of range

                result = await node.execute(execution_context)

                # Should succeed but extract 0 pages
                assert result["success"] is True
                assert mock_writer.add_page.call_count == 0

    # =========================================================================
    # PDFToImagesNode Tests (3 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_pdf_to_images_node_success(
        self, execution_context, tmp_path
    ) -> None:
        """Test PDFToImagesNode converts PDF to images."""
        from casare_rpa.nodes.pdf_nodes import PDFToImagesNode

        pdf_file = tmp_path / "convert.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")
        output_dir = tmp_path / "images"

        mock_images = [MagicMock(), MagicMock()]

        with patch.dict(sys.modules, {"pdf2image": MagicMock()}):
            with patch("pdf2image.convert_from_path", return_value=mock_images):
                node = PDFToImagesNode(
                    node_id="test_to_images", config={"dpi": 150, "format": "png"}
                )
                node.set_input_value("input_file", str(pdf_file))
                node.set_input_value("output_dir", str(output_dir))

                result = await node.execute(execution_context)

                assert result["success"] is True
                assert result["data"]["page_count"] == 2
                output_files = node.get_output_value("output_files")
                assert len(output_files) == 2

    @pytest.mark.asyncio
    async def test_pdf_to_images_node_page_range(
        self, execution_context, tmp_path
    ) -> None:
        """Test PDFToImagesNode respects page range."""
        from casare_rpa.nodes.pdf_nodes import PDFToImagesNode

        pdf_file = tmp_path / "convert.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")
        output_dir = tmp_path / "images"

        mock_images = [MagicMock()]

        with patch.dict(sys.modules, {"pdf2image": MagicMock()}):
            with patch(
                "pdf2image.convert_from_path", return_value=mock_images
            ) as mock_convert:
                node = PDFToImagesNode(node_id="test_range_images")
                node.set_input_value("input_file", str(pdf_file))
                node.set_input_value("output_dir", str(output_dir))
                node.set_input_value("start_page", 2)
                node.set_input_value("end_page", 3)

                result = await node.execute(execution_context)

                assert result["success"] is True
                # Verify convert was called with page range
                call_kwargs = mock_convert.call_args[1]
                assert call_kwargs["first_page"] == 2
                assert call_kwargs["last_page"] == 3

    @pytest.mark.asyncio
    async def test_pdf_to_images_node_file_not_found(
        self, execution_context, tmp_path
    ) -> None:
        """Test PDFToImagesNode handles missing file."""
        from casare_rpa.nodes.pdf_nodes import PDFToImagesNode

        node = PDFToImagesNode(node_id="test_missing_convert")
        node.set_input_value("input_file", "/nonexistent/file.pdf")
        node.set_input_value("output_dir", str(tmp_path))

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestPDFNodesEdgeCases:
    """Edge case tests for PDF nodes."""

    @pytest.fixture
    def execution_context(self) -> Mock:
        """Create a mock execution context."""
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_read_pdf_encrypted_no_password(
        self, execution_context, tmp_path
    ) -> None:
        """Test ReadPDFTextNode fails on encrypted PDF without password."""
        from casare_rpa.nodes.pdf_nodes import ReadPDFTextNode

        pdf_file = tmp_path / "encrypted.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 encrypted")

        mock_reader = MagicMock()
        mock_reader.is_encrypted = True

        with patch.dict(sys.modules, {"PyPDF2": MagicMock()}):
            with patch("PyPDF2.PdfReader", return_value=mock_reader):
                node = ReadPDFTextNode(node_id="test_no_pass")
                node.set_input_value("file_path", str(pdf_file))

                result = await node.execute(execution_context)

                assert result["success"] is False
                assert "password" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_read_pdf_wrong_password(self, execution_context, tmp_path) -> None:
        """Test ReadPDFTextNode fails with wrong password."""
        from casare_rpa.nodes.pdf_nodes import ReadPDFTextNode

        pdf_file = tmp_path / "encrypted.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 encrypted")

        mock_reader = MagicMock()
        mock_reader.is_encrypted = True
        mock_reader.decrypt.return_value = False  # Wrong password

        with patch.dict(sys.modules, {"PyPDF2": MagicMock()}):
            with patch("PyPDF2.PdfReader", return_value=mock_reader):
                node = ReadPDFTextNode(node_id="test_wrong_pass")
                node.set_input_value("file_path", str(pdf_file))
                node.set_input_value("password", "wrong")

                result = await node.execute(execution_context)

                assert result["success"] is False
                assert "invalid password" in result["error"].lower()
