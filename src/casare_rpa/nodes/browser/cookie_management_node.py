"""
Browser cookie management node.

This module provides node for managing browser cookies:
- get: Get all cookies or specific cookie by name
- set: Set a cookie or multiple cookies
- delete: Delete a cookie by name
- delete_all: Delete all cookies
- export: Export cookies as JSON
- import: Import cookies from JSON

Uses Playwright's cookie management APIs.
"""

import json
from typing import Any

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.browser.browser_base import BrowserBaseNode


@properties(
    PropertyDef(
        "operation",
        PropertyType.CHOICE,
        default="get",
        choices=["get", "set", "delete", "delete_all", "export", "import"],
        label="Operation",
        tooltip="Cookie operation to perform",
        essential=True,
    ),
    PropertyDef(
        "cookie_name",
        PropertyType.STRING,
        default="",
        label="Cookie Name",
        placeholder="session_id",
        tooltip="Name of the cookie (for get/set/delete operations)",
    ),
    PropertyDef(
        "cookie_value",
        PropertyType.STRING,
        default="",
        label="Cookie Value",
        placeholder="abc123xyz",
        tooltip="Value of the cookie (for set operation)",
    ),
    PropertyDef(
        "cookies_json",
        PropertyType.TEXT,
        default="",
        label="Cookies JSON",
        placeholder='[{"name": "session", "value": "abc123", "domain": ".example.com"}]',
        tooltip="JSON array of cookies (for set/import operations)",
        tab="advanced",
    ),
    PropertyDef(
        "domain",
        PropertyType.STRING,
        default="",
        label="Domain",
        placeholder=".example.com",
        tooltip="Cookie domain (for set operation, defaults to current page)",
    ),
    PropertyDef(
        "path",
        PropertyType.STRING,
        default="/",
        label="Path",
        tooltip="Cookie path (for set operation)",
    ),
    PropertyDef(
        "expires",
        PropertyType.FLOAT,
        default=0,
        label="Expires (seconds)",
        tooltip="Cookie expiration time in seconds from now (0 = session cookie)",
        min_value=0,
    ),
    PropertyDef(
        "secure",
        PropertyType.BOOLEAN,
        default=False,
        label="Secure",
        tooltip="Set secure flag (HTTPS only)",
    ),
    PropertyDef(
        "http_only",
        PropertyType.BOOLEAN,
        default=False,
        label="HttpOnly",
        tooltip="Set HttpOnly flag (not accessible via JavaScript)",
    ),
    PropertyDef(
        "same_site",
        PropertyType.CHOICE,
        default="None",
        choices=["None", "Lax", "Strict"],
        label="SameSite",
        tooltip="SameSite attribute for cookie",
    ),
)
@node(category="browser")
class CookieManagementNode(BrowserBaseNode):
    """
    Manage browser cookies.

    Supports the following operations:
    - **get**: Get all cookies or a specific cookie by name
    - **set**: Set a single cookie (using properties) or multiple cookies (using JSON)
    - **delete**: Delete a specific cookie by name
    - **delete_all**: Delete all cookies for the current context
    - **export**: Export all cookies as JSON string
    - **import**: Import cookies from JSON string

    Example:
        # Get all cookies
        CookieManagementNode(operation="get")

        # Set a session cookie
        CookieManagementNode(operation="set", cookie_name="session", cookie_value="abc123")

        # Set a persistent cookie with options
        CookieManagementNode(
            operation="set",
            cookie_name="user_pref",
            cookie_value="dark_mode",
            domain=".example.com",
            expires=86400  # 24 hours
        )

        # Export all cookies
        CookieManagementNode(operation="export")  # Returns cookies via output port
    """

    def __init__(self, node_id: str, config: dict | None = None, **kwargs: Any) -> None:
        """Initialize CookieManagementNode."""
        super().__init__(node_id, config, **kwargs)

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Page passthrough
        self.add_page_passthrough_ports(required=False)

        # Optional: cookies_json can come from input port
        self.add_input_port("cookies_input", DataType.STRING, required=False)

        # Outputs
        self.add_output_port("cookies", DataType.STRING)  # JSON string
        self.add_output_port("cookie", DataType.DICT)  # Single cookie dict
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute the cookie management operation.

        Args:
            context: Execution context

        Returns:
            Execution result with operation information
        """
        try:
            page = self.get_page(context)

            # Get parameters
            operation = self.get_parameter("operation", "get")
            cookie_name = self.get_parameter("cookie_name", "")
            cookie_value = self.get_parameter("cookie_value", "")
            cookies_json = self.get_parameter("cookies_json", "")
            domain = self.get_parameter("domain", "")
            path = self.get_parameter("path", "/")
            expires = self.get_parameter("expires", 0)
            secure = self.get_parameter("secure", False)
            http_only = self.get_parameter("http_only", False)
            same_site = self.get_parameter("same_site", "None")

            # Allow cookies from input port
            if not cookies_json:
                cookies_json = self.get_input_value("cookies_input") or ""

            result: dict[str, Any] = {
                "success": False,
                "cookies": "[]",
                "cookie": {},
                "count": 0,
            }

            # Get the browser context for cookie operations
            browser_context = page.context

            if operation == "get":
                result = await self._get_cookies(browser_context, cookie_name)

            elif operation == "set":
                result = await self._set_cookies(
                    browser_context,
                    cookie_name,
                    cookie_value,
                    cookies_json,
                    domain,
                    path,
                    expires,
                    secure,
                    http_only,
                    same_site,
                )

            elif operation == "delete":
                result = await self._delete_cookie(browser_context, cookie_name)

            elif operation == "delete_all":
                result = await self._delete_all_cookies(browser_context)

            elif operation == "export":
                result = await self._export_cookies(browser_context)

            elif operation == "import":
                result = await self._import_cookies(browser_context, cookies_json)

            # Set output values
            self.set_output_value("cookies", result["cookies"])
            self.set_output_value("cookie", result["cookie"])
            self.set_output_value("success", result["success"])
            self.set_output_value("count", result["count"])

            # Pass page through
            output_page = self.get_input_value("page") or context.get_active_page()
            if output_page:
                self.set_output_value("page", output_page)

            return self.success_result(
                data=result,
                next_nodes=["exec_out"] if result["success"] else [],
            )

        except Exception as e:
            logger.error(f"Cookie management failed: {e}")
            self.set_output_value("success", False)
            return self.error_result(e)

    async def _get_cookies(self, browser_context: Any, cookie_name: str) -> dict[str, Any]:
        """Get all cookies or a specific cookie by name."""
        cookies = await browser_context.cookies()

        if cookie_name:
            # Filter by name
            cookies = [c for c in cookies if c.get("name") == cookie_name]

        return {
            "success": True,
            "cookies": json.dumps(cookies, default=str),
            "cookie": cookies[0] if cookies else {},
            "count": len(cookies),
        }

    async def _set_cookies(
        self,
        browser_context: Any,
        cookie_name: str,
        cookie_value: str,
        cookies_json: str,
        domain: str,
        path: str,
        expires: float,
        secure: bool,
        http_only: bool,
        same_site: str,
    ) -> dict[str, Any]:
        """Set cookie(s)."""
        cookies_to_set = []

        # Check if bulk cookies are provided via JSON
        if cookies_json:
            try:
                cookies_to_set = json.loads(cookies_json)
                if isinstance(cookies_to_set, dict):
                    cookies_to_set = [cookies_to_set]
            except json.JSONDecodeError as e:
                logger.error(f"Invalid cookies JSON: {e}")
                return {"success": False, "cookies": "[]", "cookie": {}, "count": 0}

        # Check if single cookie is provided via properties
        elif cookie_name:
            cookie_dict: dict[str, Any] = {
                "name": cookie_name,
                "value": cookie_value,
                "path": path,
                "secure": secure,
                "httpOnly": http_only,
                "sameSite": same_site,
            }

            if domain:
                cookie_dict["domain"] = domain
            if expires > 0:
                import time

                cookie_dict["expires"] = time.time() + expires

            cookies_to_set = [cookie_dict]

        else:
            logger.warning("No cookies to set - provide cookie_name/value or cookies_json")
            return {"success": False, "cookies": "[]", "cookie": {}, "count": 0}

        # Set cookies
        await browser_context.add_cookies(cookies_to_set)
        logger.info(f"Set {len(cookies_to_set)} cookie(s)")

        return {
            "success": True,
            "cookies": json.dumps(cookies_to_set, default=str),
            "cookie": cookies_to_set[0] if cookies_to_set else {},
            "count": len(cookies_to_set),
        }

    async def _delete_cookie(self, browser_context: Any, cookie_name: str) -> dict[str, Any]:
        """Delete a specific cookie by name."""
        if not cookie_name:
            logger.warning("Cookie name required for delete operation")
            return {"success": False, "cookies": "[]", "cookie": {}, "count": 0}

        await browser_context.add_cookies([{"name": cookie_name, "value": "", "expires": 0}])
        logger.info(f"Deleted cookie: {cookie_name}")

        return {
            "success": True,
            "cookies": "[]",
            "cookie": {"name": cookie_name},
            "count": 1,
        }

    async def _delete_all_cookies(self, browser_context: Any) -> dict[str, Any]:
        """Delete all cookies."""
        cookies_before = await browser_context.cookies()
        count = len(cookies_before)

        await browser_context.clear_cookies()
        logger.info(f"Cleared {count} cookie(s)")

        return {
            "success": True,
            "cookies": "[]",
            "cookie": {},
            "count": count,
        }

    async def _export_cookies(self, browser_context: Any) -> dict[str, Any]:
        """Export all cookies as JSON."""
        cookies = await browser_context.cookies()

        return {
            "success": True,
            "cookies": json.dumps(cookies, default=str),
            "cookie": {},
            "count": len(cookies),
        }

    async def _import_cookies(self, browser_context: Any, cookies_json: str) -> dict[str, Any]:
        """Import cookies from JSON."""
        if not cookies_json:
            logger.warning("No cookies JSON provided for import")
            return {"success": False, "cookies": "[]", "cookie": {}, "count": 0}

        try:
            cookies = json.loads(cookies_json)
            if isinstance(cookies, dict):
                cookies = [cookies]

            await browser_context.add_cookies(cookies)
            logger.info(f"Imported {len(cookies)} cookie(s)")

            return {
                "success": True,
                "cookies": json.dumps(cookies, default=str),
                "cookie": cookies[0] if cookies else {},
                "count": len(cookies),
            }

        except json.JSONDecodeError as e:
            logger.error(f"Invalid cookies JSON: {e}")
            return {"success": False, "cookies": "[]", "cookie": {}, "count": 0}
