"""
Google API Picker Widgets for CasareRPA.

Concrete implementations of CascadingDropdownBase for Google APIs:
- GoogleSpreadsheetPicker: Fetches spreadsheets from Google Drive
- GoogleSheetPicker: Fetches sheets within a spreadsheet
- GoogleDriveFilePicker: Fetches files from Google Drive

All pickers use async aiohttp for API calls and the GoogleOAuthManager
for token management.
"""

from __future__ import annotations

from typing import Any

from loguru import logger
from PySide6.QtWidgets import QWidget

from casare_rpa.presentation.canvas.ui.widgets.cascading_dropdown import (
    CascadingDropdownBase,
    DropdownItem,
)

# Google API endpoints
DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
SHEETS_API_BASE = "https://sheets.googleapis.com/v4"


def _get_http_client() -> Any:
    """Get configured UnifiedHttpClient for Google API calls."""
    from casare_rpa.infrastructure.http import UnifiedHttpClient, UnifiedHttpClientConfig

    # Configure client for external Google APIs (SSRF protection enabled)
    return UnifiedHttpClient(
        UnifiedHttpClientConfig(
            enable_ssrf_protection=True,
            max_retries=2,
            default_timeout=30.0,
        )
    )


async def _get_access_token(credential_id: str) -> str:
    """Get a valid access token for the credential."""
    from casare_rpa.infrastructure.security.google_oauth import (
        get_google_access_token,
    )

    return await get_google_access_token(credential_id)


class GoogleSpreadsheetPicker(CascadingDropdownBase):
    """
    Picker for Google Spreadsheets.

    Fetches spreadsheets from Google Drive API filtered by MIME type.
    Parent: credential picker (set via set_parent_value with credential_id)

    Usage:
        picker = GoogleSpreadsheetPicker()
        picker.set_parent_value(credential_id)  # Triggers load
        picker.selection_changed.connect(on_spreadsheet_selected)
    """

    SPREADSHEET_MIME_TYPE = "application/vnd.google-apps.spreadsheet"

    def __init__(
        self,
        parent: QWidget | None = None,
        cache_ttl: float = 300.0,
        max_results: int = 100,
    ) -> None:
        super().__init__(parent=parent, cache_ttl=cache_ttl)
        self._max_results = max_results

    async def _fetch_items(self) -> list[DropdownItem]:
        """Fetch spreadsheets from Google Drive API."""
        credential_id = self._parent_value

        if not credential_id:
            logger.debug("No credential ID set for spreadsheet picker")
            return []

        try:
            access_token = await _get_access_token(credential_id)

            # Build Drive API query
            query = f"mimeType='{self.SPREADSHEET_MIME_TYPE}' and trashed=false"
            params = {
                "q": query,
                "pageSize": self._max_results,
                "fields": "files(id,name,modifiedTime,owners)",
                "orderBy": "modifiedTime desc",
            }

            headers = {
                "Authorization": f"Bearer {access_token}",
            }

            async with _get_http_client() as http_client:
                url = f"{DRIVE_API_BASE}/files"
                response = await http_client.get(url, params=params, headers=headers)
                if response.status == 401:
                    raise Exception("Authentication failed - token may be expired")
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API error ({response.status}): {error_text}")

                data = await response.json()

            files = data.get("files", [])
            logger.debug(f"Fetched {len(files)} spreadsheets")

            items = []
            for file in files:
                file_id = file.get("id", "")
                name = file.get("name", "Untitled")

                # Include owner info if available
                owners = file.get("owners", [])
                owner_email = ""
                if owners:
                    owner_email = owners[0].get("emailAddress", "")

                items.append(
                    DropdownItem(
                        id=file_id,
                        label=name,
                        data={
                            "name": name,
                            "modifiedTime": file.get("modifiedTime", ""),
                            "owner": owner_email,
                        },
                    )
                )

            return items

        except Exception as e:
            logger.error(f"Failed to fetch spreadsheets: {e}")
            raise

    def get_spreadsheet_id(self) -> str | None:
        """Convenience alias for get_selected_id()."""
        return self.get_selected_id()


