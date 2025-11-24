"""
Variable nodes for data flow and storage.

This module provides nodes for setting and getting variables in the execution context.
"""

from typing import Any, Optional

from ..core.base_node import BaseNode
from ..core.types import NodeStatus, PortType, DataType, ExecutionResult
from ..core.execution_context import ExecutionContext
from loguru import logger


class SetVariableNode(BaseNode):
    """
    Set variable node - stores a value in the execution context.
    
    Stores a value under a variable name for later retrieval.
    """
    
    def __init__(
        self,
        node_id: str,
        name: str = "Set Variable",
        variable_name: str = "",
        default_value: Optional[Any] = None,
        **kwargs
    ) -> None:
        """
        Initialize set variable node.
        
        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            variable_name: Name of the variable to set
            default_value: Default value if no input provided
        """
        config = kwargs.get("config", {"variable_name": variable_name, "default_value": default_value})
        if "variable_name" not in config:
            config["variable_name"] = variable_name
        if "default_value" not in config:
            config["default_value"] = default_value
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "SetVariableNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("value", PortType.INPUT, DataType.ANY)
        self.add_input_port("variable_name", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("value", PortType.OUTPUT, DataType.ANY)
    
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
            # Get variable name from input or config
            variable_name = self.get_input_value("variable_name")
            if variable_name is None:
                variable_name = self.config.get("variable_name", "")
            
            if not variable_name:
                raise ValueError("Variable name is required")
            
            # Get value from input or default
            value = self.get_input_value("value")
            if value is None:
                value = self.config.get("default_value")
            
            # Apply type conversion if specified
            variable_type = self.config.get("variable_type", "String")
            
            if value is not None and variable_type != "String":
                try:
                    if variable_type == "Boolean":
                        if isinstance(value, str):
                            value = value.lower() in ("true", "1", "yes", "on")
                        else:
                            value = bool(value)
                    elif variable_type == "Int32":
                        value = int(value)
                    elif variable_type in ("Object", "Array", "DataTable"):
                        if isinstance(value, str):
                            import json
                            value = json.loads(value)
                except Exception as e:
                    logger.warning(f"Failed to convert value '{value}' to {variable_type}: {e}")
                    # Keep original value if conversion fails
            
            # Store in context
            context.set_variable(variable_name, value)
            
            # Output the value
            self.set_output_value("value", value)
            
            self.status = NodeStatus.SUCCESS
            logger.info(f"Set variable '{variable_name}' = {value} (Type: {type(value).__name__})")
            
            return {
                "success": True,
                "data": {
                    "variable_name": variable_name,
                    "value": value,
                    "type": type(value).__name__
                },
                "next_nodes": ["exec_out"]
            }
            
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to set variable: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }
    
    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        variable_name = self.config.get("variable_name", "")
        if not variable_name:
            return False, "Variable name is required"
        return True, ""


class GetVariableNode(BaseNode):
    """
    Get variable node - retrieves a value from the execution context.
    
    Retrieves a previously stored variable value.
    """
    
    def __init__(
        self,
        node_id: str,
        name: str = "Get Variable",
        variable_name: str = "",
        default_value: Optional[Any] = None,
        **kwargs
    ) -> None:
        """
        Initialize get variable node.
        
        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            variable_name: Name of the variable to get
            default_value: Default value if variable not found
        """
        config = kwargs.get("config", {"variable_name": variable_name, "default_value": default_value})
        if "variable_name" not in config:
            config["variable_name"] = variable_name
        if "default_value" not in config:
            config["default_value"] = default_value
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetVariableNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("variable_name", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("value", PortType.OUTPUT, DataType.ANY)
    
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
            # Get variable name from input or config
            variable_name = self.get_input_value("variable_name")
            if variable_name is None:
                variable_name = self.config.get("variable_name", "")
            
            if not variable_name:
                raise ValueError("Variable name is required")
            
            # Get value from context
            value = context.get_variable(variable_name)
            
            # Use default if not found
            if value is None:
                value = self.config.get("default_value")
            
            # Output the value
            self.set_output_value("value", value)
            
            self.status = NodeStatus.SUCCESS
            logger.info(f"Get variable '{variable_name}' = {value}")
            
            return {
                "success": True,
                "data": {
                    "variable_name": variable_name,
                    "value": value
                },
                "next_nodes": ["exec_out"]
            }
            
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to get variable: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }
    
    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        variable_name = self.config.get("variable_name", "")
        if not variable_name:
            return False, "Variable name is required"
        return True, ""


class IncrementVariableNode(BaseNode):
    """
    Increment variable node - increments a numeric variable.
    
    Retrieves a variable, increments it, and stores the result.
    """
    
    def __init__(
        self,
        node_id: str,
        name: str = "Increment Variable",
        variable_name: str = "",
        increment: float = 1.0,
        **kwargs
    ) -> None:
        """
        Initialize increment variable node.
        
        Args:
            node_id: Unique identifier for this node
            name: Display name for the node
            variable_name: Name of the variable to increment
            increment: Amount to increment by
        """
        config = kwargs.get("config", {"variable_name": variable_name, "increment": increment})
        if "variable_name" not in config:
            config["variable_name"] = variable_name
        if "increment" not in config:
            config["increment"] = increment
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "IncrementVariableNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("variable_name", PortType.INPUT, DataType.STRING)
        self.add_input_port("increment", PortType.INPUT, DataType.FLOAT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("value", PortType.OUTPUT, DataType.FLOAT)
    
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
            # Get variable name from input or config
            variable_name = self.get_input_value("variable_name")
            if variable_name is None:
                variable_name = self.config.get("variable_name", "")
            
            if not variable_name:
                raise ValueError("Variable name is required")
            
            # Get increment from input or config
            increment = self.get_input_value("increment")
            if increment is None:
                increment = self.config.get("increment", 1.0)
            
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
            logger.info(f"Incremented variable '{variable_name}': {current_value} + {increment} = {new_value}")
            
            return {
                "success": True,
                "data": {
                    "variable_name": variable_name,
                    "old_value": current_value,
                    "increment": increment,
                    "new_value": new_value
                },
                "next_nodes": ["exec_out"]
            }
            
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Failed to increment variable: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }
    
    def _validate_config(self) -> tuple[bool, str]:
        """Validate node configuration."""
        variable_name = self.config.get("variable_name", "")
        if not variable_name:
            return False, "Variable name is required"
        return True, ""

