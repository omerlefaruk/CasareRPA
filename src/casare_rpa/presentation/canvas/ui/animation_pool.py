"""
Animation object pool for high-performance UI animations.

Prevents GC churn by reusing QPropertyAnimation instances instead of
creating/destroying them repeatedly.

Usage:
    anim = AnimationPool.acquire("fade")
    anim.setTargetObject(widget)
    anim.setPropertyName(b"windowOpacity")
    anim.setDuration(150)
    anim.setStartValue(0)
    anim.setEndValue(1)
    anim.finished.connect(lambda: AnimationPool.release(anim, "fade"))
    anim.start()

Pool Sizes:
    - fade: 20 (most common for node hover, selection)
    - slide: 20 (panel transitions, popups)
    - scale: 10 (zoom effects, emphasis)
    - color: 10 (status changes, highlights)

Thread Safety:
    Uses threading.Lock for thread-safe singleton and pool access.
    Safe to use from Qt main thread and worker threads.
"""

import threading
from typing import Dict, List, Optional

from loguru import logger
from PySide6.QtCore import QEasingCurve, QPropertyAnimation

from casare_rpa.presentation.canvas.ui.theme import Theme


# =============================================================================
# POOL CONFIGURATION
# =============================================================================

POOL_SIZES: Dict[str, int] = {
    "fade": 20,
    "slide": 20,
    "scale": 10,
    "color": 10,
}

# Default animation durations (ms) per type
DEFAULT_DURATIONS: Dict[str, int] = {
    "fade": 150,
    "slide": 200,
    "scale": 150,
    "color": 200,
}

# Default easing curves per type
DEFAULT_EASINGS: Dict[str, QEasingCurve.Type] = {
    "fade": QEasingCurve.Type.OutCubic,
    "slide": QEasingCurve.Type.OutCubic,
    "scale": QEasingCurve.Type.OutBack,
    "color": QEasingCurve.Type.InOutQuad,
}


# =============================================================================
# ANIMATION POOL SINGLETON
# =============================================================================


