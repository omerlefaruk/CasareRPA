"""
Google Docs API Client

Async HTTP client for interacting with the Google Docs API v1.
Supports reading, creating, and modifying Google Documents.
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import aiohttp
from loguru import logger


class GoogleDocsAPIError(Exception):
    """Exception raised for Google Docs API errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[int] = None,
        status: Optional[str] = None,
        details: Optional[List[Dict]] = None,
    ):
        self.error_code = error_code
        self.status = status
        self.details = details or []
        super().__init__(message)


class ExportFormat(str, Enum):
    """Supported export formats for Google Docs."""

    PDF = "application/pdf"
    HTML = "text/html"
    TXT = "text/plain"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ODT = "application/vnd.oasis.opendocument.text"
    RTF = "application/rtf"
    EPUB = "application/epub+zip"


@dataclass
class GoogleDocsConfig:
    """Configuration for Google Docs API client."""

    access_token: str
    base_url: str = "https://docs.googleapis.com/v1"
    drive_base_url: str = "https://www.googleapis.com/drive/v3"
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class DocumentStyle:
    """Represents text styling options."""

    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underline: Optional[bool] = None
    strikethrough: Optional[bool] = None
    font_size: Optional[int] = None
    font_family: Optional[str] = None
    foreground_color: Optional[Dict[str, float]] = None
    background_color: Optional[Dict[str, float]] = None

    def to_api_format(self) -> Dict[str, Any]:
        """Convert to Google Docs API format."""
        style: Dict[str, Any] = {}
        fields: List[str] = []

        if self.bold is not None:
            style["bold"] = self.bold
            fields.append("bold")
        if self.italic is not None:
            style["italic"] = self.italic
            fields.append("italic")
        if self.underline is not None:
            style["underline"] = self.underline
            fields.append("underline")
        if self.strikethrough is not None:
            style["strikethrough"] = self.strikethrough
            fields.append("strikethrough")
        if self.font_size is not None:
            style["fontSize"] = {"magnitude": self.font_size, "unit": "PT"}
            fields.append("fontSize")
        if self.font_family is not None:
            style["weightedFontFamily"] = {"fontFamily": self.font_family}
            fields.append("weightedFontFamily")
        if self.foreground_color is not None:
            style["foregroundColor"] = {"color": {"rgbColor": self.foreground_color}}
            fields.append("foregroundColor")
        if self.background_color is not None:
            style["backgroundColor"] = {"color": {"rgbColor": self.background_color}}
            fields.append("backgroundColor")

        return {"textStyle": style, "fields": ",".join(fields)}


@dataclass
class GoogleDocument:
    """Represents a Google Document response."""

    document_id: str
    title: str
    body: Dict[str, Any]
    revision_id: Optional[str] = None
    headers: Optional[Dict] = None
    footers: Optional[Dict] = None
    raw: Dict = field(default_factory=dict)

    @classmethod
    def from_response(cls, data: Dict[str, Any]) -> "GoogleDocument":
        """Create GoogleDocument from API response."""
        return cls(
            document_id=data.get("documentId", ""),
            title=data.get("title", ""),
            body=data.get("body", {}),
            revision_id=data.get("revisionId"),
            headers=data.get("headers"),
            footers=data.get("footers"),
            raw=data,
        )

    def extract_text(self) -> str:
        """Extract plain text from document body."""
        text_parts: List[str] = []
        content = self.body.get("content", [])

        for element in content:
            if "paragraph" in element:
                paragraph = element["paragraph"]
                for elem in paragraph.get("elements", []):
                    if "textRun" in elem:
                        text_parts.append(elem["textRun"].get("content", ""))

        return "".join(text_parts)


