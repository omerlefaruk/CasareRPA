"""
CasareRPA - Phase 2 Demo
Demonstrates the core architecture components.
"""

import asyncio
from pathlib import Path
from loguru import logger

from casare_rpa.core import (
    BaseNode,
    DataType,
    ExecutionContext,
    ExecutionMode,
    WorkflowSchema,
    WorkflowMetadata,
    NodeConnection,
    EventBus,
    EventType,
    EventLogger,
    get_event_bus,
)
from casare_rpa.utils import setup_logging


# ============================================================================
# DEMO NODE IMPLEMENTATIONS
# ============================================================================


class StartNode(BaseNode):
    """Demo start node - initiates workflow."""

    def _define_ports(self) -> None:
        self.category = "Control"
        self.add_output_port("message", DataType.STRING, "Start message")

    async def execute(self, context: ExecutionContext) -> dict:
        message = self.config.get("start_message", "Workflow Started!")
        self.set_output_value("message", message)
        logger.info(f"🚀 {message}")
        return {"message": message}


class ProcessTextNode(BaseNode):
    """Demo node - processes text."""

    def _define_ports(self) -> None:
        self.category = "Processing"
        self.add_input_port("input_text", DataType.STRING, "Input text", required=True)
        self.add_output_port("output_text", DataType.STRING, "Processed text")

    async def execute(self, context: ExecutionContext) -> dict:
        input_text = self.get_input_value("input_text", "")
        operation = self.config.get("operation", "uppercase")

        if operation == "uppercase":
            result = input_text.upper()
        elif operation == "lowercase":
            result = input_text.lower()
        elif operation == "reverse":
            result = input_text[::-1]
        else:
            result = input_text

        self.set_output_value("output_text", result)
        logger.info(f"📝 Processed: '{input_text}' → '{result}'")
        return {"output_text": result}


class SaveToVariableNode(BaseNode):
    """Demo node - saves value to context variable."""

    def _define_ports(self) -> None:
        self.category = "Data"
        self.add_input_port("value", DataType.STRING, "Value to save", required=True)

    async def execute(self, context: ExecutionContext) -> dict:
        value = self.get_input_value("value")
        var_name = self.config.get("variable_name", "result")
        
        context.set_variable(var_name, value)
        logger.info(f"💾 Saved variable: {var_name} = '{value}'")
        return {}


class EndNode(BaseNode):
    """Demo end node - completes workflow."""

    def _define_ports(self) -> None:
        self.category = "Control"
        self.add_input_port("final_message", DataType.STRING, "Final message")

    async def execute(self, context: ExecutionContext) -> dict:
        message = self.get_input_value("final_message", "Workflow Completed!")
        logger.success(f"✅ {message}")
        return {}


# ============================================================================
# DEMO FUNCTIONS
# ============================================================================


