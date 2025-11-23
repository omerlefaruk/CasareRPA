"""
Comprehensive demonstration of CasareRPA debugging features.

This script showcases:
1. Basic breakpoint usage
2. Step-by-step execution
3. Execution history tracking
4. Variable inspection
5. Complex workflow debugging
"""

import asyncio
from casare_rpa.core.workflow_schema import WorkflowSchema, NodeConnection, WorkflowMetadata
from casare_rpa.runner.workflow_runner import WorkflowRunner
from casare_rpa.nodes.basic_nodes import StartNode, EndNode
from casare_rpa.nodes.variable_nodes import SetVariableNode, GetVariableNode
from casare_rpa.nodes.control_flow_nodes import IfNode, ForLoopNode
from loguru import logger


def create_runnable_workflow(metadata, nodes_dict, connections):
    """Helper to create executable workflow."""
    workflow = WorkflowSchema(metadata)
    workflow.nodes = nodes_dict
    workflow.connections = connections
    return workflow


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_history(history):
    """Print execution history in a formatted way."""
    print("\n📊 Execution History:")
    print("-" * 80)
    for i, entry in enumerate(history, 1):
        print(f"{i}. [{entry['timestamp']}] {entry['node_type']} ({entry['node_id']})")
        print(f"   Status: {entry['status']}, Time: {entry['execution_time']:.4f}s")
    print("-" * 80)


def print_variables(variables):
    """Print variables in a formatted way."""
    print("\n🔍 Variables:")
    print("-" * 80)
    if variables:
        for name, value in variables.items():
            print(f"  {name} = {value}")
    else:
        print("  (No variables set)")
    print("-" * 80)


def print_node_debug_info(node_id, debug_info):
    """Print node debug information."""
    print(f"\n🔧 Debug Info for Node '{node_id}':")
    print("-" * 80)
    print(f"  Node Type: {debug_info['node_type']}")
    print(f"  Status: {debug_info['status']}")
    print(f"  Breakpoint: {'✓' if debug_info['breakpoint_enabled'] else '✗'}")
    print(f"  Execution Count: {debug_info['execution_count']}")
    print(f"  Last Execution Time: {debug_info['last_execution_time']:.4f}s" 
          if debug_info['last_execution_time'] else "  Last Execution Time: N/A")
    print(f"  Input Values: {debug_info['input_values']}")
    print(f"  Output Values: {debug_info['output_values']}")
    print("-" * 80)


async def demo_1_basic_breakpoints():
    """Demo 1: Basic breakpoint usage."""
    print_section("Demo 1: Basic Breakpoint Usage")
    
    print("Creating a simple workflow with 3 nodes...")
    
    # Create workflow
    start = StartNode("start")
    set1 = SetVariableNode("set1", {"variable_name": "step", "default_value": "1"})
    set2 = SetVariableNode("set2", {"variable_name": "step", "default_value": "2"})
    set3 = SetVariableNode("set3", {"variable_name": "step", "default_value": "3"})
    end = EndNode("end")
    
    workflow = create_runnable_workflow(
        WorkflowMetadata(name="breakpoint_demo"),
        {"start": start, "set1": set1, "set2": set2, "set3": set3, "end": end},
        [
            NodeConnection("start", "exec_out", "set1", "exec_in"),
            NodeConnection("set1", "exec_out", "set2", "exec_in"),
            NodeConnection("set2", "exec_out", "set3", "exec_in"),
            NodeConnection("set3", "exec_out", "end", "exec_in")
        ]
    )
    
    runner = WorkflowRunner(workflow)
    runner.enable_debug_mode(True)
    
    print("✓ Setting breakpoint on 'set2' node")
    runner.set_breakpoint("set2", True)
    
    print("✓ Starting execution in background...")
    run_task = asyncio.create_task(runner.run())
    
    # Wait for breakpoint
    await asyncio.sleep(0.2)
    
    print("\n⏸️  Execution paused at breakpoint on 'set2'")
    print(f"   Breakpoints active: {runner.breakpoints}")
    
    # Check current state
    variables = runner.get_variables()
    print_variables(variables)
    
    print("\n▶️  Continuing execution...")
    runner.set_breakpoint("set2", False)  # Remove breakpoint
    runner.step()  # Resume
    
    await run_task
    
    print("\n✓ Workflow completed!")
    print_history(runner.get_execution_history())