class AnimationPool:
    """
    Thread-safe singleton pool for QPropertyAnimation instances.

    Implements the object pool pattern to minimize animation object
    creation/destruction overhead. Pre-allocates animations at startup
    and reuses them throughout the application lifecycle.

    Attributes:
        _instance: Singleton instance
        _lock: Thread lock for singleton creation
        _pools: Dictionary of animation pools by type
        _pool_locks: Per-pool locks for concurrent access
        _stats: Pool usage statistics
    """

    _instance: Optional["AnimationPool"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "AnimationPool":
        """Thread-safe singleton creation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize the animation pool (only once)."""
        if self._initialized:
            return

        self._pools: Dict[str, List[QPropertyAnimation]] = {
            anim_type: [] for anim_type in POOL_SIZES
        }
        self._pool_locks: Dict[str, threading.Lock] = {
            anim_type: threading.Lock() for anim_type in POOL_SIZES
        }
        self._stats: Dict[str, Dict[str, int]] = {
            anim_type: {"acquired": 0, "released": 0, "created": 0, "exhausted": 0}
            for anim_type in POOL_SIZES
        }
        self._initialized = True
        logger.debug("AnimationPool initialized")

    # =========================================================================
    # CLASS METHODS (PUBLIC API)
    # =========================================================================

    @classmethod
    def acquire(cls, anim_type: str) -> QPropertyAnimation:
        """
        Acquire an animation from the pool.

        Gets a pre-allocated animation if available, otherwise creates a new one.
        The animation is reset to default state before returning.

        Args:
            anim_type: Type of animation ("fade", "slide", "scale", "color")

        Returns:
            A QPropertyAnimation instance ready for configuration.

        Raises:
            ValueError: If anim_type is not a valid pool type.

        Example:
            anim = AnimationPool.acquire("fade")
            anim.setTargetObject(my_widget)
            anim.setPropertyName(b"windowOpacity")
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.finished.connect(lambda: AnimationPool.release(anim, "fade"))
            anim.start()
        """
        instance = cls()
        return instance._acquire(anim_type)

    @classmethod
    def release(cls, animation: QPropertyAnimation, anim_type: str) -> None:
        """
        Return an animation to the pool.

        Resets the animation state and returns it to the pool for reuse.
        Should be called when the animation finishes.

        Args:
            animation: The animation instance to release.
            anim_type: Type of animation pool to return to.

        Example:
            anim.finished.connect(lambda: AnimationPool.release(anim, "fade"))
        """
        instance = cls()
        instance._release(animation, anim_type)

    @classmethod
    def prewarm(cls) -> None:
        """
        Pre-allocate all animation pools at startup.

        Call this during application initialization to avoid allocation
        delays during first use. Creates all animations in their respective
        pools up to the configured pool sizes.

        Example:
            # In main window initialization
            AnimationPool.prewarm()
        """
        instance = cls()
        instance._prewarm()

    @classmethod
    def get_stats(cls) -> Dict[str, Dict[str, int]]:
        """
        Get pool usage statistics.

        Returns:
            Dictionary with per-type stats including:
            - acquired: Total acquisitions
            - released: Total releases
            - created: Dynamically created (exceeded pool)
            - exhausted: Times pool was empty

        Example:
            stats = AnimationPool.get_stats()
            logger.info(f"Fade pool stats: {stats['fade']}")
        """
        instance = cls()
        return dict(instance._stats)

    @classmethod
    def get_pool_status(cls) -> Dict[str, Dict[str, int]]:
        """
        Get current pool status.

        Returns:
            Dictionary with per-type status:
            - available: Animations currently in pool
            - capacity: Configured pool size
        """
        instance = cls()
        return {
            anim_type: {
                "available": len(instance._pools[anim_type]),
                "capacity": POOL_SIZES[anim_type],
            }
            for anim_type in POOL_SIZES
        }

    @classmethod
    def clear(cls) -> None:
        """
        Clear all pools and reset statistics.

        Use for cleanup during shutdown or testing.
        """
        instance = cls()
        for anim_type in POOL_SIZES:
            with instance._pool_locks[anim_type]:
                instance._pools[anim_type].clear()
                instance._stats[anim_type] = {
                    "acquired": 0,
                    "released": 0,
                    "created": 0,
                    "exhausted": 0,
                }
        logger.debug("AnimationPool cleared")

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    def _acquire(self, anim_type: str) -> QPropertyAnimation:
        """Internal acquire implementation."""
        if anim_type not in POOL_SIZES:
            raise ValueError(
                f"Invalid animation type '{anim_type}'. "
                f"Valid types: {list(POOL_SIZES.keys())}"
            )

        with self._pool_locks[anim_type]:
            self._stats[anim_type]["acquired"] += 1

            if self._pools[anim_type]:
                animation = self._pools[anim_type].pop()
                self._reset_animation(animation, anim_type)
                return animation

            # Pool exhausted - create new animation
            self._stats[anim_type]["exhausted"] += 1
            self._stats[anim_type]["created"] += 1

            if self._stats[anim_type]["exhausted"] % 5 == 1:
                logger.warning(
                    f"AnimationPool '{anim_type}' exhausted "
                    f"(exhausted_count={self._stats[anim_type]['exhausted']}, "
                    f"pool_size={POOL_SIZES[anim_type]}). "
                    f"Consider increasing pool size."
                )

            return self._create_animation(anim_type)

    def _release(self, animation: QPropertyAnimation, anim_type: str) -> None:
        """Internal release implementation."""
        if anim_type not in POOL_SIZES:
            logger.warning(f"Cannot release animation: invalid type '{anim_type}'")
            return

        # Stop animation if running
        if animation.state() == QPropertyAnimation.State.Running:
            animation.stop()

        # Disconnect all signals to prevent memory leaks
        try:
            animation.finished.disconnect()
        except (RuntimeError, TypeError):
            pass  # No connections or already disconnected

        try:
            animation.stateChanged.disconnect()
        except (RuntimeError, TypeError):
            pass

        try:
            animation.valueChanged.disconnect()
        except (RuntimeError, TypeError):
            pass

        with self._pool_locks[anim_type]:
            self._stats[anim_type]["released"] += 1

            # Only return to pool if under capacity
            if len(self._pools[anim_type]) < POOL_SIZES[anim_type]:
                self._reset_animation(animation, anim_type)
                self._pools[anim_type].append(animation)

    def _prewarm(self) -> None:
        """Pre-allocate all pools to capacity."""
        total_created = 0
        for anim_type, size in POOL_SIZES.items():
            with self._pool_locks[anim_type]:
                current_size = len(self._pools[anim_type])
                needed = size - current_size
                for _ in range(needed):
                    animation = self._create_animation(anim_type)
                    self._pools[anim_type].append(animation)
                total_created += needed

        logger.info(
            f"AnimationPool prewarmed: {total_created} animations created "
            f"(fade={POOL_SIZES['fade']}, slide={POOL_SIZES['slide']}, "
            f"scale={POOL_SIZES['scale']}, color={POOL_SIZES['color']})"
        )

    def _create_animation(self, anim_type: str) -> QPropertyAnimation:
        """Create a new animation with default settings for the type."""
        animation = QPropertyAnimation()
        self._reset_animation(animation, anim_type)
        return animation

    def _reset_animation(self, animation: QPropertyAnimation, anim_type: str) -> None:
        """Reset animation to default state for reuse."""
        # Clear target (must be set by caller)
        animation.setTargetObject(None)

        # Set type-specific defaults
        animation.setDuration(DEFAULT_DURATIONS.get(anim_type, 150))
        animation.setEasingCurve(
            DEFAULT_EASINGS.get(anim_type, QEasingCurve.Type.OutCubic)
        )

        # Reset value ranges
        animation.setStartValue(None)
        animation.setEndValue(None)

        # Clear property name (must be set by caller)
        animation.setPropertyName(b"")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def create_fade_animation(
    target: object,
    start_opacity: float = 0.0,
    end_opacity: float = 1.0,
    duration: Optional[int] = None,
    on_finished: Optional[callable] = None,
) -> QPropertyAnimation:
    """
    Create a configured fade animation from the pool.

    Args:
        target: Widget to animate (must have windowOpacity property).
        start_opacity: Starting opacity (0.0-1.0).
        end_opacity: Ending opacity (0.0-1.0).
        duration: Animation duration in ms (default: 150).
        on_finished: Callback when animation completes.

    Returns:
        Configured QPropertyAnimation ready to start.

    Example:
        anim = create_fade_animation(popup, 0.0, 1.0, on_finished=cleanup)
        anim.start()
    """
    anim = AnimationPool.acquire("fade")
    anim.setTargetObject(target)
    anim.setPropertyName(b"windowOpacity")
    anim.setStartValue(start_opacity)
    anim.setEndValue(end_opacity)

    if duration is not None:
        anim.setDuration(duration)

    def release_and_callback() -> None:
        AnimationPool.release(anim, "fade")
        if on_finished:
            on_finished()

    anim.finished.connect(release_and_callback)
    return anim


def create_slide_animation(
    target: object,
    property_name: bytes,
    start_value: object,
    end_value: object,
    duration: Optional[int] = None,
    on_finished: Optional[callable] = None,
) -> QPropertyAnimation:
    """
    Create a configured slide animation from the pool.

    Args:
        target: Widget to animate.
        property_name: Property to animate (e.g., b"pos", b"geometry").
        start_value: Starting value (QPoint, QRect, etc.).
        end_value: Ending value.
        duration: Animation duration in ms (default: 200).
        on_finished: Callback when animation completes.

    Returns:
        Configured QPropertyAnimation ready to start.

    Example:
        anim = create_slide_animation(
            panel, b"pos",
            QPoint(-200, 0), QPoint(0, 0)
        )
        anim.start()
    """
    anim = AnimationPool.acquire("slide")
    anim.setTargetObject(target)
    anim.setPropertyName(property_name)
    anim.setStartValue(start_value)
    anim.setEndValue(end_value)

    if duration is not None:
        anim.setDuration(duration)

    def release_and_callback() -> None:
        AnimationPool.release(anim, "slide")
        if on_finished:
            on_finished()

    anim.finished.connect(release_and_callback)
    return anim


def create_scale_animation(
    target: object,
    property_name: bytes,
    start_value: object,
    end_value: object,
    duration: Optional[int] = None,
    on_finished: Optional[callable] = None,
) -> QPropertyAnimation:
    """
    Create a configured scale animation from the pool.

    Args:
        target: Widget to animate.
        property_name: Property to animate (e.g., b"size", b"geometry").
        start_value: Starting value.
        end_value: Ending value.
        duration: Animation duration in ms (default: 150).
        on_finished: Callback when animation completes.

    Returns:
        Configured QPropertyAnimation ready to start.

    Example:
        anim = create_scale_animation(
            node, b"size",
            QSize(100, 50), QSize(120, 60)
        )
        anim.start()
    """
    anim = AnimationPool.acquire("scale")
    anim.setTargetObject(target)
    anim.setPropertyName(property_name)
    anim.setStartValue(start_value)
    anim.setEndValue(end_value)

    if duration is not None:
        anim.setDuration(duration)

    def release_and_callback() -> None:
        AnimationPool.release(anim, "scale")
        if on_finished:
            on_finished()

    anim.finished.connect(release_and_callback)
    return anim


def create_color_animation(
    target: object,
    property_name: bytes,
    start_color: object,
    end_color: object,
    duration: Optional[int] = None,
    on_finished: Optional[callable] = None,
) -> QPropertyAnimation:
    """
    Create a configured color animation from the pool.

    Args:
        target: Widget to animate (must have color property).
        property_name: Property to animate (e.g., b"color", b"backgroundColor").
        start_color: Starting QColor.
        end_color: Ending QColor.
        duration: Animation duration in ms (default: 200).
        on_finished: Callback when animation completes.

    Returns:
        Configured QPropertyAnimation ready to start.

    Example:
        anim = create_color_animation(
            indicator, b"color",
            QColor("#666666"), QColor("#00FF00")
        )
        anim.start()
    """
    anim = AnimationPool.acquire("color")
    anim.setTargetObject(target)
    anim.setPropertyName(property_name)
    anim.setStartValue(start_color)
    anim.setEndValue(end_color)

    if duration is not None:
        anim.setDuration(duration)

    def release_and_callback() -> None:
        AnimationPool.release(anim, "color")
        if on_finished:
            on_finished()

    anim.finished.connect(release_and_callback)
    return anim
