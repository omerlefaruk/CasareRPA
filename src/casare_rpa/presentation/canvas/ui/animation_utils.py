"""
Animation utilities for CasareRPA Canvas.

Provides throttling, debouncing, and batch update mechanisms to prevent
animation spam and optimize scene repaints.

Usage:
    from casare_rpa.presentation.canvas.ui.animation_utils import (
        AnimationThrottler,
        BatchUpdater,
        EASING_PRESETS,
    )

    # Throttle hover animations
    throttler = AnimationThrottler()
    if throttler.throttle(f"hover_{node.id}", animate, 100):
        animate()

    # Debounce search highlighting
    throttler.debounce("search", lambda: highlight(text), 200)

    # Batch scene updates for single repaint
    batch = BatchUpdater()
    for node in nodes:
        node._selected = True
        batch.schedule_update(node)
    # Single repaint happens automatically on next event loop
"""

from __future__ import annotations

import time
from typing import Callable, Dict, Optional, Set

from loguru import logger
from PySide6.QtCore import QEasingCurve, QObject, QTimer
from PySide6.QtWidgets import QGraphicsItem


# =============================================================================
# EASING PRESETS
# =============================================================================

EASING_PRESETS: Dict[str, QEasingCurve.Type] = {
    # Fade animations - smooth acceleration out
    "FADE_IN": QEasingCurve.Type.OutCubic,
    "FADE_OUT": QEasingCurve.Type.InCubic,
    # Slide/move animations - natural deceleration
    "SLIDE": QEasingCurve.Type.OutCubic,
    "SLIDE_IN": QEasingCurve.Type.OutCubic,
    "SLIDE_OUT": QEasingCurve.Type.InCubic,
    # Bounce effect - playful overshoot
    "BOUNCE": QEasingCurve.Type.OutBack,
    "BOUNCE_IN": QEasingCurve.Type.InBack,
    # Zoom/scale - smooth in-out for transforms
    "ZOOM": QEasingCurve.Type.InOutSine,
    "ZOOM_IN": QEasingCurve.Type.OutCubic,
    "ZOOM_OUT": QEasingCurve.Type.InCubic,
    # Elastic - spring-like effect
    "ELASTIC": QEasingCurve.Type.OutElastic,
    # Linear - constant speed (use sparingly)
    "LINEAR": QEasingCurve.Type.Linear,
    # Hover states - quick response
    "HOVER": QEasingCurve.Type.OutQuad,
    # Selection animations
    "SELECT": QEasingCurve.Type.OutCubic,
    "DESELECT": QEasingCurve.Type.InCubic,
}


def get_easing(preset: str) -> QEasingCurve:
    """
    Get a QEasingCurve instance for the given preset name.

    Args:
        preset: Name of the easing preset (e.g., "FADE_IN", "SLIDE", "BOUNCE").
                Case-insensitive. Falls back to OutCubic if not found.

    Returns:
        QEasingCurve instance configured with the appropriate easing type.

    Example:
        curve = get_easing("FADE_IN")
        animation.setEasingCurve(curve)
    """
    preset_upper = preset.upper()
    easing_type = EASING_PRESETS.get(preset_upper, QEasingCurve.Type.OutCubic)
    return QEasingCurve(easing_type)


# =============================================================================
# ANIMATION THROTTLER
# =============================================================================


