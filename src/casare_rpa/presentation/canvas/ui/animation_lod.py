"""
Level-of-Detail animation system for canvas performance.

Reduces animation complexity at low zoom levels where details
are not visible, maintaining 60fps with 100+ nodes.

This module provides zoom-aware animation control that integrates
with ViewportLODManager to skip or simplify animations when they
would not be visible to the user.

Usage:
    from casare_rpa.presentation.canvas.ui.animation_lod import AnimationLOD

    # Check if animation should run
    if AnimationLOD.should_animate(current_zoom, "hover"):
        duration = base_duration * AnimationLOD.get_duration_multiplier(current_zoom)
        animate_hover(duration)

    # Get current animation level
    level = AnimationLOD.get_animation_level(0.3)  # Returns "REDUCED"

Animation Categories:
    - CRITICAL: selection, error, running - Always animate
    - STANDARD: hover, glow, bounce - Skip at reduced zoom
    - DETAIL: running_border, selection_highlight - Minimal zoom only
"""

from enum import Enum, auto
from typing import Dict, FrozenSet, Optional


class AnimationLevel(Enum):
    """Animation detail levels based on viewport zoom."""

    FULL = auto()  # >= 50% zoom - all animations enabled
    REDUCED = auto()  # 25-50% zoom - skip non-critical animations
    MINIMAL = auto()  # 10-25% zoom - only critical animations
    DISABLED = auto()  # < 10% zoom - no animations


class AnimationCategory(Enum):
    """Categories of animations by importance."""

    CRITICAL = auto()  # Always animate: selection, error, running state
    STANDARD = auto()  # Skip at reduced: hover, glow, bounce
    DETAIL = auto()  # Minimal only: borders, highlights, subtle effects


# Animation type to category mapping
_ANIMATION_CATEGORIES: Dict[str, AnimationCategory] = {
    # Critical - always visible, user feedback
    "selection": AnimationCategory.CRITICAL,
    "error": AnimationCategory.CRITICAL,
    "running": AnimationCategory.CRITICAL,
    "focus": AnimationCategory.CRITICAL,
    "drop": AnimationCategory.CRITICAL,
    # Standard - nice-to-have, skip at low zoom
    "hover": AnimationCategory.STANDARD,
    "glow": AnimationCategory.STANDARD,
    "bounce": AnimationCategory.STANDARD,
    "pulse": AnimationCategory.STANDARD,
    "fade": AnimationCategory.STANDARD,
    "slide": AnimationCategory.STANDARD,
    # Detail - only at full zoom
    "running_border": AnimationCategory.DETAIL,
    "selection_highlight": AnimationCategory.DETAIL,
    "port_glow": AnimationCategory.DETAIL,
    "wire_flow": AnimationCategory.DETAIL,
    "subtle_pulse": AnimationCategory.DETAIL,
}

# Zoom thresholds for each level
_ZOOM_THRESHOLDS: Dict[float, AnimationLevel] = {
    0.10: AnimationLevel.DISABLED,  # < 10% zoom
    0.25: AnimationLevel.MINIMAL,  # 10-25% zoom
    0.50: AnimationLevel.REDUCED,  # 25-50% zoom
}

# Which categories are enabled at each level
_LEVEL_CATEGORIES: Dict[AnimationLevel, FrozenSet[AnimationCategory]] = {
    AnimationLevel.FULL: frozenset(
        {
            AnimationCategory.CRITICAL,
            AnimationCategory.STANDARD,
            AnimationCategory.DETAIL,
        }
    ),
    AnimationLevel.REDUCED: frozenset(
        {
            AnimationCategory.CRITICAL,
            AnimationCategory.STANDARD,
        }
    ),
    AnimationLevel.MINIMAL: frozenset(
        {
            AnimationCategory.CRITICAL,
        }
    ),
    AnimationLevel.DISABLED: frozenset(),
}

# Duration multipliers by level (speed up at lower zoom)
_DURATION_MULTIPLIERS: Dict[AnimationLevel, float] = {
    AnimationLevel.FULL: 1.0,  # Normal speed
    AnimationLevel.REDUCED: 0.7,  # 30% faster
    AnimationLevel.MINIMAL: 0.5,  # 50% faster
    AnimationLevel.DISABLED: 0.0,  # Instant (no animation)
}


