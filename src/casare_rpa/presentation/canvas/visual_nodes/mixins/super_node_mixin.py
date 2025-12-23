"""
Super Node Mixin for CasareRPA.

Provides dynamic port and widget management for Super Nodes that
change their input/output ports and visible properties based on action selection.

Usage:
    class VisualFileSystemSuperNode(SuperNodeMixin, VisualNode):
        DYNAMIC_PORT_SCHEMA = FILE_SYSTEM_PORT_SCHEMA

        def setup_widgets(self):
            super().setup_widgets()
            self._setup_action_listener()
"""

from typing import TYPE_CHECKING, Any, Dict, Optional

from loguru import logger
from PySide6.QtCore import QTimer, Slot

if TYPE_CHECKING:
    from casare_rpa.domain.schemas import NodeSchema
    from casare_rpa.domain.value_objects.dynamic_port_config import (
        ActionPortConfig,
        DynamicPortSchema,
    )


class SuperNodeMixin:
    """
    Mixin for visual nodes that support dynamic port and widget management.

    This mixin provides:
    - Automatic port refresh when action dropdown changes
    - Dynamic widget visibility (removes/adds widgets based on display_when)
    - Safe Qt signal blocking during port manipulation (prevents segfaults)
    - Port configuration from DynamicPortSchema

    Class Attributes:
        DYNAMIC_PORT_SCHEMA: DynamicPortSchema mapping actions to port configs

    Instance Attributes:
        _hidden_widgets: Dict storing widgets that are currently hidden
        _widget_values: Dict storing values for hidden widgets

    Example:
        class VisualFileSystemSuperNode(SuperNodeMixin, VisualNode):
            DYNAMIC_PORT_SCHEMA = FILE_SYSTEM_PORT_SCHEMA

            def setup_widgets(self):
                super().setup_widgets()
                self._setup_action_listener()
    """

    DYNAMIC_PORT_SCHEMA: Optional["DynamicPortSchema"] = None

    def set_casare_node(self, node) -> None:
        """
        Override to trigger widget filtering after casare node is linked.

        This is needed because widgets are created in set_casare_node() via
        _auto_create_widgets_from_schema(), but the initial filter may have
        already run (and found no widgets to filter).
        """
        # Call parent implementation (creates widgets from schema)
        super().set_casare_node(node)

        # NOTE: Do NOT call _apply_ports_for_action() here!
        # This method is called during __init__ BEFORE setup_ports() runs,
        # so ports would be created too early and then setup_ports() would fail.
        #
        # Port refresh is handled by:
        # 1. workflow_deserializer._apply_config() after action config is applied
        # 2. _on_action_changed() when user changes the action dropdown

        # Defer widget filtering only (can happen after connections)
        QTimer.singleShot(0, self._apply_initial_widget_filter)

    def _apply_ports_for_action(self) -> None:
        """Create ports for the current action SYNCHRONOUSLY."""
        if not self.DYNAMIC_PORT_SCHEMA:
            return

        action = self.get_current_action()
        if not action:
            return

        config = self.DYNAMIC_PORT_SCHEMA.get_config(action)
        if not config:
            return

        # Clear existing data ports and create new ones
        self._clear_dynamic_ports()
        self._create_ports_from_config(config)

        # Apply port colors
        if hasattr(self, "_configure_port_colors"):
            self._configure_port_colors()

        logger.debug(f"SuperNodeMixin: Created ports synchronously for action '{action}'")

    def _apply_initial_widget_filter(self) -> None:
        """Apply widget filter after casare node is set.

        Note: Ports are created synchronously in _apply_ports_for_action(),
        so this method only handles widget filtering.
        """
        if getattr(self, "_super_node_widgets_filtered", False):
            return  # Already filtered

        action = self.get_current_action()
        if action:
            logger.debug(f"SuperNodeMixin: Applying widget filter for action '{action}'")

            # Sync the combo widget to match the config action value
            # This is needed because the combo may still have the default value
            self._sync_action_combo_to_config(action)

            # NOTE: Port creation is now done synchronously in _apply_ports_for_action()
            # called from set_casare_node(). We only filter widgets here.

            self._filter_widgets_for_action(action)
            self._super_node_widgets_filtered = True

    def _sync_action_combo_to_config(self, action: str) -> None:
        """
        Sync the action combo widget to match the config value.

        This ensures the combo displays the correct action after loading
        a workflow where the action differs from the default.

        Args:
            action: The action value from config to set
        """
        try:
            action_widget = self.get_widget("action")
            if not action_widget:
                return

            combo = action_widget.get_custom_widget()
            if not combo or not hasattr(combo, "currentText"):
                return

            # Only update if different (prevents redundant signal emissions)
            if combo.currentText() != action:
                # Find the index of the action in the combo
                index = combo.findText(action)
                if index >= 0:
                    # Block signals to prevent triggering _on_action_changed
                    combo.blockSignals(True)
                    combo.setCurrentIndex(index)
                    combo.blockSignals(False)
                    logger.debug(f"SuperNodeMixin: Synced combo to action '{action}'")
        except Exception as e:
            logger.debug(f"SuperNodeMixin: Error syncing combo: {e}")

    def _setup_action_listener(self) -> None:
        """
        Connect action dropdown change to port and widget refresh.

        NOTE: This method is called from setup_widgets() which runs BEFORE
        _auto_create_widgets_from_schema() creates the action widget.
        We use QTimer.singleShot(0, ...) to defer until after __init__ completes.
        """
        # Initialize storage for hidden widgets and their values
        if not hasattr(self, "_hidden_widgets"):
            self._hidden_widgets: dict[str, Any] = {}
        if not hasattr(self, "_widget_values"):
            self._widget_values: dict[str, Any] = {}

        # Ensure super nodes start in expanded state (not collapsed)
        # This prevents all non-essential widgets from being hidden on init
        if not hasattr(self, "_collapsed"):
            self._collapsed = False

        # Defer connection until after widgets are created
        QTimer.singleShot(0, self._connect_action_listener)

    def _connect_action_listener(self) -> None:
        """
        Actually connect the action listener (called after widgets exist).

        Finds the 'action' widget and connects its change signal
        to the port refresh handler.
        """
        try:
            action_widget = self.get_widget("action")
            if not action_widget:
                logger.warning("SuperNodeMixin: No 'action' widget found after defer")
                return

            # Get the underlying QComboBox from the widget
            combo = action_widget.get_custom_widget()
            if combo and hasattr(combo, "currentTextChanged"):
                # Direct method connection - @Slot decorator handles the signature
                combo.currentTextChanged.connect(self._on_action_changed)
                logger.debug("SuperNodeMixin: Connected action listener")

                # Apply initial widget filtering based on default action
                current_action = combo.currentText()
                if current_action:
                    self._filter_widgets_for_action(current_action)
        except Exception as e:
            logger.error(f"SuperNodeMixin: Failed to setup action listener: {e}")

    @Slot(str)
    def _on_action_changed(self, action: str) -> None:
        """
        Handle action dropdown change - refresh ports and filter widgets.

        CRITICAL: Uses QSignalBlocker to prevent Qt segfaults during
        port manipulation.

        Args:
            action: The newly selected action string
        """
        if not self.DYNAMIC_PORT_SCHEMA:
            logger.warning("SuperNodeMixin: No DYNAMIC_PORT_SCHEMA defined")
            return

        config = self.DYNAMIC_PORT_SCHEMA.get_config(action)
        if not config:
            logger.warning(f"SuperNodeMixin: No port config for action: {action}")
            return

        logger.debug(f"SuperNodeMixin: Refreshing for action: {action}")

        try:
            # Clear and recreate ports
            # Note: QSignalBlocker requires QObject, but visual nodes aren't QObjects
            # The view is a QGraphicsItem, so we skip signal blocking here
            self._clear_dynamic_ports()
            self._create_ports_from_config(config)

            # Re-apply port colors after creating new ports
            if hasattr(self, "_configure_port_colors"):
                self._configure_port_colors()

            # Filter widgets - remove non-matching, restore matching
            self._filter_widgets_for_action(action)

            # Update node geometry and layout
            if hasattr(self, "view") and self.view is not None:
                if hasattr(self.view, "post_init"):
                    self.view.post_init()

            logger.debug(f"SuperNodeMixin: Refreshed for action: {action}")

        except Exception as e:
            logger.error(f"SuperNodeMixin: Error refreshing: {e}")

    def _filter_widgets_for_action(self, action: str) -> None:
        """
        Filter widgets based on display_when conditions.

        This method physically removes widgets that don't match the current action
        and restores widgets that do match. This is more robust than setVisible()
        because NodeGraphQt's layout system doesn't respect visibility flags.

        Args:
            action: The currently selected action
        """
        # Try to get schema from casare_node first
        schema: NodeSchema | None = None

        if hasattr(self, "_casare_node") and self._casare_node is not None:
            schema = getattr(self._casare_node.__class__, "__node_schema__", None)

        # Fallback: try to get schema from the node class directly via CASARE_NODE_CLASS
        if schema is None:
            casare_class_name = getattr(self, "CASARE_NODE_CLASS", None)
            if casare_class_name:
                try:
                    from casare_rpa.utils.workflow.workflow_loader import get_node_class

                    node_class = get_node_class(casare_class_name)
                    if node_class:
                        schema = getattr(node_class, "__node_schema__", None)
                except Exception as e:
                    logger.debug(f"Could not get schema from CASARE_NODE_CLASS: {e}")

        # Second fallback: try to get schema from get_node_class method
        if schema is None and hasattr(self, "get_node_class"):
            try:
                node_class = self.get_node_class()
                if node_class:
                    schema = getattr(node_class, "__node_schema__", None)
            except Exception as e:
                logger.debug(f"Could not get schema from get_node_class(): {e}")

        if not schema:
            logger.warning("SuperNodeMixin: No schema found for filtering widgets")
            return

        logger.debug(f"SuperNodeMixin: Filtering widgets for action '{action}'")

        # Ensure storage dicts exist
        if not hasattr(self, "_hidden_widgets"):
            self._hidden_widgets = {}
        if not hasattr(self, "_widget_values"):
            self._widget_values = {}

        # Ensure _collapsed is initialized (False by default for super nodes)
        if not hasattr(self, "_collapsed"):
            self._collapsed = False

        # Build current config for display_when evaluation
        current_config = {"action": action}

        # Get the view's internal widget dict (this is where widgets are stored)
        if not hasattr(self, "view") or self.view is None:
            return

        view_widgets = getattr(self.view, "_widgets", None)
        if view_widgets is None:
            logger.warning("SuperNodeMixin: view._widgets is None")
            return

        # Pre-compute which properties should be visible for this action
        visible_props = ["action"]  # action is always visible
        for p in schema.properties:
            if p.name != "action" and schema.should_display(p.name, current_config):
                visible_props.append(p.name)

        for prop_def in schema.properties:
            prop_name = prop_def.name

            # Skip the action property itself (always visible)
            if prop_name == "action":
                continue

            # Check if widget should be visible for this action
            should_show_base = schema.should_display(prop_name, current_config)
            should_show = should_show_base

            # NOTE: For SuperNodes, we do NOT hide action-visible widgets due to collapse state.
            # If a widget is supposed to be visible for this action, it stays visible.
            # The collapse logic was causing issues where essential action widgets were hidden.

            widget_in_view = prop_name in view_widgets
            widget_in_hidden = prop_name in self._hidden_widgets

            if should_show and widget_in_hidden:
                # Restore widget from hidden storage
                self._restore_widget(prop_name)
            elif not should_show and widget_in_view:
                # Hide widget by removing from view
                self._hide_widget(prop_name)

        # Trigger layout recalculation
        if hasattr(self.view, "post_init"):
            self.view.post_init()

    def _hide_widget(self, prop_name: str) -> None:
        """
        Hide a widget by removing it from the node's widget collection.

        The widget is stored in _hidden_widgets so it can be restored later.
        Widget values are preserved in _widget_values.

        Args:
            prop_name: Name of the property/widget to hide
        """
        try:
            view_widgets = getattr(self.view, "_widgets", None)
            if view_widgets is None or prop_name not in view_widgets:
                return

            widget = view_widgets[prop_name]

            # Save current value before hiding
            try:
                value = self.get_property(prop_name)
                self._widget_values[prop_name] = value

                # CRITICAL: Also sync to casare_node.config for execution!
                # Hidden widgets still need their values available during execution.
                if hasattr(self, "_casare_node") and self._casare_node is not None:
                    if hasattr(self._casare_node, "config"):
                        self._casare_node.config[prop_name] = value
                        logger.debug(f"  Synced hidden widget value to config: {prop_name}={value}")
            except Exception:
                pass

            # Sync widget value to prevent data loss
            if hasattr(widget, "on_value_changed"):
                try:
                    widget.on_value_changed()
                except Exception:
                    pass

            # Remove from view's widget collection
            del view_widgets[prop_name]

            # Hide the widget visually (belt and suspenders)
            widget.setVisible(False)

            # Store in hidden collection
            self._hidden_widgets[prop_name] = widget

            logger.debug(f"SuperNodeMixin: Hidden widget '{prop_name}'")

        except Exception as e:
            logger.debug(f"SuperNodeMixin: Error hiding widget '{prop_name}': {e}")

    def _restore_widget(self, prop_name: str) -> None:
        """
        Restore a previously hidden widget.

        Args:
            prop_name: Name of the property/widget to restore
        """
        try:
            if prop_name not in self._hidden_widgets:
                return

            view_widgets = getattr(self.view, "_widgets", None)
            if view_widgets is None:
                return

            widget = self._hidden_widgets.pop(prop_name)

            # Re-add to view's widget collection
            view_widgets[prop_name] = widget

            # Make visible
            widget.setVisible(True)

            # Restore saved value
            if prop_name in self._widget_values:
                try:
                    self.set_property(prop_name, self._widget_values[prop_name])
                except Exception:
                    pass

            logger.debug(f"SuperNodeMixin: Restored widget '{prop_name}'")

        except Exception as e:
            logger.debug(f"SuperNodeMixin: Error restoring widget '{prop_name}': {e}")

    def sync_hidden_widget_values(self) -> None:
        """
        Sync all hidden widget values to casare_node.config.

        This is a safety net to ensure hidden widget values are available
        during execution. Called before workflow execution starts.
        """
        if not hasattr(self, "_casare_node") or self._casare_node is None:
            return
        if not hasattr(self._casare_node, "config"):
            return

        for prop_name, value in self._widget_values.items():
            if value is not None:
                self._casare_node.config[prop_name] = value
                logger.debug(f"SuperNodeMixin: Synced hidden value {prop_name}={value}")

    def _clear_dynamic_ports(self) -> None:
        """
        Remove all non-exec ports.

        Preserves exec_in and exec_out ports, removes all data ports
        to prepare for new port configuration.
        """
        # Get lists of ports to remove (exclude exec ports)
        # Must copy to list since we're modifying during iteration
        input_ports = list(self.input_ports())
        output_ports = list(self.output_ports())

        logger.debug(
            f"Clearing ports. Inputs: {[p.name() for p in input_ports]}, Outputs: {[p.name() for p in output_ports]}"
        )

        for port in input_ports:
            port_name = port.name()
            if port_name != "exec_in":
                try:
                    # delete_input expects the port OBJECT, not the name
                    self.delete_input(port)
                    logger.debug(f"  Deleted input port: {port_name}")
                except Exception as e:
                    logger.warning(f"Could not delete input port {port_name}: {e}")

        for port in output_ports:
            port_name = port.name()
            if port_name != "exec_out":
                try:
                    # delete_output expects the port OBJECT, not the name
                    self.delete_output(port)
                    logger.debug(f"  Deleted output port: {port_name}")
                except Exception as e:
                    logger.warning(f"Could not delete output port {port_name}: {e}")

    def _create_ports_from_config(self, config: "ActionPortConfig") -> None:
        """
        Create ports based on action configuration.

        Args:
            config: ActionPortConfig containing input and output port definitions

        Note: Exec ports (exec_in, exec_out) are created by setup_ports() and
        should NOT be touched here. We only create data ports.
        """
        # Create input data ports (exec_in already exists from setup_ports)
        for port_def in config.inputs:
            # Skip if port already exists
            if self.get_input(port_def.name):
                continue
            try:
                self.add_typed_input(port_def.name, port_def.data_type)
            except Exception as e:
                logger.debug(f"Could not create input port {port_def.name}: {e}")

        # Create output data ports (exec_out already exists from setup_ports)
        for port_def in config.outputs:
            # Skip if port already exists
            if self.get_output(port_def.name):
                continue
            try:
                self.add_typed_output(port_def.name, port_def.data_type)
            except Exception as e:
                logger.debug(f"Could not create output port {port_def.name}: {e}")

    def get_current_action(self) -> str | None:
        """
        Get the currently selected action.

        Priority order:
        1. casare_node.config["action"] (authoritative during workflow load)
        2. Combo widget text (interactive selection)

        Returns:
            Current action string or None if not available
        """
        # First, check casare_node.config (authoritative during workflow loading)
        # This is needed because the combo widget may still have the default value
        # when the node is first loaded from a workflow file
        if hasattr(self, "_casare_node") and self._casare_node is not None:
            config_action = getattr(self._casare_node, "config", {}).get("action")
            if config_action:
                return config_action

        # Fallback to combo widget (for interactive use)
        try:
            action_widget = self.get_widget("action")
            if action_widget:
                combo = action_widget.get_custom_widget()
                if combo and hasattr(combo, "currentText"):
                    return combo.currentText()
        except Exception:
            pass
        return None

    def get_port_config_for_action(self, action: str) -> Optional["ActionPortConfig"]:
        """
        Get port configuration for a specific action.

        Args:
            action: Action name to look up

        Returns:
            ActionPortConfig or None if not found
        """
        if self.DYNAMIC_PORT_SCHEMA:
            return self.DYNAMIC_PORT_SCHEMA.get_config(action)
        return None

    # Keep old method name for backward compatibility
    def _update_widget_visibility_for_action(self, action: str) -> None:
        """Alias for _filter_widgets_for_action for backward compatibility."""
        self._filter_widgets_for_action(action)
