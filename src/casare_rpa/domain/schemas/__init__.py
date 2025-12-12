"""
Schema system for CasareRPA.

Provides:
- Property definitions for nodes via @properties decorator
- AI workflow generation schemas with security validation
"""

from casare_rpa.domain.schemas.property_schema import NodeSchema, PropertyDef
from casare_rpa.domain.schemas.property_types import PropertyType
from casare_rpa.domain.schemas.workflow_ai import (
    ConnectionSchema,
    NodeConfigSchema,
    NodeSchema as AINodeSchema,
    PositionSchema,
    SecurityValidationError,
    WorkflowAISchema,
    WorkflowMetadataSchema,
    WorkflowSettingsSchema,
    DANGEROUS_PATTERNS,
    MAX_CONFIG_DEPTH,
    MAX_CONNECTIONS,
    MAX_NODE_ID_LENGTH,
    MAX_NODES,
    MAX_STRING_LENGTH,
)

__all__ = [
    # Property schema (existing)
    "PropertyType",
    "PropertyDef",
    "NodeSchema",
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
