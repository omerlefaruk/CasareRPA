"""
Node Icon System

Professional icon generation for all CasareRPA node types using
Unicode symbols and custom drawing.

All colors are sourced from the unified theme system (theme.py).
"""

import os
import tempfile

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPixmap

# Import unified theme system for all colors
from casare_rpa.presentation.canvas.theme import THEME_V2 as THEME

# ============================================================================
# CATEGORY COLORS - Delegated to unified theme system
# ============================================================================
# Legacy CATEGORY_COLORS dict is replaced with lazy initialization that
# uses CATEGORY_COLOR_MAP for consistency across nodes, icons, and wires.

# Cache for QColor objects (populated on first access)
_CATEGORY_COLORS_CACHE: dict[str, QColor] | None = None

# Default category color map - sourced from unified THEME system
# Matches category_utils.py CATEGORY_COLOR_MAP (design-system-unified-2025)
_CATEGORY_HEX_MAP = {
    "basic": THEME.category_basic,
    "browser": THEME.category_browser,
    "navigation": THEME.category_navigation,
    "interaction": THEME.category_interaction,
    "data": THEME.category_data,
    "data_operations": THEME.category_data_operations,
    "desktop": THEME.category_desktop,
    "desktop_automation": THEME.category_desktop_automation,
    "file": THEME.category_file,
    "file_operations": THEME.category_file_operations,
    "http": THEME.category_http,
    "rest_api": THEME.category_rest_api,
    "system": THEME.category_system,
    "control_flow": THEME.category_control_flow,
    "error_handling": THEME.category_error_handling,
    "variable": THEME.category_variable,
    "wait": THEME.category_wait,
    "google": THEME.category_google,
    "microsoft": THEME.category_microsoft,
    "database": THEME.category_database,
    "email": THEME.category_email,
    "office_automation": THEME.category_office_automation,
    "scripts": THEME.category_scripts,
    "debug": THEME.category_debug,
    "utility": THEME.category_utility,
    "triggers": THEME.category_triggers,
    "messaging": THEME.category_messaging,
    "document": THEME.category_document,
}


def _init_category_colors() -> dict[str, QColor]:
    """
    Initialize category colors from unified theme system.

    Returns:
        Dictionary mapping category names to QColor objects
    """
    global _CATEGORY_COLORS_CACHE
    if _CATEGORY_COLORS_CACHE is None:
        _CATEGORY_COLORS_CACHE = {
            category: QColor(hex_color) for category, hex_color in _CATEGORY_HEX_MAP.items()
        }
    return _CATEGORY_COLORS_CACHE


def get_category_color_qcolor(category: str) -> QColor:
    """
    Get QColor for a category from unified theme.

    Args:
        category: Category name

    Returns:
        QColor for the category (cached for performance)
    """
    colors = _init_category_colors()
    return colors.get(category, QColor(_CATEGORY_HEX_MAP.get("utility", "#64748b")))


# Legacy CATEGORY_COLORS dict - kept for backward compatibility
# This is a lazy proxy that initializes on first attribute access
class _CategoryColorsProxy:
    """Lazy proxy for CATEGORY_COLORS that delegates to theme."""

    def get(self, key: str, default: QColor | None = None) -> QColor:
        colors = _init_category_colors()
        return colors.get(key, default or QColor(_CATEGORY_HEX_MAP.get("utility", "#64748b")))

    def __getitem__(self, key: str) -> QColor:
        colors = _init_category_colors()
        return colors[key]

    def __contains__(self, key: str) -> bool:
        colors = _init_category_colors()
        return key in colors

    def keys(self):
        colors = _init_category_colors()
        return colors.keys()

    def values(self):
        colors = _init_category_colors()
        return colors.values()

    def items(self):
        colors = _init_category_colors()
        return colors.items()


CATEGORY_COLORS = _CategoryColorsProxy()


