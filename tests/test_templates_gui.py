"""Test script to verify all templates can be loaded in GUI."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from casare_rpa.utils.template_loader import TemplateLoader

def test_all_templates():
    """Test that all templates can be created."""
    loader = TemplateLoader()
    templates = loader.discover_templates()
    
    print(f"\nTesting {sum(len(t) for t in templates.values())} templates...")
    print("=" * 60)
    
    failed = []
    success_count = 0
    
    for category, template_list in templates.items():
        print(f"\n{category.upper()}:")
        for template_info in template_list:
            try:
                workflow = loader.create_workflow_from_template(template_info)
                
                # Verify workflow has nodes and connections
                assert workflow.nodes, f"Template {template_info.name} has no nodes"
                assert workflow.connections, f"Template {template_info.name} has no connections"
                
                # Verify all nodes have correct attributes
                for node_id, node in workflow.nodes.items():
                    assert hasattr(node, 'node_id'), f"Node {node_id} missing node_id"
                    assert hasattr(node, 'node_type'), f"Node {node_id} missing node_type"
                    assert hasattr(node, 'config'), f"Node {node_id} missing config"
                
                print(f"  ✓ {template_info.name}: {len(workflow.nodes)} nodes, {len(workflow.connections)} connections")
                success_count += 1
                
            except Exception as e:
                print(f"  ✗ {template_info.name}: {str(e)}")
                failed.append((template_info.name, str(e)))
    
    print("\n" + "=" * 60)
    print(f"Results: {success_count} passed, {len(failed)} failed")
    
    if failed:
        print("\nFailed templates:")
        for name, error in failed:
            print(f"  - {name}: {error}")
        return False
    
    print("\n✓ All templates passed!")
    return True

if __name__ == "__main__":
    success = test_all_templates()
    sys.exit(0 if success else 1)
