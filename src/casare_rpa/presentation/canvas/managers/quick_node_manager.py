"""
Quick Node Manager.

Manages single-key hotkeys used to quickly create nodes at the cursor position
on the canvas.

This is used by:
- QuickNodeConfigDialog (configure bindings)
- NodeGraphWidget event filter (create nodes on key press)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from loguru import logger


@dataclass(frozen=True, slots=True)
class QuickNodeBinding:
    node_type: str
    display_name: str
    category: str


class QuickNodeManager:
    _SETTINGS_KEY_ENABLED = "canvas.quick_node_mode"
    _SETTINGS_KEY_BINDINGS = "canvas.quick_node_bindings"

    _VALID_KEYS: tuple[str, ...] = tuple(chr(c) for c in range(ord("a"), ord("z") + 1))

    def __init__(self, settings_manager: Any | None = None) -> None:
        if settings_manager is None:
            from casare_rpa.utils.settings_manager import get_settings_manager

            settings_manager = get_settings_manager()

        self._settings = settings_manager

        self._enabled: bool = bool(self._settings.get(self._SETTINGS_KEY_ENABLED, True))
        self._bindings: dict[str, QuickNodeBinding] = {}

        self._load_bindings_from_settings()

        # Only apply defaults if user has never configured bindings.
        _missing = object()
        saved = self._settings.get(self._SETTINGS_KEY_BINDINGS, _missing)
        if saved is _missing:
            self.reset_to_defaults()

    def is_enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        try:
            self._settings.set(self._SETTINGS_KEY_ENABLED, self._enabled)
        except Exception as e:
            logger.debug(f"QuickNodeManager: Failed to persist enabled state: {e}")

    def get_bindings(self) -> dict[str, QuickNodeBinding]:
        return dict(self._bindings)

    def get_binding(self, key: str) -> QuickNodeBinding | None:
        k = (key or "").strip().lower()
        if not k:
            return None
        return self._bindings.get(k)

    def get_available_keys(self) -> list[str]:
        used = set(self._bindings.keys())
        return [k for k in self._VALID_KEYS if k not in used]

    def remove_binding(self, key: str) -> None:
        k = (key or "").strip().lower()
        if not k:
            return
        self._bindings.pop(k, None)

    def set_binding(self, key: str, node_type: str, display_name: str, category: str) -> None:
        k = (key or "").strip().lower()
        if k not in self._VALID_KEYS:
            raise ValueError(f"Invalid quick node key: {key!r}")

        node_type = (node_type or "").strip()
        if not node_type:
            raise ValueError("node_type is required")

        if not self._is_valid_node_type(node_type):
            raise ValueError(f"Unknown node type: {node_type}")

        # Enforce 1:1 mapping (a node can only be bound to one key).
        for existing_key, binding in list(self._bindings.items()):
            if binding.node_type == node_type and existing_key != k:
                self._bindings.pop(existing_key, None)

        self._bindings[k] = QuickNodeBinding(
            node_type=node_type,
            display_name=display_name or node_type,
            category=category or "",
        )

    def reset_to_defaults(self) -> None:
        """
        Reset bindings to a small sensible default set.

        Defaults are only applied for node types that exist in the current build.
        """
        self._bindings.clear()

        defaults: list[tuple[str, str]] = [
            ("b", "LaunchBrowserNode"),
            ("c", "ClickElementNode"),
            ("t", "TypeTextNode"),
        ]

        for key, node_type in defaults:
            if not self._is_valid_node_type(node_type):
                continue

            display_name, category = self._get_node_metadata(node_type)
            self._bindings[key] = QuickNodeBinding(
                node_type=node_type,
                display_name=display_name,
                category=category,
            )

    def save_bindings(self) -> None:
        payload: dict[str, dict[str, str]] = {}
        for key, binding in self._bindings.items():
            payload[key] = {
                "node_type": binding.node_type,
                "display_name": binding.display_name,
                "category": binding.category,
            }

        try:
            self._settings.set(self._SETTINGS_KEY_BINDINGS, payload)
        except Exception as e:
            logger.debug(f"QuickNodeManager: Failed to persist bindings: {e}")

    def get_all_node_types(self) -> list[tuple[str, str]]:
        """
        Return all registered node types for UI selection.

        Returns:
            List of (node_type, display_name) tuples.
        """
        from casare_rpa.presentation.canvas.graph.node_registry import get_node_type_mapping

        mapping = get_node_type_mapping()
        nodes: list[tuple[str, str]] = []
        for node_type, entry in mapping.items():
            visual_class = entry[0]
            display_name = getattr(visual_class, "NODE_NAME", None) or node_type
            nodes.append((node_type, display_name))

        nodes.sort(key=lambda x: x[1].lower())
        return nodes

    def _load_bindings_from_settings(self) -> None:
        self._bindings.clear()
        raw = self._settings.get(self._SETTINGS_KEY_BINDINGS, {}) or {}
        if not isinstance(raw, dict):
            return

        for key, data in raw.items():
            if not isinstance(key, str):
                continue

            k = key.strip().lower()
            if k not in self._VALID_KEYS:
                continue

            if not isinstance(data, dict):
                continue

            node_type = str(data.get("node_type", "")).strip()
            if not node_type or not self._is_valid_node_type(node_type):
                continue

            display_name, category = self._get_node_metadata(node_type)
            self._bindings[k] = QuickNodeBinding(
                node_type=node_type,
                display_name=str(data.get("display_name") or display_name),
                category=str(data.get("category") or category),
            )

    def _is_valid_node_type(self, node_type: str) -> bool:
        from casare_rpa.presentation.canvas.graph.node_registry import is_valid_node_type

        return is_valid_node_type(node_type)

    def _get_node_metadata(self, node_type: str) -> tuple[str, str]:
        from casare_rpa.presentation.canvas.graph.node_registry import get_node_type_mapping

        mapping = get_node_type_mapping()
        entry = mapping.get(node_type)
        if not entry:
            return node_type, ""

        visual_class = entry[0]
        display_name = getattr(visual_class, "NODE_NAME", None) or node_type
        category = getattr(visual_class, "NODE_CATEGORY", None) or ""
        return display_name, category
