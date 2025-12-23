"""
CasareRPA - Google Sheets Trigger

Trigger that fires when changes are detected in a Google Sheets spreadsheet.
Uses Google Sheets API with OAuth 2.0 authentication.

Supports watch modes:
- new_rows: Trigger only when new rows are added
- any_change: Trigger when any cell value changes
- content: Trigger on content changes (same as any_change)
- structure: Trigger on structural changes (via Drive API)
- any: Trigger on any type of change
"""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from loguru import logger

from casare_rpa.triggers.base import BaseTriggerConfig, TriggerType
from casare_rpa.triggers.implementations.google_trigger_base import GoogleTriggerBase
from casare_rpa.triggers.registry import register_trigger


@register_trigger
class SheetsTrigger(GoogleTriggerBase):
    """
    Trigger that monitors Google Sheets for changes.

    Configuration options:
        client_id: Google OAuth client ID
        client_secret_credential: Credential alias for client secret
        access_token_credential: Credential alias for access token
        refresh_token_credential: Credential alias for refresh token
        spreadsheet_id: Google Sheets spreadsheet ID
        sheet_name: Specific sheet to monitor (optional, monitors all if not specified)
        range: Cell range to monitor (e.g., 'A1:Z100')
        watch_mode: Watch mode - new_rows | any_change | content | structure | any
        change_types: Legacy alias for watch_mode (deprecated)
        include_values: Include changed cell values in payload
        poll_interval: Polling interval in seconds (default: 60)

    Payload provided to workflow:
        spreadsheet_id: ID of the spreadsheet
        spreadsheet_title: Title of the spreadsheet
        sheet_name: Name of the changed sheet
        change_type: Type of change detected (new_row, content, structure)
        row_number: Row number for new_rows mode
        values: Changed values (row values for new_rows, range values for others)
        previous_values: Previous values (for any_change mode)
        row_count: Number of rows in the monitored range
        column_count: Number of columns in the monitored range
        timestamp: When the change was detected
    """

    trigger_type = TriggerType.SHEETS
    display_name = "Sheets: Row Changed"
    description = "Trigger when spreadsheet changes"
    icon = "spreadsheet"
    category = "Google"

    SHEETS_API_BASE = "https://sheets.googleapis.com/v4/spreadsheets"
    DRIVE_API_BASE = "https://www.googleapis.com/drive/v3/files"

    def __init__(self, config: BaseTriggerConfig, event_callback=None):
        super().__init__(config, event_callback)
        self._last_content_hash: str | None = None
        self._last_modified_time: str | None = None
        self._spreadsheet_title: str | None = None
        # State for new_rows mode
        self._last_row_count: int = 0
        self._last_values: list[list[Any]] = []
        self._initialized: bool = False

    def get_required_scopes(self) -> list[str]:
        """Return required Google Sheets API scopes."""
        return [
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.metadata.readonly",
        ]

    async def start(self) -> bool:
        """Start the Sheets trigger."""
        result = await super().start()
        if result:
            # Initialize by capturing current state
            try:
                await self._capture_initial_state()
            except Exception as e:
                logger.warning(f"Failed to capture initial Sheets state: {e}")
        return result

    async def _capture_initial_state(self) -> None:
        """Capture initial spreadsheet state for change detection."""
        client = await self._get_google_client()
        config = self.config.config
        spreadsheet_id = config.get("spreadsheet_id", "")

        if not spreadsheet_id:
            raise ValueError("spreadsheet_id is required")

        # Get spreadsheet metadata
        metadata = await client.get(f"{self.SHEETS_API_BASE}/{spreadsheet_id}")
        self._spreadsheet_title = metadata.get("properties", {}).get("title", "")

        # Get last modified time from Drive API
        drive_metadata = await client.get(
            f"{self.DRIVE_API_BASE}/{spreadsheet_id}",
            params={"fields": "modifiedTime"},
        )
        self._last_modified_time = drive_metadata.get("modifiedTime")

        # Get current values for new_rows and any_change modes
        range_spec = self._get_range_spec()
        try:
            response = await client.get(
                f"{self.SHEETS_API_BASE}/{spreadsheet_id}/values/{range_spec}"
            )
            self._last_values = response.get("values", [])
            self._last_row_count = len(self._last_values)
        except Exception as e:
            logger.warning(f"Failed to get initial values: {e}")
            self._last_values = []
            self._last_row_count = 0

        # Compute content hash for change detection
        self._last_content_hash = await self._compute_content_hash(client)
        self._initialized = True

        hash_val = self._last_content_hash
        hash_preview = hash_val[:16] if hash_val else "none"
        logger.debug(
            f"Sheets trigger initialized: {self._spreadsheet_title} "
            f"(rows: {self._last_row_count}, hash: {hash_preview}...)"
        )

    async def _compute_content_hash(self, client) -> str:
        """Compute hash of current spreadsheet content."""
        config = self.config.config
        spreadsheet_id = config.get("spreadsheet_id", "")
        range_spec = self._get_range_spec()

        try:
            response = await client.get(
                f"{self.SHEETS_API_BASE}/{spreadsheet_id}/values/{range_spec}"
            )
            values = response.get("values", [])
            content_str = json.dumps(values, sort_keys=True)
            return hashlib.sha256(content_str.encode()).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to compute content hash: {e}")
            return ""

    def _get_range_spec(self) -> str:
        """Get the range specification for API requests."""
        config = self.config.config
        sheet_name = config.get("sheet_name", "")
        range_addr = config.get("range", "")

        if sheet_name and range_addr:
            return f"'{sheet_name}'!{range_addr}"
        elif sheet_name:
            return f"'{sheet_name}'"
        elif range_addr:
            return range_addr
        else:
            return "Sheet1"

    def _get_watch_mode(self) -> str:
        """Get watch mode from config, with legacy support for change_types."""
        config = self.config.config
        # Prefer watch_mode, fall back to change_types for backwards compatibility
        watch_mode = config.get("watch_mode", "")
        if not watch_mode:
            watch_mode = config.get("change_types", "any")
        return watch_mode

    async def _poll(self) -> None:
        """Poll Google Sheets for changes."""
        config = self.config.config
        spreadsheet_id = config.get("spreadsheet_id", "")
        watch_mode = self._get_watch_mode()

        if not spreadsheet_id:
            logger.error("No spreadsheet_id configured")
            return

        try:
            client = await self._get_google_client()

            # Handle new_rows mode
            if watch_mode == "new_rows":
                await self._poll_new_rows(client, spreadsheet_id)
                return

            # Handle any_change mode
            if watch_mode == "any_change":
                await self._poll_any_change(client, spreadsheet_id)
                return

            # Handle legacy modes (content, structure, any)
            changes_detected = []

            # Check for modification time change (any change to the file)
            if watch_mode in ("any", "structure"):
                drive_metadata = await client.get(
                    f"{self.DRIVE_API_BASE}/{spreadsheet_id}",
                    params={"fields": "modifiedTime"},
                )
                current_modified = drive_metadata.get("modifiedTime")

                if self._last_modified_time and current_modified != self._last_modified_time:
                    changes_detected.append("structure")
                    self._last_modified_time = current_modified

            # Check for content changes
            if watch_mode in ("any", "content"):
                current_hash = await self._compute_content_hash(client)
                if self._last_content_hash and current_hash != self._last_content_hash:
                    changes_detected.append("content")
                    self._last_content_hash = current_hash

            # Emit trigger if changes detected
            if changes_detected:
                await self._emit_change(client, changes_detected)

        except Exception as e:
            logger.error(f"Sheets poll error: {e}")
            raise

    async def _poll_new_rows(self, client, spreadsheet_id: str) -> None:
        """Poll for new rows added to the spreadsheet."""
        config = self.config.config
        range_spec = self._get_range_spec()
        sheet_name = config.get("sheet_name", "")

        # Get current values
        try:
            response = await client.get(
                f"{self.SHEETS_API_BASE}/{spreadsheet_id}/values/{range_spec}"
            )
            current_values = response.get("values", [])
        except Exception as e:
            logger.warning(f"Failed to get values: {e}")
            return

        current_row_count = len(current_values)

        # Check for new rows
        if current_row_count > self._last_row_count:
            new_rows_start = self._last_row_count
            new_rows = current_values[new_rows_start:]

            for i, row_values in enumerate(new_rows):
                row_number = new_rows_start + i + 1  # 1-indexed

                payload = {
                    "spreadsheet_id": spreadsheet_id,
                    "spreadsheet_title": self._spreadsheet_title or "",
                    "sheet_name": sheet_name,
                    "change_type": "new_row",
                    "row_number": row_number,
                    "values": row_values,
                    "row_count": current_row_count,
                    "column_count": len(row_values) if row_values else 0,
                    "timestamp": datetime.now(UTC).isoformat(),
                }

                metadata = {
                    "source": "google_sheets",
                    "watch_mode": "new_rows",
                    "spreadsheet_id": spreadsheet_id,
                    "previous_row_count": self._last_row_count,
                    "current_row_count": current_row_count,
                }

                await self.emit(payload, metadata)
                logger.info(
                    f"Sheets trigger fired: new row {row_number} " f"in {self._spreadsheet_title}"
                )

        # Update state
        self._last_row_count = current_row_count
        self._last_values = current_values

    async def _poll_any_change(self, client, spreadsheet_id: str) -> None:
        """Poll for any cell value changes in the spreadsheet."""
        config = self.config.config
        range_spec = self._get_range_spec()
        sheet_name = config.get("sheet_name", "")

        # Get current values
        try:
            response = await client.get(
                f"{self.SHEETS_API_BASE}/{spreadsheet_id}/values/{range_spec}"
            )
            current_values = response.get("values", [])
        except Exception as e:
            logger.warning(f"Failed to get values: {e}")
            return

        current_hash = self._compute_hash(current_values)

        if self._last_content_hash and current_hash != self._last_content_hash:
            # Find what changed
            changes = self._find_changes(self._last_values, current_values)

            payload = {
                "spreadsheet_id": spreadsheet_id,
                "spreadsheet_title": self._spreadsheet_title or "",
                "sheet_name": sheet_name,
                "change_type": "content_change",
                "row_number": changes.get("first_changed_row", 0),
                "values": current_values,
                "previous_values": self._last_values,
                "changes": changes,
                "row_count": len(current_values),
                "column_count": (max(len(row) for row in current_values) if current_values else 0),
                "timestamp": datetime.now(UTC).isoformat(),
            }

            metadata = {
                "source": "google_sheets",
                "watch_mode": "any_change",
                "spreadsheet_id": spreadsheet_id,
                "changed_cells": changes.get("changed_cells", 0),
                "previous_hash": self._last_content_hash,
                "current_hash": current_hash,
            }

            await self.emit(payload, metadata)
            logger.info(
                f"Sheets trigger fired: content changed in {self._spreadsheet_title} "
                f"({changes.get('changed_cells', 0)} cells)"
            )

        # Update state
        self._last_content_hash = current_hash
        self._last_values = current_values
        self._last_row_count = len(current_values)

    def _compute_hash(self, values: list[list[Any]]) -> str:
        """Compute hash of sheet content."""
        content_str = json.dumps(values, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def _find_changes(
        self,
        old_values: list[list[Any]],
        new_values: list[list[Any]],
    ) -> dict[str, Any]:
        """Find differences between old and new values."""
        changes: dict[str, Any] = {
            "changed_cells": 0,
            "changed_rows": [],
            "first_changed_row": 0,
            "row_count_change": len(new_values) - len(old_values),
        }

        changed_rows_set: set = set()
        max_rows = max(len(old_values), len(new_values))

        for row_idx in range(max_rows):
            old_row = old_values[row_idx] if row_idx < len(old_values) else []
            new_row = new_values[row_idx] if row_idx < len(new_values) else []

            max_cols = max(len(old_row), len(new_row))
            for col_idx in range(max_cols):
                old_val = old_row[col_idx] if col_idx < len(old_row) else None
                new_val = new_row[col_idx] if col_idx < len(new_row) else None

                if old_val != new_val:
                    changes["changed_cells"] += 1
                    changed_rows_set.add(row_idx + 1)  # 1-indexed

                    if changes["first_changed_row"] == 0:
                        changes["first_changed_row"] = row_idx + 1

        changes["changed_rows"] = sorted(changed_rows_set)
        return changes

    async def _emit_change(self, client, change_types: list[str]) -> None:
        """Emit trigger event for detected changes."""
        config = self.config.config
        spreadsheet_id = config.get("spreadsheet_id", "")
        range_spec = self._get_range_spec()

        # Build payload
        payload = {
            "spreadsheet_id": spreadsheet_id,
            "spreadsheet_title": self._spreadsheet_title or "",
            "sheet_name": config.get("sheet_name", ""),
            "change_type": ",".join(change_types),
            "range": range_spec,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Include values if configured
        if config.get("include_values", False):
            try:
                response = await client.get(
                    f"{self.SHEETS_API_BASE}/{spreadsheet_id}/values/{range_spec}"
                )
                values = response.get("values", [])
                payload["values"] = values
                payload["row_count"] = len(values)
                payload["column_count"] = max(len(row) for row in values) if values else 0
            except Exception as e:
                logger.warning(f"Failed to fetch values for payload: {e}")
                payload["values"] = []
                payload["row_count"] = 0
                payload["column_count"] = 0

        metadata = {
            "source": "google_sheets",
            "spreadsheet_id": spreadsheet_id,
            "change_types": change_types,
        }

        await self.emit(payload, metadata)
        logger.info(
            f"Sheets trigger fired: {self._spreadsheet_title} "
            f"(changes: {', '.join(change_types)})"
        )

    def validate_config(self) -> tuple[bool, str | None]:
        """Validate Google Sheets trigger configuration."""
        valid, error = super().validate_config()
        if not valid:
            return valid, error

        config = self.config.config

        # Validate spreadsheet_id
        spreadsheet_id = config.get("spreadsheet_id", "")
        if not spreadsheet_id:
            return False, "spreadsheet_id is required"

        # Validate watch_mode / change_types
        watch_mode = self._get_watch_mode()
        valid_modes = ["new_rows", "any_change", "content", "structure", "any"]
        if watch_mode not in valid_modes:
            return False, f"watch_mode must be one of: {valid_modes}"

        return True, None

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get JSON schema for Google Sheets trigger configuration."""
        base_schema = super().get_config_schema()
        base_schema["properties"].update(
            {
                "spreadsheet_id": {
                    "type": "string",
                    "description": "Google Sheets spreadsheet ID (from URL)",
                },
                "sheet_name": {
                    "type": "string",
                    "description": "Specific sheet name to monitor (optional)",
                },
                "range": {
                    "type": "string",
                    "description": "Cell range to monitor (e.g., 'A1:Z100')",
                },
                "watch_mode": {
                    "type": "string",
                    "enum": ["new_rows", "any_change", "content", "structure", "any"],
                    "default": "new_rows",
                    "description": "new_rows: per row, any_change: on cell changes",
                },
                "change_types": {
                    "type": "string",
                    "enum": ["new_rows", "any_change", "content", "structure", "any"],
                    "default": "any",
                    "description": "Legacy alias for watch_mode (deprecated)",
                },
                "include_values": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include cell values in payload (for legacy modes)",
                },
            }
        )
        base_schema["required"].append("spreadsheet_id")
        return base_schema


__all__ = ["SheetsTrigger"]
