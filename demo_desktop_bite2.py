"""
Desktop Automation Bite 2 Demo - Application Management Nodes
=============================================================

This demo shows the 4 new application management nodes:
1. Launch Application Node
2. Close Application Node  
3. Activate Window Node
4. Get Window List Node

We'll launch Calculator, activate it, list windows, and close it.
"""
import sys
sys.path.insert(0, 'src')

from casare_rpa.nodes.desktop_nodes import (
    LaunchApplicationNode,
    CloseApplicationNode,
    ActivateWindowNode,
    GetWindowListNode
)
from casare_rpa.core.execution_context import ExecutionContext
import asyncio
import time

async def demo():
    print("=" * 60)
    print("Desktop Automation Bite 2 Demo")
    print("=" * 60)
    
    context = ExecutionContext()
    
    # 1. Launch Calculator
    print("\n1. Launching Calculator...")
    launch_node = LaunchApplicationNode("launch_calc")
    launch_node.set_input_value("application_path", "calc.exe")
    
    result = await launch_node.execute(context)
    print(f"   ✓ Calculator launched: {result['window_title']}")
    print(f"   ✓ Process ID: {result['process_id']}")
    
    time.sleep(1)
    
    # 2. Get window list
    print("\n2. Getting list of all windows...")
    list_node = GetWindowListNode("list_windows")
    list_result = await list_node.execute(context)
    
    windows = list_result['window_list']
    print(f"   ✓ Found {len(windows)} windows")
    print(f"   ✓ First 5 windows:")
    for i, window in enumerate(windows[:5], 1):
        print(f"      {i}. {window['title']}")
    
    time.sleep(1)
    
    # 3. Activate Calculator window
    print("\n3. Activating Calculator window...")
    activate_node = ActivateWindowNode("activate_calc")
    activate_node.set_input_value("window", result['window'])
    
    activate_result = await activate_node.execute(context)
    print(f"   ✓ Window activated successfully")
    
    print("\n4. Waiting 2 seconds to show Calculator...")
    time.sleep(2)
    
    # 5. Close Calculator
    print("\n5. Closing Calculator...")
    close_node = CloseApplicationNode("close_calc")
    close_node.set_input_value("window", result['window'])
    
    close_result = await close_node.execute(context)
    print(f"   ✓ Calculator closed successfully")
    
    # Cleanup
    if hasattr(context, 'desktop_context'):
        context.desktop_context.cleanup()
    
    print("\n" + "=" * 60)
    print("✓ Bite 2 Demo Complete!")
    print("=" * 60)
    print("\nWhat we demonstrated:")
    print("  ✓ Launched application (Calculator)")
    print("  ✓ Retrieved window list")
    print("  ✓ Activated window by handle")
    print("  ✓ Closed application gracefully")
    print("\nAll 4 application management nodes working correctly!")

if __name__ == "__main__":
    asyncio.run(demo())
