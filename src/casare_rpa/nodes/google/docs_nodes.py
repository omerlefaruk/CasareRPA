"""
Google Docs nodes for CasareRPA.

Provides nodes for interacting with Google Docs API:
- Document creation and retrieval
- Text insertion and modification
- Formatting and structure operations
"""

from typing import Any, Dict

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, ExecutionResult
from casare_rpa.infrastructure.execution import ExecutionContext


async def _get_docs_service(context: ExecutionContext, credential_name: str) -> Any:
    """Get authenticated Docs service from context."""
    google_client = context.resources.get("google_client")
    if not google_client:
        raise RuntimeError(
            "Google client not initialized. " "Use 'Google: Authenticate' node first."
        )
    return await google_client.get_service("docs", "v1", credential_name)


# =============================================================================
# Document Operations
# =============================================================================


class DocsCreateDocumentNode(BaseNode):
    """Create a new Google Document."""

    # @category: google
    # @requires: none
    # @ports: title -> document_id, document_url, success, error

    NODE_NAME = "Docs: Create Document"
    CATEGORY = "google/docs"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("title", DataType.STRING, "Document title")
        self.add_exec_output()
        self.add_output_port("document_id", DataType.STRING, "New document ID")
        self.add_output_port("document_url", DataType.STRING, "Document URL")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            title = self.get_input_value("title") or self.get_parameter(
                "title", "New Document"
            )

            service = await _get_docs_service(context, credential_name)

            body = {"title": title}
            result = service.documents().create(body=body).execute()

            document_id = result.get("documentId", "")
            document_url = f"https://docs.google.com/document/d/{document_id}"

            self.set_output_value("document_id", document_id)
            self.set_output_value("document_url", document_url)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "document_id": document_id}

        except Exception as e:
            logger.error(f"Docs create document error: {e}")
            self.set_output_value("document_id", "")
            self.set_output_value("document_url", "")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class DocsGetDocumentNode(BaseNode):
    """Get a Google Document's metadata."""

    # @category: google
    # @requires: none
    # @ports: document_id -> title, body, revision_id, success, error

    NODE_NAME = "Docs: Get Document"
    CATEGORY = "google/docs"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("document_id", DataType.STRING, "Document ID")
        self.add_exec_output()
        self.add_output_port("title", DataType.STRING, "Document title")
        self.add_output_port("body", DataType.OBJECT, "Document body object")
        self.add_output_port("revision_id", DataType.STRING, "Revision ID")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            document_id = self.get_input_value("document_id") or self.get_parameter(
                "document_id", ""
            )

            if not document_id:
                raise ValueError("Document ID is required")

            service = await _get_docs_service(context, credential_name)

            result = service.documents().get(documentId=document_id).execute()

            self.set_output_value("title", result.get("title", ""))
            self.set_output_value("body", result.get("body", {}))
            self.set_output_value("revision_id", result.get("revisionId", ""))
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "document_id": document_id}

        except Exception as e:
            logger.error(f"Docs get document error: {e}")
            self.set_output_value("title", "")
            self.set_output_value("body", {})
            self.set_output_value("revision_id", "")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class DocsGetContentNode(BaseNode):
    """Get the text content of a Google Document."""

    # @category: google
    # @requires: none
    # @ports: document_id -> text, word_count, character_count, success, error

    NODE_NAME = "Docs: Get Content"
    CATEGORY = "google/docs"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("document_id", DataType.STRING, "Document ID")
        self.add_exec_output()
        self.add_output_port("text", DataType.STRING, "Plain text content")
        self.add_output_port("word_count", DataType.INTEGER, "Word count")
        self.add_output_port("character_count", DataType.INTEGER, "Character count")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            document_id = self.get_input_value("document_id") or self.get_parameter(
                "document_id", ""
            )

            if not document_id:
                raise ValueError("Document ID is required")

            service = await _get_docs_service(context, credential_name)

            result = service.documents().get(documentId=document_id).execute()

            text_parts = []
            body = result.get("body", {})
            content = body.get("content", [])

            for element in content:
                if "paragraph" in element:
                    paragraph = element["paragraph"]
                    for elem in paragraph.get("elements", []):
                        text_run = elem.get("textRun", {})
                        text_content = text_run.get("content", "")
                        text_parts.append(text_content)

            full_text = "".join(text_parts)
            word_count = len(full_text.split())
            character_count = len(full_text)

            self.set_output_value("text", full_text)
            self.set_output_value("word_count", word_count)
            self.set_output_value("character_count", character_count)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "word_count": word_count}

        except Exception as e:
            logger.error(f"Docs get content error: {e}")
            self.set_output_value("text", "")
            self.set_output_value("word_count", 0)
            self.set_output_value("character_count", 0)
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


