"""
Test script to manually execute workflow and identify execution issues.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loguru import logger
from casare_rpa.infrastructure.execution.execution_context import ExecutionContext

logger.add(sys.stderr, level="DEBUG")


def test_workflow_execution():
    """Test basic workflow execution with MessageBox."""
    logger.info("Starting workflow execution test")

    # Create execution context
    context = ExecutionContext()

    # Import nodes
    from casare_rpa.nodes.basic_nodes import StartNode
    from casare_rpa.nodes.data_nodes import AssignNode
    from casare_rpa.nodes.system_nodes import MessageBoxNode

    logger.info("All nodes imported successfully")

    try:
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

    except Exception as e:
        logger.exception(f"Execution test failed: {e}")


if __name__ == "__main__":
    test_workflow_execution()
