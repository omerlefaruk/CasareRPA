from typing import Any, Dict, List
from pydantic import BaseModel, Field, validator
from loguru import logger


class WorkflowMetadataSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

    @validator("name")
    def check_name(cls, v):
        if any(p in v.lower() for p in ["__import__", "eval", "exec"]):
            raise ValueError("Dangerous pattern")
        return v


class WorkflowNodeSchema(BaseModel):
    node_id: str = Field(..., min_length=1, max_length=128)
    node_type: str


class WorkflowSchema(BaseModel):
    metadata: WorkflowMetadataSchema
    nodes: List[WorkflowNodeSchema] = Field(..., min_items=1)


def validate_workflow_json(data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        WorkflowSchema(**data)
        return data
    except Exception as e:
        raise ValueError(f"Invalid workflow: {e}")
