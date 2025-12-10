"""
UIAnimator - Centralized animation utilities for CasareRPA UI.

Provides static methods for common animation patterns with:
- Automatic animation object pooling
- LOD-aware duration scaling
- Accessibility support (reduced motion)
- Automatic cleanup on completion

Usage:
    from casare_rpa.presentation.canvas.ui.animation import UIAnimator

    # Simple fade in
    UIAnimator.fade_in(dialog, duration=200)

    # Fade out then close
    UIAnimator.fade_out(popup, on_finished=popup.close)

    # Slide panel in from right
    UIAnimator.slide_in(panel, direction="right", duration=250)

    # Shake on validation error
    UIAnimator.shake(input_field)
"""

import platform
from typing import Callable, Dict, List, Optional, Union

from loguru import logger
from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QObject,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    QVariantAnimation,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsItem, QGraphicsOpacityEffect, QWidget

from casare_rpa.presentation.canvas.graph.lod_manager import LODLevel, get_lod_manager
from casare_rpa.presentation.canvas.ui.theme import ANIMATIONS


# =============================================================================
# ACCESSIBILITY: REDUCED MOTION DETECTION
# =============================================================================


class AccessibilitySettings:
    """Check system accessibility preferences."""

    _cached_reduced_motion: Optional[bool] = None

    @classmethod
    def prefers_reduced_motion(cls) -> bool:
        """
        Check if user prefers reduced motion.

        Caches result to avoid repeated system calls.

        Returns:
            True if user has reduced motion enabled
        """
        if cls._cached_reduced_motion is not None:
            return cls._cached_reduced_motion

        cls._cached_reduced_motion = cls._detect_reduced_motion()
        return cls._cached_reduced_motion

    @classmethod
    def _detect_reduced_motion(cls) -> bool:
        """Detect reduced motion preference from OS."""
        system = platform.system()

        if system == "Windows":
            try:
                import ctypes

                SPI_GETCLIENTAREAANIMATION = 0x1042
                result = ctypes.c_bool()
                ctypes.windll.user32.SystemParametersInfoW(
                    SPI_GETCLIENTAREAANIMATION, 0, ctypes.byref(result), 0
                )
                # False = animations disabled = prefers reduced motion
                return not result.value
            except Exception as e:
                logger.debug(f"Could not detect Windows animation setting: {e}")
                return False

        elif system == "Darwin":  # macOS
            try:
                from AppKit import NSWorkspace

                return NSWorkspace.sharedWorkspace().accessibilityDisplayShouldReduceMotion()
            except Exception as e:
                logger.debug(f"Could not detect macOS reduced motion setting: {e}")
                return False

        return False

    @classmethod
    def reset_cache(cls) -> None:
        """Reset the cached value (for testing or settings change)."""
        cls._cached_reduced_motion = None


# =============================================================================
# ANIMATION LOD SETTINGS
# =============================================================================


class AnimationLOD:
    """LOD-based animation duration multipliers."""

    # Duration multipliers by LOD level
    # At lower LOD (zoomed out), reduce animation durations for performance
    _MULTIPLIERS: Dict[LODLevel, float] = {
        LODLevel.ULTRA_LOW: 0.0,  # Instant - no animations
        LODLevel.LOW: 0.5,  # 50% duration
        LODLevel.MEDIUM: 0.75,  # 75% duration
        LODLevel.FULL: 1.0,  # Full duration
    }

    @classmethod
    def get_multiplier(cls) -> float:
        """
        Get current LOD-based duration multiplier.

        Returns:
            Float multiplier (0.0 to 1.0)
        """
        lod = get_lod_manager().current_lod
        return cls._MULTIPLIERS.get(lod, 1.0)

    @classmethod
    def should_animate(cls) -> bool:
        """
        Whether animations should run at current LOD.

        Returns:
            True if multiplier > 0
        """
        return cls.get_multiplier() > 0


# =============================================================================
# ANIMATION POOL
# =============================================================================


