"""
Variable nodes for data flow and storage.

This module provides nodes for setting and getting variables in the execution context.
"""

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.services.variable_resolver import resolve_variables
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from loguru import logger


@node(category="variable")
@properties(
    PropertyDef(
        "variable_name",
        PropertyType.STRING,
        required=True,
        label="Variable Name",
        tooltip="Name of the variable to set",
        placeholder="my_variable",
    ),
    PropertyDef(
        "default_value",
        PropertyType.ANY,
        default=None,
        label="Default Value",
        tooltip="Default value if no input provided",
    ),
    PropertyDef(
        "variable_type",
        PropertyType.CHOICE,
        default="String",
        choices=[
            "String",
            "Boolean",
            "Int32",
            "Float",
            "Object",
            "Array",
            "List",
            "Dict",
            "FilePath",
            "DataTable",
        ],
        label="Variable Type",
        tooltip="Type to convert value to",
    ),
)
class SetVariableNode(BaseNode):
    """
    Set variable node - stores a value in the execution context.

    Stores a value under a variable name for later retrieval.
    """

    # @category: data
    # @requires: none
    # @ports: value, variable_name -> value

    def __init__(
        self,
        node_id: str,
        name: str = "Set Variable",
        **kwargs,
    ) -> None:
        """
        Initialize set variable node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
        """
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "SetVariableNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # value port is optional - can use default_value from config instead
        self.add_input_port("value", DataType.ANY, required=False)
        self.add_input_port("variable_name", DataType.STRING, required=False)
        self.add_output_port("value", DataType.ANY)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute set variable.

        Args:
            context: Execution context for the workflow

        Returns:
            Success result after storing the variable
        """
        self.status = NodeStatus.RUNNING

        try:
            variable_name = self.get_parameter("variable_name")
            value = self.get_parameter("value", self.get_parameter("default_value"))
            variable_type = self.get_parameter("variable_type", "String")

            # Resolve {{variable}} patterns in value
            if isinstance(value, str):
                value = resolve_variables(value, context.variables)

            if not variable_name:
                raise ValueError("Variable name is required")

            # Apply type conversion if specified
            if value is not None and variable_type != "String":
                try:
                    if variable_type == "Boolean":
                        if isinstance(value, str):
                            value = value.lower() in ("true", "1", "yes", "on")
                        else:
                            value = bool(value)
                    elif variable_type == "Int32":
                        value = int(value)
                    elif variable_type == "Float":
                        value = float(value)
                    elif variable_type == "FilePath":
                        # Keep as string but validate path exists (optional)
                        value = str(value)
                    elif variable_type in ("Object", "Dict"):
                        if isinstance(value, str):
                            import json

                            value = json.loads(value)
                        elif not isinstance(value, dict):
                            value = {"value": value}
                    elif variable_type in ("Array", "List"):
                        if isinstance(value, str):
                            import json

                            try:
                                value = json.loads(value)
                            except json.JSONDecodeError:
                                # Treat as comma-separated list
                                value = [
                                    v.strip() for v in value.split(",") if v.strip()
                                ]
                        elif not isinstance(value, list):
                            value = [value]
                    elif variable_type == "DataTable":
                        if isinstance(value, str):
                            import json

                            value = json.loads(value)
                except Exception as e:
                    logger.warning(
                        f"Failed to convert value '{value}' to {variable_type}: {e}"
                    )
                    # Keep original value if conversion fails

            # Store in context
            context.set_variable(variable_name, value)

            # Output the value
            self.set_output_value("value", value)

            self.status = NodeStatus.SUCCESS
            logger.info(
                f"Set variable '{variable_name}' = {value} (Type: {type(value).__name__})"
            )

            return {
                "success": True,
                "data": {
                    "variable_name": variable_name,
                    "value": value,
                    "type": type(value).__name__,
                },
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to set variable: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@node(category="variable")
@properties(
    PropertyDef(
        "variable_name",
        PropertyType.STRING,
        required=True,
        label="Variable Name",
        tooltip="Name of the variable to get",
        placeholder="my_variable",
    ),
    PropertyDef(
        "default_value",
        PropertyType.ANY,
        default=None,
        label="Default Value",
        tooltip="Default value if variable not found",
    ),
)
class GetVariableNode(BaseNode):
    """
    Get variable node - retrieves a value from the execution context.

    Retrieves a previously stored variable value.
    """

    # @category: data
    # @requires: none
    # @ports: variable_name -> value

    def __init__(
        self,
        node_id: str,
        name: str = "Get Variable",
        **kwargs,
    ) -> None:
        """
        Initialize get variable node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
        """
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetVariableNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # variable_name optional - can come from config or port
        self.add_input_port("variable_name", DataType.STRING, required=False)
        self.add_output_port("value", DataType.ANY)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute get variable.

        Args:
            context: Execution context for the workflow

        Returns:
            Success result with the variable value
        """
        self.status = NodeStatus.RUNNING

        try:
            variable_name = self.get_parameter("variable_name")

            if not variable_name:
                raise ValueError("Variable name is required")

            # Get value from context
            value = context.get_variable(variable_name)

            # Use default if not found
            if value is None:
                value = self.get_parameter("default_value")

            # Output the value
            self.set_output_value("value", value)

            self.status = NodeStatus.SUCCESS
            logger.info(f"Get variable '{variable_name}' = {value}")

            return {
                "success": True,
                "data": {"variable_name": variable_name, "value": value},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to get variable: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@node(category="variable")
@properties(
    PropertyDef(
        "variable_name",
        PropertyType.STRING,
        required=True,
        label="Variable Name",
        tooltip="Name of the variable to increment",
        placeholder="counter",
    ),
    PropertyDef(
        "increment",
        PropertyType.FLOAT,
        default=1.0,
        label="Increment",
        tooltip="Amount to increment by",
    ),
)
class IncrementVariableNode(BaseNode):
    """
    Increment variable node - increments a numeric variable.

    Retrieves a variable, increments it, and stores the result.
    """

    # @category: data
    # @requires: none
    # @ports: variable_name, increment -> value

    def __init__(
        self,
        node_id: str,
        name: str = "Increment Variable",
        **kwargs,
    ) -> None:
        """
        Initialize increment variable node.

        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
        """
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "IncrementVariableNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Ports optional - can come from config or port connections
        self.add_input_port("variable_name", DataType.STRING, required=False)
        self.add_input_port("increment", DataType.FLOAT, required=False)
        self.add_output_port("value", DataType.FLOAT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute increment variable.

        Args:
            context: Execution context for the workflow

        Returns:
            Success result with the new value
        """
        self.status = NodeStatus.RUNNING

        try:
            variable_name = self.get_parameter("variable_name")
            increment = self.get_parameter("increment", 1.0)

            if not variable_name:
                raise ValueError("Variable name is required")

            # Get current value
            current_value = context.get_variable(variable_name)
            if current_value is None:
                current_value = 0

            # Increment
            new_value = float(current_value) + float(increment)

            # Store new value
            context.set_variable(variable_name, new_value)

            # Output the new value
            self.set_output_value("value", new_value)

            self.status = NodeStatus.SUCCESS
            logger.info(
                f"Incremented variable '{variable_name}': {current_value} + {increment} = {new_value}"
            )

            return {
                "success": True,
                "data": {
                    "variable_name": variable_name,
                    "old_value": current_value,
                    "increment": increment,
                    "new_value": new_value,
                },
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to increment variable: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}
