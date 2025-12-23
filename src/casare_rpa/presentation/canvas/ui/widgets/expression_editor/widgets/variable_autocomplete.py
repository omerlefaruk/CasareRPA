"""
Variable Autocomplete Widget for CasareRPA Expression Editors.

Provides a popup autocomplete dropdown for variable insertion,
triggered by typing "{{" or via keyboard shortcut.
"""

from typing import Any

from PySide6.QtCore import QPoint, Qt, Signal, Slot
from PySide6.QtGui import QColor, QKeyEvent
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QWidget,
)

from casare_rpa.presentation.canvas.ui.theme import (
    TYPE_BADGES,
    TYPE_COLORS,
    Theme,
)
from casare_rpa.presentation.canvas.ui.widgets.variable_picker import (
    VariableInfo,
    VariableProvider,
    fuzzy_match,
)


class VariableAutocomplete(QListWidget):
    """
    Autocomplete dropdown for variables and expressions.

    Features:
    - Popup below cursor position
    - Fuzzy matching (reuses fuzzy_match from variable_picker.py)
    - Keyboard: Up/Down to navigate, Enter to select, Escape to close
    - Shows type badges (reuses TYPE_BADGES from variable_picker.py)
    - Groups: workflow variables, node outputs, system variables

    Signals:
        variable_selected: Emitted when user selects a variable (str: insertion_text)
        cancelled: Emitted when user cancels (Escape or click outside)

    Usage:
        autocomplete = VariableAutocomplete()
        autocomplete.set_filter("us")  # Filters to variables matching "us"
        autocomplete.show_at_cursor(widget, cursor_pos)
        autocomplete.variable_selected.connect(self.insert_variable)
    """

    variable_selected = Signal(str)
    cancelled = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the autocomplete widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)

        self._all_variables: list[VariableInfo] = []
        self._filtered_variables: list[VariableInfo] = []
        self._current_node_id: str | None = None
        self._graph: Any | None = None
        self._filter_text: str = ""

        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the autocomplete UI."""
        self.setMinimumWidth(280)
        self.setMaximumWidth(400)
        self.setMinimumHeight(100)
        self.setMaximumHeight(300)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _apply_styles(self) -> None:
        """Apply THEME styling."""
        c = Theme.get_colors()
        self.setStyleSheet(f"""
            QListWidget {{
                background: {c.surface};
                border: 1px solid {c.border_light};
                border-radius: 6px;
                outline: none;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 6px 10px;
                border-radius: 4px;
                margin: 1px 0px;
            }}
            QListWidget::item:hover {{
                background: {c.surface_hover};
            }}
            QListWidget::item:selected {{
                background: {c.selection};
                color: {c.text_primary};
            }}
            QScrollBar:vertical {{
                background: {c.background};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {c.secondary_hover};
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {c.border_light};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self.itemClicked.connect(self._on_item_clicked)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

    def set_node_context(
        self,
        node_id: str | None,
        graph: Any | None,
    ) -> None:
        """
        Set the current node context for upstream variable detection.

        Args:
            node_id: ID of the currently selected node
            graph: NodeGraphQt graph instance
        """
        self._current_node_id = node_id
        self._graph = graph

    def refresh_variables(self) -> None:
        """Refresh the variable list from provider."""
        provider = VariableProvider.get_instance()
        self._all_variables = provider.get_all_variables(
            self._current_node_id,
            self._graph,
        )
        self._apply_filter()

    def set_filter(self, text: str) -> None:
        """
        Set the filter text and update the list.

        Args:
            text: Filter text for fuzzy matching
        """
        self._filter_text = text.strip()
        self._apply_filter()

    def _apply_filter(self) -> None:
        """Apply fuzzy filter and populate the list."""
        if self._filter_text:
            scored_vars = []
            for var in self._all_variables:
                match, score = fuzzy_match(self._filter_text, var.name)
                if match and score > 0:
                    scored_vars.append((var, score))

                # Also check path
                if var.path:
                    path_match, path_score = fuzzy_match(self._filter_text, var.path)
                    if path_match and path_score > score:
                        scored_vars.append((var, path_score))

            # Sort by score descending
            scored_vars.sort(key=lambda x: x[1], reverse=True)
            self._filtered_variables = [var for var, _ in scored_vars[:20]]
        else:
            self._filtered_variables = self._all_variables[:20]

        self._populate_list()

    def _populate_list(self) -> None:
        """Populate the list widget with filtered variables."""
        self.clear()

        Theme.get_colors()

        for var in self._filtered_variables:
            badge = TYPE_BADGES.get(var.var_type, TYPE_BADGES["Any"])
            type_color = TYPE_COLORS.get(var.var_type, TYPE_COLORS["Any"])

            # Display: [badge] name (source)
            source_hint = ""
            if var.source.startswith("node:"):
                source_hint = f" ({var.source[5:]})"
            elif var.source == "system":
                source_hint = " (system)"

            display_text = f"[{badge}] {var.name}{source_hint}"

            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, var)
            item.setForeground(QColor(type_color))

            # Tooltip with value preview
            tooltip = f"{var.display_name}: {var.var_type}"
            if var.value is not None:
                preview = str(var.value)[:50]
                if len(str(var.value)) > 50:
                    preview += "..."
                tooltip += f"\nValue: {preview}"
            item.setToolTip(tooltip)

            self.addItem(item)

        # Select first item
        if self.count() > 0:
            self.setCurrentRow(0)

    def show_at_cursor(
        self,
        editor_widget: QWidget,
        cursor_rect: Any,
    ) -> None:
        """
        Show the autocomplete popup at the cursor position.

        Args:
            editor_widget: The text editor widget
            cursor_rect: QRect from cursorRect()
        """
        self.refresh_variables()

        if self.count() == 0:
            return

        # Position below cursor
        global_pos = editor_widget.mapToGlobal(QPoint(cursor_rect.left(), cursor_rect.bottom() + 2))
        self.move(global_pos)
        self.show()
        self.setFocus()
        self.activateWindow()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle keyboard navigation."""
        key = event.key()

        if key == Qt.Key.Key_Escape:
            self.cancelled.emit()
            self.hide()
            event.accept()
            return

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab):
            self._select_current_item()
            event.accept()
            return

        if key == Qt.Key.Key_Down:
            current = self.currentRow()
            if current < self.count() - 1:
                self.setCurrentRow(current + 1)
            event.accept()
            return

        if key == Qt.Key.Key_Up:
            current = self.currentRow()
            if current > 0:
                self.setCurrentRow(current - 1)
            event.accept()
            return

        super().keyPressEvent(event)

    @Slot(QListWidgetItem)
    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle single click - select variable."""
        self._select_item(item)

    @Slot(QListWidgetItem)
    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle double click - same as single click."""
        self._select_item(item)

    def _select_current_item(self) -> None:
        """Select the currently highlighted item."""
        item = self.currentItem()
        if item:
            self._select_item(item)

    def _select_item(self, item: QListWidgetItem) -> None:
        """Select an item and emit the variable text."""
        var = item.data(Qt.ItemDataRole.UserRole)
        if var and isinstance(var, VariableInfo):
            self.variable_selected.emit(var.insertion_text)
            self.hide()

    def focusOutEvent(self, event) -> None:
        """Hide when focus is lost."""
        super().focusOutEvent(event)
        # Small delay to allow click to register
        if not self.underMouse():
            self.cancelled.emit()
            self.hide()

    def has_matches(self) -> bool:
        """Check if there are any matching variables."""
        return self.count() > 0