class AnimationPool:
    """
    Object pool for animation instances.

    Reuses animation objects to reduce garbage collection overhead.
    """

    # Pool storage by animation type
    _pools: Dict[str, List[QAbstractAnimation]] = {
        "property": [],
        "sequential": [],
        "parallel": [],
        "variant": [],
    }

    # Maximum pool size per type
    _MAX_POOL_SIZE = 20

    @classmethod
    def acquire_property(
        cls, target: QObject, property_name: bytes
    ) -> QPropertyAnimation:
        """
        Acquire a QPropertyAnimation from pool or create new.

        Args:
            target: Target QObject for animation
            property_name: Property to animate (e.g. b"opacity")

        Returns:
            QPropertyAnimation instance
        """
        pool = cls._pools["property"]
        if pool:
            anim = pool.pop()
            anim.setTargetObject(target)
            anim.setPropertyName(property_name)
            return anim

        return QPropertyAnimation(target, property_name)

    @classmethod
    def acquire_sequential(cls) -> QSequentialAnimationGroup:
        """
        Acquire a QSequentialAnimationGroup from pool or create new.

        Returns:
            QSequentialAnimationGroup instance
        """
        pool = cls._pools["sequential"]
        if pool:
            group = pool.pop()
            group.clear()
            return group

        return QSequentialAnimationGroup()

    @classmethod
    def acquire_parallel(cls) -> QParallelAnimationGroup:
        """
        Acquire a QParallelAnimationGroup from pool or create new.

        Returns:
            QParallelAnimationGroup instance
        """
        pool = cls._pools["parallel"]
        if pool:
            group = pool.pop()
            group.clear()
            return group

        return QParallelAnimationGroup()

    @classmethod
    def acquire_variant(cls) -> QVariantAnimation:
        """
        Acquire a QVariantAnimation from pool or create new.

        Returns:
            QVariantAnimation instance
        """
        pool = cls._pools["variant"]
        if pool:
            return pool.pop()

        return QVariantAnimation()

    @classmethod
    def release(cls, anim: QAbstractAnimation, pool_type: str) -> None:
        """
        Release an animation back to pool.

        Args:
            anim: Animation to release
            pool_type: Type key ("property", "sequential", "parallel", "variant")
        """
        pool = cls._pools.get(pool_type)
        if pool is None:
            return

        if len(pool) < cls._MAX_POOL_SIZE:
            # Disconnect signals to prevent stale callbacks
            try:
                anim.finished.disconnect()
            except (RuntimeError, TypeError):
                pass

            pool.append(anim)

    @classmethod
    def clear_all(cls) -> None:
        """Clear all pools."""
        for pool in cls._pools.values():
            pool.clear()


# =============================================================================
# UI ANIMATOR - MAIN CLASS
# =============================================================================


