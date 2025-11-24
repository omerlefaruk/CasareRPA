"""
Test Notion launch to verify no freezing
"""
import sys
sys.path.insert(0, 'src')

from casare_rpa.nodes.desktop_nodes import LaunchApplicationNode
from casare_rpa.core.execution_context import ExecutionContext
from loguru import logger
import asyncio

async def test_notion():
    print("=" * 60)
    print("Testing Notion Launch (No Freeze Test)")
    print("=" * 60)
    
    # Create node
    node = LaunchApplicationNode(
        "notion_launch", 
        config={
            "timeout": 10.0,
            "window_title_hint": "Notion"
        }
    )
    
    context = ExecutionContext()
    
    # Use the path from the error logs
    notion_path = "Notion.exe"  # Let Windows find it in PATH
    node.set_input_value("application_path", notion_path)
    
    print(f"\n1. Launching Notion...")
    print(f"   - Path: {notion_path}")
    print(f"   - Timeout: 10 seconds")
    print(f"   - Window hint: 'Notion'")
    
    try:
        result = await node.execute(context)
        
        print(f"\n✓ Notion launched successfully!")
        print(f"   - Window: {result['window_title']}")
        print(f"   - PID: {result['process_id']}")
        
        print(f"\n2. Press Enter to close Notion...")
        input()
        
        # Cleanup
        if hasattr(context, 'desktop_context'):
            context.desktop_context.cleanup()
            
    except Exception as e:
        print(f"\n✗ Failed to launch Notion: {e}")
        logger.exception("Full error:")
        
        # Check if it's just a window title issue (which is fine)
        if "Failed to find window" in str(e):
            print("\nNote: This error means Notion launched but we couldn't find its window.")
            print("This is expected if Notion minimizes to tray or has a different window title.")
            print("The important thing is: DID THE APP FREEZE? (should be NO)")
        
        # Cleanup
        if hasattr(context, 'desktop_context'):
            context.desktop_context.cleanup()

if __name__ == "__main__":
    asyncio.run(test_notion())
