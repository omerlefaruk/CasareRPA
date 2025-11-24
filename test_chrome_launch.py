"""
Test Chrome launch with better logging
"""
import sys
sys.path.insert(0, 'src')

from casare_rpa.nodes.desktop_nodes import LaunchApplicationNode
from casare_rpa.core.execution_context import ExecutionContext
from loguru import logger
import asyncio

async def test_chrome():
    print("=" * 60)
    print("Testing Chrome Launch")
    print("=" * 60)
    
    # Create node with longer timeout
    node = LaunchApplicationNode(
        "chrome_launch", 
        config={
            "timeout": 15.0,  # Give Chrome more time
            "window_title_hint": "Chrome"  # Will match any window with "Chrome" in title
        }
    )
    
    context = ExecutionContext()
    
    # Set the Chrome path
    chrome_path = r" node.set_input_value("application_path", chrome_path)
    
    print(f"\n1. Launching Chrome from: {chrome_path}")
    print(f"   - Timeout: 15 seconds")
    print(f"   - Window title hint: 'Chrome'")
    
    try:
        result = await node.execute(context)
        
        print(f"\n✓ Chrome launched successfully!")
        print(f"   - Window: {result['window_title']}")
        print(f"   - PID: {result['process_id']}")
        
        print(f"\n2. Press Enter to close Chrome...")
        input()
        
        # Cleanup
        if hasattr(context, 'desktop_context'):
            context.desktop_context.cleanup()
            
    except Exception as e:
        print(f"\n✗ Failed to launch Chrome: {e}")
        logger.exception("Full error:")
        
        # Try to show what windows we can find
        try:
            from casare_rpa.desktop import DesktopContext
            ctx = DesktopContext()
            windows = ctx.get_all_windows()
            print(f"\nFound {len(windows)} windows:")
            for i, w in enumerate(windows[:10], 1):  # Show first 10
                print(f"  {i}. {w.get_text()}")
            ctx.cleanup()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_chrome())
