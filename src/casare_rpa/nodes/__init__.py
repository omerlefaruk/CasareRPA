"""
CasareRPA - Nodes Package

Automation node implementations for workflow execution.

Entry Points:
    - StartNode, EndNode: Workflow entry/exit points
    - LaunchBrowserNode, ClickElementNode, TypeTextNode: Browser automation
    - ReadFileNode, WriteFileNode: File system operations
    - HttpRequestNode: REST API integration
    - ForLoopStartNode, IfNode, TryNode: Control flow
    - get_all_node_classes(): Get all registered node classes
    - preload_nodes(names): Preload specific nodes for performance

Key Patterns:
    - Lazy Loading: Nodes imported on first access via NODE_REGISTRY
    - Decorator Registration: @node registers node metadata
    - Base Classes: BrowserBaseNode, GoogleBaseNode for shared functionality
    - Async Execution: All node execute() methods are async
    - Property System: Nodes define input/output via typed properties
    - Category Organization: Nodes grouped by domain (browser, file, database)

Related:
    - Domain layer: Nodes implement BaseNode protocol
    - Application layer: NodeExecutor orchestrates node execution
    - Infrastructure layer: Nodes use adapters (Playwright, database drivers)
    - visual_nodes package: Visual representation for Canvas UI

This module uses lazy loading to improve startup performance.
Node classes are only imported when first accessed.
"""

import importlib
from typing import TYPE_CHECKING, Any

# Import separate registry data
from casare_rpa.nodes.registry_data import NODE_REGISTRY

__version__ = "0.1.0"

# Type hints for IDE support - these don't actually import at runtime
if TYPE_CHECKING:
    # Use TYPE_CHECKING imports here, keeping them minimal or just referring to base types?
    # To keep this file small, we might skip the massive block of TYPE_CHECKING imports
    # and rely on the registry for runtime behavior. IDEs might lose some intellisense
    # for `from casare_rpa.nodes import X` but explicit subpackage imports `from casare_rpa.nodes.browser import X` work fine.
    # However, to preserve existing DX, we can keep key imports if needed,
    # but the goal is "Reduce file size".
    pass


# Cache for loaded modules and classes
_loaded_modules: dict[str, Any] = {}
_loaded_classes: dict[str, type] = {}


def _lazy_import(name: str) -> type:
    """
    Lazily import a node class by name.

    Args:
        name: The name of the node class to import

    Returns:
        The node class

    Raises:
        AttributeError: If the class doesn't exist
    """
    # Check cache first
    if name in _loaded_classes:
        return _loaded_classes[name]

    # Check if it's a known node class
    if name not in NODE_REGISTRY:
        raise AttributeError(f"module 'casare_rpa.nodes' has no attribute '{name}'")

    registry_entry = NODE_REGISTRY[name]

    # Handle both string and tuple entries
    if isinstance(registry_entry, tuple):
        module_name, class_name = registry_entry
    else:
        module_name = registry_entry
        class_name = name

    # Load the module if not already loaded
    if module_name not in _loaded_modules:
        full_module_name = f".{module_name}"
        _loaded_modules[module_name] = importlib.import_module(
            full_module_name, package="casare_rpa.nodes"
        )

    # Get the class from the module
    module = _loaded_modules[module_name]
    cls = getattr(module, class_name)

    # Cache and return
    _loaded_classes[name] = cls
    return cls


def __getattr__(name: str) -> Any:
    """
    Module-level __getattr__ for lazy loading.

    This is called when an attribute is accessed that doesn't exist
    in the module's namespace.
    """
    if name in NODE_REGISTRY:
        return _lazy_import(name)

    # Handle special attributes
    if name == "__all__":
        return list(NODE_REGISTRY.keys()) + ["__version__"]

    raise AttributeError(f"module 'casare_rpa.nodes' has no attribute '{name}'")


def __dir__() -> list[str]:
    """Return the list of available attributes for tab completion."""
    return list(NODE_REGISTRY.keys()) + [
        "__version__",
        "get_all_node_classes",
        "preload_nodes",
    ]


def get_all_node_classes() -> dict[str, type]:
    """
    Get all node classes (this will trigger loading all modules).

    Returns:
        Dictionary mapping class names to class objects
    """
    result = {}
    for name in NODE_REGISTRY:
        result[name] = _lazy_import(name)
    return result


def get_node_class(name: str) -> type:
    """
    Get a node class by class name via the lazy registry.

    Args:
        name: Node class name (e.g. "ClickElementNode")

    Returns:
        Node class

    Raises:
        AttributeError: If the class name is not registered.
    """
    return _lazy_import(name)


def preload_nodes(node_names: list[str] = None) -> None:
    """
    Preload specific nodes or all nodes.

    This can be called during application startup to preload
    frequently used nodes, or in a background thread.

    Args:
        node_names: List of node class names to preload, or None for all
    """
    names_to_load = node_names if node_names else list(NODE_REGISTRY.keys())
    for name in names_to_load:
        if name in NODE_REGISTRY:
            _lazy_import(name)


# Re-export preloader functions for convenience
def start_node_preload() -> None:
    """Start background node preloading for improved startup performance."""
    from casare_rpa.nodes.preloader import start_node_preload as _start

    _start()


def is_preload_complete() -> bool:
    """Check if preloading has completed."""
    from casare_rpa.nodes.preloader import is_preload_complete as _check

    return _check()


def wait_for_preload(timeout: float = 5.0) -> bool:
    """Wait for preloading to complete."""
    from casare_rpa.nodes.preloader import wait_for_preload as _wait

    return _wait(timeout)


# Export __all__ for explicit imports
__all__ = [
    "__version__",
    "get_all_node_classes",
    "get_node_class",
    "preload_nodes",
    "start_node_preload",
    "is_preload_complete",
    "wait_for_preload",
] + list(NODE_REGISTRY.keys())
