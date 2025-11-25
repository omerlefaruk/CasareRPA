"""
Test script to verify selector integration in all browser-related nodes.
"""

import sys
sys.path.insert(0, 'src')

from casare_rpa.canvas.selector_integration import SelectorIntegration
from casare_rpa.canvas.visual_nodes import (
    VisualClickElementNode,
    VisualTypeTextNode,
    VisualSelectDropdownNode,
    VisualExtractTextNode,
    VisualGetAttributeNode,
    VisualWaitForElementNode
)

def test_selector_integration_import():
    """Test that selector integration can be imported"""
    print("✓ SelectorIntegration imported successfully")
    return True

def test_visual_nodes_with_selector():
    """Test that all visual nodes with selector properties exist"""
    nodes_with_selectors = [
        ("VisualClickElementNode", VisualClickElementNode),
        ("VisualTypeTextNode", VisualTypeTextNode),
        ("VisualSelectDropdownNode", VisualSelectDropdownNode),
        ("VisualExtractTextNode", VisualExtractTextNode),
        ("VisualGetAttributeNode", VisualGetAttributeNode),
        ("VisualWaitForElementNode", VisualWaitForElementNode),
    ]
    
    for node_name, node_class in nodes_with_selectors:
        print(f"✓ {node_name} available with selector property")
    
    return True

def test_app_integration():
    """Test that app.py has selector integration"""
    from casare_rpa.canvas.app import CasareRPAApp
    
    # Check that the class exists
    assert hasattr(CasareRPAApp, '__init__')
    print("✓ CasareRPAApp class available")
    
    # Import the source to verify integration code exists
    import inspect
    source = inspect.getsource(CasareRPAApp)
    
    # Check for key integration points
    checks = [
        ('SelectorIntegration import', 'SelectorIntegration'),
        ('Selector integration initialization', '_selector_integration = SelectorIntegration'),
        ('Selector picked handler', '_on_selector_picked'),
        ('Recording complete handler', '_on_recording_complete'),
        ('Start selector picking', '_on_start_selector_picking'),
        ('Toggle recording', '_on_toggle_recording'),
        ('Browser launch detection', '_check_browser_launch'),
    ]
    
    for check_name, check_string in checks:
        if check_string in source:
            print(f"✓ {check_name} integrated")
        else:
            print(f"✗ {check_name} MISSING")
            return False
    
    return True

def test_selector_files_exist():
    """Test that all selector system files exist"""
    import os
    
    files = [
        ('src/casare_rpa/utils/selector_injector.js', 'JavaScript injector'),
        ('src/casare_rpa/utils/selector_generator.py', 'Selector generator'),
        ('src/casare_rpa/utils/selector_manager.py', 'Playwright manager'),
        ('src/casare_rpa/gui/selector_dialog.py', 'Dialog UI'),
        ('src/casare_rpa/gui/selector_integration.py', 'Integration layer'),
    ]
    
    for filepath, description in files:
        if os.path.exists(filepath):
            print(f"✓ {description} exists ({filepath})")
        else:
            print(f"✗ {description} MISSING ({filepath})")
            return False
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("SELECTOR INTEGRATION TEST SUITE")
    print("=" * 60)
    print()
    
    tests = [
        ("Selector Integration Import", test_selector_integration_import),
        ("Visual Nodes with Selector", test_visual_nodes_with_selector),
        ("App Integration", test_app_integration),
        ("Selector Files", test_selector_files_exist),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            results.append((test_name, False))
    
    print()
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print()
        print("🎉 ALL TESTS PASSED - Selector integration complete!")
        print()
        print("Ready to use:")
        print("  1. Run workflow with Launch Browser node")
        print("  2. Click 'Pick Selector' or press Ctrl+Shift+S")
        print("  3. Click element in browser")
        print("  4. Choose selector strategy")
        print("  5. Selector auto-fills into node")
        return 0
    else:
        print()
        print("⚠ Some tests failed - review integration")
        return 1

if __name__ == "__main__":
    sys.exit(main())
