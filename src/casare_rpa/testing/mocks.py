"""
CasareRPA - Mock Objects for Testing.

Provides mock implementations for testing workflows and nodes in isolation.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class MockCall:
    """Record of a method call on a mock object."""

    method: str
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    result: Any = None
    exception: Exception | None = None


class MockService:
    """
    Base class for mock services.

    Tracks all method calls and allows configuring return values.
    """

    def __init__(self, name: str = "MockService") -> None:
        self.name = name
        self.calls: list[MockCall] = []
        self._return_values: dict[str, Any] = {}
        self._side_effects: dict[str, Callable] = {}
        self._exceptions: dict[str, Exception] = {}

    def configure_return(self, method: str, value: Any) -> MockService:
        """Configure return value for a method."""
        self._return_values[method] = value
        return self

    def configure_side_effect(self, method: str, side_effect: Callable[..., Any]) -> MockService:
        """Configure side effect function for a method."""
        self._side_effects[method] = side_effect
        return self

    def configure_exception(self, method: str, exception: Exception) -> MockService:
        """Configure exception to raise for a method."""
        self._exceptions[method] = exception
        return self

    def _record_call(
        self,
        method: str,
        args: tuple,
        kwargs: dict,
        result: Any = None,
        exception: Exception | None = None,
    ) -> None:
        """Record a method call."""
        self.calls.append(
            MockCall(
                method=method,
                args=args,
                kwargs=kwargs,
                result=result,
                exception=exception,
            )
        )

    def _get_response(self, method: str, *args: Any, **kwargs: Any) -> Any:
        """Get configured response for a method call."""
        # Check for exception
        if method in self._exceptions:
            exc = self._exceptions[method]
            self._record_call(method, args, kwargs, exception=exc)
            raise exc

        # Check for side effect
        if method in self._side_effects:
            result = self._side_effects[method](*args, **kwargs)
            self._record_call(method, args, kwargs, result=result)
            return result

        # Check for return value
        if method in self._return_values:
            result = self._return_values[method]
            self._record_call(method, args, kwargs, result=result)
            return result

        # Default: return None
        self._record_call(method, args, kwargs)
        return None

    def get_calls(self, method: str | None = None) -> list[MockCall]:
        """Get recorded calls, optionally filtered by method name."""
        if method is None:
            return self.calls
        return [c for c in self.calls if c.method == method]

    def call_count(self, method: str | None = None) -> int:
        """Get number of calls, optionally filtered by method name."""
        return len(self.get_calls(method))

    def was_called(self, method: str) -> bool:
        """Check if a method was called."""
        return self.call_count(method) > 0

    def reset(self) -> None:
        """Reset all recorded calls."""
        self.calls.clear()


class MockExecutionContext:
    """
    Mock execution context for testing nodes.

    Provides isolated environment for node execution without
    actual services, browser, or file system access.
    """

    def __init__(self) -> None:
        self.variables: dict[str, Any] = {}
        self.services: dict[str, Any] = {}
        self.node_outputs: dict[str, dict[str, Any]] = {}
        self.call_log: list[tuple[str, tuple, dict]] = []
        self.events: list[dict[str, Any]] = []

        # Default mock services
        self.services["http_client"] = MockHttpClient()
        self.services["browser_pool"] = MockBrowserPool()

    def get_variable(self, name: str) -> Any:
        """Get variable value."""
        return self.variables.get(name)

    def set_variable(self, name: str, value: Any) -> None:
        """Set variable value."""
        self.variables[name] = value
        self.call_log.append(("set_variable", (name, value), {}))

    def get_service(self, name: str) -> Any:
        """Get a mock service by name."""
        return self.services.get(name)

    def register_service(self, name: str, service: Any) -> None:
        """Register a mock service."""
        self.services[name] = service

    def get_node_output(self, node_id: str, port: str) -> Any:
        """Get output from a previously executed node."""
        outputs = self.node_outputs.get(node_id, {})
        return outputs.get(port)

    def set_node_output(self, node_id: str, port: str, value: Any) -> None:
        """Set output for a node (for test setup)."""
        if node_id not in self.node_outputs:
            self.node_outputs[node_id] = {}
        self.node_outputs[node_id][port] = value

    def emit_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Emit an event (for logging/tracking)."""
        self.events.append({"type": event_type, "data": data})
        self.call_log.append(("emit_event", (event_type, data), {}))

    def log_call(self, method: str, args: tuple, kwargs: dict) -> None:
        """Log a method call."""
        self.call_log.append((method, args, kwargs))

    def reset(self) -> None:
        """Reset context state."""
        self.variables.clear()
        self.node_outputs.clear()
        self.call_log.clear()
        self.events.clear()

    def with_variable(self, name: str, value: Any) -> MockExecutionContext:
        """Fluent method to set a variable."""
        self.set_variable(name, value)
        return self

    def with_service(self, name: str, service: Any) -> MockExecutionContext:
        """Fluent method to register a service."""
        self.register_service(name, service)
        return self


