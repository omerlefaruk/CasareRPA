"""
Keyboard Controller - Keyboard operations for desktop automation

Handles sending keys, hotkeys, and text input.
All operations are async-first with proper error handling.
"""

import asyncio

import uiautomation as auto
from loguru import logger


class KeyboardController:
    """
    Controls keyboard operations for desktop automation.

    Provides async methods for sending keys, hotkeys, and text.
    Uses asyncio.to_thread() for blocking operations.
    """

    # Modifier key mappings
    MODIFIERS = {
        "ctrl": "{Ctrl}",
        "control": "{Ctrl}",
        "alt": "{Alt}",
        "shift": "{Shift}",
        "win": "{Win}",
        "windows": "{Win}",
    }

    def __init__(self) -> None:
        """Initialize keyboard controller."""
        logger.debug("Initializing KeyboardController")

    async def send_keys(self, keys: str, interval: float = 0.0) -> bool:
        """
        Send keyboard input.

        Args:
            keys: Keys to send. Supports special keys in braces:
                  {Enter}, {Tab}, {Escape}, {Backspace}, {Delete},
                  {Up}, {Down}, {Left}, {Right}, {Home}, {End},
                  {PageUp}, {PageDown}, {F1}-{F12}, {Ctrl}, {Alt}, {Shift}
            interval: Delay between keys in seconds

        Returns:
            True if successful

        Raises:
            ValueError: If send fails
        """
        logger.debug(f"Sending keys: '{keys[:50]}...' (interval={interval}s)")

        # Use clipboard for multi-line or long text to avoid SendKeys parsing issues
        use_clipboard = "\n" in keys or len(keys) > 100

        def _send() -> bool:
            if use_clipboard:
                import pyperclip

                original = pyperclip.paste()
                try:
                    pyperclip.copy(keys)
                    auto.SendKeys("{Ctrl}v", waitTime=0)
                finally:
                    pyperclip.copy(original if original else "")
            else:
                auto.SendKeys(keys, interval=interval, waitTime=0)
            return True

        try:
            result = await asyncio.to_thread(_send)
            logger.info(f"Sent keys: '{keys[:50]}...'")
            return result

        except Exception as e:
            error_msg = f"Failed to send keys: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    async def send_hotkey(self, *keys: str) -> bool:
        """
        Send a hotkey combination (e.g., Ctrl+C, Alt+Tab).

        Args:
            *keys: Keys in the combination (e.g., "ctrl", "c")
                   Supported modifiers: ctrl, alt, shift, win

        Returns:
            True if successful

        Raises:
            ValueError: If send fails
        """
        logger.debug(f"Sending hotkey: {'+'.join(keys)}")

        def _send_hotkey() -> bool:
            hotkey_str = ""
            regular_keys = []

            for key in keys:
                key_lower = key.lower()
                if key_lower in self.MODIFIERS:
                    hotkey_str += self.MODIFIERS[key_lower]
                else:
                    regular_keys.append(key)

            for key in regular_keys:
                if len(key) == 1:
                    hotkey_str += key
                else:
                    hotkey_str += "{" + key.capitalize() + "}"

            auto.SendKeys(hotkey_str, interval=0, waitTime=0)
            return True

        try:
            result = await asyncio.to_thread(_send_hotkey)
            logger.info(f"Sent hotkey: {'+'.join(keys)}")
            return result

        except Exception as e:
            error_msg = f"Failed to send hotkey: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    async def type_text(
        self,
        text: str,
        interval: float = 0.01,
        use_clipboard: bool = False,
    ) -> bool:
        """
        Type text character by character or via clipboard.

        Args:
            text: Text to type
            interval: Delay between characters in seconds
            use_clipboard: If True, paste via clipboard (faster for long text)

        Returns:
            True if successful

        Raises:
            ValueError: If typing fails
        """
        logger.debug(f"Typing text: '{text[:50]}...' (use_clipboard={use_clipboard})")

        def _type_text() -> bool:
            if use_clipboard:
                import pyperclip

                original = pyperclip.paste()
                try:
                    pyperclip.copy(text)
                    auto.SendKeys("{Ctrl}v", waitTime=0)
                finally:
                    pyperclip.copy(original)
            else:
                auto.SendKeys(text, interval=interval, waitTime=0)
            return True

        try:
            result = await asyncio.to_thread(_type_text)
            logger.info(f"Typed text: '{text[:50]}...'")
            return result

        except Exception as e:
            error_msg = f"Failed to type text: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    async def press_key(self, key: str, modifiers: tuple[str, ...] = ()) -> bool:
        """
        Press a single key with optional modifiers.

        Args:
            key: Key to press (e.g., "Enter", "Tab", "a", "F1")
            modifiers: Tuple of modifier keys (e.g., ("ctrl", "shift"))

        Returns:
            True if successful

        Raises:
            ValueError: If key press fails
        """
        logger.debug(f"Pressing key: '{key}' with modifiers: {modifiers}")

        def _press_key() -> bool:
            hotkey_str = ""

            for mod in modifiers:
                mod_lower = mod.lower()
                if mod_lower in self.MODIFIERS:
                    hotkey_str += self.MODIFIERS[mod_lower]

            if len(key) == 1:
                hotkey_str += key
            else:
                hotkey_str += "{" + key + "}"

            auto.SendKeys(hotkey_str, interval=0, waitTime=0)
            return True

        try:
            result = await asyncio.to_thread(_press_key)
            mod_str = "+".join(modifiers) + "+" if modifiers else ""
            logger.info(f"Pressed key: {mod_str}{key}")
            return result

        except Exception as e:
            error_msg = f"Failed to press key: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    async def key_down(self, key: str) -> bool:
        """
        Press and hold a key down.

        Args:
            key: Key to hold down

        Returns:
            True if successful

        Raises:
            ValueError: If operation fails
        """
        logger.debug(f"Holding key down: '{key}'")

        def _key_down() -> bool:
            key_code = self._get_vk_code(key)
            if key_code is None:
                raise ValueError(f"Unknown key: {key}")

            import ctypes

            ctypes.windll.user32.keybd_event(key_code, 0, 0, 0)
            return True

        try:
            result = await asyncio.to_thread(_key_down)
            logger.info(f"Key held down: '{key}'")
            return result

        except Exception as e:
            error_msg = f"Failed to hold key down: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    async def key_up(self, key: str) -> bool:
        """
        Release a held key.

        Args:
            key: Key to release

        Returns:
            True if successful

        Raises:
            ValueError: If operation fails
        """
        logger.debug(f"Releasing key: '{key}'")

        def _key_up() -> bool:
            key_code = self._get_vk_code(key)
            if key_code is None:
                raise ValueError(f"Unknown key: {key}")

            import ctypes

            KEYEVENTF_KEYUP = 0x0002
            ctypes.windll.user32.keybd_event(key_code, 0, KEYEVENTF_KEYUP, 0)
            return True

        try:
            result = await asyncio.to_thread(_key_up)
            logger.info(f"Key released: '{key}'")
            return result

        except Exception as e:
            error_msg = f"Failed to release key: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    def _get_vk_code(self, key: str) -> int:
        """Get virtual key code for a key name."""
        VK_CODES = {
            "ctrl": 0x11,
            "control": 0x11,
            "alt": 0x12,
            "shift": 0x10,
            "win": 0x5B,
            "windows": 0x5B,
            "enter": 0x0D,
            "return": 0x0D,
            "tab": 0x09,
            "escape": 0x1B,
            "esc": 0x1B,
            "backspace": 0x08,
            "delete": 0x2E,
            "insert": 0x2D,
            "home": 0x24,
            "end": 0x23,
            "pageup": 0x21,
            "pagedown": 0x22,
            "up": 0x26,
            "down": 0x28,
            "left": 0x25,
            "right": 0x27,
            "space": 0x20,
            "f1": 0x70,
            "f2": 0x71,
            "f3": 0x72,
            "f4": 0x73,
            "f5": 0x74,
            "f6": 0x75,
            "f7": 0x76,
            "f8": 0x77,
            "f9": 0x78,
            "f10": 0x79,
            "f11": 0x7A,
            "f12": 0x7B,
        }

        key_lower = key.lower()
        if key_lower in VK_CODES:
            return VK_CODES[key_lower]

        if len(key) == 1:
            return ord(key.upper())

        return None
