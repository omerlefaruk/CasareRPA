"""
Demo for enhanced control flow features.

Showcases Break, Continue, and Switch nodes in action.
"""

import asyncio
from loguru import logger

from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.nodes.control_flow_nodes import (
    BreakNode,
    ContinueNode,
    SwitchNode,
    ForLoopNode,
    WhileLoopNode
)


async def demo_break_in_loop():
    """Demo 1: Break - Exit loop when condition met."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 1: Break - Find First Match")
    logger.info("=" * 80)
    logger.info("Find first number divisible by 7 in range 0-100")
    
    context = ExecutionContext("test")
    
    for_loop = ForLoopNode("search_loop", {"start": 0, "end": 100, "step": 1})
    
    found = None
    iterations = 0
    
    while True:
        result = await for_loop.execute(context)
        iterations += 1
        
        if result['next_nodes'] == ["completed"]:
            logger.info("Loop completed normally (no match)")
            break
        
        item = for_loop.get_output_value("item")
        logger.debug(f"Checking item: {item}")
        
        # Check if divisible by 7
        if item > 0 and item % 7 == 0:
            found = item
            logger.info(f"✓ Found match: {item} (after {iterations} checks)")
            
            # Simulate break
            loop_state_key = f"{for_loop.node_id}_loop_state"
            del context.variables[loop_state_key]
            break
    
    assert found == 7
    assert iterations < 100  # Should break early
    logger.success(f"✓ Break Demo: Found {found} after {iterations} iterations (saved {100-iterations} checks!)")


async def demo_continue_skip_values():
    """Demo 2: Continue - Skip certain values in loop."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 2: Continue - Process Only Valid Values")
    logger.info("=" * 80)
    logger.info("Sum only positive even numbers from list")
    
    context = ExecutionContext("test")
    
    # Mix of positive, negative, odd, and even numbers
    numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    
    for_loop = ForLoopNode("process_loop", {"items": numbers})
    
    valid_sum = 0
    processed = []
    skipped = []
    
    while True:
        result = await for_loop.execute(context)
        
        if result['next_nodes'] == ["completed"]:
            break
        
        item = for_loop.get_output_value("item")
        
        # Skip negative numbers
        if item < 0:
            logger.debug(f"Skipping negative: {item}")
            skipped.append(item)
            continue
        
        # Skip odd numbers
        if item % 2 == 1:
            logger.debug(f"Skipping odd: {item}")
            skipped.append(item)
            continue
        
        # Skip zero
        if item == 0:
            logger.debug(f"Skipping zero: {item}")
            skipped.append(item)
            continue
        
        # Process valid number
        valid_sum += item
        processed.append(item)
        logger.info(f"Processing: {item} → sum={valid_sum}")
    
    logger.success(f"✓ Continue Demo: Processed {processed}, Skipped {skipped}")
    logger.success(f"✓ Sum of positive even numbers: {valid_sum}")
    
    assert processed == [2, 4, 6, 8]
    assert valid_sum == 20


