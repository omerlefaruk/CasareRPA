"""
Category Utilities - Hierarchical category path support.

Provides utilities for parsing, building, and managing hierarchical
node categories with arbitrary depth (e.g., "google/gmail/send").

Features:
- CategoryPath dataclass for parsing paths like "google/gmail/send"
- Category tree building from flat category lists
- Display name resolution with leaf fallback
- Color inheritance with distinct subcategory shades
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from PySide6.QtGui import QColor


@dataclass(frozen=True)
class CategoryPath:
    """
    Immutable representation of a hierarchical category path.

    Examples:
        CategoryPath.parse("google/gmail/send")
        -> CategoryPath(parts=["google", "gmail", "send"])

        CategoryPath.parse("basic")
        -> CategoryPath(parts=["basic"])
    """

    parts: Tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def parse(cls, path: str) -> "CategoryPath":
        """Parse a category path string into parts."""
        if not path:
            return cls(parts=())
        parts = tuple(p.strip() for p in path.split("/") if p.strip())
        return cls(parts=parts)

    @property
    def depth(self) -> int:
        """Get the nesting depth (1 = top-level)."""
        return len(self.parts)

    @property
    def root(self) -> str:
        """Get the root (top-level) category."""
        return self.parts[0] if self.parts else ""

    @property
    def leaf(self) -> str:
        """Get the leaf (deepest) category."""
        return self.parts[-1] if self.parts else ""

    @property
    def parent(self) -> Optional["CategoryPath"]:
        """Get parent path, or None if root."""
        if len(self.parts) <= 1:
            return None
        return CategoryPath(parts=self.parts[:-1])

    @property
    def parent_path(self) -> str:
        """Get parent as string path."""
        parent = self.parent
        return str(parent) if parent else ""

    def is_ancestor_of(self, other: "CategoryPath") -> bool:
        """Check if this path is an ancestor of another."""
        if len(self.parts) >= len(other.parts):
            return False
        return other.parts[: len(self.parts)] == self.parts

    def is_descendant_of(self, other: "CategoryPath") -> bool:
        """Check if this path is a descendant of another."""
        return other.is_ancestor_of(self)

    def __str__(self) -> str:
        """Convert back to path string."""
        return "/".join(self.parts)

    def __bool__(self) -> bool:
        """Check if path is non-empty."""
        return bool(self.parts)


@dataclass
class CategoryNode:
    """Node in a category tree structure."""

    name: str
    path: str
    children: Dict[str, "CategoryNode"] = field(default_factory=dict)
    node_count: int = 0  # Direct nodes in this category
    total_count: int = 0  # Total nodes including all descendants

    def add_child(self, name: str, path: str) -> "CategoryNode":
        """Add or get a child category node."""
        if name not in self.children:
            self.children[name] = CategoryNode(name=name, path=path)
        return self.children[name]

    def get_all_paths(self) -> List[str]:
        """Get all paths in this subtree (including self)."""
        paths = [self.path] if self.path else []
        for child in self.children.values():
            paths.extend(child.get_all_paths())
        return paths

    def has_nodes(self) -> bool:
        """Check if this category or any descendant has nodes."""
        return self.total_count > 0


def build_category_tree(categories: List[str]) -> CategoryNode:
    """
    Build a hierarchical tree structure from flat category paths.

    Args:
        categories: List of category path strings (e.g., ["google/gmail", "browser/navigation"])

    Returns:
        Root CategoryNode with children representing the hierarchy
    """
    root = CategoryNode(name="", path="")

    for category_path in categories:
        parsed = CategoryPath.parse(category_path)
        if not parsed:
            continue

        current = root
        path_so_far = []

        for part in parsed.parts:
            path_so_far.append(part)
            full_path = "/".join(path_so_far)
            current = current.add_child(part, full_path)

    return root


def update_category_counts(
    tree: CategoryNode, category_node_counts: Dict[str, int]
) -> None:
    """
    Update node counts in the category tree.

    Args:
        tree: Root of category tree
        category_node_counts: Dict mapping category path -> number of nodes
    """

    def _update_recursive(node: CategoryNode) -> int:
        # Direct nodes in this category
        node.node_count = category_node_counts.get(node.path, 0)

        # Sum children
        child_total = sum(_update_recursive(child) for child in node.children.values())

        # Total = direct + children
        node.total_count = node.node_count + child_total
        return node.total_count

    _update_recursive(tree)


# Display names for categories and subcategories
CATEGORY_DISPLAY_NAMES = {
    # Root categories
    "basic": "Basic",
    "browser": "Browser",
    "control_flow": "Control Flow",
    "data": "Data",
    "data_operations": "Data Operations",  # Alias for migration
    "database": "Database",
    "desktop": "Desktop",
    "desktop_automation": "Desktop Automation",  # Alias for migration
    "email": "Email",
    "error_handling": "Error Handling",
    "file": "File",
    "file_operations": "File Operations",  # Alias for migration
    "google": "Google Workspace",
    "messaging": "Messaging",
    "office_automation": "Office Automation",
    "rest_api": "REST API / HTTP",
    "scripts": "Scripts",
    "system": "System",
    "triggers": "Triggers",
    "utility": "Utility",
    "variable": "Variables",
    "ai_ml": "AI / Machine Learning",
    "document": "Document AI",
    # Browser subcategories
    "launch": "Launch",
    "navigation": "Navigation",
    "interaction": "Interaction",
    "wait": "Wait",
    # Desktop subcategories
    "application": "Application",
    "window": "Window",
    "element": "Element",
    "input": "Input",
    "capture": "Capture",
    # Data subcategories
    "string": "String",
    "list": "List",
    "dict": "Dictionary",
    "json": "JSON",
    "math": "Math",
    # File subcategories
    "csv": "CSV",
    "xml": "XML",
    "pdf": "PDF",
    "ftp": "FTP",
    "archive": "Archive",
    # Google subcategories
    "gmail": "Gmail",
    "sheets": "Sheets",
    "docs": "Docs",
    "drive": "Drive",
    "calendar": "Calendar",
    # Google 3rd level
    "send": "Send",
    "read": "Read",
    "manage": "Manage",
    "batch": "Batch",
    "cell": "Cell",
    "sheet": "Sheet",
    "row_column": "Rows & Columns",
    "format": "Format",
    "text": "Text",
    "folder": "Folder",
    "permissions": "Permissions",
    "export": "Export",
    "events": "Events",
    # Messaging subcategories
    "telegram": "Telegram",
    "whatsapp": "WhatsApp",
    "actions": "Actions",
    # Database subcategories
    "connection": "Connection",
    "query": "Query",
    "transaction": "Transaction",
    # REST API subcategories
    "auth": "Authentication",
    "advanced": "Advanced",
    # Error handling subcategories
    "try_catch": "Try/Catch",
    "retry": "Retry",
    "logging": "Logging",
    # System subcategories
    "clipboard": "Clipboard",
    "dialog": "Dialog",
    "service": "Service",
    "terminal": "Terminal",
    # Trigger subcategories
    "schedule": "Schedule",
    "webhook": "Webhook",
    "file_watch": "File Watch",
    "misc": "Miscellaneous",
    # Office Automation subcategories
    "excel": "Excel",
    "word": "Word",
    "outlook": "Outlook",
    # Utility subcategories
    "random": "Random",
    "datetime": "Date & Time",
    # Control Flow subcategories
    "conditional": "Conditional",
    "loop": "Loop",
    "flow": "Flow",
    # SuperNode subcategory
    "super": "Super Nodes",
}


def get_display_name(category_path: str) -> str:
    """
    Get the display name for a category path.

    Uses leaf name lookup, falling back to title case.

    Args:
        category_path: Full category path (e.g., "google/gmail/send")

    Returns:
        Human-readable display name (e.g., "Send")
    """
    parsed = CategoryPath.parse(category_path)
    if not parsed:
        return ""

    # Try full path first
    if category_path in CATEGORY_DISPLAY_NAMES:
        return CATEGORY_DISPLAY_NAMES[category_path]

    # Try leaf name
    leaf = parsed.leaf
    if leaf in CATEGORY_DISPLAY_NAMES:
        return CATEGORY_DISPLAY_NAMES[leaf]

    # Fallback to title case
    return leaf.replace("_", " ").title()


def get_full_display_path(category_path: str, separator: str = " > ") -> str:
    """
    Get full display path with all levels.

    Args:
        category_path: Full category path (e.g., "google/gmail/send")
        separator: String to join parts

    Returns:
        Full display path (e.g., "Google Workspace > Gmail > Send")
    """
    parsed = CategoryPath.parse(category_path)
    if not parsed:
        return ""

    parts = []
    path_so_far = []
    for part in parsed.parts:
        path_so_far.append(part)
        full_path = "/".join(path_so_far)
        parts.append(get_display_name(full_path))

    return separator.join(parts)


# ============================================================================
# CATEGORY COLORS - Now delegating to unified theme
# ============================================================================
# ROOT_CATEGORY_COLORS is kept for backward compatibility but colors
# are now sourced from the unified theme system (theme.py).

from casare_rpa.presentation.canvas.ui.theme import Theme, CATEGORY_COLOR_MAP


def _hex_to_rgb_tuple(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple for backward compatibility."""
    hex_color = hex_color.lstrip("#")
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )


