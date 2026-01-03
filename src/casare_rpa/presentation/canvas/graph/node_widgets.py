"""
Custom Node Widget Wrappers for NodeGraphQt.

This module provides wrapper classes that extend NodeGraphQt's widget classes
with custom behavior and styling.

Classes:
    CasareComboBox: Fixes combo dropdown z-order issue
    CasareCheckBox: Adds dark blue checkbox styling
    NodeFilePathWidget: File path input with browse button
    NodeDirectoryPathWidget: Directory path input with browse button

Font Fixes:
    Font initialization moved to CasareNodeItem._create_port_text_item()
    which properly initializes fonts without global patching.
    Custom CasareQFont class available in casare_font.py for explicit font protection.

Note: Modernized versions of fixes have been moved to proper subclasses:
    - NodeGraph._on_node_data_dropped -> CasareNodeGraph (custom_graph.py)
    - NodeItem.paint -> CasareNodeItem.paint (custom_node_item.py)
    - PortItem.paint -> CasarePortItem.paint (custom_port_item.py)
    - NodeItem._add_port -> CasareNodeItem._add_port (custom_node_item.py)
    - Font init -> CasareNodeItem._create_port_text_item() (custom_node_item.py)

    Widget init patches removed - CasareComboBox.apply_fix() and CasareCheckBox.apply_styling()
    are called directly in those wrapper classes' __init__ methods.
    No longer using global patching for widgets.
"""

import re
from functools import partial

from loguru import logger
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QPushButton, QSizePolicy

from casare_rpa.presentation.canvas.graph.custom_widgets import (
    COMBO_RAISED_Z,
    CasareCheckBox,
    CasareComboBox,
)
from casare_rpa.presentation.canvas.theme import THEME_V2 as THEME
from casare_rpa.presentation.canvas.theme import TOKENS_V2 as TOKENS
from casare_rpa.presentation.canvas.ui.widgets.variable_picker import (
    VariableAwareLineEdit,
)

# Pre-compiled pattern for existing secret references
_SECRET_REFERENCE_PATTERN = re.compile(r"\{\{\$secret:[^}]+\}\}")


def apply_all_fixes() -> None:
    """
    Apply all NodeGraphQt core and widget fixes.

    MODERNIZED: Many fixes have been moved to proper subclasses:
    - NodeGraph._on_node_data_dropped -> CasareNodeGraph (modernized)
    - NodeItem.paint -> CasareNodeItem.paint (modernized)
    - PortItem.paint -> CasarePortItem.paint (modernized)
    - NodeItem._add_port -> CasareNodeItem._add_port (modernized)
    - Font initialization -> CasareNodeItem._create_port_text_item() (modernized)

    Widget fixes via CasareComboBox and CasareCheckBox classes are applied
    directly by those wrapper classes. No global patching needed.

    For explicit font protection, use CasareQFont.from_base() when needed.
    """
    # Import and trigger custom items to ensure their patches (if any) are applied
    try:
        from casare_rpa.presentation.canvas.graph.custom_port_item import (
            CasarePortItem,  # noqa: F401
        )
    except ImportError:
        pass

    # Widget init patches removed - wrapper classes handle z-order and styling
    # CasareComboBox.apply_fix() and CasareCheckBox.apply_styling() are called
    # directly in those wrapper classes' __init__ methods.

    """
    Install patches on NodeComboBox and NodeCheckBox __init__ methods.

    This ensures that every new instance gets the fixes applied automatically.
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeCheckBox, NodeComboBox

        # Patch NodeComboBox
        original_combo_init = NodeComboBox.__init__

        def patched_combo_init(self, parent=None, name="", label="", items=None):
            original_combo_init(self, parent, name, label, items)
            CasareComboBox.apply_fix(self)

        NodeComboBox.__init__ = patched_combo_init

        # Patch NodeCheckBox
        original_checkbox_init = NodeCheckBox.__init__

        def patched_checkbox_init(self, parent=None, name="", label="", text="", state=False):
            original_checkbox_init(self, parent, name, label, text, state)
            CasareCheckBox.apply_styling(self)

        NodeCheckBox.__init__ = patched_checkbox_init

    except ImportError as e:
        logger.warning(f"Could not install widget init patches: {e}")
    except Exception as e:
        logger.warning(f"Error installing widget init patches: {e}")


def apply_all_node_widget_fixes() -> None:
    """Backwards-compatible entrypoint for node widget fixes."""
    apply_all_fixes()


# =============================================================================
# Variable-Aware Text Widget - Direct creation for performance
# =============================================================================


@Slot()
def _trigger_widget_value_changed(widget, *args) -> None:
    """
    Trigger value changed on a widget, ignoring any signal arguments.

    Used with functools.partial to replace lambdas in signal connections.
    This avoids closure issues with lambdas in factory functions.

    Args:
        widget: NodeBaseWidget to trigger value change on
        *args: Ignored signal arguments
    """
    widget.on_value_changed()


@Slot()
def _set_parent_value_from_picker(target_picker, source_picker, *args) -> None:
    """
    Set parent value on target picker from source picker's selected ID.

    Used for cascading picker widgets where the target needs to update
    when the source selection changes.

    Args:
        target_picker: Picker widget to update
        source_picker: Picker widget to get selected ID from
        *args: Ignored signal arguments
    """
    target_picker.set_parent_value(source_picker.get_selected_id())


def create_variable_text_widget(
    name: str,
    label: str,
    text: str = "",
    placeholder_text: str = "",
    tooltip: str = "",
    show_expand_button: bool = True,
):
    """
    Factory function to create a variable-aware text input widget.

    Creates a widget with:
    - Variable picker {x} button for inserting variables
    - Lock 🔒 button for encrypting sensitive values
    - Optional expand ... button for expression editor

    Args:
        name: Property name for the node
        label: Label text displayed above the widget
        text: Initial text value
        placeholder_text: Placeholder text when empty
        tooltip: Tooltip text for the widget
        show_expand_button: Whether to show expand button for expression editor

    Returns:
        NodeBaseWidget with VariableAwareLineEdit, or None if unavailable
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget

        from casare_rpa.presentation.canvas.ui.widgets.variable_picker import (
            VariableAwareLineEdit,
            VariableProvider,
        )
    except ImportError:
        logger.error("NodeGraphQt or variable picker not available")
        return None

    # Create VariableAwareLineEdit directly with expand button option
    line_edit = VariableAwareLineEdit(show_expand_button=show_expand_button)
    line_edit.setText(text)
    line_edit.setPlaceholderText(placeholder_text)

    # Apply standard styling with padding for buttons
    # Extra padding on right: variable button (16px) + expand button (16px) + spacing + margin
    right_padding = 46 if show_expand_button else 28
    line_edit.setStyleSheet(f"""
        QLineEdit {{
            background: {THEME.bg_component};
            border: 1px solid {THEME.border};
            border-radius: {TOKENS.radius.sm}px;
            color: {THEME.text_primary};
            padding: 2px {right_padding}px 2px 4px;
            selection-background-color: {THEME.primary};
        }}
        QLineEdit:focus {{
            background: {THEME.bg_hover};
            border: 1px solid {THEME.border_focus};
        }}
    """)

    if tooltip:
        line_edit.setToolTip(tooltip)

    # Connect to global variable provider
    line_edit.set_provider(VariableProvider.get_instance())

    # Create NodeBaseWidget with VariableAwareLineEdit as custom widget
    widget = NodeBaseWidget(parent=None, name=name, label=label)
    widget.set_custom_widget(line_edit)

    # Connect signals
    line_edit.editingFinished.connect(widget.on_value_changed)
    line_edit.variable_inserted.connect(partial(_trigger_widget_value_changed, widget))

    # Store reference
    widget._line_edit = line_edit

    # Override get_value and set_value for consistent behavior
    # Use getValue()/setValue() which handle encrypted secrets properly
    def get_value():
        return line_edit.getValue()

    def set_value(value):
        line_edit.setValue(str(value) if value else "")

    widget.get_value = get_value
    widget.set_value = set_value

    return widget