async def demo_2_step_execution():
    """Demo 2: Step-by-step execution."""
    print_section("Demo 2: Step-by-Step Execution")
    
    print("Creating a workflow with 5 variable assignments...")
    
    # Create workflow
    nodes = {"start": StartNode("start")}
    connections = []
    
    for i in range(5):
        node_id = f"set{i}"
        nodes[node_id] = SetVariableNode(node_id, {
            "variable_name": f"var{i}",
            "default_value": f"value_{i}"
        })
        prev_id = "start" if i == 0 else f"set{i-1}"
        connections.append(NodeConnection(prev_id, "exec_out", node_id, "exec_in"))
    
    nodes["end"] = EndNode("end")
    connections.append(NodeConnection("set4", "exec_out", "end", "exec_in"))
    
    workflow = create_runnable_workflow(
        WorkflowMetadata(name="step_demo"),
        nodes,
        connections
    )
    
    runner = WorkflowRunner(workflow)
    runner.enable_debug_mode(True)
    runner.enable_step_mode(True)
    
    print("✓ Step mode enabled")
    print("✓ Starting execution...\n")
    
    # Start execution in background
    run_task = asyncio.create_task(runner.run())
    await asyncio.sleep(0.1)
    
    # Step through each node
    for i in range(7):  # start + 5 sets + end
        print(f"⏭️  Step {i+1}: Executing next node...")
        runner.step()
        await asyncio.sleep(0.15)
        
        # Show current state
        history = runner.get_execution_history()
        if history:
            last_executed = history[-1]
            print(f"   Just executed: {last_executed['node_type']} ({last_executed['node_id']})")
        
        variables = runner.get_variables()
        if variables:
            print(f"   Variables: {list(variables.keys())}")
    
    await run_task
    
    print("\n✓ Step-by-step execution completed!")
    print_history(runner.get_execution_history())


async def demo_3_execution_history():
    """Demo 3: Execution history tracking."""
    print_section("Demo 3: Execution History Tracking")
    
    print("Creating a workflow to demonstrate history tracking...")
    
    # Create workflow
    start = StartNode("start")
    set1 = SetVariableNode("set1", {"variable_name": "counter", "default_value": "0"})
    set2 = SetVariableNode("set2", {"variable_name": "name", "default_value": "Alice"})
    set3 = SetVariableNode("set3", {"variable_name": "status", "default_value": "active"})
    end = EndNode("end")
    
    workflow = create_runnable_workflow(
        WorkflowMetadata(name="history_demo"),
        {"start": start, "set1": set1, "set2": set2, "set3": set3, "end": end},
        [
            NodeConnection("start", "exec_out", "set1", "exec_in"),
            NodeConnection("set1", "exec_out", "set2", "exec_in"),
            NodeConnection("set2", "exec_out", "set3", "exec_in"),
            NodeConnection("set3", "exec_out", "end", "exec_in")
        ]
    )
    
    runner = WorkflowRunner(workflow)
    runner.enable_debug_mode(True)
    
    print("✓ Debug mode enabled (history tracking active)")
    print("✓ Running workflow...\n")
    
    await runner.run()
    
    print("✓ Workflow completed!\n")
    
    # Display detailed history
    history = runner.get_execution_history()
    print_history(history)
    
    # Show timing analysis
    print("\n⏱️  Timing Analysis:")
    print("-" * 80)
    total_time = sum(h["execution_time"] for h in history)
    print(f"  Total execution time: {total_time:.4f}s")
    print(f"  Average node time: {total_time/len(history):.4f}s")
    slowest = max(history, key=lambda h: h["execution_time"])
    print(f"  Slowest node: {slowest['node_id']} ({slowest['execution_time']:.4f}s)")
    print("-" * 80)


async def demo_4_variable_inspection():
    """Demo 4: Variable inspection during debugging."""
    print_section("Demo 4: Variable Inspection")
    
    print("Creating a workflow with multiple variables...")
    
    # Create workflow
    start = StartNode("start")
    set_name = SetVariableNode("set_name", {"variable_name": "name", "default_value": "Bob"})
    set_age = SetVariableNode("set_age", {"variable_name": "age", "default_value": "30"})
    set_city = SetVariableNode("set_city", {"variable_name": "city", "default_value": "NYC"})
    set_status = SetVariableNode("set_status", {"variable_name": "status", "default_value": "active"})
    end = EndNode("end")
    
    workflow = create_runnable_workflow(
        WorkflowMetadata(name="variables_demo"),
        {
            "start": start,
            "set_name": set_name,
            "set_age": set_age,
            "set_city": set_city,
            "set_status": set_status,
            "end": end
        },
        [
            NodeConnection("start", "exec_out", "set_name", "exec_in"),
            NodeConnection("set_name", "exec_out", "set_age", "exec_in"),
            NodeConnection("set_age", "exec_out", "set_city", "exec_in"),
            NodeConnection("set_city", "exec_out", "set_status", "exec_in"),
            NodeConnection("set_status", "exec_out", "end", "exec_in")
        ]
    )
    
    runner = WorkflowRunner(workflow)
    runner.enable_debug_mode(True)
    runner.enable_step_mode(True)
    
    print("✓ Starting execution in step mode...\n")
    
    run_task = asyncio.create_task(runner.run())
    await asyncio.sleep(0.1)
    
    # Step through and inspect variables after each step
    for i in range(6):
        runner.step()
        await asyncio.sleep(0.15)
        
        print(f"Step {i+1}:")
        variables = runner.get_variables()
        print_variables(variables)
    
    await run_task
    
    print("\n✓ All variables set!")


