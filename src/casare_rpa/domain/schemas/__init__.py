"""
Schema system for CasareRPA.

Provides:
- Property definitions for nodes via @properties decorator
- AI workflow generation schemas with security validation
- Common PropertyDef constants for reuse across nodes
"""

from casare_rpa.domain.schemas.common_properties import (
    PROP_BODY,
    PROP_CREATE_DIRS,
    # Structured data
    PROP_DELIMITER,
    PROP_DIRECTORY_PATH,
    PROP_ENCODING,
    PROP_ENCODING_CHOICE,
    # File properties
    PROP_FILE_PATH,
    PROP_FILE_PATH_OPTIONAL,
    PROP_HAS_HEADER,
    PROP_HEADERS,
    PROP_INDENT,
    PROP_METHOD,
    PROP_OUTPUT_PATH,
    # Boolean flags
    PROP_OVERWRITE,
    PROP_RECURSIVE,
    PROP_RETRY_COUNT,
    PROP_RETRY_INTERVAL,
    # Selector
    PROP_SELECTOR,
    PROP_SELECTOR_REQUIRED,
    # Core properties
    PROP_TIMEOUT,
    PROP_TIMEOUT_SECONDS,
    # HTTP
    PROP_URL,
    PROP_VALUE,
    # Variable
    PROP_VARIABLE_NAME,
    get_csv_properties,
    get_file_properties,
    get_http_properties,
    # Helper functions
    get_retry_properties,
)
from casare_rpa.domain.schemas.property_schema import NodeSchema, PropertyDef
from casare_rpa.domain.schemas.property_types import PropertyType
from casare_rpa.domain.schemas.workflow_ai import (
    DANGEROUS_PATTERNS,
    MAX_CONFIG_DEPTH,
    MAX_CONNECTIONS,
    MAX_NODE_ID_LENGTH,
    MAX_NODES,
    MAX_STRING_LENGTH,
    ConnectionSchema,
    NodeConfigSchema,
    PositionSchema,
    SecurityValidationError,
    WorkflowAISchema,
    WorkflowMetadataSchema,
    WorkflowSettingsSchema,
)
from casare_rpa.domain.schemas.workflow_ai import (
    NodeSchema as AINodeSchema,
)

__all__ = [
    # Property schema (existing)
    "PropertyType",
    "PropertyDef",
    "NodeSchema",
    # Common property constants
    "PROP_TIMEOUT",
    "PROP_TIMEOUT_SECONDS",
    "PROP_RETRY_COUNT",
    "PROP_RETRY_INTERVAL",
    "PROP_FILE_PATH",
    "PROP_FILE_PATH_OPTIONAL",
    "PROP_DIRECTORY_PATH",
    "PROP_OUTPUT_PATH",
    "PROP_ENCODING",
    "PROP_ENCODING_CHOICE",
    "PROP_DELIMITER",
    "PROP_HAS_HEADER",
    "PROP_INDENT",
    "PROP_SELECTOR",
    "PROP_SELECTOR_REQUIRED",
    "PROP_OVERWRITE",
    "PROP_CREATE_DIRS",
    "PROP_RECURSIVE",
    "PROP_URL",
    "PROP_METHOD",
    "PROP_HEADERS",
    "PROP_BODY",
    "PROP_VARIABLE_NAME",
    "PROP_VALUE",
    # Property helper functions
    "get_retry_properties",
    "get_file_properties",
    "get_csv_properties",
    "get_http_properties",
    # AI workflow schemas
    "WorkflowAISchema",
    "WorkflowMetadataSchema",
    "AINodeSchema",
    "NodeConfigSchema",
    "ConnectionSchema",
    "WorkflowSettingsSchema",
    "PositionSchema",
    "SecurityValidationError",
    # Constants
    "MAX_NODES",
    "MAX_CONNECTIONS",
    "MAX_NODE_ID_LENGTH",
    "MAX_CONFIG_DEPTH",
    "MAX_STRING_LENGTH",
    "DANGEROUS_PATTERNS",
]
