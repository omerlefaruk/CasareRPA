"""
Property types for node configuration schema.

Defines the types of properties that can be used in node schemas.
"""

from enum import Enum


class PropertyType(str, Enum):
    """Types of properties for node configuration."""

    # Basic types
    STRING = "string"
    TEXT = "text"  # Multi-line text area
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"

    # Selection types
    CHOICE = "choice"  # Dropdown with predefined choices
    MULTI_CHOICE = "multi_choice"  # Multiple selection

    # File/Path types
    FILE_PATH = "file_path"
    DIRECTORY_PATH = "directory_path"
    FILE_PATTERN = "file_pattern"  # Glob pattern

    # Advanced types
    JSON = "json"  # JSON object
    CODE = "code"  # Code snippet (Python, JavaScript, etc.)
    SELECTOR = "selector"  # Web/desktop element selector
    COLOR = "color"  # Color picker
    DATE = "date"  # Date picker
    TIME = "time"  # Time picker
    DATETIME = "datetime"  # DateTime picker
    LIST = "list"  # List of values

    # Custom widget type
    CUSTOM = "custom"  # Fully custom widget class
