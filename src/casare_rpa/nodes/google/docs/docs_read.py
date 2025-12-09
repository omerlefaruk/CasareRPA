"""
CasareRPA - Google Docs Read Nodes

Nodes for reading and exporting Google Documents.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    PortType,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.infrastructure.resources.google_docs_client import (
    ExportFormat,
    GoogleDocsClient,
)
from casare_rpa.nodes.google.google_base import DocsBaseNode


# ============================================================================
# Reusable Property Definitions for Google Docs Nodes
# ============================================================================

GOOGLE_ACCESS_TOKEN = PropertyDef(
    "access_token",
    PropertyType.STRING,
    default="",
    label="Access Token",
    placeholder="ya29.a0...",
    tooltip="Google OAuth2 access token",
    tab="connection",
)

GOOGLE_CREDENTIAL_NAME = PropertyDef(
    "credential_name",
    PropertyType.STRING,
    default="",
    label="Credential Name",
    placeholder="google",
    tooltip="Name of stored Google OAuth2 credential (alternative to access token)",
    tab="connection",
)

GOOGLE_DOCUMENT_ID = PropertyDef(
    "document_id",
    PropertyType.STRING,
    default="",
    required=True,
    label="Document ID",
    placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    tooltip="Google Docs document ID from the URL",
)


@node_schema(
    GOOGLE_ACCESS_TOKEN,
    GOOGLE_CREDENTIAL_NAME,
    GOOGLE_DOCUMENT_ID,
)
@executable_node
class DocsGetDocumentNode(DocsBaseNode):
    """
    Get full document content from Google Docs.

    Retrieves the complete document structure including body content,
    headers, footers, and metadata.

    Inputs:
        - document_id: Google Docs document ID
        - access_token: OAuth2 access token (or use credential_name)

    Outputs:
        - document: Full document JSON structure
        - title: Document title
        - document_id: The document ID
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: none -> document, title

    NODE_TYPE = "docs_get_document"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Google Docs: Get Document"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Google Docs Get Document", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Additional outputs
        self.add_output_port("document", PortType.OUTPUT, DataType.OBJECT)
        self.add_output_port("title", PortType.OUTPUT, DataType.STRING)

    async def _execute_docs(
        self,
        context: ExecutionContext,
        client: GoogleDocsClient,
    ) -> ExecutionResult:
        """Get full document content."""
        document_id = self._get_document_id(context)

        if not document_id:
            self._set_error_outputs("Document ID is required")
            return {
                "success": False,
                "error": "Document ID is required",
                "next_nodes": [],
            }

        logger.debug(f"Getting Google Doc: {document_id}")

        # Get document
        doc = await client.get_document(document_id)

        # Set outputs
        self._set_success_outputs(document_id)
        self.set_output_value("document", doc.raw)
        self.set_output_value("title", doc.title)

        logger.info(f"Retrieved Google Doc: {doc.title}")

        return {
            "success": True,
            "document_id": document_id,
            "title": doc.title,
            "document": doc.raw,
            "next_nodes": [],
        }


