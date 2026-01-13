"""
Queue Management Dock for CasareRPA.

UiPath-style transaction queue management dock widget.
Provides tabs for Queues, Transactions, and Statistics.
"""

from loguru import logger
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.application.services import QueueService
from casare_rpa.presentation.canvas.theme_system import THEME
from casare_rpa.presentation.canvas.ui.widgets.orchestrator.queues_tab import QueuesTab
from casare_rpa.presentation.canvas.ui.widgets.orchestrator.transactions_tab import (
    TransactionsTab,
)


class StatisticsTab(QWidget):
    """Simple statistics display for queue metrics."""

    def __init__(
        self,
        queue_service: QueueService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._queue_service = queue_service
        self._current_queue_id: str | None = None
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Set up the statistics UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        title = QLabel("Queue Statistics")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        self._queue_label = QLabel("Select a queue to view statistics")
        layout.addWidget(self._queue_label)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self._total_card = self._create_stat_card("Total Items", "0")
        cards_layout.addWidget(self._total_card)

        self._new_card = self._create_stat_card("New", "0", THEME.info)
        cards_layout.addWidget(self._new_card)

        self._progress_card = self._create_stat_card("In Progress", "0", THEME.warning)
        cards_layout.addWidget(self._progress_card)

        self._completed_card = self._create_stat_card("Completed", "0", THEME.success)
        cards_layout.addWidget(self._completed_card)

        self._failed_card = self._create_stat_card("Failed", "0", THEME.error)
        cards_layout.addWidget(self._failed_card)

        layout.addLayout(cards_layout)

        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(16)

        self._success_rate_card = self._create_stat_card("Success Rate", "0%", THEME.success)
        metrics_layout.addWidget(self._success_rate_card)

        self._avg_duration_card = self._create_stat_card("Avg Duration", "-")
        metrics_layout.addWidget(self._avg_duration_card)

        layout.addLayout(metrics_layout)

        layout.addStretch()

    def _create_stat_card(self, title: str, value: str, color: str | None = None) -> QFrame:
        """Create a statistics card widget."""
        c = THEME

        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {c.bg_component};
                border: 1px solid {c.border};
                border-radius: 8px;
                padding: 16px;
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {c.text_secondary}; font-size: 11px;")
        card_layout.addWidget(title_label)

        value_label = QLabel(value)
        value_color = color or c.text_primary
        value_label.setStyleSheet(f"color: {value_color}; font-size: 24px; font-weight: bold;")
        value_label.setObjectName("value_label")
        card_layout.addWidget(value_label)

        return card

    def _update_card_value(self, card: QFrame, value: str) -> None:
        """Update a card's value label."""
        label = card.findChild(QLabel, "value_label")
        if label:
            label.setText(value)

    def _apply_styles(self) -> None:
        """Apply theme styles."""
        c = THEME
        self.setStyleSheet(f"""
            QLabel {{
                color: {c.text_primary};
            }}
        """)

    def set_queue(self, queue_id: str) -> None:
        """Set the current queue for statistics."""
        self._current_queue_id = queue_id
        queue = self._queue_service.get_queue(queue_id)
        if queue:
            self._queue_label.setText(f"Statistics for: {queue.name}")
        self.refresh()

    def refresh(self) -> None:
        """Refresh statistics."""
        if not self._current_queue_id:
            return

        stats = self._queue_service.get_queue_statistics(self._current_queue_id)
        if not stats:
            return

        self._update_card_value(self._total_card, str(stats.get("total_items", 0)))
        self._update_card_value(self._new_card, str(stats.get("new_count", 0)))
        self._update_card_value(self._progress_card, str(stats.get("in_progress_count", 0)))
        self._update_card_value(self._completed_card, str(stats.get("completed_count", 0)))
        self._update_card_value(self._failed_card, str(stats.get("failed_count", 0)))

        success_rate = stats.get("success_rate", 0)
        self._update_card_value(self._success_rate_card, f"{success_rate:.1f}%")

        avg_duration_ms = stats.get("avg_duration_ms", 0)
        if avg_duration_ms > 0:
            if avg_duration_ms < 1000:
                duration_str = f"{avg_duration_ms:.0f}ms"
            elif avg_duration_ms < 60000:
                duration_str = f"{avg_duration_ms / 1000:.1f}s"
            else:
                duration_str = f"{avg_duration_ms / 60000:.1f}m"
        else:
            duration_str = "-"
        self._update_card_value(self._avg_duration_card, duration_str)


class QueueManagementDock(QDockWidget):
    """
    Dockable queue management panel.

    Provides UiPath-style transaction queue management with tabs for:
    - Queues: Queue definitions and configuration
    - Transactions: Queue items with filtering and actions
    - Statistics: Queue metrics and performance data

    Signals:
        queue_selected: Emitted when a queue is selected (queue_id: str)
        item_selected: Emitted when an item is selected (queue_id: str, item_id: str)
    """

    queue_selected = Signal(str)
    item_selected = Signal(str, str)

    TAB_QUEUES = 0
    TAB_TRANSACTIONS = 1
    TAB_STATISTICS = 2

    def __init__(
        self,
        queue_service: QueueService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize the queue management dock.

        Args:
            queue_service: Queue service instance (creates one if not provided)
            parent: Optional parent widget
        """
        super().__init__("Queue Management", parent)
        self.setObjectName("QueueManagementDock")

        self._queue_service = queue_service or QueueService()
        self._current_queue_id: str | None = None

        self._setup_dock()
        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

        logger.debug("QueueManagementDock initialized")

    def _setup_dock(self) -> None:
        """Configure dock widget properties."""
        self.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
            | Qt.DockWidgetArea.LeftDockWidgetArea
        )

        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
            # NO DockWidgetFloatable - dock-only enforcement (v2 requirement)
        )

        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def sizeHint(self) -> QSize:
        """Return preferred size for dock widget."""
        return QSize(800, 350)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tab_widget = QTabWidget()
        self._tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self._tab_widget.setDocumentMode(True)
        self._tab_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._queues_tab = QueuesTab(self._queue_service, self)
        self._tab_widget.addTab(self._queues_tab, "Queues")

        self._transactions_tab = TransactionsTab(self._queue_service, self)
        self._tab_widget.addTab(self._transactions_tab, "Transactions")

        self._statistics_tab = StatisticsTab(self._queue_service, self)
        self._tab_widget.addTab(self._statistics_tab, "Statistics")

        layout.addWidget(self._tab_widget, stretch=1)
        self.setWidget(container)

    def _apply_styles(self) -> None:
        """Apply theme styles."""
        c = THEME
        self.setStyleSheet(f"""
            QDockWidget {{
                background-color: {c.bg_elevated};
            }}
            QDockWidget::title {{
                background-color: {c.bg_header};
                color: {c.text_header};
                padding: 8px 12px;
                font-weight: 600;
            }}
            QTabWidget::pane {{
                background-color: {c.bg_elevated};
                border: none;
            }}
            QTabBar::tab {{
                background-color: transparent;
                color: {c.text_secondary};
                padding: 10px 18px;
                border: none;
                border-bottom: 2px solid transparent;
            }}
            QTabBar::tab:selected {{
                background-color: {c.bg_elevated};
                color: {c.text_primary};
                border-bottom: 2px solid {c.primary};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {c.bg_hover};
            }}
        """)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self._queues_tab.queue_selected.connect(self._on_queue_selected)
        self._transactions_tab.item_selected.connect(self._on_item_selected)
        self._tab_widget.currentChanged.connect(self._on_tab_changed)

    def _on_queue_selected(self, queue_id: str) -> None:
        """Handle queue selection."""
        self._current_queue_id = queue_id
        self._transactions_tab.set_queue(queue_id)
        self._statistics_tab.set_queue(queue_id)
        self._tab_widget.setCurrentIndex(self.TAB_TRANSACTIONS)
        self.queue_selected.emit(queue_id)

    def _on_item_selected(self, queue_id: str, item_id: str) -> None:
        """Handle item selection."""
        self.item_selected.emit(queue_id, item_id)

    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change."""
        if index == self.TAB_QUEUES:
            self._queues_tab.refresh()
        elif index == self.TAB_TRANSACTIONS:
            self._transactions_tab.refresh()
        elif index == self.TAB_STATISTICS:
            self._statistics_tab.refresh()

    def refresh(self) -> None:
        """Refresh all tabs."""
        self._queues_tab.refresh()
        if self._current_queue_id:
            self._transactions_tab.refresh()
            self._statistics_tab.refresh()

    @property
    def queue_service(self) -> QueueService:
        """Get the queue service instance."""
        return self._queue_service

    def showEvent(self, event) -> None:
        """Handle show event."""
        super().showEvent(event)
        self._queues_tab.refresh()
