"""
CasareRPA - E2E Test Fixtures.

Real fixtures for end-to-end testing with actual execution (no mocks).

Fixtures:
- real_execution_context: Real ExecutionContext instance
- temp_workspace: Temporary directory for file tests
- test_server: pytest-aiohttp server for browser tests
- browser_context: Real headless Playwright browser
"""

import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Generator, Optional

import pytest
import pytest_asyncio

# Real imports from application (NOT mocked)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.domain.value_objects.types import ExecutionMode


# =============================================================================
# REAL EXECUTION CONTEXT
# =============================================================================


@pytest_asyncio.fixture
async def real_execution_context() -> AsyncGenerator[ExecutionContext, None]:
    """
    Create a REAL ExecutionContext for E2E testing.

    Unlike unit test fixtures, this is NOT mocked. It provides:
    - Real variable storage and resolution
    - Real browser resource management (when browser_context fixture used)
    - Real execution state tracking

    Usage:
        @pytest.mark.asyncio
        async def test_workflow(real_execution_context):
            real_execution_context.set_variable("counter", 0)
            # Execute real nodes...

    Yields:
        Real ExecutionContext with async cleanup.
    """
    context = ExecutionContext(
        workflow_name="E2E Test Workflow",
        mode=ExecutionMode.NORMAL,
        initial_variables={},
        project_context=None,
    )

    try:
        yield context
    finally:
        # Ensure proper cleanup
        await context.cleanup()


@pytest_asyncio.fixture
async def real_execution_context_with_variables() -> (
    AsyncGenerator[ExecutionContext, None]
):
    """
    Create a real ExecutionContext pre-populated with test variables.

    Pre-set variables:
    - test_string: "hello"
    - test_number: 42
    - test_list: [1, 2, 3]
    - test_dict: {"key": "value"}
    - counter: 0

    Yields:
        Real ExecutionContext with pre-populated variables.
    """
    context = ExecutionContext(
        workflow_name="E2E Test Workflow",
        mode=ExecutionMode.NORMAL,
        initial_variables={
            "test_string": "hello",
            "test_number": 42,
            "test_list": [1, 2, 3],
            "test_dict": {"key": "value"},
            "counter": 0,
        },
        project_context=None,
    )

    try:
        yield context
    finally:
        await context.cleanup()


# =============================================================================
# TEMPORARY WORKSPACE
# =============================================================================


@pytest.fixture
def temp_workspace() -> Generator[Path, None, None]:
    """
    Create a temporary directory for file operation tests.

    The directory is automatically cleaned up after the test.

    Usage:
        def test_file_write(temp_workspace):
            file_path = temp_workspace / "output.txt"
            # Test file operations...

    Yields:
        Path to temporary directory.
    """
    temp_dir = tempfile.mkdtemp(prefix="casare_e2e_")
    workspace = Path(temp_dir)

    try:
        yield workspace
    finally:
        # Clean up after test
        if workspace.exists():
            shutil.rmtree(workspace, ignore_errors=True)


@pytest.fixture
def temp_file(temp_workspace: Path) -> Generator[Path, None, None]:
    """
    Create a temporary file within the workspace.

    Usage:
        def test_read_file(temp_file):
            temp_file.write_text("test content")
            # Test reading...

    Yields:
        Path to temporary file.
    """
    file_path = temp_workspace / "test_file.txt"
    file_path.touch()

    yield file_path

    # Cleanup handled by temp_workspace


# =============================================================================
# TEST SERVER FOR BROWSER TESTS (pytest-aiohttp)
# =============================================================================


@pytest.fixture
def test_pages_dir() -> Path:
    """
    Get path to the test pages directory.

    Returns:
        Path to tests/e2e/fixtures/test_pages/
    """
    return Path(__file__).parent / "fixtures" / "test_pages"


@pytest.fixture
def aiohttp_server_handler(test_pages_dir: Path):
    """
    Create aiohttp request handler for serving test pages.

    Serves static HTML files from the test_pages directory.

    Usage with pytest-aiohttp:
        async def test_browser(test_server):
            page.goto(test_server.make_url("/form.html"))
    """
    from aiohttp import web

    async def handle_static(request: web.Request) -> web.Response:
        """Serve static files from test_pages directory."""
        path = request.match_info.get("path", "index.html")

        # Security: prevent path traversal
        if ".." in path:
            raise web.HTTPForbidden()

        file_path = test_pages_dir / path

        if not file_path.exists():
            raise web.HTTPNotFound(text=f"File not found: {path}")

        # Determine content type
        suffix = file_path.suffix.lower()
        content_types = {
            ".html": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".svg": "image/svg+xml",
        }
        content_type = content_types.get(suffix, "text/plain")

        content = file_path.read_bytes()
        return web.Response(body=content, content_type=content_type)

    return handle_static


