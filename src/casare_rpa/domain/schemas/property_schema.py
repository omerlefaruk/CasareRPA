"""
Property schema system for declarative node configuration.

Provides PropertyDef and NodeSchema for defining node properties
once and auto-generating config, widgets, and validation.

Note: Use the @properties decorator from casare_rpa.domain.decorators
to apply PropertyDef definitions to node classes.
"""

import logging
import re
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

logger = logging.getLogger(__name__)

from casare_rpa.domain.schemas.property_types import PropertyType

# PERFORMANCE: Module-level type validators to avoid rebuilding on every call
# Previously rebuilt with 18 lambdas on every _validate_type() invocation
TYPE_VALIDATORS: dict[PropertyType, Callable[[Any], bool]] = {
    PropertyType.STRING: lambda v: isinstance(v, str),
    PropertyType.TEXT: lambda v: isinstance(v, str),
    PropertyType.INTEGER: lambda v: isinstance(v, int) and not isinstance(v, bool),
    PropertyType.FLOAT: lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    PropertyType.BOOLEAN: lambda v: isinstance(v, bool),
    PropertyType.ANY: lambda v: True,
    PropertyType.CHOICE: lambda v: isinstance(v, str),
    PropertyType.MULTI_CHOICE: lambda v: isinstance(v, list),
    PropertyType.LIST: lambda v: isinstance(v, list),
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
    PropertyType.CUSTOM: lambda v: True,
}


@dataclass
class PropertyDef:
    """
    Definition of a single node property.

    Used in @properties decorator to declaratively define
    node configuration properties.
    """

    name: str
    """Property name (becomes config key)."""

    type: PropertyType
    """Property type (STRING, INTEGER, BOOLEAN, etc.)."""

    default: Any = None
    """Default value for the property."""

    label: str | None = None
    """Display label in UI (auto-generated from name if None)."""

    placeholder: str = ""
    """Placeholder text for input widgets."""

    choices: list[str] | None = None
    """Available choices for CHOICE/MULTI_CHOICE types."""

    tab: str = "properties"
    """Tab in properties panel where this property appears."""

    readonly: bool = False
    """Whether property is read-only in UI."""

    tooltip: str = ""
    """Tooltip shown on hover in UI."""

    required: bool = False
    """Whether property must have a value (not None/empty)."""

    min_value: float | None = None
    """Minimum value for numeric types."""

    max_value: float | None = None
    """Maximum value for numeric types."""

    widget_class: type | None = None
    """Custom widget class for CUSTOM type or special rendering."""

    essential: bool = False
    """Whether this property is essential (visible when node is collapsed)."""

    # NEW fields for enhanced property system (backward compatible with defaults)
    visibility: Literal["essential", "normal", "advanced", "internal"] = "normal"
    """Property visibility level in UI."""

    order: int = 0
    """Sort order for property display (lower = first)."""

    display_when: dict[str, Any] | None = None
    """Conditional display: show only when other properties match these values."""

    hidden_when: dict[str, Any] | None = None
    """Conditional hiding: hide when other properties match these values."""

    dynamic_choices: Callable[[dict[str, Any]], list[str]] | None = None
    """Callable that returns choices based on current config state."""

    dynamic_default: Callable[[dict[str, Any]], Any] | None = None
    """Callable that returns default value based on current config state."""

    group: str | None = None
    """Group name for organizing related properties together."""

    group_collapsed: bool = True
    """Whether the group starts collapsed in UI."""

    pattern: str | None = None
    """Regex pattern for STRING validation."""

    supports_expressions: bool = True
    """Whether this property supports expression syntax (e.g., {{variable}})."""

    metadata: dict[str, Any] = field(default_factory=dict)
    """Additional metadata attributes for the property."""

    def __init__(
        self,
        name: str,
        type: PropertyType,
        default: Any = None,
        label: str | None = None,
        placeholder: str = "",
        choices: list[str] | None = None,
        tab: str = "properties",
        readonly: bool = False,
        tooltip: str = "",
        required: bool = False,
        min_value: float | None = None,
        max_value: float | None = None,
        widget_class: type | None = None,
        essential: bool = False,
        visibility: Literal["essential", "normal", "advanced", "internal"] = "normal",
        order: int = 0,
        display_when: dict[str, Any] | None = None,
        hidden_when: dict[str, Any] | None = None,
        dynamic_choices: Callable[[dict[str, Any]], list[str]] | None = None,
        dynamic_default: Callable[[dict[str, Any]], Any] | None = None,
        group: str | None = None,
        group_collapsed: bool = True,
        pattern: str | None = None,
        supports_expressions: bool = True,
        **kwargs: Any,
    ) -> None:
        self.name = name
        self.type = type
        self.default = default
        self.label = label
        self.placeholder = placeholder
        self.choices = choices
        self.tab = tab
        self.readonly = readonly
        self.tooltip = tooltip
        self.required = required
        self.min_value = min_value
        self.max_value = max_value
        self.widget_class = widget_class
        self.essential = essential
        self.visibility = visibility
        self.order = order
        self.display_when = display_when
        self.hidden_when = hidden_when
        self.dynamic_choices = dynamic_choices
        self.dynamic_default = dynamic_default
        self.group = group
        self.group_collapsed = group_collapsed
        self.pattern = pattern
        self.supports_expressions = supports_expressions
        self.metadata = kwargs

        # Post-init logic
        if self.label is None:
            self.label = self.name.replace("_", " ").title()

        if self.essential and self.visibility == "normal":
            self.visibility = "essential"

        if self.visibility == "essential" and not self.essential:
            self.essential = True

        # Add kwargs as attributes for easy access
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __post_init__(self) -> None:
        # Since we added a manual __init__ to support **kwargs, we move post_init logic there.
        pass


