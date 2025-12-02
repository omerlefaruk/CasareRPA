"""Visual nodes for rest_api category."""

import inspect
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.domain.value_objects.types import DataType


class VisualHttpRequestNode(VisualNode):
    """Visual representation of HttpRequestNode.

    Widgets are auto-generated from HttpRequestNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "HTTP Request"
    NODE_CATEGORY = "rest_api/basic"
    CASARE_NODE_MODULE = "http_nodes"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("url", DataType.STRING)
        self.add_typed_input("headers", DataType.DICT)
        self.add_typed_input("body", DataType.STRING)
        self.add_typed_input("params", DataType.DICT)
        self.add_exec_output("exec_out")
        self.add_typed_output("response_body", DataType.STRING)
        self.add_typed_output("response_json", DataType.ANY)
        self.add_typed_output("status_code", DataType.INTEGER)
        self.add_typed_output("response_headers", DataType.DICT)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualSetHttpHeadersNode(VisualNode):
    """Visual representation of SetHttpHeadersNode.

    Widgets are auto-generated from SetHttpHeadersNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "Set HTTP Headers"
    NODE_CATEGORY = "rest_api/auth"
    CASARE_NODE_MODULE = "http_nodes"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("base_headers", DataType.DICT)
        self.add_typed_input("header_name", DataType.STRING)
        self.add_typed_input("header_value", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("headers", DataType.DICT)


class VisualHttpAuthNode(VisualNode):
    """Visual representation of HttpAuthNode.

    Widgets are auto-generated from HttpAuthNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "HTTP Auth"
    NODE_CATEGORY = "rest_api/auth"
    CASARE_NODE_MODULE = "http_nodes"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("token", DataType.STRING)
        self.add_typed_input("username", DataType.STRING)
        self.add_typed_input("password", DataType.STRING)
        self.add_typed_input("base_headers", DataType.DICT)
        self.add_exec_output("exec_out")
        self.add_typed_output("headers", DataType.DICT)


class VisualParseJsonResponseNode(VisualNode):
    """Visual representation of ParseJsonResponseNode.

    Widgets are auto-generated from ParseJsonResponseNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "Parse JSON Response"
    NODE_CATEGORY = "rest_api/advanced"
    CASARE_NODE_MODULE = "http_nodes"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("json_data", DataType.ANY)
        self.add_typed_input("path", DataType.STRING)
        self.add_typed_input("default", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("value", DataType.ANY)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualHttpDownloadFileNode(VisualNode):
    """Visual representation of HttpDownloadFileNode.

    Widgets are auto-generated from HttpDownloadFileNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "HTTP Download File"
    NODE_CATEGORY = "rest_api/advanced"
    CASARE_NODE_MODULE = "http_nodes"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("url", DataType.STRING)
        self.add_typed_input("save_path", DataType.STRING)
        self.add_typed_input("headers", DataType.DICT)
        self.add_exec_output("exec_out")
        self.add_typed_output("file_path", DataType.STRING)
        self.add_typed_output("file_size", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualHttpUploadFileNode(VisualNode):
    """Visual representation of HttpUploadFileNode.

    Widgets are auto-generated from HttpUploadFileNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "HTTP Upload File"
    NODE_CATEGORY = "rest_api/advanced"
    CASARE_NODE_MODULE = "http_nodes"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("url", DataType.STRING)
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_input("headers", DataType.DICT)
        self.add_typed_input("extra_fields", DataType.DICT)
        self.add_exec_output("exec_out")
        self.add_typed_output("response_body", DataType.STRING)
        self.add_typed_output("response_json", DataType.ANY)
        self.add_typed_output("status_code", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualBuildUrlNode(VisualNode):
    """Visual representation of BuildUrlNode.

    Widgets are auto-generated from BuildUrlNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "Build URL"
    NODE_CATEGORY = "rest_api/basic"
    CASARE_NODE_MODULE = "http_nodes"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("base_url", DataType.STRING)
        self.add_typed_input("path", DataType.STRING)
        self.add_typed_input("params", DataType.DICT)
        self.add_exec_output("exec_out")
        self.add_typed_output("url", DataType.STRING)


# Dynamic node discovery
def _get_visual_node_classes():
    """Dynamically discover all VisualNode subclasses in this module."""
    classes = []
    for name, obj in globals().items():
        if (
            inspect.isclass(obj)
            and issubclass(obj, VisualNode)
            and obj is not VisualNode
        ):
            # Ensure it has a valid NODE_NAME and is not a base class
            if (
                hasattr(obj, "NODE_NAME")
                and obj.NODE_NAME
                and obj.NODE_NAME != "Visual Node"
            ):
                # Skip internal nodes from menu (they're created programmatically)
                if getattr(obj, "INTERNAL_NODE", False):
                    continue
                classes.append(obj)
    return classes


def _get_all_visual_node_classes():
    """Get ALL visual node classes including internal ones (for registration)."""
    classes = []
    for name, obj in globals().items():
        if (
            inspect.isclass(obj)
            and issubclass(obj, VisualNode)
            and obj is not VisualNode
        ):
            if (
                hasattr(obj, "NODE_NAME")
                and obj.NODE_NAME
                and obj.NODE_NAME != "Visual Node"
            ):
                classes.append(obj)
    return classes


# VISUAL_NODE_CLASSES - for menu display (excludes internal nodes)
VISUAL_NODE_CLASSES = _get_visual_node_classes()

# ALL_VISUAL_NODE_CLASSES - for registration (includes internal nodes)
ALL_VISUAL_NODE_CLASSES = _get_all_visual_node_classes()
