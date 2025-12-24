"""
Playwright MCP Client for browser automation via MCP protocol.

Provides async interface to Playwright MCP server for navigating pages,
capturing snapshots, and interacting with web elements.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any

from loguru import logger


@dataclass
class MCPToolResult:
    """Result from an MCP tool call."""

    success: bool
    content: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None

    def get_text(self) -> str:
        """Extract text content from result."""
        for item in self.content:
            if item.get("type") == "text":
                return item.get("text", "")
        return ""


class PlaywrightMCPClient:
    """
    Client for communicating with Playwright MCP server.

    Uses subprocess/stdio to communicate with the MCP server via JSON-RPC protocol.
    Provides high-level methods for browser automation tasks.

    Example:
        async with PlaywrightMCPClient() as client:
            await client.navigate("https://example.com")
            snapshot = await client.get_snapshot()
            await client.close()
    """

    # Default timeouts in seconds
    DEFAULT_NAVIGATE_TIMEOUT = 30.0
    DEFAULT_SNAPSHOT_TIMEOUT = 10.0
    DEFAULT_ACTION_TIMEOUT = 10.0
    DEFAULT_INIT_TIMEOUT = 30.0

    def __init__(
        self,
        headless: bool = True,
        browser: str = "chrome",
        npx_path: str | None = None,
    ) -> None:
        """
        Initialize Playwright MCP client.

        Args:
            headless: Run browser in headless mode
            browser: Browser to use (chrome, msedge, chromium, firefox, webkit)
            npx_path: Path to npx executable (auto-detected if None)
        """
        self._headless = headless
        self._browser = browser
        self._npx_path = npx_path or self._find_npx()
        self._process: asyncio.subprocess.Process | None = None
        self._request_id = 0
        self._initialized = False
        self._pending_requests: dict[int, asyncio.Future] = {}
        self._reader_task: asyncio.Task | None = None

    def _find_npx(self) -> str:
        """Find npx executable path."""
        if sys.platform == "win32":
            # Check common Windows paths
            candidates = [
                os.environ.get("NPX_PATH", ""),
                r"C:\nvm4w\nodejs\npx.cmd",
                r"C:\Program Files\nodejs\npx.cmd",
                os.path.join(os.environ.get("APPDATA", ""), "nvm", "nodejs", "npx.cmd"),
                "npx.cmd",
                "npx",
            ]
            for candidate in candidates:
                if candidate and os.path.isfile(candidate):
                    return candidate
            return "npx.cmd"  # Fallback, rely on PATH
        return "npx"

    async def __aenter__(self) -> PlaywrightMCPClient:
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.stop()

    async def start(self) -> bool:
        """
        Start the Playwright MCP server subprocess.

        Returns:
            True if server started successfully
        """
        if self._process is not None:
            logger.warning("MCP server already running")
            return True

        try:
            args = [
                self._npx_path,
                "-y",
                "@playwright/mcp@latest",
                f"--browser={self._browser}",
                "--isolated",  # Allow multiple browser instances
            ]
            if self._headless:
                args.append("--headless")

            logger.info(f"Starting Playwright MCP server: {' '.join(args)}")

            self._process = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Start reader task for responses
            self._reader_task = asyncio.create_task(self._read_responses())

            # Initialize MCP connection
            success = await self._initialize()
            if success:
                logger.info("Playwright MCP server started successfully")
            return success

        except FileNotFoundError as e:
            logger.error(f"Failed to find npx: {e}. Install Node.js and ensure npx is in PATH")
            return False
        except Exception as e:
            logger.error(f"Failed to start Playwright MCP server: {e}")
            await self.stop()
            return False

    async def stop(self) -> None:
        """Stop the Playwright MCP server subprocess."""
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
            self._reader_task = None

        if self._process:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except TimeoutError:
                self._process.kill()
            except Exception as e:
                logger.warning(f"Error stopping MCP server: {e}")
            finally:
                self._process = None
                self._initialized = False

        # Cancel pending requests
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()

        logger.debug("Playwright MCP server stopped")

    async def _read_responses(self) -> None:
        """Read and dispatch responses from MCP server."""
        if not self._process or not self._process.stdout:
            return

        buffer = ""
        while True:
            try:
                chunk = await self._process.stdout.read(4096)
                if not chunk:
                    break

                buffer += chunk.decode("utf-8", errors="replace")

                # Process complete JSON-RPC messages
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        message = json.loads(line)
                        await self._handle_message(message)
                    except json.JSONDecodeError:
                        logger.debug(f"Non-JSON line from MCP: {line[:100]}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error reading MCP responses: {e}")
                break

    async def _handle_message(self, message: dict[str, Any]) -> None:
        """Handle incoming MCP message."""
        msg_id = message.get("id")
        if msg_id is not None and msg_id in self._pending_requests:
            future = self._pending_requests.pop(msg_id)
            if not future.done():
                if "error" in message:
                    future.set_exception(
                        Exception(message["error"].get("message", "Unknown error"))
                    )
                else:
                    future.set_result(message.get("result"))

    async def _send_request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> Any:
        """
        Send JSON-RPC request to MCP server.

        Args:
            method: MCP method name
            params: Method parameters
            timeout: Request timeout in seconds

        Returns:
            Response result

        Raises:
            Exception: If request fails or times out
        """
        if not self._process or not self._process.stdin:
            raise RuntimeError("MCP server not running")

        self._request_id += 1
        request_id = self._request_id

        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params:
            request["params"] = params

        # Create future for response
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending_requests[request_id] = future

        # Send request
        request_line = json.dumps(request) + "\n"
        self._process.stdin.write(request_line.encode("utf-8"))
        await self._process.stdin.drain()

        logger.debug(f"MCP request: {method} (id={request_id})")

        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except TimeoutError:
            self._pending_requests.pop(request_id, None)
            raise TimeoutError(f"MCP request {method} timed out after {timeout}s") from None

    async def _initialize(self) -> bool:
        """Initialize MCP connection."""
        try:
            result = await self._send_request(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "casare-rpa",
                        "version": "1.0.0",
                    },
                },
                timeout=self.DEFAULT_INIT_TIMEOUT,
            )
            self._initialized = True
            logger.debug(f"MCP initialized: {result}")

            # Send initialized notification
            if self._process and self._process.stdin:
                notification = (
                    json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"
                )
                self._process.stdin.write(notification.encode("utf-8"))
                await self._process.stdin.drain()

            return True
        except Exception as e:
            logger.error(f"Failed to initialize MCP: {e}")
            return False

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        timeout: float = DEFAULT_ACTION_TIMEOUT,
    ) -> MCPToolResult:
        """
        Call an MCP tool.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            timeout: Request timeout

        Returns:
            MCPToolResult with tool output
        """
        if not self._initialized:
            return MCPToolResult(success=False, error="MCP not initialized")

        try:
            result = await self._send_request(
                "tools/call",
                {
                    "name": tool_name,
                    "arguments": arguments or {},
                },
                timeout=timeout,
            )

            content = result.get("content", []) if result else []
            is_error = result.get("isError", False) if result else True

            return MCPToolResult(
                success=not is_error,
                content=content,
                error=content[0].get("text") if is_error and content else None,
            )

        except Exception as e:
            logger.error(f"Tool call {tool_name} failed: {e}")
            return MCPToolResult(success=False, error=str(e))

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available MCP tools."""
        if not self._initialized:
            return []

        try:
            result = await self._send_request("tools/list", timeout=10.0)
            return result.get("tools", []) if result else []
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []

    # High-level browser automation methods

    async def navigate(self, url: str) -> MCPToolResult:
        """
        Navigate to a URL.

        Args:
            url: URL to navigate to

        Returns:
            MCPToolResult with navigation status
        """
        logger.info(f"Navigating to: {url}")
        return await self.call_tool(
            "browser_navigate",
            {"url": url},
            timeout=self.DEFAULT_NAVIGATE_TIMEOUT,
        )

    async def get_snapshot(self) -> MCPToolResult:
        """
        Get accessibility snapshot of current page.

        Returns:
            MCPToolResult with page snapshot text
        """
        return await self.call_tool(
            "browser_snapshot",
            timeout=self.DEFAULT_SNAPSHOT_TIMEOUT,
        )

    async def click(self, ref: str, element_description: str = "element") -> MCPToolResult:
        """
        Click an element.

        Args:
            ref: Element reference from snapshot
            element_description: Human-readable description

        Returns:
            MCPToolResult with click status
        """
        return await self.call_tool(
            "browser_click",
            {"ref": ref, "element": element_description},
        )

    async def type_text(
        self,
        ref: str,
        text: str,
        element_description: str = "input field",
        submit: bool = False,
    ) -> MCPToolResult:
        """
        Type text into an element.

        Args:
            ref: Element reference from snapshot
            text: Text to type
            element_description: Human-readable description
            submit: Whether to press Enter after typing

        Returns:
            MCPToolResult with type status
        """
        return await self.call_tool(
            "browser_type",
            {
                "ref": ref,
                "text": text,
                "element": element_description,
                "submit": submit,
            },
        )

    async def close_browser(self) -> MCPToolResult:
        """Close the browser."""
        return await self.call_tool("browser_close")

    async def take_screenshot(self, filename: str | None = None) -> MCPToolResult:
        """
        Take a screenshot of the current page.

        Args:
            filename: Optional filename to save screenshot

        Returns:
            MCPToolResult with screenshot info
        """
        args: dict[str, Any] = {}
        if filename:
            args["filename"] = filename
        return await self.call_tool("browser_take_screenshot", args)

    async def wait_for(
        self,
        text: str | None = None,
        text_gone: str | None = None,
        time_seconds: float | None = None,
    ) -> MCPToolResult:
        """
        Wait for a condition.

        Args:
            text: Text to wait for to appear
            text_gone: Text to wait for to disappear
            time_seconds: Time to wait in seconds

        Returns:
            MCPToolResult with wait status
        """
        args: dict[str, Any] = {}
        if text:
            args["text"] = text
        if text_gone:
            args["textGone"] = text_gone
        if time_seconds:
            args["time"] = time_seconds
        return await self.call_tool("browser_wait_for", args)

    async def evaluate(self, js_function: str, ref: str | None = None) -> MCPToolResult:
        """
        Evaluate JavaScript on the page.

        Args:
            js_function: JavaScript function to evaluate
            ref: Optional element reference

        Returns:
            MCPToolResult with evaluation result
        """
        args: dict[str, Any] = {"function": js_function}
        if ref:
            args["ref"] = ref
            args["element"] = "target element"
        return await self.call_tool("browser_evaluate", args)


async def fetch_page_context(
    url: str,
    headless: bool = True,
    timeout: float = 30.0,
) -> dict[str, Any] | None:
    """
    Convenience function to fetch page context from a URL.

    Args:
        url: URL to fetch
        headless: Run browser in headless mode
        timeout: Navigation timeout

    Returns:
        Dict with url, title, and snapshot, or None on failure
    """
    try:
        async with PlaywrightMCPClient(headless=headless) as client:
            nav_result = await client.navigate(url)
            if not nav_result.success:
                logger.error(f"Failed to navigate to {url}: {nav_result.error}")
                return None

            # Small wait for page to stabilize
            await client.wait_for(time_seconds=1.0)

            snapshot_result = await client.get_snapshot()
            if not snapshot_result.success:
                logger.error(f"Failed to get snapshot: {snapshot_result.error}")
                return None

            # Get page title via evaluate
            title_result = await client.evaluate("() => document.title")
            title = title_result.get_text() if title_result.success else ""

            return {
                "url": url,
                "title": title,
                "snapshot": snapshot_result.get_text(),
            }

    except Exception as e:
        logger.error(f"Failed to fetch page context for {url}: {e}")
        return None
