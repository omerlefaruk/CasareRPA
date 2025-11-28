"""
Tests for KeyboardController.

Tests sending keys, hotkeys, text typing, key down/up operations.
All tests mock uiautomation and ctypes to avoid real keyboard interactions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from casare_rpa.desktop.managers import KeyboardController


class TestKeyboardControllerInit:
    """Test KeyboardController initialization."""

    def test_init_sets_modifiers(self):
        """KeyboardController has correct modifier mappings."""
        controller = KeyboardController()

        assert controller.MODIFIERS["ctrl"] == "{Ctrl}"
        assert controller.MODIFIERS["control"] == "{Ctrl}"
        assert controller.MODIFIERS["alt"] == "{Alt}"
        assert controller.MODIFIERS["shift"] == "{Shift}"
        assert controller.MODIFIERS["win"] == "{Win}"
        assert controller.MODIFIERS["windows"] == "{Win}"


class TestSendKeys:
    """Test sending keyboard input."""

    @pytest.mark.asyncio
    async def test_send_keys_simple(self, mock_uiautomation):
        """Send simple key sequence."""
        controller = KeyboardController()
        result = await controller.send_keys("Hello World")

        assert result is True
        mock_uiautomation["SendKeys"].assert_called_once()

    @pytest.mark.asyncio
    async def test_send_keys_special(self, mock_uiautomation):
        """Send special keys in braces."""
        controller = KeyboardController()
        result = await controller.send_keys("{Enter}{Tab}")

        assert result is True
        mock_uiautomation["SendKeys"].assert_called_with(
            "{Enter}{Tab}", interval=0.0, waitTime=0
        )

    @pytest.mark.asyncio
    async def test_send_keys_with_interval(self, mock_uiautomation):
        """Send keys with interval between keystrokes."""
        controller = KeyboardController()
        result = await controller.send_keys("abc", interval=0.1)

        assert result is True
        mock_uiautomation["SendKeys"].assert_called_with(
            "abc", interval=0.1, waitTime=0
        )

    @pytest.mark.asyncio
    async def test_send_keys_failure(self, mock_uiautomation):
        """Raises ValueError on send failure."""
        mock_uiautomation["SendKeys"].side_effect = Exception("Send failed")

        controller = KeyboardController()

        with pytest.raises(ValueError, match="Failed to send keys"):
            await controller.send_keys("test")


class TestSendHotkey:
    """Test sending hotkey combinations."""

    @pytest.mark.asyncio
    async def test_send_hotkey_ctrl_c(self, mock_uiautomation):
        """Send Ctrl+C hotkey."""
        controller = KeyboardController()
        result = await controller.send_hotkey("ctrl", "c")

        assert result is True
        mock_uiautomation["SendKeys"].assert_called()
        # Verify the call contains Ctrl modifier
        call_args = mock_uiautomation["SendKeys"].call_args[0][0]
        assert "{Ctrl}" in call_args

    @pytest.mark.asyncio
    async def test_send_hotkey_ctrl_shift_s(self, mock_uiautomation):
        """Send Ctrl+Shift+S hotkey."""
        controller = KeyboardController()
        result = await controller.send_hotkey("ctrl", "shift", "s")

        assert result is True
        call_args = mock_uiautomation["SendKeys"].call_args[0][0]
        assert "{Ctrl}" in call_args
        assert "{Shift}" in call_args

    @pytest.mark.asyncio
    async def test_send_hotkey_alt_tab(self, mock_uiautomation):
        """Send Alt+Tab hotkey."""
        controller = KeyboardController()
        result = await controller.send_hotkey("alt", "Tab")

        assert result is True
        call_args = mock_uiautomation["SendKeys"].call_args[0][0]
        assert "{Alt}" in call_args
        assert "{Tab}" in call_args

    @pytest.mark.asyncio
    async def test_send_hotkey_win_key(self, mock_uiautomation):
        """Send Windows key hotkey."""
        controller = KeyboardController()
        result = await controller.send_hotkey("win", "e")

        assert result is True
        call_args = mock_uiautomation["SendKeys"].call_args[0][0]
        assert "{Win}" in call_args

    @pytest.mark.asyncio
    async def test_send_hotkey_failure(self, mock_uiautomation):
        """Raises ValueError on hotkey failure."""
        mock_uiautomation["SendKeys"].side_effect = Exception("Hotkey failed")

        controller = KeyboardController()

        with pytest.raises(ValueError, match="Failed to send hotkey"):
            await controller.send_hotkey("ctrl", "c")


class TestTypeText:
    """Test typing text."""

    @pytest.mark.asyncio
    async def test_type_text_simple(self, mock_uiautomation):
        """Type simple text."""
        controller = KeyboardController()
        result = await controller.type_text("Hello World")

        assert result is True
        mock_uiautomation["SendKeys"].assert_called()

    @pytest.mark.asyncio
    async def test_type_text_with_interval(self, mock_uiautomation):
        """Type text with interval between characters."""
        controller = KeyboardController()
        result = await controller.type_text("abc", interval=0.05)

        assert result is True
        mock_uiautomation["SendKeys"].assert_called_with(
            "abc", interval=0.05, waitTime=0
        )

    @pytest.mark.asyncio
    async def test_type_text_via_clipboard(self, mock_uiautomation):
        """Type text using clipboard paste."""
        with (
            patch("pyperclip.paste", return_value="original"),
            patch("pyperclip.copy") as mock_copy,
        ):
            controller = KeyboardController()
            result = await controller.type_text(
                "Long text to paste", use_clipboard=True
            )

            assert result is True
            # Should copy text to clipboard
            mock_copy.assert_called()
            # Should send Ctrl+V
            mock_uiautomation["SendKeys"].assert_called()

    @pytest.mark.asyncio
    async def test_type_text_failure(self, mock_uiautomation):
        """Raises ValueError on type failure."""
        mock_uiautomation["SendKeys"].side_effect = Exception("Type failed")

        controller = KeyboardController()

        with pytest.raises(ValueError, match="Failed to type text"):
            await controller.type_text("test")


class TestPressKey:
    """Test pressing single keys."""

    @pytest.mark.asyncio
    async def test_press_key_single(self, mock_uiautomation):
        """Press single key."""
        controller = KeyboardController()
        result = await controller.press_key("Enter")

        assert result is True
        mock_uiautomation["SendKeys"].assert_called()
        call_args = mock_uiautomation["SendKeys"].call_args[0][0]
        assert "{Enter}" in call_args

    @pytest.mark.asyncio
    async def test_press_key_with_modifiers(self, mock_uiautomation):
        """Press key with modifiers."""
        controller = KeyboardController()
        result = await controller.press_key("a", modifiers=("ctrl", "shift"))

        assert result is True
        call_args = mock_uiautomation["SendKeys"].call_args[0][0]
        assert "{Ctrl}" in call_args
        assert "{Shift}" in call_args

    @pytest.mark.asyncio
    async def test_press_key_single_char(self, mock_uiautomation):
        """Press single character key."""
        controller = KeyboardController()
        result = await controller.press_key("a")

        assert result is True
        call_args = mock_uiautomation["SendKeys"].call_args[0][0]
        assert "a" in call_args

    @pytest.mark.asyncio
    async def test_press_key_failure(self, mock_uiautomation):
        """Raises ValueError on key press failure."""
        mock_uiautomation["SendKeys"].side_effect = Exception("Press failed")

        controller = KeyboardController()

        with pytest.raises(ValueError, match="Failed to press key"):
            await controller.press_key("Enter")


class TestKeyDownUp:
    """Test key down and key up operations."""

    @pytest.mark.asyncio
    async def test_key_down(self, mock_ctypes):
        """Hold key down."""
        controller = KeyboardController()
        result = await controller.key_down("ctrl")

        assert result is True
        mock_ctypes["keybd_event"].assert_called()

    @pytest.mark.asyncio
    async def test_key_up(self, mock_ctypes):
        """Release held key."""
        controller = KeyboardController()
        result = await controller.key_up("ctrl")

        assert result is True
        mock_ctypes["keybd_event"].assert_called()

    @pytest.mark.asyncio
    async def test_key_down_unknown_key(self, mock_ctypes):
        """Raises ValueError for unknown key."""
        controller = KeyboardController()

        with pytest.raises(ValueError, match="Unknown key"):
            await controller.key_down("unknownkey")

    @pytest.mark.asyncio
    async def test_key_up_unknown_key(self, mock_ctypes):
        """Raises ValueError for unknown key."""
        controller = KeyboardController()

        with pytest.raises(ValueError, match="Unknown key"):
            await controller.key_up("unknownkey")

    @pytest.mark.asyncio
    async def test_key_down_failure(self, mock_ctypes):
        """Raises ValueError on key down failure."""
        mock_ctypes["keybd_event"].side_effect = Exception("Key down failed")

        controller = KeyboardController()

        with pytest.raises(ValueError, match="Failed to hold key down"):
            await controller.key_down("ctrl")


class TestGetVKCode:
    """Test virtual key code lookup."""

    def test_get_vk_code_modifiers(self):
        """Get VK codes for modifier keys."""
        controller = KeyboardController()

        assert controller._get_vk_code("ctrl") == 0x11
        assert controller._get_vk_code("alt") == 0x12
        assert controller._get_vk_code("shift") == 0x10
        assert controller._get_vk_code("win") == 0x5B

    def test_get_vk_code_navigation(self):
        """Get VK codes for navigation keys."""
        controller = KeyboardController()

        assert controller._get_vk_code("enter") == 0x0D
        assert controller._get_vk_code("tab") == 0x09
        assert controller._get_vk_code("escape") == 0x1B
        assert controller._get_vk_code("backspace") == 0x08

    def test_get_vk_code_arrows(self):
        """Get VK codes for arrow keys."""
        controller = KeyboardController()

        assert controller._get_vk_code("up") == 0x26
        assert controller._get_vk_code("down") == 0x28
        assert controller._get_vk_code("left") == 0x25
        assert controller._get_vk_code("right") == 0x27

    def test_get_vk_code_function_keys(self):
        """Get VK codes for function keys."""
        controller = KeyboardController()

        assert controller._get_vk_code("f1") == 0x70
        assert controller._get_vk_code("f12") == 0x7B

    def test_get_vk_code_single_char(self):
        """Get VK code for single character."""
        controller = KeyboardController()

        assert controller._get_vk_code("a") == ord("A")
        assert controller._get_vk_code("z") == ord("Z")
        assert controller._get_vk_code("1") == ord("1")

    def test_get_vk_code_unknown(self):
        """Returns None for unknown key."""
        controller = KeyboardController()

        assert controller._get_vk_code("unknownkey") is None
