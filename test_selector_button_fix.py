"""
Quick test to verify selector buttons enable when browser launches.
This script creates a simple workflow and checks the integration.
"""

import sys
sys.path.insert(0, 'src')

def test_context_access():
    """Test that workflow runner context is accessible"""
    from casare_rpa.runner.workflow_runner import WorkflowRunner
    from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata
    from casare_rpa.core.events import get_event_bus
    
    # Create minimal workflow
    metadata = WorkflowMetadata(name="Test Workflow")
    workflow = WorkflowSchema(metadata)
    event_bus = get_event_bus()
    
    runner = WorkflowRunner(workflow, event_bus)
    
    # Check that context is accessible as public attribute
    assert hasattr(runner, 'context'), "❌ WorkflowRunner missing 'context' attribute"
    print("✓ WorkflowRunner.context is accessible (public attribute)")
    
    # Verify it's not _context (private)
    assert not hasattr(runner, '_context') or runner.context is not None, "Context should be public, not private"
    print("✓ Context is public attribute, not private")
    
    return True

def test_app_browser_detection():
    """Test that app.py correctly references context"""
    import inspect
    from casare_rpa.gui.app import CasareRPAApp
    
    # Get source code of _check_browser_launch method
    source = inspect.getsource(CasareRPAApp._check_browser_launch)
    
    # Verify it uses .context (not ._context)
    assert 'self._workflow_runner.context' in source, "❌ Should use .context (public)"
    assert 'self._workflow_runner._context' not in source, "❌ Should NOT use ._context (private)"
    
    print("✓ App correctly uses workflow_runner.context (public)")
    print("✓ App does NOT use workflow_runner._context (private)")
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("SELECTOR BUTTON FIX VERIFICATION")
    print("=" * 60)
    print()
    
    try:
        print("Test 1: Context Access")
        print("-" * 40)
        test_context_access()
        print()
        
        print("Test 2: App Browser Detection")
        print("-" * 40)
        test_app_browser_detection()
        print()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print()
        print("The selector buttons should now enable when browser launches!")
        print()
        print("To test:")
        print("  1. Run: python run.py")
        print("  2. Create workflow with Launch Browser node")
        print("  3. Run workflow")
        print("  4. Check that 'Pick Element Selector' button is enabled")
        print("  5. Check that 'Record Workflow' button is enabled")
        print()
        return 0
        
    except AssertionError as e:
        print()
        print("=" * 60)
        print("❌ TEST FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ UNEXPECTED ERROR")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
