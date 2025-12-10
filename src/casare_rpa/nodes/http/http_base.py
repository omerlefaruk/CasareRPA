"""
Base HTTP node providing common functionality for all HTTP nodes.

This module provides the HttpBaseNode abstract class with shared HTTP request logic.
HttpRequestNode extends this to support all HTTP methods via a dropdown selector.

Uses a shared aiohttp.ClientSession for connection pooling across requests.
"""

from __future__ import annotations

import asyncio
import ipaddress
import json
import socket
from abc import abstractmethod
from typing import Any, Dict, Optional, Set
from urllib.parse import urlparse

import aiohttp
from aiohttp import ClientTimeout, TCPConnector
from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
    PortType,
)
from casare_rpa.infrastructure.execution import ExecutionContext


# SSRF Protection: Blocked hosts and schemes
_BLOCKED_HOSTS: Set[str] = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "[::]",
    "[::1]",
}

_BLOCKED_SCHEMES: Set[str] = {
    "file",
    "ftp",
    "gopher",
    "data",
    "javascript",
}


def _is_private_ip(ip_str: str) -> bool:
    """Check if an IP address is in a private range."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local
    except ValueError:
        return False


def validate_url_for_ssrf(
    url: str,
    allow_internal: bool = False,
    allow_private_ips: bool = False,
) -> str:
    """
    Validate a URL to prevent Server-Side Request Forgery (SSRF) attacks.

    Args:
        url: The URL to validate
        allow_internal: If True, allow requests to localhost and internal hosts
        allow_private_ips: If True, allow requests to private IP ranges (10.x, 192.168.x, etc.)

    Returns:
        The validated URL

    Raises:
        ValueError: If the URL is invalid or targets a blocked host/scheme
    """
    if not url:
        raise ValueError("URL is required")

    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValueError(f"Invalid URL format: {e}")

    # Check scheme
    scheme = (parsed.scheme or "").lower()
    if not scheme:
        raise ValueError("URL must have a scheme (http or https)")

    if scheme in _BLOCKED_SCHEMES:
        raise ValueError(f"URL scheme '{scheme}' is not allowed")

    if scheme not in ("http", "https"):
        raise ValueError(f"Only http and https schemes are allowed, got '{scheme}'")

    # Check hostname
    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise ValueError("URL must have a hostname")

    # Check for blocked hosts (unless internal access allowed)
    if not allow_internal:
        if hostname in _BLOCKED_HOSTS:
            raise ValueError(
                f"Requests to '{hostname}' are not allowed for security reasons. "
                "Set allow_internal=True if you need to access internal services."
            )

        # Check if hostname resolves to a blocked IP
        try:
            # Resolve hostname to check for private IPs
            ip_str = socket.gethostbyname(hostname)
            if not allow_private_ips and _is_private_ip(ip_str):
                raise ValueError(
                    f"URL hostname '{hostname}' resolves to private IP '{ip_str}'. "
                    "Private IP addresses are not allowed for security reasons."
                )
        except socket.gaierror:
            # DNS resolution failed - let the request fail naturally later
            pass

    return url


# =============================================================================
# Shared HTTP Session for Connection Pooling
# =============================================================================

_shared_session: Optional[aiohttp.ClientSession] = None
_session_lock = asyncio.Lock()


async def get_shared_http_session() -> aiohttp.ClientSession:
    """
    Get a shared HTTP session for connection pooling.

    This session is reused across all HTTP requests to avoid creating
    new TCP connections and SSL handshakes for each request.
    Per-request configuration (timeout, ssl, proxy) is passed to each request.
    """
    global _shared_session

    if _shared_session is None or _shared_session.closed:
        async with _session_lock:
            if _shared_session is None or _shared_session.closed:
                # Create connector with connection pooling
                connector = TCPConnector(
                    limit=100,  # Total concurrent connections
                    limit_per_host=10,  # Connections per host
                    keepalive_timeout=30,  # Keep connections alive
                    enable_cleanup_closed=True,
                )
                _shared_session = aiohttp.ClientSession(connector=connector)
                logger.debug("Created shared HTTP session for connection pooling")

    return _shared_session


async def close_shared_http_session() -> None:
    """Close the shared HTTP session (call on application shutdown)."""
    global _shared_session
    if _shared_session and not _shared_session.closed:
        await _shared_session.close()
        _shared_session = None
        logger.debug("Closed shared HTTP session")


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

    # @category: http
    # @requires: requests
    # @ports: none -> none

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
        timeout: Optional[ClientTimeout] = None,
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
        if timeout:
            request_kwargs["timeout"] = timeout

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

            # SSRF protection: validate URL before making request
            allow_internal = self.get_parameter("allow_internal_urls", False)
            url = validate_url_for_ssrf(
                url,
                allow_internal=allow_internal,
                allow_private_ips=allow_internal,
            )

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

            # Get shared session for connection pooling
            session = await get_shared_http_session()

            # Retry loop
            last_error: Optional[Exception] = None
            for attempt in range(max(1, retry_count + 1)):
                try:
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
                        timeout=timeout,
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


__all__ = [
    "HttpBaseNode",
    "validate_url_for_ssrf",
    "get_shared_http_session",
    "close_shared_http_session",
]
