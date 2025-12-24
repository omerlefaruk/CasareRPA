"""
CasareRPA - Google Sheets API Client

Provides async client for Google Sheets API operations using service account
or OAuth 2.0 credentials.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import aiohttp
from loguru import logger


class GoogleSheetsError(Exception):
    """Base exception for Google Sheets operations."""

    def __init__(
        self,
        message: str,
        status_code: int = 0,
        error_details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.error_details = error_details or {}


class GoogleAuthError(GoogleSheetsError):
    """Authentication error with Google APIs."""

    pass


class GoogleRateLimitError(GoogleSheetsError):
    """Rate limit exceeded error."""

    pass


@dataclass
class GoogleSheetsConfig:
    """Configuration for Google Sheets client."""

    # Service account credentials JSON file path
    service_account_file: str = ""

    # Or provide credentials directly
    service_account_json: dict[str, Any] | None = None

    # Or use OAuth 2.0 access token
    access_token: str = ""

    # API key for read-only public sheets
    api_key: str = ""

    # Request configuration
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0

    def get_auth_method(self) -> str:
        """Determine which authentication method to use."""
        if self.access_token:
            return "oauth"
        if self.service_account_file or self.service_account_json:
            return "service_account"
        if self.api_key:
            return "api_key"
        return "none"


@dataclass
class SpreadsheetProperties:
    """Properties of a Google Spreadsheet."""

    spreadsheet_id: str
    title: str
    locale: str = ""
    auto_recalc: str = "ON_CHANGE"
    time_zone: str = "UTC"
    sheets: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SheetProperties:
    """Properties of a worksheet within a spreadsheet."""

    sheet_id: int
    title: str
    index: int = 0
    row_count: int = 1000
    column_count: int = 26
    frozen_row_count: int = 0
    frozen_column_count: int = 0


class GoogleSheetsClient:
    """
    Async client for Google Sheets API.

    Supports:
    - Service account authentication
    - OAuth 2.0 access tokens
    - API key for public sheets

    Usage:
        config = GoogleSheetsConfig(
            service_account_file="/path/to/credentials.json"
        )
        async with GoogleSheetsClient(config) as client:
            data = await client.get_values("spreadsheet_id", "Sheet1!A1:B10")
    """

    BASE_URL = "https://sheets.googleapis.com/v4/spreadsheets"
    AUTH_URL = "https://oauth2.googleapis.com/token"
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    def __init__(self, config: GoogleSheetsConfig) -> None:
        self.config = config
        self._session: aiohttp.ClientSession | None = None
        self._access_token: str | None = None
        self._token_expires_at: float = 0

    async def __aenter__(self) -> GoogleSheetsClient:
        """Enter async context."""
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        self._session = aiohttp.ClientSession(timeout=timeout)

        # Pre-authenticate if using service account
        if self.config.get_auth_method() == "service_account":
            await self._authenticate_service_account()
        elif self.config.get_auth_method() == "oauth":
            self._access_token = self.config.access_token

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context."""
        if self._session:
            await self._session.close()
            self._session = None

    async def _authenticate_service_account(self) -> None:
        """Authenticate using service account credentials."""
        try:
            import time

            import jwt

            # Load service account credentials
            creds = self.config.service_account_json
            if not creds and self.config.service_account_file:
                creds_path = Path(self.config.service_account_file)
                if creds_path.exists():
                    creds = json.loads(creds_path.read_text())

            if not creds:
                raise GoogleAuthError(
                    "No service account credentials found. "
                    "Provide service_account_file or service_account_json."
                )

            # Create JWT
            now = int(time.time())
            claim_set = {
                "iss": creds["client_email"],
                "scope": " ".join(self.SCOPES),
                "aud": self.AUTH_URL,
                "iat": now,
                "exp": now + 3600,  # 1 hour
            }

            # Sign JWT with private key
            signed_jwt = jwt.encode(
                claim_set,
                creds["private_key"],
                algorithm="RS256",
            )

            # Exchange JWT for access token
            async with self._session.post(
                self.AUTH_URL,
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": signed_jwt,
                },
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise GoogleAuthError(
                        f"Failed to authenticate: {error_text}",
                        status_code=response.status,
                    )

                token_data = await response.json()
                self._access_token = token_data["access_token"]
                self._token_expires_at = now + token_data.get("expires_in", 3600)

            logger.debug("Google Sheets service account authentication successful")

        except ImportError:
            raise GoogleAuthError(
                "PyJWT package required for service account auth. "
                "Install with: pip install PyJWT"
            )
        except Exception as e:
            if isinstance(e, GoogleAuthError):
                raise
            raise GoogleAuthError(f"Service account authentication failed: {e}") from e

    def _get_headers(self, use_api_key: bool = False) -> dict[str, str]:
        """Get request headers with authentication.

        Args:
            use_api_key: If True, use API key header instead of OAuth token

        Returns:
            Dict with appropriate authentication headers
        """
        headers = {"Content-Type": "application/json"}

        if use_api_key and self.config.api_key:
            # Use header-based API key auth (more secure than URL query param)
            headers["X-Goog-Api-Key"] = self.config.api_key
        elif self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        return headers

    def _get_url(self, endpoint: str) -> str:
        """Build API URL.

        Args:
            endpoint: API endpoint path

        Returns:
            Full API URL
        """
        return f"{self.BASE_URL}{endpoint}"

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make authenticated API request with retry logic."""
        if not self._session:
            raise GoogleSheetsError("Client not initialized. Use async context manager.")

        use_api_key = self.config.get_auth_method() == "api_key"
        url = self._get_url(endpoint)
        headers = self._get_headers(use_api_key=use_api_key)

        last_error: Exception | None = None

        for attempt in range(max(1, self.config.max_retries)):
            try:
                async with self._session.request(
                    method,
                    url,
                    json=data,
                    params=params,
                    headers=headers,
                ) as response:
                    response_text = await response.text()

                    if response.status == 429:
                        # Rate limit - retry with exponential backoff
                        if attempt < self.config.max_retries - 1:
                            delay = self.config.retry_delay * (2**attempt)
                            logger.warning(
                                f"Rate limited. Retrying in {delay:.1f}s "
                                f"(attempt {attempt + 1}/{self.config.max_retries})"
                            )
                            await asyncio.sleep(delay)
                            continue
                        raise GoogleRateLimitError(
                            "Rate limit exceeded",
                            status_code=429,
                        )

                    if response.status >= 400:
                        try:
                            error_data = json.loads(response_text)
                            error_message = error_data.get("error", {}).get(
                                "message", response_text
                            )
                        except json.JSONDecodeError:
                            error_message = response_text

                        raise GoogleSheetsError(
                            f"API error: {error_message}",
                            status_code=response.status,
                            error_details=error_data if "error_data" in locals() else {},
                        )

                    if response_text:
                        return json.loads(response_text)
                    return {}

            except aiohttp.ClientError as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay)
                else:
                    raise GoogleSheetsError(f"Network error: {e}") from e

        if last_error:
            raise GoogleSheetsError(f"Request failed after {self.config.max_retries} attempts")
        return {}

    # =========================================================================
    # Spreadsheet Operations
    # =========================================================================

    async def create_spreadsheet(
        self,
        title: str,
        sheets: list[str] | None = None,
        locale: str = "en_US",
    ) -> SpreadsheetProperties:
        """
        Create a new spreadsheet.

        Args:
            title: Spreadsheet title
            sheets: List of sheet names to create (default: ["Sheet1"])
            locale: Locale string (e.g., "en_US")

        Returns:
            SpreadsheetProperties with spreadsheet_id and details
        """
        sheet_list = sheets or ["Sheet1"]

        request_body = {
            "properties": {
                "title": title,
                "locale": locale,
            },
            "sheets": [{"properties": {"title": name}} for name in sheet_list],
        }

        result = await self._request("POST", "", data=request_body)

        props = result.get("properties", {})
        return SpreadsheetProperties(
            spreadsheet_id=result.get("spreadsheetId", ""),
            title=props.get("title", title),
            locale=props.get("locale", locale),
            time_zone=props.get("timeZone", "UTC"),
            sheets=result.get("sheets", []),
        )

    async def get_spreadsheet(
        self,
        spreadsheet_id: str,
        include_grid_data: bool = False,
    ) -> SpreadsheetProperties:
        """
        Get spreadsheet metadata.

        Args:
            spreadsheet_id: Spreadsheet ID
            include_grid_data: Include cell data in response

        Returns:
            SpreadsheetProperties
        """
        params = {}
        if include_grid_data:
            params["includeGridData"] = "true"

        result = await self._request(
            "GET",
            f"/{spreadsheet_id}",
            params=params,
        )

        props = result.get("properties", {})
        return SpreadsheetProperties(
            spreadsheet_id=result.get("spreadsheetId", spreadsheet_id),
            title=props.get("title", ""),
            locale=props.get("locale", ""),
            time_zone=props.get("timeZone", "UTC"),
            sheets=result.get("sheets", []),
        )

    async def add_sheet(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        row_count: int = 1000,
        column_count: int = 26,
    ) -> SheetProperties:
        """
        Add a new sheet to an existing spreadsheet.

        Args:
            spreadsheet_id: Spreadsheet ID
            sheet_name: Name for the new sheet
            row_count: Initial row count
            column_count: Initial column count

        Returns:
            SheetProperties of created sheet
        """
        request_body = {
            "requests": [
                {
                    "addSheet": {
                        "properties": {
                            "title": sheet_name,
                            "gridProperties": {
                                "rowCount": row_count,
                                "columnCount": column_count,
                            },
                        }
                    }
                }
            ]
        }

        result = await self._request(
            "POST",
            f"/{spreadsheet_id}:batchUpdate",
            data=request_body,
        )

        replies = result.get("replies", [{}])
        add_sheet_reply = replies[0].get("addSheet", {})
        props = add_sheet_reply.get("properties", {})

        return SheetProperties(
            sheet_id=props.get("sheetId", 0),
            title=props.get("title", sheet_name),
            index=props.get("index", 0),
            row_count=props.get("gridProperties", {}).get("rowCount", row_count),
            column_count=props.get("gridProperties", {}).get("columnCount", column_count),
        )

    async def delete_sheet(
        self,
        spreadsheet_id: str,
        sheet_id: int,
    ) -> bool:
        """
        Delete a sheet from a spreadsheet.

        Args:
            spreadsheet_id: Spreadsheet ID
            sheet_id: Numeric sheet ID to delete

        Returns:
            True if successful
        """
        request_body = {
            "requests": [
                {
                    "deleteSheet": {
                        "sheetId": sheet_id,
                    }
                }
            ]
        }

        await self._request(
            "POST",
            f"/{spreadsheet_id}:batchUpdate",
            data=request_body,
        )

        logger.debug(f"Deleted sheet {sheet_id} from {spreadsheet_id}")
        return True

    async def copy_sheet(
        self,
        source_spreadsheet_id: str,
        source_sheet_id: int,
        destination_spreadsheet_id: str,
    ) -> SheetProperties:
        """
        Copy a sheet to another spreadsheet.

        Args:
            source_spreadsheet_id: Source spreadsheet ID
            source_sheet_id: Sheet ID to copy
            destination_spreadsheet_id: Destination spreadsheet ID

        Returns:
            SheetProperties of the new sheet
        """
        request_body = {
            "destinationSpreadsheetId": destination_spreadsheet_id,
        }

        result = await self._request(
            "POST",
            f"/{source_spreadsheet_id}/sheets/{source_sheet_id}:copyTo",
            data=request_body,
        )

        return SheetProperties(
            sheet_id=result.get("sheetId", 0),
            title=result.get("title", ""),
            index=result.get("index", 0),
        )

    # =========================================================================
    # Data Operations
    # =========================================================================

    async def get_values(
        self,
        spreadsheet_id: str,
        range_notation: str,
        value_render_option: str = "FORMATTED_VALUE",
        date_time_render_option: str = "SERIAL_NUMBER",
    ) -> list[list[Any]]:
        """
        Get values from a range.

        Args:
            spreadsheet_id: Spreadsheet ID
            range_notation: A1 notation range (e.g., "Sheet1!A1:B10")
            value_render_option: How to render values
            date_time_render_option: How to render dates

        Returns:
            2D list of cell values
        """
        params = {
            "valueRenderOption": value_render_option,
            "dateTimeRenderOption": date_time_render_option,
        }

        result = await self._request(
            "GET",
            f"/{spreadsheet_id}/values/{range_notation}",
            params=params,
        )

        return result.get("values", [])

    async def update_values(
        self,
        spreadsheet_id: str,
        range_notation: str,
        values: list[list[Any]],
        value_input_option: str = "USER_ENTERED",
    ) -> dict[str, Any]:
        """
        Update values in a range.

        Args:
            spreadsheet_id: Spreadsheet ID
            range_notation: A1 notation range
            values: 2D list of values to write
            value_input_option: How to interpret input

        Returns:
            Update response with updated cells info
        """
        request_body = {
            "range": range_notation,
            "values": values,
        }

        params = {"valueInputOption": value_input_option}

        result = await self._request(
            "PUT",
            f"/{spreadsheet_id}/values/{range_notation}",
            data=request_body,
            params=params,
        )

        return result

    async def append_values(
        self,
        spreadsheet_id: str,
        range_notation: str,
        values: list[list[Any]],
        value_input_option: str = "USER_ENTERED",
        insert_data_option: str = "INSERT_ROWS",
    ) -> dict[str, Any]:
        """
        Append values to a range.

        Args:
            spreadsheet_id: Spreadsheet ID
            range_notation: A1 notation range to append to
            values: 2D list of values to append
            value_input_option: How to interpret input
            insert_data_option: Whether to insert rows or overwrite

        Returns:
            Append response with updated range info
        """
        request_body = {
            "range": range_notation,
            "values": values,
        }

        params = {
            "valueInputOption": value_input_option,
            "insertDataOption": insert_data_option,
        }

        result = await self._request(
            "POST",
            f"/{spreadsheet_id}/values/{range_notation}:append",
            data=request_body,
            params=params,
        )

        return result

    async def clear_values(
        self,
        spreadsheet_id: str,
        range_notation: str,
    ) -> dict[str, Any]:
        """
        Clear values from a range.

        Args:
            spreadsheet_id: Spreadsheet ID
            range_notation: A1 notation range to clear

        Returns:
            Clear response
        """
        result = await self._request(
            "POST",
            f"/{spreadsheet_id}/values/{range_notation}:clear",
        )

        return result

    # =========================================================================
    # Batch Operations
    # =========================================================================

    async def batch_get_values(
        self,
        spreadsheet_id: str,
        ranges: list[str],
        value_render_option: str = "FORMATTED_VALUE",
    ) -> dict[str, list[list[Any]]]:
        """
        Get values from multiple ranges in one request.

        Args:
            spreadsheet_id: Spreadsheet ID
            ranges: List of A1 notation ranges
            value_render_option: How to render values

        Returns:
            Dictionary mapping range to values
        """
        params = {
            "ranges": ranges,
            "valueRenderOption": value_render_option,
        }

        result = await self._request(
            "GET",
            f"/{spreadsheet_id}/values:batchGet",
            params=params,
        )

        # Convert to dict mapping range -> values
        output = {}
        for value_range in result.get("valueRanges", []):
            range_name = value_range.get("range", "")
            output[range_name] = value_range.get("values", [])

        return output

    async def batch_update_values(
        self,
        spreadsheet_id: str,
        data: list[dict[str, Any]],
        value_input_option: str = "USER_ENTERED",
    ) -> dict[str, Any]:
        """
        Update multiple ranges in one request.

        Args:
            spreadsheet_id: Spreadsheet ID
            data: List of {range, values} dicts
            value_input_option: How to interpret input

        Returns:
            Batch update response
        """
        request_body = {
            "valueInputOption": value_input_option,
            "data": data,
        }

        result = await self._request(
            "POST",
            f"/{spreadsheet_id}/values:batchUpdate",
            data=request_body,
        )

        return result

    async def batch_clear_values(
        self,
        spreadsheet_id: str,
        ranges: list[str],
    ) -> dict[str, Any]:
        """
        Clear multiple ranges in one request.

        Args:
            spreadsheet_id: Spreadsheet ID
            ranges: List of A1 notation ranges to clear

        Returns:
            Batch clear response
        """
        request_body = {
            "ranges": ranges,
        }

        result = await self._request(
            "POST",
            f"/{spreadsheet_id}/values:batchClear",
            data=request_body,
        )

        return result

    async def batch_update(
        self,
        spreadsheet_id: str,
        requests: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Execute batch spreadsheet updates (formatting, structure, etc.).

        Args:
            spreadsheet_id: Spreadsheet ID
            requests: List of update requests

        Returns:
            Batch update response with replies
        """
        request_body = {
            "requests": requests,
        }

        result = await self._request(
            "POST",
            f"/{spreadsheet_id}:batchUpdate",
            data=request_body,
        )

        return result

    # =========================================================================
    # Utility Methods
    # =========================================================================

    async def get_sheet_row_count(
        self,
        spreadsheet_id: str,
        sheet_name: str,
    ) -> int:
        """
        Get the number of rows with data in a sheet.

        Args:
            spreadsheet_id: Spreadsheet ID
            sheet_name: Sheet name

        Returns:
            Number of rows with data
        """
        # Get all values in column A to count rows
        values = await self.get_values(spreadsheet_id, f"{sheet_name}!A:A")
        return len(values)

    async def get_sheet_by_name(
        self,
        spreadsheet_id: str,
        sheet_name: str,
    ) -> SheetProperties | None:
        """
        Get sheet properties by name.

        Args:
            spreadsheet_id: Spreadsheet ID
            sheet_name: Sheet name to find

        Returns:
            SheetProperties or None if not found
        """
        spreadsheet = await self.get_spreadsheet(spreadsheet_id)

        for sheet in spreadsheet.sheets:
            props = sheet.get("properties", {})
            if props.get("title") == sheet_name:
                return SheetProperties(
                    sheet_id=props.get("sheetId", 0),
                    title=props.get("title", ""),
                    index=props.get("index", 0),
                    row_count=props.get("gridProperties", {}).get("rowCount", 1000),
                    column_count=props.get("gridProperties", {}).get("columnCount", 26),
                )

        return None


__all__ = [
    "GoogleSheetsClient",
    "GoogleSheetsConfig",
    "GoogleSheetsError",
    "GoogleAuthError",
    "GoogleRateLimitError",
    "SpreadsheetProperties",
    "SheetProperties",
]
