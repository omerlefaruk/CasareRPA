"""
Common PropertyDef constants for reuse across all nodes.

Provides centralized, reusable PropertyDef definitions to ensure
consistency across all node types. Import specific properties or
use helper functions to get property groups.

Usage:
    from casare_rpa.domain.schemas.common_properties import (
        PROP_TIMEOUT,
        PROP_ENCODING,
        PROP_FILE_PATH,
        get_file_properties,
    )

    @properties(
        PROP_FILE_PATH,
        PROP_ENCODING,
        PROP_TIMEOUT,
    )
    @node(category="file")
    class MyFileNode(BaseNode):
        ...
"""

from casare_rpa.domain.schemas.property_schema import PropertyDef
from casare_rpa.domain.schemas.property_types import PropertyType

# =============================================================================
# Core Timeout Properties
# =============================================================================

PROP_TIMEOUT = PropertyDef(
    "timeout",
    PropertyType.INTEGER,
    default=30000,
    label="Timeout (ms)",
    tooltip="Maximum time to wait in milliseconds",
    min_value=0,
)

PROP_TIMEOUT_SECONDS = PropertyDef(
    "timeout_seconds",
    PropertyType.FLOAT,
    default=30.0,
    label="Timeout (seconds)",
    tooltip="Maximum time to wait in seconds",
    min_value=0.0,
)


# =============================================================================
# Retry Properties
# =============================================================================

PROP_RETRY_COUNT = PropertyDef(
    "retry_count",
    PropertyType.INTEGER,
    default=0,
    label="Retry Count",
    tooltip="Number of retries on failure (0 = no retry)",
    min_value=0,
    max_value=10,
)

PROP_RETRY_INTERVAL = PropertyDef(
    "retry_interval",
    PropertyType.INTEGER,
    default=1000,
    label="Retry Interval (ms)",
    tooltip="Delay between retries in milliseconds",
    min_value=0,
)


# =============================================================================
# File Properties
# =============================================================================

PROP_FILE_PATH = PropertyDef(
    "file_path",
    PropertyType.FILE_PATH,
    default="",
    label="File Path",
    tooltip="Path to the file",
    required=True,
)

PROP_FILE_PATH_OPTIONAL = PropertyDef(
    "file_path",
    PropertyType.FILE_PATH,
    default="",
    label="File Path",
    tooltip="Path to the file",
    required=False,
)

PROP_DIRECTORY_PATH = PropertyDef(
    "directory_path",
    PropertyType.DIRECTORY_PATH,
    default="",
    label="Directory Path",
    tooltip="Path to the directory",
)

PROP_OUTPUT_PATH = PropertyDef(
    "output_path",
    PropertyType.FILE_PATH,
    default="",
    label="Output Path",
    tooltip="Path for output file",
)


# =============================================================================
# Text/Encoding Properties
# =============================================================================

PROP_ENCODING = PropertyDef(
    "encoding",
    PropertyType.STRING,
    default="utf-8",
    label="Encoding",
    tooltip="File encoding (e.g., utf-8, latin-1, cp1252)",
)

PROP_ENCODING_CHOICE = PropertyDef(
    "encoding",
    PropertyType.CHOICE,
    default="utf-8",
    choices=["utf-8", "utf-16", "latin-1", "cp1252", "ascii"],
    label="Encoding",
    tooltip="File encoding",
)


# =============================================================================
# CSV/Structured Data Properties
# =============================================================================

PROP_DELIMITER = PropertyDef(
    "delimiter",
    PropertyType.STRING,
    default=",",
    label="Delimiter",
    tooltip="Field separator character",
)

PROP_HAS_HEADER = PropertyDef(
    "has_header",
    PropertyType.BOOLEAN,
    default=True,
    label="Has Header",
    tooltip="First row contains column names",
)

PROP_INDENT = PropertyDef(
    "indent",
    PropertyType.INTEGER,
    default=2,
    label="Indent",
    tooltip="Number of spaces for indentation",
    min_value=0,
    max_value=8,
)


# =============================================================================
# Selector Properties
# =============================================================================

PROP_SELECTOR = PropertyDef(
    "selector",
    PropertyType.SELECTOR,
    default="",
    label="Selector",
    tooltip="CSS or XPath selector",
    placeholder="#element-id or //xpath",
)

PROP_SELECTOR_REQUIRED = PropertyDef(
    "selector",
    PropertyType.SELECTOR,
    default="",
    label="Selector",
    tooltip="CSS or XPath selector",
    required=True,
)


# =============================================================================
# Boolean Flags
# =============================================================================

PROP_OVERWRITE = PropertyDef(
    "overwrite",
    PropertyType.BOOLEAN,
    default=False,
    label="Overwrite",
    tooltip="Overwrite existing file if it exists",
)

PROP_CREATE_DIRS = PropertyDef(
    "create_directories",
    PropertyType.BOOLEAN,
    default=True,
    label="Create Directories",
    tooltip="Create parent directories if they don't exist",
)

PROP_RECURSIVE = PropertyDef(
    "recursive",
    PropertyType.BOOLEAN,
    default=False,
    label="Recursive",
    tooltip="Process directories recursively",
)


# =============================================================================
# HTTP/Network Properties
# =============================================================================

PROP_URL = PropertyDef(
    "url",
    PropertyType.STRING,
    default="",
    label="URL",
    tooltip="Target URL",
    required=True,
)

PROP_METHOD = PropertyDef(
    "method",
    PropertyType.CHOICE,
    default="GET",
    choices=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    label="Method",
    tooltip="HTTP method",
)

PROP_HEADERS = PropertyDef(
    "headers",
    PropertyType.JSON,
    default={},
    label="Headers",
    tooltip="HTTP headers as JSON object",
)

PROP_BODY = PropertyDef(
    "body",
    PropertyType.TEXT,
    default="",
    label="Body",
    tooltip="Request body",
)


# =============================================================================
# Variable Properties
# =============================================================================

PROP_VARIABLE_NAME = PropertyDef(
    "variable_name",
    PropertyType.STRING,
    default="",
    label="Variable Name",
    tooltip="Name of the variable",
    required=True,
)

PROP_VALUE = PropertyDef(
    "value",
    PropertyType.ANY,
    default="",
    label="Value",
    tooltip="Value to assign",
)


# =============================================================================
# Helper Functions
# =============================================================================


def get_retry_properties() -> list[PropertyDef]:
    """Get standard retry properties (retry_count, retry_interval)."""
    return [PROP_RETRY_COUNT, PROP_RETRY_INTERVAL]


def get_file_properties() -> list[PropertyDef]:
    """Get standard file properties (file_path, encoding)."""
    return [PROP_FILE_PATH, PROP_ENCODING]


def get_csv_properties() -> list[PropertyDef]:
    """Get standard CSV properties (delimiter, has_header, encoding)."""
    return [PROP_DELIMITER, PROP_HAS_HEADER, PROP_ENCODING]


def get_http_properties() -> list[PropertyDef]:
    """Get standard HTTP properties (url, method, headers, body, timeout)."""
    return [PROP_URL, PROP_METHOD, PROP_HEADERS, PROP_BODY, PROP_TIMEOUT]
