try:
    from casare_rpa.nodes.interaction_nodes import ClickElementNode

    print("Successfully imported ClickElementNode")
except Exception as e:
    print(f"Failed to import: {e}")
    import traceback

    traceback.print_exc()

try:
    from casare_rpa.nodes.navigation_nodes import GoToURLNode

    print("Successfully imported GoToURLNode")
except Exception as e:
    print(f"Failed to import: {e}")
    traceback.print_exc()
