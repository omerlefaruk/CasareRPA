"""
Property schema system for declarative node configuration.

Provides PropertyDef and NodeSchema for defining node properties
once and auto-generating config, widgets, and validation.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, Tuple
from loguru import logger

from .property_types import PropertyType


@dataclass
class PropertyDef:
    """
    Definition of a single node property.

    Used in @node_schema decorator to declaratively define
    node configuration properties.
    """

    name: str
    """Property name (becomes config key)."""

    type: PropertyType
    """Property type (STRING, INTEGER, BOOLEAN, etc.)."""

    default: Any = None
    """Default value for the property."""

    label: Optional[str] = None
    """Display label in UI (auto-generated from name if None)."""

    placeholder: str = ""
    """Placeholder text for input widgets."""

    choices: Optional[List[str]] = None
    """Available choices for CHOICE/MULTI_CHOICE types."""

    tab: str = "properties"
    """Tab in properties panel where this property appears."""

    readonly: bool = False
    """Whether property is read-only in UI."""

    tooltip: str = ""
    """Tooltip shown on hover in UI."""

    required: bool = False
    """Whether property must have a value (not None/empty)."""

    min_value: Optional[float] = None
    """Minimum value for numeric types."""

    max_value: Optional[float] = None
    """Maximum value for numeric types."""

    widget_class: Optional[Type] = None
    """Custom widget class for CUSTOM type or special rendering."""

    def __post_init__(self):
        """Auto-generate label if not provided."""
        if self.label is None:
            # Convert snake_case to Title Case
            self.label = self.name.replace("_", " ").title()


@dataclass
class NodeSchema:
    """
    Schema for a node's configuration properties.

    Attached to node classes via @node_schema decorator.
    """

    properties: List[PropertyDef] = field(default_factory=list)
    """List of property definitions."""

    def get_default_config(self) -> Dict[str, Any]:
        """
        Generate default configuration dictionary from schema.

        Returns:
            Dict mapping property names to default values
        """
        return {prop.name: prop.default for prop in self.properties}

    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate configuration against schema.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        errors = []

        for prop in self.properties:
            value = config.get(prop.name)

            # Check required fields
            if prop.required and (value is None or value == ""):
                errors.append(f"{prop.label or prop.name} is required")
                continue

            # Skip validation if value is None and not required
            if value is None:
                continue

            # Coerce string values to proper types (widgets often return strings)
            value = self._coerce_value(prop, value)
            config[prop.name] = value  # Update config with coerced value

            # Type validation
            if not self._validate_type(prop, value):
                # Better error messages for specific types
                if prop.type == PropertyType.FLOAT:
                    type_desc = "number (int or float)"
                elif prop.type == PropertyType.INTEGER:
                    type_desc = "integer"
                else:
                    type_desc = prop.type.value

                errors.append(f"{prop.label or prop.name} must be of type {type_desc}")
                continue

            # Range validation for numeric types
            if prop.type in (PropertyType.INTEGER, PropertyType.FLOAT):
                if prop.min_value is not None and value < prop.min_value:
                    errors.append(
                        f"{prop.label or prop.name} must be >= {prop.min_value}"
                    )
                if prop.max_value is not None and value > prop.max_value:
                    errors.append(
                        f"{prop.label or prop.name} must be <= {prop.max_value}"
                    )

            # Choice validation
            if prop.type == PropertyType.CHOICE:
                if prop.choices and value not in prop.choices:
                    errors.append(
                        f"{prop.label or prop.name} must be one of: {', '.join(prop.choices)}"
                    )

            if prop.type == PropertyType.MULTI_CHOICE:
                if prop.choices and isinstance(value, list):
                    invalid = [v for v in value if v not in prop.choices]
                    if invalid:
                        errors.append(
                            f"{prop.label or prop.name} contains invalid choices: {', '.join(invalid)}"
                        )

        if errors:
            return False, "; ".join(errors)

        return True, ""

    def _validate_type(self, prop: PropertyDef, value: Any) -> bool:
        """
        Validate that value matches property type.

        Args:
            prop: Property definition
            value: Value to validate

        Returns:
            True if type matches, False otherwise
        """
        type_validators = {
            PropertyType.STRING: lambda v: isinstance(v, str),
            PropertyType.INTEGER: lambda v: isinstance(v, int)
            and not isinstance(v, bool),
            PropertyType.FLOAT: lambda v: isinstance(v, (int, float))
            and not isinstance(v, bool),
            PropertyType.BOOLEAN: lambda v: isinstance(v, bool),
            PropertyType.CHOICE: lambda v: isinstance(v, str),
            PropertyType.MULTI_CHOICE: lambda v: isinstance(v, list),
            PropertyType.FILE_PATH: lambda v: isinstance(v, str),
            PropertyType.DIRECTORY_PATH: lambda v: isinstance(v, str),
            PropertyType.FILE_PATTERN: lambda v: isinstance(v, str),
            PropertyType.JSON: lambda v: isinstance(v, (dict, list)),
            PropertyType.CODE: lambda v: isinstance(v, str),
            PropertyType.SELECTOR: lambda v: isinstance(v, str),
            PropertyType.COLOR: lambda v: isinstance(v, str),
            PropertyType.DATE: lambda v: isinstance(v, str),
            PropertyType.TIME: lambda v: isinstance(v, str),
            PropertyType.DATETIME: lambda v: isinstance(v, str),
            PropertyType.CUSTOM: lambda v: True,  # Custom widgets handle validation
        }

        validator = type_validators.get(prop.type)
        if validator is None:
            logger.warning(f"Unknown property type: {prop.type}")
            return True  # Unknown types pass validation

        return validator(value)

    def _coerce_value(self, prop: PropertyDef, value: Any) -> Any:
        """
        Coerce string values to proper types.

        Widgets often return string values even for numeric/boolean types.
        This method converts them to the expected type.

        Args:
            prop: Property definition
            value: Value to coerce

        Returns:
            Coerced value, or original if coercion not needed/possible
        """
        if not isinstance(value, str):
            return value

        # Handle empty strings
        if value == "":
            return prop.default

        try:
            if prop.type == PropertyType.INTEGER:
                return int(value)
            elif prop.type == PropertyType.FLOAT:
                return float(value)
            elif prop.type == PropertyType.BOOLEAN:
                return value.lower() in ("true", "1", "yes", "on")
        except (ValueError, AttributeError):
            # Return original value if coercion fails
            pass

        return value

    def get_property(self, name: str) -> Optional[PropertyDef]:
        """
        Get property definition by name.

        Args:
            name: Property name

        Returns:
            PropertyDef if found, None otherwise
        """
        for prop in self.properties:
            if prop.name == name:
                return prop
        return None
