"""
Google Drive API Client

Async HTTP client for interacting with the Google Drive API v3.
Supports file and folder operations with resumable uploads.
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union

import aiohttp
from loguru import logger


class DriveAPIError(Exception):
    """Exception raised for Google Drive API errors."""

    def __init__(
        self,
        message: str,
        error_code: int | None = None,
        reason: str | None = None,
    ):
        self.error_code = error_code
        self.reason = reason
        super().__init__(message)


class DriveScope(str, Enum):
    """Google Drive API scopes."""

    FULL = "https://www.googleapis.com/auth/drive"
    FILE = "https://www.googleapis.com/auth/drive.file"
    READONLY = "https://www.googleapis.com/auth/drive.readonly"
    METADATA = "https://www.googleapis.com/auth/drive.metadata"
    METADATA_READONLY = "https://www.googleapis.com/auth/drive.metadata.readonly"
    APPDATA = "https://www.googleapis.com/auth/drive.appdata"


# Common MIME types for Google Workspace
class DriveMimeType:
    """Google Drive MIME type constants."""

    # Google Workspace types
    FOLDER = "application/vnd.google-apps.folder"
    DOCUMENT = "application/vnd.google-apps.document"
    SPREADSHEET = "application/vnd.google-apps.spreadsheet"
    PRESENTATION = "application/vnd.google-apps.presentation"
    FORM = "application/vnd.google-apps.form"
    DRAWING = "application/vnd.google-apps.drawing"
    SCRIPT = "application/vnd.google-apps.script"
    SITE = "application/vnd.google-apps.site"
    MAP = "application/vnd.google-apps.map"
    SHORTCUT = "application/vnd.google-apps.shortcut"

    # Common file types
    PDF = "application/pdf"
    TEXT = "text/plain"
    HTML = "text/html"
    CSV = "text/csv"
    JSON = "application/json"
    XML = "application/xml"
    ZIP = "application/zip"

    # Microsoft Office
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

    # Images
    JPEG = "image/jpeg"
    PNG = "image/png"
    GIF = "image/gif"
    BMP = "image/bmp"
    WEBP = "image/webp"
    SVG = "image/svg+xml"

    @classmethod
    def from_extension(cls, ext: str) -> str:
        """Get MIME type from file extension."""
        ext = ext.lower().lstrip(".")
        mapping = {
            "pdf": cls.PDF,
            "txt": cls.TEXT,
            "html": cls.HTML,
            "htm": cls.HTML,
            "csv": cls.CSV,
            "json": cls.JSON,
            "xml": cls.XML,
            "zip": cls.ZIP,
            "docx": cls.DOCX,
            "xlsx": cls.XLSX,
            "pptx": cls.PPTX,
            "jpg": cls.JPEG,
            "jpeg": cls.JPEG,
            "png": cls.PNG,
            "gif": cls.GIF,
            "bmp": cls.BMP,
            "webp": cls.WEBP,
            "svg": cls.SVG,
        }
        return mapping.get(ext, "application/octet-stream")


@dataclass
class DriveConfig:
    """Configuration for Google Drive API client."""

    access_token: str
    base_url: str = "https://www.googleapis.com/drive/v3"
    upload_url: str = "https://www.googleapis.com/upload/drive/v3"
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0
    chunk_size: int = 256 * 1024  # 256KB chunks for resumable upload


@dataclass
class DriveFile:
    """Represents a Google Drive file or folder."""

    id: str
    name: str
    mime_type: str
    size: int | None = None
    created_time: str | None = None
    modified_time: str | None = None
    parents: list[str] = field(default_factory=list)
    web_view_link: str | None = None
    web_content_link: str | None = None
    description: str | None = None
    starred: bool = False
    trashed: bool = False
    shared: bool = False
    owners: list[dict] = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_response(cls, data: dict) -> "DriveFile":
        """Create DriveFile from API response."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            mime_type=data.get("mimeType", ""),
            size=int(data["size"]) if data.get("size") else None,
            created_time=data.get("createdTime"),
            modified_time=data.get("modifiedTime"),
            parents=data.get("parents", []),
            web_view_link=data.get("webViewLink"),
            web_content_link=data.get("webContentLink"),
            description=data.get("description"),
            starred=data.get("starred", False),
            trashed=data.get("trashed", False),
            shared=data.get("shared", False),
            owners=data.get("owners", []),
            raw=data,
        )

    @property
    def is_folder(self) -> bool:
        """Check if this is a folder."""
        return self.mime_type == DriveMimeType.FOLDER

    @property
    def is_google_doc(self) -> bool:
        """Check if this is a Google Workspace document."""
        return self.mime_type.startswith("application/vnd.google-apps.")


