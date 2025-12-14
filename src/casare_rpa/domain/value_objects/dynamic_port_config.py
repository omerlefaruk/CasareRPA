"""
CasareRPA - Dynamic Port Configuration Value Objects

Value objects for Super Node dynamic port management. These define
how input/output ports should change based on the selected action.

Used by SuperNodeMixin in the presentation layer to dynamically
update port visibility based on action dropdown selection.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from casare_rpa.domain.value_objects.types import DataType


@dataclass(frozen=True)
class PortDef:
    """
    Definition for a single port in a Super Node.

    Immutable value object describing a port's name, type, and metadata.
    Used to dynamically create/remove ports based on action selection.
    """

    name: str
    """Port name (e.g., 'file_path', 'content')."""

    data_type: DataType
    """Data type for the port (e.g., DataType.STRING)."""

    required: bool = False
    """Whether this port must be connected for execution."""

    label: Optional[str] = None
    """Display label (auto-generated from name if None)."""

    def __post_init__(self) -> None:
        """Auto-generate label if not provided."""
        if self.label is None:
            # Convert snake_case to Title Case
            object.__setattr__(self, "label", self.name.replace("_", " ").title())


@dataclass(frozen=True)
class ActionPortConfig:
    """
    Port configuration for a specific action in a Super Node.

    Defines which input and output ports should be visible
    when a particular action is selected.
    """

    inputs: tuple[PortDef, ...] = field(default_factory=tuple)
    """Input ports for this action."""

    outputs: tuple[PortDef, ...] = field(default_factory=tuple)
    """Output ports for this action."""

    @classmethod
    def create(
        cls,
        inputs: Optional[List[PortDef]] = None,
        outputs: Optional[List[PortDef]] = None,
    ) -> "ActionPortConfig":
        """
        Factory method to create ActionPortConfig from lists.

        Args:
            inputs: List of input port definitions
            outputs: List of output port definitions

        Returns:
            Immutable ActionPortConfig
        """
        return cls(
            inputs=tuple(inputs or []),
            outputs=tuple(outputs or []),
        )


@dataclass
class DynamicPortSchema:
    """
    Schema mapping actions to their port configurations.

    Used by Super Nodes to define how ports change based on
    the selected action from the dropdown.

    Example:
        schema = DynamicPortSchema()
        schema.register("Read File", ActionPortConfig.create(
            inputs=[PortDef("file_path", DataType.STRING)],
            outputs=[PortDef("content", DataType.STRING)],
        ))
    """

    action_configs: Dict[str, ActionPortConfig] = field(default_factory=dict)
    """Mapping of action name to port configuration."""

    def register(self, action: str, config: ActionPortConfig) -> None:
        """
        Register port configuration for an action.

        Args:
            action: Action name (must match dropdown choice)
            config: Port configuration for this action
        """
        self.action_configs[action] = config

    def get_config(self, action: str) -> Optional[ActionPortConfig]:
        """
        Get port configuration for an action.

        Args:
            action: Action name to look up

        Returns:
            ActionPortConfig if found, None otherwise
        """
        return self.action_configs.get(action)

    def get_actions(self) -> List[str]:
        """
        Get all registered action names.

        Returns:
            List of action names in registration order
        """
        return list(self.action_configs.keys())

    def has_action(self, action: str) -> bool:
        """
        Check if an action is registered.

        Args:
            action: Action name to check

        Returns:
            True if action is registered
        """
        return action in self.action_configs


__all__ = [
    "PortDef",
    "ActionPortConfig",
    "DynamicPortSchema",
]