def _add_lock_button_to_line_edit(line_edit, widget):
    """Add an encryption lock button to a VariableAwareLineEdit."""
    from PySide6.QtCore import Qt, Slot
    from PySide6.QtWidgets import QPushButton

    from casare_rpa.presentation.canvas.theme import THEME_V2 as THEME
    from casare_rpa.presentation.canvas.theme import TOKENS_V2 as TOKENS

    c = THEME

    # Create lock button with better visibility
    lock_button = QPushButton("🔒", line_edit)
    lock_button.setFixedSize(20, 20)
    lock_button.setCursor(Qt.CursorShape.PointingHandCursor)
    lock_button.setToolTip("Encrypt this value (makes it a secret)")      
    lock_button.setStyleSheet(f"""
        QPushButton {{
            background: {c.bg_component};
            border: 1px solid {c.border};
            border-radius: 3px;
            font-size: 11px;
            padding: 0px;
        }}
        QPushButton:hover {{
            background: {c.primary};
            border: 1px solid {c.primary};
        }}
    """)
    lock_button.show()  # Ensure button is visible
    lock_button.raise_()  # Bring to front

    # Position the lock button (will be repositioned on resize)
    def position_lock_button():
        # Position to the left of the variable button (which is at right edge - 25)
        x = line_edit.width() - 50  # Lock button position
        y = (line_edit.height() - lock_button.height()) // 2
        lock_button.move(x, y)
        lock_button.raise_()  # Keep on top

    # Store state on the line edit
    line_edit._encryption_state = {
        "is_encrypted": False,
        "credential_id": None,
        "plaintext_cache": None,
        "lock_button": lock_button,
    }

    @Slot()
    def on_lock_clicked():
        state = line_edit._encryption_state
        if state["is_encrypted"]:
            # Unlock: show plaintext for editing
            _unlock_for_editing(line_edit, widget)
        else:
            # Lock: encrypt current text
            _encrypt_current_text(line_edit, widget)

    lock_button.clicked.connect(on_lock_clicked)

    # Reposition on resize
    original_resize = line_edit.resizeEvent

    def new_resize_event(event):
        if original_resize:
            original_resize(event)
        position_lock_button()

    line_edit.resizeEvent = new_resize_event

    # Initial position with slight delay to ensure layout is ready
    from PySide6.QtCore import QTimer

    QTimer.singleShot(10, position_lock_button)
    QTimer.singleShot(100, position_lock_button)  # Second call for safety


def _encrypt_current_text(line_edit, widget):
    """Encrypt the current text in a line edit."""
    from loguru import logger

    text = line_edit.text().strip()
    if not text:
        return

    # Don't encrypt if already a secret reference
    if _SECRET_REFERENCE_PATTERN.match(text):
        return

    try:
        from casare_rpa.infrastructure.security.credential_store import (
            get_credential_store,
        )

        store = get_credential_store()
        credential_id = store.encrypt_inline_secret(
            plaintext=text,
            name="inline_secret",
            description="Encrypted from parameter widget",
        )

        state = line_edit._encryption_state
        state["credential_id"] = credential_id
        state["is_encrypted"] = True
        state["plaintext_cache"] = text

        # Store the secret reference for workflow serialization
        secret_reference = f"{{{{$secret:{credential_id}}}}}"
        state["secret_reference"] = secret_reference

        # Override get_value to return the secret reference
        original_get_value = getattr(widget, "_original_get_value", widget.get_value)
        widget._original_get_value = original_get_value

        def get_value_with_secret():
            enc_state = getattr(line_edit, "_encryption_state", None)
            if enc_state and enc_state.get("is_encrypted") and enc_state.get("secret_reference"):
                return enc_state["secret_reference"]
            return original_get_value()

        widget.get_value = get_value_with_secret

        # Update display to show masked text
        line_edit.blockSignals(True)
        line_edit.setText("•••••••••")
        line_edit.setReadOnly(True)
        line_edit.blockSignals(False)

        # Update button appearance
        state["lock_button"].setText("🔓")
        state["lock_button"].setToolTip("Click to edit this secret")

        # Notify widget of value change (will use get_value_with_secret)
        widget.on_value_changed()

        logger.debug(f"Encrypted text to credential: {credential_id}")

    except Exception as e:
        logger.error(f"Failed to encrypt text: {e}")


