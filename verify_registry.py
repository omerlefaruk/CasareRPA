import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from casare_rpa.nodes import get_all_node_classes, TextSplitNode, MessageBoxNode


def verify_registry():
    print("Verifying Node Registry...")

    # Check direct import
    print(f"TextSplitNode imported: {TextSplitNode}")
    print(f"MessageBoxNode imported: {MessageBoxNode}")

    # Check dynamic loading
    nodes = get_all_node_classes()
    print(f"Total nodes loaded: {len(nodes)}")

    assert "TextSplitNode" in nodes
    assert "MessageBoxNode" in nodes

    print("Verification Successful!")


if __name__ == "__main__":
    verify_registry()
