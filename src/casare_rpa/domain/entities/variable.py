"""
CasareRPA - Domain Entity: Variable

Unified variable definition for workflows and projects.
Consolidates VariableDefinition and ProjectVariable into a single class.
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Variable:
    """
    Unified variable definition for workflows, projects, and global scope.

    This class represents a typed variable with metadata, usable across:
    - Workflow variables
    - Project variables
    - Global variables

    Attributes:
        name: Variable name (must be valid Python identifier)
        type: Variable type (String, Integer, Float, Boolean, List, Dict, DataTable)
        default_value: Default value for the variable
        description: Optional description of the variable's purpose
        sensitive: If True, value should be masked in UI (for passwords, etc.)
        readonly: If True, cannot be modified at runtime
    """

    name: str
    type: str = "String"
    default_value: Any = ""
    description: str = ""
    sensitive: bool = False
    readonly: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "default_value": self.default_value,
            "description": self.description,
            "sensitive": self.sensitive,
            "readonly": self.readonly,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Variable":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            type=data.get("type", "String"),
            default_value=data.get("default_value", ""),
            description=data.get("description", ""),
            sensitive=data.get("sensitive", False),
            readonly=data.get("readonly", False),
        )


# Backward compatibility aliases
VariableDefinition = Variable
ProjectVariable = Variable
