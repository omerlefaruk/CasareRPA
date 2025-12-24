"""
Quick node creation manager for hotkey-based node creation.

Press a single key to instantly create a node at cursor position.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCursor, QKeySequence
from PySide6.QtWidgets import QApplication, QLineEdit, QTextEdit

if TYPE_CHECKING:
    from ..main_window import MainWindow


@dataclass
class QuickNodeBinding:
    """A hotkey-to-node binding."""

    key: str  # Single key like "b", "c", "n"
    node_type: str  # Node type name like "LaunchBrowserNode"
    display_name: str  # Human readable name like "Launch Browser"
    category: str  # Category for organization like "browser"


# Default hotkey bindings - single lowercase letters for speed
DEFAULT_BINDINGS: list[QuickNodeBinding] = [
    # Browser nodes
    QuickNodeBinding("b", "LaunchBrowserNode", "Launch Browser", "browser"),
    QuickNodeBinding("u", "GoToURLNode", "Go To URL", "browser"),
    QuickNodeBinding("c", "ClickElementNode", "Click Element", "browser"),
    QuickNodeBinding("t", "TypeTextNode", "Type Text", "browser"),
    # Navigation
    QuickNodeBinding("n", "NewTabNode", "New Tab", "browser"),
    QuickNodeBinding("r", "RefreshPageNode", "Refresh Page", "browser"),
    # Data extraction
    QuickNodeBinding("e", "ExtractTextNode", "Extract Text", "browser"),
    QuickNodeBinding("a", "GetAttributeNode", "Get Attribute", "browser"),
    # Wait nodes
    QuickNodeBinding("w", "WaitNode", "Wait", "browser"),
    QuickNodeBinding("q", "WaitForElementNode", "Wait For Element", "browser"),
    # Flow control
    QuickNodeBinding("i", "IfNode", "If Condition", "flow"),
    QuickNodeBinding("l", "ForLoopStartNode", "For Loop", "flow"),
    # Desktop
    QuickNodeBinding("d", "LaunchApplicationNode", "Launch Application", "desktop"),
    # Variables
    QuickNodeBinding("v", "SetVariableNode", "Set Variable", "variables"),
    QuickNodeBinding("g", "GetVariableNode", "Get Variable", "variables"),
    # Interaction
    QuickNodeBinding("m", "MessageBoxNode", "Message Box", "interaction"),
]


class QuickNodeManager:
    """
    Manages hotkey-based quick node creation.

    Features:
    - Single key press creates a node at cursor position
    - Node is centered on cursor (cursor at middle of node)
    - Configurable bindings with persistence
    - Default bindings for common nodes
    """

    CONFIG_FILE = "quick_node_bindings.json"

    def __init__(self, main_window: "MainWindow") -> None:
        """
        Initialize quick node manager.

        Args:
            main_window: Parent MainWindow instance
        """
        self._main_window = main_window
        self._bindings: dict[str, QuickNodeBinding] = {}
        self._actions: dict[str, QAction] = {}
        self._enabled = True

        # Load bindings and enabled state
        self._load_bindings()
        self._load_enabled_state()

    def _get_config_path(self) -> Path:
        """Get path to config file."""
        from casare_rpa.utils.config import CONFIG_DIR

        return CONFIG_DIR / self.CONFIG_FILE

    def _load_enabled_state(self) -> None:
        """Load enabled state from settings."""
        try:
            from casare_rpa.utils.settings_manager import get_settings_manager

            settings = get_settings_manager()
            self._enabled = settings.get("canvas.quick_node_mode", True)
            logger.debug(f"Loaded quick node mode enabled state: {self._enabled}")
        except Exception as e:
            logger.debug(f"Could not load quick node mode preference: {e}")
            self._enabled = True

    def _load_bindings(self) -> None:
        """Load bindings from config or use defaults."""
        config_path = self._get_config_path()

        if config_path.exists():
            try:
                with open(config_path, encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("bindings", []):
                        binding = QuickNodeBinding(**item)
                        self._bindings[binding.key] = binding
                    self._enabled = data.get("enabled", True)
                logger.debug(f"Loaded {len(self._bindings)} quick node bindings")
                return
            except Exception as e:
                logger.warning(f"Failed to load quick node bindings: {e}")

        # Use defaults
        for binding in DEFAULT_BINDINGS:
            self._bindings[binding.key] = binding
        logger.debug(f"Using {len(self._bindings)} default quick node bindings")

    def save_bindings(self) -> None:
        """Save current bindings to config file."""
        config_path = self._get_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "enabled": self._enabled,
            "bindings": [asdict(b) for b in self._bindings.values()],
        }

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self._bindings)} quick node bindings")
        except Exception as e:
            logger.error(f"Failed to save quick node bindings: {e}")

    def create_actions(self) -> None:
        """Create QActions for all bindings."""
        for key, binding in self._bindings.items():
            action = self._create_action(binding)
            if action:
                self._actions[key] = action

        logger.debug(f"Created {len(self._actions)} quick node actions")

    def _create_action(self, binding: QuickNodeBinding) -> QAction | None:
        """
        Create a QAction for a binding.

        Args:
            binding: The hotkey binding

        Returns:
            Created QAction or None
        """
        action = QAction(f"Quick: {binding.display_name}", self._main_window)
        action.setShortcut(QKeySequence(binding.key))
        action.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        action.setStatusTip(f"Create {binding.display_name} at cursor ({binding.key})")

        # Connect to handler with binding captured
        def make_handler(b: QuickNodeBinding):
            def handler():
                self._on_quick_create(b)

            return handler

        action.triggered.connect(make_handler(binding))
        action.setEnabled(self._enabled)

        # Add to main window for global shortcut
        self._main_window.addAction(action)

        return action

    def _is_text_widget_focused(self) -> bool:
        """Check if a text input widget has focus (suppress hotkeys when typing)."""
        focus_widget = QApplication.focusWidget()
        return isinstance(focus_widget, QLineEdit | QTextEdit)

    def _on_quick_create(self, binding: QuickNodeBinding) -> None:
        """
        Handle quick node creation.

        Args:
            binding: The triggered binding
        """
        if not self._enabled:
            return

        # Don't trigger when typing in text fields
        if self._is_text_widget_focused():
            return

        graph = self._main_window.get_graph()
        if not graph:
            logger.warning("No graph available for quick node creation")
            return

        viewer = graph.viewer()
        if not viewer:
            return

        # Get cursor position in scene coordinates
        global_pos = QCursor.pos()
        view_pos = viewer.mapFromGlobal(global_pos)
        scene_pos = viewer.mapToScene(view_pos)

        # Create the node
        from casare_rpa.presentation.canvas.graph.node_registry import (
            get_identifier_for_type,
            get_node_factory,
        )

        identifier = get_identifier_for_type(binding.node_type)
        if not identifier:
            logger.error(f"Unknown node type: {binding.node_type}")
            self._main_window.show_status(f"Unknown node type: {binding.node_type}", 3000)
            return

        try:
            # Create visual node at cursor first
            node = graph.create_node(identifier, pos=[scene_pos.x(), scene_pos.y()])

            if node:
                # Get actual node dimensions and recenter on cursor
                node_view = node.view
                if node_view:
                    rect = node_view.boundingRect()
                    # Move so cursor is at center of node
                    centered_x = scene_pos.x() - rect.width() / 2
                    centered_y = scene_pos.y() - rect.height() / 2
                    node.set_pos(centered_x, centered_y)

                # Attach CasareRPA node
                factory = get_node_factory()
                casare_node = factory.create_casare_node(node)
                if casare_node:
                    node.set_casare_node(casare_node)

                # Select the new node
                graph.clear_selection()
                node.set_selected(True)

                self._main_window.show_status(
                    f"Created {binding.display_name} [{binding.key}]", 1500
                )
                logger.debug(f"Quick created {binding.display_name} centered at cursor")
            else:
                logger.error(f"Failed to create node: {binding.node_type}")

        except Exception as e:
            logger.error(f"Quick node creation failed: {e}")
            self._main_window.show_status(f"Failed to create node: {e}", 3000)

    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable quick node creation.

        Args:
            enabled: Whether quick node hotkeys are active
        """
        self._enabled = enabled
        for action in self._actions.values():
            action.setEnabled(enabled)
        logger.info(f"Quick node creation {'enabled' if enabled else 'disabled'}")

    def is_enabled(self) -> bool:
        """Check if quick node creation is enabled."""
        return self._enabled

    def get_bindings(self) -> dict[str, QuickNodeBinding]:
        """Get all current bindings."""
        return self._bindings.copy()

    def set_binding(self, key: str, node_type: str, display_name: str, category: str) -> None:
        """
        Set or update a binding.

        Args:
            key: Single key (lowercase letter)
            node_type: Node type name
            display_name: Human readable name
            category: Category for organization
        """
        # Remove old action if exists
        if key in self._actions:
            old_action = self._actions.pop(key)
            self._main_window.removeAction(old_action)

        # Create new binding
        binding = QuickNodeBinding(key, node_type, display_name, category)
        self._bindings[key] = binding

        # Create new action
        action = self._create_action(binding)
        if action:
            self._actions[key] = action

        logger.debug(f"Set quick binding: {key} -> {node_type}")

    def remove_binding(self, key: str) -> bool:
        """
        Remove a binding.

        Args:
            key: Key to remove

        Returns:
            True if removed, False if not found
        """
        if key not in self._bindings:
            return False

        del self._bindings[key]

        if key in self._actions:
            action = self._actions.pop(key)
            self._main_window.removeAction(action)

        logger.debug(f"Removed quick binding: {key}")
        return True

    def reset_to_defaults(self) -> None:
        """Reset all bindings to defaults."""
        # Remove all current actions
        for action in self._actions.values():
            self._main_window.removeAction(action)
        self._actions.clear()
        self._bindings.clear()

        # Load defaults
        for binding in DEFAULT_BINDINGS:
            self._bindings[binding.key] = binding

        # Recreate actions
        self.create_actions()

        logger.info("Reset quick node bindings to defaults")

    def get_available_keys(self) -> list[str]:
        """
        Get list of available (unbound) single letter keys.

        Returns:
            List of available lowercase letters
        """
        all_keys = set("abcdefghijklmnopqrstuvwxyz")
        used_keys = set(self._bindings.keys())
        return sorted(all_keys - used_keys)

    def get_all_node_types(self) -> list[tuple[str, str]]:
        """
        Get all available node types for binding.

        Returns:
            List of (node_type, display_name) tuples
        """
        from casare_rpa.presentation.canvas.graph.node_registry import (
            get_node_type_mapping,
        )

        mapping = get_node_type_mapping()
        result = []

        for node_type, (visual_class, _, _) in mapping.items():
            display_name = getattr(visual_class, "NODE_NAME", node_type)
            # Skip internal/composite nodes
            if getattr(visual_class, "INTERNAL_NODE", False):
                continue
            if getattr(visual_class, "COMPOSITE_NODE", False):
                continue
            result.append((node_type, display_name))

        return sorted(result, key=lambda x: x[1])
