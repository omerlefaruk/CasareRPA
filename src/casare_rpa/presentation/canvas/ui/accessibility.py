"""
Accessibility settings for UI animations.

Detects OS-level reduced motion preferences and provides helpers
to respect user accessibility settings.

WCAG 2.3.3 compliance: Animations can be disabled by user preference.

Usage:
    from casare_rpa.presentation.canvas.ui.accessibility import AccessibilitySettings

    # Check preference before animating
    if not AccessibilitySettings.prefers_reduced_motion():
        UIAnimator.fade_in(widget, duration=200)
    else:
        widget.show()  # Instant, no animation

    # Or use helper to get effective duration
    duration = AccessibilitySettings.get_duration(200)  # Returns 0 if reduced motion

    # Testing override
    AccessibilitySettings.set_override(True)  # Force reduced motion
    AccessibilitySettings.set_override(None)  # Use OS setting
"""

import sys
from typing import Optional

from loguru import logger


class AccessibilitySettings:
    """
    Manages accessibility preferences for UI animations.

    Detects OS-level reduced motion settings on Windows and macOS.
    Caches the result to avoid repeated OS queries.

    Thread-safe for read operations (cache is set once).
    """

    _cached_preference: Optional[bool] = None
    _manual_override: Optional[bool] = None

    @classmethod
    def prefers_reduced_motion(cls) -> bool:
        """
        Check if user prefers reduced motion.

        Returns:
            True if reduced motion is preferred (animations should be disabled),
            False if animations are enabled.

        Note:
            - Checks manual override first
            - Falls back to cached OS preference
            - Queries OS only once, then caches result
            - Returns False (animations enabled) if detection fails
        """
        # Manual override takes precedence
        if cls._manual_override is not None:
            return cls._manual_override

        # Use cached value if available
        if cls._cached_preference is not None:
            return cls._cached_preference

        # Detect from OS and cache
        cls._cached_preference = cls._detect_os_preference()
        logger.debug(f"Detected reduced motion preference: {cls._cached_preference}")
        return cls._cached_preference

    @classmethod
    def get_duration(cls, base_duration: int) -> int:
        """
        Return effective animation duration based on accessibility settings.

        Args:
            base_duration: The normal animation duration in milliseconds.

        Returns:
            0 if reduced motion is preferred (instant transition),
            base_duration otherwise.
        """
        if cls.prefers_reduced_motion():
            return 0
        return base_duration

    @classmethod
    def set_override(cls, value: Optional[bool]) -> None:
        """
        Set manual override for reduced motion preference.

        Args:
            value: True to force reduced motion,
                   False to force animations enabled,
                   None to use OS setting.

        Use for testing or user preference settings that override OS.
        """
        cls._manual_override = value
        logger.debug(f"Reduced motion override set to: {value}")

    @classmethod
    def clear_cache(cls) -> None:
        """
        Clear cached OS preference.

        Call this to force re-detection of OS setting.
        Useful if user changes OS accessibility settings while app is running.
        Does not affect manual override.
        """
        cls._cached_preference = None
        logger.debug("Reduced motion preference cache cleared")

    @classmethod
    def _detect_os_preference(cls) -> bool:
        """
        Detect reduced motion preference from OS.

        Returns:
            True if reduced motion is enabled,
            False otherwise (including on detection failure).
        """
        if sys.platform == "win32":
            return cls._detect_windows()
        elif sys.platform == "darwin":
            return cls._detect_macos()
        else:
            # Linux/other: no standard API, assume animations enabled
            logger.debug(f"Reduced motion detection not supported on {sys.platform}")
            return False

    @classmethod
    def _detect_windows(cls) -> bool:
        """
        Detect reduced motion on Windows.

        Uses SystemParametersInfo to query SPI_GETCLIENTAREAANIMATION.
        This setting corresponds to:
        Settings > Ease of Access > Display > Show animations in Windows

        Returns:
            True if animations are disabled (reduced motion),
            False if animations are enabled or detection fails.
        """
        try:
            import ctypes

            SPI_GETCLIENTAREAANIMATION = 0x1042
            result = ctypes.c_bool()

            success = ctypes.windll.user32.SystemParametersInfoW(
                SPI_GETCLIENTAREAANIMATION,
                0,
                ctypes.byref(result),
                0,
            )

            if not success:
                logger.warning(
                    "SystemParametersInfoW failed for SPI_GETCLIENTAREAANIMATION"
                )
                return False

            # result.value is True if animations ENABLED, False if DISABLED
            # We return True if reduced motion (animations disabled)
            reduced_motion = not result.value
            logger.debug(
                f"Windows animation setting: {'disabled' if reduced_motion else 'enabled'}"
            )
            return reduced_motion

        except Exception as e:
            logger.warning(f"Failed to detect Windows animation preference: {e}")
            return False

    @classmethod
    def _detect_macos(cls) -> bool:
        """
        Detect reduced motion on macOS.

        Reads NSReduceMotion from com.apple.universalaccess preferences.
        This setting corresponds to:
        System Preferences > Accessibility > Display > Reduce motion

        Returns:
            True if reduced motion is enabled,
            False if animations are enabled or detection fails.
        """
        try:
            import subprocess

            result = subprocess.run(
                [
                    "defaults",
                    "read",
                    "com.apple.universalaccess",
                    "reduceMotion",
                ],
                capture_output=True,
                text=True,
                timeout=2,
            )

            if result.returncode != 0:
                # Key doesn't exist = animations enabled (default)
                logger.debug(
                    "macOS reduceMotion key not set, defaulting to animations enabled"
                )
                return False

            # Value is "1" if reduced motion enabled
            reduced_motion = result.stdout.strip() == "1"
            logger.debug(
                f"macOS reduce motion: {'enabled' if reduced_motion else 'disabled'}"
            )
            return reduced_motion

        except subprocess.TimeoutExpired:
            logger.warning("Timeout reading macOS accessibility preferences")
            return False
        except FileNotFoundError:
            logger.warning("'defaults' command not found on macOS")
            return False
        except Exception as e:
            logger.warning(f"Failed to detect macOS animation preference: {e}")
            return False