def _unlock_for_editing(line_edit, widget):
    """Unlock an encrypted value for editing."""
    from loguru import logger

    state = line_edit._encryption_state
    if not state["credential_id"]:
        return

    try:
        # Get plaintext from cache or decrypt
        plaintext = state["plaintext_cache"]
        if not plaintext:
            from casare_rpa.infrastructure.security.credential_store import (
                get_credential_store,
            )

            store = get_credential_store()
            plaintext = store.decrypt_inline_secret(state["credential_id"])

        if plaintext:
            line_edit.blockSignals(True)
            line_edit.setText(plaintext)
            line_edit.setReadOnly(False)
            line_edit.blockSignals(False)

            # Update button
            state["lock_button"].setText("🔒")
            state["lock_button"].setToolTip("Click to re-encrypt this value")

            # Clear encrypted state
            state["is_encrypted"] = False

    except Exception as e:
        logger.error(f"Failed to unlock for editing: {e}")


# =============================================================================
# NodeFilePathWidget - File path input with browse button for NodeGraphQt
# =============================================================================


def create_file_path_widget(
    name: str, label: str, file_filter: str, placeholder: str, text: str = ""
):
    """
    Factory function to create a NodeFilePathWidget.

    This creates a proper NodeBaseWidget subclass instance with file browse functionality.
    Includes variable picker integration via VariableAwareLineEdit - hover to see {x} button.
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget
        from PySide6 import QtWidgets
    except ImportError:
        logger.error("NodeGraphQt not available")
        return None

    # Create the container widget with horizontal layout
    container = QtWidgets.QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    # Set explicit minimum size to ensure visibility
    # NOTE: Minimum width should be large enough to fit within node bounds
    # when combined with the label that NodeGraphQt's _NodeGroupBox adds above
    container.setMinimumHeight(26)
    container.setMinimumWidth(180)  # Increased from 160 to fit better in nodes
    container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    # Create variable-aware line edit with {x} button for variable insertion
    line_edit = VariableAwareLineEdit()
    line_edit.setText(text)
    line_edit.setPlaceholderText(placeholder)
    line_edit.setMinimumHeight(24)
    line_edit.setMinimumWidth(100)
    line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    # Padding on right side accommodates the {x} variable button
    line_edit.setStyleSheet(f"""
        QLineEdit {{
            background: {THEME.bg_component};
            border: 1px solid {THEME.border};
            border-radius: {TOKENS.radius.sm}px;
            color: {THEME.text_primary};
            padding: 2px 28px 2px 4px;
        }}
        QLineEdit:focus {{
            border: 1px solid {THEME.border_focus};
        }}
    """)
    layout.addWidget(line_edit, 1)

    # Create browse button - use "..." text for guaranteed cross-platform visibility
    browse_btn = QPushButton("...")
    browse_btn.setFixedSize(30, 24)
    browse_btn.setToolTip("Browse for file")
    # Use theme colors for browse button
    browse_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {THEME.primary};
            border: 1px solid {THEME.border};
            border-radius: {TOKENS.radius.sm}px;
            color: #ffffff;
            font-size: {TOKENS.typography.body}px;
            font-weight: bold;
            padding: 0px;
        }}
        QPushButton:hover {{
            background-color: {THEME.primary_hover};
        }}
        QPushButton:pressed {{
            background-color: {THEME.primary_active};
        }}
    """)

    def on_browse():
        import os

        current_path = line_edit.text().strip()
        start_dir = ""
        if current_path:
            if os.path.isdir(current_path):
                start_dir = current_path
            elif os.path.dirname(current_path):
                parent = os.path.dirname(current_path)
                if os.path.isdir(parent):
                    start_dir = parent

        path, _ = QFileDialog.getOpenFileName(
            None,  # Use None for proper modal behavior
            "Select File",
            start_dir,
            file_filter,
        )
        if path:
            line_edit.setText(path)
            # CRITICAL: Manually trigger value change - setText() doesn't emit editingFinished
            # Without this, the property value is never synced to the model
            widget.on_value_changed()
            logger.debug(f"Selected file: {path}")

    browse_btn.clicked.connect(on_browse)
    layout.addWidget(browse_btn)

    # Create NodeBaseWidget and set up
    widget = NodeBaseWidget(parent=None, name=name, label=label)
    widget.set_custom_widget(container)

    # Force geometry update
    container.adjustSize()

    # Connect line edit changes to widget's value changed signal
    line_edit.editingFinished.connect(widget.on_value_changed)

    # Connect variable insertion to trigger value change
    line_edit.variable_inserted.connect(partial(_trigger_widget_value_changed, widget))

    # Store reference to line edit for get/set value
    widget._line_edit = line_edit
    widget._browse_btn = browse_btn

    # Override get_value and set_value
    def get_value():
        return line_edit.text()

    def set_value(value):
        line_edit.setText(str(value) if value else "")

    widget.get_value = get_value
    widget.set_value = set_value

    return widget


class NodeFilePathWidget:
    """
    File path widget for NodeGraphQt nodes.

    Provides a text input with a folder browse button that opens
    Windows Explorer to select a file.

    Usage in visual node:
        from casare_rpa.presentation.canvas.graph.node_widgets import NodeFilePathWidget

        def __init__(self):
            super().__init__()
            # Add file path widget with Excel filter
            widget = NodeFilePathWidget(
                name="file_path",
                label="Excel File",
                file_filter="Excel Files (*.xlsx *.xls);;All Files (*.*)",
            )
            self.add_custom_widget(widget)
    """

    def __new__(
        cls,
        name: str = "",
        label: str = "",
        file_filter: str = "All Files (*.*)",
        text: str = "",
        placeholder: str = "Select file...",
    ):
        """
        Create a new NodeFilePathWidget.

        Args:
            name: Property name for the node
            label: Label text displayed above the widget
            file_filter: File type filter for dialog (e.g., "Excel Files (*.xlsx)")
            text: Initial text value
            placeholder: Placeholder text when empty
        """
        return create_file_path_widget(name, label, file_filter, placeholder, text)


