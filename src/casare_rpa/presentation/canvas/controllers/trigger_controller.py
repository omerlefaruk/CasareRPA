"""
Trigger controller for workflow trigger management.

Handles all trigger-related operations:
- Add/edit/delete triggers
- Toggle trigger enabled state
- Run triggers manually
- Trigger state management
"""

from typing import TYPE_CHECKING, Optional, List, Dict, Any
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QMessageBox
from loguru import logger

from .base_controller import BaseController

if TYPE_CHECKING:
    from ....canvas.main_window import MainWindow


class TriggerController(BaseController):
    """
    Manages workflow trigger operations.

    Single Responsibility: Trigger creation, management, and execution.

    This controller handles all trigger-related UI interactions from MainWindow,
    delegating to the BottomPanelDock's TriggersTab for display and providing
    dialog management for trigger configuration.

    Signals:
        trigger_added: Emitted when a trigger is created (dict: trigger_config)
        trigger_updated: Emitted when a trigger is modified (dict: trigger_config)
        trigger_deleted: Emitted when a trigger is deleted (str: trigger_id)
        trigger_toggled: Emitted when trigger state changes (str: trigger_id, bool: enabled)
        trigger_run_requested: Emitted when user wants to run a trigger (str: trigger_id)
        triggers_changed: Emitted when triggers list is modified
    """

    # Signals
    trigger_added = Signal(dict)  # trigger_config
    trigger_updated = Signal(dict)  # trigger_config
    trigger_deleted = Signal(str)  # trigger_id
    trigger_toggled = Signal(str, bool)  # trigger_id, enabled
    trigger_run_requested = Signal(str)  # trigger_id
    triggers_changed = Signal()

    def __init__(self, main_window: "MainWindow"):
        """
        Initialize trigger controller.

        Args:
            main_window: Reference to main window for accessing shared components
        """
        super().__init__(main_window)
        self._triggers: List[Dict[str, Any]] = []

    def initialize(self) -> None:
        """Initialize controller resources and connections.

        Note: Signal connections are handled by MainWindow._create_bottom_panel()
        which connects bottom panel signals to MainWindow methods, which then
        delegate to this controller. This avoids double-handling of signals.
        """
        super().initialize()
        logger.info("TriggerController initialized")

    def cleanup(self) -> None:
        """Clean up controller resources."""
        super().cleanup()
        self._triggers.clear()
        logger.info("TriggerController cleanup")

    def add_trigger(self) -> None:
        """
        Open dialog to add a new trigger.

        Shows trigger type selector dialog, then configuration dialog.
        On success, adds the trigger to the workflow and emits trigger_added.
        """
        try:
            from ....canvas.dialogs import (
                TriggerTypeSelectorDialog,
                TriggerConfigDialog,
            )

            # Show trigger type selector
            type_dialog = TriggerTypeSelectorDialog(self.main_window)
            if type_dialog.exec() != QDialog.DialogCode.Accepted:
                logger.debug("Trigger type selection cancelled")
                return

            trigger_type = type_dialog.get_selected_type()
            if not trigger_type:
                logger.warning("No trigger type selected")
                return

            # Show trigger configuration dialog
            config_dialog = TriggerConfigDialog(trigger_type, parent=self.main_window)
            if config_dialog.exec() != QDialog.DialogCode.Accepted:
                logger.debug("Trigger configuration cancelled")
                return

            # Get the configuration and add to triggers list
            trigger_config = config_dialog.get_config()
            self._add_trigger_to_panel(trigger_config)
            self.main_window.set_modified(True)

            # Emit signals
            self.trigger_added.emit(trigger_config)
            self.triggers_changed.emit()

            trigger_name = trigger_config.get("name", "Unnamed")
            logger.info(f"Added trigger: {trigger_name}")
            self.main_window.show_status(f"Trigger added: {trigger_name}", 3000)

        except ImportError as e:
            logger.error(f"Failed to import trigger dialog module: {e}")
            self._show_trigger_error(f"Trigger dialog not available: {e}")
        except Exception as e:
            logger.error(f"Failed to add trigger: {e}")
            self._show_trigger_error(str(e))

    def edit_trigger(self, trigger_config: Dict[str, Any]) -> None:
        """
        Open dialog to edit an existing trigger.

        Args:
            trigger_config: The trigger configuration to edit
        """
        try:
            from ....canvas.dialogs import TriggerConfigDialog
            from ....triggers.base import TriggerType

            trigger_type_str = trigger_config.get("type", "manual")
            try:
                trigger_type = TriggerType(trigger_type_str)
            except ValueError:
                logger.error(f"Unknown trigger type: {trigger_type_str}")
                self._show_trigger_error(f"Unknown trigger type: {trigger_type_str}")
                return

            # Show trigger configuration dialog with existing config
            config_dialog = TriggerConfigDialog(
                trigger_type, trigger_config, parent=self.main_window
            )
            if config_dialog.exec() != QDialog.DialogCode.Accepted:
                logger.debug("Trigger edit cancelled")
                return

            # Get updated configuration
            updated_config = config_dialog.get_config()
            self._update_trigger_in_panel(updated_config)
            self.main_window.set_modified(True)

            # Emit signals
            self.trigger_updated.emit(updated_config)
            self.triggers_changed.emit()

            trigger_name = updated_config.get("name", "Unnamed")
            logger.info(f"Updated trigger: {trigger_name}")
            self.main_window.show_status(f"Trigger updated: {trigger_name}", 3000)

        except ImportError as e:
            logger.error(f"Failed to import trigger dialog module: {e}")
            self._show_trigger_error(f"Trigger dialog not available: {e}")
        except Exception as e:
            logger.error(f"Failed to edit trigger: {e}")
            self._show_trigger_error(str(e))

    def delete_trigger(self, trigger_id: str) -> bool:
        """
        Delete a trigger after confirmation.

        Args:
            trigger_id: ID of the trigger to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        # Find trigger to get name for confirmation message
        trigger_name = self._get_trigger_name(trigger_id)

        # Confirm deletion
        reply = QMessageBox.question(
            self.main_window,
            "Delete Trigger",
            f"Are you sure you want to delete the trigger '{trigger_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            logger.debug(f"Trigger deletion cancelled: {trigger_id}")
            return False

        # Remove from panel
        self._remove_trigger_from_panel(trigger_id)
        self.main_window.set_modified(True)

        # Update internal list
        self._triggers = [t for t in self._triggers if t.get("id") != trigger_id]

        # Emit signals
        self.trigger_deleted.emit(trigger_id)
        self.triggers_changed.emit()

        logger.info(f"Deleted trigger: {trigger_id} ({trigger_name})")
        self.main_window.show_status(f"Trigger deleted: {trigger_name}", 3000)

        return True

    def toggle_trigger(self, trigger_id: str, enabled: bool) -> None:
        """
        Toggle a trigger's enabled state.

        Args:
            trigger_id: ID of the trigger to toggle
            enabled: New enabled state
        """
        bottom_panel = self.main_window.get_bottom_panel()
        if not bottom_panel:
            logger.error("Bottom panel not available for trigger toggle")
            return

        triggers = bottom_panel.get_triggers()
        for trigger in triggers:
            if trigger.get("id") == trigger_id:
                trigger["enabled"] = enabled
                bottom_panel.update_trigger(trigger)
                self.main_window.set_modified(True)

                # Emit signals
                self.trigger_toggled.emit(trigger_id, enabled)
                self.triggers_changed.emit()

                state = "enabled" if enabled else "disabled"
                trigger_name = trigger.get("name", "Unnamed")
                logger.info(f"Trigger {trigger_id} ({trigger_name}) {state}")
                self.main_window.show_status(f"Trigger {state}: {trigger_name}", 3000)
                return

        logger.warning(f"Trigger not found for toggle: {trigger_id}")

    def run_trigger(self, trigger_id: str) -> None:
        """
        Manually run a trigger.

        This requests immediate execution of the workflow associated with the trigger.

        Args:
            trigger_id: ID of the trigger to run
        """
        trigger_name = self._get_trigger_name(trigger_id)
        logger.info(f"Manual trigger run requested: {trigger_id} ({trigger_name})")

        # Emit signal for handler
        self.trigger_run_requested.emit(trigger_id)

        # Also emit workflow run signal through main window
        self.main_window.workflow_run.emit()

        self.main_window.show_status(f"Running trigger: {trigger_name}", 3000)

    def get_triggers(self) -> List[Dict[str, Any]]:
        """
        Get all triggers from the bottom panel.

        Returns:
            List of trigger configuration dictionaries
        """
        bottom_panel = self.main_window.get_bottom_panel()
        if bottom_panel:
            return bottom_panel.get_triggers()
        return []

    def get_trigger_count(self) -> int:
        """
        Get the number of triggers.

        Returns:
            Number of triggers
        """
        return len(self.get_triggers())

    def get_trigger_by_id(self, trigger_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a trigger by its ID.

        Args:
            trigger_id: ID of the trigger to find

        Returns:
            Trigger configuration dictionary or None if not found
        """
        triggers = self.get_triggers()
        for trigger in triggers:
            if trigger.get("id") == trigger_id:
                return trigger
        return None

    def set_triggers(self, triggers: List[Dict[str, Any]]) -> None:
        """
        Set the list of triggers (used when loading a workflow).

        Args:
            triggers: List of trigger configuration dictionaries
        """
        bottom_panel = self.main_window.get_bottom_panel()
        if bottom_panel:
            bottom_panel.set_triggers(triggers)
            self._triggers = triggers.copy()
            self.triggers_changed.emit()
            logger.debug(f"Set {len(triggers)} triggers")

    def clear_triggers(self) -> None:
        """Clear all triggers."""
        bottom_panel = self.main_window.get_bottom_panel()
        if bottom_panel:
            bottom_panel.clear_triggers()
            self._triggers.clear()
            self.triggers_changed.emit()
            logger.debug("Cleared all triggers")

    def _add_trigger_to_panel(self, trigger_config: Dict[str, Any]) -> None:
        """
        Add a trigger to the bottom panel.

        Args:
            trigger_config: Trigger configuration to add
        """
        bottom_panel = self.main_window.get_bottom_panel()
        if bottom_panel:
            bottom_panel.add_trigger(trigger_config)
            self._triggers.append(trigger_config)
        else:
            logger.error("Bottom panel not available for adding trigger")

    def _update_trigger_in_panel(self, trigger_config: Dict[str, Any]) -> None:
        """
        Update a trigger in the bottom panel.

        Args:
            trigger_config: Updated trigger configuration
        """
        bottom_panel = self.main_window.get_bottom_panel()
        if bottom_panel:
            bottom_panel.update_trigger(trigger_config)
            # Update internal list
            trigger_id = trigger_config.get("id")
            for i, t in enumerate(self._triggers):
                if t.get("id") == trigger_id:
                    self._triggers[i] = trigger_config
                    break
        else:
            logger.error("Bottom panel not available for updating trigger")

    def _remove_trigger_from_panel(self, trigger_id: str) -> None:
        """
        Remove a trigger from the bottom panel.

        Args:
            trigger_id: ID of the trigger to remove
        """
        bottom_panel = self.main_window.get_bottom_panel()
        if bottom_panel:
            bottom_panel.remove_trigger(trigger_id)
        else:
            logger.error("Bottom panel not available for removing trigger")

    def _get_trigger_name(self, trigger_id: str) -> str:
        """
        Get the name of a trigger by its ID.

        Args:
            trigger_id: ID of the trigger

        Returns:
            Trigger name or 'Unknown' if not found
        """
        trigger = self.get_trigger_by_id(trigger_id)
        if trigger:
            return trigger.get("name", "Unnamed")
        return "Unknown"

    def _show_trigger_error(self, error_message: str) -> None:
        """
        Display trigger error to user.

        Args:
            error_message: Error message to display
        """
        QMessageBox.warning(
            self.main_window,
            "Trigger Error",
            f"Trigger operation failed:\n{error_message}",
        )