class GoogleDriveClient:
    """
    Async client for Google Drive API v3.

    Features:
    - File and folder CRUD operations
    - Resumable uploads for large files
    - Search and list with query support
    - Automatic retry on transient errors
    - Rate limiting awareness

    Usage:
        config = DriveConfig(access_token="ya29.xxx")
        client = GoogleDriveClient(config)

        async with client:
            files = await client.list_files(folder_id="root")
            file = await client.upload_file("document.pdf", folder_id="xxx")
    """

    # Standard fields to request for file metadata
    DEFAULT_FIELDS = (
        "id,name,mimeType,size,createdTime,modifiedTime,parents,"
        "webViewLink,webContentLink,description,starred,trashed,shared,owners"
    )

    def __init__(self, config: DriveConfig):
        """Initialize the Google Drive client."""
        self.config = config
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "GoogleDriveClient":
        """Enter async context manager."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        await self.close()

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure HTTP session exists with auth headers."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            headers = {
                "Authorization": f"Bearer {self.config.access_token}",
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
        params: dict | None = None,
        json_data: dict | None = None,
        data: bytes | None = None,
        headers: dict | None = None,
    ) -> dict:
        """Make a request to the Google Drive API."""
        session = await self._ensure_session()

        for attempt in range(self.config.max_retries):
            try:
                request_headers = headers.copy() if headers else {}

                async with session.request(
                    method,
                    url,
                    params=params,
                    json=json_data,
                    data=data,
                    headers=request_headers,
                ) as response:
                    # Handle rate limiting (403 with userRateLimitExceeded)
                    if response.status == 403:
                        result = await response.json()
                        error = result.get("error", {})
                        errors = error.get("errors", [])
                        if errors and errors[0].get("reason") == "userRateLimitExceeded":
                            wait_time = min(2**attempt, 32)
                            logger.warning(f"Rate limited. Waiting {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue

                    # Handle 5xx server errors (retry)
                    if response.status >= 500:
                        if attempt < self.config.max_retries - 1:
                            wait_time = self.config.retry_delay * (attempt + 1)
                            logger.warning(
                                f"Server error {response.status}. Retrying in {wait_time}s..."
                            )
                            await asyncio.sleep(wait_time)
                            continue

                    # Handle non-JSON responses (e.g., file downloads)
                    content_type = response.headers.get("Content-Type", "")
                    if "application/json" not in content_type:
                        if response.status == 200 or response.status == 204:
                            return {"_raw_content": await response.read()}
                        raise DriveAPIError(
                            f"HTTP error: {response.status}",
                            error_code=response.status,
                        )

                    result = await response.json()

                    # Handle API errors
                    if response.status >= 400:
                        error = result.get("error", {})
                        message = error.get("message", f"HTTP {response.status}")
                        code = error.get("code", response.status)
                        errors = error.get("errors", [])
                        reason = errors[0].get("reason") if errors else None

                        raise DriveAPIError(
                            f"Drive API error: {message}",
                            error_code=code,
                            reason=reason,
                        )

                    return result

            except aiohttp.ClientError as e:
                if attempt < self.config.max_retries - 1:
                    wait_time = self.config.retry_delay * (attempt + 1)
                    logger.warning(f"Network error (attempt {attempt + 1}): {e}. Retrying...")
                    await asyncio.sleep(wait_time)
                else:
                    raise DriveAPIError(f"Network error: {e}") from e

        raise DriveAPIError("Max retries exceeded")

    # =========================================================================
    # File Operations
    # =========================================================================

    async def get_file(
        self,
        file_id: str,
        fields: str | None = None,
    ) -> DriveFile:
        """
        Get file metadata by ID.

        Args:
            file_id: ID of the file
            fields: Comma-separated list of fields to return

        Returns:
            DriveFile with metadata
        """
        url = f"{self.config.base_url}/files/{file_id}"
        params = {"fields": fields or self.DEFAULT_FIELDS}

        result = await self._request("GET", url, params=params)
        return DriveFile.from_response(result)

    async def upload_file(
        self,
        file_path: str | Path,
        folder_id: str | None = None,
        name: str | None = None,
        mime_type: str | None = None,
        description: str | None = None,
        resumable: bool = True,
    ) -> DriveFile:
        """
        Upload a file to Google Drive.

        Args:
            file_path: Local path to the file
            folder_id: Parent folder ID (default: root)
            name: Name in Drive (default: local filename)
            mime_type: MIME type (auto-detected if not provided)
            description: File description
            resumable: Use resumable upload for large files

        Returns:
            DriveFile with uploaded file metadata
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise DriveAPIError(f"File not found: {file_path}")

        file_name = name or file_path.name
        file_mime_type = mime_type or DriveMimeType.from_extension(file_path.suffix)
        file_size = file_path.stat().st_size

        # Build metadata
        metadata: dict[str, Any] = {"name": file_name}
        if folder_id:
            metadata["parents"] = [folder_id]
        if description:
            metadata["description"] = description

        # Use resumable upload for files > 5MB
        if resumable and file_size > 5 * 1024 * 1024:
            return await self._resumable_upload(file_path, metadata, file_mime_type)

        # Simple multipart upload
        return await self._simple_upload(file_path, metadata, file_mime_type)

    async def _simple_upload(
        self,
        file_path: Path,
        metadata: dict,
        mime_type: str,
    ) -> DriveFile:
        """Simple multipart upload for smaller files."""
        session = await self._ensure_session()
        url = f"{self.config.upload_url}/files"

        params = {
            "uploadType": "multipart",
            "fields": self.DEFAULT_FIELDS,
        }

        # Build multipart request
        with aiohttp.MultipartWriter("related") as mpwriter:
            # Part 1: Metadata
            metadata_part = mpwriter.append_json(metadata)
            metadata_part.set_content_disposition("form-data", name="metadata")

            # Part 2: File content
            file_content = file_path.read_bytes()
            file_part = mpwriter.append(
                file_content,
                {"Content-Type": mime_type},
            )
            file_part.set_content_disposition("form-data", name="file", filename=file_path.name)

            async with session.post(url, params=params, data=mpwriter) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    raise DriveAPIError(
                        f"Upload failed: {error_text}",
                        error_code=response.status,
                    )
                result = await response.json()
                return DriveFile.from_response(result)

    async def _resumable_upload(
        self,
        file_path: Path,
        metadata: dict,
        mime_type: str,
    ) -> DriveFile:
        """Resumable upload for large files."""
        session = await self._ensure_session()
        url = f"{self.config.upload_url}/files"
        file_size = file_path.stat().st_size

        # Step 1: Initiate resumable upload session
        params = {
            "uploadType": "resumable",
            "fields": self.DEFAULT_FIELDS,
        }
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": mime_type,
            "X-Upload-Content-Length": str(file_size),
        }

        async with session.post(url, params=params, json=metadata, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                raise DriveAPIError(
                    f"Failed to initiate upload: {error_text}",
                    error_code=response.status,
                )
            upload_url = response.headers.get("Location")
            if not upload_url:
                raise DriveAPIError("No upload URL in response")

        # Step 2: Upload file in chunks
        chunk_size = self.config.chunk_size
        with open(file_path, "rb") as f:
            offset = 0
            while offset < file_size:
                chunk = f.read(chunk_size)
                chunk_end = offset + len(chunk) - 1

                headers = {
                    "Content-Type": mime_type,
                    "Content-Range": f"bytes {offset}-{chunk_end}/{file_size}",
                }

                async with session.put(upload_url, data=chunk, headers=headers) as response:
                    if response.status == 200 or response.status == 201:
                        # Upload complete
                        result = await response.json()
                        return DriveFile.from_response(result)
                    elif response.status == 308:
                        # Chunk uploaded, continue
                        range_header = response.headers.get("Range", "")
                        if range_header:
                            offset = int(range_header.split("-")[1]) + 1
                        else:
                            offset += len(chunk)
                    else:
                        error_text = await response.text()
                        raise DriveAPIError(
                            f"Chunk upload failed: {error_text}",
                            error_code=response.status,
                        )

        raise DriveAPIError("Upload did not complete")

    async def download_file(
        self,
        file_id: str,
        destination_path: str | Path,
    ) -> Path:
        """
        Download a file from Google Drive.

        Args:
            file_id: ID of the file to download
            destination_path: Local path to save the file

        Returns:
            Path to the downloaded file

        Note:
            Google Workspace files (Docs, Sheets, etc.) must be exported.
            Use export_file() for those.
        """
        destination = Path(destination_path)
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Get file to check type
        file_info = await self.get_file(file_id)

        if file_info.is_google_doc:
            raise DriveAPIError(
                f"Cannot download Google Workspace file directly. "
                f"Use export_file() instead. MIME type: {file_info.mime_type}"
            )

        url = f"{self.config.base_url}/files/{file_id}"
        params = {"alt": "media"}

        result = await self._request("GET", url, params=params)
        content = result.get("_raw_content", b"")

        destination.write_bytes(content)
        logger.info(f"Downloaded {file_info.name} to {destination}")

        return destination

    async def export_file(
        self,
        file_id: str,
        destination_path: str | Path,
        export_mime_type: str,
    ) -> Path:
        """
        Export a Google Workspace file to a specific format.

        Args:
            file_id: ID of the Google Workspace file
            destination_path: Local path to save the exported file
            export_mime_type: MIME type to export as (e.g., 'application/pdf')

        Returns:
            Path to the exported file

        Example:
            # Export Google Doc as PDF
            await client.export_file(doc_id, "report.pdf", DriveMimeType.PDF)

            # Export Google Sheet as XLSX
            await client.export_file(sheet_id, "data.xlsx", DriveMimeType.XLSX)
        """
        destination = Path(destination_path)
        destination.parent.mkdir(parents=True, exist_ok=True)

        url = f"{self.config.base_url}/files/{file_id}/export"
        params = {"mimeType": export_mime_type}

        result = await self._request("GET", url, params=params)
        content = result.get("_raw_content", b"")

        destination.write_bytes(content)
        logger.info(f"Exported file {file_id} to {destination}")

        return destination

    async def copy_file(
        self,
        file_id: str,
        new_name: str | None = None,
        folder_id: str | None = None,
    ) -> DriveFile:
        """
        Create a copy of a file.

        Args:
            file_id: ID of the file to copy
            new_name: Name for the copy (default: "Copy of {original}")
            folder_id: Parent folder for the copy

        Returns:
            DriveFile with the new file's metadata
        """
        url = f"{self.config.base_url}/files/{file_id}/copy"
        params = {"fields": self.DEFAULT_FIELDS}

        body: dict[str, Any] = {}
        if new_name:
            body["name"] = new_name
        if folder_id:
            body["parents"] = [folder_id]

        result = await self._request("POST", url, params=params, json_data=body)
        logger.info(f"Copied file {file_id} to {result.get('id')}")
        return DriveFile.from_response(result)

    async def move_file(
        self,
        file_id: str,
        new_folder_id: str,
    ) -> DriveFile:
        """
        Move a file to a different folder.

        Args:
            file_id: ID of the file to move
            new_folder_id: ID of the destination folder

        Returns:
            DriveFile with updated metadata
        """
        # Get current parents
        file_info = await self.get_file(file_id, fields="id,parents")
        current_parents = ",".join(file_info.parents) if file_info.parents else ""

        url = f"{self.config.base_url}/files/{file_id}"
        params = {
            "addParents": new_folder_id,
            "removeParents": current_parents,
            "fields": self.DEFAULT_FIELDS,
        }

        result = await self._request("PATCH", url, params=params)
        logger.info(f"Moved file {file_id} to folder {new_folder_id}")
        return DriveFile.from_response(result)

    async def rename_file(
        self,
        file_id: str,
        new_name: str,
    ) -> DriveFile:
        """
        Rename a file or folder.

        Args:
            file_id: ID of the file to rename
            new_name: New name for the file

        Returns:
            DriveFile with updated metadata
        """
        url = f"{self.config.base_url}/files/{file_id}"
        params = {"fields": self.DEFAULT_FIELDS}
        body = {"name": new_name}

        result = await self._request("PATCH", url, params=params, json_data=body)
        logger.info(f"Renamed file {file_id} to {new_name}")
        return DriveFile.from_response(result)

    async def delete_file(
        self,
        file_id: str,
        permanent: bool = False,
    ) -> bool:
        """
        Delete or trash a file.

        Args:
            file_id: ID of the file to delete
            permanent: If True, permanently delete. If False, move to trash.

        Returns:
            True if successful
        """
        if permanent:
            url = f"{self.config.base_url}/files/{file_id}"
            await self._request("DELETE", url)
            logger.info(f"Permanently deleted file {file_id}")
        else:
            url = f"{self.config.base_url}/files/{file_id}"
            body = {"trashed": True}
            await self._request("PATCH", url, json_data=body)
            logger.info(f"Moved file {file_id} to trash")

        return True

    async def update_file(
        self,
        file_id: str,
        name: str | None = None,
        description: str | None = None,
        starred: bool | None = None,
        trashed: bool | None = None,
    ) -> DriveFile:
        """
        Update file metadata.

        Args:
            file_id: ID of the file
            name: New name
            description: New description
            starred: Star/unstar
            trashed: Trash/restore

        Returns:
            DriveFile with updated metadata
        """
        url = f"{self.config.base_url}/files/{file_id}"
        params = {"fields": self.DEFAULT_FIELDS}

        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if starred is not None:
            body["starred"] = starred
        if trashed is not None:
            body["trashed"] = trashed

        result = await self._request("PATCH", url, params=params, json_data=body)
        return DriveFile.from_response(result)

    # =========================================================================
    # Folder Operations
    # =========================================================================

    async def create_folder(
        self,
        name: str,
        parent_id: str | None = None,
        description: str | None = None,
    ) -> DriveFile:
        """
        Create a new folder.

        Args:
            name: Folder name
            parent_id: Parent folder ID (default: root)
            description: Folder description

        Returns:
            DriveFile with the new folder's metadata
        """
        url = f"{self.config.base_url}/files"
        params = {"fields": self.DEFAULT_FIELDS}

        body: dict[str, Any] = {
            "name": name,
            "mimeType": DriveMimeType.FOLDER,
        }
        if parent_id:
            body["parents"] = [parent_id]
        if description:
            body["description"] = description

        result = await self._request("POST", url, params=params, json_data=body)
        logger.info(f"Created folder: {name} ({result.get('id')})")
        return DriveFile.from_response(result)

    async def list_files(
        self,
        folder_id: str | None = None,
        query: str | None = None,
        mime_type: str | None = None,
        page_size: int = 100,
        order_by: str = "name",
        include_trashed: bool = False,
        page_token: str | None = None,
    ) -> tuple[list[DriveFile], str | None]:
        """
        List files in a folder or matching a query.

        Args:
            folder_id: Folder to list (default: all accessible files)
            query: Custom search query (Drive API query syntax)
            mime_type: Filter by MIME type
            page_size: Max results per page (1-1000)
            order_by: Sort order (e.g., "name", "modifiedTime desc")
            include_trashed: Include trashed files
            page_token: Token for next page

        Returns:
            Tuple of (list of DriveFile, next_page_token or None)

        Example queries:
            "name contains 'report'"
            "mimeType = 'application/pdf'"
            "'folder_id' in parents and name contains 'budget'"
        """
        url = f"{self.config.base_url}/files"

        # Build query
        query_parts = []
        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")
        if mime_type:
            query_parts.append(f"mimeType = '{mime_type}'")
        if not include_trashed:
            query_parts.append("trashed = false")
        if query:
            query_parts.append(f"({query})")

        params = {
            "fields": f"nextPageToken,files({self.DEFAULT_FIELDS})",
            "pageSize": min(page_size, 1000),
            "orderBy": order_by,
        }
        if query_parts:
            params["q"] = " and ".join(query_parts)
        if page_token:
            params["pageToken"] = page_token

        result = await self._request("GET", url, params=params)

        files = [DriveFile.from_response(f) for f in result.get("files", [])]
        next_token = result.get("nextPageToken")

        return files, next_token

    async def search_files(
        self,
        query: str,
        mime_type: str | None = None,
        max_results: int = 100,
        include_trashed: bool = False,
    ) -> list[DriveFile]:
        """
        Search for files matching a query.

        Args:
            query: Search query (Drive API query syntax)
            mime_type: Filter by MIME type
            max_results: Maximum number of results
            include_trashed: Include trashed files

        Returns:
            List of matching DriveFile objects

        Example queries:
            "name contains 'budget' and mimeType = 'application/pdf'"
            "fullText contains 'quarterly report'"
            "modifiedTime > '2024-01-01T00:00:00'"
        """
        all_files: list[DriveFile] = []
        page_token: str | None = None

        while len(all_files) < max_results:
            page_size = min(100, max_results - len(all_files))
            files, page_token = await self.list_files(
                query=query,
                mime_type=mime_type,
                page_size=page_size,
                include_trashed=include_trashed,
                page_token=page_token,
            )
            all_files.extend(files)

            if not page_token:
                break

        return all_files[:max_results]

    # =========================================================================
    # Utility Methods
    # =========================================================================

    async def get_about(self) -> dict:
        """Get information about the user's Drive."""
        url = f"{self.config.base_url}/about"
        params = {"fields": "user,storageQuota"}
        return await self._request("GET", url, params=params)

    async def empty_trash(self) -> bool:
        """Permanently delete all trashed files."""
        url = f"{self.config.base_url}/files/trash"
        await self._request("DELETE", url)
        logger.info("Emptied trash")
        return True


__all__ = [
    "GoogleDriveClient",
    "DriveConfig",
    "DriveFile",
    "DriveAPIError",
    "DriveScope",
    "DriveMimeType",
]