def create_directory_path_widget(name: str, label: str, placeholder: str, text: str = ""):
    """
    Factory function to create a NodeDirectoryPathWidget.

    This creates a proper NodeBaseWidget subclass instance with directory browse functionality.
    Includes variable picker integration via VariableAwareLineEdit - hover to see {x} button.
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget
        from PySide6 import QtWidgets
    except ImportError:
        logger.error("NodeGraphQt not available")
        return None

    # Create the container widget with horizontal layout
    container = QtWidgets.QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    # Set explicit minimum size to ensure visibility
    # NOTE: Minimum width should be large enough to fit within node bounds
    # when combined with the label that NodeGraphQt's _NodeGroupBox adds above
    container.setMinimumHeight(26)
    container.setMinimumWidth(180)  # Increased from 160 to fit better in nodes
    container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    # Create variable-aware line edit with {x} button for variable insertion
    line_edit = VariableAwareLineEdit()
    line_edit.setText(text)
    line_edit.setPlaceholderText(placeholder)
    line_edit.setMinimumHeight(24)
    line_edit.setMinimumWidth(100)
    line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    # Padding on right side accommodates the {x} variable button
    line_edit.setStyleSheet(f"""
        QLineEdit {{
            background: {THEME.bg_component};
            border: 1px solid {THEME.border};
            border-radius: {TOKENS.radius.sm}px;
            color: {THEME.text_primary};
            padding: 2px 28px 2px 4px;
        }}
        QLineEdit:focus {{
            border: 1px solid {THEME.border_focus};
        }}
    """)
    layout.addWidget(line_edit, 1)

    # Create browse button - use folder icon style
    browse_btn = QPushButton("...")
    browse_btn.setFixedSize(30, 24)
    browse_btn.setToolTip("Browse for folder")
    # Warning color for folder selection (differentiate from file selection)
    browse_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {THEME.warning};
            border: 1px solid {THEME.border};
            border-radius: {TOKENS.radius.sm}px;
            color: #ffffff;
            font-size: {TOKENS.typography.body}px;
            font-weight: bold;
            padding: 0px;
        }}
        QPushButton:hover {{
            background-color: {THEME.primary_hover};
        }}
        QPushButton:pressed {{
            background-color: {THEME.primary_active};
        }}
    """)

    def on_browse():
        import os

        current_path = line_edit.text().strip()
        start_dir = ""
        if current_path and os.path.isdir(current_path):
            start_dir = current_path

        path = QFileDialog.getExistingDirectory(
            None,
            "Select Directory",
            start_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if path:
            line_edit.setText(path)
            # CRITICAL: Manually trigger value change - setText() doesn't emit editingFinished
            # Without this, the property value is never synced to the model
            widget.on_value_changed()
            logger.debug(f"Selected directory: {path}")

    browse_btn.clicked.connect(on_browse)
    layout.addWidget(browse_btn)

    # Create NodeBaseWidget and set up
    widget = NodeBaseWidget(parent=None, name=name, label=label)
    widget.set_custom_widget(container)

    # Force geometry update
    container.adjustSize()

    # Connect line edit changes to widget's value changed signal
    line_edit.editingFinished.connect(widget.on_value_changed)

    # Connect variable insertion to trigger value change
    line_edit.variable_inserted.connect(partial(_trigger_widget_value_changed, widget))

    # Store reference to line edit for get/set value
    widget._line_edit = line_edit
    widget._browse_btn = browse_btn

    # Override get_value and set_value
    def get_value():
        return line_edit.text()

    def set_value(value):
        line_edit.setText(str(value) if value else "")

    widget.get_value = get_value
    widget.set_value = set_value

    return widget


class NodeDirectoryPathWidget:
    """
    Directory path widget for NodeGraphQt nodes.

    Provides a text input with a folder browse button that opens
    a directory selection dialog.

    Usage in visual node:
        from casare_rpa.presentation.canvas.graph.node_widgets import NodeDirectoryPathWidget

        def __init__(self):
            super().__init__()
            widget = NodeDirectoryPathWidget(
                name="output_dir",
                label="Output Directory",
            )
            self.add_custom_widget(widget)
            widget.setParentItem(self.view)
    """

    def __new__(
        cls,
        name: str = "",
        label: str = "",
        text: str = "",
        placeholder: str = "Select directory...",
    ):
        """
        Create a new NodeDirectoryPathWidget.

        Args:
            name: Property name for the node
            label: Label text displayed above the widget
            text: Initial text value
            placeholder: Placeholder text when empty
        """
        return create_directory_path_widget(name, label, placeholder, text)


# =============================================================================
# Helper function to set node context for variable picker
# =============================================================================


def set_variable_picker_node_context(
    line_edit: VariableAwareLineEdit,
    node_widget,
) -> None:
    """
    Set the node context on a VariableAwareLineEdit for upstream variable detection.

    This enables the variable picker to show output variables from nodes
    connected upstream of the current node.

    Args:
        line_edit: The VariableAwareLineEdit to configure
        node_widget: The NodeBaseWidget containing the line edit

    Note:
        This function attempts to discover the node and graph from the widget
        hierarchy. It should be called after the widget is added to a node.
        If discovery fails (widget not yet in hierarchy), context will be
        set to None and the picker will still work with workflow/system variables.
    """
    try:
        # Try to discover the owning node from the widget hierarchy
        node = None
        graph = None

        # Walk up the parent chain to find the node
        if hasattr(node_widget, "node"):
            node = node_widget.node
        elif hasattr(node_widget, "_node"):
            node = node_widget._node

        if node:
            # Get node ID
            node_id = None
            if hasattr(node, "get_property"):
                node_id = node.get_property("node_id")
            elif hasattr(node, "id") and callable(node.id):
                node_id = node.id()

            # Get graph reference
            if hasattr(node, "graph"):
                graph = node.graph

            # Set context on line edit
            if node_id and graph:
                line_edit.set_node_context(node_id, graph)
                logger.debug(f"Variable picker node context set: node_id={node_id}")
                return

        # If discovery failed, log debug message
        logger.debug("Variable picker: Node context not available (widget not yet in hierarchy)")

    except Exception as e:
        logger.debug(f"Variable picker: Could not set node context: {e}")


def update_node_context_for_widgets(node) -> None:
    """
    Update node context for all VariableAwareLineEdit widgets in a node.

    Call this after a node is fully added to the graph to enable
    upstream variable detection in all text inputs.

    Args:
        node: The visual node (VisualNode subclass) to update
    """
    try:
        # Get node ID
        node_id = None
        if hasattr(node, "get_property"):
            node_id = node.get_property("node_id")
        elif hasattr(node, "id") and callable(node.id):
            node_id = node.id()

        # Get graph
        graph = None
        if hasattr(node, "graph"):
            graph = node.graph

        if not node_id or not graph:
            return

        # Find all widgets in the node
        widgets = {}
        if hasattr(node, "widgets") and callable(node.widgets):
            widgets = node.widgets()

        for _widget_name, widget in widgets.items():
            # Check if widget has a VariableAwareLineEdit
            if hasattr(widget, "_line_edit"):
                line_edit = widget._line_edit
                if isinstance(line_edit, VariableAwareLineEdit):
                    line_edit.set_node_context(node_id, graph)

            # Also check for direct custom widget
            if hasattr(widget, "get_custom_widget"):
                custom = widget.get_custom_widget()
                if custom and hasattr(custom, "findChildren"):
                    # Find any VariableAwareLineEdit in the custom widget tree
                    for child in custom.findChildren(VariableAwareLineEdit):
                        child.set_node_context(node_id, graph)

    except Exception as e:
        logger.debug(f"Could not update node context for widgets: {e}")


# =============================================================================
# Selector Widget for Element Picking
# =============================================================================


def create_selector_widget(name: str, label: str, placeholder: str, text: str = ""):
    """
    Factory function to create a NodeSelectorWidget.

    Creates a NodeBaseWidget with selector input and element picker button.
    The picker button opens the Element Selector Dialog for visual element selection.
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget
        from PySide6 import QtWidgets
    except ImportError:
        logger.error("NodeGraphQt not available")
        return None

    # Truncate long labels to prevent widget from being too wide
    # Max 12 chars with ellipsis keeps widget compact on nodes
    MAX_LABEL_LENGTH = 12
    display_label = label
    if label and len(label) > MAX_LABEL_LENGTH:
        display_label = label[: MAX_LABEL_LENGTH - 1] + "…"

    # Create the container widget with horizontal layout
    container = QtWidgets.QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)

    # Set explicit minimum size
    # NOTE: Minimum width should be large enough to fit within node bounds
    container.setMinimumHeight(26)
    container.setMinimumWidth(180)  # Increased from 160 to fit better in nodes
    container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    # Create variable-aware line edit
    line_edit = VariableAwareLineEdit()
    line_edit.setText(text)
    line_edit.setPlaceholderText(placeholder)
    line_edit.setMinimumHeight(24)
    line_edit.setMinimumWidth(100)
    line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    # Blue-tinted styling for selectors
    line_edit.setStyleSheet(f"""
        QLineEdit {{
            background: {THEME.bg_surface};
            border: 1px solid {THEME.border};
            border-radius: {TOKENS.radius.sm}px;
            color: {THEME.info};
            padding: 2px 28px 2px 4px;
            font-family: {TOKENS.typography.mono};
        }}
        QLineEdit:focus {{
            border: 1px solid {THEME.border_focus};
        }}
    """)
    layout.addWidget(line_edit, 1)

    # Create element picker button
    picker_btn = QPushButton("...")
    picker_btn.setFixedSize(30, 24)
    picker_btn.setToolTip("Click to open Element Selector")
    # Info color for selector picking
    picker_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {THEME.info};
            border: 1px solid {THEME.border};
            border-radius: {TOKENS.radius.sm}px;
            color: #ffffff;
            font-size: {TOKENS.typography.body}px;
            font-weight: bold;
            padding: 0px;
        }}
        QPushButton:hover {{
            background-color: {THEME.primary_hover};
        }}
        QPushButton:pressed {{
            background-color: {THEME.primary_active};
        }}
    """)

    # Store references for later
    widget_ref = {"widget": None, "node": None}

    def on_picker_click():
        """Open Element Selector Dialog."""
        try:
            from casare_rpa.presentation.canvas.selectors.element_selector_dialog import (
                ElementSelectorDialog,
            )

            # Try to get browser page from node context
            browser_page = None
            node = widget_ref.get("node")

            if node:
                # Try to get browser page from execution context or controller
                if hasattr(node, "graph") and node.graph:
                    graph = node.graph
                    # Try to get from selector controller via main window
                    if hasattr(graph, "_viewer") and graph._viewer:
                        viewer = graph._viewer
                        if hasattr(viewer, "window"):
                            main_window = viewer.window()
                            if main_window and hasattr(main_window, "_selector_controller"):
                                browser_page = main_window._selector_controller.get_browser_page()

            # Determine mode
            mode = "browser" if browser_page else "desktop"

            # Create and show dialog
            dialog = ElementSelectorDialog(
                parent=None,
                mode=mode,
                browser_page=browser_page,
                initial_selector=line_edit.text(),
                target_node=node,
                property_name=name,
            )

            def on_selector_confirmed(result):
                """Handle confirmed selector."""
                if not result:
                    return

                # Special handling for image_template property
                if name == "image_template":
                    # Extract cv_template from healing_context
                    image_base64 = None
                    logger.info("ImageTemplate: Processing result for image_template property")
                    logger.info(
                        f"ImageTemplate: has healing_context={hasattr(result, 'healing_context')}"
                    )

                    if hasattr(result, "healing_context") and result.healing_context:
                        logger.info(
                            f"ImageTemplate: healing_context keys={list(result.healing_context.keys())}"
                        )
                        cv_template = result.healing_context.get("cv_template", {})
                        if cv_template:
                            logger.info(
                                f"ImageTemplate: cv_template keys={list(cv_template.keys())}"
                            )
                            image_base64 = cv_template.get("image_base64", "")
                            logger.info(
                                f"ImageTemplate: image_base64 length={len(image_base64) if image_base64 else 0}"
                            )
                        else:
                            logger.warning("ImageTemplate: cv_template is empty or missing")
                    else:
                        logger.warning(
                            f"ImageTemplate: No healing_context or empty. Value={getattr(result, 'healing_context', 'N/A')}"
                        )

                    if image_base64:
                        line_edit.setText(image_base64)
                        if widget_ref.get("widget"):
                            widget_ref["widget"].on_value_changed()
                        logger.info(f"Image template set: {len(image_base64)} chars")
                    else:
                        # Fallback: use selector_value if no cv_template
                        if hasattr(result, "selector_value"):
                            line_edit.setText(result.selector_value)
                            if widget_ref.get("widget"):
                                widget_ref["widget"].on_value_changed()
                        logger.warning(
                            "No cv_template found in result, using selector_value as fallback"
                        )
                    return

                # Standard selector handling
                if hasattr(result, "selector_value"):
                    line_edit.setText(result.selector_value)
                    # Trigger value change
                    if widget_ref.get("widget"):
                        widget_ref["widget"].on_value_changed()
                    logger.debug(f"Selector set: {result.selector_value[:50]}...")

                    # Save anchor config if present
                    _save_anchor_to_node(result, node, name)

            dialog.selector_confirmed.connect(on_selector_confirmed)
            dialog.exec()

        except ImportError as e:
            logger.warning(f"Element Selector Dialog not available: {e}")
        except Exception as e:
            logger.error(f"Failed to open Element Selector: {e}")

    picker_btn.clicked.connect(on_picker_click)
    layout.addWidget(picker_btn)

    # Create NodeBaseWidget with truncated label for compact display
    widget = NodeBaseWidget(parent=None, name=name, label=display_label)
    widget.set_custom_widget(container)
    widget_ref["widget"] = widget
    # Store original label for tooltip/reference
    widget._original_label = label

    # Force geometry update
    container.adjustSize()

    # Connect line edit changes
    line_edit.editingFinished.connect(widget.on_value_changed)
    line_edit.variable_inserted.connect(partial(_trigger_widget_value_changed, widget))

    # Store references
    widget._line_edit = line_edit
    widget._picker_btn = picker_btn

    # Override get_value and set_value
    def get_value():
        return line_edit.text()

    def set_value(value):
        line_edit.setText(str(value) if value else "")

    widget.get_value = get_value
    widget.set_value = set_value

    # Method to set node reference (called after widget is added to node)
    def set_node_ref(node):
        widget_ref["node"] = node

    widget.set_node_ref = set_node_ref

    return widget


