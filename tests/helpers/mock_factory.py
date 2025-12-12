"""
CasareRPA - Mock Factory.

Provides pre-built mock objects for common external resources.
Reduces boilerplate in tests by providing realistic mock behavior.

Usage:
    # Browser mocks
    mock_page = MockFactory.mock_page()
    mock_browser = MockFactory.mock_browser()
    mock_context = MockFactory.mock_browser_context()

    # HTTP mocks
    mock_response = MockFactory.mock_http_response(status=200, json={'ok': True})

    # Database mocks
    mock_conn = MockFactory.mock_database_connection()

    # File system mocks
    mock_file = MockFactory.mock_file_handle()
"""

from typing import Any, Dict, List, Optional, Union
from unittest.mock import AsyncMock, MagicMock, Mock, PropertyMock


class MockFactory:
    """
    Factory for creating realistic mock objects.

    Mocks are designed to match the behavior of real objects
    so tests remain valid even when implementations change.
    """

    # =========================================================================
    # Browser Mocks (Playwright)
    # =========================================================================

    @staticmethod
    def mock_page(
        url: str = "https://example.com",
        title: str = "Example Page",
        content: str = "<html><body>Hello</body></html>",
    ) -> AsyncMock:
        """
        Create a mock Playwright Page object.

        Args:
            url: Initial URL to return from page.url
            title: Page title to return from page.title()
            content: HTML content to return from page.content()

        Returns:
            AsyncMock configured as Playwright Page

        Example:
            mock_page = MockFactory.mock_page(url='https://example.com')
            context.set_active_page(mock_page, 'default')
        """
        mock = AsyncMock()

        # Properties
        mock.url = url

        # Navigation
        mock.goto = AsyncMock(return_value=None)
        mock.reload = AsyncMock(return_value=None)
        mock.go_back = AsyncMock(return_value=None)
        mock.go_forward = AsyncMock(return_value=None)

        # Content
        mock.title = AsyncMock(return_value=title)
        mock.content = AsyncMock(return_value=content)

        # Selectors
        mock.query_selector = AsyncMock(return_value=None)
        mock.query_selector_all = AsyncMock(return_value=[])
        mock.wait_for_selector = AsyncMock(return_value=None)

        # Actions
        mock.click = AsyncMock()
        mock.fill = AsyncMock()
        mock.type = AsyncMock()
        mock.press = AsyncMock()
        mock.check = AsyncMock()
        mock.uncheck = AsyncMock()
        mock.select_option = AsyncMock(return_value=[])

        # Evaluation
        mock.evaluate = AsyncMock(return_value=None)
        mock.evaluate_handle = AsyncMock(return_value=None)

        # Screenshots/PDF
        mock.screenshot = AsyncMock(return_value=b"fake_screenshot")
        mock.pdf = AsyncMock(return_value=b"fake_pdf")

        # Wait functions
        mock.wait_for_load_state = AsyncMock()
        mock.wait_for_timeout = AsyncMock()
        mock.wait_for_url = AsyncMock()
        mock.wait_for_function = AsyncMock()

        # Input
        mock.keyboard = MagicMock()
        mock.keyboard.press = AsyncMock()
        mock.keyboard.type = AsyncMock()
        mock.mouse = MagicMock()
        mock.mouse.click = AsyncMock()
        mock.mouse.move = AsyncMock()

        # Frames
        mock.frames = []
        mock.main_frame = mock

        # Lifecycle
        mock.close = AsyncMock()
        mock.is_closed = Mock(return_value=False)

        return mock

    @staticmethod
    def mock_element(
        visible: bool = True,
        enabled: bool = True,
        text: str = "Element text",
        tag_name: str = "div",
    ) -> AsyncMock:
        """
        Create a mock Playwright ElementHandle.

        Args:
            visible: Whether element is visible
            enabled: Whether element is enabled
            text: Text content of element
            tag_name: HTML tag name

        Returns:
            AsyncMock configured as Playwright ElementHandle
        """
        mock = AsyncMock()

        mock.is_visible = AsyncMock(return_value=visible)
        mock.is_enabled = AsyncMock(return_value=enabled)
        mock.is_disabled = AsyncMock(return_value=not enabled)
        mock.is_checked = AsyncMock(return_value=False)
        mock.text_content = AsyncMock(return_value=text)
        mock.inner_text = AsyncMock(return_value=text)
        mock.inner_html = AsyncMock(return_value=f"<{tag_name}>{text}</{tag_name}>")
        mock.get_attribute = AsyncMock(return_value=None)

        mock.click = AsyncMock()
        mock.fill = AsyncMock()
        mock.type = AsyncMock()
        mock.check = AsyncMock()
        mock.uncheck = AsyncMock()
        mock.focus = AsyncMock()
        mock.scroll_into_view_if_needed = AsyncMock()

        mock.bounding_box = AsyncMock(
            return_value={"x": 100, "y": 100, "width": 200, "height": 50}
        )
        mock.screenshot = AsyncMock(return_value=b"fake_screenshot")

        return mock

    @staticmethod
    def mock_browser() -> AsyncMock:
        """
        Create a mock Playwright Browser object.

        Returns:
            AsyncMock configured as Playwright Browser
        """
        mock = AsyncMock()

        mock.new_context = AsyncMock(return_value=MockFactory.mock_browser_context())
        mock.new_page = AsyncMock(return_value=MockFactory.mock_page())
        mock.contexts = []
        mock.close = AsyncMock()
        mock.is_connected = Mock(return_value=True)

        return mock

    @staticmethod
    def mock_browser_context() -> AsyncMock:
        """
        Create a mock Playwright BrowserContext object.

        Returns:
            AsyncMock configured as Playwright BrowserContext
        """
        mock = AsyncMock()

        mock.new_page = AsyncMock(return_value=MockFactory.mock_page())
        mock.pages = []
        mock.close = AsyncMock()
        mock.cookies = AsyncMock(return_value=[])
        mock.add_cookies = AsyncMock()
        mock.clear_cookies = AsyncMock()
        mock.storage_state = AsyncMock(return_value={})

        return mock

    # =========================================================================
    # HTTP Mocks
    # =========================================================================

    @staticmethod
    def mock_http_response(
        status: int = 200,
        json: Optional[Dict[str, Any]] = None,
        text: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        raise_for_status: bool = False,
    ) -> AsyncMock:
        """
        Create a mock aiohttp response object.

        Args:
            status: HTTP status code
            json: JSON response body
            text: Text response body
            headers: Response headers
            raise_for_status: Whether raise_for_status should raise

        Returns:
            AsyncMock configured as aiohttp ClientResponse
        """
        mock = AsyncMock()

        mock.status = status
        mock.headers = headers or {"Content-Type": "application/json"}

        if json is not None:
            mock.json = AsyncMock(return_value=json)
            mock.text = AsyncMock(return_value=str(json))
        elif text is not None:
            mock.text = AsyncMock(return_value=text)
            mock.json = AsyncMock(side_effect=ValueError("Not JSON"))
        else:
            mock.json = AsyncMock(return_value={})
            mock.text = AsyncMock(return_value="")

        mock.read = AsyncMock(return_value=b"")

        if raise_for_status and status >= 400:
            from aiohttp import ClientResponseError

            mock.raise_for_status = Mock(
                side_effect=ClientResponseError(
                    request_info=MagicMock(),
                    history=(),
                    status=status,
                )
            )
        else:
            mock.raise_for_status = Mock()

        # Context manager support
        mock.__aenter__ = AsyncMock(return_value=mock)
        mock.__aexit__ = AsyncMock(return_value=False)

        return mock

    @staticmethod
    def mock_http_client(
        default_response: Optional[AsyncMock] = None,
    ) -> AsyncMock:
        """
        Create a mock HTTP client (aiohttp ClientSession-like).

        Args:
            default_response: Default response for all requests

        Returns:
            AsyncMock configured as HTTP client
        """
        mock = AsyncMock()

        if default_response is None:
            default_response = MockFactory.mock_http_response()

        mock.get = AsyncMock(return_value=default_response)
        mock.post = AsyncMock(return_value=default_response)
        mock.put = AsyncMock(return_value=default_response)
        mock.patch = AsyncMock(return_value=default_response)
        mock.delete = AsyncMock(return_value=default_response)
        mock.head = AsyncMock(return_value=default_response)
        mock.options = AsyncMock(return_value=default_response)
        mock.request = AsyncMock(return_value=default_response)

        mock.close = AsyncMock()

        # Context manager support
        mock.__aenter__ = AsyncMock(return_value=mock)
        mock.__aexit__ = AsyncMock(return_value=False)

        return mock

    # =========================================================================
    # Database Mocks
    # =========================================================================

    @staticmethod
    def mock_database_connection(
        rows: Optional[List[Dict[str, Any]]] = None,
        row_count: int = 0,
    ) -> AsyncMock:
        """
        Create a mock asyncpg database connection.

        Args:
            rows: Default rows to return from fetch operations
            row_count: Number of rows affected by execute

        Returns:
            AsyncMock configured as asyncpg Connection
        """
        mock = AsyncMock()

        rows = rows or []

        mock.fetch = AsyncMock(return_value=rows)
        mock.fetchrow = AsyncMock(return_value=rows[0] if rows else None)
        mock.fetchval = AsyncMock(return_value=rows[0] if rows else None)
        mock.execute = AsyncMock(return_value=f"UPDATE {row_count}")
        mock.executemany = AsyncMock()

        mock.close = AsyncMock()
        mock.is_closed = Mock(return_value=False)

        # Transaction support
        mock.transaction = MagicMock()
        mock.transaction.return_value.__aenter__ = AsyncMock()
        mock.transaction.return_value.__aexit__ = AsyncMock()

        return mock

    @staticmethod
    def mock_database_pool(
        connection: Optional[AsyncMock] = None,
    ) -> AsyncMock:
        """
        Create a mock asyncpg connection pool.

        Args:
            connection: Connection mock to return from acquire

        Returns:
            AsyncMock configured as asyncpg Pool
        """
        mock = AsyncMock()

        if connection is None:
            connection = MockFactory.mock_database_connection()

        mock.acquire = AsyncMock(return_value=connection)
        mock.release = AsyncMock()
        mock.close = AsyncMock()
        mock.terminate = Mock()

        # Context manager for acquire
        mock.acquire.return_value.__aenter__ = AsyncMock(return_value=connection)
        mock.acquire.return_value.__aexit__ = AsyncMock()

        return mock

    # =========================================================================
    # File System Mocks
    # =========================================================================

    @staticmethod
    def mock_file_handle(
        content: Union[str, bytes] = "",
        name: str = "test_file.txt",
    ) -> AsyncMock:
        """
        Create a mock aiofiles file handle.

        Args:
            content: File content to return from read
            name: File name

        Returns:
            AsyncMock configured as aiofiles file handle
        """
        mock = AsyncMock()

        mock.name = name

        if isinstance(content, bytes):
            mock.read = AsyncMock(return_value=content)
            mock.write = AsyncMock(return_value=len(content))
        else:
            mock.read = AsyncMock(return_value=content)
            mock.write = AsyncMock(return_value=len(content))
            mock.readline = AsyncMock(
                return_value=content.split("\n")[0] if content else ""
            )
            mock.readlines = AsyncMock(
                return_value=content.split("\n") if content else []
            )

        mock.seek = AsyncMock()
        mock.tell = AsyncMock(return_value=0)
        mock.close = AsyncMock()
        mock.flush = AsyncMock()

        # Context manager
        mock.__aenter__ = AsyncMock(return_value=mock)
        mock.__aexit__ = AsyncMock()

        return mock

    # =========================================================================
    # Desktop UI Mocks
    # =========================================================================

    @staticmethod
    def mock_ui_control(
        name: str = "Button",
        control_type: str = "Button",
        enabled: bool = True,
        visible: bool = True,
        automation_id: str = "",
    ) -> MagicMock:
        """
        Create a mock UIAutomation control element.

        Args:
            name: Control name
            control_type: Control type name
            enabled: Whether control is enabled
            visible: Whether control is visible
            automation_id: Automation ID

        Returns:
            MagicMock configured as UIAutomation Control
        """
        mock = MagicMock()

        mock.Name = name
        mock.ControlTypeName = control_type
        mock.ControlType = control_type
        mock.AutomationId = automation_id
        mock.IsEnabled = enabled
        mock.IsOffscreen = not visible
        mock.ProcessId = 12345
        mock.NativeWindowHandle = 0x12345

        # Bounding rectangle
        mock.BoundingRectangle = MagicMock()
        mock.BoundingRectangle.left = 100
        mock.BoundingRectangle.top = 100
        mock.BoundingRectangle.right = 300
        mock.BoundingRectangle.bottom = 150
        mock.BoundingRectangle.width = Mock(return_value=200)
        mock.BoundingRectangle.height = Mock(return_value=50)

        # Property access
        def get_property(prop_id: int) -> Any:
            prop_map = {
                30003: enabled,  # IsEnabled
                30005: name,  # Name
                30011: control_type,  # ControlType
                30012: automation_id,  # AutomationId
            }
            return prop_map.get(prop_id)

        mock.GetCurrentPropertyValue = Mock(side_effect=get_property)

        # Pattern support
        mock.GetPattern = Mock(return_value=None)
        mock.GetInvokePattern = Mock(return_value=MagicMock())
        mock.GetValuePattern = Mock(return_value=MagicMock())
        mock.GetSelectionPattern = Mock(return_value=None)

        # Child finding
        mock.FindAll = Mock(return_value=[])
        mock.FindFirst = Mock(return_value=None)

        # Actions
        mock.SetFocus = Mock()
        mock.Click = Mock()
        mock.SendKeys = Mock()

        return mock

    @staticmethod
    def mock_desktop_element(
        name: str = "Window",
        class_name: str = "ClassName",
        visible: bool = True,
        position: tuple = (100, 100, 800, 600),
    ) -> MagicMock:
        """
        Create a mock desktop window element.

        Args:
            name: Window title
            class_name: Window class name
            visible: Whether window is visible
            position: Window position (left, top, right, bottom)

        Returns:
            MagicMock configured as desktop element
        """
        mock = MagicMock()

        mock.Name = name
        mock.ClassName = class_name
        mock.IsVisible = visible
        mock.Left = position[0]
        mock.Top = position[1]
        mock.Right = position[2]
        mock.Bottom = position[3]
        mock.Width = position[2] - position[0]
        mock.Height = position[3] - position[1]

        mock.Close = Mock()
        mock.Minimize = Mock()
        mock.Maximize = Mock()
        mock.Restore = Mock()
        mock.SetFocus = Mock()
        mock.MoveTo = Mock()
        mock.Resize = Mock()

        return mock

    # =========================================================================
    # Email Mocks
    # =========================================================================

    @staticmethod
    def mock_smtp_client() -> AsyncMock:
        """
        Create a mock SMTP client.

        Returns:
            AsyncMock configured as SMTP client
        """
        mock = AsyncMock()

        mock.connect = AsyncMock()
        mock.login = AsyncMock()
        mock.sendmail = AsyncMock()
        mock.send_message = AsyncMock()
        mock.quit = AsyncMock()

        # Context manager
        mock.__aenter__ = AsyncMock(return_value=mock)
        mock.__aexit__ = AsyncMock()

        return mock

    @staticmethod
    def mock_imap_client(
        messages: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncMock:
        """
        Create a mock IMAP client.

        Args:
            messages: List of message dicts with 'subject', 'from', 'body'

        Returns:
            AsyncMock configured as IMAP client
        """
        mock = AsyncMock()

        mock.login = AsyncMock()
        mock.select = AsyncMock(return_value=(b"OK", [b"10"]))
        mock.search = AsyncMock(return_value=(b"OK", [b"1 2 3"]))
        mock.fetch = AsyncMock(return_value=(b"OK", [(b"1", b"message data")]))
        mock.logout = AsyncMock()

        # Context manager
        mock.__aenter__ = AsyncMock(return_value=mock)
        mock.__aexit__ = AsyncMock()

        return mock

    # =========================================================================
    # Credential Provider Mock
    # =========================================================================

    @staticmethod
    def mock_credential_provider(
        credentials: Optional[Dict[str, Any]] = None,
    ) -> AsyncMock:
        """
        Create a mock credential provider.

        Args:
            credentials: Dictionary mapping alias -> credential value

        Returns:
            AsyncMock configured as VaultCredentialProvider
        """
        mock = AsyncMock()

        credentials = credentials or {}

        async def get_credential(alias: str, required: bool = False) -> Optional[Any]:
            if alias in credentials:
                return credentials[alias]
            if required:
                raise ValueError(f"Credential '{alias}' not found")
            return None

        mock.initialize = AsyncMock()
        mock.get_credential = AsyncMock(side_effect=get_credential)
        mock.set_execution_context = Mock()
        mock.register_bindings = Mock()
        mock.shutdown = AsyncMock()

        return mock

    # =========================================================================
    # Execution Context Mock
    # =========================================================================

    @staticmethod
    def mock_execution_context(
        variables: Optional[Dict[str, Any]] = None,
        page: Optional[AsyncMock] = None,
        browser: Optional[AsyncMock] = None,
    ) -> MagicMock:
        """
        Create a mock ExecutionContext.

        Args:
            variables: Initial variables
            page: Mock page to attach
            browser: Mock browser to attach

        Returns:
            MagicMock configured as ExecutionContext
        """
        mock = MagicMock()

        variables = variables or {}
        mock.variables = variables.copy()

        # Variable methods
        mock.get_variable = Mock(
            side_effect=lambda name, default=None: mock.variables.get(name, default)
        )
        mock.set_variable = Mock(
            side_effect=lambda name, value: mock.variables.__setitem__(name, value)
        )
        mock.has_variable = Mock(side_effect=lambda name: name in mock.variables)
        mock.delete_variable = Mock(
            side_effect=lambda name: mock.variables.pop(name, None)
        )
        mock.resolve_value = Mock(side_effect=lambda x: x)

        # Browser resources
        mock.get_active_page = Mock(return_value=page or MockFactory.mock_page())
        mock.get_page = Mock(return_value=page)
        mock.get_browser = Mock(return_value=browser)
        mock.set_active_page = Mock()
        mock.set_browser = Mock()

        # Execution tracking
        mock.execution_path = []
        mock.errors = []
        mock.set_current_node = Mock()
        mock.add_error = Mock()
        mock.stop_execution = Mock()
        mock.is_stopped = Mock(return_value=False)

        # Cleanup
        mock.cleanup = AsyncMock()

        # Resources
        mock.resources = {}

        return mock
