"""
Basic HTTP request nodes for CasareRPA.

This module provides nodes for making standard HTTP requests:
- HttpRequestNode: Generic HTTP request (all methods)
- HttpGetNode: GET request with query parameters
- HttpPostNode: POST request with body
- HttpPutNode: PUT request for updating resources
- HttpPatchNode: PATCH request for partial updates
- HttpDeleteNode: DELETE request for deleting resources
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import aiohttp
from aiohttp import ClientTimeout
from loguru import logger

from ...core.base_node import BaseNode
from ...core.execution_context import ExecutionContext
from ...core.types import DataType, ExecutionResult, NodeStatus, PortType


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
        default_config = {
            "method": "GET",
            "url": "",
            "headers": {},
            "body": "",
            "params": {},
            "timeout": 30.0,
            "verify_ssl": True,
            "follow_redirects": True,
            "max_redirects": 10,
            "content_type": "application/json",
            "proxy": "",
            "retry_count": 0,
            "retry_delay": 1.0,
            "response_encoding": "",
        }

        config = kwargs.get("config", {})
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        super().__init__(node_id, config)
        self.name = name
        self.node_type = "HttpRequestNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)

        self.add_input_port("url", PortType.INPUT, DataType.STRING)
        self.add_input_port("method", PortType.INPUT, DataType.STRING)
        self.add_input_port("headers", PortType.INPUT, DataType.DICT)
        self.add_input_port("body", PortType.INPUT, DataType.ANY)
        self.add_input_port("params", PortType.INPUT, DataType.DICT)
        self.add_input_port("timeout", PortType.INPUT, DataType.FLOAT)

        self.add_output_port("response_body", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("response_json", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("status_code", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("response_headers", PortType.OUTPUT, DataType.DICT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            url = self.get_input_value("url") or self.config.get("url", "")
            method = (
                self.get_input_value("method") or self.config.get("method", "GET")
            ).upper()
            headers = self.get_input_value("headers") or self.config.get("headers", {})
            body = self.get_input_value("body") or self.config.get("body", "")
            params = self.get_input_value("params") or self.config.get("params", {})
            timeout_seconds = self.get_input_value("timeout") or self.config.get(
                "timeout", 30.0
            )
            verify_ssl = self.config.get("verify_ssl", True)
            follow_redirects = self.config.get("follow_redirects", True)
            max_redirects = self.config.get("max_redirects", 10)
            content_type = self.config.get("content_type", "application/json")
            proxy = self.config.get("proxy", "")
            retry_count = self.config.get("retry_count", 0)
            retry_delay = self.config.get("retry_delay", 1.0)
            response_encoding = self.config.get("response_encoding", "")

            url = context.resolve_value(url)
            if isinstance(body, str):
                body = context.resolve_value(body)

            if not url:
                raise ValueError("URL is required")

            if isinstance(headers, str):
                try:
                    headers = json.loads(headers)
                except json.JSONDecodeError:
                    headers = {}

            if content_type and "Content-Type" not in headers:
                headers["Content-Type"] = content_type

            request_body = None
            if body and method in ["POST", "PUT", "PATCH"]:
                if isinstance(body, (dict, list)):
                    request_body = json.dumps(body)
                else:
                    request_body = str(body)

            timeout = ClientTimeout(total=float(timeout_seconds))
            ssl_context = None if verify_ssl else False

            if proxy:
                logger.debug(f"Using proxy: {proxy}")

            logger.debug(f"HTTP {method} request to {url}")

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
                            if response_encoding:
                                response_body = await response.text(
                                    encoding=response_encoding
                                )
                            else:
                                response_body = await response.text()
                            status_code = response.status
                            response_headers = dict(response.headers)

                            response_json = None
                            try:
                                response_json = json.loads(response_body)
                            except (json.JSONDecodeError, ValueError):
                                pass

                            success = 200 <= status_code < 300

                            self.set_output_value("response_body", response_body)
                            self.set_output_value("response_json", response_json)
                            self.set_output_value("status_code", status_code)
                            self.set_output_value("response_headers", response_headers)
                            self.set_output_value("success", success)
                            self.set_output_value(
                                "error", "" if success else f"HTTP {status_code}"
                            )

                            logger.info(f"HTTP {method} {url} -> {status_code}")

                            self.status = NodeStatus.SUCCESS
                            return {
                                "success": True,
                                "data": {
                                    "status_code": status_code,
                                    "url": url,
                                    "method": method,
                                    "attempts": attempt + 1,
                                },
                                "next_nodes": ["exec_out"],
                            }

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    last_error = e
                    if attempt < retry_count:
                        logger.warning(
                            f"HTTP request failed (attempt {attempt + 1}/{retry_count + 1}): {e}"
                        )
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
        default_config = {
            "url": "",
            "params": {},
            "headers": {},
            "timeout": 30.0,
            "verify_ssl": True,
            "retry_count": 0,
            "retry_delay": 1.0,
        }

        config = kwargs.get("config", {})
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

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
            timeout_seconds = self.get_input_value("timeout") or self.config.get(
                "timeout", 30.0
            )
            verify_ssl = self.config.get("verify_ssl", True)
            retry_count = self.config.get("retry_count", 0)
            retry_delay = self.config.get("retry_delay", 1.0)

            url = context.resolve_value(url)

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

            for attempt in range(max(1, retry_count + 1)):
                try:
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get(
                            url, params=params, headers=headers, ssl=ssl_context
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
                                f"HTTP GET {url} -> {status_code} (attempt {attempt + 1})"
                            )

                            self.status = NodeStatus.SUCCESS
                            return {
                                "success": True,
                                "data": {
                                    "status_code": status_code,
                                    "url": url,
                                    "attempts": attempt + 1,
                                },
                                "next_nodes": ["exec_out"],
                            }

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt < retry_count:
                        logger.warning(
                            f"HTTP GET failed (attempt {attempt + 1}/{retry_count + 1}): {e}"
                        )
                        await asyncio.sleep(retry_delay)
                    else:
                        raise

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
        default_config = {
            "url": "",
            "body": "",
            "headers": {},
            "content_type": "application/json",
            "timeout": 30.0,
            "verify_ssl": True,
            "retry_count": 0,
            "retry_delay": 1.0,
        }

        config = kwargs.get("config", {})
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

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
            timeout_seconds = self.get_input_value("timeout") or self.config.get(
                "timeout", 30.0
            )
            verify_ssl = self.config.get("verify_ssl", True)
            retry_count = self.config.get("retry_count", 0)
            retry_delay = self.config.get("retry_delay", 1.0)

            url = context.resolve_value(url)
            if isinstance(body, str):
                body = context.resolve_value(body)

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

            logger.debug(f"HTTP POST request to {url}")

            for attempt in range(max(1, retry_count + 1)):
                try:
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.post(
                            url, data=request_body, headers=headers, ssl=ssl_context
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
                                f"HTTP POST {url} -> {status_code} (attempt {attempt + 1})"
                            )

                            self.status = NodeStatus.SUCCESS
                            return {
                                "success": True,
                                "data": {
                                    "status_code": status_code,
                                    "url": url,
                                    "attempts": attempt + 1,
                                },
                                "next_nodes": ["exec_out"],
                            }

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt < retry_count:
                        logger.warning(
                            f"HTTP POST failed (attempt {attempt + 1}/{retry_count + 1}): {e}"
                        )
                        await asyncio.sleep(retry_delay)
                    else:
                        raise

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
        default_config = {
            "url": "",
            "body": "",
            "headers": {},
            "content_type": "application/json",
            "timeout": 30.0,
            "verify_ssl": True,
            "retry_count": 0,
            "retry_delay": 1.0,
        }

        config = kwargs.get("config", {})
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

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
            timeout_seconds = self.get_input_value("timeout") or self.config.get(
                "timeout", 30.0
            )
            verify_ssl = self.config.get("verify_ssl", True)
            retry_count = self.config.get("retry_count", 0)
            retry_delay = self.config.get("retry_delay", 1.0)

            url = context.resolve_value(url)
            if isinstance(body, str):
                body = context.resolve_value(body)

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

            for attempt in range(max(1, retry_count + 1)):
                try:
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.put(
                            url, data=request_body, headers=headers, ssl=ssl_context
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
                                f"HTTP PUT {url} -> {status_code} (attempt {attempt + 1})"
                            )

                            self.status = NodeStatus.SUCCESS
                            return {
                                "success": True,
                                "data": {
                                    "status_code": status_code,
                                    "url": url,
                                    "attempts": attempt + 1,
                                },
                                "next_nodes": ["exec_out"],
                            }

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt < retry_count:
                        logger.warning(
                            f"HTTP PUT failed (attempt {attempt + 1}/{retry_count + 1}): {e}"
                        )
                        await asyncio.sleep(retry_delay)
                    else:
                        raise

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
        default_config = {
            "url": "",
            "body": "",
            "headers": {},
            "content_type": "application/json",
            "timeout": 30.0,
            "verify_ssl": True,
            "retry_count": 0,
            "retry_delay": 1.0,
        }

        config = kwargs.get("config", {})
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

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
            timeout_seconds = self.get_input_value("timeout") or self.config.get(
                "timeout", 30.0
            )
            verify_ssl = self.config.get("verify_ssl", True)
            retry_count = self.config.get("retry_count", 0)
            retry_delay = self.config.get("retry_delay", 1.0)

            url = context.resolve_value(url)
            if isinstance(body, str):
                body = context.resolve_value(body)

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

            for attempt in range(max(1, retry_count + 1)):
                try:
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.patch(
                            url, data=request_body, headers=headers, ssl=ssl_context
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
                                f"HTTP PATCH {url} -> {status_code} (attempt {attempt + 1})"
                            )

                            self.status = NodeStatus.SUCCESS
                            return {
                                "success": True,
                                "data": {
                                    "status_code": status_code,
                                    "url": url,
                                    "attempts": attempt + 1,
                                },
                                "next_nodes": ["exec_out"],
                            }

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt < retry_count:
                        logger.warning(
                            f"HTTP PATCH failed (attempt {attempt + 1}/{retry_count + 1}): {e}"
                        )
                        await asyncio.sleep(retry_delay)
                    else:
                        raise

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
        default_config = {
            "url": "",
            "headers": {},
            "timeout": 30.0,
            "verify_ssl": True,
            "retry_count": 0,
            "retry_delay": 1.0,
        }

        config = kwargs.get("config", {})
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

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
            timeout_seconds = self.get_input_value("timeout") or self.config.get(
                "timeout", 30.0
            )
            verify_ssl = self.config.get("verify_ssl", True)
            retry_count = self.config.get("retry_count", 0)
            retry_delay = self.config.get("retry_delay", 1.0)

            url = context.resolve_value(url)

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

            for attempt in range(max(1, retry_count + 1)):
                try:
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.delete(
                            url, headers=headers, ssl=ssl_context
                        ) as response:
                            response_body = await response.text()
                            status_code = response.status

                            success = 200 <= status_code < 300

                            self.set_output_value("response_body", response_body)
                            self.set_output_value("status_code", status_code)
                            self.set_output_value("success", success)
                            self.set_output_value(
                                "error", "" if success else f"HTTP {status_code}"
                            )

                            logger.info(
                                f"HTTP DELETE {url} -> {status_code} (attempt {attempt + 1})"
                            )

                            self.status = NodeStatus.SUCCESS
                            return {
                                "success": True,
                                "data": {
                                    "status_code": status_code,
                                    "url": url,
                                    "attempts": attempt + 1,
                                },
                                "next_nodes": ["exec_out"],
                            }

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt < retry_count:
                        logger.warning(
                            f"HTTP DELETE failed (attempt {attempt + 1}/{retry_count + 1}): {e}"
                        )
                        await asyncio.sleep(retry_delay)
                    else:
                        raise

        except Exception as e:
            error_msg = f"HTTP DELETE error: {str(e)}"
            logger.error(error_msg)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.set_output_value("status_code", 0)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


__all__ = [
    "HttpRequestNode",
    "HttpGetNode",
    "HttpPostNode",
    "HttpPutNode",
    "HttpPatchNode",
    "HttpDeleteNode",
]
