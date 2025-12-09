"""
Google Drive sharing nodes for CasareRPA.

This module provides nodes for managing Google Drive file permissions:
- DriveShareFileNode: Add permission to a file/folder
- DriveRemoveShareNode: Remove permission from a file/folder
- DriveGetPermissionsNode: List all permissions on a file/folder
- DriveCreateShareLinkNode: Create a shareable link

All nodes use Google Drive API v3 and require OAuth2 authentication.
Credential selection is handled by NodeGoogleCredentialWidget in the visual layer.
"""

from typing import Any, Dict, List, Optional

import aiohttp
from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    PortType,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.infrastructure.resources.google_drive_client import GoogleDriveClient
from casare_rpa.nodes.google.google_base import DriveBaseNode


# ============================================================================
# Reusable Property Definitions
# ============================================================================

# NOTE: access_token and credential_name are NOT defined here.
# Credential selection is handled by NodeGoogleCredentialWidget in the visual layer.
# The credential_id property is set by the picker widget.

DRIVE_FILE_ID = PropertyDef(
    "file_id",
    PropertyType.STRING,
    default="",
    required=True,
    label="File ID",
    placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    tooltip="Google Drive file ID",
)


# ============================================================================
# Drive Share File Node
# ============================================================================


@node_schema(
    DRIVE_FILE_ID,
    PropertyDef(
        "email",
        PropertyType.STRING,
        default="",
        label="Email",
        placeholder="user@example.com",
        tooltip="Email address of user or group to share with",
    ),
    PropertyDef(
        "role",
        PropertyType.CHOICE,
        default="reader",
        choices=["reader", "writer", "commenter", "owner"],
        label="Role",
        tooltip="Permission role to grant",
    ),
    PropertyDef(
        "permission_type",
        PropertyType.CHOICE,
        default="user",
        choices=["user", "group", "domain", "anyone"],
        label="Type",
        tooltip="Permission type",
    ),
    PropertyDef(
        "domain",
        PropertyType.STRING,
        default="",
        label="Domain",
        placeholder="example.com",
        tooltip="Domain for domain-type permissions",
    ),
    PropertyDef(
        "send_notification",
        PropertyType.BOOLEAN,
        default=True,
        label="Send Notification",
        tooltip="Send email notification to the user being granted access",
    ),
    PropertyDef(
        "email_message",
        PropertyType.TEXT,
        default="",
        label="Email Message",
        tooltip="Custom message to include in the notification email",
    ),
    PropertyDef(
        "transfer_ownership",
        PropertyType.BOOLEAN,
        default=False,
        label="Transfer Ownership",
        tooltip="Transfer ownership to this user (requires role=owner)",
    ),
)
@executable_node
class DriveShareFileNode(DriveBaseNode):
    """
    Add a permission to a Google Drive file or folder.

    This node grants access to a file/folder by creating a new permission.
    Supports sharing with:
    - Individual users (by email)
    - Google Groups (by email)
    - Domains (for G Suite/Workspace)

    Inputs:
        file_id: ID of the file or folder to share
        email: Email address of user or group to share with
        role: Permission role (reader, writer, commenter, owner)
        permission_type: Permission type (user, group, domain, anyone)
        domain: Domain for domain-type permissions

    Outputs:
        permission_id: ID of the created permission
        permission: Full permission object
        success: Whether sharing succeeded
        error: Error message if failed
    """

    # @category: google
    # @requires: requests
    # @ports: file_id, email, role, permission_type, domain -> permission_id, permission

    NODE_TYPE = "drive_share_file"
    NODE_CATEGORY = "google_drive"
    NODE_DISPLAY_NAME = "Drive: Share File"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Drive Share File", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Share-specific inputs
        self.add_input_port("file_id", DataType.STRING, required=True)
        self.add_input_port("email", DataType.STRING, required=False)
        self.add_input_port("role", DataType.STRING, required=False)
        self.add_input_port("permission_type", DataType.STRING, required=False)
        self.add_input_port("domain", DataType.STRING, required=False)

        # Share-specific outputs
        self.add_output_port("permission_id", DataType.STRING)
        self.add_output_port("permission", DataType.DICT)

    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: GoogleDriveClient,
    ) -> ExecutionResult:
        """Share a file in Google Drive."""
        file_id = self._resolve_value(context, self.get_parameter("file_id"))
        email = self._resolve_value(context, self.get_parameter("email"))
        role = self.get_parameter("role") or "reader"
        perm_type = self.get_parameter("permission_type") or "user"
        domain = self._resolve_value(context, self.get_parameter("domain"))

        send_notification = self.get_parameter("send_notification", True)
        email_message = self.get_parameter("email_message", "")
        transfer_ownership = self.get_parameter("transfer_ownership", False)

        if not file_id:
            self._set_error_outputs("File ID is required")
            return {
                "success": False,
                "error": "File ID is required",
                "next_nodes": [],
            }

        # Validate inputs
        if perm_type in ["user", "group"] and not email:
            self._set_error_outputs(f"Email is required for type '{perm_type}'")
            return {
                "success": False,
                "error": f"Email is required for type '{perm_type}'",
                "next_nodes": [],
            }

        if perm_type == "domain" and not domain:
            self._set_error_outputs("Domain is required for type 'domain'")
            return {
                "success": False,
                "error": "Domain is required for type 'domain'",
                "next_nodes": [],
            }

        logger.debug(f"Sharing file in Drive: {file_id} with {email or perm_type}")

        # Create permission
        result = await client.create_permission(
            file_id=file_id,
            role=role,
            type=perm_type,
            email_address=email if perm_type in ["user", "group"] else None,
            domain=domain if perm_type == "domain" else None,
            send_notification_email=send_notification,
            email_message=email_message if send_notification else None,
            transfer_ownership=transfer_ownership,
        )

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("permission_id", result.id)
        self.set_output_value(
            "permission",
            {
                "id": result.id,
                "type": result.type,
                "role": result.role,
                "emailAddress": result.email_address,
                "domain": result.domain,
                "displayName": result.display_name,
            },
        )

        logger.info(f"Shared file in Drive: {file_id} with {email or perm_type}")

        return {
            "success": True,
            "permission_id": result.id,
            "role": role,
            "next_nodes": [],
        }


