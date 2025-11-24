"""
Demo: Desktop Automation Bite 1
Demonstrates basic window/element finding and interaction with Calculator
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from casare_rpa.desktop import DesktopContext


def main():
    print("=" * 60)
    print("Desktop Automation Bite 1 Demo")
    print("=" * 60)
    print()
    
    # Initialize context
    print("1. Initializing Desktop Context...")
    context = DesktopContext()
    print("   ✓ DesktopContext initialized")
    print()
    
    try:
        # Launch Calculator
        print("2. Launching Calculator...")
        calc_window = context.launch_application("calc.exe", timeout=10.0, window_title="Calculator")
        print(f"   ✓ Calculator launched: {calc_window.get_text()}")
        print()
        
        # Wait a moment for Calculator to fully load
        time.sleep(1.0)
        
        # Find the "One" button
        print("3. Finding 'One' button...")
        selector = {
            "strategy": "name",
            "value": "One"
        }
        
        one_button = calc_window.find_child(selector, timeout=5.0)
        print(f"   ✓ Found button: {one_button.get_text()}")
        print()
        
        # Get button properties
        print("4. Reading button properties...")
        control_type = one_button.get_property("ControlTypeName")
        automation_id = one_button.get_property("AutomationId")
        is_enabled = one_button.is_enabled()
        bounds = one_button.get_bounding_rect()
        
        print(f"   ✓ Control Type: {control_type}")
        print(f"   ✓ Automation ID: {automation_id}")
        print(f"   ✓ Enabled: {is_enabled}")
        print(f"   ✓ Position: ({bounds['left']}, {bounds['top']})")
        print(f"   ✓ Size: {bounds['width']}x{bounds['height']}")
        print()
        
        # Click the button
        print("5. Clicking 'One' button...")
        one_button.click()
        print("   ✓ Button clicked!")
        print()
        
        # Find and click "Plus" button
        print("6. Finding 'Plus' button...")
        plus_selector = {
            "strategy": "name",
            "value": "Plus"
        }
        
        plus_button = calc_window.find_child(plus_selector, timeout=5.0)
        print(f"   ✓ Found button: {plus_button.get_text()}")
        print()
        
        print("7. Clicking 'Plus' button...")
        plus_button.click()
        print("   ✓ Button clicked!")
        print()
        
        # Click "One" again
        print("8. Clicking 'One' button again...")
        one_button.click()
        print("   ✓ Button clicked!")
        print()
        
        # Click "Equals"
        print("9. Finding 'Equals' button...")
        equals_selector = {
            "strategy": "name",
            "value": "Equals"
        }
        
        equals_button = calc_window.find_child(equals_selector, timeout=5.0)
        print(f"   ✓ Found button: {equals_button.get_text()}")
        print()
        
        print("10. Clicking 'Equals' button...")
        equals_button.click()
        print("   ✓ Button clicked! (1 + 1 = 2)")
        print()
        
        # Wait to show result
        print("11. Waiting 2 seconds to show result...")
        time.sleep(2.0)
        print("   ✓ Wait complete")
        print()
        
        # Wait for user
        input("12. Press Enter to close Calculator...")
        print()
        
        # Close application
        print("13. Closing Calculator...")
        context.close_application(calc_window, force=False)
        print("   ✓ Calculator closed")
        print()
        
        print("=" * 60)
        print("✓ Bite 1 Demo Complete!")
        print("=" * 60)
        print()
        print("What we demonstrated:")
        print("  ✓ Initialized DesktopContext")
        print("  ✓ Launched Calculator application")
        print("  ✓ Found window by title")
        print("  ✓ Found buttons by name selector")
        print("  ✓ Read element properties")
        print("  ✓ Clicked multiple buttons")
        print("  ✓ Performed calculation (1 + 1 = 2)")
        print("  ✓ Closed application gracefully")
        print()
        print("Next: Bite 2 - Application Management Nodes")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"   Type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Ensure cleanup
        try:
            context.cleanup()
        except:
            pass


if __name__ == "__main__":
    main()
