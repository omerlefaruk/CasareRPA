"""
Simple test to check if LaunchBrowserNode works correctly.
"""
import asyncio
import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from casare_rpa.nodes.basic_nodes import StartNode
from casare_rpa.nodes.browser_nodes import LaunchBrowserNode
from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.core.workflow_schema import WorkflowMetadata


async def test_browser_launch():
    """Test launching browser directly."""
    print("\n" + "=" * 70)
    print("Testing Browser Launch")
    print("=" * 70)
    
    # Create execution context
    metadata = WorkflowMetadata(name="Browser Test")
    context = ExecutionContext(metadata.name)
    
    # Create and execute browser node
    browser_node = LaunchBrowserNode(node_id="browser_1")
    
    print("\n→ Attempting to launch browser...")
    print(f"  Node ID: {browser_node.node_id}")
    print(f"  Browser Type: {browser_node.config.get('browser_type', 'chromium')}")
    print(f"  Headless: {browser_node.config.get('headless', True)}")
    
    try:
        result = await browser_node.execute(context)
        
        print(f"\n✓ Result received:")
        print(f"  Success: {result.get('success')}")
        
        if result.get('success'):
            print(f"  Browser: {context.browser}")
            print(f"  Browser Type: {result.get('data', {}).get('browser_type')}")
            print("\n✓ Browser launched successfully!")
            
            # Close the browser
            if context.browser:
                print("\n→ Closing browser...")
                await context.browser.close()
                print("✓ Browser closed")
        else:
            print(f"  Error: {result.get('error')}")
            print("\n✗ Browser launch failed!")
            
    except Exception as e:
        print(f"\n✗ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(test_browser_launch())