# ============================================================================
# Drive Remove Share Node
# ============================================================================


@node_schema(
    DRIVE_FILE_ID,
    PropertyDef(
        "permission_id",
        PropertyType.STRING,
        default="",
        required=True,
        label="Permission ID",
        placeholder="12345678901234567890",
        tooltip="ID of the permission to remove",
    ),
)
@executable_node
class DriveRemoveShareNode(DriveBaseNode):
    """
    Remove a permission from a Google Drive file or folder.

    This node revokes access by deleting a specific permission.
    Requires the permission ID, which can be obtained from DriveGetPermissionsNode.

    Inputs:
        file_id: ID of the file or folder
        permission_id: ID of the permission to remove

    Outputs:
        success: Whether removal succeeded
        error: Error message if failed
    """

    # @category: google
    # @requires: requests
    # @ports: file_id, permission_id -> none

    NODE_TYPE = "drive_remove_share"
    NODE_CATEGORY = "google_drive"
    NODE_DISPLAY_NAME = "Drive: Remove Share"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Drive Remove Share", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Remove share inputs
        self.add_input_port("file_id", DataType.STRING, required=True)
        self.add_input_port("permission_id", DataType.STRING, required=True)

    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: GoogleDriveClient,
    ) -> ExecutionResult:
        """Remove a permission from a file in Google Drive."""
        file_id = self._resolve_value(context, self.get_parameter("file_id"))
        permission_id = self._resolve_value(
            context, self.get_parameter("permission_id")
        )

        if not file_id:
            self._set_error_outputs("File ID is required")
            return {
                "success": False,
                "error": "File ID is required",
                "next_nodes": [],
            }

        if not permission_id:
            self._set_error_outputs("Permission ID is required")
            return {
                "success": False,
                "error": "Permission ID is required",
                "next_nodes": [],
            }

        logger.debug(f"Removing permission {permission_id} from file {file_id}")

        # Delete permission
        await client.delete_permission(file_id=file_id, permission_id=permission_id)

        # Set outputs
        self._set_success_outputs()

        logger.info(f"Removed permission {permission_id} from file {file_id}")

        return {
            "success": True,
            "permission_id": permission_id,
            "removed": True,
            "next_nodes": [],
        }


# ============================================================================
# Drive Get Permissions Node
# ============================================================================


