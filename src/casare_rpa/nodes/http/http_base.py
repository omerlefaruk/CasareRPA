"""
Base HTTP node providing common functionality for all HTTP nodes.

This module provides the HttpBaseNode abstract class with shared HTTP request logic.
HttpRequestNode extends this to support all HTTP methods via a dropdown selector.

PERFORMANCE: Uses UnifiedHttpClient for:
- Connection pooling via HttpSessionPool
- Per-domain rate limiting via SlidingWindowRateLimiter
- Circuit breaker for failure isolation
- Exponential backoff retry logic
- SSRF protection
"""

from __future__ import annotations
from casare_rpa.domain.decorators import node, properties


import asyncio
import json
from abc import abstractmethod
from typing import Any, Dict, Optional, TYPE_CHECKING

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)

if TYPE_CHECKING:
    from casare_rpa.infrastructure.execution import ExecutionContext
    from casare_rpa.infrastructure.http.unified_http_client import UnifiedHttpClient


# Resource key for storing UnifiedHttpClient in ExecutionContext
HTTP_CLIENT_RESOURCE_KEY = "_unified_http_client"


async def get_http_client_from_context(
    context: "ExecutionContext",
) -> "UnifiedHttpClient":
    """
    Get or create UnifiedHttpClient from ExecutionContext resources.

    The client is stored in context.resources for reuse across all HTTP nodes
    in the workflow execution. This ensures:
    - Connection reuse via keep-alive
    - Shared rate limiting state per domain
    - Shared circuit breaker state per base URL
    - Proper cleanup at workflow end

    Args:
        context: ExecutionContext for the workflow

    Returns:
        UnifiedHttpClient instance (shared across all HTTP nodes)
    """
    from casare_rpa.infrastructure.http.unified_http_client import UnifiedHttpClient

    if HTTP_CLIENT_RESOURCE_KEY not in context.resources:
        client = UnifiedHttpClient()
        await client.start()
        context.resources[HTTP_CLIENT_RESOURCE_KEY] = client
        logger.debug("Created UnifiedHttpClient for workflow execution")

    return context.resources[HTTP_CLIENT_RESOURCE_KEY]


async def close_http_client_from_context(context: "ExecutionContext") -> None:
    """
    Close UnifiedHttpClient stored in ExecutionContext.

    Called automatically during ExecutionContext.cleanup().

    Args:
        context: ExecutionContext for the workflow
    """
    if HTTP_CLIENT_RESOURCE_KEY in context.resources:
        client = context.resources[HTTP_CLIENT_RESOURCE_KEY]
        if client is not None:
            await client.close()
            logger.debug("Closed UnifiedHttpClient for workflow execution")
        del context.resources[HTTP_CLIENT_RESOURCE_KEY]


# =============================================================================
# Legacy functions for backward compatibility
# =============================================================================


# DEPRECATED: Use get_http_client_from_context instead
async def get_shared_http_session():
    """
    DEPRECATED: Use get_http_client_from_context(context) instead.

    This function is kept for backward compatibility but creates a new
    UnifiedHttpClient that is NOT managed by ExecutionContext cleanup.
    """
    import warnings

    warnings.warn(
        "get_shared_http_session() is deprecated. Use get_http_client_from_context(context) "
        "for proper resource management and pooling benefits.",
        DeprecationWarning,
        stacklevel=2,
    )
    from casare_rpa.infrastructure.http.unified_http_client import (
        get_unified_http_client,
    )

    return await get_unified_http_client()


async def close_shared_http_session() -> None:
    """
    DEPRECATED: Cleanup is now handled automatically by ExecutionContext.

    This function is kept for backward compatibility.
    """
    import warnings

    warnings.warn(
        "close_shared_http_session() is deprecated. HTTP client cleanup is now "
        "handled automatically by ExecutionContext.",
        DeprecationWarning,
        stacklevel=2,
    )
    from casare_rpa.infrastructure.http.unified_http_client import (
        close_unified_http_client,
    )

    await close_unified_http_client()


