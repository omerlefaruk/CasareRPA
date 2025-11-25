"""
HTTP/REST API Nodes for CasareRPA.

This module provides nodes for making HTTP requests and interacting with REST APIs.
Supports all HTTP methods, authentication, headers, and response parsing.

Nodes:
    - HttpRequestNode: Generic HTTP request (all methods)
    - HttpGetNode: GET request with query parameters
    - HttpPostNode: POST request with body
    - HttpPutNode: PUT request with body
    - HttpPatchNode: PATCH request with body
    - HttpDeleteNode: DELETE request
    - SetHttpHeadersNode: Configure headers for requests
    - HttpAuthNode: Configure authentication (Bearer, Basic, API Key)
    - ParseJsonResponseNode: Parse JSON response and extract data
    - HttpDownloadFileNode: Download file from URL
    - HttpUploadFileNode: Upload file via HTTP
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode, urlparse, parse_qs, urljoin

import aiohttp
from aiohttp import ClientTimeout, FormData, BasicAuth
from loguru import logger

from ..core.base_node import BaseNode
from ..core.execution_context import ExecutionContext
from ..core.types import DataType, ExecutionResult, NodeStatus, PortType


class HttpRequestNode(BaseNode):
    """
    Generic HTTP request node supporting all HTTP methods.

    Inputs:
        - exec_in: Execution input
        - url: Target URL (required)
        - method: HTTP method (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS)
        - headers: Request headers as dict
        - body: Request body (for POST, PUT, PATCH)
        - params: Query parameters as dict
        - timeout: Request timeout in seconds

    Outputs:
        - exec_out: Execution output
        - response_body: Response body as string
        - response_json: Parsed JSON response (if applicable)
        - status_code: HTTP status code
        - response_headers: Response headers as dict
        - success: True if status code is 2xx
        - error: Error message if request failed
    """

    def __init__(self, node_id: str, name: str = "HTTP Request", **kwargs: Any) -> None:
        # Default config with all HTTP request options
        default_config = {
            "method": "GET",
            "url": "",
            "headers": {},
            "body": "",
            "params": {},
            "timeout": 30.0,
            "verify_ssl": True,
            "follow_redirects": True,
            "max_redirects": 10,  # Maximum number of redirects to follow
            "content_type": "application/json",
            # Proxy settings
            "proxy": "",  # Proxy URL (e.g., http://proxy:8080)
            # Retry settings
            "retry_count": 0,  # Number of retry attempts (0 = no retries)
            "retry_delay": 1.0,  # Delay between retries in seconds
            # Response handling
            "response_encoding": "",  # Force response encoding (empty = auto-detect)
        }

        config = kwargs.get("config", {})
        # Merge with defaults
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        super().__init__(node_id, config)
        self.name = name
        self.node_type = "HttpRequestNode"

    def _define_ports(self) -> None:
        # Execution ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        # Data input ports
        self.add_input_port("url", PortType.INPUT, DataType.STRING)
        self.add_input_port("method", PortType.INPUT, DataType.STRING)
        self.add_input_port("headers", PortType.INPUT, DataType.DICT)
        self.add_input_port("body", PortType.INPUT, DataType.ANY)
        self.add_input_port("params", PortType.INPUT, DataType.DICT)
        self.add_input_port("timeout", PortType.INPUT, DataType.FLOAT)

        # Data output ports
        self.add_output_port("response_body", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("response_json", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("status_code", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("response_headers", PortType.OUTPUT, DataType.DICT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # Get input values
            url = self.get_input_value("url") or self.config.get("url", "")
            method = (self.get_input_value("method") or self.config.get("method", "GET")).upper()
            headers = self.get_input_value("headers") or self.config.get("headers", {})
            body = self.get_input_value("body") or self.config.get("body", "")
            params = self.get_input_value("params") or self.config.get("params", {})
            timeout_seconds = self.get_input_value("timeout") or self.config.get("timeout", 30.0)
            verify_ssl = self.config.get("verify_ssl", True)
            follow_redirects = self.config.get("follow_redirects", True)
            max_redirects = self.config.get("max_redirects", 10)
            content_type = self.config.get("content_type", "application/json")
            proxy = self.config.get("proxy", "")
            retry_count = self.config.get("retry_count", 0)
            retry_delay = self.config.get("retry_delay", 1.0)
            response_encoding = self.config.get("response_encoding", "")

            # Validate URL
            if not url:
                raise ValueError("URL is required")

            # Ensure headers is a dict
            if isinstance(headers, str):
                try:
                    headers = json.loads(headers)
                except json.JSONDecodeError:
                    headers = {}

            # Set content type if not already set
            if content_type and "Content-Type" not in headers:
                headers["Content-Type"] = content_type

            # Prepare body
            request_body = None
            if body and method in ["POST", "PUT", "PATCH"]:
                if isinstance(body, (dict, list)):
                    request_body = json.dumps(body)
                else:
                    request_body = str(body)

            # Create timeout
            timeout = ClientTimeout(total=float(timeout_seconds))

            # Create SSL context
            ssl_context = None if verify_ssl else False

            # Build connector with proxy if specified
            connector = None
            if proxy:
                logger.debug(f"Using proxy: {proxy}")

            logger.debug(f"HTTP {method} request to {url}")

            # Retry loop
            last_error = None
            for attempt in range(max(1, retry_count + 1)):
                try:
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        request_kwargs = {
                            "method": method,
                            "url": url,
                            "headers": headers,
                            "data": request_body,
                            "params": params,
                            "ssl": ssl_context,
                            "allow_redirects": follow_redirects,
                            "max_redirects": max_redirects,
                        }
                        if proxy:
                            request_kwargs["proxy"] = proxy

                        async with session.request(**request_kwargs) as response:
                            # Handle response encoding
                            if response_encoding:
                                response_body = await response.text(encoding=response_encoding)
                            else:
                                response_body = await response.text()
                            status_code = response.status
                            response_headers = dict(response.headers)

                            # Try to parse JSON
                            response_json = None
                            try:
                                response_json = json.loads(response_body)
                            except (json.JSONDecodeError, ValueError):
                                pass

                            # Determine success
                            success = 200 <= status_code < 300

                            # Set outputs
                            self.set_output_value("response_body", response_body)
                            self.set_output_value("response_json", response_json)
                            self.set_output_value("status_code", status_code)
                            self.set_output_value("response_headers", response_headers)
                            self.set_output_value("success", success)
                            self.set_output_value("error", "" if success else f"HTTP {status_code}")

                            logger.info(f"HTTP {method} {url} -> {status_code}")

                            self.status = NodeStatus.SUCCESS
                            return {
                                "success": True,
                                "data": {
                                    "status_code": status_code,
                                    "url": url,
                                    "method": method,
                                    "attempts": attempt + 1
                                },
                                "next_nodes": ["exec_out"]
                            }

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    last_error = e
                    if attempt < retry_count:
                        logger.warning(f"HTTP request failed (attempt {attempt + 1}/{retry_count + 1}): {e}")
                        await asyncio.sleep(retry_delay)
                    else:
                        raise

        except aiohttp.ClientError as e:
            error_msg = f"HTTP request failed: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.set_output_value("status_code", 0)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

        except asyncio.TimeoutError:
            error_msg = f"Request timed out after {timeout_seconds} seconds"
            logger.error(error_msg)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.set_output_value("status_code", 0)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

        except Exception as e:
            error_msg = f"HTTP request error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


class HttpGetNode(BaseNode):
    """
    HTTP GET request node with query parameter support.

    Inputs:
        - exec_in: Execution input
        - url: Target URL (required)
        - params: Query parameters as dict
        - headers: Request headers as dict
        - timeout: Request timeout in seconds

    Outputs:
        - exec_out: Execution output
        - response_body: Response body as string
        - response_json: Parsed JSON response
        - status_code: HTTP status code
        - success: True if status code is 2xx
    """

    def __init__(self, node_id: str, name: str = "HTTP GET", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        config.setdefault("url", "")
        config.setdefault("params", {})
        config.setdefault("headers", {})
        config.setdefault("timeout", 30.0)
        config.setdefault("verify_ssl", True)
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "HttpGetNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        self.add_input_port("url", PortType.INPUT, DataType.STRING)
        self.add_input_port("params", PortType.INPUT, DataType.DICT)
        self.add_input_port("headers", PortType.INPUT, DataType.DICT)
        self.add_input_port("timeout", PortType.INPUT, DataType.FLOAT)

        self.add_output_port("response_body", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("response_json", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("status_code", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            url = self.get_input_value("url") or self.config.get("url", "")
            params = self.get_input_value("params") or self.config.get("params", {})
            headers = self.get_input_value("headers") or self.config.get("headers", {})
            timeout_seconds = self.get_input_value("timeout") or self.config.get("timeout", 30.0)
            verify_ssl = self.config.get("verify_ssl", True)

            if not url:
                raise ValueError("URL is required")

            if isinstance(headers, str):
                try:
                    headers = json.loads(headers)
                except json.JSONDecodeError:
                    headers = {}

            if isinstance(params, str):
                try:
                    params = json.loads(params)
                except json.JSONDecodeError:
                    params = {}

            timeout = ClientTimeout(total=float(timeout_seconds))
            ssl_context = None if verify_ssl else False

            logger.debug(f"HTTP GET request to {url}")

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    url,
                    params=params,
                    headers=headers,
                    ssl=ssl_context
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
                    self.set_output_value("error", "" if success else f"HTTP {status_code}")

                    logger.info(f"HTTP GET {url} -> {status_code}")

                    self.status = NodeStatus.SUCCESS
                    return {
                        "success": True,
                        "data": {"status_code": status_code, "url": url},
                        "next_nodes": ["exec_out"]
                    }

        except Exception as e:
            error_msg = f"HTTP GET error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.set_output_value("status_code", 0)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


class HttpPostNode(BaseNode):
    """
    HTTP POST request node with body support.

    Inputs:
        - exec_in: Execution input
        - url: Target URL (required)
        - body: Request body (JSON, form data, or string)
        - headers: Request headers as dict
        - content_type: Content type (default: application/json)
        - timeout: Request timeout in seconds

    Outputs:
        - exec_out: Execution output
        - response_body: Response body as string
        - response_json: Parsed JSON response
        - status_code: HTTP status code
        - success: True if status code is 2xx
    """

    def __init__(self, node_id: str, name: str = "HTTP POST", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        config.setdefault("url", "")
        config.setdefault("body", "")
        config.setdefault("headers", {})
        config.setdefault("content_type", "application/json")
        config.setdefault("timeout", 30.0)
        config.setdefault("verify_ssl", True)
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "HttpPostNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        self.add_input_port("url", PortType.INPUT, DataType.STRING)
        self.add_input_port("body", PortType.INPUT, DataType.ANY)
        self.add_input_port("headers", PortType.INPUT, DataType.DICT)
        self.add_input_port("timeout", PortType.INPUT, DataType.FLOAT)

        self.add_output_port("response_body", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("response_json", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("status_code", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            url = self.get_input_value("url") or self.config.get("url", "")
            body = self.get_input_value("body") or self.config.get("body", "")
            headers = self.get_input_value("headers") or self.config.get("headers", {})
            content_type = self.config.get("content_type", "application/json")
            timeout_seconds = self.get_input_value("timeout") or self.config.get("timeout", 30.0)
            verify_ssl = self.config.get("verify_ssl", True)

            if not url:
                raise ValueError("URL is required")

            if isinstance(headers, str):
                try:
                    headers = json.loads(headers)
                except json.JSONDecodeError:
                    headers = {}

            # Set content type
            if "Content-Type" not in headers:
                headers["Content-Type"] = content_type

            # Prepare body
            request_body = None
            if body:
                if isinstance(body, (dict, list)):
                    request_body = json.dumps(body)
                else:
                    request_body = str(body)

            timeout = ClientTimeout(total=float(timeout_seconds))
            ssl_context = None if verify_ssl else False

            logger.debug(f"HTTP POST request to {url}")

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    url,
                    data=request_body,
                    headers=headers,
                    ssl=ssl_context
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
                    self.set_output_value("error", "" if success else f"HTTP {status_code}")

                    logger.info(f"HTTP POST {url} -> {status_code}")

                    self.status = NodeStatus.SUCCESS
                    return {
                        "success": True,
                        "data": {"status_code": status_code, "url": url},
                        "next_nodes": ["exec_out"]
                    }

        except Exception as e:
            error_msg = f"HTTP POST error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.set_output_value("status_code", 0)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


class HttpPutNode(BaseNode):
    """
    HTTP PUT request node for updating resources.

    Inputs:
        - exec_in: Execution input
        - url: Target URL (required)
        - body: Request body
        - headers: Request headers as dict
        - timeout: Request timeout in seconds

    Outputs:
        - exec_out: Execution output
        - response_body: Response body as string
        - response_json: Parsed JSON response
        - status_code: HTTP status code
        - success: True if status code is 2xx
    """

    def __init__(self, node_id: str, name: str = "HTTP PUT", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        config.setdefault("url", "")
        config.setdefault("body", "")
        config.setdefault("headers", {})
        config.setdefault("content_type", "application/json")
        config.setdefault("timeout", 30.0)
        config.setdefault("verify_ssl", True)
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "HttpPutNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        self.add_input_port("url", PortType.INPUT, DataType.STRING)
        self.add_input_port("body", PortType.INPUT, DataType.ANY)
        self.add_input_port("headers", PortType.INPUT, DataType.DICT)
        self.add_input_port("timeout", PortType.INPUT, DataType.FLOAT)

        self.add_output_port("response_body", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("response_json", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("status_code", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            url = self.get_input_value("url") or self.config.get("url", "")
            body = self.get_input_value("body") or self.config.get("body", "")
            headers = self.get_input_value("headers") or self.config.get("headers", {})
            content_type = self.config.get("content_type", "application/json")
            timeout_seconds = self.get_input_value("timeout") or self.config.get("timeout", 30.0)
            verify_ssl = self.config.get("verify_ssl", True)

            if not url:
                raise ValueError("URL is required")

            if isinstance(headers, str):
                try:
                    headers = json.loads(headers)
                except json.JSONDecodeError:
                    headers = {}

            if "Content-Type" not in headers:
                headers["Content-Type"] = content_type

            request_body = None
            if body:
                if isinstance(body, (dict, list)):
                    request_body = json.dumps(body)
                else:
                    request_body = str(body)

            timeout = ClientTimeout(total=float(timeout_seconds))
            ssl_context = None if verify_ssl else False

            logger.debug(f"HTTP PUT request to {url}")

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.put(
                    url,
                    data=request_body,
                    headers=headers,
                    ssl=ssl_context
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
                    self.set_output_value("error", "" if success else f"HTTP {status_code}")

                    logger.info(f"HTTP PUT {url} -> {status_code}")

                    self.status = NodeStatus.SUCCESS
                    return {
                        "success": True,
                        "data": {"status_code": status_code, "url": url},
                        "next_nodes": ["exec_out"]
                    }

        except Exception as e:
            error_msg = f"HTTP PUT error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.set_output_value("status_code", 0)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


class HttpPatchNode(BaseNode):
    """
    HTTP PATCH request node for partial updates.

    Inputs:
        - exec_in: Execution input
        - url: Target URL (required)
        - body: Request body (partial update data)
        - headers: Request headers as dict
        - timeout: Request timeout in seconds

    Outputs:
        - exec_out: Execution output
        - response_body: Response body as string
        - response_json: Parsed JSON response
        - status_code: HTTP status code
        - success: True if status code is 2xx
    """

    def __init__(self, node_id: str, name: str = "HTTP PATCH", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        config.setdefault("url", "")
        config.setdefault("body", "")
        config.setdefault("headers", {})
        config.setdefault("content_type", "application/json")
        config.setdefault("timeout", 30.0)
        config.setdefault("verify_ssl", True)
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "HttpPatchNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        self.add_input_port("url", PortType.INPUT, DataType.STRING)
        self.add_input_port("body", PortType.INPUT, DataType.ANY)
        self.add_input_port("headers", PortType.INPUT, DataType.DICT)
        self.add_input_port("timeout", PortType.INPUT, DataType.FLOAT)

        self.add_output_port("response_body", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("response_json", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("status_code", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            url = self.get_input_value("url") or self.config.get("url", "")
            body = self.get_input_value("body") or self.config.get("body", "")
            headers = self.get_input_value("headers") or self.config.get("headers", {})
            content_type = self.config.get("content_type", "application/json")
            timeout_seconds = self.get_input_value("timeout") or self.config.get("timeout", 30.0)
            verify_ssl = self.config.get("verify_ssl", True)

            if not url:
                raise ValueError("URL is required")

            if isinstance(headers, str):
                try:
                    headers = json.loads(headers)
                except json.JSONDecodeError:
                    headers = {}

            if "Content-Type" not in headers:
                headers["Content-Type"] = content_type

            request_body = None
            if body:
                if isinstance(body, (dict, list)):
                    request_body = json.dumps(body)
                else:
                    request_body = str(body)

            timeout = ClientTimeout(total=float(timeout_seconds))
            ssl_context = None if verify_ssl else False

            logger.debug(f"HTTP PATCH request to {url}")

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.patch(
                    url,
                    data=request_body,
                    headers=headers,
                    ssl=ssl_context
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
                    self.set_output_value("error", "" if success else f"HTTP {status_code}")

                    logger.info(f"HTTP PATCH {url} -> {status_code}")

                    self.status = NodeStatus.SUCCESS
                    return {
                        "success": True,
                        "data": {"status_code": status_code, "url": url},
                        "next_nodes": ["exec_out"]
                    }

        except Exception as e:
            error_msg = f"HTTP PATCH error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.set_output_value("status_code", 0)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


class HttpDeleteNode(BaseNode):
    """
    HTTP DELETE request node for deleting resources.

    Inputs:
        - exec_in: Execution input
        - url: Target URL (required)
        - headers: Request headers as dict
        - timeout: Request timeout in seconds

    Outputs:
        - exec_out: Execution output
        - response_body: Response body as string
        - status_code: HTTP status code
        - success: True if status code is 2xx
    """

    def __init__(self, node_id: str, name: str = "HTTP DELETE", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        config.setdefault("url", "")
        config.setdefault("headers", {})
        config.setdefault("timeout", 30.0)
        config.setdefault("verify_ssl", True)
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "HttpDeleteNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        self.add_input_port("url", PortType.INPUT, DataType.STRING)
        self.add_input_port("headers", PortType.INPUT, DataType.DICT)
        self.add_input_port("timeout", PortType.INPUT, DataType.FLOAT)

        self.add_output_port("response_body", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("status_code", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            url = self.get_input_value("url") or self.config.get("url", "")
            headers = self.get_input_value("headers") or self.config.get("headers", {})
            timeout_seconds = self.get_input_value("timeout") or self.config.get("timeout", 30.0)
            verify_ssl = self.config.get("verify_ssl", True)

            if not url:
                raise ValueError("URL is required")

            if isinstance(headers, str):
                try:
                    headers = json.loads(headers)
                except json.JSONDecodeError:
                    headers = {}

            timeout = ClientTimeout(total=float(timeout_seconds))
            ssl_context = None if verify_ssl else False

            logger.debug(f"HTTP DELETE request to {url}")

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.delete(
                    url,
                    headers=headers,
                    ssl=ssl_context
                ) as response:
                    response_body = await response.text()
                    status_code = response.status

                    success = 200 <= status_code < 300

                    self.set_output_value("response_body", response_body)
                    self.set_output_value("status_code", status_code)
                    self.set_output_value("success", success)
                    self.set_output_value("error", "" if success else f"HTTP {status_code}")

                    logger.info(f"HTTP DELETE {url} -> {status_code}")

                    self.status = NodeStatus.SUCCESS
                    return {
                        "success": True,
                        "data": {"status_code": status_code, "url": url},
                        "next_nodes": ["exec_out"]
                    }

        except Exception as e:
            error_msg = f"HTTP DELETE error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.set_output_value("status_code", 0)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


class SetHttpHeadersNode(BaseNode):
    """
    Configure HTTP headers for subsequent requests.

    Inputs:
        - exec_in: Execution input
        - base_headers: Existing headers to extend
        - header_name: Header name to add
        - header_value: Header value to add
        - headers_json: Headers as JSON string

    Outputs:
        - exec_out: Execution output
        - headers: Combined headers dict
    """

    def __init__(self, node_id: str, name: str = "Set HTTP Headers", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        config.setdefault("header_name", "")
        config.setdefault("header_value", "")
        config.setdefault("headers_json", "{}")
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "SetHttpHeadersNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        self.add_input_port("base_headers", PortType.INPUT, DataType.DICT)
        self.add_input_port("header_name", PortType.INPUT, DataType.STRING)
        self.add_input_port("header_value", PortType.INPUT, DataType.STRING)
        self.add_input_port("headers_json", PortType.INPUT, DataType.STRING)

        self.add_output_port("headers", PortType.OUTPUT, DataType.DICT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            base_headers = self.get_input_value("base_headers") or {}
            header_name = self.get_input_value("header_name") or self.config.get("header_name", "")
            header_value = self.get_input_value("header_value") or self.config.get("header_value", "")
            headers_json = self.get_input_value("headers_json") or self.config.get("headers_json", "{}")

            # Start with base headers
            headers = dict(base_headers)

            # Parse JSON headers
            if headers_json:
                try:
                    json_headers = json.loads(headers_json)
                    if isinstance(json_headers, dict):
                        headers.update(json_headers)
                except json.JSONDecodeError:
                    pass

            # Add single header if provided
            if header_name and header_value:
                headers[header_name] = header_value

            self.set_output_value("headers", headers)

            logger.debug(f"Set HTTP headers: {list(headers.keys())}")

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"header_count": len(headers)},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            error_msg = f"Set headers error: {str(e)}"
            logger.error(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


class HttpAuthNode(BaseNode):
    """
    Configure HTTP authentication headers.

    Supports:
        - Bearer token authentication
        - Basic authentication (username/password)
        - API Key authentication (header or query param)

    Inputs:
        - exec_in: Execution input
        - auth_type: Type of authentication (Bearer, Basic, ApiKey)
        - token: Bearer token or API key
        - username: Username for Basic auth
        - password: Password for Basic auth
        - api_key_name: Header name for API key (default: X-API-Key)
        - base_headers: Existing headers to extend

    Outputs:
        - exec_out: Execution output
        - headers: Headers with authentication
    """

    def __init__(self, node_id: str, name: str = "HTTP Auth", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        config.setdefault("auth_type", "Bearer")
        config.setdefault("token", "")
        config.setdefault("username", "")
        config.setdefault("password", "")
        config.setdefault("api_key_name", "X-API-Key")
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "HttpAuthNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        self.add_input_port("auth_type", PortType.INPUT, DataType.STRING)
        self.add_input_port("token", PortType.INPUT, DataType.STRING)
        self.add_input_port("username", PortType.INPUT, DataType.STRING)
        self.add_input_port("password", PortType.INPUT, DataType.STRING)
        self.add_input_port("api_key_name", PortType.INPUT, DataType.STRING)
        self.add_input_port("base_headers", PortType.INPUT, DataType.DICT)

        self.add_output_port("headers", PortType.OUTPUT, DataType.DICT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            auth_type = self.get_input_value("auth_type") or self.config.get("auth_type", "Bearer")
            token = self.get_input_value("token") or self.config.get("token", "")
            username = self.get_input_value("username") or self.config.get("username", "")
            password = self.get_input_value("password") or self.config.get("password", "")
            api_key_name = self.get_input_value("api_key_name") or self.config.get("api_key_name", "X-API-Key")
            base_headers = self.get_input_value("base_headers") or {}

            headers = dict(base_headers)

            if auth_type.lower() == "bearer":
                if not token:
                    raise ValueError("Bearer token is required")
                headers["Authorization"] = f"Bearer {token}"
                logger.debug("Set Bearer token authentication")

            elif auth_type.lower() == "basic":
                if not username or not password:
                    raise ValueError("Username and password are required for Basic auth")
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"
                logger.debug("Set Basic authentication")

            elif auth_type.lower() == "apikey":
                if not token:
                    raise ValueError("API key is required")
                headers[api_key_name] = token
                logger.debug(f"Set API key in header: {api_key_name}")

            else:
                raise ValueError(f"Unknown auth type: {auth_type}")

            self.set_output_value("headers", headers)

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"auth_type": auth_type},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            error_msg = f"HTTP auth error: {str(e)}"
            logger.error(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


class ParseJsonResponseNode(BaseNode):
    """
    Parse JSON response and extract data using JSONPath-like expressions.

    Inputs:
        - exec_in: Execution input
        - json_data: JSON string or dict to parse
        - path: Path to extract (e.g., "data.users[0].name" or "results.*.id")
        - default: Default value if path not found

    Outputs:
        - exec_out: Execution output
        - value: Extracted value
        - success: True if extraction succeeded
    """

    def __init__(self, node_id: str, name: str = "Parse JSON", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        config.setdefault("path", "")
        config.setdefault("default", None)
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ParseJsonResponseNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

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
            path = self.get_input_value("path") or self.config.get("path", "")
            default = self.get_input_value("default") or self.config.get("default")

            # Parse JSON if string
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
            return {
                "success": True,
                "data": {"path": path},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            error_msg = f"JSON parse error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


class HttpDownloadFileNode(BaseNode):
    """
    Download a file from a URL and save to disk.

    Inputs:
        - exec_in: Execution input
        - url: URL to download from (required)
        - save_path: Path to save file (required)
        - headers: Request headers
        - timeout: Download timeout in seconds
        - overwrite: Overwrite existing file

    Outputs:
        - exec_out: Execution output
        - file_path: Path to downloaded file
        - file_size: Size of downloaded file in bytes
        - success: True if download succeeded
    """

    def __init__(self, node_id: str, name: str = "HTTP Download File", **kwargs: Any) -> None:
        # Default config with all download options
        default_config = {
            "url": "",
            "save_path": "",
            "headers": {},
            "timeout": 300.0,  # 5 minutes for large files
            "overwrite": True,
            "verify_ssl": True,
            # Proxy settings
            "proxy": "",  # Proxy URL (e.g., http://proxy:8080)
            # Retry settings
            "retry_count": 0,  # Number of retry attempts
            "retry_delay": 2.0,  # Delay between retries
            # Download options
            "chunk_size": 8192,  # Download chunk size in bytes
            "resume": False,  # Resume partial downloads if supported
        }

        config = kwargs.get("config", {})
        # Merge with defaults
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        super().__init__(node_id, config)
        self.name = name
        self.node_type = "HttpDownloadFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

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
            url = self.get_input_value("url") or self.config.get("url", "")
            save_path = self.get_input_value("save_path") or self.config.get("save_path", "")
            headers = self.get_input_value("headers") or self.config.get("headers", {})
            timeout_seconds = self.get_input_value("timeout") or self.config.get("timeout", 300.0)
            overwrite = self.config.get("overwrite", True)
            verify_ssl = self.config.get("verify_ssl", True)
            proxy = self.config.get("proxy", "")
            retry_count = self.config.get("retry_count", 0)
            retry_delay = self.config.get("retry_delay", 2.0)
            chunk_size = self.config.get("chunk_size", 8192)

            if not url:
                raise ValueError("URL is required")
            if not save_path:
                raise ValueError("Save path is required")

            save_path = Path(save_path)

            # Check if file exists
            if save_path.exists() and not overwrite:
                raise FileExistsError(f"File already exists: {save_path}")

            # Create parent directory if needed
            save_path.parent.mkdir(parents=True, exist_ok=True)

            if isinstance(headers, str):
                try:
                    headers = json.loads(headers)
                except json.JSONDecodeError:
                    headers = {}

            timeout = ClientTimeout(total=float(timeout_seconds))
            ssl_context = None if verify_ssl else False

            logger.info(f"Downloading file from {url}")

            # Retry loop
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

                            # Download and write file
                            with open(save_path, 'wb') as f:
                                async for chunk in response.content.iter_chunked(chunk_size):
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
                                    "attempts": attempt + 1
                                },
                                "next_nodes": ["exec_out"]
                            }

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt < retry_count:
                        logger.warning(f"Download failed (attempt {attempt + 1}/{retry_count + 1}): {e}")
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


class HttpUploadFileNode(BaseNode):
    """
    Upload a file via HTTP POST multipart/form-data.

    Inputs:
        - exec_in: Execution input
        - url: Upload URL (required)
        - file_path: Path to file to upload (required)
        - field_name: Form field name for file (default: "file")
        - headers: Additional headers
        - extra_fields: Extra form fields as dict
        - timeout: Upload timeout in seconds

    Outputs:
        - exec_out: Execution output
        - response_body: Response body
        - response_json: Parsed JSON response
        - status_code: HTTP status code
        - success: True if upload succeeded
    """

    def __init__(self, node_id: str, name: str = "HTTP Upload File", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        config.setdefault("url", "")
        config.setdefault("file_path", "")
        config.setdefault("field_name", "file")
        config.setdefault("headers", {})
        config.setdefault("extra_fields", {})
        config.setdefault("timeout", 300.0)
        config.setdefault("verify_ssl", True)
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "HttpUploadFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

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
            url = self.get_input_value("url") or self.config.get("url", "")
            file_path = self.get_input_value("file_path") or self.config.get("file_path", "")
            field_name = self.get_input_value("field_name") or self.config.get("field_name", "file")
            headers = self.get_input_value("headers") or self.config.get("headers", {})
            extra_fields = self.get_input_value("extra_fields") or self.config.get("extra_fields", {})
            timeout_seconds = self.get_input_value("timeout") or self.config.get("timeout", 300.0)
            verify_ssl = self.config.get("verify_ssl", True)

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

            # Create form data
            data = FormData()

            # Add file
            data.add_field(
                field_name,
                open(file_path, 'rb'),
                filename=file_path.name
            )

            # Add extra fields
            for key, value in extra_fields.items():
                data.add_field(key, str(value))

            logger.info(f"Uploading file {file_path} to {url}")

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    url,
                    data=data,
                    headers=headers,
                    ssl=ssl_context
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
                    self.set_output_value("error", "" if success else f"HTTP {status_code}")

                    logger.info(f"Upload completed: HTTP {status_code}")

                    self.status = NodeStatus.SUCCESS
                    return {
                        "success": True,
                        "data": {"status_code": status_code, "file": str(file_path)},
                        "next_nodes": ["exec_out"]
                    }

        except Exception as e:
            error_msg = f"Upload error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.set_output_value("status_code", 0)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


class BuildUrlNode(BaseNode):
    """
    Build a URL with query parameters.

    Inputs:
        - exec_in: Execution input
        - base_url: Base URL
        - path: Path to append
        - params: Query parameters as dict

    Outputs:
        - exec_out: Execution output
        - url: Complete URL with parameters
    """

    def __init__(self, node_id: str, name: str = "Build URL", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        config.setdefault("base_url", "")
        config.setdefault("path", "")
        config.setdefault("params", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "BuildUrlNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        self.add_input_port("base_url", PortType.INPUT, DataType.STRING)
        self.add_input_port("path", PortType.INPUT, DataType.STRING)
        self.add_input_port("params", PortType.INPUT, DataType.DICT)

        self.add_output_port("url", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            base_url = self.get_input_value("base_url") or self.config.get("base_url", "")
            path = self.get_input_value("path") or self.config.get("path", "")
            params = self.get_input_value("params") or self.config.get("params", {})

            if not base_url:
                raise ValueError("Base URL is required")

            if isinstance(params, str):
                try:
                    params = json.loads(params)
                except json.JSONDecodeError:
                    params = {}

            # Build URL
            url = base_url
            if path:
                url = urljoin(base_url.rstrip('/') + '/', path.lstrip('/'))

            # Add query parameters
            if params:
                query_string = urlencode(params)
                separator = '&' if '?' in url else '?'
                url = f"{url}{separator}{query_string}"

            self.set_output_value("url", url)

            logger.debug(f"Built URL: {url}")

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "data": {"url": url},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            error_msg = f"Build URL error: {str(e)}"
            logger.error(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


# Export all node classes
__all__ = [
    "HttpRequestNode",
    "HttpGetNode",
    "HttpPostNode",
    "HttpPutNode",
    "HttpPatchNode",
    "HttpDeleteNode",
    "SetHttpHeadersNode",
    "HttpAuthNode",
    "ParseJsonResponseNode",
    "HttpDownloadFileNode",
    "HttpUploadFileNode",
    "BuildUrlNode",
]
