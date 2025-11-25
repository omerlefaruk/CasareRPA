"""
Test script for auto-connect feature.
"""
import sys
from PySide6.QtWidgets import QApplication
from casare_rpa.canvas import NodeGraphWidget
from casare_rpa.canvas.node_registry import get_node_registry

def test_auto_connect():
    """Test that auto-connect initializes properly."""
    app = QApplication(sys.argv)
    
    # Create node graph widget
    widget = NodeGraphWidget()
    
    # Check that auto-connect is initialized
    assert hasattr(widget, '_auto_connect'), "Auto-connect manager not initialized"
    assert widget.auto_connect is not None, "Auto-connect manager is None"
    
    # Check methods exist
    assert hasattr(widget.auto_connect, 'set_active'), "set_active method missing"
    assert hasattr(widget.auto_connect, 'is_active'), "is_active method missing"
    
    # Check that it's active by default
    assert widget.auto_connect.is_active(), "Auto-connect should be active by default"
    
    # Test enable/disable
    widget.auto_connect.set_active(False)
    assert not widget.auto_connect.is_active(), "Auto-connect should be disabled"
    
    widget.auto_connect.set_active(True)
    assert widget.auto_connect.is_active(), "Auto-connect should be enabled"
    
    # Test distance setting
    widget.auto_connect.set_max_distance(500)
    assert widget.auto_connect.get_max_distance() == 500, "Distance not set correctly"
    
    print("✓ All auto-connect tests passed!")
    
    app.quit()

if __name__ == "__main__":
    test_auto_connect()
