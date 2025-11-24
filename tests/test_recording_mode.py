"""
Test script for workflow recording mode.

Run this to test the recording functionality with a real browser.
"""

import asyncio
from playwright.async_api import async_playwright
from loguru import logger

# Add src to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from casare_rpa.recorder import RecordingSession, ActionType, WorkflowGenerator
from casare_rpa.utils.selector_manager import SelectorManager


async def test_recording():
    """Test recording mode with a real browser."""
    
    print("=" * 80)
    print("WORKFLOW RECORDING MODE TEST")
    print("=" * 80)
    
    recording_session = RecordingSession()
    selector_manager = SelectorManager()
    recorded_actions = []
    
    def on_recording_complete(actions):
        """Callback when recording completes."""
        nonlocal recorded_actions
        recorded_actions = actions
        print(f"\n✓ Recording complete: {len(actions)} actions captured")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("\n1. Loading Google homepage...")
        await page.goto("https://www.google.com")
        print("   ✓ Page loaded")
        
        # Inject selector with recording support
        print("\n2. Injecting recorder...")
        await selector_manager.inject_into_page(page)
        print("   ✓ Recorder injected")
        
        # Start recording mode
        print("\n3. Starting recording mode...")
        await selector_manager.activate_selector_mode(
            recording=True,
            on_recording_complete=on_recording_complete
        )
        print("   ✓ Recording mode activated")
        print("\n   🔴 RECORDING - Interact with the page:")
        print("      - Click on elements")
        print("      - Type in input fields")
        print("      - Press Ctrl+R to stop recording")
        
        # Wait for user interactions
        print("\n   Waiting for user interactions...")
        await asyncio.sleep(30)  # Give user 30 seconds to interact
        
        # Stop recording
        print("\n4. Stopping recording...")
        await page.evaluate("window.__casareRPA.selector.stopRecording()")
        await asyncio.sleep(1)  # Wait for callback
        
        # Display results
        print("\n" + "=" * 80)
        print("RECORDED ACTIONS:")
        print("=" * 80)
        
        if recorded_actions:
            for i, action in enumerate(recorded_actions, 1):
                action_type = action.get('action', 'unknown')
                element = action.get('element', {})
                selectors = element.get('selectors', {})
                xpath = selectors.get('xpath', 'N/A')
                value = action.get('value', '')
                
                print(f"\nAction {i}: {action_type.upper()}")
                print(f"  Selector: {xpath}")
                if value:
                    print(f"  Value: {value}")
            
            # Generate workflow
            print("\n" + "=" * 80)
            print("GENERATING WORKFLOW:")
            print("=" * 80)
            
            # Convert to RecordedAction objects
            from casare_rpa.recorder.recording_session import RecordedAction
            from datetime import datetime
            
            converted_actions = []
            for action_dict in recorded_actions:
                element_info = action_dict.get('element', {})
                selectors = element_info.get('selectors', {})
                selector = selectors.get('xpath', selectors.get('css', ''))
                
                action_type_str = action_dict.get('action', 'click')
                try:
                    action_type = ActionType(action_type_str)
                except ValueError:
                    print(f"  ⚠ Unknown action type: {action_type_str}, skipping")
                    continue
                
                recorded_action = RecordedAction(
                    action_type=action_type,
                    selector=selector,
                    value=action_dict.get('value'),
                    timestamp=datetime.fromtimestamp(action_dict.get('timestamp', 0) / 1000),
                    element_info=element_info
                )
                converted_actions.append(recorded_action)
            
            # Generate workflow
            generator = WorkflowGenerator()
            node_specs = generator.generate_workflow(converted_actions)
            
            print(f"\n✓ Generated {len(node_specs)} workflow nodes:")
            for i, spec in enumerate(node_specs, 1):
                print(f"  {i}. {spec['type']}: {spec['name']}")
            
            print("\n" + "=" * 80)
            print("TEST COMPLETE")
            print("=" * 80)
            print("✓ Recording mode is working!")
            print("✓ Workflow generation is working!")
            print("\nNext steps:")
            print("  1. Test in the main GUI application")
            print("  2. Verify node creation in the graph")
            print("  3. Execute generated workflows")
            
        else:
            print("\n⚠ No actions were recorded")
            print("  Try clicking elements or typing in input fields next time")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_recording())
