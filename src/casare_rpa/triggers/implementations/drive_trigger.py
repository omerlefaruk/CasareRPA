"""
CasareRPA - Google Drive Trigger

Trigger that fires when changes are detected in Google Drive.
Supports both push notifications (webhooks) and polling.

Push notifications require a publicly accessible HTTPS endpoint.
Falls back to polling if push notifications cannot be established.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from loguru import logger

from casare_rpa.triggers.base import BaseTriggerConfig, TriggerType
from casare_rpa.triggers.implementations.google_trigger_base import GoogleTriggerBase
from casare_rpa.triggers.registry import register_trigger


@register_trigger
class DriveTrigger(GoogleTriggerBase):
    """
    Trigger that monitors Google Drive for changes.

    Supports two modes:
    1. Push notifications (preferred): Requires a public HTTPS webhook URL
    2. Polling (fallback): Checks for changes at regular intervals

    Configuration options:
        client_id: Google OAuth client ID
        client_secret_credential: Credential alias for client secret
        access_token_credential: Credential alias for access token
        refresh_token_credential: Credential alias for refresh token
        folder_id: Google Drive folder ID to monitor (optional)
        file_id: Specific file ID to monitor (optional)
        watch_type: Type of changes to watch (all, create, update, delete, move)
        include_shared: Include shared files/folders
        include_trashed: Include trashed items
        use_push_notifications: Enable push notifications (requires webhook_url)
        webhook_url: Public HTTPS URL for push notifications
        poll_interval: Polling interval in seconds (default: 60)

    Payload provided to workflow:
        change_type: Type of change (create, update, delete, move)
        file_id: ID of the changed file/folder
        file_name: Name of the changed file/folder
        mime_type: MIME type of the file
        is_folder: Whether the item is a folder
        parent_id: Parent folder ID
        modified_time: When the file was last modified
        modified_by: Email of user who made the change
        file_url: URL to access the file
        thumbnail_url: URL of file thumbnail (if available)
    """

    trigger_type = TriggerType.DRIVE
    display_name = "Google Drive"
    description = "Trigger when files or folders change in Google Drive"
    icon = "folder"
    category = "Google"

    DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
    CHANNEL_EXPIRATION_HOURS = 24  # Push notification channel expires after 24h

    def __init__(self, config: BaseTriggerConfig, event_callback=None):
        super().__init__(config, event_callback)
        self._start_page_token: str | None = None
        self._known_file_ids: set[str] = set()
        self._channel_id: str | None = None
        self._channel_resource_id: str | None = None
        self._channel_expiration: datetime | None = None
        self._use_push: bool = False

    def get_required_scopes(self) -> list[str]:
        """Return required Google Drive API scopes."""
        return [
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/drive.metadata.readonly",
        ]

    async def start(self) -> bool:
        """Start the Drive trigger."""
        result = await super().start()
        if result:
            try:
                await self._initialize_change_tracking()
                # Try to set up push notifications if configured
                if self.config.config.get("use_push_notifications", False):
                    await self._setup_push_notifications()
            except Exception as e:
                logger.warning(f"Failed to initialize Drive trigger fully: {e}")
        return result

    async def stop(self) -> bool:
        """Stop the Drive trigger."""
        # Stop push notification channel if active
        if self._channel_id:
            try:
                await self._stop_push_notifications()
            except Exception as e:
                logger.warning(f"Failed to stop push notification channel: {e}")

        return await super().stop()

    async def _initialize_change_tracking(self) -> None:
        """Initialize change tracking by getting start page token."""
        client = await self._get_google_client()
        config = self.config.config

        # Get start page token for change tracking
        params = {}
        if config.get("include_shared", False):
            params["supportsAllDrives"] = "true"
            params["includeItemsFromAllDrives"] = "true"

        response = await client.get(f"{self.DRIVE_API_BASE}/changes/startPageToken", params=params)
        self._start_page_token = response.get("startPageToken")

        # Build initial list of known files if monitoring specific folder
        folder_id = config.get("folder_id", "")
        if folder_id:
            await self._build_known_files_list(client, folder_id)

        logger.debug(f"Drive change tracking initialized with token: {self._start_page_token}")

    async def _build_known_files_list(self, client, folder_id: str) -> None:
        """Build initial list of known file IDs in folder."""
        query = f"'{folder_id}' in parents"
        if not self.config.config.get("include_trashed", False):
            query += " and trashed = false"

        params = {
            "q": query,
            "fields": "files(id)",
            "pageSize": 1000,
        }

        response = await client.get(f"{self.DRIVE_API_BASE}/files", params=params)
        for file_info in response.get("files", []):
            self._known_file_ids.add(file_info["id"])

        logger.debug(f"Initial file list: {len(self._known_file_ids)} files in folder")

    async def _setup_push_notifications(self) -> None:
        """Set up Google Drive push notifications (webhook)."""
        config = self.config.config
        webhook_url = config.get("webhook_url", "")

        if not webhook_url:
            logger.warning("Push notifications enabled but no webhook_url configured")
            return

        if not webhook_url.startswith("https://"):
            logger.warning("Push notifications require HTTPS webhook URL")
            return

        client = await self._get_google_client()

        try:
            # Generate unique channel ID
            self._channel_id = f"casare-drive-{uuid.uuid4().hex[:16]}"

            # Calculate expiration (max 24 hours for Drive API)
            expiration_time = datetime.now(UTC) + timedelta(hours=self.CHANNEL_EXPIRATION_HOURS)
            expiration_ms = int(expiration_time.timestamp() * 1000)

            file_id = config.get("file_id", "")

            # Watch specific file or use changes API for folder/all
            if file_id:
                # Watch specific file
                watch_url = f"{self.DRIVE_API_BASE}/files/{file_id}/watch"
            else:
                # Watch all changes with page token
                watch_url = (
                    f"{self.DRIVE_API_BASE}/changes/watch" f"?pageToken={self._start_page_token}"
                )

            watch_body = {
                "id": self._channel_id,
                "type": "web_hook",
                "address": webhook_url,
                "expiration": str(expiration_ms),
            }

            response = await client.post(watch_url, json_data=watch_body)

            self._channel_resource_id = response.get("resourceId")
            self._channel_expiration = expiration_time
            self._use_push = True

            logger.info(
                f"Drive push notifications established: channel={self._channel_id}, "
                f"expires={expiration_time.isoformat()}"
            )

        except Exception as e:
            logger.error(f"Failed to set up push notifications: {e}")
            self._use_push = False

    async def _stop_push_notifications(self) -> None:
        """Stop the push notification channel."""
        if not self._channel_id or not self._channel_resource_id:
            return

        client = await self._get_google_client()

        try:
            await client.post(
                f"{self.DRIVE_API_BASE}/channels/stop",
                json_data={
                    "id": self._channel_id,
                    "resourceId": self._channel_resource_id,
                },
            )
            logger.debug(f"Stopped push notification channel: {self._channel_id}")
        except Exception as e:
            logger.warning(f"Error stopping push channel: {e}")
        finally:
            self._channel_id = None
            self._channel_resource_id = None
            self._use_push = False

    async def _poll(self) -> None:
        """Poll Google Drive for changes."""
        # Check if push notification channel needs renewal
        if self._use_push and self._channel_expiration:
            if datetime.now(UTC) >= (self._channel_expiration - timedelta(hours=1)):
                logger.debug("Renewing push notification channel")
                await self._stop_push_notifications()
                await self._setup_push_notifications()

        # Skip polling if push notifications are active (they handle changes)
        if self._use_push:
            return

        try:
            client = await self._get_google_client()
            await self._check_for_changes(client)
        except Exception as e:
            logger.error(f"Drive poll error: {e}")
            raise

    async def _check_for_changes(self, client) -> None:
        """Check for changes using the Changes API."""
        config = self.config.config

        if not self._start_page_token:
            logger.warning("No start page token, reinitializing...")
            await self._initialize_change_tracking()
            return

        # Define fields to request from Drive API
        file_fields = (
            "id,name,mimeType,parents,modifiedTime,"
            "lastModifyingUser,trashed,webViewLink,thumbnailLink"
        )
        params = {
            "pageToken": self._start_page_token,
            "fields": f"newStartPageToken,changes(fileId,removed,file({file_fields}))",
            "pageSize": 100,
        }

        if config.get("include_shared", False):
            params["supportsAllDrives"] = "true"
            params["includeItemsFromAllDrives"] = "true"

        response = await client.get(f"{self.DRIVE_API_BASE}/changes", params=params)

        # Process changes
        changes = response.get("changes", [])
        folder_id = config.get("folder_id", "")
        file_id = config.get("file_id", "")
        watch_type = config.get("watch_type", "all")

        for change in changes:
            change_file_id = change.get("fileId", "")
            removed = change.get("removed", False)
            file_info = change.get("file", {})

            # Filter by specific file if configured
            if file_id and change_file_id != file_id:
                continue

            # Filter by folder if configured
            if folder_id:
                parents = file_info.get("parents", [])
                if folder_id not in parents:
                    # Check if this was previously known (moved out/deleted)
                    if change_file_id not in self._known_file_ids:
                        continue

            # Determine change type
            change_type = self._determine_change_type(change_file_id, removed, file_info)

            # Filter by watch type
            if watch_type != "all" and change_type != watch_type:
                continue

            # Skip trashed items unless configured to include them
            is_trashed = file_info.get("trashed", False)
            include_trashed = config.get("include_trashed", False)
            if is_trashed and not include_trashed and change_type != "delete":
                continue

            # Emit trigger
            await self._emit_change(change_type, change_file_id, file_info, removed)

            # Update known files list
            if change_type == "create":
                self._known_file_ids.add(change_file_id)
            elif change_type == "delete" and change_file_id in self._known_file_ids:
                self._known_file_ids.discard(change_file_id)

        # Update page token
        new_token = response.get("newStartPageToken")
        if new_token:
            self._start_page_token = new_token

    def _determine_change_type(self, file_id: str, removed: bool, file_info: dict[str, Any]) -> str:
        """Determine the type of change."""
        if removed or file_info.get("trashed", False):
            return "delete"

        if file_id in self._known_file_ids:
            # Check if this is a move (parent changed)
            return "update"
        else:
            return "create"

    async def _emit_change(
        self,
        change_type: str,
        file_id: str,
        file_info: dict[str, Any],
        removed: bool,
    ) -> None:
        """Emit trigger event for a change."""
        mime_type = file_info.get("mimeType", "")
        is_folder = mime_type == "application/vnd.google-apps.folder"

        # Get modifier info
        modifier = file_info.get("lastModifyingUser", {})
        modified_by = modifier.get("emailAddress", "")

        payload = {
            "change_type": change_type,
            "file_id": file_id,
            "file_name": file_info.get("name", ""),
            "mime_type": mime_type,
            "is_folder": is_folder,
            "parent_id": (file_info.get("parents", []) or [""])[0],
            "modified_time": file_info.get("modifiedTime", ""),
            "modified_by": modified_by,
            "file_url": file_info.get("webViewLink", ""),
            "thumbnail_url": file_info.get("thumbnailLink", ""),
            "removed": removed,
            "trashed": file_info.get("trashed", False),
        }

        metadata = {
            "source": "google_drive",
            "file_id": file_id,
            "change_type": change_type,
            "is_folder": is_folder,
        }

        await self.emit(payload, metadata)
        logger.info(f"Drive trigger fired: {change_type} - {file_info.get('name', file_id)}")

    async def handle_push_notification(self, headers: dict[str, str], body: bytes) -> bool:
        """
        Handle incoming push notification from Google Drive.

        This method should be called by the TriggerManager's webhook handler
        when a push notification is received.

        Args:
            headers: HTTP headers from the webhook request
            body: Request body

        Returns:
            True if notification was handled successfully
        """
        # Verify this is for our channel
        channel_id = headers.get("X-Goog-Channel-ID", "")
        resource_id = headers.get("X-Goog-Resource-ID", "")

        if channel_id != self._channel_id:
            logger.warning(f"Received notification for unknown channel: {channel_id}")
            return False

        if resource_id != self._channel_resource_id:
            logger.warning(f"Resource ID mismatch: {resource_id}")
            return False

        # Check notification type
        resource_state = headers.get("X-Goog-Resource-State", "")
        if resource_state == "sync":
            # Initial sync notification - ignore
            logger.debug("Received sync notification from Drive")
            return True

        if resource_state == "change":
            # Actual change notification - poll for details
            try:
                client = await self._get_google_client()
                await self._check_for_changes(client)
                return True
            except Exception as e:
                logger.error(f"Error processing push notification: {e}")
                return False

        logger.debug(f"Unhandled resource state: {resource_state}")
        return True

    def validate_config(self) -> tuple[bool, str | None]:
        """Validate Google Drive trigger configuration."""
        valid, error = super().validate_config()
        if not valid:
            return valid, error

        config = self.config.config

        # Validate watch_type
        watch_type = config.get("watch_type", "all")
        valid_types = ["all", "create", "update", "delete", "move"]
        if watch_type not in valid_types:
            return False, f"watch_type must be one of: {valid_types}"

        # Validate webhook URL if push notifications enabled
        if config.get("use_push_notifications", False):
            webhook_url = config.get("webhook_url", "")
            if not webhook_url:
                return (
                    False,
                    "webhook_url is required when use_push_notifications is enabled",
                )
            if not webhook_url.startswith("https://"):
                return False, "webhook_url must use HTTPS"

        return True, None

    @classmethod
    def get_config_schema(cls) -> dict[str, Any]:
        """Get JSON schema for Google Drive trigger configuration."""
        base_schema = super().get_config_schema()
        base_schema["properties"].update(
            {
                "folder_id": {
                    "type": "string",
                    "description": "Google Drive folder ID to monitor",
                },
                "file_id": {
                    "type": "string",
                    "description": "Specific file ID to monitor",
                },
                "watch_type": {
                    "type": "string",
                    "enum": ["all", "create", "update", "delete", "move"],
                    "default": "all",
                    "description": "Types of changes to watch",
                },
                "include_shared": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include shared files and folders",
                },
                "include_trashed": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include trashed items",
                },
                "use_push_notifications": {
                    "type": "boolean",
                    "default": False,
                    "description": "Use push notifications instead of polling",
                },
                "webhook_url": {
                    "type": "string",
                    "format": "uri",
                    "description": "Public HTTPS URL for push notifications",
                },
            }
        )
        return base_schema


__all__ = ["DriveTrigger"]
