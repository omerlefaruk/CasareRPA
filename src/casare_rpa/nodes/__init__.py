"""
CasareRPA - Nodes Package
Contains all automation node implementations.
"""

__version__ = "0.1.0"

# Basic nodes
from .basic_nodes import StartNode, EndNode, CommentNode

# Browser control nodes
from .browser_nodes import LaunchBrowserNode, CloseBrowserNode, NewTabNode

# Navigation nodes
from .navigation_nodes import (
    GoToURLNode,
    GoBackNode,
    GoForwardNode,
    RefreshPageNode
)

# Interaction nodes
from .interaction_nodes import (
    ClickElementNode,
    TypeTextNode,
    SelectDropdownNode
)

# Data extraction nodes
from .data_nodes import (
    ExtractTextNode,
    GetAttributeNode,
    ScreenshotNode
)

# Wait nodes
from .wait_nodes import (
    WaitNode,
    WaitForElementNode,
    WaitForNavigationNode
)

# Variable nodes
from .variable_nodes import (
    SetVariableNode,
    GetVariableNode,
    IncrementVariableNode
)

# Control flow nodes
from .control_flow_nodes import (
    IfNode,
    ForLoopNode,
    WhileLoopNode,
    BreakNode,
    ContinueNode,
    SwitchNode
)

# Error handling nodes
from .error_handling_nodes import (
    TryNode,
    RetryNode,
    RetrySuccessNode,
    RetryFailNode,
    ThrowErrorNode
)

# Data operation nodes
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
    GetPropertyNode
)

# File system nodes
from .file_nodes import (
    ReadFileNode,
    WriteFileNode,
    AppendFileNode,
    DeleteFileNode,
    CopyFileNode,
    MoveFileNode,
    CreateDirectoryNode,
    ListDirectoryNode,
    FileExistsNode,
    GetFileInfoNode,
    ReadCSVNode,
    WriteCSVNode,
    ReadJSONFileNode,
    WriteJSONFileNode,
    ZipFilesNode,
    UnzipFilesNode
)

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
    # File system nodes
    "ReadFileNode",
    "WriteFileNode",
    "AppendFileNode",
    "DeleteFileNode",
    "CopyFileNode",
    "MoveFileNode",
    "CreateDirectoryNode",
    "ListDirectoryNode",
    "FileExistsNode",
    "GetFileInfoNode",
    "ReadCSVNode",
    "WriteCSVNode",
    "ReadJSONFileNode",
    "WriteJSONFileNode",
    "ZipFilesNode",
    "UnzipFilesNode",
]
