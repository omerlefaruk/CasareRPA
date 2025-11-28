"""
Tests for WaitManager.

Tests waiting for elements, windows, conditions, and property verification.
All tests mock UIAutomation to avoid real wait operations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import asyncio

from casare_rpa.desktop.managers import WaitManager


class MockUIControl:
    """Mock UIAutomation Control for testing (local copy)."""

    def __init__(
        self,
        name: str = "TestWindow",
        control_type: str = "WindowControl",
        class_name: str = "TestClass",
    ):
        self.Name = name
        self.ControlTypeName = control_type
        self.ClassName = class_name

    def GetChildren(self):
        return []


class MockDesktopElement:
    """Mock DesktopElement for wait manager tests (local copy)."""

    def __init__(self, exists: bool = True, enabled: bool = True):
        self._exists_val = exists
        self._control = Mock()
        self._control.IsEnabled = enabled

    def exists(self):
        return self._exists_val


class TestWaitManagerInit:
    """Test WaitManager initialization."""

    def test_init(self):
        """WaitManager initializes without error."""
        manager = WaitManager()
        assert manager is not None


class TestWaitForElement:
    """Test waiting for element states."""

    @pytest.mark.asyncio
    async def test_wait_for_element_visible(self, mock_uiautomation):
        """Wait for element to become visible."""
        mock_element = MockDesktopElement(exists=True)

        with patch(
            "casare_rpa.desktop.managers.wait_manager.selector_find_element"
        ) as mock_find:
            mock_find.return_value = mock_element

            manager = WaitManager()
            result = await manager.wait_for_element(
                selector={"name": "TestElement"}, timeout=1.0, state="visible"
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_wait_for_element_hidden(self, mock_uiautomation):
        """Wait for element to become hidden."""
        with patch(
            "casare_rpa.desktop.managers.wait_manager.selector_find_element"
        ) as mock_find:
            mock_find.return_value = None

            manager = WaitManager()
            result = await manager.wait_for_element(
                selector={"name": "TestElement"}, timeout=1.0, state="hidden"
            )

            assert result is None  # Expected for hidden state

    @pytest.mark.asyncio
    async def test_wait_for_element_enabled(self, mock_uiautomation):
        """Wait for element to become enabled."""
        mock_element = MockDesktopElement(enabled=True, exists=True)
        mock_element._control.IsEnabled = True

        with patch(
            "casare_rpa.desktop.managers.wait_manager.selector_find_element"
        ) as mock_find:
            mock_find.return_value = mock_element

            manager = WaitManager()
            result = await manager.wait_for_element(
                selector={"name": "TestElement"}, timeout=1.0, state="enabled"
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_wait_for_element_disabled(self, mock_uiautomation):
        """Wait for element to become disabled."""
        mock_element = MockDesktopElement(enabled=False, exists=True)
        mock_element._control.IsEnabled = False

        with patch(
            "casare_rpa.desktop.managers.wait_manager.selector_find_element"
        ) as mock_find:
            mock_find.return_value = mock_element

            manager = WaitManager()
            result = await manager.wait_for_element(
                selector={"name": "TestElement"}, timeout=1.0, state="disabled"
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_wait_for_element_timeout(self, mock_uiautomation):
        """Raises TimeoutError when element doesn't reach state."""
        mock_element = MockDesktopElement(exists=False)

        with patch(
            "casare_rpa.desktop.managers.wait_manager.selector_find_element"
        ) as mock_find:
            mock_find.return_value = mock_element

            manager = WaitManager()

            with pytest.raises(TimeoutError, match="did not become"):
                await manager.wait_for_element(
                    selector={"name": "TestElement"},
                    timeout=0.2,
                    state="visible",
                    poll_interval=0.1,
                )

    @pytest.mark.asyncio
    async def test_wait_for_element_invalid_state(self):
        """Raises ValueError for invalid state."""
        manager = WaitManager()

        with pytest.raises(ValueError, match="Invalid state"):
            await manager.wait_for_element(
                selector={"name": "TestElement"}, state="invalid"
            )

    @pytest.mark.asyncio
    async def test_wait_for_element_with_parent(self, mock_uiautomation):
        """Wait for element with parent scope."""
        mock_element = MockDesktopElement(exists=True)
        mock_parent = MockUIControl()

        with patch(
            "casare_rpa.desktop.managers.wait_manager.selector_find_element"
        ) as mock_find:
            mock_find.return_value = mock_element

            manager = WaitManager()
            result = await manager.wait_for_element(
                selector={"name": "TestElement"},
                timeout=1.0,
                state="visible",
                parent=mock_parent,
            )

            assert result is not None