class AnimationLOD:
    """
    Level-of-Detail controller for canvas animations.

    Static class providing zoom-aware animation decisions.
    Integrates with ViewportLODManager pattern but focuses
    specifically on animation control.

    Example:
        # In a node's hover event
        def hoverEnterEvent(self, event):
            zoom = self._get_current_zoom()
            if AnimationLOD.should_animate(zoom, "hover"):
                duration = 150 * AnimationLOD.get_duration_multiplier(zoom)
                self._start_hover_animation(int(duration))
            else:
                self._set_hover_state_immediate()

        # In execution indicator
        def show_running(self):
            zoom = self._get_current_zoom()
            # Running is CRITICAL, always animates
            if AnimationLOD.should_animate(zoom, "running"):
                self._animate_running_indicator()

    Attributes:
        _hysteresis: Zoom change threshold to prevent flickering
        _last_level: Cached last computed level
        _last_zoom: Cached last zoom value
    """

    _hysteresis: float = 0.02
    _last_level: Optional[AnimationLevel] = None
    _last_zoom: Optional[float] = None

    @staticmethod
    def get_animation_level(zoom: float) -> str:
        """
        Get the animation level name for the given zoom.

        Args:
            zoom: Current viewport zoom level (0.0 to 1.0+)

        Returns:
            Level name: "FULL", "REDUCED", "MINIMAL", or "DISABLED"

        Example:
            >>> AnimationLOD.get_animation_level(0.6)
            'FULL'
            >>> AnimationLOD.get_animation_level(0.3)
            'REDUCED'
            >>> AnimationLOD.get_animation_level(0.15)
            'MINIMAL'
            >>> AnimationLOD.get_animation_level(0.05)
            'DISABLED'
        """
        level = AnimationLOD._compute_level(zoom)
        return level.name

    @staticmethod
    def should_animate(zoom: float, animation_type: str) -> bool:
        """
        Determine if an animation should run at the given zoom level.

        Args:
            zoom: Current viewport zoom level (0.0 to 1.0+)
            animation_type: Type of animation (e.g., "hover", "selection", "error")

        Returns:
            True if the animation should run, False to skip

        Example:
            >>> AnimationLOD.should_animate(0.6, "hover")
            True
            >>> AnimationLOD.should_animate(0.3, "hover")
            True
            >>> AnimationLOD.should_animate(0.15, "hover")
            False
            >>> AnimationLOD.should_animate(0.15, "selection")
            True  # Critical animations always run
            >>> AnimationLOD.should_animate(0.05, "selection")
            False  # Nothing animates below 10%
        """
        level = AnimationLOD._compute_level(zoom)

        # Nothing animates when disabled
        if level == AnimationLevel.DISABLED:
            return False

        # Get animation category (default to STANDARD if unknown)
        category = _ANIMATION_CATEGORIES.get(
            animation_type.lower(), AnimationCategory.STANDARD
        )

        # Check if category is enabled at this level
        return category in _LEVEL_CATEGORIES[level]

    @staticmethod
    def get_duration_multiplier(zoom: float) -> float:
        """
        Get the duration multiplier for the given zoom level.

        Lower zoom levels use faster animations (smaller multiplier)
        to reduce visual noise and improve performance.

        Args:
            zoom: Current viewport zoom level (0.0 to 1.0+)

        Returns:
            Duration multiplier (0.0 to 1.0)

        Example:
            >>> base_duration = 300  # ms
            >>> AnimationLOD.get_duration_multiplier(0.6)
            1.0  # Full duration: 300ms
            >>> AnimationLOD.get_duration_multiplier(0.3)
            0.7  # Reduced: 210ms
            >>> AnimationLOD.get_duration_multiplier(0.15)
            0.5  # Minimal: 150ms
            >>> AnimationLOD.get_duration_multiplier(0.05)
            0.0  # Disabled: instant
        """
        level = AnimationLOD._compute_level(zoom)
        return _DURATION_MULTIPLIERS[level]

    @staticmethod
    def get_category(animation_type: str) -> str:
        """
        Get the category name for an animation type.

        Args:
            animation_type: Type of animation

        Returns:
            Category name: "CRITICAL", "STANDARD", or "DETAIL"

        Example:
            >>> AnimationLOD.get_category("selection")
            'CRITICAL'
            >>> AnimationLOD.get_category("hover")
            'STANDARD'
            >>> AnimationLOD.get_category("wire_flow")
            'DETAIL'
        """
        category = _ANIMATION_CATEGORIES.get(
            animation_type.lower(), AnimationCategory.STANDARD
        )
        return category.name

    @staticmethod
    def register_animation(animation_type: str, category: str) -> None:
        """
        Register a custom animation type with its category.

        Args:
            animation_type: Unique animation type identifier
            category: Category name ("CRITICAL", "STANDARD", or "DETAIL")

        Raises:
            ValueError: If category name is invalid

        Example:
            >>> AnimationLOD.register_animation("custom_glow", "STANDARD")
            >>> AnimationLOD.should_animate(0.6, "custom_glow")
            True
        """
        category_upper = category.upper()
        try:
            cat_enum = AnimationCategory[category_upper]
        except KeyError:
            valid = ", ".join(c.name for c in AnimationCategory)
            raise ValueError(f"Invalid category '{category}'. Valid: {valid}")
        _ANIMATION_CATEGORIES[animation_type.lower()] = cat_enum

    @staticmethod
    def is_animations_enabled(zoom: float) -> bool:
        """
        Check if any animations are enabled at the given zoom.

        Args:
            zoom: Current viewport zoom level

        Returns:
            True if animations are enabled (level != DISABLED)

        Example:
            >>> AnimationLOD.is_animations_enabled(0.15)
            True
            >>> AnimationLOD.is_animations_enabled(0.05)
            False
        """
        level = AnimationLOD._compute_level(zoom)
        return level != AnimationLevel.DISABLED

    @staticmethod
    def get_enabled_categories(zoom: float) -> FrozenSet[str]:
        """
        Get the set of enabled animation categories at the given zoom.

        Args:
            zoom: Current viewport zoom level

        Returns:
            Frozen set of enabled category names

        Example:
            >>> AnimationLOD.get_enabled_categories(0.6)
            frozenset({'CRITICAL', 'STANDARD', 'DETAIL'})
            >>> AnimationLOD.get_enabled_categories(0.15)
            frozenset({'CRITICAL'})
        """
        level = AnimationLOD._compute_level(zoom)
        return frozenset(cat.name for cat in _LEVEL_CATEGORIES[level])

    @staticmethod
    def _compute_level(zoom: float) -> AnimationLevel:
        """
        Compute the animation level for the given zoom.

        Uses hysteresis to prevent flickering at boundaries.

        Args:
            zoom: Current viewport zoom level

        Returns:
            The AnimationLevel for this zoom
        """
        # Check hysteresis - return cached if zoom hasn't changed much
        if (
            AnimationLOD._last_zoom is not None
            and AnimationLOD._last_level is not None
            and abs(zoom - AnimationLOD._last_zoom) < AnimationLOD._hysteresis
        ):
            return AnimationLOD._last_level

        # Compute level based on thresholds
        level = AnimationLevel.FULL
        for threshold, threshold_level in sorted(_ZOOM_THRESHOLDS.items()):
            if zoom < threshold:
                level = threshold_level
                break

        # Cache for hysteresis
        AnimationLOD._last_zoom = zoom
        AnimationLOD._last_level = level

        return level

    @staticmethod
    def reset_cache() -> None:
        """
        Reset the internal cache.

        Call when viewport is recreated or for testing.
        """
        AnimationLOD._last_zoom = None
        AnimationLOD._last_level = None

    @staticmethod
    def get_stats() -> Dict[str, object]:
        """
        Get animation LOD statistics for debugging.

        Returns:
            Dict with current state information

        Example:
            >>> AnimationLOD.get_stats()
            {
                'last_zoom': 0.6,
                'last_level': 'FULL',
                'hysteresis': 0.02,
                'registered_animations': 15
            }
        """
        return {
            "last_zoom": AnimationLOD._last_zoom,
            "last_level": (
                AnimationLOD._last_level.name if AnimationLOD._last_level else None
            ),
            "hysteresis": AnimationLOD._hysteresis,
            "registered_animations": len(_ANIMATION_CATEGORIES),
        }


# Convenience function for module-level access
def should_animate(zoom: float, animation_type: str) -> bool:
    """
    Module-level convenience function for AnimationLOD.should_animate.

    Args:
        zoom: Current viewport zoom level
        animation_type: Type of animation

    Returns:
        True if animation should run

    Example:
        from casare_rpa.presentation.canvas.ui.animation_lod import should_animate

        if should_animate(zoom, "hover"):
            start_hover_animation()
    """
    return AnimationLOD.should_animate(zoom, animation_type)


def get_duration_multiplier(zoom: float) -> float:
    """
    Module-level convenience function for AnimationLOD.get_duration_multiplier.

    Args:
        zoom: Current viewport zoom level

    Returns:
        Duration multiplier (0.0 to 1.0)

    Example:
        from casare_rpa.presentation.canvas.ui.animation_lod import (
            get_duration_multiplier
        )

        duration = int(base_duration * get_duration_multiplier(zoom))
    """
    return AnimationLOD.get_duration_multiplier(zoom)
