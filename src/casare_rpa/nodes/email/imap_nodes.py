"""
IMAP management nodes for CasareRPA.

Provides nodes for managing emails on IMAP servers:
- Mark as read/unread/flagged
- Delete emails
- Move emails between folders
- Save attachments
"""

import asyncio
import email as email_module
import imaplib
import os
from pathlib import Path
from typing import Optional

from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
    PortType,
)
from casare_rpa.infrastructure.execution import ExecutionContext

from .email_base import decode_header_value


@node_schema(
    PropertyDef(
        "imap_server",
        PropertyType.STRING,
        default="imap.gmail.com",
        label="IMAP Server",
        tooltip="IMAP server hostname",
    ),
    PropertyDef(
        "imap_port",
        PropertyType.INTEGER,
        default=993,
        label="IMAP Port",
        tooltip="IMAP server port",
    ),
    PropertyDef(
        "username",
        PropertyType.STRING,
        default="",
        label="Username",
        tooltip="Email account username",
    ),
    PropertyDef(
        "password",
        PropertyType.STRING,
        default="",
        label="Password",
        tooltip="Email account password",
    ),
    PropertyDef(
        "folder",
        PropertyType.STRING,
        default="INBOX",
        label="Folder",
        tooltip="Mailbox folder",
    ),
    PropertyDef(
        "save_path",
        PropertyType.STRING,
        default=".",
        label="Save Path",
        tooltip="Directory path to save attachments",
    ),
)
@executable_node
class SaveAttachmentNode(BaseNode):
    """
    Save email attachments to disk.

    Downloads and saves attachments from an email.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize SaveAttachment node."""
        super().__init__(node_id, config)
        self.name = "Save Attachment"
        self.node_type = "SaveAttachmentNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("imap_server", PortType.INPUT, DataType.STRING)
        self.add_input_port("username", PortType.INPUT, DataType.STRING)
        self.add_input_port("password", PortType.INPUT, DataType.STRING)
        self.add_input_port("email_uid", PortType.INPUT, DataType.STRING)
        self.add_input_port("save_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("folder", PortType.INPUT, DataType.STRING)
        self.add_output_port("saved_files", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Save email attachments."""
        self.status = NodeStatus.RUNNING

        try:
            imap_server = self.get_parameter("imap_server", "imap.gmail.com")
            imap_port = self.get_parameter("imap_port", 993)
            username = self.get_parameter("username", "")
            password = self.get_parameter("password", "")
            email_uid = self.get_parameter("email_uid", "")
            save_path = self.get_parameter("save_path", ".")
            folder = self.get_parameter("folder", "INBOX")

            # Resolve {{variable}} patterns
            imap_server = context.resolve_value(imap_server)
            username = context.resolve_value(username)
            password = context.resolve_value(password)
            email_uid = context.resolve_value(email_uid)
            save_path = context.resolve_value(save_path)
            folder = context.resolve_value(folder)

            if not email_uid:
                self.set_output_value("saved_files", [])
                self.set_output_value("count", 0)
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "No email UID provided",
                    "next_nodes": [],
                }

            # Ensure save path exists
            Path(save_path).mkdir(parents=True, exist_ok=True)

            def _save_attachments_sync() -> list:
                """Save attachments synchronously - called via run_in_executor."""
                mail = None
                try:
                    mail = imaplib.IMAP4_SSL(imap_server, imap_port)
                    mail.login(username, password)
                    mail.select(folder)

                    # Fetch the email
                    status, msg_data = mail.fetch(email_uid.encode(), "(RFC822)")
                    if status != "OK":
                        raise Exception("Failed to fetch email")

                    raw_email = msg_data[0][1]
                    msg = email_module.message_from_bytes(raw_email)

                    saved = []
                    for part in msg.walk():
                        content_disposition = str(part.get("Content-Disposition", ""))
                        if "attachment" in content_disposition:
                            filename = part.get_filename()
                            if filename:
                                filename = decode_header_value(filename)
                                # SECURITY: Sanitize filename to prevent path traversal
                                safe_filename = Path(filename).name
                                if not safe_filename:
                                    logger.warning(
                                        f"Skipping invalid filename: {filename}"
                                    )
                                    continue
                                filepath = os.path.join(save_path, safe_filename)

                                # Avoid overwriting
                                base, ext = os.path.splitext(filepath)
                                counter = 1
                                while os.path.exists(filepath):
                                    filepath = f"{base}_{counter}{ext}"
                                    counter += 1

                                payload = part.get_payload(decode=True)
                                if payload:
                                    with open(filepath, "wb") as f:
                                        f.write(payload)
                                    saved.append(filepath)

                    return saved
                finally:
                    if mail:
                        try:
                            mail.logout()
                        except Exception:
                            pass

            loop = asyncio.get_running_loop()
            saved_files = await loop.run_in_executor(None, _save_attachments_sync)

            self.set_output_value("saved_files", saved_files)
            self.set_output_value("count", len(saved_files))

            logger.info(f"Saved {len(saved_files)} attachments to {save_path}")
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"saved_files": saved_files},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("saved_files", [])
            self.set_output_value("count", 0)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to save attachments: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "imap_server",
        PropertyType.STRING,
        default="imap.gmail.com",
        label="IMAP Server",
        tooltip="IMAP server hostname",
    ),
    PropertyDef(
        "imap_port",
        PropertyType.INTEGER,
        default=993,
        label="IMAP Port",
        tooltip="IMAP server port",
    ),
    PropertyDef(
        "username",
        PropertyType.STRING,
        default="",
        label="Username",
        tooltip="Email account username",
    ),
    PropertyDef(
        "password",
        PropertyType.STRING,
        default="",
        label="Password",
        tooltip="Email account password",
    ),
    PropertyDef(
        "folder",
        PropertyType.STRING,
        default="INBOX",
        label="Folder",
        tooltip="Mailbox folder",
    ),
    PropertyDef(
        "mark_as",
        PropertyType.CHOICE,
        default="read",
        choices=["read", "unread", "flagged", "unflagged"],
        label="Mark As",
        tooltip="Flag to set on the email",
    ),
)
@executable_node
class MarkEmailNode(BaseNode):
    """
    Mark an email as read, unread, or flagged.

    Updates email flags on the IMAP server.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize MarkEmail node."""
        super().__init__(node_id, config)
        self.name = "Mark Email"
        self.node_type = "MarkEmailNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("imap_server", PortType.INPUT, DataType.STRING)
        self.add_input_port("username", PortType.INPUT, DataType.STRING)
        self.add_input_port("password", PortType.INPUT, DataType.STRING)
        self.add_input_port("email_uid", PortType.INPUT, DataType.STRING)
        self.add_input_port("folder", PortType.INPUT, DataType.STRING)
        self.add_input_port("mark_as", PortType.INPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Mark email with specified flag."""
        self.status = NodeStatus.RUNNING

        try:
            imap_server = self.get_parameter("imap_server", "imap.gmail.com")
            imap_port = self.get_parameter("imap_port", 993)
            username = self.get_parameter("username", "")
            password = self.get_parameter("password", "")
            email_uid = self.get_parameter("email_uid", "")
            folder = self.get_parameter("folder", "INBOX")
            mark_as = self.get_parameter("mark_as", "read")

            # Resolve {{variable}} patterns
            imap_server = context.resolve_value(imap_server)
            username = context.resolve_value(username)
            password = context.resolve_value(password)
            email_uid = context.resolve_value(email_uid)
            folder = context.resolve_value(folder)
            mark_as = context.resolve_value(mark_as)

            if not email_uid:
                self.set_output_value("success", False)
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "No email UID provided",
                    "next_nodes": [],
                }

            def _mark_email_sync() -> None:
                """Mark email synchronously - called via run_in_executor."""
                mail = None
                try:
                    mail = imaplib.IMAP4_SSL(imap_server, imap_port)
                    mail.login(username, password)
                    mail.select(folder)

                    if mark_as == "read":
                        mail.store(email_uid.encode(), "+FLAGS", "\\Seen")
                    elif mark_as == "unread":
                        mail.store(email_uid.encode(), "-FLAGS", "\\Seen")
                    elif mark_as == "flagged":
                        mail.store(email_uid.encode(), "+FLAGS", "\\Flagged")
                    elif mark_as == "unflagged":
                        mail.store(email_uid.encode(), "-FLAGS", "\\Flagged")
                finally:
                    if mail:
                        try:
                            mail.logout()
                        except Exception:
                            pass

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, _mark_email_sync)

            self.set_output_value("success", True)
            logger.info(f"Marked email {email_uid} as {mark_as}")
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"marked_as": mark_as},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to mark email: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "imap_server",
        PropertyType.STRING,
        default="imap.gmail.com",
        label="IMAP Server",
        tooltip="IMAP server hostname",
    ),
    PropertyDef(
        "imap_port",
        PropertyType.INTEGER,
        default=993,
        label="IMAP Port",
        tooltip="IMAP server port",
    ),
    PropertyDef(
        "username",
        PropertyType.STRING,
        default="",
        label="Username",
        tooltip="Email account username",
    ),
    PropertyDef(
        "password",
        PropertyType.STRING,
        default="",
        label="Password",
        tooltip="Email account password",
    ),
    PropertyDef(
        "folder",
        PropertyType.STRING,
        default="INBOX",
        label="Folder",
        tooltip="Mailbox folder",
    ),
    PropertyDef(
        "permanent",
        PropertyType.BOOLEAN,
        default=False,
        label="Permanent Delete",
        tooltip="Permanently delete (expunge) instead of just marking deleted",
    ),
)
@executable_node
class DeleteEmailNode(BaseNode):
    """
    Delete an email from the mailbox.

    Moves email to trash or permanently deletes it.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize DeleteEmail node."""
        super().__init__(node_id, config)
        self.name = "Delete Email"
        self.node_type = "DeleteEmailNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("imap_server", PortType.INPUT, DataType.STRING)
        self.add_input_port("username", PortType.INPUT, DataType.STRING)
        self.add_input_port("password", PortType.INPUT, DataType.STRING)
        self.add_input_port("email_uid", PortType.INPUT, DataType.STRING)
        self.add_input_port("folder", PortType.INPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Delete email from mailbox."""
        self.status = NodeStatus.RUNNING

        try:
            imap_server = self.get_parameter("imap_server", "imap.gmail.com")
            imap_port = self.get_parameter("imap_port", 993)
            username = self.get_parameter("username", "")
            password = self.get_parameter("password", "")
            email_uid = self.get_parameter("email_uid", "")
            folder = self.get_parameter("folder", "INBOX")
            permanent = self.get_parameter("permanent", False)

            # Resolve {{variable}} patterns
            imap_server = context.resolve_value(imap_server)
            username = context.resolve_value(username)
            password = context.resolve_value(password)
            email_uid = context.resolve_value(email_uid)
            folder = context.resolve_value(folder)

            if not email_uid:
                self.set_output_value("success", False)
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "No email UID provided",
                    "next_nodes": [],
                }

            def _delete_email_sync() -> None:
                """Delete email synchronously - called via run_in_executor."""
                mail = None
                try:
                    mail = imaplib.IMAP4_SSL(imap_server, imap_port)
                    mail.login(username, password)
                    mail.select(folder)

                    mail.store(email_uid.encode(), "+FLAGS", "\\Deleted")

                    if permanent:
                        mail.expunge()
                finally:
                    if mail:
                        try:
                            mail.logout()
                        except Exception:
                            pass

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, _delete_email_sync)

            self.set_output_value("success", True)
            logger.info(f"Deleted email {email_uid}")
            self.status = NodeStatus.SUCCESS
            return {"success": True, "next_nodes": ["exec_out"]}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to delete email: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "imap_server",
        PropertyType.STRING,
        default="imap.gmail.com",
        label="IMAP Server",
        tooltip="IMAP server hostname",
    ),
    PropertyDef(
        "imap_port",
        PropertyType.INTEGER,
        default=993,
        label="IMAP Port",
        tooltip="IMAP server port",
    ),
    PropertyDef(
        "username",
        PropertyType.STRING,
        default="",
        label="Username",
        tooltip="Email account username",
    ),
    PropertyDef(
        "password",
        PropertyType.STRING,
        default="",
        label="Password",
        tooltip="Email account password",
    ),
    PropertyDef(
        "source_folder",
        PropertyType.STRING,
        default="INBOX",
        label="Source Folder",
        tooltip="Source mailbox folder",
    ),
    PropertyDef(
        "target_folder",
        PropertyType.STRING,
        default="",
        label="Target Folder",
        tooltip="Target mailbox folder",
    ),
)
@executable_node
class MoveEmailNode(BaseNode):
    """
    Move an email to a different folder.

    Copies email to target folder and marks original as deleted.
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize MoveEmail node."""
        super().__init__(node_id, config)
        self.name = "Move Email"
        self.node_type = "MoveEmailNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("imap_server", PortType.INPUT, DataType.STRING)
        self.add_input_port("username", PortType.INPUT, DataType.STRING)
        self.add_input_port("password", PortType.INPUT, DataType.STRING)
        self.add_input_port("email_uid", PortType.INPUT, DataType.STRING)
        self.add_input_port("source_folder", PortType.INPUT, DataType.STRING)
        self.add_input_port("target_folder", PortType.INPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Move email to different folder."""
        self.status = NodeStatus.RUNNING

        try:
            imap_server = self.get_parameter("imap_server", "imap.gmail.com")
            imap_port = self.get_parameter("imap_port", 993)
            username = self.get_parameter("username", "")
            password = self.get_parameter("password", "")
            email_uid = self.get_parameter("email_uid", "")
            source_folder = self.get_parameter("source_folder", "INBOX")
            target_folder = self.get_parameter("target_folder", "")

            # Resolve {{variable}} patterns
            imap_server = context.resolve_value(imap_server)
            username = context.resolve_value(username)
            password = context.resolve_value(password)
            email_uid = context.resolve_value(email_uid)
            source_folder = context.resolve_value(source_folder)
            target_folder = context.resolve_value(target_folder)

            if not email_uid or not target_folder:
                self.set_output_value("success", False)
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "Email UID and target folder required",
                    "next_nodes": [],
                }

            def _move_email_sync() -> None:
                """Move email synchronously - called via run_in_executor."""
                mail = None
                try:
                    mail = imaplib.IMAP4_SSL(imap_server, imap_port)
                    mail.login(username, password)
                    mail.select(source_folder)

                    # Copy to target folder
                    result = mail.copy(email_uid.encode(), target_folder)
                    if result[0] == "OK":
                        # Mark original as deleted
                        mail.store(email_uid.encode(), "+FLAGS", "\\Deleted")
                        mail.expunge()
                finally:
                    if mail:
                        try:
                            mail.logout()
                        except Exception:
                            pass

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, _move_email_sync)

            self.set_output_value("success", True)
            logger.info(f"Moved email {email_uid} to {target_folder}")
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"target_folder": target_folder},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to move email: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}
