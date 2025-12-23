"""
CasareRPA - Project Variables

Variable-related classes for project scope.
Uses the unified Variable class from domain.entities.variable.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from casare_rpa.domain.entities.project.base import PROJECT_SCHEMA_VERSION
from casare_rpa.domain.entities.variable import Variable

# Re-export Variable as ProjectVariable for backward compatibility
ProjectVariable = Variable


class VariableScope(Enum):
    """Scope for variable storage."""

    GLOBAL = "global"
    PROJECT = "project"
    SCENARIO = "scenario"


class VariableType(Enum):
    """Supported variable data types."""

    STRING = "String"
    INTEGER = "Integer"
    FLOAT = "Float"
    BOOLEAN = "Boolean"
    LIST = "List"
    DICT = "Dict"
    DATATABLE = "DataTable"


@dataclass
class VariablesFile:
    """
    Container for variables stored in variables.json files.
    Used for both project and global variable storage.
    """

    scope: VariableScope = VariableScope.PROJECT
    variables: Dict[str, Variable] = field(default_factory=dict)
    schema_version: str = PROJECT_SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "$schema_version": self.schema_version,
            "scope": self.scope.value,
            "variables": {name: var.to_dict() for name, var in self.variables.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VariablesFile":
        """Create from dictionary."""
        scope_str = data.get("scope", "project")
        variables_data = data.get("variables", {})

        variables = {
            name: Variable.from_dict(var_data) for name, var_data in variables_data.items()
        }

        return cls(
            scope=VariableScope(scope_str),
            variables=variables,
            schema_version=data.get("$schema_version", PROJECT_SCHEMA_VERSION),
        )

    def get_variable(self, name: str) -> Optional[Variable]:
        """Get variable by name."""
        return self.variables.get(name)

    def set_variable(self, variable: Variable) -> None:
        """Add or update a variable."""
        self.variables[variable.name] = variable

    def remove_variable(self, name: str) -> bool:
        """Remove a variable. Returns True if removed."""
        if name in self.variables:
            del self.variables[name]
            return True
        return False

    def get_default_values(self) -> Dict[str, Any]:
        """Get dictionary of variable names to their default values."""
        return {name: var.default_value for name, var in self.variables.items()}
