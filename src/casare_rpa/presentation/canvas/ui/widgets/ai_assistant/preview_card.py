"""
Preview Card Widget for AI Assistant.

Shows a summary of the generated workflow with action buttons.
Displays node count, connection count, and validation status.

Features:
- Workflow summary (nodes, connections)
- "Append to Canvas" button
- "Regenerate" button
- Validation status badge
- Collapsible JSON preview
"""

from typing import Any

from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2


class PreviewCard(QFrame):
    """
    Workflow preview card with action buttons.

    Displays a summary of the generated workflow including:
    - Node count and types
    - Connection count
    - Validation status
    - Action buttons for append/regenerate

    Signals:
        append_clicked: Emitted when "Append to Canvas" is clicked
        regenerate_clicked: Emitted when "Regenerate" is clicked
        preview_toggled(bool): Emitted when JSON preview is expanded/collapsed
    """

    append_clicked = Signal()
    regenerate_clicked = Signal()
    preview_toggled = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize preview card."""
        super().__init__(parent)
        self._workflow: dict[str, Any] | None = None
        self._is_preview_expanded = False
        self._is_validated = False

        self._setup_ui()
        self._apply_style()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the preview card UI."""
        self.setObjectName("PreviewCard")
        spacing = TOKENS_V2.spacing

        layout = QVBoxLayout(self)
        layout.setContentsMargins(spacing.sm, spacing.sm, spacing.sm, spacing.sm)
        layout.setSpacing(spacing.sm)

        # Header row with title and validation badge
        header_row = QHBoxLayout()

        title_label = QLabel("Generated Workflow")
        title_label.setObjectName("PreviewTitle")
        font = title_label.font()
        font.setWeight(QFont.Weight.Bold)
        font.setPointSize(TOKENS_V2.typography.heading_md)
        title_label.setFont(font)
        header_row.addWidget(title_label)

        header_row.addStretch()

        # Validation badge
        self._validation_badge = QLabel()
        self._validation_badge.setObjectName("PreviewValidationBadge")
        self._validation_badge.setVisible(False)
        header_row.addWidget(self._validation_badge)

        layout.addLayout(header_row)

        # Summary section
        summary_frame = QFrame()
        summary_frame.setObjectName("SummaryFrame")
        summary_layout = QHBoxLayout(summary_frame)
        summary_layout.setContentsMargins(spacing.md, spacing.md, spacing.md, spacing.md)
        summary_layout.setSpacing(spacing.xl)

        # Node count
        node_section = QVBoxLayout()
        self._node_count_label = QLabel("0")
        self._node_count_label.setObjectName("CountLabel")
        node_count_font = self._node_count_label.font()
        node_count_font.setPointSize(TOKENS_V2.typography.display_lg)
        node_count_font.setWeight(QFont.Weight.Bold)
        self._node_count_label.setFont(node_count_font)
        self._node_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        node_section.addWidget(self._node_count_label)

        node_label = QLabel("Nodes")
        node_label.setObjectName("CountSubLabel")
        node_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        node_section.addWidget(node_label)

        summary_layout.addLayout(node_section)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setObjectName("SummaryDivider")
        summary_layout.addWidget(divider)

        # Connection count
        conn_section = QVBoxLayout()
        self._conn_count_label = QLabel("0")
        self._conn_count_label.setObjectName("CountLabel")
        self._conn_count_label.setFont(node_count_font)
        self._conn_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        conn_section.addWidget(self._conn_count_label)

        conn_label = QLabel("Connections")
        conn_label.setObjectName("CountSubLabel")
        conn_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        conn_section.addWidget(conn_label)

        summary_layout.addLayout(conn_section)

        layout.addWidget(summary_frame)

        # Node types summary
        self._types_label = QLabel()
        self._types_label.setObjectName("TypesLabel")
        self._types_label.setWordWrap(True)
        layout.addWidget(self._types_label)

        # JSON preview (collapsible)
        self._preview_toggle_btn = QPushButton("Show JSON")
        self._preview_toggle_btn.setObjectName("PreviewToggleButton")
        self._preview_toggle_btn.setCheckable(True)
        layout.addWidget(self._preview_toggle_btn)

        self._json_preview = QTextEdit()
        self._json_preview.setObjectName("JSONPreview")
        self._json_preview.setReadOnly(True)
        self._json_preview.setMinimumHeight(80)
        self._json_preview.setMaximumHeight(150)
        self._json_preview.setVisible(False)

        # Monospace font for JSON
        json_font = QFont("Consolas", 9)
        json_font.setStyleHint(QFont.StyleHint.Monospace)
        self._json_preview.setFont(json_font)
        layout.addWidget(self._json_preview)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(spacing.sm)

        self._append_btn = QPushButton("Append to Canvas")
        self._append_btn.setObjectName("AppendButton")
        self._append_btn.setMinimumHeight(TOKENS_V2.sizes.button_lg)
        btn_row.addWidget(self._append_btn, stretch=1)

        self._regenerate_btn = QPushButton("Regenerate")
        self._regenerate_btn.setObjectName("RegenerateButton")
        self._regenerate_btn.setMinimumHeight(TOKENS_V2.sizes.button_lg)
        btn_row.addWidget(self._regenerate_btn)

        layout.addLayout(btn_row)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

    def _apply_style(self) -> None:
        """Apply theme styling."""
        colors = THEME_V2
        radius = TOKENS_V2.radius

        self.setStyleSheet(f"""
            /* Main Card */
            #PreviewCard {{
                background-color: {colors.bg_component};
                border: 1px solid {colors.border};
                border-radius: {radius.md}px;
            }}

            /* Title */
            #PreviewTitle {{
                color: {colors.text_primary};
                background-color: transparent;
            }}

            /* Validation Badge */
            #PreviewValidationBadge {{
                background-color: {colors.success};
                color: {colors.text_on_success};
                font-size: {TOKENS_V2.typography.body_sm}px;
                font-weight: bold;
                padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.md}px;
                border-radius: {radius.sm}px;
            }}

            /* Summary Frame */
            #SummaryFrame {{
                background-color: {colors.bg_elevated};
                border: 1px solid {colors.border_dark};
                border-radius: {radius.sm}px;
            }}

            /* Count Labels */
            #CountLabel {{
                color: {colors.primary};
                background-color: transparent;
            }}
            #CountSubLabel {{
                color: {colors.text_secondary};
                background-color: transparent;
                font-size: {TOKENS_V2.typography.body}px;
            }}

            /* Divider */
            #SummaryDivider {{
                color: {colors.border};
            }}

            /* Types Label */
            #TypesLabel {{
                color: {colors.text_secondary};
                background-color: transparent;
                font-size: {TOKENS_V2.typography.body}px;
            }}

            /* Preview Toggle Button */
            #PreviewToggleButton {{
                background-color: transparent;
                color: {colors.text_secondary};
                border: 1px solid {colors.border};
                border-radius: {radius.sm}px;
                padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.md}px;
                font-size: {TOKENS_V2.typography.body}px;
            }}
            #PreviewToggleButton:hover {{
                background-color: {colors.bg_hover};
                color: {colors.text_primary};
            }}
            #PreviewToggleButton:checked {{
                background-color: {colors.bg_hover};
                color: {colors.text_primary};
            }}

            /* JSON Preview */
            #JSONPreview {{
                background-color: {colors.bg_surface};
                color: {colors.text_primary};
                border: 1px solid {colors.border_dark};
                border-radius: {radius.sm}px;
                selection-background-color: {colors.bg_selected};
            }}

            /* Append Button */
            #AppendButton {{
                background-color: {colors.primary};
                color: {colors.text_on_primary};
                border: none;
                border-radius: {radius.sm}px;
                font-weight: 600;
            }}
            #AppendButton:hover {{
                background-color: {colors.primary_hover};
            }}
            #AppendButton:pressed {{
                background-color: {colors.primary_active};
            }}
            #AppendButton:disabled {{
                background-color: {colors.bg_component};
                color: {colors.text_disabled};
            }}

            /* Regenerate Button */
            #RegenerateButton {{
                background-color: {colors.bg_component};
                color: {colors.text_primary};
                border: 1px solid {colors.border};
                border-radius: {radius.sm}px;
            }}
            #RegenerateButton:hover {{
                background-color: {colors.bg_hover};
                border-color: {colors.border_light};
            }}
            #RegenerateButton:pressed {{
                background-color: {colors.bg_component};
            }}
        """)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self._append_btn.clicked.connect(self._on_append_clicked)
        self._regenerate_btn.clicked.connect(self._on_regenerate_clicked)
        self._preview_toggle_btn.toggled.connect(self._on_preview_toggled)

    def _on_append_clicked(self) -> None:
        """Handle append button click."""
        self.append_clicked.emit()

    def _on_regenerate_clicked(self) -> None:
        """Handle regenerate button click."""
        self.regenerate_clicked.emit()

    def _on_preview_toggled(self, checked: bool) -> None:
        """Handle preview toggle."""
        self._is_preview_expanded = checked
        self._json_preview.setVisible(checked)
        self._preview_toggle_btn.setText("Hide JSON" if checked else "Show JSON")
        self.preview_toggled.emit(checked)

    def _format_workflow_json(self, workflow: dict[str, Any]) -> str:
        """Format workflow as pretty JSON."""
        import json

        try:
            return json.dumps(workflow, indent=2, ensure_ascii=False)
        except Exception:
            return str(workflow)

    def _extract_node_types(self, nodes) -> str:
        """Extract and format node types summary."""
        if not nodes:
            return "No nodes"

        # Handle both dict format (from SmartWorkflowAgent) and list format
        if isinstance(nodes, dict):
            node_list = list(nodes.values())
        else:
            node_list = nodes

        # Count node types
        type_counts: dict[str, int] = {}
        for node in node_list:
            if isinstance(node, dict):
                # Support both "type" and "node_type" keys
                node_type = node.get("node_type") or node.get("type", "Unknown")
            else:
                node_type = "Unknown"
            # Clean up type name
            clean_type = node_type.replace("Node", "")
            type_counts[clean_type] = type_counts.get(clean_type, 0) + 1

        # Format as string
        type_parts = [f"{count}x {name}" for name, count in type_counts.items()]
        return ", ".join(type_parts[:5])  # Limit to 5 types

    # ==================== Public API ====================

    def set_workflow(self, workflow: dict[str, Any]) -> None:
        """
        Set the workflow to preview.

        Args:
            workflow: Workflow dict with 'nodes' and 'connections' keys
        """
        self._workflow = workflow

        try:
            # Extract counts (handle both dict and list formats)
            nodes = workflow.get("nodes", {}) if workflow else {}
            connections = workflow.get("connections", []) if workflow else []

            node_count = len(nodes) if isinstance(nodes, dict | list) else 0
            conn_count = len(connections) if isinstance(connections, list) else 0

            self._node_count_label.setText(str(node_count))
            self._conn_count_label.setText(str(conn_count))

            # Node types summary
            try:
                types_summary = self._extract_node_types(nodes)
                self._types_label.setText(f"Types: {types_summary}")
            except Exception as e:
                logger.warning(f"Failed to extract node types: {e}")
                self._types_label.setText("Types: (unable to parse)")

            # JSON preview
            try:
                json_str = self._format_workflow_json(workflow)
                self._json_preview.setPlainText(json_str)
            except Exception as e:
                logger.warning(f"Failed to format JSON: {e}")
                self._json_preview.setPlainText(str(workflow))

            # Default to validated (will be updated externally)
            self.set_validation_status(True)

            # Ensure buttons are enabled
            self._append_btn.setEnabled(True)
            self._regenerate_btn.setEnabled(True)

            logger.debug(f"Preview card set: {node_count} nodes, {conn_count} connections")
        except Exception as e:
            logger.error(f"Error setting workflow in preview card: {e}", exc_info=True)
            # Still try to show basic info
            self._node_count_label.setText("?")
            self._conn_count_label.setText("?")
            self._types_label.setText("Error loading workflow")
            self._append_btn.setEnabled(False)
            raise  # Re-raise so caller knows something went wrong

    def set_validation_status(self, is_valid: bool, message: str = "") -> None:
        """
        Set the validation status.

        Args:
            is_valid: Whether workflow is valid
            message: Optional validation message
        """
        self._is_validated = is_valid
        self._validation_badge.setVisible(is_valid)

        if is_valid:
            self._validation_badge.setText("Verified")
            self._append_btn.setEnabled(True)
        else:
            self._validation_badge.setText(message or "Invalid")
            # Still enable append but show warning
            self._append_btn.setEnabled(True)

    def get_workflow(self) -> dict[str, Any] | None:
        """
        Get the current workflow.

        Returns:
            Workflow dict or None
        """
        return self._workflow

    def is_validated(self) -> bool:
        """
        Check if workflow is validated.

        Returns:
            True if validated
        """
        return self._is_validated

    def clear(self) -> None:
        """Clear the preview card."""
        self._workflow = None
        self._is_validated = False

        self._node_count_label.setText("0")
        self._conn_count_label.setText("0")
        self._types_label.setText("")
        self._json_preview.clear()
        self._validation_badge.setVisible(False)

        # Collapse preview if expanded
        if self._is_preview_expanded:
            self._preview_toggle_btn.setChecked(False)

    def set_append_enabled(self, enabled: bool) -> None:
        """
        Enable/disable the append button.

        Args:
            enabled: Whether button should be enabled
        """
        self._append_btn.setEnabled(enabled)

    def set_regenerate_enabled(self, enabled: bool) -> None:
        """
        Enable/disable the regenerate button.

        Args:
            enabled: Whether button should be enabled
        """
        self._regenerate_btn.setEnabled(enabled)
