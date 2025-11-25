"""
Node Icon System

Professional icon generation for all CasareRPA node types using
Unicode symbols and custom drawing.
"""

from typing import Dict, Tuple, Optional
from PySide6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QFont, QPainterPath
from PySide6.QtCore import Qt, QRectF, QPointF
import tempfile
import os


# Category color scheme - vibrant and distinctive
CATEGORY_COLORS = {
    'basic': QColor(100, 181, 246),          # Light Blue - Start/End/Comment
    'browser': QColor(156, 39, 176),         # Purple - Browser operations
    'navigation': QColor(66, 165, 245),      # Blue - Navigation
    'interaction': QColor(255, 167, 38),     # Orange - Click/Type interactions
    'data': QColor(102, 187, 106),           # Green - Data operations
    'wait': QColor(255, 202, 40),            # Yellow - Wait operations
    'variable': QColor(171, 71, 188),        # Deep Purple - Variables
    'control_flow': QColor(239, 83, 80),     # Red - If/Loop/Switch
    'error_handling': QColor(244, 67, 54),   # Dark Red - Try/Catch
    'desktop_automation': QColor(138, 43, 226),  # Blue-Violet - Desktop
    'debug': QColor(255, 112, 67),           # Coral - Breakpoints/Log
    'file': QColor(121, 134, 203),           # Indigo - File operations
}


# Node type to icon mapping using Unicode symbols and custom shapes
NODE_ICONS = {
    # Basic nodes
    'Start': ('▶', 'basic'),
    'End': ('⬛', 'basic'),
    'Comment': ('💬', 'basic'),

    # Browser nodes
    'Launch Browser': ('🌐', 'browser'),
    'Close Browser': ('✖', 'browser'),
    'Navigate': ('➜', 'navigation'),
    'Go Back': ('◀', 'navigation'),
    'Go Forward': ('▶', 'navigation'),
    'Refresh Page': ('↻', 'navigation'),
    'Get URL': ('🔗', 'navigation'),
    'Get Page Title': ('📄', 'navigation'),

    # Interaction nodes
    'Click Element': ('👆', 'interaction'),
    'Type Text': ('⌨', 'interaction'),
    'Select Option': ('☑', 'interaction'),
    'Clear Input': ('⌫', 'interaction'),
    'Submit Form': ('📤', 'interaction'),
    'Hover Element': ('👋', 'interaction'),

    # Data nodes
    'Get Element Text': ('📝', 'data'),
    'Get Element Attribute': ('🏷', 'data'),
    'Get Element Count': ('🔢', 'data'),
    'Extract Data': ('📊', 'data'),
    'Set Variable': ('📌', 'variable'),
    'Get Variable': ('📍', 'variable'),
    'Concatenate': ('🔗', 'data'),
    'Format String': ('✏', 'data'),
    'Regex Match': ('🔍', 'data'),
    'Regex Replace': ('🔄', 'data'),
    'Math Operation': ('➕', 'data'),
    'Comparison': ('⚖', 'data'),
    'Create List': ('📋', 'data'),
    'List Get Item': ('📑', 'data'),
    'JSON Parse': ('{ }', 'data'),
    'Get Property': ('🔑', 'data'),

    # Wait nodes
    'Wait': ('⏱', 'wait'),
    'Wait For Element': ('⏳', 'wait'),
    'Wait For URL': ('🕐', 'wait'),
    'Wait For Condition': ('⌛', 'wait'),

    # Control flow nodes
    'If': ('❓', 'control_flow'),
    'For Loop': ('🔁', 'control_flow'),
    'While Loop': ('↻', 'control_flow'),
    'For Each': ('⤴', 'control_flow'),
    'Break': ('🛑', 'control_flow'),
    'Continue': ('⏭', 'control_flow'),
    'Switch': ('⚡', 'control_flow'),

    # Error handling
    'Try': ('🛡', 'error_handling'),
    'Catch': ('🚨', 'error_handling'),
    'Finally': ('✓', 'error_handling'),
    'Throw': ('💥', 'error_handling'),

    # Desktop automation
    'Launch Application': ('🚀', 'desktop_automation'),
    'Close Application': ('✖', 'desktop_automation'),
    'Activate Window': ('🪟', 'desktop_automation'),
    'Get Window List': ('📋', 'desktop_automation'),
    'Find Element': ('🔍', 'desktop_automation'),
    'Click Element (Desktop)': ('👆', 'desktop_automation'),
    'Type Text (Desktop)': ('⌨', 'desktop_automation'),
    'Get Element Text': ('📝', 'desktop_automation'),
    'Get Element Property': ('🏷', 'desktop_automation'),

    # Debug nodes
    'Breakpoint': ('🔴', 'debug'),
    'Log': ('📋', 'debug'),
    'Print': ('🖨', 'debug'),
    'Assert': ('✓', 'debug'),

    # File operations
    'Read File': ('📄', 'file'),
    'Write File': ('💾', 'file'),
    'Delete File': ('🗑', 'file'),
    'File Exists': ('❓', 'file'),
}


def create_node_icon(
    node_name: str,
    size: int = 24,
    custom_color: Optional[QColor] = None
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
        base_color = custom_color or CATEGORY_COLORS.get(category, QColor(158, 158, 158))
    else:
        # Fallback for unknown nodes
        symbol = '●'
        base_color = custom_color or QColor(158, 158, 158)

    # Create pixmap
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    # Draw background circle with gradient
    from PySide6.QtGui import QRadialGradient

    gradient = QRadialGradient(size/2, size/2, size/2)
    gradient.setColorAt(0, base_color.lighter(120))
    gradient.setColorAt(1, base_color)

    painter.setBrush(QBrush(gradient))
    painter.setPen(QPen(base_color.darker(130), 1.5))

    margin = 2
    painter.drawEllipse(margin, margin, size - margin*2, size - margin*2)

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
    temp_path = os.path.join(tempfile.gettempdir(), f"casare_icon_{node_name.replace(' ', '_')}_{id(pixmap)}.png")
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
    painter.drawRoundedRect(
        margin, margin,
        size - margin*2, size - margin*2,
        4, 4
    )

    painter.end()

    # Save to temp file
    temp_path = os.path.join(tempfile.gettempdir(), f"casare_category_{category}_{id(pixmap)}.png")
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


# Cache for generated icons
_icon_cache: Dict[str, str] = {}


def get_cached_node_icon(node_name: str, size: int = 24) -> str:
    """
    Get a cached node icon or create it if not cached.

    Args:
        node_name: Name of the node
        size: Icon size

    Returns:
        Path to icon file
    """
    cache_key = f"{node_name}_{size}"

    if cache_key not in _icon_cache:
        _icon_cache[cache_key] = create_node_icon(node_name, size)

    return _icon_cache[cache_key]


def clear_icon_cache():
    """Clear the icon cache."""
    global _icon_cache
    _icon_cache = {}
