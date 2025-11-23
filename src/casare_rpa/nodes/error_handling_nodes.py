"""
Error handling nodes for CasareRPA.

This module implements error handling capabilities including try/catch,
retry logic, and error throwing for robust workflow execution.
"""

from typing import Any, Optional
from loguru import logger
import asyncio

from ..core.base_node import BaseNode
from ..core.execution_context import ExecutionContext
from ..core.types import PortType, DataType, NodeStatus, ExecutionResult


class TryNode(BaseNode):
    """
    Try block node for error handling.
    
    Wraps a section of workflow to catch errors. If the try block succeeds,
    execution continues to 'success' output. If an error occurs, routes to
    'catch' output with error details.
    """
    
    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize Try node."""
        super().__init__(node_id, config)
        self.name = "Try"
        self.node_type = "TryNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("try_body", PortType.EXEC_OUTPUT)
        self.add_output_port("success", PortType.EXEC_OUTPUT)
        self.add_output_port("catch", PortType.EXEC_OUTPUT)
        self.add_output_port("error_message", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("error_type", PortType.OUTPUT, DataType.STRING)
    
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute try block.
        
        This node marks the beginning of a try block. The actual error catching
        happens in the WorkflowRunner which monitors execution of the try_body.
        
        Args:
            context: Execution context
            
        Returns:
            Result routing to try_body for initial execution
        """
        self.status = NodeStatus.RUNNING
        
        try:
            # Store try block state
            try_state_key = f"{self.node_id}_state"
            
            if try_state_key not in context.variables:
                # First execution - enter try block
                context.variables[try_state_key] = {
                    "in_try_block": True,
                    "error_occurred": False
                }
                logger.info(f"Entering try block: {self.node_id}")
                
                self.status = NodeStatus.SUCCESS
                return {
                    "success": True,
                    "next_nodes": ["try_body"]
                }
            else:
                # Returning from try block
                try_state = context.variables[try_state_key]
                del context.variables[try_state_key]
                
                if try_state.get("error_occurred"):
                    # Error occurred - route to catch
                    error_msg = try_state.get("error_message", "Unknown error")
                    error_type = try_state.get("error_type", "Exception")
                    
                    self.set_output_value("error_message", error_msg)
                    self.set_output_value("error_type", error_type)
                    
                    logger.warning(f"Error caught in try block: {error_type}: {error_msg}")
                    
                    self.status = NodeStatus.SUCCESS
                    return {
                        "success": True,
                        "data": {
                            "error_message": error_msg,
                            "error_type": error_type
                        },
                        "next_nodes": ["catch"]
                    }
                else:
                    # No error - route to success
                    logger.info(f"Try block completed successfully: {self.node_id}")
                    
                    self.status = NodeStatus.SUCCESS
                    return {
                        "success": True,
                        "next_nodes": ["success"]
                    }
                    
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Try node execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


class RetryNode(BaseNode):
    """
    Retry node for automatic retry with backoff.
    
    Retries a failed operation multiple times with configurable delay and
    exponential backoff. Useful for handling transient failures.
    """
    
    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize Retry node."""
        super().__init__(node_id, config)
        self.name = "Retry"
        self.node_type = "RetryNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("retry_body", PortType.EXEC_OUTPUT)
        self.add_output_port("success", PortType.EXEC_OUTPUT)
        self.add_output_port("failed", PortType.EXEC_OUTPUT)
        self.add_output_port("attempt", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("last_error", PortType.OUTPUT, DataType.STRING)
    
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute retry logic.
        
        Args:
            context: Execution context
            
        Returns:
            Result with retry routing
        """
        self.status = NodeStatus.RUNNING
        
        try:
            max_attempts = self.config.get("max_attempts", 3)
            initial_delay = self.config.get("initial_delay", 1.0)  # seconds
            backoff_multiplier = self.config.get("backoff_multiplier", 2.0)
            
            retry_state_key = f"{self.node_id}_retry_state"
            
            if retry_state_key not in context.variables:
                # First attempt
                context.variables[retry_state_key] = {
                    "attempt": 0,
                    "max_attempts": max_attempts,
                    "initial_delay": initial_delay,
                    "backoff_multiplier": backoff_multiplier,
                    "last_error": None
                }
            
            retry_state = context.variables[retry_state_key]
            retry_state["attempt"] += 1
            current_attempt = retry_state["attempt"]
            
            self.set_output_value("attempt", current_attempt)
            
            if current_attempt <= max_attempts:
                # Attempt execution
                if current_attempt > 1:
                    # Apply delay with exponential backoff (except for first attempt)
                    delay = initial_delay * (backoff_multiplier ** (current_attempt - 2))
                    logger.info(f"Retry attempt {current_attempt}/{max_attempts} after {delay:.2f}s delay")
                    await asyncio.sleep(delay)
                else:
                    logger.info(f"Retry attempt {current_attempt}/{max_attempts} (initial)")
                
                self.status = NodeStatus.RUNNING
                return {
                    "success": True,
                    "data": {"attempt": current_attempt},
                    "next_nodes": ["retry_body"]
                }
            else:
                # Max attempts reached - fail
                last_error = retry_state.get("last_error", "Max retry attempts exceeded")
                self.set_output_value("last_error", last_error)
                
                logger.error(f"Retry failed after {max_attempts} attempts: {last_error}")
                
                # Clean up state
                del context.variables[retry_state_key]
                
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "data": {
                        "attempts": max_attempts,
                        "last_error": last_error
                    },
                    "next_nodes": ["failed"]
                }
                
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Retry node execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


class RetrySuccessNode(BaseNode):
    """
    Marks successful completion of retry body.
    
    This node signals that the retry operation succeeded and should exit
    the retry loop.
    """
    
    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize RetrySuccess node."""
        super().__init__(node_id, config)
        self.name = "Retry Success"
        self.node_type = "RetrySuccessNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
    
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Signal retry success.
        
        Args:
            context: Execution context
            
        Returns:
            Result with success signal
        """
        self.status = NodeStatus.RUNNING
        
        try:
            logger.info("Retry operation succeeded")
            
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "control_flow": "retry_success",
                "next_nodes": ["exec_out"]
            }
            
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"RetrySuccess execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


class RetryFailNode(BaseNode):
    """
    Marks failed attempt in retry body.
    
    This node signals that the retry operation failed and should be retried.
    """
    
    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize RetryFail node."""
        super().__init__(node_id, config)
        self.name = "Retry Fail"
        self.node_type = "RetryFailNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("error_message", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
    
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Signal retry failure.
        
        Args:
            context: Execution context
            
        Returns:
            Result with failure signal
        """
        self.status = NodeStatus.RUNNING
        
        try:
            error_message = self.get_input_value("error_message") or "Operation failed"
            
            logger.warning(f"Retry attempt failed: {error_message}")
            
            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "control_flow": "retry_fail",
                "data": {"error_message": error_message},
                "next_nodes": ["exec_out"]
            }
            
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"RetryFail execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }


class ThrowErrorNode(BaseNode):
    """
    Throws a custom error to trigger error handling.
    
    Intentionally raises an error with a custom message to trigger
    try/catch blocks or other error handling mechanisms.
    """
    
    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize ThrowError node."""
        super().__init__(node_id, config)
        self.name = "Throw Error"
        self.node_type = "ThrowErrorNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("error_message", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
    
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Throw error.
        
        Args:
            context: Execution context
            
        Returns:
            Result with error
        """
        self.status = NodeStatus.RUNNING
        
        try:
            # Get error message
            error_message = self.get_input_value("error_message")
            if error_message is None:
                error_message = self.config.get("error_message", "Custom error")
            
            logger.error(f"Throwing error: {error_message}")
            
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": error_message,
                "error_type": "CustomError",
                "next_nodes": []
            }
            
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"ThrowError node failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "next_nodes": []
            }