@pytest_asyncio.fixture
async def test_server(aiohttp_server_handler, aiohttp_server):
    """
    Create a test HTTP server for browser tests.

    Uses pytest-aiohttp to create a real HTTP server serving test pages.

    Usage:
        @pytest.mark.asyncio
        async def test_form_fill(test_server, browser_context):
            page = browser_context.pages[0]
            await page.goto(test_server.make_url("/form.html"))
            await page.fill("#name", "Test User")

    Yields:
        aiohttp TestServer instance with make_url() method.
    """
    from aiohttp import web

    app = web.Application()
    app.router.add_get("/{path:.*}", aiohttp_server_handler)
    app.router.add_get("/", aiohttp_server_handler)

    server = await aiohttp_server(app)
    yield server


# =============================================================================
# PLAYWRIGHT BROWSER FIXTURES
# =============================================================================


@pytest_asyncio.fixture
async def browser_instance():
    """
    Create a real headless Playwright browser instance.

    This creates a Chromium browser in headless mode for E2E testing.
    The browser is shared across tests in the same session for performance.

    Yields:
        Playwright Browser instance.
    """
    from playwright.async_api import async_playwright

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)

    try:
        yield browser
    finally:
        await browser.close()
        await playwright.stop()


@pytest_asyncio.fixture
async def browser_context(browser_instance) -> AsyncGenerator[Any, None]:
    """
    Create a new browser context for each test.

    Each test gets a fresh browser context (isolated cookies, storage, etc.)
    but shares the underlying browser instance.

    Usage:
        @pytest.mark.asyncio
        async def test_navigation(browser_context):
            page = await browser_context.new_page()
            await page.goto("https://example.com")
            assert "Example" in await page.title()

    Yields:
        Playwright BrowserContext instance.
    """
    context = await browser_instance.new_context()

    try:
        yield context
    finally:
        await context.close()


@pytest_asyncio.fixture
async def browser_page(browser_context) -> AsyncGenerator[Any, None]:
    """
    Create a new page in the browser context.

    Convenience fixture that provides a ready-to-use page.

    Usage:
        @pytest.mark.asyncio
        async def test_click(browser_page):
            await browser_page.goto("https://example.com")
            await browser_page.click("a")

    Yields:
        Playwright Page instance.
    """
    page = await browser_context.new_page()

    try:
        yield page
    finally:
        await page.close()


@pytest_asyncio.fixture
async def real_context_with_browser(
    real_execution_context: ExecutionContext,
    browser_instance,
    browser_context,
    browser_page,
) -> AsyncGenerator[ExecutionContext, None]:
    """
    Create an ExecutionContext with real Playwright browser attached.

    This is the fixture to use for browser automation E2E tests.

    Usage:
        @pytest.mark.asyncio
        async def test_browser_workflow(real_context_with_browser):
            context = real_context_with_browser
            page = context.get_active_page()
            await page.goto("https://example.com")

    Yields:
        ExecutionContext with browser, context, and page configured.
    """
    real_execution_context.set_browser(browser_instance)
    real_execution_context.add_browser_context(browser_context)
    real_execution_context.set_active_page(browser_page, "default")

    yield real_execution_context


# =============================================================================
# WORKFLOW EXECUTION TIMEOUT
# =============================================================================

# Default timeout for E2E workflow tests (30 seconds)
E2E_WORKFLOW_TIMEOUT = 30.0


@pytest.fixture
def workflow_timeout() -> float:
    """
    Get the default workflow execution timeout.

    Can be overridden per-test by using pytest.mark.timeout.

    Returns:
        Timeout in seconds (default: 30.0)
    """
    return E2E_WORKFLOW_TIMEOUT


# =============================================================================
# PYTEST MARKERS
# =============================================================================


def pytest_configure(config):
    """Register custom pytest markers for E2E tests."""
    config.addinivalue_line(
        "markers",
        "e2e: mark test as end-to-end test (may be slow, uses real resources)",
    )
    config.addinivalue_line(
        "markers",
        "browser: mark test as requiring browser (Playwright)",
    )
    config.addinivalue_line(
        "markers",
        "network: mark test as requiring network access",
    )