# =============================================================================
# Text Operations
# =============================================================================


class DocsInsertTextNode(BaseNode):
    """Insert text into a Google Document."""

    # @category: google
    # @requires: none
    # @ports: document_id, text, index -> success, error

    NODE_NAME = "Docs: Insert Text"
    CATEGORY = "google/docs"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("document_id", DataType.STRING, "Document ID")
        self.add_input_port("text", DataType.STRING, "Text to insert")
        self.add_input_port("index", DataType.INTEGER, "Insert position (1 = start)")
        self.add_exec_output()
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            document_id = self.get_input_value("document_id") or self.get_parameter(
                "document_id", ""
            )
            text = self.get_input_value("text") or self.get_parameter("text", "")
            index = self.get_input_value("index")
            if index is None:
                index = self.get_parameter("index", 1)

            if not document_id:
                raise ValueError("Document ID is required")
            if not text:
                raise ValueError("Text is required")

            service = await _get_docs_service(context, credential_name)

            requests = [{"insertText": {"location": {"index": index}, "text": text}}]

            service.documents().batchUpdate(
                documentId=document_id, body={"requests": requests}
            ).execute()

            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True}

        except Exception as e:
            logger.error(f"Docs insert text error: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class DocsDeleteContentNode(BaseNode):
    """Delete content from a Google Document."""

    # @category: google
    # @requires: none
    # @ports: document_id, start_index, end_index -> success, error

    NODE_NAME = "Docs: Delete Content"
    CATEGORY = "google/docs"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("document_id", DataType.STRING, "Document ID")
        self.add_input_port("start_index", DataType.INTEGER, "Start index")
        self.add_input_port("end_index", DataType.INTEGER, "End index")
        self.add_exec_output()
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            document_id = self.get_input_value("document_id") or self.get_parameter(
                "document_id", ""
            )
            start_index = self.get_input_value("start_index")
            if start_index is None:
                start_index = self.get_parameter("start_index", 1)
            end_index = self.get_input_value("end_index")
            if end_index is None:
                end_index = self.get_parameter("end_index", 2)

            if not document_id:
                raise ValueError("Document ID is required")

            service = await _get_docs_service(context, credential_name)

            requests = [
                {
                    "deleteContentRange": {
                        "range": {"startIndex": start_index, "endIndex": end_index}
                    }
                }
            ]

            service.documents().batchUpdate(
                documentId=document_id, body={"requests": requests}
            ).execute()

            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True}

        except Exception as e:
            logger.error(f"Docs delete content error: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class DocsReplaceTextNode(BaseNode):
    """Replace text in a Google Document."""

    # @category: google
    # @requires: none
    # @ports: document_id, find_text, replace_text, match_case -> occurrences_changed, success, error

    NODE_NAME = "Docs: Replace Text"
    CATEGORY = "google/docs"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("document_id", DataType.STRING, "Document ID")
        self.add_input_port("find_text", DataType.STRING, "Text to find")
        self.add_input_port("replace_text", DataType.STRING, "Replacement text")
        self.add_input_port("match_case", DataType.BOOLEAN, "Match case")
        self.add_exec_output()
        self.add_output_port(
            "occurrences_changed", DataType.INTEGER, "Number of replacements"
        )
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            document_id = self.get_input_value("document_id") or self.get_parameter(
                "document_id", ""
            )
            find_text = self.get_input_value("find_text") or self.get_parameter(
                "find_text", ""
            )
            replace_text = self.get_input_value("replace_text")
            if replace_text is None:
                replace_text = self.get_parameter("replace_text", "")
            match_case = self.get_input_value("match_case")
            if match_case is None:
                match_case = self.get_parameter("match_case", True)

            if not document_id:
                raise ValueError("Document ID is required")
            if not find_text:
                raise ValueError("Find text is required")

            service = await _get_docs_service(context, credential_name)

            requests = [
                {
                    "replaceAllText": {
                        "containsText": {"text": find_text, "matchCase": match_case},
                        "replaceText": replace_text,
                    }
                }
            ]

            result = (
                service.documents()
                .batchUpdate(documentId=document_id, body={"requests": requests})
                .execute()
            )

            replies = result.get("replies", [])
            occurrences = 0
            if replies:
                occurrences = (
                    replies[0].get("replaceAllText", {}).get("occurrencesChanged", 0)
                )

            self.set_output_value("occurrences_changed", occurrences)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True, "occurrences_changed": occurrences}

        except Exception as e:
            logger.error(f"Docs replace text error: {e}")
            self.set_output_value("occurrences_changed", 0)
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


