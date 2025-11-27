"""
CasareRPA - Workflow Schema
DEPRECATED: This module is being refactored into domain layer.

Import from:
    from casare_rpa.domain.entities.workflow import WorkflowSchema
    from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
    from casare_rpa.domain.entities.node_connection import NodeConnection
    from casare_rpa.domain.entities.workflow import VariableDefinition
"""

import warnings

# Re-export from domain layer for backward compatibility
from ..domain.entities.workflow import WorkflowSchema, VariableDefinition
from ..domain.entities.workflow_metadata import WorkflowMetadata
from ..domain.entities.node_connection import NodeConnection
from ..domain.value_objects.types import SCHEMA_VERSION

# Emit deprecation warning
warnings.warn(
    "Importing from casare_rpa.core.workflow_schema is deprecated. "
    "Import from casare_rpa.domain.entities.workflow instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["WorkflowSchema", "WorkflowMetadata", "NodeConnection", "VariableDefinition", "SCHEMA_VERSION"]
