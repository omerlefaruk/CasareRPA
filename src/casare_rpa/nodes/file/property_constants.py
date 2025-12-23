"""
Property constants for file operation nodes.

Provides reusable PropertyDef definitions to ensure consistency
across all file-related nodes (CSV, JSON, ZIP, directories).

Usage:
    from casare_rpa.nodes.file.property_constants import (
        FILE_PATH,
        FILE_ENCODING,
        CSV_DELIMITER,
    )

    @properties(
        FILE_PATH,
        FILE_ENCODING,
        CSV_DELIMITER,
        PropertyDef("custom_prop", PropertyType.STRING, default=""),
    )
    @node(category="file")
    class MyFileNode(BaseNode):
        ...
"""

from casare_rpa.domain.schemas import PropertyDef, PropertyType

# =============================================================================
# Core File Path Properties
# =============================================================================

FILE_PATH = PropertyDef(
    "file_path",
    PropertyType.STRING,
    required=True,
    label="File Path",
    placeholder="C:\\path\\to\\file",
    tooltip="Path to the file",
)

FILE_PATH_INPUT = PropertyDef(
    "file_path",
    PropertyType.STRING,
    required=True,
    label="File Path",
    placeholder="C:\\path\\to\\input.csv",
    tooltip="Path to the input file",
)

FILE_PATH_OUTPUT = PropertyDef(
    "file_path",
    PropertyType.STRING,
    required=True,
    label="File Path",
    placeholder="C:\\path\\to\\output.csv",
    tooltip="Path to the output file",
)


# =============================================================================
# Encoding Properties
# =============================================================================

FILE_ENCODING = PropertyDef(
    "encoding",
    PropertyType.STRING,
    default="utf-8",
    label="Encoding",
    tooltip="File encoding (e.g., utf-8, latin-1, cp1252)",
)


# =============================================================================
# CSV Properties
# =============================================================================

CSV_DELIMITER = PropertyDef(
    "delimiter",
    PropertyType.STRING,
    default=",",
    label="Delimiter",
    tooltip="Field delimiter character",
)

CSV_HAS_HEADER = PropertyDef(
    "has_header",
    PropertyType.BOOLEAN,
    default=True,
    label="Has Header",
    tooltip="Whether the CSV file has a header row",
)

CSV_WRITE_HEADER = PropertyDef(
    "write_header",
    PropertyType.BOOLEAN,
    default=True,
    label="Write Header",
    tooltip="Whether to write header row",
)

CSV_QUOTECHAR = PropertyDef(
    "quotechar",
    PropertyType.STRING,
    default='"',
    label="Quote Char",
    tooltip="Character used to quote fields",
    tab="advanced",
)

CSV_SKIP_ROWS = PropertyDef(
    "skip_rows",
    PropertyType.INTEGER,
    default=0,
    label="Skip Rows",
    tooltip="Number of rows to skip at start",
    tab="advanced",
)

CSV_MAX_ROWS = PropertyDef(
    "max_rows",
    PropertyType.INTEGER,
    default=0,
    label="Max Rows (0=unlimited)",
    tooltip="Maximum rows to read (0 for unlimited)",
    tab="advanced",
)

CSV_STRICT = PropertyDef(
    "strict",
    PropertyType.BOOLEAN,
    default=False,
    label="Strict Mode",
    tooltip="Enable strict parsing mode",
    tab="advanced",
)


# =============================================================================
# JSON Properties
# =============================================================================

JSON_INDENT = PropertyDef(
    "indent",
    PropertyType.INTEGER,
    default=2,
    label="Indent",
    tooltip="Number of spaces for indentation",
)

JSON_ENSURE_ASCII = PropertyDef(
    "ensure_ascii",
    PropertyType.BOOLEAN,
    default=False,
    label="Ensure ASCII",
    tooltip="Escape non-ASCII characters",
)


# =============================================================================
# ZIP Properties
# =============================================================================

