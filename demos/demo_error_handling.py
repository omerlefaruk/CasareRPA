"""
Demo: Error Handling in CasareRPA
Demonstrates Try/Catch, Retry with exponential backoff, and custom error throwing.
"""

import asyncio
from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.nodes.error_handling_nodes import (
    TryNode,
    RetryNode,
    RetrySuccessNode,
    RetryFailNode,
    ThrowErrorNode
)
from casare_rpa.nodes.variable_nodes import SetVariableNode, GetVariableNode
from casare_rpa.nodes.control_flow_nodes import IfNode


def print_separator(title: str):
    """Print a section separator."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


async def demo_try_catch():
    """Demo 1: Basic Try/Catch with error recovery."""
    print_separator("Demo 1: Try/Catch Error Recovery")
    
    context = ExecutionContext("try_catch_demo")
    
    # Create nodes
    try_node = TryNode("try1")
    throw_node = ThrowErrorNode("throw1", {"error_message": "Database connection failed"})
    
    print("🔍 Attempting operation that will fail...")
    
    # Enter try block
    result1 = await try_node.execute(context)
    print(f"✓ Entered try block: {result1['next_nodes']}")
    
    # Execute throw inside try
    throw_result = await throw_node.execute(context)
    print(f"❌ Error occurred: {throw_result['error']}")
    
    # Simulate error caught by try node
    try_state = context.variables[f"{try_node.node_id}_state"]
    try_state["error_occurred"] = True
    try_state["error_message"] = throw_result["error"]
    try_state["error_type"] = throw_result["error_type"]
    
    # Return from try with error
    result2 = await try_node.execute(context)
    print(f"✓ Caught error, routing to: {result2['next_nodes']}")
    print(f"📝 Error details: {result2['data']['error_message']}")
    print(f"📝 Error type: {result2['data']['error_type']}")
    
    print("\n✅ Error handled gracefully!")


async def demo_retry_success():
    """Demo 2: Retry with eventual success."""
    print_separator("Demo 2: Retry with Exponential Backoff")
    
    context = ExecutionContext("retry_demo")
    
    # Create retry node with aggressive backoff for demo
    retry_node = RetryNode("retry1", {
        "max_attempts": 5,
        "initial_delay": 0.5,
        "backoff_multiplier": 2.0
    })
    retry_success = RetrySuccessNode("success1")
    retry_fail = RetryFailNode("fail1")
    
    print("🔄 Simulating unreliable operation (succeeds on attempt 3)...")
    
    # Simulate 3 attempts with failure then success
    for i in range(5):
        result = await retry_node.execute(context)
        attempt = result["data"]["attempt"]
        
        if attempt == 3:
            # Success on third attempt
            print(f"✓ Attempt {attempt}: SUCCESS! 🎉")
            success_result = await retry_success.execute(context)
            print(f"✓ Operation completed successfully")
            break
        else:
            # Fail first two attempts
            print(f"⏳ Attempt {attempt}: Failed, retrying with backoff...")
            
            # Store error
            retry_state = context.variables[f"{retry_node.node_id}_retry_state"]
            retry_state["last_error"] = f"Temporary failure on attempt {attempt}"
            
            # Signal retry
            fail_result = await retry_fail.execute(context)
    
    print("\n✅ Operation succeeded after retries!")


async def demo_retry_exhaustion():
    """Demo 3: Retry exhaustion (all attempts fail)."""
    print_separator("Demo 3: Retry Exhaustion")
    
    context = ExecutionContext("retry_exhaustion_demo")
    
    # Create retry node with limited attempts
    retry_node = RetryNode("retry1", {
        "max_attempts": 3,
        "initial_delay": 0.2,
        "backoff_multiplier": 2.0
    })
    retry_fail = RetryFailNode("fail1")
    
    print("🔄 Simulating persistent failure...")
    
    # Exhaust all retry attempts
    while True:
        result = await retry_node.execute(context)
        
        if not result["success"]:
            # Max attempts exceeded
            print(f"❌ All {retry_node.config['max_attempts']} attempts failed")
            print(f"📝 Last error: {result['data'].get('last_error', 'Unknown error')}")
            print(f"✓ Routing to failed handler: {result['next_nodes']}")
            break
        
        attempt = result["data"]["attempt"]
        print(f"⏳ Attempt {attempt}: Failed, retrying...")
        
        # Store error
        retry_state = context.variables[f"{retry_node.node_id}_retry_state"]
        retry_state["last_error"] = f"Persistent error on attempt {attempt}"
        
        # Signal retry
        await retry_fail.execute(context)
    
    print("\n✅ Failure handled gracefully with fallback logic!")


async def demo_nested_try_catch():
    """Demo 4: Nested error handling."""
    print_separator("Demo 4: Nested Try/Catch")
    
    context = ExecutionContext("nested_demo")
    
    # Create outer and inner try blocks
    outer_try = TryNode("outer_try")
    inner_try = TryNode("inner_try")
    throw_inner = ThrowErrorNode("throw_inner", {"error_message": "Inner operation failed"})
    
    print("🔍 Nested error handling with multiple layers...")
    
    # Enter outer try
    result1 = await outer_try.execute(context)
    print(f"✓ Entered outer try block")
    
    # Enter inner try
    result2 = await inner_try.execute(context)
    print(f"✓ Entered inner try block")
    
    # Throw error in inner block
    throw_result = await throw_inner.execute(context)
    print(f"❌ Inner error: {throw_result['error']}")
    
    # Caught by inner try
    inner_state = context.variables[f"{inner_try.node_id}_state"]
    inner_state["error_occurred"] = True
    inner_state["error_message"] = throw_result["error"]
    
    result3 = await inner_try.execute(context)
    print(f"✓ Inner catch block handled the error")
    
    # Outer try succeeds
    outer_state = context.variables[f"{outer_try.node_id}_state"]
    outer_state["error_occurred"] = False
    
    result4 = await outer_try.execute(context)
    print(f"✓ Outer try succeeded: {result4['next_nodes']}")
    
    print("\n✅ Nested error handling successful!")


async def demo_retry_with_try_catch():
    """Demo 5: Combining Retry and Try/Catch."""
    print_separator("Demo 5: Retry with Try/Catch")
    
    context = ExecutionContext("combined_demo")
    
    print("🎯 Advanced pattern: Retry with error handling...")
    
    # Create nodes
    retry_node = RetryNode("retry1", {"max_attempts": 3, "initial_delay": 0.3})
    try_node = TryNode("try1")
    throw_node = ThrowErrorNode("throw1", {"error_message": "API rate limit exceeded"})
    retry_fail = RetryFailNode("fail1")
    retry_success = RetrySuccessNode("success1")
    
    # Simulate retry with try/catch in each attempt
    for attempt_num in range(3):
        # Execute retry
        retry_result = await retry_node.execute(context)
        print(f"\n🔄 Retry attempt {retry_result['data']['attempt']}:")
        
        # Try block for this attempt
        try_result = await try_node.execute(context)
        print(f"  ✓ Entered try block")
        
        if attempt_num < 2:
            # Simulate failure
            throw_result = await throw_node.execute(context)
            print(f"  ❌ Error: {throw_result['error']}")
            
            # Mark try as failed
            try_state = context.variables[f"{try_node.node_id}_state"]
            try_state["error_occurred"] = True
            try_state["error_message"] = throw_result["error"]
            
            # Catch the error
            catch_result = await try_node.execute(context)
            print(f"  ✓ Caught error in catch block")
            
            # Signal retry needed
            await retry_fail.execute(context)
            print(f"  ⏳ Will retry...")
        else:
            # Success on third attempt
            print(f"  ✅ Operation succeeded!")
            
            # Mark try as succeeded
            try_state = context.variables[f"{try_node.node_id}_state"]
            try_state["error_occurred"] = False
            
            success_try = await try_node.execute(context)
            print(f"  ✓ Try block completed successfully")
            
            # Signal retry success
            await retry_success.execute(context)
            print(f"  🎉 Retry loop completed successfully!")
            break
    
    print("\n✅ Combined error handling pattern successful!")


async def main():
    """Run all error handling demos."""
    print("\n" + "="*60)
    print("  CasareRPA Error Handling Demos")
    print("  Professional error handling for robust workflows")
    print("="*60)
    
    # Demo 1: Basic Try/Catch
    await demo_try_catch()
    await asyncio.sleep(0.5)
    
    # Demo 2: Retry with success
    await demo_retry_success()
    await asyncio.sleep(0.5)
    
    # Demo 3: Retry exhaustion
    await demo_retry_exhaustion()
    await asyncio.sleep(0.5)
    
    # Demo 4: Nested try/catch
    await demo_nested_try_catch()
    await asyncio.sleep(0.5)
    
    # Demo 5: Combined retry and try/catch
    await demo_retry_with_try_catch()
    
    print("\n" + "="*60)
    print("  All Error Handling Demos Complete! ✅")
    print("="*60 + "\n")
    
    print("📊 Summary:")
    print("  • Try/Catch: Exception handling with success/catch routing")
    print("  • Retry: Exponential backoff with configurable attempts")
    print("  • Throw Error: Custom error generation")
    print("  • Nested Handling: Multiple error handling layers")
    print("  • Combined Patterns: Retry + Try/Catch for robust workflows")
    print("\n🎯 Error handling nodes are ready for production use!")


if __name__ == "__main__":
    asyncio.run(main())
