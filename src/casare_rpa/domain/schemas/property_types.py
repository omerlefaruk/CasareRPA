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
    ANY = "any"  # Accepts any type of value (for variable nodes)

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

    # Google integration types
    GOOGLE_CREDENTIAL = "google_credential"  # Google OAuth credential picker
    GOOGLE_SPREADSHEET = "google_spreadsheet"  # Spreadsheet picker (cascading)
    GOOGLE_SHEET = "google_sheet"  # Sheet picker (depends on spreadsheet)
    GOOGLE_DRIVE_FILE = "google_drive_file"  # Drive file picker
    GOOGLE_DRIVE_FOLDER = "google_drive_folder"  # Drive folder picker
