"""
Custom modernized NodeGraph for CasareRPA.

Fixes QUrl handling during file drops.
"""

from PySide6.QtCore import QUrl
from NodeGraphQt import NodeGraph


class CasareNodeGraph(NodeGraph):
    """
    Subclass of NodeGraph that fixes the _on_node_data_dropped QUrl TypeError.
    """

    def _on_node_data_dropped(self, data, pos):
        """Patched version that converts QUrl objects to strings."""
        if hasattr(data, "urls") and callable(data.urls):
            urls = data.urls()
            if urls:
                converted_urls = []
                for url in urls:
                    if isinstance(url, QUrl):
                        converted_urls.append(url.toLocalFile() or url.toString())
                    else:
                        converted_urls.append(str(url))
                data._converted_paths = converted_urls

        # Call the original method on NodeGraph instances we created or managed
        # But since we are subclassing, we can use super() if we are instantiating this class.
        # However, NodeGraphQt uses its own NodeGraph.
        # So we patch the base class for global effect.
        return super()._on_node_data_dropped(data, pos)


# Apply class-level patch to NodeGraph
try:
    from NodeGraphQt.base.graph import NodeGraph as OriginalNodeGraph

    _original_on_node_data_dropped = OriginalNodeGraph._on_node_data_dropped

    def patched_on_node_data_dropped(self, data, pos):
        """Fixed version of _on_node_data_dropped that handles QUrls."""
        if hasattr(data, "urls") and callable(data.urls):
            urls = data.urls()
            if urls:
                converted_urls = []
                for url in urls:
                    if isinstance(url, QUrl):
                        converted_urls.append(url.toLocalFile() or url.toString())
                    else:
                        converted_urls.append(str(url))
                data._converted_paths = converted_urls
        return _original_on_node_data_dropped(self, data, pos)

    OriginalNodeGraph._on_node_data_dropped = patched_on_node_data_dropped
except Exception as e:
    from loguru import logger

    logger.warning(f"Could not patch NodeGraph._on_node_data_dropped: {e}")
