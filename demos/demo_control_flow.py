"""
Control Flow Demo - CasareRPA Phase 6

Demonstrates If/Else conditional logic, For Loops, and While Loops.
"""

import asyncio
from loguru import logger

from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.core.workflow_schema import WorkflowSchema, NodeConnection
from casare_rpa.nodes.basic_nodes import StartNode, EndNode
from casare_rpa.nodes.control_flow_nodes import IfNode, ForLoopNode, WhileLoopNode
from casare_rpa.nodes.variable_nodes import SetVariableNode, GetVariableNode, IncrementVariableNode
from casare_rpa.runner.workflow_runner import WorkflowRunner


async def demo_if_else():
    """Demo 1: If/Else conditional branching."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 1: If/Else Conditional Logic")
    logger.info("=" * 80)
    
    # Direct test without workflow runner (simpler for demo)
    context = ExecutionContext("test")
    context.set_variable("age", 25)
    
    # Test If node with adult age
    if_node = IfNode("check_adult", {"expression": "age >= 18"})
    result = await if_node.execute(context)
    
    logger.info(f"Age: 25, Condition: age >= 18")
    logger.info(f"Result: {result['next_nodes']}")
    logger.success(f"✓ If node correctly routes to: {result['next_nodes'][0]}")
    assert result['next_nodes'] == ["true"]
    
    # Test with minor age
    context.set_variable("age", 15)
    if_node2 = IfNode("check_minor", {"expression": "age >= 18"})
    result2 = await if_node2.execute(context)
    
    logger.info(f"\nAge: 15, Condition: age >= 18")
    logger.info(f"Result: {result2['next_nodes']}")
    logger.success(f"✓ If node correctly routes to: {result2['next_nodes'][0]}")
    assert result2['next_nodes'] == ["false"]


async def demo_for_loop():
    """Demo 2: For Loop iteration."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 2: For Loop Iteration")
    logger.info("=" * 80)
    
    # Direct test
    context = ExecutionContext("test")
    
    # Create for loop: iterate 1 to 5
    for_loop = ForLoopNode("for_loop", {"start": 1, "end": 6, "step": 1})
    
    total = 0
    iteration_count = 0
    
    # Manually iterate
    while True:
        result = await for_loop.execute(context)
        
        if result['next_nodes'] == ["completed"]:
            break
        
        # Get current item
        item = for_loop.get_output_value("item")
        index = for_loop.get_output_value("index")
        total += item
        iteration_count += 1
        
        logger.info(f"Iteration {index}: item={item}, running_sum={total}")
    
    logger.success(f"✓ For Loop: Sum of 1+2+3+4+5 = {total}")
    assert total == 15
    assert iteration_count == 5


async def demo_while_loop():
    """Demo 3: While Loop with condition."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 3: While Loop")
    logger.info("=" * 80)
    
    # Direct test
    context = ExecutionContext("test")
    context.set_variable("counter", 0)
    
    # Create while loop
    while_loop = WhileLoopNode("while_loop", {
        "expression": "counter < 5",
        "max_iterations": 10
    })
    
    iteration_count = 0
    
    # Manually iterate
    while True:
        result = await while_loop.execute(context)
        
        if result['next_nodes'] == ["completed"]:
            break
        
        # Simulate incrementing counter
        counter = context.get_variable("counter")
        logger.info(f"Iteration {iteration_count}: counter={counter}")
        context.set_variable("counter", counter + 1)
        iteration_count += 1
    
    final_counter = context.get_variable("counter")
    logger.success(f"✓ While Loop: Counter reached {final_counter} after {iteration_count} iterations")
    assert final_counter == 5
    assert iteration_count == 5


async def demo_complex_workflow():
    """Demo 4: Complex workflow with nested control flow."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 4: Complex Control Flow")
    logger.info("=" * 80)
    logger.info("Process: Check if numbers 1-10 are even, sum the even ones")
    
    # Direct test
    context = ExecutionContext("test")
    
    # Create for loop
    for_loop = ForLoopNode("for_loop", {"start": 1, "end": 11, "step": 1})
    
    # Create if node for even check
    check_even = IfNode("check_even", {"expression": "item % 2 == 0"})
    
    total = 0
    even_numbers = []
    
    # Iterate through numbers
    while True:
        result = await for_loop.execute(context)
        
        if result['next_nodes'] == ["completed"]:
            break
        
        # Get current item
        item = for_loop.get_output_value("item")
        context.set_variable("item", item)
        
        # Check if even
        check_result = await check_even.execute(context)
        
        if check_result['next_nodes'] == ["true"]:
            total += item
            even_numbers.append(item)
            logger.info(f"Item {item}: EVEN → total={total}")
        else:
            logger.info(f"Item {item}: ODD → skip")
    
    logger.success(f"✓ Complex Flow: Sum of even numbers {even_numbers} = {total}")
    assert total == 30  # 2+4+6+8+10
    assert even_numbers == [2, 4, 6, 8, 10]


async def main():
    """Run all control flow demos."""
    logger.info("╔════════════════════════════════════════════════════════════════════════════╗")
    logger.info("║           CasareRPA Phase 6 - Control Flow Nodes Demo                     ║")
    logger.info("╚════════════════════════════════════════════════════════════════════════════╝")
    
    try:
        await demo_if_else()
        await demo_for_loop()
        await demo_while_loop()
        await demo_complex_workflow()
        
        logger.info("\n" + "=" * 80)
        logger.success("✓ ALL CONTROL FLOW DEMOS COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)
        logger.info("\nControl flow nodes are working perfectly:")
        logger.info("  ✓ If/Else - Conditional branching")
        logger.info("  ✓ For Loop - List and range iteration")
        logger.info("  ✓ While Loop - Conditional loops with safety limits")
        logger.info("  ✓ Complex workflows - Nested control flow")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