def _save_anchor_to_node(result, node, property_name: str):
    """Save anchor configuration to node if present in result."""
    if not node or not result:
        return

    try:
        if hasattr(result, "anchor") and result.anchor:
            from casare_rpa.nodes.browser.anchor_config import NodeAnchorConfig

            anchor_data = result.anchor
            config = NodeAnchorConfig(
                enabled=True,
                selector=getattr(anchor_data, "selector", ""),
                position=getattr(anchor_data, "position", "near"),
                text=getattr(anchor_data, "text_content", ""),
                tag_name=getattr(anchor_data, "tag_name", ""),
                stability_score=getattr(anchor_data, "stability_score", 0.0),
                offset_x=getattr(anchor_data, "offset_x", 0),
                offset_y=getattr(anchor_data, "offset_y", 0),
            )
            anchor_json = config.to_json()

            # Save to node
            if hasattr(node, "set_property"):
                node.set_property("anchor_config", anchor_json)
                logger.info(f"Saved anchor config to node for {property_name}")

    except Exception as e:
        logger.warning(f"Failed to save anchor config: {e}")


class NodeSelectorWidget:
    """
    Selector widget for NodeGraphQt nodes.

    Provides a text input with an element picker button that opens
    the Element Selector Dialog for visual element selection.

    Usage in visual node:
        from casare_rpa.presentation.canvas.graph.node_widgets import NodeSelectorWidget

        def __init__(self):
            super().__init__()
            widget = NodeSelectorWidget(
                name="selector",
                label="Element Selector",
            )
            self.add_custom_widget(widget)
            widget.setParentItem(self.view)
    """

    def __new__(
        cls,
        name: str = "",
        label: str = "",
        text: str = "",
        placeholder: str = "Enter selector or click ...",
    ):
        """
        Create a new NodeSelectorWidget.

        Args:
            name: Property name for the node
            label: Label text displayed above the widget
            text: Initial text value
            placeholder: Placeholder text when empty
        """
        return create_selector_widget(name, label, placeholder, text)


