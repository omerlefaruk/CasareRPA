"""
Super Node for CasareRPA HTTP Operations.

This module provides a consolidated "HTTP Super Node" that combines
multiple HTTP operations into a single action-based node with dynamic ports.

HttpSuperNode (8 operations):
    Request Methods:
        - GET: Make a GET request
        - POST: Make a POST request with body
        - PUT: Make a PUT request with body
        - PATCH: Make a PATCH request with body
        - DELETE: Make a DELETE request

    File Operations:
        - Download: Download file from URL
        - Upload: Upload file via multipart form

    Configuration:
        - Auth: Configure authentication headers
"""

import json
import os
from collections.abc import Awaitable, Callable
from enum import Enum
from typing import TYPE_CHECKING, Any

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.dynamic_port_config import (
    ActionPortConfig,
    DynamicPortSchema,
    PortDef,
)
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)
from casare_rpa.nodes.http.http_base import get_http_client_from_context

if TYPE_CHECKING:
    from casare_rpa.infrastructure.execution import ExecutionContext


class HttpAction(str, Enum):
    """Actions available in HttpSuperNode."""

    # Request methods
    GET = "GET Request"
    POST = "POST Request"
    PUT = "PUT Request"
    PATCH = "PATCH Request"
    DELETE = "DELETE Request"

    # File operations
    DOWNLOAD = "Download File"
    UPLOAD = "Upload File"

    # Configuration
    AUTH = "Configure Auth"


# Port schema for dynamic port visibility
HTTP_PORT_SCHEMA = DynamicPortSchema()

# Common output ports for all request methods
_REQUEST_OUTPUTS = [
    PortDef("response_body", DataType.STRING),
    PortDef("response_json", DataType.ANY),
    PortDef("status_code", DataType.INTEGER),
    PortDef("response_headers", DataType.DICT),
    PortDef("success", DataType.BOOLEAN),
    PortDef("error", DataType.STRING),
]

# GET Request ports
HTTP_PORT_SCHEMA.register(
    HttpAction.GET.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("url", DataType.STRING),
            PortDef("headers", DataType.DICT),
            PortDef("params", DataType.DICT),
        ],
        outputs=_REQUEST_OUTPUTS,
    ),
)

# POST Request ports
HTTP_PORT_SCHEMA.register(
    HttpAction.POST.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("url", DataType.STRING),
            PortDef("headers", DataType.DICT),
            PortDef("body", DataType.ANY),
            PortDef("params", DataType.DICT),
        ],
        outputs=_REQUEST_OUTPUTS,
    ),
)

# PUT Request ports
HTTP_PORT_SCHEMA.register(
    HttpAction.PUT.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("url", DataType.STRING),
            PortDef("headers", DataType.DICT),
            PortDef("body", DataType.ANY),
        ],
        outputs=_REQUEST_OUTPUTS,
    ),
)

# PATCH Request ports
HTTP_PORT_SCHEMA.register(
    HttpAction.PATCH.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("url", DataType.STRING),
            PortDef("headers", DataType.DICT),
            PortDef("body", DataType.ANY),
        ],
        outputs=_REQUEST_OUTPUTS,
    ),
)

# DELETE Request ports
HTTP_PORT_SCHEMA.register(
    HttpAction.DELETE.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("url", DataType.STRING),
            PortDef("headers", DataType.DICT),
        ],
        outputs=_REQUEST_OUTPUTS,
    ),
)

# Download File ports
HTTP_PORT_SCHEMA.register(
    HttpAction.DOWNLOAD.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("url", DataType.STRING),
            PortDef("save_path", DataType.STRING),
            PortDef("headers", DataType.DICT),
        ],
        outputs=[
            PortDef("file_path", DataType.STRING),
            PortDef("file_size", DataType.INTEGER),
            PortDef("status_code", DataType.INTEGER),
            PortDef("success", DataType.BOOLEAN),
            PortDef("error", DataType.STRING),
        ],
    ),
)

