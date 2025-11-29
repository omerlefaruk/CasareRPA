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

    id: str = Field(..., min_length=1, max_length=128)
    type: str = Field(..., min_length=1, max_length=128)
    name: str = Field(..., min_length=1, max_length=256)
    position: Dict[str, float] = Field(...)
    properties: Dict[str, Any] = Field(default_factory=dict)
    inputs: List[WorkflowPortSchema] = Field(default_factory=list, max_length=100)
    outputs: List[WorkflowPortSchema] = Field(default_factory=list, max_length=100)

    @field_validator("type")
    @classmethod
    def validate_node_type(cls, v: str) -> str:
        """Validate node type doesn't contain dangerous patterns."""
        dangerous_patterns = [
            "__import__",
            "eval",
            "exec",
            "compile",
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

    @field_validator("properties")
    @classmethod
    def validate_properties(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate properties don't contain code execution patterns."""
        dangerous_patterns = [
            "__import__",
            "eval(",
            "exec(",
            "compile(",
            "os.system",
            "subprocess",
        ]

        # Convert dict to string for pattern matching
        props_str = str(v).lower()
        for pattern in dangerous_patterns:
            if pattern in props_str:
                raise ValueError(f"Properties contain dangerous pattern: '{pattern}'")

        return v


class WorkflowConnectionSchema(BaseModel):
    """Schema for workflow connection definition."""

    id: str = Field(..., min_length=1, max_length=128)
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
    nodes: List[WorkflowNodeSchema] = Field(..., max_length=1000)
    connections: List[WorkflowConnectionSchema] = Field(..., max_length=5000)
    variables: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("nodes")
    @classmethod
    def validate_nodes_not_empty(
        cls, v: List[WorkflowNodeSchema]
    ) -> List[WorkflowNodeSchema]:
        """Ensure workflow has at least one node."""
        if not v:
            raise ValueError("Workflow must contain at least one node")
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
