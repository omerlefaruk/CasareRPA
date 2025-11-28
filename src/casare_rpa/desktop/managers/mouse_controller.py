"""
Mouse Controller - Mouse operations for desktop automation

Handles mouse movement, clicking, dragging, and position tracking.
All operations are async-first with proper error handling.
"""

import asyncio
import ctypes
from typing import Tuple

import uiautomation as auto
from loguru import logger


class MouseController:
    """
    Controls mouse operations for desktop automation.

    Provides async methods for mouse movement, clicks, and drag operations.
    Uses asyncio.to_thread() for blocking operations and asyncio.sleep() for delays.
    """

    # Mouse event constants
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    MOUSEEVENTF_RIGHTDOWN = 0x0008
    MOUSEEVENTF_RIGHTUP = 0x0010
    MOUSEEVENTF_MIDDLEDOWN = 0x0020
    MOUSEEVENTF_MIDDLEUP = 0x0040

    def __init__(self) -> None:
        """Initialize mouse controller."""
        logger.debug("Initializing MouseController")

    async def move_mouse(self, x: int, y: int, duration: float = 0.0) -> bool:
        """
        Move mouse cursor to specified position.

        Args:
            x: Target X coordinate
            y: Target Y coordinate
            duration: Time in seconds to move (0 for instant)

        Returns:
            True if successful

        Raises:
            ValueError: If move fails
        """
        logger.debug(f"Moving mouse to ({x}, {y}) over {duration}s")

        try:
            if duration > 0:
                start_x, start_y = await self.get_position()
                steps = max(10, int(duration * 60))
                step_delay = duration / steps

                for i in range(steps + 1):
                    progress = i / steps
                    ease = 1 - (1 - progress) ** 2
                    current_x = int(start_x + (x - start_x) * ease)
                    current_y = int(start_y + (y - start_y) * ease)
                    await asyncio.to_thread(
                        ctypes.windll.user32.SetCursorPos, current_x, current_y
                    )
                    await asyncio.sleep(step_delay)
            else:
                await asyncio.to_thread(ctypes.windll.user32.SetCursorPos, x, y)

            logger.info(f"Moved mouse to ({x}, {y})")
            return True

        except Exception as e:
            error_msg = f"Failed to move mouse: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    async def click(
        self,
        x: int = None,
        y: int = None,
        button: str = "left",
        click_type: str = "single",
    ) -> bool:
        """
        Click mouse at specified position or current position.

        Args:
            x: X coordinate (None for current position)
            y: Y coordinate (None for current position)
            button: Mouse button - "left", "right", "middle"
            click_type: Click type - "single", "double", "triple"

        Returns:
            True if successful

        Raises:
            ValueError: If click fails
        """
        logger.debug(f"Clicking {button} {click_type} at ({x}, {y})")

        valid_buttons = ["left", "right", "middle"]
        if button.lower() not in valid_buttons:
            raise ValueError(
                f"Invalid button '{button}'. Must be one of: {valid_buttons}"
            )

        valid_types = ["single", "double", "triple"]
        if click_type.lower() not in valid_types:
            raise ValueError(
                f"Invalid click_type '{click_type}'. Must be one of: {valid_types}"
            )

        button = button.lower()
        click_type = click_type.lower()

        try:
            if x is None or y is None:
                x, y = await self.get_position()

            await asyncio.to_thread(ctypes.windll.user32.SetCursorPos, x, y)

            clicks = {"single": 1, "double": 2, "triple": 3}[click_type]

            for i in range(clicks):
                if button == "left":
                    await asyncio.to_thread(auto.Click, x, y)
                elif button == "right":
                    await asyncio.to_thread(auto.RightClick, x, y)
                elif button == "middle":
                    await asyncio.to_thread(auto.MiddleClick, x, y)
                if i < clicks - 1:
                    await asyncio.sleep(0.05)

            logger.info(f"Clicked {button} {click_type} at ({x}, {y})")
            return True

        except Exception as e:
            error_msg = f"Failed to click mouse: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    async def get_position(self) -> Tuple[int, int]:
        """
        Get current mouse cursor position.

        Returns:
            Tuple of (x, y) coordinates
        """
        try:
            position = await asyncio.to_thread(self._get_position_sync)
            logger.debug(f"Mouse position: {position}")
            return position

        except Exception as e:
            error_msg = f"Failed to get mouse position: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def _get_position_sync(self) -> Tuple[int, int]:
        """Synchronous helper to get mouse position."""

        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        point = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
        return (point.x, point.y)

    async def drag(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        button: str = "left",
        duration: float = 0.5,
    ) -> bool:
        """
        Drag mouse from one position to another.

        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            button: Mouse button to hold - "left", "right"
            duration: Time for drag operation in seconds

        Returns:
            True if successful

        Raises:
            ValueError: If drag fails
        """
        logger.debug(f"Dragging from ({start_x}, {start_y}) to ({end_x}, {end_y})")

        valid_buttons = ["left", "right"]
        if button.lower() not in valid_buttons:
            raise ValueError(
                f"Invalid button '{button}'. Must be one of: {valid_buttons}"
            )

        button = button.lower()

        try:
            await asyncio.to_thread(ctypes.windll.user32.SetCursorPos, start_x, start_y)
            await asyncio.sleep(0.1)

            if button == "left":
                down_flag = self.MOUSEEVENTF_LEFTDOWN
                up_flag = self.MOUSEEVENTF_LEFTUP
            else:
                down_flag = self.MOUSEEVENTF_RIGHTDOWN
                up_flag = self.MOUSEEVENTF_RIGHTUP

            await asyncio.to_thread(
                ctypes.windll.user32.mouse_event, down_flag, 0, 0, 0, 0
            )
            await asyncio.sleep(0.05)

            steps = max(10, int(duration * 60))
            step_delay = duration / steps

            for i in range(steps + 1):
                progress = i / steps
                ease = 1 - (1 - progress) ** 2
                current_x = int(start_x + (end_x - start_x) * ease)
                current_y = int(start_y + (end_y - start_y) * ease)
                await asyncio.to_thread(
                    ctypes.windll.user32.SetCursorPos, current_x, current_y
                )
                await asyncio.sleep(step_delay)

            await asyncio.sleep(0.05)
            await asyncio.to_thread(
                ctypes.windll.user32.mouse_event, up_flag, 0, 0, 0, 0
            )

            logger.info(f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})")
            return True

        except Exception as e:
            error_msg = f"Failed to drag mouse: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    async def scroll(
        self,
        x: int = None,
        y: int = None,
        direction: str = "down",
        amount: int = 3,
    ) -> bool:
        """
        Scroll mouse wheel at specified position.

        Args:
            x: X coordinate (None for current position)
            y: Y coordinate (None for current position)
            direction: Scroll direction - "up", "down"
            amount: Number of scroll clicks

        Returns:
            True if successful

        Raises:
            ValueError: If scroll fails
        """
        logger.debug(f"Scrolling {direction} by {amount} at ({x}, {y})")

        valid_directions = ["up", "down"]
        if direction.lower() not in valid_directions:
            raise ValueError(
                f"Invalid direction '{direction}'. Must be one of: {valid_directions}"
            )

        direction = direction.lower()

        def _do_scroll(pos_x: int, pos_y: int) -> bool:
            if direction == "down":
                auto.WheelDown(pos_x, pos_y, wheelTimes=amount)
            else:
                auto.WheelUp(pos_x, pos_y, wheelTimes=amount)
            return True

        try:
            if x is None or y is None:
                x, y = await self.get_position()

            result = await asyncio.to_thread(_do_scroll, x, y)
            logger.info(f"Scrolled {direction} by {amount} at ({x}, {y})")
            return result

        except Exception as e:
            error_msg = f"Failed to scroll: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)
