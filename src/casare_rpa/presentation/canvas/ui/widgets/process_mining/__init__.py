"""
Process Mining Widgets for CasareRPA.

This package contains visualization widgets for process mining:
- ProcessMapWidget: Visual graph of discovered process model
- VariantsWidget: Execution variant analysis table
- BottlenecksWidget: Performance bottleneck visualization
- ConformanceWidget: Conformance checking results
- ProcessMiningDock: Main dock container with tabs
"""

from casare_rpa.presentation.canvas.ui.widgets.process_mining.process_map import (
    ProcessMapWidget,
)
from casare_rpa.presentation.canvas.ui.widgets.process_mining.variants_widget import (
    VariantsWidget,
)
from casare_rpa.presentation.canvas.ui.widgets.process_mining.bottlenecks_widget import (
    BottlenecksWidget,
)
from casare_rpa.presentation.canvas.ui.widgets.process_mining.conformance_widget import (
    ConformanceWidget,
)
from casare_rpa.presentation.canvas.ui.widgets.process_mining.dock import (
    ProcessMiningDock,
)

__all__ = [
    "ProcessMapWidget",
    "VariantsWidget",
    "BottlenecksWidget",
    "ConformanceWidget",
    "ProcessMiningDock",
]