@properties()
@node(category="http")
class HttpBaseNode(BaseNode):
    """
    Abstract base class for HTTP request nodes.

    PERFORMANCE: Uses UnifiedHttpClient which provides:
    - Connection pooling via HttpSessionPool (keep-alive, reuse)
    - Per-domain rate limiting via SlidingWindowRateLimiter
    - Circuit breaker for failure isolation (per base URL)
    - Exponential backoff retry with jitter
    - SSRF protection (blocks internal IPs, validates schemes)

    Provides common functionality:
    - Parameter parsing and validation
    - Header/body JSON handling
    - Response processing and output setting
    - Error handling and logging

    Subclasses only need to:
    1. Define their specific ports via _define_ports()
    2. Override _get_http_method() to return the HTTP method
    3. Optionally override _has_request_body() for methods that send bodies
    """

    # @category: http
    # @requires: aiohttp
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
        self.add_output_port("response_body", DataType.STRING)
        self.add_output_port("response_json", DataType.ANY)
        self.add_output_port("status_code", DataType.INTEGER)
        self.add_output_port("response_headers", DataType.DICT)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    def _define_common_input_ports(self, include_body: bool = False) -> None:
        """Define standard input ports for HTTP request."""
        self.add_input_port("url", DataType.STRING)
        self.add_input_port("headers", DataType.DICT)
        self.add_input_port("timeout", DataType.FLOAT)
        if include_body:
            self.add_input_port("body", DataType.ANY)

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

    def _prepare_request_body(self, body: Any) -> Optional[Any]:
        """Prepare request body - return dict for JSON, string otherwise."""
        if not body:
            return None
        if isinstance(body, (dict, list)):
            return body  # UnifiedHttpClient handles JSON serialization
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

    async def execute(self, context: "ExecutionContext") -> ExecutionResult:
        """
        Execute HTTP request using UnifiedHttpClient.

        Benefits over raw aiohttp:
        - Connection pooling (keep-alive, connection reuse)
        - Rate limiting per domain (prevents overwhelming servers)
        - Circuit breaker per base URL (fails fast when server is down)
        - Exponential backoff retry with jitter (built into client)
        - SSRF protection (built into client)
        """
        self.status = NodeStatus.RUNNING
        method = self._get_http_method()

        try:
            # Get common parameters
            url = self.get_parameter("url")
            headers = self.get_parameter("headers", {})
            timeout_seconds = self.get_parameter("timeout", self.DEFAULT_TIMEOUT)
            retry_count = self.get_parameter("retry_count", 0)

            # Resolve URL from context
            url = context.resolve_value(url)
            if not url:
                raise ValueError("URL is required")

            # Parse headers
            headers = self._parse_json_param(headers, {})

            # Handle body for POST/PUT/PATCH
            request_body = None
            request_json = None
            if self._has_request_body():
                body = self.get_parameter("body", "")
                if isinstance(body, str):
                    body = context.resolve_value(body)

                content_type = self.get_parameter(
                    "content_type", self.DEFAULT_CONTENT_TYPE
                )

                prepared_body = self._prepare_request_body(body)

                # If body is dict/list and content-type is JSON, use json parameter
                if isinstance(prepared_body, (dict, list)):
                    request_json = prepared_body
                else:
                    request_body = prepared_body
                    if content_type and "Content-Type" not in headers:
                        headers["Content-Type"] = content_type

            logger.debug(f"HTTP {method} request to {url}")

            # Get UnifiedHttpClient from context (pooled, rate-limited, circuit-breaker)
            client = await get_http_client_from_context(context)

            # Make request through UnifiedHttpClient
            # Note: UnifiedHttpClient handles:
            # - SSRF protection (validates URL internally)
            # - Rate limiting (per domain)
            # - Circuit breaker (per base URL)
            # - Retry with exponential backoff (configurable)
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers if headers else None,
                    json=request_json,
                    data=request_body,
                    timeout=float(timeout_seconds),
                    retry_count=max(
                        1, retry_count + 1
                    ),  # UnifiedHttpClient uses attempts
                )

                # Read response
                response_body = await response.text()
                status_code = response.status
                response_headers = dict(response.headers)

                # Release response
                await response.release()

                self._set_success_outputs(response_body, status_code, response_headers)

                logger.info(f"HTTP {method} {url} -> {status_code}")

                self.status = NodeStatus.SUCCESS
                return {
                    "success": True,
                    "data": {
                        "status_code": status_code,
                        "url": url,
                        "method": method,
                    },
                    "next_nodes": ["exec_out"],
                }

            except Exception as e:
                # Handle specific error types from UnifiedHttpClient
                error_type = type(e).__name__

                # Check for circuit breaker open
                if "CircuitBreakerOpen" in error_type:
                    error_msg = f"Circuit breaker open for {url}: service unavailable"
                # Check for rate limit exceeded
                elif "RateLimitExceeded" in error_type:
                    error_msg = f"Rate limit exceeded for {url}"
                # Check for SSRF protection
                elif "SSRF" in str(e):
                    error_msg = f"SSRF protection blocked request to {url}"
                else:
                    error_msg = f"HTTP {method} request failed: {str(e)}"

                raise ValueError(error_msg) from e

        except asyncio.TimeoutError:
            error_msg = f"Request timed out after {self.get_parameter('timeout', self.DEFAULT_TIMEOUT)} seconds"
            logger.error(error_msg)
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

        except ValueError as e:
            error_msg = str(e)
            logger.error(f"HTTP {method} error: {error_msg}")
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}

        except Exception as e:
            error_msg = f"HTTP {method} error: {str(e)}"
            logger.error(error_msg)
            self._set_error_outputs(error_msg)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": error_msg, "next_nodes": []}


__all__ = [
    "HttpBaseNode",
    "get_http_client_from_context",
    "close_http_client_from_context",
    "HTTP_CLIENT_RESOURCE_KEY",
    # Deprecated - kept for backward compatibility
    "get_shared_http_session",
    "close_shared_http_session",
]
