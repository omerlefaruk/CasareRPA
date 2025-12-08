"""
CasareRPA - Google Docs Write Nodes

Nodes for creating and modifying Google Documents.
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
    DocumentStyle,
    GoogleDocsClient,
)
from casare_rpa.nodes.google.docs.docs_base import DocsBaseNode


# ============================================================================
# Reusable Property Definitions for Google Docs Write Nodes
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
    PropertyDef(
        "title",
        PropertyType.STRING,
        default="",
        required=True,
        label="Document Title",
        placeholder="My New Document",
        tooltip="Title for the new document",
    ),
    PropertyDef(
        "content",
        PropertyType.TEXT,
        default="",
        label="Initial Content",
        placeholder="Enter initial document content...",
        tooltip="Optional initial text content for the document",
    ),
)
@executable_node
class DocsCreateDocumentNode(DocsBaseNode):
    """
    Create a new Google Docs document.

    Creates a blank document with optional initial content.

    Inputs:
        - title: Document title
        - content: Optional initial text content
        - access_token: OAuth2 access token (or use credential_name)

    Outputs:
        - document_id: ID of the created document
        - title: Document title
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "docs_create_document"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Google Docs: Create Document"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Google Docs Create Document", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        # Connection ports (no document_id needed for create)
        self.add_input_port(
            "access_token", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port(
            "credential_name", PortType.INPUT, DataType.STRING, required=False
        )

        # Create-specific ports
        self.add_input_port("title", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port("content", PortType.INPUT, DataType.STRING, required=False)

        # Output ports
        self.add_output_port("document_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("title", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def _execute_docs(
        self,
        context: ExecutionContext,
        client: GoogleDocsClient,
    ) -> ExecutionResult:
        """Create a new document."""
        # Get title
        title = self.get_parameter("title")
        if hasattr(context, "resolve_value"):
            title = context.resolve_value(title)

        if not title:
            self._set_error_outputs("Document title is required")
            return {
                "success": False,
                "error": "Document title is required",
                "next_nodes": [],
            }

        # Get optional content
        content = self.get_parameter("content")
        if content and hasattr(context, "resolve_value"):
            content = context.resolve_value(content)

        logger.debug(f"Creating Google Doc: {title}")

        # Create document
        doc = await client.create_document(title=title, content=content)

        # Set outputs
        self._set_success_outputs(doc.document_id)
        self.set_output_value("title", doc.title)

        logger.info(f"Created Google Doc: {doc.document_id}")

        return {
            "success": True,
            "document_id": doc.document_id,
            "title": doc.title,
            "next_nodes": [],
        }


@node_schema(
    GOOGLE_ACCESS_TOKEN,
    GOOGLE_CREDENTIAL_NAME,
    GOOGLE_DOCUMENT_ID,
    PropertyDef(
        "text",
        PropertyType.TEXT,
        default="",
        required=True,
        label="Text",
        placeholder="Text to insert...",
        tooltip="Text content to insert",
    ),
    PropertyDef(
        "index",
        PropertyType.INTEGER,
        default=1,
        required=True,
        label="Index",
        tooltip="Character index position (1-based) where text will be inserted",
    ),
)
@executable_node
class DocsInsertTextNode(DocsBaseNode):
    """
    Insert text at a specific position in a Google Doc.

    Uses 1-based character index positioning.

    Inputs:
        - document_id: Google Docs document ID
        - text: Text to insert
        - index: Character position (1-based)
        - access_token: OAuth2 access token (or use credential_name)

    Outputs:
        - document_id: The document ID
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "docs_insert_text"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Google Docs: Insert Text"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Google Docs Insert Text", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Insert-specific ports
        self.add_input_port("text", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port("index", PortType.INPUT, DataType.INTEGER, required=True)

    async def _execute_docs(
        self,
        context: ExecutionContext,
        client: GoogleDocsClient,
    ) -> ExecutionResult:
        """Insert text at position."""
        document_id = self._get_document_id(context)

        if not document_id:
            self._set_error_outputs("Document ID is required")
            return {
                "success": False,
                "error": "Document ID is required",
                "next_nodes": [],
            }

        # Get text
        text = self.get_parameter("text")
        if hasattr(context, "resolve_value"):
            text = context.resolve_value(text)

        if not text:
            self._set_error_outputs("Text is required")
            return {
                "success": False,
                "error": "Text is required",
                "next_nodes": [],
            }

        # Get index
        index = self.get_parameter("index")
        if hasattr(context, "resolve_value"):
            index = context.resolve_value(index)

        try:
            index = int(index)
        except (TypeError, ValueError):
            index = 1

        if index < 1:
            index = 1

        logger.debug(f"Inserting text at index {index} in document {document_id}")

        # Insert text
        await client.insert_text(document_id=document_id, text=text, index=index)

        # Set outputs
        self._set_success_outputs(document_id)

        logger.info(f"Inserted {len(text)} characters at index {index}")

        return {
            "success": True,
            "document_id": document_id,
            "characters_inserted": len(text),
            "index": index,
            "next_nodes": [],
        }


@node_schema(
    GOOGLE_ACCESS_TOKEN,
    GOOGLE_CREDENTIAL_NAME,
    GOOGLE_DOCUMENT_ID,
    PropertyDef(
        "text",
        PropertyType.TEXT,
        default="",
        required=True,
        label="Text",
        placeholder="Text to append...",
        tooltip="Text content to append to the end of the document",
    ),
)
@executable_node
class DocsAppendTextNode(DocsBaseNode):
    """
    Append text to the end of a Google Doc.

    Automatically finds the end of the document and inserts text there.

    Inputs:
        - document_id: Google Docs document ID
        - text: Text to append
        - access_token: OAuth2 access token (or use credential_name)

    Outputs:
        - document_id: The document ID
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "docs_append_text"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Google Docs: Append Text"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Google Docs Append Text", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Append-specific ports
        self.add_input_port("text", PortType.INPUT, DataType.STRING, required=True)

    async def _execute_docs(
        self,
        context: ExecutionContext,
        client: GoogleDocsClient,
    ) -> ExecutionResult:
        """Append text to document end."""
        document_id = self._get_document_id(context)

        if not document_id:
            self._set_error_outputs("Document ID is required")
            return {
                "success": False,
                "error": "Document ID is required",
                "next_nodes": [],
            }

        # Get text
        text = self.get_parameter("text")
        if hasattr(context, "resolve_value"):
            text = context.resolve_value(text)

        if not text:
            self._set_error_outputs("Text is required")
            return {
                "success": False,
                "error": "Text is required",
                "next_nodes": [],
            }

        logger.debug(f"Appending text to document {document_id}")

        # Append text
        await client.append_text(document_id=document_id, text=text)

        # Set outputs
        self._set_success_outputs(document_id)

        logger.info(f"Appended {len(text)} characters to document")

        return {
            "success": True,
            "document_id": document_id,
            "characters_appended": len(text),
            "next_nodes": [],
        }


@node_schema(
    GOOGLE_ACCESS_TOKEN,
    GOOGLE_CREDENTIAL_NAME,
    GOOGLE_DOCUMENT_ID,
    PropertyDef(
        "search",
        PropertyType.STRING,
        default="",
        required=True,
        label="Search Text",
        placeholder="Text to find...",
        tooltip="Text to search for in the document",
    ),
    PropertyDef(
        "replace",
        PropertyType.STRING,
        default="",
        required=True,
        label="Replace With",
        placeholder="Replacement text...",
        tooltip="Text to replace matches with",
    ),
    PropertyDef(
        "match_case",
        PropertyType.BOOLEAN,
        default=True,
        label="Match Case",
        tooltip="Whether to match case when searching",
    ),
)
@executable_node
class DocsReplaceTextNode(DocsBaseNode):
    """
    Find and replace text in a Google Doc.

    Replaces all occurrences of search text with replacement text.

    Inputs:
        - document_id: Google Docs document ID
        - search: Text to find
        - replace: Replacement text
        - match_case: Whether to match case (default: True)
        - access_token: OAuth2 access token (or use credential_name)

    Outputs:
        - document_id: The document ID
        - replacements_count: Number of replacements made
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "docs_replace_text"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Google Docs: Replace Text"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Google Docs Replace Text", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Replace-specific ports
        self.add_input_port("search", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port("replace", PortType.INPUT, DataType.STRING, required=True)
        self.add_input_port(
            "match_case", PortType.INPUT, DataType.BOOLEAN, required=False
        )

        # Additional output
        self.add_output_port("replacements_count", PortType.OUTPUT, DataType.INTEGER)

    async def _execute_docs(
        self,
        context: ExecutionContext,
        client: GoogleDocsClient,
    ) -> ExecutionResult:
        """Find and replace text."""
        document_id = self._get_document_id(context)

        if not document_id:
            self._set_error_outputs("Document ID is required")
            return {
                "success": False,
                "error": "Document ID is required",
                "next_nodes": [],
            }

        # Get search text
        search_text = self.get_parameter("search")
        if hasattr(context, "resolve_value"):
            search_text = context.resolve_value(search_text)

        if not search_text:
            self._set_error_outputs("Search text is required")
            return {
                "success": False,
                "error": "Search text is required",
                "next_nodes": [],
            }

        # Get replace text (can be empty to delete matches)
        replace_text = self.get_parameter("replace") or ""
        if hasattr(context, "resolve_value"):
            replace_text = context.resolve_value(replace_text)

        # Get match_case option
        match_case = self.get_parameter("match_case")
        if match_case is None:
            match_case = True

        logger.debug(f"Replacing '{search_text}' in document {document_id}")

        # Replace text
        result = await client.replace_text(
            document_id=document_id,
            search_text=search_text,
            replace_text=replace_text,
            match_case=match_case,
        )

        # Extract replacement count from response
        replies = result.get("replies", [])
        replacements_count = 0
        for reply in replies:
            if "replaceAllText" in reply:
                replacements_count = reply["replaceAllText"].get(
                    "occurrencesChanged", 0
                )

        # Set outputs
        self._set_success_outputs(document_id)
        self.set_output_value("replacements_count", replacements_count)

        logger.info(f"Replaced {replacements_count} occurrences")

        return {
            "success": True,
            "document_id": document_id,
            "replacements_count": replacements_count,
            "next_nodes": [],
        }


@node_schema(
    GOOGLE_ACCESS_TOKEN,
    GOOGLE_CREDENTIAL_NAME,
    GOOGLE_DOCUMENT_ID,
    PropertyDef(
        "rows",
        PropertyType.INTEGER,
        default=3,
        required=True,
        label="Rows",
        tooltip="Number of rows in the table",
    ),
    PropertyDef(
        "columns",
        PropertyType.INTEGER,
        default=3,
        required=True,
        label="Columns",
        tooltip="Number of columns in the table",
    ),
    PropertyDef(
        "index",
        PropertyType.INTEGER,
        default=1,
        required=True,
        label="Index",
        tooltip="Character index position (1-based) where table will be inserted",
    ),
)
@executable_node
class DocsInsertTableNode(DocsBaseNode):
    """
    Insert a table into a Google Doc.

    Creates a table with specified rows and columns at the given position.

    Inputs:
        - document_id: Google Docs document ID
        - rows: Number of rows
        - columns: Number of columns
        - index: Character position (1-based)
        - access_token: OAuth2 access token (or use credential_name)

    Outputs:
        - document_id: The document ID
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "docs_insert_table"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Google Docs: Insert Table"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Google Docs Insert Table", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Table-specific ports
        self.add_input_port("rows", PortType.INPUT, DataType.INTEGER, required=True)
        self.add_input_port("columns", PortType.INPUT, DataType.INTEGER, required=True)
        self.add_input_port("index", PortType.INPUT, DataType.INTEGER, required=True)

    async def _execute_docs(
        self,
        context: ExecutionContext,
        client: GoogleDocsClient,
    ) -> ExecutionResult:
        """Insert table at position."""
        document_id = self._get_document_id(context)

        if not document_id:
            self._set_error_outputs("Document ID is required")
            return {
                "success": False,
                "error": "Document ID is required",
                "next_nodes": [],
            }

        # Get table dimensions
        rows = self.get_parameter("rows")
        columns = self.get_parameter("columns")
        index = self.get_parameter("index")

        if hasattr(context, "resolve_value"):
            rows = context.resolve_value(rows)
            columns = context.resolve_value(columns)
            index = context.resolve_value(index)

        try:
            rows = int(rows)
            columns = int(columns)
            index = int(index)
        except (TypeError, ValueError):
            self._set_error_outputs("Invalid rows, columns, or index value")
            return {
                "success": False,
                "error": "Invalid rows, columns, or index value",
                "next_nodes": [],
            }

        # Validate dimensions
        if rows < 1 or columns < 1:
            self._set_error_outputs("Rows and columns must be at least 1")
            return {
                "success": False,
                "error": "Rows and columns must be at least 1",
                "next_nodes": [],
            }

        if index < 1:
            index = 1

        logger.debug(
            f"Inserting {rows}x{columns} table at index {index} in document {document_id}"
        )

        # Insert table
        await client.insert_table(
            document_id=document_id, rows=rows, columns=columns, index=index
        )

        # Set outputs
        self._set_success_outputs(document_id)

        logger.info(f"Inserted {rows}x{columns} table at index {index}")

        return {
            "success": True,
            "document_id": document_id,
            "rows": rows,
            "columns": columns,
            "index": index,
            "next_nodes": [],
        }


@node_schema(
    GOOGLE_ACCESS_TOKEN,
    GOOGLE_CREDENTIAL_NAME,
    GOOGLE_DOCUMENT_ID,
    PropertyDef(
        "image_url",
        PropertyType.STRING,
        default="",
        required=True,
        label="Image URL",
        placeholder="https://example.com/image.png",
        tooltip="Public URL of the image to insert",
    ),
    PropertyDef(
        "index",
        PropertyType.INTEGER,
        default=1,
        required=True,
        label="Index",
        tooltip="Character index position (1-based) where image will be inserted",
    ),
    PropertyDef(
        "image_width",
        PropertyType.FLOAT,
        default=0,
        label="Width (pt)",
        tooltip="Optional width in points (0 for auto)",
    ),
    PropertyDef(
        "image_height",
        PropertyType.FLOAT,
        default=0,
        label="Height (pt)",
        tooltip="Optional height in points (0 for auto)",
    ),
)
@executable_node
class DocsInsertImageNode(DocsBaseNode):
    """
    Insert an image into a Google Doc.

    Inserts an inline image from a public URL at the specified position.

    Inputs:
        - document_id: Google Docs document ID
        - image_url: Public URL of the image
        - index: Character position (1-based)
        - width: Optional width in points
        - height: Optional height in points
        - access_token: OAuth2 access token (or use credential_name)

    Outputs:
        - document_id: The document ID
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "docs_insert_image"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Google Docs: Insert Image"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Google Docs Insert Image", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Image-specific ports
        self.add_input_port("image_url", DataType.STRING, required=True)
        self.add_input_port("index", DataType.INTEGER, required=True)
        self.add_input_port("image_width", DataType.FLOAT, required=False)
        self.add_input_port("image_height", DataType.FLOAT, required=False)

    async def _execute_docs(
        self,
        context: ExecutionContext,
        client: GoogleDocsClient,
    ) -> ExecutionResult:
        """Insert image at position."""
        document_id = self._get_document_id(context)

        if not document_id:
            self._set_error_outputs("Document ID is required")
            return {
                "success": False,
                "error": "Document ID is required",
                "next_nodes": [],
            }

        # Get image URL
        image_url = self.get_parameter("image_url")
        if hasattr(context, "resolve_value"):
            image_url = context.resolve_value(image_url)

        if not image_url:
            self._set_error_outputs("Image URL is required")
            return {
                "success": False,
                "error": "Image URL is required",
                "next_nodes": [],
            }

        # Get index
        index = self.get_parameter("index")
        if hasattr(context, "resolve_value"):
            index = context.resolve_value(index)

        try:
            index = int(index)
        except (TypeError, ValueError):
            index = 1

        if index < 1:
            index = 1

        # Get optional dimensions
        width = self.get_parameter("image_width")
        height = self.get_parameter("image_height")

        if hasattr(context, "resolve_value"):
            width = context.resolve_value(width)
            height = context.resolve_value(height)

        try:
            width = float(width) if width else None
            height = float(height) if height else None
        except (TypeError, ValueError):
            width = None
            height = None

        # Filter out zero values
        if width and width <= 0:
            width = None
        if height and height <= 0:
            height = None

        logger.debug(f"Inserting image at index {index} in document {document_id}")

        # Insert image
        await client.insert_image(
            document_id=document_id,
            image_url=image_url,
            index=index,
            width=width,
            height=height,
        )

        # Set outputs
        self._set_success_outputs(document_id)

        logger.info(f"Inserted image at index {index}")

        return {
            "success": True,
            "document_id": document_id,
            "image_url": image_url,
            "index": index,
            "next_nodes": [],
        }


@node_schema(
    GOOGLE_ACCESS_TOKEN,
    GOOGLE_CREDENTIAL_NAME,
    GOOGLE_DOCUMENT_ID,
    PropertyDef(
        "start_index",
        PropertyType.INTEGER,
        default=1,
        required=True,
        label="Start Index",
        tooltip="Start of text range (1-based, inclusive)",
    ),
    PropertyDef(
        "end_index",
        PropertyType.INTEGER,
        default=2,
        required=True,
        label="End Index",
        tooltip="End of text range (1-based, exclusive)",
    ),
    PropertyDef(
        "bold",
        PropertyType.BOOLEAN,
        default=False,
        label="Bold",
        tooltip="Apply bold formatting",
    ),
    PropertyDef(
        "italic",
        PropertyType.BOOLEAN,
        default=False,
        label="Italic",
        tooltip="Apply italic formatting",
    ),
    PropertyDef(
        "underline",
        PropertyType.BOOLEAN,
        default=False,
        label="Underline",
        tooltip="Apply underline formatting",
    ),
    PropertyDef(
        "strikethrough",
        PropertyType.BOOLEAN,
        default=False,
        label="Strikethrough",
        tooltip="Apply strikethrough formatting",
    ),
    PropertyDef(
        "font_size",
        PropertyType.INTEGER,
        default=0,
        label="Font Size (pt)",
        tooltip="Font size in points (0 to keep current)",
    ),
    PropertyDef(
        "font_family",
        PropertyType.STRING,
        default="",
        label="Font Family",
        placeholder="Arial, Times New Roman, etc.",
        tooltip="Font family name (empty to keep current)",
    ),
)
@executable_node
class DocsApplyStyleNode(DocsBaseNode):
    """
    Apply text formatting/styling to a range in a Google Doc.

    Applies various text styles (bold, italic, underline, etc.) to
    a specified character range.

    Inputs:
        - document_id: Google Docs document ID
        - start_index: Start of range (1-based, inclusive)
        - end_index: End of range (1-based, exclusive)
        - bold: Apply bold
        - italic: Apply italic
        - underline: Apply underline
        - strikethrough: Apply strikethrough
        - font_size: Font size in points (0 to skip)
        - font_family: Font family name (empty to skip)
        - access_token: OAuth2 access token (or use credential_name)

    Outputs:
        - document_id: The document ID
        - success: Boolean
        - error: Error message if failed
    """

    NODE_TYPE = "docs_apply_style"
    NODE_CATEGORY = "google"
    NODE_DISPLAY_NAME = "Google Docs: Apply Style"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Google Docs Apply Style", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Style-specific ports
        self.add_input_port(
            "start_index", PortType.INPUT, DataType.INTEGER, required=True
        )
        self.add_input_port(
            "end_index", PortType.INPUT, DataType.INTEGER, required=True
        )
        self.add_input_port("bold", PortType.INPUT, DataType.BOOLEAN, required=False)
        self.add_input_port("italic", PortType.INPUT, DataType.BOOLEAN, required=False)
        self.add_input_port(
            "underline", PortType.INPUT, DataType.BOOLEAN, required=False
        )
        self.add_input_port(
            "strikethrough", PortType.INPUT, DataType.BOOLEAN, required=False
        )
        self.add_input_port(
            "font_size", PortType.INPUT, DataType.INTEGER, required=False
        )
        self.add_input_port(
            "font_family", PortType.INPUT, DataType.STRING, required=False
        )

    async def _execute_docs(
        self,
        context: ExecutionContext,
        client: GoogleDocsClient,
    ) -> ExecutionResult:
        """Apply text styling to range."""
        document_id = self._get_document_id(context)

        if not document_id:
            self._set_error_outputs("Document ID is required")
            return {
                "success": False,
                "error": "Document ID is required",
                "next_nodes": [],
            }

        # Get range indices
        start_index = self.get_parameter("start_index")
        end_index = self.get_parameter("end_index")

        if hasattr(context, "resolve_value"):
            start_index = context.resolve_value(start_index)
            end_index = context.resolve_value(end_index)

        try:
            start_index = int(start_index)
            end_index = int(end_index)
        except (TypeError, ValueError):
            self._set_error_outputs("Invalid start_index or end_index")
            return {
                "success": False,
                "error": "Invalid start_index or end_index",
                "next_nodes": [],
            }

        if start_index < 1:
            start_index = 1
        if end_index <= start_index:
            self._set_error_outputs("end_index must be greater than start_index")
            return {
                "success": False,
                "error": "end_index must be greater than start_index",
                "next_nodes": [],
            }

        # Build style object
        bold = self.get_parameter("bold")
        italic = self.get_parameter("italic")
        underline = self.get_parameter("underline")
        strikethrough = self.get_parameter("strikethrough")
        font_size = self.get_parameter("font_size")
        font_family = self.get_parameter("font_family")

        if hasattr(context, "resolve_value"):
            bold = context.resolve_value(bold)
            italic = context.resolve_value(italic)
            underline = context.resolve_value(underline)
            strikethrough = context.resolve_value(strikethrough)
            font_size = context.resolve_value(font_size)
            font_family = context.resolve_value(font_family)

        # Convert font_size
        try:
            font_size = int(font_size) if font_size else None
            if font_size and font_size <= 0:
                font_size = None
        except (TypeError, ValueError):
            font_size = None

        # Create DocumentStyle
        style = DocumentStyle(
            bold=bold if bold else None,
            italic=italic if italic else None,
            underline=underline if underline else None,
            strikethrough=strikethrough if strikethrough else None,
            font_size=font_size,
            font_family=font_family if font_family else None,
        )

        logger.debug(
            f"Applying style to range [{start_index}, {end_index}) "
            f"in document {document_id}"
        )

        # Apply style
        await client.apply_style(
            document_id=document_id,
            start_index=start_index,
            end_index=end_index,
            style=style,
        )

        # Set outputs
        self._set_success_outputs(document_id)

        logger.info(f"Applied style to range [{start_index}, {end_index})")

        return {
            "success": True,
            "document_id": document_id,
            "start_index": start_index,
            "end_index": end_index,
            "next_nodes": [],
        }


__all__ = [
    "DocsCreateDocumentNode",
    "DocsInsertTextNode",
    "DocsAppendTextNode",
    "DocsReplaceTextNode",
    "DocsInsertTableNode",
    "DocsInsertImageNode",
    "DocsApplyStyleNode",
]