# Upload File ports
HTTP_PORT_SCHEMA.register(
    HttpAction.UPLOAD.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("url", DataType.STRING),
            PortDef("file_path", DataType.STRING),
            PortDef("headers", DataType.DICT),
        ],
        outputs=_REQUEST_OUTPUTS,
    ),
)

# Auth Configuration ports
HTTP_PORT_SCHEMA.register(
    HttpAction.AUTH.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("token", DataType.STRING),
            PortDef("username", DataType.STRING),
            PortDef("password", DataType.STRING),
        ],
        outputs=[
            PortDef("auth_headers", DataType.DICT),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)


# Action groupings for display_when
REQUEST_ACTIONS = [
    HttpAction.GET.value,
    HttpAction.POST.value,
    HttpAction.PUT.value,
    HttpAction.PATCH.value,
    HttpAction.DELETE.value,
]

BODY_ACTIONS = [
    HttpAction.POST.value,
    HttpAction.PUT.value,
    HttpAction.PATCH.value,
]


@properties(
    # === ESSENTIAL: Action selector (always visible) ===
    PropertyDef(
        "action",
        PropertyType.CHOICE,
        default=HttpAction.GET.value,
        label="Action",
        tooltip="HTTP operation to perform",
        essential=True,
        order=0,
        choices=[a.value for a in HttpAction],
    ),
    # === URL PROPERTY (for request actions) ===
    PropertyDef(
        "url",
        PropertyType.STRING,
        default="",
        label="URL",
        tooltip="Target URL for the request",
        placeholder="https://api.example.com/endpoint",
        order=1,
        required=True,
        display_when={
            "action": REQUEST_ACTIONS + [HttpAction.DOWNLOAD.value, HttpAction.UPLOAD.value]
        },
    ),
    # === REQUEST OPTIONS ===
    PropertyDef(
        "headers",
        PropertyType.JSON,
        default={},
        label="Headers",
        tooltip="Request headers as JSON object",
        order=10,
        display_when={
            "action": REQUEST_ACTIONS + [HttpAction.DOWNLOAD.value, HttpAction.UPLOAD.value]
        },
    ),
    PropertyDef(
        "params",
        PropertyType.JSON,
        default={},
        label="Query Parameters",
        tooltip="URL query parameters as JSON object",
        order=11,
        display_when={"action": [HttpAction.GET.value, HttpAction.POST.value]},
    ),
    PropertyDef(
        "body",
        PropertyType.TEXT,
        default="",
        label="Request Body",
        tooltip="Request body (JSON or string)",
        order=12,
        display_when={"action": BODY_ACTIONS},
    ),
    PropertyDef(
        "content_type",
        PropertyType.STRING,
        default="application/json",
        label="Content-Type",
        tooltip="Content-Type header for request body",
        order=13,
        display_when={"action": BODY_ACTIONS},
    ),
    # === TIMEOUT & RETRY OPTIONS ===
    PropertyDef(
        "timeout",
        PropertyType.FLOAT,
        default=30.0,
        min_value=0.1,
        label="Timeout (seconds)",
        tooltip="Request timeout in seconds",
        order=20,
        display_when={
            "action": REQUEST_ACTIONS + [HttpAction.DOWNLOAD.value, HttpAction.UPLOAD.value]
        },
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Retry Count",
        tooltip="Number of retry attempts on failure",
        order=21,
        display_when={"action": REQUEST_ACTIONS + [HttpAction.DOWNLOAD.value]},
    ),
    PropertyDef(
        "verify_ssl",
        PropertyType.BOOLEAN,
        default=True,
        label="Verify SSL",
        tooltip="Verify SSL certificates",
        order=22,
        display_when={
            "action": REQUEST_ACTIONS + [HttpAction.DOWNLOAD.value, HttpAction.UPLOAD.value]
        },
    ),
    # === DOWNLOAD OPTIONS ===
    PropertyDef(
        "save_path",
        PropertyType.STRING,
        default="",
        label="Save Path",
        tooltip="Path to save downloaded file",
        order=30,
        required=True,
        display_when={"action": [HttpAction.DOWNLOAD.value]},
    ),
    PropertyDef(
        "create_dirs",
        PropertyType.BOOLEAN,
        default=True,
        label="Create Directories",
        tooltip="Automatically create parent directories",
        order=31,
        display_when={"action": [HttpAction.DOWNLOAD.value]},
    ),
    PropertyDef(
        "overwrite",
        PropertyType.BOOLEAN,
        default=False,
        label="Overwrite Existing",
        tooltip="Overwrite file if it exists",
        order=32,
        display_when={"action": [HttpAction.DOWNLOAD.value]},
    ),
    # === UPLOAD OPTIONS ===
    PropertyDef(
        "file_path",
        PropertyType.STRING,
        default="",
        label="File Path",
        tooltip="Path to file to upload",
        order=30,
        required=True,
        display_when={"action": [HttpAction.UPLOAD.value]},
    ),
    PropertyDef(
        "field_name",
        PropertyType.STRING,
        default="file",
        label="Field Name",
        tooltip="Form field name for the file",
        order=31,
        display_when={"action": [HttpAction.UPLOAD.value]},
    ),
    PropertyDef(
        "extra_fields",
        PropertyType.JSON,
        default={},
        label="Extra Fields",
        tooltip="Additional form fields as JSON object",
        order=32,
        display_when={"action": [HttpAction.UPLOAD.value]},
    ),
    # === AUTH OPTIONS ===
    PropertyDef(
        "auth_type",
        PropertyType.CHOICE,
        default="bearer",
        choices=["bearer", "basic", "api_key"],
        label="Auth Type",
        tooltip="Authentication type",
        order=30,
        display_when={"action": [HttpAction.AUTH.value]},
    ),
    PropertyDef(
        "token",
        PropertyType.STRING,
        default="",
        label="Token / API Key",
        tooltip="Bearer token or API key",
        order=31,
        display_when={"action": [HttpAction.AUTH.value]},
    ),
    PropertyDef(
        "username",
        PropertyType.STRING,
        default="",
        label="Username",
        tooltip="Username for Basic auth",
        order=32,
        display_when={"action": [HttpAction.AUTH.value]},
    ),
    PropertyDef(
        "password",
        PropertyType.STRING,
        default="",
        label="Password",
        tooltip="Password for Basic auth",
        order=33,
        display_when={"action": [HttpAction.AUTH.value]},
    ),
    PropertyDef(
        "header_name",
        PropertyType.STRING,
        default="X-API-Key",
        label="Header Name",
        tooltip="Custom header name for API key auth",
        order=34,
        display_when={"action": [HttpAction.AUTH.value]},
    ),
)
@node(category="http")
class HttpSuperNode(BaseNode):
    """
    Unified HTTP operations node.

    Consolidates HTTP requests (GET, POST, PUT, PATCH, DELETE), file download/upload,
    and authentication configuration into a single configurable node.
    Select an action from the dropdown to see relevant properties and ports.

    Actions:
        Request Methods:
        - GET Request: Make a GET request
        - POST Request: Make a POST request with body
        - PUT Request: Make a PUT request with body
        - PATCH Request: Make a PATCH request with body
        - DELETE Request: Make a DELETE request

        File Operations:
        - Download File: Download file from URL
        - Upload File: Upload file via multipart form

        Configuration:
        - Configure Auth: Generate authentication headers

    Features:
        - Connection pooling for performance
        - Rate limiting per domain
        - Circuit breaker for resilience
        - Automatic retry with exponential backoff
        - SSRF protection
    """

    def __init__(self, node_id: str, name: str = "HTTP", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "HttpSuperNode"

    def _define_ports(self) -> None:
        """Define ports based on current action."""
        # Default to GET Request ports
        self.add_input_port("url", DataType.STRING)
        self.add_input_port("headers", DataType.DICT)
        self.add_input_port("params", DataType.DICT)
        self.add_output_port("response_body", DataType.STRING)
        self.add_output_port("response_json", DataType.ANY)
        self.add_output_port("status_code", DataType.INTEGER)
        self.add_output_port("response_headers", DataType.DICT)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def execute(self, context: "ExecutionContext") -> ExecutionResult:
        """Execute the selected HTTP action."""
        self.status = NodeStatus.RUNNING

        action = self.get_parameter("action", HttpAction.GET.value)

        # Map actions to handlers
        handlers: dict[str, Callable[[ExecutionContext], Awaitable[ExecutionResult]]] = {
            HttpAction.GET.value: self._execute_get,
            HttpAction.POST.value: self._execute_post,
            HttpAction.PUT.value: self._execute_put,
            HttpAction.PATCH.value: self._execute_patch,
            HttpAction.DELETE.value: self._execute_delete,
            HttpAction.DOWNLOAD.value: self._execute_download,
            HttpAction.UPLOAD.value: self._execute_upload,
            HttpAction.AUTH.value: self._execute_auth,
        }

        handler = handlers.get(action)
        if not handler:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": f"Unknown action: {action}"}

        try:
            return await handler(context)
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Error in HttpSuperNode ({action}): {e}")
            self._set_error_outputs(str(e))
            return {"success": False, "error": str(e), "next_nodes": []}

    # === HELPER METHODS ===

    def _parse_json_param(self, value: Any, default: Any = None) -> Any:
        """Parse a parameter that may be JSON string or already parsed."""
        if value is None:
            return default if default is not None else {}
        if isinstance(value, str):
            if not value.strip():
                return default if default is not None else {}
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return default if default is not None else {}
        return value

    def _get_request_params(self, context: "ExecutionContext") -> dict:
        """Get common request parameters from properties and inputs."""
        url = self.get_input_value("url", context)
        if not url:
            url = self.get_parameter("url", "")

        headers = self.get_input_value("headers", context)
        if not headers:
            headers = self.get_parameter("headers", {})
        headers = self._parse_json_param(headers, {})

        timeout = self.get_parameter("timeout", 30.0)
        retry_count = self.get_parameter("retry_count", 0)

        return {
            "url": url,
            "headers": headers,
            "timeout": float(timeout),
            "retry_count": int(retry_count),
        }

    def _set_error_outputs(self, error_msg: str) -> None:
        """Set output values for error case."""
        self.set_output_value("success", False)
        self.set_output_value("error", error_msg)
        self.set_output_value("status_code", 0)
        self.set_output_value("response_body", "")
        self.set_output_value("response_json", None)
        self.set_output_value("response_headers", {})

    def _set_success_outputs(
        self,
        response_body: str,
        status_code: int,
        response_headers: dict,
    ) -> None:
        """Set output values for successful response."""
        success = 200 <= status_code < 300

        # Try to parse JSON
        response_json = None
        try:
            response_json = json.loads(response_body)
        except (json.JSONDecodeError, ValueError):
            pass

        self.set_output_value("response_body", response_body)
        self.set_output_value("response_json", response_json)
        self.set_output_value("status_code", status_code)
        self.set_output_value("response_headers", response_headers)
        self.set_output_value("success", success)
        self.set_output_value("error", "" if success else f"HTTP {status_code}")

    async def _make_request(
        self,
        context: "ExecutionContext",
        method: str,
        include_body: bool = False,
        include_params: bool = False,
    ) -> ExecutionResult:
        """Make an HTTP request with the specified method."""
        params = self._get_request_params(context)

        if not params["url"]:
            raise ValueError("URL is required")

        # Get UnifiedHttpClient from context
        client = await get_http_client_from_context(context)

        # Build request kwargs
        request_kwargs: dict[str, Any] = {
            "method": method,
            "url": params["url"],
            "headers": params["headers"] if params["headers"] else None,
            "timeout": params["timeout"],
            "retry_count": max(1, params["retry_count"] + 1),
        }

        # Add query params
        if include_params:
            query_params = self.get_input_value("params", context)
            if not query_params:
                query_params = self.get_parameter("params", {})
            query_params = self._parse_json_param(query_params, {})
            if query_params:
                request_kwargs["params"] = query_params

        # Add body for POST/PUT/PATCH
        if include_body:
            body = self.get_input_value("body", context)
            if not body:
                body = self.get_parameter("body", "")

            content_type = self.get_parameter("content_type", "application/json")

            if body:
                # Parse JSON body if string
                if isinstance(body, str):
                    try:
                        body = json.loads(body)
                    except json.JSONDecodeError:
                        pass

                if isinstance(body, (dict, list)):
                    request_kwargs["json"] = body
                else:
                    request_kwargs["data"] = str(body)
                    if content_type and "Content-Type" not in (params["headers"] or {}):
                        if request_kwargs["headers"] is None:
                            request_kwargs["headers"] = {}
                        request_kwargs["headers"]["Content-Type"] = content_type

        logger.debug(f"HTTP {method} request to {params['url']}")

        # Make request
        response = await client.request(**request_kwargs)

        # Read response
        response_body = await response.text()
        status_code = response.status
        response_headers = dict(response.headers)

        await response.release()

        self._set_success_outputs(response_body, status_code, response_headers)

        logger.info(f"HTTP {method} {params['url']} -> {status_code}")

        self.status = NodeStatus.SUCCESS
        return {
            "success": True,
            "data": {
                "status_code": status_code,
                "url": params["url"],
                "method": method,
            },
            "next_nodes": ["exec_out"],
        }

    # === REQUEST ACTION HANDLERS ===

    async def _execute_get(self, context: "ExecutionContext") -> ExecutionResult:
        """Execute GET request."""
        return await self._make_request(context, "GET", include_params=True)

    async def _execute_post(self, context: "ExecutionContext") -> ExecutionResult:
        """Execute POST request."""
        return await self._make_request(context, "POST", include_body=True, include_params=True)

    async def _execute_put(self, context: "ExecutionContext") -> ExecutionResult:
        """Execute PUT request."""
        return await self._make_request(context, "PUT", include_body=True)

    async def _execute_patch(self, context: "ExecutionContext") -> ExecutionResult:
        """Execute PATCH request."""
        return await self._make_request(context, "PATCH", include_body=True)

    async def _execute_delete(self, context: "ExecutionContext") -> ExecutionResult:
        """Execute DELETE request."""
        return await self._make_request(context, "DELETE")

    # === FILE OPERATION HANDLERS ===

    async def _execute_download(self, context: "ExecutionContext") -> ExecutionResult:
        """Download file from URL."""
        params = self._get_request_params(context)

        if not params["url"]:
            raise ValueError("URL is required")

        save_path = self.get_input_value("save_path", context)
        if not save_path:
            save_path = self.get_parameter("save_path", "")

        if not save_path:
            raise ValueError("Save path is required")

        create_dirs = self.get_parameter("create_dirs", True)
        overwrite = self.get_parameter("overwrite", False)

        # Check/create directory
        dir_path = os.path.dirname(save_path)
        if dir_path:
            if create_dirs:
                os.makedirs(dir_path, exist_ok=True)
            elif not os.path.exists(dir_path):
                raise ValueError(f"Directory does not exist: {dir_path}")

        # Check if file exists
        if os.path.exists(save_path) and not overwrite:
            raise ValueError(f"File already exists: {save_path}")

        logger.debug(f"Downloading {params['url']} to {save_path}")

        # Get client and make request
        client = await get_http_client_from_context(context)
        response = await client.request(
            method="GET",
            url=params["url"],
            headers=params["headers"] if params["headers"] else None,
            timeout=params["timeout"],
            retry_count=max(1, params["retry_count"] + 1),
        )

        status_code = response.status
        if 200 <= status_code < 300:
            # Read and save content
            content = await response.read()
            with open(save_path, "wb") as f:  # noqa: ASYNC230
                f.write(content)

            file_size = len(content)

            self.set_output_value("file_path", save_path)
            self.set_output_value("file_size", file_size)
            self.set_output_value("status_code", status_code)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.info(f"Downloaded {params['url']} -> {save_path} ({file_size} bytes)")

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"file_path": save_path, "file_size": file_size},
                "next_nodes": ["exec_out"],
            }
        else:
            await response.release()
            error_msg = f"Download failed with status {status_code}"
            self.set_output_value("file_path", "")
            self.set_output_value("file_size", 0)
            self.set_output_value("status_code", status_code)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)

            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

    async def _execute_upload(self, context: "ExecutionContext") -> ExecutionResult:
        """Upload file via multipart form."""
        import aiohttp

        params = self._get_request_params(context)

        if not params["url"]:
            raise ValueError("URL is required")

        file_path = self.get_input_value("file_path", context)
        if not file_path:
            file_path = self.get_parameter("file_path", "")

        if not file_path:
            raise ValueError("File path is required")

        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")

        field_name = self.get_parameter("field_name", "file")
        extra_fields = self.get_parameter("extra_fields", {})
        extra_fields = self._parse_json_param(extra_fields, {})

        logger.debug(f"Uploading {file_path} to {params['url']}")

        # Build multipart form data
        form_data = aiohttp.FormData()

        # Add file
        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:  # noqa: ASYNC230
            file_content = f.read()
        form_data.add_field(
            field_name,
            file_content,
            filename=filename,
        )

        # Add extra fields
        for key, value in extra_fields.items():
            form_data.add_field(key, str(value))

        # Get client and make request
        # Note: For multipart, we need to use the underlying aiohttp session
        await get_http_client_from_context(context)

        async with aiohttp.ClientSession() as session:
            headers = params["headers"] if params["headers"] else {}
            async with session.post(
                params["url"],
                data=form_data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=params["timeout"]),
            ) as response:
                response_body = await response.text()
                status_code = response.status
                response_headers = dict(response.headers)

        self._set_success_outputs(response_body, status_code, response_headers)

        logger.info(f"Uploaded {file_path} to {params['url']} -> {status_code}")

        self.status = NodeStatus.SUCCESS
        return {
            "success": True,
            "data": {
                "status_code": status_code,
                "file_path": file_path,
            },
            "next_nodes": ["exec_out"],
        }

    # === AUTH CONFIGURATION HANDLER ===

    async def _execute_auth(self, context: "ExecutionContext") -> ExecutionResult:
        """Configure authentication headers."""
        import base64

        auth_type = self.get_parameter("auth_type", "bearer")

        auth_headers = {}

        if auth_type == "bearer":
            token = self.get_input_value("token", context)
            if not token:
                token = self.get_parameter("token", "")

            if token:
                auth_headers["Authorization"] = f"Bearer {token}"
            else:
                raise ValueError("Token is required for Bearer auth")

        elif auth_type == "basic":
            username = self.get_input_value("username", context)
            if not username:
                username = self.get_parameter("username", "")

            password = self.get_input_value("password", context)
            if not password:
                password = self.get_parameter("password", "")

            if username:
                credentials = f"{username}:{password}"
                encoded = base64.b64encode(credentials.encode()).decode()
                auth_headers["Authorization"] = f"Basic {encoded}"
            else:
                raise ValueError("Username is required for Basic auth")

        elif auth_type == "api_key":
            token = self.get_input_value("token", context)
            if not token:
                token = self.get_parameter("token", "")

            header_name = self.get_parameter("header_name", "X-API-Key")

            if token:
                auth_headers[header_name] = token
            else:
                raise ValueError("API key is required")

        self.set_output_value("auth_headers", auth_headers)
        self.set_output_value("success", True)

        logger.info(f"Configured {auth_type} authentication")

        self.status = NodeStatus.SUCCESS
        return {
            "success": True,
            "data": {"auth_type": auth_type},
            "next_nodes": ["exec_out"],
        }


__all__ = [
    "HttpSuperNode",
    "HttpAction",
    "HTTP_PORT_SCHEMA",
]