# Node type to icon mapping using Unicode symbols and custom shapes
NODE_ICONS = {
    # Basic nodes
    "Start": ("\u25b6", "basic"),
    "End": ("\u2b1b", "basic"),
    "Comment": ("\U0001f4ac", "basic"),
    # Subflow node
    "Subflow": ("\u2b14", "utility"),  # Square lozenge - represents nested workflow
    # Browser nodes
    "Launch Browser": ("🌐", "browser"),
    "Close Browser": ("✖", "browser"),
    "Navigate": ("➜", "navigation"),
    "Go Back": ("◀", "navigation"),
    "Go Forward": ("▶", "navigation"),
    "Refresh Page": ("↻", "navigation"),
    "Get URL": ("🔗", "navigation"),
    "Get Page Title": ("📄", "navigation"),
    # Interaction nodes
    "Click Element": ("👆", "interaction"),
    "Type Text": ("⌨", "interaction"),
    "Select Option": ("☑", "interaction"),
    "Clear Input": ("⌫", "interaction"),
    "Submit Form": ("📤", "interaction"),
    "Hover Element": ("👋", "interaction"),
    # Data nodes
    "Get Element Text": ("📝", "data"),
    "Get Element Attribute": ("🏷", "data"),
    "Get Element Count": ("🔢", "data"),
    "Extract Data": ("📊", "data"),
    "Set Variable": ("📌", "variable"),
    "Get Variable": ("📍", "variable"),
    "Concatenate": ("🔗", "data"),
    "Format String": ("✏", "data"),
    "Regex Match": ("🔍", "data"),
    "Regex Replace": ("🔄", "data"),
    "Math Operation": ("➕", "data"),
    "Comparison": ("⚖", "data"),
    "Create List": ("📋", "data"),
    "List Get Item": ("📑", "data"),
    "JSON Parse": ("{ }", "data"),
    "Get Property": ("🔑", "data"),
    # Wait nodes
    "Wait": ("⏱", "wait"),
    "Wait For Element": ("⏳", "wait"),
    "Wait For URL": ("🕐", "wait"),
    "Wait For Condition": ("⌛", "wait"),
    # Control flow nodes
    "If": ("❓", "control_flow"),
    "For Loop": ("🔁", "control_flow"),
    "While Loop": ("↻", "control_flow"),
    "For Each": ("⤴", "control_flow"),
    "Break": ("🛑", "control_flow"),
    "Continue": ("⏭", "control_flow"),
    "Switch": ("⚡", "control_flow"),
    # Error handling
    "Try": ("🛡", "error_handling"),
    "Catch": ("🚨", "error_handling"),
    "Finally": ("✓", "error_handling"),
    "Throw": ("💥", "error_handling"),
    # Desktop automation
    "Launch Application": ("🚀", "desktop_automation"),
    "Close Application": ("✖", "desktop_automation"),
    "Activate Window": ("🪟", "desktop_automation"),
    "Get Window List": ("📋", "desktop_automation"),
    "Find Element": ("🔍", "desktop_automation"),
    "Click Element (Desktop)": ("👆", "desktop_automation"),
    "Type Text (Desktop)": ("⌨", "desktop_automation"),
    "Get Element Text (Desktop)": ("📝", "desktop_automation"),
    "Get Element Property": ("🏷", "desktop_automation"),
    # Debug nodes
    "Breakpoint": ("🔴", "debug"),
    "Log": ("📋", "debug"),
    "Print": ("🖨", "debug"),
    "Assert": ("✓", "debug"),
    # File operations
    "Read File": ("📄", "file"),
    "Write File": ("💾", "file"),
    "Delete File": ("🗑", "file"),
    "File Exists": ("❓", "file"),
}


def create_node_icon(node_name: str, size: int = 24, custom_color: QColor | None = None) -> str:
    """
    Create a professional icon for a node type.

    Args:
        node_name: Name of the node (e.g., "Click Element")
        size: Icon size in pixels
        custom_color: Override category color

    Returns:
        Path to saved icon PNG file
    """
    # Get icon symbol and category
    icon_data = NODE_ICONS.get(node_name)

    if icon_data:
        symbol, category = icon_data
        base_color = custom_color or CATEGORY_COLORS.get(
            category, QColor(_CATEGORY_HEX_MAP.get("utility", "#64748b"))
        )
    else:
        # Fallback for unknown nodes
        symbol = "●"
        base_color = custom_color or QColor(_CATEGORY_HEX_MAP.get("utility", "#64748b"))

    # Create pixmap
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # Draw background circle with gradient
    from PySide6.QtGui import QRadialGradient

    gradient = QRadialGradient(size / 2, size / 2, size / 2)
    gradient.setColorAt(0, base_color.lighter(120))
    gradient.setColorAt(1, base_color)

    painter.setBrush(QBrush(gradient))
    painter.setPen(QPen(base_color.darker(130), 1.5))

    margin = 2
    painter.drawEllipse(margin, margin, size - margin * 2, size - margin * 2)

    # Draw icon symbol
    font_size = max(1, int(size * 0.5))  # Ensure font size is at least 1
    font = QFont("Segoe UI Emoji", font_size)  # Use emoji font
    painter.setFont(font)
    painter.setPen(QPen(Qt.GlobalColor.white))

    # Center the text
    rect = QRectF(0, 0, size, size)
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, symbol)

    painter.end()

    # Save to temp file
    temp_path = os.path.join(
        tempfile.gettempdir(),
        f"casare_icon_{node_name.replace(' ', '_')}_{id(pixmap)}.png",
    )
    pixmap.save(temp_path, "PNG")

    return temp_path


def create_category_icon(category: str, size: int = 24) -> str:
    """
    Create an icon representing a category.

    Args:
        category: Category name
        size: Icon size in pixels

    Returns:
        Path to saved icon PNG file
    """
    color = CATEGORY_COLORS.get(category, QColor(_CATEGORY_HEX_MAP.get("utility", "#64748b")))

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Draw rounded square
    painter.setBrush(QBrush(color))
    painter.setPen(QPen(color.darker(120), 1.5))

    margin = 2
    painter.drawRoundedRect(margin, margin, size - margin * 2, size - margin * 2, 4, 4)

    painter.end()

    # Save to temp file
    temp_path = os.path.join(tempfile.gettempdir(), f"casare_category_{category}_{id(pixmap)}.png")
    pixmap.save(temp_path, "PNG")

    return temp_path