class AnimationThrottler(QObject):
    """
    Prevents animation spam from rapid events using throttling and debouncing.

    Throttling: Allows at most one call per interval, dropping intermediate calls.
    Debouncing: Delays execution until calls stop for the specified duration.

    Thread-safe for Qt's single-threaded event loop.

    Example:
        throttler = AnimationThrottler()

        # Throttle: Execute immediately, then ignore for 100ms
        def on_hover():
            if throttler.throttle(f"hover_{node.id}", animate, 100):
                animate()

        # Debounce: Wait until typing stops for 200ms
        def on_search_change(text):
            throttler.debounce("search", lambda: highlight(text), 200)

        # Cancel pending operations
        throttler.cancel("search")

        # Clean up
        throttler.cancel_all()
    """

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """
        Initialize the throttler.

        Args:
            parent: Optional parent QObject for memory management.
        """
        super().__init__(parent)
        self._last_call: Dict[str, float] = {}
        self._debounce_timers: Dict[str, QTimer] = {}
        self._debounce_callbacks: Dict[str, Callable[[], None]] = {}

    def throttle(
        self,
        key: str,
        callback: Callable[[], None],
        min_interval_ms: int = 100,
    ) -> bool:
        """
        Throttle a callback to execute at most once per interval.

        The callback is NOT executed by this method. It returns True if
        the caller should execute the callback, False to skip.

        Args:
            key: Unique identifier for this throttle group (e.g., "hover_node_123").
            callback: The callback function (used for logging/debugging only).
            min_interval_ms: Minimum time between executions in milliseconds.

        Returns:
            True if enough time has passed and callback should execute.
            False if still within throttle window.

        Example:
            if throttler.throttle("hover", animate_hover, 100):
                animate_hover()
        """
        if min_interval_ms <= 0:
            return True

        current_time = time.perf_counter() * 1000  # Convert to ms
        last_time = self._last_call.get(key, 0.0)
        elapsed = current_time - last_time

        if elapsed >= min_interval_ms:
            self._last_call[key] = current_time
            return True

        logger.trace(
            "Throttled callback for key '{}': {:.1f}ms < {}ms threshold",
            key,
            elapsed,
            min_interval_ms,
        )
        return False

    def debounce(
        self,
        key: str,
        callback: Callable[[], None],
        delay_ms: int = 150,
    ) -> None:
        """
        Debounce a callback to execute after calls stop for the delay duration.

        Each call resets the timer. The callback executes only after no calls
        for the specified delay.

        Args:
            key: Unique identifier for this debounce group (e.g., "search").
            callback: The callback function to execute after the delay.
            delay_ms: Time to wait after last call before executing, in ms.

        Example:
            # Called on every keystroke, but executes only after typing stops
            throttler.debounce("search", lambda: highlight(text), 200)
        """
        if delay_ms <= 0:
            try:
                callback()
            except Exception as e:
                logger.error("Debounced callback '{}' raised exception: {}", key, e)
            return

        # Cancel existing timer for this key
        if key in self._debounce_timers:
            self._debounce_timers[key].stop()
            self._debounce_timers[key].deleteLater()

        # Store callback reference
        self._debounce_callbacks[key] = callback

        # Create new timer
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(delay_ms)
        timer.timeout.connect(lambda: self._execute_debounced(key))
        self._debounce_timers[key] = timer
        timer.start()

        logger.trace("Debouncing callback for key '{}' with {}ms delay", key, delay_ms)

    def _execute_debounced(self, key: str) -> None:
        """Execute debounced callback and clean up."""
        callback = self._debounce_callbacks.pop(key, None)
        timer = self._debounce_timers.pop(key, None)

        if timer is not None:
            timer.deleteLater()

        if callback is not None:
            try:
                callback()
                logger.trace("Executed debounced callback for key '{}'", key)
            except Exception as e:
                logger.error("Debounced callback '{}' raised exception: {}", key, e)

    def cancel(self, key: str) -> None:
        """
        Cancel pending debounced callback for a key.

        Does not affect throttle state.

        Args:
            key: The debounce group identifier to cancel.
        """
        if key in self._debounce_timers:
            self._debounce_timers[key].stop()
            self._debounce_timers[key].deleteLater()
            del self._debounce_timers[key]
            self._debounce_callbacks.pop(key, None)
            logger.trace("Cancelled debounced callback for key '{}'", key)

    def cancel_all(self) -> None:
        """
        Cancel all pending debounced callbacks and reset throttle state.

        Call this during cleanup to prevent memory leaks.
        """
        for timer in self._debounce_timers.values():
            timer.stop()
            timer.deleteLater()
        self._debounce_timers.clear()
        self._debounce_callbacks.clear()
        self._last_call.clear()
        logger.trace("Cancelled all throttler state")

    def reset_throttle(self, key: str) -> None:
        """
        Reset throttle timer for a key, allowing immediate execution.

        Args:
            key: The throttle group identifier to reset.
        """
        self._last_call.pop(key, None)


