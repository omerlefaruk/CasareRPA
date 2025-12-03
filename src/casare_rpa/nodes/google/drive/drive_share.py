"""
Google Drive sharing nodes for CasareRPA.

This module provides nodes for managing Google Drive file permissions:
- DriveShareFileNode: Add permission to a file/folder
- DriveRemoveShareNode: Remove permission from a file/folder
- DriveGetPermissionsNode: List all permissions on a file/folder
- DriveCreateShareLinkNode: Create a shareable link

All nodes use Google Drive API v3 and require OAuth2 authentication.
"""

from typing import Any, Dict, List, Optional

import aiohttp
from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
    PortType,
)
from casare_rpa.infrastructure.execution import ExecutionContext


DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"


async def _make_drive_request(
    session: aiohttp.ClientSession,
    method: str,
    endpoint: str,
    access_token: str,
    json_body: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Make an authenticated request to Google Drive API.

    Args:
        session: aiohttp client session
        method: HTTP method (GET, POST, DELETE, PATCH)
        endpoint: API endpoint path
        access_token: OAuth2 access token
        json_body: Optional JSON request body
        params: Optional query parameters

    Returns:
        JSON response from API

    Raises:
        ValueError: If API returns an error
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    url = f"{DRIVE_API_BASE}{endpoint}"

    async with session.request(
        method=method,
        url=url,
        headers=headers,
        json=json_body,
        params=params,
    ) as response:
        if response.status == 204:
            return {"success": True}

        response_data = await response.json()

        if response.status >= 400:
            error = response_data.get("error", {})
            error_msg = error.get("message", f"HTTP {response.status}")
            error_code = error.get("code", response.status)
            raise ValueError(f"Drive API error ({error_code}): {error_msg}")

        return response_data


@node_schema(
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
        "move_to_new_owners_root",
        PropertyType.BOOLEAN,
        default=False,
        label="Move to Owner's Root",
        tooltip="For ownership transfers, move file to new owner's root folder",
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
class DriveShareFileNode(BaseNode):
    """
    Add a permission to a Google Drive file or folder.

    This node grants access to a file/folder by creating a new permission.
    Supports sharing with:
    - Individual users (by email)
    - Google Groups (by email)
    - Domains (for G Suite/Workspace)

    Config (via @node_schema):
        send_notification: Send email notification (default: True)
        email_message: Custom message in notification email
        move_to_new_owners_root: Move file on ownership transfer
        transfer_ownership: Transfer ownership (requires role=owner)

    Inputs:
        access_token: OAuth2 access token with drive scope
        file_id: ID of the file or folder to share
        email: Email address of user or group to share with
        role: Permission role (reader, writer, commenter, owner)
        type: Permission type (user, group, domain, anyone)
        domain: Domain for domain-type permissions

    Outputs:
        permission_id: ID of the created permission
        permission: Full permission object
        success: Whether sharing succeeded
    """

    def __init__(
        self, node_id: str, name: str = "Drive: Share File", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DriveShareFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("access_token", PortType.INPUT, DataType.STRING)
        self.add_input_port("file_id", PortType.INPUT, DataType.STRING)
        self.add_input_port("email", PortType.INPUT, DataType.STRING)
        self.add_input_port("role", PortType.INPUT, DataType.STRING)
        self.add_input_port("type", PortType.INPUT, DataType.STRING)
        self.add_input_port("domain", PortType.INPUT, DataType.STRING)

        self.add_output_port("permission_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("permission", PortType.OUTPUT, DataType.DICT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            access_token = self.get_parameter("access_token", "")
            file_id = self.get_parameter("file_id", "")
            email = self.get_parameter("email", "")
            role = self.get_parameter("role", "reader")
            perm_type = self.get_parameter("type", "user")
            domain = self.get_parameter("domain", "")

            send_notification = self.get_parameter("send_notification", True)
            email_message = self.get_parameter("email_message", "")
            move_to_root = self.get_parameter("move_to_new_owners_root", False)
            transfer_ownership = self.get_parameter("transfer_ownership", False)

            # Resolve from context
            access_token = context.resolve_value(access_token)
            file_id = context.resolve_value(file_id)
            email = context.resolve_value(email)

            if not access_token:
                raise ValueError("access_token is required")
            if not file_id:
                raise ValueError("file_id is required")

            # Validate role
            valid_roles = ["reader", "writer", "commenter", "owner"]
            if role not in valid_roles:
                raise ValueError(f"role must be one of: {valid_roles}")

            # Validate type
            valid_types = ["user", "group", "domain", "anyone"]
            if perm_type not in valid_types:
                raise ValueError(f"type must be one of: {valid_types}")

            # Require email for user/group types
            if perm_type in ["user", "group"] and not email:
                raise ValueError(f"email is required for type '{perm_type}'")

            # Require domain for domain type
            if perm_type == "domain" and not domain:
                raise ValueError("domain is required for type 'domain'")

            # Build permission body
            permission_body: Dict[str, Any] = {
                "role": role,
                "type": perm_type,
            }

            if perm_type in ["user", "group"]:
                permission_body["emailAddress"] = email
            elif perm_type == "domain":
                permission_body["domain"] = domain

            # Build query params
            params: Dict[str, str] = {}
            if send_notification:
                params["sendNotificationEmail"] = "true"
                if email_message:
                    params["emailMessage"] = email_message
            else:
                params["sendNotificationEmail"] = "false"

            if transfer_ownership:
                params["transferOwnership"] = "true"
                if move_to_root:
                    params["moveToNewOwnersRoot"] = "true"

            logger.info(f"Sharing file {file_id} with {email or perm_type}")

            async with aiohttp.ClientSession() as session:
                result = await _make_drive_request(
                    session=session,
                    method="POST",
                    endpoint=f"/files/{file_id}/permissions",
                    access_token=access_token,
                    json_body=permission_body,
                    params=params,
                )

            permission_id = result.get("id", "")

            self.set_output_value("permission_id", permission_id)
            self.set_output_value("permission", result)
            self.set_output_value("success", True)

            self.status = NodeStatus.SUCCESS
            logger.info(f"File shared successfully, permission_id: {permission_id}")

            return {
                "success": True,
                "data": {"permission_id": permission_id, "role": role},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = f"Drive share error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("permission_id", "")
            self.set_output_value("permission", {})
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


@node_schema()
@executable_node
class DriveRemoveShareNode(BaseNode):
    """
    Remove a permission from a Google Drive file or folder.

    This node revokes access by deleting a specific permission.
    Requires the permission ID, which can be obtained from DriveGetPermissionsNode.

    Inputs:
        access_token: OAuth2 access token with drive scope
        file_id: ID of the file or folder
        permission_id: ID of the permission to remove

    Outputs:
        success: Whether removal succeeded
    """

    def __init__(
        self, node_id: str, name: str = "Drive: Remove Share", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DriveRemoveShareNode"

    def _define_ports(self) -> None:
        self.add_input_port("access_token", PortType.INPUT, DataType.STRING)
        self.add_input_port("file_id", PortType.INPUT, DataType.STRING)
        self.add_input_port("permission_id", PortType.INPUT, DataType.STRING)

        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            access_token = self.get_parameter("access_token", "")
            file_id = self.get_parameter("file_id", "")
            permission_id = self.get_parameter("permission_id", "")

            # Resolve from context
            access_token = context.resolve_value(access_token)
            file_id = context.resolve_value(file_id)
            permission_id = context.resolve_value(permission_id)

            if not access_token:
                raise ValueError("access_token is required")
            if not file_id:
                raise ValueError("file_id is required")
            if not permission_id:
                raise ValueError("permission_id is required")

            logger.info(f"Removing permission {permission_id} from file {file_id}")

            async with aiohttp.ClientSession() as session:
                await _make_drive_request(
                    session=session,
                    method="DELETE",
                    endpoint=f"/files/{file_id}/permissions/{permission_id}",
                    access_token=access_token,
                )

            self.set_output_value("success", True)

            self.status = NodeStatus.SUCCESS
            logger.info(f"Permission {permission_id} removed successfully")

            return {
                "success": True,
                "data": {"permission_id": permission_id, "removed": True},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = f"Drive remove share error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


@node_schema(
    PropertyDef(
        "include_permissions_for_view",
        PropertyType.BOOLEAN,
        default=False,
        label="Include Published Permissions",
        tooltip="Include permissions for published files",
    ),
)
@executable_node
class DriveGetPermissionsNode(BaseNode):
    """
    List all permissions on a Google Drive file or folder.

    Returns a list of all users and groups with access to the file,
    including their roles and permission IDs.

    Config (via @node_schema):
        include_permissions_for_view: Include published file permissions

    Inputs:
        access_token: OAuth2 access token with drive scope
        file_id: ID of the file or folder

    Outputs:
        permissions: List of permission objects
        count: Number of permissions
        success: Whether listing succeeded
    """

    def __init__(
        self, node_id: str, name: str = "Drive: Get Permissions", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DriveGetPermissionsNode"

    def _define_ports(self) -> None:
        self.add_input_port("access_token", PortType.INPUT, DataType.STRING)
        self.add_input_port("file_id", PortType.INPUT, DataType.STRING)

        self.add_output_port("permissions", PortType.OUTPUT, DataType.ARRAY)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            access_token = self.get_parameter("access_token", "")
            file_id = self.get_parameter("file_id", "")
            include_for_view = self.get_parameter("include_permissions_for_view", False)

            # Resolve from context
            access_token = context.resolve_value(access_token)
            file_id = context.resolve_value(file_id)

            if not access_token:
                raise ValueError("access_token is required")
            if not file_id:
                raise ValueError("file_id is required")

            logger.info(f"Getting permissions for file {file_id}")

            params = {
                "fields": "permissions(id,type,role,emailAddress,domain,displayName,photoLink,expirationTime,deleted,pendingOwner)",
            }
            if include_for_view:
                params["includePermissionsForView"] = "published"

            all_permissions: List[Dict[str, Any]] = []
            page_token: Optional[str] = None

            async with aiohttp.ClientSession() as session:
                while True:
                    if page_token:
                        params["pageToken"] = page_token

                    result = await _make_drive_request(
                        session=session,
                        method="GET",
                        endpoint=f"/files/{file_id}/permissions",
                        access_token=access_token,
                        params=params,
                    )

                    permissions = result.get("permissions", [])
                    all_permissions.extend(permissions)

                    page_token = result.get("nextPageToken")
                    if not page_token:
                        break

            count = len(all_permissions)

            self.set_output_value("permissions", all_permissions)
            self.set_output_value("count", count)
            self.set_output_value("success", True)

            self.status = NodeStatus.SUCCESS
            logger.info(f"Retrieved {count} permissions for file {file_id}")

            return {
                "success": True,
                "data": {"count": count},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = f"Drive get permissions error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("permissions", [])
            self.set_output_value("count", 0)
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


@node_schema(
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
class DriveCreateShareLinkNode(BaseNode):
    """
    Create a shareable link for a Google Drive file or folder.

    This creates an "anyone" or "anyoneWithLink" permission to enable
    link sharing. The file can then be accessed by anyone with the link.

    Config (via @node_schema):
        access_type: "anyone" (public) or "anyoneWithLink" (unlisted)
        link_role: reader, writer, or commenter
        allow_file_discovery: Allow file in search results

    Inputs:
        access_token: OAuth2 access token with drive scope
        file_id: ID of the file or folder

    Outputs:
        share_link: The shareable link (webViewLink)
        permission_id: ID of the created permission
        success: Whether link creation succeeded
    """

    def __init__(
        self, node_id: str, name: str = "Drive: Create Share Link", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DriveCreateShareLinkNode"

    def _define_ports(self) -> None:
        self.add_input_port("access_token", PortType.INPUT, DataType.STRING)
        self.add_input_port("file_id", PortType.INPUT, DataType.STRING)

        self.add_output_port("share_link", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("permission_id", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            access_token = self.get_parameter("access_token", "")
            file_id = self.get_parameter("file_id", "")
            access_type = self.get_parameter("access_type", "anyone")
            link_role = self.get_parameter("link_role", "reader")
            allow_discovery = self.get_parameter("allow_file_discovery", False)

            # Resolve from context
            access_token = context.resolve_value(access_token)
            file_id = context.resolve_value(file_id)

            if not access_token:
                raise ValueError("access_token is required")
            if not file_id:
                raise ValueError("file_id is required")

            logger.info(f"Creating share link for file {file_id}")

            # Create the anyone permission
            permission_body: Dict[str, Any] = {
                "role": link_role,
                "type": access_type,
            }

            if allow_discovery:
                permission_body["allowFileDiscovery"] = True

            async with aiohttp.ClientSession() as session:
                # Create permission
                perm_result = await _make_drive_request(
                    session=session,
                    method="POST",
                    endpoint=f"/files/{file_id}/permissions",
                    access_token=access_token,
                    json_body=permission_body,
                )

                permission_id = perm_result.get("id", "")

                # Get the file to retrieve webViewLink
                file_result = await _make_drive_request(
                    session=session,
                    method="GET",
                    endpoint=f"/files/{file_id}",
                    access_token=access_token,
                    params={"fields": "webViewLink,webContentLink"},
                )

            share_link = file_result.get("webViewLink", "")

            self.set_output_value("share_link", share_link)
            self.set_output_value("permission_id", permission_id)
            self.set_output_value("success", True)

            self.status = NodeStatus.SUCCESS
            logger.info(f"Share link created: {share_link}")

            return {
                "success": True,
                "data": {"share_link": share_link, "permission_id": permission_id},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = f"Drive create share link error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("share_link", "")
            self.set_output_value("permission_id", "")
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


__all__ = [
    "DriveShareFileNode",
    "DriveRemoveShareNode",
    "DriveGetPermissionsNode",
    "DriveCreateShareLinkNode",
]