def get_node_color(node_name: str) -> QColor:
    """
    Get the category color for a node type.

    Delegates to unified theme system for consistency across
    nodes, icons, and wires.

    Args:
        node_name: Name of the node

    Returns:
        QColor for the node category
    """
    icon_data = NODE_ICONS.get(node_name)
    if icon_data:
        _, category = icon_data
        return QColor(_CATEGORY_HEX_MAP.get(category, "#64748b"))

    # Default fallback from theme
    return QColor(_CATEGORY_HEX_MAP.get("utility", "#64748b"))


def register_custom_icon(node_name: str, symbol: str, category: str):
    """
    Register a custom icon for a node type.

    Args:
        node_name: Name of the node
        symbol: Unicode symbol to use
        category: Category name
    """
    NODE_ICONS[node_name] = (symbol, category)


def get_all_node_icons() -> dict[str, tuple[str, str]]:
    """
    Get all registered node icons.

    Returns:
        Dictionary mapping node names to (symbol, category) tuples
    """
    return NODE_ICONS.copy()


# Dual-cache system for performance + serialization:
# - QPixmap cache for fast rendering (in-memory)
# - File path cache for NodeGraphQt model.icon (required for copy/paste serialization)
_icon_pixmap_cache: dict[str, QPixmap] = {}
_icon_path_cache: dict[str, str] = {}


def create_node_icon_pixmap(
    node_name: str, size: int = 24, custom_color: QColor | None = None
) -> QPixmap:
    """
    Create a professional icon for a node type and return QPixmap directly.
    This is the optimized version that avoids file I/O.

    Args:
        node_name: Name of the node (e.g., "Click Element")
        size: Icon size in pixels
        custom_color: Override category color

    Returns:
        QPixmap containing the rendered icon
    """
    # Get icon symbol and category
    icon_data = NODE_ICONS.get(node_name)

    if icon_data:
        symbol, category = icon_data
        base_color = custom_color or CATEGORY_COLORS.get(
            category, QColor(_CATEGORY_HEX_MAP.get("utility", "#64748b"))
        )
    else:
        # Fallback for unknown nodes
        symbol = "●"
        base_color = custom_color or QColor(_CATEGORY_HEX_MAP.get("utility", "#64748b"))

    # Create pixmap
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # Draw background circle with gradient
    from PySide6.QtGui import QRadialGradient

    gradient = QRadialGradient(size / 2, size / 2, size / 2)
    gradient.setColorAt(0, base_color.lighter(120))
    gradient.setColorAt(1, base_color)

    painter.setBrush(QBrush(gradient))
    painter.setPen(QPen(base_color.darker(130), 1.5))

    margin = 2
    painter.drawEllipse(margin, margin, size - margin * 2, size - margin * 2)

    # Draw icon symbol
    font_size = max(1, int(size * 0.5))
    font = QFont("Segoe UI Emoji", font_size)
    painter.setFont(font)
    painter.setPen(QPen(Qt.GlobalColor.white))

    # Center the text
    rect = QRectF(0, 0, size, size)
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, symbol)

    painter.end()

    return pixmap


def get_cached_node_icon(node_name: str, size: int = 24) -> QPixmap:
    """
    Get a cached node icon QPixmap or create it if not cached.
    Uses in-memory QPixmap cache for lightning-fast rendering performance.

    Args:
        node_name: Name of the node
        size: Icon size

    Returns:
        QPixmap containing the icon
    """
    cache_key = f"{node_name}_{size}"

    if cache_key not in _icon_pixmap_cache:
        _icon_pixmap_cache[cache_key] = create_node_icon_pixmap(node_name, size)

    return _icon_pixmap_cache[cache_key]


def get_cached_node_icon_path(node_name: str, size: int = 24) -> str:
    """
    Get a cached node icon file path or create it if not cached.
    Uses file path cache for NodeGraphQt model.icon (required for JSON serialization).

    This function generates the file only once per node type and caches the path,
    avoiding repeated file I/O while still providing a serializable path.

    Args:
        node_name: Name of the node
        size: Icon size

    Returns:
        File path to the cached icon PNG
    """
    cache_key = f"{node_name}_{size}"

    if cache_key not in _icon_path_cache:
        # Create icon and save to temp file (but only once per node type)
        _icon_path_cache[cache_key] = create_node_icon(node_name, size)

    return _icon_path_cache[cache_key]


def clear_icon_cache():
    """Clear both icon caches (pixmap and path)."""
    global _icon_pixmap_cache, _icon_path_cache
    _icon_pixmap_cache = {}
    _icon_path_cache = {}