# ROOT_CATEGORY_COLORS now built from theme for consistency
# This maintains backward compatibility with code that expects RGB tuples
ROOT_CATEGORY_COLORS = {
    category: _hex_to_rgb_tuple(hex_color)
    for category, hex_color in CATEGORY_COLOR_MAP.items()
}


def get_category_color(category_path: str) -> QColor:
    """
    Get color for a category, with distinct shades for subcategories.

    Now delegates to the unified theme system for consistency across
    nodes, icons, and wires.

    Subcategories get progressively lighter shades of their parent's color.
    Each depth level lightens by ~15%.

    Args:
        category_path: Full category path (e.g., "google/gmail/send")

    Returns:
        QColor for the category (from unified theme)
    """
    parsed = CategoryPath.parse(category_path)
    if not parsed:
        cc = Theme.get_canvas_colors()
        return QColor(cc.category_default)

    # Get base color from unified theme
    base_color = Theme.get_category_qcolor(parsed.root)

    # Lighten for subcategories (depth > 1)
    depth = parsed.depth
    if depth > 1:
        # Each level adds ~15% lightening
        # depth 2 -> lighter(115), depth 3 -> lighter(130), etc.
        lighten_factor = 100 + (depth - 1) * 15
        return base_color.lighter(lighten_factor)

    return QColor(base_color)  # Return copy to avoid modifying cached color