# =============================================================================
# BATCH UPDATER
# =============================================================================


class BatchUpdater(QObject):
    """
    Coalesces multiple scene updates into a single repaint.

    Uses a QTimer with 0ms interval to defer updates to the next event loop
    iteration, allowing multiple items to be marked for update before a
    single repaint occurs.

    Example:
        batch = BatchUpdater()

        # Mark multiple items for update
        for node in selected_nodes:
            node._selected = True
            batch.schedule_update(node)

        # Single repaint happens automatically on next event loop
        # Or force immediate flush:
        batch.flush()
    """

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """
        Initialize the batch updater.

        Args:
            parent: Optional parent QObject for memory management.
        """
        super().__init__(parent)
        self._pending_items: Set[QGraphicsItem] = set()
        self._timer: Optional[QTimer] = None
        self._is_flushing: bool = False

    def schedule_update(self, item: QGraphicsItem) -> None:
        """
        Schedule a graphics item for update on next event loop.

        Multiple calls with the same item are coalesced.

        Args:
            item: QGraphicsItem to update. Must have a valid scene.

        Example:
            batch.schedule_update(node_item)
            batch.schedule_update(connection_item)
            # Both updated in single repaint
        """
        if item is None:
            logger.warning("BatchUpdater.schedule_update called with None item")
            return

        self._pending_items.add(item)

        # Start timer if not already running
        if self._timer is None or not self._timer.isActive():
            self._timer = QTimer(self)
            self._timer.setSingleShot(True)
            self._timer.setInterval(0)  # Execute on next event loop
            self._timer.timeout.connect(self._do_flush)
            self._timer.start()

    def flush(self) -> None:
        """
        Immediately flush all pending updates.

        Safe to call even if no updates are pending.
        Prevents re-entrant flushing.
        """
        if self._timer is not None:
            self._timer.stop()
        self._do_flush()

    def _do_flush(self) -> None:
        """Internal flush implementation with re-entrancy protection."""
        if self._is_flushing:
            return

        self._is_flushing = True
        try:
            if not self._pending_items:
                return

            items = list(self._pending_items)
            self._pending_items.clear()

            update_count = 0
            for item in items:
                try:
                    # Check item is still valid and has a scene
                    if item.scene() is not None:
                        item.update()
                        update_count += 1
                except RuntimeError:
                    # Item was deleted
                    pass

            if update_count > 0:
                logger.trace("BatchUpdater flushed {} items", update_count)

        finally:
            self._is_flushing = False
            if self._timer is not None:
                self._timer.deleteLater()
                self._timer = None

    def clear(self) -> None:
        """
        Clear all pending updates without executing them.

        Useful during scene destruction.
        """
        self._pending_items.clear()
        if self._timer is not None:
            self._timer.stop()
            self._timer.deleteLater()
            self._timer = None

    @property
    def pending_count(self) -> int:
        """Return number of items pending update."""
        return len(self._pending_items)


# =============================================================================
# MODULE-LEVEL SINGLETONS
# =============================================================================

# Global instances for convenience (optional usage)
_global_throttler: Optional[AnimationThrottler] = None
_global_batch_updater: Optional[BatchUpdater] = None


def get_throttler() -> AnimationThrottler:
    """
    Get the global AnimationThrottler instance.

    Creates one on first call. For most use cases, prefer creating
    local instances with appropriate parent objects.

    Returns:
        Global AnimationThrottler singleton.
    """
    global _global_throttler
    if _global_throttler is None:
        _global_throttler = AnimationThrottler()
    return _global_throttler


def get_batch_updater() -> BatchUpdater:
    """
    Get the global BatchUpdater instance.

    Creates one on first call. For most use cases, prefer creating
    local instances with appropriate parent objects.

    Returns:
        Global BatchUpdater singleton.
    """
    global _global_batch_updater
    if _global_batch_updater is None:
        _global_batch_updater = BatchUpdater()
    return _global_batch_updater


__all__ = [
    "EASING_PRESETS",
    "get_easing",
    "AnimationThrottler",
    "BatchUpdater",
    "get_throttler",
    "get_batch_updater",
]