# =============================================================================
# Formatting Operations
# =============================================================================


class DocsInsertTableNode(BaseNode):
    """Insert a table into a Google Document."""

    # @category: google
    # @requires: none
    # @ports: document_id, rows, columns, index -> success, error

    NODE_NAME = "Docs: Insert Table"
    CATEGORY = "google/docs"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("document_id", DataType.STRING, "Document ID")
        self.add_input_port("rows", DataType.INTEGER, "Number of rows")
        self.add_input_port("columns", DataType.INTEGER, "Number of columns")
        self.add_input_port("index", DataType.INTEGER, "Insert position")
        self.add_exec_output()
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            document_id = self.get_input_value("document_id") or self.get_parameter(
                "document_id", ""
            )
            rows = self.get_input_value("rows")
            if rows is None:
                rows = self.get_parameter("rows", 3)
            columns = self.get_input_value("columns")
            if columns is None:
                columns = self.get_parameter("columns", 3)
            index = self.get_input_value("index")
            if index is None:
                index = self.get_parameter("index", 1)

            if not document_id:
                raise ValueError("Document ID is required")

            service = await _get_docs_service(context, credential_name)

            requests = [
                {
                    "insertTable": {
                        "rows": rows,
                        "columns": columns,
                        "location": {"index": index},
                    }
                }
            ]

            service.documents().batchUpdate(
                documentId=document_id, body={"requests": requests}
            ).execute()

            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True}

        except Exception as e:
            logger.error(f"Docs insert table error: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class DocsInsertImageNode(BaseNode):
    """Insert an image into a Google Document."""

    # @category: google
    # @requires: none
    # @ports: document_id, image_uri, index, width, height -> success, error

    NODE_NAME = "Docs: Insert Image"
    CATEGORY = "google/docs"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("document_id", DataType.STRING, "Document ID")
        self.add_input_port("image_uri", DataType.STRING, "Image URL")
        self.add_input_port("index", DataType.INTEGER, "Insert position")
        self.add_input_port("width", DataType.FLOAT, "Width in points")
        self.add_input_port("height", DataType.FLOAT, "Height in points")
        self.add_exec_output()
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            document_id = self.get_input_value("document_id") or self.get_parameter(
                "document_id", ""
            )
            image_uri = self.get_input_value("image_uri") or self.get_parameter(
                "image_uri", ""
            )
            index = self.get_input_value("index")
            if index is None:
                index = self.get_parameter("index", 1)
            width = self.get_input_value("width")
            if width is None:
                width = self.get_parameter("width", 0)
            height = self.get_input_value("height")
            if height is None:
                height = self.get_parameter("height", 0)

            if not document_id:
                raise ValueError("Document ID is required")
            if not image_uri:
                raise ValueError("Image URI is required")

            service = await _get_docs_service(context, credential_name)

            insert_request: Dict[str, Any] = {
                "insertInlineImage": {"uri": image_uri, "location": {"index": index}}
            }

            if width > 0 or height > 0:
                object_size = {}
                if width > 0:
                    object_size["width"] = {"magnitude": width, "unit": "PT"}
                if height > 0:
                    object_size["height"] = {"magnitude": height, "unit": "PT"}
                insert_request["insertInlineImage"]["objectSize"] = object_size

            requests = [insert_request]

            service.documents().batchUpdate(
                documentId=document_id, body={"requests": requests}
            ).execute()

            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True}

        except Exception as e:
            logger.error(f"Docs insert image error: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class DocsUpdateStyleNode(BaseNode):
    """Update text style in a range."""

    # @category: google
    # @requires: none
    # @ports: document_id, start_index, end_index -> success, error

    NODE_NAME = "Docs: Update Style"
    CATEGORY = "google/docs"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("document_id", DataType.STRING, "Document ID")
        self.add_input_port("start_index", DataType.INTEGER, "Start index")
        self.add_input_port("end_index", DataType.INTEGER, "End index")
        self.add_exec_output()
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            document_id = self.get_input_value("document_id") or self.get_parameter(
                "document_id", ""
            )
            start_index = self.get_input_value("start_index")
            if start_index is None:
                start_index = self.get_parameter("start_index", 1)
            end_index = self.get_input_value("end_index")
            if end_index is None:
                end_index = self.get_parameter("end_index", 10)

            bold = self.get_parameter("bold", False)
            italic = self.get_parameter("italic", False)
            underline = self.get_parameter("underline", False)
            font_size = self.get_parameter("font_size", 0)

            if not document_id:
                raise ValueError("Document ID is required")

            service = await _get_docs_service(context, credential_name)

            text_style: Dict[str, Any] = {}
            fields = []

            if bold:
                text_style["bold"] = bold
                fields.append("bold")
            if italic:
                text_style["italic"] = italic
                fields.append("italic")
            if underline:
                text_style["underline"] = underline
                fields.append("underline")
            if font_size > 0:
                text_style["fontSize"] = {"magnitude": font_size, "unit": "PT"}
                fields.append("fontSize")

            if not fields:
                raise ValueError("At least one style property must be set")

            requests = [
                {
                    "updateTextStyle": {
                        "range": {"startIndex": start_index, "endIndex": end_index},
                        "textStyle": text_style,
                        "fields": ",".join(fields),
                    }
                }
            ]

            service.documents().batchUpdate(
                documentId=document_id, body={"requests": requests}
            ).execute()

            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True}

        except Exception as e:
            logger.error(f"Docs update style error: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}


class DocsBatchUpdateNode(BaseNode):
    """Execute multiple document updates in a single batch."""

    # @category: google
    # @requires: none
    # @ports: document_id, requests -> replies, success, error

    NODE_NAME = "Docs: Batch Update"
    CATEGORY = "google/docs"

    def _define_ports(self) -> None:
        self.add_exec_input()
        self.add_input_port("document_id", DataType.STRING, "Document ID")
        self.add_input_port("requests", DataType.LIST, "Array of request objects")
        self.add_exec_output()
        self.add_output_port("replies", DataType.LIST, "Response replies")
        self.add_output_port("success", DataType.BOOLEAN, "Success status")
        self.add_output_port("error", DataType.STRING, "Error message")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        try:
            credential_name = self.get_parameter("credential_name", "google")
            document_id = self.get_input_value("document_id") or self.get_parameter(
                "document_id", ""
            )
            requests = self.get_input_value("requests") or []

            if not document_id:
                raise ValueError("Document ID is required")
            if not requests:
                raise ValueError("Requests array is required")

            service = await _get_docs_service(context, credential_name)

            result = (
                service.documents()
                .batchUpdate(documentId=document_id, body={"requests": requests})
                .execute()
            )

            self.set_output_value("replies", result.get("replies", []))
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {"success": True}

        except Exception as e:
            logger.error(f"Docs batch update error: {e}")
            self.set_output_value("replies", [])
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e)}