# =============================================================================
# Google Integration Widgets
# =============================================================================


def _apply_combo_z_fix(widget) -> None:
    """
    Apply z-value fix to a NodeBaseWidget containing a combo box.

    When QComboBox is embedded in a QGraphicsProxyWidget, the dropdown popup
    can get clipped by other widgets. This fix raises the z-value when
    the popup is shown and restores it when hidden.

    Args:
        widget: NodeBaseWidget containing a picker with _combo attribute
    """
    try:
        picker = getattr(widget, "_picker", None)
        if not picker:
            return

        combo = getattr(picker, "_combo", None)
        if not combo:
            return

        # Store original z-value for restoration
        widget._original_z = widget.zValue() if hasattr(widget, "zValue") else 0

        # Store original methods
        original_show_popup = combo.showPopup
        original_hide_popup = combo.hidePopup

        def patched_show_popup():
            """Raise z-value when popup opens."""
            if hasattr(widget, "setZValue"):
                widget.setZValue(COMBO_RAISED_Z)
            original_show_popup()

        def patched_hide_popup():
            """Restore original z-value when popup closes."""
            try:
                original_hide_popup()
                if hasattr(widget, "setZValue") and hasattr(widget, "_original_z"):
                    widget.setZValue(widget._original_z)
            except RuntimeError:
                pass  # Widget already deleted

        # Apply patches
        combo.showPopup = patched_show_popup
        combo.hidePopup = patched_hide_popup

    except Exception as e:
        logger.debug(f"Could not apply combo z-fix: {e}")


def create_google_credential_widget(
    name: str,
    label: str,
    scopes: list = None,
):
    """
    Factory function to create a Google credential picker widget.

    Creates a dropdown showing only Google OAuth credentials with
    "Add Google Account..." option at the bottom.

    Args:
        name: Property name for the node
        label: Label text displayed above the widget
        scopes: Optional list of required scopes (for filtering)

    Returns:
        NodeBaseWidget with GoogleCredentialPicker
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget

        from casare_rpa.presentation.canvas.ui.widgets.google_credential_picker import (
            GoogleCredentialPicker,
        )
    except ImportError as e:
        logger.error(f"Google credential picker not available: {e}")
        return None

    # Create the picker widget
    picker = GoogleCredentialPicker(required_scopes=scopes or [])

    # Create NodeBaseWidget
    widget = NodeBaseWidget(parent=None, name=name, label=label)
    widget.set_custom_widget(picker)

    # Connect signals
    picker.credential_changed.connect(partial(_trigger_widget_value_changed, widget))

    # Store reference
    widget._picker = picker

    # Apply z-value fix for combo popup visibility
    _apply_combo_z_fix(widget)

    # Override get_value and set_value
    def get_value():
        return picker.get_credential_id()

    def set_value(value):
        if value:
            picker.set_credential_id(value)

    widget.get_value = get_value
    widget.set_value = set_value

    return widget


def create_google_spreadsheet_widget(
    name: str,
    label: str,
    credential_widget=None,
):
    """
    Factory function to create a Google Spreadsheet picker widget.

    Creates a cascading dropdown that loads spreadsheets when a
    credential is selected.

    Args:
        name: Property name for the node
        label: Label text displayed above the widget
        credential_widget: Optional parent credential widget for cascading

    Returns:
        NodeBaseWidget with GoogleSpreadsheetPicker
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget

        from casare_rpa.presentation.canvas.ui.widgets.google_pickers import (
            GoogleSpreadsheetPicker,
        )
    except ImportError as e:
        logger.error(f"Google spreadsheet picker not available: {e}")
        return None

    # Create the picker widget
    picker = GoogleSpreadsheetPicker()

    # Connect to parent credential widget if provided
    if credential_widget and hasattr(credential_widget, "_picker"):
        cred_picker = credential_widget._picker
        cred_picker.credential_changed.connect(picker.set_parent_value)
        # Initialize with current credential if already selected
        current_cred = cred_picker.get_credential_id()
        if current_cred:
            picker.set_parent_value(current_cred)

    # Create NodeBaseWidget
    widget = NodeBaseWidget(parent=None, name=name, label=label)
    widget.set_custom_widget(picker)

    # Connect signals
    picker.selection_changed.connect(partial(_trigger_widget_value_changed, widget))

    # Store reference
    widget._picker = picker

    # Apply z-value fix for combo popup visibility
    _apply_combo_z_fix(widget)

    # Override get_value and set_value
    def get_value():
        return picker.get_selected_id()

    def set_value(value):
        if value:
            picker.set_selected_id(value)

    widget.get_value = get_value
    widget.set_value = set_value

    return widget


