"""Search functionality components.

Provides:
- NodeSearchDialog: Legacy node search (v1 UI)
- NodeSearchV2: V2 node search using THEME_V2/TOKENS_V2

NOTE: Command palette removed per decision log (2025-12-30).

Usage:
    # V2 components (recommended)
    from casare_rpa.presentation.canvas.search import NodeSearchV2

    search = NodeSearchV2(graph=graph, parent=main_window)

    # V1 components (legacy)
    from casare_rpa.presentation.canvas.search import NodeSearchDialog
"""

from casare_rpa.presentation.canvas.search.node_search import (
    NodeSearchDialog,
)
from casare_rpa.presentation.canvas.search.node_search import (
    NodeSearchResult as NodeSearchResultV1,
)
from casare_rpa.presentation.canvas.search.node_search_v2 import (
    NodeItemWidget,
    NodeSearchResult,
    NodeSearchV2,
)

__all__ = [
    # V2 components
    "NodeSearchV2",
    "NodeSearchResult",
    "NodeItemWidget",
    # V1 components (legacy)
    "NodeSearchDialog",
    "NodeSearchResultV1",
]