async def demo_basic_node() -> None:
    """Demonstrate basic node functionality."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 1: Basic Node Functionality")
    logger.info("=" * 80)

    # Create a node
    node = ProcessTextNode("process_1", {"operation": "uppercase"})
    logger.info(f"Created node: {node}")

    # Set input
    node.set_input_value("input_text", "hello world")

    # Validate
    is_valid, error = node.validate()
    logger.info(f"Validation: {'✅ PASS' if is_valid else '❌ FAIL'} {error or ''}")

    # Execute
    context = ExecutionContext("demo_workflow")
    result = await node.execute(context)
    logger.info(f"Result: {result}")

    # Serialize
    serialized = node.serialize()
    logger.info(f"Serialized: {serialized['node_type']}")


async def demo_workflow_schema() -> None:
    """Demonstrate workflow schema and connections."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 2: Workflow Schema")
    logger.info("=" * 80)

    # Create workflow
    metadata = WorkflowMetadata(
        name="Demo Workflow",
        description="Text processing workflow",
        author="Demo User",
        tags=["demo", "text-processing"]
    )
    workflow = WorkflowSchema(metadata)

    # Add nodes
    start = StartNode("start", {"start_message": "Processing text..."})
    process = ProcessTextNode("process", {"operation": "uppercase"})
    save = SaveToVariableNode("save", {"variable_name": "processed_text"})
    end = EndNode("end")

    workflow.add_node(start.serialize())
    workflow.add_node(process.serialize())
    workflow.add_node(save.serialize())
    workflow.add_node(end.serialize())

    # Add connections
    conn1 = NodeConnection("start", "message", "process", "input_text")
    conn2 = NodeConnection("process", "output_text", "save", "value")
    conn3 = NodeConnection("save", "message", "end", "final_message")  # Demo connection

    workflow.add_connection(conn1)
    workflow.add_connection(conn2)

    # Validate workflow
    is_valid, errors = workflow.validate()
    logger.info(f"Workflow validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
    if errors:
        for error in errors:
            logger.warning(f"  - {error}")

    # Display workflow info
    logger.info(f"Workflow: {workflow}")
    logger.info(f"Nodes: {len(workflow.nodes)}")
    logger.info(f"Connections: {len(workflow.connections)}")

    # Save workflow to file
    workflow_path = Path("workflows/demo_workflow.json")
    workflow.save_to_file(workflow_path)
    logger.success(f"Workflow saved to: {workflow_path}")

    # Load workflow back
    loaded = WorkflowSchema.load_from_file(workflow_path)
    logger.success(f"Workflow loaded: {loaded.metadata.name}")


async def demo_execution_context() -> None:
    """Demonstrate execution context."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 3: Execution Context")
    logger.info("=" * 80)

    # Create context
    context = ExecutionContext("demo_workflow", ExecutionMode.NORMAL)
    logger.info(f"Created context: {context}")

    # Set variables
    context.set_variable("user_name", "John Doe")
    context.set_variable("count", 42)
    context.set_variable("items", ["apple", "banana", "orange"])

    # Retrieve variables
    logger.info(f"Variable 'user_name': {context.get_variable('user_name')}")
    logger.info(f"Variable 'count': {context.get_variable('count')}")
    logger.info(f"Variable 'items': {context.get_variable('items')}")

    # Track execution
    context.set_current_node("node_1")
    context.set_current_node("node_2")
    context.set_current_node("node_3")

    # Add errors (demo)
    context.add_error("node_2", "Demo error for testing")

    # Mark completed
    context.mark_completed()

    # Get summary
    summary = context.get_execution_summary()
    logger.info("Execution Summary:")
    logger.info(f"  Workflow: {summary['workflow_name']}")
    logger.info(f"  Nodes executed: {summary['nodes_executed']}")
    logger.info(f"  Duration: {summary['duration_seconds']:.2f}s")
    logger.info(f"  Variables: {summary['variables_count']}")
    logger.info(f"  Errors: {len(summary['errors'])}")


async def demo_event_system() -> None:
    """Demonstrate event system."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 4: Event System")
    logger.info("=" * 80)

    # Get event bus
    bus = get_event_bus()

    # Subscribe event logger
    event_logger = EventLogger("INFO")
    event_logger.subscribe_all(bus)

    # Emit events
    logger.info("Emitting events...")
    bus.emit(EventType.WORKFLOW_STARTED, {"workflow": "demo"})
    bus.emit(EventType.NODE_STARTED, {"message": "Processing..."}, "node_1")
    bus.emit(EventType.NODE_COMPLETED, {"result": "success"}, "node_1")
    bus.emit(EventType.WORKFLOW_COMPLETED, {"status": "success"})

    # Get event history
    history = bus.get_history(limit=5)
    logger.info(f"Event history (last 5): {len(history)} events")
    for event in history:
        logger.info(f"  - {event.event_type.name} @ {event.timestamp.strftime('%H:%M:%S')}")


async def demo_complete_workflow() -> None:
    """Demonstrate a complete workflow execution."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 5: Complete Workflow Execution")
    logger.info("=" * 80)

    # Setup event system
    bus = get_event_bus()
    event_logger = EventLogger("INFO")
    event_logger.subscribe_all(bus)

    # Create context
    context = ExecutionContext("complete_demo", ExecutionMode.NORMAL)

    # Emit workflow start
    bus.emit(EventType.WORKFLOW_STARTED, {"workflow": "complete_demo"})

    # Node 1: Start
    node1 = StartNode("start", {"start_message": "Hello, CasareRPA!"})
    bus.emit(EventType.NODE_STARTED, {}, "start")
    result1 = await node1.execute(context)
    bus.emit(EventType.NODE_COMPLETED, result1, "start")

    # Node 2: Process
    node2 = ProcessTextNode("process", {"operation": "uppercase"})
    node2.set_input_value("input_text", result1["message"])
    bus.emit(EventType.NODE_STARTED, {}, "process")
    result2 = await node2.execute(context)
    bus.emit(EventType.NODE_COMPLETED, result2, "process")

    # Node 3: Save
    node3 = SaveToVariableNode("save", {"variable_name": "final_result"})
    node3.set_input_value("value", result2["output_text"])
    bus.emit(EventType.NODE_STARTED, {}, "save")
    await node3.execute(context)
    bus.emit(EventType.NODE_COMPLETED, {}, "save")

    # Node 4: End
    node4 = EndNode("end")
    node4.set_input_value("final_message", "Workflow completed successfully!")
    bus.emit(EventType.NODE_STARTED, {}, "end")
    await node4.execute(context)
    bus.emit(EventType.NODE_COMPLETED, {}, "end")

    # Complete workflow
    context.mark_completed()
    bus.emit(EventType.WORKFLOW_COMPLETED, {"status": "success"})

    # Display results
    logger.info("\n📊 Workflow Results:")
    logger.info(f"  Final variable value: {context.get_variable('final_result')}")
    logger.info(f"  Execution path: {' → '.join(context.execution_path)}")
    logger.info(f"  Duration: {context.get_execution_summary()['duration_seconds']:.3f}s")


async def main() -> None:
    """Run all demos."""
    setup_logging()

    logger.info("=" * 80)
    logger.info("🤖 CasareRPA - Phase 2 Core Architecture Demo")
    logger.info("=" * 80)

    try:
        await demo_basic_node()
        await demo_workflow_schema()
        await demo_execution_context()
        await demo_event_system()
        await demo_complete_workflow()

        logger.info("\n" + "=" * 80)
        logger.success("✅ All demos completed successfully!")
        logger.info("=" * 80)

    except Exception as e:
        logger.exception(f"Demo failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
