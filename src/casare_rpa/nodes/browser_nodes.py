"""
Browser control nodes for Playwright automation.

This module provides nodes for controlling browser lifecycle:
launching browsers, managing tabs, and cleanup.
"""

import asyncio
from typing import Any, Optional

from playwright.async_api import Browser, Page, BrowserContext

from ..core.base_node import BaseNode
from ..core.types import NodeStatus, PortType, DataType, ExecutionResult
from ..core.execution_context import ExecutionContext
from ..utils.config import DEFAULT_BROWSER, HEADLESS_MODE, BROWSER_ARGS
from loguru import logger


class LaunchBrowserNode(BaseNode):
    """
    Launch browser node - creates a new browser instance.
    
    Opens a browser (Chromium, Firefox, or WebKit) using Playwright
    and stores it in the execution context for use by other nodes.
    """
    
    def __init__(
        self,
        node_id: str,
        name: str = "Launch Browser",
        browser_type: str = DEFAULT_BROWSER,
        headless: bool = HEADLESS_MODE,
        **kwargs
    ) -> None:
        """
        Initialize launch browser node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            browser_type: Browser to launch (chromium, firefox, webkit)
            headless: Whether to run in headless mode
        """
        # Default config with all Playwright options
        default_config = {
            "browser_type": browser_type,
            "headless": headless,
            # Performance options
            "slow_mo": 0,  # Slow down operations by ms (for debugging)
            "channel": "",  # Browser channel (chrome, msedge, chrome-beta)
            # Viewport options
            "viewport_width": 1280,
            "viewport_height": 720,
            # Browser identity options
            "user_agent": "",  # Custom user agent string
            "locale": "",  # Locale (e.g., "en-US")
            "timezone_id": "",  # Timezone (e.g., "America/New_York")
            "color_scheme": "light",  # Preferred color scheme (light/dark/no-preference)
            # Security options
            "ignore_https_errors": False,
            "proxy_server": "",  # Proxy server URL
            # Retry options
            "retry_count": 0,  # Number of retries on failure
            "retry_interval": 2000,  # Delay between retries in ms
        }

        config = kwargs.get("config", {})
        # Merge with defaults
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        super().__init__(node_id, config)
        self.name = name
        self.node_type = "LaunchBrowserNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("url", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("browser", PortType.OUTPUT, DataType.BROWSER)
        self.add_output_port("page", PortType.OUTPUT, DataType.PAGE)
    
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute browser launch.

        Args:
            context: Execution context for the workflow

        Returns:
            Result with browser instance
        """
        self.status = NodeStatus.RUNNING

        # Helper to safely parse int values with defaults
        def safe_int(value, default: int) -> int:
            if value is None or value == "":
                return default
            try:
                return int(value)
            except (ValueError, TypeError):
                return default

        # Get retry options
        retry_count = safe_int(self.config.get("retry_count"), 0)
        retry_interval = safe_int(self.config.get("retry_interval"), 2000)

        last_error = None
        attempts = 0
        max_attempts = retry_count + 1

        while attempts < max_attempts:
            try:
                attempts += 1
                if attempts > 1:
                    logger.info(f"Retry attempt {attempts - 1}/{retry_count} for browser launch")

                from playwright.async_api import async_playwright

                browser_type = self.config.get("browser_type", DEFAULT_BROWSER)
                headless = self.config.get("headless", HEADLESS_MODE)

                logger.info(f"Launching {browser_type} browser (headless={headless})")

                # Build launch options
                launch_options = {"headless": headless}

                # Add slow_mo if specified (for debugging)
                slow_mo = self.config.get("slow_mo", 0)
                # Handle empty strings and convert to int safely
                if slow_mo and str(slow_mo).strip():
                    try:
                        slow_mo_int = int(slow_mo)
                        if slow_mo_int > 0:
                            launch_options["slow_mo"] = slow_mo_int
                    except (ValueError, TypeError):
                        pass  # Ignore invalid slow_mo values

                # Add channel for chromium-based browsers
                channel = self.config.get("channel", "")
                if channel and browser_type == "chromium":
                    launch_options["channel"] = channel

                # Launch playwright
                playwright = await async_playwright().start()

                # Get browser type and launch with options
                if browser_type == "firefox":
                    browser = await playwright.firefox.launch(**launch_options)
                elif browser_type == "webkit":
                    browser = await playwright.webkit.launch(**launch_options)
                else:  # chromium (default)
                    # Add chromium-specific args
                    launch_options["args"] = BROWSER_ARGS
                    browser = await playwright.chromium.launch(**launch_options)

                # Store browser in context
                context.browser = browser

                # Build browser context options
                context_options = {}

                # Viewport settings - safely parse with defaults (using safe_int defined above)
                viewport_width = safe_int(self.config.get("viewport_width"), 1280)
                viewport_height = safe_int(self.config.get("viewport_height"), 720)
                context_options["viewport"] = {"width": viewport_width, "height": viewport_height}

                # User agent
                user_agent = self.config.get("user_agent", "")
                if user_agent:
                    context_options["user_agent"] = user_agent

                # Locale
                locale = self.config.get("locale", "")
                if locale:
                    context_options["locale"] = locale

                # Timezone
                timezone_id = self.config.get("timezone_id", "")
                if timezone_id:
                    context_options["timezone_id"] = timezone_id

                # Color scheme
                color_scheme = self.config.get("color_scheme", "light")
                if color_scheme and color_scheme != "light":
                    context_options["color_scheme"] = color_scheme

                # HTTPS errors
                if self.config.get("ignore_https_errors", False):
                    context_options["ignore_https_errors"] = True

                # Proxy
                proxy_server = self.config.get("proxy_server", "")
                if proxy_server:
                    context_options["proxy"] = {"server": proxy_server}

                logger.debug(f"Browser context options: {context_options}")

                # Create initial tab automatically with context options
                browser_context = await browser.new_context(**context_options)
                context.add_browser_context(browser_context)  # Track for cleanup
                page = await browser_context.new_page()

                # Navigate to URL if provided
                # Check input port first, then config
                url = self.get_input_value("url")
                if url is None:
                    # Only use config if no input connection exists
                    url = self.config.get("url", "")

                # Strip whitespace and normalize to empty string if None or whitespace-only
                url = url.strip() if url else ""

                # Resolve {{variable}} patterns in URL using context variables
                url = context.resolve_value(url)
                logger.debug(f"LaunchBrowserNode URL after variable resolution: '{url}'")

                if url:
                    # Add protocol if missing
                    if not url.startswith(("http://", "https://", "file://", "about:")):
                        url = f"https://{url}"
                    logger.info(f"Navigating to URL: {url}")
                    await page.goto(url)
                else:
                    logger.info("Opening blank page")
                    await page.goto("about:blank")

                # Store page in context
                tab_name = "main"
                context.add_page(page, tab_name)
                context.set_active_page(page, tab_name)

                # Set outputs
                self.set_output_value("browser", browser)
                self.set_output_value("page", page)

                self.status = NodeStatus.SUCCESS
                logger.info(f"Browser launched successfully: {browser_type} with initial tab (attempt {attempts})")

                return {
                    "success": True,
                    "data": {
                        "browser": browser,
                        "page": page,
                        "browser_type": browser_type,
                        "headless": headless,
                        "attempts": attempts
                    },
                    "next_nodes": ["exec_out"]
                }

            except Exception as e:
                last_error = e
                if attempts < max_attempts:
                    logger.warning(f"Browser launch failed (attempt {attempts}): {e}")
                    await asyncio.sleep(retry_interval / 1000)
                else:
                    break

        # All retries exhausted
        self.status = NodeStatus.ERROR
        logger.error(f"Failed to launch browser after {attempts} attempts: {last_error}")
        return {
            "success": False,
            "error": str(last_error),
            "next_nodes": []
        }

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        browser_type = self.config.get("browser_type", "")
        if browser_type not in ["chromium", "firefox", "webkit"]:
            return False, f"Invalid browser type: {browser_type}"
        return True, ""


class CloseBrowserNode(BaseNode):
    """
    Close browser node - closes the browser instance.

    Properly closes the browser and cleans up resources.
    """

    def __init__(self, node_id: str, name: str = "Close Browser", **kwargs) -> None:
        """
        Initialize close browser node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
        """
        # Default config with close options
        default_config = {
            "timeout": 30000,  # Timeout for close operation in ms
            "force_close": False,  # Force close even if pages have unsaved changes
            "retry_count": 0,  # Number of retries on failure
            "retry_interval": 1000,  # Delay between retries in ms
        }

        config = kwargs.get("config", {})
        # Merge with defaults
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        super().__init__(node_id, config)
        self.name = name
        self.node_type = "CloseBrowserNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("browser", PortType.INPUT, DataType.BROWSER)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
    
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute browser close.

        Args:
            context: Execution context for the workflow

        Returns:
            Success result
        """
        self.status = NodeStatus.RUNNING

        # Helper to safely parse int values with defaults
        def safe_int(value, default: int) -> int:
            if value is None or value == "":
                return default
            try:
                return int(value)
            except (ValueError, TypeError):
                return default

        try:
            # Get browser from input or context
            browser = self.get_input_value("browser")
            if browser is None:
                browser = context.browser

            if browser is None:
                raise ValueError("No browser instance found to close")

            # Get retry options
            retry_count = safe_int(self.config.get("retry_count"), 0)
            retry_interval = safe_int(self.config.get("retry_interval"), 1000)

            logger.info("Closing browser")

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(f"Retry attempt {attempts - 1}/{retry_count} for browser close")

                    # Close browser
                    await browser.close()

                    # Clear from context
                    context.browser = None
                    context.clear_pages()

                    self.status = NodeStatus.SUCCESS
                    logger.info(f"Browser closed successfully (attempt {attempts})")

                    return {
                        "success": True,
                        "data": {"message": "Browser closed", "attempts": attempts},
                        "next_nodes": ["exec_out"]
                    }

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(f"Browser close failed (attempt {attempts}): {e}")
                        await asyncio.sleep(retry_interval / 1000)
                    else:
                        break

            raise last_error

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to close browser: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        return True, ""


