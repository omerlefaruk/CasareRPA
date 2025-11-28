"""
Test script to manually execute workflow and identify execution issues.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loguru import logger
from casare_rpa.infrastructure.execution.execution_context import ExecutionContext
from casare_rpa.nodes.registry import NodeRegistry

logger.add(sys.stderr, level="DEBUG")


def test_workflow_execution():
    """Test basic workflow execution with MessageBox."""
    logger.info("Starting workflow execution test")

    # Initialize node registry
    registry = NodeRegistry()
    logger.info(f"Registry initialized with {len(registry._node_classes)} node types")

    # Create execution context
    context = ExecutionContext()

    # Create simple workflow programmatically
    from casare_rpa.nodes.flow.start_node import StartNode
    from casare_rpa.nodes.data.assign_node import AssignNode

    try:
        # Try to import MessageBoxNode
        from casare_rpa.nodes.ui.message_box_node import MessageBoxNode

        logger.info("MessageBoxNode imported successfully")

        # Create nodes
        start = StartNode(node_id="start_1")
        assign = AssignNode(node_id="assign_1")
        msgbox = MessageBoxNode(node_id="msgbox_1")

        # Configure assign node
        assign.set_property("variable_name", "test_message")
        assign.set_property("value", "Hello from test script!")
        assign.set_property("value_type", "String")

        # Configure msgbox node
        msgbox.set_property("title", "Test")
        msgbox.set_property("message", "{{test_message}}")
        msgbox.set_property("icon", "Information")
        msgbox.set_property("buttons", "OK")

        logger.info("Nodes created and configured")

        # Execute nodes in sequence
        logger.info("Executing StartNode...")
        start_result = start.execute(context)
        logger.info(f"StartNode result: {start_result}")

        logger.info("Executing AssignNode...")
        assign_result = assign.execute(context)
        logger.info(f"AssignNode result: {assign_result}")
        logger.info(f"Context variables: {context.variables}")

        logger.info("Executing MessageBoxNode...")
        msgbox_result = msgbox.execute(context)
        logger.info(f"MessageBoxNode result: {msgbox_result}")

        logger.success("Workflow execution test completed successfully!")

    except ImportError as e:
        logger.error(f"Failed to import MessageBoxNode: {e}")
        logger.info("Available node types:")
        for node_type in registry._node_classes.keys():
            logger.info(f"  - {node_type}")
    except Exception as e:
        logger.exception(f"Execution test failed: {e}")


if __name__ == "__main__":
    test_workflow_execution()
