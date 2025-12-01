"""
Base HTTP node providing common functionality for all HTTP nodes.

This module extracts shared HTTP request logic to reduce code duplication
across HttpGetNode, HttpPostNode, HttpPutNode, HttpPatchNode, HttpDeleteNode.
"""

from __future__ import annotations

import asyncio
import json
from abc import abstractmethod
from typing import Any, Dict, Optional

import aiohttp
from aiohttp import ClientTimeout
from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
    PortType,
)
from casare_rpa.infrastructure.execution import ExecutionContext


class HttpBaseNode(BaseNode):
    """
    Abstract base class for HTTP request nodes.

    Provides common functionality:
    - Parameter parsing and validation
    - Header/body JSON handling
    - Retry logic with exponential backoff
    - Response processing and output setting
    - Error handling and logging

    Subclasses only need to:
    1. Define their specific ports via _define_ports()
    2. Override _get_http_method() to return the HTTP method
    3. Optionally override _has_request_body() for methods that send bodies
    """

    # Subclasses can override these defaults
    DEFAULT_TIMEOUT: float = 30.0
    DEFAULT_CONTENT_TYPE: str = "application/json"

    def __init__(self, node_id: str, name: str = "HTTP Request", **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name

    @abstractmethod
    def _get_http_method(self) -> str:
        """Return the HTTP method for this node (GET, POST, PUT, PATCH, DELETE)."""
        ...

    def _has_request_body(self) -> bool:
        """Return True if this HTTP method typically has a request body."""
        return self._get_http_method() in ("POST", "PUT", "PATCH")

    def _define_common_output_ports(self) -> None:
        """Define standard output ports for HTTP response."""
        self.add_output_port("response_body", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("response_json", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("status_code", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("response_headers", PortType.OUTPUT, DataType.DICT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    def _define_common_input_ports(self, include_body: bool = False) -> None:
        """Define standard input ports for HTTP request."""
        self.add_input_port("url", PortType.INPUT, DataType.STRING)
        self.add_input_port("headers", PortType.INPUT, DataType.DICT)
        self.add_input_port("timeout", PortType.INPUT, DataType.FLOAT)
        if include_body:
            self.add_input_port("body", PortType.INPUT, DataType.ANY)

    def _parse_json_param(self, value: Any, default: Any = None) -> Any:
        """Parse a parameter that may be JSON string or already parsed."""
        if value is None:
            return default if default is not None else {}
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return default if default is not None else {}
        return value

    def _prepare_request_body(self, body: Any) -> Optional[str]:
        """Serialize request body to string if needed."""
        if not body:
            return None
        if isinstance(body, (dict, list)):
            return json.dumps(body)
        return str(body)

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
        response_headers: Dict[str, str],
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
        session: aiohttp.ClientSession,
        url: str,
        method: str,
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
        data: Optional[str] = None,
        ssl_context: Any = None,
        follow_redirects: bool = True,
        max_redirects: int = 10,
        proxy: Optional[str] = None,
        response_encoding: Optional[str] = None,
    ) -> tuple[str, int, Dict[str, str]]:
        """Execute HTTP request and return response tuple."""
        request_kwargs: Dict[str, Any] = {
            "method": method,
            "url": url,
            "headers": headers,
            "ssl": ssl_context,
            "allow_redirects": follow_redirects,
            "max_redirects": max_redirects,
        }

        if params:
            request_kwargs["params"] = params
        if data:
            request_kwargs["data"] = data
        if proxy:
            request_kwargs["proxy"] = proxy

        async with session.request(**request_kwargs) as response:
            if response_encoding:
                response_body = await response.text(encoding=response_encoding)
            else:
                response_body = await response.text()

            return response_body, response.status, dict(response.headers)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute HTTP request with retry logic."""
        self.status = NodeStatus.RUNNING
        method = self._get_http_method()

        try:
            # Get common parameters
            url = self.get_parameter("url")
            headers = self.get_parameter("headers", {})
            timeout_seconds = self.get_parameter("timeout", self.DEFAULT_TIMEOUT)
            verify_ssl = self.get_parameter("verify_ssl", True)
            retry_count = self.get_parameter("retry_count", 0)
            retry_delay = self.get_parameter("retry_delay", 1.0)

            # Resolve URL from context
            url = context.resolve_value(url)
            if not url:
                raise ValueError("URL is required")

            # Parse headers
            headers = self._parse_json_param(headers, {})

            # Handle body for POST/PUT/PATCH
            request_body = None
            if self._has_request_body():
                body = self.get_parameter("body", "")
                if isinstance(body, str):
                    body = context.resolve_value(body)

                content_type = self.get_parameter(
                    "content_type", self.DEFAULT_CONTENT_TYPE
                )
                if content_type and "Content-Type" not in headers:
                    headers["Content-Type"] = content_type

                request_body = self._prepare_request_body(body)

            # Handle query params for GET
            params = None
            if method == "GET":
                params = self.get_parameter("params", {})
                params = self._parse_json_param(params, {})

            # Optional advanced parameters
            follow_redirects = self.get_parameter("follow_redirects", True)
            max_redirects = self.get_parameter("max_redirects", 10)
            proxy = self.get_parameter("proxy", "")
            response_encoding = self.get_parameter("response_encoding", "")

            # Prepare request config
            timeout = ClientTimeout(total=float(timeout_seconds))
            ssl_context = None if verify_ssl else False

            if proxy:
                logger.debug(f"Using proxy: {proxy}")

            logger.debug(f"HTTP {method} request to {url}")

            # Retry loop
            last_error: Optional[Exception] = None
            for attempt in range(max(1, retry_count + 1)):
                try:
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        (
                            response_body,
                            status_code,
                            response_headers,
                        ) = await self._make_request(
                            session=session,
                            url=url,
                            method=method,
                            headers=headers,
                            params=params,
                            data=request_body,
                            ssl_context=ssl_context,
                            follow_redirects=follow_redirects,
                            max_redirects=max_redirects,
                            proxy=proxy if proxy else None,
                            response_encoding=response_encoding
                            if response_encoding
                            else None,
                        )

                        self._set_success_outputs(
                            response_body, status_code, response_headers
                        )

                        logger.info(
                            f"HTTP {method} {url} -> {status_code} (attempt {attempt + 1})"
                        )

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
                            f"HTTP {method} failed (attempt {attempt + 1}/{retry_count + 1}): {e}"
                        )
                        await asyncio.sleep(retry_delay)
                    else:
                        raise

            # Should not reach here, but handle just in case
            if last_error:
                raise last_error

        except aiohttp.ClientError as e:
            error_msg = f"HTTP {method} request failed: {str(e)}"
            logger.error(error_msg)
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

        except asyncio.TimeoutError:
            error_msg = f"Request timed out after {self.get_parameter('timeout', self.DEFAULT_TIMEOUT)} seconds"
            logger.error(error_msg)
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

        except ValueError as e:
            error_msg = str(e)
            logger.error(f"HTTP {method} validation error: {error_msg}")
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

        except Exception as e:
            error_msg = f"HTTP {method} error: {str(e)}"
            logger.error(error_msg)
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

        # Fallback (should never reach)
        return {"success": False, "error": "Unknown error", "next_nodes": []}


__all__ = ["HttpBaseNode"]