@node_schema(
    DRIVE_FILE_ID,
    PropertyDef(
        "include_permissions_for_view",
        PropertyType.BOOLEAN,
        default=False,
        label="Include Published Permissions",
        tooltip="Include permissions for published files",
    ),
)
@executable_node
class DriveGetPermissionsNode(DriveBaseNode):
    """
    List all permissions on a Google Drive file or folder.

    Returns a list of all users and groups with access to the file,
    including their roles and permission IDs.

    Inputs:
        file_id: ID of the file or folder

    Outputs:
        permissions: List of permission objects
        count: Number of permissions
        success: Whether listing succeeded
        error: Error message if failed
    """

    # @category: google
    # @requires: requests
    # @ports: file_id -> permissions, count

    NODE_TYPE = "drive_get_permissions"
    NODE_CATEGORY = "google_drive"
    NODE_DISPLAY_NAME = "Drive: Get Permissions"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Drive Get Permissions", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Get permissions inputs
        self.add_input_port("file_id", DataType.STRING, required=True)

        # Get permissions outputs
        self.add_output_port("permissions", DataType.LIST)
        self.add_output_port("count", DataType.INTEGER)

    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: GoogleDriveClient,
    ) -> ExecutionResult:
        """Get all permissions for a file in Google Drive."""
        file_id = self._resolve_value(context, self.get_parameter("file_id"))

        if not file_id:
            self._set_error_outputs("File ID is required")
            return {
                "success": False,
                "error": "File ID is required",
                "next_nodes": [],
            }

        logger.debug(f"Getting permissions for file {file_id}")

        # Get permissions
        permissions = await client.list_permissions(file_id=file_id)

        # Convert to serializable format
        permissions_data = []
        for perm in permissions:
            permissions_data.append(
                {
                    "id": perm.id,
                    "type": perm.type,
                    "role": perm.role,
                    "emailAddress": perm.email_address,
                    "domain": perm.domain,
                    "displayName": perm.display_name,
                    "photoLink": perm.photo_link,
                    "expirationTime": perm.expiration_time,
                    "deleted": perm.deleted,
                    "pendingOwner": perm.pending_owner,
                }
            )

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("permissions", permissions_data)
        self.set_output_value("count", len(permissions_data))

        logger.info(f"Retrieved {len(permissions_data)} permissions for file {file_id}")

        return {
            "success": True,
            "permissions": permissions_data,
            "count": len(permissions_data),
            "next_nodes": [],
        }


# ============================================================================
# Drive Create Share Link Node
# ============================================================================


@node_schema(
    DRIVE_FILE_ID,
    PropertyDef(
        "access_type",
        PropertyType.CHOICE,
        default="anyone",
        choices=["anyone", "anyoneWithLink"],
        label="Link Access",
        tooltip="Who can access via the link",
    ),
    PropertyDef(
        "link_role",
        PropertyType.CHOICE,
        default="reader",
        choices=["reader", "writer", "commenter"],
        label="Link Role",
        tooltip="Role granted to anyone accessing via link",
    ),
    PropertyDef(
        "allow_file_discovery",
        PropertyType.BOOLEAN,
        default=False,
        label="Allow File Discovery",
        tooltip="Allow file to appear in search results",
    ),
)
@executable_node
class DriveCreateShareLinkNode(DriveBaseNode):
    """
    Create a shareable link for a Google Drive file or folder.

    This creates an "anyone" or "anyoneWithLink" permission to enable
    link sharing. The file can then be accessed by anyone with the link.

    Inputs:
        file_id: ID of the file or folder

    Outputs:
        share_link: The shareable link (webViewLink)
        permission_id: ID of the created permission
        success: Whether link creation succeeded
        error: Error message if failed
    """

    # @category: google
    # @requires: requests
    # @ports: file_id -> share_link, permission_id

    NODE_TYPE = "drive_create_share_link"
    NODE_CATEGORY = "google_drive"
    NODE_DISPLAY_NAME = "Drive: Create Share Link"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name="Drive Create Share Link", **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self._define_common_input_ports()
        self._define_common_output_ports()

        # Create share link inputs
        self.add_input_port("file_id", DataType.STRING, required=True)

        # Create share link outputs
        self.add_output_port("share_link", DataType.STRING)
        self.add_output_port("permission_id", DataType.STRING)

    async def _execute_drive(
        self,
        context: ExecutionContext,
        client: GoogleDriveClient,
    ) -> ExecutionResult:
        """Create a shareable link for a file in Google Drive."""
        file_id = self._resolve_value(context, self.get_parameter("file_id"))
        access_type = self.get_parameter("access_type") or "anyone"
        link_role = self.get_parameter("link_role") or "reader"
        allow_discovery = self.get_parameter("allow_file_discovery", False)

        if not file_id:
            self._set_error_outputs("File ID is required")
            return {
                "success": False,
                "error": "File ID is required",
                "next_nodes": [],
            }

        logger.debug(f"Creating share link for file {file_id}")

        # Create permission
        permission = await client.create_permission(
            file_id=file_id,
            role=link_role,
            type=access_type,
            allow_file_discovery=allow_discovery,
        )

        # Get file to retrieve webViewLink
        file_info = await client.get_file(file_id=file_id)
        share_link = file_info.web_view_link or ""

        # Set outputs
        self._set_success_outputs()
        self.set_output_value("share_link", share_link)
        self.set_output_value("permission_id", permission.id)

        logger.info(f"Created share link for file {file_id}: {share_link}")

        return {
            "success": True,
            "share_link": share_link,
            "permission_id": permission.id,
            "next_nodes": [],
        }


__all__ = [
    "DriveShareFileNode",
    "DriveRemoveShareNode",
    "DriveGetPermissionsNode",
    "DriveCreateShareLinkNode",
]
