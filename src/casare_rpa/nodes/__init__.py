"""
CasareRPA - Nodes Package
Contains all automation node implementations.

This module uses lazy loading to improve startup performance.
Node classes are only imported when first accessed.
"""

import importlib
from typing import TYPE_CHECKING, Any, Dict, List, Type

__version__ = "0.1.0"

# Type hints for IDE support - these don't actually import at runtime
if TYPE_CHECKING:
    from .basic_nodes import StartNode, EndNode, CommentNode
    from .browser_nodes import LaunchBrowserNode, CloseBrowserNode, NewTabNode
    from .navigation_nodes import (
        GoToURLNode,
        GoBackNode,
        GoForwardNode,
        RefreshPageNode,
    )
    from .interaction_nodes import (
        ClickElementNode,
        TypeTextNode,
        SelectDropdownNode,
    )
    from .data_nodes import (
        ExtractTextNode,
        GetAttributeNode,
        ScreenshotNode,
    )
    from .wait_nodes import (
        WaitNode,
        WaitForElementNode,
        WaitForNavigationNode,
    )
    from .variable_nodes import (
        SetVariableNode,
        GetVariableNode,
        IncrementVariableNode,
    )
    from .control_flow_nodes import (
        IfNode,
        ForLoopNode,
        WhileLoopNode,
        BreakNode,
        ContinueNode,
        SwitchNode,
    )
    from .error_handling_nodes import (
        TryNode,
        RetryNode,
        RetrySuccessNode,
        RetryFailNode,
        ThrowErrorNode,
    )
    from .data_operation_nodes import (
        ConcatenateNode,
        FormatStringNode,
        RegexMatchNode,
        RegexReplaceNode,
        MathOperationNode,
        ComparisonNode,
        CreateListNode,
        ListGetItemNode,
        JsonParseNode,
        GetPropertyNode,
    )
    from .utility_nodes import (
        HttpRequestNode,
        ValidateNode,
        TransformNode,
        LogNode,
    )


# Lazy loading registry - maps node class names to their module paths
_NODE_REGISTRY: Dict[str, str] = {
    # Basic nodes
    "StartNode": "basic_nodes",
    "EndNode": "basic_nodes",
    "CommentNode": "basic_nodes",
    # Browser control nodes
    "LaunchBrowserNode": "browser_nodes",
    "CloseBrowserNode": "browser_nodes",
    "NewTabNode": "browser_nodes",
    # Navigation nodes
    "GoToURLNode": "navigation_nodes",
    "GoBackNode": "navigation_nodes",
    "GoForwardNode": "navigation_nodes",
    "RefreshPageNode": "navigation_nodes",
    # Interaction nodes
    "ClickElementNode": "interaction_nodes",
    "TypeTextNode": "interaction_nodes",
    "SelectDropdownNode": "interaction_nodes",
    # Data extraction nodes
    "ExtractTextNode": "data_nodes",
    "GetAttributeNode": "data_nodes",
    "ScreenshotNode": "data_nodes",
    # Wait nodes
    "WaitNode": "wait_nodes",
    "WaitForElementNode": "wait_nodes",
    "WaitForNavigationNode": "wait_nodes",
    # Variable nodes
    "SetVariableNode": "variable_nodes",
    "GetVariableNode": "variable_nodes",
    "IncrementVariableNode": "variable_nodes",
    # Control flow nodes
    "IfNode": "control_flow_nodes",
    "ForLoopNode": "control_flow_nodes",
    "WhileLoopNode": "control_flow_nodes",
    "BreakNode": "control_flow_nodes",
    "ContinueNode": "control_flow_nodes",
    "SwitchNode": "control_flow_nodes",
    # Error handling nodes
    "TryNode": "error_handling_nodes",
    "RetryNode": "error_handling_nodes",
    "RetrySuccessNode": "error_handling_nodes",
    "RetryFailNode": "error_handling_nodes",
    "ThrowErrorNode": "error_handling_nodes",
    # Data operation nodes
    "ConcatenateNode": "data_operation_nodes",
    "FormatStringNode": "data_operation_nodes",
    "RegexMatchNode": "data_operation_nodes",
    "RegexReplaceNode": "data_operation_nodes",
    "MathOperationNode": "data_operation_nodes",
    "ComparisonNode": "data_operation_nodes",
    "CreateListNode": "data_operation_nodes",
    "ListGetItemNode": "data_operation_nodes",
    "JsonParseNode": "data_operation_nodes",
    "GetPropertyNode": "data_operation_nodes",
    # Utility nodes
    "HttpRequestNode": "utility_nodes",
    "ValidateNode": "utility_nodes",
    "TransformNode": "utility_nodes",
    "LogNode": "utility_nodes",
}

