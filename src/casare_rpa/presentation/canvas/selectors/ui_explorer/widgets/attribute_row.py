"""
Attribute Row Widget for UI Explorer.

Single row widget displaying:
[checkbox] attribute_name    value

Supports multiple visual states for included/excluded/required attributes.
"""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QWidget,
)
from PySide6.QtGui import QFont

from casare_rpa.presentation.canvas.selectors.ui_explorer.models.selector_model import (
    SelectorAttribute,
)


class AttributeRow(QWidget):
    """
    Single attribute row in the Selector Editor.

    Displays a checkbox, attribute name, and value.
    Visual states:
    - Included (checked): Blue accent, bold name
    - Excluded (unchecked): Gray text
    - Required (checked, disabled): Green accent, bold name

    Signals:
        toggled: Emitted when checkbox is toggled (attribute_name, is_checked)
    """

    toggled = Signal(str, bool)  # attribute_name, is_checked

    # Style constants
    INCLUDED_NAME_COLOR = "#60a5fa"  # Blue
    EXCLUDED_NAME_COLOR = "#888888"  # Gray
    REQUIRED_NAME_COLOR = "#4ade80"  # Green
    INCLUDED_VALUE_COLOR = "#e0e0e0"  # Light
    EXCLUDED_VALUE_COLOR = "#666666"  # Dark gray
    COMPUTED_VALUE_COLOR = "#a78bfa"  # Purple (for computed values)

    def __init__(
        self,
        attribute: SelectorAttribute,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the attribute row.

        Args:
            attribute: SelectorAttribute to display
            parent: Parent widget
        """
        super().__init__(parent)

        self._attribute = attribute
        self._setup_ui()
        self._apply_state()

    @property
    def attribute(self) -> SelectorAttribute:
        """Get the underlying attribute."""
        return self._attribute

    @property
    def name(self) -> str:
        """Get the attribute name."""
        return self._attribute.name

    @property
    def is_checked(self) -> bool:
        """Check if the checkbox is checked."""
        return self._checkbox.isChecked()

    def _setup_ui(self) -> None:
        """Build the row UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Checkbox
        self._checkbox = QCheckBox()
        self._checkbox.setChecked(self._attribute.included)
        self._checkbox.setEnabled(not self._attribute.required)
        self._checkbox.stateChanged.connect(self._on_checkbox_changed)
        self._checkbox.setFixedWidth(20)
        layout.addWidget(self._checkbox)

        # Name label (fixed width for alignment)
        self._name_label = QLabel(self._attribute.name)
        self._name_label.setFixedWidth(120)
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._name_label)

        # Value label (stretches)
        self._value_label = QLabel(self._attribute.display_value)
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._value_label.setWordWrap(False)
        self._value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self._value_label, 1)  # Stretch factor 1

        # Set fixed height
        self.setFixedHeight(32)

        # Apply base styling
        self.setStyleSheet("""
            AttributeRow {
                background: transparent;
                border-radius: 4px;
            }
            AttributeRow:hover {
                background: #2a2a2a;
            }
        """)

    def _apply_state(self) -> None:
        """Apply visual state based on attribute properties."""
        attr = self._attribute

        # Determine colors based on state
        if attr.required:
            name_color = self.REQUIRED_NAME_COLOR
            value_color = self.INCLUDED_VALUE_COLOR
            name_bold = True
        elif attr.included:
            name_color = self.INCLUDED_NAME_COLOR
            value_color = self.INCLUDED_VALUE_COLOR
            name_bold = True
        else:
            name_color = self.EXCLUDED_NAME_COLOR
            value_color = self.EXCLUDED_VALUE_COLOR
            name_bold = False

        # Override value color for computed attributes
        if attr.computed:
            value_color = self.COMPUTED_VALUE_COLOR

        # Override value color for empty values
        if attr.is_empty:
            value_color = "#555555"

        # Apply name styling
        font = QFont()
        font.setBold(name_bold)
        font.setPointSize(10)
        self._name_label.setFont(font)
        self._name_label.setStyleSheet(f"color: {name_color}; background: transparent;")

        # Apply value styling
        value_font = QFont()
        value_font.setPointSize(10)
        if attr.is_empty:
            value_font.setItalic(True)
        self._value_label.setFont(value_font)
        self._value_label.setStyleSheet(f"color: {value_color}; background: transparent;")

        # Style checkbox for required state
        if attr.required:
            self._checkbox.setStyleSheet("""
                QCheckBox::indicator:checked {
                    background: #166534;
                    border: 1px solid #4ade80;
                }
                QCheckBox::indicator:checked:disabled {
                    background: #166534;
                    border: 1px solid #4ade80;
                }
            """)
        elif attr.included:
            self._checkbox.setStyleSheet("""
                QCheckBox::indicator:checked {
                    background: #1d4ed8;
                    border: 1px solid #60a5fa;
                }
            """)
        else:
            self._checkbox.setStyleSheet("""
                QCheckBox::indicator:unchecked {
                    background: #333333;
                    border: 1px solid #555555;
                }
            """)

    def _on_checkbox_changed(self, state: int) -> None:
        """Handle checkbox state change."""
        is_checked = state == Qt.CheckState.Checked.value

        # Update internal state
        self._attribute.included = is_checked

        # Update visual state
        self._apply_state()

        # Emit signal
        self.toggled.emit(self._attribute.name, is_checked)

    def set_checked(self, checked: bool) -> None:
        """
        Set checkbox state programmatically.

        Args:
            checked: Whether to check the checkbox
        """
        if self._attribute.required and not checked:
            return  # Cannot uncheck required attributes

        # Block signals to avoid double emission
        self._checkbox.blockSignals(True)
        self._checkbox.setChecked(checked)
        self._attribute.included = checked
        self._checkbox.blockSignals(False)

        # Update visual state
        self._apply_state()

    def update_attribute(self, attribute: SelectorAttribute) -> None:
        """
        Update with new attribute data.

        Args:
            attribute: New SelectorAttribute
        """
        self._attribute = attribute
        self._checkbox.setChecked(attribute.included)
        self._checkbox.setEnabled(not attribute.required)
        self._name_label.setText(attribute.name)
        self._value_label.setText(attribute.display_value)
        self._apply_state()

    def enterEvent(self, event) -> None:
        """Handle mouse enter for hover effect."""
        super().enterEvent(event)
        self.setStyleSheet("""
            AttributeRow {
                background: #2a2a2a;
                border-radius: 4px;
            }
        """)

    def leaveEvent(self, event) -> None:
        """Handle mouse leave for hover effect."""
        super().leaveEvent(event)
        self.setStyleSheet("""
            AttributeRow {
                background: transparent;
                border-radius: 4px;
            }
        """)