class NewTabNode(BaseNode):
    """
    New tab node - creates a new browser tab/page.

    Opens a new tab in the browser and optionally sets it as active.
    """

    def __init__(
        self,
        node_id: str,
        name: str = "New Tab",
        tab_name: str = "main",
        **kwargs
    ) -> None:
        """
        Initialize new tab node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            tab_name: Name to identify this tab
        """
        # Default config with all options
        default_config = {
            "tab_name": tab_name,
            "url": "",  # Optional URL to navigate to after creating tab
            "timeout": 30000,  # Navigation timeout in ms
            "wait_until": "load",  # Navigation wait event
            "retry_count": 0,  # Number of retries on failure
            "retry_interval": 1000,  # Delay between retries in ms
            "screenshot_on_fail": False,  # Take screenshot on failure
            "screenshot_path": "",  # Path for failure screenshot
        }

        config = kwargs.get("config", {})
        # Merge with defaults
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        super().__init__(node_id, config)
        self.name = name
        self.node_type = "NewTabNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("browser", PortType.INPUT, DataType.BROWSER, required=False)  # Optional: uses context browser if not connected
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("page", PortType.OUTPUT, DataType.PAGE)
    
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute new tab creation.

        Args:
            context: Execution context for the workflow

        Returns:
            Result with new page instance
        """
        self.status = NodeStatus.RUNNING

        try:
            # Get browser from input or context
            browser = self.get_input_value("browser")
            if browser is None:
                browser = context.browser

            if browser is None:
                raise ValueError("No browser instance found")

            tab_name = self.config.get("tab_name", "main")
            url = self.config.get("url", "")

            # Helper to safely parse int values with defaults
            def safe_int(value, default: int) -> int:
                if value is None or value == "":
                    return default
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return default

            # Safely parse timeout
            timeout = safe_int(self.config.get("timeout"), 30000)
            wait_until = self.config.get("wait_until", "load")

            # Get retry options
            retry_count = safe_int(self.config.get("retry_count"), 0)
            retry_interval = safe_int(self.config.get("retry_interval"), 1000)
            screenshot_on_fail = self.config.get("screenshot_on_fail", False)
            screenshot_path = self.config.get("screenshot_path", "")

            logger.info(f"Creating new tab: {tab_name}")

            last_error = None
            attempts = 0
            max_attempts = retry_count + 1
            page = None

            while attempts < max_attempts:
                try:
                    attempts += 1
                    if attempts > 1:
                        logger.info(f"Retry attempt {attempts - 1}/{retry_count} for new tab")

                    # Create new context and page
                    browser_context = await browser.new_context()
                    context.add_browser_context(browser_context)  # Track for cleanup
                    page = await browser_context.new_page()

                    # Navigate to URL if specified
                    if url and url.strip():
                        nav_url = url.strip()
                        # Resolve {{variable}} patterns in URL
                        nav_url = context.resolve_value(nav_url)
                        logger.debug(f"NewTabNode URL after variable resolution: '{nav_url}'")
                        # Add protocol if missing
                        if not nav_url.startswith(("http://", "https://", "file://", "about:")):
                            nav_url = f"https://{nav_url}"
                        logger.info(f"Navigating new tab to: {nav_url}")
                        await page.goto(nav_url, timeout=timeout, wait_until=wait_until)

                    # Store page in context
                    context.add_page(page, tab_name)
                    context.set_active_page(page, tab_name)

                    # Set output
                    self.set_output_value("page", page)

                    self.status = NodeStatus.SUCCESS
                    logger.info(f"Tab created successfully: {tab_name} (attempt {attempts})")

                    return {
                        "success": True,
                        "data": {
                            "tab_name": tab_name,
                            "page": page,
                            "url": url if url else "about:blank",
                            "attempts": attempts
                        },
                        "next_nodes": ["exec_out"]
                    }

                except Exception as e:
                    last_error = e
                    if attempts < max_attempts:
                        logger.warning(f"New tab creation failed (attempt {attempts}): {e}")
                        await asyncio.sleep(retry_interval / 1000)
                    else:
                        break

            # All attempts failed - take screenshot if requested
            if screenshot_on_fail and page:
                try:
                    import os
                    from datetime import datetime
                    if screenshot_path:
                        path = screenshot_path
                    else:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        path = f"new_tab_fail_{timestamp}.png"

                    dir_path = os.path.dirname(path)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)

                    await page.screenshot(path=path)
                    logger.info(f"Failure screenshot saved: {path}")
                except Exception as ss_error:
                    logger.warning(f"Failed to take screenshot: {ss_error}")

            raise last_error

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to create tab: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }

    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        tab_name = self.config.get("tab_name", "")
        if not tab_name:
            return False, "Tab name cannot be empty"
        return True, ""


class GetAllImagesNode(BaseNode):
    """
    Get all images from the current page.

    Extracts all image URLs (from <img> tags and CSS background images)
    from the current page. Can filter by minimum size and file type.

    Config:
        - min_width: Minimum image width in pixels (0 = no filter)
        - min_height: Minimum image height in pixels (0 = no filter)
        - include_backgrounds: Include CSS background images
        - file_types: Comma-separated file extensions to include (empty = all)

    Outputs:
        - images: List of image URLs
        - count: Number of images found
    """

    def __init__(
        self,
        node_id: str,
        name: str = "Get All Images",
        **kwargs
    ) -> None:
        default_config = {
            "min_width": 0,
            "min_height": 0,
            "include_backgrounds": True,
            "file_types": "",  # e.g., "jpg,png,webp"
        }
        config = kwargs.get("config", {})
        merged_config = {**default_config, **config}
        super().__init__(node_id, merged_config)
        self.name = name
        self.node_type = "GetAllImagesNode"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("images", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Extract all image URLs from the page."""
        try:
            page = context.get_active_page()
            if not page:
                raise ValueError("No active page. Launch browser and navigate first.")

            # Handle empty strings from UI text inputs gracefully
            min_width = int(self.config.get("min_width") or 0)
            min_height = int(self.config.get("min_height") or 0)
            include_backgrounds = self.config.get("include_backgrounds", True)
            file_types_str = self.config.get("file_types") or ""

            # Parse allowed file types
            allowed_types = []
            if file_types_str:
                allowed_types = [f".{t.strip().lower().lstrip('.')}" for t in file_types_str.split(",")]

            # JavaScript to extract all images
            js_code = """
            (includeBackgrounds) => {
                const images = [];
                const seen = new Set();

                // Get all <img> elements
                document.querySelectorAll('img').forEach(img => {
                    const src = img.src || img.dataset.src || img.getAttribute('data-lazy-src');
                    if (src && !seen.has(src)) {
                        seen.add(src);
                        images.push({
                            url: src,
                            width: img.naturalWidth || img.width || 0,
                            height: img.naturalHeight || img.height || 0,
                            alt: img.alt || '',
                            type: 'img'
                        });
                    }
                });

                // Get <source> elements in <picture>
                document.querySelectorAll('picture source').forEach(source => {
                    const srcset = source.srcset;
                    if (srcset) {
                        // Parse srcset and get the largest image
                        const urls = srcset.split(',').map(s => s.trim().split(' ')[0]);
                        urls.forEach(url => {
                            if (url && !seen.has(url)) {
                                seen.add(url);
                                images.push({
                                    url: url,
                                    width: 0,
                                    height: 0,
                                    alt: '',
                                    type: 'source'
                                });
                            }
                        });
                    }
                });

                // Get CSS background images if requested
                if (includeBackgrounds) {
                    const elements = document.querySelectorAll('*');
                    elements.forEach(el => {
                        const style = window.getComputedStyle(el);
                        const bgImage = style.backgroundImage;
                        if (bgImage && bgImage !== 'none') {
                            const match = bgImage.match(/url\\(['"]?([^'"\\)]+)['"]?\\)/);
                            if (match && match[1] && !seen.has(match[1])) {
                                seen.add(match[1]);
                                images.push({
                                    url: match[1],
                                    width: 0,
                                    height: 0,
                                    alt: '',
                                    type: 'background'
                                });
                            }
                        }
                    });
                }

                return images;
            }
            """

            # Execute JavaScript
            all_images = await page.evaluate(js_code, include_backgrounds)

            # Filter by size and file type
            filtered_images = []
            for img in all_images:
                url = img.get("url", "")
                if not url or url.startswith("data:"):
                    continue

                # Check size filter
                width = img.get("width", 0)
                height = img.get("height", 0)
                if min_width > 0 and width < min_width:
                    continue
                if min_height > 0 and height < min_height:
                    continue

                # Check file type filter
                if allowed_types:
                    url_lower = url.lower().split("?")[0]  # Remove query params
                    if not any(url_lower.endswith(ext) for ext in allowed_types):
                        continue

                filtered_images.append(url)

            # Set outputs
            self.set_output_value("images", filtered_images)
            self.set_output_value("count", len(filtered_images))

            self.status = NodeStatus.SUCCESS
            logger.info(f"Found {len(filtered_images)} images on page")

            return {
                "success": True,
                "data": {
                    "images": filtered_images,
                    "count": len(filtered_images)
                },
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to get images: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


class DownloadFileNode(BaseNode):
    """
    Download a file from URL to local path.

    Downloads any file (image, document, etc.) from a URL and saves it
    to a local file path. Supports both direct URL downloads and
    downloading through the browser context for authenticated sessions.

    Config:
        - save_path: Local file path to save to (supports {{variables}})
        - use_browser: Use browser context for download (for authenticated sites)
        - timeout: Download timeout in milliseconds
        - overwrite: Overwrite existing file if it exists

    Inputs:
        - url: URL of the file to download
        - filename: Optional filename override

    Outputs:
        - path: Full path where file was saved
        - size: File size in bytes
        - success: Whether download succeeded
    """

    def __init__(
        self,
        node_id: str,
        name: str = "Download File",
        **kwargs
    ) -> None:
        default_config = {
            "save_path": "",  # Directory or full path
            "use_browser": False,
            "timeout": 30000,
            "overwrite": True,
        }
        config = kwargs.get("config", {})
        merged_config = {**default_config, **config}
        super().__init__(node_id, merged_config)
        self.name = name
        self.node_type = "DownloadFileNode"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_input_port("url", PortType.INPUT, DataType.STRING)
        self.add_input_port("filename", PortType.INPUT, DataType.STRING)
        self.add_output_port("path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("size", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Download file from URL."""
        import os
        import urllib.request
        import ssl
        from urllib.parse import urlparse, unquote

        try:
            url = self.get_input_value("url")
            filename_override = self.get_input_value("filename")

            # Resolve variables
            if hasattr(context, 'resolve_value'):
                if url:
                    url = context.resolve_value(url)
                if filename_override:
                    filename_override = context.resolve_value(filename_override)

            if not url:
                raise ValueError("URL is required")

            save_path = self.config.get("save_path", "")
            if hasattr(context, 'resolve_value') and save_path:
                save_path = context.resolve_value(save_path)

            use_browser = self.config.get("use_browser", False)
            timeout = int(self.config.get("timeout", 30000))
            overwrite = self.config.get("overwrite", True)

            # Determine filename
            if filename_override:
                filename = filename_override
            else:
                # Extract filename from URL
                parsed = urlparse(url)
                filename = os.path.basename(unquote(parsed.path))
                if not filename or '.' not in filename:
                    # Generate a filename based on URL hash
                    import hashlib
                    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                    # Try to guess extension from URL
                    ext = ".jpg"  # Default
                    url_lower = url.lower()
                    for e in [".png", ".gif", ".webp", ".svg", ".jpeg", ".bmp"]:
                        if e in url_lower:
                            ext = e
                            break
                    filename = f"download_{url_hash}{ext}"

            # Determine full save path
            if save_path:
                if os.path.isdir(save_path):
                    full_path = os.path.join(save_path, filename)
                else:
                    # save_path is the full file path
                    full_path = save_path
            else:
                # Default to downloads folder
                downloads_dir = os.path.expanduser("~/Downloads")
                os.makedirs(downloads_dir, exist_ok=True)
                full_path = os.path.join(downloads_dir, filename)

            # Create directory if needed
            dir_path = os.path.dirname(full_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            # Check if file exists
            if os.path.exists(full_path) and not overwrite:
                # Add number suffix
                base, ext = os.path.splitext(full_path)
                counter = 1
                while os.path.exists(f"{base}_{counter}{ext}"):
                    counter += 1
                full_path = f"{base}_{counter}{ext}"

            file_size = 0

            if use_browser:
                # Download using browser context (for authenticated sessions)
                page = context.get_active_page()
                if not page:
                    raise ValueError("No active page for browser download")

                # Use page.request to download
                response = await page.request.get(url, timeout=timeout)
                content = await response.body()

                with open(full_path, 'wb') as f:
                    f.write(content)
                file_size = len(content)
            else:
                # Direct download using urllib (run in executor to not block)
                import asyncio

                def download_file():
                    # Create SSL context that doesn't verify (for flexibility)
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE

                    req = urllib.request.Request(
                        url,
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                    )
                    with urllib.request.urlopen(req, timeout=timeout/1000, context=ctx) as response:
                        content = response.read()
                        with open(full_path, 'wb') as f:
                            f.write(content)
                        return len(content)

                loop = asyncio.get_event_loop()
                file_size = await loop.run_in_executor(None, download_file)

            # Set outputs
            self.set_output_value("path", full_path)
            self.set_output_value("size", file_size)
            self.set_output_value("success", True)

            self.status = NodeStatus.SUCCESS
            logger.info(f"Downloaded {url} to {full_path} ({file_size} bytes)")

            return {
                "success": True,
                "data": {
                    "path": full_path,
                    "size": file_size,
                    "url": url
                },
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            self.set_output_value("success", False)
            logger.error(f"Failed to download file: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }

