"""
CasareRPA - Workflow Runner
Executes workflows by running nodes in the correct order based on connections.
"""

import asyncio
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from loguru import logger

from ..core.base_node import BaseNode
from ..core.workflow_schema import WorkflowSchema, NodeConnection
from ..core.execution_context import ExecutionContext
from ..core.types import NodeId, NodeStatus, EventType
from ..core.events import EventBus, Event


class ExecutionState:
    """Tracks the state of workflow execution."""
    
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ERROR = "error"


class WorkflowRunner:
    """
    Executes workflows asynchronously.
    
    Features:
    - Sequential node execution following connections
    - Async support for Playwright operations
    - Real-time progress tracking
    - Pause/Resume/Stop controls
    - Error handling and recovery
    """
    
    def __init__(
        self,
        workflow: WorkflowSchema,
        event_bus: Optional[EventBus] = None
    ) -> None:
        """
        Initialize workflow runner.
        
        Args:
            workflow: The workflow schema to execute
            event_bus: Optional event bus for progress updates
        """
        self.workflow = workflow
        
        # Import get_event_bus to get the global instance
        from ..core.events import get_event_bus
        self.event_bus = event_bus or get_event_bus()
        
        # Execution state
        self.state = ExecutionState.IDLE
        self.context: Optional[ExecutionContext] = None
        self.current_node_id: Optional[NodeId] = None
        
        # Progress tracking
        self.executed_nodes: Set[NodeId] = set()
        self.total_nodes = len(workflow.nodes)
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # Control flags
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Not paused initially
        self._stop_requested = False
        
        logger.info(f"WorkflowRunner initialized for workflow: {workflow.metadata.name}")
    
    @property
    def progress(self) -> float:
        """Get execution progress as percentage (0-100)."""
        if self.total_nodes == 0:
            return 0.0
        return (len(self.executed_nodes) / self.total_nodes) * 100
    
    @property
    def is_running(self) -> bool:
        """Check if workflow is currently running."""
        return self.state == ExecutionState.RUNNING
    
    @property
    def is_paused(self) -> bool:
        """Check if workflow is paused."""
        return self.state == ExecutionState.PAUSED
    
    def _emit_event(self, event_type: EventType, data: Dict[str, Any]) -> None:
        """Emit an event to the event bus."""
        if self.event_bus:
            event = Event(
                event_type=event_type,
                data=data,
                node_id=self.current_node_id
            )
            self.event_bus.publish(event)
    
    def _find_start_node(self) -> Optional[BaseNode]:
        """Find the StartNode in the workflow."""
        for node in self.workflow.nodes.values():
            if node.__class__.__name__ == "StartNode":
                return node
        return None
    
    def _get_next_nodes(self, current_node_id: NodeId) -> List[BaseNode]:
        """
        Get the next nodes to execute based on connections.
        
        Args:
            current_node_id: ID of the current node
            
        Returns:
            List of nodes connected to the current node's output
        """
        next_nodes = []
        
        for connection in self.workflow.connections:
            if connection.source_node == current_node_id:
                # Found a connection from current node
                target_node_id = connection.target_node
                if target_node_id in self.workflow.nodes:
                    next_nodes.append(self.workflow.nodes[target_node_id])
        
        return next_nodes
    
    def _transfer_data(self, connection: NodeConnection) -> None:
        """
        Transfer data from source port to target port.
        
        Args:
            connection: The connection defining source and target
        """
        source_node = self.workflow.nodes.get(connection.source_node)
        target_node = self.workflow.nodes.get(connection.target_node)
        
        if not source_node or not target_node:
            return
        
        # Get value from source output port
        value = source_node.get_output_value(connection.source_port)
        
        # Set value to target input port
        if value is not None:
            target_node.set_input_value(connection.target_port, value)
            logger.debug(
                f"Data transferred: {connection.source_node}.{connection.source_port} "
                f"-> {connection.target_node}.{connection.target_port} = {value}"
            )
    
    async def _execute_node(self, node: BaseNode) -> bool:
        """
        Execute a single node.
        
        Args:
            node: The node to execute
            
        Returns:
            True if execution succeeded, False otherwise
        """
        self.current_node_id = node.node_id
        node.status = NodeStatus.RUNNING
        
        self._emit_event(EventType.NODE_STARTED, {
            "node_id": node.node_id,
            "node_type": node.__class__.__name__
        })
        
        try:
            # Validate node before execution
            if not node.validate():
                logger.error(f"Node validation failed: {node.node_id}")
                node.status = NodeStatus.ERROR
                self._emit_event(EventType.NODE_ERROR, {
                    "node_id": node.node_id,
                    "error": "Validation failed"
                })
                return False
            
            # Execute the node
            result = await node.execute(self.context)
            
            if result and result.get("success", False):
                node.status = NodeStatus.SUCCESS
                self.executed_nodes.add(node.node_id)
                
                self._emit_event(EventType.NODE_COMPLETED, {
                    "node_id": node.node_id,
                    "message": result.get("data", {}).get("message", "Completed"),
                    "progress": self.progress
                })
                
                logger.info(f"Node executed successfully: {node.node_id}")
                return True
            else:
                node.status = NodeStatus.ERROR
                error_msg = result.get("error", "Unknown error") if result else "No result"
                self._emit_event(EventType.NODE_ERROR, {
                    "node_id": node.node_id,
                    "error": error_msg
                })
                logger.error(f"Node execution failed: {node.node_id} - {error_msg}")
                return False
                
        except Exception as e:
            node.status = NodeStatus.ERROR
            error_msg = str(e)
            
            self._emit_event(EventType.NODE_ERROR, {
                "node_id": node.node_id,
                "error": error_msg
            })
            
            logger.exception(f"Exception during node execution: {node.node_id}")
            return False
    
    async def _execute_workflow(self) -> None:
        """Execute the workflow from start to finish."""
        # Find the start node
        start_node = self._find_start_node()
        if not start_node:
            raise ValueError("No StartNode found in workflow")
        
        # Execute nodes in order, following connections
        nodes_to_execute = [start_node]
        
        while nodes_to_execute and not self._stop_requested:
            # Wait if paused
            await self._pause_event.wait()
            
            current_node = nodes_to_execute.pop(0)
            
            # Skip if already executed
            if current_node.node_id in self.executed_nodes:
                continue
            
            # Transfer data from connected input ports
            for connection in self.workflow.connections:
                if connection.target_node == current_node.node_id:
                    self._transfer_data(connection)
            
            # Execute the node
            success = await self._execute_node(current_node)
            
            if not success:
                # Stop on error (can be made configurable)
                logger.warning(f"Stopping workflow due to node error: {current_node.node_id}")
                break
            
            # Get next nodes to execute
            next_nodes = self._get_next_nodes(current_node.node_id)
            nodes_to_execute.extend(next_nodes)
    
    async def run(self) -> bool:
        """
        Run the workflow asynchronously.
        
        Returns:
            True if workflow completed successfully, False otherwise
        """
        if self.state == ExecutionState.RUNNING:
            logger.warning("Workflow is already running")
            return False
        
        self.state = ExecutionState.RUNNING
        self.start_time = datetime.now()
        self._stop_requested = False
        self.executed_nodes.clear()
        
        # Create execution context
        self.context = ExecutionContext(
            workflow_name=self.workflow.metadata.name
        )
        
        self._emit_event(EventType.WORKFLOW_STARTED, {
            "workflow_name": self.workflow.metadata.name,
            "total_nodes": self.total_nodes
        })
        
        logger.info(f"Starting workflow execution: {self.workflow.metadata.name}")
        
        try:
            await self._execute_workflow()
            
            # Check if completed successfully
            if self._stop_requested:
                self.state = ExecutionState.STOPPED
                self._emit_event(EventType.WORKFLOW_STOPPED, {
                    "executed_nodes": len(self.executed_nodes),
                    "total_nodes": self.total_nodes
                })
                logger.info("Workflow execution stopped by user")
                return False
            else:
                self.state = ExecutionState.COMPLETED
                self.end_time = datetime.now()
                duration = (self.end_time - self.start_time).total_seconds()
                
                self._emit_event(EventType.WORKFLOW_COMPLETED, {
                    "executed_nodes": len(self.executed_nodes),
                    "total_nodes": self.total_nodes,
                    "duration": duration
                })
                
                logger.info(
                    f"Workflow completed successfully in {duration:.2f}s "
                    f"({len(self.executed_nodes)}/{self.total_nodes} nodes)"
                )
                return True
                
        except Exception as e:
            self.state = ExecutionState.ERROR
            self.end_time = datetime.now()
            
            self._emit_event(EventType.WORKFLOW_ERROR, {
                "error": str(e),
                "executed_nodes": len(self.executed_nodes)
            })
            
            logger.exception("Workflow execution failed with exception")
            return False
        
        finally:
            # Cleanup
            self.current_node_id = None
    
    def pause(self) -> None:
        """Pause workflow execution."""
        if self.state == ExecutionState.RUNNING:
            self.state = ExecutionState.PAUSED
            self._pause_event.clear()
            
            self._emit_event(EventType.WORKFLOW_PAUSED, {
                "executed_nodes": len(self.executed_nodes),
                "total_nodes": self.total_nodes,
                "progress": self.progress
            })
            
            logger.info("Workflow execution paused")
    
    def resume(self) -> None:
        """Resume paused workflow execution."""
        if self.state == ExecutionState.PAUSED:
            self.state = ExecutionState.RUNNING
            self._pause_event.set()
            
            self._emit_event(EventType.WORKFLOW_RESUMED, {
                "executed_nodes": len(self.executed_nodes),
                "total_nodes": self.total_nodes
            })
            
            logger.info("Workflow execution resumed")
    
    def stop(self) -> None:
        """Stop workflow execution."""
        if self.state in (ExecutionState.RUNNING, ExecutionState.PAUSED):
            self._stop_requested = True
            self._pause_event.set()  # Unblock if paused
            
            logger.info("Workflow stop requested")
    
    def reset(self) -> None:
        """Reset the runner to initial state."""
        self.state = ExecutionState.IDLE
        self.context = None
        self.current_node_id = None
        self.executed_nodes.clear()
        self.start_time = None
        self.end_time = None
        self._stop_requested = False
        self._pause_event.set()
        
        # Reset all node statuses
        for node in self.workflow.nodes.values():
            node.reset()
        
        logger.info("WorkflowRunner reset to initial state")