class GoogleDocsClient:
    """
    Async client for Google Docs API v1.

    Features:
    - Document CRUD operations
    - Text insertion and formatting
    - Table creation and manipulation
    - Image insertion
    - Export to various formats (PDF, HTML, TXT, DOCX)
    - Automatic retry on transient errors

    Usage:
        config = GoogleDocsConfig(access_token="ya29.xxx...")
        client = GoogleDocsClient(config)

        async with client:
            doc = await client.get_document("document_id")
            text = doc.extract_text()
    """

    def __init__(self, config: GoogleDocsConfig):
        """Initialize the Google Docs client.

        Args:
            config: GoogleDocsConfig with access token and settings
        """
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "GoogleDocsClient":
        """Enter async context manager."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        await self.close()

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure HTTP session exists."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            headers = {
                "Authorization": f"Bearer {self.config.access_token}",
                "Content-Type": "application/json",
            }
            self._session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _request(
        self,
        method: str,
        url: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Make a request to the Google Docs API.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL
            data: Request body
            params: Query parameters

        Returns:
            API response data

        Raises:
            GoogleDocsAPIError: If the API returns an error
        """
        session = await self._ensure_session()

        for attempt in range(self.config.max_retries):
            try:
                async with session.request(
                    method, url, json=data, params=params
                ) as response:
                    result = await response.json()

                    if response.status >= 400:
                        error = result.get("error", {})
                        error_code = error.get("code", response.status)
                        error_status = error.get("status", "UNKNOWN")
                        error_message = error.get("message", f"HTTP {response.status}")
                        details = error.get("details", [])

                        # Check for rate limiting (429) or server errors (5xx)
                        if response.status == 429 or response.status >= 500:
                            if attempt < self.config.max_retries - 1:
                                wait_time = self.config.retry_delay * (2**attempt)
                                logger.warning(
                                    f"Google Docs API error {response.status}, "
                                    f"retrying in {wait_time}s..."
                                )
                                await asyncio.sleep(wait_time)
                                continue

                        raise GoogleDocsAPIError(
                            f"Google Docs API error: {error_message}",
                            error_code=error_code,
                            status=error_status,
                            details=details,
                        )

                    return result

            except aiohttp.ClientError as e:
                if attempt < self.config.max_retries - 1:
                    logger.warning(
                        f"Google Docs request failed (attempt {attempt + 1}): {e}"
                    )
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    raise GoogleDocsAPIError(f"Network error: {e}") from e

        raise GoogleDocsAPIError("Max retries exceeded")

    # =========================================================================
    # Document Reading Methods
    # =========================================================================

    async def get_document(self, document_id: str) -> GoogleDocument:
        """
        Get a document by ID.

        Args:
            document_id: The ID of the document

        Returns:
            GoogleDocument with full document content
        """
        url = f"{self.config.base_url}/documents/{document_id}"
        result = await self._request("GET", url)
        return GoogleDocument.from_response(result)

    async def get_text(self, document_id: str) -> str:
        """
        Get plain text content from a document.

        Args:
            document_id: The ID of the document

        Returns:
            Plain text content
        """
        doc = await self.get_document(document_id)
        return doc.extract_text()

    async def export_document(
        self,
        document_id: str,
        export_format: ExportFormat,
        output_path: Optional[Union[str, Path]] = None,
    ) -> Union[bytes, str]:
        """
        Export a document to a specific format.

        Uses the Drive API export endpoint.

        Args:
            document_id: The ID of the document
            export_format: Target format (PDF, HTML, TXT, etc.)
            output_path: Optional path to save the file

        Returns:
            Bytes content if no output_path, otherwise the path as string
        """
        url = f"{self.config.drive_base_url}/files/{document_id}/export"
        params = {"mimeType": export_format.value}

        session = await self._ensure_session()

        for attempt in range(self.config.max_retries):
            try:
                async with session.get(url, params=params) as response:
                    if response.status >= 400:
                        error_text = await response.text()
                        raise GoogleDocsAPIError(
                            f"Export failed: {error_text}",
                            error_code=response.status,
                        )

                    content = await response.read()

                    if output_path:
                        path = Path(output_path)
                        path.write_bytes(content)
                        logger.info(f"Document exported to {path}")
                        return str(path)

                    return content

            except aiohttp.ClientError as e:
                if attempt < self.config.max_retries - 1:
                    logger.warning(f"Export failed (attempt {attempt + 1}): {e}")
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    raise GoogleDocsAPIError(f"Export network error: {e}") from e

        raise GoogleDocsAPIError("Export max retries exceeded")

    # =========================================================================
    # Document Creation Methods
    # =========================================================================

    async def create_document(
        self,
        title: str,
        content: Optional[str] = None,
    ) -> GoogleDocument:
        """
        Create a new document.

        Args:
            title: Document title
            content: Optional initial text content

        Returns:
            GoogleDocument with the created document
        """
        url = f"{self.config.base_url}/documents"
        data = {"title": title}

        result = await self._request("POST", url, data=data)
        doc = GoogleDocument.from_response(result)

        # If content provided, insert it
        if content:
            await self.insert_text(doc.document_id, content, 1)
            # Refresh document
            doc = await self.get_document(doc.document_id)

        logger.info(f"Created document: {doc.document_id}")
        return doc

    # =========================================================================
    # Document Modification Methods (batchUpdate)
    # =========================================================================

    async def batch_update(
        self,
        document_id: str,
        requests: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Execute a batch of update requests.

        Args:
            document_id: The ID of the document
            requests: List of request objects

        Returns:
            API response with replies
        """
        url = f"{self.config.base_url}/documents/{document_id}:batchUpdate"
        data = {"requests": requests}

        result = await self._request("POST", url, data=data)
        return result

    async def insert_text(
        self,
        document_id: str,
        text: str,
        index: int,
    ) -> Dict[str, Any]:
        """
        Insert text at a specific position.

        Args:
            document_id: The ID of the document
            text: Text to insert
            index: 1-based character index position

        Returns:
            API response
        """
        requests = [
            {
                "insertText": {
                    "location": {"index": index},
                    "text": text,
                }
            }
        ]
        return await self.batch_update(document_id, requests)

    async def append_text(
        self,
        document_id: str,
        text: str,
    ) -> Dict[str, Any]:
        """
        Append text to the end of the document.

        Args:
            document_id: The ID of the document
            text: Text to append

        Returns:
            API response
        """
        # Get document to find end index
        doc = await self.get_document(document_id)
        content = doc.body.get("content", [])

        # Find the last content element's end index
        end_index = 1
        if content:
            last_element = content[-1]
            end_index = last_element.get("endIndex", 1) - 1

        return await self.insert_text(document_id, text, max(1, end_index))

    async def replace_text(
        self,
        document_id: str,
        search_text: str,
        replace_text: str,
        match_case: bool = True,
    ) -> Dict[str, Any]:
        """
        Find and replace text in the document.

        Args:
            document_id: The ID of the document
            search_text: Text to find
            replace_text: Replacement text
            match_case: Whether to match case

        Returns:
            API response with number of replacements
        """
        requests = [
            {
                "replaceAllText": {
                    "containsText": {
                        "text": search_text,
                        "matchCase": match_case,
                    },
                    "replaceText": replace_text,
                }
            }
        ]
        return await self.batch_update(document_id, requests)

    async def insert_table(
        self,
        document_id: str,
        rows: int,
        columns: int,
        index: int,
    ) -> Dict[str, Any]:
        """
        Insert a table at a specific position.

        Args:
            document_id: The ID of the document
            rows: Number of rows
            columns: Number of columns
            index: 1-based character index position

        Returns:
            API response
        """
        requests = [
            {
                "insertTable": {
                    "rows": rows,
                    "columns": columns,
                    "location": {"index": index},
                }
            }
        ]
        return await self.batch_update(document_id, requests)

    async def insert_image(
        self,
        document_id: str,
        image_url: str,
        index: int,
        width: Optional[float] = None,
        height: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Insert an image at a specific position.

        Args:
            document_id: The ID of the document
            image_url: Public URL of the image
            index: 1-based character index position
            width: Optional width in points
            height: Optional height in points

        Returns:
            API response
        """
        request: Dict[str, Any] = {
            "insertInlineImage": {
                "uri": image_url,
                "location": {"index": index},
            }
        }

        if width or height:
            size = {}
            if width:
                size["width"] = {"magnitude": width, "unit": "PT"}
            if height:
                size["height"] = {"magnitude": height, "unit": "PT"}
            request["insertInlineImage"]["objectSize"] = size

        return await self.batch_update(document_id, [request])

    async def apply_style(
        self,
        document_id: str,
        start_index: int,
        end_index: int,
        style: DocumentStyle,
    ) -> Dict[str, Any]:
        """
        Apply text styling to a range.

        Args:
            document_id: The ID of the document
            start_index: Start of range (1-based)
            end_index: End of range (exclusive)
            style: DocumentStyle with formatting options

        Returns:
            API response
        """
        style_data = style.to_api_format()
        requests = [
            {
                "updateTextStyle": {
                    "range": {
                        "startIndex": start_index,
                        "endIndex": end_index,
                    },
                    "textStyle": style_data["textStyle"],
                    "fields": style_data["fields"],
                }
            }
        ]
        return await self.batch_update(document_id, requests)

    async def delete_content(
        self,
        document_id: str,
        start_index: int,
        end_index: int,
    ) -> Dict[str, Any]:
        """
        Delete content in a range.

        Args:
            document_id: The ID of the document
            start_index: Start of range (1-based)
            end_index: End of range (exclusive)

        Returns:
            API response
        """
        requests = [
            {
                "deleteContentRange": {
                    "range": {
                        "startIndex": start_index,
                        "endIndex": end_index,
                    }
                }
            }
        ]
        return await self.batch_update(document_id, requests)


__all__ = [
    "GoogleDocsClient",
    "GoogleDocsConfig",
    "GoogleDocument",
    "GoogleDocsAPIError",
    "ExportFormat",
    "DocumentStyle",
]
