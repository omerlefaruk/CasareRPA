"""Visual nodes for rest_api category."""

import inspect
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


class VisualHttpRequestNode(VisualNode):
    """Visual representation of HttpRequestNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "HTTP Request"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize HTTP Request node."""
        super().__init__()
        self.add_text_input("url", "URL", text="", tab="inputs")
        self.add_combo_menu(
            "method",
            "Method",
            items=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
            tab="config",
        )
        self.add_text_input("body", "Body (JSON)", text="", tab="inputs")
        self.create_property("timeout", 30.0, widget_type=2, tab="config")
        self.create_property("verify_ssl", True, widget_type=1, tab="config")
        self.create_property("follow_redirects", True, widget_type=1, tab="config")
        # Advanced options
        self.add_text_input(
            "proxy", "Proxy URL", placeholder_text="http://proxy:port", tab="advanced"
        )
        self.add_text_input(
            "retry_count", "Retry Count", placeholder_text="0", tab="advanced"
        )
        self.add_text_input(
            "retry_delay", "Retry Delay (s)", placeholder_text="1.0", tab="advanced"
        )
        self.add_text_input(
            "max_redirects", "Max Redirects", placeholder_text="10", tab="advanced"
        )
        self.add_combo_menu(
            "response_encoding",
            "Response Encoding",
            items=["utf-8", "latin-1", "ascii", "auto"],
            tab="advanced",
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("url")
        self.add_input("headers")
        self.add_input("body")
        self.add_input("params")
        self.add_output("exec_out")
        self.add_output("response_body")
        self.add_output("response_json")
        self.add_output("status_code")
        self.add_output("response_headers")
        self.add_output("success")
        self.add_output("error")


class VisualHttpGetNode(VisualNode):
    """Visual representation of HttpGetNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "HTTP GET"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize HTTP GET node."""
        super().__init__()
        self.add_text_input("url", "URL", text="", tab="inputs")
        self.create_property("timeout", 30.0, widget_type=2, tab="config")
        self.create_property("verify_ssl", True, widget_type=1, tab="config")
        # Retry options
        self.add_text_input(
            "retry_count", "Retry Count", placeholder_text="0", tab="advanced"
        )
        self.add_text_input(
            "retry_delay", "Retry Delay (s)", placeholder_text="1.0", tab="advanced"
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("url")
        self.add_input("params")
        self.add_input("headers")
        self.add_output("exec_out")
        self.add_output("response_body")
        self.add_output("response_json")
        self.add_output("status_code")
        self.add_output("success")
        self.add_output("error")


class VisualHttpPostNode(VisualNode):
    """Visual representation of HttpPostNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "HTTP POST"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize HTTP POST node."""
        super().__init__()
        self.add_text_input("url", "URL", text="", tab="inputs")
        self.add_text_input("body", "Body (JSON)", text="", tab="inputs")
        self.add_combo_menu(
            "content_type",
            "Content Type",
            items=[
                "application/json",
                "application/x-www-form-urlencoded",
                "text/plain",
            ],
            tab="config",
        )
        self.create_property("timeout", 30.0, widget_type=2, tab="config")
        self.create_property("verify_ssl", True, widget_type=1, tab="config")
        # Retry options
        self.add_text_input(
            "retry_count", "Retry Count", placeholder_text="0", tab="advanced"
        )
        self.add_text_input(
            "retry_delay", "Retry Delay (s)", placeholder_text="1.0", tab="advanced"
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("url")
        self.add_input("body")
        self.add_input("headers")
        self.add_output("exec_out")
        self.add_output("response_body")
        self.add_output("response_json")
        self.add_output("status_code")
        self.add_output("success")
        self.add_output("error")


class VisualHttpPutNode(VisualNode):
    """Visual representation of HttpPutNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "HTTP PUT"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize HTTP PUT node."""
        super().__init__()
        self.add_text_input("url", "URL", text="", tab="inputs")
        self.add_text_input("body", "Body (JSON)", text="", tab="inputs")
        self.create_property("timeout", 30.0, widget_type=2, tab="config")
        self.create_property("verify_ssl", True, widget_type=1, tab="config")
        # Retry options
        self.add_text_input(
            "retry_count", "Retry Count", placeholder_text="0", tab="advanced"
        )
        self.add_text_input(
            "retry_delay", "Retry Delay (s)", placeholder_text="1.0", tab="advanced"
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("url")
        self.add_input("body")
        self.add_input("headers")
        self.add_output("exec_out")
        self.add_output("response_body")
        self.add_output("response_json")
        self.add_output("status_code")
        self.add_output("success")
        self.add_output("error")


class VisualHttpPatchNode(VisualNode):
    """Visual representation of HttpPatchNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "HTTP PATCH"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize HTTP PATCH node."""
        super().__init__()
        self.add_text_input("url", "URL", text="", tab="inputs")
        self.add_text_input("body", "Body (JSON)", text="", tab="inputs")
        self.create_property("timeout", 30.0, widget_type=2, tab="config")
        self.create_property("verify_ssl", True, widget_type=1, tab="config")
        # Retry options
        self.add_text_input(
            "retry_count", "Retry Count", placeholder_text="0", tab="advanced"
        )
        self.add_text_input(
            "retry_delay", "Retry Delay (s)", placeholder_text="1.0", tab="advanced"
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("url")
        self.add_input("body")
        self.add_input("headers")
        self.add_output("exec_out")
        self.add_output("response_body")
        self.add_output("response_json")
        self.add_output("status_code")
        self.add_output("success")
        self.add_output("error")


class VisualHttpDeleteNode(VisualNode):
    """Visual representation of HttpDeleteNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "HTTP DELETE"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize HTTP DELETE node."""
        super().__init__()
        self.add_text_input("url", "URL", text="", tab="inputs")
        self.create_property("timeout", 30.0, widget_type=2, tab="config")
        self.create_property("verify_ssl", True, widget_type=1, tab="config")
        # Retry options
        self.add_text_input(
            "retry_count", "Retry Count", placeholder_text="0", tab="advanced"
        )
        self.add_text_input(
            "retry_delay", "Retry Delay (s)", placeholder_text="1.0", tab="advanced"
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("url")
        self.add_input("headers")
        self.add_output("exec_out")
        self.add_output("response_body")
        self.add_output("status_code")
        self.add_output("success")
        self.add_output("error")


class VisualSetHttpHeadersNode(VisualNode):
    """Visual representation of SetHttpHeadersNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "Set HTTP Headers"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize Set HTTP Headers node."""
        super().__init__()
        self.add_text_input("header_name", "Header Name", text="", tab="inputs")
        self.add_text_input("header_value", "Header Value", text="", tab="inputs")
        self.add_text_input("headers_json", "Headers (JSON)", text="{}", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("base_headers")
        self.add_input("header_name")
        self.add_input("header_value")
        self.add_output("exec_out")
        self.add_output("headers")


class VisualHttpAuthNode(VisualNode):
    """Visual representation of HttpAuthNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "HTTP Auth"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize HTTP Auth node."""
        super().__init__()
        self.add_combo_menu(
            "auth_type", "Auth Type", items=["Bearer", "Basic", "ApiKey"], tab="config"
        )
        self.add_text_input("token", "Token/API Key", text="", tab="inputs")
        self.add_text_input("username", "Username", text="", tab="inputs")
        self.add_text_input("password", "Password", text="", tab="inputs")
        self.add_text_input(
            "api_key_name", "API Key Header", text="X-API-Key", tab="inputs"
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("token")
        self.add_input("username")
        self.add_input("password")
        self.add_input("base_headers")
        self.add_output("exec_out")
        self.add_output("headers")


class VisualParseJsonResponseNode(VisualNode):
    """Visual representation of ParseJsonResponseNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "Parse JSON Response"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize Parse JSON Response node."""
        super().__init__()
        self.add_text_input("path", "JSON Path", text="", tab="inputs")
        self.add_text_input("default", "Default Value", text="", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("json_data")
        self.add_input("path")
        self.add_input("default")
        self.add_output("exec_out")
        self.add_output("value")
        self.add_output("success")
        self.add_output("error")


class VisualHttpDownloadFileNode(VisualNode):
    """Visual representation of HttpDownloadFileNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "HTTP Download File"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize HTTP Download File node."""
        super().__init__()
        self.add_text_input("url", "URL", text="", tab="inputs")
        self.add_text_input("save_path", "Save Path", text="", tab="inputs")
        self.create_property("timeout", 300.0, widget_type=2, tab="config")
        self.create_property("overwrite", True, widget_type=1, tab="config")
        self.create_property("verify_ssl", True, widget_type=1, tab="config")
        # Advanced options
        self.add_text_input(
            "proxy", "Proxy URL", placeholder_text="http://proxy:port", tab="advanced"
        )
        self.add_text_input(
            "retry_count", "Retry Count", placeholder_text="0", tab="advanced"
        )
        self.add_text_input(
            "retry_delay", "Retry Delay (s)", placeholder_text="1.0", tab="advanced"
        )
        self.add_text_input(
            "chunk_size", "Chunk Size (bytes)", placeholder_text="8192", tab="advanced"
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("url")
        self.add_input("save_path")
        self.add_input("headers")
        self.add_output("exec_out")
        self.add_output("file_path")
        self.add_output("file_size")
        self.add_output("success")
        self.add_output("error")


class VisualHttpUploadFileNode(VisualNode):
    """Visual representation of HttpUploadFileNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "HTTP Upload File"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize HTTP Upload File node."""
        super().__init__()
        self.add_text_input("url", "Upload URL", text="", tab="inputs")
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.add_text_input("field_name", "Field Name", text="file", tab="inputs")
        self.create_property("timeout", 300.0, widget_type=2, tab="config")
        self.create_property("verify_ssl", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("url")
        self.add_input("file_path")
        self.add_input("headers")
        self.add_input("extra_fields")
        self.add_output("exec_out")
        self.add_output("response_body")
        self.add_output("response_json")
        self.add_output("status_code")
        self.add_output("success")
        self.add_output("error")


class VisualBuildUrlNode(VisualNode):
    """Visual representation of BuildUrlNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "Build URL"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize Build URL node."""
        super().__init__()
        self.add_text_input("base_url", "Base URL", text="", tab="inputs")
        self.add_text_input("path", "Path", text="", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("base_url")
        self.add_input("path")
        self.add_input("params")
        self.add_output("exec_out")
        self.add_output("url")


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