ZIP_PATH = PropertyDef(
    "zip_path",
    PropertyType.STRING,
    required=True,
    label="ZIP Path",
    placeholder="C:\\output\\archive.zip",
    tooltip="Path to the ZIP archive",
)

ZIP_SOURCE_PATH = PropertyDef(
    "source_path",
    PropertyType.STRING,
    default="",
    label="Source Path",
    placeholder="C:\\folder\\to\\zip or C:\\folder\\*.txt",
    tooltip="Folder path (zips entire folder) or glob pattern (e.g., *.txt)",
)

ZIP_BASE_DIR = PropertyDef(
    "base_dir",
    PropertyType.STRING,
    default="",
    label="Base Directory",
    placeholder="C:\\source\\folder",
    tooltip="Base directory for relative paths in archive (auto-set if source_path is folder)",
)

ZIP_COMPRESSION = PropertyDef(
    "compression",
    PropertyType.CHOICE,
    default="ZIP_DEFLATED",
    choices=["ZIP_STORED", "ZIP_DEFLATED"],
    label="Compression",
    tooltip="Compression method to use",
)

ZIP_EXTRACT_TO = PropertyDef(
    "extract_to",
    PropertyType.STRING,
    required=True,
    label="Extract To",
    placeholder="C:\\output\\extracted",
    tooltip="Directory to extract files to",
)


# =============================================================================
# Helper Functions for Common Property Groups
# =============================================================================


def get_file_io_properties() -> list[PropertyDef]:
    """Get common file I/O properties (file_path, encoding)."""
    return [FILE_PATH, FILE_ENCODING]


def get_csv_read_properties() -> list[PropertyDef]:
    """Get standard CSV read properties."""
    return [
        FILE_PATH_INPUT,
        CSV_DELIMITER,
        CSV_HAS_HEADER,
        FILE_ENCODING,
        CSV_QUOTECHAR,
        CSV_SKIP_ROWS,
        CSV_MAX_ROWS,
        CSV_STRICT,
    ]


def get_csv_write_properties() -> list[PropertyDef]:
    """Get standard CSV write properties."""
    return [
        FILE_PATH_OUTPUT,
        CSV_DELIMITER,
        CSV_WRITE_HEADER,
        FILE_ENCODING,
    ]


def get_json_read_properties() -> list[PropertyDef]:
    """Get standard JSON read properties."""
    return [FILE_PATH_INPUT, FILE_ENCODING]


def get_json_write_properties() -> list[PropertyDef]:
    """Get standard JSON write properties."""
    return [FILE_PATH_OUTPUT, FILE_ENCODING, JSON_INDENT, JSON_ENSURE_ASCII]


def get_zip_create_properties() -> list[PropertyDef]:
    """Get standard ZIP creation properties."""
    return [ZIP_PATH, ZIP_SOURCE_PATH, ZIP_BASE_DIR, ZIP_COMPRESSION]


def get_zip_extract_properties() -> list[PropertyDef]:
    """Get standard ZIP extraction properties."""
    return [ZIP_PATH, ZIP_EXTRACT_TO]


__all__ = [
    # File path properties
    "FILE_PATH",
    "FILE_PATH_INPUT",
    "FILE_PATH_OUTPUT",
    # Encoding
    "FILE_ENCODING",
    # CSV properties
    "CSV_DELIMITER",
    "CSV_HAS_HEADER",
    "CSV_WRITE_HEADER",
    "CSV_QUOTECHAR",
    "CSV_SKIP_ROWS",
    "CSV_MAX_ROWS",
    "CSV_STRICT",
    # JSON properties
    "JSON_INDENT",
    "JSON_ENSURE_ASCII",
    # ZIP properties
    "ZIP_PATH",
    "ZIP_SOURCE_PATH",
    "ZIP_BASE_DIR",
    "ZIP_COMPRESSION",
    "ZIP_EXTRACT_TO",
    # Helper functions
    "get_file_io_properties",
    "get_csv_read_properties",
    "get_csv_write_properties",
    "get_json_read_properties",
    "get_json_write_properties",
    "get_zip_create_properties",
    "get_zip_extract_properties",
]
