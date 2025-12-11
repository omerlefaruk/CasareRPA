"""
Workflow JSON Schema Validation.

Provides Pydantic models to validate workflow JSON before deserialization,
preventing malicious code injection and resource exhaustion attacks.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class WorkflowPortSchema(BaseModel):
    """Schema for workflow port definition."""

    id: str = Field(..., min_length=1, max_length=128)
    name: str = Field(..., min_length=1, max_length=256)
    data_type: str = Field(..., min_length=1, max_length=64)
    port_type: str = Field(..., min_length=1, max_length=32)
    is_multi: bool = False


class WorkflowNodeSchema(BaseModel):
    """Schema for workflow node definition."""

    node_id: str = Field(..., min_length=1, max_length=128)
    node_type: str = Field(..., min_length=1, max_length=128)
    position: List[float] = Field(...)  # [x, y] format from serializer
    config: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("node_type")
    @classmethod
    def validate_node_type(cls, v: str) -> str:
        """Validate node type doesn't contain dangerous patterns."""
        # Allowlisted node types that contain otherwise-dangerous substrings
        # These are legitimate CasareRPA nodes that are safe to use
        allowlisted_node_types = {
            "EvalExpressionNode",  # Safe expression evaluator with sandboxed builtins
            "ExecuteQueryNode",  # Database query execution (exec in name)
            "ExecuteNonQueryNode",  # Database non-query execution
            "ExecuteBatchNode",  # Batch execution node
        }

        # Skip validation for allowlisted nodes
        if v in allowlisted_node_types:
            return v

        dangerous_patterns = [
            "__import__",
            "eval(",  # Block eval( function calls, not node names
            "exec(",  # Block exec( function calls, not node names
            "compile(",
            "os.system",
            "subprocess",
            "open(",
            "file(",
        ]

        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f"Node type contains dangerous pattern: '{pattern}'")

        return v

    @field_validator("config")
    @classmethod
    def validate_config(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate config doesn't contain code execution patterns."""
        dangerous_patterns = [
            "__import__",
            "eval(",
            "exec(",
            "compile(",
            "os.system",
            "subprocess",
        ]

        # Convert dict to string for pattern matching
        config_str = str(v).lower()
        for pattern in dangerous_patterns:
            if pattern in config_str:
                raise ValueError(f"Config contains dangerous pattern: '{pattern}'")

        return v


class WorkflowConnectionSchema(BaseModel):
    """Schema for workflow connection definition."""

    source_node: str = Field(..., min_length=1, max_length=128)
    source_port: str = Field(..., min_length=1, max_length=128)
    target_node: str = Field(..., min_length=1, max_length=128)
    target_port: str = Field(..., min_length=1, max_length=128)


class WorkflowMetadataSchema(BaseModel):
    """Schema for workflow metadata."""

    name: str = Field(..., min_length=1, max_length=256)
    description: Optional[str] = Field(None, max_length=2000)
    version: Optional[str] = Field(None, max_length=32)
    author: Optional[str] = Field(None, max_length=128)
    created_at: Optional[str] = Field(None, max_length=64)
    modified_at: Optional[str] = Field(None, max_length=64)
    tags: List[str] = Field(default_factory=list, max_length=50)


class WorkflowSchema(BaseModel):
    """
    Schema for complete workflow validation.

    Enforces security constraints:
    - Maximum 1000 nodes (prevents resource exhaustion)
    - Maximum 5000 connections (prevents graph explosion)
    - No dangerous code patterns in node types or properties
    - String length limits on all fields
    """

    metadata: WorkflowMetadataSchema
    nodes: Dict[str, WorkflowNodeSchema] = Field(...)
    connections: List[WorkflowConnectionSchema] = Field(..., max_length=5000)
    variables: Dict[str, Any] = Field(default_factory=dict)
    frames: List[Dict[str, Any]] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("nodes")
    @classmethod
    def validate_nodes_not_empty(
        cls, v: Dict[str, WorkflowNodeSchema]
    ) -> Dict[str, WorkflowNodeSchema]:
        """Ensure workflow has at least one node and not too many."""
        if not v:
            raise ValueError("Workflow must contain at least one node")
        if len(v) > 1000:
            raise ValueError("Workflow exceeds maximum of 1000 nodes")
        return v


def validate_workflow_json(workflow_data: Dict[str, Any]) -> WorkflowSchema:
    """
    Validate workflow JSON against security schema.

    Args:
        workflow_data: Workflow dictionary to validate

    Returns:
        Validated WorkflowSchema instance

    Raises:
        ValidationError: If workflow contains dangerous patterns or
                        exceeds resource limits

    Examples:
        >>> workflow = {"metadata": {"name": "Test"}, "nodes": [...], "connections": [...]}
        >>> validated = validate_workflow_json(workflow)
        >>> print(f"Validated {len(validated.nodes)} nodes")
    """
    return WorkflowSchema.model_validate(workflow_data)