# Cache for loaded modules and classes
_loaded_modules: Dict[str, Any] = {}
_loaded_classes: Dict[str, Type] = {}


def _lazy_import(name: str) -> Type:
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
    if name not in _NODE_REGISTRY:
        raise AttributeError(f"module 'casare_rpa.nodes' has no attribute '{name}'")

    module_name = _NODE_REGISTRY[name]

    # Load the module if not already loaded
    if module_name not in _loaded_modules:
        full_module_name = f".{module_name}"
        _loaded_modules[module_name] = importlib.import_module(
            full_module_name, package="casare_rpa.nodes"
        )

    # Get the class from the module
    module = _loaded_modules[module_name]
    cls = getattr(module, name)

    # Cache and return
    _loaded_classes[name] = cls
    return cls


def __getattr__(name: str) -> Any:
    """
    Module-level __getattr__ for lazy loading.

    This is called when an attribute is accessed that doesn't exist
    in the module's namespace.
    """
    if name in _NODE_REGISTRY:
        return _lazy_import(name)

    # Handle special attributes
    if name == "__all__":
        return list(_NODE_REGISTRY.keys()) + ["__version__"]

    raise AttributeError(f"module 'casare_rpa.nodes' has no attribute '{name}'")


def __dir__() -> List[str]:
    """Return the list of available attributes for tab completion."""
    return list(_NODE_REGISTRY.keys()) + ["__version__", "get_all_node_classes", "preload_nodes"]


def get_all_node_classes() -> Dict[str, Type]:
    """
    Get all node classes (this will trigger loading all modules).

    Returns:
        Dictionary mapping class names to class objects
    """
    result = {}
    for name in _NODE_REGISTRY:
        result[name] = _lazy_import(name)
    return result


def preload_nodes(node_names: List[str] = None) -> None:
    """
    Preload specific nodes or all nodes.

    This can be called during application startup to preload
    frequently used nodes, or in a background thread.

    Args:
        node_names: List of node class names to preload, or None for all
    """
    names_to_load = node_names if node_names else list(_NODE_REGISTRY.keys())
    for name in names_to_load:
        if name in _NODE_REGISTRY:
            _lazy_import(name)


# Export __all__ for explicit imports
__all__ = [
    "__version__",
    # Basic nodes
    "StartNode",
    "EndNode",
    "CommentNode",
    # Browser control
    "LaunchBrowserNode",
    "CloseBrowserNode",
    "NewTabNode",
    # Navigation
    "GoToURLNode",
    "GoBackNode",
    "GoForwardNode",
    "RefreshPageNode",
    # Interaction
    "ClickElementNode",
    "TypeTextNode",
    "SelectDropdownNode",
    # Data extraction
    "ExtractTextNode",
    "GetAttributeNode",
    "ScreenshotNode",
    # Wait nodes
    "WaitNode",
    "WaitForElementNode",
    "WaitForNavigationNode",
    # Variable nodes
    "SetVariableNode",
    "GetVariableNode",
    "IncrementVariableNode",
    # Control flow nodes
    "IfNode",
    "ForLoopNode",
    "WhileLoopNode",
    "BreakNode",
    "ContinueNode",
    "SwitchNode",
    # Error handling nodes
    "TryNode",
    "RetryNode",
    "RetrySuccessNode",
    "RetryFailNode",
    "ThrowErrorNode",
    # Data operation nodes
    "ConcatenateNode",
    "FormatStringNode",
    "RegexMatchNode",
    "RegexReplaceNode",
    "MathOperationNode",
    "ComparisonNode",
    "CreateListNode",
    "ListGetItemNode",
    "JsonParseNode",
    "GetPropertyNode",
    # Utility nodes
    "HttpRequestNode",
    "ValidateNode",
    "TransformNode",
    "LogNode",
    # Utility functions
    "get_all_node_classes",
    "preload_nodes",
]
