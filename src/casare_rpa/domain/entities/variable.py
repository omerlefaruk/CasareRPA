"""
CasareRPA - Domain Entity: Variable

Unified variable definition for workflows and projects.
Consolidates VariableDefinition and ProjectVariable into a single class.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict


# Valid Python identifier pattern (excluding reserved keywords)
_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

# Python reserved keywords that cannot be used as variable names
_RESERVED_KEYWORDS = frozenset(
    [
        "False",
        "None",
        "True",
        "and",
        "as",
        "assert",
        "async",
        "await",
        "break",
        "class",
        "continue",
        "def",
        "del",
        "elif",
        "else",
        "except",
        "finally",
        "for",
        "from",
        "global",
        "if",
        "import",
        "in",
        "is",
        "lambda",
        "nonlocal",
        "not",
        "or",
        "pass",
        "raise",
        "return",
        "try",
        "while",
        "with",
        "yield",
    ]
)


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

    def __post_init__(self) -> None:
        """Validate variable attributes after initialization."""
        self._validate_name(self.name)
        self._validate_type(self.type)

    @staticmethod
    def _validate_name(name: str) -> None:
        """Validate variable name is a valid Python identifier."""
        if not name:
            raise ValueError("Variable name cannot be empty")
        if not _IDENTIFIER_PATTERN.match(name):
            raise ValueError(
                f"Variable name '{name}' is not a valid Python identifier. "
                "Must start with letter/underscore, contain only alphanumeric/underscore."
            )
        if name in _RESERVED_KEYWORDS:
            raise ValueError(f"Variable name '{name}' is a Python reserved keyword")
        if len(name) > 128:
            raise ValueError(f"Variable name too long: {len(name)} chars (max 128)")

    @staticmethod
    def _validate_type(var_type: str) -> None:
        """Validate variable type is supported."""
        valid_types = {
            "String",
            "Integer",
            "Float",
            "Boolean",
            "List",
            "Dict",
            "DataTable",
            "Any",
        }
        if var_type not in valid_types:
            raise ValueError(
                f"Invalid variable type '{var_type}'. Valid: {', '.join(sorted(valid_types))}"
            )

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
