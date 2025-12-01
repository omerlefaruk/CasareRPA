"""
Node Icon System

Professional icon generation for all CasareRPA node types using
Unicode symbols and custom drawing.
"""

from typing import Dict, Tuple, Optional
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QFont
from PySide6.QtCore import Qt, QRectF
import tempfile
import os


# Category color scheme - VSCode Dark+ syntax colors for semantic consistency
CATEGORY_COLORS = {
    "basic": QColor(0x56, 0x9C, 0xD6),  # #569CD6 - Keyword blue
    "browser": QColor(0xC5, 0x86, 0xC0),  # #C586C0 - Control flow purple
    "navigation": QColor(0x4E, 0xC9, 0xB0),  # #4EC9B0 - Type teal
    "interaction": QColor(0xCE, 0x91, 0x78),  # #CE9178 - String orange
    "data": QColor(0x89, 0xD1, 0x85),  # #89D185 - Success green
    "wait": QColor(0xD7, 0xBA, 0x7D),  # #D7BA7D - Warning yellow
    "variable": QColor(0x9C, 0xDC, 0xFE),  # #9CDCFE - Variable light blue
    "control_flow": QColor(0xF4, 0x87, 0x71),  # #F48771 - Error red
    "error_handling": QColor(0xF4, 0x87, 0x71),  # #F48771 - Error red
    "desktop_automation": QColor(0xC5, 0x86, 0xC0),  # #C586C0 - Purple
    "debug": QColor(0xD7, 0xBA, 0x7D),  # #D7BA7D - Yellow
    "file": QColor(0x4E, 0xC9, 0xB0),  # #4EC9B0 - Teal
    "triggers": QColor(0x9C, 0x27, 0xB0),  # #9C27B0 - Purple (Material Purple 500)
    "ai_ml": QColor(0x00, 0xBC, 0xD4),  # #00BCD4 - Cyan (Material Cyan 500) - AI/ML
}


# Node type to icon mapping using Unicode symbols and custom shapes
NODE_ICONS = {
    # Basic nodes
    "Start": ("▶", "basic"),
    "End": ("⬛", "basic"),
    "Comment": ("💬", "basic"),
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
    # AI/ML nodes
    "LLM Completion": ("🤖", "ai_ml"),
    "LLM Chat": ("💬", "ai_ml"),
    "LLM Extract Data": ("📊", "ai_ml"),
    "LLM Summarize": ("📝", "ai_ml"),
    "LLM Classify": ("🏷", "ai_ml"),
    "LLM Translate": ("🌐", "ai_ml"),
}


def create_node_icon(
    node_name: str, size: int = 24, custom_color: Optional[QColor] = None
) -> str:
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
            category, QColor(158, 158, 158)
        )
    else:
        # Fallback for unknown nodes
        symbol = "●"
        base_color = custom_color or QColor(158, 158, 158)

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
    color = CATEGORY_COLORS.get(category, QColor(158, 158, 158))

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
    temp_path = os.path.join(
        tempfile.gettempdir(), f"casare_category_{category}_{id(pixmap)}.png"
    )
    pixmap.save(temp_path, "PNG")

    return temp_path


def get_node_color(node_name: str) -> QColor:
    """
    Get the category color for a node type.

    Args:
        node_name: Name of the node

    Returns:
        QColor for the node category
    """
    icon_data = NODE_ICONS.get(node_name)
    if icon_data:
        _, category = icon_data
        return CATEGORY_COLORS.get(category, QColor(158, 158, 158))

    return QColor(158, 158, 158)


def register_custom_icon(node_name: str, symbol: str, category: str):
    """
    Register a custom icon for a node type.

    Args:
        node_name: Name of the node
        symbol: Unicode symbol to use
        category: Category name
    """
    NODE_ICONS[node_name] = (symbol, category)


def get_all_node_icons() -> Dict[str, Tuple[str, str]]:
    """
    Get all registered node icons.

    Returns:
        Dictionary mapping node names to (symbol, category) tuples
    """
    return NODE_ICONS.copy()


# Dual-cache system for performance + serialization:
# - QPixmap cache for fast rendering (in-memory)
# - File path cache for NodeGraphQt model.icon (required for copy/paste serialization)
_icon_pixmap_cache: Dict[str, QPixmap] = {}
_icon_path_cache: Dict[str, str] = {}


def create_node_icon_pixmap(
    node_name: str, size: int = 24, custom_color: Optional[QColor] = None
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
            category, QColor(158, 158, 158)
        )
    else:
        # Fallback for unknown nodes
        symbol = "●"
        base_color = custom_color or QColor(158, 158, 158)

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