class TestWaitForWindow:
    """Test waiting for window states."""

    @pytest.mark.asyncio
    async def test_wait_for_window_by_title(self, mock_uiautomation):
        """Wait for window by title."""
        mock_window = MockUIControl(name="Test Window")
        mock_uiautomation["root"].GetChildren = Mock(return_value=[mock_window])

        manager = WaitManager()
        result = await manager.wait_for_window(
            title="Test Window", timeout=1.0, state="visible"
        )

        assert result is not None
        assert result.Name == "Test Window"

    @pytest.mark.asyncio
    async def test_wait_for_window_by_regex(self, mock_uiautomation):
        """Wait for window by title regex."""
        mock_window = MockUIControl(name="App - Document.txt")
        mock_uiautomation["root"].GetChildren = Mock(return_value=[mock_window])

        manager = WaitManager()
        result = await manager.wait_for_window(
            title_regex=r"App - .*\.txt", timeout=1.0
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_wait_for_window_by_class(self, mock_uiautomation):
        """Wait for window by class name."""
        mock_window = MockUIControl(name="Window", class_name="Notepad")
        mock_uiautomation["root"].GetChildren = Mock(return_value=[mock_window])

        manager = WaitManager()
        result = await manager.wait_for_window(class_name="Notepad", timeout=1.0)

        assert result is not None

    @pytest.mark.asyncio
    async def test_wait_for_window_hidden(self, mock_uiautomation):
        """Wait for window to close/hide."""
        mock_uiautomation["root"].GetChildren = Mock(return_value=[])

        manager = WaitManager()
        result = await manager.wait_for_window(
            title="Test Window", timeout=1.0, state="hidden"
        )

        assert result is None  # Expected for hidden state

    @pytest.mark.asyncio
    async def test_wait_for_window_timeout(self, mock_uiautomation):
        """Raises TimeoutError when window not found."""
        mock_uiautomation["root"].GetChildren = Mock(return_value=[])

        manager = WaitManager()

        with pytest.raises(TimeoutError, match="did not become"):
            await manager.wait_for_window(
                title="NonexistentWindow",
                timeout=0.2,
                state="visible",
                poll_interval=0.1,
            )

    @pytest.mark.asyncio
    async def test_wait_for_window_no_criteria_raises(self):
        """Raises ValueError when no search criteria provided."""
        manager = WaitManager()

        with pytest.raises(ValueError, match="Must provide at least one"):
            await manager.wait_for_window(timeout=1.0)

    @pytest.mark.asyncio
    async def test_wait_for_window_invalid_state(self):
        """Raises ValueError for invalid state."""
        manager = WaitManager()

        with pytest.raises(ValueError, match="Invalid state"):
            await manager.wait_for_window(
                title="Test",
                state="enabled",  # Only visible/hidden valid for windows
            )


class TestElementExists:
    """Test element existence check."""

    @pytest.mark.asyncio
    async def test_element_exists_true(self, mock_uiautomation):
        """Returns True when element exists."""
        mock_element = MockDesktopElement(exists=True)

        with patch(
            "casare_rpa.desktop.managers.wait_manager.selector_find_element"
        ) as mock_find:
            mock_find.return_value = mock_element

            manager = WaitManager()
            result = await manager.element_exists(selector={"name": "TestElement"})

            assert result is True

    @pytest.mark.asyncio
    async def test_element_exists_false(self, mock_uiautomation):
        """Returns False when element doesn't exist."""
        with patch(
            "casare_rpa.desktop.managers.wait_manager.selector_find_element"
        ) as mock_find:
            mock_find.return_value = None

            manager = WaitManager()
            result = await manager.element_exists(
                selector={"name": "NonexistentElement"}
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_element_exists_with_timeout(self, mock_uiautomation):
        """Respects timeout parameter."""
        mock_element = MockDesktopElement(exists=True)

        with patch(
            "casare_rpa.desktop.managers.wait_manager.selector_find_element"
        ) as mock_find:
            mock_find.return_value = mock_element

            manager = WaitManager()
            result = await manager.element_exists(
                selector={"name": "TestElement"}, timeout=2.0
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_element_exists_handles_exception(self, mock_uiautomation):
        """Returns False on exception."""
        with patch(
            "casare_rpa.desktop.managers.wait_manager.selector_find_element"
        ) as mock_find:
            mock_find.side_effect = Exception("Search failed")

            manager = WaitManager()
            result = await manager.element_exists(selector={"name": "TestElement"})

            assert result is False


class TestVerifyElementProperty:
    """Test element property verification."""

    @pytest.mark.asyncio
    async def test_verify_property_equals(self, mock_desktop_element):
        """Verify property equals expected value."""
        manager = WaitManager()
        result = await manager.verify_element_property(
            mock_desktop_element,
            property_name="Name",
            expected_value="TestElement",
            comparison="equals",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_verify_property_not_equals(self, mock_desktop_element):
        """Verify property not equals value."""
        manager = WaitManager()
        result = await manager.verify_element_property(
            mock_desktop_element,
            property_name="Name",
            expected_value="OtherElement",
            comparison="not_equals",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_verify_property_contains(self, mock_desktop_element):
        """Verify property contains substring."""
        manager = WaitManager()
        result = await manager.verify_element_property(
            mock_desktop_element,
            property_name="Name",
            expected_value="Test",
            comparison="contains",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_verify_property_startswith(self, mock_desktop_element):
        """Verify property starts with prefix."""
        manager = WaitManager()
        result = await manager.verify_element_property(
            mock_desktop_element,
            property_name="Name",
            expected_value="Test",
            comparison="startswith",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_verify_property_endswith(self, mock_desktop_element):
        """Verify property ends with suffix."""
        manager = WaitManager()
        result = await manager.verify_element_property(
            mock_desktop_element,
            property_name="Name",
            expected_value="Element",
            comparison="endswith",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_verify_property_regex(self, mock_desktop_element):
        """Verify property matches regex."""
        manager = WaitManager()
        result = await manager.verify_element_property(
            mock_desktop_element,
            property_name="Name",
            expected_value=r"Test\w+",
            comparison="regex",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_verify_property_greater(self, mock_desktop_element):
        """Verify numeric property greater than value."""
        mock_desktop_element._control.ProcessId = 100

        manager = WaitManager()
        result = await manager.verify_element_property(
            mock_desktop_element,
            property_name="ProcessId",
            expected_value=50,
            comparison="greater",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_verify_property_less(self, mock_desktop_element):
        """Verify numeric property less than value."""
        mock_desktop_element._control.ProcessId = 100

        manager = WaitManager()
        result = await manager.verify_element_property(
            mock_desktop_element,
            property_name="ProcessId",
            expected_value=200,
            comparison="less",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_verify_property_invalid_comparison(self, mock_desktop_element):
        """Raises ValueError for invalid comparison."""
        manager = WaitManager()

        with pytest.raises(ValueError, match="Invalid comparison"):
            await manager.verify_element_property(
                mock_desktop_element,
                property_name="Name",
                expected_value="Test",
                comparison="invalid",
            )

    @pytest.mark.asyncio
    async def test_verify_property_not_found(self, mock_desktop_element):
        """Returns False when property not found."""
        manager = WaitManager()
        result = await manager.verify_element_property(
            mock_desktop_element,
            property_name="NonexistentProperty",
            expected_value="Test",
            comparison="equals",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_verify_property_mapped_names(self, mock_desktop_element):
        """Uses property name mapping for common aliases."""
        manager = WaitManager()

        # Test 'text' maps to Name
        result = await manager.verify_element_property(
            mock_desktop_element,
            property_name="text",
            expected_value="TestElement",
            comparison="equals",
        )

        assert result is True


class TestWaitForCondition:
    """Test waiting for custom conditions."""

    @pytest.mark.asyncio
    async def test_wait_for_condition_met_immediately(self):
        """Returns immediately when condition already met."""

        def condition():
            return True

        manager = WaitManager()
        result = await manager.wait_for_condition(condition_fn=condition, timeout=1.0)

        assert result is True

    @pytest.mark.asyncio
    async def test_wait_for_condition_becomes_true(self):
        """Waits until condition becomes true."""
        call_count = 0

        def condition():
            nonlocal call_count
            call_count += 1
            return call_count >= 3

        manager = WaitManager()
        result = await manager.wait_for_condition(
            condition_fn=condition, timeout=1.0, poll_interval=0.05
        )

        assert result is True
        assert call_count >= 3

    @pytest.mark.asyncio
    async def test_wait_for_condition_timeout(self):
        """Raises TimeoutError when condition never met."""

        def condition():
            return False

        manager = WaitManager()

        with pytest.raises(TimeoutError, match="not met"):
            await manager.wait_for_condition(
                condition_fn=condition,
                timeout=0.2,
                poll_interval=0.05,
                error_message="Condition not met",
            )

    @pytest.mark.asyncio
    async def test_wait_for_condition_custom_error_message(self):
        """Uses custom error message in TimeoutError."""

        def condition():
            return False

        manager = WaitManager()

        with pytest.raises(TimeoutError, match="Custom error"):
            await manager.wait_for_condition(
                condition_fn=condition, timeout=0.1, error_message="Custom error"
            )

    @pytest.mark.asyncio
    async def test_wait_for_condition_handles_exception(self):
        """Continues polling when condition raises exception."""
        call_count = 0

        def condition():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary error")
            return True

        manager = WaitManager()
        result = await manager.wait_for_condition(
            condition_fn=condition, timeout=1.0, poll_interval=0.05
        )

        assert result is True