@node_schema(
    GOOGLE_ACCESS_TOKEN,
    GOOGLE_CREDENTIAL_NAME,
    GOOGLE_DOCUMENT_ID,
)
@executable_node
class DocsGetTextNode(DocsBaseNode):
    """
    Extract plain text content from a Google Doc.

    Retrieves the document and extracts all text content,
    stripping formatting and structure.

    Inputs:
        - document_id: Google Docs document ID
        - access_token: OAuth2 access token (or use credential_name)

    Outputs:
        - text: Plain text content of the document
        - document_id: The document ID
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: none -> text

    NODE_TYPE = "docs_get_text"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Google Docs: Get Text"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Google Docs Get Text", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Text-specific output
        self.add_output_port("text", PortType.OUTPUT, DataType.STRING)

    async def _execute_docs(
        self,
        context: ExecutionContext,
        client: GoogleDocsClient,
    ) -> ExecutionResult:
        """Extract plain text from document."""
        document_id = self._get_document_id(context)

        if not document_id:
            self._set_error_outputs("Document ID is required")
            return {
                "success": False,
                "error": "Document ID is required",
                "next_nodes": [],
            }

        logger.debug(f"Extracting text from Google Doc: {document_id}")

        # Get text content
        text = await client.get_text(document_id)

        # Set outputs
        self._set_success_outputs(document_id)
        self.set_output_value("text", text)

        logger.info(f"Extracted {len(text)} characters from document")

        return {
            "success": True,
            "document_id": document_id,
            "text": text,
            "character_count": len(text),
            "next_nodes": [],
        }


@node_schema(
    GOOGLE_ACCESS_TOKEN,
    GOOGLE_CREDENTIAL_NAME,
    GOOGLE_DOCUMENT_ID,
    PropertyDef(
        "format",
        PropertyType.CHOICE,
        default="PDF",
        choices=["PDF", "HTML", "TXT", "DOCX", "ODT", "RTF", "EPUB"],
        label="Export Format",
        tooltip="Target format for export",
    ),
    PropertyDef(
        "output_path",
        PropertyType.STRING,
        default="",
        label="Output Path",
        placeholder="C:\\exports\\document.pdf",
        tooltip="File path to save exported document (optional, returns bytes if empty)",
    ),
)
@executable_node
class DocsExportNode(DocsBaseNode):
    """
    Export a Google Doc to various formats.

    Supports exporting to PDF, HTML, plain text, DOCX, ODT, RTF, or EPUB.
    Uses the Google Drive API export endpoint.

    Inputs:
        - document_id: Google Docs document ID
        - format: Target format (PDF, HTML, TXT, DOCX, ODT, RTF, EPUB)
        - output_path: Optional file path to save the export

    Outputs:
        - content: Exported content (bytes if no output_path)
        - output_path: Path where file was saved (if output_path provided)
        - document_id: The document ID
        - success: Boolean
        - error: Error message if failed
    """

    # @category: google
    # @requires: none
    # @ports: format, output_path -> content, output_path

    NODE_TYPE = "docs_export"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Google Docs: Export"

    # Map format names to ExportFormat enum
    FORMAT_MAP = {
        "PDF": ExportFormat.PDF,
        "HTML": ExportFormat.HTML,
        "TXT": ExportFormat.TXT,
        "DOCX": ExportFormat.DOCX,
        "ODT": ExportFormat.ODT,
        "RTF": ExportFormat.RTF,
        "EPUB": ExportFormat.EPUB,
    }

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Google Docs Export", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Export-specific ports
        self.add_input_port("format", PortType.INPUT, DataType.STRING, required=False)
        self.add_input_port(
            "output_path", PortType.INPUT, DataType.STRING, required=False
        )

        # Additional outputs
        self.add_output_port("content", PortType.OUTPUT, DataType.OBJECT)
        self.add_output_port("output_path", PortType.OUTPUT, DataType.STRING)

    async def _execute_docs(
        self,
        context: ExecutionContext,
        client: GoogleDocsClient,
    ) -> ExecutionResult:
        """Export document to specified format."""
        document_id = self._get_document_id(context)

        if not document_id:
            self._set_error_outputs("Document ID is required")
            return {
                "success": False,
                "error": "Document ID is required",
                "next_nodes": [],
            }

        # Get format
        format_name = self.get_parameter("format") or "PDF"
        if hasattr(context, "resolve_value"):
            format_name = context.resolve_value(format_name)

        format_name = format_name.upper()
        if format_name not in self.FORMAT_MAP:
            self._set_error_outputs(f"Unsupported format: {format_name}")
            return {
                "success": False,
                "error": f"Unsupported format: {format_name}",
                "next_nodes": [],
            }

        export_format = self.FORMAT_MAP[format_name]

        # Get optional output path
        output_path = self.get_parameter("output_path")
        if output_path and hasattr(context, "resolve_value"):
            output_path = context.resolve_value(output_path)

        logger.debug(f"Exporting Google Doc {document_id} to {format_name}")

        # Export document
        result = await client.export_document(
            document_id=document_id,
            export_format=export_format,
            output_path=output_path if output_path else None,
        )

        # Set outputs
        self._set_success_outputs(document_id)

        if output_path:
            self.set_output_value("output_path", str(result))
            self.set_output_value("content", None)
            logger.info(f"Exported document to {result}")
        else:
            self.set_output_value("content", result)
            self.set_output_value("output_path", "")
            logger.info(f"Exported document as {format_name} ({len(result)} bytes)")

        return {
            "success": True,
            "document_id": document_id,
            "format": format_name,
            "output_path": str(result) if output_path else "",
            "content_size": len(result) if isinstance(result, bytes) else 0,
            "next_nodes": [],
        }


__all__ = [
    "DocsGetDocumentNode",
    "DocsGetTextNode",
    "DocsExportNode",
]