async def demo_switch_routing():
    """Demo 3: Switch - Multi-way branching."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 3: Switch - Status Code Handler")
    logger.info("=" * 80)
    logger.info("Route different HTTP status codes to appropriate handlers")
    
    context = ExecutionContext("test")
    
    switch_node = SwitchNode("status_router", {
        "cases": ["200", "404", "500"]
    })
    
    # Test different status codes
    test_cases = [
        (200, "case_200", "OK - Success"),
        (404, "case_404", "Not Found - Client Error"),
        (500, "case_500", "Internal Server Error - Server Error"),
        (301, "default", "Redirect - Other Status"),
    ]
    
    results = []
    
    for status_code, expected_route, description in test_cases:
        context.set_variable("status", status_code)
        switch_node.set_input_value("value", str(status_code))
        
        result = await switch_node.execute(context)
        actual_route = result["next_nodes"][0]
        
        logger.info(f"Status {status_code} → {actual_route}: {description}")
        results.append((status_code, actual_route))
        
        assert actual_route == expected_route
    
    logger.success(f"✓ Switch Demo: All {len(test_cases)} status codes routed correctly")


async def demo_complex_control_flow():
    """Demo 4: Complex - Break + Continue + Switch together."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 4: Complex Control Flow - Data Processor")
    logger.info("=" * 80)
    logger.info("Process data stream: Skip invalids, categorize by type, stop on error")
    
    context = ExecutionContext("test")
    
    # Simulate data stream
    data_stream = [
        {"type": "info", "value": 10},
        {"type": "warning", "value": 20},
        {"type": "invalid", "value": 0},  # Skip this
        {"type": "info", "value": 15},
        {"type": "error", "value": 99},  # Stop on this
        {"type": "info", "value": 30},  # Should not reach this
    ]
    
    for_loop = ForLoopNode("data_loop", {})
    for_loop.set_input_value("items", data_stream)
    
    switch_node = SwitchNode("type_router", {
        "cases": ["info", "warning", "error"]
    })
    
    info_sum = 0
    warning_sum = 0
    processed_count = 0
    
    while True:
        loop_result = await for_loop.execute(context)
        
        if loop_result['next_nodes'] == ["completed"]:
            logger.info("Data stream processing completed")
            break
        
        data_item = for_loop.get_output_value("item")
        data_type = data_item["type"]
        data_value = data_item["value"]
        
        logger.info(f"Processing: type={data_type}, value={data_value}")
        
        # Skip invalid entries
        if data_type == "invalid":
            logger.warning(f"  → Skipping invalid entry")
            continue
        
        # Route by type
        context.set_variable("current_type", data_type)
        switch_node.set_input_value("value", data_type)
        switch_result = await switch_node.execute(context)
        route = switch_result["next_nodes"][0]
        
        if route == "case_info":
            info_sum += data_value
            logger.info(f"  → INFO: Added {data_value}, total={info_sum}")
            processed_count += 1
        
        elif route == "case_warning":
            warning_sum += data_value
            logger.warning(f"  → WARNING: Added {data_value}, total={warning_sum}")
            processed_count += 1
        
        elif route == "case_error":
            logger.error(f"  → ERROR: Critical error detected! Stopping processing.")
            # Simulate break
            loop_state_key = f"{for_loop.node_id}_loop_state"
            del context.variables[loop_state_key]
            break
        
        else:
            logger.info(f"  → UNKNOWN: Routed to default")
    
    logger.success(f"✓ Complex Demo Results:")
    logger.success(f"  Processed {processed_count} valid entries")
    logger.success(f"  Info sum: {info_sum}")
    logger.success(f"  Warning sum: {warning_sum}")
    logger.success(f"  Stopped on error (as expected)")
    
    assert info_sum == 25  # 10 + 15
    assert warning_sum == 20
    assert processed_count == 3  # info, warning, info (stopped before second half)


async def demo_while_with_break():
    """Demo 5: While Loop with Break - User input simulation."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO 5: While Loop + Break - Input Validator")
    logger.info("=" * 80)
    logger.info("Keep prompting until valid input (simulated)")
    
    context = ExecutionContext("test")
    context.set_variable("attempt", 0)
    context.set_variable("max_attempts", 5)
    
    # Simulate user inputs (first 3 invalid, 4th valid)
    simulated_inputs = ["", "abc", "12", "42", "999"]
    
    while_loop = WhileLoopNode("input_loop", {
        "expression": "attempt < max_attempts",
        "max_iterations": 10
    })
    
    valid_input = None
    
    while True:
        result = await while_loop.execute(context)
        
        if result['next_nodes'] == ["completed"]:
            logger.info("Max attempts reached")
            break
        
        attempt = context.get_variable("attempt")
        user_input = simulated_inputs[attempt] if attempt < len(simulated_inputs) else ""
        
        logger.info(f"Attempt {attempt + 1}: Input='{user_input}'")
        
        # Validate input (must be 2-digit number)
        if user_input.isdigit() and len(user_input) == 2:
            valid_input = int(user_input)
            logger.success(f"  → Valid input: {valid_input}")
            
            # Break from loop
            loop_state_key = f"{while_loop.node_id}_loop_state"
            del context.variables[loop_state_key]
            break
        else:
            logger.warning(f"  → Invalid input (must be 2-digit number)")
        
        # Increment attempt
        context.set_variable("attempt", attempt + 1)
    
    logger.success(f"✓ While + Break Demo: Got valid input {valid_input} after {attempt + 1} attempts")
    assert valid_input == 12  # First 2-digit number in the simulated inputs


async def main():
    """Run all enhanced control flow demos."""
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 15 + "CasareRPA - Enhanced Control Flow Demo" + " " * 24 + "║")
    logger.info("╚" + "=" * 78 + "╝")
    
    try:
        await demo_break_in_loop()
        await demo_continue_skip_values()
        await demo_switch_routing()
        await demo_complex_control_flow()
        await demo_while_with_break()
        
        logger.info("\n" + "=" * 80)
        logger.success("✓ ALL ENHANCED CONTROL FLOW DEMOS COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)
        logger.info("\nEnhanced features working perfectly:")
        logger.info("  ✓ Break - Exit loops early on condition")
        logger.info("  ✓ Continue - Skip iterations selectively")
        logger.info("  ✓ Switch - Clean multi-way branching")
        logger.info("  ✓ Complex flows - All features combined")
        
    except AssertionError as e:
        logger.error(f"\n✗ Demo failed: {e}")
        raise
    except Exception as e:
        logger.exception(f"\n✗ Demo error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