def create_google_sheet_widget(
    name: str,
    label: str,
    spreadsheet_widget=None,
    credential_widget=None,
):
    """
    Factory function to create a Google Sheet picker widget.

    Creates a cascading dropdown that loads sheets when a
    spreadsheet is selected.

    Args:
        name: Property name for the node
        label: Label text displayed above the widget
        spreadsheet_widget: Optional parent spreadsheet widget for cascading
        credential_widget: Optional credential widget for authentication

    Returns:
        NodeBaseWidget with GoogleSheetPicker
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget

        from casare_rpa.presentation.canvas.ui.widgets.google_pickers import (
            GoogleSheetPicker,
        )
    except ImportError as e:
        logger.error(f"Google sheet picker not available: {e}")
        return None

    # Create the picker widget
    picker = GoogleSheetPicker()

    # Connect to parent credential widget if provided
    if credential_widget and hasattr(credential_widget, "_picker"):
        credential_widget._picker.credential_changed.connect(picker.set_credential_id)

    # Connect to parent spreadsheet widget if provided
    if spreadsheet_widget and hasattr(spreadsheet_widget, "_picker"):
        spreadsheet_widget._picker.selection_changed.connect(
            partial(_set_parent_value_from_picker, picker, spreadsheet_widget._picker)
        )

    # Create NodeBaseWidget
    widget = NodeBaseWidget(parent=None, name=name, label=label)
    widget.set_custom_widget(picker)

    # Connect signals
    picker.selection_changed.connect(partial(_trigger_widget_value_changed, widget))

    # Store reference
    widget._picker = picker

    # Apply z-value fix for combo popup visibility
    _apply_combo_z_fix(widget)

    # Override get_value and set_value
    def get_value():
        return picker.get_selected_id()

    def set_value(value):
        if value:
            picker.set_selected_id(value)

    widget.get_value = get_value
    widget.set_value = set_value

    return widget


def create_google_drive_file_widget(
    name: str,
    label: str,
    credential_widget=None,
    mime_types: list = None,
    folder_id: str = None,
):
    """
    Factory function to create a Google Drive file picker widget.

    Args:
        name: Property name for the node
        label: Label text displayed above the widget
        credential_widget: Optional parent credential widget for cascading
        mime_types: Optional list of MIME types to filter (first one used)
        folder_id: Optional folder ID to restrict search

    Returns:
        NodeBaseWidget with GoogleDriveFilePicker
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget

        from casare_rpa.presentation.canvas.ui.widgets.google_pickers import (
            GoogleDriveFilePicker,
        )
    except ImportError as e:
        logger.error(f"Google Drive file picker not available: {e}")
        return None

    # Create the picker widget (GoogleDriveFilePicker takes mime_type singular)
    mime_type = mime_types[0] if mime_types else None
    picker = GoogleDriveFilePicker(mime_type=mime_type, folder_id=folder_id)

    # Connect to parent credential widget if provided
    if credential_widget and hasattr(credential_widget, "_picker"):
        cred_picker = credential_widget._picker
        cred_picker.credential_changed.connect(picker.set_parent_value)
        # Initialize with current credential if already selected
        current_cred = cred_picker.get_credential_id()
        if current_cred:
            picker.set_parent_value(current_cred)

    # Create NodeBaseWidget
    widget = NodeBaseWidget(parent=None, name=name, label=label)
    widget.set_custom_widget(picker)

    # Connect signals
    picker.selection_changed.connect(partial(_trigger_widget_value_changed, widget))

    # Store reference
    widget._picker = picker

    # Apply z-value fix for combo popup visibility
    _apply_combo_z_fix(widget)

    # Override get_value and set_value
    def get_value():
        return picker.get_selected_id()

    def set_value(value):
        if value:
            picker.set_selected_id(value)

    widget.get_value = get_value
    widget.set_value = set_value

    return widget


