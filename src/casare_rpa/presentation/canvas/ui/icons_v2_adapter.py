"""
Icon Adapter v2 - Bridge between legacy toolbar icons and IconProviderV2.

Epic 2.2: Provides get_icon_v2() function that maps legacy action names
to v2 Lucide SVG icons from IconProviderV2.

Features:
- Legacy action name → v2 icon name mapping
- Consistent sizing (uses TOKENS_V2.sizes)
- State management (normal/disabled/accent)
- Feature flag for easy rollback
- Graceful fallback for missing icons

Usage:
    from casare_rpa.presentation.canvas.ui.icons_v2_adapter import get_icon_v2

    icon = get_icon_v2("run", size=20, state="accent")
    action.setIcon(icon)

See: docs/UX_REDESIGN_PLAN.md Phase 2 Epic 2.2
"""

from __future__ import annotations

from typing import Literal

from loguru import logger

from casare_rpa.presentation.canvas.theme_system.icons_v2 import icon_v2

# =============================================================================
# LEGACY → V2 ICON NAME MAPPING
# =============================================================================

# Maps legacy toolbar action names to v2 Lucide SVG icon names
# Format: legacy_name: (v2_name, default_state)
_LEGACY_TO_V2_MAP: dict[str, tuple[str, str]] = {
    # File operations
    "new": ("file", "normal"),
    "open": ("folder", "normal"),
    "reload": ("refresh", "normal"),
    "save": ("save", "normal"),
    "save_as": ("save", "normal"),
    # Edit operations
    "undo": ("undo", "normal"),
    "redo": ("redo", "normal"),
    "cut": ("cut", "normal"),
    "copy": ("copy", "normal"),
    "paste": ("paste", "normal"),
    "delete": ("trash", "normal"),
    "find": ("search", "normal"),
    # Execution operations (accent = primary color)
    "run": ("play", "accent"),
    "pause": ("pause", "normal"),
    "resume": ("play", "accent"),
    "stop": ("stop", "accent"),
    "restart": ("refresh", "normal"),
    "step": ("chevron-right", "normal"),
    "continue": ("chevron-right", "normal"),
    # Debug operations
    "debug": ("code", "normal"),
    "breakpoint": ("alert", "normal"),
    "clear_breakpoints": ("trash", "normal"),
    # View operations
    "zoom_in": ("zoom-in", "normal"),
    "zoom_out": ("zoom-out", "normal"),
    "zoom_reset": ("refresh", "normal"),
    "fit_view": ("panel-left", "normal"),  # closest match
    "save_layout": ("save", "normal"),
    # Tools
    "record": ("circle", "accent"),
    "pick_selector": ("cursor", "normal"),
    "preferences": ("settings", "normal"),
    "settings": ("settings", "normal"),
    "help": ("info", "normal"),
    "about": ("info", "normal"),
    # Status indicators
    "info": ("info", "normal"),
    "warning": ("warning", "normal"),
    "error": ("alert", "normal"),
    "success": ("check", "normal"),
    # Performance/Monitoring
    "performance": ("activity", "normal"),
    "dashboard": ("home", "normal"),
    "metrics": ("bar-chart", "normal"),
    # Project/Settings
    "project": ("folder", "normal"),
    "fleet": ("database", "normal"),
    "layout": ("panel-left", "normal"),
    # Trigger controls
    "listen": ("play", "normal"),
    "stop_listen": ("stop", "normal"),
    # AI & Credentials
    "ai_assistant": ("activity", "accent"),
    "ai": ("activity", "accent"),
    "credentials": ("lock", "accent"),
}


# =============================================================================
# ICON ADAPTER FUNCTION
# =============================================================================

IconState = Literal["normal", "disabled", "accent"]
IconSize = Literal[16, 20, 24]


def get_icon_v2(
    name: str,
    size: IconSize = 20,
    state: IconState = "normal"
) -> QIcon:
    """
    Get a v2 icon by legacy action name.

    Maps legacy action names to v2 Lucide SVG icons and applies
    theme colors based on state.

    Args:
        name: Legacy action name (e.g., "run", "stop", "save")
        size: Icon size: 16, 20, or 24 (default: 20)
        state: Icon state: "normal", "disabled", or "accent" (default: "normal")

    Returns:
        QIcon with the themed icon (may be empty if icon not found)

    Example:
        from casare_rpa.presentation.canvas.ui.icons_v2_adapter import get_icon_v2

        icon = get_icon_v2("run", size=20, state="accent")
        run_action.setIcon(icon)
    """
    from PySide6.QtGui import QIcon

    # Look up mapping
    mapping = _LEGACY_TO_V2_MAP.get(name)
    if not mapping:
        logger.debug(f"No v2 mapping for legacy icon: {name}")
        return QIcon()

    v2_name, default_state = mapping

    # Use provided state, or default from mapping
    icon_state = state if state != "normal" else default_state

    # Get icon from IconProviderV2
    return icon_v2.get_icon(v2_name, size=size, state=icon_state)


def get_icon_v2_safe(
    name: str,
    size: IconSize = 20,
    state: IconState = "normal",
    fallback: QIcon | None = None
) -> QIcon:
    """
    Get a v2 icon with fallback to legacy if not found.

    Args:
        name: Legacy action name
        size: Icon size: 16, 20, or 24 (default: 20)
        state: Icon state: "normal", "disabled", or "accent" (default: "normal")
        fallback: Optional fallback QIcon to return if v2 lookup fails

    Returns:
        QIcon with the themed icon, or fallback if not found
    """

    icon = get_icon_v2(name, size, state)
    if not icon.isNull() or fallback is None:
        return icon
    return fallback


def is_v2_enabled() -> bool:
    """Check if v2 icons are enabled (always True in v2)."""
    return True


def get_available_mappings() -> list[str]:
    """Get list of legacy action names that have v2 mappings."""
    return list(_LEGACY_TO_V2_MAP.keys())


def map_legacy_to_v2(name: str) -> str | None:
    """
    Get the v2 icon name for a legacy action name.

    Args:
        name: Legacy action name

    Returns:
        V2 icon name, or None if no mapping exists
    """
    mapping = _LEGACY_TO_V2_MAP.get(name)
    return mapping[0] if mapping else None


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "get_icon_v2",
    "get_icon_v2_safe",
    "is_v2_enabled",
    "get_available_mappings",
    "map_legacy_to_v2",
    "IconState",
    "IconSize",
]