class GoogleSheetPicker(CascadingDropdownBase):
    """
    Picker for sheets within a Google Spreadsheet.

    Fetches individual sheet tabs from Google Sheets API.
    Parent: spreadsheet picker (set via set_parent_value with spreadsheet_id)
    Also requires credential_id to be set via set_credential_id().

    Usage:
        picker = GoogleSheetPicker()
        picker.set_credential_id(credential_id)
        picker.set_parent_value(spreadsheet_id)  # Triggers load
        picker.selection_changed.connect(on_sheet_selected)
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        cache_ttl: float = 300.0,
    ) -> None:
        super().__init__(parent=parent, cache_ttl=cache_ttl)
        self._credential_id: str | None = None

    def set_credential_id(self, credential_id: str) -> None:
        """
        Set the credential ID for API authentication.

        This must be called before set_parent_value().

        Args:
            credential_id: Google OAuth credential ID
        """
        self._credential_id = credential_id

    def _get_cache_key(self) -> str:
        """Include credential ID in cache key."""
        return f"{self._credential_id}:{self._parent_value}"

    async def _fetch_items(self) -> list[DropdownItem]:
        """Fetch sheets from Google Sheets API."""
        spreadsheet_id = self._parent_value
        credential_id = self._credential_id

        if not credential_id:
            logger.debug("No credential ID set for sheet picker")
            return []

        if not spreadsheet_id:
            logger.debug("No spreadsheet ID set for sheet picker")
            return []

        try:
            access_token = await _get_access_token(credential_id)

            headers = {
                "Authorization": f"Bearer {access_token}",
            }

            # Get spreadsheet metadata including sheet list
            url = f"{SHEETS_API_BASE}/spreadsheets/{spreadsheet_id}"
            params = {
                "fields": "sheets.properties",
            }

            async with _get_http_client() as http_client:
                response = await http_client.get(url, params=params, headers=headers)
                if response.status == 401:
                    raise Exception("Authentication failed - token may be expired")
                if response.status == 404:
                    raise Exception("Spreadsheet not found")
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API error ({response.status}): {error_text}")

                data = await response.json()

            sheets = data.get("sheets", [])
            logger.debug(f"Fetched {len(sheets)} sheets from spreadsheet")

            items = []
            for sheet in sheets:
                props = sheet.get("properties", {})
                sheet_id = props.get("sheetId", 0)
                title = props.get("title", "Sheet")
                index = props.get("index", 0)

                # Get grid properties if available
                grid_props = props.get("gridProperties", {})
                row_count = grid_props.get("rowCount", 0)
                col_count = grid_props.get("columnCount", 0)

                items.append(
                    DropdownItem(
                        id=str(sheet_id),
                        label=title,
                        data={
                            "title": title,
                            "sheetId": sheet_id,
                            "index": index,
                            "rowCount": row_count,
                            "columnCount": col_count,
                        },
                    )
                )

            # Sort by index
            items.sort(key=lambda x: x.data.get("index", 0))

            return items

        except Exception as e:
            logger.error(f"Failed to fetch sheets: {e}")
            raise

    def get_sheet_id(self) -> int | None:
        """Get the selected sheet ID as integer."""
        sheet_id = self.get_selected_id()
        if sheet_id:
            try:
                return int(sheet_id)
            except ValueError:
                pass
        return None

    def get_sheet_title(self) -> str:
        """Get the selected sheet title."""
        item = self.get_selected_item()
        if item and item.data:
            return item.data.get("title", "")
        return self.get_selected_label()


class GoogleDriveFilePicker(CascadingDropdownBase):
    """
    Picker for files from Google Drive.

    Fetches files from Google Drive API with optional MIME type filter.
    Parent: credential picker (set via set_parent_value with credential_id)

    Usage:
        picker = GoogleDriveFilePicker(mime_type="application/pdf")
        picker.set_parent_value(credential_id)  # Triggers load
        picker.selection_changed.connect(on_file_selected)
    """

    # Common MIME types
    MIME_TYPES: dict[str, str] = {
        "spreadsheet": "application/vnd.google-apps.spreadsheet",
        "document": "application/vnd.google-apps.document",
        "presentation": "application/vnd.google-apps.presentation",
        "folder": "application/vnd.google-apps.folder",
        "pdf": "application/pdf",
        "image": "image/",  # Prefix match
        "video": "video/",  # Prefix match
    }

    def __init__(
        self,
        parent: QWidget | None = None,
        cache_ttl: float = 300.0,
        mime_type: str | None = None,
        folder_id: str | None = None,
        max_results: int = 100,
        include_shared: bool = True,
    ) -> None:
        """
        Initialize Drive file picker.

        Args:
            parent: Parent widget
            cache_ttl: Cache TTL in seconds
            mime_type: Filter by MIME type (exact or prefix with trailing /)
            folder_id: Filter by parent folder ID
            max_results: Maximum number of files to fetch
            include_shared: Include files shared with the user
        """
        super().__init__(parent=parent, cache_ttl=cache_ttl)
        self._mime_type = mime_type
        self._folder_id = folder_id
        self._max_results = max_results
        self._include_shared = include_shared

    def set_mime_type(self, mime_type: str | None) -> None:
        """Set the MIME type filter."""
        if mime_type != self._mime_type:
            self._mime_type = mime_type
            self.clear_cache()
            if self._parent_value:
                self.refresh()

    def set_folder_id(self, folder_id: str | None) -> None:
        """Set the folder ID filter."""
        if folder_id != self._folder_id:
            self._folder_id = folder_id
            self.clear_cache()
            if self._parent_value:
                self.refresh()

    def _get_cache_key(self) -> str:
        """Include filters in cache key."""
        return f"{self._parent_value}:{self._mime_type}:{self._folder_id}"

    async def _fetch_items(self) -> list[DropdownItem]:
        """Fetch files from Google Drive API."""
        credential_id = self._parent_value

        if not credential_id:
            logger.debug("No credential ID set for drive picker")
            return []

        try:
            access_token = await _get_access_token(credential_id)

            # Build query
            query_parts = ["trashed=false"]

            if self._mime_type:
                if self._mime_type.endswith("/"):
                    # Prefix match (e.g., "image/")
                    query_parts.append(f"mimeType contains '{self._mime_type}'")
                else:
                    # Exact match
                    query_parts.append(f"mimeType='{self._mime_type}'")

            if self._folder_id:
                query_parts.append(f"'{self._folder_id}' in parents")

            query = " and ".join(query_parts)

            params = {
                "q": query,
                "pageSize": self._max_results,
                "fields": "files(id,name,mimeType,modifiedTime,size,iconLink)",
                "orderBy": "modifiedTime desc",
            }

            if self._include_shared:
                params["includeItemsFromAllDrives"] = "true"
                params["supportsAllDrives"] = "true"

            headers = {
                "Authorization": f"Bearer {access_token}",
            }

            async with _get_http_client() as http_client:
                url = f"{DRIVE_API_BASE}/files"
                response = await http_client.get(url, params=params, headers=headers)
                if response.status == 401:
                    raise Exception("Authentication failed - token may be expired")
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API error ({response.status}): {error_text}")

                data = await response.json()

            files = data.get("files", [])
            logger.debug(f"Fetched {len(files)} files from Drive")

            items = []
            for file in files:
                file_id = file.get("id", "")
                name = file.get("name", "Untitled")
                mime_type = file.get("mimeType", "")
                size = file.get("size", 0)

                # Format size for display
                size_str = self._format_file_size(int(size) if size else 0)

                # Add file type indicator to label
                type_indicator = self._get_type_indicator(mime_type)
                label = f"{type_indicator} {name}" if type_indicator else name

                items.append(
                    DropdownItem(
                        id=file_id,
                        label=label,
                        data={
                            "name": name,
                            "mimeType": mime_type,
                            "modifiedTime": file.get("modifiedTime", ""),
                            "size": size,
                            "sizeFormatted": size_str,
                            "iconLink": file.get("iconLink", ""),
                        },
                    )
                )

            return items

        except Exception as e:
            logger.error(f"Failed to fetch Drive files: {e}")
            raise

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size for display."""
        if size_bytes == 0:
            return ""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def _get_type_indicator(self, mime_type: str) -> str:
        """Get a visual indicator for file type."""
        if not mime_type:
            return ""

        if "spreadsheet" in mime_type:
            return "[Sheet]"
        elif "document" in mime_type:
            return "[Doc]"
        elif "presentation" in mime_type:
            return "[Slides]"
        elif "folder" in mime_type:
            return "[Folder]"
        elif mime_type.startswith("image/"):
            return "[Image]"
        elif mime_type.startswith("video/"):
            return "[Video]"
        elif mime_type == "application/pdf":
            return "[PDF]"
        else:
            return ""

    def get_file_id(self) -> str | None:
        """Convenience alias for get_selected_id()."""
        return self.get_selected_id()

    def get_file_name(self) -> str:
        """Get the selected file name (without type indicator)."""
        item = self.get_selected_item()
        if item and item.data:
            return item.data.get("name", "")
        return ""