async def demo_5_node_debug_info():
    """Demo 5: Node debug information."""
    print_section("Demo 5: Node Debug Information")
    
    print("Creating a workflow and executing it multiple times...")
    
    # Create simple workflow
    start = StartNode("start")
    set_var = SetVariableNode("set_var", {"variable_name": "counter", "default_value": "0"})
    end = EndNode("end")
    
    workflow = create_runnable_workflow(
        WorkflowMetadata(name="debug_info_demo"),
        {"start": start, "set_var": set_var, "end": end},
        [
            NodeConnection("start", "exec_out", "set_var", "exec_in"),
            NodeConnection("set_var", "exec_out", "end", "exec_in")
        ]
    )
    
    runner = WorkflowRunner(workflow)
    
    # Run workflow 3 times
    for i in range(3):
        print(f"\n▶️  Execution #{i+1}")
        await runner.run()
        runner.reset()
    
    # Don't reset after last run to see metrics
    await runner.run()
    
    print("\n✓ Workflow executed 4 times total\n")
    
    # Show debug info for each node
    for node_id in ["start", "set_var", "end"]:
        debug_info = runner.get_node_debug_info(node_id)
        if debug_info:
            print_node_debug_info(node_id, debug_info)


async def demo_6_complex_workflow():
    """Demo 6: Debugging a complex workflow with control flow."""
    print_section("Demo 6: Complex Workflow with Control Flow")
    
    print("Creating a workflow with conditionals and loops...")
    
    # Create workflow
    start = StartNode("start")
    
    # Set initial value
    set_val = SetVariableNode("set_val", {"variable_name": "number", "default_value": "15"})
    
    # Check if number > 10
    if_node = IfNode("if_check", {"condition": "number > 10"})
    
    # Then branch: iterate 3 times
    for_loop = ForLoopNode("for_loop", {"items": "[1, 2, 3]"})
    loop_body = SetVariableNode("loop_body", {"variable_name": "iteration", "default_value": "0"})
    
    # Else branch: set error flag
    else_branch = SetVariableNode("else_branch", {"variable_name": "error", "default_value": "too_low"})
    
    end = EndNode("end")
    
    workflow = create_runnable_workflow(
        WorkflowMetadata(name="complex_demo"),
        {
            "start": start,
            "set_val": set_val,
            "if_check": if_node,
            "for_loop": for_loop,
            "loop_body": loop_body,
            "else_branch": else_branch,
            "end": end
        },
        [
            NodeConnection("start", "exec_out", "set_val", "exec_in"),
            NodeConnection("set_val", "exec_out", "if_check", "exec_in"),
            NodeConnection("if_check", "true_out", "for_loop", "exec_in"),
            NodeConnection("for_loop", "loop_body", "loop_body", "exec_in"),
            NodeConnection("loop_body", "exec_out", "for_loop", "loop_continue"),
            NodeConnection("for_loop", "completed", "end", "exec_in"),
            NodeConnection("if_check", "false_out", "else_branch", "exec_in"),
            NodeConnection("else_branch", "exec_out", "end", "exec_in")
        ]
    )
    
    runner = WorkflowRunner(workflow)
    runner.enable_debug_mode(True)
    
    print("✓ Debug mode enabled")
    print("✓ Setting breakpoint before loop...")
    runner.set_breakpoint("for_loop", True)
    
    print("✓ Running workflow...\n")
    
    run_task = asyncio.create_task(runner.run())
    
    # Wait for breakpoint
    await asyncio.sleep(0.2)
    
    print("⏸️  Paused at breakpoint (for_loop)")
    variables = runner.get_variables()
    print_variables(variables)
    
    print("\n▶️  Continuing execution...")
    runner.set_breakpoint("for_loop", False)
    runner.step()
    
    await run_task
    
    print("\n✓ Complex workflow completed!")
    print_history(runner.get_execution_history())
    
    # Final variables
    variables = runner.get_variables()
    print_variables(variables)
    
    # Show that loop executed 3 times
    loop_body_executions = [h for h in runner.get_execution_history() if h["node_id"] == "loop_body"]
    print(f"\n📊 Loop body executed {len(loop_body_executions)} times")


async def main():
    """Run all demonstrations."""
    print("\n" + "=" * 80)
    print(" " * 20 + "CasareRPA Debugging Features Demo")
    print("=" * 80)
    
    try:
        await demo_1_basic_breakpoints()
        await demo_2_step_execution()
        await demo_3_execution_history()
        await demo_4_variable_inspection()
        await demo_5_node_debug_info()
        await demo_6_complex_workflow()
        
        print("\n" + "=" * 80)
        print(" " * 25 + "All Demos Completed! ✓")
        print("=" * 80 + "\n")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