class UIAnimator:
    """
    Factory for common UI animations.

    All methods respect:
    - Accessibility (reduced motion)
    - LOD-based duration scaling
    - Automatic cleanup via animation pool

    Usage:
        UIAnimator.fade_in(widget)
        UIAnimator.slide_out(panel, direction="right")
        UIAnimator.shake(input_field)
    """

    # ==========================================================================
    # INTERNAL HELPERS
    # ==========================================================================

    @staticmethod
    def _get_effective_duration(base_duration: int) -> int:
        """
        Apply LOD multiplier and reduced motion to duration.

        Args:
            base_duration: Requested duration in milliseconds

        Returns:
            Effective duration (0 if reduced motion or ULTRA_LOW LOD)
        """
        # Check accessibility first
        if AccessibilitySettings.prefers_reduced_motion():
            return 0

        # Apply LOD multiplier
        multiplier = AnimationLOD.get_multiplier()
        return int(base_duration * multiplier)

    @staticmethod
    def _setup_cleanup(
        anim: QAbstractAnimation,
        pool_type: str,
        on_finished: Optional[Callable] = None,
    ) -> None:
        """
        Setup automatic cleanup and callback on animation finish.

        Args:
            anim: Animation to setup
            pool_type: Pool type for release
            on_finished: Optional callback to run on finish
        """

        def _cleanup() -> None:
            if on_finished:
                try:
                    on_finished()
                except Exception as e:
                    logger.debug(f"Animation callback error: {e}")
            AnimationPool.release(anim, pool_type)

        anim.finished.connect(_cleanup)

    @staticmethod
    def _get_or_create_opacity_effect(widget: QWidget) -> QGraphicsOpacityEffect:
        """
        Get existing opacity effect or create new one.

        Args:
            widget: Widget to get/create effect for

        Returns:
            QGraphicsOpacityEffect attached to widget
        """
        effect = widget.graphicsEffect()
        if isinstance(effect, QGraphicsOpacityEffect):
            return effect

        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        return effect

    # ==========================================================================
    # FADE ANIMATIONS
    # ==========================================================================

    @staticmethod
    def fade_in(
        widget: QWidget,
        duration: int = 150,
        easing: QEasingCurve.Type = QEasingCurve.Type.OutCubic,
        on_finished: Optional[Callable] = None,
    ) -> Optional[QPropertyAnimation]:
        """
        Fade in a widget from transparent to opaque.

        Args:
            widget: Widget to animate
            duration: Base duration in milliseconds
            easing: Easing curve type
            on_finished: Optional callback when complete

        Returns:
            QPropertyAnimation or None if instant (reduced motion/LOD)
        """
        effective_duration = UIAnimator._get_effective_duration(duration)

        effect = UIAnimator._get_or_create_opacity_effect(widget)

        if effective_duration == 0:
            # Instant - no animation
            effect.setOpacity(1.0)
            if on_finished:
                on_finished()
            return None

        effect.setOpacity(0.0)

        anim = AnimationPool.acquire_property(effect, b"opacity")
        anim.setDuration(effective_duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(easing)

        UIAnimator._setup_cleanup(anim, "property", on_finished)
        anim.start()

        return anim

    @staticmethod
    def fade_out(
        widget: QWidget,
        duration: int = 100,
        easing: QEasingCurve.Type = QEasingCurve.Type.InCubic,
        on_finished: Optional[Callable] = None,
    ) -> Optional[QPropertyAnimation]:
        """
        Fade out a widget from opaque to transparent.

        Args:
            widget: Widget to animate
            duration: Base duration in milliseconds
            easing: Easing curve type
            on_finished: Optional callback when complete

        Returns:
            QPropertyAnimation or None if instant
        """
        effective_duration = UIAnimator._get_effective_duration(duration)

        effect = UIAnimator._get_or_create_opacity_effect(widget)

        if effective_duration == 0:
            effect.setOpacity(0.0)
            if on_finished:
                on_finished()
            return None

        effect.setOpacity(1.0)

        anim = AnimationPool.acquire_property(effect, b"opacity")
        anim.setDuration(effective_duration)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(easing)

        UIAnimator._setup_cleanup(anim, "property", on_finished)
        anim.start()

        return anim

    # ==========================================================================
    # SLIDE ANIMATIONS
    # ==========================================================================

    @staticmethod
    def slide_in(
        widget: QWidget,
        direction: str = "left",
        distance: int = 50,
        duration: int = 200,
        easing: QEasingCurve.Type = QEasingCurve.Type.OutCubic,
        on_finished: Optional[Callable] = None,
    ) -> Optional[QPropertyAnimation]:
        """
        Slide a widget in from off-screen.

        Args:
            widget: Widget to animate
            direction: "left", "right", "up", or "down"
            distance: Pixels to slide from
            duration: Base duration in milliseconds
            easing: Easing curve type
            on_finished: Optional callback when complete

        Returns:
            QPropertyAnimation or None if instant
        """
        effective_duration = UIAnimator._get_effective_duration(duration)

        target_pos = widget.pos()

        # Calculate start position based on direction
        offsets = {
            "left": QPoint(-distance, 0),
            "right": QPoint(distance, 0),
            "up": QPoint(0, -distance),
            "down": QPoint(0, distance),
        }
        offset = offsets.get(direction, QPoint(-distance, 0))
        start_pos = target_pos + offset

        if effective_duration == 0:
            widget.move(target_pos)
            if on_finished:
                on_finished()
            return None

        widget.move(start_pos)

        anim = AnimationPool.acquire_property(widget, b"pos")
        anim.setDuration(effective_duration)
        anim.setStartValue(start_pos)
        anim.setEndValue(target_pos)
        anim.setEasingCurve(easing)

        UIAnimator._setup_cleanup(anim, "property", on_finished)
        anim.start()

        return anim

    @staticmethod
    def slide_out(
        widget: QWidget,
        direction: str = "left",
        distance: int = 50,
        duration: int = 150,
        easing: QEasingCurve.Type = QEasingCurve.Type.InCubic,
        on_finished: Optional[Callable] = None,
    ) -> Optional[QPropertyAnimation]:
        """
        Slide a widget out to off-screen.

        Args:
            widget: Widget to animate
            direction: "left", "right", "up", or "down"
            distance: Pixels to slide to
            duration: Base duration in milliseconds
            easing: Easing curve type
            on_finished: Optional callback when complete

        Returns:
            QPropertyAnimation or None if instant
        """
        effective_duration = UIAnimator._get_effective_duration(duration)

        start_pos = widget.pos()

        # Calculate end position based on direction
        offsets = {
            "left": QPoint(-distance, 0),
            "right": QPoint(distance, 0),
            "up": QPoint(0, -distance),
            "down": QPoint(0, distance),
        }
        offset = offsets.get(direction, QPoint(-distance, 0))
        end_pos = start_pos + offset

        if effective_duration == 0:
            widget.move(end_pos)
            if on_finished:
                on_finished()
            return None

        anim = AnimationPool.acquire_property(widget, b"pos")
        anim.setDuration(effective_duration)
        anim.setStartValue(start_pos)
        anim.setEndValue(end_pos)
        anim.setEasingCurve(easing)

        UIAnimator._setup_cleanup(anim, "property", on_finished)
        anim.start()

        return anim

    # ==========================================================================
    # SCALE ANIMATIONS (for QGraphicsItems)
    # ==========================================================================

    @staticmethod
    def scale_in(
        item: QGraphicsItem,
        from_scale: float = 0.8,
        duration: int = 200,
        easing: QEasingCurve.Type = QEasingCurve.Type.OutCubic,
        on_finished: Optional[Callable] = None,
    ) -> Optional[QVariantAnimation]:
        """
        Scale a graphics item in from smaller size.

        Args:
            item: QGraphicsItem to animate
            from_scale: Starting scale factor
            duration: Base duration in milliseconds
            easing: Easing curve type
            on_finished: Optional callback when complete

        Returns:
            QVariantAnimation or None if instant
        """
        effective_duration = UIAnimator._get_effective_duration(duration)

        if effective_duration == 0:
            item.setScale(1.0)
            if on_finished:
                on_finished()
            return None

        item.setScale(from_scale)

        anim = AnimationPool.acquire_variant()
        anim.setDuration(effective_duration)
        anim.setStartValue(from_scale)
        anim.setEndValue(1.0)
        anim.setEasingCurve(easing)

        def _update_scale(value: float) -> None:
            try:
                item.setScale(value)
            except RuntimeError:
                pass  # Item may be destroyed

        anim.valueChanged.connect(_update_scale)

        UIAnimator._setup_cleanup(anim, "variant", on_finished)
        anim.start()

        return anim

    @staticmethod
    def scale_out(
        item: QGraphicsItem,
        to_scale: float = 0.8,
        duration: int = 150,
        easing: QEasingCurve.Type = QEasingCurve.Type.InCubic,
        on_finished: Optional[Callable] = None,
    ) -> Optional[QVariantAnimation]:
        """
        Scale a graphics item out to smaller size.

        Args:
            item: QGraphicsItem to animate
            to_scale: Ending scale factor
            duration: Base duration in milliseconds
            easing: Easing curve type
            on_finished: Optional callback when complete

        Returns:
            QVariantAnimation or None if instant
        """
        effective_duration = UIAnimator._get_effective_duration(duration)

        if effective_duration == 0:
            item.setScale(to_scale)
            if on_finished:
                on_finished()
            return None

        current_scale = item.scale()

        anim = AnimationPool.acquire_variant()
        anim.setDuration(effective_duration)
        anim.setStartValue(current_scale)
        anim.setEndValue(to_scale)
        anim.setEasingCurve(easing)

        def _update_scale(value: float) -> None:
            try:
                item.setScale(value)
            except RuntimeError:
                pass  # Item may be destroyed

        anim.valueChanged.connect(_update_scale)

        UIAnimator._setup_cleanup(anim, "variant", on_finished)
        anim.start()

        return anim

    # ==========================================================================
    # ATTENTION ANIMATIONS
    # ==========================================================================

    @staticmethod
    def shake(
        widget: QWidget,
        intensity: int = 5,
        duration: int = 300,
        on_finished: Optional[Callable] = None,
    ) -> Optional[QSequentialAnimationGroup]:
        """
        Shake a widget horizontally (error/attention animation).

        Args:
            widget: Widget to animate
            intensity: Pixels to shake left/right
            duration: Total duration in milliseconds
            on_finished: Optional callback when complete

        Returns:
            QSequentialAnimationGroup or None if instant
        """
        effective_duration = UIAnimator._get_effective_duration(duration)

        if effective_duration == 0:
            if on_finished:
                on_finished()
            return None

        original_pos = widget.pos()

        # Create shake sequence: left, right, left, right, center
        group = AnimationPool.acquire_sequential()

        # Number of shakes
        num_shakes = 4
        shake_duration = effective_duration // (num_shakes + 1)

        positions = [
            QPoint(original_pos.x() - intensity, original_pos.y()),
            QPoint(original_pos.x() + intensity, original_pos.y()),
            QPoint(original_pos.x() - intensity // 2, original_pos.y()),
            QPoint(original_pos.x() + intensity // 2, original_pos.y()),
            original_pos,  # Return to center
        ]

        current_pos = original_pos
        for target_pos in positions:
            anim = QPropertyAnimation(widget, b"pos")
            anim.setDuration(shake_duration)
            anim.setStartValue(current_pos)
            anim.setEndValue(target_pos)
            anim.setEasingCurve(QEasingCurve.Type.OutQuad)
            group.addAnimation(anim)
            current_pos = target_pos

        UIAnimator._setup_cleanup(group, "sequential", on_finished)
        group.start()

        return group

    @staticmethod
    def pulse_glow(
        widget: QWidget,
        color: QColor,
        cycles: int = 2,
        duration: int = 600,
        on_finished: Optional[Callable] = None,
    ) -> Optional[QSequentialAnimationGroup]:
        """
        Pulse a glow effect on a widget (attention/success animation).

        Note: This modifies the widget's stylesheet. Ensure the widget
        supports border styling.

        Args:
            widget: Widget to animate
            color: Glow color
            cycles: Number of pulse cycles
            duration: Total duration in milliseconds
            on_finished: Optional callback when complete

        Returns:
            QSequentialAnimationGroup or None if instant
        """
        effective_duration = UIAnimator._get_effective_duration(duration)

        if effective_duration == 0:
            if on_finished:
                on_finished()
            return None

        group = AnimationPool.acquire_sequential()

        cycle_duration = effective_duration // cycles
        half_cycle = cycle_duration // 2

        # Each cycle: fade in glow, fade out glow
        for _ in range(cycles):
            # Fade in
            anim_in = QVariantAnimation()
            anim_in.setDuration(half_cycle)
            anim_in.setStartValue(0.0)
            anim_in.setEndValue(1.0)
            anim_in.setEasingCurve(QEasingCurve.Type.OutQuad)

            def _update_glow_in(
                value: float, w: QWidget = widget, c: QColor = color
            ) -> None:
                try:
                    alpha = int(value * 150)
                    glow_color = QColor(c.red(), c.green(), c.blue(), alpha)
                    w.setStyleSheet(
                        f"border: 2px solid rgba({c.red()},{c.green()},{c.blue()},{alpha});"
                    )
                except RuntimeError:
                    pass

            anim_in.valueChanged.connect(_update_glow_in)
            group.addAnimation(anim_in)

            # Fade out
            anim_out = QVariantAnimation()
            anim_out.setDuration(half_cycle)
            anim_out.setStartValue(1.0)
            anim_out.setEndValue(0.0)
            anim_out.setEasingCurve(QEasingCurve.Type.InQuad)

            def _update_glow_out(
                value: float, w: QWidget = widget, c: QColor = color
            ) -> None:
                try:
                    alpha = int(value * 150)
                    w.setStyleSheet(
                        f"border: 2px solid rgba({c.red()},{c.green()},{c.blue()},{alpha});"
                    )
                except RuntimeError:
                    pass

            anim_out.valueChanged.connect(_update_glow_out)
            group.addAnimation(anim_out)

        # Clear style at end
        def _clear_style() -> None:
            try:
                widget.setStyleSheet("")
            except RuntimeError:
                pass
            if on_finished:
                on_finished()

        UIAnimator._setup_cleanup(group, "sequential", _clear_style)
        group.start()

        return group

    # ==========================================================================
    # COMBINED ANIMATIONS
    # ==========================================================================

    @staticmethod
    def combined(
        animations: List[QAbstractAnimation],
        parallel: bool = True,
        on_finished: Optional[Callable] = None,
    ) -> Optional[Union[QParallelAnimationGroup, QSequentialAnimationGroup]]:
        """
        Combine multiple animations into a group.

        Args:
            animations: List of animations to combine
            parallel: True for parallel, False for sequential
            on_finished: Optional callback when all complete

        Returns:
            Animation group or None if no animations
        """
        if not animations:
            if on_finished:
                on_finished()
            return None

        if parallel:
            group = AnimationPool.acquire_parallel()
            pool_type = "parallel"
        else:
            group = AnimationPool.acquire_sequential()
            pool_type = "sequential"

        for anim in animations:
            group.addAnimation(anim)

        UIAnimator._setup_cleanup(group, pool_type, on_finished)
        group.start()

        return group

    # ==========================================================================
    # WINDOW ANIMATIONS
    # ==========================================================================

    @staticmethod
    def fade_window_in(
        window: QWidget,
        duration: int = 150,
        easing: QEasingCurve.Type = QEasingCurve.Type.OutCubic,
        on_finished: Optional[Callable] = None,
    ) -> Optional[QPropertyAnimation]:
        """
        Fade in a window/dialog using windowOpacity.

        Args:
            window: Window to animate
            duration: Base duration in milliseconds
            easing: Easing curve type
            on_finished: Optional callback when complete

        Returns:
            QPropertyAnimation or None if instant
        """
        effective_duration = UIAnimator._get_effective_duration(duration)

        if effective_duration == 0:
            window.setWindowOpacity(1.0)
            if on_finished:
                on_finished()
            return None

        window.setWindowOpacity(0.0)

        anim = AnimationPool.acquire_property(window, b"windowOpacity")
        anim.setDuration(effective_duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(easing)

        UIAnimator._setup_cleanup(anim, "property", on_finished)
        anim.start()

        return anim

    @staticmethod
    def fade_window_out(
        window: QWidget,
        duration: int = 100,
        easing: QEasingCurve.Type = QEasingCurve.Type.InCubic,
        on_finished: Optional[Callable] = None,
    ) -> Optional[QPropertyAnimation]:
        """
        Fade out a window/dialog using windowOpacity.

        Args:
            window: Window to animate
            duration: Base duration in milliseconds
            easing: Easing curve type
            on_finished: Optional callback when complete

        Returns:
            QPropertyAnimation or None if instant
        """
        effective_duration = UIAnimator._get_effective_duration(duration)

        if effective_duration == 0:
            window.setWindowOpacity(0.0)
            if on_finished:
                on_finished()
            return None

        window.setWindowOpacity(1.0)

        anim = AnimationPool.acquire_property(window, b"windowOpacity")
        anim.setDuration(effective_duration)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(easing)

        UIAnimator._setup_cleanup(anim, "property", on_finished)
        anim.start()

        return anim

    # ==========================================================================
    # UTILITY METHODS
    # ==========================================================================

    @staticmethod
    def should_animate() -> bool:
        """
        Check if animations should run (respects accessibility and LOD).

        Returns:
            True if animations are enabled
        """
        if AccessibilitySettings.prefers_reduced_motion():
            return False
        return AnimationLOD.should_animate()

    @staticmethod
    def get_effective_duration(base_duration: int) -> int:
        """
        Get effective duration after applying all modifiers.

        Public method for components that need to know the adjusted duration.

        Args:
            base_duration: Requested duration in milliseconds

        Returns:
            Effective duration
        """
        return UIAnimator._get_effective_duration(base_duration)

    @staticmethod
    def clear_pools() -> None:
        """Clear all animation pools (call on application shutdown)."""
        AnimationPool.clear_all()
