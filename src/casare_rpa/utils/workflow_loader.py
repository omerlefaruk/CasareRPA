"""
Workflow Loader Utility
Deserializes workflow JSON into executable WorkflowSchema with node instances.
"""
from typing import Dict
from loguru import logger

from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata, NodeConnection
from casare_rpa.core.base_node import BaseNode

# Import all node classes
from casare_rpa.nodes.basic_nodes import StartNode, EndNode
from casare_rpa.nodes.variable_nodes import SetVariableNode, GetVariableNode, IncrementVariableNode
from casare_rpa.nodes.control_flow_nodes import IfNode, ForLoopNode, WhileLoopNode
from casare_rpa.nodes.error_handling_nodes import TryNode, RetryNode
from casare_rpa.nodes.wait_nodes import WaitNode, WaitForElementNode, WaitForNavigationNode
from casare_rpa.nodes.browser_nodes import LaunchBrowserNode, CloseBrowserNode
from casare_rpa.nodes.navigation_nodes import GoToURLNode, GoBackNode, GoForwardNode, RefreshPageNode
from casare_rpa.nodes.interaction_nodes import ClickElementNode, TypeTextNode, SelectDropdownNode
from casare_rpa.nodes.data_nodes import ExtractTextNode, GetAttributeNode, ScreenshotNode
from casare_rpa.nodes.desktop_nodes import LaunchApplicationNode, CloseApplicationNode, ActivateWindowNode, GetWindowListNode

# Map node types to classes
NODE_TYPE_MAP = {
    "StartNode": StartNode,
    "EndNode": EndNode,
    "SetVariableNode": SetVariableNode,
    "GetVariableNode": GetVariableNode,
    "IncrementVariableNode": IncrementVariableNode,
    "IfNode": IfNode,
    "ForLoopNode": ForLoopNode,
    "WhileLoopNode": WhileLoopNode,
    "TryNode": TryNode,
    "RetryNode": RetryNode,
    "WaitNode": WaitNode,
    "WaitForElementNode": WaitForElementNode,
    "WaitForNavigationNode": WaitForNavigationNode,
    "LaunchBrowserNode": LaunchBrowserNode,
    "CloseBrowserNode": CloseBrowserNode,
    "GoToURLNode": GoToURLNode,
    "GoBackNode": GoBackNode,
    "GoForwardNode": GoForwardNode,
    "RefreshPageNode": RefreshPageNode,
    "ClickElementNode": ClickElementNode,
    "TypeTextNode": TypeTextNode,
    "SelectDropdownNode": SelectDropdownNode,
    "ExtractTextNode": ExtractTextNode,
    "GetAttributeNode": GetAttributeNode,
    "ScreenshotNode": ScreenshotNode,
    "LaunchApplicationNode": LaunchApplicationNode,
    "CloseApplicationNode": CloseApplicationNode,
    "ActivateWindowNode": ActivateWindowNode,
    "GetWindowListNode": GetWindowListNode,
}


def load_workflow_from_dict(workflow_data: Dict) -> WorkflowSchema:
    """
    Load a workflow from serialized dictionary data.
    
    Args:
        workflow_data: Serialized workflow data
        
    Returns:
        WorkflowSchema with actual node instances
    """
    # Create metadata
    metadata = WorkflowMetadata.from_dict(workflow_data.get("metadata", {}))
    workflow = WorkflowSchema(metadata)
    
    # Deserialize nodes into instances
    nodes_dict: Dict[str, BaseNode] = {}
    
    for node_id, node_data in workflow_data.get("nodes", {}).items():
        node_type = node_data.get("node_type")
        config = node_data.get("config", {})
        
        if node_type in NODE_TYPE_MAP:
            node_class = NODE_TYPE_MAP[node_type]
            # Pass config as keyword argument
            node_instance = node_class(node_id, config=config)
            nodes_dict[node_id] = node_instance
            logger.debug(f"Loaded node {node_id}: {node_type} with config: {config}")
        else:
            logger.warning(f"Unknown node type: {node_type}")
    
    
    # Check if workflow already has a StartNode (from Canvas)
    has_start_node = any(node.node_type == "StartNode" for node in nodes_dict.values())
    
    # Auto-create hidden Start node ONLY if workflow doesn't have one (like Canvas does)
    if not has_start_node:
        start_node = StartNode("__auto_start__")
        nodes_dict["__auto_start__"] = start_node
        logger.info("Added auto-start node (no StartNode found in workflow)")
    else:
        logger.info("Workflow already has a StartNode, skipping auto-start creation")
    
    # Set nodes as instances (WorkflowRunner needs this)
    workflow.nodes = nodes_dict
    
    # Load connections
    for conn_data in workflow_data.get("connections", []):
        workflow.connections.append(NodeConnection.from_dict(conn_data))
    
    # Find entry points (nodes without exec_in connections) and auto-connect Start node
    # Only do this if we created __auto_start__
    if not has_start_node:
        connected_exec_ins = set()
        for conn in workflow.connections:
            if conn.target_port == "exec_in":
                connected_exec_ins.add(conn.target_node)
        
        # Auto-connect Start to entry points
        for node_id, node in nodes_dict.items():
            if node_id == "__auto_start__":
                continue
            # Check if node has exec_in port and it's not connected
            if "exec_in" in node.input_ports and node_id not in connected_exec_ins:
                connection = NodeConnection(
                    source_node="__auto_start__",
                    source_port="exec_out",
                    target_node=node_id,
                    target_port="exec_in"
                )
                workflow.connections.append(connection)
                logger.info(f"Auto-connected Start → {node_id}")
    
    # Load variables and settings
    workflow.variables = workflow_data.get("variables", {})
    workflow.settings = workflow_data.get("settings", workflow.settings)
    
    logger.info(f"Loaded workflow '{metadata.name}' with {len(nodes_dict)} nodes and {len(workflow.connections)} connections")
    return workflow
