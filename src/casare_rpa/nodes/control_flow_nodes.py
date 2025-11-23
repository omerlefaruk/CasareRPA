"""
Control flow nodes for CasareRPA.

This module implements conditional and loop nodes for workflow control flow.
"""

from typing import Any, Optional
from loguru import logger

from ..core.base_node import BaseNode
from ..core.execution_context import ExecutionContext
from ..core.types import PortType, DataType, NodeStatus, ExecutionResult


class IfNode(BaseNode):
    """
    Conditional node that executes different paths based on condition.
    
    Evaluates a condition and routes execution to either 'true' or 'false' output.
    Supports boolean inputs or expression evaluation.
    """
    
    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize If node."""
        super().__init__(node_id, config)
        self.name = "If"
        self.node_type = "IfNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("condition", PortType.INPUT, DataType.ANY, required=False)
        self.add_output_port("true", PortType.EXEC_OUTPUT)
        self.add_output_port("false", PortType.EXEC_OUTPUT)
    
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute conditional logic.
        
        Args:
            context: Execution context
            
        Returns:
            Result with next node based on condition
        """
        self.status = NodeStatus.RUNNING
        
        try:
            # Get condition value
            condition = self.get_input_value("condition")
            
            # If no input, check config for expression
            if condition is None:
                expression = self.config.get("expression", "")
                if expression:
                    # Evaluate expression with context variables
                    try:
                        condition = eval(expression, {"__builtins__": {}}, context.variables)
                    except Exception as e:
                        logger.warning(f"Failed to evaluate expression '{expression}': {e}")
                        condition = False
                else:
                    condition = False
            
            # Convert to boolean
            result = bool(condition)
            
            # Determine next node
            next_port = "true" if result else "false"
            
            self.status = NodeStatus.SUCCESS
            logger.info(f"If condition evaluated to: {result} -> {next_port}")
            
            return {
                "success": True,
                "data": {"condition": result},
                "next_nodes": [next_port]
            }
            
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"If node execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


class ForLoopNode(BaseNode):
    """
    For loop node that iterates over a range or list.
    
    Supports iteration over:
    - Ranges: start, end, step
    - Lists: any iterable input
    
    Outputs current item and index on each iteration.
    """
    
    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize For Loop node."""
        super().__init__(node_id, config)
        self.name = "For Loop"
        self.node_type = "ForLoopNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("items", PortType.INPUT, DataType.ANY, required=False)
        self.add_output_port("loop_body", PortType.EXEC_OUTPUT)
        self.add_output_port("completed", PortType.EXEC_OUTPUT)
        self.add_output_port("item", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("index", PortType.OUTPUT, DataType.ANY)
    
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute for loop iteration.
        
        Args:
            context: Execution context
            
        Returns:
            Result with loop iteration data
        """
        self.status = NodeStatus.RUNNING
        
        try:
            # Get items to iterate
            items = self.get_input_value("items")
            
            # If no input, create range from config
            if items is None:
                start = self.config.get("start", 0)
                end = self.config.get("end", 10)
                step = self.config.get("step", 1)
                items = list(range(start, end, step))
            
            # Ensure items is iterable
            if not hasattr(items, "__iter__") or isinstance(items, str):
                items = [items]
            
            # Store loop state in context
            loop_state_key = f"{self.node_id}_loop_state"
            
            # Check if this is first iteration or continuation
            if loop_state_key not in context.variables:
                # Initialize loop state
                context.variables[loop_state_key] = {
                    "items": list(items),
                    "index": 0
                }
            
            loop_state = context.variables[loop_state_key]
            index = loop_state["index"]
            items_list = loop_state["items"]
            
            # Check if loop is complete
            if index >= len(items_list):
                # Loop finished
                del context.variables[loop_state_key]
                self.status = NodeStatus.SUCCESS
                logger.info(f"For loop completed after {index} iterations")
                
                return {
                    "success": True,
                    "data": {"iterations": index},
                    "next_nodes": ["completed"]
                }
            
            # Get current item
            current_item = items_list[index]
            
            # Set output values
            self.set_output_value("item", current_item)
            self.set_output_value("index", index)
            
            # Increment index for next iteration
            loop_state["index"] = index + 1
            
            self.status = NodeStatus.RUNNING
            logger.debug(f"For loop iteration {index}: {current_item}")
            
            return {
                "success": True,
                "data": {
                    "item": current_item,
                    "index": index,
                    "remaining": len(items_list) - index - 1
                },
                "next_nodes": ["loop_body"]
            }
            
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"For loop execution failed: {e}")
            # Clean up loop state
            loop_state_key = f"{self.node_id}_loop_state"
            if loop_state_key in context.variables:
                del context.variables[loop_state_key]
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


class WhileLoopNode(BaseNode):
    """
    While loop node that executes while condition is true.
    
    Evaluates condition on each iteration and continues until false.
    Includes max iterations safety limit to prevent infinite loops.
    """
    
    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize While Loop node."""
        super().__init__(node_id, config)
        self.name = "While Loop"
        self.node_type = "WhileLoopNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("condition", PortType.INPUT, DataType.ANY, required=False)
        self.add_output_port("loop_body", PortType.EXEC_OUTPUT)
        self.add_output_port("completed", PortType.EXEC_OUTPUT)
        self.add_output_port("iteration", PortType.OUTPUT, DataType.ANY)
    
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute while loop iteration.
        
        Args:
            context: Execution context
            
        Returns:
            Result with loop iteration data
        """
        self.status = NodeStatus.RUNNING
        
        try:
            # Store loop state in context
            loop_state_key = f"{self.node_id}_loop_state"
            max_iterations = self.config.get("max_iterations", 1000)
            
            # Initialize or get loop state
            if loop_state_key not in context.variables:
                context.variables[loop_state_key] = {"iteration": 0}
            
            loop_state = context.variables[loop_state_key]
            iteration = loop_state["iteration"]
            
            # Safety check for infinite loops
            if iteration >= max_iterations:
                del context.variables[loop_state_key]
                logger.warning(f"While loop hit max iterations limit: {max_iterations}")
                self.status = NodeStatus.SUCCESS
                return {
                    "success": True,
                    "data": {"iterations": iteration, "reason": "max_iterations"},
                    "next_nodes": ["completed"]
                }
            
            # Evaluate condition
            condition = self.get_input_value("condition")
            
            # If no input, check config for expression
            if condition is None:
                expression = self.config.get("expression", "")
                if expression:
                    try:
                        condition = eval(expression, {"__builtins__": {}}, context.variables)
                    except Exception as e:
                        logger.warning(f"Failed to evaluate expression '{expression}': {e}")
                        condition = False
                else:
                    # No condition means exit immediately
                    condition = False
            
            # Convert to boolean
            should_continue = bool(condition)
            
            if not should_continue:
                # Loop finished
                del context.variables[loop_state_key]
                self.status = NodeStatus.SUCCESS
                logger.info(f"While loop completed after {iteration} iterations")
                
                return {
                    "success": True,
                    "data": {"iterations": iteration},
                    "next_nodes": ["completed"]
                }
            
            # Continue loop
            self.set_output_value("iteration", iteration)
            loop_state["iteration"] = iteration + 1
            
            self.status = NodeStatus.RUNNING
            logger.debug(f"While loop iteration {iteration}")
            
            return {
                "success": True,
                "data": {"iteration": iteration},
                "next_nodes": ["loop_body"]
            }
            
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"While loop execution failed: {e}")
            # Clean up loop state
            loop_state_key = f"{self.node_id}_loop_state"
            if loop_state_key in context.variables:
                del context.variables[loop_state_key]
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }
