"""
FTP operation nodes for CasareRPA.

This module provides nodes for FTP/SFTP operations:
- FTPConnectNode: Connect to FTP server
- FTPUploadNode: Upload file to FTP
- FTPDownloadNode: Download file from FTP
- FTPListNode: List directory contents
- FTPDeleteNode: Delete file on FTP
- FTPMakeDirNode: Create directory on FTP
- FTPDisconnectNode: Disconnect from FTP
- SFTPConnectNode: Connect to SFTP server
"""

import asyncio
import ftplib
import os
from pathlib import Path
from typing import Any, Optional, List

from loguru import logger

from ..core.base_node import BaseNode
from ..core.types import NodeStatus, PortType, DataType, ExecutionResult
from ..core.execution_context import ExecutionContext


class FTPConnectNode(BaseNode):
    """
    Connect to an FTP server.

    Config:
        passive: Use passive mode (default: True)
        timeout: Connection timeout in seconds (default: 30)
        use_tls: Use FTPS/TLS (default: False)
        retry_count: Number of connection retries (default: 0)
        retry_interval: Delay between retries in ms (default: 2000)

    Inputs:
        host: FTP server hostname
        port: FTP port (default: 21)
        username: FTP username
        password: FTP password

    Outputs:
        connected: Whether connection succeeded
        server_message: Server welcome message
    """

    def __init__(self, node_id: str, name: str = "FTP Connect", **kwargs) -> None:
        # Default config with all options
        default_config = {
            "passive": True,
            "timeout": 30,
            "use_tls": False,
            "retry_count": 0,  # Number of connection retries
            "retry_interval": 2000,  # Delay between retries in ms
        }

        config = kwargs.get("config", {})
        # Merge with defaults
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FTPConnectNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("host", PortType.INPUT, DataType.STRING)
        self.add_input_port("port", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("username", PortType.INPUT, DataType.STRING)
        self.add_input_port("password", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("connected", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("server_message", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            host = str(self.get_input_value("host", context) or "")
            port = int(self.get_input_value("port", context) or 21)
            username = str(self.get_input_value("username", context) or "anonymous")
            password = str(self.get_input_value("password", context) or "")
            passive = self.config.get("passive", True)
            timeout = self.config.get("timeout", 30)
            use_tls = self.config.get("use_tls", False)

            # Get retry options
            retry_count = int(self.config.get("retry_count", 0))
            retry_interval = int(self.config.get("retry_interval", 2000))

            if not host:
                raise ValueError("host is required")

            logger.info(f"Connecting to FTP server: {host}:{port}")

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(f"Retry attempt {attempts - 1}/{retry_count} for FTP connect")

                    # Create FTP connection
                    if use_tls:
                        ftp = ftplib.FTP_TLS(timeout=timeout)
                    else:
                        ftp = ftplib.FTP(timeout=timeout)

                    ftp.connect(host, port)
                    welcome = ftp.login(username, password)

                    if use_tls:
                        ftp.prot_p()  # Switch to protected data connection

                    ftp.set_pasv(passive)

                    # Store connection in context for other nodes
                    context.set_variable("_ftp_connection", ftp)

                    self.set_output_value("connected", True)
                    self.set_output_value("server_message", welcome)
                    self.status = NodeStatus.SUCCESS

                    logger.info(f"FTP connected successfully to {host} (attempt {attempts})")

                    return {
                        "success": True,
                        "data": {"connected": True, "attempts": attempts},
                        "next_nodes": ["exec_out"]
                    }

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(f"FTP connect failed (attempt {attempts}): {e}")
                        await asyncio.sleep(retry_interval / 1000)
                    else:
                        break

            raise last_error

        except Exception as e:
            self.set_output_value("connected", False)
            self.set_output_value("server_message", str(e))
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to connect to FTP: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class FTPUploadNode(BaseNode):
    """
    Upload a file to FTP server.

    Config:
        binary_mode: Transfer in binary mode (default: True)
        create_dirs: Create remote directories if needed (default: False)
        retry_count: Number of upload retries (default: 0)
        retry_interval: Delay between retries in ms (default: 2000)

    Inputs:
        local_path: Local file path to upload
        remote_path: Remote destination path

    Outputs:
        uploaded: Whether upload succeeded
        bytes_sent: Number of bytes transferred
    """

    def __init__(self, node_id: str, name: str = "FTP Upload", **kwargs) -> None:
        # Default config with all options
        default_config = {
            "binary_mode": True,
            "create_dirs": False,
            "retry_count": 0,  # Number of upload retries
            "retry_interval": 2000,  # Delay between retries in ms
        }

        config = kwargs.get("config", {})
        # Merge with defaults
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FTPUploadNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("local_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("remote_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("uploaded", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("bytes_sent", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            local_path = str(self.get_input_value("local_path", context) or "")
            remote_path = str(self.get_input_value("remote_path", context) or "")
            binary_mode = self.config.get("binary_mode", True)
            create_dirs = self.config.get("create_dirs", False)

            # Get retry options
            retry_count = int(self.config.get("retry_count", 0))
            retry_interval = int(self.config.get("retry_interval", 2000))

            if not local_path:
                raise ValueError("local_path is required")
            if not remote_path:
                raise ValueError("remote_path is required")

            local = Path(local_path)
            if not local.exists():
                raise FileNotFoundError(f"Local file not found: {local_path}")

            ftp = context.get_variable("_ftp_connection")
            if ftp is None:
                raise RuntimeError("No FTP connection. Use FTP Connect node first.")

            # Create remote directories if needed
            if create_dirs:
                remote_dir = str(Path(remote_path).parent)
                if remote_dir and remote_dir != ".":
                    try:
                        ftp.mkd(remote_dir)
                    except ftplib.error_perm:
                        pass  # Directory may already exist

            file_size = local.stat().st_size
            logger.info(f"Uploading {local_path} to {remote_path} ({file_size} bytes)")

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(f"Retry attempt {attempts - 1}/{retry_count} for FTP upload")

                    # Upload file
                    with open(local, "rb") as f:
                        if binary_mode:
                            ftp.storbinary(f"STOR {remote_path}", f)
                        else:
                            ftp.storlines(f"STOR {remote_path}", f)

                    self.set_output_value("uploaded", True)
                    self.set_output_value("bytes_sent", file_size)
                    self.status = NodeStatus.SUCCESS

                    logger.info(f"FTP upload completed: {remote_path} (attempt {attempts})")

                    return {
                        "success": True,
                        "data": {"bytes_sent": file_size, "attempts": attempts},
                        "next_nodes": ["exec_out"]
                    }

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(f"FTP upload failed (attempt {attempts}): {e}")
                        await asyncio.sleep(retry_interval / 1000)
                    else:
                        break

            raise last_error

        except Exception as e:
            self.set_output_value("uploaded", False)
            self.set_output_value("bytes_sent", 0)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to upload file: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class FTPDownloadNode(BaseNode):
    """
    Download a file from FTP server.

    Config:
        binary_mode: Transfer in binary mode (default: True)
        overwrite: Overwrite local file if exists (default: False)
        retry_count: Number of download retries (default: 0)
        retry_interval: Delay between retries in ms (default: 2000)

    Inputs:
        remote_path: Remote file path to download
        local_path: Local destination path

    Outputs:
        downloaded: Whether download succeeded
        bytes_received: Number of bytes transferred
    """

    def __init__(self, node_id: str, name: str = "FTP Download", **kwargs) -> None:
        # Default config with all options
        default_config = {
            "binary_mode": True,
            "overwrite": False,
            "retry_count": 0,  # Number of download retries
            "retry_interval": 2000,  # Delay between retries in ms
        }

        config = kwargs.get("config", {})
        # Merge with defaults
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FTPDownloadNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("remote_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("local_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("downloaded", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("bytes_received", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            remote_path = str(self.get_input_value("remote_path", context) or "")
            local_path = str(self.get_input_value("local_path", context) or "")
            binary_mode = self.config.get("binary_mode", True)
            overwrite = self.config.get("overwrite", False)

            # Get retry options
            retry_count = int(self.config.get("retry_count", 0))
            retry_interval = int(self.config.get("retry_interval", 2000))

            if not remote_path:
                raise ValueError("remote_path is required")
            if not local_path:
                raise ValueError("local_path is required")

            local = Path(local_path)
            if local.exists() and not overwrite:
                raise FileExistsError(f"Local file already exists: {local_path}")

            if local.parent:
                local.parent.mkdir(parents=True, exist_ok=True)

            ftp = context.get_variable("_ftp_connection")
            if ftp is None:
                raise RuntimeError("No FTP connection. Use FTP Connect node first.")

            logger.info(f"Downloading {remote_path} to {local_path}")

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(f"Retry attempt {attempts - 1}/{retry_count} for FTP download")

                    # Download file
                    bytes_received = 0

                    with open(local, "wb") as f:
                        def callback(data):
                            nonlocal bytes_received
                            f.write(data)
                            bytes_received += len(data)

                        if binary_mode:
                            ftp.retrbinary(f"RETR {remote_path}", callback)
                        else:
                            ftp.retrlines(f"RETR {remote_path}", lambda line: callback((line + "\n").encode()))

                    self.set_output_value("downloaded", True)
                    self.set_output_value("bytes_received", bytes_received)
                    self.status = NodeStatus.SUCCESS

                    logger.info(f"FTP download completed: {local_path} ({bytes_received} bytes, attempt {attempts})")

                    return {
                        "success": True,
                        "data": {"bytes_received": bytes_received, "attempts": attempts},
                        "next_nodes": ["exec_out"]
                    }

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(f"FTP download failed (attempt {attempts}): {e}")
                        await asyncio.sleep(retry_interval / 1000)
                    else:
                        break

            raise last_error

        except Exception as e:
            self.set_output_value("downloaded", False)
            self.set_output_value("bytes_received", 0)
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to download file: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class FTPListNode(BaseNode):
    """
    List contents of a directory on FTP server.

    Config:
        detailed: Get detailed file info (default: False)

    Inputs:
        remote_path: Remote directory path (default: current directory)

    Outputs:
        items: List of file/directory names or detailed info
        count: Number of items
    """

    def __init__(self, node_id: str, name: str = "FTP List", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FTPListNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("remote_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("items", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            remote_path = str(self.get_input_value("remote_path", context) or "")
            detailed = self.config.get("detailed", False)

            ftp = context.get_variable("_ftp_connection")
            if ftp is None:
                raise RuntimeError("No FTP connection. Use FTP Connect node first.")

            if detailed:
                items = []
                ftp.dir(remote_path or ".", items.append)
            else:
                if remote_path:
                    items = ftp.nlst(remote_path)
                else:
                    items = ftp.nlst()

            self.set_output_value("items", items)
            self.set_output_value("count", len(items))
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"count": len(items)},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("items", [])
            self.set_output_value("count", 0)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class FTPDeleteNode(BaseNode):
    """
    Delete a file on FTP server.

    Inputs:
        remote_path: Remote file path to delete

    Outputs:
        deleted: Whether deletion succeeded
    """

    def __init__(self, node_id: str, name: str = "FTP Delete", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FTPDeleteNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("remote_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("deleted", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            remote_path = str(self.get_input_value("remote_path", context) or "")

            if not remote_path:
                raise ValueError("remote_path is required")

            ftp = context.get_variable("_ftp_connection")
            if ftp is None:
                raise RuntimeError("No FTP connection. Use FTP Connect node first.")

            ftp.delete(remote_path)

            self.set_output_value("deleted", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"deleted": True},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("deleted", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class FTPMakeDirNode(BaseNode):
    """
    Create a directory on FTP server.

    Config:
        parents: Create parent directories (default: False)

    Inputs:
        remote_path: Remote directory path to create

    Outputs:
        created: Whether creation succeeded
    """

    def __init__(self, node_id: str, name: str = "FTP Make Dir", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FTPMakeDirNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("remote_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("created", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            remote_path = str(self.get_input_value("remote_path", context) or "")
            parents = self.config.get("parents", False)

            if not remote_path:
                raise ValueError("remote_path is required")

            ftp = context.get_variable("_ftp_connection")
            if ftp is None:
                raise RuntimeError("No FTP connection. Use FTP Connect node first.")

            if parents:
                # Create parent directories
                parts = remote_path.replace("\\", "/").split("/")
                current = ""
                for part in parts:
                    if part:
                        current = f"{current}/{part}" if current else part
                        try:
                            ftp.mkd(current)
                        except ftplib.error_perm:
                            pass  # Directory may already exist
            else:
                ftp.mkd(remote_path)

            self.set_output_value("created", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"created": True},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("created", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class FTPRemoveDirNode(BaseNode):
    """
    Remove a directory on FTP server.

    Inputs:
        remote_path: Remote directory path to remove

    Outputs:
        removed: Whether removal succeeded
    """

    def __init__(self, node_id: str, name: str = "FTP Remove Dir", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FTPRemoveDirNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("remote_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("removed", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            remote_path = str(self.get_input_value("remote_path", context) or "")

            if not remote_path:
                raise ValueError("remote_path is required")

            ftp = context.get_variable("_ftp_connection")
            if ftp is None:
                raise RuntimeError("No FTP connection. Use FTP Connect node first.")

            ftp.rmd(remote_path)

            self.set_output_value("removed", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"removed": True},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("removed", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class FTPRenameNode(BaseNode):
    """
    Rename a file or directory on FTP server.

    Inputs:
        old_path: Current remote path
        new_path: New remote path

    Outputs:
        renamed: Whether rename succeeded
    """

    def __init__(self, node_id: str, name: str = "FTP Rename", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FTPRenameNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("old_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("new_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("renamed", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            old_path = str(self.get_input_value("old_path", context) or "")
            new_path = str(self.get_input_value("new_path", context) or "")

            if not old_path or not new_path:
                raise ValueError("old_path and new_path are required")

            ftp = context.get_variable("_ftp_connection")
            if ftp is None:
                raise RuntimeError("No FTP connection. Use FTP Connect node first.")

            ftp.rename(old_path, new_path)

            self.set_output_value("renamed", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"renamed": True},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("renamed", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class FTPDisconnectNode(BaseNode):
    """
    Disconnect from FTP server.

    Outputs:
        disconnected: Whether disconnect succeeded
    """

    def __init__(self, node_id: str, name: str = "FTP Disconnect", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FTPDisconnectNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("disconnected", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            ftp = context.get_variable("_ftp_connection")
            if ftp is not None:
                try:
                    ftp.quit()
                except Exception:
                    ftp.close()
                context.set_variable("_ftp_connection", None)

            self.set_output_value("disconnected", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"disconnected": True},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("disconnected", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class FTPGetSizeNode(BaseNode):
    """
    Get the size of a file on FTP server.

    Inputs:
        remote_path: Remote file path

    Outputs:
        size: File size in bytes
        found: Whether file was found
    """

    def __init__(self, node_id: str, name: str = "FTP Get Size", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FTPGetSizeNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("remote_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("size", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("found", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            remote_path = str(self.get_input_value("remote_path", context) or "")

            if not remote_path:
                raise ValueError("remote_path is required")

            ftp = context.get_variable("_ftp_connection")
            if ftp is None:
                raise RuntimeError("No FTP connection. Use FTP Connect node first.")

            size = ftp.size(remote_path)

            self.set_output_value("size", size or 0)
            self.set_output_value("found", size is not None)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"size": size},
                "next_nodes": ["exec_out"]
            }

        except ftplib.error_perm:
            self.set_output_value("size", 0)
            self.set_output_value("found", False)
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"found": False},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("size", 0)
            self.set_output_value("found", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""
