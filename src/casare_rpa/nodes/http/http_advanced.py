"""
Advanced HTTP nodes for CasareRPA.

This module provides advanced HTTP operations:
- SetHttpHeadersNode: Configure headers for requests
- ParseJsonResponseNode: Parse JSON response and extract data
- HttpDownloadFileNode: Download file from URL
- HttpUploadFileNode: Upload file via HTTP
- BuildUrlNode: Build URL with query parameters
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urljoin

import aiohttp
from aiohttp import ClientTimeout, FormData
from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
    PortType,
)


@executable_node
@node_schema(
    PropertyDef(
        "header_name",
        PropertyType.STRING,
        default="",
        label="Header Name",
        tooltip="Single header name to add",
    ),
    PropertyDef(
        "header_value",
        PropertyType.STRING,
        default="",
        label="Header Value",
        tooltip="Single header value to add",
    ),
    PropertyDef(
        "headers_json",
        PropertyType.JSON,
        default={},
        label="Headers JSON",
        tooltip="Multiple headers as JSON object",
    ),
)
class SetHttpHeadersNode(BaseNode):
    """
    Configure HTTP headers for subsequent requests.

    Config (via @node_schema):
        header_name: Single header name
        header_value: Single header value
        headers_json: Multiple headers as dict

    Inputs:
        base_headers: Existing headers to extend
        header_name: Header name override
        header_value: Header value override
        headers_json: Headers JSON override

    Outputs:
        headers: Combined headers dict
    """

    def __init__(
        self, node_id: str, name: str = "Set HTTP Headers", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "SetHttpHeadersNode"

    def _define_ports(self) -> None:
        self.add_input_port("base_headers", PortType.INPUT, DataType.DICT)
        self.add_input_port("header_name", PortType.INPUT, DataType.STRING)
        self.add_input_port("header_value", PortType.INPUT, DataType.STRING)
        self.add_input_port("headers_json", PortType.INPUT, DataType.DICT)

        self.add_output_port("headers", PortType.OUTPUT, DataType.DICT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            base_headers = self.get_input_value("base_headers") or {}
            header_name = self.get_parameter("header_name", "")
            header_value = self.get_parameter("header_value", "")
            headers_json = self.get_parameter("headers_json", {})

            headers = dict(base_headers)

            if headers_json:
                if isinstance(headers_json, str):
                    try:
                        json_headers = json.loads(headers_json)
                        if isinstance(json_headers, dict):
                            headers.update(json_headers)
                    except json.JSONDecodeError:
                        pass
                elif isinstance(headers_json, dict):
                    headers.update(headers_json)

            if header_name and header_value:
                headers[header_name] = header_value

            self.set_output_value("headers", headers)

            logger.debug(f"Set HTTP headers: {list(headers.keys())}")

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"header_count": len(headers)},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = f"Set headers error: {str(e)}"
            logger.error(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


@executable_node
@node_schema(
    PropertyDef(
        "path",
        PropertyType.STRING,
        default="",
        label="JSON Path",
        tooltip="Path to extract (e.g., 'data.users[0].name')",
        placeholder="data.items[0].name",
    ),
    PropertyDef(
        "default",
        PropertyType.STRING,
        default="",
        label="Default Value",
        tooltip="Default value if path not found",
    ),
)
class ParseJsonResponseNode(BaseNode):
    """
    Parse JSON response and extract data using JSONPath-like expressions.

    Config (via @node_schema):
        path: Path to extract (dot notation)
        default: Default value if path not found

    Inputs:
        json_data: JSON string or dict to parse
        path: Path override
        default: Default value override

    Outputs:
        value: Extracted value
        success: True if extraction succeeded
        error: Error message if failed
    """

    def __init__(self, node_id: str, name: str = "Parse JSON", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ParseJsonResponseNode"

    def _define_ports(self) -> None:
        self.add_input_port("json_data", PortType.INPUT, DataType.ANY)
        self.add_input_port("path", PortType.INPUT, DataType.STRING)
        self.add_input_port("default", PortType.INPUT, DataType.ANY)

        self.add_output_port("value", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    def _extract_path(self, data: Any, path: str) -> Any:
        """Extract value from data using dot notation path."""
        if not path:
            return data

        parts = path.replace("[", ".").replace("]", "").split(".")
        current = data

        for part in parts:
            if not part:
                continue

            if isinstance(current, dict):
                if part in current:
                    current = current[part]
                else:
                    raise KeyError(f"Key '{part}' not found")

            elif isinstance(current, list):
                try:
                    index = int(part)
                    current = current[index]
                except (ValueError, IndexError) as e:
                    raise IndexError(f"Invalid list index '{part}'") from e
            else:
                raise TypeError(f"Cannot access '{part}' on {type(current).__name__}")

        return current

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            json_data = self.get_input_value("json_data")
            path = self.get_parameter("path", "")
            default = self.get_parameter("default")

            if isinstance(json_data, str):
                try:
                    json_data = json.loads(json_data)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON: {str(e)}")

            if json_data is None:
                raise ValueError("No JSON data provided")

            try:
                value = self._extract_path(json_data, path)
                self.set_output_value("value", value)
                self.set_output_value("success", True)
                self.set_output_value("error", "")

                logger.debug(f"Extracted '{path}' from JSON")

            except (KeyError, IndexError, TypeError) as e:
                if default is not None:
                    self.set_output_value("value", default)
                    self.set_output_value("success", True)
                    self.set_output_value("error", "")
                    logger.debug(f"Path '{path}' not found, using default")
                else:
                    raise ValueError(str(e))

            self.status = NodeStatus.SUCCESS
            return {"success": True, "data": {"path": path}, "next_nodes": ["exec_out"]}

        except Exception as e:
            error_msg = f"JSON parse error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


@executable_node
@node_schema(
    PropertyDef(
        "url",
        PropertyType.STRING,
        required=True,
        label="URL",
        tooltip="URL to download from",
        placeholder="https://example.com/file.pdf",
    ),
    PropertyDef(
        "save_path",
        PropertyType.FILE_PATH,
        required=True,
        label="Save Path",
        tooltip="Path to save downloaded file",
        placeholder="C:\\Downloads\\file.pdf",
    ),
    PropertyDef(
        "headers",
        PropertyType.JSON,
        default={},
        label="Headers",
        tooltip="Request headers as JSON object",
    ),
    PropertyDef(
        "timeout",
        PropertyType.FLOAT,
        default=300.0,
        min_value=0.1,
        label="Timeout (seconds)",
        tooltip="Download timeout in seconds",
    ),
    PropertyDef(
        "overwrite",
        PropertyType.BOOLEAN,
        default=True,
        label="Overwrite Existing",
        tooltip="Overwrite file if it already exists",
    ),
    PropertyDef(
        "verify_ssl",
        PropertyType.BOOLEAN,
        default=True,
        label="Verify SSL",
        tooltip="Verify SSL certificates",
    ),
    PropertyDef(
        "proxy",
        PropertyType.STRING,
        default="",
        label="Proxy URL",
        tooltip="HTTP proxy URL (optional)",
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Retry Count",
        tooltip="Number of retry attempts on failure",
    ),
    PropertyDef(
        "retry_delay",
        PropertyType.FLOAT,
        default=2.0,
        min_value=0.0,
        label="Retry Delay (seconds)",
        tooltip="Delay between retry attempts",
    ),
    PropertyDef(
        "chunk_size",
        PropertyType.INTEGER,
        default=8192,
        min_value=512,
        label="Chunk Size (bytes)",
        tooltip="Download chunk size in bytes",
    ),
)
class HttpDownloadFileNode(BaseNode):
    """
    Download a file from a URL and save to disk.

    Config (via @node_schema):
        url: URL to download from (required)
        save_path: Path to save file (required)
        headers: Request headers
        timeout: Download timeout
        overwrite: Overwrite existing file
        verify_ssl: Verify SSL certificates
        proxy: Proxy URL (optional)
        retry_count: Retry attempts
        retry_delay: Delay between retries
        chunk_size: Download chunk size

    Inputs:
        url, save_path, headers, timeout

    Outputs:
        file_path, file_size, success, error
    """

    def __init__(
        self, node_id: str, name: str = "HTTP Download File", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "HttpDownloadFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("url", PortType.INPUT, DataType.STRING)
        self.add_input_port("save_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("headers", PortType.INPUT, DataType.DICT)
        self.add_input_port("timeout", PortType.INPUT, DataType.FLOAT)

        self.add_output_port("file_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("file_size", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            url = self.get_parameter("url")
            save_path = self.get_parameter("save_path")
            headers = self.get_parameter("headers", {})
            timeout_seconds = self.get_parameter("timeout", 300.0)
            overwrite = self.get_parameter("overwrite", True)
            verify_ssl = self.get_parameter("verify_ssl", True)
            proxy = self.get_parameter("proxy", "")
            retry_count = self.get_parameter("retry_count", 0)
            retry_delay = self.get_parameter("retry_delay", 2.0)
            chunk_size = self.get_parameter("chunk_size", 8192)

            url = context.resolve_value(url)
            save_path = context.resolve_value(save_path)

            if not url:
                raise ValueError("URL is required")
            if not save_path:
                raise ValueError("Save path is required")

            save_path = Path(save_path)

            if save_path.exists() and not overwrite:
                raise FileExistsError(f"File already exists: {save_path}")

            save_path.parent.mkdir(parents=True, exist_ok=True)

            if isinstance(headers, str):
                try:
                    headers = json.loads(headers)
                except json.JSONDecodeError:
                    headers = {}

            timeout = ClientTimeout(total=float(timeout_seconds))
            ssl_context = None if verify_ssl else False

            logger.info(f"Downloading file from {url}")

            for attempt in range(max(1, retry_count + 1)):
                try:
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        request_kwargs = {
                            "headers": headers,
                            "ssl": ssl_context,
                        }
                        if proxy:
                            request_kwargs["proxy"] = proxy

                        async with session.get(url, **request_kwargs) as response:
                            if response.status != 200:
                                raise aiohttp.ClientError(f"HTTP {response.status}")

                            with open(save_path, "wb") as f:
                                async for chunk in response.content.iter_chunked(
                                    chunk_size
                                ):
                                    f.write(chunk)

                            file_size = save_path.stat().st_size

                            self.set_output_value("file_path", str(save_path))
                            self.set_output_value("file_size", file_size)
                            self.set_output_value("success", True)
                            self.set_output_value("error", "")

                            logger.info(f"Downloaded {file_size} bytes to {save_path}")

                            self.status = NodeStatus.SUCCESS
                            return {
                                "success": True,
                                "data": {
                                    "file_path": str(save_path),
                                    "file_size": file_size,
                                    "attempts": attempt + 1,
                                },
                                "next_nodes": ["exec_out"],
                            }

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt < retry_count:
                        logger.warning(
                            f"Download failed (attempt {attempt + 1}/{retry_count + 1}): {e}"
                        )
                        await asyncio.sleep(retry_delay)
                    else:
                        raise

        except Exception as e:
            error_msg = f"Download error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


@executable_node
@node_schema(
    PropertyDef(
        "url",
        PropertyType.STRING,
        required=True,
        label="URL",
        tooltip="Upload URL",
        placeholder="https://example.com/upload",
    ),
    PropertyDef(
        "file_path",
        PropertyType.FILE_PATH,
        required=True,
        label="File Path",
        tooltip="Path to file to upload",
        placeholder="C:\\Documents\\file.pdf",
    ),
    PropertyDef(
        "field_name",
        PropertyType.STRING,
        default="file",
        label="Form Field Name",
        tooltip="Form field name for the file",
    ),
    PropertyDef(
        "headers",
        PropertyType.JSON,
        default={},
        label="Headers",
        tooltip="Additional headers as JSON object",
    ),
    PropertyDef(
        "extra_fields",
        PropertyType.JSON,
        default={},
        label="Extra Form Fields",
        tooltip="Extra form fields as JSON object",
    ),
    PropertyDef(
        "timeout",
        PropertyType.FLOAT,
        default=300.0,
        min_value=0.1,
        label="Timeout (seconds)",
        tooltip="Upload timeout in seconds",
    ),
    PropertyDef(
        "verify_ssl",
        PropertyType.BOOLEAN,
        default=True,
        label="Verify SSL",
        tooltip="Verify SSL certificates",
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Retry Count",
        tooltip="Number of retry attempts on failure",
    ),
    PropertyDef(
        "retry_delay",
        PropertyType.FLOAT,
        default=2.0,
        min_value=0.0,
        label="Retry Delay (seconds)",
        tooltip="Delay between retry attempts",
    ),
)
class HttpUploadFileNode(BaseNode):
    """
    Upload a file via HTTP POST multipart/form-data.

    Config (via @node_schema):
        url: Upload URL (required)
        file_path: Path to file (required)
        field_name: Form field name
        headers: Additional headers
        extra_fields: Extra form fields
        timeout: Upload timeout
        verify_ssl: Verify SSL certificates
        retry_count: Retry attempts
        retry_delay: Delay between retries

    Inputs:
        url, file_path, field_name, headers, extra_fields, timeout

    Outputs:
        response_body, response_json, status_code, success, error
    """

    def __init__(
        self, node_id: str, name: str = "HTTP Upload File", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "HttpUploadFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("url", PortType.INPUT, DataType.STRING)
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("field_name", PortType.INPUT, DataType.STRING)
        self.add_input_port("headers", PortType.INPUT, DataType.DICT)
        self.add_input_port("extra_fields", PortType.INPUT, DataType.DICT)
        self.add_input_port("timeout", PortType.INPUT, DataType.FLOAT)

        self.add_output_port("response_body", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("response_json", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("status_code", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            url = self.get_parameter("url")
            file_path = self.get_parameter("file_path")
            field_name = self.get_parameter("field_name", "file")
            headers = self.get_parameter("headers", {})
            extra_fields = self.get_parameter("extra_fields", {})
            timeout_seconds = self.get_parameter("timeout", 300.0)
            verify_ssl = self.get_parameter("verify_ssl", True)
            retry_count = self.get_parameter("retry_count", 0)
            retry_delay = self.get_parameter("retry_delay", 2.0)

            url = context.resolve_value(url)
            file_path = context.resolve_value(file_path)

            if not url:
                raise ValueError("URL is required")
            if not file_path:
                raise ValueError("File path is required")

            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            if isinstance(headers, str):
                try:
                    headers = json.loads(headers)
                except json.JSONDecodeError:
                    headers = {}

            if isinstance(extra_fields, str):
                try:
                    extra_fields = json.loads(extra_fields)
                except json.JSONDecodeError:
                    extra_fields = {}

            timeout = ClientTimeout(total=float(timeout_seconds))
            ssl_context = None if verify_ssl else False

            logger.info(f"Uploading file {file_path} to {url}")

            for attempt in range(max(1, retry_count + 1)):
                try:
                    data = FormData()
                    data.add_field(
                        field_name, open(file_path, "rb"), filename=file_path.name
                    )
                    for key, value in extra_fields.items():
                        data.add_field(key, str(value))

                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.post(
                            url, data=data, headers=headers, ssl=ssl_context
                        ) as response:
                            response_body = await response.text()
                            status_code = response.status

                            response_json = None
                            try:
                                response_json = json.loads(response_body)
                            except (json.JSONDecodeError, ValueError):
                                pass

                            success = 200 <= status_code < 300

                            self.set_output_value("response_body", response_body)
                            self.set_output_value("response_json", response_json)
                            self.set_output_value("status_code", status_code)
                            self.set_output_value("success", success)
                            self.set_output_value(
                                "error", "" if success else f"HTTP {status_code}"
                            )

                            logger.info(
                                f"Upload completed: HTTP {status_code} (attempt {attempt + 1})"
                            )

                            self.status = NodeStatus.SUCCESS
                            return {
                                "success": True,
                                "data": {
                                    "status_code": status_code,
                                    "file": str(file_path),
                                    "attempts": attempt + 1,
                                },
                                "next_nodes": ["exec_out"],
                            }

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt < retry_count:
                        logger.warning(
                            f"Upload failed (attempt {attempt + 1}/{retry_count + 1}): {e}"
                        )
                        await asyncio.sleep(retry_delay)
                    else:
                        raise

        except Exception as e:
            error_msg = f"Upload error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.set_output_value("status_code", 0)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


@executable_node
@node_schema(
    PropertyDef(
        "base_url",
        PropertyType.STRING,
        required=True,
        label="Base URL",
        tooltip="Base URL (e.g., https://api.example.com)",
        placeholder="https://api.example.com",
    ),
    PropertyDef(
        "path",
        PropertyType.STRING,
        default="",
        label="Path",
        tooltip="Path to append to base URL",
        placeholder="/users/123",
    ),
    PropertyDef(
        "params",
        PropertyType.JSON,
        default={},
        label="Query Parameters",
        tooltip="Query parameters as JSON object",
    ),
)
class BuildUrlNode(BaseNode):
    """
    Build a URL with query parameters.

    Config (via @node_schema):
        base_url: Base URL (required)
        path: Path to append
        params: Query parameters

    Inputs:
        base_url, path, params

    Outputs:
        url: Complete URL with parameters
    """

    def __init__(self, node_id: str, name: str = "Build URL", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "BuildUrlNode"

    def _define_ports(self) -> None:
        self.add_input_port("base_url", PortType.INPUT, DataType.STRING)
        self.add_input_port("path", PortType.INPUT, DataType.STRING)
        self.add_input_port("params", PortType.INPUT, DataType.DICT)

        self.add_output_port("url", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            base_url = self.get_parameter("base_url")
            path = self.get_parameter("path", "")
            params = self.get_parameter("params", {})

            base_url = context.resolve_value(base_url)
            path = context.resolve_value(path)

            if not base_url:
                raise ValueError("Base URL is required")

            if isinstance(params, str):
                try:
                    params = json.loads(params)
                except json.JSONDecodeError:
                    params = {}

            url = base_url
            if path:
                url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))

            if params:
                query_string = urlencode(params)
                separator = "&" if "?" in url else "?"
                url = f"{url}{separator}{query_string}"

            self.set_output_value("url", url)

            logger.debug(f"Built URL: {url}")

            self.status = NodeStatus.SUCCESS
            return {"success": True, "data": {"url": url}, "next_nodes": ["exec_out"]}

        except Exception as e:
            error_msg = f"Build URL error: {str(e)}"
            logger.error(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


__all__ = [
    "SetHttpHeadersNode",
    "ParseJsonResponseNode",
    "HttpDownloadFileNode",
    "HttpUploadFileNode",
    "BuildUrlNode",
]