class MockHttpClient(MockService):
    """
    Mock HTTP client for testing HTTP nodes.

    Allows configuring responses for specific URLs and methods.
    """

    def __init__(self) -> None:
        super().__init__("MockHttpClient")
        self._responses: dict[str, dict[str, Any]] = {}

    def configure_response(
        self,
        url: str,
        status: int = 200,
        json: dict | None = None,
        text: str | None = None,
        headers: dict[str, str] | None = None,
        method: str = "*",
    ) -> MockHttpClient:
        """
        Configure response for a URL.

        Args:
            url: URL pattern (exact match or contains)
            status: HTTP status code
            json: JSON response body
            text: Text response body
            headers: Response headers
            method: HTTP method (* for any)
        """
        key = f"{method}:{url}"
        self._responses[key] = {
            "status": status,
            "json": json,
            "text": text,
            "headers": headers or {},
        }
        return self

    async def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> MockHttpResponse:
        """Make a mock HTTP request."""
        # Find matching response
        response_config = self._find_response(method, url)

        response = MockHttpResponse(
            status=response_config.get("status", 200),
            json_data=response_config.get("json"),
            text_data=response_config.get("text", ""),
            headers=response_config.get("headers", {}),
        )

        self._record_call("request", (method, url), kwargs, result=response)
        return response

    async def get(self, url: str, **kwargs: Any) -> MockHttpResponse:
        """Mock GET request."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> MockHttpResponse:
        """Mock POST request."""
        return await self.request("POST", url, **kwargs)

    def _find_response(self, method: str, url: str) -> dict[str, Any]:
        """Find configured response for method/url."""
        # Try exact match with method
        key = f"{method}:{url}"
        if key in self._responses:
            return self._responses[key]

        # Try wildcard method
        key = f"*:{url}"
        if key in self._responses:
            return self._responses[key]

        # Try partial URL match
        for resp_key, config in self._responses.items():
            resp_method, resp_url = resp_key.split(":", 1)
            if (resp_method == "*" or resp_method == method) and resp_url in url:
                return config

        # Default response
        return {"status": 200, "text": ""}


@dataclass
class MockHttpResponse:
    """Mock HTTP response object."""

    status: int = 200
    json_data: dict | None = None
    text_data: str = ""
    headers: dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        """Check if response is successful."""
        return 200 <= self.status < 300

    async def json(self) -> dict | None:
        """Get JSON response body."""
        return self.json_data

    async def text(self) -> str:
        """Get text response body."""
        if self.json_data:
            import json

            return json.dumps(self.json_data)
        return self.text_data


class MockBrowserPool(MockService):
    """
    Mock browser pool for testing browser nodes.

    Returns mock browser contexts and pages.
    """

    def __init__(self) -> None:
        super().__init__("MockBrowserPool")
        self._pages: list[MockPage] = []

    async def acquire(
        self,
        browser_type: str = "chromium",
        headless: bool = True,
    ) -> MockBrowserContext:
        """Acquire a mock browser context."""
        context = MockBrowserContext(browser_type=browser_type, headless=headless)
        self._record_call("acquire", (browser_type,), {"headless": headless}, result=context)
        return context

    async def release(self, context: MockBrowserContext) -> None:
        """Release a browser context back to pool."""
        self._record_call("release", (context,), {})


@dataclass
class MockBrowserContext:
    """Mock browser context."""

    browser_type: str = "chromium"
    headless: bool = True
    pages: list[MockPage] = field(default_factory=list)

    async def new_page(self) -> MockPage:
        """Create a new mock page."""
        page = MockPage()
        self.pages.append(page)
        return page

    async def close(self) -> None:
        """Close the context."""
        pass


class MockPage:
    """
    Mock browser page for testing.

    Tracks navigation, clicks, typing, and other interactions.
    """

    def __init__(self) -> None:
        self.url = ""
        self.title = "Mock Page"
        self.content = "<html><body></body></html>"
        self.calls: list[MockCall] = []
        self._elements: dict[str, MockElement] = {}
        self._responses: dict[str, str] = {}

    def configure_element(
        self,
        selector: str,
        text: str = "",
        visible: bool = True,
        enabled: bool = True,
    ) -> MockPage:
        """Configure a mock element."""
        self._elements[selector] = MockElement(
            selector=selector,
            text=text,
            visible=visible,
            enabled=enabled,
        )
        return self

    def configure_content(self, url_pattern: str, content: str) -> MockPage:
        """Configure page content for a URL pattern."""
        self._responses[url_pattern] = content
        return self

    async def goto(self, url: str, **kwargs: Any) -> None:
        """Navigate to URL."""
        self.url = url
        self.calls.append(MockCall("goto", (url,), kwargs))

        # Load configured content
        for pattern, content in self._responses.items():
            if pattern in url:
                self.content = content
                break

    async def click(self, selector: str, **kwargs: Any) -> None:
        """Click an element."""
        self.calls.append(MockCall("click", (selector,), kwargs))

    async def fill(self, selector: str, value: str, **kwargs: Any) -> None:
        """Fill an input field."""
        self.calls.append(MockCall("fill", (selector, value), kwargs))

    async def type(self, selector: str, text: str, **kwargs: Any) -> None:
        """Type text into an element."""
        self.calls.append(MockCall("type", (selector, text), kwargs))

    async def wait_for_selector(self, selector: str, **kwargs: Any) -> MockElement:
        """Wait for an element to appear."""
        self.calls.append(MockCall("wait_for_selector", (selector,), kwargs))
        return self._elements.get(selector, MockElement(selector=selector))

    async def query_selector(self, selector: str) -> MockElement | None:
        """Query for an element."""
        self.calls.append(MockCall("query_selector", (selector,), {}))
        return self._elements.get(selector)

    async def screenshot(self, **kwargs: Any) -> bytes:
        """Take a screenshot."""
        self.calls.append(MockCall("screenshot", (), kwargs))
        # Return minimal valid PNG
        return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"

    async def evaluate(self, expression: str, *args: Any) -> Any:
        """Evaluate JavaScript."""
        self.calls.append(MockCall("evaluate", (expression,) + args, {}))
        return None

    async def content(self) -> str:
        """Get page HTML content."""
        return self.content


@dataclass
class MockElement:
    """Mock browser element."""

    selector: str
    text: str = ""
    visible: bool = True
    enabled: bool = True
    attributes: dict[str, str] = field(default_factory=dict)

    async def click(self) -> None:
        """Click the element."""
        pass

    async def fill(self, value: str) -> None:
        """Fill the element."""
        self.text = value

    async def text_content(self) -> str:
        """Get text content."""
        return self.text

    async def get_attribute(self, name: str) -> str | None:
        """Get attribute value."""
        return self.attributes.get(name)

    async def is_visible(self) -> bool:
        """Check if visible."""
        return self.visible

    async def is_enabled(self) -> bool:
        """Check if enabled."""
        return self.enabled


__all__ = [
    "MockService",
    "MockCall",
    "MockExecutionContext",
    "MockHttpClient",
    "MockHttpResponse",
    "MockBrowserPool",
    "MockBrowserContext",
    "MockPage",
    "MockElement",
]
