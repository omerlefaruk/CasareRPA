"""Manual test for minimap overlay."""
import sys
from casare_rpa.gui import CasareRPAApp
from casare_rpa.gui.node_graph_widget import NodeGraphWidget

def main():
    """Run minimap manual test."""
    # Create main app (it creates QApplication internally)
    casare_app = CasareRPAApp()
    window = casare_app.main_window
    
    # Create and set node graph
    node_graph = NodeGraphWidget()
    window.set_central_widget(node_graph)
    
    # Note: Create some nodes manually in the GUI to test minimap properly
    # For now, just test the minimap visibility and interaction
    
    # Show window
    window.show()
    
    # Toggle minimap on
    window.action_toggle_minimap.setChecked(True)
    window.show_minimap()
    
    print("Minimap Test Instructions:")
    print("- Press Ctrl+M to toggle minimap (bottom-left corner)")
    print("- Click on minimap to navigate to that area")
    print("- Drag on minimap to pan the view")
    print("- Zoom IN on main canvas -> viewport indicator gets BIGGER")
    print("- Zoom OUT on main canvas -> viewport indicator gets SMALLER (you see more)")
    print("- Nodes scale with zoom level in minimap")
    print("- Red box shows what's currently visible in main view")
    
    sys.exit(casare_app.run())

if __name__ == '__main__':
    main()
