"""
Test script to verify node creation fixes
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from PySide6.QtWidgets import QApplication
from NodeGraphQt import NodeGraph

# Import our modules
from casare_rpa.gui.node_registry import get_node_registry, get_node_factory
from casare_rpa.gui.visual_nodes import VisualStartNode

def test_node_creation():
    """Test that nodes are created with CasareRPA nodes attached."""
    app = QApplication(sys.argv)
    
    # Create graph
    graph = NodeGraph()
    
    # Register nodes
    registry = get_node_registry()
    registry.register_all_nodes(graph)
    
    # Create a node through the graph (simulating menu action)
    visual_node = graph.create_node(
        'casare_rpa.basic.VisualStartNode',
        name='Start',
        pos=[0, 0]
    )
    
    # Try to create CasareRPA node
    factory = get_node_factory()
    casare_node = factory.create_casare_node(visual_node)
    
    print(f"Visual node created: {visual_node.name()}")
    print(f"Visual node type: {type(visual_node)}")
    print(f"Has _casare_node attr: {hasattr(visual_node, '_casare_node')}")
    print(f"CasareRPA node: {casare_node}")
    if casare_node:
        print(f"CasareRPA node ID: {casare_node.node_id}")
        print(f"Can get from visual: {visual_node.get_casare_node()}")
    
    # Test getting node_id property
    node_id_prop = visual_node.get_property("node_id")
    print(f"node_id property: '{node_id_prop}'")
    
    return casare_node is not None

if __name__ == "__main__":
    success = test_node_creation()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