class GoogleDriveFolderPicker(GoogleDriveFilePicker):
    """
    Picker specifically for Google Drive folders.

    Convenience subclass that pre-filters to folders only.
    Shows only user's own folders (not shared) by default.
    Includes "Root (My Drive)" as the first option.
    """

    # Special ID for root folder selection
    ROOT_FOLDER_ID: str = "root"

    def __init__(
        self,
        parent: QWidget | None = None,
        cache_ttl: float = 300.0,
        parent_folder_id: str | None = None,
        max_results: int = 100,
    ) -> None:
        super().__init__(
            parent=parent,
            cache_ttl=cache_ttl,
            mime_type="application/vnd.google-apps.folder",
            folder_id=parent_folder_id,
            max_results=max_results,
            include_shared=False,  # Only show user's own folders
        )

    async def _fetch_items(self) -> list[DropdownItem]:
        """Fetch folders with 'Root (My Drive)' as first option."""
        # Start with root folder option
        items = [
            DropdownItem(
                id=self.ROOT_FOLDER_ID,
                label="[Root] My Drive",
                data={"name": "My Drive", "isRoot": True},
            )
        ]

        # Fetch user's folders
        try:
            fetched = await super()._fetch_items()
            items.extend(fetched)
        except Exception as e:
            logger.error(f"Failed to fetch folders: {e}")
            # Still return root option even if fetch fails

        return items

    def get_folder_id(self) -> str | None:
        """Convenience alias for get_selected_id()."""
        return self.get_selected_id()

    def get_folder_name(self) -> str:
        """Get the selected folder name."""
        return self.get_file_name()


__all__ = [
    "GoogleSpreadsheetPicker",
    "GoogleSheetPicker",
    "GoogleDriveFilePicker",
    "GoogleDriveFolderPicker",
]
