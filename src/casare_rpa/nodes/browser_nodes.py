"""
DEPRECATED: Browser nodes have been moved to src/casare_rpa/nodes/browser/ package.
This module is kept for backward compatibility and re-exports the original classes.
"""

# Re-export from new locations
from .browser.lifecycle import (
    LaunchBrowserNode,
    CloseBrowserNode,
    _get_browser_profile_path,
)
from .browser.tabs import NewTabNode
from .browser.extraction_nodes import (
    GetAllImagesNode,
    DownloadFileNode,
)

# Explicitly export so wildcard imports work
__all__ = [
    "LaunchBrowserNode",
    "CloseBrowserNode",
    "NewTabNode",
    "GetAllImagesNode",
    "DownloadFileNode",
    "_get_browser_profile_path",
]