def create_google_drive_folder_widget(
    name: str,
    label: str,
    credential_widget=None,
    enhanced: bool = False,
):
    """
    Factory function to create a Google Drive folder picker widget.

    Args:
        name: Property name for the node
        label: Label text displayed above the widget
        credential_widget: Optional parent credential widget for cascading
        enhanced: If True, use the enhanced folder navigator with
                  browse/search/manual ID modes. If False (default),
                  use simple dropdown picker.

    Returns:
        NodeBaseWidget with GoogleDriveFolderPicker or GoogleDriveFolderNavigator
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget
    except ImportError as e:
        logger.error(f"NodeGraphQt not available: {e}")
        return None

    if enhanced:
        # Use enhanced navigator with browse/search/manual modes
        return _create_enhanced_folder_widget(name, label, credential_widget)
    else:
        # Use simple dropdown picker (original behavior)
        return _create_simple_folder_widget(name, label, credential_widget)


def _create_simple_folder_widget(
    name: str,
    label: str,
    credential_widget=None,
):
    """Create simple folder dropdown widget (original implementation)."""
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget

        from casare_rpa.presentation.canvas.ui.widgets.google_pickers import (
            GoogleDriveFolderPicker,
        )
    except ImportError as e:
        logger.error(f"Google Drive folder picker not available: {e}")
        return None

    # Create the picker widget
    picker = GoogleDriveFolderPicker()

    # Connect to parent credential widget if provided
    if credential_widget and hasattr(credential_widget, "_picker"):
        cred_picker = credential_widget._picker
        cred_picker.credential_changed.connect(picker.set_parent_value)
        # Initialize with current credential if already selected
        current_cred = cred_picker.get_credential_id()
        if current_cred:
            picker.set_parent_value(current_cred)

    # Create NodeBaseWidget
    widget = NodeBaseWidget(parent=None, name=name, label=label)
    widget.set_custom_widget(picker)

    # Connect signals
    picker.selection_changed.connect(partial(_trigger_widget_value_changed, widget))

    # Store reference
    widget._picker = picker

    # Apply z-value fix for combo popup visibility
    _apply_combo_z_fix(widget)

    # Override get_value and set_value
    def get_value():
        return picker.get_selected_id()

    def set_value(value):
        if value:
            picker.set_selected_id(value)

    widget.get_value = get_value
    widget.set_value = set_value

    return widget


def _create_enhanced_folder_widget(
    name: str,
    label: str,
    credential_widget=None,
):
    """
    Create enhanced folder navigator widget with browse/search/manual ID modes.

    Features:
    - Browse mode: Navigate folder hierarchy with breadcrumb
    - Search mode: Search folders across Drive
    - Manual ID mode: Paste folder ID from Google Drive URL
    """
    try:
        from NodeGraphQt.widgets.node_widgets import NodeBaseWidget

        from casare_rpa.presentation.canvas.ui.widgets.google_folder_navigator import (
            GoogleDriveFolderNavigator,
        )
    except ImportError as e:
        logger.error(f"Google Drive folder navigator not available: {e}")
        # Fall back to simple widget
        return _create_simple_folder_widget(name, label, credential_widget)

    # Create the navigator widget
    navigator = GoogleDriveFolderNavigator(show_mode_buttons=True)

    # Connect to parent credential widget if provided
    if credential_widget and hasattr(credential_widget, "_picker"):
        cred_picker = credential_widget._picker
        cred_picker.credential_changed.connect(navigator.set_credential_id)
        # Initialize with current credential if already selected
        current_cred = cred_picker.get_credential_id()
        if current_cred:
            navigator.set_credential_id(current_cred)

    # Create NodeBaseWidget
    widget = NodeBaseWidget(parent=None, name=name, label=label)
    widget.set_custom_widget(navigator)

    # Connect signals
    navigator.folder_selected.connect(partial(_trigger_widget_value_changed, widget))

    # Store reference
    widget._navigator = navigator
    widget._picker = navigator  # For compatibility with z-fix

    # Override get_value and set_value
    def get_value():
        return navigator.get_folder_id()

    def set_value(value):
        if value:
            navigator.set_folder_id(value)

    widget.get_value = get_value
    widget.set_value = set_value

    return widget


class NodeGoogleCredentialWidget:
    """
    Google credential picker widget for NodeGraphQt nodes.

    Shows a dropdown with connected Google accounts and
    "Add Google Account..." option to add new ones.

    Usage:
        widget = NodeGoogleCredentialWidget(name="credential", label="Google Account")
        self.add_custom_widget(widget)
    """

    def __new__(
        cls,
        name: str = "",
        label: str = "",
        scopes: list = None,
    ):
        return create_google_credential_widget(name, label, scopes)


class NodeGoogleSpreadsheetWidget:
    """
    Google Spreadsheet picker widget for NodeGraphQt nodes.

    Cascading dropdown that loads spreadsheets from Google Drive.

    Usage:
        cred_widget = NodeGoogleCredentialWidget(...)
        sheet_widget = NodeGoogleSpreadsheetWidget(
            name="spreadsheet",
            label="Spreadsheet",
            credential_widget=cred_widget,
        )
    """

    def __new__(
        cls,
        name: str = "",
        label: str = "",
        credential_widget=None,
    ):
        return create_google_spreadsheet_widget(name, label, credential_widget)


class NodeGoogleSheetWidget:
    """
    Google Sheet picker widget for NodeGraphQt nodes.

    Cascading dropdown that loads sheet tabs from a spreadsheet.
    """

    def __new__(
        cls,
        name: str = "",
        label: str = "",
        spreadsheet_widget=None,
        credential_widget=None,
    ):
        return create_google_sheet_widget(name, label, spreadsheet_widget, credential_widget)


class NodeGoogleDriveFileWidget:
    """
    Google Drive file picker widget for NodeGraphQt nodes.
    """

    def __new__(
        cls,
        name: str = "",
        label: str = "",
        credential_widget=None,
        mime_types: list = None,
        folder_id: str = None,
    ):
        return create_google_drive_file_widget(
            name, label, credential_widget, mime_types, folder_id
        )


class NodeGoogleDriveFolderWidget:
    """
    Google Drive folder picker widget for NodeGraphQt nodes.

    With enhanced=False (default): Simple dropdown with folder list.
    With enhanced=True: Full navigator with browse/search/manual ID modes.

    Usage:
        # Simple dropdown
        widget = NodeGoogleDriveFolderWidget(
            name="folder_id",
            label="Destination Folder",
            credential_widget=cred_widget,
        )

        # Enhanced navigator
        widget = NodeGoogleDriveFolderWidget(
            name="folder_id",
            label="Destination Folder",
            credential_widget=cred_widget,
            enhanced=True,
        )
    """

    def __new__(
        cls,
        name: str = "",
        label: str = "",
        credential_widget=None,
        enhanced: bool = False,
    ):
        return create_google_drive_folder_widget(name, label, credential_widget, enhanced)


class NodeTextWidget:
    """
    Text input widget for NodeGraphQt nodes.

    Provides a variable-aware text input (with {x} button).

    Usage:
        widget = NodeTextWidget(name="my_prop", label="Label")
        self.add_custom_widget(widget)
    """

    def __new__(
        cls,
        name: str = "",
        label: str = "",
        text: str = "",
        placeholder_text: str = "",
    ):
        return create_variable_text_widget(name, label, text, placeholder_text)

