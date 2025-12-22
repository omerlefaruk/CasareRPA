"""
Google Docs Client Resource.
(Recreated as a stub to fix import errors)
"""

from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass


class ExportFormat(Enum):
    PDF = "application/pdf"
    HTML = "text/html"
    TXT = "text/plain"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ODT = "application/vnd.oasis.opendocument.text"
    RTF = "application/rtf"
    EPUB = "application/epub+zip"


@dataclass
class DocumentStyle:
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underline: Optional[bool] = None
    strikethrough: Optional[bool] = None
    font_size: Optional[int] = None
    font_family: Optional[str] = None


class GoogleDocsClient:
    """Client for interacting with Google Docs API."""

    def __init__(self, resource: Any):
        self.resource = resource

    async def get_document(self, document_id: str) -> Any:
        raise NotImplementedError("Stub method")

    async def get_text(self, document_id: str) -> str:
        raise NotImplementedError("Stub method")

    async def export_document(
        self, document_id: str, export_format: ExportFormat, output_path: Optional[str] = None
    ) -> Any:
        raise NotImplementedError("Stub method")

    async def create_document(self, title: str, content: Optional[str] = None) -> Any:
        raise NotImplementedError("Stub method")

    async def insert_text(self, document_id: str, text: str, index: int) -> None:
        raise NotImplementedError("Stub method")

    async def append_text(self, document_id: str, text: str) -> None:
        raise NotImplementedError("Stub method")

    async def replace_text(
        self, document_id: str, search_text: str, replace_text: str, match_case: bool = True
    ) -> Any:
        raise NotImplementedError("Stub method")

    async def insert_table(self, document_id: str, rows: int, columns: int, index: int) -> None:
        raise NotImplementedError("Stub method")

    async def insert_image(
        self,
        document_id: str,
        image_url: str,
        index: int,
        width: Optional[float] = None,
        height: Optional[float] = None,
    ) -> None:
        raise NotImplementedError("Stub method")

    async def apply_style(
        self, document_id: str, start_index: int, end_index: int, style: DocumentStyle
    ) -> None:
        raise NotImplementedError("Stub method")