def get_category_color_with_alpha(category_path: str, alpha: int = 180) -> QColor:
    """
    Get category color with transparency for child nodes.

    Args:
        category_path: Full category path
        alpha: Alpha value (0-255)

    Returns:
        QColor with alpha applied
    """
    color = get_category_color(category_path)
    color.setAlpha(alpha)
    return color


# Category aliases for backward compatibility (old name -> new name)
CATEGORY_ALIASES = {
    "data_operations": "data",
    "file_operations": "file",
    "desktop_automation": "desktop",
}


def normalize_category(category_path: str) -> str:
    """
    Normalize category path, applying aliases.

    Args:
        category_path: Category path (possibly using old names)

    Returns:
        Normalized path using new names
    """
    parsed = CategoryPath.parse(category_path)
    if not parsed:
        return category_path

    # Apply alias to root if applicable
    parts = list(parsed.parts)
    if parts and parts[0] in CATEGORY_ALIASES:
        parts[0] = CATEGORY_ALIASES[parts[0]]

    return "/".join(parts)


def get_all_parent_paths(category_path: str) -> List[str]:
    """
    Get all parent paths for a category.

    Args:
        category_path: Full category path (e.g., "google/gmail/send")

    Returns:
        List of parent paths ["google", "google/gmail"]
    """
    parsed = CategoryPath.parse(category_path)
    if not parsed or parsed.depth <= 1:
        return []

    parents = []
    path_so_far = []
    for part in parsed.parts[:-1]:  # Exclude leaf
        path_so_far.append(part)
        parents.append("/".join(path_so_far))

    return parents


# Category sort order (alphabetical)
CATEGORY_ORDER = [
    "ai_ml",
    "basic",
    "browser",
    "control_flow",
    "data_operations",
    "database",
    "desktop",  # SuperNode category (distinct from desktop_automation)
    "desktop_automation",
    "document",
    "email",
    "error_handling",
    "file_operations",
    "google",
    "messaging",
    "office_automation",
    "rest_api",
    "scripts",
    "system",
    "text",  # SuperNode category for text operations
    "triggers",
    "utility",
    "variable",
]


def get_category_sort_key(category_path: str) -> Tuple[int, str]:
    """
    Get sort key for a category path.

    Sorts by:
    1. Root category order (from CATEGORY_ORDER)
    2. Alphabetically within same root

    Args:
        category_path: Full category path

    Returns:
        Tuple for sorting (order_index, path)
    """
    parsed = CategoryPath.parse(category_path)
    if not parsed:
        return (999, category_path)

    root = parsed.root
    try:
        order = CATEGORY_ORDER.index(root)
    except ValueError:
        order = 999

    return (order, category_path)