@dataclass
class NodeSchema:
    """
    Schema for a node's configuration properties.

    Attached to node classes via @properties decorator.
    """

    properties: list[PropertyDef] = field(default_factory=list)
    """List of property definitions."""

    def get_default_config(self) -> dict[str, Any]:
        """
        Generate default configuration dictionary from schema.

        Returns:
            Dict mapping property names to default values
        """
        return {prop.name: prop.default for prop in self.properties}

    def validate_config(self, config: dict[str, Any]) -> tuple[bool, str]:
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
                    errors.append(f"{prop.label or prop.name} must be >= {prop.min_value}")
                if prop.max_value is not None and value > prop.max_value:
                    errors.append(f"{prop.label or prop.name} must be <= {prop.max_value}")

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

            # Pattern validation for STRING types
            if prop.pattern and prop.type == PropertyType.STRING and isinstance(value, str):
                if not re.match(prop.pattern, value):
                    errors.append(f"{prop.label or prop.name} does not match required pattern")

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
        # Uses module-level TYPE_VALIDATORS for O(1) lookup
        # Previously rebuilt dict with 18 lambdas on every call
        validator = TYPE_VALIDATORS.get(prop.type)
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

        # Handle empty strings - only convert to default for non-string types
        # Empty string is a valid value for STRING, TEXT, etc.
        if value == "":
            if prop.type in (
                PropertyType.STRING,
                PropertyType.TEXT,
                PropertyType.FILE_PATH,
                PropertyType.DIRECTORY_PATH,
                PropertyType.CODE,
                PropertyType.SELECTOR,
                PropertyType.ANY,  # ANY should preserve empty strings
            ):
                return value  # Keep empty string as-is
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

    def get_property(self, name: str) -> PropertyDef | None:
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

    def get_essential_properties(self) -> list[str]:
        """
        Get list of essential property names.

        Essential properties are shown when the node is collapsed.

        Returns:
            List of property names marked as essential
        """
        return [prop.name for prop in self.properties if prop.essential]

    def get_collapsible_properties(self) -> list[str]:
        """
        Get list of collapsible (non-essential) property names.

        Collapsible properties are hidden when the node is collapsed.

        Returns:
            List of property names NOT marked as essential
        """
        return [prop.name for prop in self.properties if not prop.essential]

    def should_display(self, prop_name: str, current_config: dict[str, Any]) -> bool:
        """
        Check if property should be displayed based on conditions.

        Evaluates display_when and hidden_when conditions against the
        current configuration state.

        Args:
            prop_name: Name of the property to check
            current_config: Current configuration dictionary

        Returns:
            True if property should be displayed, False otherwise
        """
        prop = self.get_property(prop_name)
        if not prop:
            return False

        # Internal properties are never displayed
        if prop.visibility == "internal":
            return False

        # Check display_when conditions (all must match to display)
        if prop.display_when:
            for key, expected in prop.display_when.items():
                actual = current_config.get(key)
                # Support both single value and list of allowed values
                if isinstance(expected, (list, tuple)):
                    if actual not in expected:
                        return False
                elif actual != expected:
                    return False

        # Check hidden_when conditions (any match hides the property)
        if prop.hidden_when:
            for key, expected in prop.hidden_when.items():
                actual = current_config.get(key)
                # Support both single value and list of values that trigger hiding
                if isinstance(expected, (list, tuple)):
                    if actual in expected:
                        return False
                elif actual == expected:
                    return False

        return True

    def get_sorted_properties(self) -> list[PropertyDef]:
        """
        Get properties sorted by order field.

        Returns:
            List of PropertyDef sorted by order (ascending)
        """
        return sorted(self.properties, key=lambda p: p.order)

    def get_properties_by_visibility(self, visibility: str) -> list[PropertyDef]:
        """
        Get properties filtered by visibility level.

        Args:
            visibility: One of "essential", "normal", "advanced", "internal"

        Returns:
            List of PropertyDef with matching visibility
        """
        return [p for p in self.properties if p.visibility == visibility]

    def get_properties_by_group(self) -> dict[str | None, list[PropertyDef]]:
        """
        Group properties by their group field.

        Properties without a group are keyed under None.

        Returns:
            Dict mapping group names to lists of PropertyDef
        """
        groups: dict[str | None, list[PropertyDef]] = defaultdict(list)
        for prop in self.get_sorted_properties():
            groups[prop.group].append(prop)
        return dict(groups)

    def get_dynamic_choices(
        self, prop_name: str, current_config: dict[str, Any]
    ) -> list[str] | None:
        """
        Get dynamic choices for a property based on current config.

        Args:
            prop_name: Name of the property
            current_config: Current configuration dictionary

        Returns:
            List of choices if dynamic_choices is defined, None otherwise
        """
        prop = self.get_property(prop_name)
        if not prop or not prop.dynamic_choices:
            return None

        try:
            return prop.dynamic_choices(current_config)
        except Exception as e:
            logger.warning(f"Error getting dynamic choices for {prop_name}: {e}")
            return prop.choices  # Fall back to static choices

    def get_dynamic_default(self, prop_name: str, current_config: dict[str, Any]) -> Any:
        """
        Get dynamic default value for a property based on current config.

        Args:
            prop_name: Name of the property
            current_config: Current configuration dictionary

        Returns:
            Dynamic default if defined, otherwise static default
        """
        prop = self.get_property(prop_name)
        if not prop:
            return None

        if not prop.dynamic_default:
            return prop.default

        try:
            return prop.dynamic_default(current_config)
        except Exception as e:
            logger.warning(f"Error getting dynamic default for {prop_name}: {e}")
            return prop.default
